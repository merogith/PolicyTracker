"""Automatic recovery, publication and settings use invented data; no live AI."""
import base64
import copy
import http.client
import json
import shutil
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from policytracker.ai_runtime import AIError, AIService, AISession
from policytracker.country_runs import CountryRunner, synthesis_batches, synthesis_evidence, merge_synthesis, check_translation
from policytracker.engineering import compose_v2, read_json, extraction_errors
from policytracker.inventory import register_document
from policytracker.preparation import recover_page, recovery_check, RECOVERY_SCHEMA
from policytracker.profiles import ProfileStore, demo_bundle, encoded, sha, validate_bundle
from policytracker.settings import DEFAULTS, apply_settings, settings_view, method_module
from policytracker.local_server import LocalServer
from test_ai_runtime import FakeAPI, FakeRPC, KEY
from test_country_runs import FixtureRunner, FixtureProvider, SELECTION
from test_document_preparation import pdf_bytes
from test_method_customization import workspace_test_directory
from test_operation_runs import OperationProvider, OperationRunner, request

ROOT = Path(__file__).resolve().parents[1]


class AutomationTests(unittest.TestCase):
    def setUp(self):
        self.temp = workspace_test_directory(); self.root = self.temp.__enter__()
        for folder in ('src/policytracker', 'config', 'schemas', 'prompts', 'examples/v2', 'scripts'):
            shutil.copytree(ROOT/folder, self.root/folder, ignore=shutil.ignore_patterns('__pycache__'))
        self.path = self.root/'test.sqlite3'

    def tearDown(self):
        self.temp.__exit__(None, None, None)

    def document(self):
        path = self.root/'data/sources/Kazakhstan/NDC/Invented/Original.pdf'
        path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(pdf_bytes())
        return dict(document_id='doc-invented', title='Invented PDF', country_code='KAZ',
                    relative_path=path.relative_to(self.root).as_posix(), sha256=sha(path.read_bytes()))

    def test_recovery_uses_image_automatically_and_corrects_numeric_omissions(self):
        doc = self.document(); raw = (self.root/doc['relative_path']).read_bytes()
        image = self.root/'data/derived/page.png'; image.parent.mkdir(parents=True); image.write_bytes(b'\x89PNG\r\n\x1a\nfixture')
        page = dict(page=1, text='Install 20 warning systems by 2030.', concerns=['raster_content_may_contain_text'], review=None)
        visual = Mock(side_effect=[{'status':'complete','text':'Install warning systems by 2030.','notes':[]},
                                   {'status':'complete','text':page['text']+' Chart: 5 regions.','notes':[]}])
        with patch('policytracker.preparation.alternate_text', return_value=page['text']), patch('policytracker.preparation.find_ocr_engine', return_value=None), patch('policytracker.preparation.render_page', return_value=image):
            result = recover_page(self.root, doc, page, DEFAULTS, visual)
        self.assertEqual(result['status'], 'complete'); self.assertEqual(visual.call_count, 2)
        self.assertIn('20', visual.call_args.args[1]['discrepancies'][0])
        self.assertEqual(result['method'], 'vision'); self.assertEqual(result['artifacts'][0]['sha256'],sha(image.read_bytes()))
        self.assertEqual((self.root/doc['relative_path']).read_bytes(), raw)
        self.assertFalse(list((self.root/'data/derived').glob('**/*review.json')))

    def test_vision_unavailable_keeps_readable_text_with_partial_coverage(self):
        doc = self.document(); page=dict(page=1,text='Readable caption',concerns=['raster_content_may_contain_text'],review=None)
        with patch('policytracker.preparation.alternate_text', return_value='Readable caption'), patch('policytracker.preparation.find_ocr_engine', return_value=None):
            result=recover_page(self.root, doc, page, {**DEFAULTS,'vision_recovery':False})
        self.assertEqual((result['status'],result['text']),('partial','Readable caption')); self.assertTrue(result['notes'])

    def test_every_problem_page_and_broken_document_gets_coverage(self):
        doc=self.document(); bad={**doc,'document_id':'bad','title':'Broken','relative_path':'data/sources/broken.pdf','sha256':sha(b'broken')}
        (self.root/bad['relative_path']).write_bytes(b'broken')
        runner=CountryRunner(self.root,self.path,Mock())
        job=dict(id='coverage-test',country='KAZ',documents=[doc,bad],settings=DEFAULTS,selection=SELECTION,method=runner.method())
        pages=[dict(page=1,text='',concerns=['sparse_text'],review=None),dict(page=2,text='',concerns=['parse_failed'],review=None)]
        recovered=[dict(status='complete',text='Recovered first page',method='vision',notes=[],artifacts=[]),dict(status='unreadable',text='',method='native_partial',notes=['Clipped page'],artifacts=[])]
        with patch('policytracker.country_runs.inspect_document',side_effect=[pages,ValueError('Broken structure')]), patch('policytracker.country_runs.pdf_page_count',side_effect=ValueError('No pages')), patch('policytracker.country_runs.recover_page',side_effect=recovered) as recover:
            sources=runner.prepare_automatically(job)
        self.assertEqual(recover.call_count,2); self.assertEqual(len(sources[0]['page_checks']),2)
        self.assertEqual([d['status'] for d in job['source_coverage']],['partial','unreadable'])
        self.assertEqual(job['source_coverage'][0]['issues'][0]['page'],2)

    def test_partial_profile_publishes_and_can_be_unpublished_without_changing_archive(self):
        provider=FixtureProvider()
        runner=FixtureRunner(self.root,self.path,provider,synthetic=True)
        limitation='One cropped table cell'
        received={}
        generate=provider.generate_json
        def respond(session,selection,packet):
            response=generate(session,selection,packet)
            if packet['route'] in ('translate','extract'):
                received[packet['route']]=json.loads(packet['input'])['task_context']['source_coverage']
                output=json.loads(response['text'])
                if packet['route']=='translate':
                    output['segments'][0]['notes'].append(limitation)
                else:
                    output['notes'].append(limitation)
                response['text']=json.dumps(output)
            return response
        provider.generate_json=respond
        original=runner.prepare_sources
        def prepare(job):
            sources=original(job); source=sources[0]; text=''.join(s['text'] for s in source['segments'])
            source['page_checks']=[{'page':1,'concerns':['sparse_text'],'review':None,'parsed_text_sha256':sha(text.encode()),
                'automatic':dict(page=1,source_sha256=source['sha256'],text=text,text_sha256=sha(text.encode()),status='partial',method='vision',notes=['One cropped table cell'],artifacts=[])}]
            job['source_coverage']=[dict(document_id=source['document_id'],title=source['title'],sha256=source['sha256'],status='partial',pages=1,issues=[{'page':1,'status':'partial','notes':['One cropped table cell']}])]
            return sources
        runner.prepare_sources=prepare
        started=runner.start(AISession(),{'country':'KAZ','document_ids':['synthetic-document'],**SELECTION})
        runner.thread.join(30); self.assertFalse(runner.thread.is_alive())
        job=runner.get(started['id']); self.assertEqual(job['status'],'completed',job.get('error'))
        self.assertEqual(set(received),{'translate','extract'})
        for coverage in received.values():
            self.assertEqual(coverage,job['source_coverage'])
            self.assertEqual(coverage[0]['status'],'partial')
            self.assertEqual(coverage[0]['issues'][0]['notes'],[limitation])
        with ProfileStore(self.root,self.path) as store:
            saved=store.country('KAZ',True)['profile']; self.assertTrue(saved['published']); self.assertEqual(saved['report']['availability'],'partial')
            self.assertEqual(saved['source_coverage'],job['source_coverage'])
            self.assertIn(limitation,saved['sources'][0]['segments'][0]['translation_notes'])
            self.assertIn(limitation,saved['extraction']['notes'])
            before=[tuple(r) for r in store.db.execute('SELECT * FROM objects')]
            self.assertIsNone(store.moderate(saved['id'],False)['profile'])
            self.assertFalse(store.profile(saved['id'])['published'])
            selection=store.selection('KAZ',True)
            with self.assertRaisesRegex(ValueError,'Publish this version'):store.select('KAZ',saved['id'],selection['revision'],True)
            self.assertEqual(store.moderate(saved['id'],True)['profile']['id'],saved['id'])
            self.assertEqual(before,[tuple(r) for r in store.db.execute('SELECT * FROM objects')])
            forged={k:v for k,v in saved.items() if k in demo_bundle(self.root) or k=='source_coverage'}
            forged['source_coverage'][0]['status']='complete'
            with self.assertRaisesRegex(ValueError,'hides unresolved'):validate_bundle(self.root,forged)

    def test_vision_recovery_receipt_survives_profile_publication_and_cached_rerun(self):
        doc=self.document()
        manifest=self.root/'data/manifests/corpus.json'; manifest.parent.mkdir(parents=True)
        manifest.write_text(json.dumps({'documents':[doc]}))
        fixture=demo_bundle(self.root)
        text=''.join(s['text'] for s in fixture['sources'][0]['segments'])
        segment_id=doc['document_id']+':p1:s1'
        self.assertLess(len(text),3000)
        provider=FixtureProvider(); generate=provider.generate_json
        def respond(session,selection,packet):
            if packet['route']=='recover':
                provider.calls.append('recover')
                return {'text':json.dumps({'status':'complete','text':text,'notes':[]}),
                        'route':selection['route'],'actual_model':selection['model'],
                        'confirmed_effort':selection['effort'],'request_id':'synthetic-recovery','usage':{}}
            response=generate(session,selection,packet); output=json.loads(response['text'])
            if packet['route']=='triage':
                profile=output['document_profiles'][0];profile['input_id']=doc['document_id']
                profile['metadata_evidence_ids']=[segment_id];profile['geography']['evidence_ids']=[segment_id]
            elif packet['route']=='translate':
                template=output['segments'][0]
                output['segments']=[{**template,'segment_id':segment_id,'source_language':'mul',
                    'method':'machine_translation','english_text':' '.join(s['english_text'] for s in fixture['sources'][0]['segments'])}]
            elif packet['route']=='extract':
                for evidence in output['evidence']:
                    evidence['segment_id']=segment_id
                    if evidence['english_segment_id'] is not None:evidence['english_segment_id']=segment_id
                output['coverage']=[{**output['coverage'][0],'segment_id':segment_id,'disposition':'extracted',
                    'record_ids':[r['local_id'] for r in output['records']]}]
            return {**response,'text':json.dumps(output),'route':selection['route']}
        provider.generate_json=respond
        runner=CountryRunner(self.root,self.path,provider,synthetic=True)
        image=self.root/'tmp/recovery.png';image.parent.mkdir();image.write_bytes(b'synthetic image')
        page={'page':1,'text':'','concerns':['sparse_text'],'review':None}
        def recover(root,document,page,settings,visual):
            result=visual(image,{'source_sha256':doc['sha256'],'physical_page':1})
            return {**result,'method':'vision','artifacts':[]}
        receipts=[]
        for _ in range(2):
            with patch('policytracker.country_runs.inspect_document',return_value=[page]),patch('policytracker.country_runs.recover_page',side_effect=recover):
                started=runner.start(AISession(),{'country':'KAZ','document_ids':[doc['document_id']],**SELECTION})
                runner.thread.join(30);self.assertFalse(runner.thread.is_alive())
            job=runner.get(started['id']);self.assertEqual(job['status'],'completed',job.get('error'))
            with runner.store() as store:
                saved=store.profile(job['profile_id']);self.assertTrue(saved['published'])
                automatic=saved['sources'][0]['page_checks'][0]['automatic']
                receipt=automatic['generation_step'];receipts.append(copy.deepcopy(receipt))
                step=next(s for s in saved['generation']['steps'] if s['step']=='recover:'+doc['document_id']+':1')
                self.assertEqual(step['result_hash'],receipt['result_hash'])
                result=json.loads(store.get(receipt['result_hash']))
                self.assertEqual(json.loads(store.get(result['response_hash']))['text'],json.dumps({'status':'complete','text':text,'notes':[]}))
                self.assertEqual(automatic['text'],text)
                invalid=copy.deepcopy({k:v for k,v in saved.items() if k in fixture or k=='source_coverage'})
                invalid['sources'][0]['page_checks'][0]['automatic']['generation_step']['signature']='not-a-fingerprint'
                with self.assertRaisesRegex(ValueError,'signature'):validate_bundle(self.root,invalid)
        self.assertEqual(receipts[0],receipts[1])
        self.assertEqual(provider.calls.count('recover'),1)

    def test_upstream_gap_notes_do_not_allow_new_translation_or_extraction_defects(self):
        segments=demo_bundle(self.root)['sources'][0]['segments']
        translation=read_json(self.root/'examples/v2/translation.json')
        translation['segments'][0]['notes']=['An upstream cropped cell remains missing; supplied text is preserved.']
        check_translation(translation,segments)
        for defect,expected in [('missing','every segment'),('altered','changed the original'),('unreadable','Translation needs attention')]:
            with self.subTest(defect=defect):
                output=copy.deepcopy(translation)
                if defect=='missing':output['segments'].pop()
                elif defect=='altered':output['segments'][0]['english_text']='Only part of the supplied text.'
                else:output['segments'][0]['quality_flags']=['A supplied numeric condition cannot be rendered faithfully.']
                with self.assertRaisesRegex(ValueError,expected):check_translation(output,segments)
        extraction=read_json(self.root/'examples/v2/extraction.json')
        extraction['notes'].append('An upstream cropped cell remains missing.')
        extraction['issues'].append('A supplied numeric condition is unreadable.')
        errors=extraction_errors(self.root,extraction,'KAZ',
            source_segments={s['id']:s['text'] for s in segments},owned_segment_ids=[s['id'] for s in segments])
        self.assertTrue(any('unresolved blocking issue: A supplied numeric condition is unreadable.' in error for error in errors))

    def test_partial_visual_result_is_retried_not_reused_as_success(self):
        provider=FixtureProvider(); runner=FixtureRunner(self.root,self.path,provider,synthetic=True)
        response=dict(status='partial',text='Readable fragment',notes=['Rest illegible'])
        provider.generate_json=Mock(return_value={'text':json.dumps(response)})
        job=dict(id='recovery-1',country='KAZ',selection=SELECTION,settings=DEFAULTS,method=runner.method(),stage='prepare')
        for ident in ['recovery-1','recovery-2']:
            job['id']=ident
            with runner.store() as store:runner.write(store,job)
            runner.step(AISession(),job,'recover:1','recover',{}, {}, recovery_check)
        self.assertEqual(provider.generate_json.call_count,2)

    def test_images_are_hashed_and_sent_on_both_provider_routes(self):
        image=self.root/'data/derived/page.png'; image.parent.mkdir(parents=True); image.write_bytes(b'\x89PNG\r\n\x1a\nfixture')
        packet=compose_v2(self.root,'translate',{},{}); packet['images']=[dict(path='data/derived/page.png',sha256=sha(image.read_bytes()))]
        api,rpc=FakeAPI(),FakeRPC(); service=AIService(self.root,rpc=rpc,transport=api); session=AISession()
        service.connect_api(session,KEY);service.generate_json(session,SELECTION,packet)
        self.assertEqual(api.calls[-1][2]['input'][0]['content'][1]['type'],'input_image')
        service.connect_chatgpt(session);service.generate_json(session,{**SELECTION,'route':'codex_chatgpt'},packet)
        self.assertEqual(dict(rpc.calls)['turn/start']['input'][1]['type'],'image')
        image.write_bytes(b'\x89PNG\r\n\x1a\nchanged')
        with self.assertRaisesRegex(AIError,'changed'):service.generate_json(session,SELECTION,packet)

    def test_settings_persist_restore_and_reject_stale_or_invalid_values(self):
        module=method_module(self.root); module.rebuild=Mock()
        untouched={f['path']:(self.root/f['path']).read_bytes() for f in module.pack()['files'] if f['path']!='config/automation.json'}
        first=settings_view(self.root)
        with patch('policytracker.settings.method_module',return_value=module):
            after=apply_settings(self.root,dict(revision=first['revision'],settings={**first['settings'],'detail':'concise','glossary':'Preserve institution names'}))
            self.assertEqual(settings_view(self.root)['settings']['detail'],'concise'); module.rebuild.assert_called_once()
            for path,raw in untouched.items(): self.assertEqual((self.root/path).read_bytes(),raw,path)
            with self.assertRaisesRegex(ValueError,'another window'):apply_settings(self.root,dict(revision=first['revision'],settings=first['settings']))
            before=next(h for h in after['history'] if h['version']==first['settings']['version'])
            restored=apply_settings(self.root,dict(revision=after['revision'],restore=before['id']))
            self.assertEqual(restored['settings']['detail'],first['settings']['detail'])
            module.rebuild.side_effect=[ValueError('Synthetic build failure'),None]
            original=(self.root/'config/automation.json').read_bytes()
            with self.assertRaisesRegex(ValueError,'build failure'):apply_settings(self.root,dict(revision=restored['revision'],settings={**restored['settings'],'detail':'detailed'}))
            self.assertEqual((self.root/'config/automation.json').read_bytes(),original)
            with self.assertRaisesRegex(ValueError,'existing topics'):apply_settings(self.root,dict(revision=restored['revision'],settings={**restored['settings'],'topic_ids':['unknown']}))

    def test_settings_affect_requests_and_reuse_unaffected_translation(self):
        provider=FixtureProvider(); runner=FixtureRunner(self.root,self.path,provider,synthetic=True); packets=[]
        generate=provider.generate_json
        def capture(session,selection,packet): packets.append(packet);return generate(session,selection,packet)
        provider.generate_json=capture
        for detail in ['standard','concise']:
            settings={**DEFAULTS,'detail':detail,'glossary':'Preferred terms'}
            (self.root/'config/automation.json').write_text(json.dumps(settings))
            started=runner.start(AISession(),{'country':'KAZ','document_ids':['synthetic-document'],**SELECTION}); runner.thread.join(30)
            self.assertEqual(runner.get(started['id'])['status'],'completed')
        self.assertEqual(provider.calls.count('translate'),1);self.assertEqual(provider.calls.count('prime'),2)
        self.assertEqual(json.loads(next(p for p in reversed(packets) if p['route']=='prime')['input'])['task_context']['user_preferences']['detail'],'concise')

    def test_upload_registers_original_name_bytes_and_stable_duplicate(self):
        path=self.root/'data/manifests/corpus.json';path.parent.mkdir(parents=True);path.write_text('{"documents":[]}')
        raw=pdf_bytes();payload=dict(country='KAZ',type='NDC',title='Invented upload',filename='My original.pdf',base64=base64.b64encode(raw).decode())
        with patch('policytracker.preparation.run_local'):
            first=register_document(self.root,payload); second=register_document(self.root,payload)
        self.assertEqual(first['document']['document_id'],second['document']['document_id']);self.assertTrue(second['already_registered'])
        saved=self.root/first['document']['relative_path'];self.assertEqual(saved.name,payload['filename']);self.assertEqual(saved.read_bytes(),raw)
        self.assertTrue(saved.with_name('Source.txt').is_file())
        with self.assertRaisesRegex(ValueError,'filename'):register_document(self.root,{**payload,'filename':'../escape.pdf'})

    def test_large_synthesis_keeps_every_record_quote_and_context(self):
        extraction=read_json(self.root/'examples/v2/extraction.json'); source=copy.deepcopy(extraction)
        extraction['records']=[{**source['records'][0],'local_id':f'r-{i}','description_en':'x'*2000} for i in range(10)]
        limit=len(encoded(synthesis_evidence({**extraction,'records':extraction['records'][:1]})))+100
        parts=synthesis_batches(extraction,limit)
        self.assertGreater(len(parts),1)
        self.assertEqual([r['local_id'] for p in parts for r in p['records']],[r['local_id'] for r in extraction['records']])
        self.assertEqual({e['local_id'] for p in parts for e in p['evidence']},{e['local_id'] for e in extraction['evidence']})
        report=read_json(self.root/'examples/v2/prime-report.json')
        merged=merge_synthesis([report,copy.deepcopy(report)])
        self.assertEqual(merged['headline_findings'],report['headline_findings']);self.assertIn('bounded batches',merged['limitations'][-1])

    def test_batched_partial_outputs_work_for_every_analysis_shape(self):
        provider=OperationProvider();runner=OperationRunner(self.root,self.path,provider,synthetic=True)
        original=runner.prepare_sources
        def prepare(job):
            sources=original(job)
            job['source_coverage']=[dict(document_id=s['document_id'],title=s['title'],sha256=s['sha256'],pages=1,
                status='partial',issues=[{'page':1,'status':'partial','notes':['Invented clipped cell']}]) for s in sources]
            return sources
        runner.prepare_sources=prepare
        def bounded(extraction, **kwargs):
            # Force more than one part while still fitting each indivisible
            # source batch, rather than relying on an unenforced one-byte cap.
            limit=max(len(encoded(synthesis_evidence(p))) for p in kwargs['note_scopes'])
            return synthesis_batches(extraction,limit,**kwargs)
        with patch('policytracker.country_runs.synthesis_batches',side_effect=bounded):
            for task in ['extract','brief','gaps','compare']:
                started=runner.start(AISession(),{'operation':request(task,['doc-1','doc-2'])});runner.thread.join(40)
                job=runner.get(started['id']);self.assertEqual(job['status'],'completed',job.get('error'))
                result=runner.operation_result(job['id']);self.assertTrue(result['published'])
                self.assertTrue(any('Incomplete source coverage' in x for x in result['output']['limitations']))
                if task in ('extract','brief'):self.assertEqual(result['output']['availability'],'partial')
                else:self.assertNotIn('availability',result['output'])
                runner.moderate(job['id'],False);self.assertFalse(runner.operation_result(job['id'])['published'])

    def test_unreadable_selected_document_can_be_disclosed_in_analysis(self):
        provider=OperationProvider();runner=OperationRunner(self.root,self.path,provider,synthetic=True)
        original=runner.prepare_sources
        def prepare(job):
            sources=original(job);bad=sources.pop()
            job['source_coverage']=[dict(document_id=bad['document_id'],title=bad['title'],sha256=bad['sha256'],pages=1,status='unreadable',issues=['Broken PDF'])]
            return sources
        runner.prepare_sources=prepare
        started=runner.start(AISession(),{'operation':request('extract',['doc-1','doc-2'])});runner.thread.join(40)
        job=runner.get(started['id']);self.assertEqual(job['status'],'completed',job.get('error'))
        result=runner.operation_result(job['id']);self.assertEqual(result['output']['availability'],'partial')
        self.assertEqual(result['request']['source_groups'][0]['document_ids'],['doc-1','doc-2'])
        self.assertEqual(len(result['sources']),1)

    def test_retry_setting_allows_three_retries_without_changing_route(self):
        provider=FixtureProvider();runner=FixtureRunner(self.root,self.path,provider,synthetic=True)
        provider.generate_json=Mock(side_effect=[AIError('network','Temporary')] * 3 + [{'text':json.dumps(dict(status='complete',text='Recovered',notes=[]))}])
        job=dict(id='retry',country='KAZ',selection=SELECTION,settings={**DEFAULTS,'retry_limit':3},method=runner.method(),stage='prepare')
        with runner.store() as store:runner.write(store,job)
        with patch.object(runner.stop_event,'wait',return_value=False):
            result=runner.step(AISession(),job,'recover:1','recover',{}, {}, recovery_check)
        self.assertEqual(result['status'],'complete');self.assertEqual(provider.generate_json.call_count,4)
        self.assertTrue(all(c.args[1]==SELECTION for c in provider.generate_json.call_args_list))

    def test_translation_does_not_require_a_national_attribution_decision(self):
        runner=CountryRunner(self.root,self.path,Mock())
        result=runner.operation_metadata(AISession(),{'operation':{'task':'translate'}},demo_bundle(self.root)['sources'],[])
        self.assertFalse(result[0]['verified']);runner.service.generate_json.assert_not_called()

    def test_new_writes_require_session_and_settings_wait_for_active_jobs(self):
        server=LocalServer(self.root,0,service=AIService(self.root,rpc=FakeRPC()),profiles_path=self.path)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        connection=http.client.HTTPConnection('127.0.0.1',server.server_port)
        try:
            for path in ('settings','method','documents/register','publication'):
                connection.request('POST','/api/ai/'+path,'{}',{'Content-Type':'application/json'})
                response=connection.getresponse();self.assertEqual(response.status,401);response.read()
            connection.request('GET','/api/ai/session');response=connection.getresponse()
            cookie=response.getheader('Set-Cookie').split(';')[0];token=json.loads(response.read())['csrf']
            headers={'Content-Type':'application/json','Cookie':cookie,'Origin':f'http://127.0.0.1:{server.server_port}','X-PolicyTracker-CSRF':token}
            server.countries.active='synthetic-active'
            for path in ('settings','method','documents/register'):
                connection.request('POST','/api/ai/'+path,'{}',headers);response=connection.getresponse()
                self.assertEqual(response.status,409);response.read()
        finally:
            server.countries.active=None;connection.close();server.shutdown();server.server_close();thread.join(2)


if __name__=='__main__':unittest.main()

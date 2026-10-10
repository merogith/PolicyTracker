"""Real worker/storage boundaries with invented sources and a synthetic provider."""
import copy
import json
import shutil
import unittest
import http.client
import threading
from pathlib import Path

from policytracker.ai_runtime import AISession, AIService
from policytracker.country_runs import CountryRunner
from policytracker.engineering import read_json
from policytracker.operations import compose_operation, normalize_request, scoped_evidence, validate_operation_output
from policytracker.profiles import ProfileStore, demo_bundle, encoded, sha
from policytracker.local_server import LocalServer
from test_country_runs import FixtureProvider, ROOT, SELECTION
from test_ai_runtime import FakeRPC
from test_method_customization import workspace_test_directory


def request(task, ids=None):
    task_config = next(t for t in read_json(ROOT / 'config/operations/tasks.json')['tasks'] if t['id'] == task)
    ids = ids or ['doc-1']
    return {'schema_version':'2.0.0','kind':'ad_hoc','task':task,
            'source_groups':([{'id':d,'label':d,'document_ids':[d]} for d in ids] if task=='compare' else [{'id':'selected','label':'Selected documents','document_ids':ids}]),
            'filters':{'domain_ids':[],'topic_ids':[],'hazards':[],'risk_functions':[]},
            'requested_fields':[o['id'] for o in task_config['options'] if o['default']],
            'comparison_mode':'documents' if task=='compare' else None,'include_analyst_proposals':False,
            'question':'Which commitments need finance?' if task=='brief' else '', 'instructions':'',
            'model':{**SELECTION,'fallback_allowed':'never'},
            'output':{'artifact':task_config['artifact'],'language':'en','include_original_evidence':True,'coverage_mode':'all_selected_documents'},
            'uploads':[],'execution_state':'not_run'}


class OperationProvider(FixtureProvider):
    def generate_json(self, session, selection, packet):
        self.calls.append(packet['route'])
        data = json.loads(packet['input'])['untrusted_source_data']
        ctx = json.loads(packet['input'])['task_context']
        route=packet['route']
        if route=='triage':
            if 'pairs' in ctx:
                out={'document_profiles':[],'relationships':[{'input_ids':pair,'kind':getattr(self,'relationship','revision'),'evidence_ids':[data['source_samples'][d][0]['id'] for d in pair],'reason':'Invented edition dates'} for pair in ctx['pairs']]}
            else:
                doc=data['input_id']; out={'document_profiles':[{'input_id':doc,'title':doc,'instrument_type':'NDC','document_state':'submitted','publication_date':'2020' if doc=='doc-1' else '2025','languages':['ru','en'],'geography':{'country_codes':['KAZ'],'reporting_party':'Kazakhstan','scope':'national','locations':[],'evidence_ids':[data['segments'][0]['id']]},'disposition':'prime_candidate','metadata_evidence_ids':[data['segments'][0]['id']],'notes':['Synthetic preview only'],'issues':[]}],'relationships':[]}
        elif route=='translate':
            base=read_json(ROOT/'examples/v2/translation.json')['segments']
            out={'segments':[{**copy.deepcopy(next(r for r in base if s['id'].endswith(r['segment_id']))),'segment_id':s['id'],'quality_flags':[]} for s in data['segments']]}
            for s,row in zip(data['segments'],out['segments']):
                if row['method']=='identity':row['english_text']=s['text']
        elif route=='extract':
            out=read_json(ROOT/'examples/v2/extraction.json')
            for e in out['evidence']:e['segment_id']=data['document_id']+':'+e['segment_id']
            for c in out['coverage']:c['segment_id']=data['document_id']+':'+c['segment_id']
        else:
            req=ctx['operation_request']; records=data['extraction'].get('records', [])
            def finding(r):return {'text_en':r['description_en'],'kind':'source_fact','citations':{'record_ids':[r['local_id']],'evidence_ids':r['evidence_ids']},'calculation':None,'limitations':[]}
            findings=[finding(r) for r in records]
            if route in ('focused_analysis','briefing'):
                out={'country_codes':ctx['country_codes'],'source_group_ids':ctx['source_group_ids'],'availability':'complete_in_declared_scope','headline_findings':findings,'sections':[{'section_id':s,'state':'found' if findings else 'not_found_in_scope','findings':findings,'gap_note':None if findings else 'No matching evidence in selected sources.'} for s in ctx['required_sections']],'prioritized_commitments':[],'followup_questions':[],'limitations':['Synthetic provider; no semantic quality claim.']}
                if route=='briefing' and 'questions' in req['requested_fields'] and findings:
                    out['followup_questions']=[{**findings[0],'kind':'analyst_suggestion','text_en':'What financing information should be checked next?'}]
            elif route=='workplan':
                out={'country_codes':ctx['country_codes'],'source_group_ids':ctx['source_group_ids'],'rows':[{'commitment_ids':[r['local_id']],'source_stated_action':finding(r),'source_actor_ids':[],'source_finance_ids':[],'source_indicator_ids':[],'proposed_support_activity':None,'proposed_indicator':None,'missing_information':data['delivery_checks'][r['local_id']],'verification_questions':[]} for r in records],'limitations':[]}
                if req['include_analyst_proposals']:
                    for row in out['rows']:
                        row['proposed_support_activity']={**row['source_stated_action'],'kind':'analyst_suggestion','text_en':'Ask the source owner to clarify financing.'}
            else:
                def group_findings(g):
                    allowed={e['local_id'] for e in data['extraction']['evidence'] if data['segment_documents'][e['segment_id']] in g['document_ids']}
                    return [f for f in findings if set(f['citations']['evidence_ids'])<=allowed]
                out={'groups':[{'group_id':g['id'],'label':g['label'],'document_version_ids':g['document_ids'],'release_ids':[],'scope_note':'Selected documents'} for g in req['source_groups']],
                     'rows':[{'dimension':d,'cells':[{'group_id':g['id'],'state':'found' if group_findings(g) else 'not_found_in_scope','findings':group_findings(g)} for g in req['source_groups']],'comparability':'descriptive_only','comparability_reason':'Source statements retained; no arithmetic.','normalization_calculation':None} for d in req['requested_fields']], 'synthesis':[],'exclusions':[],'limitations':[]}
        if route=='triage' and 'input_id' in data:
            out['document_profiles'][0]['instrument_type']=getattr(self,'instruments',{}).get(data['input_id'],'NDC')
            out['document_profiles'][0]['geography']['country_codes']=[getattr(self,'countries',{}).get(data['input_id'],'KAZ')]
        if route=='extract':
            code=getattr(self,'countries',{}).get(data['document_id'],'KAZ')
            for r in out['records']:r['geography']['country_codes']=[code]
        if self.on_result:self.on_result(route)
        return {'text':json.dumps(out),'actual_model':selection['model'],'confirmed_effort':selection['effort'],'request_id':'synthetic','usage':{'input_tokens':1,'output_tokens':1}}


class OperationRunner(CountryRunner):
    def documents(self,country,ids):
        docs=[]
        for doc in ids:
            path=self.root/'tmp'/f'{doc}.json';path.parent.mkdir(exist_ok=True);path.write_text(doc)
            docs.append({'document_id':doc,'relative_path':path.relative_to(self.root).as_posix(),'sha256':sha(path.read_bytes()),'country_code':getattr(self.service,'countries',{}).get(doc,'KAZ'),'title':doc})
        return docs

    def check_current(self,job):
        if self.method()!=job['method']:raise ValueError('Method changed')

    def prepare_sources(self,job):
        sources=[]
        for doc in job['documents']:
            source=demo_bundle(self.root)['sources'][0]
            source.update(document_id=doc['document_id'],path=doc['relative_path'],sha256=doc['sha256'],country_code=doc['country_code'])
            for s in source['segments']:
                s['id']=doc['document_id']+':'+s['id']
                for key in ('language','english_text','translation_method'):s.pop(key)
            source['segments'][0]['text'] += ' Edition: '+('2020' if doc['document_id']=='doc-1' else '2025')+'.'
            sources.append(source)
        return sources


class OperationTests(unittest.TestCase):
    def setUp(self):
        self.temp=workspace_test_directory();self.root=self.temp.__enter__()
        for folder in ('src/policytracker','config','schemas','prompts','examples/v2'):
            shutil.copytree(ROOT/folder,self.root/folder,ignore=shutil.ignore_patterns('__pycache__'))
        self.provider=OperationProvider();self.path=self.root/'tmp/runs.sqlite3'
        self.runner=OperationRunner(self.root,self.path,self.provider,synthetic=True);self.session=AISession()
    def tearDown(self):
        if self.runner.thread:self.runner.thread.join(30)
        self.temp.__exit__(None,None,None)
    def run_request(self,req):
        job=self.runner.start(self.session,{'operation':req});self.runner.thread.join(40)
        job=self.runner.get(job['id']);self.assertEqual(job['status'],'completed',job.get('error'))
        return self.runner.operation_result(job['id'])
    def test_every_default_task_executes_and_persists_separately(self):
        for task in ('extract','compare','gaps','brief','translate'):
            with self.subTest(task=task):
                out=self.run_request(request(task,['doc-1','doc-2'] if task=='compare' else None))
                self.assertEqual(out['request']['task'],task);self.assertTrue(out['generation']['step_receipts'])
        with ProfileStore(self.root,self.path) as store:
            self.assertEqual(store.db.execute('select count(*) from profiles').fetchone()[0],0)
        restarted=OperationRunner(self.root,self.path,self.provider,synthetic=True)
        self.assertEqual(len(restarted.operations()['runs']),5)
    def test_filters_no_match_and_selected_columns_do_not_broaden(self):
        req=request('extract');req['requested_fields']=['indicators'];req['filters']['hazards']=['drought']
        out=self.run_request(req);self.assertEqual(out['extraction']['records'],[]);self.assertEqual(out['evidence_table'],[])
        self.assertTrue(out['coverage'])
        req['filters']['hazards']=[];out=self.run_request(req)
        self.assertIn('indicators',out['evidence_table'][0]);self.assertNotIn('finance',out['evidence_table'][0])
    def test_translation_stop_resume_reuse_and_no_extraction(self):
        self.provider.on_result=lambda route:self.runner.stop_event.set() if route=='translate' else None
        job=self.runner.start(self.session,{'operation':request('translate')});self.runner.thread.join(30)
        self.assertEqual(self.runner.get(job['id'])['status'],'stopped')
        self.provider.on_result=None;self.runner.resume(self.session,job['id']);self.runner.thread.join(30)
        self.assertEqual(self.runner.get(job['id'])['status'],'completed')
        saved=self.run_request(request('translate'))
        self.assertTrue(any(s.get('translation_notes') for d in saved['sources'] for s in d['segments']))
        self.assertEqual(self.provider.calls.count('translate'),1);self.assertNotIn('extract',self.provider.calls)
    def test_omitted_options_use_defaults_but_empty_and_false_are_not_reinterpreted(self):
        req=request('gaps');del req['requested_fields'];del req['include_analyst_proposals']
        normalized=normalize_request(self.root,req);self.assertTrue(normalized['requested_fields']);self.assertFalse(normalized['include_analyst_proposals'])
        req['requested_fields']=[]
        with self.assertRaisesRegex(ValueError,'Invalid analysis request'):compose_operation(self.root,req,{})
    def test_unknown_citations_disabled_proposals_and_group_leak_are_rejected(self):
        out=self.run_request(request('compare',['doc-1','doc-2']))
        broken=copy.deepcopy(out['output']);broken['rows'][0]['cells'][0]['findings']=broken['rows'][0]['cells'][1]['findings']
        with self.assertRaisesRegex(ValueError,'different comparison group'):
            validate_operation_output(self.root,out['request'],broken,out['extraction'],out['sources'])
        # A citation can exist in the selected scope and still support a different commitment.
        scoped_request=request('extract',['doc-1','doc-2'])
        first,other=out['extraction']['records']
        priority_report={'country_codes':['KAZ'],'source_group_ids':['selected'],
            'availability':'complete_in_declared_scope','headline_findings':[],
            'sections':[{'section_id':key,'state':'not_found_in_scope','findings':[],
                         'gap_note':'Synthetic validation fixture.'}
                        for key in ['scope',*scoped_request['requested_fields'],'limitations']],
            'prioritized_commitments':[{'commitment_id':first['local_id'],'reason':'Synthetic priority',
                                       'evidence_ids':first['evidence_ids']}],
            'followup_questions':[],'limitations':[]}
        validate_operation_output(self.root,scoped_request,priority_report,out['extraction'],out['sources'])
        priority_report['prioritized_commitments'][0]['evidence_ids']=other['evidence_ids']
        with self.assertRaisesRegex(ValueError,'Priority evidence is unrelated'):
            validate_operation_output(self.root,scoped_request,priority_report,out['extraction'],out['sources'])
        gap=self.run_request(request('gaps'));broken=copy.deepcopy(gap['output']);f=copy.deepcopy(broken['rows'][0]['source_stated_action']);f['kind']='analyst_suggestion';broken['rows'][0]['proposed_indicator']=f
        with self.assertRaisesRegex(ValueError,'disabled'):
            validate_operation_output(self.root,gap['request'],broken,gap['extraction'],gap['sources'])

    def test_all_comparison_modes_and_ineligible_editions(self):
        for mode in ('revision','ndc_nap','countries','custom'):
            with self.subTest(mode=mode):
                self.provider.instruments={'doc-2':'NAP'} if mode=='ndc_nap' else {}
                self.provider.countries={'doc-2':'ALB'} if mode=='countries' else {}
                # Changed metadata fixtures must invalidate earlier test responses.
                prompt=self.root/'prompts/v2/02-triage.md';prompt.write_text(prompt.read_text()+'\nSynthetic '+mode+' fixture.\n')
                req=request('compare',['doc-1','doc-2']);req['comparison_mode']=mode
                out=self.run_request(req);self.assertEqual(len(out['output']['groups']),2)
        self.provider.countries={};self.provider.instruments={};self.provider.relationship='translation'
        prompt=self.root/'prompts/v2/02-triage.md';prompt.write_text(prompt.read_text()+'\nSynthetic equivalent edition.\n')
        self.provider.calls.clear()
        job=self.runner.start(self.session,{'operation':request('compare',['doc-1','doc-2'])});self.runner.thread.join(40)
        self.assertEqual(self.runner.get(job['id'])['status'],'failed')
        self.assertIn('Equivalent translations',self.runner.get(job['id'])['error'])
        self.assertNotIn('translate',self.provider.calls);self.assertNotIn('extract',self.provider.calls)

    def test_saved_analysis_http_archive_uses_original_method_and_attempts(self):
        out=self.run_request(request('extract'))
        prompt=self.root/'prompts/operations/extract.md';before=prompt.read_text();prompt.write_text(before+'\nLater method.\n')
        server=LocalServer(self.root,0,service=AIService(self.root,rpc=FakeRPC()),profiles_path=self.path)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            conn=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=30)
            path='/api/ai/analyses/'+out['id']+'?archive=1'
            conn.request('GET',path);response=conn.getresponse();self.assertEqual(response.status,401);response.read()
            conn.request('GET','/api/ai/session');response=conn.getresponse();cookie=response.getheader('Set-Cookie').split(';')[0];response.read()
            connection = conn.sock
            self.assertIsNotNone(connection)
            for _ in range(3):
                conn.request('GET',path,headers={'Cookie':cookie});response=conn.getresponse();self.assertEqual(response.status,200)
                body=response.read()
                self.assertEqual(len(body), int(response.getheader('Content-Length')))
                self.assertIs(conn.sock, connection)
                saved=json.loads(body)
            archive=saved['generation_archive']
            self.assertEqual(archive['method']['prompts/operations/extract.md'],before)
            self.assertTrue(archive['attempts']);self.assertIn('request',archive['attempts'][0]);self.assertTrue(archive['requests_and_responses'])
            conn.request('GET','/api/ai/translations',headers={'Cookie':cookie});response=conn.getresponse()
            self.assertEqual(json.loads(response.read())['versions'],[],'Synthetic translations must stay outside the real library')
            conn.close()
        finally:
            conn.close()
            server.shutdown();server.server_close();thread.join(5)

    def test_each_field_switch_changes_the_saved_task_structure(self):
        catalog=read_json(self.root/'config/operations/tasks.json')
        for task in catalog['tasks']:
            for option in task['options']:
                with self.subTest(task=task['id'],option=option['id']):
                    req=request(task['id'],['doc-1','doc-2'] if task['id']=='compare' else None)
                    req['requested_fields']=[option['id']];out=self.run_request(req)
                    if task['id']=='compare':self.assertEqual([r['dimension'] for r in out['output']['rows']],[option['id']])
                    elif task['id'] in ('extract','brief'):
                        self.assertEqual([s['section_id'] for s in out['output']['sections']],['scope',option['id'],'limitations'])
                    else:
                        missing=out['output']['rows'][0]['missing_information']
                        self.assertEqual(len(missing),1 if option['id'] in ('finance','indicators') else 0)
                    if task['id']=='extract':
                        selected=option['id'] if option['id']!='risk_context' else 'risk_contexts'
                        self.assertEqual(set(out['evidence_table'][0]) & {'targets','actors','finance','indicators','risk_contexts'},{selected})
                    if task['id']=='brief':self.assertEqual(bool(out['output']['followup_questions']),option['id']=='questions')
        req=request('gaps');req['include_analyst_proposals']=True;out=self.run_request(req)
        self.assertEqual(out['output']['rows'][0]['proposed_support_activity']['kind'],'analyst_suggestion')

    def test_each_filter_and_combination_preserves_scope(self):
        extraction=read_json(self.root/'examples/v2/extraction.json');req=request('extract')
        for field,yes,no in (('domain_ids','climate','water'),('topic_ids','CLM-04','WAT-01'),('hazards','flood','drought'),('risk_functions','early_warning_preparedness','recovery_reconstruction')):
            with self.subTest(field=field):
                one=copy.deepcopy(req);one['filters'][field]=[yes]
                self.assertEqual(len(scoped_evidence(self.root,one,extraction)['records']),1)
                one['filters'][field]=[no];self.assertEqual(scoped_evidence(self.root,one,extraction)['records'],[])
                one['filters'][field]=[yes,no];self.assertEqual(len(scoped_evidence(self.root,one,extraction)['records']),1)
        req['filters'].update(hazards=['flood'],risk_functions=['recovery_reconstruction'])
        self.assertEqual(scoped_evidence(self.root,req,extraction)['records'],[])


if __name__=='__main__':unittest.main()

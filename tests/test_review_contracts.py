"""Regressions for review findings; synthetic input only, no provider calls."""
import copy
import hashlib
import json
import shutil
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from policytracker.engineering import compose_v2, digest, validate_v2
from policytracker.operations import compose_operation, validate_source_groups
from policytracker.translations import save_translation_bundle
from test_method_customization import workspace_test_directory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import method_pack
import topic_csv
import build_methodology


def edit_config(pack, path, edit):
    entry = next(f for f in pack['files'] if f['path'] == path)
    value = json.loads(entry['content']); edit(value)
    entry['content'] = json.dumps(value, ensure_ascii=False)


class CustomizationReview(unittest.TestCase):
    def test_direct_edit_cannot_redefine_its_own_execution_constraints(self):
        with workspace_test_directory() as folder:
            for name in ('config','prompts','schemas'):
                shutil.copytree(ROOT/name,folder/name)
            path=folder/'config/operations/tasks.json'
            value=json.loads(path.read_text(encoding='utf-8'))
            value['tasks'][0]['minimum_documents']=0
            path.write_text(json.dumps(value),encoding='utf-8')
            with patch.object(method_pack,'ROOT',folder):
                with self.assertRaisesRegex(ValueError,'execution constraints'):
                    method_pack.validate(method_pack.pack())

    def test_new_option_and_dimension_require_code(self):
        value=method_pack.pack()
        edit_config(value,'config/operations/tasks.json',lambda c:c['tasks'][0]['options'].append({'id':'imaginary','label':'Imaginary','effect':'Does something','default':True}))
        with self.assertRaisesRegex(ValueError,'output options'):method_pack.validate(value)
        value=method_pack.pack()
        edit_config(value,'config/v2/vocabulary.json',lambda c:c.update(extra_facet=['x']))
        edit_config(value,'config/v2/label-guide.json',lambda c:c['dimensions'].append({'id':'extra_facet'}))
        with self.assertRaisesRegex(ValueError,'dimensions'):method_pack.validate(value)

    def test_stale_package_and_blank_id_fail(self):
        value=method_pack.pack();method_pack.check_base(value)
        value['files'][0]['base_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'Stale'):method_pack.check_base(value)
        value=method_pack.pack()
        edit_config(value,'config/v2/taxonomy.json',lambda c:c['topics'][0].update(id=''))
        with self.assertRaisesRegex(ValueError,'IDs'):method_pack.validate(value)

    def test_topic_csv_roundtrip_preserves_unicode_relationships_and_nested_extras(self):
        pack=method_pack.pack()
        entry=next(f for f in pack['files'] if f['path']=='config/v2/taxonomy.json')
        tax=json.loads(entry['content'])
        tax['topics'][0]['definition']='=Çığ, flood and "risk"\nsecond line'
        tax['topics'][1]['definition']="'literal apostrophe"
        tax['topics'][0]['extra_metadata']={'source':'retained'}
        entry['content']=json.dumps(tax)
        csv=topic_csv.export_topics(tax)
        self.assertIn("'=Çığ",csv)
        with self.assertRaisesRegex(ValueError,'Stale topic CSV'):
            topic_csv.import_topics(csv,pack,'test-next','0'*64)
        result=topic_csv.import_topics('\ufeff'+csv,pack,'test-next')
        updated=json.loads(next(f for f in result['files'] if f['path']==entry['path'])['content'])
        self.assertEqual(updated['topics'],tax['topics'])
        for bad,expected in [(csv.replace(tax['topics'][0]['id'],'',1),'required'),
                             (csv.replace(tax['topics'][0]['id'],'RENAMED',1),'stable IDs'),
                             (csv+csv.splitlines()[1]+'\n','')]:
            with self.subTest(expected=expected):
                with self.assertRaises(ValueError):topic_csv.import_topics(bad,pack,'test-next')
        bad=copy.deepcopy(tax);bad['topics'][0]['domain_ids']=['unknown_domain']
        with self.assertRaisesRegex(ValueError,'domain mapping'):
            topic_csv.import_topics(topic_csv.export_topics(bad),pack,'test-next')

    def test_supported_edits_survive_build_and_reach_composer_and_ui(self):
        with workspace_test_directory() as folder:
            for name in ('config','prompts','schemas','scripts','src','docs','design','integrations','examples'):
                shutil.copytree(ROOT/name,folder/name,ignore=shutil.ignore_patterns('__pycache__'))
            shutil.copytree(ROOT/'data/manifests',folder/'data/manifests')
            with patch.object(method_pack,'ROOT',folder):
                package=method_pack.pack()
                next(f for f in package['files'] if f['path']=='prompts/v2/04-extract.md')['content']+='\nSynthetic customization sentinel.\n'
                edit_config(package,'config/v2/taxonomy.json',lambda c:c['topics'].append({'id':'WAT-TEST','name':'Synthetic topic','domain_ids':['water'],'definition':'Synthetic definition','routing_rule':'Synthetic rule'}))
                edit_config(package,'config/v2/label-guide.json',lambda c:c['dimensions'][0]['options'][0].update(definition='Revised test definition'))
                edit_config(package,'config/operations/tasks.json',lambda c:c['tasks'][0]['options'][-1].update(default=True,effect='Include source-stated cadence; preserve missing reasons.'))
                edit_config(package,'config/methodology.json',lambda c:c['views'][0].update(description='Synthetic UI explanation'))
                items=method_pack.validate(package)
                before={name:text.encode('utf-8') for name,text in items.items()}
                draft=folder/'draft.json';draft.write_text(json.dumps(package),encoding='utf-8')
                with patch.object(sys,'argv',['method_pack.py','apply',str(draft)]):method_pack.main()
                self.assertEqual(before,{name:(folder/name).read_bytes() for name in items})
                self.assertEqual(len(list((folder/'data/methods').glob('*/before.json'))),1)
                with self.assertRaisesRegex(ValueError,'Stale'):method_pack.check_base(package)
                packet=compose_v2(folder,'extract',{}, {})
                self.assertIn('Synthetic customization sentinel',packet['instructions'])
                payload=json.loads(packet['input'])
                self.assertIn('WAT-TEST',[t['id'] for t in payload['taxonomy']['topics']])
                self.assertEqual(payload['labeling_guide']['dimensions'][0]['options'][0]['definition'],'Revised test definition')
                catalog=json.loads((folder/'integrations/fixtures/operation-tasks.json').read_text(encoding='utf-8'))
                self.assertTrue(catalog['tasks'][0]['options'][-1]['default'])
                request=json.loads((ROOT/'examples/operations/requests.json').read_text(encoding='utf-8'))[0]
                request['requested_fields']=['indicators']
                operation=compose_operation(folder,request,{'synthetic':True})
                self.assertEqual(json.loads(operation['input'])['task_context']['selected_options'][0]['effect'],'Include source-stated cadence; preserve missing reasons.')
                region=json.loads((folder/'integrations/fixtures/regional-workspace.json').read_text(encoding='utf-8'))
                self.assertEqual(region['features'][0]['description'],'Synthetic UI explanation')
                schema=json.loads((folder/'schemas/operations/analysis-request.schema.json').read_text(encoding='utf-8'))
                self.assertIn('WAT-TEST',schema['properties']['filters']['properties']['topic_ids']['items']['enum'])


class EvidenceReview(unittest.TestCase):
    def setUp(self):
        self.value=json.loads((ROOT/'examples/v2/extraction.json').read_text(encoding='utf-8'))

    def check(self):return validate_v2(ROOT,'extraction',self.value)

    def test_planned_result_is_not_an_observation(self):
        self.value['records'][0]['kind']='result_observation'
        self.value['records'][0]['documentation_status']='result_reported'
        self.assertTrue(any('documentation_status' in error for error in self.check()))

    def test_missing_condition_and_wrong_support_pointer(self):
        record=self.value['records'][0]
        record['targets'][0]['condition_text']=None
        record['field_support'][0]['field_path']='/targets/-1/value'
        self.assertTrue(any('/targets/0/condition_text: unresolved conditional-target detail' in error
                            for error in self.check()))
        self.assertIn('field support references a nonexistent field',self.check())

    def test_wrong_coverage_links_and_orphan_records(self):
        self.value['coverage'][0]['segment_id']='invented'
        self.assertTrue(any('coverage[invented]' in error and 'not evidenced by its segment' in error for error in self.check()))
        self.value['coverage']=[]
        self.assertIn('records missing from coverage ledger',self.check())

    def test_report_citations_and_availability(self):
        report=json.loads((ROOT/'examples/v2/prime-report.json').read_text(encoding='utf-8'))
        self.assertIn('finding cites unknown evidence',validate_v2(ROOT,'report',report,known_evidence_ids=set()))
        self.assertIn('finding cites unknown records',validate_v2(ROOT,'report',report,known_record_ids=set()))
        report['headline_findings']=[];report['availability']='no_documents_supplied'
        self.assertIn('no-document report cannot invent findings',validate_v2(ROOT,'report',report))
        report['sections'][1]['state']='not_found_in_scope'
        self.assertIn('non-found section cannot contain findings',validate_v2(ROOT,'report',report))

    def test_comparison_missing_verified_metadata_has_actionable_error(self):
        request={'task':'compare','comparison_mode':'documents','source_groups':[{'document_ids':['a']},{'document_ids':['b']}]}
        docs=[{'id':i,'verified':True,'country_code':'KAZ','instrument':'NDC'} for i in ('a','b')]
        with self.assertRaisesRegex(ValueError,'edition IDs'):validate_source_groups(request,docs)

    def test_inverted_numeric_range(self):
        target=self.value['records'][0]['targets'][0]
        target['comparator']='range';target['lower']=copy.deepcopy(target['value']);target['upper']=copy.deepcopy(target['value'])
        target['upper'].update(raw_token='2030',decimal='2030')
        target['lower'],target['upper']=target['upper'],target['lower'];target['value']=None
        self.assertIn('inverted target range',self.check())

    def test_english_original_cannot_be_rewritten_as_translation(self):
        with workspace_test_directory() as folder:
            source=folder/'original.txt';source.write_bytes(b'Original English.')
            provenance={'document_id':'synthetic','translation_id':'t1','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'route':'fixture','model':'fixture','effort':'fixture','prompt_hash':'fixture'}
            segments=[{'id':'s1','language':'en','page':1,'text':'Original English.'}]
            translated={'segments':[{'segment_id':'s1','method':'machine_translation','english_text':'Rewritten English.','quality_flags':[]}]}
            with self.assertRaisesRegex(ValueError,'must use identity'):
                save_translation_bundle(folder/'out',source,segments,translated,provenance)


class CompositionReview(unittest.TestCase):
    def test_crlf_sources_equal_actual_instructions_and_packet_hash(self):
        with workspace_test_directory() as folder:
            for name in ('config','prompts','schemas'):shutil.copytree(ROOT/name,folder/name)
            path=folder/'prompts/v2/04-extract.md'
            raw=path.read_bytes().replace(b'\r\n',b'\n').replace(b'\n',b'\r\n');path.write_bytes(raw)
            packet=compose_v2(folder,'extract',{}, {'text':'UNTRUSTED'})
            expected='\n\n'.join((folder/p).read_bytes().decode('utf-8') for p in packet['instruction_paths'])
            self.assertEqual(packet['instructions'],expected)
            self.assertEqual(packet['packet_hash'],digest({k:v for k,v in packet.items() if k!='packet_hash'}))
            self.assertNotIn('UNTRUSTED',packet['instructions'])

    def test_visible_assembly_matches_real_operational_composition(self):
        catalog=build_methodology.build()
        for request in json.loads((ROOT/'examples/operations/requests.json').read_text(encoding='utf-8')):
            if request['task'] == 'translate':
                continue  # Independent translation is assembled directly by the worker.
            packet=compose_operation(ROOT,request,{'synthetic':True})
            assembly=next(a for a in catalog['assemblies'] if a['id']=='operation:'+request['task'])
            self.assertEqual(assembly['instruction_paths'],packet['instruction_paths'])
            self.assertEqual(assembly['instructions_hash'],packet['instructions_hash'])
            self.assertEqual(assembly['component_hashes'],packet['component_hashes'])
            self.assertEqual(packet['packet_hash'],digest({k:v for k,v in packet.items() if k!='packet_hash'}))

    def test_visible_translation_assembly_matches_dispatched_worker_packet(self):
        from policytracker.country_runs import CountryRunner
        with workspace_test_directory() as folder:
            provider = Mock()
            provider.generate_json.return_value = {'text': '{"segments": []}'}
            runner = CountryRunner(ROOT, folder / 'translation.sqlite3', provider, synthetic=True)
            job = {'id': 'synthetic-translation', 'method': runner.method(),
                   'selection': {'route': 'fixture', 'model': 'fixture', 'effort': 'fixture'},
                   'operation': {'task': 'translate', 'instructions': 'Preserve source terminology.'}}
            with patch.object(runner, 'check_current'):
                runner.step(None, job, 'translate:0', 'translate', {}, {'segments': []}, lambda output: None)
            packet = provider.generate_json.call_args.args[2]
            assembly = next(a for a in build_methodology.build()['assemblies'] if a['id'] == 'operation:translate')
            self.assertEqual(assembly['instruction_paths'], packet['instruction_paths'])
            self.assertEqual(assembly['instructions_hash'], packet['instructions_hash'])
            self.assertEqual(assembly['component_hashes'], packet['component_hashes'])
            self.assertNotIn('prompts/operations/00-request-contract.md', packet['instruction_paths'])


if __name__=='__main__':unittest.main()

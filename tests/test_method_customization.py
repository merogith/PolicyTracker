import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
import uuid
import shutil
from contextlib import contextmanager
from pathlib import Path
from policytracker.translations import save_translation_bundle
from policytracker.country_runs import check_translation
from policytracker.engineering import validate_v2
from policytracker.operations import validate_source_groups

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('method_pack',ROOT/'scripts/method_pack.py')
method_pack=importlib.util.module_from_spec(spec);spec.loader.exec_module(method_pack)

@contextmanager
def workspace_test_directory():
    parent=(ROOT/'tmp').resolve();parent.mkdir(exist_ok=True)
    folder=(parent/('translation-test-'+str(uuid.uuid4()))).resolve()
    assert folder.is_relative_to(parent)
    folder.mkdir()
    try:yield folder
    finally:
        assert folder.is_relative_to(parent)
        shutil.rmtree(folder)

class MethodAndTranslationTests(unittest.TestCase):
    def test_advisory_translation_notes_survive_without_clearing_blocking_defects(self):
        with workspace_test_directory() as folder:
            source=folder/'source.txt';source.write_bytes(b'Original English.')
            segments=[{'id':'s1','page':1,'language':'en','text':'Original English.'}]
            row={'segment_id':'s1','source_language':'en','method':'identity','official_parallel_segment_id':None,
                 'english_text':'Original English.','term_decisions':[],
                 'notes':['Declared sample only <untrusted>'],'quality_flags':[]}
            translated={'segments':[row]}
            self.assertEqual(validate_v2(ROOT,'translation',translated),[])
            check_translation(translated,segments)
            provenance={'document_id':'synthetic','translation_id':'t1','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                        'route':'fixture','model':'fixture','effort':'fixture','prompt_hash':'fixture'}
            save_translation_bundle(folder/'accepted',source,segments,translated,provenance)
            saved=json.loads((folder/'accepted/alignment.json').read_text(encoding='utf-8'))
            self.assertEqual(saved[0]['notes'],row['notes'])
            self.assertIn('Declared sample only &lt;untrusted&gt;', (folder/'accepted/bilingual.html').read_text(encoding='utf-8'))
            row['quality_flags']=['Required source text is illegible']
            with self.assertRaisesRegex(ValueError,'Translation needs attention'):
                check_translation(translated,segments)
            with self.assertRaisesRegex(ValueError,'quality flags'):
                save_translation_bundle(folder/'blocked',source,segments,translated,provenance)
            self.assertFalse((folder/'blocked').exists())

    def test_package_accepts_prompt_changes_and_rejects_extra_paths(self):
        p=method_pack.pack();method_pack.validate(p)
        next(f for f in p['files'] if f['path']=='prompts/v2/08-prime-report.md')['content']+='\nKeep all deadlines visible.\n'
        method_pack.validate(p)
        p['files'].append({'path':'../outside.txt','content':'bad'})
        with self.assertRaisesRegex(ValueError,'allowlisted'):method_pack.validate(p)

    def test_added_label_needs_matching_definition(self):
        p=method_pack.pack();vfile=next(f for f in p['files'] if f['path']=='config/v2/vocabulary.json')
        v=json.loads(vfile['content']);v['hazards'].append('test_hazard');vfile['content']=json.dumps(v)
        with self.assertRaisesRegex(ValueError,'definition'):method_pack.validate(p)
        gfile=next(f for f in p['files'] if f['path']=='config/v2/label-guide.json');g=json.loads(gfile['content'])
        next(d for d in g['dimensions'] if d['id']=='hazards')['options'].append({'id':'test_hazard','label':'Test hazard','definition':'Synthetic test category.'})
        gfile['content']=json.dumps(g);method_pack.validate(p)

    def test_rebuild_refreshes_report_codebook_without_rewriting_saved_data(self):
        with workspace_test_directory() as folder:
            for name in ('config','prompts','schemas','scripts','src','examples'):
                shutil.copytree(ROOT/name,folder/name,ignore=shutil.ignore_patterns('__pycache__'))
            for name in ('design/ux-contract.json','integrations/fixtures/report-experience.json'):
                target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(ROOT/name,target)
            manifest=folder/'data/manifests/corpus.json';manifest.parent.mkdir(parents=True)
            manifest.write_text(json.dumps({'documents':[],'countries':[],
                'inventory_date':'2026-01-01','country_code_note':'Synthetic empty inventory.'}),encoding='utf-8')
            saved=folder/'data/local-profiles/archived-profile.json';saved.parent.mkdir(parents=True)
            saved.write_bytes((folder/'integrations/fixtures/report-experience.json').read_bytes())
            source=folder/'data/sources/synthetic/source.txt';source.parent.mkdir(parents=True)
            source.write_bytes(b'Preserved synthetic original.\r\n')

            guide_path=folder/'config/v2/label-guide.json'
            guide=json.loads(guide_path.read_text(encoding='utf-8'))
            definition='A source-stated delivery step; accounting assumptions alone are not implementation.'
            def implementation_definition(codebook):
                dimension=next(d for d in codebook['dimensions'] if d['id']=='detail_kinds')
                return next(o for o in dimension['options'] if o['id']=='implementation_step')
            self.assertNotEqual(implementation_definition(json.loads(saved.read_text(encoding='utf-8'))['validation_codebook'])['definition'],definition)
            implementation_definition(guide)['definition']=definition
            guide_path.write_text(json.dumps(guide,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            preserved={path:path.read_bytes() for name in ('config','prompts','examples','data')
                       for path in (folder/name).rglob('*') if path.is_file()}
            environment={**os.environ,'PYTHONPATH':str(folder/'src')}
            result=subprocess.run([sys.executable,str(folder/'scripts/method_pack.py'),'build'],
                cwd=folder,env=environment,capture_output=True,text=True,timeout=60)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)

            knowledge=json.loads((folder/'integrations/fixtures/knowledge.json').read_text(encoding='utf-8'))
            fixture=json.loads((folder/'integrations/fixtures/report-experience.json').read_text(encoding='utf-8'))
            self.assertEqual(implementation_definition(knowledge)['definition'],definition)
            self.assertEqual(fixture['validation_codebook']['dimensions'],guide['dimensions'])
            self.assertEqual(fixture['validation_codebook']['guide_version'],guide['version'])
            self.assertEqual(preserved,{path:path.read_bytes() for path in preserved})
            checked=subprocess.run([sys.executable,str(folder/'scripts/check_report_experience.py')],
                cwd=folder,env=environment,capture_output=True,text=True,timeout=60)
            self.assertEqual(checked.returncode,0,checked.stdout+checked.stderr)

    def test_translation_preserves_copies_and_rejects_incomplete_and_overwrite(self):
        temporary_parent=ROOT/'tmp';temporary_parent.mkdir(exist_ok=True)
        with workspace_test_directory() as folder:
            root=Path(folder).resolve()
            assert root.is_relative_to(temporary_parent.resolve())
            source=root/'source.txt';source.write_text('Оригинал',encoding='utf-8')
            segments=[{'id':'a','page':1,'language':'ru','text':'Оригинал'}]
            translated={'segments':[{'segment_id':'a','method':'machine_translation','english_text':'Original','official_parallel_segment_id':None,'term_decisions':[],'quality_flags':[]}]}
            provenance={'document_id':'synthetic','translation_id':'t1','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'route':'fixture','model':'fixture','effort':'fixture','prompt_hash':'fixture'}
            result=save_translation_bundle(root/'v1',source,segments,translated,provenance)
            self.assertEqual((root/'v1/source-original.txt').read_bytes(),source.read_bytes())
            rows=json.loads((root/'v1/alignment.json').read_text(encoding='utf-8'))
            self.assertEqual(rows[0]['original_text'],'Оригинал');self.assertEqual(rows[0]['english_text'],'Original')
            self.assertEqual(len(result['files']),5)
            with self.assertRaises(FileExistsError):save_translation_bundle(root/'v1',source,segments,translated,provenance)
            with self.assertRaisesRegex(ValueError,'coverage'):save_translation_bundle(root/'v2',source,segments,{'segments':[]},provenance)
            translated['segments'][0]['method']='identity'
            with self.assertRaisesRegex(ValueError,'Identity'):save_translation_bundle(root/'v2',source,segments,translated,provenance)
            translated['segments'][0]['method']='official_parallel';translated['segments'][0]['official_parallel_segment_id']='invented'
            with self.assertRaisesRegex(ValueError,'verified'):save_translation_bundle(root/'v2',source,segments,translated,provenance)

    def test_comparison_blocks_equivalent_translations_and_reversed_editions(self):
        docs=[{'id':'a','verified':True,'country_code':'KAZ','edition_id':'first','instrument':'NDC','edition_order':1}, {'id':'b','verified':True,'country_code':'KAZ','edition_id':'second','instrument':'NDC','edition_order':2}]
        request={'task':'compare','comparison_mode':'revision','source_groups':[{'document_ids':['a']},{'document_ids':['b']}]}
        validate_source_groups(request,docs)
        docs[1]['edition_id']='first'
        with self.assertRaisesRegex(ValueError,'Equivalent'):validate_source_groups(request,docs)
        docs[1]['edition_id']='second';docs[1]['edition_order']=0
        with self.assertRaisesRegex(ValueError,'reversed'):validate_source_groups(request,docs)
        docs[1]['edition_order']=2;docs[1]['verified']=False
        with self.assertRaisesRegex(ValueError,'verified'):validate_source_groups(request,docs)

if __name__=='__main__':unittest.main()

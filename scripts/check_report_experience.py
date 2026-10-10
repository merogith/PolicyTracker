"""Read-only alignment checks for presentation fixtures and source configuration."""
import json
from pathlib import Path
from jsonschema import Draft202012Validator
from build_report_design_examples import build

ROOT=Path(__file__).resolve().parents[1]
def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def main():
    fixture=read('integrations/fixtures/report-experience.json')
    assert fixture==build(),'Stale presentation fixtures: rebuild report design examples'
    for name in ('extraction','report'):
        Draft202012Validator(read(f'schemas/v2/{name}.schema.json')).validate(fixture[name])
    tax=read('config/v2/taxonomy.json');vocab=read('config/v2/vocabulary.json');guide=read('config/v2/label-guide.json')
    for d in guide['dimensions']:assert [o['id'] for o in d['options']]==vocab[d['id']]
    assert fixture['validation_codebook']['topics']==tax['topics']
    assert len({d['id'] for d in tax['domains']})==len(tax['domains'])
    assert len({t['id'] for t in tax['topics']})==len(tax['topics'])
    ids={r['local_id'] for r in fixture['extraction']['records']}
    ev={e['local_id']:e for e in fixture['extraction']['evidence']}
    segments={s['id']:s for d in fixture['sources'] for s in d['segments']}
    for e in ev.values():assert e['quote_original'] in segments[e['segment_id']]['text']
    for r in fixture['extraction']['records']:
        assert set(r['evidence_ids'])<=ev.keys()
        targets={t['local_id'] for t in r['targets']}
        for kind in ('actors','finance','indicators','risk_contexts','details'):
            for detail in r[kind]:
                assert set(detail['target_ids'])<=targets
                assert set(detail['evidence_ids'])<=ev.keys()
    for f in fixture['report']['headline_findings']+fixture['report']['followup_questions']:
        assert set(f['citations']['record_ids'])<=ids and set(f['citations']['evidence_ids'])<=ev.keys()
    assert set(read('design/ux-contract.json')['exploration_lenses'])==set(read('config/methodology.json')['presentation']['perspectives'])
    Draft202012Validator.check_schema(read('schemas/presentation-view.schema.json'))
    print('Verified 12 isolated fixture records, extraction/report schemas, exact quotes, target links, archived label alignment, four perspectives and presentation-state schema. No inference or country import.')
if __name__=='__main__':main()

"""Export/validate/apply an editable local method package. Never runs inference."""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import uuid
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CONFIGS=['config/v2/taxonomy.json','config/v2/vocabulary.json','config/v2/label-guide.json','config/v2/pipelines.json','config/operations/tasks.json','config/methodology.json','config/translations.json','config/automation.json']
def paths():return CONFIGS+sorted(p.relative_to(ROOT).as_posix() for folder in ('prompts/v2','prompts/operations') for p in (ROOT/folder).glob('*.md'))
def pack():
    return {'format':'policytracker-method-pack-v1','status':'editable_configuration_not_a_run','files':[{'path':p,'content':(ROOT/p).read_bytes().decode('utf-8'),'base_sha256':hashlib.sha256((ROOT/p).read_bytes()).hexdigest()} for p in paths()]}

def stable_ids(values, label):
    if not values or any(not isinstance(v,str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*',v) for v in values) or len(values)!=len(set(values)):
        raise ValueError(f'{label}: IDs must be nonempty, unique, and use letters, digits, underscores or hyphens')

def nonblank(value, label):
    if not isinstance(value,str) or not value.strip():raise ValueError(f'{label}: nonempty text required')

def validate(value):
    try:
        return _validate(value)
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError(f'Malformed method configuration: {exc}') from exc

def _validate(value):
    if value.get('format')!='policytracker-method-pack-v1':raise ValueError('Unknown method package format')
    entries=value['files'];items={x['path']:x['content'] for x in entries}
    if len(items)!=len(entries) or set(items)!=set(paths()):raise ValueError('Package must contain exactly the allowlisted method files; no extra paths or omissions')
    if any(not isinstance(s,str) or not s.strip() for s in items.values()):raise ValueError('Blank or non-text file')
    cfg={p:json.loads(items[p]) for p in CONFIGS}
    protocol=json.loads((ROOT/'schemas/method-protocol.json').read_text(encoding='utf-8'))
    for p,config in cfg.items():nonblank(config.get('version'),p+' version')
    taxonomy=cfg[CONFIGS[0]];vocab=cfg[CONFIGS[1]];guide=cfg[CONFIGS[2]];pipeline=cfg[CONFIGS[3]];tasks=cfg[CONFIGS[4]]
    domains=[d['id'] for d in taxonomy['domains']];topic_ids=[t['id'] for t in taxonomy['topics']]
    stable_ids(domains,'Domain');stable_ids(topic_ids,'Topic')
    for d in taxonomy['domains']:
        nonblank(d['name'],'Domain name')
        nonblank(guide['domain_definitions'].get(d['id']),'Domain definition')
    if len(domains)!=len(set(domains)) or len(topic_ids)!=len(set(topic_ids)):raise ValueError('Duplicate domain/topic IDs')
    if set(domains)!=set(guide['domain_definitions']):raise ValueError('Every domain needs a guide definition')
    for topic in taxonomy['topics']:
        if 'domains' in topic:raise ValueError('Use domain_ids only; domain names are derived from the domain table')
        nonblank(topic['name'],'Topic name');stable_ids(topic['domain_ids'],'Topic domains')
        if not topic['domain_ids'] or not set(topic['domain_ids'])<=set(domains) or not topic['definition'].strip() or not topic['routing_rule'].strip():raise ValueError('Invalid topic definition or domain mapping')
    dims={d['id']:d for d in guide['dimensions']}
    if set(dims)!=set(protocol['label_dimensions']):raise ValueError('New label dimensions require schema and application implementation')
    if len(dims)!=len(guide['dimensions']) or set(dims)!={k for k,v in vocab.items() if isinstance(v,list)}:raise ValueError('Vocabulary and guide dimensions differ')
    for key,d in dims.items():
        stable_ids(vocab[key],key)
        if key in protocol['fixed_label_values'] and set(vocab[key]) != set(protocol['fixed_label_values'][key]):
            raise ValueError(f'{key}: changing values with application semantics requires code and tests; edit definitions or descriptive facets instead')
        for field in ('label','question','rule'):nonblank(d[field],key+' '+field)
        for o in d['options']:nonblank(o['label'],key+' label')
        if not vocab[key] or len(vocab[key])!=len(set(vocab[key])) or [o['id'] for o in d['options']]!=vocab[key] or any(not o['definition'].strip() for o in d['options']):raise ValueError(f'Missing/duplicate label or definition: {key}')
    # Task/pipeline operation shapes are protocol, not editable labels. Preserve
    # supported IDs; adding a new operation or stage requires implementation.
    if set(pipeline['routes'])!=set(protocol['routes']):raise ValueError('New route types require implementation')
    if pipeline['stages']!=protocol['stages']:raise ValueError('Changing executable stages requires implementation')
    for key in ('shared_contract','labeling_contract'):
        if pipeline[key] not in items or not pipeline[key].startswith('prompts/'):raise ValueError('Unknown shared prompt')
    for route,spec in pipeline['routes'].items():
        if 'prompts/v2/'+spec['prompt'] not in items or spec['schema']!=protocol['routes'][route]:raise ValueError('Route must use an existing prompt and supported schema')
    if set(pipeline['features'])!=set(protocol['features']):raise ValueError('New features require implementation')
    for key,feature in pipeline['features'].items():
        if any(feature[k]!=v for k,v in protocol['features'][key].items()):raise ValueError('Feature routing/history/source policy requires implementation')
        if feature['required_sections']:stable_ids(feature['required_sections'],'Report sections')
    if [t['id'] for t in tasks['tasks']]!=list(protocol['tasks']):raise ValueError('Changing supported task types requires implementation')
    if tasks['shared_required_fields']!=protocol['shared_required_fields']:raise ValueError('Shared output fields require implementation')
    for task in tasks['tasks']:
        baseline=protocol['tasks'][task['id']]
        if any(task[k]!=baseline[k] for k in ('route','artifact','pipeline','minimum_documents','allows_filters','requires_question')):raise ValueError('Task execution constraints are fixed; edit labels, option effects/defaults and prompts')
        if task['supplement'] not in items or not task['supplement'].startswith('prompts/operations/'):raise ValueError('Unknown task prompt')
        for field in ('label','description','requirements'):nonblank(task[field],'Task '+field)
        ids=[o['id'] for o in task['options']]
        if set(ids)!=set(baseline['option_ids']):raise ValueError('New or removed output options require implementation')
        for o in task['options']:
            nonblank(o['label'],'Option label')
            if type(o['default']) is not bool:raise ValueError('Option default must be a boolean')
        if len(ids)!=len(set(ids)) or any(not o['effect'].strip() for o in task['options']):raise ValueError('Options require distinct IDs and explicit effects')
    if [m['id'] for m in tasks['comparison_modes']]!=list(protocol['comparison_modes']):raise ValueError('Comparison modes require implementation')
    for mode in tasks['comparison_modes']:
        if {k:v for k,v in mode.items() if k not in ('label','help','labels')}!=protocol['comparison_modes'][mode['id']]:raise ValueError('Comparison grouping rules require implementation')
    method=cfg['config/methodology.json']
    if [v['id'] for v in method['views']]!=['brief','commitments']:raise ValueError('Core view identities are fixed')
    if {s for v in method['views'] for s in v['schema_sections']}!=set(pipeline['features']['prime']['required_sections']):raise ValueError('Every required report section must map to a core view')
    if [stage for step in method['steps'] for stage in step['pipeline_stages']]!=[s['id'] for s in pipeline['stages']]:raise ValueError('Method explanation must cover the executable stage sequence')
    for part in ('views','utilities','steps'):
        if any(r not in pipeline['routes'] for item in method[part] for r in item['routes']):raise ValueError('Unknown route in methodology')
    if any(cfg['config/translations.json'][k]!=v for k,v in protocol['translation_invariants'].items()):raise ValueError('Translation writer format/preservation changes require implementation')
    from policytracker.settings import validate_settings
    validate_settings(cfg['config/automation.json'], topic_ids)
    return items

def check_base(value):
    for entry in value['files']:
        expected=entry.get('base_sha256')
        if not expected or hashlib.sha256((ROOT/entry['path']).read_bytes()).hexdigest()!=expected:
            raise ValueError(f"Stale or unversioned package: {entry['path']}. Export a fresh package and merge your changes.")

def main():
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['export','validate','apply','build']);ap.add_argument('file',nargs='?');args=ap.parse_args()
    if args.command=='export':
        target=Path(args.file or ROOT/'integrations/fixtures/method-pack.json');target.write_text(json.dumps(pack(),ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(f'Exported editable method package: {target}');return
    if args.command in ('validate','apply'):
        value=json.loads(Path(args.file).read_text(encoding='utf-8'));items=validate(value)
        if args.command=='validate':print('Method package passes structural checks. Semantic changes still need evaluation.');return
        check_base(value)
        digest=hashlib.sha256(json.dumps(items,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        archive=ROOT/'data/methods'/(digest+'-'+uuid.uuid4().hex)
        archive.mkdir(parents=True,exist_ok=False)
        (archive/'method-pack.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        originals={p:(ROOT/p).read_bytes() for p in items}
        (archive/'before.json').write_text(json.dumps(pack(),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        try:
            for p,s in items.items():(ROOT/p).write_bytes(s.encode('utf-8'))
            rebuild()
        except Exception:
            for p,raw in originals.items():(ROOT/p).write_bytes(raw)
            rebuild()
            raise
        print('Applied local method files and rebuilt derived contracts. Historical reports were not modified.');return
    validate(pack());rebuild()

def rebuild():
    for script in ['build_v2_contracts.py','build_workspace_design.py','build_knowledge.py','build_report_design_examples.py','build_methodology.py','build_integration_contracts.py']:
        subprocess.run([sys.executable,str(ROOT/'scripts'/script)],cwd=ROOT,check=True)
    (ROOT/'integrations/fixtures/method-pack.json').write_text(json.dumps(pack(),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()

"""Spreadsheet editing for topics only. JSON stays authoritative; import makes a draft pack."""
import argparse
import copy
import csv
import io
import json
from pathlib import Path

import method_pack

COLUMNS = ['id', 'name', 'domain_ids', 'definition', 'routing_rule']


def protect_cell(value):
    # Reversible text escape for spreadsheet formula prefixes, including leading spaces.
    return "'" + value if value.startswith("'") or value.lstrip().startswith(('=', '+', '-', '@')) else value


def unprotect_cell(value):
    return value[1:] if value.startswith("'") and protect_cell(value[1:]) == value else value


def export_topics(taxonomy):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=COLUMNS, lineterminator='\n')
    writer.writeheader()
    for topic in taxonomy['topics']:
        row = {**{k: topic[k] for k in COLUMNS}, 'domain_ids': '|'.join(topic['domain_ids'])}
        writer.writerow({k: protect_cell(v) for k,v in row.items()})
    return stream.getvalue()


def import_topics(text, package, version, expected_taxonomy_hash=None):
    """Replace the complete topic table; prohibit silent deletions/renames and lost fields."""
    result = copy.deepcopy(package)
    entry = next(f for f in result['files'] if f['path'] == 'config/v2/taxonomy.json')
    if expected_taxonomy_hash is not None and expected_taxonomy_hash != entry['base_sha256']:
        raise ValueError('Stale topic CSV: taxonomy changed since export; export again and merge edits')
    taxonomy = json.loads(entry['content'])
    if not version.strip() or version == taxonomy['version']:
        raise ValueError('Choose a new taxonomy version')
    reader = csv.DictReader(io.StringIO(text.lstrip('\ufeff'), newline=''))
    if reader.fieldnames != COLUMNS:
        raise ValueError('CSV headers must be: ' + ','.join(COLUMNS))
    rows = list(reader)
    if not rows or any(set(row) != set(COLUMNS) or any(not isinstance(v,str) or not v.strip() for v in row.values()) for row in rows):
        raise ValueError('Every CSV cell is required; missing values are not zero, NA or empty relationships')
    original = {t['id']: t for t in taxonomy['topics']}
    rows = [{k: unprotect_cell(v) for k,v in row.items()} for row in rows]
    if not set(original) <= {row['id'] for row in rows}:
        raise ValueError('CSV cannot delete or rename stable IDs; use an explicit JSON migration')
    topics = []
    for row in rows:
        # Preserve future JSON-only fields, which are deliberately outside this table.
        topic = {**original.get(row['id'], {}), **row}
        topic['domain_ids'] = row['domain_ids'].split('|')
        topics.append(topic)
    taxonomy['topics'] = topics
    taxonomy['version'] = version
    entry['content'] = json.dumps(taxonomy, ensure_ascii=False, indent=2) + '\n'
    method_pack.validate(result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    export = sub.add_parser('export'); export.add_argument('file', type=Path)
    load = sub.add_parser('import'); load.add_argument('file', type=Path)
    load.add_argument('--output', type=Path, required=True); load.add_argument('--version', required=True)
    args = parser.parse_args()
    package = method_pack.pack()
    metadata_path = args.file.with_suffix(args.file.suffix+'.meta.json')
    if args.command == 'export':
        entry = next(f for f in package['files'] if f['path'] == 'config/v2/taxonomy.json')
        # A BOM helps spreadsheet apps detect UTF-8; IDs are text, never numbers.
        with args.file.open('w', encoding='utf-8-sig', newline='') as stream:
            stream.write(export_topics(json.loads(entry['content'])))
        metadata_path.write_text(json.dumps({'format':'policytracker-topic-csv-v1','taxonomy_sha256':entry['base_sha256']},indent=2)+'\n',encoding='utf-8')
        print('Exported topic table and .csv.meta.json fingerprint. Keep both; neither is an active configuration.')
    else:
        metadata=json.loads(metadata_path.read_text(encoding='utf-8'))
        if metadata.get('format')!='policytracker-topic-csv-v1' or not metadata.get('taxonomy_sha256'):
            raise ValueError('Missing topic CSV fingerprint; export a fresh table')
        result = import_topics(args.file.read_text(encoding='utf-8-sig'), package, args.version, metadata['taxonomy_sha256'])
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        print('Wrote validated draft method package. Apply it with method_pack.py; no source was changed.')


if __name__ == '__main__':
    main()

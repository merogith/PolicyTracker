"""Regressions for observed blocking notes, fragmented repairs and lost ranges."""
import copy
import json
import sys
import unittest
from unittest.mock import patch
from pathlib import Path

from policytracker.engineering import (compact_json_text, compact_packet, compose_v2, extraction_errors,
                                      normalize_extraction_evidence,
                                      read_json, repair_feedback, record_attribution_errors,
                                      schema_allows_absence_marker)
from policytracker.operations import evidence_table
from policytracker.profiles import demo_bundle, validate_bundle, register_csv, encoded
from policytracker.country_runs import (synthesis_evidence, extraction_batches, namespace_extraction,
                                       extraction_source_data, EXTRACTION_REPAIR_RESERVE_BYTES, MAX_REQUEST_BYTES)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_v2_contracts import build as build_contracts


class ExtractionAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.bundle = demo_bundle(ROOT)
        self.output = self.bundle['extraction']
        self.segments = {s['id']: s['text'] for d in self.bundle['sources'] for s in d['segments']}
        self.schema = build_contracts()[1]['extraction']

    def errors(self, output=None, schema=None):
        return extraction_errors(ROOT, output or self.output, 'KAZ', source_segments=self.segments,
                                 owned_segment_ids=list(self.segments), schema=schema or self.schema)

    def test_repeated_policy_occurrences_keep_original_evidence_and_coverage(self):
        repeated = namespace_extraction(self.output, 'repeat:')
        for row in repeated['evidence']:
            row['segment_id'] = 'repeat:' + row['segment_id']
        for row in repeated['coverage']:
            row['segment_id'] = 'repeat:' + row['segment_id']
        self.segments.update({'repeat:' + key: text for key, text in list(self.segments.items())})
        for key in self.output:
            self.output[key].extend(repeated[key])
        self.assertEqual(self.errors(), [])
        table = evidence_table({'requested_fields': ['targets']}, self.output)
        self.assertEqual(len(table), 2)
        self.assertEqual(len(self.output['coverage']), len(self.segments))
        self.assertEqual(self.output['evidence'][1]['quote_original'], repeated['evidence'][1]['quote_original'])
        # A model cannot hide the second occurrence in an unsupported skip state.
        for disposition in ('duplicate', 'relevant_no_new_records', 'excluded'):
            with self.subTest(disposition=disposition):
                self.output['coverage'][-1]['disposition'] = disposition
                self.assertTrue(any('disposition' in error and 'not one of' in error for error in self.errors()))

    def test_notes_survive_acceptance_synthesis_projection_and_csv(self):
        self.output['notes'] = ['Sample scope; unselected pages were not reviewed.']
        self.assertEqual(self.errors(), [])
        validate_bundle(ROOT, self.bundle)
        self.assertEqual(synthesis_evidence(self.output)['notes'], self.output['notes'])
        table = evidence_table({'requested_fields': ['targets']}, self.output)
        self.assertEqual(table[0]['extraction_notes'], self.output['notes'])
        self.assertIn(self.output['notes'][0], register_csv({'id':'test', **self.bundle}))

    def test_all_acceptance_defects_reach_one_repair(self):
        self.output['issues'] = ['Required table unreadable']
        self.output['records'][0]['geography']['country_codes'] = []
        self.output['evidence'][0]['quote_original'] = 'Invented text'
        errors = '; '.join(self.errors())
        for expected in ['Required table unreadable', 'geography.country_codes', 'quote must resolve']:
            self.assertIn(expected, errors)
        with self.assertRaises(ValueError) as failure:
            validate_bundle(ROOT, self.bundle)
        self.assertIn('Required table unreadable', str(failure.exception))
        self.assertIn('geography.country_codes', str(failure.exception))

    def test_unreadable_is_not_an_advisory_note(self):
        self.output['coverage'][0].update(disposition='unreadable', record_ids=[])
        self.assertIn('unresolved unreadable segment', '; '.join(self.errors()))

    def test_nonnational_evidence_retains_affected_countries_separately_from_reporter(self):
        # Reproduce regional-center/global-call shapes with the synthetic evidence
        # fixture. These structural checks do not establish factual entailment.
        for kind, countries in [('implementation_observation', ['KAZ', 'KGZ', 'AFG']),
                                ('proposal', []), ('context', [])]:
            with self.subTest(kind=kind, countries=countries):
                output = copy.deepcopy(self.output)
                record = output['records'][0]
                record['kind'] = kind
                record['geography'].update(scope='multi_country', country_codes=countries)
                before = copy.deepcopy(output)
                self.assertEqual(record_attribution_errors(record, 'KAZ'), [])
                self.assertEqual(self.errors(output), [])
                self.assertEqual(output, before)
                self.assertEqual(record['geography']['reporting_party'],
                                 self.output['records'][0]['geography']['reporting_party'])

    def test_commitments_and_national_records_keep_strict_country_attribution(self):
        for kind, scope, countries in [
                ('commitment', 'multi_country', []),
                ('commitment', 'regional', ['KAZ', 'KGZ']),
                ('commitment', 'EU', ['FRA']),
                ('unclear', 'multi_country', []),
                ('context', 'national', []),
                ('proposal', 'subnational', ['KGZ']),
                ('context', 'unknown', [])]:
            with self.subTest(kind=kind, scope=scope, countries=countries):
                output = copy.deepcopy(self.output)
                record = output['records'][0]
                record['kind'] = kind
                record['geography'].update(scope=scope, country_codes=countries)
                errors = record_attribution_errors(record, 'KAZ')
                self.assertTrue(errors)
                self.assertTrue(all(error in self.errors(output) for error in errors))
                self.assertIn('national-profile attribution', errors[0])
                # Old coercive errors identify legacy repair receipts for rerun.
                self.assertNotIn('.geography.country_codes: expected [', errors[0])
        self.assertEqual(record_attribution_errors(self.output['records'][0], 'KAZ'), [])

    def test_nonnational_attribution_does_not_clear_other_acceptance_failures(self):
        record = self.output['records'][0]
        record['kind'] = 'proposal'
        record['geography'].update(scope='multi_country', country_codes=[])
        self.output['issues'] = ['Unresolved source defect']
        record['targets'][0]['value']['decimal'] = '999'
        before = copy.deepcopy(self.output)
        self.assertEqual(record_attribution_errors(record, 'KAZ'), [])
        errors = '; '.join(self.errors())
        self.assertIn('Unresolved source defect', errors)
        self.assertIn('numeric value differs from source token', errors)
        self.assertEqual(self.output, before)

    def test_populated_missing_field_error_identifies_record_and_path(self):
        record = self.output['records'][0]
        record['missing_fields'][0].update(field_path='/label_en', reason='not_stated')
        errors = '; '.join(self.errors())
        self.assertIn(f"records[{record['local_id']}]/label_en: not_stated cannot qualify a populated value", errors)

    def conditional_without_stated_details(self):
        output = copy.deepcopy(self.output)
        quote = 'Historical benchmark: install 20 flood early-warning systems by 2030 (conditional).'
        self.segments['s-1'] = quote
        next(e for e in output['evidence'] if e['local_id'] == 'e-1')['quote_original'] = quote
        record = output['records'][0]
        record.update(kind='context', label_en='Historical conditional benchmark', description_en=quote)
        record['targets'][0].update(condition_text=None, unit_raw='systems')
        record['field_support'] = [row for row in record['field_support']
                                   if row['field_path'] != '/targets/0/condition_text']
        record['missing_fields'].append({'field_path':'/targets/0/condition_text', 'reason':'not_stated',
                                        'detail':'The benchmark is labelled conditional; its specific condition is not supplied.'})
        return output

    def test_missing_reason_accepts_schema_declared_absence_enums(self):
        # Structural regression: the enum encodes absence instead of a nullable
        # value. Source entailment is still a separate evidence-quality question.
        cases = [('/targets/0/total_or_additional', 'not_stated'),
                 ('/geography/scope', 'unknown'), ('/kind', 'unclear'),
                 ('/actors/0/role', 'unspecified'), ('/labels/objectives/0', 'unspecified')]
        for pointer, value in cases:
            with self.subTest(pointer=pointer, value=value):
                output = copy.deepcopy(self.output)
                record = output['records'][0]
                node = record
                keys = pointer[1:].split('/')
                for key in keys[:-1]: node = node[int(key)] if isinstance(node, list) else node[key]
                node[int(keys[-1]) if isinstance(node, list) else keys[-1]] = value
                record['missing_fields'].append({'field_path':pointer, 'reason':'not_stated',
                                                'detail':'The selected evidence does not establish this attribute.'})
                before = copy.deepcopy(output)
                self.assertEqual(self.errors(output), [])
                self.assertEqual(output, before)

    def test_missing_reason_still_blocks_meaningful_or_freeform_values(self):
        for pointer, value in [('/targets/0/total_or_additional', 'total'),
                               ('/targets/0/total_or_additional', 'additional'),
                               ('/label_en', 'not_stated'), ('/description_en', 'unknown')]:
            with self.subTest(pointer=pointer, value=value):
                output = copy.deepcopy(self.output)
                record = output['records'][0]
                if pointer.startswith('/targets/'):
                    record['targets'][0]['total_or_additional'] = value
                else: record[pointer[1:]] = value
                record['missing_fields'].append({'field_path':pointer, 'reason':'not_stated', 'detail':None})
                self.assertIn('not_stated cannot qualify a populated value', '; '.join(self.errors(output)))
        record = self.output['records'][0]
        for pointer in ('/geography', '/labels/objectives', '/targets/0/value/decimal'):
            record['missing_fields'] = [{'field_path':pointer, 'reason':'not_stated', 'detail':None}]
            self.assertIn('not_stated cannot qualify a populated value', '; '.join(self.errors()))

    def test_absence_marker_needs_the_actual_archived_schema_enum(self):
        record = self.output['records'][0]
        record['missing_fields'].append({'field_path':'/targets/0/total_or_additional', 'reason':'not_stated', 'detail':None})
        freeform = copy.deepcopy(self.schema)
        freeform['properties']['records']['items']['properties']['targets']['items']['properties']['total_or_additional'] = {'type':'string'}
        self.assertEqual(self.errors(), [])
        self.assertIn('not_stated cannot qualify a populated value', '; '.join(self.errors(schema=freeform)))
        nested = {'properties':{'items':{'type':'array','items':{'anyOf':[
            {'type':'object','properties':{'state':{'enum':['known','unknown']}}}, {'type':'null'}]}}}}
        self.assertTrue(schema_allows_absence_marker(nested, '/items/0/state', 'unknown'))
        for pointer, value in [('/items/0/missing','unknown'), ('/items/0/state','known'),
                               ('/items/0/state',False), ('/items/0/state',0), ('/items/0/state',['unknown'])]:
            self.assertFalse(schema_allows_absence_marker(nested, pointer, value))
        self.assertFalse(schema_allows_absence_marker({'$ref':'unsupported'}, '/items/0/state', 'unknown'))

    def test_absence_enum_change_keeps_legacy_label_validation_behavior(self):
        record = self.output['records'][0]
        record['labels'].pop('risk_functions')
        record['targets'][0]['total_or_additional'] = 'total'
        record['missing_fields'].append({'field_path':'/targets/0/total_or_additional', 'reason':'not_stated', 'detail':None})
        old = copy.deepcopy(self.schema)
        labels = old['properties']['records']['items']['properties']['labels']
        labels['properties'].pop('risk_functions'); labels['required'].remove('risk_functions')
        self.assertEqual(self.errors(schema=old), [])

    def test_explicit_conditional_label_can_preserve_documented_unknown_condition(self):
        output = self.conditional_without_stated_details()
        before = copy.deepcopy(output)
        self.assertEqual(self.errors(output), [])
        self.assertEqual(output, before)
        target = output['records'][0]['targets'][0]
        self.assertEqual(target['conditionality'], 'explicitly_conditional')
        self.assertIsNone(target['condition_text'])
        self.assertEqual(target['value']['decimal'], '20')
        self.assertEqual(target['target_period'], '2030')

    def test_unknown_condition_requires_exact_documented_absence(self):
        output = self.conditional_without_stated_details()
        for change in ('missing', 'wrong_path', 'wrong_reason', 'blank_detail', 'null_detail', 'empty_value', 'blank_value'):
            with self.subTest(change=change):
                candidate = copy.deepcopy(output)
                record = candidate['records'][0]
                missing = record['missing_fields'][-1]
                if change == 'missing': record['missing_fields'].pop()
                elif change == 'wrong_path': missing['field_path'] = '/targets/0/scenario'
                elif change == 'wrong_reason': missing['reason'] = 'ambiguous'
                elif change == 'blank_detail': missing['detail'] = '  '
                elif change == 'null_detail': missing['detail'] = None
                elif change == 'empty_value': record['targets'][0]['condition_text'] = ''
                elif change == 'blank_value': record['targets'][0]['condition_text'] = '  '
                errors = '; '.join(self.errors(candidate))
                self.assertIn(f"records[{record['local_id']}].targets[t-1]/targets/0/condition_text", errors)
                self.assertIn('unresolved conditional-target detail', errors)
                self.assertNotIn('conditional target missing condition', errors)

    def test_documented_unknown_condition_keeps_other_acceptance_checks(self):
        output = self.conditional_without_stated_details()
        output['issues'] = ['Required table has an unresolved defect']
        output['records'][0]['targets'][0]['value']['decimal'] = '200'
        before = copy.deepcopy(output)
        errors = '; '.join(self.errors(output))
        self.assertIn('Required table has an unresolved defect', errors)
        self.assertIn('numeric value differs from source token', errors)
        self.assertNotIn('unresolved conditional-target detail', errors)
        self.assertEqual(output, before)

    def test_archived_schema_without_notes_still_validates(self):
        old = read_json(ROOT/'schemas/v2/extraction.schema.json')
        old['properties'].pop('notes'); old['required'].remove('notes')
        self.output.pop('notes')
        self.assertEqual(self.errors(schema=old), [])

    def test_compaction_preserves_quote_whitespace_numbers_and_malformed_response(self):
        raw = ' { "quote" : "line  one\\nline two\\\"", "n" : 1.2300, "range" : [22, 25] } '
        compact = compact_json_text(raw)
        self.assertEqual(json.loads(raw), json.loads(compact))
        self.assertIn('1.2300', compact)
        self.assertIn('line  one', compact)
        self.assertLess(len(compact), len(raw))
        self.assertEqual(compact_json_text('{ incomplete'), '{ incomplete')
        feedback = repair_feedback('all errors', raw)
        self.assertEqual(feedback['errors'], 'all errors')
        self.assertEqual(json.loads(feedback['previous_output']), json.loads(raw))

    def test_structured_repair_keeps_complete_response_without_double_encoding(self):
        output = {'quote':'line  one\nline two', 'raw_token':'123,73', 'decimal':'123.73', 'notes':['Sample only']}
        feedback = repair_feedback('two errors', json.dumps(output, indent=4))
        self.assertEqual(feedback['previous_output'], output)
        packet = {'instructions':'Rules', 'input':json.dumps({'repair':feedback}), 'schema':{}}
        compact = compact_packet(packet)
        self.assertEqual(json.loads(compact['input'])['repair']['previous_output'], output)
        self.assertEqual(packet['instructions'], compact['instructions'])

    def test_batch_headroom_splits_before_dispatch_and_preserves_owned_segments(self):
        source = self.bundle['sources'][0]
        context = {'document_profiles':[{'input_id':source['document_id'], 'metadata_evidence_ids':['s-meta'],
                                         'geography':{'evidence_ids':['s-meta']}}]}
        def packet(root, route, context, data):
            # The wire budget grows with owned material; model calls are never made.
            return {'instructions':'rules', 'input':json.dumps({'padding':'x'*(45000*len(data['segments']))}), 'schema':{}}
        with patch('policytracker.country_runs.compose_v2', side_effect=packet):
            batches = extraction_batches(ROOT, source, context)
        self.assertGreater(len(batches), 1)
        self.assertEqual([s for batch, _ in batches for s in batch], source['segments'])
        for batch, surrounding in batches:
            self.assertIn('s-meta', [s['id'] for s in batch+surrounding])

    def test_english_identity_context_fits_without_repeating_the_reading_layer(self):
        # Real-country failure shape: three metadata segments plus neighbors
        # repeated English source text, exhausting headroom even for one owner.
        text=('Invented policy text with an unchanged English reading layer. '*60)[:2800]
        source={'document_id':'dense', 'segments':[
            {'id':f's-{i}', 'page':i+1, 'text':text, 'english_text':text, 'language':'en',
             'translation_method':'identity', 'term_decisions':[], 'translation_notes':['Invented source qualification']}
            for i in range(8)]}
        original=copy.deepcopy(source)
        context={'document_profiles':[{'input_id':'dense','metadata_evidence_ids':['s-0','s-1','s-2'],
                                      'geography':{'evidence_ids':['s-0']}}]}
        settings={'instructions':'Retain every original quotation and its qualifications.', 'topic_ids':[]}
        def repeated(source,batch,surrounding):
            return {'document_id':source['document_id'],'segments':batch,'context_segments':surrounding}
        with patch('policytracker.country_runs.extraction_source_data',side_effect=repeated):
            with self.assertRaisesRegex(ValueError,'insufficient repair headroom'):
                extraction_batches(ROOT,source,context,settings)
        batches=extraction_batches(ROOT,source,context,settings)
        self.assertEqual([s['id'] for batch,_ in batches for s in batch],[s['id'] for s in source['segments']])
        for batch,surrounding in batches:
            # This is step()'s exact canonicalization and preference assembly.
            request_context=json.loads(encoded({**context,'owned_segment_ids':[s['id'] for s in batch]}))
            request_context['user_preferences']=settings
            data=json.loads(encoded(extraction_source_data(source,batch,surrounding)))
            packet=compact_packet(compose_v2(ROOT,'extract',request_context,data))
            self.assertLessEqual(len(encoded(packet))+EXTRACTION_REPAIR_RESERVE_BYTES,MAX_REQUEST_BYTES)
            for segment in data['segments']+data['context_segments']:
                self.assertNotIn('english_text',segment)
                self.assertEqual(segment['text'],text)
                self.assertEqual(segment['translation_notes'],['Invented source qualification'])
        self.assertEqual(source,original)

    def test_extraction_payload_retains_every_distinct_translation_and_annotation(self):
        source={'document_id':'translated'}
        segment={'id':'s-1','page':1,'text':'Original wording','english_text':'Different English wording',
                 'language':'mul','translation_method':'machine_translation',
                 'term_decisions':['Keep the original institution name'],'translation_notes':['Source remains partial']}
        original=copy.deepcopy(segment)
        data=extraction_source_data(source,[segment],[{**segment,'id':'s-2','translation_method':'identity'}])
        self.assertEqual(data['segments'][0],original)
        self.assertEqual(data['context_segments'][0]['english_text'],'Different English wording')
        self.assertEqual(segment,original)

    def test_extraction_planner_includes_saved_preferences_in_request_budget(self):
        source={'document_id':'one','segments':[{'id':'s-1','text':'Invented source.'}]}
        context={'document_profiles':[{'input_id':'one','metadata_evidence_ids':['s-1'],
                                      'geography':{'evidence_ids':['s-1']}}]}
        self.assertEqual(len(extraction_batches(ROOT,source,context)),1)
        with self.assertRaisesRegex(ValueError,'insufficient repair headroom'):
            extraction_batches(ROOT,source,context,{'instructions':'x'*40000,'topic_ids':[]})

    def test_conditional_projection_range_survives_selected_columns(self):
        # Invented wording reproduces the lost-range shape, not a new country claim.
        quote = 'These conditions would enable a 22 – 25 percent reduction in GDP energy intensity by 2035 relative to 2010.'
        self.segments['s-range'] = quote
        record = self.output['records'][0]
        record.update(kind='projection', label_en='Conditional projected energy-intensity reduction', description_en=quote)
        record['missing_fields'] = [m for m in record['missing_fields'] if m['field_path'] != '/targets/0/baseline_period']
        eid = 'e-range'
        self.output['evidence'].append({'local_id':eid, 'segment_id':'s-range', 'quote_original':quote,
                                        'english_segment_id':None, 'context_evidence_ids':['e-1']})
        record['evidence_ids'].append(eid)
        target = record['targets'][0]
        number = lambda value: {'raw_token':value, 'decimal':value, 'notation':'dot_decimal', 'evidence_id':eid}
        target.update(value=None, lower=number('22'), upper=number('25'), comparator='range',
                      metric_text='GDP energy intensity', unit_raw='percent', baseline_period='2010', target_period='2035',
                      condition_text='Subject to international financing', conditionality='explicitly_conditional',
                      evidence_ids=['e-1', eid])
        self.output['coverage'].append({'segment_id':'s-range','disposition':'extracted','record_ids':[record['local_id']], 'reason':'Conditional projected range'})
        self.assertEqual(self.errors(), [])
        projected = evidence_table({'requested_fields':['targets']}, self.output)[0]
        self.assertEqual(projected['kind'], 'projection')
        self.assertEqual(projected['targets'][0]['upper']['decimal'], '25')
        self.assertEqual(projected['targets'][0]['baseline_period'], '2010')
        self.assertEqual(projected['targets'][0]['conditionality'], 'explicitly_conditional')

    def test_dense_multi_page_sample_splits_even_when_initial_request_fits(self):
        # The observed failure was a small request with a very large response.
        source = {'document_id':'dense', 'segments':[{'id':f's-{i}', 'text':'x'*size}
                  for i, size in enumerate((1923, 2488, 1426))]}
        context = {'document_profiles':[{'input_id':'dense', 'metadata_evidence_ids':['s-0'],
                                         'geography':{'evidence_ids':['s-0']}}]}
        with patch('policytracker.country_runs.compose_v2', return_value={'instructions':'rules', 'input':'{}', 'schema':{}}):
            batches = extraction_batches(ROOT, source, context)
        self.assertEqual([s for batch, _ in batches for s in batch], source['segments'])
        self.assertEqual(len(batches), 3)
        for batch, surrounding in batches:
            self.assertIn('s-0', [s['id'] for s in batch+surrounding])

    def test_context_and_coverage_errors_identify_record_and_missing_evidence(self):
        self.output['records'][0]['evidence_ids'].remove('e-meta')
        self.output['coverage'][0]['segment_id'] = 'wrong-segment'
        errors = '; '.join(self.errors())
        self.assertIn('r-1', errors)
        self.assertIn('e-meta', errors)
        self.assertIn('wrong-segment', errors)

    def test_explicit_label_support_is_closed_with_a_detached_replayable_trace(self):
        evidence=copy.deepcopy(self.output['evidence'][0])
        evidence['local_id']='e-label'
        self.output['evidence'].append(evidence)
        record=self.output['records'][0]
        position=len(record['field_support'])
        record['field_support'].append({'field_path':'/labels/objectives','evidence_ids':['e-label'],
            'basis':'inherited_context','reason':'The supplied national context supports this label.'})
        before=copy.deepcopy(self.output)
        self.assertTrue(any('Record omits supporting evidence' in error for error in self.errors()))
        normalized,additions=normalize_extraction_evidence(self.output,self.schema)
        expected=copy.deepcopy(before)
        expected['records'][0]['evidence_ids'].append('e-label')
        self.assertEqual(normalized,expected)
        self.assertEqual(self.output,before)
        self.assertEqual(additions,[{'record_id':record['local_id'],'evidence_id':'e-label',
            'source_paths':[f'/records/0/field_support/{position}/evidence_ids/0'],
            'destination_path':'/records/0/evidence_ids'}])
        self.assertEqual(self.errors(normalized),[])
        replay=normalize_extraction_evidence(json.loads(json.dumps(before,sort_keys=True)),self.schema)
        self.assertEqual(replay,(normalized,additions))
        self.assertEqual(normalize_extraction_evidence(normalized,self.schema),(normalized,[]))
        normalized['records'][0]['description_en']='Changed caller copy'
        self.assertEqual(self.output,before)

    def test_normalization_preserves_blocking_issues_and_does_not_infer_context_closure(self):
        record=self.output['records'][0]
        record['evidence_ids'].remove('e-meta')
        self.output['issues']=['An unresolved source defect remains.']
        before=copy.deepcopy(self.output)
        normalized,additions=normalize_extraction_evidence(self.output,self.schema)
        self.assertEqual(normalized['issues'],before['issues'])
        self.assertIn('unresolved blocking issue','; '.join(self.errors(normalized)))
        extra=copy.deepcopy(self.output['evidence'][0]);extra['local_id']='context-only'
        self.output['evidence'].append(extra)
        self.output['evidence'][1]['context_evidence_ids'].append('context-only')
        normalized,additions=normalize_extraction_evidence(self.output,self.schema)
        self.assertNotIn('context-only',normalized['records'][0]['evidence_ids'])
        self.assertTrue(any('context-only' in error for error in self.errors(normalized)))

    def test_normalization_rejects_unknown_references_and_malformed_output(self):
        self.output['records'][0]['field_support'][0]['evidence_ids']=['unknown']
        before=copy.deepcopy(self.output)
        with self.assertRaisesRegex(ValueError,'Unknown evidence reference'):
            normalize_extraction_evidence(self.output,self.schema)
        self.assertEqual(self.output,before)
        malformed=copy.deepcopy(self.output);malformed['records'][0]['targets']='not an array'
        with self.assertRaisesRegex(ValueError,'schema'):
            normalize_extraction_evidence(malformed,self.schema)

    def test_normalization_leaves_accepted_output_and_non_link_defects_unchanged(self):
        before=copy.deepcopy(self.output)
        self.assertEqual(normalize_extraction_evidence(before,self.schema),(before,[]))
        before['records'][0]['targets'][0]['value']['decimal']='999'
        normalized,additions=normalize_extraction_evidence(before,self.schema)
        self.assertEqual(normalized,before)
        self.assertEqual(additions,[])
        self.assertIn('numeric value differs from source token',self.errors(normalized))


if __name__ == '__main__':
    unittest.main()

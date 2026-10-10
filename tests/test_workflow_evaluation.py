"""Offline spending guards for the explicitly authorized sample evaluator."""
import importlib.util
import copy
import json
import shutil
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from policytracker.ai_runtime import AIError
from test_method_customization import workspace_test_directory

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("evaluate_workflow", ROOT / "scripts/evaluate_workflow.py")
evaluation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluation)


class EvaluationBudgetTests(unittest.TestCase):
    def evaluator(self, folder):
        instance = evaluation.Evaluation.__new__(evaluation.Evaluation)
        instance.output = folder
        instance.manifest = {"method": {}}
        instance.service = Mock()
        instance.session = object()
        return instance

    def reserve(self, folder, count, step="other", repair=False, failed=False):
        for number in range(1, count + 1):
            call = folder / "calls" / f"{number:02d}"
            evaluation.save_new(call / "dispatch.json", {"call": number, "step": step, "repair": repair})
            if failed:
                evaluation.save_new(call / "validation.json", {"passed": False, "errors": "synthetic invalid output"})
                evaluation.save_new(call / "response.json", {"text": "{}"})

    def test_reserved_calls_count_even_without_provider_responses(self):
        with workspace_test_directory() as folder:
            instance = self.evaluator(folder)
            self.reserve(folder, 14)
            with self.assertRaisesRegex(ValueError, "14-call"):
                instance.call("next", Mock(), Mock())
            instance.service.generate_json.assert_not_called()

    def test_global_and_per_step_repair_limits_survive_resume(self):
        for step, message in (("other", "global reserve"), ("next", "Two repair")):
            with self.subTest(step=step), workspace_test_directory() as folder:
                instance = self.evaluator(folder)
                self.reserve(folder, 3, step=step, repair=True, failed=True)
                if step == "other":
                    call = folder / "calls" / "04"
                    evaluation.save_new(call / "dispatch.json", {"call": 4, "step": "next", "repair": False})
                    evaluation.save_new(call / "validation.json", {"passed": False, "errors": "synthetic invalid output"})
                    evaluation.save_new(call / "response.json", {"text": "{}"})
                with self.assertRaisesRegex(ValueError, message):
                    instance.call("next", Mock(), Mock())
                instance.service.generate_json.assert_not_called()

    def test_provider_failure_remains_counted_and_is_not_automatically_retried(self):
        with workspace_test_directory() as folder:
            instance = self.evaluator(folder)
            instance.service.generate_json.side_effect = AIError("test_failure", "Synthetic failure")
            packet = {"route": "triage", "packet_hash": "synthetic"}
            with patch.object(evaluation, "frozen_method", return_value={}):
                with self.assertRaises(AIError):
                    instance.call("next", lambda repair: packet, Mock())
            self.assertEqual(len(instance.attempts()), 1)
            self.assertTrue((folder / "calls/01/provider-error.json").is_file())
            with self.assertRaisesRegex(ValueError, "no validated result"):
                instance.call("next", Mock(), Mock())
            self.assertEqual(instance.service.generate_json.call_count, 1)

    def test_oversized_repair_and_closed_ledger_never_dispatch(self):
        with workspace_test_directory() as folder:
            instance = self.evaluator(folder)
            self.reserve(folder, 1, step='next', failed=True)
            with patch.object(evaluation, 'frozen_method', return_value={}):
                with self.assertRaisesRegex(ValueError, '180,000'):
                    instance.call('next', lambda repair: {'payload':'x'*180001}, Mock())
            self.assertEqual(len(instance.attempts()), 1)
            instance.service.generate_json.assert_not_called()
            evaluation.save_new(folder/'execution-summary.json', {'status':'closed_not_passed'})
            with self.assertRaisesRegex(ValueError, 'closed'):
                instance.call('next', Mock(), Mock())
            instance.service.generate_json.assert_not_called()

    def test_method_change_prevents_dispatch(self):
        with workspace_test_directory() as folder:
            instance = self.evaluator(folder)
            with patch.object(evaluation, "frozen_method", return_value={"changed": "hash"}):
                with self.assertRaisesRegex(ValueError, "Method changed"):
                    instance.call("next", Mock(), Mock())
            self.assertEqual(instance.attempts(), [])
            instance.service.generate_json.assert_not_called()

    def test_extraction_repair_combines_link_numeric_and_country_errors(self):
        accepted = evaluation.read_json(ROOT/'examples/v2/extraction.json')
        rejected = copy.deepcopy(accepted)
        rejected['issues'] = ['Unresolved required text']
        rejected['records'][0]['geography']['country_codes'] = []
        rejected['records'][0]['evidence_ids'].remove('e-meta')
        rejected['records'][0]['targets'][0]['value']['decimal'] = '999'
        repairs = []
        def compose(repair):
            if repair:
                repairs.append(repair)
            return {'route':'extract', 'packet_hash':'synthetic'}
        def check(output):
            errors = evaluation.extraction_errors(ROOT, output, 'KAZ')
            evaluation.require(not errors, '; '.join(errors))
        with workspace_test_directory() as folder:
            instance = self.evaluator(folder)
            instance.service.generate_json.side_effect = [{'text':json.dumps(o)} for o in (rejected, accepted)]
            with patch.object(evaluation, 'frozen_method', return_value={}):
                result = instance.call('extract', compose, check)
        self.assertEqual(result, accepted)
        self.assertEqual(len(repairs), 1)
        for message in ('numeric value differs', 'e-meta', 'r-1', 'geography.country_codes', 'Unresolved required text'):
            self.assertIn(message, repairs[0]['errors'])

    def test_changed_batch_plan_stops_before_provider_connection(self):
        with workspace_test_directory() as folder:
            instance = self.evaluator(folder)
            instance.documents = [{'segments':[{'text':'x'*2000}, {'text':'y'*2000}]}]
            instance.connect = Mock()
            with self.assertRaisesRegex(ValueError, 'revised bounded plan'):
                instance.run()
            instance.connect.assert_not_called()
            instance.service.generate_json.assert_not_called()

    def documents(self):
        return [{'document_id': doc, 'title': 'Invented source', 'country_code': 'BLR', 'sha256': fingerprint,
                 'path': 'synthetic.json', 'pages': 8 if index == 0 else 25, 'sample_pages': pages,
                 'segments': [{'id': f'{doc}:p{page}:s1', 'page': page, 'text': 'Synthetic English text. ' * 80} for page in pages]}
                for index, (doc, pages, fingerprint) in enumerate(evaluation.SAMPLES)]

    def triage(self, doc):
        segment_id = doc['segments'][0]['id']
        return {'document_profiles': [{'input_id': doc['document_id'], 'title': 'Invented source', 'instrument_type': 'NDC',
                'document_state': 'submitted', 'publication_date': None, 'languages': ['en'],
                'geography': {'country_codes': ['BLR'], 'reporting_party': 'Belarus', 'scope': 'national', 'locations': [], 'evidence_ids': [segment_id]},
                'disposition': 'prime_candidate', 'metadata_evidence_ids': [segment_id], 'notes': ['Synthetic sample'], 'issues': []}], 'relationships': []}

    def translation(self, doc):
        return {'segments': [{'segment_id': s['id'], 'source_language': 'en', 'method': 'identity', 'english_text': s['text'],
                             'official_parallel_segment_id': None, 'term_decisions': [], 'notes': [], 'quality_flags': []} for s in doc['segments']]}

    def archive(self, folder):
        archive = folder / 'prior'
        documents = self.documents()
        paths = set()
        for route in ('triage', 'translate'):
            paths.update(evaluation.compose_v2(ROOT, route, {}, {})['component_hashes'])
        paths.add('prompts/operations/translate.md')
        method = {}
        for path in paths:
            target = archive / 'method' / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / path, target)
            method[path] = evaluation.sha(target.read_bytes())
        evaluation.save_new(archive / 'manifest.json', {'plan_id': evaluation.PLAN_ID, 'selection': evaluation.SELECTION, 'scope': evaluation.SCOPE,
                            'source_hashes': {doc: sha for doc, _, sha in evaluation.SAMPLES}, 'method': method})
        evaluation.save_new(archive / 'source-samples.json', documents)
        evaluation.save_new(archive / 'execution-summary.json', {'status': 'closed_not_passed'})
        for index, doc in enumerate(documents):
            triage = self.triage(doc)
            for offset, route in enumerate(('triage', 'translate')):
                number = 2 * index + offset + 1
                step = f'{index+1}-{route}'
                packet = evaluation.fresh_preparation_packet(ROOT, route, doc, triage if offset else None)
                output = self.translation(doc) if offset else triage
                call = archive / 'calls' / f'{number:02d}'
                evaluation.save_new(call / 'request.json', packet)
                evaluation.save_new(call / 'dispatch.json', {'call': number, 'step': step, 'route': route, 'repair': False,
                                    'selection': evaluation.SELECTION, 'packet_hash': packet['packet_hash'], 'packet_bytes': len(evaluation.encoded(packet))})
                evaluation.save_new(call / 'response.json', {**evaluation.SELECTION, 'actual_model': evaluation.SELECTION['model'],
                                    'confirmed_effort': evaluation.SELECTION['effort'], 'request_id': 'synthetic-' + step, 'text': json.dumps(output)})
                evaluation.save_new(call / 'validation.json', {'passed': True})
                evaluation.save_new(archive / 'outputs' / (step + '.json'), output)
        return archive, documents

    def test_reuse_requires_exact_archived_request_output_and_current_instructions(self):
        with workspace_test_directory() as folder:
            archive, documents = self.archive(folder)
            result = evaluation.verified_reuse(archive, documents)
            self.assertEqual(len(result['receipts']), 4)
            self.assertEqual(result['documents'][0]['segments'][0]['translation_method'], 'identity')
            response_path = archive / 'calls/01/response.json'
            response = evaluation.read_json(response_path)
            response['text'] = '{}'
            response_path.write_text(json.dumps(response), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'saved output differs'):
                evaluation.verified_reuse(archive, documents)
        with workspace_test_directory() as folder:
            archive, documents = self.archive(folder)
            original = evaluation.fresh_preparation_packet
            def changed(root, *args, **kwargs):
                packet = original(root, *args, **kwargs)
                if root == ROOT:
                    packet['instructions'] += '\nDifferent current instructions.'
                return packet
            with patch.object(evaluation, 'fresh_preparation_packet', side_effect=changed):
                with self.assertRaisesRegex(ValueError, 'model-facing preparation is incompatible'):
                    evaluation.verified_reuse(archive, documents)

    def test_reuse_rejects_source_and_archived_method_tampering(self):
        with workspace_test_directory() as folder:
            archive, documents = self.archive(folder)
            documents[0]['segments'][0]['text'] += 'Changed source'
            with self.assertRaisesRegex(ValueError, 'source samples differ'):
                evaluation.verified_reuse(archive, documents)
        with workspace_test_directory() as folder:
            archive, documents = self.archive(folder)
            prompt = archive / 'method/prompts/v2/00-evidence-contract.md'
            prompt.write_bytes(prompt.read_bytes() + b'Changed archived instructions')
            with self.assertRaisesRegex(ValueError, 'archived method was changed'):
                evaluation.verified_reuse(archive, documents)

    def test_reuse_reconstructs_request_even_if_dispatch_hash_is_recomputed(self):
        with workspace_test_directory() as folder:
            archive, documents = self.archive(folder)
            request_path = archive / 'calls/01/request.json'
            request = evaluation.read_json(request_path)
            payload = json.loads(request['input'])
            payload['task_context']['scope'] = 'Tampered source scope'
            request['input'] = json.dumps(payload)
            request['packet_hash'] = evaluation.digest({k: v for k, v in request.items() if k != 'packet_hash'})
            request_path.write_text(json.dumps(request), encoding='utf-8')
            dispatch_path = archive / 'calls/01/dispatch.json'
            dispatch = evaluation.read_json(dispatch_path)
            dispatch.update(packet_hash=request['packet_hash'], packet_bytes=len(evaluation.encoded(request)))
            dispatch_path.write_text(json.dumps(dispatch), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'cannot be reconstructed exactly'):
                evaluation.verified_reuse(archive, documents)

    def test_reuse_allows_metadata_only_changes_but_rejects_provider_selection(self):
        with workspace_test_directory() as folder:
            archive, documents = self.archive(folder)
            current = folder / 'current'
            shutil.copytree(archive / 'method', current)
            path = current / 'config/v2/pipelines.json'
            pipeline = evaluation.read_json(path)
            pipeline['execution_note'] = 'New descriptive metadata, never sent to the model.'
            path.write_text(json.dumps(pipeline), encoding='utf-8')
            with patch.object(evaluation, 'ROOT', current):
                self.assertEqual(len(evaluation.verified_reuse(archive, documents)['receipts']), 4)
            response_path = archive / 'calls/01/response.json'
            response = evaluation.read_json(response_path)
            response['actual_model'] = 'unexpected-model'
            response_path.write_text(json.dumps(response), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'exact provider selection receipt'):
                evaluation.verified_reuse(archive, documents)

    def test_fresh_plan_checks_five_owned_batches_before_connection(self):
        documents = self.documents()
        plan = evaluation.preflight_plan(documents)
        self.assertEqual(plan['baseline_calls'], 11)
        self.assertEqual(plan['extraction_batches'], [2, 3])
        measured = [p for p in plan['packet_measurements'] if 'owned_segment_ids' in p]
        self.assertEqual([s for p in measured for s in p['owned_segment_ids']], [s['id'] for d in documents for s in d['segments']])
        self.assertTrue(all(p['context_segment_ids'] for p in measured))
        documents[1]['segments'].append({'id': 'extra', 'text': 'Unexpected sixth segment'})
        with workspace_test_directory() as folder:
            instance = self.evaluator(folder)
            instance.manifest['plan_id'] = evaluation.PLAN_ID
            instance.documents = documents
            instance.connect = Mock()
            with self.assertRaisesRegex(ValueError, 'revised bounded plan'):
                instance.run()
            instance.connect.assert_not_called()

    def test_closed_ledger_is_refused_before_preparation_or_connection(self):
        with workspace_test_directory() as folder:
            evaluation.save_new(folder / 'execution-summary.json', {'status': 'closed_not_passed'})
            with patch.object(evaluation, 'sources') as sources:
                with self.assertRaisesRegex(ValueError, 'closed'):
                    evaluation.Evaluation(folder)
                sources.assert_not_called()

    def test_country_only_run_uses_both_documents_and_checked_reconciliation(self):
        documents = self.documents()
        with workspace_test_directory() as folder:
            instance = self.evaluator(folder)
            instance.manifest['plan_id'] = evaluation.PLAN_ID
            instance.documents = documents
            instance.connect = Mock()
            called = []
            def call(step, compose, check):
                packet = compose(None)
                payload = json.loads(packet['input'])
                called.append((step, payload))
                if packet['route'] in ('triage', 'translate', 'extract'):
                    source = documents[int(step[0])-1]
                    context = payload['task_context']
                    expected = evaluation.document_context(source, {})
                    self.assertEqual(context['source_group_ids'], expected['source_group_ids'])
                    self.assertEqual(context['country_codes'], expected['country_codes'])
                    self.assertTrue(all(p['input_id'] == source['document_id'] for p in context.get('document_profiles', [])))
                    if packet['route'] == 'translate':
                        self.assertNotIn('prompts/operations/translate.md', packet['instruction_paths'])
                        self.assertIn('glossary', context['user_preferences'])
                if packet['route'] == 'triage':
                    result = self.triage(documents[int(step[0])-1])
                elif packet['route'] == 'translate':
                    result = self.translation(documents[int(step[0])-1])
                elif packet['route'] == 'extract':
                    result = {'evidence': [], 'records': [], 'coverage': [{'segment_id': sid, 'disposition': 'background',
                              'record_ids': [], 'reason': 'Invented test prose'} for sid in payload['task_context']['owned_segment_ids']], 'notes': [], 'issues': []}
                elif packet['route'] == 'reconcile':
                    result = {'groups': [], 'relations': [], 'changes': [], 'issues': []}
                else:
                    result = evaluation.read_json(ROOT / 'examples/v2/prime-report.json')
                    result.update(country_codes=['BLR'], source_group_ids=[d['document_id'] for d in documents],
                                  headline_findings=[], prioritized_commitments=[], followup_questions=[])
                    for section in result['sections']:
                        section.update(state='not_found_in_scope', findings=[], gap_note='Invented test prose')
                check(result)
                return result
            instance.call = call
            instance.run()
            self.assertEqual([step for step, _ in called], evaluation.preflight_plan(documents)['stages'])
            self.assertEqual(len(called), 11)
            overview = called[-1][1]
            self.assertEqual(overview['task_context']['source_group_ids'], [d['document_id'] for d in documents])
            self.assertIn('reconciliation', overview['untrusted_source_data'])


if __name__ == "__main__":
    unittest.main()

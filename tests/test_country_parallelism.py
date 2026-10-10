"""Bounded country work uses fake providers and events; no live model calls."""
import json
import shutil
import threading
import unittest
from contextlib import contextmanager
from pathlib import Path

from policytracker.ai_runtime import AISession, AIError
from policytracker.country_runs import extraction_source_data
from policytracker.engineering import extraction_errors
from policytracker.profiles import demo_bundle, require
from test_country_runs import FixtureProvider, FixtureRunner, ROOT, SELECTION
from test_method_customization import workspace_test_directory


class ParallelProvider(FixtureProvider):
    def __init__(self):
        super().__init__()
        self.entered = [threading.Event() for _ in range(3)]
        self.release = [threading.Event() for _ in range(3)]
        self.failed = set()
        self.group = object()

    @contextmanager
    def country_request_group(self, session, job_id):
        yield self.group

    def generate_json(self, session, selection, packet, *, country_group=None):
        assert country_group is self.group
        number = json.loads(packet['input'])['task_context']['test_batch']
        self.entered[number].set()
        if not self.release[number].wait(15):
            raise AssertionError('The test did not release its synthetic request')
        if number in self.failed:
            raise AIError('test', 'Synthetic failed batch')
        return super().generate_json(session, selection, packet)


class ParallelCountryTests(unittest.TestCase):
    def setUp(self):
        self.temp = workspace_test_directory()
        self.root = self.temp.__enter__()
        for folder in ('src/policytracker', 'config', 'schemas', 'prompts/v2', 'examples/v2'):
            shutil.copytree(ROOT / folder, self.root / folder, ignore=shutil.ignore_patterns('__pycache__'))
        self.provider = ParallelProvider()
        self.runner = FixtureRunner(self.root, self.root / 'parallel.sqlite3', self.provider, synthetic=True)
        self.session = AISession()
        self.job = dict(id='parallel', country='KAZ', status='running', selection=SELECTION,
                        synthetic=True, settings={}, method=self.runner.method(), stage='extract')
        self.runner.active = self.job['id']
        with self.runner.store() as store:
            self.runner.write(store, self.job)
        self.source = demo_bundle(self.root)['sources'][0]
        self.results, self.errors = [], []
        self.thread = None

    def tearDown(self):
        for release in self.provider.release:
            release.set()
        if self.thread:
            self.thread.join(20)
        self.temp.__exit__(None, None, None)

    def start(self, count=3):
        def work(number, item, group):
            def check(output):
                errors = extraction_errors(self.root, output, 'KAZ',
                    source_segments={s['id']: s['text'] for s in self.source['segments']},
                    owned_segment_ids=[s['id'] for s in self.source['segments']])
                require(not errors, '; '.join(errors))
            self.runner.step(self.session, self.job, f'extract:{number}', 'extract',
                dict(country_codes=['KAZ'], source_group_ids=['synthetic'], test_batch=number),
                extraction_source_data(self.source, self.source['segments'], []), check, country_group=group)
            return number
        def run():
            try:
                self.results.extend(self.runner.run_batches(self.session, self.job, list(range(count)), work,
                    'extract', 'Extracting test evidence'))
            except Exception as exc:
                self.errors.append(exc)
        self.thread = threading.Thread(target=run)
        self.thread.start()

    def receipts(self):
        with self.runner.store() as store:
            return [r[0] for r in store.db.execute('SELECT step FROM country_steps WHERE job_id=? ORDER BY step', (self.job['id'],))]

    def join(self):
        self.thread.join(20)
        self.assertFalse(self.thread.is_alive())

    def test_two_overlap_third_waits_and_results_keep_source_order(self):
        self.start()
        self.assertTrue(self.provider.entered[0].wait(10))
        self.assertTrue(self.provider.entered[1].wait(10))
        self.assertFalse(self.provider.entered[2].is_set())
        self.provider.release[1].set()
        self.assertTrue(self.provider.entered[2].wait(10))
        self.provider.release[2].set()
        self.provider.release[0].set()
        self.join()
        self.assertEqual(self.errors, [])
        self.assertEqual(self.results, [0, 1, 2])
        self.assertEqual(self.receipts(), ['extract:0', 'extract:1', 'extract:2'])
        self.assertEqual((self.job['completed'], self.job['total']), (3, 3))

    def test_stop_drains_two_valid_receipts_and_dispatches_no_third(self):
        self.start()
        self.assertTrue(self.provider.entered[0].wait(10))
        self.assertTrue(self.provider.entered[1].wait(10))
        self.runner.stop(self.job['id'])
        self.provider.release[0].set()
        self.assertTrue(self.thread.is_alive())
        self.provider.release[1].set()
        self.join()
        self.assertFalse(self.provider.entered[2].is_set())
        self.assertEqual(self.receipts(), ['extract:0', 'extract:1'])
        self.assertEqual(type(self.errors[0]).__name__, 'Stopped')
        self.assertEqual(self.runner.get(self.job['id'])['status'], 'stopping')

    def test_failure_drains_sibling_without_dispatch_or_publication(self):
        self.provider.failed.add(0)
        self.start()
        self.assertTrue(self.provider.entered[0].wait(10))
        self.assertTrue(self.provider.entered[1].wait(10))
        self.provider.release[0].set()
        self.assertTrue(self.runner.stop_event.wait(10))
        self.assertTrue(self.thread.is_alive())
        self.provider.release[1].set()
        self.join()
        self.assertEqual(str(self.errors[0]), 'Synthetic failed batch')
        self.assertFalse(self.provider.entered[2].is_set())
        self.assertEqual(self.receipts(), ['extract:1'])
        with self.runner.store() as store:
            self.assertIsNone(store.country('KAZ', True)['profile'])


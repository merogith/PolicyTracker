"""Country workflow tests use invented documents and fake providers; no model calls."""
import copy
import http.client
import io
import json
import shutil
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from policytracker.ai_runtime import AIService, AISession, AIError
from policytracker.country_runs import CountryRunner, check_reconciliation, check_translation, synthesis_evidence, merge_synthesis, namespace_extraction
from policytracker.engineering import compose_v2, read_json, validate_v2
from policytracker.profiles import ProfileStore, demo_bundle
from policytracker.local_server import LocalServer
from test_ai_runtime import FakeAPI, FakeRPC, KEY
from test_method_customization import workspace_test_directory

ROOT = Path(__file__).resolve().parents[1]
SELECTION = {"route": "openai_api", "model": "gpt-6-astra", "effort": "high"}


class FixtureProvider:
    def __init__(self):
        self.calls = []
        self.fail = None
        self.on_result = None
        self.bad = False

    def catalog(self, session, route):
        return {"models": [{"id": "gpt-6-astra", "efforts": ["high"]}]}

    def generate_json(self, session, selection, packet):
        self.calls.append(packet["route"])
        if self.fail == packet["route"]:
            raise AIError("test", "Synthetic provider interruption")
        payload = json.loads(packet["input"])
        context, data = payload["task_context"], payload["untrusted_source_data"]
        if packet["route"] == "triage":
            output = {"document_profiles": [{"input_id": "synthetic-document", "title": "Invented NDC", "instrument_type": "NDC",
                "document_state": "submitted", "publication_date": None, "languages": ["ru", "en"],
                "geography": {"country_codes": ["KAZ"], "reporting_party": "Kazakhstan", "scope": "national", "locations": [], "evidence_ids": ["s-meta"]},
                "disposition": "prime_candidate", "metadata_evidence_ids": ["s-meta"], "notes": ["Synthetic preview only"], "issues": []}], "relationships": []}
        elif packet["route"] == "translate":
            output = read_json(ROOT / "examples/v2/translation.json")
            for segment in output["segments"]:
                segment["quality_flags"] = []  # Synthetic scope is marked on the saved profile.
        elif packet["route"] == "extract":
            output = read_json(ROOT / "examples/v2/extraction.json")
        elif packet["route"] == "reconcile":
            output = {"groups": [], "relations": [], "changes": [], "issues": []}
        else:
            output = read_json(ROOT / "examples/v2/prime-report.json")
            # Re-map local fixture IDs to the worker's stable chunk-scoped IDs.
            def visit(value):
                if isinstance(value, list): return [visit(v) for v in value]
                if isinstance(value, dict): return {k: visit(v) for k,v in value.items()}
                return "b0:" + value if isinstance(value, str) and value in {"e-meta", "e-1", "e-2", "r-1"} else value
            output = visit(output)
            output["source_group_ids"] = context["source_group_ids"]
            if self.bad:
                output["headline_findings"][0]["citations"]["evidence_ids"] = ["invented-evidence"]
        if self.on_result:
            self.on_result(packet["route"])
        return {"text": json.dumps(output), "actual_model": selection["model"], "confirmed_effort": selection["effort"],
                "request_id": "synthetic-request", "usage": {"input_tokens": 10, "output_tokens": 10}}


class FixtureRunner(CountryRunner):
    def documents(self, country, ids):
        return [{"document_id": "synthetic-document", "relative_path": "examples/v2/synthetic-input.json",
                 "sha256": demo_bundle(self.root)["sources"][0]["sha256"]}]

    def check_current(self, job):
        if self.method() != job["method"]:
            raise ValueError("The method or worker changed")

    def prepare_sources(self, job):
        sources = demo_bundle(self.root)["sources"]
        for source in sources:
            for segment in source["segments"]:
                for key in ("language", "english_text", "translation_method"):
                    segment.pop(key)
        return sources


class CountryTests(unittest.TestCase):
    def setUp(self):
        self.temp = workspace_test_directory()
        self.root = self.temp.__enter__()
        for folder in ("src/policytracker", "config", "schemas", "prompts/v2", "examples/v2"):
            shutil.copytree(ROOT / folder, self.root / folder, ignore=shutil.ignore_patterns("__pycache__"))
        self.path = self.root / "data/local-profiles/workspace.sqlite3"
        self.provider = FixtureProvider()
        self.runner = FixtureRunner(self.root, self.path, self.provider, synthetic=True)
        self.session = AISession()

    def tearDown(self):
        if self.runner.thread:
            self.runner.thread.join(20)
        self.temp.__exit__(None, None, None)

    def start(self):
        job = self.runner.start(self.session, {"country": "KAZ", "document_ids": ["synthetic-document"], **SELECTION})
        self.runner.thread.join(25)
        self.assertFalse(self.runner.thread.is_alive())
        return self.runner.get(job["id"])

    def test_full_run_saves_shared_views_provenance_and_reuses_valid_steps(self):
        job = self.start()
        self.assertEqual(job["status"], "completed", job.get("error"))
        self.assertEqual(self.provider.calls, ["triage", "translate", "extract", "reconcile", "prime"])
        with ProfileStore(self.root, self.path) as store:
            profile = store.country("KAZ", True)["profile"]
            self.assertEqual(profile["validation"]["generation_method"], "recorded")
            self.assertEqual(profile["extraction"]["records"][0]["local_id"], "b0:r-1")
            self.assertIn("b0:e-1", profile["report"]["headline_findings"][0]["citations"]["evidence_ids"])
            self.assertEqual(profile["generation"]["selection"], SELECTION)
            self.assertEqual(profile["generation"]["step_receipts"][0]["actual_model"], SELECTION["model"])
            self.assertEqual(store.summaries(), [])
            self.assertTrue(profile["sources"][0]["segments"][1]["english_text"])
            self.assertEqual(profile['extraction']['notes'], read_json(ROOT/'examples/v2/extraction.json')['notes'])
        second = self.start()
        self.assertEqual(second["status"], "completed", second.get("error"))
        self.assertEqual(len(self.provider.calls), 5)

    def test_overview_receives_checked_relationship_proposals(self):
        original = self.provider.generate_json
        received = []
        proposal = {"groups": [{"local_group_id": "g-1", "proposed_existing_commitment_id": None,
                    "record_ids": ["b0:r-1"], "variants": [], "reason": "Source statement retained",
                    "unresolved": ["The source does not resolve the funding scenario"]}],
                    "relations": [], "changes": [], "issues": []}
        def respond(session, selection, packet):
            response = original(session, selection, packet)
            if packet["route"] == "reconcile":
                response["text"] = json.dumps(proposal)
            if packet["route"] == "prime":
                received.append(json.loads(packet["input"])["untrusted_source_data"])
            return response
        self.provider.generate_json = respond
        job = self.start()
        self.assertEqual(job["status"], "completed", job.get("error"))
        self.assertEqual(received[0]["reconciliation"], proposal)
        self.assertEqual(received[0]["extraction"]["records"][0]["local_id"], "b0:r-1")

    def test_adding_or_repairing_another_document_reuses_unchanged_reading_steps(self):
        from test_operation_runs import OperationProvider, OperationRunner, request
        shutil.copytree(ROOT / "prompts/operations", self.root / "prompts/operations")
        provider = OperationProvider()
        runner = OperationRunner(self.root, self.path, provider, synthetic=True)
        def run(ids):
            job = runner.start(AISession(), {"operation": request("extract", ids)})
            runner.thread.join(30)
            result = runner.get(job["id"])
            self.assertEqual(result["status"], "completed", result.get("error"))
        run(["doc-1"])
        run(["doc-1", "doc-2"])
        run(["doc-2", "doc-1"])
        for route in ("triage", "translate", "extract"):
            self.assertEqual(provider.calls.count(route), 2, route)
        original = runner.prepare_sources
        def repaired(job):
            sources = original(job)
            sources[1]["segments"][0]["text"] += " Recovered source footnote."
            return sources
        runner.prepare_sources = repaired
        run(["doc-1", "doc-2"])
        for route in ("triage", "translate", "extract"):
            self.assertEqual(provider.calls.count(route), 3, route)

    def test_translation_batches_receive_neighbors_but_return_owned_segments_only(self):
        original = self.provider.generate_json
        received = []
        def respond(session, selection, packet):
            response = original(session, selection, packet)
            if packet["route"] == "translate":
                data = json.loads(packet["input"])["untrusted_source_data"]
                received.append(data)
                output = json.loads(response["text"])
                owned = {s["id"] for s in data["segments"]}
                output["segments"] = [s for s in output["segments"] if s["segment_id"] in owned]
                response["text"] = json.dumps(output)
            return response
        self.provider.generate_json = respond
        from policytracker.country_runs import chunks
        with patch("policytracker.country_runs.chunks", side_effect=lambda segments, limit=9000: chunks(segments, 1 if limit == 9000 else limit)):
            job = self.start()
        self.assertEqual(job["status"], "completed", job.get("error"))
        self.assertGreater(len(received), 1)
        self.assertIn(received[1]["segments"][0]["id"], {s["id"] for s in received[0]["context_segments"]})
        self.assertTrue(all(not ({s["id"] for s in d["segments"]} & {s["id"] for s in d["context_segments"]}) for d in received))

    def test_cached_vision_text_keeps_its_request_response_in_the_new_job(self):
        from test_document_preparation import pdf_bytes
        from policytracker.profiles import sha
        from policytracker.settings import DEFAULTS
        source = self.root / "data/sources/Kazakhstan/NDC/Fixture/source.pdf"
        source.parent.mkdir(parents=True)
        source.write_bytes(pdf_bytes())
        doc = {"document_id": "scan", "country_code": "KAZ", "title": "Invented scan",
               "relative_path": source.relative_to(self.root).as_posix(), "sha256": sha(source.read_bytes())}
        page = {"page": 1, "text": "", "concerns": ["sparse_text"], "review": None}
        image = self.root / "tmp/page.png"
        image.parent.mkdir(exist_ok=True); image.write_bytes(b"synthetic image")
        output = {"status": "complete", "text": "Recovered source statement", "notes": []}
        self.runner.preparation_session = self.session
        self.provider.generate_json = Mock(return_value={"text": json.dumps(output)})
        def recover(root, document, page, settings, visual):
            result = visual(image, {"source_sha256": doc["sha256"], "physical_page": 1})
            return {**result, "method": "vision", "artifacts": []}
        jobs = []
        for number in (1, 2):
            job = {"id": f"recovery-{number}", "country": "KAZ", "status": "running", "stage": "prepare",
                   "documents": [doc], "settings": DEFAULTS, "selection": SELECTION, "method": self.runner.method()}
            with patch("policytracker.country_runs.inspect_document", return_value=[page]), patch("policytracker.country_runs.recover_page", side_effect=recover) as mocked:
                sources = self.runner.prepare_automatically(job)
            self.assertEqual(mocked.call_count, 1 if number == 1 else 0)
            jobs.append(job)
        self.assertEqual(self.provider.generate_json.call_count, 1)
        with self.runner.store() as store:
            rows = store.db.execute("SELECT job_id,result_hash FROM country_steps ORDER BY job_id").fetchall()
            self.assertEqual([r["job_id"] for r in rows], [j["id"] for j in jobs])
            self.assertEqual(rows[0]["result_hash"], rows[1]["result_hash"])
            receipt = json.loads(store.get(rows[1]["result_hash"]))
            self.assertEqual(json.loads(store.get(receipt["response_hash"]))["text"], json.dumps(output))
            self.assertEqual(sources[0]["page_checks"][0]["automatic"]["generation_step"]["result_hash"], rows[1]["result_hash"])

    def test_one_repair_receives_all_acceptance_errors_and_preserves_notes(self):
        original = self.provider.generate_json
        repairs = []
        def respond(session, selection, packet):
            response = original(session, selection, packet)
            if packet['route'] == 'extract':
                context = json.loads(packet['input'])['task_context']
                if 'repair' in context:
                    repairs.append(context['repair'])
                else:
                    result = json.loads(response['text'])
                    result['issues'] = ['Synthetic required text unresolved']
                    result['records'][0]['geography']['country_codes'] = []
                    result['records'][0]['evidence_ids'].remove('e-meta')
                    result['records'][0]['targets'][0]['value']['decimal'] = '999'
                    response['text'] = json.dumps(result, indent=2)
            return response
        self.provider.generate_json = respond
        job = self.start()
        self.assertEqual(job['status'], 'completed', job.get('error'))
        self.assertEqual(len(repairs), 1)
        self.assertIn('Synthetic required text unresolved', repairs[0]['errors'])
        self.assertIn('geography.country_codes', repairs[0]['errors'])
        self.assertIn('numeric value differs', repairs[0]['errors'])
        self.assertNotIn('references absent from its evidence_ids', repairs[0]['errors'])
        self.assertNotIn('e-meta', repairs[0]['previous_output']['records'][0]['evidence_ids'])
        self.assertIsInstance(repairs[0]['previous_output'], dict)

    def test_stop_finishes_current_step_and_resume_skips_it(self):
        self.provider.on_result = lambda route: self.runner.stop_event.set() if route == "translate" else None
        job = self.start()
        self.assertEqual(job["status"], "stopped", job.get("error"))
        self.assertEqual(self.provider.calls, ["triage", "translate"])
        self.provider.on_result = None
        self.runner.resume(self.session, job["id"])
        self.runner.thread.join(25)
        self.assertEqual(self.runner.get(job["id"])["status"], "completed", self.runner.get(job["id"]).get("error"))
        self.assertEqual(self.provider.calls.count("translate"), 1)

    def test_failed_run_preserves_previous_profile_and_retries_only_missing_step(self):
        first = self.start()
        self.assertEqual(first["status"], "completed", first.get("error"))
        # Change a prompt to invalidate cached outputs while keeping the prior profile.
        prompt = self.root / "prompts/v2/08-prime-report.md"
        prompt.write_text(prompt.read_text(encoding="utf-8") + "\nSynthetic revision.\n", encoding="utf-8")
        self.provider.bad = True
        failed = self.start()
        self.assertEqual(failed["status"], "failed")
        with ProfileStore(self.root, self.path) as store:
            self.assertEqual(store.country("KAZ", True)["profile"]["id"], first["profile_id"])
        count = len(self.provider.calls)
        self.provider.bad = False
        self.runner.resume(self.session, failed["id"])
        self.runner.thread.join(25)
        self.assertEqual(self.runner.get(failed["id"])["status"], "completed", self.runner.get(failed["id"]).get("error"))
        self.assertEqual(self.provider.calls[count:], ["prime"])

    def test_resume_after_restart_requires_compatible_method_and_never_autostarts(self):
        self.provider.fail = "extract"
        job = self.start()
        self.assertEqual(job["status"], "failed")
        restarted = FixtureRunner(self.root, self.path, self.provider, synthetic=True)
        self.assertIsNone(restarted.active)
        self.assertEqual(restarted.status("KAZ")["runs"][0]["status"], "failed")
        prompt = self.root / "prompts/v2/03-translate.md"
        prompt.write_text("changed", encoding="utf-8")
        with self.assertRaisesRegex(AIError, "changed"):
            restarted.resume(self.session, job["id"])

    def test_single_active_country_and_connection_changes_are_blocked(self):
        entered, release = threading.Event(), threading.Event()
        def pause(route):
            entered.set()
            release.wait(10)
        self.provider.on_result = pause
        job = self.runner.start(self.session, {"country": "KAZ", "document_ids": ["synthetic-document"], **SELECTION})
        self.assertTrue(entered.wait(10))
        try:
            with self.assertRaises(AIError):
                self.runner.start(self.session, {"country": "KAZ", **SELECTION})
            with self.assertRaises(AIError):
                self.session.idle()
            self.assertEqual(self.runner.stop(job["id"])["status"], "stopping")
        finally:
            release.set()
            self.runner.thread.join(25)

    def test_production_rejects_changed_sources_and_cross_country_selection_before_inference(self):
        runner = CountryRunner(self.root, self.path, self.provider)
        manifest = self.root / "data/manifests/corpus.json"
        manifest.parent.mkdir(parents=True, exist_ok=True)
        source = self.root / "original.pdf"
        source.write_bytes(b"not a real PDF")
        manifest.write_text(json.dumps({"documents": [{"document_id": "doc", "country_code": "KAZ", "relative_path": "original.pdf", "sha256": "a"*64}]}), encoding="utf-8")
        for country in ("ALB", "KAZ"):
            with self.assertRaises(AIError):
                runner.start(self.session, {"country": country, "document_ids": ["doc"], **SELECTION})
        self.assertFalse(self.provider.calls)

    def test_unreadable_page_stops_before_model_requests(self):
        from pypdf import PdfWriter
        writer = PdfWriter(); writer.add_blank_page(width=100, height=100)
        buffer = io.BytesIO(); writer.write(buffer)
        with self.runner.store() as store:
            source_hash = store.put(buffer.getvalue())
        job = {"country": "KAZ", "documents": [{"document_id": "blank", "title": "Blank fixture",
               "sha256": source_hash, "relative_path": "blank.pdf"}]}
        with self.assertRaisesRegex(ValueError, "1 source page in 1 document"):
            CountryRunner.prepare_sources(self.runner, job)
        self.assertFalse(self.provider.calls)

    def test_dense_page_is_partitioned_losslessly_before_extraction(self):
        # A dense page must not bypass the smaller extraction response budget.
        text = ('A quantified source statement with its conditions.\n' * 145) + 'Final source sentence.'
        with self.runner.store() as store:
            source_hash = store.put(b'synthetic PDF bytes')
        job = {'country':'KAZ', 'documents':[{'document_id':'dense', 'title':'Dense fixture',
               'sha256':source_hash, 'relative_path':'dense.pdf'}]}
        with patch('policytracker.preparation.parsed_pages', return_value=((text, ()),)):
            source = CountryRunner.prepare_sources(self.runner, job)[0]
        self.assertEqual(''.join(s['text'] for s in source['segments']), text)
        self.assertTrue(all(len(s['text']) <= 3000 for s in source['segments']))
        self.assertTrue(all(s['page'] == 1 for s in source['segments']))
        self.assertEqual(source['sha256'], source_hash)
        self.assertFalse(self.provider.calls)


class StructuredTransportTests(unittest.TestCase):
    def test_chunk_ids_preserve_source_and_taxonomy_ids_with_the_same_spelling(self):
        bundle = demo_bundle(ROOT)
        segments = {s["id"]: s["text"] for source in bundle["sources"] for s in source["segments"]}
        for shared in (bundle["extraction"]["evidence"][0]["segment_id"],
                       bundle["extraction"]["records"][0]["labels"]["topic_ids"][0]):
            with self.subTest(shared_id=shared):
                extraction = copy.deepcopy(bundle["extraction"])
                original_id = extraction["evidence"][0]["local_id"]
                def rename(value, key=""):
                    if isinstance(value, dict): return {k: rename(v, k) for k, v in value.items()}
                    if isinstance(value, list): return [rename(v, key) for v in value]
                    if key in ("local_id", "evidence_id", "evidence_ids", "context_evidence_ids") and value == original_id:
                        return shared
                    return value
                extraction = rename(extraction)
                self.assertEqual(validate_v2(ROOT, "extraction", extraction, source_segments=segments,
                                            owned_segment_ids=list(segments)), [])
                namespaced = namespace_extraction(extraction, "b0:")
                self.assertEqual(validate_v2(ROOT, "extraction", namespaced, source_segments=segments,
                                            owned_segment_ids=list(segments)), [])
                self.assertEqual(namespaced["records"][0]["labels"], extraction["records"][0]["labels"])
                self.assertEqual(namespaced["evidence"][0]["local_id"], "b0:" + shared)
                self.assertEqual(extraction["evidence"][0]["local_id"], shared)

    def test_merging_empty_sections_preserves_incomplete_and_inapplicable_states(self):
        report = read_json(ROOT / "examples/v2/prime-report.json")
        for state in ("not_processed", "not_applicable"):
            first, second = copy.deepcopy(report), copy.deepcopy(report)
            for output in (first, second):
                output["sections"][0].update(state=state, findings=[], gap_note="Explicit scope limitation")
                if state == "not_processed": output["availability"] = "partial"
            merged = merge_synthesis([first, second])
            self.assertEqual(merged["sections"][0]["state"], state)
        second["sections"][0]["state"] = "not_processed"
        second["availability"] = "partial"
        merged = merge_synthesis([first, second])
        self.assertEqual(merged["sections"][0]["state"], "not_processed")
        self.assertEqual(merged["availability"], "partial")
        from policytracker.engineering import validate_v2
        self.assertFalse(validate_v2(ROOT, "report", merged))

    def test_api_uses_schema_selection_and_records_usage_without_live_calls(self):
        api, rpc = FakeAPI(), FakeRPC()
        service = AIService(ROOT, rpc=rpc, transport=api)
        session = AISession()
        service.connect_api(session, KEY)
        packet = compose_v2(ROOT, "translate", {}, {})
        response = service.generate_json(session, SELECTION, packet)
        body = api.calls[-1][2]
        self.assertEqual(body["text"]["format"]["schema"], packet["schema"])
        self.assertEqual(body["instructions"], packet["instructions"])
        self.assertEqual(body["input"], packet["input"])
        self.assertEqual(response["confirmed_effort"], "high")
        self.assertFalse(body["store"])

    def test_api_rejects_a_different_returned_model(self):
        api = FakeAPI()
        def wrong_model(key, path, body=None):
            response = api(key, path, body)
            if path == "responses": response["model"] = "different-model"
            return response
        service = AIService(ROOT, rpc=FakeRPC(), transport=wrong_model)
        session = AISession(); service.connect_api(session, KEY)
        with self.assertRaisesRegex(AIError, "different model"):
            service.generate_json(session, SELECTION, compose_v2(ROOT, "translate", {}, {}))

    def test_compact_synthesis_retains_all_records_quotes_and_zero_values(self):
        extraction = read_json(ROOT / "examples/v2/extraction.json")
        before = copy.deepcopy(extraction)
        compact = synthesis_evidence(extraction)
        self.assertEqual(extraction, before)
        self.assertEqual(len(compact["records"]), len(extraction["records"]))
        self.assertEqual([e["quote_original"] for e in compact["evidence"]], [e["quote_original"] for e in extraction["evidence"]])
        self.assertNotIn("field_support", compact["records"][0])
        self.assertEqual(synthesis_evidence({"records": [{"zero": 0, "false": False}], "evidence": []})["records"], [{"zero": 0, "false": False}])

    def test_codex_receives_output_schema_and_no_fallback(self):
        service = AIService(ROOT, rpc=FakeRPC(), transport=FakeAPI())
        session = AISession()
        service.connect_chatgpt(session)
        packet = compose_v2(ROOT, "translate", {}, {})
        service.generate_json(session, {**SELECTION, "route": "codex_chatgpt"}, packet)
        calls = dict(service.rpc.calls)
        self.assertEqual(calls["turn/start"]["outputSchema"], packet["schema"])
        self.assertFalse(calls["thread/start"]["allowProviderModelFallback"])
        self.assertEqual(calls["thread/start"]["baseInstructions"], packet["instructions"])
        self.assertEqual(calls["thread/start"]["config"]["mcp_servers.example.enabled"], False)

    def test_missing_translation_and_unrelated_reconciliation_are_rejected(self):
        with self.assertRaises(ValueError):
            check_translation({"segments": []}, [{"id": "s", "text": "Original"}])
        extraction = read_json(ROOT / "examples/v2/extraction.json")
        output = {"groups": [], "changes": [], "relations": [{"source_record_ids": ["r-1"],
                    "target_record_ids": ["unknown"], "evidence_ids": ["e-1"]}]}
        with self.assertRaises(ValueError):
            check_reconciliation(output, extraction)

    def test_run_endpoints_require_session_csrf_and_same_origin(self):
        with workspace_test_directory() as folder:
            server = LocalServer(ROOT, port=0, service=AIService(ROOT, rpc=FakeRPC()), profiles_path=folder/"test.sqlite3")
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                conn = http.client.HTTPConnection("127.0.0.1", server.server_port)
                conn.request("POST", "/api/ai/country-runs", "{}", {"Content-Type": "application/json"})
                response = conn.getresponse(); self.assertEqual(response.status, 401); response.read()
                conn.request("GET", "/api/ai/session")
                response = conn.getresponse(); cookie = response.getheader("Set-Cookie").split(";")[0]; token = json.loads(response.read())["csrf"]
                conn.request("POST", "/api/ai/country-runs", "{}", {"Cookie": cookie, "Content-Type": "application/json"})
                response = conn.getresponse(); self.assertEqual(response.status, 403); response.read()
                for endpoint in ('/api/ai/analyses', '/api/ai/profile-selection/KAZ'):
                    conn.request("POST", endpoint, "{}", {"Cookie": cookie, "Content-Type": "application/json"})
                    response = conn.getresponse(); self.assertEqual(response.status, 403); response.read()
                conn.request("POST", "/api/ai/country-runs", "{}", {"Cookie": cookie, "Content-Type": "application/json", "X-PolicyTracker-CSRF": token, "Origin": "https://example.invalid"})
                response = conn.getresponse(); self.assertEqual(response.status, 403); response.read()
                conn.request("GET", "/api/ai/countries/KAZ", headers={"Cookie": cookie})
                response = conn.getresponse(); self.assertEqual(response.status, 200); self.assertEqual(json.loads(response.read())["runs"], [])
                conn.close()
            finally:
                server.shutdown(); server.server_close(); thread.join(5)


class ExactRequestCacheTests(unittest.TestCase):
    setUp = CountryTests.setUp
    tearDown = CountryTests.tearDown
    start = CountryTests.start

    def saved_reading(self):
        original = self.provider.generate_json
        self.provider.generate_json = lambda session, selection, packet: {
            **original(session, selection, packet), "route": selection["route"]}
        self.provider.fail = "extract"
        old = self.start()
        self.assertEqual(old["status"], "failed")
        with self.runner.store() as store:
            row = store.db.execute("SELECT result_hash FROM country_steps WHERE job_id=? AND step='translate:0'", (old["id"],)).fetchone()
            result = json.loads(store.get(row[0]))
            packet = json.loads(store.get(result["request_hash"]))
        worker = self.root / "src/policytracker/country_runs.py"
        worker.write_bytes(worker.read_bytes() + b"\n# Unrelated extraction planner correction.\n")
        self.provider.fail = None
        return old, row[0], result, packet

    def new_step(self, old, packet, *, check=None, selection=None):
        # This direct step represents a new explicit run, whose launch clears Stop.
        self.runner.stop_event.clear()
        job = {**copy.deepcopy(old), "id": "new-reading-job", "method": self.runner.method(),
               "selection": selection or old["selection"], "status": "running"}
        payload = json.loads(packet["input"])
        return self.runner.step(self.session, job, "translate:0", "translate", payload["task_context"],
                                payload["untrusted_source_data"], check or (lambda out: check_translation(out, payload["untrusted_source_data"]["segments"])))

    def test_new_worker_reuses_identical_reading_requests_and_keeps_original_receipts(self):
        old, original_hash, result, packet = self.saved_reading()
        with self.runner.store() as store:
            before = store.db.execute("SELECT data FROM country_jobs WHERE id=?", (old["id"],)).fetchone()[0]
            original_bytes = store.get(original_hash)
        with self.assertRaisesRegex(AIError, "method or worker changed"):
            self.runner.resume(self.session, old["id"])
        self.provider.calls.clear()
        current = self.start()
        self.assertEqual(current["status"], "completed", current.get("error"))
        self.assertNotIn("triage", self.provider.calls)
        self.assertNotIn("translate", self.provider.calls)
        self.assertIn("extract", self.provider.calls)
        self.assertEqual(set(current["reused_steps"]), {"triage:synthetic-document", "translate:0"})
        with self.runner.store() as store:
            self.assertEqual(store.db.execute("SELECT data FROM country_jobs WHERE id=?", (old["id"],)).fetchone()[0], before)
            self.assertEqual(store.get(original_hash), original_bytes)
            self.assertEqual(store.db.execute("SELECT result_hash FROM country_steps WHERE job_id=? AND step='translate:0'", (current["id"],)).fetchone()[0], original_hash)
            profile = store.profile(current["profile_id"])
            origin = profile["generation"]["reused_steps"]["translate:0"]
            self.assertEqual(origin["method"], old["method"])
            self.assertEqual(origin["result_hash"], original_hash)
            for fingerprint in origin["method"].values():
                store.get(fingerprint)
        self.provider.calls.clear()
        repeated = self.start()
        self.assertEqual(repeated["status"], "completed", repeated.get("error"))
        self.assertEqual(self.provider.calls, [])
        self.assertEqual(repeated["reused_steps"], current["reused_steps"])
        with self.runner.store() as store:
            self.assertEqual(store.profile(repeated["profile_id"])["generation"]["reused_steps"], current["reused_steps"])

    def test_exact_cache_rejects_changed_requests_and_requested_selection(self):
        old, original_hash, result, packet = self.saved_reading()
        self.provider.generate_json = Mock(side_effect=AIError("test", "Fresh request required"))
        changed = copy.deepcopy(packet)
        payload = json.loads(changed["input"])
        payload["task_context"]["scope"] += " Changed source scope."
        changed["input"] = json.dumps(payload)
        for source, selection in ((changed, None), (packet, {**old["selection"], "effort": "low"})):
            with self.subTest(selection=selection), self.assertRaisesRegex(AIError, "Fresh request required"):
                self.new_step(old, source, selection=selection)

    def test_exact_cache_requires_real_synthetic_provenance_and_confirmed_response(self):
        from policytracker.profiles import encoded
        old, original_hash, result, packet = self.saved_reading()
        self.provider.generate_json = Mock(side_effect=AIError("test", "Fresh request required"))
        with self.runner.store() as store:
            response = json.loads(store.get(result["response_hash"]))
        for defect in ("missing_synthetic", "different_synthetic", "actual_model", "confirmed_effort", "route", "selection", "response_output", "schema", "repaired_request"):
            with self.subTest(defect=defect):
                producer, candidate, reply = copy.deepcopy(old), copy.deepcopy(result), copy.deepcopy(response)
                with self.runner.store() as store:
                    if defect == "missing_synthetic": producer.pop("synthetic")
                    elif defect == "different_synthetic": producer["synthetic"] = not self.runner.synthetic
                    elif defect in ("actual_model", "confirmed_effort", "route"): reply[defect] = "different"
                    elif defect == "selection": candidate["selection"]["model"] = "different"
                    elif defect == "response_output": reply["text"] = '{}'
                    elif defect == "schema":
                        candidate["output"]["unexpected"] = True
                        reply["text"] = json.dumps(candidate["output"])
                    elif defect == "repaired_request":
                        candidate["request_hash"] = store.put(encoded({**packet, "repair": "Different request"}))
                        candidate["attempt"] = 2
                    candidate["response_hash"] = store.put(encoded(reply))
                    self.runner.write(store, producer)
                    store.db.execute("UPDATE country_steps SET result_hash=? WHERE job_id=? AND step='translate:0'",
                                     (store.put(encoded(candidate)), old["id"]))
                with self.assertRaisesRegex(AIError, "Fresh request required"):
                    self.new_step(old, packet)

    def test_exact_cache_rechecks_current_route_acceptance(self):
        old, original_hash, result, packet = self.saved_reading()
        self.provider.generate_json = Mock(side_effect=AIError("test", "Fresh request required"))
        checked = Mock(side_effect=ValueError("New acceptance requirement"))
        with self.assertRaisesRegex(AIError, "Fresh request required"):
            self.new_step(old, packet, check=checked)
        checked.assert_called_once_with(result["output"])


class ExtractionReceiptTests(unittest.TestCase):
    setUp = CountryTests.setUp
    tearDown = CountryTests.tearDown
    start = CountryTests.start

    def configure(self, *, omit=False, repair=False):
        original = self.provider.generate_json
        def respond(session, selection, packet):
            response = {**original(session, selection, packet), "route": selection["route"]}
            if packet["route"] == "extract":
                output = json.loads(response["text"])
                if omit:
                    output["records"][0]["evidence_ids"].remove("e-meta")
                if repair and "repair" not in json.loads(packet["input"])["task_context"]:
                    output["issues"] = ["Unresolved source defect"]
                response["text"] = json.dumps(output, indent=2)
            return response
        self.provider.generate_json = respond

    def direct_step(self, job_id="original", context=None, check=None):
        from policytracker.engineering import extraction_errors
        from policytracker.profiles import require
        source = demo_bundle(self.root)["sources"][0]
        context = context or {"country_codes": ["KAZ"], "owned_segment_ids": [s["id"] for s in source["segments"]]}
        job = {"id": job_id, "country": "KAZ", "status": "running", "stage": "extract",
               "method": self.runner.method(), "selection": SELECTION, "synthetic": True}
        with self.runner.store() as store:
            for path in job["method"]:
                store.put((self.root / path).read_bytes())
            self.runner.write(store, job)
        def accept(output):
            errors = extraction_errors(self.root, output, "KAZ", source_segments={s["id"]: s["text"] for s in source["segments"]},
                                       owned_segment_ids=context["owned_segment_ids"])
            require(not errors, "; ".join(errors))
        output = self.runner.step(self.session, job, "extract:0", "extract", context, {"segments": source["segments"]}, check or accept)
        return job, output

    def worker_change(self):
        worker = self.root / "src/policytracker/country_runs.py"
        worker.write_bytes(worker.read_bytes() + b"\n# Synthetic unrelated worker change.\n")

    def receipt(self, job_id):
        with self.runner.store() as store:
            row = store.db.execute("SELECT result_hash FROM country_steps WHERE job_id=? AND step='extract:0'", (job_id,)).fetchone()
            return row[0], json.loads(store.get(row[0]))

    def test_new_extraction_closes_explicit_links_and_preserves_raw_receipt_and_profile_trace(self):
        self.configure(omit=True)
        original = self.start()
        self.assertEqual(original["status"], "completed", original.get("error"))
        self.assertEqual(self.provider.calls.count("extract"), 1)
        receipt_hash, result = self.receipt(original["id"])
        self.assertEqual(result["normalization"]["kind"], "explicit_record_evidence_closure_v1")
        self.assertEqual([a["evidence_id"] for a in result["normalization"]["additions"]], ["e-meta"])
        with self.runner.store() as store:
            raw_response = store.get(result["response_hash"])
            raw_output = json.loads(json.loads(raw_response)["text"])
            self.assertNotIn("e-meta", raw_output["records"][0]["evidence_ids"])
            self.assertIn("e-meta", result["output"]["records"][0]["evidence_ids"])
            expected = copy.deepcopy(raw_output)
            expected["records"][0]["evidence_ids"].append("e-meta")
            self.assertEqual(result["output"], expected)
            profile = store.profile(original["profile_id"])
            receipt = next(r for r in profile["generation"]["step_receipts"] if r["step"] == "extract:0")
            self.assertEqual(receipt["normalization"], result["normalization"])
        self.worker_change()
        self.provider.calls.clear()
        reused = self.start()
        self.assertEqual(reused["status"], "completed", reused.get("error"))
        self.assertNotIn("extract", self.provider.calls)
        self.assertEqual(self.receipt(reused["id"])[0], receipt_hash)
        with self.runner.store() as store:
            self.assertEqual(store.get(result["response_hash"]), raw_response)
            self.assertEqual(reused["reused_steps"]["extract:0"]["method"], original["method"])

    def test_successful_repair_reuses_exact_initial_and_repair_chain(self):
        self.configure(repair=True)
        old, output = self.direct_step()
        receipt_hash, result = self.receipt(old["id"])
        self.assertEqual(result["attempt"], 2)
        self.assertNotIn("normalization", result)
        self.worker_change()
        self.provider.generate_json = Mock(side_effect=AIError("test", "Fresh request required"))
        new, reused = self.direct_step("new")
        self.assertEqual(reused, output)
        self.assertEqual(self.receipt(new["id"])[0], receipt_hash)
        with self.runner.store() as store:
            attempts = [dict(r) for r in store.db.execute("SELECT * FROM country_attempts WHERE job_id=? ORDER BY sequence", (old["id"],))]
        # Use only the original candidate when deliberately corrupting its chain.
            store.db.execute("DELETE FROM country_steps WHERE job_id=?", (new["id"],))
        for defect in ("changed_base", "missing_first", "changed_error", "failed_success", "missing_success"):
            with self.subTest(defect=defect), self.runner.store() as store:
                store.db.execute("DELETE FROM country_attempts WHERE job_id=?", (old["id"],))
                for row in attempts:
                    if defect == "missing_first" and row == attempts[0]: continue
                    if defect == "missing_success" and row == attempts[-1]: continue
                    error = "Changed repair reason" if defect == "changed_error" and row == attempts[0] else row["error"]
                    if defect == "failed_success" and row == attempts[-1]: error = "Not accepted"
                    store.db.execute("INSERT INTO country_attempts(sequence,job_id,step,request_hash,response_hash,error) VALUES(?,?,?,?,?,?)",
                                     (row["sequence"], row["job_id"], row["step"], row["request_hash"], row["response_hash"], error))
            context = None
            if defect == "changed_base":
                context = {"country_codes": ["KAZ"], "owned_segment_ids": ["s-meta", "s-1", "s-2"], "scope": "different"}
            with self.assertRaisesRegex(AIError, "Fresh request required"):
                self.direct_step("rejected-" + defect, context=context)

    def test_normalized_cache_requires_exact_trace_and_current_full_acceptance(self):
        from policytracker.profiles import encoded
        self.configure(omit=True)
        old, _ = self.direct_step()
        _, original = self.receipt(old["id"])
        self.worker_change()
        self.provider.generate_json = Mock(side_effect=AIError("test", "Fresh request required"))
        for defect in ("missing_trace", "changed_trace", "changed_output", "current_acceptance"):
            candidate = copy.deepcopy(original)
            if defect == "missing_trace": candidate.pop("normalization")
            elif defect == "changed_trace": candidate["normalization"]["additions"][0]["source_paths"] = []
            elif defect == "changed_output": candidate["output"]["records"][0]["description_en"] = "Unsupported new claim"
            with self.subTest(defect=defect), self.runner.store() as store:
                store.db.execute("UPDATE country_steps SET result_hash=? WHERE job_id=? AND step='extract:0'",
                                 (store.put(encoded(candidate)), old["id"]))
            check = Mock(side_effect=ValueError("Current acceptance rejected")) if defect == "current_acceptance" else None
            with self.assertRaisesRegex(AIError, "Fresh request required"):
                self.direct_step("rejected-" + defect, check=check)
            if check: check.assert_called_once_with(original["output"])

    def test_legacy_geography_repair_requires_fresh_request_without_changing_receipts(self):
        from policytracker.profiles import require
        self.configure()
        fresh_response = self.provider.generate_json
        def regional_response(session, selection, packet):
            response = fresh_response(session, selection, packet)
            if "repair" not in json.loads(packet["input"])["task_context"]:
                output = json.loads(response["text"])
                output["records"][0]["geography"].update(country_codes=["KAZ", "KGZ", "AFG"], scope="regional")
                response["text"] = json.dumps(output)
            return response
        self.provider.generate_json = regional_response
        def retired_check(output):
            countries = output["records"][0]["geography"]["country_codes"]
            require(countries == ["KAZ"],
                    f"records[c-1].geography.country_codes: expected [KAZ], got {countries}")
        old, _ = self.direct_step(check=retired_check)
        receipt_hash, result = self.receipt(old["id"])
        self.assertEqual(result["attempt"], 2)
        with self.runner.store() as store:
            old_job_bytes = store.db.execute("SELECT data FROM country_jobs WHERE id=?", (old["id"],)).fetchone()[0]
            attempts = [dict(row) for row in store.db.execute(
                "SELECT * FROM country_attempts WHERE job_id=? ORDER BY sequence", (old["id"],))]
            fingerprints = {receipt_hash, *(row[key] for row in attempts for key in ("request_hash", "response_hash"))}
            archived = {key: store.get(key) for key in fingerprints}
            self.assertIn(".geography.country_codes: expected [", attempts[0]["error"])
            raw_first = json.loads(json.loads(store.get(attempts[0]["response_hash"]))["text"])
            self.assertEqual(raw_first["records"][0]["geography"]["country_codes"], ["KAZ", "KGZ", "AFG"])
        self.worker_change()
        self.provider.calls.clear()
        self.provider.generate_json = fresh_response
        new, _ = self.direct_step("fresh-after-geography-fix")
        self.assertEqual(self.provider.calls, ["extract"])
        self.assertNotIn("extract:0", new.get("reused_steps", {}))
        new_hash, new_result = self.receipt(new["id"])
        self.assertNotEqual(new_hash, receipt_hash)
        self.assertEqual(new_result["attempt"], 1)
        self.assertEqual(new_result["request_hash"], attempts[0]["request_hash"])
        with self.runner.store() as store:
            self.assertEqual(store.db.execute("SELECT data FROM country_jobs WHERE id=?", (old["id"],)).fetchone()[0], old_job_bytes)
            self.assertEqual(store.db.execute("SELECT result_hash FROM country_steps WHERE job_id=? AND step='extract:0'", (old["id"],)).fetchone()[0], receipt_hash)
            self.assertEqual([dict(row) for row in store.db.execute(
                "SELECT * FROM country_attempts WHERE job_id=? ORDER BY sequence", (old["id"],))], attempts)
            self.assertEqual({key: store.get(key) for key in archived}, archived)

    def test_legacy_condition_repair_requires_fresh_request_without_changing_receipts(self):
        from policytracker.profiles import require
        self.configure()
        base_response = self.provider.generate_json
        historical_text = "Historical conditional benchmark: 20 flood early-warning systems by 2030. The specific condition is not stated."
        source_path = self.root / "examples/v2/synthetic-input.json"
        source = read_json(source_path)
        source["source_segments"]["s-1"] = historical_text
        source_path.write_text(json.dumps(source), encoding="utf-8")
        def historical_response(session, selection, packet):
            response = base_response(session, selection, packet)
            output = json.loads(response["text"])
            output["evidence"][1]["quote_original"] = historical_text
            record = output["records"][0]
            record.update(kind="context", label_en="Historical conditional benchmark",
                          description_en=historical_text)
            repaired = "repair" in json.loads(packet["input"])["task_context"]
            record["targets"][0]["condition_text"] = "Invented international financing condition" if repaired else None
            record["details"][0]["text_en"] = "The historical benchmark's specific condition is not stated."
            record["missing_fields"] = [] if repaired else [{"field_path": "/targets/0/condition_text",
                "reason": "not_stated", "detail": "The historical benchmark has no stated condition."}]
            response["text"] = json.dumps(output)
            return response
        self.provider.generate_json = historical_response
        def retired_check(output):
            require(output["records"][0]["targets"][0]["condition_text"], "conditional target missing condition")
        old, _ = self.direct_step(check=retired_check)
        receipt_hash, result = self.receipt(old["id"])
        self.assertEqual(result["attempt"], 2)
        self.assertEqual(result["output"]["records"][0]["targets"][0]["condition_text"],
                         "Invented international financing condition")
        with self.runner.store() as store:
            old_job_bytes = store.db.execute("SELECT data FROM country_jobs WHERE id=?", (old["id"],)).fetchone()[0]
            attempts = [dict(row) for row in store.db.execute(
                "SELECT * FROM country_attempts WHERE job_id=? ORDER BY sequence", (old["id"],))]
            fingerprints = {receipt_hash, *(row[key] for row in attempts for key in ("request_hash", "response_hash"))}
            archived = {key: store.get(key) for key in fingerprints}
            self.assertEqual(attempts[0]["error"], "conditional target missing condition")
        self.worker_change()
        self.provider.calls.clear()
        new, output = self.direct_step("fresh-after-condition-fix")
        self.assertEqual(self.provider.calls, ["extract"])
        self.assertIsNone(output["records"][0]["targets"][0]["condition_text"])
        self.assertNotIn("extract:0", new.get("reused_steps", {}))
        new_hash, new_result = self.receipt(new["id"])
        self.assertNotEqual(new_hash, receipt_hash)
        self.assertEqual(new_result["attempt"], 1)
        self.assertEqual(new_result["request_hash"], attempts[0]["request_hash"])
        with self.runner.store() as store:
            self.assertEqual(store.db.execute("SELECT data FROM country_jobs WHERE id=?", (old["id"],)).fetchone()[0], old_job_bytes)
            self.assertEqual(store.db.execute("SELECT result_hash FROM country_steps WHERE job_id=? AND step='extract:0'", (old["id"],)).fetchone()[0], receipt_hash)
            self.assertEqual([dict(row) for row in store.db.execute(
                "SELECT * FROM country_attempts WHERE job_id=? ORDER BY sequence", (old["id"],))], attempts)
            self.assertEqual({key: store.get(key) for key in archived}, archived)


if __name__ == "__main__":
    unittest.main()

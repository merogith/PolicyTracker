"""Local vertical workflow regressions, using invented evidence and no providers."""
import copy
import csv
import http.client
import io
import json
import shutil
import sqlite3
import threading
import unittest
from pathlib import Path

from policytracker.profiles import CONTEXT_PATHS, ProfileStore, demo_bundle, register_csv, sha, encoded
from policytracker.local_server import LocalServer
from test_method_customization import workspace_test_directory
from test_ai_runtime import FakeRPC
from test_document_preparation import pdf_bytes
from policytracker.ai_runtime import AIService

ROOT = Path(__file__).resolve().parents[1]


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.temp = workspace_test_directory()
        self.root = self.temp.__enter__()
        for path in list(CONTEXT_PATHS) + [f"examples/v2/{name}.json" for name in
                                         ("synthetic-input", "translation", "extraction", "prime-report")]:
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / path, target)
        self.store = ProfileStore(self.root)
        self.bundle = demo_bundle(self.root)

    def tearDown(self):
        self.store.db.close()
        self.temp.__exit__(None, None, None)

    def save(self, bundle=None):
        return self.store.complete(self.store.prepare(bundle or self.bundle))

    def save_with_reused_step(self, normalization=None):
        route='extract' if normalization else 'translate'
        step=route+':0'
        extra={'normalization':normalization} if normalization else {}
        request=self.store.put(encoded({'route':route,'input':'Invented source'}))
        response=self.store.put(encoded({'text':'Invented response'}))
        receipt=self.store.put(encoded({'request_hash':request,'response_hash':response,**extra}))
        old_worker=self.store.put(b'# Original reading worker\n')
        current_worker=self.store.put(b'# Current extraction worker\n')
        generation={'method':{'src/policytracker/country_runs.py':current_worker},
                    'reconciliation':self.store.put(encoded({'groups':[],'relations':[],'changes':[],'issues':[]})),
                    'steps':[{'step':step,'result_hash':receipt}],
                    'step_receipts':[{'step':step,'request_hash':request,'response_hash':response,**extra}],
                    'reused_steps':{step:{'job_id':'invented-origin','step':step,'result_hash':receipt,
                        'method':{'src/policytracker/country_runs.py':old_worker}}},'attempts':[]}
        profile=self.store.complete(self.store.prepare(self.bundle,generation=generation))
        return profile,generation,old_worker

    def test_reused_origin_method_is_checked_without_rewriting_the_archive(self):
        profile,generation,old_worker=self.save_with_reused_step()
        before=[tuple(row) for row in self.store.db.execute('SELECT * FROM objects ORDER BY hash')]
        self.assertEqual(self.store.reused_method_files(generation),{old_worker:b'# Original reading worker\n'})
        self.assertEqual(self.store.profile(profile['id'])['generation'],generation)
        self.assertEqual(before,[tuple(row) for row in self.store.db.execute('SELECT * FROM objects ORDER BY hash')])
        self.store.db.execute('DROP TRIGGER immutable_objects_update')
        self.store.db.execute('UPDATE objects SET body=? WHERE hash=?',(b'corrupt original worker',old_worker))
        with self.assertRaisesRegex(ValueError,'missing or corrupt'):
            self.store.profile(profile['id'])

    def test_reused_origin_must_match_the_archived_step_receipt(self):
        profile,generation,old_worker=self.save_with_reused_step()
        changed=copy.deepcopy(generation)
        changed['reused_steps']['translate:0']['result_hash']=self.store.put(encoded({'different':'receipt'}))
        with self.assertRaisesRegex(ValueError,'Reused origin differs'):
            self.store.reused_method_files(changed)

    def test_country_and_analysis_archives_include_original_reused_method_bytes(self):
        normalization={'kind':'explicit_record_evidence_closure_v1','additions':[
            {'record_id':'r-1','evidence_id':'e-1','source_paths':['/records/0/field_support/0/evidence_ids/0'],
             'destination_path':'/records/0/evidence_ids'}]}
        profile,generation,old_worker=self.save_with_reused_step(normalization)
        server=LocalServer(self.root,0,service=AIService(self.root,rpc=FakeRPC()),profiles_path=self.root/'data/local-profiles/workspace.sqlite3')
        analysis_id='analysis-invented-reuse'
        with server.countries.store() as store:
            result={'id':analysis_id,'generation':generation,'full_extraction_hash':store.put(encoded({'records':[]}))}
            server.countries.write(store,{'id':analysis_id,'country':'MULTI','operation':{'task':'extract'},
                'status':'completed','result_hash':store.put(encoded(result))})
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            conn=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=30)
            conn.request('GET','/api/ai/session');response=conn.getresponse()
            cookie=response.getheader('Set-Cookie').split(';')[0];response.read()
            for path in ('/api/profiles/KAZ?synthetic=1&archive=1','/api/ai/analyses/'+analysis_id+'?archive=1'):
                with self.subTest(path=path):
                    conn.request('GET',path,headers={'Cookie':cookie});response=conn.getresponse()
                    self.assertEqual(response.status,200)
                    saved=json.loads(response.read());saved=saved.get('profile',saved)
                    origin=saved['generation']['reused_steps']['extract:0']
                    self.assertEqual(origin['method']['src/policytracker/country_runs.py'],old_worker)
                    self.assertEqual(saved['generation_archive']['reused_method_files'][old_worker],'# Original reading worker\n')
                    self.assertEqual(saved['generation_archive']['method']['src/policytracker/country_runs.py'],'# Current extraction worker\n')
                    archive=saved['generation_archive']
                    receipts=archive.get('steps',archive.get('requests_and_responses'))
                    self.assertEqual(receipts[0]['normalization'],normalization)
                    self.assertEqual(receipts[0].get('response',receipts[0].get('response_hash')),{'text':'Invented response'})
        finally:
            conn.close();server.shutdown();server.server_close();thread.join(5)

    def test_frozen_inputs_survive_source_and_config_edits_and_restart(self):
        run = self.store.prepare(self.bundle)
        (self.root / "examples/v2/synthetic-input.json").write_text("changed", encoding="utf-8")
        (self.root / "schemas/v2/report.schema.json").write_text('{"type":"null"}', encoding="utf-8")
        profile = self.store.complete(run)
        original = self.store.get(profile["archive"]["sources"]["synthetic-document"])
        self.assertIn("s-1", original.decode("utf-8"))
        self.assertEqual(profile["validation"]["generation_method"], "not_verified")
        with ProfileStore(self.root) as restarted:
            self.assertEqual(restarted.country("KAZ", True)["profile"]["id"], run)
        self.assertEqual(self.store.summaries(), [])

    def test_failed_validation_keeps_previous_profile_and_records_failure(self):
        good = self.save()
        bad = copy.deepcopy(self.bundle)
        bad["extraction"]["evidence"][1]["quote_original"] = "Invented outside the source"
        run = self.store.prepare(bad)
        with self.assertRaisesRegex(ValueError, "quote must resolve"):
            self.store.complete(run)
        self.assertEqual(self.store.selection("KAZ", True)["profile_id"], good["id"])
        self.assertEqual(self.store.history("KAZ", True)[0]["state"], "failed")
        with self.assertRaisesRegex(ValueError, "not passed"):
            self.store.profile(run)

    def test_completion_order_pin_and_optimistic_revision(self):
        older, newer = self.store.prepare(self.bundle), self.store.prepare(self.bundle)
        self.store.complete(newer)
        self.store.complete(older)
        selection = self.store.selection("KAZ", True)
        self.assertEqual(selection["profile_id"], newer)
        pinned = self.store.select("KAZ", older, selection["revision"], True)
        third = self.save()["id"]
        self.assertEqual(self.store.selection("KAZ", True)["profile_id"], older)
        with self.assertRaisesRegex(ValueError, "revision"):
            self.store.select("KAZ", None, selection["revision"], True)
        latest = self.store.select("KAZ", None, pinned["revision"], True)
        self.assertEqual(latest["profile_id"], third)
        with self.assertRaisesRegex(ValueError, "another country or scope"):
            self.store.select("KAZ", older, 0, False)

    def test_new_sources_mark_previous_version_stale_until_checked(self):
        original = self.save()
        delayed = self.store.prepare(self.bundle)
        updated = copy.deepcopy(self.bundle)
        updated["sources"][0]["title"] = "Corrected source metadata"
        new_run = self.store.prepare(updated)
        self.store.complete(delayed)
        self.assertEqual(self.store.selection("KAZ", True)["profile_id"], original["id"])
        self.assertTrue(self.store.selection("KAZ", True)["stale_sources"])
        self.store.complete(new_run)
        self.assertEqual(self.store.selection("KAZ", True)["profile_id"], new_run)
        self.assertFalse(self.store.selection("KAZ", True)["stale_sources"])

    def test_bad_attribution_coverage_and_citations_are_rejected(self):
        mutations = [
            lambda b: b["sources"][0].update(metadata_verified=False),
            lambda b: b["sources"][0].update(layout_checked=False),
            lambda b: b["sources"][0].update(pages=2),
            lambda b: b["sources"][0]["segments"][0].update(english_text="Changed original"),
            lambda b: b["report"].update(country_codes=["ALB"]),
            lambda b: b["report"].update(source_group_ids=["other"]),
            lambda b: b["report"]["headline_findings"][0]["citations"].update(evidence_ids=["unknown"]),
            lambda b: b["extraction"]["coverage"].pop(),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                bad = copy.deepcopy(self.bundle)
                mutate(bad)
                run = self.store.prepare(bad)
                with self.assertRaises(ValueError):
                    self.store.complete(run)
        self.assertIsNone(self.store.country("KAZ", True)["profile"])

    def test_sources_paths_hashes_and_validator_changes(self):
        bad = copy.deepcopy(self.bundle)
        bad["sources"][0]["path"] = "../outside.pdf"
        with self.assertRaisesRegex(ValueError, "inside"):
            self.store.prepare(bad)
        bad["sources"][0]["path"] = "examples/v2/synthetic-input.json"
        bad["sources"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "fingerprint"):
            self.store.prepare(bad)
        run = self.store.prepare(self.bundle)
        path = self.root / "src/policytracker/engineering.py"
        path.write_bytes(path.read_bytes() + b"\n# changed validator\n")
        with self.assertRaisesRegex(ValueError, "Validator changed"):
            self.store.complete(run)

    def test_archive_immutability_and_corruption_detection(self):
        profile = self.save()
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.db.execute("UPDATE objects SET body='bad'")
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.db.execute("UPDATE runs SET manifest_hash='fake'")
        self.store.db.execute("DROP TRIGGER immutable_objects_update")
        self.store.db.execute("UPDATE objects SET body=? WHERE hash=?", (b"corrupt", profile["archive"]["bundle"]))
        with self.assertRaisesRegex(ValueError, "corrupt"):
            self.store.profile(profile["id"])

    def test_csv_keeps_nested_details_and_bilingual_evidence(self):
        profile = self.save()
        profile["extraction"]["records"][0]["label_en"] = '=HYPERLINK("bad")'
        rows = list(csv.DictReader(io.StringIO(register_csv(profile).lstrip("\ufeff"))))
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["label_en"].startswith("'="))
        self.assertEqual(json.loads(rows[0]["targets"])[0]["value"]["decimal"], "20")
        self.assertEqual(json.loads(rows[0]["targets"])[0]["conditionality"], "explicitly_conditional")
        segments = json.loads(rows[0]["source_segments"])
        self.assertTrue(any("К 2030" in s["text"] for s in segments))
        self.assertTrue(any("By 2030" in s["english_text"] for s in segments))
        self.assertEqual(json.loads(rows[0]["missing_fields"]), profile["extraction"]["records"][0]["missing_fields"])

    def test_http_reads_saved_data_without_exposing_database_or_mutations(self):
        profile = self.save()
        server = LocalServer(self.root, 0, service=AIService(self.root, rpc=FakeRPC()))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            connection = http.client.HTTPConnection("127.0.0.1", server.server_port)
            connection.request("GET", "/api/profiles")
            self.assertEqual(json.loads(connection.getresponse().read()), {"countries": []})
            connection.request("GET", "/api/profiles/KAZ?synthetic=1")
            result = connection.getresponse()
            self.assertEqual(result.status, 200)
            self.assertEqual(json.loads(result.read())["profile"]["id"], profile["id"])
            version = profile["id"]
            self.save()
            connection.request("GET", f"/api/profiles/KAZ?synthetic=1&version={version}&archive=1")
            result = connection.getresponse()
            self.assertEqual(result.status, 200)
            historical = json.loads(result.read())["profile"]
            self.assertEqual(historical["id"], version)
            self.assertIn("validation_context", historical["generation_archive"])
            connection.request("GET", f"/api/profiles/ALB?synthetic=1&version={version}")
            result = connection.getresponse(); self.assertEqual(result.status, 404); result.read()
            connection.request("GET", f"/api/profiles/KAZ?synthetic=1&format=csv&version={version}")
            result = connection.getresponse()
            self.assertEqual(result.status, 200)
            self.assertEqual(result.getheader("Content-Type"), "text/csv; charset=utf-8")
            exported = list(csv.DictReader(io.StringIO(result.read().decode("utf-8-sig"))))
            self.assertEqual(exported[0]["profile_id"], version)
            connection.request("GET", f"/api/profiles/KAZ?format=csv&version={version}")
            result = connection.getresponse()
            self.assertEqual(result.status, 404)
            result.read()
            connection.request("GET", "/data/local-profiles/workspace.sqlite3")
            result = connection.getresponse()
            self.assertEqual(result.status, 404)
            result.read()
            connection.request("GET", "/api/profiles/KAZ", headers={"Origin": "https://unrelated.invalid"})
            result = connection.getresponse()
            self.assertEqual(result.status, 403)
            result.read()
            connection.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_original_pdf_inline_read_is_version_bound_and_session_authorized(self):
        original = pdf_bytes()
        path = self.root / "examples/v2/archived-original.pdf"
        path.write_bytes(original)
        bundle = copy.deepcopy(self.bundle)
        bundle["sources"][0].update(path="examples/v2/archived-original.pdf", sha256=sha(original))
        profile = self.save(bundle)
        path.write_bytes(b"%PDF-1.4\nDifferent current bytes\n%%EOF")
        server = LocalServer(self.root, 0, service=AIService(self.root, rpc=FakeRPC()))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=10)
        url = f"/api/ai/documents/{profile['id']}/synthetic-document"
        try:
            connection.request("GET", url + "?inline=1")
            response = connection.getresponse(); self.assertEqual(response.status, 401); response.read()
            connection.request("GET", "/api/ai/session")
            response = connection.getresponse(); cookie = response.getheader("Set-Cookie").split(";")[0]; response.read()
            for query, disposition in [("?inline=1", "inline"), ("", "attachment")]:
                connection.request("GET", url + query, headers={"Cookie": cookie})
                response = connection.getresponse()
                self.assertEqual(response.status, 200)
                self.assertEqual(response.getheader("Content-Type"), "application/pdf")
                self.assertTrue(response.getheader("Content-Disposition").startswith(disposition + ";"))
                self.assertEqual(response.read(), original)
            connection.request("GET", url + "?inline=1", headers={"Cookie": cookie, "Origin": "https://unrelated.invalid"})
            response = connection.getresponse(); self.assertEqual(response.status, 403); response.read()
            connection.request("GET", url.replace("synthetic-document", "outside-version") + "?inline=1", headers={"Cookie": cookie})
            response = connection.getresponse(); self.assertEqual(response.status, 404); response.read()
        finally:
            connection.close(); server.shutdown(); server.server_close(); thread.join()


if __name__ == "__main__":
    unittest.main()

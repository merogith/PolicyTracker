"""Transport and local HTTP boundary regressions; no real model spending."""
import http.client
import json
import queue
import runpy
import threading
import time
import unittest
import urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from policytracker.ai_runtime import AIError, AISession, AIService, CodexRPC, api_models, api_request, provider_error
from policytracker.local_server import LocalServer
from test_method_customization import workspace_test_directory
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
KEY = "sk-unit-test-placeholder-not-a-real-key"


class FakeRPC:
    workdir = ROOT / "tmp"

    def __init__(self):
        self.calls = []
        self.listeners = []
        self.email = "test@example.invalid"
        self.turn_status = "completed"
        self.mismatch = False

    def subscribe(self):
        events = queue.Queue()
        self.listeners.append(events)
        return events

    def unsubscribe(self, events):
        self.listeners.remove(events)

    def emit(self, method, params):
        for events in self.listeners:
            events.put({"method": method, "params": params})

    def call(self, method, params=None, **kwargs):
        self.calls.append((method, params))
        if method == "account/read":
            return {"account": {"type": "chatgpt", "planType": "plus", "email": self.email}}
        if method == "model/list":
            return {"data": [{"id": "picker-id", "model": "gpt-6-astra", "displayName": "Astra", "hidden": False,
                "supportedReasoningEfforts": [{"reasoningEffort": e} for e in ("low", "high", "xhigh")], "defaultReasoningEffort": "high"}], "nextCursor": None}
        if method == "config/read":
            return {"config": {"mcp_servers": {"example": {}}}}
        if method == "thread/start":
            return {"thread": {"id": "thread-1"}, "model": "wrong" if self.mismatch else params["model"],
                    "reasoningEffort": params["config"]["model_reasoning_effort"]}
        if method == "turn/start":
            # Completion can arrive before the turn/start RPC response.
            self.emit("item/agentMessage/delta", {"threadId": "thread-1", "delta": "Connection successful."})
            self.emit("thread/tokenUsage/updated", {"threadId": "thread-1", "tokenUsage": {"last": {"inputTokens": 4, "outputTokens": 3, "totalTokens": 7}}})
            self.emit("turn/completed", {"threadId": "thread-1", "turn": {"id": "turn-1", "status": self.turn_status}})
            return {"turn": {"id": "turn-1"}}
        if method == "account/login/start":
            return {"loginId": "login-1", "authUrl": "https://auth.openai.com/authorize?state=synthetic"}
        if method == "account/rateLimits/read":
            return {"rateLimits": {"limitId": "legacy"}, "rateLimitsByLimitId": {"primary": {"limitId": "codex", "primary": {"usedPercent": 24}}}}
        return {}

    def close(self):
        pass


class FakeAPI:
    def __init__(self):
        self.calls = []
        self.status = "completed"
        self.error = None

    def __call__(self, key, path, body=None):
        self.calls.append((key, path, body))
        if self.error:
            raise self.error
        if path == "models":
            return {"data": [{"id": "gpt-6-astra"}, {"id": "gpt-4.1"}, {"id": "gpt-image-2"}]}
        return {"status": self.status, "model": body["model"], "reasoning": body.get("reasoning"),
                "output": [{"type": "message", "content": [{"type": "output_text", "text": "Connection successful."}]}],
                "usage": {"input_tokens": 3, "output_tokens": 4, "total_tokens": 7}}


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.rpc, self.api = FakeRPC(), FakeAPI()
        self.service = AIService(ROOT, rpc=self.rpc, transport=self.api)
        self.session = AISession()

    def test_preview_explains_missing_dependencies_before_importing_server(self):
        with patch("importlib.util.find_spec", return_value=None):
            with self.assertRaisesRegex(SystemExit, "dependencies are missing: pypdf, jsonschema") as caught:
                runpy.run_path(str(ROOT / "scripts/preview_ui.py"))
        self.assertIn("-m pip install -e .", str(caught.exception))

    def test_preview_explains_unsupported_python_before_importing_server(self):
        class OldVersion(tuple):
            major, minor = 3, 9
        with patch("sys.version_info", OldVersion((3, 9, 0))):
            with self.assertRaisesRegex(SystemExit, "requires Python 3.10 or newer") as caught:
                runpy.run_path(str(ROOT / "scripts/preview_ui.py"))
        self.assertIn("This command used Python 3.9", str(caught.exception))
        self.assertIn("scripts/preview_ui.py", str(caught.exception))

    def wait_job(self, job):
        deadline = time.monotonic() + 3
        while self.session.jobs[job["id"]]["status"] in ("queued", "running") and time.monotonic() < deadline:
            time.sleep(.005)
        return self.session.jobs[job["id"]]

    def test_blocked_api_network_explains_runtime_without_rejecting_key(self):
        with patch.dict("os.environ", {"CODEX_SANDBOX_NETWORK_DISABLED": "1"}), \
                patch("policytracker.ai_runtime.urllib.request.build_opener") as opener:
            opener.return_value.open.side_effect = urllib.error.URLError(ConnectionRefusedError())
            with self.assertRaises(AIError) as caught:
                api_request(KEY, "models")
        self.assertEqual(caught.exception.code, "restricted_runtime")
        self.assertIn("normal terminal", str(caught.exception))
        self.assertNotIn(KEY, str(caught.exception))

    def test_normal_network_failure_does_not_claim_key_is_invalid(self):
        with patch.dict("os.environ", {"CODEX_SANDBOX_NETWORK_DISABLED": "0"}), \
                patch("policytracker.ai_runtime.urllib.request.build_opener") as opener:
            opener.return_value.open.side_effect = urllib.error.URLError(ConnectionRefusedError())
            with self.assertRaises(AIError) as caught:
                api_request(KEY, "models")
        self.assertEqual(caught.exception.code, "network")
        self.assertIn("No authentication result", str(caught.exception))

    def test_restricted_codex_startup_explains_restart_instead_of_sign_in(self):
        rpc = CodexRPC(ROOT / "tmp")
        with patch.dict("os.environ", {"CODEX_SANDBOX_NETWORK_DISABLED": "1"}), \
                patch("policytracker.ai_runtime.shutil.which", return_value="codex"), \
                patch("policytracker.ai_runtime.subprocess.Popen") as process, \
                patch("policytracker.ai_runtime.threading.Thread"), \
                patch.object(rpc, "call", side_effect=AIError("codex_error", "Initialization failed")):
            process.return_value.poll.return_value = None
            with self.assertRaises(AIError) as caught:
                rpc.start()
            process.return_value.terminate.assert_called_once()
        self.assertEqual(caught.exception.code, "restricted_runtime")
        self.assertIn("normal terminal", str(caught.exception))
        self.assertNotIn("sign in again", str(caught.exception))

    def test_api_catalog_excludes_other_modalities_and_unknown_families(self):
        models = api_models({"data": [{"id": "gpt-6-luna"}, {"id": "gpt-6-astra-2026-09-01"},
            {"id": "gpt-4o", "shutdown_date": "2000-01-01"}, {"id": "gpt-image-2"}, {"id": "made-up-model"}]})
        self.assertEqual({m["id"] for m in models}, {"gpt-6-luna", "gpt-6-astra-2026-09-01"})
        self.assertIn("none", next(m for m in models if m["id"] == "gpt-6-luna")["efforts"])

    def test_api_catalog_excludes_snapshots_without_structured_outputs(self):
        models = api_models({"data": [{"id": model} for model in
            ("gpt-4o-2024-05-13", "gpt-4o-2024-08-06", "gpt-4o", "gpt-4o-mini-2024-07-18")]})
        self.assertEqual({m["id"] for m in models}, {"gpt-4o-2024-08-06", "gpt-4o", "gpt-4o-mini-2024-07-18"})

    def test_structured_generation_respects_model_output_limits(self):
        limits = {"gpt-4o": 16384, "gpt-4o-mini-2024-07-18": 16384, "gpt-4.1": 32768}
        def transport(key, path, body=None):
            if path == "models":
                return {"data": [{"id": model} for model in limits]}
            self.assertLessEqual(body["max_output_tokens"], limits[body["model"]])
            self.assertEqual(body["text"]["format"]["type"], "json_schema")
            return self.api(key, path, body)
        self.service.transport = transport
        self.service.connect_api(self.session, KEY)
        for model in limits:
            with self.subTest(model=model):
                result = self.service.generate_json(self.session,
                    {"route": "openai_api", "model": model, "effort": "default"},
                    {"instructions": "Return JSON", "input": "Invented fixture", "schema": {"type": "object"}})
                self.assertEqual(result["actual_model"], model)

    def test_api_selection_reaches_responses_and_default_omits_reasoning(self):
        self.service.connect_api(self.session, KEY)
        job = self.wait_job(self.service.start_job(self.session, {"route": "openai_api", "model": "gpt-6-astra", "effort": "xhigh", "max_output_tokens": 4096}))
        self.assertEqual(job["status"], "completed")
        self.assertEqual(job["confirmed_effort"], "xhigh")
        body = self.api.calls[-1][2]
        self.assertEqual(body["model"], "gpt-6-astra")
        self.assertFalse(body["store"])
        self.assertEqual(body["max_output_tokens"], 4096)
        self.wait_job(self.service.start_job(self.session, {"route": "openai_api", "model": "gpt-4.1", "effort": "default"}))
        self.assertNotIn("reasoning", self.api.calls[-1][2])

    def test_invalid_selection_never_falls_back_or_sends_inference(self):
        self.service.connect_api(self.session, KEY)
        for model, effort in (("gpt-4.1", "xhigh"), ("missing", "low")):
            with self.assertRaises(AIError):
                self.service.start_job(self.session, {"route": "openai_api", "model": model, "effort": effort})
        self.assertFalse(any(path == "responses" for _, path, _ in self.api.calls))

    def test_incomplete_response_never_verifies(self):
        self.service.connect_api(self.session, KEY)
        self.api.status = "incomplete"
        job = self.wait_job(self.service.start_job(self.session, {"route": "openai_api", "model": "gpt-6-astra", "effort": "high"}))
        self.assertEqual(job["status"], "failed")
        self.assertEqual(job["error"]["code"], "incomplete")

    def test_api_test_rejects_model_or_effort_mismatch_and_accepts_dated_alias(self):
        self.service.connect_api(self.session, KEY)
        for actual, effort, expected in [("another-model", "high", "failed"),
                                         ("gpt-6-astra", "low", "failed"),
                                         ("gpt-6-astra-2026-09-01", "high", "completed")]:
            with self.subTest(actual=actual, effort=effort):
                def transport(key, path, body=None):
                    result = self.api(key, path, body)
                    if path == "responses":
                        result.update(model=actual, reasoning={"effort": effort})
                    return result
                self.service.transport = transport
                job = self.wait_job(self.service.start_job(self.session,
                    {"route": "openai_api", "model": "gpt-6-astra", "effort": "high"}))
                self.assertEqual(job["status"], expected)
                if expected == "failed":
                    self.assertEqual(job["error"]["code"], "selection_mismatch")
                    self.assertEqual(job["text"], "")

    def test_keys_are_not_returned_and_failed_replacement_preserves_old_key(self):
        self.service.connect_api(self.session, KEY)
        self.assertNotIn(KEY, json.dumps(self.service.status(self.session)))
        self.api.error = provider_error(401)
        with self.assertRaises(AIError):
            self.service.connect_api(self.session, "sk-invalid-placeholder-second-key")
        self.assertEqual(self.session.key, KEY)
        with self.assertRaises(AIError):
            self.service.catalog(self.session, "openai_api")
        self.assertIsNone(self.session.key)

    def test_codex_early_notifications_exact_selection_and_usage(self):
        self.service.connect_chatgpt(self.session)
        job = self.wait_job(self.service.start_job(self.session, {"route": "codex_chatgpt", "model": "gpt-6-astra", "effort": "xhigh"}))
        self.assertEqual(job["status"], "completed")
        self.assertEqual(job["text"], "Connection successful.")
        self.assertEqual(job["usage"]["total_tokens"], 7)
        self.assertFalse(any(method == "turn/interrupt" for method, _ in self.rpc.calls))
        config = next(p["config"] for m, p in self.rpc.calls if m == "thread/start")
        self.assertFalse(config["mcp_servers.example.enabled"])

    def test_codex_wrong_model_is_rejected_before_turn(self):
        self.service.connect_chatgpt(self.session)
        self.rpc.mismatch = True
        job = self.wait_job(self.service.start_job(self.session, {"route": "codex_chatgpt", "model": "gpt-6-astra", "effort": "xhigh"}))
        self.assertEqual(job["error"]["code"], "selection_mismatch")
        self.assertFalse(any(m == "turn/start" for m, _ in self.rpc.calls))

    def test_failed_codex_turn_and_account_switch_do_not_verify(self):
        self.service.connect_chatgpt(self.session)
        self.rpc.turn_status = "failed"
        job = self.wait_job(self.service.start_job(self.session, {"route": "codex_chatgpt", "model": "gpt-6-astra", "effort": "high"}))
        self.assertEqual(job["status"], "failed")
        self.rpc.email = "different@example.invalid"
        with self.assertRaises(AIError):
            self.service.catalog(self.session, "codex_chatgpt")
        self.assertFalse(self.session.chatgpt_enabled)

    def test_login_requires_matching_completion_not_existing_account(self):
        self.service.login(self.session)
        self.assertEqual(self.service.status(self.session)["login"]["login_id"], "login-1")
        self.assertEqual(self.service.login_status(self.session)["status"], "pending")
        self.rpc.emit("account/login/completed", {"loginId": "unrelated", "success": True})
        self.assertEqual(self.service.login_status(self.session)["status"], "pending")
        self.rpc.emit("account/login/completed", {"loginId": "login-1", "success": True})
        self.assertEqual(self.service.login_status(self.session)["status"], "completed")
        self.assertTrue(self.session.chatgpt_enabled)

    def test_reload_restores_job_and_expired_login_releases_owner(self):
        self.service.connect_api(self.session, KEY)
        job = self.wait_job(self.service.start_job(self.session, {"route": "openai_api", "model": "gpt-4.1", "effort": "default"}))
        self.assertEqual(self.service.status(self.session)["job"]["id"], job["id"])
        self.service.login(self.session)
        self.session.login["started"] -= 301
        self.assertEqual(self.service.login_status(self.session)["status"], "expired")
        self.assertIsNone(self.service.login_owner)

    def test_login_pending_blocks_inference_and_duplicate_login(self):
        self.service.connect_chatgpt(self.session)
        self.service.login(self.session)
        with self.assertRaises(AIError):
            self.service.start_job(self.session, {"route": "codex_chatgpt", "model": "gpt-6-astra", "effort": "xhigh"})
        with self.assertRaises(AIError):
            self.service.login(AISession())

    def test_cancel_disconnect_and_usage_buckets(self):
        self.service.login(self.session)
        self.service.cancel_login(self.session)
        self.assertIsNone(self.session.login)
        self.service.connect_chatgpt(self.session)
        self.assertEqual(self.service.usage(self.session)["buckets"][0]["limitId"], "codex")
        self.service.disconnect(self.session, "codex_chatgpt")
        self.assertFalse(self.session.chatgpt_enabled)
        self.assertFalse(any(m == "account/logout" for m, _ in self.rpc.calls))


class ControlledRPC(FakeRPC):
    """Independent synthetic turns whose completions the test controls."""
    def __init__(self):
        super().__init__()
        self.lock = threading.RLock()
        self.started = queue.Queue()
        self.turns = {}
        self.counter = 0
        self.automatic = False

    def subscribe(self):
        with self.lock:
            return super().subscribe()

    def unsubscribe(self, events):
        with self.lock:
            super().unsubscribe(events)

    def emit(self, method, params):
        with self.lock:
            super().emit(method, params)

    def call(self, method, params=None, **kwargs):
        if method == "thread/start":
            with self.lock:
                self.counter += 1
                thread_id = f"thread-{self.counter}"
                self.calls.append((method, params))
            return {"thread": {"id": thread_id}, "model": params["model"],
                    "reasoningEffort": params["config"]["model_reasoning_effort"]}
        if method == "turn/start":
            with self.lock:
                thread_id = params["threadId"]
                self.turns[thread_id] = params
                self.started.put(thread_id)
                if self.automatic:
                    self.complete(thread_id)
            return {"turn": {"id": "turn-" + thread_id}}
        return super().call(method, params, **kwargs)

    def complete(self, thread_id, status="completed"):
        self.emit("item/agentMessage/delta", {"threadId": thread_id, "delta": json.dumps({"thread": thread_id})})
        self.emit("thread/tokenUsage/updated", {"threadId": thread_id,
            "tokenUsage": {"last": {"inputTokens": 4, "outputTokens": 3, "totalTokens": 7}}})
        self.emit("turn/completed", {"threadId": thread_id,
            "turn": {"id": "turn-" + thread_id, "status": status}})

    def release_all(self):
        with self.lock:
            self.automatic = True
            for thread_id in self.turns:
                self.complete(thread_id)


class CountryRequestGroupTests(unittest.TestCase):
    def setUp(self):
        self.rpc = ControlledRPC()
        self.service = AIService(ROOT, rpc=self.rpc, transport=FakeAPI())
        self.session = AISession()
        self.service.connect_chatgpt(self.session)
        self.selection = {"route": "codex_chatgpt", "model": "gpt-6-astra", "effort": "low"}
        self.session.jobs["country-test"] = {"id": "country-test", "kind": "country",
            "status": "running", **self.selection}
        self.packet = {"route": "extract", "instructions": "Unchanged instructions",
            "input": '{"source":"Invented fixture"}', "schema": {"type": "object"}}

    def test_two_turns_overlap_third_waits_and_other_work_stays_exclusive(self):
        other = AISession()
        self.service.connect_chatgpt(other)
        with self.service.country_request_group(self.session, "country-test") as group:
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(self.service.generate_json, self.session, self.selection,
                            self.packet, country_group=group) for _ in range(3)]
                try:
                    first, second = self.rpc.started.get(timeout=3), self.rpc.started.get(timeout=3)
                    self.assertNotEqual(first, second)
                    with self.assertRaises(queue.Empty):
                        self.rpc.started.get(timeout=.1)
                    for operation in (
                            lambda: self.service.generate_json(other, self.selection, self.packet),
                            lambda: self.service.start_job(other, self.selection),
                            lambda: self.service.login(other)):
                        with self.assertRaises(AIError) as failure:
                            operation()
                        self.assertEqual(failure.exception.code, "busy")
                    self.rpc.complete(second)
                    third = self.rpc.started.get(timeout=3)
                    self.rpc.complete(first)
                    self.rpc.complete(third)
                    results = [future.result(timeout=3) for future in futures]
                    self.assertEqual({json.loads(result["text"])["thread"] for result in results}, {first, second, third})
                    self.assertEqual({result["request_id"] for result in results}, {"turn-" + tid for tid in (first, second, third)})
                    for turn in self.rpc.turns.values():
                        self.assertEqual(turn["input"], [{"type": "text", "text": self.packet["input"]}])
                        self.assertEqual(turn["outputSchema"], self.packet["schema"])
                    starts = [params for method, params in self.rpc.calls if method == "thread/start"]
                    self.assertTrue(all(row["baseInstructions"] == self.packet["instructions"] for row in starts))
                    self.assertTrue(self.service.chat_lock.locked())
                finally:
                    self.rpc.release_all()
        self.assertFalse(self.service.chat_lock.locked())

    def test_group_rejects_wrong_owner_selection_and_closed_tokens(self):
        with self.assertRaises(AIError):
            with self.service.country_request_group(self.session, "missing-country"):
                pass
        with self.service.country_request_group(self.session, "country-test") as group:
            wrong_service = AIService(ROOT, rpc=self.rpc, transport=FakeAPI())
            for service, session, selection in (
                    (self.service, AISession(), self.selection),
                    (self.service, self.session, {**self.selection, "effort": "high"}),
                    (wrong_service, self.session, self.selection)):
                with self.assertRaises(AIError):
                    service.generate_json(session, selection, self.packet, country_group=group)
            with self.assertRaises(AIError):
                with self.service.country_request_group(self.session, "country-test"):
                    pass
        with self.assertRaises(AIError):
            self.service.generate_json(self.session, self.selection, self.packet, country_group=group)
        self.assertEqual(self.rpc.counter, 0)

    def test_group_exit_waits_for_live_turn_and_rejects_new_requests(self):
        context = self.service.country_request_group(self.session, "country-test")
        group = context.__enter__()
        exited, errors = threading.Event(), []
        def close():
            try:
                context.__exit__(None, None, None)
            except BaseException as exc:
                errors.append(exc)
            finally:
                exited.set()
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(self.service.generate_json, self.session, self.selection,
                       self.packet, country_group=group) for _ in range(3)]
            closer = None
            try:
                first, second = self.rpc.started.get(timeout=3), self.rpc.started.get(timeout=3)
                with self.assertRaises(queue.Empty):
                    self.rpc.started.get(timeout=.1)
                closer = threading.Thread(target=close)
                closer.start()
                self.assertFalse(exited.wait(.1))
                self.assertTrue(self.service.chat_lock.locked())
                with self.assertRaises(AIError):
                    self.service.generate_json(self.session, self.selection, self.packet, country_group=group)
                self.rpc.complete(first)
                self.assertFalse(exited.wait(.1))
                self.rpc.complete(second)
                results, rejected = [], []
                for future in futures:
                    try:
                        results.append(json.loads(future.result(timeout=3)["text"])["thread"])
                    except AIError as exc:
                        rejected.append(exc.code)
                self.assertEqual(set(results), {first, second})
                self.assertEqual(rejected, ["country_group"])
                self.assertTrue(exited.wait(3))
                self.assertEqual(errors, [])
                self.assertFalse(self.service.chat_lock.locked())
            finally:
                self.rpc.release_all()
                if closer:
                    closer.join(3)
                else:
                    context.__exit__(None, None, None)

    def test_failed_turn_releases_capacity_and_api_group_does_not_lock_chatgpt(self):
        with self.service.country_request_group(self.session, "country-test") as group:
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(self.service.generate_json, self.session, self.selection,
                            self.packet, country_group=group) for _ in range(3)]
                try:
                    first, second = self.rpc.started.get(timeout=3), self.rpc.started.get(timeout=3)
                    self.rpc.complete(first, "failed")
                    third = self.rpc.started.get(timeout=3)
                    self.rpc.complete(second)
                    self.rpc.complete(third)
                    failures = []
                    for future in futures:
                        try:
                            future.result(timeout=3)
                        except AIError as exc:
                            failures.append(exc.code)
                    self.assertEqual(failures, ["turn_failed"])
                finally:
                    self.rpc.release_all()
        self.session.jobs["country-test"]["status"] = "completed"
        self.service.connect_api(self.session, KEY)
        api_selection = {**self.selection, "route": "openai_api"}
        self.session.jobs["api-country"] = {"id": "api-country", "kind": "country",
            "status": "running", **api_selection}
        with self.service.country_request_group(self.session, "api-country") as group:
            self.assertFalse(self.service.chat_lock.locked())
            result = self.service.generate_json(self.session, api_selection, self.packet, country_group=group)
            self.assertEqual(result["actual_model"], api_selection["model"])


class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = workspace_test_directory()
        folder = cls.temp.__enter__()
        cls.server = LocalServer(ROOT, 0, AIService(ROOT, rpc=FakeRPC(), transport=FakeAPI()),
                                 profiles_path=folder / "workspace.sqlite3")
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.temp.__exit__(None, None, None)

    def request(self, path, body=None, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        data = json.dumps(body) if body is not None else None
        conn.request("POST" if body is not None else "GET", path, body=data, headers=headers or {})
        result = conn.getresponse()
        status, output, response_headers = result.status, result.read(), dict(result.getheaders())
        conn.close()
        return status, output, response_headers

    def bootstrap(self):
        status, data, headers = self.request("/api/ai/session")
        self.assertEqual(status, 200)
        return {"Cookie": headers["Set-Cookie"].split(";")[0], "X-PolicyTracker-CSRF": json.loads(data)["csrf"], "Content-Type": "application/json"}

    def test_origin_csrf_host_and_private_files(self):
        headers = self.bootstrap()
        self.assertEqual(self.request("/api/ai/api-key", {"key": KEY}, {**headers, "Origin": "https://evil.invalid"})[0], 403)
        self.assertEqual(self.request("/api/ai/api-key", {"key": KEY}, {"Cookie": headers["Cookie"]})[0], 403)
        self.assertEqual(self.request("/api/ai/status", headers={**headers, "Host": "evil.invalid"})[0], 403)
        status, _, _ = self.request("/design/prototype/?page=kazakhstanDemo", headers={
            "Origin": "https://embedded-browser.invalid", "Sec-Fetch-Site": "cross-site"})
        self.assertEqual(status, 200)  # UI navigation may be embedded; session/data routes remain same-origin.
        self.assertEqual(self.request("/api/ai/session", headers={
            "Origin": "https://embedded-browser.invalid", "Sec-Fetch-Site": "cross-site"})[0], 403)
        for path in ("/.git/config", "/src/policytracker/ai_runtime.py", "/tmp/ai-start-diagnostic.log", "/design/prototype/../../.env",
                     "/data/local-profiles/workspace.sqlite3", "/data/manifests/corpus.json",
                     "/data/sources/Albania/NAP/Albania%20National%20Adaptation%20Plan%20-%20aeb6b3/Current.pdf"):
            self.assertEqual(self.request(path)[0], 404)

    def test_local_inventory_requires_session_and_reports_only_availability(self):
        self.assertEqual(self.request("/api/ai/inventory")[0], 401)
        expected = {"registered_count": 1, "available_count": 0,
                    "documents": [{"document_id": "missing", "available": False, "status": "missing", "message": "Original PDF is not installed."}]}
        with patch("policytracker.local_server.local_availability", return_value=expected) as availability:
            status, body, _ = self.request("/api/ai/inventory", headers=self.bootstrap())
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body), expected)
        availability.assert_called_once_with(ROOT)

    def test_ui_assets_and_catalogs_are_served_at_their_repository_paths(self):
        status, html, _ = self.request("/design/prototype/")
        self.assertEqual(status, 200)
        self.assertIn(b'<script type="module" src="app.js">', html)
        for folder in ("design/prototype", "integrations/javascript", "integrations/fixtures", "examples/v2"):
            for path in (ROOT / folder).iterdir():
                if path.suffix not in (".js", ".mjs", ".css", ".json"):
                    continue
                with self.subTest(path=path.name):
                    status, body, headers = self.request("/" + path.relative_to(ROOT).as_posix())
                    self.assertEqual(status, 200)
                    self.assertEqual(body, path.read_bytes())
                    if path.suffix in (".js", ".mjs"):
                        self.assertIn("javascript", {key.lower(): value for key, value in headers.items()}["content-type"])

    def test_redirect_body_is_bounded_and_connection_remains_usable(self):
        conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=3)
        try:
            conn.request('GET', '/')
            response = conn.getresponse()
            self.assertEqual(response.status, 302)
            self.assertEqual(response.getheader('Content-Length'), '0')
            self.assertEqual(response.read(), b'')
            connection = conn.sock
            self.assertIsNotNone(connection)
            conn.request('GET', '/api/ai/session')
            response = conn.getresponse()
            self.assertEqual(response.status, 200)
            self.assertIn('csrf', json.loads(response.read()))
            self.assertIs(conn.sock, connection)
        finally:
            conn.close()

    def test_credentials_and_jobs_are_isolated_per_browser_session(self):
        a, b = self.bootstrap(), self.bootstrap()
        status, data, _ = self.request("/api/ai/api-key", {"key": KEY}, a)
        self.assertEqual(status, 200)
        self.assertNotIn(KEY.encode(), data)
        self.assertFalse(json.loads(self.request("/api/ai/status", headers=b)[1])["api"]["connected"])
        status, data, _ = self.request("/api/ai/jobs", {"route": "openai_api", "model": "gpt-4.1", "effort": "default"}, a)
        self.assertEqual(status, 200)
        self.assertEqual(self.request("/api/ai/jobs/" + json.loads(data)["id"], headers=b)[0], 404)

    def test_disconnect_blocks_new_calls(self):
        headers = self.bootstrap()
        self.request("/api/ai/api-key", {"key": KEY}, headers)
        self.assertEqual(self.request("/api/ai/disconnect", {"route": "openai_api"}, headers)[0], 200)
        self.assertEqual(self.request("/api/ai/jobs", {"route": "openai_api", "model": "gpt-4.1", "effort": "default"}, headers)[0], 401)

    def test_second_server_cannot_share_the_listener_port(self):
        with patch("policytracker.local_server.CountryRunner") as worker:
            with self.assertRaises(OSError):
                LocalServer(ROOT, self.server.server_port, AIService(ROOT, rpc=FakeRPC(), transport=FakeAPI()),
                            profiles_path=self.server.profiles_path)
            worker.assert_not_called()  # A failed launch must not recover or change active jobs.


if __name__ == "__main__":
    unittest.main()

"""Allowlisted loopback UI and session-bound AI endpoints."""
from __future__ import annotations

import argparse
import json
import secrets
import socket
import sqlite3
import threading
import time
from http.cookies import SimpleCookie
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

from .ai_runtime import AIError, AISession, AIService
from .profiles import ProfileStore, register_csv
from .inventory import COUNTRIES, local_availability, register_document
from .country_runs import CountryRunner


class LocalServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def server_bind(self):
        # Windows SO_REUSEADDR can let an old preview and the AI server both
        # bind a port, sending browser requests to the wrong process.
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()

    def __init__(self, root, port=8765, service=None, profiles_path=None):
        self.root = Path(root).resolve()
        self.service = service or AIService(root)
        self.profiles_path = Path(profiles_path) if profiles_path else self.root / "data/local-profiles/workspace.sqlite3"
        self.sessions = {}
        self.session_lock = threading.Lock()
        self.countries = None
        super().__init__(("127.0.0.1", port), Handler)
        # Acquire the listener before recovering persisted jobs. A second preview
        # on an occupied port must not mark the running server's jobs as stopped.
        try:
            self.countries = CountryRunner(self.root, self.profiles_path, self.service)
        except Exception:
            self.server_close()
            raise

    def server_close(self):
        if self.countries is not None:
            self.countries.stop_event.set()
        self.service.rpc.close()
        super().server_close()


class Handler(SimpleHTTPRequestHandler):
    # Keep large archives/assets on a reusable connection; do not close the
    # server side immediately after enqueueing a large response on Windows.
    protocol_version = "HTTP/1.1"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(args[2].root), **kwargs)

    def setup(self):
        super().setup()
        self.connection.settimeout(15)

    def log_message(self, *args):
        pass  # Never log auth URLs, keys, cookies or request payloads.

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        super().end_headers()

    def allowed_local_host(self):
        port = self.server.server_port
        hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        return self.headers.get("Host") in hosts

    def allowed_origin(self):
        host = self.headers.get("Host")
        return (self.allowed_local_host() and self.headers.get("Sec-Fetch-Site") != "cross-site"
                and self.headers.get("Origin", f"http://{host}") == f"http://{host}")

    def json_response(self, data, status=200, cookie=None):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        if cookie:
            self.send_header("Set-Cookie", f"pt_session={cookie}; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800")
        self.end_headers()
        self.wfile.write(body)

    def session(self, create=False):
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get("Cookie", ""))
            sid = cookie["pt_session"].value if "pt_session" in cookie else None
        except Exception:
            sid = None
        with self.server.session_lock:
            now = time.time()
            for key, value in list(self.server.sessions.items()):
                if value["expires"] < now and not any(j["status"] in ("queued", "running") for j in value["ai"].jobs.values()):
                    del self.server.sessions[key]
            session = self.server.sessions.get(sid)
            if session and session["expires"] < now:
                raise AIError("session_expired", "Reload the page to start a new connection session.", 401)
            if not session and create:
                if len(self.server.sessions) >= 64:
                    raise AIError("sessions", "Too many local sessions. Restart the local server.", 429)
                sid = secrets.token_urlsafe(32)
                session = {"csrf": secrets.token_urlsafe(32), "ai": AISession(), "expires": now + 28800}
                self.server.sessions[sid] = session
            if not session:
                raise AIError("session_expired", "Reload the page to reconnect.", 401)
        return sid, session

    def do_GET(self):
        path = urlsplit(self.path).path
        # Static UI assets contain no session data. Allow navigation from the
        # exact loopback host even when an embedded browser supplies a different
        # Origin; keep data and AI routes protected by the strict origin check.
        protected = path.startswith("/api/")
        if not self.allowed_local_host() or (protected and not self.allowed_origin()):
            self.json_response({"error": {"code": "origin", "message": "Use the local PolicyTracker address."}}, 403)
            return
        if path.startswith("/api/ai/"):
            self.api(path, False)
        elif path == "/api/profiles" or path.startswith("/api/profiles/"):
            self.profiles(path)
        else:
            super().do_GET()

    def do_HEAD(self):
        path = urlsplit(self.path).path
        if not self.allowed_local_host() or path.startswith("/api/"):
            self.send_error(403)
            return
        super().do_HEAD()

    def profiles(self, path):
        """Read-only same-origin profile data; selection writes use the AI session route."""
        country = path.removeprefix("/api/profiles/") if path != "/api/profiles" else None
        if country and country not in COUNTRIES.values():
            return self.json_response({"error": "Unknown country"}, 404)
        query = parse_qs(urlsplit(self.path).query)
        synthetic = query.get("synthetic") == ["1"]
        if not self.server.profiles_path.exists():
            return self.json_response({"countries": []} if not country else {"profile": None, "history": [], "selection": None})
        try:
            with ProfileStore(self.server.root, self.server.profiles_path) as store:
                result = store.country(country, synthetic) if country else {"countries": store.summaries()}
                if country and (query.get("version") or query.get("format") == ["csv"]):
                    version = query.get("version", [None])[0]
                    if not version or not store.db.execute("SELECT 1 FROM profiles WHERE id=?", (version,)).fetchone():
                        return self.json_response({"error": "Select a saved profile version to export."}, 404)
                    profile = store.profile(version)
                    if profile["country_code"] != country or profile["synthetic"] != synthetic:
                        return self.json_response({"error": "Profile is outside this country or scope."}, 404)
                    result["profile"] = profile
                if country and query.get("format") == ["csv"]:
                    body = register_csv(profile).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "text/csv; charset=utf-8")
                    self.send_header("Content-Disposition", f'attachment; filename="{country}-register.csv"')
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                    return
                if country and result.get("profile") and query.get("archive") == ["1"]:
                    profile = result["profile"]
                    archive = {"validation_context": {p: store.get(h).decode("utf-8") for p, h in profile["archive"]["validation_context"].items()}}
                    if profile.get("generation"):
                        generation = profile["generation"]
                        archive["method"] = {p: store.get(h).decode("utf-8") for p, h in generation["method"].items()}
                        archive["reused_method_files"] = {h: raw.decode("utf-8") for h, raw in store.reused_method_files(generation).items()}
                        archive["steps"] = []
                        for step in generation["steps"]:
                            saved = json.loads(store.get(step["result_hash"]))
                            archive["steps"].append({"step": step["step"], "request": json.loads(store.get(saved["request_hash"])),
                                                     "response": json.loads(store.get(saved["response_hash"])),
                                                     **({"normalization": saved["normalization"]} if saved.get("normalization") else {})})
                        archive["attempts"] = [{**attempt,
                            "request": json.loads(store.get(attempt["request_hash"])),
                            "response": json.loads(store.get(attempt["response_hash"])) if attempt["response_hash"] else None}
                            for attempt in generation.get("attempts", [])]
                    profile["generation_archive"] = archive
            self.json_response(result)
        except (ValueError, sqlite3.DatabaseError):
            self.json_response({"error": "The local profile archive failed its integrity check."}, 503)

    def do_POST(self):
        # Consume a bounded request body before an early 403. On Windows,
        # closing with unread POST bytes can reset the socket before the caller
        # receives the rejection. Reading bytes does not authorize the request.
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        route = urlsplit(self.path).path
        limit = 35_000_000 if route == "/api/ai/documents/register" else 2_000_000 if route == "/api/ai/method" else 100000
        if not 0 < length <= limit:
            self.close_connection = True
            return self.json_response({"error": {"code": "request_size", "message": "The request is too large or empty."}}, 413)
        self._post_body = self.rfile.read(length)
        if not self.allowed_origin():
            self.json_response({"error": {"code": "origin", "message": "Cross-origin requests are blocked."}}, 403)
            return
        self.api(urlsplit(self.path).path, True)

    def api(self, path, post):
        try:
            sid, session = self.session(create=path == "/api/ai/session" and not post)
            ai, service = session["ai"], self.server.service
            body = {}
            if post:
                if not secrets.compare_digest(self.headers.get("X-PolicyTracker-CSRF", ""), session["csrf"]):
                    raise AIError("csrf", "Reload the page before continuing.", 403)
                if self.headers.get_content_type() != "application/json":
                    raise AIError("content_type", "Expected a JSON request.", 415)
                try:
                    body = json.loads(self._post_body)
                except (ValueError, UnicodeError):
                    raise AIError("json", "The request contains invalid JSON.") from None
                if not isinstance(body, dict):
                    raise AIError("json", "Expected a JSON object.")
            if not post and path == "/api/ai/session":
                return self.json_response({"csrf": session["csrf"]}, cookie=sid)
            if not post and path == "/api/ai/status":
                result = service.status(ai)
            elif not post and path == "/api/ai/inventory":
                with self.server.countries.lock:
                    result = local_availability(self.server.root)
            elif path == "/api/ai/settings":
                from .settings import settings_view, apply_settings
                if post:
                    with self.server.countries.lock:
                        if self.server.countries.active: raise AIError("busy", "Settings can be saved after the current run finishes", 409)
                        result = apply_settings(self.server.root, body)
                else:
                    result = settings_view(self.server.root)
            elif path == "/api/ai/method":
                from .settings import method_module, apply_pack
                if post:
                    with self.server.countries.lock:
                        if self.server.countries.active: raise AIError("busy", "Method changes apply after the current run finishes", 409)
                        result = apply_pack(self.server.root, body)
                else:
                    result = method_module(self.server.root).pack()
            elif post and path == "/api/ai/documents/register":
                with self.server.countries.lock:
                    if self.server.countries.active: raise AIError("busy", "Documents can be added after the current run finishes", 409)
                    result = register_document(self.server.root, body)
            elif post and path == "/api/ai/publication":
                result = self.server.countries.moderate(body.get("id", ""), body.get("published"))
            elif not post and path.startswith("/api/ai/countries/"):
                result = self.server.countries.status(path.rsplit("/", 1)[-1])
            elif post and path == "/api/ai/preparation":
                result = self.server.countries.preparation(body)
            elif not post and path.startswith("/api/ai/preparation/"):
                parts = path.split("/")
                if len(parts) != 7 or parts[-1] != "render" or not parts[-2].isdigit():
                    raise AIError("not_found", "Page preview not found", 404)
                raw = self.server.countries.preparation_render(unquote(parts[-3]), int(parts[-2]))
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
                return
            elif post and path == "/api/ai/country-runs":
                result = self.server.countries.start(ai, body)
            elif not post and path == "/api/ai/analyses":
                result = self.server.countries.operations()
            elif post and path == "/api/ai/analyses":
                result = self.server.countries.start(ai, {"operation": body})
            elif not post and path.startswith("/api/ai/analyses/"):
                result = self.server.countries.operation_result(path.rsplit("/", 1)[-1])
                if parse_qs(urlsplit(self.path).query).get("archive") == ["1"]:
                    with ProfileStore(self.server.root, self.server.profiles_path) as store:
                        result["generation_archive"] = {"method": {p: store.get(h).decode("utf-8") for p, h in result["generation"]["method"].items()},
                            "reused_method_files": {h: raw.decode("utf-8") for h, raw in store.reused_method_files(result["generation"]).items()},
                            "requests_and_responses": [{"step": step["step"], **{key: json.loads(store.get(step[key])) for key in ("request_hash", "response_hash")},
                                **({"normalization": step["normalization"]} if step.get("normalization") else {})} for step in result["generation"]["step_receipts"]],
                            "complete_extraction": json.loads(store.get(result["full_extraction_hash"]))}
                        result["generation_archive"]["attempts"] = [{**attempt,
                            "request": json.loads(store.get(attempt["request_hash"])),
                            "response": json.loads(store.get(attempt["response_hash"])) if attempt["response_hash"] else None}
                            for attempt in result["generation"].get("attempts", [])]
            elif not post and path == "/api/ai/translations":
                versions = []
                with ProfileStore(self.server.root, self.server.profiles_path) as store:
                    for row in store.db.execute("SELECT id FROM profiles"):
                        p = store.profile(row[0])
                        if not p["synthetic"] and p["published"]:
                            versions.extend({"document_id": d["document_id"], "version": p["id"], "country": p["country_code"], "kind": "profile", "created_at": p["created_at"]} for d in p["sources"])
                for job in self.server.countries.operations()["runs"]:
                    if job["status"] == "completed" and not job.get("synthetic") and job.get("published", True):
                        versions.extend({"document_id": d, "version": job["id"], "kind": "analysis", "created_at": job["created_at"]} for d in job["document_ids"])
                result = {"versions": sorted(versions, key=lambda v: v["created_at"], reverse=True)}
            elif not post and path.startswith("/api/ai/documents/"):
                parts = path.split("/")
                if len(parts) != 6:
                    raise AIError("not_found", "Document not found", 404)
                version, doc_id = parts[-2:]
                with ProfileStore(self.server.root, self.server.profiles_path) as store:
                    if version == "current":
                        from .engineering import read_json
                        from .profiles import sha
                        doc = next((d for d in read_json(self.server.root / "data/manifests/corpus.json")["documents"] if d["document_id"] == doc_id), None)
                        if not doc:
                            raise AIError("not_found", "Unknown registered document", 404)
                        source = (self.server.root / doc["relative_path"]).resolve()
                        if not source.is_relative_to(self.server.root / "data/sources"):
                            raise AIError("source", "Invalid source location", 404)
                        raw = source.read_bytes()
                        if sha(raw) != doc["sha256"]:
                            raise AIError("source_changed", "Source changed; refresh the inventory", 409)
                    else:
                        saved = self.server.countries.operation_result(version) if version.startswith("analysis-") else store.profile(version)
                        doc = next((d for d in saved["sources"] if d["document_id"] == doc_id), None)
                        if not doc:
                            raise AIError("not_found", "Document is outside this saved version", 404)
                        raw = store.get(doc["sha256"])
                    if not raw.startswith(b"%PDF-"):
                        raise AIError("source", "This synthetic source is not a PDF", 404)
                self.send_response(200)
                self.send_header("Content-Type", "application/pdf")
                disposition = "inline" if parse_qs(urlsplit(self.path).query).get("inline") == ["1"] else "attachment"
                self.send_header("Content-Disposition", f'{disposition}; filename="source-original.pdf"')
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
                return
            elif post and path.startswith("/api/ai/profile-selection/"):
                country = path.rsplit("/", 1)[-1]
                if country not in COUNTRIES.values() or type(body.get("revision")) is not int or type(body.get("synthetic", False)) is not bool:
                    raise AIError("input", "Choose a country and the current selection revision.")
                try:
                    with ProfileStore(self.server.root, self.server.profiles_path) as store:
                        result = store.select(country, body.get("profile_id"), body["revision"], body.get("synthetic", False))
                except ValueError as exc:
                    raise AIError("selection", str(exc), 409) from None
            elif post and path.startswith("/api/ai/country-runs/"):
                parts = path.split("/")
                if len(parts) != 6 or parts[-1] not in ("stop", "resume"):
                    raise AIError("not_found", "Country action not found.", 404)
                result = (self.server.countries.stop(parts[-2]) if parts[-1] == "stop" else
                          self.server.countries.resume(ai, parts[-2]))
            elif not post and path == "/api/ai/usage":
                result = service.usage(ai)
            elif not post and path == "/api/ai/login/status":
                result = service.login_status(ai)
            elif not post and path.startswith("/api/ai/jobs/"):
                result = ai.jobs.get(path.rsplit("/", 1)[-1])
                if result is None:
                    raise AIError("not_found", "Request not found in this session.", 404)
                result = dict(result)
            elif post and path == "/api/ai/chatgpt/connect":
                result = service.connect_chatgpt(ai)
            elif post and path == "/api/ai/login/start":
                result = service.login(ai)
            elif post and path == "/api/ai/login/cancel":
                result = service.cancel_login(ai)
            elif post and path == "/api/ai/api-key":
                result = service.connect_api(ai, body.get("key"))
            elif post and path in ("/api/ai/models", "/api/ai/disconnect"):
                route = body.get("route")
                if route not in ("codex_chatgpt", "openai_api"):
                    raise AIError("route", "Choose a supported usage route.")
                result = service.catalog(ai, route) if path.endswith("models") else service.disconnect(ai, route)
            elif post and path == "/api/ai/jobs":
                result = service.start_job(ai, body)
            else:
                raise AIError("not_found", "Endpoint not found.", 404)
            self.json_response(result)
        except AIError as exc:
            self.json_response({"error": {"code": exc.code, "message": str(exc)}}, exc.status)
        except (ValueError, OSError) as exc:
            self.json_response({"error": {"code": "input", "message": str(exc)}}, 400)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass
        except Exception:
            self.json_response({"error": {"code": "internal", "message": "The local server could not complete this request."}}, 500)

    def send_head(self):
        route = unquote(urlsplit(self.path).path)
        if route == "/":
            self.send_response(302)
            self.send_header("Location", "/design/prototype/")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return None
        root = self.server.root
        target = (root / route.lstrip("/")).resolve()
        allowed = [root / p for p in ("design/prototype", "integrations/javascript", "integrations/fixtures", "examples/v2")]
        if not any(target.is_relative_to(p) for p in allowed):
            self.send_error(404)
            return None
        return super().send_head()

    def list_directory(self, path):
        self.send_error(404)
        return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--profiles-path", type=Path, help="Separate local database for an isolated preview")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    server = LocalServer(root, args.port, profiles_path=args.profiles_path)
    print(f"PolicyTracker: http://127.0.0.1:{server.server_port}/design/prototype/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

"""Read capabilities without accessing or printing credentials or account identity."""
import json
import queue
import shutil
import subprocess
import threading
from pathlib import Path


def main():
    events = queue.Queue()
    log_path = Path("tmp/provider-preflight.stderr.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    error_log = log_path.open("w", encoding="utf-8")
    proc = subprocess.Popen([shutil.which("codex"), "app-server", "--listen", "stdio://"],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=error_log,
                            text=True, encoding="utf-8", creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    def consume():
        for line in proc.stdout:
            try:
                events.put(json.loads(line))
            except json.JSONDecodeError:
                pass
    threading.Thread(target=consume, daemon=True).start()
    def request(i, method, params):
        proc.stdin.write(json.dumps({"id": i, "method": method, "params": params}) + "\n")
        proc.stdin.flush()
        while True:
            event = events.get(timeout=30)
            if event.get("id") == i:
                if "error" in event:
                    raise RuntimeError(event["error"])
                return event["result"]
    try:
        request(1, "initialize", {"clientInfo": {"name": "policytracker_preflight", "title": "PolicyTracker preflight", "version": "0.1.0"}})
        proc.stdin.write('{"method":"initialized"}\n')
        proc.stdin.flush()
        account = request(2, "account/read", {"refreshToken": False})
        models = request(3, "model/list", {"includeHidden": False, "limit": 100})
        safe = {"auth_type": (account.get("account") or {}).get("type"),
                "models": [{k: m.get(k) for k in ["id", "model", "displayName", "supportedReasoningEfforts"]}
                           for m in models.get("data", [])],
                "next_cursor": models.get("nextCursor"), "inference_verified": False}
        path = Path("data/manifests/provider-preflight.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(safe, indent=2), encoding="utf-8")
        print(json.dumps(safe, indent=2))
    except queue.Empty:
        print(json.dumps({"status": "initialization_timeout", "inference_verified": False,
                          "process_exit_code": proc.poll(), "diagnostic_log": str(log_path)}))
    finally:
        proc.terminate()
        proc.wait(timeout=10)
        error_log.close()


if __name__ == "__main__":
    main()

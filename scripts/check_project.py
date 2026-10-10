"""One offline check command for repository paths, contracts and both test suites."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sqlite3
import subprocess
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def check_web_paths(root: Path) -> None:
    """Check the UI's local HTML assets, module imports and literal JSON loads."""
    checked = 0
    for folder in ("design/prototype", "integrations/javascript"):
        for path in (root / folder).iterdir():
            if path.suffix not in (".html", ".js", ".mjs"):
                continue
            pattern = (r'''(?:src|href)=["']([^"']+)["']''' if path.suffix == ".html" else
                       r'''(?:\bfrom\s*|\bimport\s*|\bload\()\s*["'](\.{1,2}/[^"']+)["']''')
            for reference in re.findall(pattern, path.read_text(encoding="utf-8")):
                url = urlsplit(reference)
                if url.scheme or url.netloc or not url.path:
                    continue
                target = (path.parent / unquote(url.path)).resolve()
                if not target.is_relative_to(root.resolve()) or not target.is_file():
                    raise ValueError(f"Broken UI reference: {path.relative_to(root)} -> {reference}")
                checked += 1
    print(f"Local HTML assets, module imports and JSON loads resolved: {checked} references.", flush=True)


def check_paths(root: Path, require_local: bool = False) -> None:
    from policytracker.inventory import COUNTRIES

    manifest = json.loads((root / "data/manifests/corpus.json").read_text(encoding="utf-8"))
    sources = root / "data/sources"
    local = sources.is_dir()
    if require_local and not local:
        raise ValueError("Local sources are missing: restore country folders into data/sources/.")
    misplaced = [name for name in COUNTRIES if (root / name).exists()]
    if misplaced:
        raise ValueError("Country folders belong in data/sources/: " + ", ".join(misplaced))
    paths, ids = set(), set()
    for doc in manifest["documents"]:
        relative = PurePosixPath(doc["relative_path"])
        expected = ("data", "sources", doc["country_folder"])
        if (relative.parts[:3] != expected or ".." in relative.parts
                or "\\" in str(relative) or relative.suffix.lower() != ".pdf"):
            raise ValueError(f"Invalid source path: {relative}")
        if COUNTRIES.get(doc["country_folder"]) != doc["country_code"]:
            raise ValueError(f"Country mapping differs: {relative}")
        if str(relative) in paths or doc["document_id"] in ids:
            raise ValueError(f"Duplicate source path or document ID: {relative}")
        paths.add(str(relative))
        ids.add(doc["document_id"])
        if local:
            path = (root / relative).resolve()
            if not path.is_relative_to(sources.resolve()) or not path.is_file():
                raise ValueError(f"Missing or misplaced source: {relative}")
            if hashlib.sha256(path.read_bytes()).hexdigest() != doc["sha256"]:
                raise ValueError(f"Source differs from inventory: {relative}. Refresh the inventory.")
    if local:
        actual = {p.relative_to(root).as_posix() for p in sources.rglob("*")
                  if p.is_file() and p.suffix.lower() == ".pdf"}
        if actual != paths:
            raise ValueError("Source files and inventory differ. Refresh the inventory; check country folder names.")
        print(f"Source paths and SHA-256 verified: {len(paths)} PDFs.", flush=True)
    else:
        print(f"Manifest paths checked: {len(paths)}. Local source hashes SKIPPED (no data/sources/).", flush=True)

    database = root / "data/local-profiles/workspace.sqlite3"
    if database.exists():
        with sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True) as connection:
            if connection.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
                raise ValueError("Local profile database failed its integrity check.")
            if connection.execute("PRAGMA foreign_key_check").fetchall():
                raise ValueError("Local profile database contains broken references.")
        print("Local profile database integrity and references passed (read-only).", flush=True)
    else:
        print("Local profile database check SKIPPED (no saved profiles yet).", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-data", action="store_true", help="Require source files as well as checking code")
    parser.add_argument("--node", default="node", help="Node 24+ executable (default: node on PATH)")
    args = parser.parse_args()
    if sys.version_info < (3, 10):
        print("Use Python 3.10+ from the project environment.", file=sys.stderr)
        return 1
    node = shutil.which(args.node)
    if not node:
        print("Node 24+ is required. Put it on PATH or pass --node <executable>.", file=sys.stderr)
        return 1
    version = subprocess.check_output([node, "--version"], text=True).strip()
    if int(version.lstrip("v").split(".")[0]) < 24:
        print(f"Found Node {version}; use Node 24+ or pass --node <executable>.", file=sys.stderr)
        return 1

    failures = []
    try:
        check_paths(ROOT, args.local_data)
        check_web_paths(ROOT)
    except (ValueError, KeyError, OSError, sqlite3.DatabaseError) as exc:
        print(f"FAIL paths/data: {exc}", flush=True)
        failures.append("paths/data")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src") + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    env["PYTHONUTF8"] = "1"
    checks = [(name, [sys.executable, str(ROOT / "scripts" / f"{name}.py")]) for name in (
        "check_contracts", "check_v2_pack", "check_integration_contracts", "check_operations", "check_methodology", "check_report_experience")]
    checks.append(("Python tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]))
    checks.append(("JavaScript tests", [node, "--test", "--test-isolation=none",
                   *[str(p) for p in sorted((ROOT / "tests").glob("*.test.mjs"))]]))
    for label, command in checks:
        print(f"\nRunning {label}...", flush=True)
        if subprocess.run(command, cwd=ROOT, env=env).returncode:
            failures.append(label)
    print("\nFAILED: " + ", ".join(failures) if failures else "\nAll offline project checks passed. No live model calls.")
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())

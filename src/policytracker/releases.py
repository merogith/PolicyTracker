"""Local reference release registry, not a hosted authorization service.

Role arguments represent a trusted calling application. An HTTP wrapper MUST
derive them from verified sessions, never from user-supplied request bodies.
"""
from __future__ import annotations
import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone


def utcnow():
    return datetime.now(timezone.utc).isoformat()


class ReleaseRegistry:
    def __init__(self, path):
        self.db = sqlite3.connect(path, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS runs (
          sequence INTEGER PRIMARY KEY AUTOINCREMENT,
          id TEXT NOT NULL UNIQUE, kind TEXT NOT NULL,
          country TEXT, owner TEXT NOT NULL, started_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS reports (
          sequence INTEGER PRIMARY KEY AUTOINCREMENT,
          id TEXT NOT NULL UNIQUE,
          kind TEXT NOT NULL CHECK(kind IN ('prime_candidate','ad_hoc','comparison')),
          country TEXT,
          owner TEXT NOT NULL,
          run_id TEXT NOT NULL UNIQUE REFERENCES runs(id),
          artifact_json TEXT NOT NULL,
          artifact_hash TEXT NOT NULL,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS approvals (
          report_id TEXT PRIMARY KEY REFERENCES reports(id),
          reviewer TEXT NOT NULL, receipt_json TEXT NOT NULL, approved_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS primes (
          country TEXT PRIMARY KEY,
          report_id TEXT NOT NULL REFERENCES reports(id),
          mode TEXT NOT NULL CHECK(mode IN ('pinned','latest_approved')),
          revision INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS assignments (
          id INTEGER PRIMARY KEY AUTOINCREMENT, country TEXT NOT NULL,
          previous_report TEXT, report_id TEXT NOT NULL REFERENCES reports(id),
          actor TEXT NOT NULL, reason TEXT NOT NULL, mode TEXT NOT NULL,
          revision INTEGER NOT NULL, assigned_at TEXT NOT NULL
        );
        CREATE TRIGGER IF NOT EXISTS immutable_report_update BEFORE UPDATE ON reports
          BEGIN SELECT RAISE(ABORT, 'reports are immutable'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_report_delete BEFORE DELETE ON reports
          BEGIN SELECT RAISE(ABORT, 'reports are immutable'); END;
        """)

    def close(self):
        self.db.close()

    @contextmanager
    def transaction(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.db.execute("COMMIT")
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def start_run(self, run_id, kind, country, owner):
        if kind not in {"prime_candidate", "ad_hoc", "comparison"}:
            raise ValueError("Unknown run kind")
        if kind == "prime_candidate" and not country:
            raise ValueError("Prime run requires a country")
        self.db.execute("INSERT INTO runs(id,kind,country,owner,started_at) VALUES(?,?,?,?,?)",
                        (run_id, kind, country, owner, utcnow()))

    def add_report(self, report_id, kind, country, owner, artifact, run_id=None):
        if kind == "prime_candidate" and not country:
            raise ValueError("Prime candidate requires exactly one country")
        body = json.dumps(artifact, sort_keys=True, ensure_ascii=False)
        digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
        if run_id is None:
            run_id = "run-" + report_id
            self.start_run(run_id, kind, country, owner)
        run = self.db.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
        if not run or (run["kind"], run["country"], run["owner"]) != (kind, country, owner):
            raise ValueError("Report must match its originating run")
        self.db.execute("INSERT INTO reports(id,kind,country,owner,run_id,artifact_json,artifact_hash,created_at) VALUES(?,?,?,?,?,?,?,?)",
                        (report_id, kind, country, owner, run_id, body, digest, utcnow()))
        return digest

    def approve(self, report_id, reviewer, role, validation_receipt):
        if role not in {"reviewer", "publisher", "admin"}:
            raise PermissionError("Reviewer role required")
        r = self.db.execute("SELECT * FROM reports WHERE id=?", (report_id,)).fetchone()
        if not r:
            raise ValueError("Unknown report")
        # A production validator must issue this receipt over the complete bundle.
        if validation_receipt.get("artifact_hash") != r["artifact_hash"] or validation_receipt.get("gate") != "passed" or validation_receipt.get("critical_issues") != 0 or validation_receipt.get("coverage_complete") is not True:
            raise ValueError("A matching complete validation receipt is required")
        self.db.execute("INSERT INTO approvals VALUES(?,?,?,?)", (report_id, reviewer, json.dumps(validation_receipt), utcnow()))

    def prime(self, country):
        row = self.db.execute("SELECT * FROM primes WHERE country=?", (country,)).fetchone()
        return dict(row) if row else None

    def assign(self, country, report_id, expected_revision, actor, role, reason, mode="pinned"):
        if role not in {"publisher", "admin"}:
            raise PermissionError("Publisher role required")
        if not reason.strip() or mode not in {"pinned", "latest_approved"}:
            raise ValueError("Assignment needs a reason and a valid selection mode")
        with self.transaction():
            r = self.db.execute("SELECT r.*, a.report_id approved FROM reports r LEFT JOIN approvals a ON r.id=a.report_id WHERE r.id=?", (report_id,)).fetchone()
            if not r or r["kind"] != "prime_candidate" or r["country"] != country or not r["approved"]:
                raise ValueError("Only an approved Prime candidate for this country is eligible")
            current = self.prime(country)
            revision = current["revision"] if current else 0
            if revision != expected_revision:
                raise ValueError("Stale pointer revision")
            if mode == "latest_approved":
                newest = self.db.execute("SELECT r.id FROM reports r JOIN approvals a ON r.id=a.report_id JOIN runs j ON r.run_id=j.id WHERE r.kind='prime_candidate' AND r.country=? ORDER BY j.sequence DESC LIMIT 1", (country,)).fetchone()
                if newest["id"] != report_id:
                    raise ValueError("Older completion cannot replace the newest approved candidate")
            new_revision = revision + 1
            self.db.execute("INSERT INTO primes VALUES(?,?,?,?) ON CONFLICT(country) DO UPDATE SET report_id=excluded.report_id,mode=excluded.mode,revision=excluded.revision",
                            (country, report_id, mode, new_revision))
            self.db.execute("INSERT INTO assignments(country,previous_report,report_id,actor,reason,mode,revision,assigned_at) VALUES(?,?,?,?,?,?,?,?)",
                            (country, current["report_id"] if current else None, report_id, actor, reason, mode, new_revision, utcnow()))
        return self.prime(country)

    def history(self, kind, country=None, owner=None):
        if kind == "prime":
            rows = self.db.execute("SELECT id,kind,country,created_at FROM reports WHERE kind='prime_candidate' AND country=? ORDER BY sequence", (country,))
        elif kind == "ad_hoc" and owner:
            rows = self.db.execute("SELECT id,kind,country,created_at FROM reports WHERE kind IN ('ad_hoc','comparison') AND owner=? ORDER BY sequence", (owner,))
        else:
            raise ValueError("Choose a country Prime history or an owner's ad hoc history")
        return [dict(r) for r in rows]

"""Small local workflow for saved evidence: freeze -> check -> select -> export.

No model dispatch, hosted publication or approval API. Imported outputs never
claim to have used the method currently installed. SQLite owns the transaction
and immutable byte archive; no separate queue, object server or ORM is needed.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator

from .engineering import _walk, digest, read_json, validate_v2, extraction_errors
from .inventory import COUNTRIES


VALIDATOR_VERSION = "local-profile-3"
CONTEXT_PATHS = (
    "schemas/local-profile-input.schema.json", "schemas/v2/extraction.schema.json",
    "schemas/v2/report.schema.json", "config/v2/pipelines.json",
    "config/v2/taxonomy.json", "config/v2/vocabulary.json", "config/v2/label-guide.json",
    "src/policytracker/engineering.py", "src/policytracker/profiles.py",
)


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False).encode("utf-8")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_bundle(root, bundle, context=None):
    """Validate original quotes, coverage, geography and joined report references.

    This is a deterministic import check, not a semantic accuracy certificate.
    A supplied context contains the archived bytes, never today's configuration.
    """
    def load(path):
        return json.loads(context[path]) if context is not None else read_json(root / path)

    errors = list(Draft202012Validator(load(CONTEXT_PATHS[0])).iter_errors(bundle))
    require(not errors, "; ".join(f"{e.json_path}: {e.message}" for e in errors))
    country = bundle["country_code"]
    require(country in COUNTRIES.values(), "Country is outside the configured region")
    sources = bundle["sources"]
    require(len({s["document_id"] for s in sources}) == len(sources), "Duplicate document IDs")
    require(len({s["sha256"] for s in sources}) == len(sources), "Duplicate source bytes")
    coverage = bundle.get("source_coverage", [])
    if coverage:
        require(len({d["document_id"] for d in coverage}) == len(coverage), "Duplicate document coverage")
        declared = {d["document_id"]: d for d in coverage}
        require({s["document_id"] for s in sources} <= set(declared), "Source missing from coverage contract")
        for source in sources:
            d = declared[source["document_id"]]
            require(d["sha256"] == source["sha256"] and d["pages"] == source["pages"], "Coverage differs from source identity or page count")
            require({p["page"] for p in source.get("page_checks", []) if p.get("automatic")} == set(range(1, source["pages"]+1)), "Automatic coverage must account for every physical page")
            gaps = any(p["automatic"]["status"] in ("partial", "unreadable") for p in source["page_checks"])
            require(d["status"] == ("partial" if gaps else "complete"), "Document coverage hides unresolved pages")
        for d in coverage:
            require(d["status"] == "complete" or d["issues"], "Incomplete document coverage needs reasons")
            require(d["document_id"] in {s["document_id"] for s in sources} or d["status"] == "unreadable", "Missing source cannot claim complete coverage")
    segments = {}
    for source in sources:
        require(source["country_code"] == country and source["metadata_verified"], "Verify source country attribution before import")
        require(source["layout_checked"], "Inspect source layout, OCR and tables before import")
        page_checks = source.get("page_checks", [])
        require(len({p["page"] for p in page_checks}) == len(page_checks), "Duplicate physical page checks")
        for check in page_checks:
            require(1 <= check["page"] <= source["pages"], "Page check is outside the source")
            review = check.get("review")
            if review:
                require(review.get("page") == check["page"] and review.get("source_sha256") == source["sha256"] and
                        review.get("reviewed") is True and review.get("note", "").strip(), "Invalid physical source page review")
                require(isinstance(review.get("text"), str) and sha(review["text"].encode("utf-8")) == review.get("text_sha256"), "Page review text hash differs")
                require(review.get("method") in ("reviewed_text", "ocr", "nontext") and
                        bool(review["text"].strip()) != (review["method"] == "nontext"), "Text/nontext page review is inconsistent")
            automatic = check.get("automatic")
            if automatic:
                require(automatic["source_sha256"] == source["sha256"] and automatic["page"] == check["page"] and
                        sha(automatic["text"].encode("utf-8")) == automatic["text_sha256"], "Automatic page record does not match source/text")
                require(bool(automatic["text"].strip()) == (automatic["status"] in ("complete", "partial")), "Automatic page coverage is inconsistent")
                if automatic["status"] in ("partial", "unreadable"):
                    require(automatic["notes"] and report_partial(bundle), "Unresolved pages require partial coverage and limitations")
                original = ''.join(s["text"] for s in source["segments"] if s["page"] == check["page"])
                require(original == automatic["text"], "Source segments differ from automatic page text")
        nontext = {p["page"] for p in page_checks if (p.get("review") and p["review"]["method"] == "nontext") or
                   (p.get("automatic") and p["automatic"]["status"] in ("nontext", "unreadable"))}
        require({s["page"] for s in source["segments"]} | nontext == set(range(1, source["pages"] + 1)), "Every physical source page needs segment accounting")
        for segment in source["segments"]:
            require(segment["id"] not in segments, "Segment IDs must be unique across the bundle")
            require(segment["text"].strip() and segment["english_text"].strip(), "Blank source or English segment")
            if segment["language"] == "en" or segment["translation_method"] == "identity":
                require(segment["language"] == "en" and segment["translation_method"] == "identity" and
                        segment["english_text"] == segment["text"], "English identity must preserve source text exactly")
            segments[segment["id"]] = segment
    extraction, report = bundle["extraction"], bundle["report"]
    errors = extraction_errors(root, extraction, country,
                         source_segments={key: s["text"] for key, s in segments.items()},
                         owned_segment_ids=list(segments), schema=load("schemas/v2/extraction.schema.json"))
    require(not errors, "; ".join(errors))
    records = {r["local_id"]: r for r in extraction["records"]}
    evidence = {e["local_id"]: e for e in extraction["evidence"]}
    topics = {t["id"] for t in load("config/v2/taxonomy.json")["topics"]}
    for record in records.values():
        require(set(record["labels"]["topic_ids"]) <= topics, "Record uses an unknown topic")
        for node in _walk(record):
            references = set(node.get("evidence_ids", []))
            if "evidence_id" in node:
                references.add(node["evidence_id"])
            require(references <= set(record["evidence_ids"]), "Record omits supporting evidence used by its details")
    for item in evidence.values():
        require(item["english_segment_id"] in (None, item["segment_id"]), "English locator does not match original segment")
    # Context can carry a table unit or inherited condition. A flat record/CSV
    # must not lose it simply because the direct quote points to another quote.
    for record in records.values():
        linked = set(record["evidence_ids"])
        require(all(set(evidence[eid]["context_evidence_ids"]) <= linked for eid in linked),
                "Record omits contextual evidence required by its quotations")
    sections = load("config/v2/pipelines.json")["features"]["prime"]["required_sections"]
    errors = validate_v2(root, "report", report, required_sections=sections,
                         known_evidence_ids=set(evidence), known_record_ids=set(records),
                         known_record_evidence={key:set(r['evidence_ids']) for key, r in records.items()},
                         known_commitment_ids={key for key, r in records.items() if r["kind"] == "commitment"},
                         schema=load("schemas/v2/report.schema.json"))
    require(not errors, "; ".join(errors))
    require(report["country_codes"] == [country], "Report country differs from source country")
    require(report["source_group_ids"] == [bundle["source_group_id"]], "Report source group differs from the frozen input")
    gaps = any(d["status"] != "complete" for d in bundle.get("source_coverage", []))
    require(report_partial(bundle) if gaps else report["availability"] == "complete_in_declared_scope", "Report availability must match declared source coverage")
    findings = (report["headline_findings"] + [f for s in report["sections"] for f in s["findings"]]
                + report["followup_questions"])
    for finding in findings:
        require(finding["calculation"] is None, "No application-verified calculation was supplied; retain source values without computed changes")
        citations = finding["citations"]
        linked = {eid for rid in citations["record_ids"] for eid in records[rid]["evidence_ids"]}
        require(set(citations["evidence_ids"]) <= linked, "Finding evidence is unrelated to its cited records")
    for priority in report["prioritized_commitments"]:
        require(set(priority["evidence_ids"]) <= set(records[priority["commitment_id"]]["evidence_ids"]),
                "Priority evidence is unrelated to its commitment")


def report_partial(bundle):
    return bundle["report"]["availability"] == "partial" and bool(bundle["report"].get("limitations"))


class ProfileStore:
    """A per-operation connection; callers must close it or use a with block."""
    def __init__(self, root, path=None):
        self.root = Path(root).resolve()
        path = Path(path) if path else self.root / "data/local-profiles/workspace.sqlite3"
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, isolation_level=None, timeout=15)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript("""
          CREATE TABLE IF NOT EXISTS objects(hash TEXT PRIMARY KEY, body BLOB NOT NULL);
          CREATE TABLE IF NOT EXISTS runs(
            sequence INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT NOT NULL UNIQUE,
            country TEXT NOT NULL, synthetic INTEGER NOT NULL, source_hash TEXT NOT NULL,
            manifest_hash TEXT NOT NULL REFERENCES objects(hash),
            state TEXT NOT NULL CHECK(state IN ('prepared','failed','checked')),
            error TEXT, created_at TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS profiles(
            id TEXT PRIMARY KEY REFERENCES runs(id), receipt_hash TEXT NOT NULL REFERENCES objects(hash));
          CREATE TABLE IF NOT EXISTS selections(
            country TEXT NOT NULL, synthetic INTEGER NOT NULL, profile_id TEXT REFERENCES profiles(id),
            pinned INTEGER NOT NULL DEFAULT 0, revision INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY(country, synthetic));
          CREATE TABLE IF NOT EXISTS publication_flags(
            id TEXT PRIMARY KEY, published INTEGER NOT NULL, updated_at TEXT NOT NULL);
          CREATE TRIGGER IF NOT EXISTS immutable_objects_update BEFORE UPDATE ON objects
            BEGIN SELECT RAISE(ABORT, 'archived bytes are immutable'); END;
          CREATE TRIGGER IF NOT EXISTS immutable_objects_delete BEFORE DELETE ON objects
            BEGIN SELECT RAISE(ABORT, 'archived bytes are immutable'); END;
          CREATE TRIGGER IF NOT EXISTS immutable_profiles_update BEFORE UPDATE ON profiles
            BEGIN SELECT RAISE(ABORT, 'profiles are immutable'); END;
          CREATE TRIGGER IF NOT EXISTS immutable_profiles_delete BEFORE DELETE ON profiles
            BEGIN SELECT RAISE(ABORT, 'profiles are immutable'); END;
          CREATE TRIGGER IF NOT EXISTS immutable_run_input BEFORE UPDATE OF id,country,synthetic,source_hash,manifest_hash,created_at ON runs
            BEGIN SELECT RAISE(ABORT, 'run input is immutable'); END;
        """)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.db.close()

    @contextmanager
    def transaction(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def put(self, raw):
        key = sha(raw)
        self.db.execute("INSERT OR IGNORE INTO objects VALUES(?,?)", (key, raw))
        require(self.get(key) == raw, "Archive hash collision or corruption")
        return key

    def get(self, key):
        row = self.db.execute("SELECT body FROM objects WHERE hash=?", (key,)).fetchone()
        require(row is not None and isinstance(row[0], bytes) and sha(row[0]) == key, "Archived bytes missing or corrupt")
        return row[0]

    def reused_method_files(self, generation):
        """Verify reused receipts and collect their original method bytes once."""
        steps = {step["step"]: step["result_hash"] for step in generation.get("steps", [])}
        files = {}
        for name, origin in generation.get("reused_steps", {}).items():
            require(steps.get(name) == origin.get("result_hash"), "Reused origin differs from the archived step receipt")
            receipt = json.loads(self.get(origin["result_hash"]))
            self.get(receipt["request_hash"])
            self.get(receipt["response_hash"])
            for fingerprint in origin["method"].values():
                if fingerprint not in files:
                    files[fingerprint] = self.get(fingerprint)
        return files

    def prepare(self, bundle, *, generation=None):
        # Detach caller-owned data. Freeze context before any validation or write.
        bundle = json.loads(encoded(bundle))
        context = {p: (self.root / p).read_bytes() for p in CONTEXT_PATHS}
        errors = list(Draft202012Validator(json.loads(context[CONTEXT_PATHS[0]])).iter_errors(bundle))
        require(not errors, "; ".join(f"{e.json_path}: {e.message}" for e in errors))
        binaries = {}
        for source in bundle["sources"]:
            relative = Path(source["path"])
            path = (self.root / relative).resolve()
            require(not relative.is_absolute() and path.is_relative_to(self.root), "Source path must remain inside the project")
            # Only original PDFs and the explicitly marked demonstration input.
            require(path.suffix.lower() == ".pdf" or (bundle["synthetic"] and
                    path == self.root / "examples/v2/synthetic-input.json"), "Expected a PDF source")
            raw = path.read_bytes()
            require(sha(raw) == source["sha256"], "Source file fingerprint changed")
            if path.suffix.lower() == ".pdf":
                from .preparation import pdf_page_count
                require(pdf_page_count(path) == source["pages"], "Source page count mismatch")
            binaries[source["document_id"]] = raw
        with self.transaction():
            manifest = {"bundle": self.put(encoded(bundle)),
                        "sources": {key: self.put(raw) for key, raw in binaries.items()},
                        "validation_context": {p: self.put(raw) for p, raw in context.items()},
                        "origin": "imported_outputs", "generation_method": "not_verified"}
            if generation is not None:
                manifest.update(origin="country_worker", generation_method="recorded",
                                generation=self.put(encoded(generation)))
            run_id = "profile-" + uuid.uuid4().hex
            self.db.execute("INSERT INTO runs(id,country,synthetic,source_hash,manifest_hash,state,created_at) VALUES(?,?,?,?,?,'prepared',?)",
                            (run_id, bundle["country_code"], int(bundle["synthetic"]), digest(bundle["sources"]), self.put(encoded(manifest)), now()))
        return run_id

    def _input(self, run_id):
        run = self.db.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
        require(run is not None, "Unknown profile run")
        manifest = json.loads(self.get(run["manifest_hash"]))
        bundle = json.loads(self.get(manifest["bundle"]))
        for key in list(manifest["sources"].values()) + list(manifest["validation_context"].values()):
            self.get(key)
        if "generation" in manifest:
            generation = json.loads(self.get(manifest["generation"]))
            if generation.get("prepared_sources"):
                self.get(generation["prepared_sources"])
            for key in generation["method"].values():
                self.get(key)
            self.get(generation["reconciliation"])
            for step in generation["steps"]:
                result = json.loads(self.get(step["result_hash"]))
                self.get(result["request_hash"])
                self.get(result["response_hash"])
            self.reused_method_files(generation)
            for attempt in generation.get("attempts", []):
                self.get(attempt["request_hash"])
                if attempt["response_hash"]:
                    self.get(attempt["response_hash"])
        return run, manifest, bundle

    def complete(self, run_id):
        run, manifest, bundle = self._input(run_id)
        if run["state"] == "checked":
            return self.profile(run_id)
        try:
            # Validate archived JSON in memory; archived Python is never executed.
            context = {path: self.get(key) for path, key in manifest["validation_context"].items()}
            for path in CONTEXT_PATHS[-2:]:
                require(sha((self.root / path).read_bytes()) == manifest["validation_context"][path],
                        "Validator changed; prepare a new run")
            validate_bundle(self.root, bundle, context)
        except ValueError as exc:
            self.db.execute("UPDATE runs SET state='failed',error=? WHERE id=? AND state!='checked'", (str(exc), run_id))
            raise
        with self.transaction():
            receipt = {"validator": VALIDATOR_VERSION, "manifest_hash": run["manifest_hash"],
                       "checked_at": now(), "checks": "schema, source hashes, page accounting, quotes, references, coverage, attribution",
                       "semantic_accuracy": "not_certified", "generation_method": manifest["generation_method"]}
            self.db.execute("INSERT OR IGNORE INTO profiles VALUES(?,?)", (run_id, self.put(encoded(receipt))))
            self.db.execute("UPDATE runs SET state='checked',error=NULL WHERE id=?", (run_id,))
            self._select_latest(run["country"], run["synthetic"])
        return self.profile(run_id)

    def _latest(self, country, synthetic):
        current = self.db.execute("SELECT source_hash FROM runs WHERE country=? AND synthetic=? ORDER BY sequence DESC LIMIT 1", (country, synthetic)).fetchone()
        if not current:
            return None
        row = self.db.execute("SELECT r.id FROM runs r JOIN profiles p ON p.id=r.id LEFT JOIN publication_flags f ON f.id=r.id WHERE country=? AND synthetic=? AND source_hash=? AND COALESCE(f.published,1)=1 ORDER BY sequence DESC LIMIT 1",
                              (country, synthetic, current["source_hash"])).fetchone()
        return row[0] if row else None

    def _select_latest(self, country, synthetic):
        selection = self.selection(country, synthetic)
        if selection["pinned"]:
            return
        latest = self._latest(country, synthetic)
        if latest and latest != selection["profile_id"]:
            self._write_selection(country, synthetic, latest, False, selection["revision"])

    def selection(self, country, synthetic=False):
        row = self.db.execute("SELECT * FROM selections WHERE country=? AND synthetic=?", (country, int(synthetic))).fetchone()
        value = dict(row) if row else {"country": country, "synthetic": int(synthetic), "profile_id": None, "pinned": 0, "revision": 0}
        latest = self.db.execute("SELECT source_hash FROM runs WHERE country=? AND synthetic=? ORDER BY sequence DESC LIMIT 1", (country, int(synthetic))).fetchone()
        selected = self.db.execute("SELECT source_hash FROM runs WHERE id=?", (value["profile_id"],)).fetchone()
        value["stale_sources"] = bool(latest and selected and latest[0] != selected[0])
        return value

    def _write_selection(self, country, synthetic, profile_id, pinned, revision):
        self.db.execute("INSERT INTO selections VALUES(?,?,?,?,?) ON CONFLICT(country,synthetic) DO UPDATE SET profile_id=excluded.profile_id,pinned=excluded.pinned,revision=excluded.revision",
                        (country, int(synthetic), profile_id, int(pinned), revision + 1))

    def select(self, country, profile_id, expected_revision, synthetic=False):
        """Pin an existing checked profile; None unpins to latest current sources."""
        with self.transaction():
            selection = self.selection(country, synthetic)
            require(selection["revision"] == expected_revision, "Selection changed; refresh its revision")
            if profile_id:
                profile = self.profile(profile_id)
                require(profile["country_code"] == country and profile["synthetic"] == bool(synthetic), "Profile belongs to another country or scope")
                require(profile["published"], "Publish this version before selecting it")
            self._write_selection(country, synthetic, profile_id or self._latest(country, int(synthetic)), bool(profile_id), expected_revision)
        return self.selection(country, synthetic)

    def history(self, country, synthetic=False):
        return [dict(r) for r in self.db.execute("SELECT r.id,sequence,state,error,created_at,COALESCE(f.published,1) AS published FROM runs r LEFT JOIN publication_flags f ON f.id=r.id WHERE country=? AND synthetic=? ORDER BY sequence DESC", (country, int(synthetic)))]

    def published(self, result_id):
        row = self.db.execute("SELECT published FROM publication_flags WHERE id=?", (result_id,)).fetchone()
        return bool(row[0]) if row else True

    def moderate(self, result_id, published):
        require(type(published) is bool, "Choose Publish or Unpublish")
        profile = self.profile(result_id)
        with self.transaction():
            self.db.execute("INSERT INTO publication_flags VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET published=excluded.published,updated_at=excluded.updated_at", (result_id, int(published), now()))
            country, synthetic = profile["country_code"], profile["synthetic"]
            selection = self.selection(country, synthetic)
            if published:
                self._write_selection(country, synthetic, result_id, False, selection["revision"])
            elif selection["profile_id"] == result_id:
                previous = self.db.execute("SELECT r.id FROM runs r JOIN profiles p ON p.id=r.id LEFT JOIN publication_flags f ON f.id=r.id WHERE country=? AND synthetic=? AND COALESCE(f.published,1)=1 ORDER BY sequence DESC LIMIT 1", (country, int(synthetic))).fetchone()
                self._write_selection(country, synthetic, previous[0] if previous else None, False, selection["revision"])
        return self.country(country, synthetic)

    def profile(self, run_id):
        row = self.db.execute("SELECT receipt_hash FROM profiles WHERE id=?", (run_id,)).fetchone()
        require(row is not None, "Profile has not passed local checks")
        run, manifest, bundle = self._input(run_id)
        receipt = json.loads(self.get(row[0]))
        require(receipt["manifest_hash"] == run["manifest_hash"], "Receipt does not match archived input")
        # Resolve historical definitions only from the archived validation bytes.
        # This is the import codebook, not proof of a generator's method.
        context = manifest["validation_context"]
        taxonomy = json.loads(self.get(context["config/v2/taxonomy.json"]))
        guide = json.loads(self.get(context["config/v2/label-guide.json"]))
        vocabulary = json.loads(self.get(context["config/v2/vocabulary.json"]))
        codebook = {"basis": "archived_validation" if "generation" in manifest else "archived_import_validation_not_generation",
                    "taxonomy_version": taxonomy["version"], "guide_version": guide["version"],
                    "vocabulary_version": vocabulary["version"],
                    "domains": [{**d, "definition": guide["domain_definitions"][d["id"]]} for d in taxonomy["domains"]],
                    "topics": taxonomy["topics"], "dimensions": guide["dimensions"]}
        generated = {}
        if "generation" in manifest:
            generation = json.loads(self.get(manifest["generation"]))
            generated = {"generation": generation, "reconciliation": json.loads(self.get(generation["reconciliation"]))}
        return {"id": run_id, "created_at": run["created_at"], "published": self.published(run_id), **bundle, **generated,
                "validation": receipt, "archive": manifest, "validation_codebook": codebook}

    def country(self, country, synthetic=False):
        selection = self.selection(country, synthetic)
        return {"selection": selection, "history": self.history(country, synthetic),
                "profile": self.profile(selection["profile_id"]) if selection["profile_id"] else None}

    def summaries(self):
        result = []
        for row in self.db.execute("SELECT DISTINCT country FROM runs WHERE synthetic=0"):
            selected = self.selection(row[0])
            # Verify bytes before making the profile visible to the regional UI.
            if selected["profile_id"]:
                self.profile(selected["profile_id"])
            result.append({**selected, "history_count": len(self.history(row[0]))})
        return result


def register_csv(profile):
    """One row per record; nested lists are JSON cells, never silently dropped."""
    output = io.StringIO(newline="")
    fields = ["profile_id", "country_code", "record_id", "kind", "label_en", "description_en",
              "assertion_kind", "documentation_status", "geography", "labels", "targets", "actors", "finance",
              "indicators", "risk_contexts", "details", "reference_period", "field_support", "missing_fields",
              "quality_flags", "extraction_notes", "evidence", "source_segments", "source_coverage", "limitations"]
    if not any("assertion_kind" in r for r in profile["extraction"]["records"]):
        fields = [f for f in fields if f not in ("assertion_kind", "documentation_status")]
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    evidence = {e["local_id"]: e for e in profile["extraction"]["evidence"]}
    segments = {s["id"]: {**s, "document_id": d["document_id"], "source_sha256": d["sha256"]}
                for d in profile["sources"] for s in d["segments"]}
    for record in profile["extraction"]["records"]:
        linked = [evidence[key] for key in record["evidence_ids"]]
        row = {field: record.get(field) for field in fields}
        row.update(profile_id=profile["id"], country_code=profile["country_code"], record_id=record["local_id"],
                   extraction_notes=profile["extraction"].get("notes", []),
                   source_coverage=profile.get("source_coverage", []), limitations=profile["report"].get("limitations", []),
                   evidence=linked, source_segments=[segments[key] for key in dict.fromkeys(e["segment_id"] for e in linked)])
        for key, value in row.items():
            text = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value) if value is not None else ""
            row[key] = "'" + text if text.lstrip().startswith(("=", "+", "-", "@", "'")) or text.startswith(("\t", "\r", "\n")) else text
        writer.writerow(row)
    return "\ufeff" + output.getvalue()


def demo_bundle(root):
    """Explicit synthetic import through the same workflow, isolated from countries."""
    root = Path(root)
    source = read_json(root / "examples/v2/synthetic-input.json")
    english = {s["segment_id"]: s for s in read_json(root / "examples/v2/translation.json")["segments"]}
    path = "examples/v2/synthetic-input.json"
    return {"format": "local-profile-1", "country_code": "KAZ", "synthetic": True,
            "source_group_id": "synthetic-group", "provenance_note": "Invented fixture imported locally; no model was run.",
            "sources": [{"document_id": "synthetic-document", "title": "Invented flood preparedness example", "path": path,
                         "sha256": sha((root / path).read_bytes()), "country_code": "KAZ", "metadata_verified": True,
                         "pages": 1, "layout_checked": True, "segments": [
                             {"id": key, "page": 1, "language": "en" if english[key]["method"] == "identity" else "ru",
                              "text": value, "english_text": english[key]["english_text"], "translation_method": english[key]["method"]}
                             for key, value in source["source_segments"].items()]}],
            "extraction": read_json(root / "examples/v2/extraction.json"), "report": read_json(root / "examples/v2/prime-report.json")}

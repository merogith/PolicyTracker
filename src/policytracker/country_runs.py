"""One local country worker, with SQLite checkpoints and immutable request bytes.

Starts and resumes are explicit. At most two independent batches run together.
Stop drains active requests, saves valid results, and prevents dispatch or commit.
"""
from __future__ import annotations

import io
import json
import re
import shutil
import threading
import uuid
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from contextlib import nullcontext
from pathlib import Path

from .ai_runtime import AIError
from .engineering import (_walk, compose_v2, digest, read_json, validate_v2,
                          extraction_errors, compact_packet, repair_feedback, normalize_extraction_evidence)
from .inventory import COUNTRIES
from .profiles import CONTEXT_PATHS, ProfileStore, encoded, now, require, sha, validate_bundle
from .operations import (compose_operation, normalize_request, validate_source_groups,
                         scoped_evidence, validate_operation_output, evidence_table, delivery_checks)
from .preparation import (inspect_document, review_paths, review_path, read_review, source_bytes,
                          save_review, validate_review, render_page, ocr_page, find_ocr_engine, PreparationRequired,
                          recover_page, pdf_page_count, RECOVERY_SCHEMA, recovery_check)
from .settings import read_settings

ROUTES = ("triage", "translate", "extract", "reconcile", "prime", "focused_analysis", "comparison", "workplan", "briefing")
STAGES = ("prepare", "translate", "extract", "reconcile", "overview", "validate")
MAX_REQUEST_BYTES = 180_000  # A conservative local ceiling; never silently truncate.
EXTRACTION_REPAIR_RESERVE_BYTES = 65_000  # Headroom, not a guarantee about model output size.
EXTRACTION_TEXT_LIMIT = 3_000  # Dense multi-page samples produced oversized repair responses.


def chunks(segments, limit=9000):
    result, batch, size = [], [], 0
    for segment in segments:
        if batch and size + len(segment["text"]) > limit:
            result.append(batch)
            batch, size = [], 0
        batch.append(segment)
        size += len(segment["text"])
    if batch:
        result.append(batch)
    return result


def document_context(source, context):
    """Scope source-reading requests to this document, independently of selection."""
    return {**context, "country_codes": [source["country_code"]],
            "source_group_ids": ["document-" + digest((source["document_id"], source["sha256"]))[:20]],
            "scope": "this document only; never infer national absence or implementation progress",
            "source_coverage": [c for c in context.get("source_coverage", []) if c["document_id"] == source["document_id"]],
            **({"document_profiles": [p for p in context["document_profiles"] if p["input_id"] == source["document_id"]]}
               if "document_profiles" in context else {})}


def adjacent_segments(source, batch):
    start = source["segments"].index(batch[0])
    return (source["segments"][max(0, start-1):start]
            + source["segments"][start+len(batch):start+len(batch)+1])


def extraction_source_data(source, batch, surrounding):
    """Keep original/translated evidence without duplicating English identity text."""
    def segment_data(segment):
        result = dict(segment)
        if result.get("translation_method") == "identity" and result.get("english_text") == result.get("text"):
            result.pop("english_text", None)
        return result
    return {"document_id": source["document_id"], "segments": [segment_data(s) for s in batch],
            "context_segments": [segment_data(s) for s in surrounding]}


def extraction_batches(root, source, context, settings=None):
    """Plan deterministic owned batches before extraction, retaining neighbor context."""
    segments = source["segments"]
    metadata = next(p for p in context["document_profiles"] if p["input_id"] == source["document_id"])
    planned = []
    def fit(batch):
        neighbors = adjacent_segments(source, batch)
        context_ids = {s["id"] for s in neighbors} | set(metadata["metadata_evidence_ids"]) | set(metadata["geography"]["evidence_ids"])
        owned = {s["id"] for s in batch}
        surrounding = [s for s in segments if s["id"] in context_ids and s["id"] not in owned]
        # Match step()'s canonical request and preferences, including their bytes
        # in the same budget used for dispatch. Source archives remain complete.
        request_context = json.loads(encoded({**context, "owned_segment_ids": [s["id"] for s in batch]}))
        if settings:
            request_context["user_preferences"] = {k: settings[k] for k in ("instructions", "topic_ids")}
        data = json.loads(encoded(extraction_source_data(source, batch, surrounding)))
        packet = compact_packet(compose_v2(root, "extract", request_context, data))
        if len(encoded(packet)) + EXTRACTION_REPAIR_RESERVE_BYTES <= MAX_REQUEST_BYTES:
            planned.append((batch, surrounding))
        else:
            require(len(batch) > 1, "Extraction segment and required context leave insufficient repair headroom; prepare a smaller segment or scope. No source text was dropped.")
            midpoint = len(batch) // 2
            fit(batch[:midpoint]); fit(batch[midpoint:])
    for batch in chunks(segments, EXTRACTION_TEXT_LIMIT):
        require(all(len(s["text"]) <= EXTRACTION_TEXT_LIMIT for s in batch),
                "Extraction segment exceeds the source-text limit; prepare smaller segments before dispatch. No source text was dropped.")
        fit(batch)
    return planned


def namespace_extraction(output, prefix):
    """Local model IDs become stable, chunk-scoped IDs without changing quotations."""
    ids = {node["local_id"] for node in _walk(output) if "local_id" in node}
    local_references = {"local_id", "evidence_id", "evidence_ids", "context_evidence_ids", "record_ids", "target_ids"}
    def visit(value, key=""):
        if isinstance(value, dict):
            return {k: visit(v, k) for k, v in value.items()}
        if isinstance(value, list):
            return [visit(v, key) for v in value]
        if isinstance(value, str) and key in local_references and value in ids:
            return prefix + value
        return value
    return visit(output)


def synthesis_evidence(extraction):
    """Omit validation bookkeeping from model inputs, retaining every record and quote.

    Full records, null reasons, support pointers and coverage remain in the saved
    profile. This is deterministic compaction, not a model-written summary.
    """
    def compact(value):
        if isinstance(value, dict):
            return {k: compact(v) for k, v in value.items() if k != "field_support" and v not in (None, [], {})}
        if isinstance(value, list):
            return [compact(v) for v in value]
        return value
    return compact({"records": extraction["records"], "evidence": extraction["evidence"],
                    "notes": extraction.get("notes", [])})


def synthesis_batches(extraction, limit=65000, note_scopes=None):
    """Bound synthesis inputs, retaining source-scoped notes and quote context.

    Scopes are the original namespaced extraction outputs. Filtering may remove
    their records, but their notes remain intact in separate bounded parts. An
    archive without scopes keeps global notes with every record/quote part;
    an indivisible part must fail explicitly rather than exceed the limit.
    """
    require(type(limit) is int and limit > 0, "synthesis limit must be a positive byte count")
    notes = extraction.get("notes", [])
    record_scopes, evidence_scopes = {}, {}
    if note_scopes is not None:
        require([note for scope in note_scopes for note in scope.get("notes", [])] == notes,
                "synthesis notes differ from their extraction scopes")
        for number, scope in enumerate(note_scopes):
            for key, lookup in (("records", record_scopes), ("evidence", evidence_scopes)):
                for item in scope[key]:
                    require(item["local_id"] not in lookup, "synthesis notes scopes contain duplicate source IDs")
                    lookup[item["local_id"]] = (number, item)
        for key, lookup in (("records", record_scopes), ("evidence", evidence_scopes)):
            require(all(item["local_id"] in lookup and lookup[item["local_id"]][1] == item
                        for item in extraction[key]), "synthesis notes scopes do not match the supplied source records/evidence")

    def size(value):
        return len(encoded(synthesis_evidence(value)))

    def bounded(value):
        require(size(value) <= limit,
                "synthesis record, quote context, or note exceeds the byte limit; reduce the source scope. No evidence or notes were dropped.")
        return value

    if size(extraction) <= limit:
        return [extraction]
    evidence = {e["local_id"]: e for e in extraction["evidence"]}

    def matched_scopes(records, ids):
        return ({record_scopes[r["local_id"]][0] for r in records}
                | {evidence_scopes[eid][0] for eid in ids}) if note_scopes is not None else set()

    def part(records, extra_ids=()):
        ids = set(extra_ids) | {eid for r in records for eid in r["evidence_ids"]}
        pending = list(ids)
        while pending:
            current = pending.pop()
            require(current in evidence, "synthesis quote context references missing evidence")
            for eid in evidence[current].get("context_evidence_ids", []):
                if eid not in ids: ids.add(eid); pending.append(eid)
        scopes = matched_scopes(records, ids)
        attached_notes = (notes if note_scopes is None else
                          [note for number, scope in enumerate(note_scopes) if number in scopes
                           for note in scope.get("notes", [])])
        return {**extraction, "records": list(records), "evidence": [e for k, e in evidence.items() if k in ids],
                "notes": list(attached_notes)}

    result, batch = [], []
    for record in extraction["records"]:
        candidate = part(batch + [record])
        if batch and size(candidate) > limit:
            result.append(part(batch))
            batch = []
            candidate = part([record])
        bounded(candidate)
        batch.append(record)
    if batch:
        result.append(part(batch))
    used = {e["local_id"] for p in result for e in p["evidence"]}
    for item in extraction["evidence"]:
        if item["local_id"] in used:
            continue
        candidate = (part(result[-1]["records"], [e["local_id"] for e in result[-1]["evidence"]] + [item["local_id"]])
                     if result else part([], [item["local_id"]]))
        if result and size(candidate) <= limit:
            result[-1] = candidate
        else:
            candidate = bounded(part([], [item["local_id"]]))
            result.append(candidate)
        used.update(e["local_id"] for e in candidate["evidence"])

    represented = set().union(*(matched_scopes(p["records"], {e["local_id"] for e in p["evidence"]}) for p in result))
    orphan_notes = ([note for number, scope in enumerate(note_scopes) if number not in represented
                     for note in scope.get("notes", [])] if note_scopes is not None else notes if not result else [])
    batch = []
    def note_part(values):
        return {**extraction, "records": [], "evidence": [], "notes": list(values)}
    for note in orphan_notes:
        if batch and size(note_part(batch + [note])) > limit:
            result.append(note_part(batch))
            batch = []
        bounded(note_part(batch + [note]))
        batch.append(note)
    if batch:
        result.append(note_part(batch))
    return [bounded(p) for p in result] or [bounded(extraction)]


def merge_synthesis(outputs):
    """Combine checked chunks; never let a later summary replace their evidence."""
    if len(outputs) == 1: return outputs[0]
    def union(values):
        return list({encoded(v):v for v in values}.values())
    def empty_state(rows):
        states = {row["state"] for row in rows}
        return next((state for state in ("not_processed", "not_found_in_scope", "not_applicable") if state in states), "not_found_in_scope")
    result = json.loads(encoded(outputs[0]))
    if "sections" in result:
        if (len({out["availability"] for out in outputs}) > 1
                or any(out["availability"] == "partial" for out in outputs)
                or any(s["state"] == "not_processed" for out in outputs for s in out["sections"])):
            result["availability"] = "partial"
        for key in ("headline_findings", "prioritized_commitments", "followup_questions"):
            result[key] = union([v for out in outputs for v in out[key]])
        for section in result["sections"]:
            matches = [s for out in outputs for s in out["sections"] if s["section_id"] == section["section_id"]]
            section["findings"] = union([f for s in matches for f in s["findings"]])
            section["state"] = "found" if section["findings"] else empty_state(matches)
            section["gap_note"] = None if section["findings"] else " ".join(dict.fromkeys(s["gap_note"] for s in matches if s["gap_note"])) or "No finding in the processed source material."
    elif "groups" in result:  # Comparison: each bounded chunk retains every requested group/dimension.
        for key in ("synthesis", "exclusions"):
            result[key] = union([v for out in outputs for v in out[key]])
        for row in result["rows"]:
            matches = [r for out in outputs for r in out["rows"] if r["dimension"] == row["dimension"]]
            for cell in row["cells"]:
                cells = [c for r in matches for c in r["cells"] if c["group_id"] == cell["group_id"]]
                cell["findings"] = union([f for c in cells for f in c["findings"]])
                cell["state"] = "found" if cell["findings"] else empty_state(cells)
            row["comparability"] = "descriptive_only"
            row["comparability_reason"] = "Combined from bounded evidence batches; no cross-batch normalization or numerical comparison was performed."
    else:  # Delivery: each source commitment belongs to exactly one chunk.
        result["rows"] = [r for out in outputs for r in out["rows"]]
    result["limitations"] = union([v for out in outputs for v in out["limitations"]] +
        ["Large source scope was synthesized in bounded batches. Cross-batch relationships and priorities are not exhaustive."])
    return result


def check_translation(output, segments):
    lookup = {s["id"]: s for s in segments}
    rows = output["segments"]
    require(len(rows) == len(lookup) and {r["segment_id"] for r in rows} == set(lookup),
            "Translation must cover every segment exactly once.")
    for row in rows:
        require(row["english_text"].strip() and not row["quality_flags"],
                "Translation needs attention: " + "; ".join(row["quality_flags"]))
        require(row["method"] in ("identity", "machine_translation") and row["official_parallel_segment_id"] is None,
                "No verified official parallel text was supplied.")
        if row["method"] == "identity":
            require(row["english_text"] == lookup[row["segment_id"]]["text"], "English identity changed the original text.")
        if "source_language" in row:
            require(re.fullmatch(r"[a-z]{2,3}(?:-[A-Za-z0-9]+)*", row["source_language"]), "Use a source language code per segment")
            require((row["source_language"] == "en") == (row["method"] == "identity"), "English segments must use exact identity; mixed segments use mul")


def check_reconciliation(output, extraction, sources=None, profiles=None):
    records = {r["local_id"]: r for r in extraction["records"]}
    evidence = {e["local_id"] for e in extraction["evidence"]}
    targets = {t["local_id"] for r in records.values() for t in r["targets"]}
    seen = set()
    for group in output["groups"]:
        require(group["local_group_id"] not in seen, "Duplicate reconciliation group.")
        seen.add(group["local_group_id"])
        require(group["record_ids"] and set(group["record_ids"]) <= set(records), "Unknown reconciliation record.")
        require(group["proposed_existing_commitment_id"] is None, "No canonical commitment registry is supplied.")
        allowed_targets = {t["local_id"] for rid in group["record_ids"] for t in records[rid]["targets"]}
        allowed_evidence = {e for rid in group["record_ids"] for e in records[rid]["evidence_ids"]}
        for variant in group["variants"]:
            require(set(variant["target_ids"]) <= allowed_targets and variant["evidence_ids"] and
                    set(variant["evidence_ids"]) <= allowed_evidence, "Variant references unrelated targets or evidence.")
    for node in _walk(output):
        for key, value in node.items():
            if key.endswith("record_ids"):
                require(set(value) <= set(records), "Reconciliation references unknown records.")
            if key == "evidence_ids":
                require(set(value) <= evidence, "Reconciliation references unknown evidence.")
            if key == "target_ids":
                require(set(value) <= targets, "Reconciliation references unknown targets.")
    for relation in output["relations"]:
        ids = relation["source_record_ids"] + relation["target_record_ids"]
        require(relation["source_record_ids"] and relation["target_record_ids"], "A relationship needs both sides.")
        linked = {e for rid in ids for e in records[rid]["evidence_ids"]}
        require(relation["evidence_ids"] and set(relation["evidence_ids"]) <= linked, "Relationship lacks linked evidence.")
    for change in output["changes"]:
        ids = change["before_record_ids"] + change["after_record_ids"]
        finding = change["finding"]
        require(finding["calculation"] is None, "Reconciliation cannot assert an unchecked calculation")
        linked = {e for rid in ids for e in records[rid]["evidence_ids"]}
        require(finding["citations"]["evidence_ids"] and set(finding["citations"]["evidence_ids"]) <= linked and
                set(finding["citations"]["record_ids"]) <= set(ids), "Change lacks linked evidence.")
        if sources is not None and change["before_record_ids"] and change["after_record_ids"]:
            segments = {s["id"]: d["document_id"] for d in sources for s in d["segments"]}
            quotes = {e["local_id"]: e for e in extraction["evidence"]}
            metadata = {p["input_id"]: p for p in profiles or []}
            def document_dates(record_ids):
                docs = {segments[quotes[e]["segment_id"]] for rid in record_ids for e in records[rid]["evidence_ids"]}
                return [metadata.get(d, {}).get("publication_date") for d in docs]
            before, after = document_dates(change["before_record_ids"]), document_dates(change["after_record_ids"])
            require(all(isinstance(d, str) and re.fullmatch(r"\d{4}(?:-\d{2}(?:-\d{2})?)?", d) for d in before + after)
                    and len({len(d) for d in before + after}) == 1 and max(before) < min(after),
                    "Before/after change lacks verified edition order; use a descriptive relationship instead")


class Stopped(Exception):
    pass


def needs_source_review(job):
    # Old saved jobs retain their original error and archive unchanged.
    if job.get("automatic"):
        return False
    return job.get("required_action") == "review_sources" or (
        job.get("stage") == "prepare" and any(marker in (job.get("error") or "")
        for marker in ("text needs inspection", "pages need review", "source page")))


class CountryRunner:
    def __init__(self, root, path, service, *, synthetic=False):
        self.root, self.path, self.service = Path(root), Path(path), service
        self.synthetic = synthetic  # Only test harnesses set this; never accepted by HTTP.
        self.lock, self.stop_event = threading.RLock(), threading.Event()
        self.active, self.thread = None, None
        with self.store() as store:
            store.db.executescript("""
              CREATE TABLE IF NOT EXISTS country_jobs(id TEXT PRIMARY KEY, country TEXT NOT NULL, data TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS country_steps(
                job_id TEXT NOT NULL, step TEXT NOT NULL, signature TEXT NOT NULL,
                result_hash TEXT NOT NULL REFERENCES objects(hash), PRIMARY KEY(job_id,step));
              CREATE INDEX IF NOT EXISTS country_step_cache ON country_steps(signature);
              CREATE TABLE IF NOT EXISTS automatic_pages(signature TEXT PRIMARY KEY, result_hash TEXT NOT NULL REFERENCES objects(hash));
              CREATE TABLE IF NOT EXISTS country_attempts(
                sequence INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT NOT NULL, step TEXT NOT NULL,
                request_hash TEXT NOT NULL REFERENCES objects(hash), response_hash TEXT REFERENCES objects(hash), error TEXT);
            """)
            # An interrupted process never resumes automatically or retains credentials.
            for row in store.db.execute("SELECT id,data FROM country_jobs").fetchall():
                job = json.loads(row["data"])
                if job["status"] in ("running", "stopping"):
                    job.update(status="stopped", message="The server restarted. Reconnect AI and resume the saved steps.")
                    self.write(store, job)

    def store(self):
        return ProfileStore(self.root, self.path)

    @staticmethod
    def write(store, job):
        job["updated_at"] = now()
        store.db.execute("INSERT INTO country_jobs VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data",
                         (job["id"], job["country"], encoded(job).decode()))

    def get(self, job_id):
        with self.store() as store:
            row = store.db.execute("SELECT data FROM country_jobs WHERE id=?", (job_id,)).fetchone()
            if not row:
                raise AIError("not_found", "Country run not found.", 404)
            return json.loads(row[0])

    def status(self, country):
        if country not in COUNTRIES.values():
            raise AIError("country", "Choose a country in this workspace.")
        with self.store() as store:
            jobs = [json.loads(r[0]) for r in store.db.execute(
                "SELECT data FROM country_jobs WHERE country=? ORDER BY rowid DESC LIMIT 10", (country,))]
        return {"runs": [self.public(job) for job in jobs], "active_country": self.get(self.active)["country"] if self.active else None}

    @staticmethod
    def public(job):
        result = {k: job.get(k) for k in ("id", "country", "status", "stage", "message", "completed", "total",
                "selection", "document_ids", "created_at", "updated_at", "profile_id", "error", "operation", "result_hash", "synthetic",
                "preparation_issues", "required_action", "automatic", "source_coverage", "published")}
        result["can_resume"] = job.get("status") in ("failed", "stopped") and not needs_source_review(job)
        if needs_source_review(job):
            result["required_action"] = "review_sources"
        return result

    def inspect_sources(self, documents):
        result = []
        for doc in documents:
            item = {"document_id": doc["document_id"], "title": doc["title"], "sha256": doc["sha256"],
                    "pages": [], "error": None, "ready": False}
            try:
                pages = inspect_document(self.root, doc)
                item.update(total_pages=len(pages), reviewed_pages=sum(p["review"] is not None for p in pages),
                            reviewed_page_numbers=[p["page"] for p in pages if p["review"] is not None],
                            pages=[{k: p[k] for k in ("page", "concerns", "review_error")} for p in pages if p["needs_review"]])
                substantive = any((p["review"]["text"] if p["review"] else p["text"]).strip() for p in pages)
                if not substantive and not item["pages"]:
                    item["error"] = "No substantive text remains after page review. Choose a substantive source document."
                item["ready"] = not item["pages"] and not item["error"]
            except (ValueError, OSError) as exc:
                item["error"] = str(exc)
            result.append(item)
        return {"documents": result, "ready": all(d["ready"] for d in result),
                "pages_needing_review": sum(len(d["pages"]) for d in result)}

    def preparation(self, payload):
        """Local parsing/review only. No model, credential or saved-profile operation."""
        try:
            action = payload.get("action", "inspect")
            if action == "inspect":
                return self.inspect_sources(self.documents(payload.get("country"), payload.get("document_ids")))
            require(action in ("page", "ocr", "save"), "Unknown preparation action")
            doc = self.documents(None, [payload.get("document_id")])[0]
            source, raw = source_bytes(self.root, doc)
            pages = inspect_document(self.root, doc, raw)
            page = payload.get("page")
            require(type(page) is int and 1 <= page <= len(pages), "Choose a physical page in this PDF")
            current = pages[page - 1]
            candidate_path = review_path(self.root, doc["sha256"], page, candidate=True)
            if action in ("save", "ocr"):
                with self.lock:
                    require(not self.active, "Stop the active country or analysis run before changing page preparation")
                    require(payload.get("source_sha256") == doc["sha256"], "Source changed. Reopen this page before saving")
                    require(not review_path(self.root, doc["sha256"], page).exists(), "This page already has a saved review. Preserve it before a deliberate correction")
                    if action == "ocr":
                        require(not candidate_path.exists(), "An OCR/review draft already exists. Check the saved draft instead of overwriting it")
                        item = ocr_page(self.root, source, page, payload.get("language", "eng"))
                        source_bytes(self.root, doc)
                        save_review(self.root, item, candidate=True)
                    else:
                        require(payload.get("confirmed") is True, "Confirm that the text was checked against the original page")
                        method = payload.get("method")
                        require(method in ("reviewed_text", "nontext"), "Choose checked text or a non-substantive page")
                        text, note = payload.get("text"), payload.get("note")
                        require(isinstance(text, str) and isinstance(note, str), "Supply page text and an inspection note")
                        item = {"source_sha256": doc["sha256"], "page": page, "method": method, "text": text,
                                "text_sha256": sha(text.encode("utf-8")), "reviewed": True, "note": note, "created_at": now()}
                        if candidate_path.exists() and method == "reviewed_text":
                            candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
                            validate_review(self.root, candidate, doc["sha256"], page, approved=False)
                            if candidate.get("method") == "ocr":
                                item.update({k: v for k, v in candidate.items() if k.startswith("ocr_") or k in ("review_image", "render_sha256", "tsv_sha256")})
                                item["candidate_text_sha256"] = candidate["text_sha256"]
                        source_bytes(self.root, doc)
                        save_review(self.root, item)
                        return {"saved": True, "page": page, "document_id": doc["document_id"]}
            candidate, candidate_error = None, None
            if candidate_path.exists():
                try:
                    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
                    validate_review(self.root, candidate, doc["sha256"], page, approved=False)
                except (ValueError, OSError) as exc:
                    candidate, candidate_error = None, str(exc)
            return {**current, "document_id": doc["document_id"], "title": doc["title"], "source_sha256": doc["sha256"],
                    "candidate": candidate, "candidate_error": candidate_error,
                    "has_candidate": candidate_path.exists(), "renderer_available": shutil.which("pdftoppm") is not None,
                    "ocr_available": find_ocr_engine(self.root) is not None}
        except (ValueError, OSError) as exc:
            raise AIError("preparation", str(exc)) from exc

    def preparation_render(self, document_id, page):
        try:
            doc = self.documents(None, [document_id])[0]
            source, _ = source_bytes(self.root, doc)
            return render_page(self.root, source, page).read_bytes()
        except (ValueError, OSError) as exc:
            raise AIError("preparation", str(exc)) from exc

    def operations(self):
        with self.store() as store:
            jobs = [json.loads(row[0]) for row in store.db.execute("SELECT data FROM country_jobs ORDER BY rowid DESC")]
            for job in jobs: job["published"] = store.published(job["id"]) if job["status"] == "completed" else False
        return {"runs": [self.public(j) for j in jobs if j.get("operation")]}

    def operation_result(self, job_id):
        job = self.get(job_id)
        if not (job.get("operation") and job["status"] == "completed" and job.get("result_hash")):
            raise AIError("incomplete", "Analysis is not complete; read its run status and resume if appropriate", 409)
        with self.store() as store:
            result = json.loads(store.get(job["result_hash"]))
            result["published"] = store.published(job_id)
        return result

    def moderate(self, result_id, published):
        require(type(published) is bool, "Choose Publish or Unpublish")
        if result_id.startswith("analysis-"):
            self.operation_result(result_id)
            with self.store() as store:
                store.db.execute("INSERT INTO publication_flags VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET published=excluded.published,updated_at=excluded.updated_at", (result_id, int(published), now()))
            return {"id": result_id, "published": published}
        with self.store() as store:
            return store.moderate(result_id, published)

    def method(self):
        paths = set(CONTEXT_PATHS) | {"src/policytracker/country_runs.py", "src/policytracker/ai_runtime.py",
            "src/policytracker/operations.py", "src/policytracker/preparation.py", "config/operations/tasks.json", "schemas/operations/analysis-request.schema.json"}
        paths.update(p.relative_to(self.root).as_posix() for p in (self.root / "prompts/operations").glob("*.md"))
        paths.update(p for p in ("config/automation.json", "prompts/v2/14-recover-page.md", "src/policytracker/settings.py") if (self.root / p).is_file())
        for route in ROUTES:
            paths.update(compose_v2(self.root, route, {}, {})["component_hashes"])
        return {p: sha((self.root / p).read_bytes()) for p in sorted(paths)}

    def documents(self, country, ids):
        require(isinstance(ids, list) and ids and all(isinstance(i, str) for i in ids) and len(ids) == len(set(ids)),
                "Select one or more distinct documents.")
        inventory = read_json(self.root / "data/manifests/corpus.json")["documents"]
        lookup = {d["document_id"]: d for d in inventory if country is None or d["country_code"] == country}
        require(set(ids) <= set(lookup), "Selected documents must belong to this country inventory.")
        return [lookup[i] for i in sorted(ids)]

    def check_current(self, job):
        require(self.method() == job["method"], "The method or worker changed. Start a new run; completed translations with matching inputs can be reused.")
        for doc in job["documents"]:
            path = (self.root / doc["relative_path"]).resolve()
            require(path.is_relative_to(self.root.resolve()) and path.suffix.lower() == ".pdf", "Invalid source path.")
            require(sha(path.read_bytes()) == doc["sha256"], "A source file changed. Refresh the inventory and start a new run.")
        require(self.page_reviews(job["documents"], tolerant=job.get("automatic", False)) == job.get("page_reviews", {}), "Page preparation changed. Start a new run to preserve historical source preparation.")

    def page_reviews(self, documents, tolerant=False):
        result = {}
        for doc in documents:
            for path in review_paths(self.root, doc["sha256"]):
                result[path.relative_to(self.root).as_posix()] = sha(path.read_bytes())
                try:
                    item = read_review(self.root, doc["sha256"], int(path.stem.removeprefix("page-")))
                except (ValueError, OSError):
                    if tolerant: continue
                    raise
                for key in ("review_image", "ocr_tsv"):
                    if item.get(key):
                        artifact = self.root / item[key]
                        result[item[key]] = sha(artifact.read_bytes())
        return result

    def start(self, session, payload):
        with self.lock, session.lock:
            if self.active:
                raise AIError("busy", "A country is already running. Stop it or wait for it to finish.", 409)
            try:
                operation = normalize_request(self.root, payload["operation"]) if "operation" in payload else None
                if operation:
                    compose_operation(self.root, operation, {})  # Validate before any dispatch.
                country = payload.get("country") if not operation else None
                require(operation or country in COUNTRIES.values(), "Choose a country in this workspace.")
                selection = {k: (operation["model"] if operation else payload).get(k) for k in ("route", "model", "effort")}
                self.check_selection(session, selection)
                documents = self.documents(country, [d for g in operation["source_groups"] for d in g["document_ids"]] if operation else payload.get("document_ids"))
                require(len({d["sha256"] for d in documents}) == len(documents), "Duplicate source bytes are not distinct documents")
                job = {"id": ("analysis-" if operation else "country-") + uuid.uuid4().hex, "country": country or "MULTI", "selection": selection,
                       "document_ids": [d["document_id"] for d in documents], "documents": documents,
                       "operation": operation, "synthetic": self.synthetic,
                       "page_reviews": self.page_reviews(documents, tolerant=True), "automatic": True, "settings": read_settings(self.root),
                       "method": self.method(), "status": "running", "stage": "prepare", "message": "Reading selected documents",
                       "completed": 0, "total": len(documents), "created_at": now(), "profile_id": None, "error": None}
                if operation and operation["task"] != "translate":
                    language = job["settings"]["output_language"]
                    operation["output"]["language"] = "en" if language.lower() == "english" else language
                self.check_current(job)
                with self.store() as store:
                    with store.transaction():
                        for path in job["method"]:
                            require(store.put((self.root / path).read_bytes()) == job["method"][path], "Method changed during preparation.")
                        for doc in documents:
                            require(store.put((self.root / doc["relative_path"]).read_bytes()) == doc["sha256"], "Source changed during preparation.")
                        for path, fingerprint in job["page_reviews"].items():
                            require(store.put((self.root / path).read_bytes()) == fingerprint, "Page review changed during preparation")
                        self.write(store, job)
                self.launch(session, job)
                return self.public(job)
            except (ValueError, TypeError, KeyError) as exc:
                raise AIError("input", str(exc)) from None

    def check_selection(self, session, selection):
        require(selection["route"] in ("codex_chatgpt", "openai_api"), "Choose an AI usage route.")
        session.idle()
        models = self.service.catalog(session, selection["route"])["models"]
        require(any(m["id"] == selection["model"] and selection["effort"] in m["efforts"] for m in models),
                "Choose an available model and reasoning effort in AI connection.")

    def resume(self, session, job_id):
        with self.lock, session.lock:
            if self.active:
                raise AIError("busy", "A country is already running.", 409)
            job = self.get(job_id)
            try:
                require(job["status"] in ("stopped", "failed"), "Only stopped or failed runs can be resumed.")
                require(not needs_source_review(job), "Generate again to start a new run with automatic recovery. This run retains its original preparation.")
                self.check_current(job)
                self.check_selection(session, job["selection"])
            except ValueError as exc:
                raise AIError("resume", str(exc)) from None
            job.update(status="running", error=None, message="Resuming saved steps")
            with self.store() as store:
                self.write(store, job)
            self.launch(session, job)
            return self.public(job)

    def stop(self, job_id):
        with self.lock:
            if self.active != job_id:
                raise AIError("inactive", "This run is no longer active.", 409)
            self.stop_event.set()
            with self.store() as store:
                job = self.get(job_id)
                job.update(status="stopping", message="Finishing active requests, then stopping. Their valid results will be saved.")
                self.write(store, job)
            return self.public(job)

    def launch(self, session, job):
        self.stop_event.clear()
        self.active = job["id"]
        # Connections cannot be changed while the country worker uses them.
        session.jobs[job["id"]] = {"id": job["id"], "status": "running", "kind": "country", **job["selection"]}
        self.thread = threading.Thread(target=self.run, args=(session, job), daemon=True)
        self.thread.start()

    def progress(self, job, stage, message, completed=0, total=1):
        with self.lock:
            if self.stop_event.is_set():
                raise Stopped()
            job.update(stage=stage, message=message, completed=completed, total=total)
            with self.store() as store:
                self.write(store, job)

    def run_batches(self, session, job, items, work, stage, message):
        """Bound dispatch, save in-flight results on stop, and return source order."""
        self.progress(job, stage, message, 0, len(items))
        factory = getattr(self.service, "country_request_group", None)
        # Simple fixture/embedded providers retain the existing serial protocol.
        group_context = factory(session, job["id"]) if factory else nullcontext()
        results = [None] * len(items)
        completed, next_item, failure = 0, 0, None
        with group_context as group, ThreadPoolExecutor(max_workers=2 if factory else 1) as pool:
            pending = {}

            def dispatch():
                nonlocal next_item
                with self.lock:
                    while not self.stop_event.is_set() and next_item < len(items) and len(pending) < (2 if factory else 1):
                        n = next_item
                        pending[pool.submit(work, n, items[n], group)] = n
                        next_item += 1

            dispatch()
            while pending:
                ready, _ = wait(pending, return_when=FIRST_COMPLETED)
                for future in sorted(ready, key=lambda f: pending[f]):
                    n = pending.pop(future)
                    try:
                        results[n] = future.result()
                        completed += 1
                    except Exception as exc:
                        if failure is None:
                            failure = exc
                        # Prevent sibling retries/new requests, but still let its
                        # already running response finish validation and save.
                        self.stop_event.set()
                if not self.stop_event.is_set():
                    self.progress(job, stage, message, completed, len(items))
                    dispatch()
            if failure is not None:
                raise failure
            if self.stop_event.is_set():
                raise Stopped()
        return results

    def reuse_exact_request(self, store, job, key, route, packet, signature, check):
        """Revalidate identical reading/extraction requests in a new run."""
        if route not in ("triage", "translate", "extract"):
            return None
        raw = encoded(packet)
        request_hash = sha(raw)
        candidates = store.db.execute(
            "SELECT s.job_id,s.step,s.signature,s.result_hash,j.data FROM country_steps s "
            "JOIN country_jobs j ON j.id=s.job_id WHERE s.step LIKE ? ORDER BY s.rowid DESC",
            (route + ":%",)).fetchall()
        for candidate in candidates:
            try:
                result = json.loads(store.get(candidate["result_hash"]))
                repaired_extraction = route == "extract" and result.get("attempt", 1) > 1
                if result.get("request_hash") != request_hash and not repaired_extraction:
                    continue
                producer = json.loads(candidate["data"])
                require(type(producer.get("synthetic")) is bool and producer["synthetic"] == self.synthetic,
                        "Cached request belongs to a different real/synthetic scope")
                require(producer["selection"] == result["selection"] == job["selection"], "Cached selection differs")
                origin = producer.get("reused_steps", {}).get(candidate["step"]) or {"job_id": candidate["job_id"], "step": candidate["step"],
                    "result_hash": candidate["result_hash"], "method": producer["method"]}
                original = json.loads(store.get(origin["result_hash"]))
                require(original == result, "Cached origin differs from the reused receipt")
                for fingerprint in origin["method"].values():
                    store.get(fingerprint)
                if route == "extract":
                    self.check_extraction_repair_chain(store, origin, result, packet)
                else:
                    require(store.get(result["request_hash"]) == raw, "Cached request bytes differ")
                response = json.loads(store.get(result["response_hash"]))
                require(response.get("route") == job["selection"]["route"] and
                        response.get("actual_model") == job["selection"]["model"] and
                        response.get("confirmed_effort") == job["selection"]["effort"], "Cached response selection differs")
                raw_output = json.loads(response["text"])
                if "normalization" in result:
                    require(route == "extract", "Unexpected cached normalization")
                    normalized, additions = normalize_extraction_evidence(raw_output, packet["schema"])
                    require(bool(additions) and result["normalization"] == {
                        "kind": "explicit_record_evidence_closure_v1", "additions": additions}, "Cached normalization trace differs")
                    require(normalized == result["output"], "Cached normalization output differs")
                else:
                    require(raw_output == result["output"], "Cached output differs from its model response")
                schema = read_json(self.root / "config/v2/pipelines.json")["routes"][route]["schema"]
                errors = validate_v2(self.root, schema, result["output"])
                require(not errors, "; ".join(errors))
                check(result["output"])
            except (ValueError, TypeError, KeyError):
                continue  # An incompatible receipt cannot substitute for a fresh request.
            # Record the original method separately; the immutable receipt and its
            # original completion time remain unchanged under their existing hash.
            job.setdefault("reused_steps", {})[key] = origin
            self.write(store, job)
            store.db.execute("INSERT OR REPLACE INTO country_steps VALUES(?,?,?,?)",
                             (job["id"], key, signature, candidate["result_hash"]))
            return result["output"]
        return None

    def check_extraction_repair_chain(self, store, origin, result, packet):
        """Prove a saved successful repair belongs to this exact initial request."""
        row = store.db.execute("SELECT signature,result_hash FROM country_steps WHERE job_id=? AND step=?",
                               (origin["job_id"], origin["step"])).fetchone()
        expected_signature = digest({"packet": packet, "selection": result["selection"],
                                     "worker": {p: h for p, h in origin["method"].items() if p.startswith("src/")},
                                     "synthetic": self.synthetic})
        require(row and row["signature"] == expected_signature and row["result_hash"] == origin["result_hash"],
                "Cached extraction base request differs")
        payload, expected = json.loads(packet["input"]), packet
        attempts = store.db.execute("SELECT request_hash,response_hash,error FROM country_attempts WHERE job_id=? AND step=? ORDER BY sequence",
                                    (origin["job_id"], origin["step"])).fetchall()
        for attempt in attempts:
            # This retired rule conflated the reporting party with every
            # affected country. Its repairs may have coerced supported geography.
            require(".geography.country_codes: expected [" not in (attempt["error"] or ""),
                    "Cached extraction used the retired geography constraint; a fresh request is required")
            # Explicit conditional labels may lack their condition in the source.
            # The retired rule could pressure a repair to invent that condition.
            require("conditional target missing condition" not in (attempt["error"] or ""),
                    "Cached extraction used the retired condition constraint; a fresh request is required")
            require(store.get(attempt["request_hash"]) == encoded(expected), "Cached repair request chain differs")
            if attempt["response_hash"] is None:
                require(bool(attempt["error"]), "Cached retry has no recorded error")
                continue  # Transport retries repeat the same request.
            response = json.loads(store.get(attempt["response_hash"]))
            require(response.get("route") == result["selection"]["route"] and
                    response.get("actual_model") == result["selection"]["model"] and
                    response.get("confirmed_effort") == result["selection"]["effort"], "Cached repair response selection differs")
            if attempt["request_hash"] == result["request_hash"] and attempt["response_hash"] == result["response_hash"]:
                require(attempt["error"] is None, "Cached extraction was not accepted")
                return
            require(bool(attempt["error"]), "Cached repair has no preceding validation error")
            expected = compact_packet(compose_v2(self.root, "extract", {
                **payload["task_context"], "repair": repair_feedback(attempt["error"], response["text"])},
                payload["untrusted_source_data"]))
        raise ValueError("Cached accepted extraction attempt is missing")

    def step(self, session, job, key, route, context, data, check, images=None, *, country_group=None):
        if self.stop_event.is_set():
            raise Stopped()
        self.check_current(job)
        # Archive JSON is key-sorted. Canonicalize before composing so a cached
        # extraction produces the same downstream request as a fresh response.
        context, data = json.loads(encoded(context)), json.loads(encoded(data))
        settings = job.get("settings", {})
        preference_keys = {"translate": ("glossary",), "extract": ("instructions", "topic_ids"),
                           "prime": ("instructions", "detail", "output_language"),
                           "focused_analysis": ("instructions", "detail", "output_language"),
                           "comparison": ("instructions", "detail", "output_language"),
                           "workplan": ("instructions", "detail", "output_language"),
                           "briefing": ("instructions", "detail", "output_language")}.get(route, ())
        if settings and preference_keys:
            context["user_preferences"] = {k: settings[k] for k in preference_keys}
        def compose(repair=None):
            if route == "recover":
                path = "prompts/v2/14-recover-page.md"
                raw = (self.root / path).read_bytes()
                return {"route": route, "instructions": raw.decode("utf-8"), "schema": RECOVERY_SCHEMA,
                        "input": encoded({"task_context": context, "untrusted_source_data": data, "repair": repair}).decode(),
                        "component_hashes": {path: sha(raw)}, "images": images or []}
            if key == "analysis" or key.startswith("analysis:"):
                return compact_packet(compose_operation(self.root, job["operation"], {**data, **context, **({"repair": repair} if repair else {})}))
            extra = {"repair": repair} if repair else {}
            if route == "translate" and (job.get("operation") or {}).get("task") == "translate":
                extra["translation_instructions"] = job["operation"]["instructions"]
            packet = compose_v2(self.root, route, {**context, **extra}, data)
            if route == "translate" and (job.get("operation") or {}).get("task") == "translate":
                from .engineering import fingerprint_packet
                path = "prompts/operations/translate.md"
                raw = (self.root / path).read_bytes()
                packet["instructions"] += "\n\n" + raw.decode("utf-8")
                packet["instruction_paths"].append(path)
                packet["component_hashes"][path] = sha(raw)
                packet = fingerprint_packet(packet)
            return compact_packet(packet)
        packet = compose()
        require(all(job["method"].get(p) == h for p, h in packet["component_hashes"].items()), "Method changed while assembling request")
        require(len(encoded(packet)) <= MAX_REQUEST_BYTES,
                "This step exceeds the current single-request size limit. Choose fewer documents for a new run; no source text was dropped.")
        signature = digest({"packet": packet, "selection": job["selection"],
                            "worker": {p:h for p,h in job["method"].items() if p.startswith("src/")}, "synthetic": self.synthetic})
        # Cache reuse can update shared provenance and the job snapshot. Keep
        # it atomic with progress/Stop, while live model calls remain outside.
        with self.lock, self.store() as store:
            if self.stop_event.is_set():
                raise Stopped()
            row = store.db.execute("SELECT result_hash,job_id,step FROM country_steps WHERE signature=? LIMIT 1", (signature,)).fetchone()
            if row:
                result = json.loads(store.get(row[0]))
                if route != "recover" or result["output"]["status"] in ("complete", "nontext"):
                    check(result["output"])
                    producer = store.db.execute("SELECT data FROM country_jobs WHERE id=?", (row["job_id"],)).fetchone()
                    origin = json.loads(producer[0]).get("reused_steps", {}).get(row["step"]) if producer else None
                    if origin:
                        job.setdefault("reused_steps", {})[key] = origin
                        self.write(store, job)
                    store.db.execute("INSERT OR REPLACE INTO country_steps VALUES(?,?,?,?)", (job["id"], key, signature, row[0]))
                    return result["output"]
            reused = self.reuse_exact_request(store, job, key, route, packet, signature, check)
            if reused is not None:
                return reused
        repair = None
        for attempt in range(3):
            if self.stop_event.is_set():
                raise Stopped()
            self.check_current(job)
            request = packet if repair is None else compose(repair_feedback(*repair))
            require(len(encoded(request)) <= MAX_REQUEST_BYTES, "Repair request exceeds the size limit. No partial profile was saved.")
            for retry in range(settings.get("retry_limit", 2) + 1):
                with self.store() as store:
                    request_hash = store.put(encoded(request))
                    attempt_id = store.db.execute("INSERT INTO country_attempts(job_id,step,request_hash) VALUES(?,?,?)",
                                                  (job["id"], key, request_hash)).lastrowid
                try:
                    kwargs = {"country_group": country_group} if country_group is not None else {}
                    response = self.service.generate_json(session, job["selection"], request, **kwargs)
                    break
                except AIError as exc:
                    with self.store() as store:
                        store.db.execute("UPDATE country_attempts SET error=? WHERE sequence=?", (str(exc), attempt_id))
                    if exc.code not in ("provider_error", "network", "api_network", "busy", "incomplete", "usage_limit", "connection_lost", "timeout") or retry == settings.get("retry_limit", 2): raise
                    with self.lock:
                        self.progress(job, job["stage"], "Retrying a temporary connection problem automatically",
                                      job.get("completed", 0), job.get("total", 1))
                    if self.stop_event.wait(2 ** (retry + 1)): raise Stopped()
                    self.check_current(job)
            with self.store() as store:
                response_hash = store.put(encoded(response))
                store.db.execute("UPDATE country_attempts SET response_hash=? WHERE sequence=?", (response_hash, attempt_id))
            self.check_current(job)
            try:
                output = json.loads(response["text"])
                normalization = None
                schema_name = read_json(self.root / "config/v2/pipelines.json")["routes"].get(route, {}).get("schema")
                if route == "extract":
                    output, additions = normalize_extraction_evidence(output, request["schema"])
                    if additions:
                        normalization = {"kind": "explicit_record_evidence_closure_v1", "additions": additions}
                if route not in ("extract", "prime", "recover"):
                    errors = validate_v2(self.root, schema_name, output)
                    require(not errors, "; ".join(errors))
                # These checks combine schema, evidence and acceptance errors.
                check(output)
            except (ValueError, TypeError, KeyError) as exc:
                with self.store() as store:
                    store.db.execute("UPDATE country_attempts SET error=? WHERE sequence=?", (str(exc)[:6000], attempt_id))
                repair = (str(exc), response["text"])
                if attempt == 2:
                    raise ValueError("This step did not pass validation after two repairs: " + str(exc)[:1800]) from None
                continue
            with self.store() as store:
                result = {"output": output, "request_hash": request_hash, "response_hash": response_hash,
                          "selection": job["selection"], "completed_at": now(), "attempt": attempt + 1}
                if normalization:
                    result["normalization"] = normalization
                store.db.execute("INSERT OR REPLACE INTO country_steps VALUES(?,?,?,?)",
                                 (job["id"], key, signature, store.put(encoded(result))))
            return output

    def prepare_sources(self, job):
        if job.get("automatic"):
            return self.prepare_automatically(job)
        sources, issues = [], []
        with self.store() as store:
            for doc in job["documents"]:
                if self.stop_event.is_set():
                    raise Stopped()
                try:
                    pages = inspect_document(self.root, doc, store.get(doc["sha256"]))
                except (ValueError, OSError) as exc:
                    issues.append({"document_id": doc["document_id"], "title": doc["title"], "pages": [], "error": str(exc)})
                    continue
                segments, page_checks, problems = [], [], []
                for page in pages:
                    if self.stop_event.is_set():
                        raise Stopped()
                    number, text, concerns, review = (page[k] for k in ("page", "text", "concerns", "review"))
                    if page["needs_review"]:
                        problems.append({k: page[k] for k in ("page", "concerns", "review_error")})
                        continue
                    page_checks.append({"page": number, "concerns": concerns, "review": review,
                                        "parsed_text_sha256": sha(text.encode("utf-8"))})
                    if review:
                        if review["method"] == "nontext":
                            continue  # Explicitly accounted for in page_checks, never evidence.
                        text = review["text"]
                    # Prefer paragraph/line boundaries; retain every original character.
                    offset, part = 0, 1
                    while offset < len(text):
                        end = min(offset + EXTRACTION_TEXT_LIMIT, len(text))
                        if end < len(text):
                            boundary = text.rfind("\n", offset + EXTRACTION_TEXT_LIMIT // 2, end)
                            if boundary > offset:
                                end = boundary + 1
                        segment = text[offset:end]
                        if segment.strip():
                            segments.append({"id": f'{doc["document_id"]}:p{number}:s{part}', "page": number, "text": segment})
                        offset, part = end, part + 1
                if problems or not segments:
                    issues.append({"document_id": doc["document_id"], "title": doc["title"], "pages": problems,
                                   "error": None if problems else "Document has no readable substantive text after page review"})
                    continue
                sources.append({"document_id": doc["document_id"], "title": doc["title"], "path": doc["relative_path"],
                                "sha256": doc["sha256"], "country_code": doc.get("country_code", job["country"]), "metadata_verified": False,
                                "layout_checked": True, "pages": len(pages), "segments": segments, "page_checks": page_checks})
        if issues:
            raise PreparationRequired(issues)
        return sources

    def prepare_automatically(self, job):
        sources, coverage = [], []
        job["source_coverage"] = coverage
        settings = job.get("settings", read_settings(self.root))
        for doc in job["documents"]:
            self.progress(job, "prepare", "Reading and recovering " + doc["title"])
            try:
                source, raw = source_bytes(self.root, doc)
            except FileNotFoundError:
                coverage.append({"document_id": doc["document_id"], "title": doc["title"], "sha256": doc["sha256"],
                                 "status": "unreadable", "pages": doc.get("pages") or 0, "issues": ["Registered source file is missing"]})
                continue
            try:
                pages = inspect_document(self.root, doc, raw)
            except ValueError as exc:
                try:
                    pages = [{"page": n, "text": "", "concerns": ["parse_failed"], "review": None, "review_error": None}
                             for n in range(1, pdf_page_count(source) + 1)]
                except ValueError:
                    coverage.append({"document_id": doc["document_id"], "title": doc["title"], "sha256": doc["sha256"],
                                     "status": "unreadable", "pages": doc.get("pages") or 0, "issues": [str(exc)]})
                    continue
            segments, checks, problems = [], [], []
            for page in pages:
                number = page["page"]
                if self.stop_event.is_set(): raise Stopped()
                self.progress(job, "prepare", f"Reading {doc['title']} · page {number} of {len(pages)}", number - 1, len(pages))
                recovery_key = f"recover:{doc['document_id']}:{number}"
                signature = digest({"receipt_version": 1, "source": doc["sha256"], "page": number, "review": page.get("review"),
                    "settings": {k:settings[k] for k in ("ocr_languages", "vision_recovery")},
                    "model": job["selection"], "code": job["method"].get("src/policytracker/preparation.py"),
                    "prompt": job["method"].get("prompts/v2/14-recover-page.md")})
                with self.store() as store:
                    row = store.db.execute("SELECT result_hash FROM automatic_pages WHERE signature=?", (signature,)).fetchone()
                    recovered = json.loads(store.get(row[0])) if row else None
                    if recovered:
                        for artifact in recovered["artifacts"]: store.get(artifact["sha256"])
                        if recovered.get("generation_step"):
                            receipt = recovered["generation_step"]
                            saved = json.loads(store.get(receipt["result_hash"]))
                            store.get(saved["request_hash"]); store.get(saved["response_hash"])
                            require(saved["output"]["text"] == recovered["text"], "Cached recovery differs from its recorded response")
                            store.db.execute("INSERT OR REPLACE INTO country_steps VALUES(?,?,?,?)",
                                (job["id"], recovery_key, receipt["signature"], receipt["result_hash"]))
                if recovered is None:
                    def visual(image, data):
                        try:
                            return self.step(self.preparation_session, job, recovery_key, "recover", {}, data,
                                recovery_check, images=[{"path": image.relative_to(self.root).as_posix(), "sha256": sha(image.read_bytes())}])
                        except AIError as exc:
                            if exc.code in ("authentication", "access", "restricted_runtime", "session_expired"): raise
                            raise ValueError(str(exc)) from exc
                    recovered = recover_page(self.root, doc, page, settings, visual if getattr(self, "preparation_session", None) else None)
                    recovered.update(source_sha256=doc["sha256"], page=number, text_sha256=sha(recovered["text"].encode("utf-8")))
                    with self.store() as store:
                        if recovered["method"] == "vision":
                            receipt = store.db.execute("SELECT signature,result_hash FROM country_steps WHERE job_id=? AND step=?",
                                                       (job["id"], recovery_key)).fetchone()
                            if receipt:
                                recovered["generation_step"] = dict(receipt)
                        for artifact in recovered["artifacts"]:
                            require(store.put((self.root / artifact["path"]).read_bytes()) == artifact["sha256"], "Recovered page artifact changed")
                        # Incomplete recovery is retried on a later run, never permanently cached as success.
                        if recovered["status"] in ("complete", "nontext"):
                            store.db.execute("INSERT OR REPLACE INTO automatic_pages VALUES(?,?)", (signature, store.put(encoded(recovered))))
                checks.append({"page": number, "concerns": page["concerns"], "review": page.get("review"),
                               "parsed_text_sha256": sha(page["text"].encode("utf-8")), "automatic": recovered})
                if recovered["status"] in ("partial", "unreadable"):
                    problems.append({"page": number, "status": recovered["status"], "notes": recovered["notes"]})
                text = recovered["text"]
                offset, part = 0, 1
                while offset < len(text):
                    end = min(offset + EXTRACTION_TEXT_LIMIT, len(text))
                    if end < len(text):
                        boundary = text.rfind("\n", offset + EXTRACTION_TEXT_LIMIT // 2, end)
                        if boundary > offset: end = boundary + 1
                    if text[offset:end].strip():
                        segments.append({"id": f"{doc['document_id']}:p{number}:s{part}", "page": number, "text": text[offset:end]})
                    elif segments and segments[-1]["page"] == number:
                        segments[-1]["text"] += text[offset:end]
                    offset, part = end, part + 1
            coverage.append({"document_id": doc["document_id"], "title": doc["title"], "sha256": doc["sha256"], "pages": len(pages),
                             "status": "partial" if problems else "complete", "issues": problems})
            if segments:
                sources.append({"document_id": doc["document_id"], "title": doc["title"], "path": doc["relative_path"],
                    "sha256": doc["sha256"], "country_code": doc["country_code"], "metadata_verified": False,
                    "layout_checked": True, "pages": len(pages), "segments": segments, "page_checks": checks})
            else:
                coverage[-1].update(status="unreadable", issues=problems or ["No substantive source text"])
        job["source_coverage"] = coverage
        require(sources, "No usable source evidence could be recovered. Existing published results are unchanged.")
        return sources

    def operation_metadata(self, session, job, sources, profiles):
        """Resolve eligibility before spending requests on translation/extraction."""
        request = job["operation"]
        if request["task"] == "translate":
            # Reading copies make no national attribution or edition-comparison claim.
            return [{"id": s["document_id"], "country_code": s["country_code"], "verified": False} for s in sources]
        metadata = [{"id": p["input_id"], "country_code": p["geography"]["country_codes"][0],
                     "instrument": p["instrument_type"], "verified": True,
                     "edition_id": p["input_id"], "edition_order": p["publication_date"]} for p in profiles]
        if request["task"] == "compare":
            self.progress(job, "prepare", "Checking comparison editions and equivalent copies")
            samples = {s["document_id"]: s["segments"][:3] + s["segments"][3:][-2:] for s in sources}
            pairs = [(a, b) for i, a in enumerate(metadata) for b in metadata[i+1:]
                     if (a["country_code"], a["instrument"]) == (b["country_code"], b["instrument"])]
            def check_pairs(output):
                supplied = {s["id"] for rows in samples.values() for s in rows}
                for a, b in pairs:
                    relations = [r for r in output["relationships"] if set(r["input_ids"]) == {a["id"], b["id"]}]
                    require(len(relations) == 1 and relations[0]["kind"] in ("revision", "translation", "duplicate"),
                            "Comparison edition relationship is uncertain; verify the selected editions")
                    require(relations[0]["evidence_ids"] and set(relations[0]["evidence_ids"]) <= supplied,
                            "Edition relationship needs supplied source locators")
                    require(all(set(relations[0]["evidence_ids"]) & {s["id"] for s in samples[d]} for d in (a["id"], b["id"])),
                            "Edition relationship must cite both documents")
            if pairs:
                checked = self.step(session, job, "comparison-editions", "triage",
                    {"purpose": "Verify every supplied pair as revision, translation, duplicate or unknown. Do not infer distinct editions from filenames.",
                     "pairs": [[a["id"], b["id"]] for a, b in pairs]},
                    {"document_profiles": profiles, "source_samples": samples}, check_pairs)
                families = {item["id"]: item["id"] for item in metadata}
                def family(key):
                    while families[key] != key:
                        key = families[key]
                    return key
                for relation in checked["relationships"]:
                    if relation["kind"] in ("translation", "duplicate"):
                        require(set(relation["input_ids"]) <= set(families) and len(relation["input_ids"]) >= 2, "Unknown edition relation inputs")
                        shared = family(relation["input_ids"][0])
                        for doc_id in relation["input_ids"][1:]:
                            families[family(doc_id)] = shared
                for item in metadata:
                    item["edition_id"] = family(item["id"])
            if request["comparison_mode"] == "revision":
                for item in metadata:
                    date = item["edition_order"]
                    require(isinstance(date, str) and re.fullmatch(r"\d{4}(?:-\d{2}(?:-\d{2})?)?", date),
                            "Revision comparison requires source-supported edition dates")
                    require(date[:4] in " ".join(s["text"] for s in samples[item["id"]]), "Edition year has no support in the metadata sample")
                require(len({len(m["edition_order"]) for m in metadata}) == 1, "Edition dates have incompatible precision")
        validate_source_groups(request, metadata,
            unavailable_ids={d["document_id"] for d in job.get("source_coverage", []) if d["status"] == "unreadable"})
        return metadata

    def run_operation(self, session, job, sources, extraction, profiles, metadata, note_scopes=None):
        request = job["operation"]
        scoped = scoped_evidence(self.root, request, extraction)
        self.progress(job, "analysis", "Preparing the requested analysis from validated evidence")
        task = next(t for t in read_json(self.root / "config/operations/tasks.json")["tasks"] if t["id"] == request["task"])
        parts = synthesis_batches(scoped, note_scopes=note_scopes)
        outputs = []
        partial = any(d["status"] != "complete" for d in job.get("source_coverage", []))
        for i, part in enumerate(parts):
            outputs.append(self.step(session, job, "analysis" if len(parts)==1 else f"analysis:{i}", task["route"], {},
                {"extraction": synthesis_evidence(part), "document_metadata": metadata,
                 "segment_documents": {s["id"]: d["document_id"] for d in sources for s in d["segments"]},
                 "no_matches": not part["records"], "application_calculations": [],
                 "delivery_checks": delivery_checks(request, part) if request["task"] == "gaps" else {},
                 "source_coverage": job.get("source_coverage", []), "batch": {"number": i+1, "total": len(parts)},
                 "coverage_note": "Every readable source segment was processed. This synthesis covers the supplied evidence batch. Never infer policy absence from missing content or another batch."},
                lambda output: validate_operation_output(self.root, request, self.coverage_output(job, output), part, sources, partial=partial)))
        result = self.coverage_output(job, merge_synthesis(outputs))
        validate_operation_output(self.root, request, result, scoped, sources, partial=partial)
        self.save_operation(job, sources, scoped, result, profiles, full_extraction=extraction)

    def save_operation(self, job, sources, extraction, output, profiles, full_extraction=None):
        output = self.coverage_output(job, output)
        self.check_current(job)
        with self.lock:
            if self.stop_event.is_set():
                raise Stopped()
            with self.store() as store, store.transaction():
                steps = [dict(row) for row in store.db.execute("SELECT step,signature,result_hash FROM country_steps WHERE job_id=? ORDER BY step", (job["id"],))]
                receipts = []
                for step in steps:
                    saved = json.loads(store.get(step["result_hash"]))
                    response = json.loads(store.get(saved["response_hash"]))
                    receipts.append({"step": step["step"], "request_hash": saved["request_hash"], "response_hash": saved["response_hash"],
                                     **({"normalization": saved["normalization"]} if "normalization" in saved else {}),
                                     **{key: response.get(key) for key in ("request_id", "actual_model", "confirmed_effort", "usage")}})
                result = {"id": job["id"], "format": "local-analysis-1", "created_at": now(), "synthetic": self.synthetic,
                          "request": job["operation"], "sources": sources, "document_profiles": profiles,
                          "extraction": extraction, "output": output,
                          "evidence_table": evidence_table(job["operation"], extraction),
                          "coverage": (full_extraction or extraction)["coverage"],
                          "source_coverage": job.get("source_coverage", []),
                          "full_extraction_hash": store.put(encoded(full_extraction or extraction)),
                          "generation": {"selection": job["selection"], "method": job["method"], "reused_steps": job.get("reused_steps", {}), "settings": job.get("settings", {}), "selected_documents": job["documents"], "page_reviews": job.get("page_reviews", {}), "steps": steps, "step_receipts": receipts,
                                         "attempts": [dict(row) for row in store.db.execute(
                                             "SELECT step,request_hash,response_hash,error FROM country_attempts WHERE job_id=? ORDER BY sequence", (job["id"],))]},
                          "validation": {"software_checks": "passed", "semantic_accuracy": "not_certified"},
                          "limitations": ["Source-record counts are not unique policy counts.", "Missing information applies only to selected sources.",
                                          "Automated reading and metadata checks do not certify translation, tables or extraction recall."]}
                job["result_hash"] = store.put(encoded(result))
                job.update(status="completed", stage="complete", message="Analysis published", published=True, completed=1, total=1, error=None)
                self.write(store, job)

    def run(self, session, job):
        try:
            self.preparation_session = session
            self.progress(job, "prepare", "Reading selected documents", 0, len(job["documents"]))
            with self.store() as store:
                sources = json.loads(store.get(job["prepared_sources"])) if job.get("prepared_sources") else None
            if sources is None:
                sources = self.prepare_sources(job)
                with self.store() as store:
                    job["prepared_sources"] = store.put(encoded(sources))
                    self.write(store, job)
            group = "country-" + digest([(s["document_id"], s["sha256"]) for s in sources])[:20]
            operation = job.get("operation")
            context = {"country_codes": sorted({s["country_code"] for s in sources}), "source_group_ids": [group],
                       "scope": "selected documents only; never infer national absence or implementation progress",
                       "source_coverage": job.get("source_coverage", [])}
            document_profiles = []
            for n, source in enumerate(sources):
                self.progress(job, "prepare", "Checking country and document scope: " + source["title"], n, len(sources))
                sample = source["segments"][:3] + source["segments"][3:][-2:]
                def triage_check(output):
                    rows = output["document_profiles"]
                    require(len(rows) == 1 and rows[0]["input_id"] == source["document_id"], "Document metadata must match the selected source.")
                    item = rows[0]
                    if operation and operation["task"] == "translate":
                        require(item["disposition"] not in ("quarantine", "needs_ocr"), "Recovered translation source must be readable")
                        return  # Translation is not a national-policy attribution decision.
                    require(item["disposition"] in (("prime_candidate", "ad_hoc_support") if operation else ("prime_candidate",))
                            and item["instrument_type"] in (("NDC", "NAP", "NAP_annex", "sectoral_NAP", "support") if operation else ("NDC", "NAP", "NAP_annex", "sectoral_NAP"))
                            and item["geography"]["country_codes"] == [source["country_code"]] and item["geography"]["scope"] in ("national", "subnational")
                            and not item["issues"], "Document attribution or eligibility could not be established. Regional/EU targets cannot be treated as national targets.")
                    require(item["metadata_evidence_ids"] and set(item["metadata_evidence_ids"]) <= {s["id"] for s in sample},
                            "Metadata must cite supplied segment IDs.")
                    require(item["geography"]["evidence_ids"] and set(item["geography"]["evidence_ids"]) <= {s["id"] for s in sample},
                            "Country attribution must cite supplied segment IDs.")
                metadata = self.step(session, job, "triage:" + source["document_id"], "triage",
                          {**document_context(source, context), "metadata_evidence_ids_use_segment_ids": True, "sample_only": True},
                          {"input_id": source["document_id"], "segments": sample}, triage_check)
                document_profiles.extend(metadata["document_profiles"])
                source["metadata_verified"] = True
            context["document_profiles"] = document_profiles
            operation_metadata = self.operation_metadata(session, job, sources, document_profiles) if operation else None
            batches = [(s, b) for s in sources for b in chunks(s["segments"])]
            for n, (source, batch) in enumerate(batches):
                self.progress(job, "translate", "Preparing English: " + source["title"], n, len(batches))
                def translate(batch, key):
                    try:
                        surrounding = [{k: s[k] for k in ("id", "page", "text")} for s in adjacent_segments(source, batch)]
                        return self.step(session, job, key, "translate", {**document_context(source, context), "owned_segment_ids": [s["id"] for s in batch]},
                            {"segments": batch, "context_segments": surrounding}, lambda out: check_translation(out, batch))
                    except (ValueError, AIError) as exc:
                        if not job.get("automatic") or len(batch)<2 or (isinstance(exc, AIError) and exc.code not in ("incomplete", "empty_response")): raise
                        self.check_current(job)
                        midpoint = len(batch)//2
                        left, right = translate(batch[:midpoint], key+":a"), translate(batch[midpoint:], key+":b")
                        return {"segments": left["segments"] + right["segments"]}
                translated = translate(batch, f"translate:{n}")
                lookup = {row["segment_id"]: row for row in translated["segments"]}
                for segment in batch:
                    row = lookup[segment["id"]]
                    segment.update(language=row["source_language"],
                                   english_text=row["english_text"], translation_method=row["method"], term_decisions=row["term_decisions"],
                                   translation_notes=row.get("notes", []))
            if operation and operation["task"] == "translate":
                self.save_operation(job, sources, {"evidence": [], "records": [], "coverage": [], "notes": [], "issues": []},
                                    {"availability": "complete_in_declared_scope", "limitations": ["Aligned extracted text; OCR and table structure require source inspection."]}, document_profiles)
                return
            extraction = {"evidence": [], "records": [], "coverage": [], "notes": [], "issues": []}
            all_segments = {s["id"]: s["text"] for source in sources for s in source["segments"]}
            planned = [(source, batch, surrounding) for source in sources
                       for batch, surrounding in extraction_batches(self.root, source, document_context(source, context), job.get("settings"))]
            def extract_batch(n, item, country_group):
                source, batch, surrounding = item
                def extraction_check(output):
                    errors = extraction_errors(self.root, output, source["country_code"],
                        source_segments={s["id"]: s["text"] for s in batch + surrounding}, owned_segment_ids=[s["id"] for s in batch])
                    require(not errors, "; ".join(errors))
                output = self.step(session, job, f"extract:{n}", "extract", {**document_context(source, context), "owned_segment_ids": [s["id"] for s in batch]},
                    extraction_source_data(source, batch, surrounding), extraction_check, country_group=country_group)
                return namespace_extraction(output, f"b{n}:")
            extraction_parts = self.run_batches(session, job, planned, extract_batch, "extract", "Extracting evidence from selected documents")
            for output in extraction_parts:
                for key, values in output.items():
                    extraction[key].extend(values)
            errors = validate_v2(self.root, "extraction", extraction, source_segments=all_segments, owned_segment_ids=list(all_segments))
            require(not errors, "; ".join(errors))
            if operation:
                self.run_operation(session, job, sources, extraction, document_profiles, operation_metadata, note_scopes=extraction_parts)
                return
            parts = synthesis_batches(extraction, note_scopes=extraction_parts)
            context["compact_evidence_note"] = "Empty/null fields and validation pointers are omitted from synthesis only. Every record and original quote remains archived. Each batch covers its supplied records; never infer policy absence from other batches."
            reconciliation = {"groups": [], "relations": [], "changes": [], "issues": []}
            def reconcile_part(i, part, country_group):
                out = self.step(session, job, "reconcile" if len(parts)==1 else f"reconcile:{i}", "reconcile",
                    {**context, "mode": "proposals_only; retain every source record; do not claim a canonical winner"},
                    synthesis_evidence(part), lambda out: check_reconciliation(out, part, sources, document_profiles), country_group=country_group)
                # Cached outputs can also be referenced by immutable receipts.
                out = json.loads(encoded(out))
                if len(parts)>1:
                    for group_row in out["groups"]:
                        group_row["local_group_id"] = f"part{i}:" + group_row["local_group_id"]
                return out
            reconciled_parts = self.run_batches(session, job, parts, reconcile_part, "reconcile", "Linking repeated commitments and checking differences")
            for out in reconciled_parts:
                for key in reconciliation: reconciliation[key].extend(out[key])
            check_reconciliation(reconciliation, extraction, sources, document_profiles)
            bundle = {"format": "local-profile-1", "country_code": job["country"], "synthetic": self.synthetic,
                      "source_group_id": group, "sources": sources, "extraction": extraction,
                      "provenance_note": "Generated locally from selected sources. Automated metadata and text checks; semantic accuracy, translation quality and PDF layout are not certified."}
            if job.get("automatic"):
                bundle["source_coverage"] = job.get("source_coverage", [])
            def report_part(i, part, country_group):
                def check_report(out):
                    errors = validate_v2(self.root, "report", out,
                        known_evidence_ids={e["local_id"] for e in part["evidence"]},
                        known_record_ids={r["local_id"] for r in part["records"]})
                    require(not errors, "; ".join(errors))
                    validate_bundle(self.root, {**bundle, "report": self.coverage_output(job, out)})
                return self.step(session, job, "overview" if len(parts)==1 else f"overview:{i}", "prime", {**context,
                    "batch": {"number": i+1, "total": len(parts)},
                    "required_sections": read_json(self.root / "config/v2/pipelines.json")["features"]["prime"]["required_sections"],
                    "known_commitment_ids": [r["local_id"] for r in part["records"] if r["kind"] == "commitment"],
                    "limitations": ["Automated source checks do not certify PDF layout, translation quality or extraction recall.",
                                    "Reconciliation links are proposals; conflicting source variants are retained."]},
                    {"extraction": synthesis_evidence(part), "reconciliation": reconciled_parts[i]}, check_report, country_group=country_group)
            reports = self.run_batches(session, job, parts, report_part, "overview", "Writing the Overview from saved evidence")
            report = merge_synthesis(reports)
            report = self.coverage_output(job, report)
            bundle["report"] = report
            self.progress(job, "validate", "Checking sources, coverage and citations before saving")
            self.check_current(job)
            with self.lock:
                if self.stop_event.is_set():
                    raise Stopped()
                with self.store() as store:
                    steps = [dict(row) for row in store.db.execute("SELECT step,signature,result_hash FROM country_steps WHERE job_id=? ORDER BY step", (job["id"],))]
                    receipts = []
                    for step in steps:
                        saved = json.loads(store.get(step["result_hash"]))
                        response = json.loads(store.get(saved["response_hash"]))
                        receipts.append({"step": step["step"], "completed_at": saved["completed_at"],
                                         **({"normalization": saved["normalization"]} if "normalization" in saved else {}),
                                         **{key: response.get(key) for key in ("request_id", "actual_model", "confirmed_effort", "usage")}})
                    generation = {"run_id": job["id"], "selection": job["selection"], "method": job["method"], "reused_steps": job.get("reused_steps", {}),
                                  "step_receipts": receipts,
                                  "prepared_sources": job["prepared_sources"], "page_reviews": job.get("page_reviews", {}),
                                  "selected_documents": job["documents"], "settings": job.get("settings", {}),
                                  "steps": steps, "reconciliation": store.put(encoded(reconciliation)),
                                  "attempts": [dict(row) for row in store.db.execute(
                                      "SELECT step,request_hash,response_hash,error FROM country_attempts WHERE job_id=? ORDER BY sequence", (job["id"],))]}
                    # Reuse an already prepared version after a crash around the final commit.
                    if not job["profile_id"]:
                        job["profile_id"] = store.prepare(bundle, generation=generation)
                        self.write(store, job)
                    store.complete(job["profile_id"])
                    job.update(status="completed", message="Country Profile published", published=True, completed=1, total=1, error=None)
                    self.write(store, job)
        except Stopped:
            job.update(status="stopped", message="Stopped. Completed steps are saved; resume when ready.")
        except PreparationRequired as exc:
            job.update(status="failed", message="Source documents need review before generation", error=str(exc),
                       required_action="review_sources", preparation_issues=exc.documents)
        except (AIError, ValueError, OSError) as exc:
            job.update(status="failed", message="This run needs attention", error=str(exc)[:2400])
        except Exception:
            job.update(status="failed", message="This run needs attention", error="The local worker could not finish. Completed steps remain saved; resume to retry.")
        finally:
            with self.lock:
                try:
                    with self.store() as store:
                        self.write(store, job)
                finally:
                    # A failed disk write must not leave the in-memory worker or
                    # connection permanently busy. Persisted running state is
                    # conservatively recovered as stopped on server restart.
                    session.jobs[job["id"]]["status"] = job["status"]
                    self.active = None
                    self.preparation_session = None

    @staticmethod
    def coverage_output(job, output):
        problems = [d for d in job.get("source_coverage", []) if d["status"] != "complete"]
        if not problems:
            return output
        result = json.loads(encoded(output))
        if "availability" in result:
            result["availability"] = "partial"
        note = "Incomplete source coverage: " + "; ".join(f"{d['title']} ({d['status']})" for d in problems) + ". Unreadable material is not evidence of policy absence."
        result["limitations"] = list(dict.fromkeys(result.get("limitations", []) + [note]))
        return result

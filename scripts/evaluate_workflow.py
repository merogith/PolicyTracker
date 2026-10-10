"""Prepare the bounded five-page country-pipeline evaluation; run only if authorized.

Default is offline preparation. --run uses the existing local ChatGPT account;
there is no API fallback, login flow, profile store, publication or live test call.
Resume the SAME output directory to retain the global call/repair limits.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pypdf import PdfReader
from policytracker.ai_runtime import AIError, AIService, AISession
from policytracker.country_runs import (MAX_REQUEST_BYTES, EXTRACTION_TEXT_LIMIT, ROUTES, check_translation,
    check_reconciliation, chunks, namespace_extraction, synthesis_evidence, extraction_batches, document_context)
from policytracker.engineering import (compose_v2, digest, read_json, validate_v2, _walk,
                                     extraction_errors, compact_packet, repair_feedback)
from policytracker.profiles import CONTEXT_PATHS, encoded, now, require, sha

SELECTION = {"route": "codex_chatgpt", "model": "gpt-6-astra", "effort": "xhigh"}
SAMPLES = (
    ("doc-a2b2a58ff2573b05", [1, 2], "4185e78f05f6724e984b837c76c5ebc395240e3e6d2a3fe0757860e17317006f"),
    ("doc-0c3ac57eba1f25c4", [1, 2, 3], "879977c958b50ff1daf6af6461ae35b840d6d119f18e1ea2dd95089a864add76"),
)
SCOPE = {
    "sample_only": True,
    "scope": "Evaluation of supplied page-text samples only: earlier NDC physical pages 1-2 of 8; later NDC pages 1-3 of 25. Not a full-document translation, complete country assessment or Country Profile.",
    "limitations": [
        "Unselected pages, other documents and the rest of the country's policies are outside scope.",
        "Graph data not represented by the supplied extracted text is outside scope; do not infer plotted values.",
        "The earlier page 2 extracted layer includes Cyrillic chart labels in addition to visible English; preserve and disclose the mixed extracted layer.",
        "Later page 3 includes a raster graph. The surrounding prose is supplied; image/chart recovery and layout certification are not part of this text sample.",
    ],
}
PLAN_ID = "five-page-country-pipeline-fresh-preparation-v2"
BASELINE_CALLS = 11
REUSE_STEPS = ("1-triage", "1-translate", "2-triage", "2-translate")


def save_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)


def frozen_method():
    paths = set(CONTEXT_PATHS) | {
        "scripts/evaluate_workflow.py", "src/policytracker/country_runs.py", "src/policytracker/ai_runtime.py",
        "src/policytracker/operations.py", "src/policytracker/preparation.py",
        "config/operations/tasks.json", "schemas/operations/analysis-request.schema.json",
        "evals/workflow-live-evaluation.md",
    }
    paths.update(p.relative_to(ROOT).as_posix() for p in (ROOT / "prompts/operations").glob("*.md"))
    for route in ROUTES:
        paths.update(compose_v2(ROOT, route, {}, {})["component_hashes"])
    return {p: sha((ROOT / p).read_bytes()) for p in sorted(paths)}


def sources():
    inventory = {d["document_id"]: d for d in read_json(ROOT / "data/manifests/corpus.json")["documents"]}
    result = []
    for doc_id, pages, fingerprint in SAMPLES:
        doc = inventory[doc_id]
        source = (ROOT / doc["relative_path"]).resolve()
        require(source.is_relative_to(ROOT / "data/sources") and sha(source.read_bytes()) == fingerprint == doc["sha256"], "Sample source fingerprint/path changed")
        pdf = PdfReader(source)
        segments = [{"id": f"{doc_id}:p{page}:s1", "page": page, "text": pdf.pages[page - 1].extract_text() or ""} for page in pages]
        require(all(s["text"].strip() and len(s["text"]) <= 6000 for s in segments), "Sample requires a revised segmentation plan")
        require(len(chunks(segments)) == 1, "Sample needs more than one standard batch; stop rather than expand the approved plan")
        result.append({"document_id": doc_id, "title": doc["title"], "country_code": doc["country_code"],
                       "sha256": fingerprint, "path": doc["relative_path"], "pages": len(pdf.pages),
                       "sample_pages": pages, "segments": segments})
    return result


def with_scope(packet, repair=None):
    payload = json.loads(packet["input"])
    payload["task_context"].update(copy.deepcopy(SCOPE))
    if repair:
        payload["task_context"]["repair"] = repair_feedback(repair["errors"], repair["previous_output"])
    packet["input"] = json.dumps(payload, ensure_ascii=False)
    packet["input_hash"] = digest(payload)
    return compact_packet(packet)


def sample_context(doc):
    return {"country_codes": ["BLR"], "source_group_ids": [doc["document_id"]], "sample_only": True,
            "metadata_evidence_ids_use_segment_ids": True, "owned_segment_ids": [s["id"] for s in doc["segments"]]}


def preparation_packet(root, route, doc, triage=None):
    """Reconstruct the four original preparation requests without executing archived code."""
    context = sample_context(doc)
    if route == "triage":
        return with_scope(compose_v2(root, route, context,
                          {"input_id": doc["document_id"], "segments": doc["segments"]}))
    context["document_profiles"] = triage["document_profiles"]
    packet = compose_v2(root, "translate", {**context,
                        "translation_instructions": "Use LULUCF for ЗИЗЛХ; preserve all conditional clauses."},
                        {"segments": doc["segments"]})
    path = "prompts/operations/translate.md"
    # The original evaluator normalized this supplement's line endings. Retain
    # that exact assembly for compatibility instead of silently changing reuse.
    packet["instructions"] += "\n\n" + (root / path).read_text(encoding="utf-8")
    packet["component_hashes"][path] = sha((root / path).read_bytes())
    packet["instruction_paths"].append(path)
    return with_scope(packet)


def fresh_preparation_packet(root, route, doc, triage=None):
    """Use the current worker's document context, with explicit sample boundaries."""
    context = document_context(doc, {})
    if route == "triage":
        return with_scope(compose_v2(root, route, {**context, "metadata_evidence_ids_use_segment_ids": True,
                          "sample_only": True}, {"input_id": doc["document_id"], "segments": doc["segments"]}))
    context = document_context(doc, {"document_profiles": triage["document_profiles"]})
    context.update(owned_segment_ids=[s["id"] for s in doc["segments"]],
                   user_preferences={"glossary": "Use LULUCF for ЗИЗЛХ; preserve all conditional clauses."})
    return with_scope(compose_v2(root, "translate", context, {"segments": doc["segments"], "context_segments": []}))


def check_triage(result, doc):
    errors = validate_v2(ROOT, "triage", result)
    require(not errors, "; ".join(errors))
    require(len(result["document_profiles"]) == 1, "Expected one profile for the supplied sample")
    profile = result["document_profiles"][0]
    require(profile["input_id"] == doc["document_id"] and profile["geography"]["country_codes"] == ["BLR"], "Incorrect source/country attribution")
    require(profile["instrument_type"] == "NDC" and not profile["issues"], "Incorrect or unresolved sampled instrument")
    known = {s["id"] for s in doc["segments"]}
    require(profile["metadata_evidence_ids"] and set(profile["metadata_evidence_ids"]) <= known, "Metadata lacks sample locators")
    require(profile["geography"]["evidence_ids"] and set(profile["geography"]["evidence_ids"]) <= known, "Country lacks sample locators")


def model_facing(packet):
    """Only data actually sent as instructions, input and output contract.

    Component hashes can change when pipeline descriptions change; instruction
    bytes and compact JSON input bytes must still be identical.
    """
    return {key: packet[key] for key in ("route", "instructions", "input", "schema")}


def verified_reuse(archive, documents):
    """Validate a closed ledger's four preparation results; never fall back to inference."""
    archive = Path(archive).resolve()
    raw = {}
    def read(relative):
        path = (archive / relative).resolve()
        require(path.is_relative_to(archive), "Reuse archive path escapes its directory")
        raw[relative] = path.read_bytes()
        return json.loads(raw[relative])
    manifest = read("manifest.json")
    require(read("execution-summary.json").get("status", "").startswith("closed"), "Reuse requires a closed prior ledger")
    require(manifest["selection"] == SELECTION and manifest["scope"] == SCOPE, "Reuse selection or sample scope changed")
    require(manifest["source_hashes"] == {d: h for d, _, h in SAMPLES}, "Reuse source fingerprints differ")
    require(read("source-samples.json") == documents, "Reuse source samples differ from current original bytes")
    for path, expected in manifest["method"].items():
        relative = "method/" + path
        target = (archive / relative).resolve()
        require(target.is_relative_to(archive / "method"), "Reuse method path escapes its archive")
        raw[relative] = target.read_bytes()
        require(sha(raw[relative]) == expected, "Reuse archived method was changed: " + path)
    dispatches = {}
    for path in sorted((archive / "calls").glob("*/dispatch.json")):
        dispatch = read(path.relative_to(archive).as_posix())
        if dispatch["step"] in REUSE_STEPS:
            require(dispatch["step"] not in dispatches, "Reuse preparation has multiple dispatches; explicit review required")
            dispatches[dispatch["step"]] = (path.parent.relative_to(archive).as_posix(), dispatch)
    require(set(dispatches) == set(REUSE_STEPS), "Four verified preparation dispatches are required for this call plan")
    metadata, translated_documents, receipts = [], copy.deepcopy(documents), []
    for index, doc in enumerate(documents):
        triage = None
        for route in ("triage", "translate"):
            step = f"{index+1}-{route}"
            folder, dispatch = dispatches[step]
            require(dispatch["selection"] == SELECTION and dispatch["route"] == route and not dispatch["repair"], "Reuse dispatch selection/route/repair differs")
            request = read(folder + "/request.json")
            require(dispatch["packet_hash"] == request["packet_hash"] == digest({k:v for k,v in request.items() if k != "packet_hash"}), "Reuse request fingerprint differs")
            require(dispatch["packet_bytes"] == len(encoded(request)), "Reuse request size differs")
            reconstruct = fresh_preparation_packet if manifest.get("plan_id") == PLAN_ID else preparation_packet
            reconstructed = reconstruct(archive / "method", route, doc, triage)
            require(reconstructed == request, "Archived preparation request cannot be reconstructed exactly: " + step)
            current = fresh_preparation_packet(ROOT, route, doc, triage)
            require(model_facing(current) == model_facing(request), "Current model-facing preparation is incompatible with reuse: " + step)
            validation = read(folder + "/validation.json")
            require(validation["passed"] is True, "Reuse preparation did not pass its archived checks")
            response = read(folder + "/response.json")
            require(response.get("actual_model") == SELECTION["model"] and response.get("confirmed_effort") == SELECTION["effort"]
                    and all(response.get(k) == v for k, v in SELECTION.items()) and response.get("request_id"), "Reuse lacks the exact provider selection receipt")
            result = read("outputs/" + step + ".json")
            require(result == json.loads(response["text"]), "Reuse saved output differs from its provider response")
            if route == "triage":
                check_triage(result, doc)
                triage = result
                metadata.extend(result["document_profiles"])
            else:
                errors = validate_v2(ROOT, "translation", result)
                require(not errors, "; ".join(errors))
                check_translation(result, doc["segments"])
                lookup = {row["segment_id"]: row for row in result["segments"]}
                for segment in translated_documents[index]["segments"]:
                    row = lookup[segment["id"]]
                    segment.update(english_text=row["english_text"], language=row["source_language"],
                                   translation_method=row["method"], term_decisions=row["term_decisions"],
                                   translation_notes=row.get("notes", []))
            receipts.append({"step": step, "source_call": dispatch["call"], "request_id": response["request_id"],
                             "request_sha256": sha(raw[folder + "/request.json"]), "response_sha256": sha(raw[folder + "/response.json"]),
                             "output_sha256": sha(raw["outputs/" + step + ".json"]), "model_facing_hash": digest(model_facing(current)),
                             "selection": SELECTION, "validation": "archived pass and current validation; no new inference"})
    return {"metadata": metadata, "documents": translated_documents, "receipts": receipts,
            "files": raw, "file_hashes": {path: sha(value) for path, value in raw.items()}}


def preflight_plan(documents):
    """Check the fixed source/batch plan before creating a connection.

    Translation, metadata and extraction responses do not exist yet. Their
    dependent packets are checked again at dispatch, never assumed to fit from
    these source-envelope measurements.
    """
    require(len(documents) == 2 and [len(d["segments"]) for d in documents] == [2, 3],
            "Source segment counts require a revised bounded plan before inference")
    packets, batches = [], []
    for index, doc in enumerate(documents):
        require(all(len(s["text"]) <= EXTRACTION_TEXT_LIMIT for s in doc["segments"]),
                "Source segmentation requires a revised bounded plan before inference")
        triage = fresh_preparation_packet(ROOT, "triage", doc)
        packets.append({"step": f"{index+1}-triage", "packet_bytes": len(encoded(triage)), "measurement": "exact initial request"})
        # Include every source segment as possible metadata context for sizing;
        # actual metadata remains exclusively the checked triage response.
        ids = [s["id"] for s in doc["segments"]]
        context = document_context(doc, {"sample_only": True, "document_profiles": [{"input_id": doc["document_id"],
                                   "metadata_evidence_ids": ids, "geography": {"evidence_ids": ids}}]})
        planned = extraction_batches(ROOT, doc, context)
        batches.append(len(planned))
        for number, (owned, surrounding) in enumerate(planned, 1):
            packet = with_scope(compose_v2(ROOT, "extract", {**context, "owned_segment_ids": [s["id"] for s in owned]},
                               {"document_id": doc["document_id"], "segments": owned, "context_segments": surrounding}))
            packets.append({"step": f"{index+1}-extract-{number}", "owned_segment_ids": [s["id"] for s in owned],
                            "context_segment_ids": [s["id"] for s in surrounding], "packet_bytes": len(encoded(packet)),
                            "measurement": "source envelope; checked metadata and translation added at runtime"})
    require(batches == [2, 3], "Extraction batching requires a revised bounded plan before inference")
    require(all(p["packet_bytes"] <= MAX_REQUEST_BYTES for p in packets), "Preflight packet exceeds the 180,000-byte ceiling")
    return {"plan_id": PLAN_ID, "baseline_calls": BASELINE_CALLS, "max_calls": 14,
            "max_repairs_total": 3, "max_repairs_per_step": 2, "extraction_batches": batches,
            "stages": ["1-triage", "1-translate", "2-triage", "2-translate", "1-extract-1", "1-extract-2",
                       "2-extract-1", "2-extract-2", "2-extract-3", "3-reconcile", "4-overview"],
            "packet_measurements": packets,
            "limits": "All requests and repairs are checked before dispatch. Future output-dependent packet sizes are not established by this offline preflight; oversize stops without adding batches or dropping evidence. This text-only sample bypasses automatic OCR/image recovery, whole-document page accounting, profile storage and publication. No optional analysis tasks or full-country profile generation."}


class Evaluation:
    def __init__(self, output, *, inference_authorized=False):
        self.output = output
        self.service = self.session = None
        self.manifest_path = output / "manifest.json"
        closed = output / "execution-summary.json"
        require(not closed.exists() or not read_json(closed).get("status", "").startswith("closed"),
                "This evaluation is closed; its ledger cannot be resumed or reset")
        self.documents = sources()
        plan = preflight_plan(self.documents)
        if self.manifest_path.exists():
            self.manifest = read_json(self.manifest_path)
            require(self.manifest.get("plan_id") == PLAN_ID, "Prepare a new directory for the revised bounded plan; old ledgers cannot be converted")
            require(self.manifest["method"] == frozen_method(), "Evaluation method changed; do not resume or reset the approved call budget")
            require(self.manifest["selection"] == SELECTION, "Evaluation selection changed")
        else:
            method = frozen_method()
            self.manifest = {"format": "workflow-sample-evaluation-1", "created_at": now(), "selection": SELECTION,
                             "plan_id": PLAN_ID, "baseline_calls": BASELINE_CALLS,
                             "max_calls": 14, "max_repairs_total": 3, "max_repairs_per_step": 2,
                             "scope": SCOPE, "method": method,
                             "source_hashes": {doc: h for doc, _, h in SAMPLES}, "inference_authorized_at_preparation": inference_authorized}
            for path in method:
                target = output / "method" / path
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("xb") as stream:
                    stream.write((ROOT / path).read_bytes())
            save_new(self.manifest_path, self.manifest)
        if not (output / "plan.json").exists():
            save_new(output / "plan.json", plan)
        else:
            require(read_json(output / "plan.json") == plan, "Prepared bounded plan differs")
        if not (output / "source-samples.json").exists():
            save_new(output / "source-samples.json", self.documents)
        else:
            require(read_json(output / "source-samples.json") == self.documents, "Prepared source sample differs")

    def attempts(self):
        return [read_json(p) for p in sorted((self.output / "calls").glob("*/dispatch.json"))]

    def connect(self):
        self.service, self.session = AIService(ROOT), AISession()
        catalog = self.service.connect_chatgpt(self.session)
        require(any(m["id"] == SELECTION["model"] and SELECTION["effort"] in m["efforts"] for m in catalog["models"]), "Exact approved model/effort unavailable; no fallback")
        if not (self.output / "catalog.json").exists():
            save_new(self.output / "catalog.json", {"read_at": now(), "models": catalog["models"]})
        print("Connected exact approved ChatGPT model/effort; no connection-test inference.", flush=True)

    def call(self, step, compose, check):
        closed = self.output / "execution-summary.json"
        require(not closed.exists() or not read_json(closed).get("status", "").startswith("closed"),
                "This evaluation is closed; its ledger cannot be resumed or reset")
        saved_path = self.output / "outputs" / (step + ".json")
        if saved_path.exists():
            result = read_json(saved_path)
            check(result)
            return result
        prior = [a for a in self.attempts() if a["step"] == step]
        repair = None
        if prior:
            last_dir = self.output / "calls" / f'{prior[-1]["call"]:02d}'
            if (last_dir / "validation.json").exists():
                validation = read_json(last_dir / "validation.json")
                if validation["passed"]:
                    result = json.loads(read_json(last_dir / "response.json")["text"])
                    check(result); save_new(saved_path, result); return result
                repair = {"errors": validation["errors"], "previous_output": read_json(last_dir / "response.json")["text"]}
            else:
                raise ValueError("An earlier dispatch has no validated result; inspect it before any retry. It remains counted.")
        while True:
            attempts = self.attempts()
            require(len(attempts) < 14, "Approved 14-call limit reached")
            require(sum(a["step"] == step for a in attempts) < 3, "Two repair attempts already used for this step")
            if repair:
                require(sum(a["repair"] for a in attempts) < 3, "Approved global reserve of three repair calls reached")
            require(frozen_method() == self.manifest["method"], "Method changed during evaluation")
            packet = compose(repair)
            require(len(encoded(packet)) <= MAX_REQUEST_BYTES, "Packet exceeds the existing 180,000-byte ceiling; no text dropped")
            call_number = len(attempts) + 1
            folder = self.output / "calls" / f"{call_number:02d}"
            # Exclusive creation reserves/counts the call BEFORE any dispatch.
            folder.mkdir(parents=True, exist_ok=False)
            save_new(folder / "request.json", packet)
            save_new(folder / "dispatch.json", {"call": call_number, "step": step, "route": packet["route"], "repair": repair is not None,
                      "started_at": now(), "selection": SELECTION, "packet_hash": packet["packet_hash"], "packet_bytes": len(encoded(packet))})
            print(f"Call {call_number}/14: {step}" + (" (validation repair)" if repair else ""), flush=True)
            started = time.monotonic()
            try:
                response = self.service.generate_json(self.session, SELECTION, packet)
            except AIError as exc:
                save_new(folder / "provider-error.json", {"code": exc.code, "message": str(exc), "elapsed_seconds": time.monotonic() - started})
                raise
            response["elapsed_seconds"] = time.monotonic() - started
            save_new(folder / "response.json", response)
            require(frozen_method() == self.manifest["method"], "Method changed during request")
            try:
                result = json.loads(response["text"])
                schema = read_json(ROOT / "config/v2/pipelines.json")["routes"][packet["route"]]["schema"]
                if packet["route"] not in ("extract", "prime"):
                    errors = validate_v2(ROOT, schema, result)
                    require(not errors, "; ".join(errors))
                # These checks report schema and evidence failures together.
                check(result)
            except (ValueError, KeyError, TypeError) as exc:
                errors = str(exc)
                save_new(folder / "validation.json", {"passed": False, "errors": errors})
                print(f"Validation failed for {step}: {errors[:900]}", flush=True)
                repair = {"errors": errors, "previous_output": response["text"]}
                continue
            save_new(folder / "validation.json", {"passed": True, "note": "Software checks only; semantic review still required"})
            save_new(saved_path, result)
            print(f"Saved {step}; {response['elapsed_seconds']:.1f}s; {response.get('usage')}", flush=True)
            return result

    def run(self):
        require(self.manifest.get("plan_id") == PLAN_ID,
                "Prepare a revised bounded plan before inference; the old single-batch ledger is not executable")
        closed = self.output / "execution-summary.json"
        require(not closed.exists() or not read_json(closed).get("status", "").startswith("closed"),
                "This evaluation is closed; its ledger cannot be resumed or reset")
        preflight_plan(self.documents)
        self.connect()
        metadata, extractions, documents = [], [], copy.deepcopy(self.documents)
        for index, doc in enumerate(documents):
            segments = doc["segments"]
            triage = self.call(f"{index+1}-triage", lambda repair: with_scope(fresh_preparation_packet(ROOT, "triage", doc), repair),
                              lambda result: check_triage(result, doc))
            metadata.extend(triage["document_profiles"])
            translated = self.call(f"{index+1}-translate", lambda repair: with_scope(fresh_preparation_packet(ROOT, "translate", doc, triage), repair),
                                   lambda result: check_translation(result, segments))
            lookup = {s["segment_id"]: s for s in translated["segments"]}
            for s in segments:
                row = lookup[s["id"]]
                s.update(english_text=row["english_text"], language=row["source_language"], translation_method=row["method"], term_decisions=row["term_decisions"],
                         translation_notes=row.get("notes", []))
        context = {"country_codes": ["BLR"], "source_group_ids": [doc["document_id"] for doc in documents],
                   "document_profiles": metadata, "sample_only": True}
        planned = [(doc, extraction_batches(ROOT, doc, document_context(doc, context))) for doc in documents]
        require([len(parts) for doc, parts in planned] == [2, 3], "Prepared responses need a revised extraction batch plan; stop without expanding the budget")
        # Check all five actual extraction requests before dispatching any of them.
        for index, (doc, parts) in enumerate(planned):
            for number, (owned, surrounding) in enumerate(parts, 1):
                packet = with_scope(compose_v2(ROOT, "extract", {**document_context(doc, context), "owned_segment_ids": [s["id"] for s in owned]},
                                    {"document_id": doc["document_id"], "segments": owned, "context_segments": surrounding}))
                require(len(encoded(packet)) <= MAX_REQUEST_BYTES, "Prepared extraction packet exceeds the 180,000-byte ceiling")
        for index, (doc, parts) in enumerate(planned):
            for number, (owned, surrounding) in enumerate(parts, 1):
                def extraction_check(result):
                    errors = extraction_errors(ROOT, result, "BLR", source_segments={s["id"]: s["text"] for s in owned + surrounding},
                                               owned_segment_ids=[s["id"] for s in owned])
                    require(not errors, "; ".join(errors))
                extracted = self.call(f"{index+1}-extract-{number}", lambda repair: with_scope(compose_v2(ROOT, "extract",
                                      {**document_context(doc, context), "owned_segment_ids": [s["id"] for s in owned]},
                                      {"document_id": doc["document_id"], "segments": owned, "context_segments": surrounding}), repair), extraction_check)
                extractions.append(namespace_extraction(extracted, f"d{index+1}b{number}:"))
        combined = {k: [item for ext in extractions for item in ext[k]] for k in ("evidence", "records", "coverage", "notes", "issues")}
        if not (self.output / "combined-extraction.json").exists():
            save_new(self.output / "combined-extraction.json", combined)
            save_new(self.output / "translated-samples.json", documents)
        all_segments = {s["id"]: s["text"] for doc in documents for s in doc["segments"]}
        errors = extraction_errors(ROOT, combined, "BLR", source_segments=all_segments, owned_segment_ids=list(all_segments))
        require(not errors, "; ".join(errors))
        def reconciliation_check(result):
            check_reconciliation(result, combined, documents, metadata)
        reconciliation = self.call("3-reconcile", lambda repair: with_scope(compose_v2(ROOT, "reconcile",
                                   {**context, "mode": "proposals_only; retain every source record; do not claim a canonical winner"},
                                   synthesis_evidence(combined)), repair), reconciliation_check)
        sections = read_json(ROOT / "config/v2/pipelines.json")["features"]["prime"]["required_sections"]
        prime_context = {**context, "required_sections": sections,
                         "known_commitment_ids": [r["local_id"] for r in combined["records"] if r["kind"] == "commitment"], "application_calculations": []}
        def prime_check(result):
            records = {r["local_id"]: r for r in combined["records"]}
            errors = validate_v2(ROOT, "report", result, required_sections=sections,
                                known_record_evidence={key:set(r['evidence_ids']) for key, r in records.items()},
                                known_evidence_ids={e["local_id"] for e in combined["evidence"]}, known_record_ids=set(records), known_commitment_ids=set(prime_context["known_commitment_ids"]))
            require(not errors, "; ".join(errors))
            require(result["country_codes"] == ["BLR"] and result["source_group_ids"] == prime_context["source_group_ids"], "Overview changed sample scope")
            for node in _walk(result):
                if "citations" in node:
                    linked = {eid for rid in node["citations"]["record_ids"] for eid in records[rid]["evidence_ids"]}
                    require(set(node["citations"]["evidence_ids"]) <= linked and node.get("calculation") is None, "Overview has unrelated citations or unchecked arithmetic")
        self.call("4-overview", lambda repair: with_scope(compose_v2(ROOT, "prime", prime_context,
                  {"extraction": synthesis_evidence(combined), "reconciliation": reconciliation}), repair), prime_check)
        # This ledger tests only the country pipeline; saved prior analysis
        # attempts remain readable in their original closed evaluation folders.


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="Execute only after explicit user authorization; at most 14 calls total")
    parser.add_argument("--output", type=Path, required=True, help="Explicit new evaluation directory; no previous ledger is reused by default")
    parser.add_argument("--check-reuse-from", type=Path, help="Offline compatibility audit only; never substitutes cached results or falls back to fresh model calls")
    args = parser.parse_args()
    output = (ROOT / args.output).resolve()
    require(output.is_relative_to(ROOT / "data/derived/evaluations/workflow-audit"), "Evaluation output must stay within the dedicated derived-artifact folder")
    if args.check_reuse_from:
        require(not args.run, "A reuse compatibility audit is offline only")
        archive = (ROOT / args.check_reuse_from).resolve()
        require(archive.is_relative_to(ROOT / "data/derived/evaluations/workflow-audit"), "Reuse audit must read an evaluation archive")
        reuse = verified_reuse(archive, sources())
        require(not output.exists(), "Reuse audit requires a new output folder")
        for path, raw in reuse["files"].items():
            target = output / "reuse" / path
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as stream:
                stream.write(raw)
        save_new(output / "reuse-audit.json", {"archive": archive.relative_to(ROOT).as_posix(),
                 "receipts": reuse["receipts"], "file_hashes": reuse["file_hashes"], "status": "compatible_offline_only_no_execution_plan"})
        print("Reuse audit passed; no provider connection or inference. This does not authorize execution.", flush=True)
        return
    evaluation = Evaluation(output, inference_authorized=args.run)
    print(json.dumps({"output": output.relative_to(ROOT).as_posix(), "sample_pages": sum(len(d['sample_pages']) for d in evaluation.documents),
                      "sample_characters": [sum(len(s['text']) for s in d['segments']) for d in evaluation.documents],
                      "calls_already_reserved": len(evaluation.attempts()), "live_requested": args.run}), flush=True)
    if not args.run:
        print("Offline preparation complete. No provider connection or model call.", flush=True)
        return
    try:
        evaluation.run()
        print("All planned sample steps completed; semantic review remains required.", flush=True)
    except (AIError, ValueError, OSError) as exc:
        print("EVALUATION STOPPED: " + str(exc), flush=True)
        sys.exit(2)
    finally:
        if evaluation.service:
            evaluation.service.rpc.close()


if __name__ == "__main__":
    main()

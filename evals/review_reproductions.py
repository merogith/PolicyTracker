"""Read-only design review probes, using invented evidence and isolated temporary files.

These expose current gaps; they are NOT acceptance tests that approve the behavior.
No model calls or changes to the supplied corpus are made.
"""
from __future__ import annotations
import contextlib
import io
import json
import uuid
from pathlib import Path

from jsonschema import Draft202012Validator
from pypdf import PdfWriter
from policytracker.inventory import inventory, sha256
from policytracker.releases import ReleaseRegistry
from policytracker.validation import validate_extraction

ROOT = Path(__file__).resolve().parents[1]


def schema(name):
    return json.loads((ROOT / "schemas" / f"{name}.schema.json").read_text(encoding="utf-8"))


def blank(s):
    if "enum" in s:
        return s["enum"][0]
    kind = s["type"]
    if isinstance(kind, list):
        return None if "null" in kind else ""
    if kind == "object":
        return {k: blank(v) for k, v in s["properties"].items()}
    if kind == "array":
        return []
    return {"string": "", "integer": s.get("minimum", 0), "boolean": False}[kind]


def accepted(name, value):
    return not list(Draft202012Validator(schema(name)).iter_errors(value))


def main():
    results = {}
    sx = schema("extraction")
    quote = "Will install 20 systems by 2030, subject to support."
    segments = [{"segment_id": "s1", "document_id": "d1", "pdf_page": 1, "text": quote}]
    evidence = blank(sx["properties"]["evidence"]["items"])
    evidence.update(evidence_id="e1", document_id="d1", segment_id="s1", pdf_page=1,
                    quote_original=quote, quote_english=quote)
    statement = blank(sx["properties"]["statements"]["items"])
    statement.update(statement_id="st1", label_en="Install systems", description_en="Install 200 systems by 2030.",
                     topics=["CLM-04"], documentation_status="action_committed", assertion_kind="planned",
                     evidence_ids=["e1"], performance_status="not_assessed")
    target = blank(sx["properties"]["statements"]["items"]["properties"]["targets"]["items"])
    target.update(target_id="t1", wording_english="Install 200 systems", value_decimal="200", unit="systems",
                  deadline="2030", conditionality="explicitly_conditional", condition_text="support", evidence_ids=["e1"])
    statement["targets"] = [target]
    output = {"evidence": [evidence], "statements": [statement],
              "coverage": [{"segment_id": "s1", "disposition": "extracted", "statement_ids": ["st1"], "reason": "Explicit target"}], "issues": []}
    results["R1_wrong_number_and_no_field_support"] = {
        "source_value": "20", "extracted_value": "200", "schema_accepts": accepted("extraction", output),
        "semantic_errors": validate_extraction(output, segments, {"CLM-04"})}
    dropped = {"evidence": [], "statements": [], "coverage": [{"segment_id": "s1", "disposition": "background", "statement_ids": [], "reason": "Background"}], "issues": []}
    results["R2_omitted_target_with_full_page_accounting"] = {
        "schema_accepts": accepted("extraction", dropped), "semantic_errors": validate_extraction(dropped, segments, {"CLM-04"})}
    report = blank(schema("report"))
    report.update(country_codes=["KAZ"], availability="evidence_available")
    results["R3_empty_country_report"] = {"schema_accepts": accepted("report", report)}
    dash = blank(schema("dashboard"))
    row = blank(schema("dashboard")["properties"]["policy_rows"]["items"])
    row.update(commitment_id="c1", label="Install systems", target_display="20 systems",
               performance_status="on_track", performance_assessment_id=None)
    dash["policy_rows"] = [row]
    results["R4_unsupported_progress_badge"] = {"schema_accepts": accepted("dashboard", dash)}

    store = ReleaseRegistry(":memory:")
    try:
        digest = store.add_report("empty", "prime_candidate", "KAZ", "test", {})
        store.approve("empty", "test-reviewer", "reviewer", {"artifact_hash": digest, "gate": "passed", "critical_issues": 0, "coverage_complete": True})
        pointer = store.assign("KAZ", "empty", 0, "test-editor", "publisher", "Synthetic review probe")
        results["R5_registry_trusts_empty_artifact_and_receipt"] = {"prime_report": pointer["report_id"], "artifact": {}}
    finally:
        store.close()

    scratch = ROOT / "tmp"
    scratch.mkdir(exist_ok=True)
    # Keep synthetic fixtures in the ignored workspace; no recursive cleanup.
    workdir = scratch / ("review-only-" + uuid.uuid4().hex)
    workdir.mkdir()
    with contextlib.nullcontext(workdir) as work:
        root = Path(work)
        folder = root / "data/sources/Albania/NDC/Synthetic"
        folder.mkdir(parents=True)
        pdf = folder / "Current.pdf"
        hashes = []
        for page_count in [1, 2]:
            writer = PdfWriter()
            for _ in range(page_count):
                writer.add_blank_page(width=100, height=100)
            writer.write(pdf)
            digest = sha256(pdf.read_bytes())
            hashes.append(digest)
            (folder / "Source.txt").write_text(f"Synthetic review source\nType: NDC\nRecord: doc-same-record\nCurrent file SHA-256: {digest}\n", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                inventory(root, extract=True)
        paths = list((root / "data/derived/pages").glob("*.json"))
        latest = json.loads(paths[0].read_text(encoding="utf-8"))
        results["R6_revised_source_overwrites_derived_version"] = {
            "distinct_input_hashes": len(set(hashes)), "retained_page_json_files": len(paths),
            "retained_hash_is_latest": latest["source_sha256"] == hashes[-1]}

    result = {"date": "2026-10-08", "scope": "synthetic local probes; no production data or model inference", "results": results}
    destination = ROOT / "evals/design-review-results.json"
    destination.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

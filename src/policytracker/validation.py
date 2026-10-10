"""Deterministic evidence checks. These do not certify semantic correctness."""
from __future__ import annotations
from decimal import Decimal, InvalidOperation


def resolve_pointer(value, pointer: str):
    if not pointer.startswith("/"):
        raise ValueError("field_path must be a JSON Pointer")
    for raw in pointer[1:].split("/"):
        key = raw.replace("~1", "/").replace("~0", "~")
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def validate_extraction(output: dict, segments: list[dict], topic_ids: set[str]) -> list[str]:
    """Input segments have segment_id, document_id, pdf_page and original text."""
    errors = []
    source = {s["segment_id"]: s for s in segments}
    if len(source) != len(segments):
        errors.append("duplicate input segment IDs")
    evidence = {}
    for e in output.get("evidence", []):
        eid = e["evidence_id"]
        if eid in evidence:
            errors.append(f"duplicate evidence ID: {eid}")
        evidence[eid] = e
        seg = source.get(e["segment_id"])
        if not seg:
            errors.append(f"unknown segment: {eid}")
            continue
        if e["document_id"] != seg["document_id"] or e["pdf_page"] != seg["pdf_page"]:
            errors.append(f"source locator mismatch: {eid}")
        quote = e["quote_original"]
        if not quote.strip() or quote not in seg["text"]:
            errors.append(f"original quote not found verbatim: {eid}")
    def check_refs(refs, where, required=False):
        if required and not refs:
            errors.append(f"missing evidence: {where}")
        for ref in refs:
            if ref not in evidence:
                errors.append(f"unknown evidence {ref}: {where}")
    for e in evidence.values():
        check_refs(e.get("context_evidence_ids", []), e["evidence_id"])
    statements = {}
    for s in output.get("statements", []):
        sid = s["statement_id"]
        if sid in statements:
            errors.append(f"duplicate statement ID: {sid}")
        statements[sid] = s
        check_refs(s.get("evidence_ids", []), sid, True)
        if set(s.get("topics", [])) - topic_ids:
            errors.append(f"unknown taxonomy ID: {sid}")
        if s.get("performance_status") != "not_assessed":
            errors.append(f"extraction cannot assess performance: {sid}")
        if s.get("assertion_kind") in {"planned", "projected", "scenario", "template"} and s.get("documentation_status") in {"implementation_reported", "result_reported"}:
            errors.append(f"planned/projected evidence labelled observed: {sid}")
        for f in s.get("field_support", []):
            try:
                resolve_pointer(s, f["field_path"])
            except (KeyError, IndexError, ValueError, TypeError):
                errors.append(f"unknown field path: {sid}:{f['field_path']}")
            check_refs(f.get("evidence_ids", []), sid + f["field_path"], True)
        for target in s.get("targets", []):
            check_refs(target.get("evidence_ids", []), sid + ":target", True)
            if target.get("conditionality") == "explicitly_conditional" and not target.get("condition_text"):
                errors.append(f"conditional target missing condition: {sid}")
            numbers = {}
            for key in ["value_decimal", "lower_decimal", "upper_decimal", "baseline_value"]:
                value = target.get(key)
                if value is not None:
                    try:
                        number = Decimal(value)
                        if not number.is_finite():
                            raise InvalidOperation
                        numbers[key] = number
                    except (InvalidOperation, ValueError, TypeError):
                        errors.append(f"invalid decimal {key}: {sid}")
            if "lower_decimal" in numbers and "upper_decimal" in numbers and numbers["lower_decimal"] > numbers["upper_decimal"]:
                errors.append(f"inverted target range: {sid}")
        for fact in s.get("facts", []):
            check_refs(fact.get("evidence_ids", []), sid + ":fact", True)
    seen = []
    covered_statements = set()
    for c in output.get("coverage", []):
        seg_id = c["segment_id"]
        seen.append(seg_id)
        if seg_id not in source:
            errors.append(f"coverage has unknown segment: {seg_id}")
        if c.get("disposition") == "extracted" and not c.get("statement_ids"):
            errors.append(f"extracted segment has no statements: {seg_id}")
        for sid in c.get("statement_ids", []):
            if sid not in statements:
                errors.append(f"coverage has unknown statement: {sid}")
            else:
                covered_statements.add(sid)
                refs = statements[sid].get("evidence_ids", [])
                if not any(evidence.get(ref, {}).get("segment_id") == seg_id for ref in refs):
                    errors.append(f"coverage statement not evidenced by segment: {seg_id}:{sid}")
    if set(seen) != set(source) or len(seen) != len(set(seen)):
        errors.append("coverage must account for each input segment exactly once")
    if set(statements) - covered_statements:
        errors.append("statements missing from coverage ledger")
    return errors

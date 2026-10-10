"""Offline v2 prompt composition and contract checks; not a production runner.

These checks establish selected structural/evidence invariants, not entailment,
translation quality, extraction recall, access control or publication eligibility.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

from jsonschema import Draft202012Validator


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def compose_v2(root: Path, route: str, task_context: dict, source_data: dict) -> dict:
    config = read_json(root / "config/v2/pipelines.json")
    selected = config["routes"][route]
    paths = [root / config["shared_contract"], root / config["labeling_contract"],
             root / "prompts/v2" / selected["prompt"],
             root / "schemas/v2" / (selected["schema"] + ".schema.json"),
             root / "config/v2/taxonomy.json", root / "config/v2/vocabulary.json",
             root / "config/v2/pipelines.json"]
    hashes = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    # Source/question content never gets concatenated into trusted instructions.
    payload = {"task_context": task_context, "taxonomy": read_json(paths[4]),
               "vocabulary": read_json(paths[5]), "untrusted_source_data": source_data}
    if route in ("extract", "relabel"):
        guide = root / "config/v2/label-guide.json"
        payload["labeling_guide"] = read_json(guide)
        hashes[guide.relative_to(root).as_posix()] = hashlib.sha256(guide.read_bytes()).hexdigest()
    if route == "translate":
        policy = root / "config/translations.json"
        payload["translation_policy"] = read_json(policy)
        hashes[policy.relative_to(root).as_posix()] = hashlib.sha256(policy.read_bytes()).hexdigest()
    packet = {"route": route, "instructions": "\n\n".join(p.read_bytes().decode("utf-8") for p in paths[:3]),
              "input": json.dumps(payload, ensure_ascii=False), "schema": read_json(paths[3]),
              "instruction_paths": [p.relative_to(root).as_posix() for p in paths[:3]],
              "component_hashes": hashes, "input_hash": digest(payload), "execution_state": "not_run"}
    return fingerprint_packet(packet)


def fingerprint_packet(packet: dict) -> dict:
    """Fingerprint the assembled request, including supplements, without claiming execution."""
    packet["instructions_hash"] = hashlib.sha256(packet["instructions"].encode("utf-8")).hexdigest()
    packet["packet_hash"] = digest({k: v for k, v in packet.items() if k != "packet_hash"})
    return packet


def compact_json_text(text: str) -> str:
    """Remove only insignificant JSON whitespace; preserve strings and number tokens.

    Malformed responses remain verbatim so a repair can still inspect the failure.
    """
    try:
        json.loads(text)
    except (ValueError, TypeError):
        return text
    result, quoted, escaped = [], False, False
    for char in text:
        if quoted:
            result.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
            result.append(char)
        elif char not in " \t\r\n":
            result.append(char)
    return "".join(result)


def repair_feedback(errors: str, previous_output) -> dict:
    """Avoid double-encoding valid prior JSON; retain malformed/float tokens exactly."""
    if isinstance(previous_output, str):
        def keep_float_token(token):
            raise ValueError("Retain unquoted decimal tokens verbatim, without float rounding")
        try:
            previous_output = json.loads(previous_output, parse_float=keep_float_token)
        except (ValueError, TypeError):
            previous_output = compact_json_text(previous_output)
    return {"errors": errors, "previous_output": previous_output}


def compact_packet(packet: dict) -> dict:
    """Lossless wire compaction; stored source/response bytes remain untouched."""
    return fingerprint_packet({**packet, "input": compact_json_text(packet["input"])})


def domain_ids(root: Path, topic_ids: list[str]) -> list[str]:
    lookup = {t["id"]: t["domain_ids"] for t in read_json(root / "config/v2/taxonomy.json")["topics"]}
    return sorted({d for topic in topic_ids for d in lookup[topic]})


def normalize_numeric(raw: str, notation: str) -> Decimal | None:
    if notation in ("ambiguous", "textual"):
        return None
    value = raw.replace("\u2212", "-").replace("\u00a0", " ").replace("\u202f", " ").strip()
    # A single grouping character must be used consistently. No unit, percent,
    # multiplication or currency conversion is accepted in a raw numeric token.
    point, group = (".", ",") if notation == "dot_decimal" else (",", ".")
    pattern = rf"[+-]?(?:[0-9]+|[0-9]{{1,3}}(?:{re.escape(group)}[0-9]{{3}})+|[0-9]{{1,3}}(?: [0-9]{{3}})+)(?:{re.escape(point)}[0-9]+)?"
    if not re.fullmatch(pattern, value):
        raise ValueError("unsupported numeric token")
    return Decimal(value.replace(group, "").replace(" ", "").replace(point, "."))


def _walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def normalize_extraction_evidence(output: dict, schema: dict) -> tuple[dict, list[dict]]:
    """Close explicit record references without changing claims or raw responses.

    Only schema-valid extraction JSON is eligible. Each added reference already
    occurs inside that record and names an existing evidence quotation. Unknown
    references and all other acceptance defects remain blocking. The returned
    trace can be replayed against the archived raw response to verify provenance.
    """
    errors = [f"schema {e.json_path}: {e.message}" for e in Draft202012Validator(schema).iter_errors(output)]
    if errors:
        raise ValueError("; ".join(errors))
    result = copy.deepcopy(output)
    known = {evidence["local_id"] for evidence in result["evidence"]}
    additions = []
    for index, record in enumerate(result["records"]):
        references = {}

        def reference(evidence_id, path):
            if evidence_id not in known:
                raise ValueError(f"Unknown evidence reference at {path}: {evidence_id}")
            references.setdefault(evidence_id, []).append(path)

        def visit(value, path):
            if isinstance(value, dict):
                for key in sorted(value):
                    child_path = path + "/" + key.replace("~", "~0").replace("/", "~1")
                    if key == "evidence_id":
                        reference(value[key], child_path)
                    elif key == "evidence_ids":
                        for position, evidence_id in enumerate(value[key]):
                            reference(evidence_id, child_path + "/" + str(position))
                    else:
                        visit(value[key], child_path)
            elif isinstance(value, list):
                for position, child in enumerate(value):
                    visit(child, path + "/" + str(position))

        base = f"/records/{index}"
        for key in sorted(record):
            if key != "evidence_ids":
                visit(record[key], base + "/" + key.replace("~", "~0").replace("/", "~1"))
        present = set(record["evidence_ids"])
        for evidence_id in sorted(set(references) - present):
            record["evidence_ids"].append(evidence_id)
            additions.append({"record_id": record["local_id"], "evidence_id": evidence_id,
                              "source_paths": sorted(set(references[evidence_id])),
                              "destination_path": base + "/evidence_ids"})
    return result, additions


def _pointer(value, pointer):
    if not pointer.startswith("/"):
        raise ValueError("not a JSON Pointer")
    for part in pointer[1:].split("/"):
        key = part.replace("~1", "/").replace("~0", "~")
        if isinstance(value, list):
            if not re.fullmatch(r"0|[1-9][0-9]*", key):
                raise ValueError("invalid array index in JSON Pointer")
            value = value[int(key)]
        else:
            value = value[key]
    return value


def schema_allows_absence_marker(schema: dict, pointer: str, value) -> bool:
    """Recognize declared absence enums, never similarly worded free text."""
    if not isinstance(value, str) or value not in ("not_stated", "unknown", "unclear", "unspecified"):
        return False
    if not pointer.startswith("/"):
        return False

    def branches(node):
        if isinstance(node, dict):
            yield node
            for key in ("anyOf", "oneOf", "allOf"):
                for child in node.get(key, []):
                    yield from branches(child)

    nodes = [schema]
    for token in pointer[1:].split("/"):
        key = token.replace("~1", "/").replace("~0", "~")
        children = []
        for node in nodes:
            for branch in branches(node):
                if key in branch.get("properties", {}):
                    children.append(branch["properties"][key])
                elif re.fullmatch(r"0|[1-9][0-9]*", key) and isinstance(branch.get("items"), dict):
                    children.append(branch["items"])
        nodes = children
    return any(value in branch.get("enum", []) for node in nodes for branch in branches(node))


def numeric_token_in_quote(raw: str, quote: str, notation: str) -> bool:
    """Match a whole source number, including its sign and grouping.

    A substring of -20, 1 500 or 1e20 is not evidence for positive 20/500.
    Scientific notation can be retained as ambiguous text, never normalized here.
    A hyphen between digits is a range separator rather than a unary minus.
    """
    if not raw:
        return False
    if notation == "textual":
        return re.search(rf"(?<!\w){re.escape(raw)}(?!\w)", quote) is not None
    pattern = (r"(?:(?<![0-9])[+\-\u2212][ \u00a0\u202f]*)?[0-9]+"
               r"(?:[.,][0-9]+|[ \u00a0\u202f][0-9]{3}(?![0-9]))*"
               r"(?:[eE][+\-\u2212]?[0-9]+)?")
    return any(match.group() == raw for match in re.finditer(pattern, quote))


def validate_v2(root: Path, schema_name: str, output: dict, *, source_segments: dict[str, str] | None = None,
                owned_segment_ids: list[str] | None = None, required_sections: list[str] | None = None,
                known_evidence_ids: set[str] | None = None, known_record_ids: set[str] | None = None,
                known_commitment_ids: set[str] | None = None, schema: dict | None = None,
                known_record_evidence: dict[str, set[str]] | None = None) -> list[str]:
    """Return local diagnostic failures, never a publication receipt."""
    if schema is None:
        schema = read_json(root / "schemas/v2" / (schema_name + ".schema.json"))
    errors = [f"schema {e.json_path}: {e.message}" for e in Draft202012Validator(schema).iter_errors(output)]
    if errors:
        return errors
    # Enforce label sets locally without adding uniqueItems to model wire schemas.
    # Historical label shapes retain their original validation behavior.
    for node in _walk(output):
        if "risk_functions" in node and "topic_ids" in node:
            for key, selected in node.items():
                if key != "unmapped_terms" and isinstance(selected, list) and len(selected) != len(set(selected)):
                    errors.append(f"duplicate label in {key}")
    if schema_name == "extraction":
        evidence = {e["local_id"]: e for e in output["evidence"]}
        records = {r["local_id"]: r for r in output["records"]}
        if len(evidence) != len(output["evidence"]) or len(records) != len(output["records"]):
            errors.append("duplicate evidence/record IDs")
        local_ids = [node["local_id"] for node in _walk(output) if "local_id" in node]
        if len(local_ids) != len(set(local_ids)):
            errors.append("local IDs must be globally unique within a task")
        for ev in evidence.values():
            if not ev["quote_original"].strip():
                errors.append(f"{ev['local_id']}: empty quote")
            if source_segments is not None:
                source = source_segments.get(ev["segment_id"])
                if source is None or not ev["quote_original"] or source.count(ev["quote_original"]) != 1:
                    errors.append(f"{ev['local_id']}: quote must resolve exactly once in its segment")
        for node in _walk(output):
            for key in ("evidence_ids", "context_evidence_ids"):
                for eid in node.get(key, []):
                    if eid not in evidence:
                        errors.append(f"unknown evidence: {eid}")
            if {"raw_token", "decimal", "evidence_id", "notation"}.issubset(node):
                ev = evidence.get(node["evidence_id"])
                raw = node["raw_token"]
                if ev is None or not numeric_token_in_quote(raw, ev["quote_original"], node["notation"]):
                    errors.append("numeric token lacks original evidence")
                try:
                    expected = normalize_numeric(node["raw_token"], node["notation"])
                    normalized = node["decimal"]
                    if expected is None:
                        if normalized is not None:
                            errors.append("ambiguous/textual number must not assert decimal")
                    elif normalized is None or not re.fullmatch(r"-?[0-9]+(?:\.[0-9]+)?", normalized) or Decimal(normalized) != expected:
                        errors.append("numeric value differs from source token")
                except (ValueError, InvalidOperation):
                    errors.append("invalid numeric normalization")
        for record in records.values():
            linked = set(record["evidence_ids"])
            missing_context = {context_id for eid in linked
                               for context_id in evidence.get(eid, {}).get("context_evidence_ids", [])} - linked
            if missing_context:
                errors.append(f"records[{record['local_id']}]: Record omits contextual evidence required by its quotations: {', '.join(sorted(missing_context))}")
            for node in _walk(record):
                references = set(node.get("evidence_ids", []))
                if "evidence_id" in node:
                    references.add(node["evidence_id"])
                if not references <= linked:
                    errors.append(f"records[{record['local_id']}]: Record omits supporting evidence used by its details: {', '.join(sorted(references - linked))}")
            if not record["evidence_ids"] or not record["field_support"]:
                errors.append(f"{record['local_id']}: missing evidence/field support")
            for support in record["field_support"]:
                try:
                    _pointer(record, support["field_path"])
                except (ValueError, KeyError, IndexError, TypeError):
                    errors.append("field support references a nonexistent field")
                if not support["evidence_ids"]:
                    errors.append("field support has no evidence")
            target_ids = {t["local_id"] for t in record["targets"]}
            for node in _walk(record):
                if "target_ids" in node and not set(node["target_ids"]).issubset(target_ids):
                    errors.append("detail links to a target outside its record")
                if "local_id" in node and node is not record and not node.get("evidence_ids"):
                    errors.append("typed detail has no evidence")
            # Archived schemas keep their original modality checks; new records use one type.
            if "assertion_kind" in record:
                if record["kind"] == "commitment" and record["assertion_kind"] in ("observed", "template", "projected", "scenario"):
                    errors.append("commitment confused with observed/template assertion")
                if record["assertion_kind"] in ("planned", "projected", "scenario", "template", "recommendation") and (
                        record["documentation_status"] in ("implementation_reported", "result_reported") or
                        record["kind"] in ("implementation_observation", "result_observation")):
                    errors.append("planned/projected evidence labelled observed")
                if record["kind"] == "commitment" and record["documentation_status"] in ("implementation_reported", "result_reported"):
                    errors.append("commitment must be separate from implementation/result observations")
            for missing in record["missing_fields"]:
                try:
                    missing_value = _pointer(record, missing["field_path"])
                    if "risk_functions" in record["labels"]:
                        if (missing["reason"] == "not_stated" and missing_value not in (None, [], "")
                                and not schema_allows_absence_marker(schema, "/records/0" + missing["field_path"], missing_value)):
                            errors.append(f"records[{record['local_id']}]{missing['field_path']}: not_stated cannot qualify a populated value")
                        if missing["reason"] == "conflicting_sources":
                            errors.append("Preserve conflicting values and relationships, not a missing-field conflict")
                        if missing["reason"] in ("unreadable", "not_processed"):
                            errors.append("Processing limitations belong in coverage/issues, not field absence")
                except (ValueError, KeyError, IndexError, TypeError):
                    errors.append("missing reason references a nonexistent field")
            for target_index, target in enumerate(record["targets"]):
                if not target["evidence_ids"]:
                    errors.append("target has no evidence")
                if target["conditionality"] == "explicitly_conditional" and not (target["condition_text"] or "").strip():
                    path = f"/targets/{target_index}/condition_text"
                    # A source can label a historical/scenario target conditional
                    # without supplying its dependency. Preserve that unknown,
                    # rather than forcing a fabricated or transferred condition.
                    documented_absence = target["condition_text"] is None and any(
                        missing["field_path"] == path and missing["reason"] == "not_stated"
                        and (missing["detail"] or "").strip() for missing in record["missing_fields"])
                    if not documented_absence:
                        errors.append(f"records[{record['local_id']}].targets[{target['local_id']}]{path}: "
                                      "unresolved conditional-target detail; retain the source's conditional status and "
                                      "supply its supported condition, or null with an exact not_stated missing-field "
                                      "entry explaining the absent condition. Never invent or transfer a condition.")
                if target["lower"] and target["upper"]:
                    try:
                        lo, hi = target["lower"]["decimal"], target["upper"]["decimal"]
                        if lo is not None and hi is not None and Decimal(lo) > Decimal(hi):
                            errors.append("inverted target range")
                    except InvalidOperation:
                        pass  # Numeric normalization already reports invalid decimals.
                if target["comparator"] == "range" and (target["value"] is not None or target["lower"] is None or target["upper"] is None):
                    errors.append("range target requires bounds and no single value")
                if target["comparator"] != "range" and (target["lower"] is not None or target["upper"] is not None):
                    errors.append("target bounds require range comparator")
        coverage = output["coverage"]
        owned = [c["segment_id"] for c in coverage]
        if len(owned) != len(set(owned)):
            errors.append("duplicate coverage segment")
        if owned_segment_ids is not None and set(owned) != set(owned_segment_ids):
            errors.append("owned segment coverage mismatch")
        covered = set()
        for row in coverage:
            if row["disposition"] == "extracted" and not row["record_ids"]:
                errors.append("extracted coverage without records")
            if not set(row["record_ids"]).issubset(records):
                errors.append("coverage references unknown records")
            for rid in row["record_ids"]:
                covered.add(rid)
                if rid in records and not any(evidence.get(eid, {}).get("segment_id") == row["segment_id"] for eid in records[rid]["evidence_ids"]):
                    errors.append(f"coverage[{row['segment_id']}]: coverage record {rid} not evidenced by its segment")
            if row["disposition"] in ("background", "unreadable", "excluded") and row["record_ids"]:
                errors.append("unprocessed/background coverage cannot claim extracted records")
        if set(records) - covered:
            errors.append("records missing from coverage ledger")
    if schema_name == "report":
        sections = output["sections"]
        ids = [s["section_id"] for s in sections]
        if len(ids) != len(set(ids)) or (required_sections is not None and set(ids) != set(required_sections)):
            errors.append("report required sections mismatch")
        if output["availability"] == "complete_in_declared_scope" and any(s["state"] == "not_processed" for s in sections):
            errors.append("complete report has unprocessed section")
        for section in sections:
            if section["state"] == "found" and not section["findings"]:
                errors.append("found section has no findings")
            if section["state"] != "found" and not section["gap_note"]:
                errors.append("empty section needs an explicit reason")
            if section["state"] != "found" and section["findings"]:
                errors.append("non-found section cannot contain findings")
        for node in _walk(output):
            if "citations" in node and node.get("kind") != "analyst_suggestion":
                if not node["citations"]["evidence_ids"] or not node["citations"]["record_ids"]:
                    errors.append(f"finding[{node['text_en'][:100]}]: factual finding lacks record/evidence citations")
            if "citations" in node:
                if known_evidence_ids is not None and not set(node["citations"]["evidence_ids"]) <= known_evidence_ids:
                    errors.append("finding cites unknown evidence")
                if known_record_ids is not None and not set(node["citations"]["record_ids"]) <= known_record_ids:
                    errors.append("finding cites unknown records")
                if known_record_evidence is not None:
                    linked = {eid for rid in node['citations']['record_ids'] for eid in known_record_evidence.get(rid, set())}
                    unrelated = set(node['citations']['evidence_ids']) - linked
                    if unrelated:
                        errors.append(f"finding[{node['text_en'][:100]}]: Finding evidence is unrelated to its cited records: {', '.join(sorted(unrelated))}")
                # A qualitative interpretation is derived too. Arithmetic, when
                # supplied, needs an application calculation, not model prose.
        for row in output["prioritized_commitments"]:
            if known_commitment_ids is not None and row["commitment_id"] not in known_commitment_ids:
                errors.append("unknown prioritized commitment")
            if not row["evidence_ids"] or (known_evidence_ids is not None and not set(row["evidence_ids"]) <= known_evidence_ids):
                errors.append("prioritized commitment lacks known evidence")
        if output["availability"] == "no_documents_supplied" and (output["headline_findings"] or
                output["prioritized_commitments"] or any(s["findings"] for s in sections) or
                any(f["kind"] != "analyst_suggestion" for f in output["followup_questions"])):
            errors.append("no-document report cannot invent findings")
    return errors


def record_attribution_errors(record: dict, country: str) -> list[str]:
    """Keep affected geography distinct from the source's reporting party."""
    geography = record["geography"]
    if geography["country_codes"] == [country]:
        return []
    # Explicit nonnational context is valid in a national source. A collective
    # call or regional observation must not acquire a national allocation merely
    # because this country reports it. Commitments retain the strict boundary.
    if geography["scope"] in ("regional", "EU", "multi_country") and record["kind"] in (
            "context", "priority", "proposal", "implementation_observation",
            "result_observation", "projection", "scenario"):
        return []
    return [f"records[{record['local_id']}].geography.country_codes: unresolved national-profile attribution; "
            f"{record['kind']} with {geography['scope']} scope requires affected countries [{country}], "
            f"got {geography['country_codes']}. Resolve kind/scope from evidence or report an issue; "
            "do not substitute the reporting party for affected countries."]


def extraction_errors(root: Path, output: dict, country: str, *, source_segments=None,
                      owned_segment_ids=None, schema=None) -> list[str]:
    """Code-verifiable extraction acceptance, not source entailment or recall."""
    schema = schema if schema is not None else read_json(root / "schemas/v2/extraction.schema.json")
    errors = validate_v2(root, "extraction", output, source_segments=source_segments,
                         owned_segment_ids=owned_segment_ids, schema=schema)
    if not Draft202012Validator(schema).is_valid(output):
        return errors  # Shape must be usable before inspecting record fields.
    errors.extend(f"issues[{i}]: unresolved blocking issue: {issue}" for i, issue in enumerate(output["issues"]))
    errors.extend(f"coverage[{row['segment_id']}]: unresolved {row['disposition']} segment"
                  for row in output["coverage"] if row["disposition"] not in ("extracted", "background"))
    errors.extend(error for record in output["records"] for error in record_attribution_errors(record, country))
    return errors

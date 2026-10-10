"""Task composition, deterministic scope/projections and joined output checks.

CountryRunner owns authentication, source inspection, inference and persistence.
"""
from __future__ import annotations
import copy
import hashlib
from pathlib import Path
from jsonschema import Draft202012Validator
from .engineering import _walk, compose_v2, digest, read_json, fingerprint_packet, validate_v2


def normalize_request(root: Path, request: dict) -> dict:
    """Omission uses configured defaults; explicit empty/false stays explicit."""
    if not isinstance(request, dict):
        raise ValueError("Analysis request must be an object")
    request = copy.deepcopy(request)
    task = next((t for t in read_json(root / "config/operations/tasks.json")["tasks"]
                 if t["id"] == request.get("task")), None)
    if task is None:
        raise ValueError("Choose a supported analysis task")
    request.setdefault("requested_fields", [o["id"] for o in task["options"] if o["default"]])
    request.setdefault("include_analyst_proposals", False)
    request.setdefault("filters", {})
    if not isinstance(request["filters"], dict):
        raise ValueError("Analysis filters must be an object")
    for key in ("domain_ids", "topic_ids", "hazards", "risk_functions"):
        request["filters"].setdefault(key, [])
    return request


def compose_operation(root: Path, request: dict, source_data: dict) -> dict:
    request = normalize_request(root, request)
    schema = read_json(root / "schemas/operations/analysis-request.schema.json")
    errors = list(Draft202012Validator(schema).iter_errors(request))
    if errors:
        raise ValueError("Invalid analysis request: " + "; ".join(f"{e.json_path}: {e.message}" for e in errors[:5]))
    catalog = read_json(root / "config/operations/tasks.json")
    task = next(t for t in catalog["tasks"] if t["id"] == request["task"])
    if request["output"]["artifact"] != task["artifact"]:
        raise ValueError("Artifact does not match task")
    lookup = {o["id"]: o for o in task["options"]}
    if task["options"] and not request["requested_fields"]:
        raise ValueError("Choose at least one output field; empty selection is not all fields")
    if any(f not in lookup for f in request["requested_fields"]):
        raise ValueError("Selected output field does not apply to task")
    groups = request["source_groups"]
    ids = [d for g in groups for d in g["document_ids"]]
    if len(set(ids)) < task.get("minimum_documents", 1):
        raise ValueError(f"{task['label']} requires at least {task['minimum_documents']} documents")
    if not task["options"] and request["requested_fields"]:
        raise ValueError("This task does not accept output-field selections")
    if not task.get("allows_filters", True) and any(request["filters"].values()):
        raise ValueError("Full-document translation cannot be narrowed by analysis filters")
    if any(not g["document_ids"] or not g["label"].strip() for g in groups) or len(ids) != len(set(ids)):
        raise ValueError("Source groups must be named, nonempty and disjoint")
    if len({g["id"] for g in groups}) != len(groups) or len({g["label"].strip().casefold() for g in groups}) != len(groups):
        raise ValueError("Source groups require unique IDs and names")
    if request["task"] == "compare":
        if len(groups) < 2 or not request["comparison_mode"]:
            raise ValueError("Comparison requires multiple groups and a method")
        mode = next((m for m in catalog["comparison_modes"] if m["id"] == request["comparison_mode"]), None)
        if not mode or (mode.get("max_groups") and len(groups) > mode["max_groups"]):
            raise ValueError("Invalid comparison group count")
        if mode["id"] == "documents" and any(len(g["document_ids"]) != 1 for g in groups):
            raise ValueError("Document comparison requires one document per group")
    elif request["comparison_mode"] is not None or len(groups) != 1:
        raise ValueError("Only comparison uses multiple groups or comparison mode")
    if task.get("requires_question") and not request["question"].strip():
        raise ValueError("Briefing needs a policy question")
    if request["include_analyst_proposals"] and request["task"] != "gaps":
        raise ValueError("Support proposals apply only to delivery-gap analysis")
    if request["uploads"]:
        raise ValueError("Register and inspect pending uploads before prompt compilation")
    taxonomy = read_json(root / "config/v2/taxonomy.json")
    topics = {t["id"]: t for t in taxonomy["topics"]}
    if request["filters"]["domain_ids"] and any(not set(topics[t]["domain_ids"]) & set(request["filters"]["domain_ids"]) for t in request["filters"]["topic_ids"]):
        raise ValueError("Topic is outside selected sector")
    # Offline composition is not execution eligibility. A service must authorize
    # IDs and supply verified metadata before dispatch, not trust browser grouping.
    if "document_metadata" in source_data:
        validate_source_groups(request, source_data["document_metadata"],
            unavailable_ids={d["document_id"] for d in source_data.get("source_coverage", []) if d["status"] == "unreadable"})
    selected = [lookup[f] for f in request["requested_fields"]]
    sections = ["scope", *request["requested_fields"], "limitations"] if request["task"] in ("extract", "brief") else []
    packed = compose_v2(root, task["route"], {"operation_request":request,
                         "user_preferences": source_data.get("user_preferences", {}),
                         "source_coverage": source_data.get("source_coverage", []),
                         "selected_options":selected,"required_sections":sections,
                         "country_codes": sorted({d["country_code"] for d in source_data.get("document_metadata", [])}),
                         "source_group_ids": [g["id"] for g in groups],
                         "coverage_mode":"all_selected_documents"}, source_data)
    for path in (root / "prompts/operations/00-request-contract.md", root / task["supplement"]):
        packed["instructions"] += "\n\n" + path.read_bytes().decode("utf-8")
        packed["instruction_paths"].append(path.relative_to(root).as_posix())
        packed["component_hashes"][path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    for path in (root / "config/operations/tasks.json", root / "schemas/operations/analysis-request.schema.json"):
        packed["component_hashes"][path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    packed["request_hash"] = digest(request)
    packed["artifact"] = task["artifact"]
    packed["execution_state"] = "not_run"
    packed["remaining_preconditions"] = ["authorize source IDs", "freeze registered document versions", "verify country/type/edition relationships", "verify model connection", "complete evidence processing and validation"]
    return fingerprint_packet(packed)


def validate_source_groups(request: dict, documents: list[dict], *, unavailable_ids=frozenset()) -> None:
    """Check registered metadata. Call after authorization and before dispatch."""
    lookup = {d["id"]: d for d in documents}
    if len(lookup) != len(documents):
        raise ValueError("Duplicate registered source IDs")
    groups = request["source_groups"]
    ids = [i for g in groups for i in g["document_ids"] if i not in unavailable_ids]
    if unavailable_ids and request["task"] == "compare" and request["comparison_mode"] not in ("documents", "custom"):
        raise ValueError("Unreadable documents cannot establish the requested edition/country comparison. A descriptive document comparison can use the remaining evidence.")
    if any(i not in lookup for i in ids):
        raise ValueError("Unknown registered source")
    if any(not lookup[i].get("verified") for i in ids):
        raise ValueError("Source metadata must be verified before execution")
    if request["task"] != "compare":
        return
    mode = request["comparison_mode"]
    if len(groups) < 2 or (mode in ("revision", "ndc_nap") and len(groups) != 2):
        raise ValueError("Invalid comparison group count")
    if any(not lookup[i].get(k) for i in ids for k in ("edition_id", "country_code", "instrument")):
        raise ValueError("Comparison metadata requires country, instrument and edition IDs")
    edition_groups = [{lookup[i]["edition_id"] for i in g["document_ids"] if i in lookup} for g in groups]
    if any(edition_groups[a] & edition_groups[b] for a in range(len(groups)) for b in range(a+1, len(groups))):
        raise ValueError("Equivalent translations/editions cannot be in opposing comparison groups")
    countries = {lookup[i]["country_code"] for i in ids}
    if mode == "countries":
        grouped = [{lookup[i]["country_code"] for i in g["document_ids"]} for g in groups]
        if any(len(g) != 1 for g in grouped) or len(countries) != len(groups):
            raise ValueError("Country comparison requires distinct country groups")
    if mode in ("revision", "ndc_nap") and len(countries) != 1:
        raise ValueError("This comparison requires one country")
    if mode == "ndc_nap" and [{lookup[i]["instrument"] for i in g["document_ids"]} for g in groups] != [{"NDC"}, {"NAP"}]:
        raise ValueError("NDC and NAP groups require the corresponding verified instruments")
    if mode == "revision":
        if len({lookup[i]["instrument"] for i in ids}) != 1 or any(len(g) != 1 for g in edition_groups):
            raise ValueError("Revision comparison needs two editions of the same instrument")
        orders = [{lookup[i].get("edition_order") for i in g["document_ids"]} for g in groups]
        if any(len(o) != 1 or None in o for o in orders) or next(iter(orders[0])) >= next(iter(orders[1])):
            raise ValueError("Earlier/later edition order is unverified or reversed")


def scoped_evidence(root: Path, request: dict, extraction: dict) -> dict:
    """Filter complete extracted records in code, retaining all supporting context."""
    domains = {t["id"]: set(t["domain_ids"]) for t in read_json(root / "config/v2/taxonomy.json")["topics"]}
    def matches(record):
        labels = record["labels"]
        values = {**labels, "domain_ids": set().union(*(domains[t] for t in labels["topic_ids"]))}
        return all(not selected or set(selected) & set(values.get(key, []))
                   for key, selected in request["filters"].items())
    records = [r for r in extraction["records"] if matches(r)]
    ids = {e for r in records for e in r["evidence_ids"]}
    # Include transitive quote context even if it does not itself match a filter.
    lookup = {e["local_id"]: e for e in extraction["evidence"]}
    pending = list(ids)
    while pending:
        for eid in lookup[pending.pop()]["context_evidence_ids"]:
            if eid not in ids:
                ids.add(eid)
                pending.append(eid)
    return {**extraction, "records": records, "evidence": [e for e in extraction["evidence"] if e["local_id"] in ids]}


def delivery_checks(request: dict, extraction: dict) -> dict:
    checks = {}
    for r in extraction["records"]:
        if r["kind"] != "commitment":
            continue
        missing = []
        selected = request["requested_fields"]
        if "actors" in selected and not any(a["role"] == "lead" for a in r["actors"]):
            missing.append("No source-stated lead extracted for this commitment in the selected sources.")
        if "finance" in selected and not r["finance"]:
            missing.append("No structured finance amount or arrangement extracted; retain any financing condition or stated support need separately.")
        if "indicators" in selected:
            if not r["indicators"]:
                missing.append("No indicator extracted for this commitment in the selected sources.")
            elif any(i["baseline_value"] is None for i in r["indicators"]):
                missing.append("At least one extracted indicator has no stated baseline value.")
        if "targets" in selected and not r["reference_period"] and not any(t["target_period"] for t in r["targets"]):
            missing.append("No deadline or milestone period extracted for this commitment in the selected sources.")
        checks[r["local_id"]] = missing
    return checks


def validate_operation_output(root: Path, request: dict, output: dict, extraction: dict,
                              sources: list[dict], *, partial=False) -> None:
    """Validate joins and task contracts as well as structured output shape."""
    from .profiles import require
    task = next(t for t in read_json(root / "config/operations/tasks.json")["tasks"] if t["id"] == request["task"])
    schema = read_json(root / "config/v2/pipelines.json")["routes"][task["route"]]["schema"]
    records = {r["local_id"]: r for r in extraction["records"]}
    evidence = {e["local_id"]: e for e in extraction["evidence"]}
    commitments = {key for key, r in records.items() if r["kind"] == "commitment"}
    sections = ["scope", *request["requested_fields"], "limitations"] if schema == "report" else None
    errors = validate_v2(root, schema, output, required_sections=sections,
                         known_evidence_ids=set(evidence), known_record_ids=set(records), known_commitment_ids=commitments)
    require(not errors, "; ".join(errors))
    group_ids = [g["id"] for g in request["source_groups"]]
    countries = sorted({s["country_code"] for s in sources})
    if schema != "comparison":
        require(output["country_codes"] == countries and output["source_group_ids"] == group_ids,
                "Output changed the requested country or source scope")
    if schema == "report":
        require(output["availability"] == ("partial" if partial else "complete_in_declared_scope"), "Analysis availability must match its source coverage")
        require([s["section_id"] for s in output["sections"]] == sections, "Output sections differ from selected fields")
        for priority in output["prioritized_commitments"]:
            require(set(priority["evidence_ids"]) <= set(records[priority["commitment_id"]]["evidence_ids"]),
                    "Priority evidence is unrelated to its commitment")
        if request["task"] == "brief" and "questions" not in request["requested_fields"]:
            require(not output["followup_questions"], "Follow-up questions were disabled")
    for node in _walk(output):
        if "citations" not in node:
            continue
        refs = node["citations"]
        require(refs["record_ids"] and set(refs["record_ids"]) <= set(records), "Finding needs known scoped records")
        linked = {eid for rid in refs["record_ids"] for eid in records[rid]["evidence_ids"]}
        require(refs["evidence_ids"] and set(refs["evidence_ids"]) <= linked, "Finding evidence is unrelated to its records")
        # No executable arithmetic syntax is accepted from model text. Until an
        # application calculation is supplied, comparisons remain descriptive.
        require(node.get("calculation") is None, "No application-verified calculation was supplied; describe the source values")
        if node["kind"] == "analyst_suggestion":
            require(request["include_analyst_proposals"] or
                    (request["task"] == "brief" and "questions" in request["requested_fields"]), "Analyst proposals were disabled")
    if schema == "comparison":
        expected = request["source_groups"]
        require(len(output["groups"]) == len(expected), "Comparison changed group count")
        for actual, group in zip(output["groups"], expected):
            require(actual["group_id"] == group["id"] and actual["label"] == group["label"] and
                    actual["document_version_ids"] == group["document_ids"] and not actual["release_ids"], "Comparison changed a frozen group")
        require([row["dimension"] for row in output["rows"]] == request["requested_fields"], "Comparison must include every selected dimension exactly once")
        segment_documents = {s["id"]: d["document_id"] for d in sources for s in d["segments"]}
        for row in output["rows"]:
            require(row["normalization_calculation"] is None, "Unverified normalization calculation")
            require([c["group_id"] for c in row["cells"]] == group_ids, "Comparison must include each group once per row")
            require(row["comparability_reason"].strip(), "Explain comparability and missing bases")
            for cell, group in zip(row["cells"], expected):
                require(cell["state"] != "not_processed" or (partial and not any(s["document_id"] in group["document_ids"] for s in sources)), "A comparison group was not processed")
                require(bool(cell["findings"]) == (cell["state"] == "found"), "Cell findings disagree with its state")
                for finding in cell["findings"]:
                    require(all(segment_documents[evidence[e]["segment_id"]] in group["document_ids"]
                                for e in finding["citations"]["evidence_ids"]), "Cell cites a different comparison group")
    if schema == "workplan":
        covered = set()
        checks = delivery_checks(request, extraction)
        for row in output["rows"]:
            require(row["commitment_ids"] and set(row["commitment_ids"]) <= commitments, "Unknown workplan commitment")
            require(len(row["commitment_ids"]) == 1 and not covered.intersection(row["commitment_ids"]), "Use one delivery row per source commitment")
            require(row["missing_information"] == checks[row["commitment_ids"][0]], "Missing-information checks differ from the selected application checks")
            require(row["source_stated_action"]["citations"]["record_ids"] == row["commitment_ids"], "Delivery action cites a different commitment")
            covered.update(row["commitment_ids"])
            require(row["source_stated_action"]["kind"] == "source_fact", "Source action must remain a source statement")
            for field, key in (("source_actor_ids", "actors"), ("source_finance_ids", "finance"), ("source_indicator_ids", "indicators")):
                allowed = {d["local_id"] for rid in row["commitment_ids"] for d in records[rid][key]}
                require(set(row[field]) <= allowed, "Workplan detail belongs to an unrelated commitment")
                require(key in request["requested_fields"] or not row[field], "Workplan includes a disabled field")
            for field in ("proposed_support_activity", "proposed_indicator"):
                require(row[field] is None or (request["include_analyst_proposals"] and row[field]["kind"] == "analyst_suggestion"), "Proposal must be enabled and labeled")
        require(covered == commitments, "Delivery checks omitted scoped commitments")


def evidence_table(request: dict, extraction: dict) -> list[dict]:
    """Selected columns are a projection; the complete evidence annex is retained."""
    fields = {"targets": "targets", "risk_context": "risk_contexts", "actors": "actors", "finance": "finance", "indicators": "indicators"}
    return [{**{k: r[k] for k in ("local_id", "kind", "label_en", "description_en", "geography", "evidence_ids")},
             "extraction_notes": extraction.get("notes", []),
             **{fields[f]: r[fields[f]] for f in request["requested_fields"] if f in fields}}
            for r in extraction["records"]]

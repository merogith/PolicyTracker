"""Write explicitly synthetic fixtures for the v2 engineering pack, never country data."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write(name, data):
    folder = ROOT / "examples/v2"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    segments = {
        "s-meta": "Synthetic training example only. Reporting party: Kazakhstan. National scope. This is invented policy text, not an actual government document.",
        "s-1": "К 2030 году установить 20 систем раннего предупреждения о наводнениях при условии международного финансирования.",
        "s-2": "Ведущее ведомство — Министерство водных ресурсов. Мера направлена на повышение готовности к наводнениям.",
    }
    write("synthetic-input.json", {"synthetic": True, "owned_segment_ids": list(segments), "source_segments": segments})
    def ev(eid, sid, context):
        return {"local_id": eid, "segment_id": sid, "quote_original": segments[sid], "english_segment_id": None, "context_evidence_ids": context}
    def support(path, ids, basis="explicit"):
        return {"field_path": path, "evidence_ids": ids, "basis": basis, "reason": "Supported by the cited synthetic wording/context."}
    target = {
        "local_id": "t-1", "metric_text": "Flood early-warning systems installed", "metric_key_candidate": "flood_warning_systems_installed_count",
        "target_kind": "quantitative", "value": {"raw_token": "20", "decimal": "20", "evidence_id": "e-1", "notation": "dot_decimal"},
        "lower": None, "upper": None, "comparator": "equal", "unit_raw": "систем", "unit_key_candidate": "count_systems",
        "desired_direction": "increase", "basis": "absolute", "baseline_value": None, "baseline_period": None,
        "target_period": "2030", "denominator": None, "scenario": None,
        "conditionality": "explicitly_conditional", "condition_text": "Subject to international financing",
        "total_or_additional": "not_stated", "sector_scope": [], "gas_scope": [], "lulucf_treatment": None, "gwp_basis": None, "evidence_ids": ["e-1"]}
    record = {
        "local_id": "r-1", "kind": "commitment", "label_en": "Install flood early-warning systems",
        "description_en": "Install 20 flood early-warning systems by 2030, conditional on international financing.",
        "geography": {"reporting_party": "Kazakhstan", "country_codes": ["KAZ"], "scope": "national", "locations": [], "evidence_ids": ["e-meta"]},
        "labels": {"topic_ids": ["CLM-04"], "objectives": ["disaster_risk_reduction"], "cross_cutting_tags": ["finance"],
                   "hazards": ["flood"], "population_groups": [], "risk_components": ["capacity"], "risk_functions": ["early_warning_preparedness"], "policy_instruments": ["information_warning"], "unmapped_terms": []},
        "reference_period": None,
        "targets": [target],
        "actors": [{"local_id": "a-1", "name_original": "Министерство водных ресурсов", "name_en": "Ministry of Water Resources", "role": "lead", "target_ids": ["t-1"], "evidence_ids": ["e-2"]}],
        "finance": [], "indicators": [],
        "risk_contexts": [{"local_id": "risk-1", "hazard_text": "наводнения", "exposed_assets_or_places": [], "vulnerability_drivers": [],
                           "stated_capacities": [], "consequence_en": None, "likelihood_text": None, "severity_text": None,
                           "assessment_period": None, "scenario": None, "target_ids": ["t-1"], "action_link": "prepares", "link_basis": "explicit", "evidence_ids": ["e-1", "e-2"]}],
        "details": [{"local_id": "d-1", "kind": "support_need", "text_en": "International financing is required for this commitment.", "target_ids": ["t-1"], "evidence_ids": ["e-1"]}],
        "evidence_ids": ["e-meta", "e-1", "e-2"],
        "field_support": [support("/geography", ["e-meta"], "inherited_context"), support("/kind", ["e-1"], "classification"),
                          support("/label_en", ["e-1"]), support("/description_en", ["e-1"]), support("/labels", ["e-1", "e-2"], "classification"),
                          support("/targets/0/value", ["e-1"], "numeric_normalization"), support("/targets/0/target_period", ["e-1"]),
                          support("/targets/0/conditionality", ["e-1"]), support("/targets/0/condition_text", ["e-1"]),
                          support("/targets/0/metric_text", ["e-1"]), support("/targets/0/unit_raw", ["e-1"]),
                          support("/targets/0/comparator", ["e-1"]), support("/targets/0/desired_direction", ["e-1"], "classification"),
                          support("/targets/0/basis", ["e-1"], "classification"), support("/actors/0", ["e-2"]),
                          support("/risk_contexts/0", ["e-1", "e-2"]), support("/details/0", ["e-1"])],
        "missing_fields": [{"field_path": p, "reason": "not_stated", "detail": None} for p in ["/targets/0/baseline_value", "/targets/0/baseline_period", "/reference_period"]],
        "quality_flags": ["Synthetic demonstration only; not country evidence", "Baseline and detailed financing amount not stated"]}
    output = {"evidence": [ev("e-meta", "s-meta", []), ev("e-1", "s-1", ["e-meta"]), ev("e-2", "s-2", ["e-1"])],
              "records": [record], "coverage": [{"segment_id": s, "disposition": "extracted", "record_ids": ["r-1"], "reason": "Supports the synthetic commitment or its metadata."} for s in segments], "notes": ["Invented evidence for software verification; not a country assessment."], "issues": []}
    write("extraction.json", output)
    write("translation.json", {"segments": [
        {"segment_id": "s-meta", "source_language": "en", "method": "identity", "official_parallel_segment_id": None, "english_text": segments["s-meta"], "term_decisions": [], "notes": [], "quality_flags": []},
        {"segment_id": "s-1", "source_language": "ru", "method": "machine_translation", "official_parallel_segment_id": None,
         "english_text": "By 2030, install 20 flood early-warning systems, subject to international financing.", "term_decisions": [], "notes": ["Synthetic example translation"], "quality_flags": []},
        {"segment_id": "s-2", "source_language": "ru", "method": "machine_translation", "official_parallel_segment_id": None,
         "english_text": "The lead agency is the Ministry of Water Resources. The measure aims to improve flood preparedness.", "term_decisions": [], "notes": ["Synthetic example translation"], "quality_flags": []}]})
    finding = {"text_en": record["description_en"], "kind": "source_fact", "citations": {"evidence_ids": ["e-1"], "record_ids": ["r-1"]}, "calculation": None, "limitations": ["Invented demonstration only"]}
    config = json.loads((ROOT / "config/v2/pipelines.json").read_text(encoding="utf-8"))
    supported = {
        "risk_context_and_drr": finding,
        "scope_and_method": {**finding, "text_en": "The invented source identifies Kazakhstan and national scope.", "citations": {"evidence_ids": ["e-meta"], "record_ids": ["r-1"]}},
        "implementation_and_actors": {**finding, "text_en": "The Ministry of Water Resources is named as the lead agency; this is a stated role, not evidence of implementation.", "citations": {"evidence_ids": ["e-2"], "record_ids": ["r-1"]}},
        "finance_and_support": {**finding, "text_en": "The commitment is conditional on international financing."},
        "limitations": {**finding, "text_en": "The source explicitly identifies itself as invented training text, not a government document.", "citations": {"evidence_ids": ["e-meta"], "record_ids": ["r-1"]}},
    }
    sections = [{"section_id": s, "state": "found" if s in supported else "not_found_in_scope",
                 "findings": [supported[s]] if s in supported else [],
                 "gap_note": None if s in supported else "Synthetic fixture has no material for this section."}
                for s in config["features"]["prime"]["required_sections"]]
    for section in sections:
        if section["section_id"] == "changes_and_coherence":
            section.update(state="not_applicable", gap_note="One invented source; no cross-document comparison is possible.")
    write("prime-report.json", {"country_codes": ["KAZ"], "source_group_ids": ["synthetic-group"], "availability": "complete_in_declared_scope",
                               "headline_findings": [finding], "sections": sections, "prioritized_commitments": [], "followup_questions": [], "limitations": ["This is not a real country report."]})
    print("Wrote synthetic input, extraction, translation and report fixtures")


if __name__ == "__main__":
    main()

"""Generate provider-friendly JSON schemas. Runtime validation remains mandatory."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def obj(**fields):
    return {"type": "object", "properties": fields, "required": list(fields), "additionalProperties": False}


def arr(item):
    return {"type": "array", "items": item}


def enum(*values):
    return {"type": "string", "enum": list(values)}


S = {"type": "string"}
N = {"type": ["string", "null"]}
I = {"type": "integer", "minimum": 1}
B = {"type": "boolean"}
SS = arr(S)
finding = obj(text=S, evidence_ids=SS, statement_ids=SS,
              epistemic_status=enum("source_statement", "derived", "analyst_inference"))
evidence = obj(evidence_id=S, document_id=S, segment_id=S, pdf_page=I,
               quote_original=S, quote_english=S, context_evidence_ids=SS)
target = obj(target_id=S, wording_english=S, value_decimal=N, lower_decimal=N, upper_decimal=N,
             comparator=enum("equal", "at_least", "at_most", "range", "approximate", "not_stated"),
             unit=N, target_basis=enum("absolute", "historical_reduction", "BAU_reduction", "intensity", "share", "qualitative", "other", "not_stated"),
             baseline_value=N, baseline_year=N, deadline=N, denominator=N, scenario=N,
             conditionality=enum("explicitly_conditional", "explicitly_unconditional", "not_stated", "unclear"),
             condition_text=N, total_or_additional=enum("total", "additional", "not_stated"),
             sector_scope=SS, gas_scope=SS, lulucf_treatment=N, gwp_basis=N,
             evidence_ids=SS, uncertainty=SS)
fact = obj(category=enum("actor", "institutional_arrangement", "legal_instrument", "finance_cost", "funding_secured", "funding_requested", "financing_source", "financing_gap", "indicator", "baseline", "monitoring_arrangement", "support_need", "barrier", "implementation_step", "hazard", "vulnerability", "beneficiary", "inclusion", "co_benefit", "tradeoff", "policy_link", "other"),
           name=S, value_text=S, normalized_decimal=N, unit=N, currency=N, price_year=N,
           period=N, role=N, source_or_method=N, evidence_ids=SS)
field_support = obj(field_path=S, evidence_ids=SS, method=enum("explicit", "contextual", "deterministic_conversion"), explanation=S)
statement = obj(statement_id=S, label_en=S, description_en=S,
                reporting_party=N, country_codes=SS,
                geographic_scope=enum("national", "subnational", "regional", "EU", "multi_country", "unknown"),
                location_text=N, reference_date=N, topics=SS, cross_cutting_tags=SS,
                unmapped_topic=N,
                documentation_status=enum("mentioned", "priority_stated", "action_proposed", "action_committed", "implementation_reported", "result_reported", "unclear"),
                assertion_kind=enum("planned", "observed", "projected", "scenario", "recommendation", "historical", "template", "unclear"),
                record_types=SS, objectives=arr(enum("mitigation", "adaptation", "disaster_risk_reduction", "unspecified")),
                targets=arr(target), facts=arr(fact), evidence_ids=SS,
                field_support=arr(field_support), review_flags=SS,
                performance_status=enum("not_assessed"))
coverage = obj(segment_id=S, disposition=enum("extracted", "relevant_no_new_records", "background", "duplicate", "unreadable", "excluded"),
               statement_ids=SS, reason=S)
relation = obj(source_ids=SS, target_ids=SS,
               relationship=enum("repeated_assertion", "translation_equivalent", "same_variant", "revises", "supersedes", "related", "parent_child", "contradicts", "unrelated", "unresolved"),
               evidence_ids=SS, reason=S, needs_review=B)

SCHEMAS = {
    "release-manifest": obj(schema_version=S, release_id=S, country_code=S,
                            availability=enum("complete", "partial", "no_documents_supplied"),
                            run_id=S, corpus_snapshot_id=S,
                            document_versions=arr(obj(document_id=S, sha256=S)),
                            generation=obj(provider_route=S, requested_model=S, actual_model=N,
                                           requested_effort=S, confirmed_effort=N, completed_at=N,
                                           prompt_hash=S, schema_hash=S, taxonomy_hash=S),
                            review=obj(state=enum("draft", "in_review", "approved", "rejected"), reviewer_id=N,
                                       reviewed_at=N, validation_receipt_id=N),
                            coverage=obj(pages_total={"type":"integer","minimum":0}, pages_accounted_for={"type":"integer","minimum":0},
                                         unreadable_pages={"type":"integer","minimum":0}, translation_complete=B),
                            artifacts=arr(obj(kind=S, relative_path=S, sha256=S, media_type=S)),
                            limitations=SS),
    "dashboard": obj(schema_version=S, release_id=S, country_code=S, review_state=S,
                     overview=arr(finding),
                     policy_rows=arr(obj(commitment_id=S, label=S, target_display=S, topic_ids=SS, domains=SS,
                                         objectives=SS, documentation_status=S,
                                         performance_status=enum("not_assessed", "insufficient_evidence", "on_track", "off_track", "wrong_direction", "achieved"),
                                         performance_assessment_id=N, conditionality=S, deadline=N, evidence_ids=SS)),
                     source_coverage_note=S, limitations=SS),
    "extraction": obj(evidence=arr(evidence), statements=arr(statement), coverage=arr(coverage), issues=SS),
    "translation": obj(segments=arr(obj(segment_id=S, method=enum("identity", "verified_official_parallel", "machine_translation"), english_text=S, quality_flags=SS))),
    "triage": obj(document_id=S, metadata_proposals=arr(obj(field=S, proposed_value=N, evidence_ids=SS, reason=S)),
                 language_spans=arr(obj(page_from=I, page_to=I, languages=SS, evidence_ids=SS)),
                 relationship_candidates=arr(relation), quality_issues=SS,
                 recommended_disposition=enum("eligible_for_curated_review", "ad_hoc_support", "needs_metadata_review", "needs_ocr", "unrelated"),
                 review_questions=SS),
    "reconciliation": obj(groups=arr(obj(proposed_commitment_id=S, statement_ids=SS, distinct_variant_ids=SS, evidence_ids=SS, reason=S)),
                          relations=arr(relation),
                          changes=arr(obj(before_ids=SS, after_ids=SS, change_type=enum("added", "restated", "number_changed", "scope_changed", "condition_changed", "not_restated", "withdrawn", "superseded", "unresolved"), evidence_ids=SS, description=S, comparability_note=S)),
                          conflicts=arr(finding), review_queue=SS),
    "report": obj(country_codes=SS, availability=enum("evidence_available", "partial", "no_documents_supplied"),
                  headline_findings=arr(finding),
                  sections=arr(obj(section_id=S, title=S, findings=arr(finding), evidence_gap=N)),
                  prioritized_commitment_ids=SS, questions_for_followup=arr(finding), limitations=SS),
    "comparison": obj(groups=arr(obj(group_id=S, label=S, source_ids=SS, coverage_note=S)),
                      matrix=arr(obj(dimension=S, cells=arr(obj(group_id=S, findings=arr(finding), availability=enum("found", "not_found", "not_processed", "not_applicable"))))),
                      comparability=arr(obj(group_ids=SS, dimension=S, verdict=enum("comparable", "partially_comparable", "not_comparable"), reason=S, evidence_ids=SS)),
                      synthesis=arr(finding), exclusions=SS, limitations=SS),
    "quality": obj(findings=arr(obj(severity=enum("critical", "major", "minor"), entity_id=S, field_path=S, issue=S, evidence_ids=SS, proposed_correction=N, reason=S)),
                   coverage_gaps=SS, unresolved_questions=SS,
                   proposed_gate=enum("pass_automated_checks", "needs_repair", "needs_human_review", "incomplete_inputs")),
    "chat": obj(answer_blocks=arr(finding), coverage_limitations=SS, clarification=N,
                proposed_brief=obj(task=N, topics=SS, audience=N, length=N, question=N),
                proposed_action=enum("none", "request_extraction_job", "request_comparison_job", "save_ad_hoc_report")),
    "run-request": obj(kind=enum("prime_candidate", "ad_hoc", "comparison"), country_code=N,
                       source_snapshot_id=S, source_groups=arr(obj(group_id=S, document_ids=SS, report_ids=SS)),
                       provider_route=enum("codex_chatgpt", "chatgpt_plan", "openai_api"), model=S, reasoning_effort=S,
                       prompt_version=S, taxonomy_version=S, schema_version=S,
                       brief=obj(task=S, topics=SS, audience=S, length=S, question=N), idempotency_key=S),
}


def main():
    out = ROOT / "schemas"
    out.mkdir(exist_ok=True)
    for name, schema in SCHEMAS.items():
        schema = {"$schema": "https://json-schema.org/draft/2020-12/schema", "title": name + " v1.0.0", **schema}
        (out / (name + ".schema.json")).write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(SCHEMAS)} schemas")


if __name__ == "__main__":
    main()

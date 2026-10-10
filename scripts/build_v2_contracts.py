"""Generate the v2 engineering pack. No model calls or production state changes.

These are task and persistence contracts, not a claim of implemented workers.
Editable config/v2/taxonomy.json and vocabulary.json are the source of truth.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
S = {"type": "string"}
N = {"type": ["string", "null"]}
I = {"type": "integer"}
B = {"type": "boolean"}


def obj(**fields):
    return {"type": "object", "properties": fields, "required": list(fields), "additionalProperties": False}


def arr(item):
    return {"type": "array", "items": item}


def enum(*values):
    return {"type": "string", "enum": list(values)}


def nullable(schema):
    return {"anyOf": [schema, {"type": "null"}]}


def desc(schema, explanation):
    return {**schema, "description": explanation}


SS = arr(S)
VOCABULARY = json.loads((ROOT / 'config/v2/vocabulary.json').read_text(encoding='utf-8'))


def build():
    taxonomy = json.loads((ROOT / "config/v2/taxonomy.json").read_text(encoding="utf-8"))
    topic_ids = [t["id"] for t in taxonomy["topics"]]
    domain_names = [d["id"] for d in taxonomy["domains"]]
    vocab = VOCABULARY
    cite = obj(evidence_ids=SS, record_ids=SS)
    field_support = obj(field_path=S, evidence_ids=SS,
                        basis=enum("explicit", "inherited_context", "classification", "numeric_normalization"), reason=S)
    # Processing failures and conflicts retain their own evidence/coverage locations.
    missing = obj(field_path=S, reason=enum(*(v for v in vocab["missing_reasons"]
                  if v not in ("conflicting_sources", "unreadable", "not_processed"))), detail=N)
    geo = obj(reporting_party=N, country_codes=SS,
              scope=enum(*vocab["geography_scopes"]),
              locations=SS, evidence_ids=SS)
    labels = obj(topic_ids=arr(enum(*topic_ids)), objectives=arr(enum(*vocab["objectives"])),
                 cross_cutting_tags=arr(enum(*vocab["cross_cutting_tags"])),
                 hazards=arr(enum(*vocab["hazards"])), population_groups=arr(enum(*vocab["population_groups"])),
                 risk_components=arr(enum(*vocab["risk_components"])),
                 risk_functions=arr(enum(*vocab["risk_functions"])),
                 policy_instruments=arr(enum(*vocab["policy_instruments"])),
                 unmapped_terms=arr(obj(facet=S, term=S, evidence_ids=SS, proposed_definition=S)))
    numeric = obj(raw_token=S, decimal=N, evidence_id=S,
                  notation=enum("dot_decimal", "comma_decimal", "ambiguous", "textual"))
    numeric = desc(numeric, "Exact original numeric token plus decimal-string normalization; no unit conversion or inferred values. Ambiguous/textual tokens retain decimal=null pending an explicit normalizer.")
    target = obj(local_id=S, metric_text=S, metric_key_candidate=N,
                 target_kind=enum(*vocab["target_kinds"]),
                 value=nullable(numeric), lower=nullable(numeric), upper=nullable(numeric),
                 comparator=enum(*vocab["target_comparators"]),
                 unit_raw=N, unit_key_candidate=N, desired_direction=enum(*vocab["target_directions"]),
                 basis=enum(*vocab["target_bases"]),
                 baseline_value=nullable(numeric), baseline_period=N, target_period=N,
                 denominator=N, scenario=N, conditionality=enum(*vocab["conditionalities"]),
                 condition_text=N, total_or_additional=enum(*vocab["target_totals"]),
                 sector_scope=SS, gas_scope=SS, lulucf_treatment=N, gwp_basis=N,
                 evidence_ids=SS)
    actor = obj(local_id=S, name_original=S, name_en=S,
                role=enum(*vocab["actor_roles"]),
                target_ids=SS, evidence_ids=SS)
    finance = obj(local_id=S, kind=enum(*vocab["finance_kinds"]),
                  amount=nullable(numeric), currency=N, price_period=N, implementation_period=N,
                  description_en=S, target_ids=SS, evidence_ids=SS)
    indicator = obj(local_id=S, name_en=S, unit_raw=N, baseline_value=nullable(numeric),
                    baseline_period=N, cadence=N, data_source=N, target_ids=SS, evidence_ids=SS)
    detail = obj(local_id=S, kind=enum(*vocab["detail_kinds"]),
                 text_en=S, target_ids=SS, evidence_ids=SS)
    evidence = obj(local_id=S, segment_id=S,
                   quote_original=S, english_segment_id=N, context_evidence_ids=SS)
    risk = obj(local_id=S, hazard_text=N,
               exposed_assets_or_places=SS, vulnerability_drivers=SS, stated_capacities=SS,
               consequence_en=N, likelihood_text=N, severity_text=N,
               assessment_period=N, scenario=N, target_ids=SS,
               action_link=enum(*vocab["risk_action_links"]),
               link_basis=enum("explicit", "inherited_context", "not_stated"), evidence_ids=SS)
    record = obj(local_id=S, kind=enum(*vocab["record_kinds"]), label_en=S, description_en=S,
                 geography=geo, labels=labels, reference_period=N,
                 targets=arr(target), actors=arr(actor), finance=arr(finance), indicators=arr(indicator),
                 risk_contexts=arr(risk), details=arr(detail),
                 evidence_ids=SS, field_support=arr(field_support), missing_fields=arr(missing), quality_flags=SS)
    finding = obj(text_en=S, kind=enum("source_fact", "source_reported_observation", "derived", "analyst_suggestion"),
                  citations=cite, calculation=N, limitations=SS)
    section = obj(section_id=S, state=enum(*vocab["section_states"]), findings=arr(finding), gap_note=N)
    group = obj(group_id=S, label=S, document_version_ids=SS, release_ids=SS, scope_note=S)
    relation = obj(source_record_ids=SS, target_record_ids=SS,
                   kind=enum(*vocab["relation_kinds"]),
                   evidence_ids=SS, reason=S)
    schemas = {
        "triage": obj(document_profiles=arr(obj(input_id=S, title=N,
                         instrument_type=enum("NDC", "NAP", "NAP_annex", "sectoral_NAP", "support", "unrelated", "unknown"),
                         document_state=enum("adopted", "submitted", "draft", "unknown"),
                         publication_date=N, languages=SS, geography=geo,
                         disposition=enum("prime_candidate", "ad_hoc_support", "quarantine", "needs_ocr"),
                         metadata_evidence_ids=SS,
                         notes=desc(SS, "Advisory scope, source and metadata qualifications; these do not certify official authority."),
                         issues=desc(SS, "Unresolved defects preventing the proposed country/instrument attribution or use of the supplied text. General sample limitations belong in notes."))),
                     relationships=arr(obj(input_ids=SS, kind=enum("translation", "revision", "annex", "duplicate", "unknown"), evidence_ids=SS, reason=S))),
        "translation": obj(segments=arr(obj(segment_id=S, source_language=S,
                        method=enum("identity", "official_parallel", "machine_translation"),
                        official_parallel_segment_id=N, english_text=S,
                        term_decisions=arr(obj(original=S, english=S, reason=S)),
                        notes=desc(SS, "Advisory scope and source qualifications preserved for readers; not unresolved translation defects."),
                        quality_flags=desc(SS, "Unresolved fidelity or coverage defects within the owned source text. Nonempty flags block acceptance; never clear them merely to pass validation.")))),
        "extraction": obj(evidence=arr(evidence), records=arr(record),
                          coverage=arr(obj(segment_id=S,
                                           disposition=desc(enum("extracted", "background", "unreadable"),
                                               "Use extracted for every relevant source occurrence, including repeated statements, with its supporting record/evidence links. Background covers non-policy text, blank templates and declared scope exclusions with a reason. Unreadable is a blocking processing defect, never absence. Do not discard repeated evidence as a duplicate."),
                                           record_ids=SS, reason=S)),
                          notes=desc(SS, "Advisory source, scope and accounting qualifications retained for readers. These do not certify authority or complete-document coverage."),
                          issues=desc(SS, "Unresolved defects preventing use of the owned source evidence. Nonempty issues block acceptance. Declared sample boundaries, faithful source uncertainty, unavailable out-of-scope graphs and absent separate English-layer IDs belong in notes when original evidence remains usable. Never hide genuine defects merely to pass.")),
        "labels": obj(assignments=arr(obj(record_id=S, labels=labels, field_support=arr(field_support), issues=SS))),
        "reconciliation": obj(groups=arr(obj(local_group_id=S, proposed_existing_commitment_id=N,
                                  record_ids=SS, variants=arr(obj(local_variant_id=S, target_ids=SS, temporal_role=enum(*vocab["temporal_roles"]), evidence_ids=SS)),
                                  reason=S, unresolved=SS)), relations=arr(relation),
                              changes=arr(obj(before_record_ids=SS, after_record_ids=SS,
                                  kind=enum(*vocab["change_kinds"]), finding=finding)), issues=SS),
        "quality": obj(check_scope=enum("extraction_source_coverage", "reconciliation", "report_claims", "translation"),
                       findings=arr(obj(severity=enum("critical", "major", "minor"), entity_id=N, field_path=N,
                           issue=S, evidence_ids=SS, disposition=enum("repair", "qualify", "omit_unsupported_claim", "retain_separate_variants", "record_limitation"), correction=N)),
                       coverage_gaps=SS, proposed_result=enum("pass", "repair", "incomplete")),
        "report": obj(country_codes=SS, source_group_ids=SS, availability=enum("complete_in_declared_scope", "partial", "no_documents_supplied"),
                      headline_findings=arr(finding), sections=arr(section),
                      prioritized_commitments=arr(obj(commitment_id=S, reason=S, evidence_ids=SS)),
                      followup_questions=arr(finding), limitations=SS),
        "comparison": obj(groups=arr(group),
                          rows=arr(obj(dimension=S, cells=arr(obj(group_id=S, state=enum(*vocab["section_states"]), findings=arr(finding))),
                              comparability=enum("comparable", "partially_comparable", "not_comparable", "descriptive_only"),
                              comparability_reason=S, normalization_calculation=N)),
                          synthesis=arr(finding), exclusions=SS, limitations=SS),
        "workplan": obj(country_codes=SS, source_group_ids=SS,
                        rows=arr(obj(commitment_ids=SS, source_stated_action=finding,
                            source_actor_ids=SS, source_finance_ids=SS, source_indicator_ids=SS,
                            proposed_support_activity=nullable(finding), proposed_indicator=nullable(finding),
                            missing_information=SS, verification_questions=SS)), limitations=SS),
        "chat": obj(answer_blocks=arr(finding), coverage_note=S,
                    proposed_action=enum("none", "expand_sources", "run_exhaustive_extraction", "run_comparison", "save_ad_hoc_version"),
                    proposed_brief=obj(task=N, focus_topic_ids=arr(enum(*topic_ids)), audience=N, length=N, question=N), clarification=N),
        "document-version": obj(schema_version=S, document_version_id=S, document_family_id=N,
                   blob_sha256=S, storage_key=S, source_url=N, source_checked_at=N, title=N,
                   instrument_type=S, language_codes=SS, reporting_party=N, country_codes=SS,
                   publication_date=N, authority_state=enum("verified_official", "declared_unverified", "unofficial", "unknown"),
                   relationships=arr(obj(other_version_id=S, kind=enum("translation_of", "revises", "supersedes", "annex_to", "supports"), evidence_ids=SS)),
                   provenance_event_id=S),
        "source-segment": obj(segment_id=S, document_version_id=S, source_sha256=S, parser_fingerprint=S,
                       physical_page=I, printed_page=N, kind=enum("prose", "table", "figure", "footnote", "metadata", "unreadable"),
                       language=S, original_text=S, headings=SS, required_context_segment_ids=SS,
                       bbox=nullable(obj(x0={"type":"number"},y0={"type":"number"},x1={"type":"number"},y1={"type":"number"})),
                       quality_flags=SS),
        "canonical-commitment": obj(commitment_id=S, country_codes=SS, reporting_party=N,
                       record_ids=SS, domain_ids=arr(enum(*domain_names)),
                       variants=arr(obj(variant_id=S, target_ids=SS, temporal_role=enum(*vocab["temporal_roles"]),
                                        relation_event_ids=SS)), aliases=SS, identity_event_id=S),
        "release": obj(schema_version=S, release_id=S, country_code=S, corpus_snapshot_id=S, corpus_generation=I,
                       run_id=S, run_sequence=I, bundle_sha256=S,
                       availability=enum("complete_in_declared_scope", "partial", "no_documents_supplied"),
                       automated_validation=obj(state=enum("pending", "passed", "passed_with_limitations", "failed"), receipt_id=N, validator_version=S),
                       audit=obj(state=enum("not_audited", "annotated", "corrected"), event_ids=SS),
                       artifacts=arr(obj(kind=S, storage_key=S, sha256=S)),
                       stage_provenance=arr(obj(stage=S, artifact_hash=S, reused=B, provider_route=N,
                           requested_model=N, actual_model=N, requested_effort=N, confirmed_effort=N,
                           prompt_hash=N, schema_hash=N, taxonomy_hash=N, input_hash=S,
                           origin_run_id=S, source_version_ids=SS, validation_receipt_id=S,
                           method_components=arr(obj(path=S, sha256=S, archive_key=S)),
                           prepared_packet_sha256=S, prepared_packet_archive_key=S)), limitations=SS),
        "run-request": obj(kind=enum("prime", "ad_hoc", "comparison"), feature=S, country_code=N,
                           corpus_snapshot_id=S, source_groups=arr(group),
                           model=obj(route=enum("codex_chatgpt", "chatgpt_plan", "openai_api"), model=S, effort=S, fallback_allowed=enum("never")),
                           brief=obj(focus_topic_ids=arr(enum(*topic_ids)), audience=S, length=S, question=N),
                           idempotency_key=S),
        "dashboard": obj(release_id=S, country_code=S, source_as_of=N, generated_at=S,
                         availability=enum("complete_in_declared_scope", "partial", "no_documents_supplied"),
                         audit_state=enum("not_audited", "annotated", "corrected"),
                         highlights=arr(finding),
                         counts=obj(canonical_commitments=I, quantitative_variants=I, qualitative_commitments=I, risk_context_records=I),
                         rows=arr(obj(commitment_id=S, label_en=S, topic_ids=arr(enum(*topic_ids)),
                                      domain_ids=arr(enum(*domain_names)),
                                      hazards=arr(enum(*vocab["hazards"])), risk_functions=arr(enum(*vocab["risk_functions"])),
                                      target_display=S, conditionality=S, kind=enum(*vocab["record_kinds"]),
                                      performance_status=enum("not_assessed"), evidence_ids=SS)),
                         limitations=SS),
    }
    return taxonomy, schemas


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    taxonomy, schemas = build()
    for name, body in schemas.items():
        write_json(ROOT / f"schemas/v2/{name}.schema.json", {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": f"PolicyTracker {name} method {VOCABULARY['version']}", **body})
    lines = ["# Topic catalogue v2", "", "Generated from editable config/v2/taxonomy.json. Routing definitions are proposed project guidance, not benchmarked international categories.", "", "A topic is the subdomain level. Topic-to-domain mappings may be many-to-many; derive the domain filter from selected topics. Retain unmapped material.", "", "| ID | Topic | Domain(s) | Definition | Routing rule |", "|---|---|---|---|---|"]
    for topic in taxonomy["topics"]:
        names={d["id"]:d["name"] for d in taxonomy["domains"]}
        lines.append("| " + " | ".join([topic["id"],topic["name"],", ".join(names[d] for d in topic["domain_ids"]),topic["definition"],topic["routing_rule"]]) + " |")
    path = ROOT / "docs/knowledge/topic-catalog.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(schemas)} v2 schemas, schemas from editable taxonomy/vocabulary and a topic catalogue")


if __name__ == "__main__":
    main()

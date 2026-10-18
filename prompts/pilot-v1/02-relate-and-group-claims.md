# Prompt 2 - Relate labeled records, create claims, and score response evidence

## Purpose

Use the source records from Prompt 1 plus `config/pilot-v1/relation-taxonomy.json` to create a traceable claim register. Do not read or relabel the source document.

## Workflow

1. Compare candidate records using labels for retrieval, then decide using their actual propositions and evidence. Shared topics, hazards, groups, places, actors, or document sections alone never justify a merge.
2. Assign supported record-to-record relations. Preserve singleton records as singleton claims. Every input record must belong to exactly one claim.
3. Merge duplicate/restated evidence for the same proposition. Attach supporting records only when they support the same proposition. Keep separate milestones, actions, indicators, years, and subsets as separate claims; link them when useful.
4. Before relating quantitative facts, compare metric, unit, baseline, denominator, period, scope, scenario, and condition. Preserve all variants. Mark comparable incompatible assertions as contested; never average, silently select, or overwrite source values.
5. Build each claim's `label_rollup` as the union of labels on records legitimately included in that claim. **For every rolled-up value, preserve its originating `source_record_ids`.** Preserve distinct values rather than flattening them (including statement types, places, stakeholder roles, and quantitative facts).
6. Assign one `response_evidence_score` to each final claim using the 0-4 rubric in the relation taxonomy. Score the highest stage explicitly supported by source evidence, once per claim. Repeated reports do not add points.
7. Score 0 means context, hazard/impact, projection, need/barrier, finance need, or outcome-only information that does not itself evidence a response. It is not a negative score and does not mean no real-world action exists. Report outcome direction and setbacks in separate fields.
8. Do not treat a stated target as implementation. A finance estimate/need is not allocated finance. A delivered output is not proof that the intended outcome improved.
9. Add claim-to-claim links such as `related` or `parent_child` only when they help navigate distinct claims. Preserve traceability to original document/page/segment/quote and all member record IDs.
10. Produce topic distributions using distinct claim IDs. A multi-topic claim appears once under each supported topic. Never sum or average claim scores into a domain/country score, ranking, “on track” label, or performance color.

## Output

Return valid JSON only:

```json
{
  "stage":"relate_group_score",
  "relation_taxonomy_version":"2.0.0-pilot",
  "record_relations":[{"relation_id":"...","from_record_id":"...","to_record_id":"...","type":"...","rationale":"...","confidence":0.0,"review_status":"proposed"}],
  "claims":[
    {
      "claim_id":"stable ID",
      "canonical_claim_text":"one faithful proposition",
      "member_record_ids":["..."],
      "relation_ids":[],
      "label_rollup":{
        "subject_paths":[{"domain_id":"...","subdomain_id":"...","topic_id":"...","source_record_ids":[]}],
        "statement_types":[{"value":"...","source_record_ids":[]}],
        "purposes":[{"value":"...","source_record_ids":[]}],
        "risk_components":[{"value":"...","source_record_ids":[]}],
        "hazards":[{"value":"...","source_record_ids":[]}],
        "affected_groups":[{"value":"...","source_record_ids":[]}],
        "cross_cutting_themes":[{"value":"...","source_record_ids":[]}],
        "geographic_scopes":[{"value":"...","source_record_ids":[]}],
        "places":[{"value":"...","source_record_ids":[]}],
        "stakeholders":[{"name":"...","relationship":"...","source_record_ids":[]}],
        "quantitative_fact_ids":[{"fact_id":"...","source_record_id":"..."}]
      },
      "response_evidence_score":0,
      "response_score_label":"context_outcome_only|commitment_target|defined_action|resourced_underway|delivered_output",
      "response_score_rationale":"short source-grounded reason citing record IDs",
      "score_confidence":"high|medium|low",
      "outcome_signal":"improving|worsening|no_clear_change|mixed|not_comparable|not_reported",
      "setback_flags":[],
      "status":"proposed|reviewed|contested|superseded|closed",
      "open_issue":null,
      "evidence_links":[{"record_id":"...","document_id":"...","page":0,"segment_id":null,"quote":"..."}]
    }
  ],
  "claim_relations":[{"relation_id":"...","from_claim_id":"...","to_claim_id":"...","type":"related|parent_child|unresolved","rationale":"..."}],
  "topic_rollups":[{"topic_id":"...","distinct_claim_count":0,"counts_by_response_score":{"0":0,"1":0,"2":0,"3":0,"4":0},"highest_evidenced_level":null,"coverage_note":"what the reviewed documents contain; not a performance judgment"}],
  "review_queue":[]
}
```

Do not create a country/domain score. Do not hide uncertainty behind a single color. The claim register and topic rollups describe the reviewed evidence and its documented response stage only.

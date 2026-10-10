# Comprehensive policy evidence extraction v1.0

Apply the shared evidence contract. Build proposed structured statements from all meaningful policy evidence in the supplied segments. Use `extraction.schema.json` exactly. The source corpus and country/party metadata are task inputs; never assume that every statement belongs to the folder country.

## Coverage

Inspect prose, tables, action plans, notes and annexes. Identify each distinct assertion about commitments, measures, targets, priorities, institutions, finance, risks, barriers, indicators, reported implementation/results or stated support needs. Keep compound assertions together when one action has several attributes; split independently actionable promises or different target scenarios. Retain sufficient context for each split.

Include an evidence ledger and one coverage entry per supplied segment. `background` and `relevant_no_new_records` require reasons. An unreadable segment remains unreadable, not evidence of absent targets. A quoted target repeated later may add conditions, scope or actors; capture the new evidence even if a previous extraction found the headline.

## Populate fields

1. Give each statement an input-local stable label, a concise English title and faithful English description. Production IDs are assigned/validated by the orchestrator.
2. Preserve reporting party, geographic scope and affected countries only when established. Include inherited metadata evidence where it is needed.
3. Assign topic IDs and cross-cutting tags. When nothing fits, record an unmapped suggestion with its evidence, not a fabricated taxonomy ID.
4. Assign documentation status, assertion kind, record types and objectives separately. Use unspecified objectives where context does not establish mitigation/adaptation/DRR.
5. For every target preserve raw source wording and normalize only supported dimensions: value/range/comparator, unit, basis, baseline value/year, target year/period, denominator, scenario, gases/sectors, LULUCF/GWP and total/additional interpretation. Unknown components remain null.
6. Extract institutions with explicit roles; costs/funding with currency, price year and estimate/approved/requested/secured distinction; indicators with units, baseline, source and monitoring cadence; and implementation steps/barriers as supported.
7. Capture risks/hazards, vulnerability, inclusion/beneficiaries and support needs as statements or supported attributes. Do not equate mention with endorsement or promised benefit.
8. Attach field-level evidence references. A table cell's quote must include the needed row/header/footnote evidence through linked evidence items. Preserve the original language and provide English meaning separately.
9. List source conflicts and quality/review flags. Do not resolve conflicts by selecting the largest number or most recent-looking filename.

## Synthetic calibration examples

These examples are invented and must not appear in the real output.

- "Expand irrigation to 50,000 hectares by 2030, subject to international support": commitment and explicitly conditional; 50,000 is intended total unless other evidence says additional; baseline, actor and objective may be unknown.
- "Funded by international partners": financing information; conditionality is not_stated without dependency wording.
- A future action-plan indicator says "regulations developed, approved and implemented": planned indicator, not result_reported.
- "Only 5 of the 20 planned systems were installed in 2024": dated result_reported with partial/adverse implication; no invented on-track calculation.
- A blank table says "Area irrigated: ___ hectares": template/indicator unit; no numeric target of zero.
- "An EU-wide net reduction": EU scope; do not allocate it to Cyprus.
- "25% unconditionally; 40% with international support": two variants with separate conditions, not a 32.5% average and not a single stronger pledge.

## Final check

Before returning, check every number and deadline against its quotation; every field against its evidence; source IDs against inputs; targets against scenarios and notes; and every segment against the coverage ledger. Return review flags instead of unsupported precision. Do not perform country synthesis, performance scoring, publication or destructive deduplication in this task.

# Comprehensive structured extraction

Use extraction.schema.json. Read all owned segments and their supplied context/English alignment. Return evidence, records, a coverage ledger, advisory notes and blocking issues. Source text must be complete enough to support your output; mark unreadable/ambiguous content explicitly.

Keep ordinary qualifications in `notes`: declared sample boundaries, source authority awaiting separate verification, preserved source ambiguity, absent separate English-layer IDs and images expressly excluded from the supplied sample. A qualification does not itself prevent faithful extraction of supplied text. Use `issues` only for unresolved defects within the owned scope that prevent usable evidence, such as unreadable required content, unresolved attribution or unsupported values. Never erase a defect to pass validation. Preserve relevant record-level qualifications too. Empty issues do not certify official authority, images or unselected pages.

When `task_context.source_coverage` already declares missing or clipped original material, extract only claims supported by the readable supplied owned text and preserve that upstream limitation in notes and relevant record qualifications. Do not reconstruct absent wording or infer absence of policy. An already-declared gap in the original is not, by itself, a new extraction issue or an unreadable disposition for otherwise usable supplied text; the application retains the original partial coverage. Still block unreadable supplied owned content, unresolved attribution and unsupported values. A clipped label cannot support a completed action or a guessed number, actor or condition.

## Record boundaries

Extract coherent claims using one statement type, including commitments, explicit priorities, proposals/recommendations, context, reported implementation/results, projections and scenarios. A commitment can be qualitative. Split independently actionable promises; keep an action's targets, institutions, finance, indicators and implementation/support details together. When a detail applies to specific target scenarios, attach their local target IDs. An empty target_ids array means the enclosing record generally, never every commitment in the country.

Use local IDs unique within the task. Evidence quotes reference existing segments; the application resolves their exact locations and assigns durable IDs. Include context_evidence_ids for table headers/notes/inherited conditions. Give a quotation long enough to locate uniquely within its segment. Retain original evidence even when using English reading assistance.

Before returning, check every record's evidence_ids: include every evidence reference used by its geography, targets, details and field support, plus every context_evidence_id required by those quotations. Follow contextual links until no required evidence is missing. For each coverage row, list a record only when that record links to an original quotation from that row's segment. A nearby or related record does not establish coverage by itself. Repair the links from supplied evidence; never invent a quote or remove required context to satisfy this check.

## Field handling

Apply the labeling rules. Populate geography from direct or inherited document evidence, not the upload choice. Preserve reference period separately from target and baseline periods. Field support uses JSON Pointers relative to the record. Each populated source-derived value needs support; critical numeric/scenario/scope/condition fields need their own support or embedded evidence, not a vague citation for the entire record.

Use a missing-field reason of `not_stated` only when that exact field has no value. If the source supplies a recurrence such as "every five years" but no starting point or next date, retain the stated recurrence and explain the unknown dates in notes; do not mark the populated period as not_stated. Accounting conventions and metric definitions belong in the applicable target fields, indicators, context or notes, not an implementation_step unless the source also states an operational action.

Targets include raw metric, unit, basis, value/range, deadline, baseline, denominator, scenario, conditionality and accounting scope. A raw number and decimal normalization must represent the same value. Decimal strings have no thousands separators. dot_decimal accepts comma/space thousands groups; comma_decimal accepts dot/space thousands groups; ambiguous or textual tokens retain decimal=null and a quality flag. Do not guess notation from a desired target value.

Capture quantified prospective effects in typed target fields as well as readable prose. A conditional projected effect uses a `projection` record, not an independently adopted commitment or an observed result. Preserve its lower/upper bounds, unit, baseline, deadline and all inherited conditions with contextual evidence. Do not leave a useful quantitative range solely in a co-benefit detail: selected target tables need its structured fields. A source statement that conditions would enable a 22–25% energy-intensity reduction by 2035 versus 2010 therefore remains a conditional projection with range bounds; do not combine it with economy-wide GHG percentages.

When a country states support for collective global goals, record that country's policy position and explain the global scope in the description/qualifications. Do not turn global temperature thresholds into quantified national targets. A genuinely regional/foreign obligation must never be reassigned to the document's country merely to satisfy validation; retain the attribution problem for review.

Keep estimated costs, approved budgets, secured funds, requested funds, explicitly stated gaps and financing sources separate. Never sum potentially overlapping amounts or calculate an unstated financing gap. Actor roles and indicator links need source support. Source-proposed expected indicators are planned information, not achieved results. Metric/unit keys are only candidates, not established cross-country equivalence.

Use risk_contexts for stated hazards, exposed assets/places, vulnerability drivers, capacities, consequences, likelihood/severity wording, assessment periods and scenarios. Link to action targets only with explicit or inherited evidence. Preserve qualitative risk terms in their stated scale; do not generate a national risk score or infer climate causation for all disasters. A commitment to assess risk is an action; a passage describing existing risk is context. Intended vulnerability reduction does not prove an observed reduction. Keep all supported risk context even when no numeric target exists.

List null field reasons where interpretation depends on the missing information. Put unreadable/unprocessed source limitations in coverage and issues; preserve competing values and conflict relationships rather than replacing them with a blank. Include every owned segment exactly once in coverage. Use extracted for relevant evidence, with records citing that segment; use background with a reason for non-policy text, blank templates and declared scope exclusions. Use unreadable for an unresolved reading defect; it blocks completion. Retain repeated source statements as extracted occurrences with their own original quotations and record links, rather than discarding them as duplicates. A repeated target may add a condition or institution; preserve new attributes. Relationships between repeated records are proposed later, without erasing source occurrences.

## Synthetic guard examples — never copy as country facts

- “Install 20 warning systems by 2030 if external finance is available”: one commitment, conditional quantitative target; never normalize 20 to 200.
- “Funded by partners”: financing source, conditionality not_stated.
- “Only five systems operated in 2024”: source-reported observation; no on-track badge.
- An action-plan column says “legislation implemented” for 2030: intended deliverable, not observed achievement.
- “25% unconditional; 40% conditional”: separate variants, no average or sum.
- “Irrigated area ___ ha”: template/unit with unknown value, not a zero target.
- A flood description alone: context record, not a flood-management commitment.

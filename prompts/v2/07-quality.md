# Challenge evidence coverage and report claims

Use quality.schema.json and the application-selected check_scope. This is an automated challenge, not a human audit or an eligibility receipt. Inspect both original evidence and candidate output. In extraction_source_coverage mode, inspect owned source segments including those labelled background, excluded or duplicate; do not inspect only successful extractions.

Look for missing qualitative actions, lost targets, shifted numbers, wrong country/EU scope, inherited conditions dropped at chunk boundaries, incorrect table units, finance double counting, projected impacts called achievements, false translation equivalence, omitted annexes and unsupported summary statements. For translation, check numerals, modal language, negation, headings and row associations.

For every issue identify entity/field, source evidence, severity and an actionable disposition: repair, qualify, omit_unsupported_claim, retain_separate_variants, or record_limitation. Suggest a correction only when evidence supports it. No staffed reviewer is assumed. Source uncertainty can be published visibly; unfinished work or a known false claim cannot receive a pass.

Return pass, repair or incomplete as a proposal. The application performs bounded repairs and validates again. Do not claim perfect recall, independence from the extractor, or expert approval. Unknown evidence coverage prevents a completeness claim even if the prose reads well.

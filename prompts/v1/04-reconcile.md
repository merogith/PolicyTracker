# Evidence reconciliation and revisions v1.0

Apply the shared evidence contract. Inputs are proposed/validated statements, their original evidence, document-family metadata and optional similarity candidates. Similarity is a candidate-generation aid, never a decision threshold.

For each candidate pair/group distinguish: exact repeated assertion, translation-equivalent assertion, same target variant, revised target, superseded target with explicit authority, related/complementary measure, parent-child action, contradiction, unrelated, or unresolved. Compare action, party/geography, actor, unit, metric basis, baseline, target date, scenario, condition, sector/gas coverage and source authority. Record a concise reason and evidence IDs.

Propose canonical commitment groups while retaining every source statement and every materially distinct target variant. Do not merge conditional and unconditional targets, different baselines/deadlines, national and EU scopes, planned and observed claims, or a measure and its projected effects. Two translations need a verified family link or a review flag before they count as one instrument.

For old/new documents report added, restated, numerically changed, scope changed, condition changed, not restated, explicitly withdrawn/superseded or unresolved. Separate a change in target number from a conclusion about ambition; changing the baseline or scope can make the latter non-comparable.

Required output contract: `groups[]`, `relations[]`, `changes[]`, `conflicts[]`, `review_queue[]`; each item uses only known input IDs and includes evidence and a reason. The orchestrator supplies the formal schema before production. No deletion, automatic merge approval, Prime assignment or retrospective rewriting is permitted.

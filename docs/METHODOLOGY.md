# How the Regional Policy Tracker is prepared

## What am I reading?

A Country Profile combines an Overview of saved findings with a searchable Policy register. Each finding or statement can lead to original and English evidence. Documents & translations records what was processed, while Version history preserves earlier results. Read the [browser guide](../design/prototype/README.md) to use these views without learning the processing method first.

The current method below governs future preparation. A saved profile uses its archived definitions and instructions, available under **Version, definitions and run details**. Automated checks establish software/source-link invariants, not expert review, implementation progress or policy quality. Prepared custom requests are distinct from executed results; neither filtering nor interface wording changes rewrite saved findings.

## Lean knowledge method 3.0

The existing v2 pipeline uses method 3.0 contracts for new runs. One `kind` field is displayed as **Statement type**: context/finding, priority, proposal/recommendation, commitment, implementation reported, result reported, projection, scenario or unclear. Separate assertion/documentation fields are removed from new records. Dates retain historical meaning; templates stay in coverage exclusions. A concrete commitment described as a priority remains a commitment with the source priority wording in its description/details.

One optional `labels.risk_functions` list replaces DRR phases and resilience functions: risk understanding; risk prevention and reduction; early warning and preparedness; anticipatory action; emergency response; recovery and reconstruction; coping and continuity; systemic transformation. This is a project analytical pool, not an official framework crosswalk or a performance scale.

Select substantively supported topics and labels; derive domains from topic memberships. One integrated solar-irrigation action can have AGR-01 and ENE-01 and appear in Agriculture, Water and Energy while counting once overall. Split independently actionable measures and separate promises from reported delivery. Conditional/unconditional targets remain linked variants. No primary domain or arbitrary label limit is required. Lists may be empty; preserve unmatched wording and evidence.

Co-occurring hazards and functions do not establish every possible relationship. Separate heat-preparedness and flood-recovery actions, or retain the specific relationships in existing linked risk/details for an inseparable programme. Filters identify record co-occurrence, not causal proof. Match any selected value within a field and all selected fields; condition and period must match the same target variant. Shared budgets are never multiplied or allocated across labels without source evidence.

Evidence gaps are not policy labels. Explain material missing values only. Not stated requires adequate review; unreadable/unprocessed limitations belong in coverage/issues. Preserve conflicting values and proposed source relationships. Display unexplained blanks as no extracted value, never national absence. New validation rejects field-level processing/conflict reasons and a not-stated reason on a populated value; archived contracts keep their original rules.

The taxonomy has 11 domains and 41 topics. The `climate` domain is displayed as **Climate & disaster policy**. CLM-08, **Disaster risk and management**, covers substantive cross-sector all-hazards context, governance, response and recovery without a narrower topic. Prefer CLM-04 for warnings/readiness and sector topics for sector measures. Neither this domain nor Urban membership establishes climate causation or geographic scope.

Source review for this bounded addition used existing extracted text, including Albania NAP physical pages 31 and 73 (civil emergency coordination and reconstruction) and the updated first NDC page 6 (earthquake/reconstruction context). It was a vocabulary review, not a full extraction-quality assessment or new country run.

Other optional facets keep distinct questions. An amount alone does not require a Finance theme; a group mention does not prove a benefit or gender analysis. Use linked facts for details and retain specifically useful risk concepts such as residual/cascading risk. No new processing stage or classification service is introduced.

Archived profiles retain their bytes, codebooks, original fields and evidence. Readers/exports support both record shapes without guessed relabeling. Statement/risk filters cannot be carried across vocabulary versions silently. Changed method fingerprints prevent incompatible checkpoint reuse. Moving an old extraction to this method requires a new, explicitly started extraction when record boundaries or statement meaning change; the labels-only extension cannot perform that migration.

### Old and new options

These are all options in the changed classification groups. The correspondence guides new extraction; it is not a script for relabeling archived evidence. All other definitions remain available in the generated [complete codebook](knowledge/labeling-guide.md).

| Old field and every option | New field and every option | What changes |
|---|---|---|
| **Record kind (5):** commitment, priority, context, implementation observation, result observation | **Statement type (9):** Context / finding (`context`), Priority (`priority`), Proposal / recommendation (`proposal`), Commitment (`commitment`), Implementation reported (`implementation_observation`), Result reported (`result_observation`), Projection (`projection`), Scenario (`scenario`), Unclear (`unclear`) | One choice describes each coherent claim. |
| **Assertion kind (8):** planned, observed, projected, scenario, recommendation, historical, template, unclear | Included in Statement type above; no separate choice | Planned alone does not prove commitment. Historical meaning stays in dates. Templates are excluded with a coverage reason. |
| **Documentation status (7):** mentioned, priority stated, action proposed, action committed, implementation reported, result reported, unclear | Included in Statement type above; no separate choice | Removes a second description of the same statement. No implementation score is inferred. |
| **DRR phase (9):** risk understanding, prevention, risk reduction, preparedness, anticipatory action, response, recovery, cross phase, unspecified | **Risk and resilience functions (8):** Risk understanding (`risk_understanding`), Risk prevention and reduction (`risk_prevention_reduction`), Early warning and preparedness (`early_warning_preparedness`), Anticipatory action (`anticipatory_action`), Emergency response (`emergency_response`), Recovery and reconstruction (`recovery_reconstruction`), Coping and continuity (`coping_continuity`), Systemic transformation (`systemic_transformation`) | Optional multiple selection. Cross-phase becomes the specifically supported functions. Unspecified becomes an empty list, with useful source wording retained. |
| **Resilience function (6):** anticipate, absorb, adapt, transform, recover, unspecified | Included in Risk and resilience functions above; no separate choice | Generic “adapt” is too broad for an automatic mapping; classify the actual action. Anticipate may mean readiness or triggered action and needs evidence. Absorb usually relates to continuity; recover to recovery. |
| **Missing reason (6):** not stated, ambiguous, conflicting sources, unreadable, not processed, not applicable | Same technical options retained for archive compatibility; no policy filter or required reason for every blank | New field-level gaps use not stated, ambiguous or not applicable only where material. Conflicts retain values and source relationships; unreadable/unprocessed content belongs in coverage/issues. |
| **Climate domain; 40 topics** | **Climate & disaster policy; 41 topics**, including Disaster risk and management (`CLM-08`) | Adds a home for substantive all-hazards statements without implying climate causation. Existing topic IDs and memberships remain stable. |

### Worked labeling examples

Illustrative statements below are invented. The old column shows plausible combinations under the old structure, not an automatic historical mapping.

| Source statement | Old labels | New labels and treatment |
|---|---|---|
| “We will install 20 flood warning systems by 2030, subject to international finance.” | Commitment + planned + action committed; preparedness + anticipate | **Commitment**; **Early warning and preparedness**; flood. One conditional target with quantity, deadline and financing condition. No implementation claim. |
| “The ministry should introduce heat action plans.” | Context + recommendation + action proposed; preparedness + anticipate | **Proposal / recommendation**; **Early warning and preparedness**; heat. No adopted government promise. |
| “Ten backup units were installed in hospitals in 2024.” | Implementation observation + observed + implementation reported; cross phase + absorb | **Implementation reported**; **Coping and continuity**; health topic. Keep the date and attribution. Installation is an output, not proof of health outcomes. |
| “The evaluation reports a 15% decline in losses after the programme.” | Result observation + observed + result reported; risk reduction + adapt | **Result reported**; **Risk prevention and reduction** where supported. Preserve method, period and attribution; do not assert causality beyond the evidence. |
| “Flood losses may double by 2050 under scenario X.” | Context + projected + mentioned; risk understanding | **Projection**; flood; scenario X and 2050 retained as details. Label a risk assessment function only if assessment/information is substantive. |
| “A shared programme will install solar irrigation for farms.” | Commitment + planned + action committed; separate agriculture/water/energy appearances | **Commitment**, AGR-01 + ENE-01; domains derived as Agriculture, Water and Energy. One record and one shared budget. Climate purpose needs source support. |
| “Heat contingency plans will be prepared; flood-damaged bridges will be rebuilt.” | A combined record could imply both functions for both hazards | Two **Commitment** records: heat + preparedness; flood + recovery. Keep the source link without inventing heat recovery or flood preparedness. |
| A processing failure hides the budget paragraph. | Empty budget + not processed | Coverage/processing issue; no “budget not stated” finding. A missing extraction is not evidence of source absence. |

The interface offers any-of selection within each field and all-of matching across fields. Target condition and period must match the same target. There is no primary-domain requirement or artificial label limit. The overall count uses distinct source records; overlapping domain totals are not additive.

## Reading and presentation method

The [evidence experience specification](16-evidence-experience.md) defines the implemented Understand → Explore → Verify hierarchy, report/perspective matrix, visualization/counting rules, saved-view contract and integration gaps. Overview and Policy register remain the two country views. Summary, Targets, Risks and resilience, and Delivery and support are deterministic presets over the same source records, not processing routes.

Domain → topic remains the only hierarchy. The reader derives domains from the selected version’s archived codebook and keeps independent objectives, statement types, hazard/risk/function facets, groups and instruments separate. Qualitative actions and unmapped terms remain visible. Actor, finance, indicator and risk details retain their target-specific links. Field support explains explicit wording, inherited context, classification and numeric normalization.

Counts mean source records or explicitly labeled target variants. Multi-label buckets overlap; frequency is not importance. Evidence limitations remain inspectable; unexplained empty fields never establish source absence. Full-scope saved narrative is not regenerated when the user filters records. Browser-local named views, sorting, grouping and exports do not change evidence, methods or model execution.

Optional report results are clearly labeled synthetic demonstrations. The country worker still performs its existing six-step local workflow. Method 3.0 updates the extraction contract and its active consumers; archived releases retain their own definitions.


One **Country Profile** per country, with **two core views of the same evidence**. The regional dashboard shows countries, source coverage and which views are available. It does not generate another set of reports.

The current scope is accurate document extraction, useful evidence-based analysis and clear presentation. Improve existing prompts, checks and views before adding processing stages. The six-step table also describes optional blueprint stages; it is not a required implementation backlog. Method & prompts marks what the local worker runs. For the stage-by-stage distinction, see the [verified workflow review](METHOD_REVIEW.md). For file ownership and worked edits, see [Customize the tracker](CUSTOMIZATION.md).

| View | Question it answers | What it contains |
|---|---|---|
| **Overview** | What needs attention? | A five-minute brief and expandable country narrative: priorities, climate/disaster risks, adaptation, mitigation, delivery, finance, inclusion and limitations. |
| **Policy register** | What exactly is stated, where, by whom and by when? | Searchable targets, qualitative actions, risk-context records and linked institutions, finance/support needs and indicators. Filter by sector, hazard, risk and resilience function or delivery information. Every record links to original/English evidence. |

**Documents & translations** is a reading and audit utility, not an analytical report. It provides the full English reading layer alongside preserved originals, editions, page references and translation coverage. **Version history** holds earlier complete profiles and the one version selected for everyone. These utilities do not need independent “main” reports.

Risk/DRR and delivery information are not removed. They remain explicit thematic sections in the Overview and independent labels/linked details in the Policy register. Comparison is an optional tool requiring suitable document groups. With one document, both core views remain useful and cross-document changes are not applicable. A full report is an export of this same profile, not an additional generation job.

## Six preparation steps

| Step | What happens | Actual task Markdown |
|---|---|---|
| 1. Identify and read | Freeze source versions, parse/OCR every page, identify country/type/edition/language, preserve original text and prepare aligned English. | [02-triage.md](../prompts/v2/02-triage.md), [03-translate.md](../prompts/v2/03-translate.md) |
| 2. Extract and label | Visit every scoped segment, extract typed evidence and attach source locators and independent labels. Validate the records. | [04-extract.md](../prompts/v2/04-extract.md) |
| 3. Connect documents | Propose links and supported differences within the existing reconciliation task. Preserve every source record, condition and target variant. No automatic merging. | [06-reconcile.md](../prompts/v2/06-reconcile.md) |
| 4. Additional evidence review (deferred) | Optional model challenge of omissions and interpretations. Existing deterministic checks already run; another AI pass is not required for trials. | [07-quality.md](../prompts/v2/07-quality.md) |
| 5. Prepare the profile | Write cited overview and thematic findings, including supported similarities/differences. Code renders the unchanged source records in the register. | [08-prime-report.md](../prompts/v2/08-prime-report.md) |
| 6. Check and save | Validate the bundle and select a successful local profile while respecting a pin. Results publish automatically in the local workspace; optional moderation can unpublish them. Hosted publication remains separate. | Application logic; [07-quality.md](../prompts/v2/07-quality.md) is an optional blueprint |

Structured evidence tasks include [00-evidence-contract.md](../prompts/v2/00-evidence-contract.md) and [01-labeling-rules.md](../prompts/v2/01-labeling-rules.md), plus one task prompt. Page-image recovery uses the standalone [14-recover-page.md](../prompts/v2/14-recover-page.md) and its code-defined schema. The schema, taxonomy, trusted task context and untrusted source data are separate inputs. A browser tab is not a model stage: the register, regional dashboard, filters, source reader and version selector do not need additional synthesis prompts.

New country versions reuse compatible unchanged translations/extractions, then reconcile and regenerate the affected bundle. They are not regenerated every time someone reads or exports them. Complete processing covers all source segments; targeted retrieval is suitable for follow-up questions, not a claim of exhaustive extraction.

Repeated substantive wording remains extracted with its original source occurrences and record links. New coverage rows use extracted, background (with a reason), or unreadable; unreadable owned segments fail full extraction acceptance. There is no duplicate/skip disposition that can bypass required evidence. Archived schemas retain their original vocabulary. Reconciliation proposes relationships without merging records, and checked proposals are supplied to the Overview for the same evidence batch.

Missing or clipped material already disclosed by source recovery remains an upstream coverage limit. Translation preserves the readable supplied wording, including clipped labels, and records the limitation without inventing the missing text. Extraction uses only supported readable evidence. Neither stage upgrades partial source coverage, and neither treats an existing source gap alone as a new translation or extraction defect. Omitting or altering supplied text, inventing evidence, or failing to read an owned segment still blocks acceptance.

For newly returned extraction results, the worker completes a record's main evidence list with any existing evidence IDs already explicitly cited in that same record's details or field support. This is an index of the model's existing references, not an inferred citation or a change to its claims. The raw response and an exact list of additions and source paths remain archived. Unknown evidence, invalid quotations, attribution or coverage defects and reported blocking issues still fail the unchanged acceptance checks. Saved historical results are not rewritten.

## Labels and interpretation

The [taxonomy](../config/v2/taxonomy.json) defines domains and topics; the [vocabulary](../config/v2/vocabulary.json) defines independent types and facets. A record keeps its country, document/edition/language, evidence type, sector/topic, policy purpose, relevant risk/DRR facets and source locators. Reporting party and affected countries remain distinct. Explicit regional, EU or multi-country context, proposals and observations may retain multiple affected countries or an empty list for global scope; they are not reassigned to the reporting country. Commitments and national, subnational or unknown-scope records still require the selected country's attribution. Quantitative targets additionally preserve units, baselines, years, scope and conditionality. Actors, finance, monitoring and risk details remain typed information, not forced into target fields.

- A policy commitment is not implementation evidence. “On track” requires suitable dated observations and an explicit assessment method.
- “Not found in these documents” is a scope-limited evidence gap, not proof of national absence.
- Different units, baselines, scope and conditions can make targets incomparable.
- Compare the same action or metric using existing extracted fields. The runtime currently accepts descriptive source-value comparisons, with no model-authored arithmetic. When the basis matches, explain a supported qualitative difference; when it differs or is unknown, describe the statements and the mismatch. Qualitative differences in actions, actors, funding or monitoring can still be useful. Cite both sides; use before/after wording only with supported edition order and continuity. These rules run inside existing prompts, without a separate comparison engine.
- The worker accepts a typed change only when the linked source profiles have known publication dates at the same precision and every before date precedes every after date. Undated files and historical restatements inside a single file retain descriptive relationships and source history; an adoption date is not silently substituted for publication metadata.
- Accounting definitions alone are not implementation steps. Preserve them in target fields, indicators, context or notes. A missing-field marker applies only to the exact empty field or an absence value (`not_stated`, `unknown`, `unclear`, `unspecified`) explicitly declared by that field's schema. An ordinary string containing that wording is still populated. A stated recurrence remains populated even when its next date is unknown.
- A source can explicitly label a target conditional without stating the condition. Retain that label and a null condition only with an exact, explained `not_stated` missing-field entry; never borrow another target's condition or invent one to satisfy validation. Undeclared omissions and empty pseudo-conditions remain blocking.
- Counts mean source records, not unique commitments. Repeated statements remain attached to each document. Possible links and conflicts stay proposals; neither recency nor similarity authorizes merging or choosing a winner.
- Original passages and machine translations remain distinguishable. Ambiguity is disclosed.
- No suitable document pair means limited/not-applicable alignment or revision comparison, not an invented result.
- Unreadable or unprocessed evidence must not become “not found.” An explicit source statement of absence is a cited finding within its stated scope.
- The objective “mitigation” means emissions reduction/carbon sinks; disaster-impact mitigation uses DRR labels when supported. See [UNDRR's terminology distinction](https://www.undrr.org/terminology/mitigation).

The existing ten required report sections remain intact under these two core views. Their mapping to views, output files and prompt routes is in [config/methodology.json](../config/methodology.json). `prime` remains an internal route name for compatibility.

## Optional Analysis tools

These reuse the evidence pipeline but create separate user outputs; they never select or publish a Country Profile.

| Task | Distinct result | Task route and options supplement |
|---|---|---|
| Extract evidence | A scoped evidence table with selected fields | [10-focused-analysis.md](../prompts/v2/10-focused-analysis.md) + [extract.md](../prompts/operations/extract.md) |
| Compare policies | A comparison matrix across explicit country, edition or document groups | [11-comparison.md](../prompts/v2/11-comparison.md) + [compare.md](../prompts/operations/compare.md) |
| Check delivery gaps | Missing delivery information in selected sources; optional clearly labeled support proposals | [12-workplan.md](../prompts/v2/12-workplan.md) + [gaps.md](../prompts/operations/gaps.md) |
| Prepare a brief | A cited answer to a specific policy question | [09-briefing.md](../prompts/v2/09-briefing.md) + [brief.md](../prompts/operations/brief.md) |

All analysis tasks append the [operational request contract](../prompts/operations/00-request-contract.md). Source groups, filters, output fields, optional suggestions, instructions and model/effort/route are supplied as [structured request JSON](../schemas/operations/analysis-request.schema.json). Saved Method & output settings control narrative language/detail and analysis focus; task-specific output fields remain explicit. [Relabeling](../prompts/v2/05-relabel.md) and [chat](../prompts/v2/13-chat.md) are prepared extensions, not additional first-delivery reports.

The independent [Translate documents prompt](../prompts/operations/translate.md) appends that supplement directly to the shared translation route, without the separate operational request contract, and saves full English/original copies without thematic filters. See [the current task requirements and configuration workflow](14-lean-tools-translations-and-configuration.md).

Triage, translation and extraction distinguish advisory `notes` from blocking `issues` / `quality_flags`. Notes retain declared sample limits, faithful handling of source artifacts and disclosed source ambiguity when the supplied evidence remains usable. Unresolved attribution, fidelity or required-coverage defects still stop processing. Translation notes remain with aligned segments; extraction notes remain with the saved evidence, synthesis input, readers and JSON/CSV/readable exports. Synthesis keeps a batch's notes with every part using that batch's records or evidence; unrelated batches' notes are not copied globally. Notes without retained records or evidence are preserved separately within the same bounded synthesis. Historical outputs keep their original contracts and flags; the application does not reclassify them automatically.

Quantified prospective effects use typed target fields even when their statement type is `projection`. A conditional 22–25% energy-intensity reduction retains both bounds, its 2010 baseline, 2035 target year and source conditions in a targets-only export; it is not reduced to an unstructured co-benefit or recast as an unconditional commitment. Support for a global objective is attributed to the country's statement without assigning the global numeric objective to that country's domestic target.

## Transparency and present status

The prototype's **Method & prompts** page shows the current Markdown source of the configured files, their paths, roles and SHA-256 fingerprints, with individual Markdown downloads and a complete catalog JSON download. It is generated from the repository files, not a manually maintained summary of the prompts.

For an executed report, archive the exact prompts, schemas, taxonomy, pipeline configuration, source snapshot and model settings used, including components from reused extraction runs. Keep run/input hashes, coverage and validation results with the release. Historical methodology must resolve to those archived bytes, never to whichever prompt happens to be current today. Hashes identify components; they do not establish factual accuracy.

**Current status:** one Generate action runs automatic document recovery, triage, translation, extraction, evidence checks, synthesis and local publication. No intermediate human review is required. Unrecoverable content is declared in the coverage contract and partial results; wholly unusable inputs and failed evidence checks do not replace a valid result. Settings can be saved, restored and rerun without editing code. Optional moderation applies after publication. Offline/synthetic checks establish software behavior, not real-country semantic accuracy. Historical runs retain their exact sources and method.

## Current execution boundary

All five optional tasks execute through the local worker and save independent history. Code applies thematic filters, selected table columns, comparison group checks and commitment-level missing-information checks. Full-document translation ignores no pages and accepts no thematic filters. Numeric calculations from model output are rejected unless supplied and verified by application code; the current path therefore presents source values and descriptive comparisons. Valid citations establish linkage, not semantic support. See the [workflow verification](../design/verification/workflow-audit.md).

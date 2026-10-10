# PolicyTracker product and methodology

> Engineering/design background. Current navigation, task controls and editable-source ownership are defined in [METHODOLOGY.md](METHODOLOGY.md), [document 14](14-lean-tools-translations-and-configuration.md) and [CUSTOMIZATION.md](CUSTOMIZATION.md). Earlier three/five-view and audience/length proposals below are historical; the current profile has Overview and Policy register.

Design proposal v0.2, 8 October 2026. Updated for automatic publication and optional audit as clarified by the user; see `08-product-decisions-and-feature-scope.md`. This specification follows the user's request. The two supplied PDFs are design references, not instructions to execute. This is a proposed operating model for UNDP regional experts, not an approved UNDP methodology.

## Recommended product

Build a country evidence library with two workspaces: **Country profiles** and **My reports**. The same versioned extraction pipeline serves both. Prime is a publication choice, not a different extraction algorithm or an extra model.

One country release contains the five-minute brief, policy register, document history, implementation information, finance and support needs, and the evidence behind them. Publish the whole bundle together. Avoid separate Prime pointers for summary, tracker, finance and comparison: they could otherwise describe different document sets.

The first deliverable is an evidence package for all 18 country entries. A country with no supplied documents receives an explicit availability entry, not invented analysis. The document manifest defines the scope; a local filename such as `Current.pdf` does not establish that the document is the latest official submission.

## Decisions

| Question | Decision and reason |
|---|---|
| One huge prompt for each feature? | No. Extract reusable evidence once, then synthesize small feature outputs from validated records and their source passages. |
| Different prompts for Prime and ad hoc? | Shared evidence rules and extraction prompts; separate synthesis prompts and source-selection rules. Prevent methodological drift. |
| What is a Prime report? | One immutable country bundle selected by a single country pointer. A successful run becomes visible automatically after automated bundle checks; manual audit is optional. |
| Automatically use the latest? | Default `latest_successful` selects the newest eligible successful run for the current corpus generation by submission sequence. An explicit pin holds a chosen release until reassigned or unpinned. Upload alone never publishes. |
| Does an ad hoc ministry document change Prime? | Never. An authorized editor must separately add an eligible official document to the curated country corpus and start a Prime candidate run. |
| Are old NDCs discarded? | No. Retain them for history and change detection; distinguish current, historical, superseded, parallel and unresolved commitments. |
| Is comparison a Prime feature? | Ad hoc comparison is a core analyst function. A regional evidence matrix is a useful later Prime companion. Do not delay the initial 18-country package for 18 separate regional narratives. |
| Can progress be inferred from NDC targets? | No. Document assertions and measured performance are separate dimensions. |
| Can a model run be called perfect? | No. Version the method, measure errors, expose uncertainty, and preserve corrections. |

## What experts need to answer

The proposed workflow supports country briefings, programme design, government discussions, finance preparation, technical assistance and peer learning. UNDP's NDC implementation lessons cover governance, finance, private sector engagement, gender, laws and implementation roadmaps; the NAP process also includes implementation and monitoring. These support a broader register than targets alone. This feature selection is our product recommendation, not an assertion that all UNDP teams use identical workflows. See `06-sources-and-reference-review.md`.

| Expert's question | Stored evidence | Useful output |
|---|---|---|
| What matters before a meeting? | Headline commitments, deadlines, conditions, risks and source dates | Five-minute brief with 5-8 cited takeaways and 3-5 questions to ask |
| What exactly was promised? | Quantitative targets and qualitative commitments | Searchable register with filters and original quotations |
| Who needs to act? | Lead/cooperating institutions and implementation arrangements | Actor and responsibility view; do not invent accountable owners |
| What support is requested? | Explicit finance, technology, capacity and data needs | Support-needs register and a separately labelled analyst follow-up list |
| What could be funded? | Measures, costs, currencies, cost years, financing gaps and conditions | Finance preparation view; a costed measure is not automatically bankable |
| What changed? | Revision relationships and comparable target variants | Previous-to-current changes with cited before/after evidence |
| What can be monitored? | Indicator definitions, baselines, milestones, reporting cadence, data sources | Monitoring readiness fields, not an unvalidated composite score |
| Are NDC and NAP aligned? | Linked objectives and measures; scope and time periods | Overlaps, explicit links, possible tensions and missing linkages |
| Who may be left out? | Gender, youth, disability, livelihoods, vulnerable groups and territorial evidence | Inclusion filter; no inferred benefit from generic wording |
| What can countries learn from one another? | Comparable policies, institutions and instruments | Cited peer examples with comparability limitations |

## Prime package and simple navigation

Use three visible tabs. They are views over one release, not three independently generated databases.

1. **Overview:** a five-minute brief; source coverage and dates; key targets; conditions and explicit support needs; most important changes; open questions. Show AI generation, automated check status and optional audit status separately; a usable unaudited report is not labelled draft solely for lacking human review. Show `no documents supplied` where applicable.
2. **Policy tracker:** one row per canonical commitment, expandable into its statement variants, dates and evidence. Default columns: topic, plain-English commitment, target/deadline, documentary status, conditionality and source. Finance, actors, indicators, beneficiaries, hazards and spatial details are advanced columns and filters.
3. **Sources and changes:** document versions, English reading view/original view, target change history, unresolved issues, release history and download.

The full report expands these views into sections: executive brief; corpus and method; mitigation; adaptation and resilience; governance/actors; finance/support; inclusion/just transition; monitoring; revisions/coherence; evidence limitations; references. Empty sections say whether information was not found, not processed or not applicable. They do not become unqualified claims that national policy is absent.

The existing screenshot's eight domains can be supported through a legacy export, but the evidence model retains Transport, Industry and Tourism as separate domains. The receiving site should add these filters or display an explicit `Other` group. Do not silently map everything to Climate.

## Meaning of policy status

Keep these independent fields:

| Dimension | Values and interpretation |
|---|---|
| Documentation status | `mentioned`, `priority_stated`, `action_proposed`, `action_committed`, `implementation_reported`, `result_reported`, `unclear` |
| Assertion kind | planned action, observation, projection, scenario, recommendation, historical description, template |
| Performance | `not_assessed`, `insufficient_evidence`, `on_track`, `off_track`, `wrong_direction`, `achieved` |
| Temporal relationship | current, historical, superseded, parallel, unresolved |
| Review state | proposed, needs_review, accepted, excluded, stale |

Performance requires a defined target, observed values and dates, comparable scope, and an explicit reproducible assessment method checked by the system. Record method provenance and optional human audit separately. The initial NDC/NAP product defaults to `not_assessed`; human approval is not a prerequisite for publishing the country report. A reported result can be adverse. A future monitoring indicator reading "developed and implemented" is not an achievement. A ministry's claim remains a source-reported assertion unless independently verified. Passage dates and data dates remain visible even in a newly generated report.

The NDC/NAP-only Prime package will generally leave performance unassessed. If operational monitoring is added later, use a separately curated monitoring-evidence collection, including BTRs or official data where appropriate. Its assessments reference the Prime commitment version without silently changing the NDC/NAP corpus rule.

## Extraction beyond targets

Capture these when present, always linked to original evidence:

- quantitative targets, qualitative commitments, interim milestones and explicit priorities;
- baseline value/year, target type, denominator, absolute/intensity/BAU basis, scenarios, sectors, gases, GWP basis and LULUCF treatment;
- conditions and exact support dependencies; separately record financing sources and expressed needs;
- responsible and supporting institutions, coordination mechanisms, legislation and policy instruments;
- implementation steps, sequencing, dependencies, barriers, constraints and stated institutional/data gaps;
- costs, currency, price year, time horizon, funding secured/requested, financing mechanisms and estimates versus approved budgets;
- indicators, reporting arrangements, monitoring cadence, evaluation provisions and evidence of implementation/results;
- climate hazards, exposure, vulnerability, locations, ecosystems, beneficiaries, gender and other inclusion provisions;
- mitigation/adaptation links, co-benefits and trade-offs only where supported;
- explicit NDC/NAP/sector-plan links, international cooperation and transboundary issues;
- uncertainty, assumptions, definitions and boundary conditions that change interpretation.

Retain a searchable source library for all pages. Structured extraction covers meaningful policy evidence; it does not create a policy record for every glossary entry, bibliography line or repeated header. Every processing segment receives a coverage disposition: extracted, relevant_no_new_records, background, duplicate, unreadable or excluded, with reason. An `unmapped_topic` queue prevents the starting taxonomy from suppressing useful new material.

## Knowledge structure

Use five primary entities: document version, source segment, evidence statement, canonical commitment, and report release. Add field evidence, translation alignments, relationships and review events as linked entities.

A **statement** is an assertion made at a particular location and time. A **commitment** groups statements referring to the same underlying promise. A **target variant** preserves quantities, scope, deadlines, baseline and conditional scenarios. Multiple source mentions can support one variant. Conditional and unconditional variants are never averaged or merged. A later NDC may revise a target while retaining the commitment relationship.

The 40 supplied topic IDs remain the starting vocabulary; the later PDF explicitly calls them a proposed corpus-informed pool, not an international standard. Store multi-label topic membership separately. Cross-cutting tags include gender, youth, disability, just transition, capacity, finance, technology, hazards and transboundary cooperation. Unknown topics are allowed. Expansion is reviewed and versioned rather than silently generated per run.

Every non-null factual field must have one or more source references. Derived calculations identify their formula and inputs; analytical recommendations identify their supporting records and are labelled inference. `null` means unresolved or not stated, with a reason field where relevant; zero is never used as a missing-value placeholder.

## Geography and document identity

The folder is an ingestion hint. Verify the reporting party, territorial scope, affected countries and whether the source is national, subnational, EU/regional or multi-country. Cyprus's EU submission can inform the Cyprus profile as EU-wide context; it must never become a Cyprus-only reduction target. Kosovo uses the local application code `XKX`; configure any country-name designation required by the host organization separately.

One upload may contain multiple instruments or languages. Classify at document and segment level. Display detected country/type/language for correction before the Prime corpus is curated. Wrong, corrupt, unrelated or unreadable files stay in a quarantine/review state and cannot become silent empty reports. A ministry document is a support document by default; official NAP annexes and action plans can join Prime when their relationship to the adopted NAP is verified. Sectoral NAPs are explicitly scoped, not promoted to whole-country plans.

Group translations using an instrument-family ID and translation relationships. Keep each file hash and provenance. Compare them for differences; an unofficial English translation cannot override conflicting original wording. Preserve the conflict, authority information and a review question. A new language edition is not automatically a new policy revision.

## Translation and audit

Deliver an English reading layer for every source segment, including tables, annexes and footnotes. English originals use an identity mapping. Machine translations are labelled as such and are not authoritative official translations. Translate with surrounding headings and table headers, consistent terminology, unchanged numbers/units and explicit uncertainty. Keep original text, segment/page identifiers, translation model/prompt versions and alignments.

Extract from original evidence, using the English layer as an aid. Source references open the original physical PDF page and show the English translation beside it. Store printed page labels separately. For tables preserve headers, row/column labels, units, notes and bounding boxes where the parser provides them. Page-level text alone is a preparation artifact, not a validated table parser. Scans need OCR and visual verification; do not call a textless page irrelevant without inspecting it.

## Comparison

Ad hoc comparison accepts any number of documents, countries or frozen report versions within explicit capacity limits. The preflight screen explains the actual grouping and flags mixed countries, translations, duplicate files, incompatible years and incomplete evidence. Large requests become staged jobs with complete coverage accounting, not truncated prompts.

Support three comparison modes: revisions within a country; NDC/NAP coherence within a country; country or document comparison across a chosen theme. Safe defaults are policy coverage, instruments, institutions, finance and monitoring arrangements. For numbers, require agreement or an explicit transformation for indicator, unit, baseline, deadline, denominator, scenario, sector/gas coverage and accounting basis. BAU reductions cannot be ranked against historical-base-year reductions just by percentage. Different adaptation indicators are usually descriptive comparisons.

A missing topic means "not found in the selected material," and longer documents must not earn a better score merely by containing more mentions. Never generate country league tables or aggregate ambition scores without an independently defined, validated method.

For the optional regional companion, freeze a vector of country release IDs. Build one matrix and a cited regional narrative, then derive each country's peer view. Updating one country makes the companion `outdated` and queues a new regional version; it does not rewrite the other 17 Prime country reports. A country-versus-region view excludes itself and explicitly lists missing or non-comparable peers.

## Ad hoc reports and chat

Offer only five initial controls: task (briefing, focused analysis, comparison, programme/monitoring preparation), sources/groups, focus topics, audience and length. An optional question box refines the task. Model, reasoning effort and payment route are shared run settings, not repeated custom feature controls. The four task templates and five Prime functions are detailed in `08-product-decisions-and-feature-scope.md`.

Chat is grounded in an explicitly selected report snapshot and authorized documents. A compact editable report brief stores user intent, filters and confirmed assumptions. Keep recent turns plus a cited conversation summary, retrieve relevant evidence, and allow access to neighboring source context. Chat memory is never source evidence. Broad "find all" requests invoke the complete extraction workflow rather than top-k retrieval alone.

Personalization changes presentation and emphasis, not source facts or published Prime records. Chat can propose a new report revision. `Save as report` creates an immutable ad hoc version; `Publish as Prime` is not a chat tool. Producing Prime from those materials requires a separate country run with the normal curated corpus and automated eligibility rules.

## Initial release acceptance

Every country entry needs a document coverage manifest, generation metadata, availability state and full report artifact or explicit no-document outcome. Every processed document needs original/English coverage accounting. Every published factual claim needs a valid locator and support. Quantitative headlines, conditions, revisions and geography receive automated consistency and evidence challenges. All parse failures and unresolved conflicts are visible. Unsupported interpretations are repaired or omitted with a disclosed limitation. A failed or unfinished job cannot replace a working Prime.

The first batch delivers usable reports that publish automatically after automated checks. Human audit is an optional later utility, never a release prerequisite. Distinguish successful processing, source completeness and optional audit. The $24 API experiment is a later, separate, explicitly bounded test; it is not the cost promise for translating and analysing the entire corpus with Astra Extra High.

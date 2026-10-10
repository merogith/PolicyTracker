# Reading, exploring and verifying policy evidence

Method 3.0 supersedes this document's original label layout. Default register columns remain Statement, Statement type, Topics and Sources. Advanced controls expose only the active profile's fields. Delivery uses an Institution filter; evidence gaps live in the inspector. Old methods retain their original field meanings, with no automatic conversion. Function/hazard co-occurrence is not an asserted relationship. See [the current method](METHODOLOGY.md).

Current presentation specification, 9 October 2026. This document supersedes older navigation, card-register, in-memory-only reader, and generic dashboard proposals. Extraction and synthesis semantics remain defined by the existing v2 prompts and schemas. No source-processing stage is added.

## Information architecture

The regional tracker leads to two Country Profile views: **Overview** and **Policy register**. **Documents & translations** and **Version history** support reading and audit. **Reports & analysis** keeps named browser-local prepared requests separate from executed results and persistent run history. Its three-step preparation flow has an explicit separate execution action. Synthetic demonstrations are labeled separately. Help, method, knowledge, configuration, AI connection and integrations are under **Guides & settings**. The regional list distinguishes source coverage and profile availability. Supported themes aggregate only saved real profiles, never synthetic examples; counts do not rank policy quality.

Understand → Explore → Verify is an information hierarchy, not three extra pages. Overview starts with saved cited findings, their qualifications, explicit priority explanations and investigation questions. The complete ten-section narrative remains available. Policy register offers a table with four perspectives. A shared evidence panel opens original/English passages, document/page locators, typed details, definitions, classification support and missing-value reasons. It returns focus and scroll to the initiating control.

Scope, version and synthetic/imported/generated status remain visible. Partial and stale-source states explain the actual limitation. Validation means structural/link checks, not certified semantic accuracy. Full-scope narrative is explicitly distinguished from filtered record summaries; no browser filter regenerates prose.

## Knowledge alignment

The current vocabulary has 11 domains, 41 topics, 24 controlled dimensions and 190 defined values, grouped into policy labels, typed details and evidence metadata. These are project categories, not official international crosswalks. The only hierarchy is **domain → topic**; topic is the subdomain level. The renderer derives domain membership from the selected profile's archived codebook. AGR-01, URB-01 and WST-03 have cross-domain mappings. No category is inferred from document type or a word match.

New records use one Statement type with nine options and one optional Risk and resilience function pool with eight options. Historical records retain the earlier dimensions under their archived codebooks. A recommendation, projection or intended deliverable is not an observed result. Climate mitigation remains distinct from disaster-impact mitigation. Population-group and cross-cutting labels do not by themselves establish benefits.

Targets, actors, finance, indicators, risk contexts and typed details remain attached to their source record. A detail with target IDs applies to those variants; an empty target-ID list applies to the enclosing record generally. It does not apply to all country commitments. Candidate metric/unit keys do not establish comparability.

Unmapped terms remain searchable. Definitions and recorded `field_support` can be inspected without reading JSON. A classification explanation is analytical interpretation supported by evidence, not necessarily the source's own terminology. Current Knowledge & labels is clearly distinguished from historical profile definitions.

## Perspective and report matrix

| Experience | Primary question and default content | Interactions and drill-down | Empty/limited state |
|---|---|---|---|
| Country Overview / Summary | What do these sources say? Cited findings, qualifications, priorities, follow-up and all ten expandable report sections | Explore matching records; open each finding's passages; domain bars | No saved findings, partial processing and section-specific states are explicit |
| Register / Summary | Which statements are present? All statement types with topics and source locators | Search original/English text; domain/topic and objective filters; sort/group; row → evidence | Zero matches means no matching extracted records, not national absence |
| Targets | What is promised, under which conditions and by when? Quantitative, deliverable and qualitative targets, plus commitments without targets | Condition/period filters match the same variant; baseline/scenario/accounting details in inspector | No target object does not remove a qualitative commitment; raw/unknown periods remain readable |
| Risks and resilience | Which stated hazards, exposure, vulnerability, capacity and disaster functions matter? Labels and risk-context objects | Hazard, optional component, risk function, purpose and population facets; source-linked action connections | No hazard label is distinct from no risk context; all-hazards evidence is not automatically climate-related |
| Delivery and support | What responsibilities, resources and monitoring are documented? Actors, six finance kinds, support, barriers, dependencies, indicators and timeframes | Institution filters and inspectable evidence gaps; commitment-only information matrix; inspect role/target links | Material gaps and processing limitations remain distinct in evidence; unexplained blanks say no extracted value |
| Evidence extraction | What does the selected evidence contain? Cited findings and complete scoped record table | Same perspectives and fields; searchable/sortable/grouped records; full evidence reader | Actual task executes, validates and saves a separate result; selected columns and no-match scope are deterministic |
| Policy comparison | How do valid source groups differ? A dimension × document-group matrix | Same thematic filter scope in all columns; cell → corresponding record/evidence | Missing extracted values remain visible; unsupported/unknown comparability excludes numerical changes |
| Implementation-information review | Which source-stated needs and information gaps need clarification? Responsibility, finance, indicator/baseline and timeframe matrix | Inspect each action and missing reasons; support proposals remain a separate optional analysis output | Empty/unreadable/unprocessed values never imply failure; demonstration fixtures remain distinct from executed analyses |
| Briefing | What answers the saved policy question? Direct answer, cited supporting findings and evidence annex | Filter/explore annex; inspect citations | Answer retains its original scope; filtering does not rewrite it; no answer without saved evidence |
| Translation | What does each page say in original and English? Stored aligned segments | Choose document/page; read bilingual text and translation status | Authorized local original-PDF and saved translation readers are connected; hosted reading is deferred; no charts or thematic translation filters |

Perspectives change presentation over shared evidence. The reader supports more facets than the optional request-builder schema. Do not silently send reader-only facets as supported generation options.

## Visualization specification

| Visual and question | Required fields / counting unit | Aggregation, denominator and missing values | Interaction / alternative |
|---|---|---|---|
| Domain bars: where is evidence classified? | `records.local_id`, `labels.topic_ids`, archived topic→domain mapping; source record | Distinct ID once per domain. Denominator = filtered record count, including unmapped records. Multi-domain buckets overlap. Missing topics are unassigned, not zero evidence. Repeated statements in different records remain separate. | Keyboard-operable bar narrows the domain and opens the register. Exact-count table and rule disclosure. |
| Hazard / risk-function bars: which source-reported categories occur? | `labels.hazards` or `labels.risk_functions` (archived profiles keep their original facets); source record | Distinct record per category; same filtered-record denominator. Multiple labels overlap. Missing labels are unassigned. No severity, national risk score or policy-importance inference. | Bar filters the same records; exact-count table; row → source evidence. |
| Stated dates: what periods are given? | Matched `targets.local_id`, `target_period`, metric, condition and parent record | One row per matching target variant; show target and source-record counts separately. Preserve raw periods, unknowns and conditions. No inferred date normalization or progress. A table is preferable to an invented chronological scale. | Table rows open full record/target evidence. Keyboard and screen-reader table semantics. |
| Implementation information: what is documented? | Commitment kind; actors/roles, finance, indicators, target periods, `missing_fields` | One row per filtered commitment source record. Other record kinds excluded from this matrix, retained in register. A named supporting actor is not a lead. Empty arrays without a missing reason mean no extracted value. No completeness score. | Text cells distinguish recorded information and missing reason. Action opens readable linked details. |
| Policy comparison: what differs? | Authorized source groups, record/evidence membership and typed fields | No summation/ranking. Show all selected groups even without extracted matches. Numerical comparison needs compatible metric, unit, basis, denominator, period, scope and condition; candidate IDs alone are insufficient. | Evidence-linked table is its own accessible alternative. Prototype comparability explanations are authored synthetic findings, not a new calculation engine. |

Every chart operates on the filtered record subset. Neither document frequency nor elapsed target dates establish implementation success/failure. Finance costs, budgets, secured/requested funding, explicitly stated gaps and financing sources remain separate. Multi-label bucket sums must not be presented as an overall total.

## Presentation state and persistence

`integrations/javascript/evidence-model.mjs` supplies the pure view contract and selectors. `report-state.js` saves presentation preferences under `policytracker.presentation.v1` in browser local storage, keyed by synthetic/country scope, country code and exact profile ID. No quotations, report bodies or credentials are stored in preferences. Storage failure degrades to tab memory with an explicit message.

The minimal named view contains `schemaVersion`, `profileId`, `codebook` versions, `perspective`, `filters`, `sort`, `group`, `columns`, visible `sections` and `name`. Named views are scoped by country, synthetic status and report type. Applying one to another version is explicit; unavailable filter IDs, unsupported columns or unsupported state are rejected. Current definitions always come from the version being read. Presentation changes never alter shared selection, evidence, methodology or model execution.

Default Overview starts with findings; exploration controls, coverage details and technical provenance are disclosures. The register keeps conditions beneath statements even without a visible target column. Search and common filters apply immediately. Advanced multi-value filters have a visible Apply action. OR within a dimension and AND across dimensions are preserved. A condition and period must match the same target; linked details do not leak from a different scenario. Saved profile tabs retain filters and session scroll positions. Browser routes carry page/country/tab/version; back/forward restores selected versions. Prepared requests use a separate `policytracker.request-drafts.v1` browser store and never represent completed reports. Dialogs preserve initiating focus and position.

Shared defaults are not editable from this browser preference control. Production per-user synchronization and shared-default permissions need a separate persistence/authorization service. A context link must carry a fixed profile/report version and presentation state, fetch using ordinary access checks, and refuse unavailable versions rather than silently show a newer one. **Copy local view link** carries the fixed version, report/example route, tab and presentation JSON. Opening the link validates those values and refuses unavailable versions; it never silently substitutes the latest profile. Clipboard failure offers a selectable link. Local preview URLs are not hosted sharing or access grants.

## Exports

- **Current view / readable HTML:** filtered records, original/English evidence annex, readable details, definitions, scope/version and limitations. Overview exports label included saved headlines as full-scope narrative, not a regenerated filtered answer.
- **Current view / CSV:** selected columns plus version, filters, counting unit, codebook versions, limitations, evidence IDs, topic definitions, missing reasons and bilingual source annex. Unicode and formula-like cell escaping are preserved.
- **Current view / evidence JSON:** selected source records with complete parent-record/variant context, linked contextual evidence, relevant source segments and archived codebook. Metadata explicitly identifies filtering; hidden siblings in complete parent records are context, not additional matching variants.
- **Full saved report / JSON:** exact loaded profile content, regardless of filters. Existing real/saved-synthetic full-register CSV remains bound to the explicit archived version endpoint. Presentation fixtures do not advertise that archive endpoint.

## Simplification and wording

| Decision | Reason |
|---|---|
| Keep Overview and Policy register | Interpretation and detailed exploration remain connected without duplicate reports |
| Combine risk, targets and delivery as perspectives | Shared evidence and filters; no extra pipeline/navigation hierarchy |
| Replace card wall and ordinary JSON inspection | Compact comparisons and readable evidence/details |
| Move methods/configuration/integrations into utilities | Reading needs less setup and fewer competing controls |
| Use “source records”, “stated date”, “source-reported observation”, “no extracted value” | Preserve counting, temporal and evidentiary meaning |
| Move evidence gaps out of policy-label controls | Preserve material uncertainty, competing values and processing coverage without annotating every irrelevant blank |
| Defer unrestricted builders, drag/drop, formula languages and performance scores | No supporting user need or evidence model |
| Defer hosted sharing and shared defaults | Local PDF access and optional execution are connected; hosted permissions remain separate work |

## Implementation boundaries and handoff

1. **P0 — Real country acceptance:** user-run country trials must check source attribution, extraction recall, table interpretation and translation quality. Interface fixtures and software tests do not establish these.
2. **Implemented locally — Version-aware reading:** explicit profile IDs resolve behind country/synthetic scope checks. The UI reads earlier checked versions and pins/unpins with optimistic selection revisions. Historical fixtures remain labeled separately.
3. **Implemented locally — Optional result adapters:** completed task schemas, comparison matrices, citations, selected fields, JSON/CSV/HTML and separate persisted history are connected. General named-view customization remains richer in the country reader than optional results.
4. **Implemented locally — Authorized document access:** version-bound original PDFs and aligned translations resolve through session-checked routes without broad static-file exposure. Inline PDF-page rendering and hosted permissions remain deferred.
5. **P2 — Shared links/preferences:** implement account/workspace authorization, per-user preferences and controlled shared defaults. Version/label mismatches must remain explicit.
6. **P2 — Large profiles:** measure real record volumes before adding virtualization or server-side querying. Current tables are client-side; no corpus-scale performance claim.

The standalone reusable tracker accepts `profile` plus optional `view`, projecting through the same pure source-record model. Legacy `data` projections remain supported and are labeled loaded records, never canonical/unique commitments. The event includes all evidence IDs and a record ID; authorization remains the host's responsibility.

Verification and representative screenshots are recorded in `design/verification/report-experience.md`. See the pre-implementation impact assessment in `design/implementation-plan.md`.

The [9 October usability review](../design/verification/usability-review.md) covers current navigation, saved drafts, actual result readers, responsive screenshots and remaining validation limits.

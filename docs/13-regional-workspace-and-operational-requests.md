# Regional delivery workspace and useful operational customization

**Historical design proposal.** Navigation and implementation-status descriptions below record an earlier design, not current capabilities. Use the [browser guide](../design/prototype/README.md), [current evidence experience](16-evidence-experience.md) and [working architecture](ARCHITECTURE.md) for maintained behavior. Do not implement older proposals as additional requirements.

> Engineering/design background. Current navigation, task controls and editable-source ownership are defined in [METHODOLOGY.md](METHODOLOGY.md), [document 14](14-lean-tools-translations-and-configuration.md) and [CUSTOMIZATION.md](CUSTOMIZATION.md). Earlier three/five-view and audience/length proposals below are historical; the current profile has Overview and Policy register.

**Latest scope/naming:** [document 00](00-mvp-deliverable.md) and the simple [methodology](METHODOLOGY.md) define one Country Profile with two core views. Documents & translations is a utility. Analysis tools are an optional second layer. “Prime” in this technical document refers to the existing internal country-release contract, not a separate user-facing product.

This revision makes the regional dashboard the product's main entry point and replaces generic audience/length customization. It supersedes the navigation/task defaults in documents 8, 10 and 11. Automatic Prime publication, optional audit, pin/unpin and separate ad hoc history remain unchanged.

## Why change the earlier form

The previous audience and length choices did not have a strong, testable effect on an operational deliverable. The form also treated a comparison like a briefing, with no grouping or comparison dimensions. Its saved setup omitted instructions, source selection and other information needed to reproduce a run. A single-country sample obscured the main regional delivery.

Use a question protocol: keep a field only when its answer changes source scope, an analysis rule, an output section/column or execution behavior. This follows [GOV.UK's guidance to justify every question](https://design-system.service.gov.uk/patterns/question-pages/). It is not a claim that this prototype has passed formal usability research. The repeated-use analyst workbench groups related controls on one page instead of copying a public-service one-question-per-page flow.

A searchable matrix is appropriate for scanning countries and accessing a specific feature; use an independent document table for source inspection. This is consistent with [Carbon's data-table guidance](https://www.carbondesignsystem.com/building-blocks/core/components/data-table/guidelines). A map can be added later if a spatial question warrants it; it is not required to navigate 18 countries.

The operational tasks prioritize implementation responsibilities, finance, monitoring and policy alignment. These are also covered by the [UNDP NDC Implementation Guide](https://climatepromise.undp.org/research-and-reports/ndc-implementation-guide). Our task selection is a design recommendation for this team, not a UNDP-prescribed software standard.

## Regional dashboard is the first deliverable's front door

Main navigation: **Regional tracker**, **Documents & translations**, with **Method & prompts** and Integrations as utilities. **Analysis tools** is a secondary workspace. The regional dashboard lists all 18 countries, source counts, two view states, and version-history links. Country, source, view and history links open their respective destinations.

Two core views use one coherent selected country release:

| View | Expert use | Processing |
|---|---|---|
| Overview | Five-minute brief and full thematic narrative, including risk/DRR and delivery | Country synthesis |
| Policy register | Targets, actions, risk context and linked delivery information, filtered by independent facets | Deterministic projection of canonical evidence |

Documents & translations supplies the cached bilingual reading layer. Risk/DRR and delivery remain visible in the narrative and register, without duplicate reports or publication pointers. The Method & prompts page exposes exact current Markdown sources and distinguishes configured methodology from executed provenance. No cross-country narrative is needed to show regional delivery status. Later comparisons may reuse selected country releases without 18 repeated full-corpus runs.

Use separate facts for source availability, feature readiness, run state, audit state and Prime selection. Ready means a verified artifact exists in the selected bundle. `not_applicable` needs a recorded reason (for example no second eligible revision); it is different from an extraction failure. A newer run in progress must not erase the selected report's ready state. Show selected release/date, automatic/pinned mode and source-update status in production. The regional response reads one atomic map of country pointers, with an ETag; feature links retain the selected release ID.

Current prototype data is honest: **18 country entries, 42 documents, zero completed Prime reports**. Kosovo has no supplied source. All other feature cells say Not run. The separately labeled illustrative report is excluded from delivery counts. Inventoried files do not establish complete national coverage, verified country scope or a completed English translation.

Production country controls belong on the country page: inspect/register a new eligible source → freeze a verified NDC/NAP snapshot → generate all Prime features with selected model settings → automatically publish after checks. The whole bundle becomes selected unless pinned. History provides open/export/pin/unpin and older editions. No feature-specific publication switches or compulsory reviewer are added. These generation/selection services are still not implemented; the prototype currently exposes the inventory and empty history honestly.

**Current supplement:** [document 14](14-lean-tools-translations-and-configuration.md) defines the independent translation task, comparison requirements and editable method workflow.

## Four analyses, plus independent translation

| Task | Real customization | Result |
|---|---|---|
| Extract evidence | Sources; sector/hazard/DRR phase; supplementary target/risk/actor/finance/indicator fields | Complete scoped evidence table plus a cited synthesis |
| Compare policies | Country/revision/NDC–NAP/custom mode; explicit groups; selected comparison dimensions | Matrix with one cell per group, citations and comparability explanations |
| Check delivery gaps | Which checks: lead, finance/capacity, indicator/baseline, deadline; optional proposals | Stated-needs and missing-information table; optional separately labeled support/indicator suggestions |
| Prepare a brief | A concrete policy question; source/topic scope; required sections; optional follow-up questions | Short question-led brief, roughly 500–700 words, with complete cited evidence annex |

The user can keep sensible defaults. Source IDs, original/English citations, country attribution, conditionality and coverage limitations are mandatory, not optional checkboxes. Model, effort and usage route are shared execution controls. No generic audience field or vague length selector remains. A source's English/original pairing does not become two policy commitments.

### What each field changes

| Control | Stored field | Enforced effect |
|---|---|---|
| Task | `task`, `output.artifact` | Selects one prompt route/schema and allowed options |
| Selected documents | `source_groups[].document_ids` | Defines exact source scope before registration/version freezing |
| Comparison mode/groups | `comparison_mode`, `source_groups` | Defines matrix columns, ordering and country/edition/type constraints |
| Sector/hazard/phase | `filters` | AND across facets, OR within a facet; relevant unclassified material remains accounted for |
| Fields/dimensions/checks | `requested_fields` | Determines table columns, thematic sections or missing-field checks |
| Policy question | `question` | Brief must answer this question; required for briefing |
| Draft proposals | `include_analyst_proposals` | Enables separated proposals only for delivery-gap task; default false |
| Follow-up questions | `requested_fields: questions` | Adds a separately typed section of grounded discussion questions |
| Additional instructions | `instructions` | Preserves explicit analytical constraints, subordinate to evidence/safety boundaries |
| Model/effort/route | `model` | Selects the actual provider capability, provenance and budget; no silent fallback |

Switching tasks drops irrelevant option fields instead of accidentally reusing them. Save the complete request and display its effective source/groups/filters before a production run. A request preview describes the expected artifact; it is not a preview of findings. The local form currently saves requests in memory and can download their JSON; no API call is made.

Comparison requires at least two non-empty groups. Country mode supports any number of selected countries. Revision mode requires one country and user-assigned earlier/later groups, then service verification of edition relationships. NDC–NAP mode requires one country and correctly assigned instrument groups. Custom mode supports any number of named groups, with every selected document assigned exactly once. The group names do not prove source authority or chronology. Server checks must use verified document metadata, never trust the UI alone.

Pending support uploads remain explicitly pending and are rejected by offline prompt compilation until registered. The prototype cannot yet run a support-only upload request because uploads are not inspected or assigned IDs. Production must accept support-only reports after registration and country/role inspection, as well as mixed policy/support documents. Using selected Prime snapshots will be added to the same source picker once actual bundles exist. The current supplied-document picker does not pretend those bundles already exist.

## LLM and data path

`config/operations/tasks.json` is the option/effect catalog. `schemas/operations/analysis-request.schema.json` is a separate versioned request contract; it does not silently modify the older v2 run-request schema. `integrations/javascript/operation-request.mjs` compiles the form and catches local scope errors. `policytracker.operations.compose_operation` validates and assembles the existing v2 evidence/labeling/task instructions plus a shared operational contract and task-specific Markdown supplement. It keeps user/source text in JSON input, records hashes and makes no model call.

Processing: authorize → register/inspect sources → resolve document versions and translation families → freeze snapshot → reuse compatible translation/extraction or process missing scope → reconcile/check → execute the selected synthesis route → validate required fields/sections and evidence → render requested table/brief/matrix → save in ad hoc history. Required source-oriented completeness checks cannot be replaced by summary retrieval. Filtering or exporting an already processed evidence table should use deterministic data operations; a new narrative, semantic gap analysis or unresolved source set may need inference.

Routes: Extract → `focused_analysis` with canonical table projection; Compare → `comparison`; Gaps → `workplan`; Brief → `briefing`. Return the v2 output schema and a deterministic artifact manifest linking request hash, effective settings, source snapshot, artifact IDs and limitations. Target/user output choices do not alter source truth or silently omit conditions.

New API contracts: `GET /v1/workspaces/{workspace_id}/regional-workspace` and `POST /v1/workspaces/{workspace_id}/analysis-requests`. The latter accepts the operational request plus a server-authorized inference connection and an Idempotency-Key header. It must reject unresolved uploads, unknown/unauthorized IDs, type/group conflicts and unavailable model settings before dispatch. The older `/runs` remains available for Prime/legacy v2 clients. No conversion may discard operational selections into a generic prompt string. Adapters must keep this typed request in the job manifest even where they use legacy internal scheduling.

The default MCP catalog now includes regional status reading. A separately disabled optional operational tool accepts the same structured options. All transports use the same authorization and compilation path. JSON definitions are not an installed plugin or deployed API.

## Release and verification boundaries

Implemented locally: inventory-backed regional matrix, all country profiles, feature navigation, document metadata library, empty Prime histories, task-dependent ad hoc controls, grouped comparison validation, saved full request inspection/download, four offline prompt routes and structured contracts. Model execution, source upload/reading service, complete English translation, real country bundles, automatic publication and persistent histories remain production work.

Tests exercise changed options, unknown sources, duplicate/unassigned groups, one-country comparison, NDC/NAP type mismatch, briefing purpose, pending uploads and unchanged Prime counts. Browser verification covers regional navigation and task setup; it does not establish analytical accuracy or full accessibility conformance. After real extraction, test that each selected option changes the resulting artifact and that all required sections/fields and evidence links exist. A parameter in a prompt alone is not proof the model obeyed it.

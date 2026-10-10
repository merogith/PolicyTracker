# Method, knowledge and customization review

## Lean method update — 9 October 2026

Method 3.0 consolidates three statement dimensions into one and two risk dimensions into one. It also separates evidence limitations from policy labels, preserves source-level counting, and adds one evidence-motivated disaster topic. Current implementation, old/new mapping and compatibility rules are in [METHODOLOGY.md](METHODOLOGY.md). Earlier review entries below describe their dated versions and do not override the new contract.

Regression coverage includes original-schema validation, immutable legacy rendering/export, incompatible saved filters, duplicate labels, cross-sector budgets, same-variant matching and field-gap misuse. Tests establish software behavior; source review and fixtures do not establish real model classification accuracy.

Earlier review, 9 October 2026. Later same-day execution changes and current limits are recorded in the [complete workflow audit](../design/verification/workflow-audit.md). This document retains earlier review findings.

Reviewed 9 October 2026 against the current code, prompts, schemas, generators, synthetic fixtures, tests and rendered interface. Keep **one Country Profile with Overview and Policy register**, supported by **Documents & translations and Version history**.

The user will run country trials later. Extra source/report AI checks and canonical merging are deferred, not prerequisites. The priority is accurate extraction, useful analysis and clear presentation through the existing pipeline; fix observed problems rather than implement every blueprint feature. The local worker exists and has synthetic-provider tests; a regional analytical batch and evidence of real-country accuracy do not. Country-worker/AI changes appeared independently in this shared workspace during the review and were preserved. This review made no model calls or external publication and did not edit original PDFs or the user's saved profile database.

## Prioritized findings

| Priority | Finding, location and consequence | Disposition |
|---|---|---|
| P1 | `engineering.py` matched numeric substrings: `20` could be accepted from `-20`, `500` from `1 500`, or `20` from `1e20`. Correct decimal normalization could still certify the wrong source value. | Fixed whole-token matching for signs, grouping and exponent boundaries. Tests retain valid negative numbers, ranges and grouped tokens. Unsupported normalization still fails explicitly. |
| P1 | `profiles.py` checked joined citations for headline/section findings but omitted follow-up questions. A valid evidence ID unrelated to the cited record could pass there. Typed details could have empty evidence, and a record could omit the contextual quote carrying a unit or condition. | Fixed follow-up joins, typed-detail evidence requirements, and record closure over contextual evidence. Nested CSV/JSON keeps those quotations. This checks links, not entailment. |
| P1 | `method_pack.py` accepted new values for dimensions interpreted by hardcoded logic. A new conditionality/status could bypass application checks after a schema rebuild. | Fixed developer-owned constraints in `schemas/method-protocol.json` for record/assertion/documentation states, conditionalities, section states and target comparators. Definitions and descriptive facets remain editable. |
| P1 | The intended 13-stage pipeline includes source and report challenges; the new `country_runs.py` worker runs neither `quality` stage. A structurally valid but incomplete or unsupported interpretation can still be saved. | Corrected Method & prompts and methodology docs to identify the implemented subset. Semantic challengers, evaluation and eligibility based on their results remain production work. |
| P2 | `profile-view.js` omitted priorities and follow-up questions, displayed citation IDs without an accessible passage, and showed topic IDs without their meanings. The full register had no filters. | Added expandable original/English/context evidence in Overview, priorities/questions, named topics and definitions, and search/sector/type/hazard/DRR filters. Source records remain distinct; exports contain the full version regardless of filters. |
| P2 | Historical label meanings were not exposed. Using today's Knowledge page to interpret yesterday's records could silently change their meaning. | `ProfileStore.profile()` now resolves a codebook from archived validation bytes. Both views/exported profile JSON identify that provenance; imports do not claim it was the generating model's method. Current codebook edits cannot change the saved definitions. |
| P2 | The browser textarea normalized CRLF to LF, so undoing a visible configuration edit still produced a changed file and different prompt bytes. | Fixed exact-byte restoration and preservation of a consistent original newline convention. Invalid JSON blocks download; a reverted edit returns to the unchanged state. |
| P2 | The synthetic one-source report marked cross-document comparison `not_found_in_scope`, contradicting its prompt. | Corrected the example generator and fixture to `not_applicable`, with a scope explanation. Existing archived examples are not rewritten. |
| P2 | “Inspect a complete request” actually showed instructions and component hashes, without source data or task settings. Older review text also said there was no worker or CSV exporter. | Renamed the inspector, retained exact Markdown assembly, and updated current documentation. The local worker and checked import/export path are distinguished from blueprints and live analytical evidence. |

Earlier safeguards remain verified: stale method packages reject before overwriting files; supported customizations survive rebuilding; comparison groups reject overlapping editions; English identity preserves original bytes; planned results cannot become implementation observations; unknown citations and missing owned-segment coverage fail. See [verification](../design/verification/method-review.md).

## Actual workflow and responsibility

The human-readable six steps describe the intended method. `config/v2/pipelines.json` is a blueprint and composer routing source, **not an executable DAG interpreter**. The local worker implements a fixed sequence in `country_runs.py`; some pipeline policy settings are therefore specifications rather than live controls.

| Stage | Inputs and instructions | Validation/output | What runs today |
|---|---|---|---|
| Register and parse | Supplied PDFs, `Source.txt`, corpus manifest; `inventory.py`; worker source snapshot | Original SHA-256, physical pages, parsed text and parser flags; frozen source bytes/segments | Inventory works. Worker uses PDF text and stops on low-text or damaged pages. No automatic OCR/table reconstruction. The older inventory cache is mutable preparation data, not an immutable run archive. |
| Triage and English | Frozen segments, shared evidence/label rules, `02-triage.md`, `03-translate.md`, JSON schemas and translation policy | Metadata proposals; one original/English row per owned segment; identity or machine translation; archived requests/results | Worker triage samples document segments. Country/instrument declarations and text-readability flags are automated checks, not independent source-authority/layout certification. Official parallel matching and language-span verification remain incomplete. `translations.py` separately writes supplied aligned reading copies. |
| Extract and label | Owned segments plus adjacent/metadata context; `04-extract.md`; taxonomy, vocabulary and label guide | Typed records, targets, evidence and segment ledger; schema, exact quote, numeric, coverage and reference checks | Worker processes chunks, namespaces local IDs and combines results. It does not certify all-field support, completeness of parsed tables, recall or semantic interpretation. |
| Reconcile | Entire extracted record/quote set; `06-reconcile.md`; compact synthesis input | Proposed groups, variants, conflicts and changes; reference checks | Worker retains all records and link proposals. Stable canonical commitments, complete grouping membership and equivalent-edition resolution remain incomplete. Counts are source-record counts. |
| Challenge source coverage | Original coverage including background/duplicates/exclusions, candidate extraction; `07-quality.md` | Intended omission/interpretation findings and bounded repair | Prompt/schema exist; worker does not call this route. Its structural repair loop is not an equivalent omission check. |
| Prepare profile | Evidence, reconciliation proposals, country scope, ten required sections; `08-prime-report.md` | Cited findings, priorities, questions and limitations; deterministic register | Worker writes Overview; application renders both views. Request-size guard stops oversized work rather than truncating it. Compact inputs omit empty fields/support pointers; every record/quote is retained, but interpretation still needs evaluation. |
| Check, save, display and export | Frozen bundle; archived schemas/codebook; `profiles.py`; optional generation receipt | Internal deterministic receipt; SQLite archive/history/shared selection; bilingual views; JSON/register CSV | Local selection respects pins and source snapshots. Report semantic challenge and external publication are not implemented. Exports use the immutable selected version; credentials and hidden reasoning are not exposed. |

Model tasks propose metadata, translations, records, links and prose. Code owns IDs, byte archives, source accounting, reference checks, transactions, selection and projections. Optional analysis and independent translation now execute through the same local worker, persist separate results, and do not alter a Country Profile. The old v1 composer, schemas and approval-based `releases.py` registry remain legacy reference code. The large storage/API/MCP packs are separate blueprints, not the local runtime.

## Methodological boundaries

- A commitment is a promise; a source-reported observation is not independent implementation verification. Expired deadlines do not prove failure. No NDC/NAP-only progress score is justified.
- `not_found_in_scope` means no evidence in processed material, `not_processed` means incomplete work, and `not_applicable` means the question does not apply. A quoted statement of absence remains a finding with its stated scope. Empty arrays/nulls are not zero or national absence.
- Original quotations, stored translations, classification interpretations, derived calculations and analyst suggestions remain distinct. The reader labels the English **segment**, because it can include more text than the original quotation.
- Targets preserve unit, comparator, baseline/denominator, date, scenario, condition and accounting scope. Preserve separate unconditional/conditional variants. “Funded by partners” does not itself establish conditionality. Numeric comparability needs matching meanings, not matching numbers or candidate unit IDs.
- Source coverage is the supplied corpus, not proof of current official national coverage. The inventory contains 42 PDFs, 2,670 pages and 18 country entries, 17 with sources. Kosovo is a no-source entry. EU documents in the Cyprus folder must not be treated as national allocations.
- Low text is a request for inspection, not absence of policy. Text-readable tables can still lose row/header/footnote relationships. Do not replace original PDFs to correct parsing; preserve the original and register a separate corrected derivative with provenance.

UNDRR distinguishes disaster-impact mitigation from the climate-policy use referring to emissions reduction, and treats disaster risk in relation to hazard, exposure, vulnerability and capacity. These support separate facets, **not certification of the tracker taxonomy**. The 11 domains, 40 topics and 27 dimensions/208 values are project choices requiring multilingual calibration. [UNDRR mitigation](https://www.undrr.org/terminology/mitigation), [UNDRR disaster risk](https://www.undrr.org/terminology/disaster-risk).

UNFCCC describes NAP planning as country-driven, participatory and attentive to vulnerable groups and ecosystems. This supports capturing planning context and inclusion; it does not prescribe these labels or interface views. Direct retrieval timed out in this review; the official indexed page and guidance summaries were checked. [UNFCCC NAP process](https://www.unfccc.int/national-adaptation-plans), [official technical guidelines](https://unfccc.int/topics/adaptation-and-resilience/resources/publications/technical-guidelines-for-the-national-adaptation-plan-process).

## Trace one example

This trace is entirely synthetic; it is **not Kazakhstan policy evidence**.

| Boundary | Trace |
|---|---|
| Original | `examples/v2/synthetic-input.json`, `s-1`: a Russian promise to install 20 flood early-warning systems by 2030 conditional on international finance. `s-meta` explicitly identifies invented national scope. |
| English | `translation.json`, `s-1`, `machine_translation`; the original remains unchanged. Metadata uses English identity. |
| Extraction | `extraction.json`, evidence `e-1` plus contextual `e-meta`; record `r-1`; target `t-1` preserves raw/decimal `20`, 2030 and financing condition. Baseline is null with `not_stated`. Institution comes from `e-2`. |
| Labels | `CLM-04` → climate; DRR objective, flood, preparedness and anticipation. `kind=commitment`, `assertion_kind=planned`, `documentation_status=action_committed`; no implementation achievement. |
| Saved profile | `demo_bundle()` passes through the same import/archive boundary; synthetic scope is excluded from country counts. The worker fixture prefixes chunk IDs (`b0:r-1`) but does not create a canonical cross-document identity. |
| Display/export | Overview expands `e-1` and linked metadata, with original/English text. Register resolves CLM-04 through the archived validation codebook. JSON includes the full bundle/receipt/codebook; CSV preserves nested targets, actors, missing values, evidence and source segments as JSON cells. CSV is not a re-import format. |

The synthetic single-document comparison section is now `not_applicable`. Further evaluation should include signed/grouped numbers, multiple conditional targets, contradictory editions, table context spanning chunks, mixed-language documents, qualitative commitments and explicit statements of absence. Stable topic IDs and many-to-many domain mappings prevent a cross-sector record from being counted twice within a filtered register; they do not deduplicate source records across editions.

## Prompt composition and provenance

`compose_v2()` assembles evidence contract → labeling rules → task Markdown. Optional `compose_operation()` appends operational contract → option supplement. The output schema is separate. Task context and source input are separate JSON; source text never becomes trusted instructions. The supplement refines task output options and cannot waive evidence or schema requirements. Maintained prompt conflicts need correction; there is no general “last sentence wins” rule.

Extraction/relabeling receive the label guide; translation receives its policy. Schemas, taxonomy, vocabulary and pipeline/task files have component hashes. The inspector is rebuilt from raw UTF-8 bytes and its displayed assembled hash matches the actual composer. It shows current instructions, not an executed source-specific packet.

The local store archives original bytes and validation context. Generated profiles additionally archive prepared packets, model responses/settings, usage/requests, attempts and step-result hashes. Imports explicitly lack verified generation provenance. Reused steps retain the original stored response, but explicit origin-run/reuse labels remain limited; `archive=1` now exports the frozen historical requests/responses and method bytes. Do not substitute the current catalog or infer deterministic model reproducibility from hashes. The method-pack before/after archive records local edits, not model execution.

## File ownership and customization

Use the [beginner guide](CUSTOMIZATION.md) for five worked changes, validation/rebuild commands, application-code boundaries and regeneration effects. Its authoritative-file table covers Markdown prompts/methodology, JSON taxonomy/vocabulary/guide/task settings, generated schemas/catalogs and runtime code. Topic CSV is an editing interchange with its fingerprint sidecar; JSON remains authoritative. Register CSV is an export only.

The five supported edits are exercised in an isolated workspace through package validation, apply, real rebuild, schemas, prompt composition and generated interface catalogs. Browser editing is a draft; download is not application. Local apply checks original fingerprints and archives before/after. Saved profiles retain archived meanings. The current worker uses conservative whole-method cache keys, so even a narrowly relevant method edit can require all stages to rerun.

## Remaining work, in recommended order

1. Keep the existing pipeline. The user will run trials later; no trial or extra AI review stage was started here. When a concrete extraction or interpretation error appears, fix its cause with the smallest useful change.
2. Comparison now uses clearer instructions in the existing reconciliation, Overview and optional comparison prompts: align the same action/metric, check relevant baseline/unit/period/scope/conditions, cite both sides and explain mismatches. Unknown basis is not agreement; different statements do not automatically imply revision, conflict or progress. No new calls, schemas or comparison engine are needed.
3. Preserve source records and proposed relationships. The register shows source titles/pages directly, all displayed record counts say source records, and potential conflicts remain proposals. Defer canonical merging and deduplicated totals unless the user requests an output that needs them.
4. Treat the audit's other gaps as limitations, not an automatic backlog. Extra review stages, richer provenance screens, selective reruns, large-scale orchestration and hosted deployment need a demonstrated problem or explicit user need before implementation.

The pre-edit snapshot is in ignored `tmp/system-review-20261009-015221/`. No initial Git commit existed; unrelated concurrent work was preserved rather than reset.

# Customize the tracker

## Five common presentation and method edits

Use the existing files below; there is no separate theme or content-management service. Refresh the browser after presentation edits. Run `python scripts/check_project.py --local-data` with Python 3.10+ and Node 24+ (`--node <executable>` if needed), and exercise affected views with `python scripts/preview_ui.py`.

| Requested change and short example | Authoritative source | Build/check | Effect |
|---|---|---|---|
| Change interface wording/help: revise a practical answer in the Help route of `render()` or a main navigation label | `design/prototype/app.js` and `index.html`; task labels in `config/operations/tasks.json`; method explanations in `config/methodology.json` | JS/HTML edits need no generation; config edits require `python scripts/method_pack.py build`; run project check and inspect wording in the browser | Presentation only for help/wording. Changing option defaults/effects affects future requests; saved requests/results keep their snapshots |
| Clarify a label: revise the definition/example of `conditionalities.explicitly_conditional`, keeping its ID | `config/v2/label-guide.json`; topic names/definitions in `config/v2/taxonomy.json`; vocabulary IDs in `config/v2/vocabulary.json` | `python scripts/method_pack.py build`, then project check and Knowledge & labels search | A display-name correction is presentation; meanings/routing rules also affect future analyses. Bump affected versions. Do not rewrite archived labels; changed interpretation needs explicit relabeling/re-extraction as appropriate |
| Change default filters/fields: select a smaller default column set or adjust the shared report layout | `integrations/javascript/evidence-model.mjs` (`defaultView`, `PERSPECTIVES`); `design/prototype/report-components.js`, `profile-view.js`, `operations-view.js`; storage behavior in `report-state.js` | No catalog build for JS-only presentation edits; run evidence/usability JS tests through the project check and inspect profile/results at all three widths | Presentation only; saved named views remain explicit. Never omit conditional qualifications, missing reasons or complete evidence from detail/export access |
| Change shared appearance: adjust body text size, spacing or mobile navigation | `design/prototype/reports.css` and the existing shell styles in `index.html` | No catalog build; project check plus browser/screenshot inspection at 1440, 1024 and 390 pixels | Presentation only; no evidence regeneration |
| Change an extraction rule or prompt: clarify treatment of an implementation period | `prompts/v2/04-extract.md`, shared contracts in `prompts/v2/`; optional task supplements in `prompts/operations/`; routing in `config/v2/pipelines.json` | Stop active country jobs; `python scripts/method_pack.py build`, then project check | Future analyses change and method fingerprints change. Existing evidence needs an explicitly started compatible new run if its meaning/scope must change; building alone does not regenerate results |

Prepared requests use browser storage key `policytracker.request-drafts.v1`; presentation preferences use `policytracker.presentation.v1`. Neither is a method source. Requests save a whitelist of task/scope/options and model identifiers, never credentials. Local storage is per browser/origin, with tab-only fallback disclosed; executed results remain in the existing local store.

## Current method: 3.0

The existing v2 folders now host the lean method. Edit `record_kinds` for supported statement-type definitions and `risk_functions` for the combined function pool. New outputs have no separate assertion/documentation fields. The guide groups policy labels, linked facts and evidence/processing metadata separately. Missing reasons remain technical metadata for compatibility, not normal policy filter options.

The `climate` ID is stable with display name Climate & disaster policy. CLM-08 adds cross-sector disaster risk and management. Update definitions/routing without renumbering existing topics. Rebuild synthetic extraction examples with `build_v2_examples.py` after contract changes, then rebuild the method assets and run the project check. The method build also refreshes the invented report fixture and its codebook after knowledge generation. `examples/v2/legacy-profile.json` is a frozen synthetic compatibility fixture; do not regenerate it from the current method.

Archive behavior and the labels-only migration limit are documented in [METHODOLOGY.md](METHODOLOGY.md). New operational requests use schema 2.0 and `risk_functions`; saved prior results keep their original requests.

## Customize a view without changing the method

Use **Customize view** in a loaded report to select columns, sort/group records, show/hide summary sections, apply independent filters, and save a named view on this browser. **Reset view** restores the presentation default. These preferences are separate from this document’s Markdown/JSON method-editing workflow and never call a model or rewrite evidence.

The browser stores versioned view preferences, scoped by country/profile and report type. Applying a named view to another version is explicit and rejects unavailable filter values. Archived report definitions remain authoritative. Advanced multi-value filters apply with AND between dimensions and OR within each dimension; target period and condition match the same variant. Saved narrative remains bound to its original scope.

Presentation layout: `design/prototype/profile-view.js`, `report-components.js`, `evidence-reader.js`, `report-results.js`, `reports.css`. Pure filtering/counting/export semantics: `integrations/javascript/evidence-model.mjs`. Contract and integration gaps: [evidence experience](16-evidence-experience.md). Rebuild changed explanatory methodology with `build_methodology.py`; rebuild dependent catalogs and the invented report fixture with `method_pack.py build`. For changes only to invented UI cases, `build_report_design_examples.py` can also run separately.


Saved local profiles now have a [persistent import, view and export workflow](ARCHITECTURE.md). Method edits affect future preparation/validation, never archived profile bytes. Imported generation prompts/model settings remain unverified.

The editable method is Markdown plus JSON. **Method & output settings** provides plain-language language/detail, focus/topics, terminology and processing controls backed by `config/automation.json`. **Save settings** persists, validates and rebuilds the existing catalogs; **Save & rerun** then executes the current country or analysis. Previous settings can be restored. **Advanced method editor → Apply method changes** applies edited prompts/taxonomies/options through the same validated package workflow. Active jobs block these writes. Historical results keep their frozen method. Download remains useful for an unfinished draft, but is no longer required to make a setting work. Saving alone makes no model call.

Use Python 3.10+ from the project environment with this project installed (`python -m pip install -e .`) and Node 24+. Follow the [repository guidelines](../AGENTS.md); the [README](../README.md#local-development) explains setup and the single offline check command. Do not rely on an older system Python/Node being suitable.

## Which file owns what?

| Edit this authoritative source | Meaning | Derived outputs: do not edit these |
|---|---|---|
| `docs/METHODOLOGY.md` | Human explanation of the current method | No automatic UI copy; UI wording belongs to the JSON below |
| `prompts/v2/*.md` | Shared evidence rules, labeling and stage instructions | Prompt catalog inside `integrations/fixtures/methodology.json` |
| `prompts/operations/*.md` | Shared optional-task rules and option supplements | Same catalog and composed optional requests |
| `config/v2/taxonomy.json` | Topic/domain IDs, names, definitions, many-to-many routing | Topic catalog, knowledge catalog, request filters and schema enums |
| `config/v2/vocabulary.json` | Independent categorical values | Schema enums and request facets |
| `config/v2/label-guide.json` | Meanings/rules for those values; domain definitions | `docs/knowledge/labeling-guide.md`, `integrations/fixtures/knowledge.json` |
| `config/operations/tasks.json` | Supported task/option labels, effects and defaults | `operation-tasks.json`, operation request schema, API/MCP request definitions |
| `config/methodology.json` | Explanatory view/stage text, report-section mapping | Regional view descriptions and methodology catalog |
| `config/v2/pipelines.json` | Prompt routing and required sections; full intended pipeline | Composer inputs and methodology catalog. The local worker uses a fixed subset; changing stage policy does not implement missing stages |
| `config/translations.json` | Full original/English policy, attached to translation composition | Not a programmable filename/cache engine: writer format changes need code |
| `scripts/build_v2_contracts.py`, `scripts/build_workspace_design.py`, `scripts/build_integration_contracts.py` | Schema and projection implementation | `schemas/v2/*.schema.json`, `schemas/operations/*.schema.json`, OpenAPI, MCP and synthetic dashboard |
| `schemas/method-protocol.json` | Developer-owned supported shapes, task constraints and dimensions | Validation only; not an editable method-pack file |
| `config/product.json`, `config/v2/tools.json`, `config/v2/exports.json`, `config/initial-run-profile.json` | Product/worker/export blueprints and requested profile | Mostly specifications, not live controls; changing them does not implement a worker/exporter |
| `data/manifests/corpus.json` | Generated supplied-file inventory | Regional inventory projection; original PDFs and `Source.txt` remain untouched |

`config/topic-pool.json`, `prompts/v1/`, top-level v1 schemas and `scripts/build_taxonomy.py` belong to the legacy path. Editing them does not change v2. Do not run the legacy generators to customize today's method. `design/prototype/*.js` owns layout, editor behavior and static interface text not represented in `config/methodology.json`.

## A safe local editing cycle

For a package downloaded from Configuration:

```powershell
python scripts/method_pack.py validate path/to/method-pack-draft.json
python scripts/method_pack.py apply path/to/method-pack-draft.json
```

Apply checks each original file fingerprint. If someone edited the repository after you exported, it rejects the stale package: export afresh and merge the intended changes. Old packages without fingerprints must also be refreshed. Before/after packages are retained in ignored `data/methods/`. Source files roll back if rebuilding fails; this is a local operation with workers stopped, not a concurrent deployment service.

For direct file edits:

```powershell
python scripts/method_pack.py build
python scripts/check_project.py --local-data
```

`build` validates the current files before rebuilding. It does not restore edited source definitions from Python defaults. Refresh the browser to load the rebuilt catalogs. A direct edit affects the next composition immediately; keep editing and rebuilding together to avoid a stale displayed catalog. Stop local country jobs before editing. A changed worker, method or source prevents an old job from resuming; start a new run. There is no hosted activation pointer yet. Increment affected configuration versions, keep existing stable IDs, and evaluate semantic changes on representative sources.

## Five worked changes

### 1. Edit a prompt

In `prompts/v2/04-extract.md`, add: “Keep the implementation period separate from the finance price year.” Run the editing cycle above. Method & prompts → Extract evidence shows the changed Markdown; **Inspect instruction assembly** shows it between the shared contracts and any optional supplement. The assembled instruction hash changes. New extraction requests use the instruction; old evidence requires a new extraction and dependent synthesis if the rule changes what was captured. Merely rebuilding the catalog does not regenerate evidence.

### 2. Add a topic

Add this illustrative entry to `config/v2/taxonomy.json` → `topics`, after checking the proposed concept does not duplicate an existing topic. Use an unused permanent ID and bump the taxonomy version.

```json
{
  "id": "WAT-06",
  "name": "Managed aquifer recharge",
  "domain_ids": ["water"],
  "definition": "Deliberate recharge of groundwater stores for later use or ecosystem support.",
  "routing_rule": "Use for explicit recharge measures, not every reference to groundwater or irrigation."
}
```

This is a customization example, not an endorsed taxonomy addition; it has not been added to the live catalog. Build regenerates schema enums, the codebook and sector/topic choices together. Adding a **domain** also needs its definition in `label-guide.json`. A new topic can be applied to existing captured passages using a new labeling version; if the old extraction omitted the concept, re-extract. Rebuild affected reports/exports under a new release. Never silently change historical classifications.

### 3. Revise a label definition

In `config/v2/label-guide.json`, find dimension `conditionalities`, option `not_stated`. Clarify its definition without changing its ID: “The selected source states no condition; this is not evidence that the target is unconditional.” Increment the guide version. Extraction/relabeling receive this guide as JSON with a fingerprint. A definition-only edit needs no vocabulary change. Adding a supported facet value, such as a hazard, needs matching entries in both `vocabulary.json` and the guide's option list, in the same order. Statement types, conditionalities, section states and target comparator IDs are fixed by `schemas/method-protocol.json`, because code interprets them. Their definitions remain editable. Adding or removing these values needs code and tests; new dimensions also need implementation. Descriptive facets such as hazards can be extended with matching guide entries.

Rebuild, inspect Knowledge & labels and compose an extraction. Re-evaluate or relabel prior records if the interpretation changed; unchanged historical releases keep their prior guide.

### 4. Change a supported task option

In `config/operations/tasks.json`, task `extract`, option `indicators`, set `default` to `true`. An effect could read: “Include source-stated indicator cadence and data sources; preserve missing reasons.” Keep option ID, task route and artifact unchanged. Rebuild. A **new** analysis form now preselects indicators; an already saved request keeps its original selection. The offline composer includes the selected option and its effect in `task_context.selected_options`. Existing requests/results are not retroactively changed. New output structures, option IDs, task types or execution constraints require implementation and tests.

### 5. Change an explanation in the interface

In `config/methodology.json`, update `views[0].description`, for example: “A short country brief with expandable evidence and limitations.” Keep `id: "brief"`. Rebuild and reload: the method reference and any view descriptions using this catalog show the revised wording. The simplified regional availability table does not repeat every view description. Saved report prose is unchanged. Step-by-step implementation notes come from `steps[].implementation`. No evidence regeneration is needed for a wording-only explanation. Changing layout, navigation, hardcoded headings or the bilingual reader needs JavaScript/CSS. Reclassifying evidence through an explanatory text edit is not supported.

## Topics in CSV

CSV editing is supported for the genuinely tabular **topic catalog only**. JSON remains authoritative for nested guides, prompts, task settings and evidence. Saved local profiles also support **register CSV export**, with nested data in JSON cells; country records cannot be imported from that CSV. See the [export commands](ARCHITECTURE.md).

```powershell
python scripts/topic_csv.py export topics.csv
# Edit in a spreadsheet and save as UTF-8 CSV, preserving the header and IDs.
python scripts/topic_csv.py import topics.csv --version 2.2.0 --output topic-draft.json
python scripts/method_pack.py validate topic-draft.json
python scripts/method_pack.py apply topic-draft.json
```

Use your actual next taxonomy version rather than reusing the example number. Columns are `id,name,domain_ids,definition,routing_rule`. Separate multiple domain IDs with `|`, e.g. `agriculture|water`. Every cell is required. The importer validates encoding, duplicates, IDs and relationships, and rejects deletion/renaming of existing IDs. `NA`, `null` and zero are literal text, not missing-value encodings. JSON-only metadata is retained. Quoted commas, newlines and Unicode round-trip. Spreadsheet formula prefixes are escaped with a reversible leading apostrophe on export; preserve text formatting when editing.

Import creates a **draft method package**, never a competing live CSV source. For retirement/renaming, use a deliberate JSON migration with aliases and historical resolution in the future runtime. No general historical-ID migration service exists yet.

Keep the generated `topics.csv.meta.json` beside the CSV. It records the exported taxonomy fingerprint so importing an older spreadsheet cannot silently overwrite later JSON edits. If the taxonomy changed, export again and merge the intended cell changes. The subsequent package apply separately checks for edits made after import.

## What requires new results?

| Change | Required new work in the local runner |
|---|---|
| Presentation wording only | Reload/re-render; evidence unchanged |
| Synthesis prompt or selected brief sections | New synthesis from compatible frozen evidence |
| Label definition/topic mapping | New labels and dependent views; extraction if useful evidence was omitted |
| Extraction instruction, source, parser or translation meaning | Reprocess affected stages, reconcile and create a new release |
| Default optional-task settings | Future requests only; saved requests are explicit snapshots |

The worker keys each reusable step by its assembled request, selected model/route and worker code. Reading requests use document-specific identity, metadata and coverage, so adding or repairing another selected document can reuse unchanged document work. Relevant settings are included in that stage's request: changing narrative detail can reuse an unchanged translation, while changing the glossary invalidates translation and dependent work. Worker code changes conservatively invalidate all steps. Automatic page recovery has its own source/page/model/recovery-settings fingerprint and preserves the producing vision request/response when reused; incomplete recovery is retried on a new run. Reruns traverse the pipeline and reuse compatible completed work; a separate relabeling command is not implemented.

Store each stage's original method, source and model provenance when reusing artifacts. A current configured prompt is never evidence that a historical run used it. See the [review and remaining production work](METHOD_REVIEW.md).

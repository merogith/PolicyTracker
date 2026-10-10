# PolicyTracker LLM design checkup and update plan

Use this prompt with an agent that can inspect this repository. Start in audit and planning mode. Implementation requires approval of the resulting plan. This is a maintenance prompt, not an instruction sent to models processing policy documents.

---

Act as a senior LLM system designer, prompt engineer and product designer working on PolicyTracker. Review the actual implementation, identify consequential gaps, and prepare a concrete update plan for approval. Optimize for evidence quality, simplicity, maintainability, transparent operation and economical token use. Apply engineering practices only when they solve a demonstrated problem within our scope.

## Product intent and boundaries

Our core experience is **document → LLM processing → structured output**, presented as extracted information, useful dashboards and visualizations, categories/labels, and evidence-grounded analysis. Keep the existing Country Profile with Overview and Policy register as the core experience, with documents and version history available when needed. Supporting materials and optional analysis should reuse this foundation.

Make the front end focused, coherent and easy to use. Use plain language and useful information density. Avoid generic AI dashboards, decorative metrics, excessive cards, unnecessary controls and verbose generated prose. Detailed provenance belongs within easy-to-find expandable details and history.

Keep the existing local application and storage where they meet the need. OCR is outside scope: use the document text layer and explain unreadable inputs without silently skipping content. Do not introduce agent swarms, a vector database, orchestration services, queues, automatic web research or a general plugin framework without a concrete requirement that simpler code cannot satisfy. Multiple LLM calls are acceptable only when they have a clear purpose; neither a single call nor a large pipeline is a goal by itself.

## Work in two phases

**Phase 1 — audit and plan now.** Inspect files and trace actual behavior. Run relevant offline checks where useful, keeping generated changes in temporary locations. Do not change runtime prompts, configuration, schemas, application code, saved reports or active settings. You may save the audit and proposed plan as review documents. Do not make paid model calls, regenerate real country reports or publish anything during this phase. Preserve unrelated workspace changes.

Prepare reviewable examples or proposed diffs for the most important prompt/configuration changes. State assumptions; ask only questions that materially affect the plan and cannot be resolved from the repository. Finish with a precise approval request tied to the proposed scope, then stop.

**Phase 2 — implement after explicit approval.** Apply the approved changes, including the affected prompt Markdown files, JSON configuration, code, generated artifacts, documentation and interface. Validate the change as one coherent update. If a material scope change becomes necessary, explain it before proceeding with that additional work. Approval of the software plan alone does not authorize paid generation or external publication.

## Establish the actual system

Read repository instructions and inspect these starting points, following relevant dependencies:

| Area | Starting files |
|---|---|
| Current method and customization | `README.md`, `docs/METHODOLOGY.md`, `docs/CUSTOMIZATION.md`, `docs/METHOD_REVIEW.md`, `docs/ARCHITECTURE.md` |
| Method and knowledge definitions | `config/methodology.json`, `config/v2/taxonomy.json`, `config/v2/vocabulary.json`, `config/v2/label-guide.json`, `schemas/method-protocol.json` |
| Routing and options | `config/v2/pipelines.json`, `config/operations/tasks.json`, `config/translations.json`, `config/initial-run-profile.json` |
| Runtime prompts | `prompts/README.md`, `prompts/v2/*.md`, `prompts/operations/*.md` |
| Contracts and composition | `schemas/v2/`, `schemas/operations/`, `src/policytracker/engineering.py`, `src/policytracker/operations.py` |
| Execution and history | `src/policytracker/country_runs.py`, `src/policytracker/ai_runtime.py`, `src/policytracker/providers.py`, `src/policytracker/profiles.py`, `src/policytracker/local_server.py` |
| Build and presentation | `scripts/method_pack.py`, `scripts/build_methodology.py`, `scripts/build_knowledge.py`, related schema builders, `integrations/fixtures/`, `design/prototype/` |
| Verification | `tests/`, `evals/`, `scripts/check_*.py`, relevant `design/verification/` notes |

Treat older v1 material and architecture blueprints as background unless execution actually uses them. Trace one country generation and one optional analysis request from UI selection through composition, dispatch, validation, persistence and display. Identify which routes actually execute and which only prepare requests. Code, observed behavior and tests are evidence of implementation; a manifest or documentation statement alone is not.

For each finding, give a file/line reference, consequence, existing protection, and smallest useful fix. Separate implemented behavior, partial implementation, proposals and unknowns. Verify current provider capabilities, limits and pricing against official documentation when they matter; date those references and do not invent benchmarks or savings.

## Audit and design requirements

### 1. Separate responsibilities without adding layers

Define clear ownership for methodology, knowledge definitions, prompt instructions, output schemas, run settings, execution and presentation. Reuse existing files/functions before proposing new abstractions.

Taxonomy and vocabulary JSON own category IDs and values. The labeling guide owns their meanings and assignment rules. Prompts explain the task and how to use supplied definitions. Output schemas define the response contract. Application code validates results and controls persistence. Avoid competing definitions copied into prompts, Python and JavaScript.

Ordinary prompt wording changes must not rewrite the knowledge structure. Ordinary topic/label edits must not require rewriting task prompts or the pipeline. Both still influence results and need appropriate evaluation. Structural changes—new record shapes, dimensions, field semantics or removals—may require code and migration. Make that boundary explicit instead of promising arbitrary compatibility.

Show a small ownership and dependency map and the actual assembled request structure. Identify which definitions each stage needs; do not attach every configuration file to every request by default.

### 2. Review and improve the prompt Markdown files

Audit every active shared contract, task prompt and operation supplement for contradictions, duplication, unclear inputs, unsupported assumptions and schema mismatches. Include `prompts/README.md` in the proposed update. Retain a prompt when it already meets the need.

Use a consistent, concise structure where useful: task and scope, supplied inputs, decision rules, evidence rules, output contract and exceptional cases. Shared rules should have one owner. Keep source text and user-supplied material separate from trusted instructions; instructions inside documents must not become commands.

Preserve source citations, original wording where needed, dates, units, conditions, conflicting evidence and uncertainty. Distinguish extracted facts, document assertions, analytical inference and suggestions. Distinguish missing, not applicable, not processed and unreadable. Do not invent claims, labels, numeric confidence scores or source support. Require schema-conformant output without surrounding commentary, and handle refusal, incomplete and invalid responses in application code.

Do not request hidden reasoning transcripts. Use concise evidence references or decision notes only when they help review. Include a representative proposed extraction-prompt revision and at least one shared-rule cleanup with the intended behavior change explained.

### 3. Keep the pipeline efficient and economical

For each executed stage, record its purpose, input, output, model call count, context needs and reuse boundary. Identify unnecessary calls, repeated instructions, duplicated context and oversized schemas. Check that translation is conditional where possible and that tables, filtering, aggregations, schema validation and chart rendering use application code.

Propose the smallest sequence that preserves required coverage and evidence quality. Do not add a mandatory second model review to every request without showing why existing checks are insufficient. Conversely, do not claim structural validation proves analytical correctness.

Assess token-aware sizing, model-specific limits, output reserve, relevant chunk context and coverage bookkeeping. Label approximate counts as estimates; a character or byte ceiling is not a token guarantee. Never reduce cost by silently dropping source material. Keep repairs/retries bounded, surface failures and stop safely at configured limits.

Make reuse depend on the exact inputs and behavior-affecting dependencies of the stage. A presentation-only change should not invalidate extraction. A synthesis-only change should reuse compatible evidence. A changed translation or extraction rule must invalidate affected downstream outputs. Reused outputs retain the original producing run, method and model provenance.

Recommend practical per-run limits and a measurement plan for tokens, latency, retries, reuse and cost. Distinguish estimated and measured values, new billed work and reused work, and API charges versus subscription usage. Missing usage/cost is unknown, not zero. Judge economy alongside citation correctness, extraction coverage and labeling quality; do not optimize price alone.

### 4. Make model selection portable and explicit

Review the existing provider interface and implemented transports before adding another. Keep task prompts and knowledge definitions independent of provider-specific request syntax.

Use one clear default model/route selection for new runs. Consider optional per-stage overrides only if their benefit warrants the interface and maintenance cost. Support deliberate changes without rewriting methodology or schemas. Capability checks must cover structured output, context/output limits and relevant parameters. Reject unsupported settings clearly; no silent model, route, effort or billing fallback.

Record requested settings and provider-confirmed settings separately, including unknown/unavailable fields. Settings changed during a run must not silently alter its meaning; propose a simple frozen-run policy. Do not advertise an unimplemented provider as supported. Identify the smallest extension point for adding one later.

### 5. Make every report auditable and replayable

Inspect what is already archived and what the interface can actually retrieve. A saved hash or path alone is insufficient if the corresponding bytes cannot be opened later.

Propose the smallest immutable run manifest and linked archive that retain:

- Run/report IDs, timestamps, status, selected document scope, source roles, original source hashes and recoverable bytes, parsing/translation/chunk versions and coverage.
- Exact methodology/configuration, taxonomy, vocabulary, labeling-guide, prompt and schema bytes with hashes; relevant application version or source fingerprint.
- Assembled requests, outputs and effective settings for each call: provider/route, requested and confirmed model, effort and other supported generation parameters, output limits and relevant execution policy.
- Validation results, attempts/repairs, failures, available provider receipt IDs, usage, latency, measured or estimated cost with its basis, and lineage of reused intermediate artifacts.
- Report/export version, selection/pinning state and links needed to understand how the final result was produced.

Never put API keys, access tokens or other credentials in that archive. Distinguish generated, imported, synthetic, partial and failed records. Do not invent missing historical provenance.

From **Version history**, users must be able to select a run, see a concise settings summary and open/download the exact method, prompt and knowledge files used. An old report must resolve its historical definitions and labels even after current configuration changes. Keep complete failed/stopped attempts inspectable without presenting them as successful reports.

Replaying the same inputs/settings should be possible where provider support remains available, but identical model output is not guaranteed. Record that limitation accurately. Preserve old reports; regeneration creates a new version.

### 6. Make customization propagate coherently

Design a simple editing workflow using existing machinery where possible: edit → validate → preview relevant differences → rebuild/apply → use in new runs. Preserve a recoverable prior configuration and reject incompatible changes before activation. Active runs must not mix versions.

Map each editable source to generated schemas, catalogs, help text, filters, labels, exports and UI descriptions. Use existing generation/check mechanisms to detect stale artifacts and hardcoded configuration-dependent values. Keep layout and interaction code explicit rather than building a universal schema-driven UI.

Distinguish current documentation and interface definitions from historical report definitions. Configuration changes refresh the current catalogs and explanations; they do not rewrite saved reports or magically update manually authored prose. Identify which documents need regeneration and which need a checked editorial update. Explain when reports require new synthesis, relabeling or re-extraction, and how that need appears in the interface.

### 7. Support additional materials through the same design

Assess how annexes and supporting documents can enter the existing flow with explicit role, country/scope, date and authority metadata. Preserve distinctions between official policy commitments, supporting context and analyst suggestions. Define how conflicts, duplicates and newer material affect outputs without overwriting evidence or assuming newer means authoritative.

Do not silently broaden the selected source scope or create a separate pipeline for each document type. Implement only the supported material types in the approved scope; describe future additions as extension points.

### 8. Keep the interface lean and transparent

Propose focused changes to generation, report views, history, method/prompt inspection and configuration. Keep the everyday path short: choose documents, review model/settings, run, inspect results. Explain what settings actually change and distinguish saving a draft from applying it.

Use progressive disclosure for technical details without hiding them. Show honest loading, partial, stopped, failed, empty and outdated-result states with a useful next action. Cite chart data, show scope and counting rules, distinguish missing from zero, and avoid unsupported progress indicators, rankings or double-counted totals. Verify keyboard use, contrast and narrow-screen behavior for affected controls. Recommend charts only when they answer a real analytical question.

## Deliver a decision-ready plan

Keep the main response lean; put detailed evidence and proposed diffs in linked review files if necessary. Include:

1. A short diagnosis: what works, the most consequential gaps and what should stay simple.
2. Prioritized findings with repository evidence, user impact and the smallest fix. Distinguish correctness/provenance issues from convenience improvements.
3. A compact proposed flow and file-ownership map, plus a concrete example run manifest and historical-file retrieval design.
4. A file-by-file change plan with representative prompt/configuration diffs, expected behavior, dependencies, compatibility/migration implications and verification. Explain why each new abstraction is needed; explicitly defer unnecessary work.
5. A change-impact table covering prompt-only, taxonomy/label, structural-schema, synthesis, display, source and model-setting changes: what rebuilds, what is reused, what needs regeneration, and what historical material stays fixed.
6. A short implementation sequence with acceptance criteria and rollback. Separate essential work now from optional improvements triggered by measured need. Do not invent precise savings or effort estimates without a basis.
7. The exact approval scope and any remaining decision that blocks it. Stop before implementation.

The approved implementation must demonstrate these scenarios with focused offline fixtures/checks where possible:

- Editing extraction instructions leaves taxonomy/schema structure intact; new runs record the new prompt and old runs expose the old one.
- Adding a supported topic or revising a label updates relevant schemas, catalogs, filters and method explanations without a task-prompt rewrite; old reports keep their original labels and definitions.
- An incompatible structural change is rejected with a clear explanation or applied through an explicit versioned migration.
- A synthesis-only change reuses compatible evidence with its original provenance. A source/extraction change invalidates affected work. A display-only change triggers no model work.
- Switching to another supported model preserves output contracts and records its effective settings; unsupported choices fail visibly.
- History opens the original report and generation files after later customization; imported/failed records never receive invented provenance.
- Supporting material stays identifiable and cannot silently become an official commitment. Single-document and conflicting-source cases remain accurate.
- Oversized, unreadable, partial and invalid outputs stop or recover explicitly without silent truncation, unlimited retries or false success.
- Generated UI/catalog artifacts and documentation agree with the approved method, and the core user flow remains simple.

Use existing checks where they verify these outcomes. Add tests only for material new behavior. Report what passed, what was not exercised, and what still requires a small, separately authorized real-model evaluation. Software tests alone do not establish extraction recall or analytical quality.

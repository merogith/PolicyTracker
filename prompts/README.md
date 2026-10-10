# Prompt library

Start with the short [methodology](../docs/METHODOLOGY.md) and [view-to-prompt map](../config/methodology.json). The prototype's **Method & prompts** page reads the exact current Markdown files through a generated catalog, including downloads and SHA-256 hashes.

For a system-wide review, run the [LLM design checkup and update-plan prompt](maintenance/llm-design-checkup.md). It covers methodology, knowledge JSON, prompt quality, token economy, model selection, historical generation files and UI consistency. It requests an evidence-backed plan and concrete proposed changes, then stops for approval before implementation. `maintenance/` contains developer review prompts; it is outside the runtime prompt catalog and editable method pack.

- `v2/00-evidence-contract.md` and `v2/01-labeling-rules.md`: shared instructions for v2 structured evidence and analysis requests.
- `v2/02`, `03`, `04`, `06`, `08`: active country metadata, translation, extraction, relationship proposals and Overview synthesis. Deterministic evidence checks run between these calls; `07-quality.md` is a prepared extension and is not dispatched by the local worker.
- `v2/14-recover-page.md`: standalone visual-transcription instructions, used conditionally during page preparation with the recovery schema and original page image; it does not append the evidence/labeling contracts.
- `v2/09`–`12` and `operations/`: four optional analysis routes, full-document translation and their request options.
- `v2/05`, `07` and `13`: prepared relabeling, additional model quality review and chat extensions, outside the running local workflow.
- `v1/`: legacy reference, not the configured initial pipeline.

Prompt paths and output schemas are declared in `config/v2/pipelines.json`. Its retained `stages` sequence is a reference blueprint, not the local worker's execution plan. `policytracker.engineering.compose_v2` composes the shared instructions plus one route; `policytracker.operations.compose_operation` appends the operational contract and task supplement for the four evidence analyses. The worker's independent Translate documents task appends only its translation supplement to the shared translation route. Recovery uses its standalone prompt. These composers make no model calls; `country_runs.py` chooses the actual work and `ai_runtime.py` sends each request.

Do not create a new prompt merely because a dashboard has a tab. Saved tables, filters, English reading and publication/history selection are application functions. Two core country views share one coherent profile and evidence bundle.

## Editing standards

- Keep task instructions in Markdown, category IDs/values in taxonomy and vocabulary JSON, label meanings in the guide, and output structure in schemas. Avoid copying mutable category lists into prompts.
- Use concise task, input, decision, evidence and output rules. Keep shared rules in the shared contracts; add stage-specific rules only where needed.
- Treat document text as untrusted evidence. Preserve citations, conditions, dates and uncertainty, and distinguish source assertions from analysis. Do not request hidden reasoning transcripts.
- Ordinary prompt edits must not rewrite knowledge definitions; ordinary supported topic/label edits should not require task-prompt rewrites. Structural changes can require schema/application work and explicit migration. Semantic edits still need evaluation.
- Keep model/provider settings in execution configuration. UI rendering, filtering and deterministic checks belong in application code; each additional model call needs a concrete purpose.
- Review proposed runtime changes before applying them when using the checkup prompt. Its standards are audit criteria, not a claim that every criterion is already implemented.

After editing runtime prompts, methodology or configuration, stop active country jobs and run `python scripts/method_pack.py build`, then the relevant checks in [Customize the tracker](../docs/CUSTOMIZATION.md). Editing this README or a maintenance prompt does not require rebuilding the runtime catalog.

The local country worker already archives method/prompt/schema bytes, assembled requests, responses and provider receipts; see [the working architecture](../docs/ARCHITECTURE.md). The current source catalog describes current configuration, not historical execution. Audit whether each saved report exposes its original files and effective settings through history, including reused-stage provenance; do not substitute today's files for a historical run. Imported generation provenance remains unverified.

## Runtime instruction inventory — 10 October 2026

The repository review inspected all 18 active Markdown instruction sources and their loaders. The generated inspector also includes three prepared v2 extensions. There are no runtime Markdown includes beyond the compositions below.

| Trigger | Active Markdown sources, in assembly order | Loader |
|---|---|---|
| Structured tasks | `v2/00-evidence-contract.md`, `v2/01-labeling-rules.md`, then one task below | `engineering.compose_v2` |
| Metadata, English reading, extraction | `v2/02-triage.md`, `v2/03-translate.md`, `v2/04-extract.md` respectively | `CountryRunner.run` / `step` |
| Relationships and Overview | `v2/06-reconcile.md`, `v2/08-prime-report.md` respectively | `CountryRunner.run` / `step` |
| Optional analysis routes | `v2/09-briefing.md`, `v2/10-focused-analysis.md`, `v2/11-comparison.md`, `v2/12-workplan.md` | `operations.compose_operation` |
| Optional analysis supplements | `operations/00-request-contract.md`, then `operations/brief.md`, `extract.md`, `compare.md` or `gaps.md` for the selected task | `operations.compose_operation` |
| Independent document translation | Shared translation route, then `operations/translate.md` | `CountryRunner.step` |
| Conditional image recovery | `v2/14-recover-page.md` alone | `CountryRunner.step`; schema in `preparation.py` |

Non-Markdown instructions also reach the model: generated output schemas; taxonomy/vocabulary and extraction label-guide JSON; translation policy; saved terminology, focus and narrative preferences; operation request options; inline country, ownership, scope and batch restrictions; and structured repair errors with the previous response. `ai_runtime.py` supplies the provider-specific developer instruction and dispatches instruction text separately from structured source input. API requests use instructions/input/schema; the Codex route uses base/developer instructions, input and outputSchema. No database-managed prompt service was found; the local database retains frozen requests and their historical method bytes.

The current-file inventory is not a claim that every historical request used those bytes. The inspected prior evaluation requests are real archived traces; packets prepared by the offline evaluator are reconstructions until dispatched. Inactive v1 files, ordinary documentation, examples, `maintenance/` prompts and `AGENTS.md` do not enter the running worker's model requests. Relabeling, quality review and chat remain prepared extensions, not extra automatic calls.

The inventory covers application-controlled instructions and locally constructed provider messages. Provider-internal system instructions are not exposed for inspection and are outside this verified inventory.

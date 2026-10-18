# The working local architecture

## Reading and prepared requests

Everyday navigation is Regional picture, Documents & translations, and Reports & analysis. Guides & settings holds secondary destinations. `app.js` maintains URL/history routes for country, tab and exact version; `report-state.js` keeps view/position state separate from evidence. Back/forward and evidence dismissal retain the selected context. Historical links refuse unavailable versions.

Selected profiles and historical reader versions have separate cache entries. Regional themes use selected published profiles; opening history cannot replace that selection. Completion refresh is keyed by run/profile identity, including a new run that finishes between polls. An open historical reader keeps its exact version until the user chooses another result.

The analysis form shows task and documents with one Generate action; optional customization and named presets retain unexecuted drafts in browser local storage (task, source IDs, options, question and model identifiers only). Storage failure falls back to tab memory with a visible notice. The existing analysis runner and SQLite store hold executed results separately. Saving or reopening a draft does not invoke a model. Read-only AI endpoints renew an expired session once; mutating/execution requests are never automatically replayed.

See [the browser guide](../design/prototype/README.md) for practical use and [the usability verification](../design/verification/usability-review.md) for tested states. The existing SQLite store adds recovery-cache and publication-flag tables on opening; no new service is introduced and archived content is not rewritten.

## Method 3.0 compatibility

New extractions use `kind` as the single statement type and `labels.risk_functions` as the combined optional function list. Existing pipeline directories and application boundaries stay in place. Operational request schema 2.0 replaces `filters.drr_phases` with `filters.risk_functions`; old requests are not silently reinterpreted or resumed under changed methods.

`engineering.validate_v2` uses the supplied archived schema when validating stored bundles and retains legacy semantic checks. `profiles.register_csv` includes old modality columns only for old records. The browser chooses function controls from each profile's archived codebook and preserves old fields in evidence exports. Saved statement/risk filters with different vocabulary versions require explicit reselection. Original source records, historical profiles, pins and source fingerprints are not migrated.

Existing method hashes already cover configuration, schemas, prompts and worker code; incompatible checkpoints require a new run. No new service, database architecture, canonical-merging mechanism or model stage was added. See [methodology](METHODOLOGY.md) for record boundaries and counting rules.

## Evidence presentation layer

The reader now uses `integrations/javascript/evidence-model.mjs` for immutable projections, filters, variant matching, counts and scoped exports. `design/prototype/profile-view.js` binds the two views; `report-components.js` provides controls/tables/visual summaries; `evidence-reader.js` renders evidence and readable typed details; `report-state.js` stores browser-local presentation preferences. The reusable dashboard accepts the same profile/view projection.

`report-results.js` and `integrations/fixtures/report-experience.json` demonstrate optional reports and exceptional states with invented evidence. `scripts/build_report_design_examples.py` rebuilds those fixtures without processing or importing any country. The preview verification uses a separate SQLite copy. No database migration, worker change, provider call or stored-profile rewrite is involved.

The country endpoint returns the selected profile or an explicitly requested historical version. JSON with `archive=1` includes frozen method and execution inputs/responses where available. Optional analyses execute and persist separately. Session-authorized PDF downloads resolve registered or archived source hashes. Evidence citations link to the archived PDF and physical page, with native-text, reviewed-transcription or automatic-recovery provenance. The explicit `inline=1` option allows browser viewing; default downloads remain attachments. A page link does not claim an exact passage highlight. Shared preferences and hosted sharing remain deferred. See [the workflow audit](../design/verification/workflow-audit.md).


Updated 10 October 2026. One Python application, one SQLite database and the existing browser interface. Start one country at a time; no batch scheduler or extra service.

```mermaid
flowchart LR
  A[Select country and documents] --> B[Read and check scope]
  B --> C[Save aligned English text]
  C --> D[Extract evidence]
  D --> E[Link duplicates and conflicts]
  E --> F[Write Overview and validate]
  F --> G[Save one Country Profile]
  G --> H[Overview and Policy register]
```

## Use the workflow

Run `python scripts/preview_ui.py` from the project root with Python 3.10+ and the project dependencies. Open the printed address, connect an AI route, then open a country and choose **Generate profile**. The button starts with saved defaults. Documents and model choices remain in Options.

Progress shows completed documents/chunks. **Stop** immediately shows that a stop was requested, disables repeat clicks and prevents new requests or a profile commit. Active requests finish and their valid responses are saved before the worker becomes stopped. Keep the server running until the stopped state appears. Another active country is named beside disabled generation controls. Requests may take several minutes. **Resume run** reuses compatible completed steps. Older manual-preparation failures offer a new automatic run. Their original errors and receipts remain archived. Closing the browser page does not stop the server worker. After a server restart, reconnect AI and resume explicitly. Credentials are never saved in checkpoints.

New runs use automatic source recovery: native extraction, an alternate Poppler parser, orientation-aware local Tesseract OCR and image transcription through the selected AI connection. Original PDFs are never rewritten. Valid older review receipts remain reusable; unapproved candidates never become human-approved receipts. Each physical page receives a source/text-hash-bound automatic record: complete, partial, nontext or unreadable. Shared numeric tokens in independent readings are checked against visual recovery, with one automatic correction pass for omissions. Remaining disagreements become explicit partial coverage. Broken or encrypted documents are listed in the coverage contract; readable documents continue, and a run with no usable evidence fails without replacing an existing result.

## Important components

Original PDFs and their `Source.txt` metadata live in `data/sources/<country>/<NDC or NAP>/<document>/`. The inventory records project-relative paths in `data/manifests/corpus.json`; the worker reads selected documents through that manifest. See the [data guide](../data/README.md) for the folder layout and update steps.

| Responsibility | File |
|---|---|
| One worker, checkpoints, bounded repair | `src/policytracker/country_runs.py` |
| ChatGPT/API connections and structured requests | `src/policytracker/ai_runtime.py` |
| Loopback HTTP, session and CSRF checks | `src/policytracker/local_server.py` |
| Immutable archive, validation, selection and exports | `src/policytracker/profiles.py` |
| Generation panel and progress | `design/prototype/generation-view.js`, `generation.css` |
| Profile views, bilingual evidence and conflict links | `design/prototype/profile-view.js` |
| Optional task scope, output validation and projection | `src/policytracker/operations.py`, `design/prototype/operations-view.js` |
| Automatic page recovery and legacy receipts | `src/policytracker/preparation.py`, `scripts/prepare_document.py` |

`data/local-profiles/workspace.sqlite3` holds byte objects, profile runs, checked profiles, country selections, country jobs, checkpoints and request attempts. It is excluded from Git and static HTTP serving. Stop the server before copying it for backup. The larger `architecture/v2/storage.sql` remains a separate blueprint.

## What is saved and checked

1. Freeze selected PDFs and method files by hash. Parse physical pages into bounded segments with original text/page references; archive the parse for resume. Low-text/damaged pages trigger automatic recovery; unresolved content carries page-specific coverage limits. Metadata triage uses a declared first/last-segment sample; uncertain or non-national attribution stops the run.
2. Prepare aligned English for every segment, supplying adjacent original segments as context without duplicating them in output. English identity preserves the original exactly. Other text is labeled machine translation. Matching valid requests are reused; the normal cache key includes assembled requests, component hashes, worker code and model settings. A new run after a worker change may also reuse triage, translation or extraction when the base request is byte-for-byte identical, model/effort and synthetic status match, original response integrity and provenance pass, and current schema and route checks accept it. Repaired extraction receipts additionally require verification of the original signature and saved request/repair chain. The old run and its method remain immutable; this does not permit resuming an incompatible run. Triage, translation and extraction receive only their own document's identity, metadata and coverage, so adding or repairing another document does not invalidate unchanged reading requests. Presentation-only settings do not invalidate unchanged translation requests. Original and English text stay together in source records.
3. Extract commitments, targets, dates, conditions, institutions, finance and risk information in chunks with adjacent context. Extraction requests omit a duplicate English field only when an identity translation exactly equals the supplied original; the complete bilingual source remains archived. Planning and dispatch use this same projection, preserving room for repair without truncating source text or increasing request limits. A schema-valid new response may have its record-level evidence lists completed from explicit references already present within each record. Only existing evidence IDs can be added; raw responses and a deterministic normalization trace are retained in receipts and exports. Check quotations, numeric tokens, labels, attribution and coverage without clearing reported issues or changing claims. Namespace model IDs by chunk to prevent collisions.
4. Propose duplicate/conflict/revision links and validate their record/evidence references. Preserve all variants and uncertainties. The register count remains a count of source records, not unique commitments.
5. Write the Overview from saved evidence and that batch's checked link proposals. Synthesis inputs omit empty fields and repeated validation pointers, retaining every record and quote. Full records remain archived. Empty merged sections retain not-processed and not-applicable states; missing processing must not become a finding of absence. Render the register directly from saved records.
6. Validate and save one immutable profile for both views. Existing selection rules preserve pins and the previous good profile on failure. JSON/CSV downloads stay bound to a specific version.

Exact prompt/schema/config bytes, assembled requests, responses, returned model/effort/usage and request attempts are archived. Each step permits up to two validation repairs. Transient connection failures retry with bounded backoff using the saved retry limit. Authentication failures stop with a reconnect action. Failed translation batches split automatically before retrying smaller batches. There is no silent model or billing-route fallback. Changed source files or methods require a new run.

One country job may run two independent extraction, reconciliation or Overview batches concurrently through the same selected account/model. Dispatch keeps at most two requests in flight; completed batches are assembled in source order. The ChatGPT connection remains exclusive to that country, including during draining, so unrelated tests and sign-in cannot overlap it. Stop or a failed batch prevents further dispatch/retries, waits for active responses to be checked and saved, then clears the worker. Request bytes, evidence checks and source coverage are unchanged by concurrency.

New automatic page-cache entries carry the producing vision step's result hash. Reuse restores that step into the new job, so its exported archive includes the original request and response. Native/reviewed pages require no model receipt. Old page-cache entries are conservatively recomputed under the updated recovery fingerprint; archived profiles and earlier receipts are unchanged.

For a country run, baseline inference requests are `D + T + E + 2S + V`: document triages, translation batches, extraction batches, reconciliation and Overview partitions, and visual-recovery requests. Translation batches own at most approximately 9,000 characters; extraction owns at most 3,000, with context supplied separately. An illustrative 100-page document at 3,000 characters/page therefore needs approximately `1 + 34 + 100 + 2S + V` requests before cache reuse, repairs and retries. Page count alone cannot predict requests or tokens. English identity still uses the translation route because document-level language lists cannot reliably detect mixed-language segments. Each logical step permits up to `3 × (retry_limit + 1)` dispatch attempts; failed translation batches may split. No monetary or token savings are inferred from the synthetic reuse tests.

Extraction acceptance uses the same checks in the worker, profile validator and bounded evaluator. It reports all structurally inspectable blocking issues, incomplete coverage and country-attribution errors together, with record and missing-evidence identifiers. Advisory extraction notes do not fail acceptance. Report validation identifies findings with missing or unrelated citations together. Repair requests retain the full error set and previous response; valid JSON is embedded structurally where its number tokens can be preserved, and insignificant input whitespace is removed. New source segments and extraction batches contain at most 3,000 owned text characters, retaining adjacent and attribution context. This limits the amount of source material that generates records: an initially small request can still produce a large response. Batches also reserve 65,000 bytes for repair inside the existing 180,000-byte ceiling. Neither heuristic guarantees output size; oversized repairs still stop before dispatch without dropping evidence. Existing archived segments are unchanged. Closed evaluation ledgers cannot be resumed or reset.

Affected countries and reporting party are separate fields. Commitments, and records with national, subnational or unknown scope, still require the selected country's attribution. Non-commitment records explicitly marked regional, EU or multi-country may retain their supported affected-country list, including an empty list for global context. The validator never substitutes the reporting country into that list. New runs do not reuse legacy extraction repairs triggered by the former blanket country-code rule; those batches are regenerated so a previously coerced geography cannot silently survive in a new profile. Their original requests, responses and archives remain unchanged.

An explicitly conditional target may have a null condition when the source does not state the dependency and an exact `missing_fields` pointer records `not_stated` with an explanation. Undeclared nulls and blank strings still fail. This preserves a known historical conditional benchmark without transferring conditions from a different target or edition. Repairs triggered by the former unconditional requirement for condition text are excluded from cross-run reuse, preserving the archived responses while requiring a fresh extraction under the corrected rule.

The missing-value check resolves the exact field against the record's schema. Alongside null, empty strings and empty lists, it recognizes `not_stated`, `unknown`, `unclear` and `unspecified` only where that schema node declares the value as an enum. These explicit absence states may carry a missing-field explanation without being mistaken for populated facts. Free-form strings with the same wording, meaningful enum values and other populated values remain subject to the existing contradiction check.

Imported profiles remain labeled imported, with generation provenance unverified. Generated profiles record request provenance. Software checks do not certify semantic accuracy, translation fidelity, PDF table layout or extraction recall.

## Deliberate limits

- **Automatic recovery has explicit limits.** Sparse/damaged text, rotation, parser errors, substantive raster content and substantial drawn table/chart structure trigger recovery. Drawn-structure detection ignores clipping, broad shading, small decorations and lone borders, but remains a heuristic with false positives and false negatives. More faithful layout coverage can increase first-run visual requests. Local tools have process timeouts; missing engines/languages or unreadable content become coverage notes. Visual recovery transcribes visible text/table structure and may not invent clipped cells or chart values. It uses Responses image input or Codex app-server image input on the selected route; credentials and billing routes are unchanged. Render and TSV bytes are archived by hash. Successful page results are reusable; incomplete pages are retried on a new run. See the [data guide](../data/README.md).
- **Bounded parsing reuse:** the worker holds at most eight parsed documents in memory, keyed by exact PDF bytes. Preflight and generation reuse that parsing; reviews are reread on every check. Editable disk text caches are not used as evidence. Page previews are bounded to 1,800 pixels on their longest edge and OCR renders to 4,000, with timeouts for local processes. These limits bound rendering, not semantic accuracy or parsing time for pathological PDFs.
- **Bounded synthesis:** requests have a 180,000-byte UTF-8 ceiling including overhead. Large evidence sets are partitioned within 65,000 bytes of compact evidence, keeping each record with its quotation context and the notes from the extraction batches that supplied its records or quotes. The complete note list stays archived; it is not repeated globally in every synthesis request. Notes without retained records or evidence travel in bounded note-only parts. Every part, including a single record, quote or note, must fit. Checked report/comparison/delivery batches are combined deterministically. Every record, quote and note is retained; cross-batch linkage and priorities are explicitly qualified. A single indivisible item or oversized repair fails explicitly rather than silently truncating or bypassing the bound.
- **Automated preparer checks:** metadata triage is sampled and layout checks are text-readability checks. The existing `metadata_verified` and `layout_checked` flags represent those automated declarations, not a human PDF audit. Inspect first real outputs, especially tables and EU/country attribution.
- **Local scope:** no regional scheduler, hosted publication, independent model quality challenge, canonical commitment registry, or automatic official-parallel translation matching. Registered optional tasks use the same resumable worker and keep their results outside the Country Profile selection.

## Publication and editable settings

Successful profiles and analyses publish in the local workspace automatically after deterministic checks. Partial source coverage is visible in results and exports. Optional **Unpublish** changes a SQLite `publication_flags` entry; archived evidence and outputs are unchanged. Republishing a profile selects it; unpublishing the current profile selects the previous published version, if one exists. Pinning unpublished profiles is rejected. No hosted publication or access-control service is introduced.

`config/automation.json` is authoritative for report language/detail, topical focus, analysis instructions, terminology, OCR languages, visual recovery and retry limits. The worker freezes it with every new run. The settings API checks a revision hash, validates, archives before/after method packages, rebuilds generated assets and rolls back source files on a failed rebuild. Settings/method/upload writes are blocked during active jobs. **Save & rerun** uses the selected documents/model or current analysis draft. Historical results retain their own method. The advanced editor applies validated method packages through the same path.

## Local endpoints and CLI

Country actions use existing same-origin sessions and CSRF protection:

`POST /api/ai/preparation` inspects registered documents, loads a page, creates a local OCR candidate, or saves a checked review. `GET /api/ai/preparation/<document-id>/<physical-page>/render` serves only a verified registered source page as PNG. Both require the existing local session; writes also require the existing CSRF token. They do not call the model or create a profile.

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/ai/settings` | GET / POST | Read/save/restore persisted settings with revision checks |
| `/api/ai/inventory` | GET | Session-authorized local availability and fingerprint check, without altering the source registry |
| `/api/ai/method` | GET / POST | Read/apply an allowlisted method package and rebuild |
| `/api/ai/documents/register` | POST | Register a PDF up to 25 MB, preserve filename/bytes, refresh inventory |
| `/api/ai/publication` | POST | Publish/unpublish a saved profile or analysis |
| `/api/ai/countries/{country}` | GET | Run states and active country |
| `/api/ai/country-runs` | POST | Start one country |
| `/api/ai/country-runs/{id}/stop` | POST | Stop after active requests finish |
| `/api/ai/country-runs/{id}/resume` | POST | Resume compatible country or analysis work |
| `/api/ai/analyses` | GET / POST | List persisted analyses / start a validated task |
| `/api/ai/analyses/{id}` | GET | Completed result; `archive=1` includes frozen method, attempts and full extraction |
| `/api/ai/translations` | GET | Saved real translation versions; no inference |
| `/api/ai/documents/{version-or-current}/{document}` | GET | Session-authorized, hash-checked original PDF |
| `/api/ai/profile-selection/{country}` | POST | Pin/unpin with selection revision and CSRF |

`GET /api/profiles` lists real selections. `GET /api/profiles/{country}` returns a profile and history. `?synthetic=1` isolates demonstrations; `?version=PROFILE_ID` reads that exact version; add `format=csv` for CSV or `archive=1` for frozen provenance. Archives include `reused_method_files` keyed by content hash when reading steps came from an earlier worker; `generation.reused_steps` links each original method path to those bytes. No arbitrary file-read or caller-supplied success-receipt endpoint exists.

The local server serves static interface files only for the expected loopback `Host`; embedded-browser navigation metadata does not block those files. API and profile reads still require the matching same-origin check, and API writes also require the session CSRF token.

Existing `profile demo`, `profile import`, `profile show`, `profile export` and `profile select` CLI commands remain available. Supplying `--id` to select pins; omitting it unpins. Use the current selection revision. Exports refuse overwrites; CSV preserves nested details and escapes formula-like text. Synthetic profiles stay outside real country counts.

CLI commands resolve their default workspace from the project location, independently of the caller's working directory; `--root` selects an explicit alternate workspace. Local pilot distributions contain the full source tree and use an editable installation; a Python wheel alone does not contain the browser, configuration or source registry. `scripts/package_local.py` builds the source ZIP without including an operator's originals, profiles or credentials. The browser reconciles registry metadata against `/api/ai/inventory` before enabling original-document actions. Missing files remain visible as registry entries; saved archived profiles and the invented sample remain readable.

See [workflow verification](../design/verification/country-generation.md), [customization](CUSTOMIZATION.md), and [AI connections](15-ai-connections.md). Dispatch follows the official [structured-output contract](https://developers.openai.com/api/docs/guides/structured-outputs) and [Codex app-server protocol](https://learn.chatgpt.com/docs/app-server).

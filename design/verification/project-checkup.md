# Project structure and local checkup

## Kazakhstan full-country acceptance — 10 October 2026 (in progress)

The follow-up root-cause audit separated throughput from downstream failure. The worker planned 100 sequential extraction calls; one accepted call produced 15,366 output tokens and took about six minutes. At 25 accepted batches, 166 accumulated notes occupied 28,116 bytes, and the synthesis planner copied them into all eight parts. A controlled replay with four times that note volume expanded the same 155 real records into 156 parts; six times the notes put every replayed reconciliation request above the 180,000-byte limit. These are scaling probes, not additional model outputs. The fix retains extraction-batch note provenance, checks every part against its size cap, and permits two independent requests under one exclusive country/account connection. The real run was safely stopped with 26 accepted extraction receipts; no complete profile has yet been published.

The next live run demonstrated overlapping requests and accepted 40 extraction batches before another controlled stop. Its attribution repairs exposed a separate contract conflict: the validator demanded the reporting country's code for every affected-country list, despite the prompt and reader treating those fields separately. In batches 26 and 35, this removed regional service countries or labeled collective global goals with Kazakhstan's code. Their prose disclaimers did not cure the structured-field error. The corrected validator retains strict national-commitment checks while permitting explicitly nonnational, non-commitment context; the cache excludes repairs made under the old coercive rule. Only those affected accepted batches need regeneration. Saved historical evidence is not rewritten. Full-country publication remains pending.

The corrected live run (`country-2a149ff807a640b28bd615ba512cf138`) regenerated both affected batches successfully. Batch 26 retains the regional centre's Kazakhstan/Kyrgyzstan/Afghanistan remit; batch 35 keeps collective global goals separate from Kazakhstan's reporting party. A separate contradictory missing-value annotation required one valid repair. Read-only cache replay verified 67 reusable reading/extraction receipts and excluded only the two coerced repairs. The complete offline check then passed with **243 Python tests and 83 JavaScript tests**, all 42 original fingerprints, 55 browser references, contracts and database integrity (`tmp/kazakhstan-project-check-attribution.log`). Those checks made no live model calls. The authorized full-country run continues; publication and the final report's citations remain to be verified.

That run preserved 49 accepted extraction batches before a further validator conflict stopped batch 45: NDC 3.0 page 26 labels the historical 289.08 benchmark a conditional NDC 2.0 target, but does not state its dependency. All three model responses correctly kept a documented null condition and refused to transfer NDC 3.0 conditions. The validator nevertheless demanded nonblank condition text. The fix accepts only an explicitly documented unknown at the exact condition pointer; it does not relax conditionality, numeric or citation checks. The remaining accepted conditional targets were checked for supported conditions. The live run also retains conflicting energy-sector percentages printed on source pages 14 and 24, which require qualification if used in the final report. Shared account quota and lengthy structured responses remain practical constraints; no full country profile has yet been published.

The following run (`country-77cf6d475c014eb79ca2014983d56a47`) accepted the historical conditional target with its documented null intact and saved 60 extraction batches before a controlled stop. Batch 57 exposed another avoidable repair: the generic missing-field validator treated the schema's literal `not_stated` enum as a populated fact. Its repair faithfully retained that enum for the 1.5 million ha restoration target and moved the explanation into a qualification; no total/additional status was invented. The corrected check recognizes explicit absence enums only at schema-authorized paths. Earlier missing-field repairs were audited and concerned genuinely populated geography, so no accepted batch requires regeneration for this correction.

The user explicitly authorized generation with the existing local ChatGPT sign-in. Both registered Kazakhstan originals were present with matching fingerprints: the updated first NDC (19 physical pages) and NDC 3.0 (93 pages). The first full run prepared all 112 pages (54 visual recoveries and 58 native pages), triaged both documents and completed 27 translation batches using `gpt-6.1-sol` at low effort through `codex_chatgpt`. No unresolved source-reading gaps were declared. This establishes saved processing coverage, not a certification of semantic accuracy.

That run stopped before extraction because duplicated English identity text exhausted the request planner's repair allowance. A separate replay then found that the local profile schema rejected the recovery receipts produced by the worker itself. Neither failure required changing source documents or archived results.

Corrections preserve the existing validation limits: extraction requests omit only an English reading layer exactly identical to the original text; planner and dispatch now account for the same settings and bytes; the local profile schema accepts strictly validated recovery receipts. New runs can revalidate byte-identical triage/translation requests from an earlier worker, retaining original request, response and method provenance. Exported archives include those original method bytes. Prompt guidance distinguishes declared upstream gaps from new defects in supplied text, and the interface acknowledges Stop immediately and explains another active country's generation lock.

Regression checks reproduce the extraction size failure, carry a vision recovery through publication and cached rerun, verify strict reuse boundaries, and detect damaged reused provenance. Read-only replay preserved all 127 Kazakhstan segments across 100 extraction batches, with the largest initial packet plus repair reserve below 180,000 bytes. Full-country publication and semantic spotchecks remain pending while the repaired live run proceeds.

The full offline check passed after these fixes: **218 Python tests, 83 JavaScript tests, all 42 original PDF fingerprints, 55 browser asset references, contracts and read-only local database integrity**. Command: `python scripts/check_project.py --local-data --node <Node 24 executable>`; log: `tmp/kazakhstan-project-check-final.log`. It made no model calls. The live run uses the separate authorized ChatGPT connection.

The continuing live run exposed repeated mechanical omissions from record-level evidence lists, despite the missing IDs already appearing in those records' label-support references. A narrow normalization now completes only those explicit references in new responses, records each addition and source path, and retains raw model responses. Unknown IDs, invalid quotes, other acceptance failures and self-reported blocking issues remain blocking. All 18 accepted outputs were unchanged in replay; five otherwise valid rejected responses passed after the mechanical fix, while one with a reported unresolved issue still failed. A new-run cache probe verified the original signatures, request/repair chains and current acceptance of all 47 reading/extraction receipts without modifying the database. The repeated full offline check passed with **225 Python tests and 83 JavaScript tests**, source fingerprints, database integrity and all project contracts (`tmp/kazakhstan-project-check-closure.log`). Final live publication remains pending.

## Port 8765 runtime repair — 10 October 2026

The user's existing `http://127.0.0.1:8765/` instance was not the isolated preview used by the release review. It was an older Python process: `/api/ai/inventory` returned 404 while current JavaScript was served from disk, and its inherited execution restrictions prevented the local ChatGPT connection. All 42 original PDFs were already present and matched their recorded hashes. The previous release verification did not establish readiness of this particular running process.

After verifying there was no active country job, that specific listener was replaced with the current project server through an approved normal-permission launch, still bound only to `127.0.0.1:8765` and using the existing workspace/database. The inventory now returns **42/42 available**, and the existing local ChatGPT account connected in the test browser session. A single explicit operational connection test completed on **gpt-6-astra / xhigh**, returning **"Connection successful."**, with 12,232 input tokens, 7 output tokens and 3.6 seconds reported by the app. This was a live connection operation, separate from offline software checks; it did not generate a country profile or establish full-country analytical quality.

The frontend was also corrected: failed/incomplete inventory checks display **availability unknown** with registered counts, rather than claiming files are missing. Unknown sources remain ineligible for generation; a successful retry restores verified document selections. Country lists, source filters, the generation panel and retry behavior are covered by regressions. All **81 JavaScript tests** passed, as did checks of 42 original fingerprints, 55 local web references and read-only database integrity. Logs and screenshots are under `tmp/runtime-repair/`. Browser connections are session-specific; another browser must reconnect its local ChatGPT account after the restart.

## Local pilot release review — 10 October 2026

**Ready for a controlled local pilot, with live provider and analytical acceptance still outstanding.** The requested first release is installed and run separately by each tester. This review fixed reproducible workflow and distribution defects, exercised the browser, installed an extracted package into a separate Python environment and ran the complete offline checks. It did not deploy a website, contact testers, change credentials, invoke a live model or generate a real country profile. No claim is made that all possible bugs or extraction errors have been eliminated.

### Issues fixed in this review

| Finding | Result |
|---|---|
| The bundled registry advertised 42 downloadable/generatable PDFs on a fresh installation with none installed | A session-authorized inventory endpoint verifies local files and fingerprints. The UI distinguishes registered metadata from installed originals; unavailable sources cannot enter new requests. Archived profiles remain readable. |
| Uploading the exact bytes of a missing registered original returned "already registered" without restoring it | The upload restores the original path, filename and stable ID, preserves existing source metadata and rejects changed existing bytes. Adding another PDF preserves registry entries for originals not installed yet. |
| A later failure in a multi-file upload hid earlier successful registrations | The document list refreshes after partial success; selected successful uploads survive and duplicate submissions are guarded. |
| Running, stopped and failed analyses appeared beneath unpublished-result moderation | Only completed unpublished outputs use that section; active progress and resume actions stay visible. |
| Model-local IDs could collide with source-segment or taxonomy IDs | Chunk namespacing now changes only local-reference fields, preserving external identifiers and quotation text. |
| An optional report priority could cite another commitment's evidence | Its evidence must belong to the selected commitment, matching country-profile validation. |
| Some offered GPT-4o requests exceeded the model output limit or used an incompatible snapshot | Structured output uses the 16,384-token family limit and excludes the May 2024 snapshot. No route fallback was introduced. |
| Analysis HTML downloads retained session-only PDF links, and CSV formula protection missed leading whitespace | Standalone exports preserve page/version/evidence information without unusable local links; spreadsheet-triggering strings are escaped consistently. |
| CLI defaults followed the caller's directory | The default root now resolves from the project; explicit `--root` remains available. |
| Old Python or missing dependencies produced confusing startup traces | The preview now explains the required interpreter and exact environment/install commands before importing the server. |
| No safe, repeatable local distribution artifact existed | `scripts/package_local.py` creates an exclusive source ZIP from an allowlist, omits local/private data and rejects symlinks and Windows junctions before traversal. Setup, testing, feedback and upgrade instructions are in the root README. |

### Verification completed

- Full `scripts/check_project.py --local-data --node <Node 24 executable>` passed: **205 Python tests and 79 JavaScript tests**, all six contract/method/fixture checks, 55 local web references, SHA-256 checks for all 42 PDFs and read-only SQLite integrity/reference checks. The source package received three further packaging regression passes after the final junction hardening; one is the additional Windows-junction case. Log: `tmp/release-readiness/final-check.log`; packaging log: `tmp/release-readiness/package-tests.log`.
- Clean editable installation of an extracted source ZIP passed in a separate Python 3.12 environment, with `pip check` reporting no broken requirements. Its resolved dependencies included pypdf 6.20.0 and jsonschema 4.26.0. All **27 AI/HTTP tests** passed there as well; its preview launched and rendered in the browser. Python's installer required ordinary process permissions because the coding sandbox blocked temporary install files. This was an installation-environment restriction, not an application failure. Logs: `tmp/release-readiness/install.log` and `clean-install-http.log`.
- Browser checks passed for the available-source workspace, a source-free extracted package, disabled missing-source choices, sample Overview/register, search and clear filters, conditional qualifiers, bilingual record evidence and saved document pages, back/forward routes, settings/method pages and disconnected AI guidance. A blank invented PDF uploaded into the disposable extracted workspace, appeared selected, and left all 42 missing registry entries intact. No original document was uploaded or modified in this test.
- A real browser HTML download retained the selected four-record scope, original/English evidence, version and qualifications, and omitted local session PDF links. The automated check is recorded in `tmp/release-readiness/download-check.json`.
- Phone (390 px), tablet (768 px) and desktop layouts were exercised; phone navigation and register controls worked, and no document-wide horizontal overflow appeared at the two constrained widths. No browser error/warning logs were observed in these journeys. Screenshots are local scratch evidence in `tmp/release-readiness/`, excluded from the distribution.
- All **730 preexisting protected files** under originals, derived evidence and saved local profiles matched their baseline hashes after verification. Receipt: `tmp/release-readiness/preservation-final.json`. No authoritative configuration or prompt changed, so no method rebuild or historical migration was required.

### Pilot handoff and remaining acceptance

Use the source ZIP and the [first-pilot instructions](../../README.md#first-local-pilot). It deliberately contains no original PDFs, saved real profiles or credentials. Users can explore the invented sample immediately after installation, then supply their documents and their own AI connection. Run the server from a normal terminal for provider access; the audit previews inherited coding-environment restrictions.

Before relying on real findings, a tester or operator must explicitly run a small real scope on the chosen connection and inspect its numbers, conditions, translations, source attribution and coverage against the PDFs. Then exercise full-country generation, stop/resume and optional tasks on representative documents. The prior bounded live evaluation below remains historical evidence; it does not certify the current release or a complete country run. Mac/Linux installation, additional browsers, screen-reader user testing, long-running provider interruptions and full-corpus semantic accuracy were not established by this review. These are pilot acceptance items, not claims of completed testing. Hosted access and multiple shared operators remain outside the chosen local pilot.

## Pipeline checkup — 10 October 2026

The implementation and offline verification below improve the existing one-button worker. **The latest authorized five-page live evaluation completed all 11 stages and passed its critical acceptance criteria with one minor classification qualification.** This is bounded sample evidence, not verification of a complete country run or general extraction accuracy. Guidance changes made after the frozen run have not been live-retested. The earlier 9 October checkup is retained below as historical evidence.

### Actual workflow and retained design

Generate freezes the selected PDF bytes, method and settings, then uses the existing local worker for page preparation/recovery, document metadata triage, aligned English translation, labeled extraction, relationship proposals, Overview, deterministic validation and one saved immutable profile. The register is projected from those saved records; ordinary navigation and filters make no model requests. Optional analyses remain separate from Country Profile selection.

The local SQLite checkpoints, bounded requests/repairs, exact quotation and attribution checks, immutable archives, stable source IDs and optional publication/pinning controls were retained. The knowledge structure already represents actions, targets, risks, actors, finance, conditions and implementation information; this audit found concrete input, instruction and display faults rather than evidence that replacing its taxonomy would help. No taxonomy IDs or historical records were migrated. A record count remains a count of source records, not a deduplicated count of national policies. Reconciliation preserves occurrences and proposes relationships; it does not erase them.

Existing moderation is profile/analysis publication and profile selection/pinning. Per-finding editing, hiding and review workflows were not found in the active implementation and were not added as speculative infrastructure. Existing saved decisions and evidence remain unchanged.

For a new country run, baseline requests are `D + T + E + 2S + V`: document triages, translation batches, extraction batches, two calls per synthesis partition, and visual page recovery. Repairs, transport retries and translation splits can add requests; valid saved requests can eliminate them. The [architecture guide](../../docs/ARCHITECTURE.md) gives the explicit 100-page estimate and limits. Synthetic cache tests establish reuse behavior, not measured token or monetary savings.

### Problems fixed

| Observed problem | Implemented behavior | Main files |
|---|---|---|
| Selectable text concealed drawn charts and table structure; alternate parsing could overstate recovery | Substantial painted linework now triggers whole-page recovery. Clipping, broad shading, small decoration and lone borders are excluded. Rotation, graphics-inspection failure and structural concerns remain partial without successful visual recovery. Automatic OCR considers all installed text language packs. | `src/policytracker/preparation.py` |
| Adding or repairing another document invalidated unchanged reading requests | Triage, translation and extraction use stable document-specific source groups, metadata and coverage. Neighbor text is supplied to translation without duplicating owned output; reordering remains harmless. | `src/policytracker/country_runs.py` |
| A reused visual recovery lacked its producing response in a new job's archive | New recovery cache entries include a verified producing-step receipt; reuse restores request/response provenance. Old cached recoveries are recomputed conservatively; old archives are untouched. | `src/policytracker/country_runs.py` |
| Checked reconciliation proposals were omitted from Overview input | Each Overview now receives its own synthesis batch's checked proposals and full evidence. | `src/policytracker/country_runs.py` |
| Combining reports could turn unprocessed sections into absence or retain a false complete status | Empty-section states and conservative partial availability survive merging. | `src/policytracker/country_runs.py` |
| Extraction instructions/schema offered duplicate/skip coverage states rejected by acceptance | Substantive repeated evidence must be extracted with source occurrences; background/unreadable states remain explicit. Authoritative contracts and generated artifacts agree; archived schemas remain supported. | `prompts/v2/04-extract.md`, `scripts/build_v2_contracts.py`, generated extraction schema |
| Current, historical and newly generated profiles could overwrite the same browser cache identity | Separate current-selection and exact-version caches preserve historical reading, regional selection and newly saved results. Polling retries failed refreshes and recognizes each completed run. | `design/prototype/app.js`, `report-state.js`, `generation-view.js` |
| Evidence inspection did not directly open the saved original page or explain transcription provenance | Bilingual readers link the exact saved PDF version and physical page, with native/reviewed/automatic preparation notes. No fabricated passage coordinates are claimed. Default downloads and source/session checks remain intact. | `design/prototype/evidence-reader.js`, `profile-view.js`, `src/policytracker/local_server.py` |
| Final review found stale history at an unchanged selection revision and unusable PDF links in downloaded HTML | Fresh history/publication metadata is retained independently of profile content; a newly discovered selection prompts a refetch. Downloaded HTML retains evidence, provenance and version details and directs readers to the tracker for original PDFs, without broken local API links. In-app PDF page links remain available. | `design/prototype/report-state.js`, `evidence-reader.js`, `profile-view.js` |
| Generated methodology described inactive stages or the wrong instruction assembly | Catalogs and the browser method reader now reflect active runtime loading, including the standalone recovery prompt and independent translation supplement. | `config/v2/pipelines.json`, `scripts/build_methodology.py`, `design/prototype/methodology-view.js` |
| A post-live label clarification exposed a stale synthetic report codebook after method rebuilding | The method build now regenerates the invented report fixture after the knowledge catalog, keeping its definitions current without modifying saved country profiles. | `scripts/method_pack.py`, generated `integrations/fixtures/report-experience.json` |

The [runtime instruction inventory](../../prompts/README.md) identifies all 18 active Markdown sources and their loaders; three additional v2 prompts are prepared/reference-only. Shared prompts, operation supplements, inline/repair instructions, schemas, vocabularies, label guidance and settings were traced. The generated method catalog matches 21 source files byte-for-byte. No database-managed application prompt store was found. Stored live requests and responses are actual execution traces; offline request preparation alone is not evidence of execution. Project/agent instructions and older proposals are distinct from runtime prompts.

### Preparation and evidence assessment

All 42 originals and 2,670 physical pages were accounted for in the read-only preparation audit. Existing routing flagged 429 pages; the new drawn-structure signal adds **1,176**, producing 1,605 recovery candidates. This is a significant potential increase in first-run model work, not a cost-saving claim. The audit found 549 pages with substantial Cyrillic text. Representative originals included the Belarus outlined-label chart, Moldova's wide costs/responsibility table, Armenia/Montenegro tables and Uzbekistan's Russian prose/chart page. Shaded prose and ordinary link underlines were checked as negative examples; a decorated Albanian cover remains a conservative false positive.

Local OCR probes were scratch candidates, not approved transcriptions or semantic acceptance. Tesseract English/Russian and page rendering were available; `pdftotext` was absent. Native reading order, borderless tables, small figures, plausible bad OCR and the fidelity of model visual recovery remain limits. Full-corpus page routing does not establish full-document extraction recall. No new human review receipts or real Country Profiles were created.

Targeted regressions cover source-qualified repeats, contextual/conditional citations, bilingual provenance, report version consistency, cache reuse after selection changes and partial-coverage reporting. Archived failed live responses still fail the current evidence-link/citation checks; acceptance was not weakened to make them pass.

### Offline verification and preservation

- `scripts/method_pack.py build` regenerated schemas, method catalogs and integration fixtures from authoritative sources.
- The final `scripts/check_project.py --local-data --node <Node 24 executable>` passed with exit code 0: **192 Python tests and 74 JavaScript tests**, local source hashes, read-only database integrity, contracts, methodology, UI references and HTTP checks. Log: `tmp/pipeline-checkup/check-project-final-clean.log`. This includes the post-closure guidance, final UI corrections and method-build fix; it made no live model calls.
- Final preparation regressions: 23 passed. The mixed-report availability regression passed after the final merge correction. The final evaluator suite passed all 14 tests, including document-specific request context, immutable budgets and rejection of incompatible archived preparation.
- An initial final-check attempt passed all 191 Python and 74 JavaScript tests but rejected the stale invented report fixture after the label clarification. The method build now refreshes that fixture; all six method-customization tests passed, including an actual isolated rebuild that verifies the new definition and preservation of saved data. The subsequent clean broad check above passed.
- UI HTTP/archive checks and focused UI-code tests passed; all seven generation-view tests passed after the final recovery-label edit. The isolated synthetic preview was started with `scripts/preview_ui.py` on port 8771. A visual walkthrough could not be completed: the browser bridge exposed no browser, and native Chrome inspection ended with `Computer Use app approval timed out`. No user tab was changed. This remains a visual-verification limitation, not a browser pass.
- Final preservation check: all **490 preexisting protected files** matched their pre-change SHA-256 values, including source documents, saved profiles and historical evaluations. All 40 frozen live-method files, reviewed outputs and review receipts also remain unchanged. Baseline and verification manifests are in `tmp/pipeline-checkup/`; the final receipt is `preservation-final.json`.

### Bounded live result and limits

The explicitly authorized [five-page evaluation](../../evals/workflow-live-evaluation.md) is closed with status **`closed_passed_with_qualifications`**. Its immutable ledger is `data/derived/evaluations/workflow-audit/pipeline-checkup-2026-10-10-v2`; the [execution summary](../../data/derived/evaluations/workflow-audit/pipeline-checkup-2026-10-10-v2/execution-summary.json), [mechanical review](../../data/derived/evaluations/workflow-audit/pipeline-checkup-2026-10-10-v2/mechanical-review.json) and [semantic review](../../data/derived/evaluations/workflow-audit/pipeline-checkup-2026-10-10-v2/semantic-review.json) record the result. The user approved this exact run separately, as recorded in `authorization.json`. The closed ledger cannot be resumed and its unused request slot grants no further inference authority. The earlier `remediated-v3` failure remains preserved and closed.

| Measure | Recorded result |
|---|---|
| Scope | Earlier NDC physical pages 1–2 of 8; later NDC pages 1–3 of 25; supplied original-text samples |
| Stages and requests | All 11 logical stages completed: two triages, two translations, five extraction batches, reconciliation and Overview; 13 requests including two repairs, within the 14-request ceiling |
| Selected route/model | `codex_chatgpt`, `gpt-6-astra`, `xhigh`; all returned selections matched |
| Usage and provider time | 432,396 input + 150,375 output = **582,771 tokens**; **3,593.392 provider seconds**, approximately 59.9 minutes; no monetary-cost or savings estimate |
| Largest dispatched packet | 175,891 bytes, below the 180,000-byte ceiling |
| Critical semantic acceptance | All **7 of 7 expected evidence rows** recovered; no observed critical numerical, condition, baseline, translation or substantive citation defects in accepted outputs |
| Quotations and output | **51 of 51 exact quotation references**, representing 41 distinct segment/quotation pairs; 22 source records and 20 targets with repetitions/contextual overlap; Overview with 10 sections and 32 cited findings |
| Preservation through closure | All 40 frozen method-file hashes verified; method unchanged through execution/closure; all 490 preexisting protected files unchanged |

The two rejected drafts were repaired within the existing limits. Extraction initially marked a populated recurring target period as `not_stated`; its repair preserved the recurrence and described the unknown starting/next date without the contradictory missing-value marker. Reconciliation initially asserted before/after changes without verified edition order; its repair retained descriptive relationships and unresolved metadata without those change claims. The accepted Overview remained explicitly partial and confined its gap statements to the assessed samples.

One minor classification error remains in the immutable accepted output: `outputs/2-extract-2.json`, record `r04`, detail `d10` uses `implementation_step` for supported accounting/baseline information that states no implementation step. The information is factually supported; that detail kind is inappropriate. The accepted Overview did not propagate it as an unsupported action or delivery claim. After closure, extraction missing-value guidance, the `implementation_step` definition (label guide 3.0.1) and reconciliation date-order guidance were clarified separately and generated outputs rebuilt. These guidance edits passed the final offline check but **have not been live-retested**; neither the accepted outputs nor their frozen method are rewritten.

The semantic review is Codex-assisted inspection of saved text and accepted outputs, not independent human expert certification or a statistical accuracy estimate. Exact substring checks separately establish quotation resolution, not semantic support by themselves. The 22 records and 20 targets are source occurrences, not unique commitments or policy-strength measures. No model-cost improvement was measured; the additional 1,176 preparation candidates above can substantially increase full-run visual-recovery work.

This evaluation excluded original-page visual review, OCR/image recovery, plotted graph values, whole-document/page accounting, Country Profile storage/publication, the real workspace database and optional analysis tasks. The normal worker would partition this accepted sample into two synthesis batches; the approved evaluator deliberately used one reconciliation and one Overview across both documents. Its success therefore does not establish identical worker execution, full-document or whole-country recall, complete one-button operation, or the quality of guidance changed after closure. The browser walkthrough limitation recorded above also remains unresolved.

### Historical checkup — 9 October 2026

Verified 9 October 2026 against the working project. These are software and local-data checks; they do not certify policy extraction or translation quality.

## Repeat the check

Use the project environment and Node 24+:

```powershell
.\.venv\Scripts\python scripts/check_project.py --local-data
```

On this workstation, the system Node is older. The successful run used the bundled Node executable:

```powershell
$checkNode = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
.\.venv\Scripts\python scripts/check_project.py --local-data --node $checkNode
```

The local `.venv` uses Python 3.12.14 with the project installed in editable mode. Dependencies include pypdf 6.20.0 and jsonschema 4.26.0; `pip check` passed. JavaScript checks used Node 24.19.0. No packages or tooling were added to the application's declared dependencies.

## Results

| Check | Result |
|---|---|
| Combined check command | Passed; exit code 0 |
| Python suite | 98 tests passed |
| JavaScript suite | 44 tests passed |
| Contracts | Legacy/v2 schemas, prompt routes, pipeline stages, integration contracts, operational requests and methodology catalog passed |
| Browser file paths | 44 local HTML assets, module imports and literal JSON loads resolved |
| Source collection | 42 PDFs / 2,670 pages; all manifest paths and file hashes matched |
| Original-file preservation | All 102 PDFs and metadata files matched the fingerprints saved before the move; original folders retained |
| Parsing cache | All 2,670 cached page-text hashes and their 42 source-version hashes verified |
| Database | SQLite integrity and foreign-key checks passed, using a read-only connection |
| Local HTTP | UI assets/catalogs served with their original bytes; private sources, database and code paths remained inaccessible |
| Saved outputs | Existing synthetic profile JSON and version-bound CSV export worked; real-country empty states returned normally |
| Browser walkthrough | Regional/country navigation, source details, generation setup, missing-source state, prompt reader, knowledge/configuration pages, report evidence reader and AI setup opened; no browser errors observed |
| Codex startup | Initialization, existing-account availability and model catalog succeeded after relaunching the preview with normal user access |

The complete local command output is in ignored `tmp/checkup-full.log`. Initial report-view failures occurred while another chat was replacing the UI; the combined command above passed against the updated files. Rerun it after subsequent changes.

## Fixes and future working rules

- `AGENTS.md` records the small-project structure, authoritative files, path rules and editing/checking cycle. `README.md` and `data/README.md` provide the human entry points.
- Inventory scans use their actual date and preserve existing parse statistics only for unchanged PDF bytes. New or changed sources still need extraction.
- The regional projection checker compares current document IDs and metadata, instead of assuming the collection will always contain exactly 42 PDFs.
- The shared check command detects misplaced country folders, unregistered/missing/changed PDFs, invalid manifest paths, stale catalogs and broken browser references.
- The footer no longer repeats a fixed inventory date. The inventory-driven dashboard carries the date.
- The local preview was restarted with `.venv` Python outside the coding sandbox, after checking there was no active country work. This resolved Codex state-directory access errors; the launch guidance is in `docs/15-ai-connections.md`.

Live model inference, real-country profile generation and hosted integrations were not exercised. The ChatGPT/API transports and country worker were tested with synthetic responses; the separate live Codex check only read startup/account/catalog information.

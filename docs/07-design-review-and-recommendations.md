# Design review and recommendations

Review date: 8 October 2026. Scope: the six initial design documents, ten prompts, schemas, taxonomy, source manifest and local reference implementation. The user subsequently clarified that successful reports publish automatically, audit is optional, and any signed-in team member can manage Prime. Recommendations here now reflect that decision; see `08-product-decisions-and-feature-scope.md`. Documentation/profile updates have been made; the technical failures below have not been repaired.

The Prime/ad hoc separation is a sound foundation. The largest weakness is the distance between the stated evidence guarantees and the actual processing/validation path. The current repository prepares the work but cannot yet produce the first analytical country report. More feature design will not close that gap. Build one complete country result, challenge it with difficult source cases, and then run the remaining countries through that proven path.

The previous statement that schemas validate and ten tests pass was accurate but narrow: it established schema syntax and selected software invariants. It did not establish that the contracts enforce the methodology or that country extractions are accurate. The cases below demonstrate that distinction.

## Priority and evidence

- **P1:** resolve before relying on the affected function for analytical delivery or publication.
- **P2:** resolve before broad analyst use or website integration; not necessarily a blocker for internal draft generation.
- **Observed:** a reproducible behavior in the current code/contracts.
- **Implementation gap:** described functionality that is not yet built.
- **Product decision:** a tradeoff requiring an explicit operating choice.

Synthetic probes are in `evals/review_reproductions.py`; observed results are in `evals/design-review-results.json`. They use invented source text, an in-memory registry and synthetic PDFs in the ignored temporary directory. They do not change the supplied PDFs, perform model inference or publish anything.

## Findings

### D01 P1 The first delivery has no executable production path

**Implementation gap.** The CLI only registers/extracts PDF text. `Provider` defines method signatures without transports, and there is no running translation, chunking, model extraction, reconciliation, synthesis or export worker. Model catalog availability is not an executed Astra request. The proposed API endpoints are specifications, not working functions.

**Recommendation:** implement an operator-controlled local job runner first. It must produce one KAZ draft bundle from both supplied documents, with persistent stage state, exact Astra/xhigh selection, full evidence references, errors and measured usage. Test Russian translation and difficult tables on selected UZB/MDA/KGZ material as additional cases. Do not make hosted OAuth, a complete chat product, or regional narratives dependencies of this first run.

**Acceptance:** a restart resumes unfinished stages; an incomplete/refused response cannot become a report; the generated bundle opens without further LLM calls; settings and usage are recorded. Authenticated inference must actually complete before account access is described as verified.

### D02 P1 Source revisions overwrite the previous extraction cache

**Observed, R6.** `inventory.py` uses the record ID from Source.txt as the output filename. If the reading copy changes but keeps that record ID, the new page JSON/text replaces the previous extraction. The corpus manifest also uses a single overwritten filename. The probe supplied two different PDF hashes for the same record ID and retained only one page JSON file.

**Recommendation:** separate instrument ID, file-version ID and processing-artifact ID. Store immutable source blobs by hash and parsed results by source hash plus parser/configuration hash. Create a new immutable corpus manifest for each snapshot, with a separate convenience pointer to the newest one. Preserve previous source bytes independently of the upstream `Current.pdf` reading copy.

**Acceptance:** revising an input retains both original PDF versions and both parsed artifacts; an old report still resolves every citation to exactly the bytes and parser output used then.

### D03 P1 A valid quotation does not validate the extracted claim

**Observed, R1.** A source quotation containing 20 systems was paired with a structured target of 200 systems. The extraction schema and current semantic validator accepted it. `field_support` can also be empty. The validator checks that a quote exists and decimals parse; it does not establish that the quote supports the number, condition, country or field.

**Recommendation:** make a single validation entry point run schema checks, foreign-key checks, required field support and semantic checks. Preserve numeric tokens and mapped spans, with explicit transformations for normalized numbers/units. Validate critical target dimensions against context, with exception handling for spelled-out numbers and locale conventions. Use a source-oriented evidence challenge for meaning that deterministic checks cannot establish; unresolved interpretations become qualified or omitted claims and visible limitations, with optional later audit. Do not reduce entailment to a substring-number match or assume a human is available.

**Acceptance:** the 20-versus-200 example fails; unsupported critical fields cannot receive a passing receipt; legitimate normalization such as two-fifths to 40% can pass only with a recorded transformation and sufficient context.

OpenAI also explicitly notes that structured output may contain mistakes. JSON correctness alone is not evidence correctness. [Official structured-output guidance](https://developers.openai.com/api/docs/guides/structured-outputs).

### D04 P1 Page accounting is being treated too much like extraction completeness

**Observed, R2.** The same explicit target can be omitted and the segment labelled background; the current checks accept it. A model can account for every page without finding every meaningful commitment. The issue is inherent in the distinction between processing coverage and recall, not something a JSON schema alone can solve.

**Recommendation:** store separate measures for parser readability, translation coverage, extraction execution and sampled extraction recall. Run a source-oriented omission pass over high-risk tables, annexes and segments labelled background; do not show only the first pass's extracted records to that checker. Require a reason and review sampling for exclusions. Do not report “100% complete extraction” merely because all page IDs appear.

**Acceptance:** the omitted explicit target is detected by the evaluation/challenge process. Reports state what was processed and the basis for their completeness claim. Review data includes false negatives, not just invalid extracted records.

### D05 P1 Report and dashboard contracts permit misleading outputs

**Observed, R3 and R4.** A country report with `evidence_available` and no findings or sections passes its schema. A dashboard row can say `on_track` with a null assessment ID and no evidence. Missing cross-field rules let output contradict the method even when all JSON keys exist.

**Recommendation:** distinguish task schemas from release validation. Define required report section IDs and explicit outcomes such as found, not_found_in_processed_scope, not_applicable and not_processed. Require factual findings to cite existing authorized evidence. Require an observation-based assessment with a reproducible method and validated evidence for every non-neutral progress label; otherwise the deterministic renderer must show not_assessed. Optional human audit is separate. Check that country/report/corpus identities agree.

**Acceptance:** both probes fail release validation. An honest empty-country availability record remains valid. An incomplete section is visible and cannot masquerade as a finished section.

### D06 P1 Publication currently trusts a receipt without verifying the full bundle

**Observed reference-boundary gap, R5.** The local registry can approve and assign an empty `{}` artifact if its trusted caller supplies a hash and booleans saying validation passed. This is not evidence of an exposed remote vulnerability: the README correctly describes the registry as a local reference implementation. It is nevertheless an unsafe production integration boundary until the trusted validation service exists.

**Recommendation:** the worker creates immutable artifacts; an internal validator independently opens and checks all required files, hashes, source references and coverage; the publisher looks up that stored automated receipt. The client must not supply its own success claim. Validate translation status and unresolved critical issues according to the actual release policy. Bind eligibility to the exact bundle hash. Human audit is optional and stored separately.

**Acceptance:** an empty or missing bundle cannot publish, even when a client requests it. Editing any artifact invalidates eligibility. A passing receipt for one report cannot validate another or a later regenerated version. A valid completed report does not wait for human approval.

### D07 P1 The promised canonical knowledge model lacks essential contracts

**Implementation/design gap.** The docs describe document families, segments, commitments, variants, document relationships and review events, but many have no dedicated persisted contract. Reconciliation emits proposed group IDs, and report synthesis expects commitment IDs; the intervening canonicalization and cross-run identity rules are not defined. Triage metadata is represented as free-text field/value pairs rather than a validated document registry.

The general `facts` record also makes some useful expert questions difficult. An institution, cost and indicator need to be attached to the right action, target variant and period. Free text in `role` or `source_or_method` is not enough for reliable regional aggregation. Targets lack an explicit normalized metric identifier and desired numeric direction; policy objective is not the same as indicator increase/decrease.

**Recommendation:** define document/version/segment contracts, canonical commitment/variant contracts, and typed links such as cost_of, implemented_by, measured_by and supported_by. Assign durable IDs in application code with an identity ledger; keep merge/split history and aliases. Store metric identity, unit and desired direction separately, with original wording and unknowns preserved. Define how a reviewed grouping becomes an accepted canonical record.

**Acceptance:** the same commitment retains an identity across a rerun; a revision creates a linked variant; splitting a mistaken merge preserves old references; finance and actor filters resolve to specific actions rather than a country-level bag of mentions.

### D08 P1 Full English translation needs an enforceable completion and authority rule

**Implementation/design gap.** The translation schema contains segment ID, method, English text and flags. It does not identify the specific official parallel segment that was used or itself supply alignment/version/authority metadata. Some provenance may correctly be server-generated, but no complete wrapper or validator is implemented. The English quotation in extraction can also drift from the stored English reading layer.

**Recommendation:** version translations against the original segment hash and retain official-edition mappings, source language, method, glossary version, model settings and review status in a server-owned record. Validate every source segment exactly once, including notes and relevant figure/table content. Link translated excerpts to that reading layer rather than generating independent untracked translations at every stage. Distinguish extraction uncertainty from translation uncertainty.

**Acceptance:** numbers, negation, conditionality and table headers survive the reviewed cases; a conflicting English edition remains visible. A failed translation cannot be counted as complete. Keep full English availability in the first-delivery requirement unless the user explicitly agrees to stage it later.

### D09 Resolved operating decision: automatic publication, optional audit

**User clarification.** There is no human review capacity to make approval a prerequisite. Reports must be usable and visible automatically after successful runs. Any signed-in team member may run Prime or pin/unpin a selected report. The earlier draft-first and mandatory-review recommendations are superseded.

**Recommendation:** separate automated eligibility, optional audit, source availability and Prime selection. The latest eligible successful run becomes Prime by default; a pin holds the selected version. Use automated evidence/omission challenges and visible limitations without inventing human acceptance. A future manual benchmark can improve evaluation but does not block operation. Do not claim measured recall from model self-evaluation.

**Acceptance:** a valid completed report becomes visible without reviewer action. A failed run does not replace the last working Prime. Pinning survives later runs, and unpinning resumes automatic selection. A partial report is never counted as a full substantive country report. The reference registry and v1 manifest still require implementation changes for this behavior.

### D10 P2 Newest run is not the same as the correct current corpus

**Design gap.** Ordering runs prevents some race conditions, but a later run can intentionally or accidentally use an older or incomplete source set. The reference registry does not store corpus identity. The single bundle has a generation stamp even though reused translation/extraction/synthesis stages may have different model/prompt provenance.

**Recommendation:** make Prime eligibility depend on an explicitly selected curated corpus snapshot and branch, then order eligible runs within that branch. Separate latest generated, latest automatically eligible and currently selected. Store stage-level provenance and reused-artifact lineage; the summary model must not be mistaken for the model that created all evidence. Candidate creation must compare its source set with the curated snapshot and explain omissions.

**Acceptance:** a later reanalysis of old documents cannot silently replace the current branch. A pinned release remains fixed. Publication shows both source-as-of date and analysis date.

### D11 P2 There is no implemented correction carry-forward or withdrawal workflow

**Implementation gap.** The docs promise edit history and invalidation, but the registry mainly stores approvals and assignments. It cannot represent correction patches, review revocation or withdrawal through its public methods. A future rerun could repeat a correction or reintroduce an excluded false merge.

**Recommendation:** store reviewer corrections separately from model proposals, tied to immutable evidence versions. Reapply only when their source hashes and semantics still match; otherwise queue them for review. Mark dependent summaries/comparisons stale and regenerate before publication. Add withdraw/revoke operations and decide whether a withdrawn Prime falls back to a previous eligible release or becomes unavailable.

**Acceptance:** correcting one target updates every affected view in a new bundle, old history remains readable, and a revoked release cannot be reassigned as Prime without a new decision.

### D12 P1 for hosted access The account login plan is not yet a proved deployment choice

**External dependency and implementation gap.** Existing local ChatGPT authentication, application-owned OAuth, and API-key billing are distinct routes. The proposed design acknowledges this, but no complete inference or application login integration has been demonstrated. The public website cannot inherit the operator's local Codex session.

**Recommendation:** prove the initial account-funded local workflow now; maintain a separate hosted integration checklist owned by the website engineer. Preserve the same business-level features across providers while negotiating real transport/model capabilities. Keep API use opt-in and never fall back to paid calls. Store an explicit principal for quota ownership and permission for resumed/background jobs.

The current official guidance describes open-source/local plan usage and a separate path for paid or remotely hosted offerings; eligibility must be established for the actual deployment. [OpenAI plan-usage overview](https://developers.openai.com/siwc/token-sharing-open-source).

**Acceptance:** a selected-model inference completes and records provenance; expired access stops and resumes cleanly; no credentials are shared across users or copied into the website.

### D13 P1 for scaling Runtime, quotas and full-pass cost are still unmeasured

**Implementation gap.** Full translation, detailed extraction, reconciliation and quality review can produce much more work than summary generation. More context is not automatically better context. The $24 future API trial does not establish full-corpus affordability, and account-funded usage still consumes quotas. The workflow has no implemented token budgeter, queue, checkpoint/retry policy or spend ledger.

**Recommendation:** measure the pilot by stage: source/translated tokens, output and reasoning usage where exposed, latency, retries, failures and expert correction time. Estimate the 18-country run from document/language/table mix, not an average PDF price. Token-budget actual requests and chunk without losing context. Keep the requested Astra/xhigh selection; propose any cheaper setting as a separately evaluated option, never a silent substitution.

**Acceptance:** a preflight displays an estimate and uncertainty; limits stop new work safely; a resumed run does not charge again for completed cached tasks; partial streaming output never becomes a completed artifact.

### D14 P2 The taxonomy needs calibration and an explicit expansion process

**Design gap.** The 40-topic vocabulary is a useful seed. The promised companion examples were unavailable and the reconstructed JSON does not include the original example corpus. No measured topic coverage exists. A fixed vocabulary could hide useful material in generic Climate or other fields.

**Recommendation:** retain the 40 stable IDs, add reviewed positive/negative examples and audit the unmapped queue across every document family. Candidate cross-cutting areas to check include climate mobility, social protection, education, technology transfer, carbon markets and loss/damage; these are hypotheses for the corpus audit, not claims that the corpus contains them. Decide whether each needs a topic, tag or typed relationship. Do not let the LLM create permanent categories independently per report.

**Acceptance:** rare and multilingual topics are evaluated, new IDs have definitions/routing rules, and a taxonomy change has an explicit migration/reprocessing policy. Country counts do not increase merely from multi-label membership.

### D15 P2 Source coverage and operational ownership are incomplete

**Product/implementation gap.** Forty-two supplied files are not proof of the latest complete official corpus. The inventory lists declarations, not verified authority. No owner is assigned for source checking, new uploads, authority conflicts or missing country material. Kosovo needs an availability outcome; Cyprus's EU context must stay regional. The support-document boundary is sensible but official annex/sector-plan inclusion needs explicit curation.

**Recommendation:** keep a curated inclusion manifest with authority, document family, language relationship, date checked, inclusion reason and curator. Set an explicit initial cutoff date and source search scope. A manual new-document update is sufficient initially; automated monitoring can wait. Show missing NAP/NDC coverage as evidence availability, not national performance. Preserve a shared regional document once and link it without implying national allocation.

**Acceptance:** every Prime source has an inclusion decision, current/historical role and authority status. A new support upload remains ad hoc. Missing sources produce a visible collection task.

### D16 P2 The receiving engineer needs a real sample bundle before many API endpoints

**Integration gap.** The screenshot does not establish the site's data model. The proposed schemas introduce domains and status meanings that may not fit the current UI. No real report bundle has been consumed by the website or a small reference renderer. No portable delivery/backup location has been selected for source files excluded from Git.

**Recommendation:** export one real automatically validated KAZ bundle, with generation/audit status and limitations, and have the engineer map it to the existing page. Agree field names, status semantics, document/page links, character encoding, multi-topic display and release IDs. Keep static versioned JSON as the first integration path. Establish source/artifact storage and a restore check; Git alone does not preserve the ignored source corpus. Add APIs only for features that need live interaction.

**Acceptance:** one page renders a coherent bundle, citations open authorized original pages, and a rollback restores the previous bundle without recomputation. The integration handles missing/partial sources and unsupported legacy domains explicitly.

## What to retain and what to postpone

Retain the shared evidence store, two separate histories, atomic country publication, original-language audit, frozen comparison inputs and explicit unknowns. These prevent costly redesign later.

Keep the initial expert experience to a country brief, searchable commitments and source/change inspection. Finance, institutions, indicators, inclusion and support needs should remain structured fields and sections, not separate products with independent Prime states. These are relevant to the implementation workflows in [UNDP's NDC support lessons](https://www.undp.org/publications/nationally-determined-contribution-support-programme-achievements-and-lessons-learned-2017-2025); their exact priority should still be tested with the intended users.

Postpone broad chat customization, all-pairs regional narratives, elaborate clustering maps, composite performance/ambition scores and a large hosted service. The initial evidence extraction should still preserve the fields needed by those future features. More features should not delay a usable country report.

## Operating decisions now answered

The user answered the three operating questions:

1. First delivery means usable reports visible automatically after successful processing, with optional audit afterward. No expert approval staffing requirement.
2. Any signed-in team member can run Prime and pin/unpin a chosen report. Automatic selection is the default; a pin persists until reassigned or removed.
3. The assignment emphasizes consistent, comparable and interpretable commitments across countries, sectors and languages. Recommend five Prime functions and four ad hoc templates as specified in `08-product-decisions-and-feature-scope.md`. True measured performance monitoring still requires observation evidence.

Recommended questions for the country experts and receiving engineer, to ask before expanding the product:

| Recipient | Question | Why the answer changes the design |
|---|---|---|
| Regional expert | What three questions do you routinely answer before a government meeting? | Defines the brief and default ordering |
| Country expert | Which examples would you consider a useful action, an explicit commitment, and mere background? | Supplies gold examples and counts users trust |
| Country expert | What is the most damaging plausible mistake: wrong number, wrong country, omitted condition or missed measure? | Prioritizes review effort and release blockers |
| Programme/finance colleague | Which fields are needed before a support need is actionable, and which must be separately verified? | Prevents a cost mention being mistaken for a project opportunity |
| Optional future auditor | Which recurrent errors should the next automated evaluation include? | Improves the system without making audit a staffing dependency |
| Receiving engineer | Can the current site consume a frozen JSON bundle, and how are documents/pages linked and access-controlled? | Determines the smallest integration |
| Operations owner | Where will original PDFs, translations and reports be retained and restored? | Preserves audit history beyond this workstation |
| Project owner | Will this remain operator-run locally, or must each expert use account-funded inference on the hosted site? | Determines auth eligibility and deployment work |

These questions are proposed for stakeholders; no messages have been sent to colleagues.

## Recommended implementation order

1. Fix source/artifact versioning, define the canonical record handoff, and build one mandatory validation path. Convert R1-R6 into regression checks for the corrected behavior.
2. Complete one small Astra/xhigh inference with the intended account route, then one end-to-end usable KAZ report using both documents. Keep all stages resumable and record actual usage.
3. Challenge the workflow with Russian tables, inherited conditions, expected-result columns, EU scope and unreadable pages. Validate the full English layer and citation drilldown.
4. Freeze a documented corpus snapshot and deliver the remaining country reports with a country-by-country readiness manifest. Kosovo remains an honest no-document outcome until evidence is supplied.
5. Automatically publish successful eligible bundles subject to pinning, test the website with a real sample, then add ad hoc templates and grounded chat using the same evidence and history boundaries. Audit remains optional.

No accuracy percentage, full-report completion claim or production security claim is established by this review. Its concrete result is a prioritized correction plan and six reproducible current failure cases.

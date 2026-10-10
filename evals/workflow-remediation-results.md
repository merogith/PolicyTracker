# Workflow remediation — 9 October 2026

The demonstrated workflow defects have direct fixes, but the complete live workflow has **not passed**. The latest authorized run closed after **9 calls and 2 repairs**: both metadata/translation steps and the earlier extraction passed; the later extraction and Overview did not. The four dependent analyses were not run. Further fixes were made after closing the run and require new live verification. All three evaluation ledgers remain preserved and closed.

## Implemented changes

1. **Advisory extraction notes:** the generated extraction contract now requires `notes` separately from blocking `issues`. Notes survive storage, synthesis input, profile and analysis readers, and JSON/CSV/readable exports. Actual attribution, quotation and coverage defects still reject the result. Archived extraction schemas remain usable without retroactively requiring notes.
2. **Repair diagnostics and attribution:** worker, profile validation and evaluator share extraction acceptance checks. Blocking issues, incomplete coverage, numeric/evidence errors and record-specific country errors are returned together. Missing contextual evidence and coverage errors name the records, segments and missing IDs. The prompt distinguishes a country's stated support for global goals from an invented national allocation of those goals.
3. **Packet size:** insignificant JSON input whitespace is removed without changing strings or numeric tokens. Valid repair responses are embedded as structured JSON when their tokens can be preserved, avoiding double escaping; malformed responses and decimal tokens remain verbatim text. New source segments and extraction batches are limited to **3,000 owned text characters**, retain attribution/neighbor context, and reserve 65,000 bytes for a repair. Both controls are heuristics, not guarantees about model output. Oversized requests still stop without dispatch or evidence truncation. Historical segments remain unchanged.
4. **Quantified projections:** a conditional prospective range uses typed target fields on a `projection` record. Regression coverage confirms that a 22–25% range, 2010 baseline, 2035 deadline and conditionality survive a targets-only table.
5. **Initial browser rendering:** a missing focused element previously produced an empty string and threw before saved-history initialization. Focus restoration now safely handles first load, removed controls and already-focused controls, with two regression tests.
6. **Evaluation guards:** closed ledgers cannot resume; oversize packets never dispatch; call reservations survive provider failure; offline preparation does not claim inference authorization.
7. **Overview citations:** missing record citations and evidence unrelated to cited records are reported together, with finding text and offending IDs. The prompt directs parser/scope qualifications to report limitations when they lack a supporting record; factual findings must retain both valid citation lists. No acceptance rule was relaxed.
8. **Large saved-archive downloads:** an intermittent Windows connection reset was reproduced in the broad check and in one of three isolated archive tests, including outside the sandbox. Persistent HTTP connections passed the same three-test experiment. The server now uses HTTP/1.1 with an explicit zero-length redirect response. A regression verifies repeated complete archive downloads on one connection; authentication, origin/CSRF protection and asset serving remain covered. The precise Windows transport cause was not established; the change avoids immediate server-side connection closure after sending a large response.

Authoritative prompt/schema generators were updated and method outputs rebuilt. Original PDFs, historical profiles and prior evaluation failures were not rewritten.

## Offline and interface verification

- **Final broad check passed: 140 Python tests and 62 JavaScript tests**, plus source hashes for **42 PDFs**, read-only local database integrity, schema/config/prompt/catalog consistency and local UI references. No live model calls were made. Results are in `tmp/workflow-remediation/check-complete.log`. The earlier 135-test run's archive-download failure remains recorded in `tmp/workflow-remediation/check-handover.log`; it was investigated and fixed before this final pass.
- Eighteen focused extraction/evaluation/worker regressions passed after the smaller-batch change. Additional report-citation coverage checks that missing and unrelated citations are diagnosed together. The two focus-restoration regressions passed.
- Seven focused HTTP/security/archive tests passed after the transport change. Seven evaluator guard tests passed, including refusing the obsolete batch plan before provider connection or inference.
- Packet preflight composed all **11 planned stages**, using prior rejected drafts only for conservative sizing, with no provider call. Packets measured **37,534–111,551 bytes**. This is sizing evidence, not acceptance of those drafts as v3 outputs.
- The formerly rejected 209,386-byte repair reconstructed with lossless structured feedback measured **176,321 bytes**; the previous response's parsed content was unchanged. Actual new output sizes remain guarded independently.
- After the latest live failure, offline preflight produced **five smaller extraction batches**, covering every original owned segment exactly once. Requests measured **100,845 bytes** for each earlier-document batch and **112,095 bytes** for each later-document batch, retaining all required context and at least **67,905 bytes** of headroom. The earlier accepted extraction still passes the final validator. This does not prove the next responses or repairs will fit.
- Browser testing used `tmp/workflow-remediation/ui.sqlite3` and synthetic evidence. Saved translation reading, English-text download, saved extraction notes, profile notes, reload/history and the reader controls were exercised. The downloaded UTF-8 file retained page/segment references, original English and translation notes. Download-event automation was slow, but returned the actual file, whose contents were checked.
- Reader/export tests cover escaping, advisory-note retention, scoped tables and archived outputs without notes. The [saved extraction screenshot](../tmp/workflow-remediation/saved-extraction.png) records the visible advisory note.
- Preservation check: **168/168 protected files unchanged**, including the real workspace database and both prior evaluation folders. Recheck at handover is recorded in `tmp/workflow-remediation/preservation-after.json`.

## PDF preparation review

All **19 previously flagged pages** were rendered and inspected. The 14 rotated Russian annex pages of `doc-0c3ac57eba1f25c4` (physical pages 12–25, printed pages 1–14) have usable normal pypdf text in table row order. Layout-mode extraction was unsuitable and was rejected. The normal extraction was checked against each render, including row continuations, numbers, dates and conditions. Fourteen source/page/text-hash-bound reviewed-text receipts now live under `data/derived/reading/879977c958b50ff1daf6af6461ae35b840d6d119f18e1ea2dd95089a864add76/`. Originals remain unchanged.

**Five pages remain blocked for complete graphical recovery**, with unapproved candidates rather than false completion receipts:

- Earlier Belarus physical page 8 and later Belarus pages 3, 5 and 9: prose, chart axes and legends recovered; plotted series have no printed individual point values. Candidate files explicitly disclose that numerical series were not recovered. No chart values were invented, and substantive graphs were not labeled nontext.
- Albania NAP `doc-479fa14721aeb6b3`, physical page 113 / printed page 109: manually transcribed all **39 visible rows (five section headings, 34 tasks)** and approximate quarter-cell spans. Several original labels are clipped at cell boundaries, and some bar endpoints cross quarter boundaries ambiguously. The candidate preserves those limits; exact dates and missing words were not invented. A readable authoritative timetable or reviewed reconstruction is needed before approval. The local OCR path remains available, but Tesseract is not installed; OCR alone would not resolve source-clipped labels or unlabelled graph values.

The 14-call evaluation still uses only the originally authorized five page texts. This preparation work does not create a Country Profile or certify full-document semantic recall.

## Closed live evaluation

The [execution summary](../data/derived/evaluations/workflow-audit/remediated-v3/execution-summary.json), [mechanical review](../data/derived/evaluations/workflow-audit/remediated-v3/mechanical-review.json) and [semantic review](../data/derived/evaluations/workflow-audit/remediated-v3/semantic-review.json) record the outcome. All nine responses confirmed `codex_chatgpt / gpt-6-astra / xhigh`. Recorded usage totals **309,171 tokens** (215,398 input; 93,773 output).

| Stage | Outcome |
| --- | --- |
| Two metadata triages | Accepted, with sample locators and country attribution |
| Two translations | Accepted; all five segment numeric-token multisets preserved; English identity unchanged |
| Earlier extraction | Accepted first attempt: six records, 16 exact unique quotations, ten advisory notes, all eight expected source distinctions retained |
| Later extraction | Rejected: 12 missing contextual links and one coverage link; all 21 quotations themselves resolve exactly |
| Earlier Overview | Rejected after two repairs: final mixed-language chart-label finding has evidence IDs but no record IDs |
| Comparison, gaps, brief, focused extraction | Not run; require both accepted extractions |

The later draft now contains the previously missing **22–25% energy-intensity range** as a typed conditional projection, with its 2010 baseline and 2035 deadline. The 15 expected later-source distinctions appear in the reviewed draft/metadata, but failed evidence links prevent acceptance. Neither those draft facts nor useful Overview prose count as an end-to-end pass.

The later extraction's full lossless repair measured **208,744 bytes**, exceeding the unchanged 180,000-byte limit, so it was never dispatched. The Overview used its two permitted repairs; the run used two of three global repairs. Unused call allowance does not permit resetting the closed ledger or changing its frozen method.

The interrupted original process left call 6's `validation.json` as 816 NUL bytes. That file was preserved. `recovered-validation.json` records validation recomputed from the intact response using the unchanged method; no provider call was repeated. The independent earlier Overview continued in the same call ledger. All archived method hashes remain intact.

The 3,000-character batching, explicit contextual-link prompt checks and improved Overview diagnostics were added **after this run closed**. Their offline checks are distinct from live quality verification.

## Recommended next action

Prepare a revised small-batch evaluation before another live request. The old plan assumed one extraction per document and no longer fits the new batching. Reuse only the four verified metadata/translation outputs, with source, prompt/schema and output hashes checked; regenerate all five extraction batches and the Overview, comparison, gaps, brief and focused extraction. That is **10 baseline calls plus at most three repairs**, within the same **14-call ceiling**, three global repairs, two per step and 180,000-byte limit. Preserve the same exact model/route/effort and five-page scope.

This revised reuse/batch plan still needs implementation in the bounded harness and explicit authorization before execution. Do not rerun the old 11-stage plan against the new batch sizes. Independently, obtain reviewed graphical recovery for the five blocked pages before attempting a complete Country Profile. No full-document or production-readiness claim is supported yet.

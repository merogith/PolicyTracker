# Follow-up workflow evaluation — 9 October 2026

**Translation improved, but the document-to-output workflow still did not pass.** Both triages and both translations passed on their first attempts. Neither extraction passed stage acceptance, so the Overview, comparison, implementation-information check, brief and focused synthesis did not run.

The user explicitly authorized the [prepared follow-up](workflow-live-evaluation.md) with the same **14-call ceiling, three repairs globally and two repairs per step**. This new run closed at **8 calls and 2 repairs**. The earlier extraction exhausted its two repairs. The later extraction's proposed repair exceeded the existing **180,000-byte packet ceiling**, so it was not dispatched. Six unused call slots and one unused repair slot do not override those other limits. No source text was dropped to fit a repair.

## Receipts and preservation

The authoritative ledger is [followup-notes](../data/derived/evaluations/workflow-audit/followup-notes/manifest.json), with frozen method files, source samples, prewritten expectations and all requests, responses and validations. See [execution totals](../data/derived/evaluations/workflow-audit/followup-notes/execution-summary.json), [mechanical checks](../data/derived/evaluations/workflow-audit/followup-notes/mechanical-review.json) and [semantic review](../data/derived/evaluations/workflow-audit/followup-notes/semantic-review.json). The [original seven-call run](workflow-live-results.md) remains closed and unchanged.

| Call | Step | Repair | Provider seconds | Reported tokens | Acceptance |
|---|---|---|---:|---:|---|
| 1 | Earlier triage | No | 40.750 | 20,459 | Passed sampled metadata checks |
| 2 | Earlier translation | No | 65.797 | 22,884 | Passed |
| 3 | Earlier extraction | No | 526.703 | 52,250 | Failed: blocking issues |
| 4 | Earlier extraction | Yes | 346.656 | 63,338 | Failed: record country attribution |
| 5 | Earlier extraction | Yes | 312.937 | 59,151 | Failed: blocking issues returned; per-step cap reached |
| 6 | Later triage | No | 62.531 | 17,893 | Passed sampled metadata checks |
| 7 | Later translation | No | 171.250 | 27,424 | Passed |
| 8 | Later extraction | No | 633.015 | 61,205 | Failed: blocking issues; repair too large |

All **8/8 responses** confirmed `gpt-6-astra` and `xhigh` on the approved `codex_chatgpt` route. No model/effort substitution, API fallback or connection-test inference occurred. Reported usage was **233,611 input + 90,993 output = 324,604 tokens**. Provider elapsed time summed to **2,159.639 seconds**; median **242.094 seconds**. These are call measurements, not total task duration or a monetary estimate. Dispatched packets ranged from **36,026 to 169,528 bytes**. All eight responses passed their frozen schemas; four passed stage acceptance.

During call 4, shared workspace files changed to a newer v3 method. The runner saved the response and stopped on its method-fingerprint guard. Continuation used byte-identical copies of all **40 frozen method files**, the original PDF paths and the same call ledger. The preserved response was validated without replaying it. Both continuation drivers and their rationale are recorded in the ledger. **This evaluation validates observations about the frozen pre-v3 method, not the newer workspace method.** The newer edits were preserved.

Final checks found both original PDF hashes unchanged and **79/79 protected files unchanged**, including the real workspace database and every protected file from the original evaluation. No real Country Profile was generated or published; no credentials were changed.

## Content review and limits

This is an assistant review of five supplied page texts, accepted translations and the last rejected extraction per source: calls 5 and 8. It is not independent human adjudication, a held-out benchmark, full-document coverage or corpus accuracy.

| Case | Source-content distinctions retained in translation and rejected extraction | Extraction locations |
|---|---|---|
| E1 | 2/2: historical ≥28%, 2030/1990, excluding LULUCF and unconditional; new ≥35%, same years, including LULUCF and unconditional | Earlier `r1`, `r2` |
| E2 | 3/3: ≥40%, 2030/1990, including LULUCF; international financing for best available technologies; separate conditional variant | Earlier `r1/t2` |
| E3 | 3/3: 137.8 / 117.2 million tonnes CO2-eq in 1990, excluding / including LULUCF; 2018 projection base distinct from target baseline | Earlier `r3`, `r1/d2` |
| E4 | 3/3: Council of Ministers resolution 06.11.2025 No. 614; 2026–2035 period; historical 28% remains historical | Later `r03`, `r05/d06` |
| E5 | 6/6: ≥42% unconditional and ≥47% conditional, 2035/1990 including LULUCF; ecosystem sink capacity, carbon-market access, exit from sanctions as a source statement, and external finance/capacity/technical/technology conditions | Later `r05/t04/t05/d07/d08/f01` |
| E6 | 3/3 in prose: energy-intensity range 22–25%, 2035/2010, separate from GHG reductions; prospective and conditional. **Not retained as structured range fields.** | Later `r05/d10` |
| E7 | 3/3: 146.02 / 123.73 million tonnes CO2-eq in 1990, excluding / including LULUCF; 2024 projection base | Later `r06`, `r07` |

Thus **23/23 source-content distinctions were retained**, with **0 observed numeric, baseline or condition errors within those distinctions**. The other two prewritten distinctions concern downstream ambition comparisons and were not assessed. There are **0/7 grouped cases established end to end** because both extractions remain rejected. Content retention is not a workflow pass.

- **Translation:** 5/5 segments aligned; 1/1 wholly English segment identical; existing English prefix/suffix on the mixed page identical. Russian chart-label units and conditionality survived. All 17 advisory notes remain visible in saved output, with empty blocking flags. The later source's unusual temperature wording, decimal commas and unfinished final sentence were preserved rather than silently corrected or completed.
- **Triage:** 7/7 metadata/geography pointer occurrences resolve. Both profiles have empty blocking issues and retain 11 advisory notes. National attribution and NDC identity are supported; official authority and complete-document readiness are not certified.
- **Extraction drafts:** 27/27 quotations resolve uniquely to the correct original segments. All four extraction attempts passed the frozen source-quote/numeric-support validator. In the latest two drafts, 11/11 record descriptions have semantic source support, with no observed invented numbers/commitments or wrong-edition/page citations. This does not adjudicate every taxonomy assignment or field-support pointer. Expected facts were reviewed for omissions as well as inventions.
- **Analyses:** citation support, unsupported analytical claims, comparison quality, proposal separation and brief relevance are **not assessed**, with zero analytical outputs generated. No zero-error claim is made for these stages.
- **Images and completeness:** no graph values were reconstructed. OCR, layout certification, full-country recall and unselected pages remain outside scope.

## Demonstrated remaining issues

1. **Extraction still confuses advisory qualifications with blocking issues.** The latest earlier draft has six root issues and the later draft ten, largely covering declared sample scope, source authority, absent separate English-layer IDs, graph exclusions and unverified implementation. The frozen extraction contract requests uncertainty disclosure but does not provide the explicit advisory-note separation added to triage and translation. The worker rejects every nonempty root issue list. Do not fix this by deleting genuine uncertainty or accepting all issues.
2. **Sequential acceptance checks waste repairs.** The first earlier draft also represented collective global temperature goals with no national country code. The first repair cleared issues, then failed the country check. The second framed Belarus's support as a national policy position, explicitly preserving global goals rather than inventing national allocations, but reintroduced advisory issues. Return all applicable acceptance errors together and clarify this attribution distinction.
3. **Repair requests need size headroom.** Offline reconstruction measured the later repair at **209,386 bytes**, versus the 180,000-byte limit. Its full previous response plus the original packet did not fit. This repair was never dispatched. Future batching/repair design must budget for response growth while retaining source evidence and guardrails.
4. **A quantitative conditional effect is only prose.** The later extraction keeps the 22–25% GDP energy-intensity range in a cited co-benefit detail, with its 2035 deadline and 2010 baseline. An offline diagnostic using the existing `evidence_table(..., requested_fields=['targets'])` omits that range because it projects typed targets but not details. The full evidence remains preserved. Decide how quantitative prospective effects should appear in structured fields and selected tables while retaining their conditional status. This diagnostic used rejected output; no focused-analysis model call ran. See [offline diagnostics](../data/derived/evaluations/workflow-audit/followup-notes/offline-limit-diagnostics.json).

## Next work

Address those four issues in the current method, regenerate authoritative outputs, add focused regressions using these retained failures, and run the relevant offline checks. Then a separately authorized bounded evaluation can test the current method and the five still-unmeasured analytical tasks. This run's method or limits must not be changed retroactively.

No production method changes were made after the freeze to force acceptance. Before freezing, the harness was aligned to pass saved translation notes into extraction, and its four spending/guard tests passed. This turn's final verification used frozen schemas, original source text, exact quotations, packet sizing and preservation hashes; it did not rerun or certify the concurrently edited v3 project. Earlier broad offline results remain documented in the [main audit](../design/verification/workflow-audit.md). Full-source Belarus and Albania OCR/preparation requirements and the previously unverified English-text download remain separate unfinished acceptance work.

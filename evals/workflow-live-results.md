# Five-page workflow evaluation — 9 October 2026

**The live workflow did not pass acceptance.** Seven requests ran against the approved `codex_chatgpt` / `gpt-6-astra` / `xhigh` selection. Both sampled triages passed the evaluator's checks, but both translation steps remained blocked by their quality flags. The earlier source used its two permitted repairs; the independent later source then used the third and final global repair. No extraction, Overview, comparison, implementation-information check, brief or focused synthesis ran.

The user authorized the [bounded plan](workflow-live-evaluation.md) with “you can run.” Its ceilings remained **14 calls, three repairs globally, two repairs per step**. Seven unused call slots did not authorize more repairs. No replacement method was dispatched after the fix described below. No real Country Profile, original document, historical profile, credential or publication was changed.

## Execution evidence

The immutable local run is [approved-2026-10-09](../data/derived/evaluations/workflow-audit/approved-2026-10-09/manifest.json). It contains frozen method files and source text, prewritten [expectations](workflow-expectations.json), every request/response/validation result, and [execution totals](../data/derived/evaluations/workflow-audit/approved-2026-10-09/execution-summary.json). Calls 1–4 used `scripts/evaluate_workflow.py`; after its stop, a recorded continuation executed only the originally planned, independent second source against the same ledger and unchanged method. It did not retry the exhausted first step or use rejected translations downstream.

| Call | Step | Repair | Provider seconds | Reported total tokens | Accepted |
|---|---|---|---:|---:|---|
| 1 | Earlier sample triage | No | 48.359 | 20,392 | Yes, sampled metadata only |
| 2 | Earlier translation | No | 74.062 | 22,630 | No |
| 3 | Earlier translation | Yes | 67.657 | 24,296 | No |
| 4 | Earlier translation | Yes | 76.359 | 24,550 | No; per-step cap reached |
| 5 | Later sample triage | No | 55.781 | 17,574 | Yes, sampled metadata only |
| 6 | Later translation | No | 166.297 | 26,929 | No |
| 7 | Later translation | Yes | 109.766 | 27,940 | No; global repair reserve exhausted |

All **7/7 responses** supplied `actual_model=gpt-6-astra` and `confirmed_effort=xhigh`, matching the request. Reported usage: **142,618 input + 21,693 output = 164,311 tokens**. Dispatch elapsed time summed to **598.281 seconds**; median **74.062 seconds**. These are provider-call measurements, not total task duration, a billing estimate or a measured improvement. Request packets ranged from **35,094 to 59,988 bytes**, below the 180,000-byte ceiling. All seven outputs were valid against their **archived** JSON schemas; only two passed stage acceptance. Schema validity alone was insufficient.

The initial sandboxed Codex startup failed before inference because it could not access normal local Codex state. The existing account initialized with approved normal local access. No connection-test inference, model fallback or alternate API billing route was used.

## Content review and denominators

This review inspected the original five extracted page texts against the **last translation response per source** (calls 4 and 7), including rejected output. It is an assistant review of a tiny, known sample, not independent human adjudication, held-out accuracy or an accepted translation release. The original plan's seven grouped expectations were recorded before reviewing extraction or analytical output.

| Case | Source-content distinctions retained in the draft translation | End-to-end result |
|---|---|---|
| E1, earlier p1 | Historical ≥28%, 2030 versus 1990, excluding LULUCF and without added conditions; updated unconditional ≥35%, same years, including LULUCF | Content retained; extraction and normalized-ambition comparison not run |
| E2, earlier p2 | ≥40%, 2030 versus 1990, including LULUCF, conditional on international financing for best available technologies; distinct from unconditional 35% | Content retained; extraction not run |
| E3, earlier p2 | 137.8 / 117.2 million tonnes CO2-eq in 1990, respectively excluding / including LULUCF; 2018 projection/policy-accounting base | Content retained; extraction not run |
| E4, later p1 | Council of Ministers resolution 06.11.2025 №614; 2026–2035 period; historical 28% pledge remains historical | Content retained; extraction not run |
| E5, later p2 | Unconditional ≥42% and conditional ≥47%, 2035 versus 1990 including LULUCF; forest/ecosystem absorption, carbon-market access, exit from sanctions, external finance, capacity, technical and technology-transfer conditions | Content retained; extraction not run |
| E6, later p2 | GDP energy-intensity reduction 22–25% by 2035 versus 2010, within the source's conditional explanation | Content retained; extraction not run |
| E7, later p3 | 146.02 / 123.73 million tonnes CO2-eq in 1990, respectively excluding / including LULUCF; 2024 projection base | Content retained; extraction and normalized-ambition comparison not run |

Of the **25 prewritten critical distinctions**, **23 concern source content** and were retained in the reviewed drafts. The other **two concern downstream ambition comparisons** and were not tested. This is **0/7 grouped cases established end to end**, not a seven-case workflow pass. Extraction recall and precision have no observations.

- Segment alignment: **5/5** expected segments returned once in the final drafts. English identity: **1/1** whole English segment byte-for-character identical; the mixed page's English prefix and suffix also remained identical. Six Russian chart-label translations retained axis units, conditional/unconditional labels and reporting-period meaning, with the ambiguous acronym interpretation disclosed as a terminology decision.
- Within the 23 reviewed source-content distinctions: **0 observed numeric, baseline, condition or attribution errors**, and **0 invented numbers/commitments**. This does not cover an entire document, chart reconstruction or all linguistic nuance. The later source's awkward temperature phrase was translated literally and qualified rather than silently replaced with standard treaty wording. The final page's unfinished sentence remained unfinished.
- Triage: **8/8 metadata/geography pointer occurrences** resolve to the five supplied source segments. Both country and NDC attributions match the sample text; the later adoption inference is disclosed, and unknown publication dates remain null. These checks do not certify official authority or satisfy a full country's metadata/preparation gate.
- Analytical citation resolution/support, unsupported analytical findings, gaps/proposal separation, comparison usefulness and brief relevance: **not assessed; zero such outputs generated**. There are no extraction quote spans to score. These are not zero-error passes.
- Both final translation drafts disclose their restricted page scope and unavailable graph content. No plotted values were invented. Raster graph recovery, page-layout fidelity, OCR and full-document coverage remain outside this evaluation.

## Demonstrated failure and correction

The original translation schema offered only `quality_flags` for qualifications, while the shared contract required scope and uncertainty disclosure. The worker rejects every nonempty quality-flag list. The model therefore put successful English identity, faithful mixed-language handling, declared sample limits and known graph exclusions into a field that blocked processing. The first final draft had three such flags; the second had four. Repairs mostly reworded disclosures and could not resolve this contract mismatch. Some source uncertainty was legitimate and must remain visible.

Triage had the analogous shape: advisory sample/date/authority qualifications appeared in `issues`, which the full country worker treats as blocking. The evaluator's narrower metadata checks accepted them, so those two passes must not be described as completed production triage.

After all live calls stopped, the following direct changes were made:

1. Authoritative triage/translation prompts and schema generator now provide **advisory `notes` separately from blocking `issues` / `quality_flags`**. Source differences and faithfully preserved uncertainty retain qualifications; unreadable required content, unresolved attribution and translation defects remain blocking. Notes never certify authority or layout.
2. The worker preserves translation notes in aligned source segments; Country Profile, evidence and analysis readers display them. JSON, readable HTML and English reading exports retain them. Older saved outputs remain readable without notes; archived flags and evidence are not reclassified or rewritten.
3. The standalone translation writer also rejects unresolved flags before creating a complete reading copy. Synthetic examples now put their demonstration disclaimer in notes, avoiding examples that normalize nonempty blocking flags.
4. Offline regressions cover advisory-note preservation/escaping, continued blocking of genuine defects, saved notes through stop/resume/reuse, and evaluation call/repair/method guards.

Sources: [schema generator](../scripts/build_v2_contracts.py), [translation prompt](../prompts/v2/03-translate.md), [triage prompt](../prompts/v2/02-triage.md), [worker](../src/policytracker/country_runs.py), [translation writer](../src/policytracker/translations.py), [shared reader](../design/prototype/evidence-reader.js). The method pack and synthetic examples were regenerated. **The revised method has not been tested with a live model.** Existing failed attempts retain their original method and result status.

## Verification and remaining acceptance

The full offline check passed **116 Python tests and 49 JavaScript tests**, all 42 original PDF hashes, 48 UI references and the real database's read-only integrity checks. The Python suite took 284.693 seconds. Results are recorded in the [main audit](../design/verification/workflow-audit.md) and `tmp/workflow-post-evaluation-check.log`.

Browser verification used `preview_ui.py --port 8877 --profiles-path tmp/workflow-live-review/notes-ui.sqlite3`, an isolated database with one synthetic translation. Its bilingual reader showed both saved notes, and its readable HTML download retained them. The separate English-text download could not be confirmed: browser automation timed out waiting for a file, so this particular UI check is **unverified**, despite the existing handler and passing export/retention tests. No model was connected to the preview. The temporary browser tab and server were closed after checking.

The original evaluation is closed at seven calls; its method and repair reserve cannot be reset on resume. A separately authorized evaluation of the corrected method is needed to establish translation acceptance and then run both extractions and all five planned synthesis tasks. It should reuse the same source hashes and expectations, retain the original failures for comparison, and specify a new bounded repair budget. Full country runs still require the page preparation described in the original plan. The unused seven-call allowance is not treated as authorization to evade the exhausted repair limits.

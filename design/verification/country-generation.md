# One-country workflow verification

9 October 2026. The update keeps the existing visual style, Python server and SQLite store. It connects a compact document/model form to one durable background worker. Both country views still read one checked profile.

## Verified

- A synthetic run completes metadata checks, aligned translation, extraction, reconciliation, Overview generation and the existing profile save boundary.
- A repeated compatible run reuses saved requests. Cache keys remain stable after JSON serialization; downstream stages are not re-executed just because object keys changed order.
- Stop retains a valid current response and prevents the next request. Resume reuses completed steps. A new worker instance does not automatically start inference.
- Validation failures are bounded to two repairs, preserve the previous checked profile and expose the failing step. Unknown citations and unrelated reconciliation links are rejected.
- Changed methods/sources, cross-country selections and unreadable pages cannot silently proceed. Source text is not truncated to fit requests.
- Structured API/Codex adapters pass the schema, selected model and effort. Returned model mismatches fail; full responses, provider receipts and usage are archived. Tests use fake transports.
- Country actions enforce session, CSRF and same-origin boundaries. Credentials and source/database paths are outside the static serving allowlist.
- Generated provenance is distinguished from imported/synthetic profiles. Conflict links and source text are HTML-escaped. Source records remain separate.

## Checks run

- Full Python regression run: **88 passed** before the last focused additions.
- Final focused country/provider/profile run: **38 passed**, including the two added Python tests (90 total Python tests now present).
- Structured transport/compaction regression rerun after the final returned-model check: **6 passed**.
- Final end-to-end save/cache check confirms readable provider receipts in profile JSON.
- JavaScript suites: **28 passed**, including progress states, escaped errors, saved evidence and generated conflict/provenance rendering.
- Existing v2 pack, methodology, operations and integration contract checks passed; prompt Markdown bytes remain unchanged.
- Browser: opened the updated loopback preview, selected a country, opened the generation form, changed document selection and navigated away/back. Selection remained intact, the disconnected start action stayed disabled, and the browser reported no JavaScript errors. No inference was started in the browser.

Commands use the bundled Python runtime with `src` and `tmp/python-deps` on `PYTHONPATH`; JavaScript uses recent Node with `--test-isolation=none` in this sandbox. Test logs are under ignored `tmp/`.

## Limits retained

Real country/model acceptance is deliberately left to the user's one-country tests. No paid model request, real country generation, corpus rewrite or external publication was performed. Automatic OCR, independent PDF-table/semantic auditing and partitioned synthesis for requests above the local size ceiling are not implemented. A stopped provider request finishes before the worker stops; the UI states this explicitly.

See [architecture and operating limits](../../docs/ARCHITECTURE.md). Screenshot: [country generation form](country-generation-form.jpg).

## Document recovery follow-up — 9 October 2026

The Albania failure exposed a resume loop: missing page reviews cannot be repaired by resuming a frozen run. Failed preparation now opens a source checklist, preserves the run's document/model selection, and reports every affected document and physical page before generation. The page editor provides an original render, checked transcription/nontext review, and local OCR drafts. The same parser and review validation are used by inventory, preflight, CLI and generation.

Verified with the real local corpus and offline fixtures:

- `scripts/check_project.py --local-data` passed: 154 Python tests, 67 JavaScript tests, all contract/build checks, all 42 original PDF hashes and read-only profile database integrity. Logs: `tmp/albania-preparation/check-project.log`.
- A final regression reproduced and fixed a malformed-draft crash. The focused document/preparation/inventory rerun passed all 21 tests, including that addition (155 Python tests now present). Logs: `tmp/albania-preparation/document-final-tests.log`.
- Recovery covers page extraction failures, unused versus drawn image resources, password-protected/corrupt documents, invalid or changed receipts, missing OCR languages, local process timeouts and protected HTTP actions. OCR artifacts are hash checked and frozen with approved reviews.
- A real Tesseract run on an invented English/Russian page retained the tested words and numbers. Browser OCR on Albania NAP physical page 110 recovered chart labels and persisted an unapproved draft with its PNG/TSV and 17 low-confidence words. It was not automatically accepted.
- Browser checks exercised the legacy failure action, all-document preflight, page rendering, nontext review saving, retained model selection and OCR draft loading. A cold check completes within the longer preparation timeout; a repeated unchanged-source check took under one second in this session.
- Albania NDC 3.0 physical page 15 has a visually checked transcription, including chart labels. An offline call to the actual source-preparation stage processed all 70 pages and consumed that transcription exactly. NAP physical page 83 was visually verified as non-substantive and saved through the editor.
- The seven original Albania source/metadata files and both existing profile databases remain byte-identical to the before-work snapshot. No live model call or real profile generation was performed.

At this check, NDC 3.0 is ready. The other two selected Albania documents still contain 47 flagged pages (7 NAP, 40 earlier NDC). Their substantive graphics and clipped content still need visual review; no blanket approval or inferred chart values were used. Local OCR is available from the project environment with English and Russian language data. Software tests and OCR confidence do not establish semantic extraction quality.

# Evidence experience verification — 9 October 2026

This is a software and interface verification record, not user research or validation of national policy findings. The implementation and its remaining service work are specified in [the evidence experience](../../docs/16-evidence-experience.md). The impact assessment and implementation sequence were written [before editing](../implementation-plan.md).

## Automated checks

`python scripts/check_project.py --local-data --node <Node 24+ executable>` passed:

- All 42 original PDF paths and SHA-256 fingerprints match the corpus manifest.
- Read-only SQLite integrity and foreign-key checks passed.
- Local HTML/module/JSON references resolve.
- Methodology, legacy/v2 schemas, operational requests and integration contracts passed. The 20 prompt sources remain byte-identical to their generated catalog.
- 98 Python tests and 44 JavaScript tests passed. Tests use offline fixtures/fake transports; no live model calls.
- The new `check_report_experience.py` verifies the deterministic 12-record fixture, extraction/report schemas, exact quotations, evidence/target links, archived labels and presentation schema. It is included in the aggregate project check.

After the final fixture wording update, its checker and all 14 affected evidence/renderer tests passed again. Following the last navigation/layout refinement, all 44 JavaScript tests, app syntax, local asset references and updated documentation links passed. The fixture labels cross-source interpretation as derived analysis. Core cases cover cross-domain counting, qualitative commitments, unmapped terms, all six missing reasons, conditional target variants, target-linked details, preserved export context, formula-safe CSV, archived definitions and unsupported saved views.

## Browser checks

Used the actual local server on loopback port 8871 with an isolated SQLite backup at `tmp/report-design-preview.sqlite3`. No generation, connection test, source import or archive write was requested. The new presentation fixture is loaded from its own JSON file and is never imported into the country archive.

- Opened Overview, then Policy register with Summary, Targets, Risks and resilience, and Delivery and support. Static narrative explicitly retains full saved scope.
- Selected irrigation and explicit conditionality: one source record, only the 50-hectare 2035 variant in the table/date view. Drafting an additional 2030 filter left the count unchanged until Apply, then produced zero matches because the predicates must match one variant.
- Saved “Conditional irrigation”, restored defaults, applied the named view, and reopened after reload. Settings and the one-record scope were restored.
- Opened Russian/English evidence with document/page and translation status. Escape closed the drawer and focus returned to the initiating statement. Filters remained intact.
- Opened the comparison, implementation-information review, question briefing, extraction and translation demonstrations. Translation page selection opened the aligned stored segment. Empty, partial, earlier-version, pending-source and failed-update explanations were exercised.
- Downloaded current-view evidence JSON through the browser. Inspected the file: exact version, one matching record, two sibling targets retained as context, definitions, citations and explicit filtered scope.
- Copied and reopened a local view link. A missing startup invocation was found and fixed; retesting restored the exact version and filter. An unavailable-version link showed a refusal instead of substituting current data.
- At 1366, 768 and 390 CSS-pixel viewport overrides, the tested pages had no page-wide horizontal overflow. The mobile comparison table scrolls within its labeled region. Mobile evidence text also stays within its dialog. Temporary viewport overrides were reset after capture.
- Visible focus, selected-state text, native checkbox/select controls, table captions/alternatives and non-color status explanations were inspected. No browser console errors were captured after the final reload.

## Screenshots

- [Desktop overview](report-experience/desktop-overview.jpg)
- [Filtered register](report-experience/filtered-register.jpg)
- [Bilingual evidence](report-experience/bilingual-evidence.jpg)
- [Policy comparison](report-experience/comparison.jpg)
- [Mobile overview](report-experience/mobile-overview.jpg)
- [Mobile evidence](report-experience/mobile-evidence.jpg)
- [Tablet overview](report-experience/tablet-overview.jpg)
- [Translation reader](report-experience/translation-reader.jpg)

## Integrity and limits

A pre-edit manifest covered 322 existing files. Source PDFs, extraction prompts, label configuration and extraction/report schemas were preserved by this change. The audit also detected unrelated edits during this task to inventory code, inventory tests/checks, AI connection documentation, generated regional metadata and the original workspace database. These were preserved rather than reverted. The database passed the read-only integrity check; the reader redesign was tested against its separate backup. A claim that the entire workspace stayed byte-identical would be incorrect.

Not verified: real user task completion, extraction recall/semantic accuracy, real model output, comprehensive WCAG conformance or screen-reader behavior, all browsers/scripts, corpus-scale performance, hosted authorization/sharing, optional report execution, full original-PDF access or real historical-version JSON retrieval. Those remain explicit, prioritized acceptance/integration work in the specification. Presentation preferences are browser-local; links provide context, not access rights.

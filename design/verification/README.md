# Prototype and contract verification

For the current connected local workflows, see the [complete workflow audit](workflow-audit.md), including feature/options matrices, corpus inspection, regression checks, browser scenarios and unverified real-model quality. Older entries below describe their original verification scope.

Current verification: [evidence experience, perspectives and saved views](report-experience.md). The material below is historical single-country design verification. The [lean tools update](lean-tools-update.md), [three-view update](methodology-update.md) and [regional update](regional-update.md) record preceding revisions.

Performed 8 October 2026 against the local synthetic design prototype. This verifies selected reference interactions and contracts, not a hosted service or national-policy accuracy.

## Verified

- Country overview, evidence tab, sector/risk switch and hazard filtering; unmatched filters show an explicit empty state.
- Source button displays the stored English and Russian excerpt, condition and unknowns.
- Evidence dialog closes with Escape and returns focus to its source button.
- In-memory pin/unpin changes the selection explanation; automatic mode can be restored.
- “Preview setup” creates an explicitly labeled setup in Reports without producing an analysis or changing country selection.
- Integrations shows the frozen-bundle API example and explicitly states that the service is not deployed.
- Overview at 390, 768 and 1366 CSS-pixel viewport overrides. Document scroll width equals client width at each. At 390, the evidence list also has no page-wide overflow and the bilingual dialog stacks vertically.
- No browser console errors were captured after the final reload. Temporary viewport override was reset.
- Five JavaScript client tests passed for URL/credential/ETag handling, missing idempotency/concurrency controls, empty 304 handling and structured errors.
- Integration checker passed for 29 operations, 35 component schemas, nine read-only tools, optional-run isolation, references and synthetic fixtures. Existing v2 pack check passed for 16 schemas, 12 routes, 13 stages and three examples.

Screenshots: [desktop](desktop-overview.jpg), [mobile](mobile-overview.jpg), [tablet](tablet-overview.jpg), [bilingual evidence](bilingual-evidence.jpg), [report setup](report-setup.jpg). Setup/history state is deliberately not persisted across browser reloads.

## Commands and limits

`python scripts/check_integration_contracts.py` uses JSON Schema validation and focused contract consistency checks, not a complete OpenAPI semantic validator. `python scripts/check_v2_pack.py` checks the existing analysis pack offline. No provider was called.

The sandbox blocked Node's subprocess-based `node --test` runner with `spawn EPERM`. Running the same test module directly (`node tests/integration-client.test.mjs`) passed all five tests in process without extra permissions.

Not assessed: comprehensive WCAG conformance, screen-reader testing, RTL/other scripts, every browser, full keyboard focus cycling, large-corpus pagination, authenticated permissions, real source uploads, OCR, model calls, persistence, export services, queue/publication concurrency, live API/MCP transport or tenant isolation. These remain production acceptance work in documents 11–12.

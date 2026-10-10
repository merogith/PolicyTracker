# Evidence experience implementation plan

Approved scope: the two-view country experience, optional report demonstrations, saved presentation preferences, accessible evidence inspection, exports, and matching methodology/design documentation. Prepared before implementation on 9 October 2026.

## Impact and boundaries

- The working path is SQLite archive → `/api/profiles/{country}` → `profile-view.js`. Current extraction, report, codebook and evidence bytes are sufficient for perspectives. No new model call, pipeline stage, record merge, taxonomy ID or database migration is needed.
- Add a pure shared evidence model in `integrations/javascript/`; keep browser state and rendering in `design/prototype/`. The reusable component consumes the same source-record projection and count semantics.
- Preserve `storedProfile`, `filterRecords`, and `bindStoredProfile` entry points where practical. Replace record-card walls with a table and a readable detail dialog. Retain archived codebooks and exact evidence joins.
- Presentation filters are independent from `operations/analysis-request` generation filters. Do not expand worker/request capabilities merely because the reader supports more facets.
- Explanatory `config/methodology.json` and documentation change; extraction prompts, taxonomy/vocabulary, output schemas, worker, archive and providers do not. Rebuild derived catalogs from authoritative sources. Do not rerun source inventory or regenerate historical outputs.
- The current read endpoint exposes the selected profile, while CSV can address a version. Historical reading, hosted access links, shared preferences and completed optional-report persistence remain integration gaps. Demonstrate these honestly with isolated fixtures, without changing selection pointers.
- All repository files were already untracked. Preserve user files and capture a pre-edit hash manifest; do not stage or commit unrelated work.

## Ordered implementation

1. Capture source/method/archive fingerprints and renderer baseline. Define pure filter/count/export/state behavior and its regression cases.
2. Implement the shared model, browser-local state, scope header, four perspectives, table, evidence inspector, and accessible visual summaries.
3. Add isolated synthetic cases and task-specific report screens; connect the regional demonstration and optional tools without modifying saved country data.
4. Update reusable component, explicit full/current-view exports, responsive styling and utility navigation.
5. Synchronize methodology, customization, architecture, UX/state contracts, report/perspective and visualization specifications, and stale documentation references. Rebuild affected catalogs.
6. Run focused and existing regressions, contract checks, browser journeys, keyboard/focus and responsive inspection. Save representative screenshots and a factual verification/handoff record.

## Acceptance invariants

Domain → topic is the only hierarchy. Domains derive from the selected version's codebook. Independent facets retain their meanings. Unmapped evidence stays searchable. AND across dimensions, OR within each. Multi-domain records count once overall and once per bucket; bucket sums may overlap. Target filters match one target variant together. Typed details remain linked to their record/target IDs. Empty extraction does not prove source absence. Narrative stays scoped to its saved report. Source facts, observations, derived counts, suggestions and user emphasis stay distinguishable. Views never mutate evidence or invoke inference.

Named views store only versioned presentation preferences on this browser. Restoring incompatible labels fails explicitly; it never broadens scope silently. Evidence dialogs preserve filters, scroll and focus. Current-view exports retain citations, definitions, scope and limitations; full exports retain complete saved evidence.

Verification uses synthetic and saved illustrative evidence. Software checks are not real user testing or certification of model accuracy.

## Implementation outcome

The six steps above are complete for the authorized front-end and supporting specification scope. The report/perspective matrix, visualization rules, saved-view contract and prioritized backend work are in `docs/16-evidence-experience.md`. Methodology/configuration documentation and generated method catalogs are synchronized. The new reader checker is included in `scripts/check_project.py`.

The aggregate offline project check passed with local source/database checks, 98 Python tests and 44 JavaScript tests. Browser journeys, responsive captures, the link-restoration fix, workspace integrity observations and remaining verification limits are recorded in `design/verification/report-experience.md`.

# PolicyTracker usability review — 9 October 2026

## Automatic pipeline follow-up — 9 October 2026

This follow-up supersedes the earlier manual-preparation and upload limitations below. The existing Python server, SQLite store and browser now run automatic page recovery, evidence processing and local publication. Optional moderation happens afterward. No live AI call or real country generation was used for this verification.

- The Albania view now has one **Generate profile** action, optional settings, and a collapsed historical failure. New runs do not require page review. Its previous failed run and original documents remain intact; generating a real replacement is a separate operating action.
- An isolated server on port 8790 used the existing fake transports and synthetic providers. Generate completed automatically; Save & rerun completed a second job. A newly uploaded invented PDF retained its filename and bytes, registered once, and appeared selected in the document picker. A saved analysis published automatically, moved to unpublished history through optional moderation, and was republished. The isolated server and tab were closed afterward.
- Settings were saved, reloaded, changed to concise output, then restored to the original standard output using version history. A discovered Windows newline-conversion bug was corrected: unchanged method files retain their exact bytes across saves. Browser tests also caught and corrected an invalid JavaScript import. The final country page produced no console errors.
- Settings and analysis source selection fit a 390 × 844 viewport without horizontal document overflow. The viewport override was reset. Screenshots: [country generation](../../tmp/automation-update/automatic-workflow.jpg), [saved settings](../../tmp/automation-update/settings-saved.jpg), [synthetic moderation](../../tmp/automation-update/synthetic-moderation.jpg).
- Regression coverage exercises automatic image transport on both AI routes, numeric recovery discrepancies, partial and unreadable coverage, retry/cache behavior, large synthesis batches, publication without review, optional moderation, saved settings and restoration, upload identity, and session/active-job guards. The suite uses invented evidence and fake model outputs.
- Final `scripts/check_project.py --local-data --node <Node 24 executable>` passed: **170 Python tests and 67 JavaScript tests**, all contract/methodology checks, source fingerprints and local-store integrity. The exact log is [check-passed.log](../../tmp/automation-update/check-passed.log). The generated methodology catalog contains all 21 configured prompt sources.
- All 102 original source files, including 42 PDFs, retained their fingerprints. Both existing SQLite stores passed read-only integrity checks; all 171 archived content objects retained their hash integrity. Historical results and review receipts were preserved.

These checks establish software behavior, not OCR fidelity, extraction recall or real multilingual model quality. The main preview remains on port 8788; connect AI and select Generate profile to start a real run with the new pipeline. Unrecoverable content is disclosed in partial results; wholly unusable inputs or failed evidence validation do not replace a valid published result.

## Earlier interface checkpoint

Implemented and checked in the existing Python/SQLite/JavaScript application. These are **agent-led task walkthroughs and visual/heuristic checks**, not testing with UNDP participants or expert validation. No participant feedback was obtained. No live model call, credential change, real country generation or publication was performed.

## Test environment and preservation

The working tree was inspected before edits; the repository's files were already untracked. Existing work, source files and archived profiles were retained. The UI was copied into `tmp/usability-baseline/` before changes, and the actual application was navigated before editing. Baseline screenshots were captured then; regional/tablet/phone comparisons were recaptured from that preserved UI copy to correct inconsistent capture dimensions. The replay used the same inventory and a read-only profile endpoint, with AI execution unavailable.

Preview command: `.venv/Scripts/python.exe scripts/preview_ui.py --port 8788 --profiles-path tmp/usability.sqlite3`. Ports 8765/8766 were already occupied. The test database was an isolated SQLite backup; extra saved profiles and five completed operations used the existing synthetic providers only. Real sources and the original local store were read, not rewritten. The real local Albania preparation attempt was already failed; no active country job needed stopping before the explanatory method update.

## Coverage and audit findings

| Destination / state | Task and observed friction before editing | Correction and shared cause | Verification |
|---|---|---|---|
| Regional picture, first visit and zero profiles | Find a country; large counters and feature explanations delayed the country list, duplicated view statuses suggested separate deliverables | Concise source/profile availability; three-column searchable list; real saved-profile themes only | Country search, no matches, clear, availability filter, country/back navigation; no invented regional findings |
| Country Overview, available sample and ungenerated real country | Read findings; technical scope/controls and two tab rows competed with content | One country navigation row; findings first; coverage/audit disclosures; generation controls secondary | Desktop/tablet/phone screenshots; Albania ungenerated and Kosovo no-source states |
| Country failed preparation | Understand next action; large stage panel dominated reading | Concise visible error with details/actions behind disclosure | Albania NAP page 83 and the required next step remain visible; no Resume/Run action taken |
| Policy register and four perspectives | Find commitment/target/responsibility; too many controls before rows | Shared search/common filters, extra facets/columns in Customize, charts in disclosure | Flood search returned 4/12, no-match search 0/12, clear restored 12; Targets retained 9 relevant records including qualitative commitments |
| Conditions and record detail | Verify financing dependence when target columns are hidden | Condition stays under the statement in shared record tables | Explicit financing wording and fallback conditional label covered by regression test; original/English and detailed record fields inspected |
| Evidence dialog | Inspect then return without losing context | Existing reusable reader with preserved focus/filter/position; clearer missing-codebook explanation for operation results | Escape restored the originating flood-record button and retained the search; nested report citation reader closed back to its result |
| Prepared requests | Tailor a brief; task, source, field and model settings appeared together; work could not be reopened reliably | Three steps, essential task options, review and named browser-local draft; separate execution disclosure | Three Albania documents and finance question saved, reloaded and reopened unchanged; no execution |
| Reopened document picker | Clear all selected files, then recover; country choices disappeared after last deselection | Keep source-country choices visible independently of selected IDs | Reproduced, corrected, retested: 3 choices remain at 0 selected; Continue disabled, reselect enables it; regression test added |
| Saved result history and exports | Identify completed work and useful output; technical receipts/text trees crowded content | Separate prepared/executed sections, dates/scope, task-specific readers, consistent Export disclosure | All five synthetic executed result types opened; extraction CSV and readable HTML downloaded and inspected; citations opened from comparison |
| Documents & translations | Identify source, language and saved coverage | Search title/country/type; saved-copy availability; unique physical-page selector and original/English labels | Registered original link inspected; synthetic bilingual copy and page selector read; saved page count distinguished from full document pages |
| Version history and returning visits | Reopen older version; raw IDs/timestamps dominated; Back could lose sample version | Readable dates, secondary exact IDs, exact selected version in browser history | Older version survived documents/Back/reload; opening newer and going Back restored the older selection without replacement |
| Method & prompts | Find instructions; long processing specification before entry point | Plain introduction, searchable exact prompt directory, complete expert reference/assembly disclosures | Extract prompt opened; exact source/hash/download available; current vs archived method explanation visible |
| Knowledge & labels | Find a definition; large information model above search and broad groups as search results | Search first, specific matching definitions, related-domain links, simple worked example; full reference retained | “conditional” returned 7 relevant definitions; nonsense returned 0; Clear restored reference |
| Configuration | Understand draft status and recover from invalid JSON | Maintainer purpose and local-apply boundary clarified, existing validator retained | Invalid JSON disabled download; restoring original restored valid status; no package applied |
| AI connection | Read reports without configuring an account | Secondary destination; connection/test/usage controls separated | Disconnected view inspected. Existing local Codex initialize error remains visible; no login, key entry or live test attempted |
| Help and Integrations | Find practical guidance without a methodology lesson | Question-led Help; integration limits remain explicit | Help links/actions and illustrative tracker visited; no hosted service implied |
| Startup, read-session error, returning results | Early navigation could be ignored during asset loading; expired read session asked for reload | Disabled startup controls until bound; complete asset-load recovery; loading-results state; GET renews once | Fresh reload → regional → sample passed with no new console errors; expired GET and concurrent initialization regression tests; POST never replayed |

Repeated causes were addressed in the shell/navigation (`index.html`, `app.js`), shared reader components/state, task readers and `reports.css`. This work did not introduce another design system, service, database schema or extraction stage.

## Walkthrough results by perspective

Action counts below are observed route/control actions, not timed participant performance. Text entry is counted as one action; scrolling and automation locator corrections are excluded. No prior baseline timing or success-rate claim is made.

| Perspective and neutral task | Result / representative steps | Friction corrected or limit |
|---|---|---|
| Executive: find Albania and understand available information | Search then country (2); visible ungenerated/failed status; Read source documents (1 further) | No need to understand feature matrix or generation pipeline. Main country findings remain unavailable because no real profiles exist |
| Executive: read the first finding of the sample | Open sample (1), read finding without configuration; Inspect evidence (1), Escape (1) | On the 390×844 comparison, first finding moved from approximately y=1094 to y=694: about 400 CSS pixels earlier. This is layout evidence, not a usability score |
| Operational: find flood-related commitments | Register (1), search (1), record (1), close (1); no backtracking | 4/12 matches and original/English financing condition remain clear. Clear filters and no-results recovery passed |
| Operational: prepare and return to a finance brief | Prepare, choose brief, Continue, choose country, Add, Continue, enter question/name, Save; reload then Reopen | Final request retains 3 source IDs/question/name. No methodological instructions were needed for the happy path; additional-file registration remains an explicit capability limit |
| Operational: read an executed result and export | Read saved result (1), Export (1), choose format (1); source citation one further action | Real saved synthetic runner output used, not a mocked result screen. HTML retains qualifications and detailed evidence; CSV retains structured values and notes |
| Expert: inspect a condition and historical method | Record → detailed target/classification/evidence; profile Version/definitions disclosure; historical version checks | Archived codebook and exact identifiers retained; current guide does not substitute historical definitions. Source relationships remain proposals, conflicts stay inspectable |
| Expert: find a definition/prompt | Guides → Knowledge → search (3); Method → prompt search → exact prompt | Search yields definitions instead of opening whole reference groups. Expert material remains available without crowding everyday pages |

No human participant needed instructions because no human participant was tested. The agent used the visible task wording and reported ambiguities; implementation knowledge still limits how strongly these walkthroughs predict first-time user success.

## Visual and accessibility checks

Screenshots were opened and inspected at 1440×1000, 1024×900 and 390×844. The regional and sample-profile layouts fit the document width at each size; broad evidence/comparison tables scroll within labeled, keyboard-focusable regions. Phone menu, wrapped country navigation, request choices, source selection, prompt reader, brief/translation dialogs and evidence panels were exercised. The phone reader prompted a second correction moving sample/coverage controls out of the main path. Prompt source text was increased to 14px after inspection.

Skip to content focused `main`; Tab from country search reached availability with a visible 3px focus outline. Evidence and prompt dialogs closed with Escape and restored initiating focus. Native dialog containment and semantic headings/labels were inspected. Main text uses dark navy, secondary text muted teal-grey, and active controls teal, with measured token contrast of 11.28:1 for main text, 5.63:1 for secondary text and 6.34:1 for the primary button; this is not a full WCAG certification or screen-reader study.

The automation interface could not perform native browser zoom. A 720×500 CSS viewport reflow check had equal document client/scroll widths (705px after the scrollbar); this does **not** substitute for testing actual 200% browser zoom with assistive technology. RTL, other browsers, OS text scaling and real touch devices remain untested.

### Comparable screenshots

| View | Before | After |
|---|---|---|
| Regional, 1440 | [Before](usability/before-regional-1440.jpg) | [After](usability/after-regional-1440.jpg) |
| Profile, 1440 | [Before](usability/before-profile-1440.jpg) | [After](usability/after-profile-1440.jpg) |
| Profile, 1024 | [Before](usability/before-profile-1024.jpg) | [After](usability/after-profile-1024.jpg) |
| Profile, 390 | [Before](usability/before-profile-390.jpg) | [After](usability/after-profile-390.jpg) |
| Request setup, 1440 | [Before](usability/before-analysis-1440.jpg) | [After](usability/after-analysis-1440.jpg) |
| Knowledge guide, 1440 | [Before](usability/before-knowledge-1440.jpg) | [After](usability/after-knowledge-1440.jpg) |

Additional evidence: [phone country list](usability/after-regional-390.jpg), [phone evidence](usability/evidence-390.jpg), [saved request](usability/request-saved-1440.jpg), [empty source selection](usability/request-documents-390.jpg), [extraction](usability/extraction-result-1440.jpg), [comparison](usability/comparison-result-1024.jpg), [phone brief](usability/brief-result-390.jpg), [translation](usability/translation-result-390.jpg), [failed country preparation](usability/country-failure-1440.jpg).

## Completeness and interpretation

All ten saved narrative sections, original/English evidence, classifications, targets/scenarios, actors, finance/support, indicators, field support, missing reasons, extraction/translation notes, coverage exclusions, proposed links/conflicts and exact version/source details remain accessible. Default table simplification does not delete fields or modify evidence. Source-stated content, interpretation and suggestions retain their labels. Full-scope narrative stays distinct from filtered records and current-view exports. Synthetic evidence remains labeled and excluded from country availability/patterns. Regional themes identify their loaded-version scope, including historical selections, rather than implying an all-current comparison.

Only explanatory presentation wording changed in `config/methodology.json`; it now describes the already-implemented optional execution and separate drafts accurately. `method_pack.py build` regenerated dependent assets. No extraction rules, prompt text, taxonomy identifiers, original documents or archived profiles were changed for this redesign. Other pre-existing/concurrent work was preserved.

## Automated verification

- `python scripts/method_pack.py build`: passed; generated assets rebuilt from authoritative configuration.
- `python scripts/check_project.py --local-data --node <Node 24 executable>`: passed, including **130 Python and 59 JavaScript tests** at that checkpoint; log in `tmp/usability-project-check.log`.
- Final JavaScript suite after browser corrections: **62 passed, 0 failed**, using `--test --test-isolation=none`; log in `tmp/usability-js-final.log`. Process-isolated Node tests encountered the Windows sandbox's spawn restriction, so the project's existing no-isolation mode was used.
- Final `check_methodology.py`: passed, including 20 byte-identical Markdown prompt sources/hashes.
- Final asset/import check: 49 references resolved. Final read-only source/store checks: all **42 PDF fingerprints** matched; SQLite integrity and references passed.
- New regression coverage includes visible conditional qualifications, saved request reload/credential exclusion/storage fallback, expired GET recovery without POST replay, shared session initialization, and clearing/reselecting documents in a reopened request. Existing archive, filtering, target-variant, export, translation, worker/transport and integrity suites also passed.
- Fresh browser reload/navigation produced no new console errors. Earlier recorded focus-restoration exceptions were no longer present after the current focus helper and its checks; existing changes were retained.

## Remaining limits

Real country profiles and production regional patterns could not be evaluated without explicitly running countries. Synthetic providers establish interface/software behavior, not translation quality, extraction recall, numerical comparability or expert approval. Current AI connectivity was not repaired or tested with live calls. The failed Albania page needs source inspection before a separate new generation action. Hosted sharing, synchronized drafts/preferences, registered ad hoc uploads and country-scale performance remain outside this local redesign.

Prepared requests are browser/origin-local; clearing browser storage removes them. Executed results remain in the local store. Large result tables may require horizontal scrolling. First-time UNDP participant testing, native zoom/screen-reader testing and real multilingual output review remain necessary evidence before claiming team-level usability or analytical validation.

The updated [customization guide](../../docs/CUSTOMIZATION.md) maps wording/help, label definitions/examples, default filters/fields, shared styling and methods/prompts to authoritative files, build/check commands and regeneration effects.

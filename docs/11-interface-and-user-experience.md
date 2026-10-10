# A simple workspace for country evidence and operational reporting

**Historical design proposal.** Navigation and implementation-status descriptions below record an earlier design, not current capabilities. Use the [browser guide](../design/prototype/README.md), [current evidence experience](16-evidence-experience.md) and [working architecture](ARCHITECTURE.md) for maintained behavior. Do not implement older proposals as additional requirements.

## Current implementation

Use [Reading, exploring and verifying policy evidence](16-evidence-experience.md) for current navigation, four perspectives, report matrix, evidence interaction, saved-view state, export rules and integration gaps. This older document is design background; its three-tab navigation and generic report controls are superseded. The working reader now has browser-local preferences, saved-profile evidence, readable typed fields and scoped exports. Optional result demonstrations are synthetic, not completed model workflows.


> Engineering/design background. Current navigation, task controls and editable-source ownership are defined in [METHODOLOGY.md](METHODOLOGY.md), [document 14](14-lean-tools-translations-and-configuration.md) and [CUSTOMIZATION.md](CUSTOMIZATION.md). Earlier three/five-view and audience/length proposals below are historical; the current profile has Overview and Policy register.

**Revision:** document 13 supersedes this document's country-first navigation and audience/length controls. The current prototype opens the regional feature matrix and uses task-specific operational requests. General evidence, accessibility and publication principles below still apply.

Design baseline, 8 October 2026. This specification extends the v2 knowledge/pipeline pack. The working [local prototype](../design/prototype/README.md) uses invented evidence only. It is a navigation and interaction reference, not a production service or a country assessment.

## The product in one sentence

Open a country to understand its documented commitments in five minutes, inspect the underlying evidence when needed, and create a separate report for an operational question.

The main design risk is exposing the entire knowledge model as navigation. Eleven domains, forty topics and multiple risk dimensions should be filters on the evidence, not dozens of competing pages. A second risk is making “generate a report” look like the normal way to read information: existing country bundles should load immediately without a model account or another extraction.

## Navigation and information depth

| Place | First view | Deeper work |
|---|---|---|
| Countries | Searchable country list with source coverage and report availability | Country overview, evidence exploration, sources/changes |
| Reports | Personal and explicitly shared ad hoc history | Four templates; saved reports; comparisons; grounded follow-up chat |
| Library | Accessible documents with country, instrument, language, edition and inspection state | Original/English reading, version relationships, source selection |
| Integrations, under utilities | Download, connect a website, connect an AI tool | API documentation, component examples, connection permissions |

Country views have three tabs. **Overview** contains the five-minute brief, a few cited highlights, important conditions/support needs, and coverage limitations. **Explore evidence** contains commitments, targets, risk context, finance/actors and indicators with search and filters. **Sources and changes** contains document editions, complete bilingual reading, NDC–NAP alignment, changes between versions and optional audit notes. All three read the same selected country bundle.

Use two exploration lenses: **By sector** and **By risk and resilience**. The latter offers hazards, exposure/vulnerability, DRR phases and resilience functions without forcing these into sector labels. Keep common filters visible; put actor, deadline, condition, geography, instrument and record type under “More filters.” Show active filters and one clear reset action. Multi-label counts cannot be summed as if categories were exclusive.

Information has four depths: brief → filtered record list → record details → original passage/page and English alignment. The detail view keeps the user's place and filters. On a narrow display it becomes a full-width dialog. The full report is a readable document view; it is not a wall of JSON. Provide JSON in the export/integration utility.

## Core journeys

| Journey | Recommended interaction | State to preserve |
|---|---|---|
| Understand a country | Countries → country overview → cited highlight | Selected release, source dates, scope limitations |
| Find DRR commitments | Explore evidence → risk lens → hazard/phase filters → record | Release, filters, scroll position, open evidence |
| Verify a statement | View source → English/original together → open authorized page | Document version, physical page, translation provenance |
| Use evidence in a meeting | Export current report or selected records | Full/filtered scope, evidence IDs, release ID, export date |
| Prepare an ad hoc report | New report → template and inputs → optional personalization → run | Source groups, question, model/effort/route and private/shared audience |
| Update country Prime | Country sources → add/inspect new edition → run country update | Curated NDC/NAP snapshot and automatic/pinned selection mode |
| Keep a stable country report | History → pin eligible version; later choose another or unpin | Pointer revision and selection history |

No publication approval step is required. The run button explains the result: “Generate country report. If successful, this becomes the shared report unless a version is pinned.” Upload alone does not launch inference or change Prime. In pinned mode use “New results will appear in history; this displayed version stays selected.” An eligible run is always usable in history even if it does not become the pointer target.

Ad hoc creation defaults to the current country/report's authorized sources. Four templates are sufficient: Briefing, Focused analysis, Comparison, and Programme/monitoring preparation. Keep personalization to focus, audience, length and optional instructions. Comparison adds named groups and a comparison purpose. If uploads contain several countries, show detected groups and unresolved attribution rather than quietly treating them as the chosen country.

The shared model panel belongs beside the run action and chat input, not on every reading screen. Remember user preferences, but show the actual model, effort and account/API route before dispatch. Capability results control available choices. Authentication expiry, unavailable Astra/Extra High or an unconfigured API route must produce a specific action state, never an automatic substitute. Signing into PolicyTracker and connecting an inference account are separate operations.

Chat opens from an existing report and visibly retains its source scope. Suggested questions can explain a condition, find related evidence or draft an operational brief. Adding a source changes the ad hoc scope explicitly. Saving a generated answer creates an ad hoc result; chat cannot silently update Prime. Ordinary filters/search operate on indexed data and do not invoke chat.

## Clear state and language

Always show country/report identity, Prime versus ad hoc, source scope/date, availability and selected version. “Automatically checked” and “Manually audited” are separate labels. Never use a green tick to imply successful implementation. Documented commitment status and real-world performance assessment have separate fields; initial performance is “Not assessed.” Do not invent a single country policy-quality score.

| State | Useful message/action |
|---|---|
| No documents | No eligible documents supplied; add sources |
| Documents, no report | Sources available; generate the initial report |
| Partial availability | State exactly which source/pages are excluded; display usable supported results |
| Processing | Current stage and completed/total units where known; cancel or leave and return |
| Quota/authentication interruption | Preserve completed work; reconnect/resume with the selected configuration |
| Failed run | Explain the failed stage; retain the previous working Prime |
| New result while pinned | Link the newer result; offer compare, select, or keep the pin |
| Restricted source | Show an access explanation; never expose hidden quotations through export/chat |
| No filter matches | Explain the current filter scope; this does not establish national policy absence |
| Stale pin/unpin | Refresh selection after a concurrent change; do not overwrite silently |

Progress percentages require a defined denominator; unknown remaining model work should use stage labels. “Updated” must distinguish source publication date, generated date and Prime selection date. A saved link preserves release/filter state but grants no access. Back/forward navigation and reload should retain route state in the production app; the prototype's state is deliberately in memory.

## Visual and accessibility contract

Use neutral reading surfaces, one accent, clear typography and restrained borders. Show text alongside status colors. Avoid decorative charts without a useful comparison; use tables for exact targets and small charts only when baselines/units are genuinely comparable. Host branding can override [design tokens](../design/tokens.json).

Target WCAG 2.2 AA, with keyboard operation, visible focus, semantic headings/tables, labeled controls, adequate contrast and text alternatives. Dialogs need focus containment, Escape/close and focus return. Errors and progress updates need accessible announcements. Touch targets should be at least the chosen 44px design target, with reflow at 390px and no page-wide horizontal scrolling. Wide evidence tables can scroll within an explicitly labeled region or offer a card view. These are implementation/verification requirements, not a claim of certification. [W3C WCAG 2.2 guidance](https://www.w3.org/WAI/standards-guidelines/wcag/new-in-22/).

Keep original text direction and language metadata per passage, using `lang` and `dir="auto"`; English is a separately labeled reading layer. Search should match English labels and original-language text without changing the stored original. Downloads must support Unicode. The current prototype exercises Russian/English only; RTL and other scripts need production verification.

## Boundaries and implementation order

The local prototype demonstrates navigation, filters, bilingual inspection, in-memory pin/unpin, report setup and integration examples. It does not implement the country list, real uploads, translation browsing at corpus scale, job queue, chat, persistent state or permission service. Saved setup entries are visibly not generated reports.

Build the first production slice around a validated country bundle: read-only overview/exploration/evidence, export, then source update/run/history/pin. Add the four ad hoc templates and grounded chat over the same services. Reuse these components for integrations rather than rebuilding analysis logic inside a website. The machine-readable interaction contract is [ux-contract.json](../design/ux-contract.json); the portability/security architecture is [document 12](12-portable-integration-architecture.md).

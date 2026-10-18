# PolicyTracker browser interface

Start `python scripts/preview_ui.py` with the project Python and open `http://127.0.0.1:8765/design/prototype/`.

## Where do I begin?

**Regional picture** shows document/profile availability and a searchable country list. Open a country for **Overview**, **Policy register**, **Documents & translations**, and **Version history**. The Overview leads with saved findings. Read a record or select **Inspect evidence** to see original/English passages, page locators and detailed classifications. Closing the reader restores focus, filters and reading position.

Use the register to search statements, targets, institutions or themes. Common filters appear first; **Customize view** holds additional fields, grouping, sorting and named views. **Clear filters** removes filters without resetting the entire presentation. Filtered record counts are source-record counts, not unique commitments; the saved narrative retains its full original scope. Conditional targets stay visibly qualified even when the target column is hidden.

**Create analysis** shows task and document choices with one Generate action. Customize output and saved presets are optional. Reading, OCR/image recovery and publication run unattended on the connected route. **Reports & analysis** holds finished results; optional moderation can unpublish or restore them while retaining history.

The registered document inventory is included with the application; original PDFs are separate local data. On startup, the server checks which originals are present and still match their registered fingerprints. Country counts and generation choices use those available files. Missing or changed originals remain visible in the document library with an explanation. Add PDFs through Create analysis or restore the original files and refresh. Saved profiles and the invented sample remain readable without the current originals. A partially successful upload keeps the successfully registered documents visible even if a later file fails.

## Where are methods and settings?

**Guides & settings** contains practical help, **Method & prompts**, **Knowledge & labels**, **Method & output settings**, **AI connection**, and **Integrations**. Search a definition or prompt directly. Complete rules, exact prompt sources and instruction assembly remain accessible. These pages show current configuration; a saved profile's **Version, definitions and run details** identifies its archived method.

Settings save and apply directly. Save & rerun starts the current scope with the saved method. Advanced prompt and label changes use Apply method changes. Browsing, exporting, presentation changes and saving a prepared request make no model calls. Connections are required only for explicit execution.

Readable HTML exports retain quotations, translations, preparation notes and the saved version ID. Open original PDFs from that version in the running tracker; downloaded HTML omits links that require its local server and authorized browser session.

Running, stopped and failed analyses appear directly in Reports & analysis with their progress and recovery actions. Only completed results that were unpublished appear under Unpublished results.

## How are unavailable states tested?

**Explore a sample profile** opens 12 invented records, excluded from country counts. Example controls at the end of the reader switch report type or demonstrate empty evidence, partial coverage, older versions, stale sources and failed updates. A separately saved synthetic profile can exercise the real local storage/version reader. These examples are not country assessments.

**Open Kazakhstan pilot dashboard** on Regional picture to browse the selected-page taxonomy test. It separates source records from grouped claims and keeps each claim's response-evidence stage (0–4) visible in the claim list. Its existing fixture has 41 topic indicators: −1 when no claim is found in the selected sample, 0 when claims are context/outcome only, and +1 when at least one claim documents a positive response. Domain totals sum their topic scores; the radar shows the average topic score (−1 to +1) to account for different topic counts across domains. Domain arrows point up/down/side according to the total's sign. Their score colors are red at zero, orange 1–2, yellow 3–4, light green 5–6, dark green 7–8 and blue above 8; a domain with all topics represented is blue, while one with no topics represented is dark red. Topic arrows use the same score-color bands. Domain cards use green/yellow/red for positive/zero/negative totals. Domain cards contain clickable topic indicators that open matching claims. A −1 topic indicates a document coverage gap, not proof of poor country performance; these scores do not measure effectiveness, attribute outcomes to policy, or say a country is on track. Claims remain searchable/filterable by taxonomy field; numeric values stay in their source wording and are not compared across units. This manual pilot is not exhaustive and is not a saved country profile.

**Open the standalone regional dashboard demo** directly at `http://127.0.0.1:8765/design/prototype/regional-dashboard-demo.html`. It is a presentation prototype outside the main app navigation and uses the expanded 53-topic taxonomy: all 16 domains have at least three topics. The regional matrix contains the 18-country inventory; 17 countries with registered documents have small, cited samples from one available NDC, while Kosovo has no registered document and remains unscored. Kazakhstan retains the richer existing selected-page pilot. Sampled pages vary by document and country, including an EU-level submission for Cyprus, so these scores demonstrate the method and are not comparable country-performance ratings. A topic scores −1 when it has no claim in that country's sample, 0 for context/outcome only, and +1 when a positive response claim exists; each domain total sums its topic scores. Country profiles show domain totals, and selecting a domain opens the supporting sample claims and page references. Registered document and catalog-page counts are metadata only; all sample scores are limited to their cited pages.

The [usability review](../verification/usability-review.md) records browser walkthroughs at desktop, tablet and phone widths, before/after screenshots, regression checks and limitations. These were agent-led checks, not participant research or expert validation. The [evidence experience](../../docs/16-evidence-experience.md) specifies counting, filtering, exports and integration boundaries.

## How do I customize and verify it?

Use existing modules and shared `reports.css`. Follow [CUSTOMIZATION.md](../../docs/CUSTOMIZATION.md) for the authoritative sources and effects of each change. Rebuild method assets with `python scripts/method_pack.py build`; rebuild invented UI cases with `python scripts/build_report_design_examples.py` only when those cases change. Verify with `python scripts/check_project.py --local-data` using Python 3.10+ and Node 24+.

The existing Python server, SQLite store and browser modules own the workflow. Hosted sharing and automatic semantic quality certification remain outside the local interface.

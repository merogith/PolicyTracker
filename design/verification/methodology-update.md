# Three country views and transparent methodology

Verified 8 October 2026, preceding revision. The [lean tools update](lean-tools-update.md) supersedes this three-view design with two core views, optional comparison, translation requests and editable methodology.

The regional dashboard now exposes Overview, Policy register, and Alignment & changes. Sources & translations is a supporting utility. The country register's explanatory view explicitly retains quantitative/qualitative commitments, risk context, DRR facets, finance, institutions and monitoring. All ten required narrative section IDs and all thirteen pipeline stage IDs are accounted for in the methodology mapping.

Browser checks:

- Regional dashboard has 18 country entries, 42 documents and zero generated profiles, with three view states per country.
- Kazakhstan's Policy register cell opens the correct country view; its method link opens the relevant content/prompt explanation.
- Method & prompts shows the six preparation steps, shared rules, optional analysis tasks and prepared extensions.
- The Country Profile prompt opens as escaped, readable Markdown with its actual path, output schema and file fingerprint. The browser-downloaded file's SHA-256 matches the repository original byte for byte.
- At the 390px viewport override, the method page and open prompt dialog fit within document/client widths of 375px (scrollbar excluded). The override was reset afterward.

Offline checks passed: exact source/hash catalog for all 19 Markdown files; three-view/10-section/13-stage mapping; operational inventory/prompt checks; 31-operation/38-schema integration consistency; 16-schema/12-route v2 pack; JavaScript syntax; all seven operational request tests. These verify configured contracts, not model output accuracy or a production API.

Artifacts: [regional tracker](three-view-tracker.jpg), [register method](register-method.jpg), [prompt reader](country-prompt-reader.jpg), [mobile method](method-mobile.jpg), [method overview](method-overview.jpg).

No country synthesis, complete translation, model call or publication was performed. The catalog is current configuration, not executed-run provenance. Production runs must archive their actual component bytes/hashes, including any reused extraction dependencies. Existing prototype limitations (in-memory navigation, no live source reader, no model worker/publication service) remain.

# Lean country tools, translations and editable methodology — verification

8 October 2026. Supersedes the preceding three-view prototype verification.

Verified in the local browser:

- One-document North Macedonia shows Overview and Policy register, an enabled translation request action and a disabled comparison action with an explicit reason.
- A translation request preserves the selected source and has no subject filters or briefing question. Saving creates a request only, not a generated translation.
- Kazakhstan's two NDC documents open a valid Documents comparison. Countries mode rejects that same selection and directs users to Documents mode.
- A comparison restricted to Climate → Early warning and disaster preparedness → Flood, with finance deselected, survives browser saving/downloading. The actual exported 1.1.0 request successfully composes through the Python comparison route with those exact settings.
- The knowledge guide shows 11 domains, 40 topics, 27 dimensions and 208 defined values. Searching “conditional” reveals matching category groups and definitions.
- The Configuration page edits Markdown draft text and exports a method package. The exported file passes CLI package validation. No draft was applied to the live method through the browser.
- At 390px viewport overrides, configuration, knowledge and analysis views had document/client widths of 375px with the scrollbar excluded; no page-wide horizontal overflow. The viewport was reset.
- Final browser load captured no console errors. The tab was left on the regional tracker with zero generated profiles.

Automated checks passed:

- 11 request-compiler cases, including one/multiple documents, comparison group rules, topic/sector compatibility and full translation scope.
- Four Python test groups covering configuration references and forbidden paths, definition requirements for new labels, source/translation identity/coverage/immutability and verified edition comparisons.
- Two core views mapped to all 10 narrative sections and all 13 pipeline stages; 20 prompt files match their catalog bytes/hashes.
- Five offline task routes, 18-country/42-document projection, pending-upload rejection and request/model hashing.
- Existing integration and v2 contract checks. These are configuration/schema consistency checks, not deployed-service security or model accuracy tests.

The translation persistence test initially hit the Windows sandbox's restricted temporary-directory permissions. It passed using a normal, uniquely named workspace test directory with a verified cleanup boundary.

Current screenshots: [regional tracker](lean-regional-tracker.jpg), [comparison setup](lean-comparison.jpg), [label guide](label-guide.jpg), [method editor](method-editor.jpg), [mobile knowledge](knowledge-mobile.jpg), [mobile analysis](analysis-mobile-lean.jpg).

Not implemented: full source-processing and model workers, account/API execution in the app, authenticated upload/reader/storage services, production method activation, persistent user histories and automatic publication. Translation artifacts were tested with synthetic inputs only. No actual country translation, analytical report or API spend was produced.

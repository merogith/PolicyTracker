# Regional tracker and operational-request verification

8 October 2026, preceding revision. The [three-view methodology update](methodology-update.md) supersedes its six-view navigation and adds the prompt reader. This record preserves verification of the operational request flow. Older screenshots remain historical design references.

Verified in the local browser:

- Regional inventory shows 18 country entries, 42 documents and zero published profiles. Missing-document filter isolates Kosovo; country search finds Kazakhstan.
- A country document-count link opens the actual inventory metadata list; a risk/DRR cell opens the correct Country Profile section with an honest Not generated state.
- A one-country country-comparison request is rejected. Adding Armenia to Kazakhstan produces two explicit groups and five source IDs.
- Saved comparison retains the Flood filter, selected output dimensions and High effort, with separate request history and no changes to published-profile counts.
- Delivery-gap task exposes different checks. Unchecking finance removes its promised check from the preview. Enabling proposals adds a separate proposal requirement. The preview shows the chosen country and hazard.
- The primary navigation now contains Regional tracker and Source documents. Analysis tools is visibly secondary. The Generation plan shows the 18-country/17-supplied/42-file scope and explicitly does not execute inference.
- At 390px viewport, both the regional page and analysis form have matching document/client widths (no page-wide horizontal overflow). The wide matrix scrolls inside its own region. Normal viewport was restored.
- No console errors were captured after the final load. The deliverable tab remains on the regional tracker.

Seven request-compiler tests passed. Offline checks validated the four prompt routes, request hashing, pending-upload rejection, inventory projection and automatic-publication batch plan without `expert_acceptance`. Integration consistency checks passed for 31 operations, 38 schemas and 10 default read-only MCP tools. The existing v2 pack check passed during this revision. None of these checks proves real model accuracy or a production API/security implementation.

Screenshots: [regional dashboard](regional-dashboard.jpg), [mobile regional page](regional-mobile.jpg), [country section](country-feature-status.jpg), [operational controls](operational-analysis.jpg), [generation plan](generation-plan.jpg). Country/operational screenshots captured before the final label cleanup may retain the earlier Prime/ad hoc wording; the regional and generation-plan screenshots show the current naming.

Still unimplemented: actual model execution, complete English translations and Country Profiles, authenticated source upload/reading, automatic publication service, persistent histories, full URL/back-button state, and comprehensive accessibility verification. No source PDF or credential is served by the preview.

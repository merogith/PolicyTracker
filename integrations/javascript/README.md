# Reference client and reusable tracker

## Shared source-record presentation

`evidence-model.mjs` is a pure presentation adapter over a frozen saved profile and archived codebook. It implements all reader facets, AND/OR filtering, matching target variants, source-record buckets, scoped exports and view-state validation. It never changes evidence or calls a provider.

`policy-tracker.profile = savedProfile` projects source records through this adapter; optional `policy-tracker.view = viewState` applies a validated presentation. Existing `.data` projections remain compatible and display “loaded records (legacy projection)”. No `canonical_commitments` value is used to claim unique commitments. `evidenceopen.detail` includes `recordId`, `evidenceIds`, `releaseId` and legacy compatibility fields. The host resolves authorized evidence for that exact version.

See `docs/16-evidence-experience.md` for counting, exports, state and integration requirements. This component is data-only; it does not grant document access or launch report execution.


Serve these modules from your own application. The client is dependency-free and accepts a fetch implementation. The component uses browser custom elements and Shadow DOM; it makes no requests and holds no credentials.

```javascript
// Server-side example after deploying an authorized PolicyTracker service.
import { PolicyTrackerClient } from './client.mjs';
const client = new PolicyTrackerClient({
  baseUrl: serviceOrigin,
  workspaceId: authorizedWorkspaceId,
  getToken: async () => serverSideServiceToken
});
const pointer = await client.getPrime('KAZ');
if (pointer.data.release_id === null) {
  // Return a specific no-Prime state to the host UI.
} else {
  const result = await client.getDashboard(pointer.data.release_id);
  // Return authorized result.data through your host's authenticated backend.
}
```

```html
<policy-tracker id="tracker"></policy-tracker>
<script type="module">
  import './dashboard-element.js';
  const tracker = document.querySelector('#tracker');
  // dashboard is already authorized, schema-validated data from your backend.
  tracker.data = dashboard;
  tracker.addEventListener('evidenceopen', ({ detail }) => {
    // Fetch authorized evidence using detail.releaseId and detail.evidenceId;
    // then open the host's original/English source view.
  });
</script>
```

Theme variables: `--pt-text`, `--pt-muted`, `--pt-accent`, `--pt-border`, `--pt-surface`, `--pt-soft`. The component searches only loaded rows; use the API's record filters/pagination for a complete large corpus. It uses text nodes for evidence-derived strings and a local table scroll region. The initial version always displays “Performance not assessed”; it does not implement an observations-based performance tracker.

`getPrime`, `getDashboard`, `queryRecords`, `getEvidence`, `startRun` and `selectPrime` are convenience methods. `request` supports the remaining contract routes. Start-run requires an idempotency key, and pointer selection requires the current ETag. The service must still enforce these rules and validate request bodies; this client is not a security boundary. No silent retries or provider fallback are included.

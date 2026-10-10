# Integration and delivery

## Portable website integration

The website and screenshot supplied in the conversation are illustrative references. No integration with or modification of that website is authorized or performed. Its internal code, framework and existing API have not been inspected. The architecture must work for any team's site. [Document 12](12-portable-integration-architecture.md) and the [OpenAPI contract](../integrations/api/openapi.json) supersede the initial endpoint sketches below for new implementation.

Start with a portable export. Your colleague can implement it with any frontend; the first delivery does not require a new production dashboard. Provide a small local inspection tool only after the data contracts and processing are reliable.

```text
exports/releases/<release-id>/
  manifest.json              Content hashes, country, corpus, review and generation metadata
  country-report.json        Brief and structured report sections
  statements.jsonl          Full dated assertions
  commitments.json          Canonical commitments and target variants
  evidence.jsonl            Source passages, locators and provenance
  documents.json            Source registry and relationships
  translations.jsonl        Original-English alignments or manifest of immutable shards
  changes.json              Supported revision/coherence findings
  unresolved.json           Missing context, conflicts and review decisions
  coverage.json             Page/segment dispositions and counts
  policy-tracker.json        Lightweight UI view retaining reference IDs
  report.md                 Human-readable full report
```

CSV equivalents are useful for audit but must quote multiline text and preserve record/evidence IDs. JSON remains canonical; arrays and multi-label memberships should not be flattened destructively. A later PDF rendering is an export of the same validated data, not a separate generation with potentially different facts. Eligibility receipts and optional human audit metadata are separate; human review is not required for publication.

## Proposed HTTP contract

These are proposed interfaces, not deployed endpoints. API versioning is independent from prompt/schema/taxonomy versions. Enforce access in the service before returning documents, snippets or export URLs.

| Endpoint | Behavior |
|---|---|
| `GET /v1/countries/{code}/prime` | One atomic pointer and immutable manifest URL; explicit no-prime/no-evidence states |
| `GET /v1/releases/{id}` | Immutable country bundle metadata and authorized artifact links |
| `GET /v1/countries/{code}/history` | Prime candidates/releases and assignment history |
| `GET /v1/releases/{id}/commitments` | Cursor pagination, topic/status/condition/deadline filters |
| `GET /v1/evidence/{id}` | Original quote, English alignment, PDF page and authorized source link |
| `POST /v1/documents` | Upload session and inspection result; no publication side effects |
| `POST /v1/corpora/{country}/snapshots` | Editor creates curated snapshot after metadata checks |
| `POST /v1/runs` | Starts a Prime candidate or ad hoc job from explicit source IDs and model settings |
| `GET /v1/runs/{id}` | State, coverage, stage counts, cost/usage, errors and resumability |
| `POST /v1/runs/{id}/cancel` | Idempotent cancel; retain completed artifacts |
| `POST /v1/releases/{id}/reviews` | Optional team audit annotation/correction with evidence; never a mandatory publication gate |
| `PUT /v1/countries/{code}/prime` | Signed-in team member pins a validated release or unpins to automatic selection, with expected revision |
| `GET /v1/reports` | Authorized ad hoc history; never merged into Prime history |
| `POST /v1/comparisons` | Explicit country/document/release groups and comparison mode |
| `POST /v1/chat/sessions` | Binds conversation to authorized immutable inputs |
| `POST /v1/chat/sessions/{id}/messages` | Grounded answer; save-report action creates a new ad hoc version |
| `GET /v1/llm/capabilities` | Route-specific model/effort list, verification state and limits |

The current integration contract requires idempotency keys on POST requests and `If-Match` on pointer changes. A stale pointer ETag returns 412; an idempotency/body conflict returns 409. Unknown/unreadable inputs produce explicit errors, not successful empty analysis. Keep validation failures distinct from authentication (401), authorization (403), missing resources (404), invalid semantics (422), quota (429) and service failure (503). Poll compact job status or authorized events; never expose raw provider traces.

An illustrative assignment body is `{ "report_id": "<eligible-release-id>", "expected_revision": 3, "mode": "pinned", "reason": "Keep this version as the shared report" }`. Unpin with `mode: latest_successful` and no report ID; the service chooses the newest eligible release. Server-side automated validation establishes eligibility; the client cannot assert success by sending a boolean. The whole bundle is switched in one transaction. Serve content hashes as ETags and invalidate the pointer cache on assignment.

## Mapping the existing tracker

| Current visible element | New source and rule |
|---|---|
| Label | Short English display label derived from a canonical commitment |
| Target | Structured target rendered with baseline, deadline and condition where needed |
| Domain | Multi-label taxonomy; primary domain optional for legacy sorting |
| Adaptation/Climate label | Display `objective` separately from topic/domain |
| On/off-track arrow | Only a separate reproducible observation-based assessment with validated evidence; initial Prime defaults to not assessed |
| Expanded row | Evidence, original/English, variants, dates, actor, finance, indicators and review flags |
| Country export | Frozen release ID and source manifest included in download |

Do not map `implementation_reported` to `on_track`, or a missing progress assessment to `off_track`. If the existing client only accepts eight domains, return an explicit unsupported-domain list and agree a migration with the engineer; no silent information loss.

## Delivery sequence

| Milestone | Concrete output | Exit condition |
|---|---|---|
| 0. Method and corpus | This architecture, prompt suite, schemas, taxonomy, inventory and honest readiness audit | Country/source scope and method are reviewable |
| 1. Representative pilot | KAZ revisions; Russian UZB table; Moldova planned indicators; CYP EU scope; GEO low-text pages; empty Kosovo | Parsing, translations, attribution and citations pass checks |
| 2. Full report production | 17 substantive country reports plus Kosovo availability entry; evidence/translation coverage; batch manifest | All 42 supplied documents processed or named gaps; incomplete countries labelled; automated eligibility recorded |
| 3. Automatic Prime delivery | Successful reports visible immediately; automatic selection or an existing pin; optional audit tools | Full bundle checks, history isolation and pin/unpin behavior pass; no human approval dependency |
| 4. Analyst workspace | New ad hoc report, comparison, history, grounded chat, provider selection | Isolation, ACL, cancellation and failure tests pass |
| 5. Website integration | JSON/static or API adapter with source drilldown | Existing country page serves correct frozen bundle |
| 6. Optional regional companion | Frozen regional matrix and peer examples | Comparability criteria and exclusions visible |

Milestone 0 does not equal the 18-country full analytical deliverable. The initial inventory/text extraction is preparation, not translation, target extraction or expert review. `README.md` and `05-corpus-readiness.md` record which milestones are actually complete.

## Required edge cases

| Input/event | Required behavior |
|---|---|
| Same PDF uploaded twice | Reuse byte-level artifact; retain each upload's access and source metadata |
| Russian original plus English translation | Keep authority/translation link; one commitment with both evidence occurrences |
| Translation disagrees about a number | Preserve both claims; qualify or omit the disputed headline, show uncertainty and allow optional audit |
| New NDC omits old target | Mark not restated; do not infer repeal or supersession without support |
| Changed baseline/deadline | New target variant; numerical ambition may be non-comparable |
| Two countries in one upload | Segment-level attribution and explicit report groups; no folder-based assignment |
| EU NDC in Cyprus folder | EU-wide context; no fabricated Cyprus allocation |
| Ministry strategy/support paper | Ad hoc by default; no direct curated Prime inclusion |
| Sectoral NAP/action-plan annex | Preserve sectoral/annex scope and verified parent relationship |
| Wrong country chosen by user | Show mismatch and request correction before Prime eligibility |
| Blank/scanned/table page | OCR/visual processing and quality flags, never "no commitments" solely from empty extraction |
| No documents | Availability entry with zero evidence; no plausible-looking country narrative |
| Prompt injection in PDF | Treat as quoted data; no tools, instructions or publishing authority |
| Output cutoff/model refusal | Incomplete task and resumable error; no success artifact |
| Lost account access/quota | Pause job with explicit reason; no API/model fallback |
| Duplicate job submission | Reuse existing idempotent task rather than charge twice |
| Older slow run finishes later | Cannot overwrite a newer eligible Prime or an intervening pin via completion time |
| Human corrects target | New evidence/report version, invalidated derived views and traceable correction |
| Ad hoc report deletion | No change to shared Prime or another user's access |

## Handoff boundaries

The starter implementation demonstrates corpus registration, prompt composition, limited evidence checks and a previous approval-based registry. The review reproduced six gaps; the registry/tests/v1 manifest need migration to automatic eligibility and optional audit. Production OCR, full translation, model jobs, secure OAuth UI, multi-user service and hosted integration need the milestone work above. Do not ship a mocked provider, invent an API key, or present an empty report shell as a completed country report. A successful validated report may publish without human audit, with its limitations visible.

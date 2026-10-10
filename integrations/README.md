# Reuse PolicyTracker without adopting its whole interface

## Lean method compatibility

New operational requests use schema 2.0 with `filters.risk_functions`. Current dashboard projections expose `risk_functions` and the single record `kind`; generated API/MCP contracts and fixtures follow the same shape. The reusable browser component also reads archived `drr_phases` without changing their meaning. JSON evidence exports preserve the selected profile's original schema and codebook, including old statement fields. Current-view CSV/HTML retain matching variant scope and overlapping source-record count rules. These are local contracts; no hosted deployment is implied.

The [working local profile routes](../docs/ARCHITECTURE.md#local-http-boundary) are implemented separately from the broad API blueprint below. They support local saved-profile reading and version-specific register CSV exports.

Start with [the portability architecture](../docs/12-portable-integration-architecture.md) and [UI specification](../docs/11-interface-and-user-experience.md).

| Folder | Status |
|---|---|
| `api/openapi.json` | Undeployed OpenAPI 3.1.1 design: 31 operations, API v1, knowledge schema v2 |
| `javascript/client.mjs` | Small working reference HTTP client; no backend or authentication flow |
| `javascript/dashboard-element.js` | Working data-only web component, used by the local prototype |
| `mcp/tools.json` | Ten read-only tool definitions; no running/registered MCP server |
| `mcp/optional-run-tool.json` | Separate optional ad hoc run definition, disabled by default |
| `fixtures/` | Actual inventory metadata plus separately labeled synthetic evidence; no completed national analyses |

Regenerate with `python scripts/build_integration_contracts.py`; verify with `python scripts/check_integration_contracts.py` and `node --test tests/integration-client.test.mjs`. If the environment disallows test-runner subprocesses, `node tests/integration-client.test.mjs` runs the same five tests in-process. The generator imports current v2 schemas and writes the synthetic fixture; do not edit generated files as the source of truth.

The reserved `.invalid` service URL must be replaced after implementing a real authorized service. No credentials, external website edits, deployed API, marketplace plugin or actual country LLM reports are supplied by this integration pack.

The current regional and operational update is described in [document 13](../docs/13-regional-workspace-and-operational-requests.md). `operation-request.mjs` compiles task-specific forms; `optional-operation-tool.json` is a separate disabled connector definition for the same requests. Generate workspace assets before rebuilding the integration contract.

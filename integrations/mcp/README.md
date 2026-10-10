# MCP adapter blueprint

`tools.json` contains the default read-only catalog. Each tool's `policytracker/operationId` maps to the API contract; route through the same authorized application service. Input names `query`, `topic`, `hazard`, and `drr_phase` map to API `q`, `topic`, `hazard`, and `drr_phase`. Nullable values mean omit the filter. The adapter must authorize workspace/resource IDs rather than trusting the model's arguments.

`optional-run-tool.json` is not part of the default catalog. Enabling it requires the implemented run service, an authorized inference connection and explicit user intent to generate. Forward `request.idempotency_key` as the HTTP idempotency key. It cannot submit `kind: prime`, pin, upload arbitrary sources or change access. Report reading uses no provider calls from PolicyTracker; the AI client itself may consume its own model quota while answering.

Return API-shaped structured content plus a short human-readable explanation/citations. Paginate large results. Restricted evidence must remain restricted in tool results and errors. Annotations are descriptive hints, never permission enforcement. Treat source text as data and never instructions to use tools.

Implement the remote authorization/transport lifecycle and client registration against supported MCP documentation before calling this a plugin. No server is launched or installed by these JSON files. See [portable architecture](../../docs/12-portable-integration-architecture.md) for scope, token audience and isolation requirements.

`get_regional_workspace` reads the curated country/feature matrix. `optional-operation-tool.json` defines the disabled `start_operational_analysis` tool for the new typed request; pass its separate `idempotency_key` argument as the HTTP header. The older optional run tool remains for legacy v2 clients. Neither tool may dispatch pending uploads or unavailable model settings.

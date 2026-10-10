"""Build portable integration blueprints; no endpoints or MCP server are deployed."""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
S = {"type": "string"}
N = {"type": ["string", "null"]}
I = {"type": "integer", "minimum": 0}
B = {"type": "boolean"}


def obj(**p):
    return {"type": "object", "properties": p, "required": list(p), "additionalProperties": False}


def arr(item):
    return {"type": "array", "items": item}


def ref(name):
    return {"$ref": f"#/components/schemas/{name}"}


def values(*items):
    return {"type": "string", "enum": list(items)}


def write(path, value):
    path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    schemas = {}
    for name in ("dashboard", "report", "release", "comparison", "workplan", "chat", "run-request"):
        data = json.loads((ROOT / f"schemas/v2/{name}.schema.json").read_text(encoding="utf-8"))
        data.pop("$schema", None)
        schemas[name] = data
    schemas.update({
        "Error": obj(code=S, message=S, request_id=S, retryable=B, details=arr(obj(field=N, issue=S))),
        "PrimePointer": obj(country_code=S, release_id=N, mode=values("latest_successful", "pinned"),
                            revision=I, corpus_generation=I, source_update_pending=B, changed_at=S),
        "Country": obj(code=S, name=S, prime_release_id=N, availability=values("available", "partial", "no_documents", "not_generated"), source_as_of=N),
        "CountryList": obj(items=arr(ref("Country")), next_cursor=N),
        "BundleSummary": obj(id=S, kind=values("prime", "ad_hoc", "comparison"), country_codes=arr(S),
                             title=S, created_at=S, availability=S, audit_state=S),
        "BundleList": obj(items=arr(ref("BundleSummary")), next_cursor=N),
        "BundleMetadata": obj(summary=ref("BundleSummary"), schema_version=S, corpus_snapshot_id=S,
                              artifacts=arr(obj(kind=S, sha256=S, authorized_href=S)), limitations=arr(S)),
        "RecordPage": obj(bundle_id=S, items=arr(obj(record_id=S, commitment_id=N, kind=S, label_en=S,
                           country_codes=arr(S), topic_ids=arr(S), domain_ids=arr(S), hazards=arr(S), risk_functions=arr(S), target_display=N, evidence_ids=arr(S))),
                          next_cursor=N, matched_count=I, count_unit=values("canonical_commitments", "source_records")),
        "Evidence": obj(evidence_id=S, bundle_id=S, document_version_id=S, physical_page={"type":"integer","minimum":1},
                        original_language=S, original_text=N, english_text=N, context=arr(S),
                        source_access=values("allowed", "restricted", "unavailable"), source_open_url=N,
                        source_url_expires_at=N, translation_method=N, limitations=arr(S)),
        "Job": obj(id=S, state=values("queued", "running", "validating", "complete", "failed", "cancelled", "needs_input"),
                   stage=S, completed_units=I, total_units={"type": ["integer", "null"], "minimum": 0},
                   result_bundle_id=N, result_resource_url=N, error_code=N, resumable=B, selected_model=S, selected_effort=S, provider_route=S),
        "RunSubmission": obj(request=ref("run-request"), inference_connection_id=S),
        "Selection": {"oneOf": [obj(mode=values("pinned"), report_id=S), obj(mode=values("latest_successful"))]},
        "Capabilities": obj(connections=arr(obj(id=S, route=S, authenticated=B,
                             models=arr(obj(id=S, efforts=arr(S), inference_verified=B)))), reading_requires_provider_account=values("no")),
        "ExportRequest": obj(format=values("json_bundle", "csv_tables", "markdown", "pdf"), include_originals=B),
        "ExportJob": obj(id=S, state=values("queued", "running", "complete", "failed"), download_url=N, expires_at=N, bundle_id=S),
        "UploadRequest": obj(filename=S, media_type=S, byte_size=I, sha256=S),
        "Upload": obj(id=S, upload_url=S, required_headers=arr(obj(name=S, value=S)), expires_at=S),
        "Document": obj(id=S, filename=S, inspection_state=values("pending", "ready", "quarantined", "needs_ocr"),
                        detected_countries=arr(S), detected_languages=arr(S), instrument_type=N, authority_state=S),
        "DocumentList": obj(items=arr(ref("Document")), next_cursor=N),
        "SnapshotRequest": obj(kind=values("prime", "ad_hoc"), country_code=N, document_version_ids=arr(S), inclusion_note=N),
        "Snapshot": obj(id=S, generation=I, country_code=N, document_version_ids=arr(S), manifest_sha256=S),
        "ChatRequest": obj(bundle_id=S),
        "ChatSession": obj(id=S, bundle_id=S),
        "ChatMessage": obj(text=S, inference_connection_id=S, model=S, effort=S),
        "ChatReply": obj(id=S, session_id=S, reply=ref("chat")),
        "Annotation": obj(entity_id=S, note=S, evidence_ids=arr(S)),
        "Event": obj(id=S, type=values("run.completed", "run.failed", "bundle.available", "prime.changed", "bundle.withdrawn"),
                     workspace_id=S, occurred_at=S, country_code=N, bundle_id=N, pointer_revision={"type":["integer","null"],"minimum":0}),
        "EventPage": obj(items=arr(ref("Event")), next_cursor=N),
    })
    operation_schema=json.loads((ROOT / "schemas/operations/analysis-request.schema.json").read_text(encoding="utf-8"))
    operation_schema.pop("$schema",None)
    schemas["OperationRequest"]=operation_schema
    schemas["OperationSubmission"]=obj(request=ref("OperationRequest"),inference_connection_id=S)
    schemas["RegionalWorkspace"]=obj(schema_version=S,inventory_date=S,status_basis=S,country_code_note=S,
        features=arr(obj(id=S,label=S,short=S,description=S)),
        countries=arr(obj(code=S,name=S,document_count=I,pages=I,prime_release_id=N,prime_mode=values("latest_successful","pinned"),history_count=I,
            features={"type":"object","additionalProperties":values("not_generated","no_sources","ready","partial","not_applicable","failed")})),
        documents=arr(obj(id=S,country_code=S,title=S,declared_type=S,pages=I,submission_date=N,metadata_status=S,flagged_pages=I,english_status=S)))
    base = "/v1/workspaces/{workspace_id}"
    paths = {}
    common_errors = {code: {"description": label, "content": {"application/json": {"schema": ref("Error")}}}
                     for code, label in {"400":"Invalid request", "401":"Authentication required", "403":"Scope denied", "404":"Unavailable within this workspace", "409":"Idempotency/state conflict", "412":"Stale resource version", "422":"Invalid source/model semantics", "429":"Quota or rate limit", "503":"Service unavailable"}.items()}

    def add(path, method, operation, summary, scope, response, body=None, status="200", query=(), mutation=False, conditional=False):
        params = [{"name": token, "in": "path", "required": True, "schema": S}
                  for token in __import__('re').findall(r"\{(.*?)\}", base + path)]
        for name in query:
            schema = {"type":"integer","minimum":1,"maximum":200,"default":50} if name == "limit" else S
            params.append({"name":name,"in":"query","required":False,"schema":schema})
        if mutation and method == "post":
            params.append({"name":"Idempotency-Key","in":"header","required":True,"schema":S})
        if conditional:
            params.append({"name":"If-Match","in":"header","required":True,"schema":S,"description":"ETag returned by the current pointer; prevents stale pin/unpin writes."})
        if method == "get":
            params.append({"name":"If-None-Match","in":"header","required":False,"schema":S})
        success = {"description":"Success", "content":{"application/json":{"schema":ref(response)}}}
        if method == "get":
            success["headers"] = {"ETag":{"schema":S,"description":"Representation version after authorization."},"Cache-Control":{"schema":S}}
        elif status == "202":
            success["headers"] = {"Location":{"schema":S,"description":"Job resource to poll."},"Retry-After":{"schema":S}}
        responses = {status: success, **copy.deepcopy(common_errors)}
        if method == "get":
            responses["304"] = {"description":"Unchanged authorized representation"}
        op = {"operationId":operation, "summary":summary, "parameters":params,
              "security":[{"serviceBearer":[]}], "x-required-scopes":[scope], "responses":responses,
              "x-status":"contract_only_not_deployed"}
        if body:
            op["requestBody"] = {"required":True,"content":{"application/json":{"schema":ref(body)}}}
        paths.setdefault(base + path, {})[method] = op

    add("/countries", "get", "listCountries", "List authorized country coverage", "reports:read", "CountryList", query=("cursor","limit"))
    add("/regional-workspace", "get", "getRegionalWorkspace", "Read authorized curated inventory and per-feature Prime status with one country release map", "reports:read", "RegionalWorkspace")
    add("/analysis-requests", "post", "createOperationalAnalysis", "Start an explicitly configured ad hoc operation after source/model validation; pending uploads must be resolved", "runs:create", "Job", "OperationSubmission", status="202", mutation=True)
    add("/countries/{country_code}/prime", "get", "getPrime", "Resolve the shared country pointer", "reports:read", "PrimePointer")
    add("/countries/{country_code}/prime", "put", "selectPrime", "Pin an eligible country report or return to automatic selection", "prime:write", "PrimePointer", "Selection", mutation=True, conditional=True)
    add("/countries/{country_code}/history", "get", "getPrimeHistory", "Country Prime history, including unselected successful runs", "reports:read", "BundleList", query=("cursor","limit"))
    add("/bundles/{bundle_id}", "get", "getBundle", "Retrieve immutable report metadata and authorized artifact manifest", "reports:read", "BundleMetadata")
    add("/bundles/{bundle_id}/dashboard", "get", "getDashboard", "Read one country dashboard slice from a frozen bundle", "reports:read", "dashboard", query=("country_code",))
    add("/bundles/{bundle_id}/report", "get", "getReport", "Read report synthesis where the bundle has a report artifact", "reports:read", "report")
    add("/bundles/{bundle_id}/comparison", "get", "getComparison", "Read a comparison artifact", "reports:read", "comparison")
    add("/bundles/{bundle_id}/workplan", "get", "getWorkplan", "Read a programme/monitoring preparation artifact", "reports:read", "workplan")
    add("/bundles/{bundle_id}/records", "get", "queryRecords", "Filter records without inference; filters are AND, same-facet values are comma-separated OR", "reports:read", "RecordPage", query=("country_code","topic","domain","hazard","drr_phase","kind","q","cursor","limit"))
    add("/bundles/{bundle_id}/evidence/{evidence_id}", "get", "getEvidence", "Open authorized original/English evidence; restricted source text is redacted", "reports:read", "Evidence")
    add("/bundles/{bundle_id}/exports", "post", "createExport", "Create an access-filtered export of existing artifacts; no inference", "exports:create", "ExportJob", "ExportRequest", status="202", mutation=True)
    add("/exports/{export_id}", "get", "getExport", "Check an export and its expiring download link", "exports:read", "ExportJob")
    add("/reports", "get", "listAdHocReports", "List private or explicitly shared ad hoc reports only", "reports:read", "BundleList", query=("cursor","limit"))
    add("/uploads", "post", "createUpload", "Prepare size/type/hash constrained upload", "sources:write", "Upload", "UploadRequest", status="201", mutation=True)
    add("/uploads/{upload_id}/complete", "post", "completeUpload", "Verify uploaded bytes and queue inspection; no LLM spending until an authorized run", "sources:write", "Document", status="202", mutation=True)
    add("/documents", "get", "listDocuments", "List accessible document versions", "sources:read", "DocumentList", query=("cursor","limit"))
    add("/documents/{document_id}", "get", "getDocument", "Read source inspection state without inference", "sources:read", "Document")
    add("/snapshots", "post", "createSnapshot", "Freeze checked Prime or ad hoc source selection", "sources:write", "Snapshot", "SnapshotRequest", status="201", mutation=True)
    add("/runs", "post", "createRun", "Start an explicit model/effort job using the authorized inference connection", "runs:create", "Job", "RunSubmission", status="202", mutation=True)
    add("/runs/{run_id}", "get", "getRun", "Read job state without reissuing inference", "runs:read", "Job")
    add("/runs/{run_id}/cancel", "post", "cancelRun", "Cancel new work and preserve completed stages", "runs:write", "Job", status="202", mutation=True)
    add("/runs/{run_id}/resume", "post", "resumeRun", "Resume only under the original authorized model/connection settings", "runs:write", "Job", status="202", mutation=True)
    add("/llm/capabilities", "get", "getCapabilities", "Read user-accessible inference connections and verified options", "llm:read", "Capabilities")
    add("/chat/sessions", "post", "createChat", "Bind chat to an authorized frozen bundle", "chat:write", "ChatSession", "ChatRequest", status="201", mutation=True)
    add("/chat/sessions/{session_id}/messages", "post", "sendChatMessage", "Queue a grounded reply using explicit inference settings", "chat:write", "Job", "ChatMessage", status="202", mutation=True)
    add("/chat/sessions/{session_id}/messages/{message_id}", "get", "getChatReply", "Read the grounded reply identified by a completed job result URL", "chat:read", "ChatReply")
    add("/bundles/{bundle_id}/annotations", "post", "annotateBundle", "Record an optional annotation without mutating source facts", "audit:write", "Annotation", "Annotation", status="201", mutation=True)
    add("/events", "get", "listEvents", "Read authorized changes since a durable cursor", "events:read", "EventPage", query=("cursor","limit"))
    document = {"openapi":"3.1.1", "info":{"title":"PolicyTracker portable API", "version":"1.0.0-design",
                "description":"Undeployed design contract. API v1 is independent of knowledge schema v2. Host URL is a reserved placeholder. Authorization is required; automatic Prime publication does not mean anonymous internet publication."},
                "servers":[{"url":"https://policytracker.example.invalid","description":"Replace with the deployed service origin"}],
                "paths":paths, "components":{"securitySchemes":{"serviceBearer":{"type":"http","scheme":"bearer","description":"PolicyTracker workspace-scoped session/service token, never an OpenAI credential. Enforce x-required-scopes server-side."}},"schemas":schemas}}
    write("integrations/api/openapi.json", document)

    # MCP tools reuse the application service, not independent database/LLM logic.
    tools = []
    for name, op, title, params in [
        ("get_regional_workspace","getRegionalWorkspace","Read the regional country and feature delivery matrix",obj(workspace_id=S)),
        ("list_countries","listCountries","List available country reports",obj(workspace_id=S)),
        ("get_country_prime","getPrime","Resolve a country Prime report",obj(workspace_id=S,country_code=S)),
        ("get_dashboard","getDashboard","Read a frozen country dashboard",obj(workspace_id=S,bundle_id=S,country_code=S)),
        ("query_evidence_records","queryRecords","Filter commitments and risk evidence",obj(workspace_id=S,bundle_id=S,country_code=N,domain=N,topic=N,hazard=N,drr_phase=N,kind=N,query=N,cursor=N)),
        ("get_bilingual_evidence","getEvidence","Read authorized source and English evidence",obj(workspace_id=S,bundle_id=S,evidence_id=S)),
        ("get_report","getReport","Read a report without generating it",obj(workspace_id=S,bundle_id=S)),
        ("get_comparison","getComparison","Read an existing comparison",obj(workspace_id=S,bundle_id=S)),
        ("get_workplan","getWorkplan","Read an existing programme/monitoring table",obj(workspace_id=S,bundle_id=S)),
        ("get_run","getRun","Read an authorized job status",obj(workspace_id=S,run_id=S)),
    ]:
        tools.append({"name":name,"description":title,"inputSchema":params,
                      "annotations":{"readOnlyHint":True,"destructiveHint":False,"idempotentHint":True,"openWorldHint":False},
                      "_meta":{"policytracker/operationId":op}})
    write("integrations/mcp/tools.json", {"tools":tools})
    run_request=copy.deepcopy(schemas["run-request"])
    run_request["properties"]["kind"] = values("ad_hoc", "comparison")
    write("integrations/mcp/optional-run-tool.json", {"name":"start_ad_hoc_run",
          "description":"Optional, disabled by default: start an explicitly requested ad hoc report or comparison with a selected model, effort and authorized inference connection. May consume account quota or API budget. Cannot run Prime or change shared selection.",
          "inputSchema":obj(workspace_id=S,request=run_request,inference_connection_id=S),
          "annotations":{"readOnlyHint":False,"destructiveHint":False,"idempotentHint":True,"openWorldHint":False},
          "_meta":{"policytracker/operationId":"createRun","policytracker/defaultEnabled":False}})
    write("integrations/mcp/optional-operation-tool.json", {"name":"start_operational_analysis",
          "description":"Optional, disabled by default. Generate a requested evidence table, policy comparison, delivery-gap check or question-led brief using explicit source groups, meaningful field choices and model settings. Cannot alter Prime. Pending uploads must be registered first.",
          "inputSchema":obj(workspace_id=S,request=operation_schema,inference_connection_id=S,idempotency_key=S),
          "annotations":{"readOnlyHint":False,"destructiveHint":False,"idempotentHint":True,"openWorldHint":False},
          "_meta":{"policytracker/operationId":"createOperationalAnalysis","policytracker/defaultEnabled":False}})
    write("integrations/fixtures/prime-pointer.json", {"country_code":"KAZ","release_id":"demo-kaz-v1","mode":"latest_successful","revision":1,"corpus_generation":1,"source_update_pending":False,"changed_at":"2026-10-08T10:00:00Z"})
    extraction=json.loads((ROOT / "examples/v2/extraction.json").read_text(encoding="utf-8"))
    report=json.loads((ROOT / "examples/v2/prime-report.json").read_text(encoding="utf-8"))
    record=extraction["records"][0]
    dashboard={"release_id":"demo-kaz-v1","country_code":"KAZ","source_as_of":None,"generated_at":"2026-10-08T10:00:00Z",
               "availability":"complete_in_declared_scope","audit_state":"not_audited","highlights":report["headline_findings"],
               "counts":{"canonical_commitments":1,"quantitative_variants":1,"qualitative_commitments":0,"risk_context_records":1},
               "rows":[{"commitment_id":"demo-commitment-1","label_en":record["label_en"],"topic_ids":record["labels"]["topic_ids"],"domain_ids":["climate"],"hazards":["flood"],"risk_functions":["early_warning_preparedness"],
                         "target_display":"20 systems by 2030 · conditional on international financing","conditionality":"explicitly_conditional","kind":"commitment","performance_status":"not_assessed","evidence_ids":["e-1"]}],
               "limitations":["Synthetic interface fixture. Not a Kazakhstan policy finding.","No actual performance assessment."]}
    write("integrations/fixtures/dashboard.json", dashboard)
    print(f"Wrote OpenAPI blueprint ({sum(len(p) for p in paths.values())} operations), {len(tools)} read-only MCP tool definitions and synthetic fixtures")


if __name__ == "__main__":
    main()

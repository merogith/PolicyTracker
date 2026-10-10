"""Offline integration consistency checks; not a deployed-service security audit."""
import copy
import json
import re
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main():
    api = read("integrations/api/openapi.json")
    assert api["openapi"] == "3.1.1"
    assert all(".invalid" in s["url"] for s in api["servers"])
    schemas = api["components"]["schemas"]
    for schema in schemas.values():
        Draft202012Validator.check_schema(schema)

    def walk(value):
        if isinstance(value, dict):
            if "$ref" in value:
                target = api
                assert value["$ref"].startswith("#/"), "Unexpected external reference"
                for part in value["$ref"][2:].split("/"):
                    target = target[part.replace("~1", "/").replace("~0", "~")]
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    walk(api)
    operations = {}
    for path, methods in api["paths"].items():
        assert path.startswith("/v1/workspaces/{workspace_id}/")
        for method, operation in methods.items():
            op = operation["operationId"]
            assert op not in operations
            operations[op] = (method, operation)
            assert operation["security"] and operation["x-required-scopes"]
            parameters = {(p["in"], p["name"]): p for p in operation["parameters"]}
            for token in re.findall(r"\{(.*?)\}", path):
                assert parameters[("path", token)]["required"]
            if method == "post":
                assert parameters[("header", "Idempotency-Key")]["required"]
            if op == "selectPrime":
                assert parameters[("header", "If-Match")]["required"]
                assert "412" in operation["responses"]
            if method == "get":
                assert "304" in operation["responses"]
            if "202" in operation["responses"]:
                assert "Location" in operation["responses"]["202"]["headers"]

    catalog = read("integrations/mcp/tools.json")["tools"]
    assert len({t["name"] for t in catalog}) == len(catalog)
    for tool in catalog:
        Draft202012Validator.check_schema(tool["inputSchema"])
        assert operations[tool["_meta"]["policytracker/operationId"]][0] == "get"
        assert tool["annotations"]["readOnlyHint"] is True
    optional = read("integrations/mcp/optional-run-tool.json")
    Draft202012Validator.check_schema(optional["inputSchema"])
    assert optional["_meta"]["policytracker/defaultEnabled"] is False
    assert "prime" not in optional["inputSchema"]["properties"]["request"]["properties"]["kind"]["enum"]
    operational = read("integrations/mcp/optional-operation-tool.json")
    Draft202012Validator.check_schema(operational["inputSchema"])
    assert operational["_meta"]["policytracker/defaultEnabled"] is False
    assert operational["inputSchema"]["properties"]["request"]["properties"]["kind"]["const"] == "ad_hoc"
    assert operational["_meta"]["policytracker/operationId"] in operations

    dashboard = read("integrations/fixtures/dashboard.json")
    pointer = read("integrations/fixtures/prime-pointer.json")
    Draft202012Validator(schemas["dashboard"]).validate(dashboard)
    Draft202012Validator(schemas["PrimePointer"]).validate(pointer)
    assert dashboard["release_id"] == pointer["release_id"]
    assert dashboard["country_code"] == pointer["country_code"]
    assert any("Synthetic" in s for s in dashboard["limitations"])

    # A source locator must never accept an index-0 PDF page.
    evidence_page = Draft202012Validator(schemas["Evidence"]["properties"]["physical_page"])
    assert not evidence_page.is_valid(0) and evidence_page.is_valid(1)
    # No-Prime is an ordinary supported state; a pointer mode typo is not.
    none = copy.deepcopy(pointer)
    none["release_id"] = None
    Draft202012Validator(schemas["PrimePointer"]).validate(none)
    none["mode"] = "latest_finished_regardless_of_pin"
    assert not Draft202012Validator(schemas["PrimePointer"]).is_valid(none)
    read("design/ux-contract.json")
    read("design/tokens.json")
    print(f"Integration checks passed: {len(operations)} operations, {len(schemas)} schemas, {len(catalog)} read tools, optional run isolation, local references and synthetic fixtures.")
    print("This is contract consistency checking, not complete OpenAPI linting or a running-service authorization test.")


if __name__ == "__main__":
    main()

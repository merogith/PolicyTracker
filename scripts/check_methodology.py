"""Check view/pipeline coverage and fidelity of the public prompt catalog."""
import hashlib
import json
from pathlib import Path
from build_methodology import build

ROOT = Path(__file__).resolve().parents[1]
def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def main():
    method = read("integrations/fixtures/methodology.json")
    assert method == build(), "Stale methodology catalog: rebuild it after editing source files"
    pipeline = read("config/v2/pipelines.json")
    product = read("config/product.json")
    region = read("integrations/fixtures/regional-workspace.json")
    view_ids = [v["id"] for v in method["views"]]
    assert view_ids == product["primary_layer"]["profile_sections"] == [v["id"] for v in region["features"]]
    assert view_ids == ["brief", "commitments"]
    assert {s for v in method["views"] for s in v["schema_sections"]} == set(pipeline["features"]["prime"]["required_sections"])
    assert [s for step in method["steps"] for s in step["pipeline_stages"]] == [s["id"] for s in pipeline["stages"]]
    entries = {p["path"]: p for p in method["prompts"]}
    paths = {p.relative_to(ROOT).as_posix() for folder in ("prompts/v2", "prompts/operations") for p in (ROOT/folder).glob("*.md")}
    assert set(entries) == paths and len(entries) == len(method["prompts"])
    for path, p in entries.items():
        raw = (ROOT/path).read_bytes()
        assert p["content"].encode("utf-8") == raw, f"Source bytes differ: {path}"
        assert p["sha256"] == hashlib.sha256(raw).hexdigest()
        if p["route"]:
            spec = pipeline["routes"][p["route"]]
            assert path == "prompts/v2/" + spec["prompt"]
            assert p["schema"] == "schemas/v2/" + spec["schema"] + ".schema.json"
            assert (ROOT/p["schema"]).is_file()
    for group in ("steps", "views", "utilities"):
        for item in method[group]:
            assert all(r in pipeline["routes"] for r in item["routes"])
    assert {p["route"] for p in entries.values() if p["group"] == "country" and p["route"]} == {"triage", "translate", "extract", "reconcile", "prime"}
    assert {p["route"] for p in entries.values() if p["group"] == "utility"} == {"quality", "relabel", "chat"}
    for t in method["analysis_tasks"]:
        assert t["supplement"] in entries
        assert t["route"] in pipeline["routes"]
    print(f"Verified two core views, all 10 report sections and 13 reference stages mapped, active/prepared routes, and {len(entries)} byte-identical Markdown sources/hashes. No inference.")

if __name__ == "__main__":
    main()

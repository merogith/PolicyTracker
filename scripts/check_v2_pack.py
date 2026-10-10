"""Validate generated v2 contracts, routing, DAG and synthetic examples offline."""
import json
from pathlib import Path
from jsonschema import Draft202012Validator
from policytracker.engineering import compose_v2, validate_v2

ROOT = Path(__file__).resolve().parents[1]


def main():
    paths = list((ROOT / "schemas/v2").glob("*.schema.json"))
    for path in paths:
        Draft202012Validator.check_schema(json.loads(path.read_text(encoding="utf-8")))
    config = json.loads((ROOT / "config/v2/pipelines.json").read_text(encoding="utf-8"))
    for route in config["routes"]:
        packed = compose_v2(ROOT, route, {"fixture": True}, {})
        Draft202012Validator.check_schema(packed["schema"])
    seen = set()
    for stage in config["stages"]:
        assert stage["id"] not in seen
        assert set(stage["depends_on"]).issubset(seen), stage["id"]
        if "route" in stage:
            assert stage["route"] in config["routes"]
        seen.add(stage["id"])
    for feature in config["features"].values():
        assert feature["route"] in config["routes"]
    inputs = json.loads((ROOT / "examples/v2/synthetic-input.json").read_text(encoding="utf-8"))
    extraction = json.loads((ROOT / "examples/v2/extraction.json").read_text(encoding="utf-8"))
    for name, schema in [("extraction", "extraction"), ("translation", "translation"), ("prime-report", "report")]:
        output = json.loads((ROOT / f"examples/v2/{name}.json").read_text(encoding="utf-8"))
        errors = validate_v2(ROOT, schema, output, source_segments=inputs["source_segments"],
                             owned_segment_ids=inputs["owned_segment_ids"],
                             required_sections=config["features"]["prime"]["required_sections"],
                             known_evidence_ids={e['local_id'] for e in extraction['evidence']},
                             known_record_ids={r['local_id'] for r in extraction['records']}, known_commitment_ids=set())
        assert not errors, (name, errors)
    taxonomy = json.loads((ROOT / "config/v2/taxonomy.json").read_text(encoding="utf-8"))
    assert len({t["id"] for t in taxonomy["topics"]}) == len(taxonomy["topics"])
    assert len({d["id"] for d in taxonomy["domains"]}) == len(taxonomy["domains"])
    print(f"Validated {len(paths)} v2 schemas, {len(config['routes'])} routes, {len(seen)} pipeline stages and 3 synthetic outputs")
    print("This is offline contract validation, not model inference or a publication receipt.")


if __name__ == "__main__":
    main()

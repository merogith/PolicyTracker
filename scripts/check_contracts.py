"""Check all JSON files, schema validity, taxonomy integrity and prompt routing."""
import json
from pathlib import Path
from jsonschema import Draft202012Validator
from policytracker.prompts import TASKS, compose

ROOT = Path(__file__).resolve().parents[1]


def main():
    for folder in ["schemas", "config", "evals", "data/manifests"]:
        for path in (ROOT / folder).glob("*.json"):
            json.loads(path.read_text(encoding="utf-8"))
    schemas = list((ROOT / "schemas").glob("*.schema.json"))
    for path in schemas:
        Draft202012Validator.check_schema(json.loads(path.read_text(encoding="utf-8")))
    taxonomy = json.loads((ROOT / "config/topic-pool.json").read_text(encoding="utf-8"))
    ids = [x["id"] for x in taxonomy["topics"]]
    assert len(ids) == len(set(ids)) == 40
    for task in TASKS:
        packed = compose(ROOT, task, {"scope": "test-only"}, {})
        Draft202012Validator.check_schema(packed["schema"])
    print(f"Validated {len(schemas)} schemas, 40 unique topics, and {len(TASKS)} prompt routes")


if __name__ == "__main__":
    main()

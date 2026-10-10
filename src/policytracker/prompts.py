"""Compose trusted instructions separately from source data."""
import hashlib
import json
from pathlib import Path

TASKS = {
    "triage": ("01-document-triage.md", "triage"),
    "translate": ("02-translate.md", "translation"),
    "extract": ("03-extract-evidence.md", "extraction"),
    "reconcile": ("04-reconcile.md", "reconciliation"),
    "prime": ("05-prime-country-report.md", "report"),
    "ad_hoc": ("06-ad-hoc-report.md", "report"),
    "compare": ("07-compare.md", "comparison"),
    "chat": ("08-grounded-chat.md", "chat"),
    "quality": ("09-quality-review.md", "quality"),
}


def compose(root: Path, task: str, context: dict, source_data: dict) -> dict:
    """The application, not a source document, chooses task and trusted context."""
    prompt_name, schema_name = TASKS[task]
    paths = [root / "prompts/v1/00-evidence-contract.md", root / "prompts/v1" / prompt_name,
             root / "schemas" / (schema_name + ".schema.json"), root / "config/topic-pool.json"]
    contents = [p.read_text(encoding="utf-8") for p in paths]
    manifest = {p.relative_to(root).as_posix(): hashlib.sha256(c.encode("utf-8")).hexdigest()
                for p, c in zip(paths, contents)}
    instructions = contents[0] + "\n\n" + contents[1]
    payload = {"task_context": context, "taxonomy": json.loads(contents[3]), "untrusted_source_data": source_data}
    return {"instructions": instructions, "input": json.dumps(payload, ensure_ascii=False),
            "schema": json.loads(contents[2]), "component_hashes": manifest,
            "input_hash": hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()}

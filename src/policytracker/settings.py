"""Plain-language settings backed by the existing authoritative method files."""
from __future__ import annotations

import importlib.util
import json
import re
import uuid
from pathlib import Path

from .profiles import encoded, require, sha

DEFAULTS = dict(version="1.0.0", output_language="English", detail="standard", topic_ids=[],
                instructions="", glossary="", ocr_languages="auto", vision_recovery=True, retry_limit=2)


def read_settings(root):
    path = Path(root) / "config/automation.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else dict(DEFAULTS)


def validate_settings(value, topic_ids):
    require(isinstance(value, dict) and set(value) == set(DEFAULTS), "Choose the supported settings fields")
    for key in ("version", "output_language", "instructions", "glossary", "ocr_languages"):
        require(isinstance(value[key], str) and len(value[key]) <= (8000 if key in ("instructions", "glossary") else 80), "Invalid " + key)
    require(value["version"].strip() and value["output_language"].strip(), "Language and version are required")
    require(value["detail"] in ("concise", "standard", "detailed"), "Choose a supported level of detail")
    require(type(value["vision_recovery"]) is bool and type(value["retry_limit"]) is int and 0 <= value["retry_limit"] <= 3, "Invalid recovery limits")
    require(value["ocr_languages"] == "auto" or re.fullmatch(r"[a-zA-Z0-9_]+(?:\+[a-zA-Z0-9_]+)*", value["ocr_languages"]), "Invalid OCR languages")
    require(isinstance(value["topic_ids"], list) and all(isinstance(x, str) for x in value["topic_ids"])
            and len(set(value["topic_ids"])) == len(value["topic_ids"]) and set(value["topic_ids"]) <= set(topic_ids), "Choose existing topics")
    return value


def method_module(root):
    spec = importlib.util.spec_from_file_location("local_method_pack_" + uuid.uuid4().hex, Path(root) / "scripts/method_pack.py")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def settings_view(root):
    root = Path(root)
    value = read_settings(root)
    history, seen = [], set()
    paths = [p for folder in (root / "data/methods").glob("*") if not (folder / "failed.txt").exists()
             for p in (folder / "method-pack.json", folder / "before.json") if p.is_file()]
    for p in sorted(paths, key=lambda p:p.stat().st_mtime, reverse=True):
        try:
            pack = json.loads(p.read_text(encoding="utf-8"))
            file = next(f for f in pack["files"] if f["path"] == "config/automation.json")
            settings = json.loads(file["content"])
            if settings["version"] in seen: continue
            seen.add(settings["version"])
            history.append({"id": p.parent.name + (":before" if p.name == "before.json" else ""), "version": settings["version"], "detail": settings["detail"], "language": settings["output_language"]})
            if len(history) == 20: break
        except (ValueError, KeyError, StopIteration):
            continue
    return {"settings": value, "revision": sha(encoded(value)), "history": history}


def apply_settings(root, payload):
    root = Path(root)
    require(payload.get("revision") == sha(encoded(read_settings(root))), "Settings changed in another window. Reload before saving")
    module = method_module(root)
    pack = module.pack()
    value = payload.get("settings")
    if payload.get("restore"):
        name = payload["restore"]
        require(isinstance(name, str) and re.fullmatch(r"[a-zA-Z0-9-]+(?::before)?", name), "Invalid saved settings version")
        folder = root / "data/methods" / name.split(":")[0]
        require(not (folder / "failed.txt").exists(), "This settings update did not complete")
        saved = json.loads((folder / ("before.json" if name.endswith(":before") else "method-pack.json")).read_text(encoding="utf-8"))
        value = json.loads(next(f["content"] for f in saved["files"] if f["path"] == "config/automation.json"))
    value = {**value, "version": "1.0.0-" + uuid.uuid4().hex[:12]} if isinstance(value, dict) else value
    topics = json.loads((root / "config/v2/taxonomy.json").read_text(encoding="utf-8"))["topics"]
    validate_settings(value, [t["id"] for t in topics])
    next(f for f in pack["files"] if f["path"] == "config/automation.json")["content"] = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    apply_pack(root, pack)
    return settings_view(root)


def apply_pack(root, pack):
    module = method_module(root)
    items = module.validate(pack); module.check_base(pack)
    folder = Path(root) / "data/methods" / (sha(encoded(items)) + "-" + uuid.uuid4().hex)
    folder.mkdir(parents=True)
    (folder / "before.json").write_bytes(encoded(module.pack()))
    (folder / "method-pack.json").write_bytes(encoded(pack))
    originals = {p:(Path(root)/p).read_bytes() for p in items}
    try:
        for p, content in items.items():
            # Package text already preserves each file's exact newline convention.
            (Path(root)/p).write_bytes(content.encode("utf-8"))
        module.rebuild()
    except Exception as exc:
        (folder / "failed.txt").write_text(str(exc), encoding="utf-8")
        for p, raw in originals.items(): (Path(root)/p).write_bytes(raw)
        module.rebuild()
        raise
    return {"saved": True, "version": folder.name}

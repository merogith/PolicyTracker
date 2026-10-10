"""Persist validated translation reading copies; this module does not call an LLM."""
from __future__ import annotations
import hashlib
import html
import json
from pathlib import Path


def save_translation_bundle(output: Path, source_file: Path, segments: list[dict], translated: dict, provenance: dict, *, verified_parallel_segments: dict[str, str] | None = None) -> dict:
    """Create one immutable bilingual bundle after translation has completed.

    Each original segment must supply id, page, language and text. Unreadable
    originals are rejected here; partial translation artifacts require a separate
    partial workflow and must not be labeled complete.
    """
    required=("document_id","translation_id","source_sha256","route","model","effort","prompt_hash")
    if any(not provenance.get(k) for k in required):raise ValueError("Missing translation provenance")
    raw=source_file.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=provenance["source_sha256"]:raise ValueError("Original file hash mismatch")
    ids=[s["id"] for s in segments]
    translated_rows=translated["segments"];by_id={s["segment_id"]:s for s in translated_rows}
    if not ids or len(ids)!=len(set(ids)) or len(by_id)!=len(translated_rows) or set(ids)!=set(by_id):raise ValueError("Translation segment coverage mismatch")
    aligned=[]
    for original in segments:
        row=by_id[original["id"]]
        if row["quality_flags"]:raise ValueError("Resolve translation quality flags before saving a complete reading copy")
        if type(original["page"]) is not int or original["page"]<1:raise ValueError("Invalid physical page locator")
        if not original["text"].strip() or not original["language"] or not row["english_text"].strip():raise ValueError("Blank or unreadable source/translation")
        if row["method"] not in ("identity","official_parallel","machine_translation"):raise ValueError("Unknown translation method")
        if original["language"]=="en" and row["method"]!="identity":raise ValueError("English originals must use identity")
        if row["method"]=="identity" and (original["language"]!="en" or row["english_text"]!=original["text"]):raise ValueError("Identity must preserve an English original exactly")
        if row["method"]=="official_parallel":
            equivalent=(verified_parallel_segments or {}).get(row.get("official_parallel_segment_id"))
            if equivalent is None or row["english_text"]!=equivalent:raise ValueError("Parallel English must exactly match a verified supplied equivalent segment")
        aligned.append({**row,"original_text":original["text"],"original_language":original["language"],"physical_page":original["page"]})
    english="# English reading copy\n\n"+"\n\n".join(f"## Page {s['physical_page']} · {s['segment_id']}\n\n{s['english_text']}" + ("\n\nTranslation notes: " + "; ".join(s["notes"]) if s.get("notes") else "") for s in aligned)
    original_text="\n\n".join(f"[Page {s['physical_page']} · {s['original_language']} · {s['segment_id']}]\n{s['original_text']}" for s in aligned)
    bilingual='<!doctype html><html lang="en"><meta charset="utf-8"><title>Bilingual reading copy</title><style>body{font:16px/1.6 system-ui;max-width:1100px;margin:40px auto;padding:20px}article{border-top:1px solid #ccc;padding:16px 0}.pair{display:grid;grid-template-columns:1fr 1fr;gap:25px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:inherit}@media(max-width:650px){.pair{display:block}}</style><h1>Original and English reading copy</h1>'
    for s in aligned:
        notes="; ".join(s.get("notes", []))
        if notes:bilingual+=f'<p><strong>Translation notes:</strong> {html.escape(notes)}</p>'
        bilingual+=f'<article><h2>Page {s["physical_page"]} · {html.escape(s["segment_id"])}</h2><p>{html.escape(s["method"])} · {html.escape("; ".join(s["quality_flags"]))}</p><div class="pair"><section><h3>Original · {html.escape(s["original_language"])}</h3><pre dir="auto" lang="{html.escape(s["original_language"],quote=True)}">{html.escape(s["original_text"])}</pre></section><section><h3>English</h3><pre>{html.escape(s["english_text"])}</pre></section></div></article>'
    bilingual+='</html>'
    files={"source-original"+source_file.suffix:raw,"original.txt":original_text.encode("utf-8"),"english.md":english.encode("utf-8"),"bilingual.html":bilingual.encode("utf-8"),"alignment.json":json.dumps(aligned,ensure_ascii=False,indent=2).encode("utf-8")}
    manifest={"schema_version":"1.0.0","availability":"complete_in_declared_scope","provenance":provenance,"segments":len(aligned),"languages":sorted({s["original_language"] for s in aligned}),"files":[{"path":name,"sha256":hashlib.sha256(value).hexdigest(),"bytes":len(value)} for name,value in files.items()]}
    # A translation rerun always needs a new directory/version, never overwrite.
    output.mkdir(parents=True,exist_ok=False)
    for name,value in files.items():(output/name).write_bytes(value)
    (output/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return manifest

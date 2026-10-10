"""Register PDFs under data/sources without changing any original file."""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path
import base64
import binascii
import sys

COUNTRIES = {
    "Albania": "ALB", "Armenia": "ARM", "Belarus": "BLR",
    "Bosnia and Herzegovina": "BIH", "Cyprus": "CYP", "Georgia": "GEO",
    "Kazakhstan": "KAZ", "Kosovo": "XKX", "Kyrgyzstan": "KGZ",
    "Moldova": "MDA", "Montenegro": "MNE", "North Macedonia": "MKD",
    "Serbia": "SRB", "Tajikistan": "TJK", "Türkiye": "TUR",
    "Turkmenistan": "TKM", "Ukraine": "UKR", "Uzbekistan": "UZB",
}


def local_availability(root):
    """Report the registered originals that can be used on this installation."""
    root = Path(root).resolve()
    manifest = root / "data/manifests/corpus.json"
    rows = json.loads(manifest.read_text(encoding="utf-8"))["documents"] if manifest.exists() else []
    documents = []
    for doc in rows:
        status, message = "available", "Original PDF is available locally."
        try:
            source = (root / doc["relative_path"]).resolve()
            if not source.is_relative_to(root / "data/sources"):
                status, message = "invalid", "The registered source location is invalid."
            elif not source.is_file():
                status, message = "missing", "Original PDF is not installed. Add the original document to use it."
            else:
                digest = hashlib.sha256()
                with source.open("rb") as handle:
                    for block in iter(lambda: handle.read(1024 * 1024), b""):
                        digest.update(block)
                if digest.hexdigest() != doc["sha256"]:
                    status, message = "changed", "Original PDF differs from the registered fingerprint. Refresh the source inventory."
        except OSError:
            status, message = "unreadable", "Original PDF could not be read. Check its local file permissions."
        documents.append({"document_id": doc["document_id"], "available": status == "available",
                          "status": status, "message": message})
    return {"documents": documents, "registered_count": len(documents),
            "available_count": sum(d["available"] for d in documents)}


def register_document(root, payload):
    """Register an uploaded original in the existing corpus, preserving its filename."""
    from .profiles import require
    from .preparation import run_local
    root = Path(root).resolve()
    country = next((name for name, code in COUNTRIES.items() if code == payload.get("country")), None)
    name, kind, title = payload.get("filename"), payload.get("type"), payload.get("title")
    require(country is not None and kind in ("NDC", "NAP"), "Choose the document's country and NDC/NAP type")
    require(isinstance(name, str) and Path(name).name == name and not any(c in name for c in '\\/:*?"<>|')
            and not any(ord(c) < 32 for c in name)
            and name.lower().endswith('.pdf') and len(name) <= 180 and not Path(name).is_reserved(), "Choose a PDF filename without path characters")
    require(isinstance(title, str) and title.strip() and len(title) <= 250 and '\n' not in title and '\r' not in title, "Enter a document title")
    try:
        raw = base64.b64decode(payload.get("base64", ""), validate=True)
    except (ValueError, TypeError, binascii.Error):
        raise ValueError("The uploaded file could not be read") from None
    require(0 < len(raw) <= 25_000_000 and raw.startswith(b"%PDF-"), "Upload a PDF no larger than 25 MB")
    digest = sha256(raw)
    manifest = root / "data/manifests/corpus.json"
    previous = json.loads(manifest.read_text(encoding="utf-8"))["documents"] if manifest.exists() else []
    existing = next((d for d in previous if d["sha256"] == digest), None)
    if existing:
        require(existing["country_code"] == payload["country"], "This exact document is already registered for another country")
        source = (root / existing["relative_path"]).resolve()
        require(source.is_relative_to(root / "data/sources"), "Invalid registered source location")
        restored = not source.exists()
        if restored:
            # Restore known bytes under their original identity and filename;
            # do not replace metadata with the new upload form's defaults.
            source.parent.mkdir(parents=True, exist_ok=True)
            with source.open("xb") as output: output.write(raw)
            receipt = source.with_name("Source.txt")
            if not receipt.exists():
                text = (f"{existing['title']}\nType: {existing['declared_type']}\nRecord: {existing['document_id']}\n"
                        f"Source: {existing.get('source_url') or 'Local upload'}\nCurrent file SHA-256: {digest}\n")
                if existing.get("submission_date"):
                    text += f"Submission date: {existing['submission_date']}\n"
                receipt.write_text(text, encoding="utf-8")
        else:
            require(source.is_file() and sha256(source.read_bytes()) == digest,
                    "The registered PDF has changed. Restore its original bytes or refresh the source inventory")
        run_local([sys.executable, str(root / "scripts/build_workspace_design.py")], "Document list refresh", 90)
        return {"document": existing, "already_registered": not restored, "restored": restored}
    doc_id = "doc-" + digest[:16]
    folder = root / "data/sources" / country / kind / ("Uploaded - " + doc_id)
    require(folder.resolve().is_relative_to(root / "data/sources") and not folder.exists(), "This source folder already exists")
    folder.mkdir(parents=True)
    with (folder / name).open('xb') as output: output.write(raw)
    (folder / "Source.txt").write_text(f"{title.strip()}\nType: {kind}\nRecord: {doc_id}\nSource: Local upload\nCurrent file SHA-256: {digest}\n", encoding="utf-8")
    result = inventory(root, extract=False, preserve_missing=True)
    run_local([sys.executable, str(root / "scripts/build_workspace_design.py")], "Document list refresh", 90)
    return {"document": next(d for d in result["documents"] if d["document_id"] == doc_id), "already_registered": False}


def dump(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def inventory(root: Path, extract: bool = False, preserve_missing: bool = False) -> dict:
    from pypdf import PdfReader, __version__ as parser_version
    from .preparation import extract_page
    sources = root / "data/sources"
    if not sources.is_dir():
        raise FileNotFoundError(
            f"Source folder not found: {sources}. Place country folders under data/sources/ first."
        )
    manifest_path = root / "data/manifests/corpus.json"
    previous = {}
    if not extract and manifest_path.exists():
        previous = {doc["document_id"]: doc for doc in
                    json.loads(manifest_path.read_text(encoding="utf-8"))["documents"]}
    records, countries = [], []
    for country, code in COUNTRIES.items():
        country_path = sources / country
        items = []
        for pdf in sorted(p for p in country_path.rglob("*") if p.is_file() and p.suffix.lower() == ".pdf"):
            source_path = pdf.with_name("Source.txt")
            source = source_path.read_text(encoding="utf-8-sig") if source_path.exists() else ""
            fields = dict(line.split(": ", 1) for line in source.splitlines() if ": " in line)
            digest = sha256(pdf.read_bytes())
            doc_id = fields.get("Record", "doc-" + digest[:16])
            if not re.fullmatch(r"[A-Za-z0-9_-]+", doc_id):
                raise ValueError(f"Invalid stable document ID in {source_path.relative_to(root)}")
            issues = []
            try:
                reader = PdfReader(pdf)
                if reader.is_encrypted and reader.decrypt("") == 0:
                    raise ValueError("password_protected")
                page_count = len(reader.pages)
                if not page_count:
                    issues.append("pdf_has_no_pages")
            except Exception as exc:
                reader, page_count = None, 0
                issues.append("pdf_unreadable:" + type(exc).__name__)
            if fields.get("Current file SHA-256") != digest:
                issues.append("source_hash_missing_or_mismatch")
            row = {
                "document_id": doc_id, "country_folder": country, "country_code": code,
                "title": source.splitlines()[0] if source else pdf.parent.name,
                "declared_type": fields.get("Type", pdf.relative_to(country_path).parts[0]),
                "submission_date": fields.get("Submission date"), "source_url": fields.get("Source"),
                "relative_path": pdf.relative_to(root).as_posix(), "sha256": digest,
                "pages": page_count, "bytes": pdf.stat().st_size,
                "reporting_party": None, "geographic_scope": None,
                "metadata_status": "unverified", "issues": issues,
            }
            if code == "CYP":
                issues.append("verify_EU_party_scope_do_not_assign_EU_targets_to_Cyprus")
            old = previous.get(doc_id, {})
            if not extract and old.get("sha256") == digest:
                # A metadata-only refresh must retain known parse statistics for
                # unchanged bytes; changed sources need a new extraction.
                row.update({key: old[key] for key in
                            ("text_characters", "flagged_pages", "cyrillic_characters") if key in old})
            if extract:
                pages = []
                for n in range(1, page_count + 1):
                    try:
                        text, flags = extract_page(reader.pages[n - 1])
                    except Exception as exc:
                        text, flags = "", ["parse_failed:" + type(exc).__name__]
                    pages.append({"page_id": f"{doc_id}:p{n}", "pdf_page": n,
                                  "printed_page": None, "text": text,
                                  "text_sha256": sha256(text.encode("utf-8")), "quality_flags": flags})
                row["text_characters"] = sum(len(p["text"]) for p in pages)
                row["flagged_pages"] = [p["pdf_page"] for p in pages if p["quality_flags"]]
                row["cyrillic_characters"] = sum(0x0400 <= ord(c) <= 0x052F for p in pages for c in p["text"])
                dump(root / "data/derived/pages" / f"{doc_id}.json", {
                    "document_id": doc_id, "source_sha256": digest,
                    "parser": {"name": "pypdf", "version": parser_version, "layout_verified": False},
                    "pages": pages,
                })
                txt = "\n\n".join(f"[PDF PAGE {p['pdf_page']} | {p['page_id']}]\n{p['text']}" for p in pages)
                (root / "data/derived/pages" / f"{doc_id}.txt").write_text(txt, encoding="utf-8")
            records.append(row)
            items.append(row)
            print(f"Registered {code} {doc_id}: {row['pages']} pages", flush=True)
        if preserve_missing:
            # Uploading one document must not unregister the originals that a
            # fresh installation has not downloaded or restored yet.
            found = {item["document_id"] for item in items}
            missing = [row for key, row in previous.items() if row["country_code"] == code and key not in found]
            records.extend(missing)
            items.extend(missing)
        countries.append({"country_code": code, "name": country, "documents": len(items),
                          "pages": sum(x["pages"] for x in items),
                          "availability": "supplied" if items else "no_documents_supplied"})
    counts = Counter(r["sha256"] for r in records)
    result = {"schema_version": "1.0.0", "inventory_date": date.today().isoformat(),
              "scope": "supplied files only; not a verification of latest official submissions",
              "country_code_note": "XKX is a local application code, not an assigned ISO 3166-1 alpha-3 code.",
              "countries": countries, "documents": records,
              "totals": {"countries": len(countries), "countries_with_documents": sum(c["documents"] > 0 for c in countries),
                         "documents": len(records), "pages": sum(r["pages"] for r in records),
                         "unique_file_hashes": len(counts)},
              "exact_duplicate_hashes": [h for h, n in counts.items() if n > 1]}
    dump(root / "data/manifests/corpus.json", result)
    return result

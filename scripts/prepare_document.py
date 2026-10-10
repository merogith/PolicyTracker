"""Inspect registered PDF pages or save a reviewed derived transcription/nontext receipt."""
import argparse
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from policytracker.preparation import (inspect_document, open_pdf, ocr_page, source_bytes, review_path,
                                       save_review, validate_review)
from policytracker.profiles import sha, now, require


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("document_id")
    p.add_argument("--page", type=int)
    p.add_argument("--ocr", action="store_true")
    p.add_argument("--language", default="eng")
    p.add_argument("--renderer", default="pdftoppm")
    p.add_argument("--engine", default="tesseract")
    p.add_argument("--text", type=Path, help="Reviewed UTF-8 transcription, including all notes and table cells")
    p.add_argument("--nontext", action="store_true", help="Explicit visual review found no substantive text")
    p.add_argument("--approve-candidate", action="store_true", help="After visual verification, retain the OCR candidate and its provenance")
    p.add_argument("--note", help="Required explanation of the visual check; stop workers before changing receipts")
    p.add_argument("--profiles-path", type=Path, default=ROOT / "data/local-profiles/workspace.sqlite3",
                   help="Database used by your preview, to check for active jobs before saving")
    a = p.parse_args()
    docs = json.loads((ROOT / "data/manifests/corpus.json").read_text(encoding="utf-8"))["documents"]
    doc = next((d for d in docs if d["document_id"] == a.document_id), None)
    require(doc is not None, "Unknown registered document")
    source, raw = source_bytes(ROOT, doc)
    if not (a.ocr or a.text or a.nontext or a.approve_candidate):
        pages = inspect_document(ROOT, doc, raw)
        print(json.dumps([{k: page[k] for k in ("page", "concerns", "needs_review", "review_error")} |
                         {"reviewed": page["review"] is not None} for page in pages], indent=2))
        return
    require(a.page is not None and 1 <= a.page <= len(open_pdf(raw).pages), "Choose a physical page")
    require(sum(bool(x) for x in (a.ocr, a.text, a.nontext, a.approve_candidate)) == 1, "Choose one preparation action")
    if a.profiles_path.exists():
        with sqlite3.connect(a.profiles_path.resolve().as_uri() + "?mode=ro", uri=True) as db:
            if db.execute("SELECT 1 FROM sqlite_master WHERE name='country_jobs'").fetchone():
                require(not any(json.loads(row[0])["status"] in ("running", "stopping")
                                for row in db.execute("SELECT data FROM country_jobs")),
                        "Stop active country/analysis jobs before changing preparation")
    target = review_path(ROOT, doc["sha256"], a.page, candidate=a.ocr)
    require(not target.exists(), "Receipt already exists. Preserve it before a deliberate correction")
    if a.ocr:
        item = ocr_page(ROOT, source, a.page, a.language, renderer=a.renderer, engine=a.engine)
    elif a.approve_candidate:
        require(a.note and a.note.strip(), "Record the visual inspection in --note")
        item = json.loads(review_path(ROOT, doc["sha256"], a.page, candidate=True).read_text(encoding="utf-8"))
        validate_review(ROOT, item, doc["sha256"], a.page, approved=False)
        item.update(reviewed=True, note=a.note, reviewed_at=now())
    else:
        require(a.note and a.note.strip(), "Record the visual inspection and any limitations in --note")
        text = a.text.read_text(encoding="utf-8") if a.text else ""
        require(a.nontext or text.strip(), "Reviewed transcription is empty")
        item = {"source_sha256": doc["sha256"], "page": a.page, "method": "nontext" if a.nontext else "reviewed_text",
                "text": text, "text_sha256": sha(text.encode("utf-8")), "reviewed": True, "note": a.note, "created_at": now()}
    source_bytes(ROOT, doc)  # Recheck after any slow OCR work.
    target = save_review(ROOT, item, candidate=a.ocr)
    print(target.relative_to(ROOT))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError) as exc:
        raise SystemExit(str(exc)) from None

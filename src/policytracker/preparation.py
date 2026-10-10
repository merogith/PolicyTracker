"""Conditional page inspection/OCR receipts. Original PDFs are never rewritten."""
from __future__ import annotations

import csv
import io
import json
import os
import re
import shutil
import subprocess
import uuid
from functools import lru_cache
from pathlib import Path

from .profiles import sha, require, now


def vector_structure(page):
    """Detect substantial painted linework, not text or clipping rectangles.

    Native extraction loses chart labels drawn as outlines and table column
    relationships. Eight long painted rules are a recovery signal, not proof
    of a table. Ignore broad fills (shading/decoration), small logos, single
    borders and clipping paths. Resolve displayed form transforms.
    """
    from pypdf.generic import ContentStream
    minimum = min(float(page.mediabox.width), float(page.mediabox.height)) * .08
    edges = set()

    def combine(current, added):
        a, b, c, d, e, f = current
        g, h, i, j, k, l = added
        return (a*g+c*h, b*g+d*h, a*i+c*j, b*i+d*j, a*k+c*l+e, b*k+d*l+f)

    def walk(stream, resources, matrix, ancestors):
        if stream is None:
            return
        resources = resources.get_object() if resources else {}
        objects = resources.get("/XObject", {})
        objects = objects.get_object() if hasattr(objects, "get_object") else objects
        content = stream if isinstance(stream, ContentStream) else ContentStream(stream, None)
        stack, pending, points, subpaths = [], [], [], []
        first = last = None

        def point(x, y):
            a, b, c, d, e, f = matrix
            return (a*float(x)+c*float(y)+e, b*float(x)+d*float(y)+f)

        def line(start, end):
            if start and sum((a-b)**2 for a, b in zip(start, end)) >= minimum**2:
                pending.append(tuple(sorted((tuple(round(v, 1) for v in start), tuple(round(v, 1) for v in end)))))

        def close_subpath():
            if points:
                bounds = [(min(p[axis] for p in points), max(p[axis] for p in points)) for axis in (0, 1)]
                subpaths.append((list(pending), bounds))
            pending.clear(); points.clear()

        for args, op in content.operations:
            if op == b"q": stack.append(matrix)
            elif op == b"Q": matrix = stack.pop() if stack else matrix
            elif op == b"cm": matrix = combine(matrix, [float(v) for v in args])
            elif op == b"m":
                close_subpath(); first = last = point(*args); points.append(last)
            elif op == b"l":
                end = point(*args); line(last, end); last = end; points.append(end)
            elif op in (b"c", b"v", b"y"):
                points.extend(point(*args[i:i+2]) for i in range(0, len(args), 2)); last = points[-1]
            elif op == b"h" and first:
                line(last, first); last = first
            elif op == b"re":
                close_subpath()
                x, y, w, h = [float(v) for v in args]
                corners = [point(x, y), point(x+w, y), point(x+w, y+h), point(x, y+h)]
                for start, end in zip(corners, corners[1:] + corners[:1]): line(start, end)
                points.extend(corners); first = last = corners[0]
            elif op in (b"S", b"s", b"f", b"F", b"f*", b"B", b"B*", b"b", b"b*", b"n"):
                close_subpath()
                if op != b"n":
                    for lines, bounds in subpaths:
                        if op not in (b"f", b"F", b"f*"):
                            edges.update(lines)
                        elif lines:
                            # A thin filled rule has two long edges; count its
                            # centre once so a few link underlines are not a grid.
                            (x0, x1), (y0, y1) = bounds
                            if 0 < y1-y0 <= 2:
                                y = round((y0+y1)/2, 1); edges.add(((round(x0, 1), y), (round(x1, 1), y)))
                            elif 0 < x1-x0 <= 2:
                                x = round((x0+x1)/2, 1); edges.add(((x, round(y0, 1)), (x, round(y1, 1))))
                subpaths, first, last = [], None, None
            elif op == b"Do":
                obj = objects[args[0]].get_object()
                if obj.get("/Subtype") == "/Form" and id(obj) not in ancestors:
                    transform = combine(matrix, [float(v) for v in obj.get("/Matrix", (1, 0, 0, 1, 0, 0))])
                    walk(obj, obj.get("/Resources", resources), transform, ancestors | {id(obj)})
            if len(edges) >= 8:
                return

    walk(page.get_contents(), page.get("/Resources"), (1, 0, 0, 1, 0, 0), set())
    return len(edges) >= 8


def page_concerns(page, text):
    """Signals for inspection, not a declaration that OCR is necessary/sufficient."""
    concerns = []
    if len(text.strip()) < 30:
        concerns.append("sparse_text")
    if "\ufffd" in text or any(ord(c) < 32 and c not in "\n\r\t" for c in text):
        concerns.append("damaged_text")
    if page.get("/Rotate", 0) % 360:
        concerns.append("rotated_page")
    def images(stream, resources, seen):
        from pypdf.generic import ContentStream
        resources = resources.get_object() if resources else {}
        objects = resources.get("/XObject", {})
        objects = objects.get_object() if hasattr(objects, "get_object") else objects
        if stream is None:
            return False
        content = stream if isinstance(stream, ContentStream) else ContentStream(stream, None)
        if not objects and b"BI" not in content.get_data():
            return False
        for operands, operator in content.operations:
            if operator == b"INLINE IMAGE":
                settings = operands["settings"]
                if settings.get("/W", settings.get("/Width", 0)) * settings.get("/H", settings.get("/Height", 0)) > 200000:
                    return True
            if operator != b"Do":
                continue
            obj = objects[operands[0]].get_object()
            if id(obj) in seen:
                continue
            seen.add(id(obj))
            if obj.get("/Subtype") == "/Image" and obj.get("/Width", 0) * obj.get("/Height", 0) > 200000:
                return True
            if obj.get("/Subtype") == "/Form" and images(obj, obj.get("/Resources", resources), seen):
                return True
        return False
    if images(page.get_contents(), page.get("/Resources"), set()):
        concerns.append("raster_content_may_contain_text")
    # Already flagged pages receive whole-page recovery; do not repeat a second
    # graphics walk merely to add another reason for that same request.
    if not concerns and vector_structure(page):
        concerns.append("vector_content_may_convey_structure")
    return concerns


def extract_page(page):
    """A broken text layer must remain reviewable, including through a receipt."""
    try:
        text = page.extract_text() or ""
    except Exception as exc:
        return "", ["parse_failed:" + type(exc).__name__]
    try:
        return text, page_concerns(page, text)
    except Exception as exc:
        return text, ["inspection_failed:" + type(exc).__name__]


def open_pdf(raw):
    from pypdf import PdfReader
    try:
        reader = PdfReader(io.BytesIO(raw))
        require(not reader.is_encrypted or reader.decrypt("") != 0,
                "This PDF is password protected. Supply an accessible source before preparation.")
        count = len(reader.pages)
        require(count > 0, "This PDF has no pages.")
    except Exception as exc:
        raise ValueError("Cannot open this PDF: " + str(exc)[:300]) from exc
    return reader


@lru_cache(maxsize=8)
def parsed_pages(raw):
    """Reuse parsing across preflight and generation, keyed by exact original bytes.

    Return immutable values; reviews are always read afresh. Keep at most eight
    documents in memory and never trust an editable disk text cache as evidence.
    """
    reader = open_pdf(raw)
    pages = []
    for index in range(len(reader.pages)):
        try:
            text, concerns = extract_page(reader.pages[index])
        except Exception as exc:
            text, concerns = "", ["parse_failed:" + type(exc).__name__]
        pages.append((text, tuple(concerns)))
    return tuple(pages)


def source_bytes(root, doc):
    root = Path(root).resolve()
    source = (root / doc["relative_path"]).resolve()
    require(source.is_relative_to(root / "data/sources") and source.suffix.lower() == ".pdf",
            "Invalid registered source path")
    raw = source.read_bytes()
    require(sha(raw) == doc["sha256"], "Source differs from inventory. Refresh the inventory before preparation.")
    return source, raw


def inspect_document(root, doc, raw=None):
    if raw is None:
        _, raw = source_bytes(root, doc)
    require(sha(raw) == doc["sha256"], "Source fingerprint differs")
    pages = []
    for number, (text, concerns) in enumerate(parsed_pages(raw), 1):
        review, error = None, None
        try:
            review = read_review(root, doc["sha256"], number)
        except (ValueError, OSError) as exc:
            error = str(exc)
        pages.append({"page": number, "text": text, "concerns": list(concerns),
                      "review": review, "review_error": error,
                      "needs_review": bool(error or (concerns and review is None))})
    return pages


class PreparationRequired(ValueError):
    def __init__(self, documents):
        self.documents = documents
        count = sum(len(d["pages"]) for d in documents)
        errors = sum(bool(d.get("error")) for d in documents)
        summary = (f"{count} source page{'s' if count != 1 else ''} in {len(documents)} "
                         f"document{'s' if len(documents) != 1 else ''} {'needs' if count == 1 else 'need'} review. "
                         if count else "Source documents could not be prepared. ")
        super().__init__(summary + (f"{errors} document{'s' if errors != 1 else ''} could not be read or contain no substantive text. " if errors else "") +
                         "Review source pages, then start a new run. Resuming this run cannot resolve the missing reviews.")


def review_path(root, source_hash, page, *, candidate=False):
    require(isinstance(source_hash, str) and re.fullmatch(r"[0-9a-f]{64}", source_hash) is not None and type(page) is int and page > 0,
            "Invalid source fingerprint or physical page")
    folder = Path(root).resolve() / "data/derived/reading" / source_hash
    require(folder.resolve().is_relative_to(Path(root).resolve() / "data/derived/reading"), "Invalid review folder")
    target = folder / f"page-{page}{'.candidate' if candidate else ''}.json"
    require(target.resolve().is_relative_to(folder.resolve()), "Invalid review path")
    return target


def review_paths(root, source_hash):
    return sorted(p for p in (Path(root) / "data/derived/reading" / source_hash).glob("page-*.json") if p.stem.removeprefix("page-").isdigit())


def read_review(root, source_hash, page):
    path = review_path(root, source_hash, page)
    if not path.exists():
        return None
    item = json.loads(path.read_text(encoding="utf-8"))
    validate_review(root, item, source_hash, page)
    return item


def validate_review(root, item, source_hash, page, *, approved=True):
    require(isinstance(item, dict), "Page review must be an object")
    require(item.get("source_sha256") == source_hash and type(item.get("page")) is int and item["page"] == page,
            "Page review does not match this source/page")
    if approved:
        require(item.get("reviewed") is True and isinstance(item.get("note"), str) and item["note"].strip(),
                "Page review needs approval and an inspection note")
    require(item.get("method") in ("reviewed_text", "ocr", "nontext"), "Unknown page preparation method")
    require(isinstance(item.get("text"), str) and sha(item["text"].encode("utf-8")) == item.get("text_sha256"), "Page review text hash differs")
    require(bool(item["text"].strip()) != (item["method"] == "nontext"), "Text/nontext review is inconsistent")
    if item["method"] == "ocr" or "ocr_tsv" in item or "review_image" in item:
        base = review_path(root, source_hash, page).parent.resolve()
        for path_key, hash_key in (("review_image", "render_sha256"), ("ocr_tsv", "tsv_sha256")):
            require(isinstance(item.get(path_key), str), "OCR provenance is missing " + path_key)
            artifact = (Path(root) / item[path_key]).resolve()
            require(artifact.is_relative_to(base) and artifact.is_file(), "OCR artifact is missing or outside this source folder")
            require(sha(artifact.read_bytes()) == item.get(hash_key), "OCR artifact hash differs: " + path_key)


def save_review(root, item, *, candidate=False):
    """Publish only a complete receipt, atomically, without replacing an old one."""
    require(isinstance(item, dict), "Page review must be an object")
    target = review_path(root, item.get("source_sha256"), item.get("page"), candidate=candidate)
    validate_review(root, item, item["source_sha256"], item["page"], approved=not candidate)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_name(".review-" + uuid.uuid4().hex + ".tmp")
    try:
        with temp.open("x", encoding="utf-8") as output:
            json.dump(item, output, ensure_ascii=False, indent=2)
            output.flush()
            os.fsync(output.fileno())
        try:
            os.link(temp, target)
        except FileExistsError:
            raise ValueError("Receipt already exists. Preserve it before a deliberate correction; start a new run after changing preparation.") from None
    finally:
        temp.unlink(missing_ok=True)
    return target


def run_local(command, label, timeout=180):
    try:
        return subprocess.run(command, check=True, timeout=timeout, capture_output=True)
    except subprocess.TimeoutExpired:
        raise ValueError(f"{label} timed out. The original is unchanged; inspect this page manually.") from None
    except subprocess.CalledProcessError as exc:
        details = (exc.stderr or b"").decode("utf-8", errors="replace").strip()[:500]
        raise ValueError(f"{label} failed. {details}") from None
    except OSError as exc:
        raise ValueError(f"{label} could not start: {exc}") from exc


def find_ocr_engine(root, engine="tesseract"):
    found = shutil.which(engine)
    if found or engine != "tesseract":
        return found
    # Optional project-local native dependency, alongside the Python environment.
    local = Path(root) / ".venv/ocr" / ("tesseract.exe" if os.name == "nt" else "tesseract")
    return str(local) if local.is_file() else None


def render_page(root, source, page, *, renderer="pdftoppm", ocr=False):
    require(shutil.which(renderer) is not None, "Install Poppler or pass --renderer with its executable")
    raw = source.read_bytes()
    require(type(page) is int and 1 <= page <= pdf_page_count(source), "Choose a physical page in this PDF")
    folder = review_path(root, sha(raw), page).parent / ("ocr-" + uuid.uuid4().hex if ocr else "previews")
    require(folder.resolve().is_relative_to(review_path(root, sha(raw), page).parent.resolve()), "Invalid render folder")
    folder.mkdir(parents=True, exist_ok=True)
    prefix = folder / f"page-{page}"
    target = prefix.with_suffix(".png")
    require(target.resolve().is_relative_to(folder.resolve()), "Invalid page preview path")
    if ocr or not target.exists():
        render_prefix = prefix if ocr else folder / ("render-" + uuid.uuid4().hex)
        rendered = render_prefix.with_suffix(".png")
        try:
            run_local([renderer, "-f", str(page), "-l", str(page), "-r", "300" if ocr else "150",
                       "-scale-to", "4000" if ocr else "1800", "-singlefile", "-png", str(source), str(render_prefix)], "PDF rendering")
            require(source.read_bytes() == raw, "Source changed during rendering. Refresh the inventory.")
            require(rendered.is_file() and rendered.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"), "PDF renderer did not produce a readable page image")
            if not ocr:
                os.replace(rendered, target)
        finally:
            if not ocr:
                rendered.unlink(missing_ok=True)
    require(source.read_bytes() == raw, "Source changed during rendering. Refresh the inventory.")
    require(target.is_file() and target.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"), "PDF renderer did not produce a readable page image")
    return target


def ocr_page(root, source, page, language, *, renderer="pdftoppm", engine="tesseract", psm=3):
    """Run local OCR for a selected page, leaving an unapproved derived candidate."""
    require(shutil.which(renderer) is not None, "Install Poppler or pass --renderer with its executable")
    engine = find_ocr_engine(root, engine)
    require(engine is not None, "Install Tesseract and the source language pack, or pass --engine")
    require(isinstance(language, str) and re.fullmatch(r"[a-zA-Z0-9_]+(?:\+[a-zA-Z0-9_]+)*", language) is not None,
            "Choose explicit installed OCR language codes")
    available = run_local([engine, "--list-langs"], "OCR language check", 15).stdout.decode("utf-8", errors="replace").splitlines()
    missing = set(language.split("+")) - {line.strip() for line in available}
    require(not missing, "Missing installed OCR language packs: " + ", ".join(sorted(missing)))
    raw = source.read_bytes()
    prefix = render_page(root, source, page, renderer=renderer, ocr=True).with_suffix("")
    result = run_local([engine, str(prefix.with_suffix(".png")), "stdout", "-l", language, "--psm", str(psm), "tsv"], "OCR")
    prefix.with_suffix(".tsv").write_bytes(result.stdout)
    rows = list(csv.DictReader(io.StringIO(result.stdout.decode("utf-8")), delimiter="\t"))
    require(all(set(("text", "conf", "block_num", "par_num", "line_num")) <= set(row) for row in rows), "OCR returned malformed word data")
    words = [r for r in rows if (r["text"] or "").strip()]
    require(words, "OCR recovered no words. Inspect the image and record a nontext review only if appropriate")
    lines = {}
    for row in words:
        lines.setdefault((row["block_num"], row["par_num"], row["line_num"]), []).append(row["text"])
    text = "\n".join(" ".join(line) for line in lines.values())
    require(source.read_bytes() == raw, "Source changed during OCR. Refresh the inventory.")
    version = run_local([engine, "--version"], "OCR version check", 15).stdout.decode("utf-8", errors="replace").splitlines()
    return {"source_sha256": sha(raw), "page": page, "method": "ocr", "text": text,
            "text_sha256": sha(text.encode("utf-8")), "reviewed": False, "note": "",
            "created_at": now(), "ocr_language": language, "ocr_engine": version[0] if version else "unknown",
            "ocr_low_confidence_words": sum(float(r["conf"]) < 80 for r in words),
            "render_sha256": sha(prefix.with_suffix(".png").read_bytes()), "tsv_sha256": sha(result.stdout),
            "review_image": prefix.with_suffix(".png").relative_to(root).as_posix(),
            "ocr_tsv": prefix.with_suffix(".tsv").relative_to(root).as_posix(),
            "warning": "Inspect all words, numbers, columns and footnotes against the render. OCR confidence does not certify completeness."}


def pdf_page_count(source):
    try:
        return len(open_pdf(source.read_bytes()).pages)
    except ValueError as original:
        if not shutil.which("pdfinfo"):
            raise original
        output = run_local(["pdfinfo", str(source)], "PDF structure recovery", 30).stdout.decode("utf-8", errors="replace")
        match = re.search(r"^Pages:\s*(\d+)", output, re.M)
        require(match is not None and int(match[1]) > 0, "No readable pages in this PDF")
        return int(match[1])


def alternate_text(source, page):
    if not shutil.which("pdftotext"):
        return ""
    return run_local(["pdftotext", "-f", str(page), "-l", str(page), "-layout", "-enc", "UTF-8", str(source), "-"],
                     "Alternative text extraction", 45).stdout.decode("utf-8", errors="replace").replace("\f", "").strip()


RECOVERY_SCHEMA = {"type": "object", "additionalProperties": False,
    "properties": {"status": {"type": "string", "enum": ["complete", "partial", "nontext", "unreadable"]},
                   "text": {"type": "string"}, "notes": {"type": "array", "items": {"type": "string"}}},
    "required": ["status", "text", "notes"]}


def recovery_check(item):
    from jsonschema import Draft202012Validator
    errors = list(Draft202012Validator(RECOVERY_SCHEMA).iter_errors(item))
    require(not errors, "Invalid recovered page: " + "; ".join(e.message for e in errors))
    require(bool(item["text"].strip()) == (item["status"] in ("complete", "partial")), "Recovered text and page status disagree")
    require(item["status"] not in ("partial", "unreadable") or item["notes"], "Incomplete pages need coverage notes")
    require("\ufffd" not in item["text"], "Recovery contains damaged characters")


def recover_page(root, doc, page, settings, vision=None):
    """Automatic recovery; never creates or impersonates a human review receipt."""
    source, _ = source_bytes(root, doc)
    number, native, concerns = page["page"], page["text"], page["concerns"]
    artifacts, notes = [], []
    if page.get("review"):
        review = page["review"]
        return {"status": "nontext" if review["method"] == "nontext" else "complete", "text": review["text"],
                "method": "existing_review", "notes": [review["note"]], "artifacts": []}
    if not concerns and not page.get("review_error"):
        return {"status": "complete", "text": native, "method": "native", "notes": [], "artifacts": []}
    if page.get("review_error"):
        notes.append("An invalid previous review was ignored; this page was processed again automatically.")
    alternate, ocr = "", None
    try:
        alternate = alternate_text(source, number)
    except ValueError as exc:
        notes.append(str(exc))
    engine = find_ocr_engine(root)
    if engine:
        try:
            language = settings.get("ocr_languages", "auto")
            if language == "auto":
                installed = run_local([engine, "--list-langs"], "OCR languages", 15).stdout.decode("utf-8", errors="replace").splitlines()[1:]
                available = [x.strip() for x in installed if re.fullmatch(r"[A-Za-z0-9_]+", x.strip()) and x.strip() != "osd"]
                # A scan has no dependable language signal. Do not silently drop
                # a source language merely because its pack sorts after four others.
                language = "+".join(sorted(set(available)))
                require(language, "No OCR text language is installed")
            ocr = ocr_page(root, source, number, language, psm=1)
            artifacts = [{"path": ocr[k], "sha256": ocr[h]} for k, h in (("review_image", "render_sha256"), ("ocr_tsv", "tsv_sha256"))]
        except ValueError as exc:
            notes.append(str(exc))
    text = native or alternate or (ocr["text"] if ocr else "")
    if settings.get("vision_recovery", True) and vision:
        try:
            image = root / ocr["review_image"] if ocr else render_page(root, source, number, ocr=True)
            if not ocr:
                artifacts.append({"path": image.relative_to(root).as_posix(), "sha256": sha(image.read_bytes())})
            result = vision(image, {"native_text": native, "alternative_text": alternate, "ocr_text": ocr["text"] if ocr else "",
                                    "physical_page": number, "source_sha256": doc["sha256"]})
            recovery_check(result)
            # Agreement between independent readings supplies a conservative numeric check.
            numbers = lambda text: set(re.findall(r"(?<!\w)\d+(?:[.,]\d+)*%?", text))
            expected = numbers(native) & numbers(ocr["text"] if ocr else alternate)
            missing = expected - numbers(result["text"])
            if missing and result["status"] in ("complete", "nontext"):
                result = vision(image, {"native_text": native, "alternative_text": alternate,
                    "ocr_text": ocr["text"] if ocr else "", "physical_page": number, "source_sha256": doc["sha256"],
                    "previous_transcription": result, "discrepancies": ["Check omitted numeric tokens: " + ", ".join(sorted(missing))]})
                recovery_check(result)
                missing = expected - numbers(result["text"])
                if missing:
                    result = {**result, "status": "partial" if result["text"].strip() else "unreadable",
                        "notes": result["notes"] + ["Numeric readings still disagree: " + ", ".join(sorted(missing))]}
            source_bytes(root, doc)
            return {**result, "method": "vision", "notes": result["notes"] + notes, "artifacts": artifacts}
        except (ValueError, OSError) as exc:
            notes.append("Visual recovery could not complete: " + str(exc)[:300])
    # A different parser can recover a damaged text layer. Rotation and failed
    # parsing/inspection may conceal graphics that were never safely inspected;
    # alternate text alone cannot certify those pages or an image/table complete.
    if alternate and set(concerns) <= {"damaged_text"} and "\ufffd" not in alternate:
        return {"status": "complete", "text": alternate, "method": "alternate_parser", "notes": notes, "artifacts": artifacts}
    if ocr and not native:
        text = ocr["text"]
    notes.append("Some page content could not be verified automatically; findings use the readable text only.")
    return {"status": "partial" if text.strip() else "unreadable", "text": text, "method": "ocr" if ocr else "native_partial",
            "notes": notes, "artifacts": artifacts}

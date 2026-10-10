# Project data

All original country documents belong in `data/sources/`. Keep the supplied country names and the existing NDC/NAP document folders:

```text
data/
  sources/
    Albania/
      Read me.txt
      NAP/
        Albania National Adaptation Plan - aeb6b3/
          Current.pdf
          Source.txt
      NDC/
        ...
    Kosovo/           No PDFs supplied yet
    Türkiye/
      ...
  manifests/          Inventory, source hashes and preparation plans
  derived/pages/      Extracted page JSON and reading text
  local-profiles/     workspace.sqlite3: saved profiles and run history
```

The folder name identifies the country; NDC/NAP identifies the document type; each document folder keeps its PDF beside its source metadata. Preserve supplied names and record IDs. There is no need for separate folders by year, language or processing status unless the collection grows to need them.

## Adding or updating documents

In **Create analysis → Add a PDF**, choose the country/type and files (up to 25 MB each). The server preserves original filenames and bytes, writes `Source.txt` with a stable ID, registers the files and refreshes the interface. Identical uploads reuse the existing registration. Active jobs must finish before adding files. The manual equivalent is:

1. Put the PDF and its `Source.txt` in `data/sources/<country>/<NDC or NAP>/<document>/`. Use a separate document folder for a new submission so earlier source files remain available. Supported country names are defined in `src/policytracker/inventory.py`.
2. From the project root, run `python -m policytracker.cli inventory --extract` in the project environment. This refreshes `data/manifests/corpus.json` and the local page cache without calling a model. Manifest paths are relative to the project root, including the `data/sources/` prefix.
3. Run `python scripts/build_workspace_design.py` to refresh the country/document list used by the interface. Review inventory warnings and source metadata before generating profiles. A new document is not a generated report.

Run `python scripts/check_project.py --local-data` after updates to catch missing or changed source files, PDFs that were not registered, stale interface metadata and broken paths. A metadata-only `inventory` scan retains existing parse statistics only when the PDF bytes still match; use `--extract` for new or changed documents.

`Source.txt` may include the title on its first line and fields such as `Type`, `Record`, `Source`, `Submission date` and `Current file SHA-256`. These are source declarations, not independently verified facts. Keep metadata with its PDF; do not hand-edit generated manifest paths.

## What to keep

| Folder | Purpose | In Git? |
|---|---|---|
| `sources/` | Original PDFs and accompanying metadata; back up together | No |
| `manifests/` | Generated inventory and preparation metadata | Yes |
| `derived/` | Parsing cache plus reviewed page receipts/OCR artifacts; back up manual reviews | No |
| `local-profiles/` | Persistent profiles, archived evidence and checkpoints; back up | No |
| `private/`, `methods/` | Optional local outputs and saved method versions | No |

A fresh checkout does not include source documents or saved profiles. Restore sources into `data/sources/` before refreshing the inventory. Stop the local server before backing up `data/local-profiles/workspace.sqlite3`. Temporary scripts and logs belong in the project-level `tmp/` folder.

The browser checks registered originals against the files and SHA-256 values on this installation. Missing or changed originals are shown explicitly and cannot be selected for new generation. Uploading the exact bytes of a missing registered original restores its original path, filename and document ID; existing `Source.txt` bytes are preserved. Adding a different PDF keeps registry entries for originals that are not installed yet. A manual inventory refresh instead describes the source collection actually present, so restore the intended collection before using it to replace the registry.

The readiness report and initial batch plan describe the supplied 8 October 2026 corpus. If the collection changes, update the narrative in `scripts/build_readiness.py` before rebuilding those two artifacts.

## Automatic recovery and optional diagnostics

Generate starts automatic reading and recovery; there is no page-review gate. Native readable text is retained. Flagged pages try Poppler extraction, Tesseract orientation-aware OCR and visual transcription using the selected model/route. Rendered images stay under `data/derived/reading/`; raw image/TSV bytes and automatic page records are frozen in SQLite. Complete/nontext recoveries can be reused by exact source, settings, model and recovery-code fingerprints. Partial/unreadable results are retried on a later new run.

Each selected document and every physical page is accounted for. Remaining gaps produce a published partial result with document/page-specific limitations, never a false claim that no policy exists. A wholly unreadable scope fails and preserves the previous published result. Missing credentials remain a connection failure; they do not turn into a page-review requirement.

Install Poppler for page rendering. Tesseract is optional local OCR support, discovered on PATH or at `.venv/ocr/tesseract.exe` (Windows) / `.venv/ocr/tesseract`. Automatic language selection uses all installed text language packs, excluding orientation-only data; Method & output settings can choose explicit codes. Sparse/damaged text, rotation, substantive raster content and substantial drawn table/chart structure trigger recovery. A selectable text layer alone does not establish readable table relationships. Visual recovery can still read a rendered page when local OCR is unavailable. Without rendering/visual recovery, readable fragments remain explicitly partial. Keep native dependencies outside Git.

The legacy `scripts/prepare_document.py DOCUMENT_ID` inspection and reviewed-transcription commands remain available for optional diagnostics. Existing human reviews and unapproved candidates are preserved, never silently overwritten or automatically marked human-approved. Stop active jobs before changing them. Older failed runs keep their original preparation snapshot; choose Generate again for the new automatic workflow. Clipped labels, unknown table cells and uncertain diagram values remain explicit limitations.

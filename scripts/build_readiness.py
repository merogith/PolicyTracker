"""Generate the actual corpus readiness report and nonexecuted batch plan."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    manifest = json.loads((ROOT / "data/manifests/corpus.json").read_text(encoding="utf-8"))
    docs = manifest["documents"]
    lines = ["# Corpus readiness", "", "Inventory date: 8 October 2026. Scope: supplied local files, not a live official-registry audit.", "",
             "42 PDFs contain 2,670 physical pages across 17 populated country folders. Kosovo has no PDFs. All 42 file hashes are distinct.", "",
             "The preparation pass extracted 6,895,473 text characters and flagged 67 pages with fewer than 80 characters. Low text can mean a cover, figure, scan or parser limitation; it is not a confirmed failure count. Character-spaced table text can be problematic even on unflagged pages. No full translation, structured country extraction or expert-reviewed release has been completed.", "",
             "| Country | Code | PDFs | Pages | Low-text pages |", "|---|---|---:|---:|---:|"]
    jobs = []
    for c in manifest["countries"]:
        selected = [d for d in docs if d["country_code"] == c["country_code"]]
        flags = sum(len(d["flagged_pages"]) for d in selected)
        lines.append(f"| {c['name']} | {c['country_code']} | {c['documents']} | {c['pages']} | {flags} |")
        jobs.append({"country_code": c["country_code"], "document_ids": [d["document_id"] for d in selected],
                     "source_hashes": {d["document_id"]: d["sha256"] for d in selected},
                     "status": "needs_corpus_and_parse_validation" if selected else "no_documents_supplied",
                     "profile_id": "initial-prime-astra-xhigh-v1", "published_report_id": None,
                     "required_stages": ["source_scope_validation", "parse_and_ocr_quality", "complete_english_layer", "evidence_extraction_and_labeling", "reconciliation", "country_profile_assembly", "automated_evidence_and_bundle_checks", "automatic_publication_respecting_pin"] if selected else [],
                     "human_review_required": False,
                     "flagged_pages": {d["document_id"]: d["flagged_pages"] for d in selected if d["flagged_pages"]}})
    lines += ["", "## Specific preparation needs", "",
              "- Inspect Georgia first: 30 of its 81 pages have very little extracted text. Do not exclude them without visual review.",
              "- Verify all tables and target-bearing figures; the Kyrgyzstan NDC 3.0 table on physical page 37 has character-spaced extracted text.",
              "- Belarus's newer NDC and the five Uzbekistan sectoral plans contain substantial Cyrillic text; language identification and full English translation remain tasks. Script counts alone do not identify a language.",
              "- Verify the scope of the two EU submissions stored under Cyprus.",
              "- Establish NDC revision families and authoritative language editions before target reconciliation.",
              "- Confirm Moldova's NAP action plan and Uzbekistan's sectoral NAPs are approved members of the intended curated corpus, preserving their scope.",
              "- Kosovo requires a supplied/registered source before a substantive country report can be generated.",
              "", "## Generated artifacts", "",
              "`data/manifests/corpus.json` retains file hashes, URLs, source dates, identifiers and relative paths. `data/derived/pages/` contains local page JSON and reading text. These text files are parser outputs, not validated English translations or analytical reports. `data/manifests/initial-batch-plan.json` accounts for all 18 entries and remains nonexecuted.",
              "", "## Next production gate", "",
              "Run a representative extraction/translation pilot with the exact requested Astra/xhigh profile. Verify access through completed inference, inspect difficult source pages and run automated evidence/coverage checks before processing the frozen full corpus. Human audit or labelled benchmark cases are optional improvements, not a publication requirement. Account execution still needs a verified supported transport; hosted authentication is a separate integration task."]
    (ROOT / "docs/05-corpus-readiness.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    (ROOT / "data/manifests/initial-batch-plan.json").write_text(json.dumps({"status": "planned_not_executed", "countries": jobs}, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(f"Wrote readiness and plan for {len(jobs)} countries")


if __name__ == "__main__":
    main()

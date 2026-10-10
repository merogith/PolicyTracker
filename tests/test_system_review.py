"""Cross-stage regressions using invented passages; never dispatch providers."""
import copy
import json
import shutil
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from policytracker.engineering import numeric_token_in_quote, validate_v2
from policytracker.profiles import CONTEXT_PATHS, ProfileStore, demo_bundle, validate_bundle
from test_method_customization import workspace_test_directory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import method_pack


class EvidenceBoundaries(unittest.TestCase):
    def test_number_substrings_cannot_change_sign_scale_or_exponent(self):
        for quote, raw in [("Target: -20", "20"), ("Target: −20", "20"),
                           ("Target: +20", "20"), ("Target: - 20", "20"),
                           ("Target: 1 500", "500"), ("Target: 1\u202f500", "500"),
                           ("Target: 1e20", "20"), ("Target: 20.5", "20")]:
            with self.subTest(quote=quote):
                bundle = demo_bundle(ROOT)
                bundle["extraction"]["evidence"][1]["quote_original"] = quote
                bundle["extraction"]["records"][0]["targets"][0]["value"].update(raw_token=raw, decimal=raw)
                self.assertIn("numeric token lacks original evidence", validate_v2(ROOT, "extraction", bundle["extraction"]))
        for raw, quote in [("-20", "Target: -20"), ("1 500", "Target: 1 500"),
                           ("20", "20–30 systems"), ("30", "20-30 systems"),
                           ("20", "By 2030, install 20 systems.")]:
            self.assertTrue(numeric_token_in_quote(raw, quote, "dot_decimal"))

    def test_typed_details_need_evidence_even_when_record_has_citations(self):
        bundle = demo_bundle(ROOT)
        bundle["extraction"]["records"][0]["actors"][0]["evidence_ids"] = []
        with self.assertRaisesRegex(ValueError, "typed detail has no evidence"):
            validate_bundle(ROOT, bundle)

    def test_followup_citations_are_joined_to_their_records(self):
        bundle = demo_bundle(ROOT)
        bundle["extraction"]["evidence"].append({"local_id": "unrelated", "segment_id": "s-meta",
            "quote_original": "Synthetic training example only.", "english_segment_id": None, "context_evidence_ids": []})
        finding = copy.deepcopy(bundle["report"]["headline_findings"][0])
        finding["citations"]["evidence_ids"] = ["unrelated"]
        bundle["report"]["followup_questions"] = [finding]
        with self.assertRaisesRegex(ValueError, "unrelated to its cited records"):
            validate_bundle(ROOT, bundle)

    def test_record_export_cannot_omit_inherited_context(self):
        bundle = demo_bundle(ROOT)
        bundle["extraction"]["evidence"].append({"local_id": "header", "segment_id": "s-meta",
            "quote_original": "National scope.", "english_segment_id": None, "context_evidence_ids": []})
        bundle["extraction"]["evidence"][1]["context_evidence_ids"].append("header")
        with self.assertRaisesRegex(ValueError, "omits contextual evidence"):
            validate_bundle(ROOT, bundle)
        bundle["extraction"]["records"][0]["evidence_ids"].append("header")
        validate_bundle(ROOT, bundle)

    def test_profile_label_meanings_survive_current_codebook_edits(self):
        with workspace_test_directory() as folder:
            for path in list(CONTEXT_PATHS) + [f"examples/v2/{name}.json" for name in
                    ("synthetic-input", "translation", "extraction", "prime-report")]:
                target = folder / path
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / path, target)
            with ProfileStore(folder) as store:
                profile = store.complete(store.prepare(demo_bundle(folder)))
                original = profile["validation_codebook"]
                for path in ("config/v2/taxonomy.json", "config/v2/label-guide.json"):
                    (folder / path).write_text("{}", encoding="utf-8")
                self.assertEqual(store.profile(profile["id"])["validation_codebook"], original)
                self.assertEqual(original["basis"], "archived_import_validation_not_generation")

    def test_control_flow_label_values_cannot_bypass_application_rules(self):
        package = method_pack.pack()
        for path, change in [
            ("config/v2/vocabulary.json", lambda v: v["conditionalities"].append("conditional_custom")),
            ("config/v2/label-guide.json", lambda v: next(d for d in v["dimensions"] if d["id"] == "conditionalities")["options"].append(
                {"id": "conditional_custom", "label": "Custom", "definition": "Conditional but no validator handles it"}))]:
            entry = next(f for f in package["files"] if f["path"] == path)
            value = json.loads(entry["content"])
            change(value)
            entry["content"] = json.dumps(value)
        with self.assertRaisesRegex(ValueError, "application semantics"):
            method_pack.validate(package)


if __name__ == "__main__":
    unittest.main()

"""Lossless synthesis bounds and extraction-note provenance; no model calls."""
import copy
import unittest
from pathlib import Path

from policytracker.country_runs import namespace_extraction, synthesis_batches, synthesis_evidence
from policytracker.engineering import read_json
from policytracker.profiles import encoded

ROOT = Path(__file__).resolve().parents[1]


def combine(scopes):
    return {key: [value for scope in scopes for value in scope[key]]
            for key in ("records", "evidence", "coverage", "notes", "issues")}


class SynthesisBatchTests(unittest.TestCase):
    def assert_bounded(self, parts, limit):
        self.assertTrue(parts)
        self.assertTrue(all(len(encoded(synthesis_evidence(part))) <= limit for part in parts))

    def test_many_extraction_notes_stay_with_their_records_without_global_replication(self):
        fixture = read_json(ROOT / "examples/v2/extraction.json")
        scopes = []
        for number in range(100):
            scope = namespace_extraction(fixture, f"b{number}:")
            scope["notes"] = [f"Qualification from extraction {number}: " + "source uncertainty; " * 70]
            scopes.append(scope)
        extraction = combine(scopes)
        before = copy.deepcopy(extraction)
        self.assertGreater(len(encoded(extraction["notes"])), 65000)
        parts = synthesis_batches(extraction, note_scopes=scopes)
        self.assert_bounded(parts, 65000)
        self.assertLess(len(parts), 30)
        self.assertEqual([r["local_id"] for p in parts for r in p["records"]],
                         [r["local_id"] for r in extraction["records"]])
        self.assertEqual({e["local_id"] for p in parts for e in p["evidence"]},
                         {e["local_id"] for e in extraction["evidence"]})
        for part in parts:
            record_ids = {r["local_id"] for r in part["records"]}
            evidence_ids = {e["local_id"] for e in part["evidence"]}
            expected_notes = [note for scope in scopes
                              if record_ids & {r["local_id"] for r in scope["records"]}
                              or evidence_ids & {e["local_id"] for e in scope["evidence"]}
                              for note in scope["notes"]]
            self.assertEqual(part["notes"], expected_notes)
        self.assertEqual(extraction, before)

    def test_cross_scope_quote_context_carries_its_own_notes(self):
        def scope(key, links):
            return {"records": [{"local_id": "r" + key, "evidence_ids": links, "description_en": key * 250}],
                    "evidence": [{"local_id": key, "quote_original": key * 250, "context_evidence_ids": []}],
                    "notes": ["Qualifier " + key], "coverage": [], "issues": []}
        a, b, c = scope("a", ["a", "b"]), scope("b", ["b"]), scope("c", ["c"])
        a["evidence"][0]["context_evidence_ids"] = ["b"]
        first = {**a, "evidence": a["evidence"] + b["evidence"], "notes": a["notes"] + b["notes"]}
        limit = len(encoded(synthesis_evidence(first))) + 10
        parts = synthesis_batches(combine([a, b, c]), limit, note_scopes=[a, b, c])
        self.assert_bounded(parts, limit)
        found = next(p for p in parts if any(r["local_id"] == "ra" for r in p["records"]))
        self.assertEqual({e["local_id"] for e in found["evidence"]}, {"a", "b"})
        self.assertEqual(found["notes"], ["Qualifier a", "Qualifier b"])

    def test_filtered_out_scopes_keep_all_notes_in_bounded_note_only_parts(self):
        first = namespace_extraction(read_json(ROOT / "examples/v2/extraction.json"), "b0:")
        first["notes"] = ["Qualifier for the included record"]
        limit = len(encoded(synthesis_evidence(first))) + 200
        second = namespace_extraction(read_json(ROOT / "examples/v2/extraction.json"), "b1:")
        second["notes"] = [str(n) + "x" * (limit // 2) for n in range(3)]
        # Operation filters retain the archive's qualifications even when their
        # original records do not match the user's filter.
        filtered = {**first, "notes": first["notes"] + second["notes"]}
        before = copy.deepcopy(filtered)
        parts = synthesis_batches(filtered, limit, note_scopes=[first, second])
        self.assert_bounded(parts, limit)
        self.assertEqual([r for p in parts for r in p["records"]], first["records"])
        self.assertEqual([n for p in parts for n in p["notes"]], filtered["notes"])
        self.assertTrue(all(not p["records"] and not p["evidence"] for p in parts[1:]))
        self.assertEqual(filtered, before)

    def test_orphan_quotes_keep_context_and_notes_and_do_not_overrun(self):
        scope = {"records": [], "evidence": [
            {"local_id": "a", "quote_original": "a" * 250, "context_evidence_ids": ["b"]},
            {"local_id": "b", "quote_original": "b" * 250, "context_evidence_ids": []}],
            "notes": ["Scope qualification"], "coverage": [], "issues": []}
        other = {"records": [], "evidence": [], "notes": ["z" * 1000], "coverage": [], "issues": []}
        limit = 1100
        parts = synthesis_batches(combine([scope, other]), limit, note_scopes=[scope, other])
        self.assert_bounded(parts, limit)
        quoted = next(p for p in parts if p["evidence"])
        self.assertEqual({e["local_id"] for e in quoted["evidence"]}, {"a", "b"})
        self.assertEqual(quoted["notes"], scope["notes"])
        self.assertEqual([n for p in parts for n in p["notes"]], scope["notes"] + other["notes"])

    def test_oversized_indivisible_payloads_fail_without_truncation(self):
        fixture = read_json(ROOT / "examples/v2/extraction.json")
        for scoped in (False, True):
            with self.subTest(scoped=scoped), self.assertRaisesRegex(ValueError, "synthesis.*limit"):
                synthesis_batches(fixture, 100, note_scopes=[fixture] if scoped else None)
        notes_only = {"records": [], "evidence": [], "notes": ["x" * 500], "coverage": [], "issues": []}
        with self.assertRaisesRegex(ValueError, "synthesis.*limit"):
            synthesis_batches(notes_only, 100, note_scopes=[notes_only])

    def test_note_scope_mismatch_is_rejected_even_when_payload_is_small(self):
        fixture = read_json(ROOT / "examples/v2/extraction.json")
        wrong = copy.deepcopy(fixture)
        wrong["notes"] = ["Unrelated provenance"]
        with self.assertRaisesRegex(ValueError, "notes.*scope"):
            synthesis_batches(fixture, note_scopes=[wrong])


if __name__ == "__main__":
    unittest.main()

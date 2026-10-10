"""Inventory the organized source tree without relying on private country PDFs."""
import contextlib
import base64
import io
import json
import unittest
from datetime import date
from unittest.mock import patch

from pypdf import PdfWriter

from policytracker.inventory import inventory, local_availability, register_document, sha256
from test_method_customization import workspace_test_directory


class InventoryTests(unittest.TestCase):
    def test_availability_distinguishes_missing_changed_and_invalid_without_rewriting_manifest(self):
        with workspace_test_directory() as root:
            source = root / "data/sources/Albania/NDC/Original.pdf"
            source.parent.mkdir(parents=True)
            source.write_bytes(b"%PDF-invented original")
            manifest = root / "data/manifests/corpus.json"
            manifest.parent.mkdir(parents=True)
            doc = dict(document_id="available", relative_path=source.relative_to(root).as_posix(),
                       sha256=sha256(source.read_bytes()))
            rows = [doc, {**doc, "document_id": "changed", "sha256": "0" * 64},
                    {**doc, "document_id": "missing", "relative_path": "data/sources/missing.pdf"},
                    {**doc, "document_id": "outside", "relative_path": "../outside.pdf"}]
            manifest.write_text(json.dumps({"documents": rows}), encoding="utf-8")
            before = manifest.read_bytes()
            result = local_availability(root)
            self.assertEqual([r["status"] for r in result["documents"]], ["available", "changed", "missing", "invalid"])
            self.assertEqual((result["registered_count"], result["available_count"]), (4, 1))
            self.assertEqual(manifest.read_bytes(), before)
            self.assertEqual(local_availability(root / "empty")["documents"], [])

    def test_upload_restores_known_missing_original_without_changing_identity_or_metadata(self):
        with workspace_test_directory() as root:
            source = root / "data/sources/Albania/NDC/Existing/Original.pdf"
            source.parent.mkdir(parents=True)
            receipt = source.with_name("Source.txt")
            receipt.write_bytes(b"Original title\r\nOriginal historical metadata\r\n")
            raw = b"%PDF-invented original"
            doc = dict(document_id="stable-original-id", relative_path=source.relative_to(root).as_posix(),
                       sha256=sha256(raw), country_code="ALB", title="Original title", declared_type="NDC")
            manifest = root / "data/manifests/corpus.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(json.dumps({"documents": [doc]}), encoding="utf-8")
            before, metadata = manifest.read_bytes(), receipt.read_bytes()
            payload = dict(country="ALB", type="NAP", title="Accidentally changed title", filename="renamed.pdf",
                           base64=base64.b64encode(raw).decode())
            with patch("policytracker.preparation.run_local"):
                restored = register_document(root, payload)
                again = register_document(root, payload)
            self.assertTrue(restored["restored"])
            self.assertFalse(restored["already_registered"])
            self.assertTrue(again["already_registered"])
            self.assertEqual(restored["document"], doc)
            self.assertEqual(source.read_bytes(), raw)
            self.assertEqual(receipt.read_bytes(), metadata)
            self.assertEqual(manifest.read_bytes(), before)
            source.write_bytes(b"changed existing original")
            with self.assertRaisesRegex(ValueError, "registered PDF has changed"):
                register_document(root, payload)
            self.assertEqual(source.read_bytes(), b"changed existing original")

    def test_new_upload_keeps_missing_registered_documents_in_a_fresh_install(self):
        with workspace_test_directory() as root:
            manifest = root / "data/manifests/corpus.json"
            manifest.parent.mkdir(parents=True)
            missing = dict(document_id="stable-missing-id", country_code="ALB", pages=1,
                           relative_path="data/sources/Albania/NDC/Missing/Original.pdf", sha256="a" * 64)
            manifest.write_text(json.dumps({"documents": [missing]}), encoding="utf-8")
            writer = PdfWriter(); writer.add_blank_page(width=100, height=100)
            output = io.BytesIO(); writer.write(output)
            payload = dict(country="ALB", type="NDC", title="New original", filename="New.pdf",
                           base64=base64.b64encode(output.getvalue()).decode())
            with patch("policytracker.preparation.run_local"), contextlib.redirect_stdout(io.StringIO()):
                result = register_document(root, payload)
            current = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(current["totals"]["documents"], 2)
            self.assertIn(missing, current["documents"])
            self.assertEqual((root / result["document"]["relative_path"]).read_bytes(), output.getvalue())
            self.assertEqual(local_availability(root)["available_count"], 1)

    def test_upload_rejects_control_character_filename_before_creating_files(self):
        with workspace_test_directory() as root:
            with self.assertRaisesRegex(ValueError, "filename"):
                register_document(root, dict(country="ALB", type="NDC", title="Original", filename="bad\0.pdf"))
            self.assertFalse((root / "data/sources").exists())

    def test_unreadable_pdf_does_not_hide_other_documents_and_uppercase_extension_is_registered(self):
        with workspace_test_directory() as root:
            folder=root/'data/sources/Albania/NDC/Broken';folder.mkdir(parents=True)
            (folder/'Current.pdf').write_bytes(b'broken source')
            other=root/'data/sources/Albania/NDC/Readable';other.mkdir(parents=True)
            writer=PdfWriter();writer.add_blank_page(width=100,height=100);writer.write(other/'Current.PDF')
            with contextlib.redirect_stdout(io.StringIO()): result=inventory(root,extract=True)
            self.assertEqual(len(result['documents']),2)
            broken,readable=result['documents']
            self.assertEqual(broken['pages'],0)
            self.assertTrue(any(i.startswith('pdf_unreadable:') for i in broken['issues']))
            self.assertEqual(readable['pages'],1)
            self.assertEqual(readable['flagged_pages'],[1])
            cache=json.loads((root/'data/derived/pages'/f"{readable['document_id']}.json").read_text())
            self.assertEqual(cache['pages'][0]['quality_flags'],['sparse_text'])

    def test_source_tree_preserves_ids_types_paths_and_extracted_pages(self):
        with workspace_test_directory() as root:
            document = root / "data/sources/Türkiye/NAP/Synthetic plan/Current.pdf"
            document.parent.mkdir(parents=True)
            writer = PdfWriter()
            writer.add_blank_page(width=100, height=100)
            writer.write(document)
            digest = sha256(document.read_bytes())
            document.with_name("Source.txt").write_text(
                f"Synthetic plan\nRecord: doc-fixture\nCurrent file SHA-256: {digest}\n",
                encoding="utf-8",
            )
            # A scratch or old root-level copy must not become a second source.
            old_copy = root / "Türkiye/NDC/Old copy/Current.pdf"
            old_copy.parent.mkdir(parents=True)
            old_copy.write_bytes(document.read_bytes())

            with contextlib.redirect_stdout(io.StringIO()):
                result = inventory(root, extract=True)

            self.assertEqual(result["totals"]["documents"], 1)
            self.assertEqual(result["totals"]["countries"], 18)
            row = result["documents"][0]
            self.assertEqual(row["document_id"], "doc-fixture")
            self.assertEqual(row["country_code"], "TUR")
            self.assertEqual(row["declared_type"], "NAP")
            self.assertEqual(root / row["relative_path"], document)
            self.assertEqual(row["sha256"], digest)
            self.assertEqual(row["issues"], [])
            cache = json.loads((root / "data/derived/pages/doc-fixture.json").read_text(encoding="utf-8"))
            self.assertEqual(cache["source_sha256"], digest)
            self.assertEqual(cache["pages"][0]["page_id"], "doc-fixture:p1")
            kosovo = next(c for c in result["countries"] if c["country_code"] == "XKX")
            self.assertEqual(kosovo["availability"], "no_documents_supplied")

            with contextlib.redirect_stdout(io.StringIO()):
                refreshed = inventory(root)
            self.assertEqual(refreshed["inventory_date"], date.today().isoformat())
            self.assertEqual(refreshed["documents"], result["documents"])

            writer.add_blank_page(width=100, height=100)
            writer.write(document)
            with contextlib.redirect_stdout(io.StringIO()):
                changed = inventory(root)
            self.assertNotIn("flagged_pages", changed["documents"][0])
            self.assertIn("source_hash_missing_or_mismatch", changed["documents"][0]["issues"])

    def test_missing_source_folder_does_not_replace_existing_manifest(self):
        with workspace_test_directory() as root:
            manifest = root / "data/manifests/corpus.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text('{"existing": true}\n', encoding="utf-8")
            before = manifest.read_bytes()
            with self.assertRaisesRegex(FileNotFoundError, "data/sources"):
                inventory(root)
            self.assertEqual(manifest.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()

"""Regressions for the check command's source-move and missing-data checks."""
import contextlib
import hashlib
import importlib.util
import io
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from test_method_customization import workspace_test_directory

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("check_project", ROOT / "scripts/check_project.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class ProjectPathTests(unittest.TestCase):
    def test_cli_default_workspace_does_not_follow_the_callers_directory(self):
        from policytracker import cli
        with workspace_test_directory() as unrelated:
            with patch.object(Path, "cwd", return_value=unrelated), patch.object(cli, "inventory") as scan:
                scan.return_value = {"totals": {}}
                with patch("sys.argv", ["policytracker", "inventory"]), contextlib.redirect_stdout(io.StringIO()):
                    cli.main()
                scan.assert_called_once_with(ROOT, False)
            with patch.object(cli, "inventory") as scan:
                scan.return_value = {"totals": {}}
                with patch("sys.argv", ["policytracker", "--root", str(unrelated), "inventory"]), contextlib.redirect_stdout(io.StringIO()):
                    cli.main()
                scan.assert_called_once_with(unrelated.resolve(), False)

    def test_web_references_resolve_relative_to_the_file_that_uses_them(self):
        with workspace_test_directory() as root:
            ui = root / "design/prototype"
            client = root / "integrations/javascript"
            ui.mkdir(parents=True)
            client.mkdir(parents=True)
            (ui / "index.html").write_text('<script src="app.js"></script><a href="#main">Skip</a>', encoding="utf-8")
            (ui / "app.js").write_text("import '../../integrations/javascript/client.mjs';", encoding="utf-8")
            module = client / "client.mjs"
            module.write_text("export const version = 1;", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                checker.check_web_paths(root)
            module.unlink()
            with self.assertRaisesRegex(ValueError, "Broken UI reference"):
                checker.check_web_paths(root)

    def fixture(self, root):
        relative = "data/sources/Albania/NDC/Synthetic/Current.pdf"
        path = root / relative
        path.parent.mkdir(parents=True)
        path.write_bytes(b"synthetic path-check bytes")
        manifest = root / "data/manifests/corpus.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text(json.dumps({"documents": [{
            "document_id": "fixture", "country_folder": "Albania", "country_code": "ALB",
            "relative_path": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }]}), encoding="utf-8")
        return path, manifest

    def test_missing_and_changed_source_files_are_reported(self):
        with workspace_test_directory() as root:
            source, _ = self.fixture(root)
            with contextlib.redirect_stdout(io.StringIO()):
                checker.check_paths(root, require_local=True)
            source.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "differs from inventory"):
                checker.check_paths(root, require_local=True)
            source.unlink()
            with self.assertRaisesRegex(ValueError, "Missing or misplaced"):
                checker.check_paths(root, require_local=True)

    def test_sources_outside_the_inventory_or_at_project_root_are_reported(self):
        with workspace_test_directory() as root:
            source, _ = self.fixture(root)
            extra = source.with_name("Unregistered.pdf")
            extra.write_bytes(b"new source")
            with self.assertRaisesRegex(ValueError, "files and inventory differ"):
                checker.check_paths(root)
            extra.unlink()
            (root / "Albania").mkdir()
            with self.assertRaisesRegex(ValueError, "Country folders belong"):
                checker.check_paths(root)

    def test_code_only_checkout_skips_hashes_but_rejects_invalid_manifest_paths(self):
        with workspace_test_directory() as root:
            source, manifest = self.fixture(root)
            source.unlink()
            for folder in (source.parent, source.parent.parent, source.parent.parent.parent, root / "data/sources"):
                folder.rmdir()
            with contextlib.redirect_stdout(io.StringIO()) as output:
                checker.check_paths(root)
            self.assertIn("SKIPPED", output.getvalue())
            with self.assertRaisesRegex(ValueError, "Local sources are missing"):
                checker.check_paths(root, require_local=True)
            value = json.loads(manifest.read_text(encoding="utf-8"))
            value["documents"][0]["relative_path"] = "data/sources/Albania/../../../outside.pdf"
            manifest.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Invalid source path"):
                checker.check_paths(root)


if __name__ == "__main__":
    unittest.main()

"""Local release packages must work without copying an operator's private workspace."""
import importlib.util
import os
from pathlib import Path
import subprocess
import unittest
import zipfile

from test_method_customization import workspace_test_directory

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("package_local", ROOT / "scripts/package_local.py")
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)


class LocalPackageTests(unittest.TestCase):
    def test_package_excludes_local_state_and_preserves_source_bytes(self):
        with workspace_test_directory() as root:
            required = (*package.FILES, "scripts/preview_ui.py", "design/prototype/index.html",
                        "src/policytracker/local_server.py", "design/tokens.json", "config/product.json")
            private = ("data/sources/Albania/NDC/doc/Current.pdf", "data/local-profiles/workspace.sqlite3",
                       "data/derived/pages/original.json", "tmp/server.log", ".env", ".git/config",
                       "config/credentials.json", "config/access-token.json", "src/.env.json",
                       "src/policytracker/__pycache__/cache.pyc")
            for name in (*required, *private):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(("contents: " + name).encode())
            output = root / "pilot.zip"
            count, digest = package.build(root, output)
            self.assertEqual(count, len(required))
            self.assertEqual(len(digest), 64)
            with zipfile.ZipFile(output) as archive:
                self.assertEqual(set(archive.namelist()), {"PolicyTracker/" + name for name in required})
                for name in required:
                    self.assertEqual(archive.read("PolicyTracker/" + name), (root / name).read_bytes())
            before = output.read_bytes()
            with self.assertRaises(FileExistsError):
                package.build(root, output)
            self.assertEqual(output.read_bytes(), before)

    def test_incomplete_checkout_cannot_produce_a_successful_package(self):
        with workspace_test_directory() as root:
            with self.assertRaisesRegex(ValueError, "Required release file"):
                package.build(root, root / "pilot.zip")
            self.assertFalse((root / "pilot.zip").exists())

    @unittest.skipUnless(os.name == "nt", "Windows directory-junction regression")
    def test_internal_junction_cannot_expose_private_json(self):
        with workspace_test_directory() as root:
            private = root / "data/local-profiles"
            private.mkdir(parents=True)
            (private / "saved-profile.json").write_text('{"private": true}', encoding="utf-8")
            source = root / "design"
            source.mkdir()
            junction = source / "private-copy"
            subprocess.run(["cmd", "/c", "mklink", "/J", str(junction), str(private)],
                           check=True, capture_output=True)
            with self.assertRaisesRegex(ValueError, "link or escapes"):
                package.build(root, root / "pilot.zip")
            self.assertFalse((root / "pilot.zip").exists())
            self.assertTrue((private / "saved-profile.json").is_file())


if __name__ == "__main__":
    unittest.main()

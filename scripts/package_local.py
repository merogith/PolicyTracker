"""Build a local pilot source ZIP without sources, credentials or saved user data."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import stat
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FOLDERS = ("src", "scripts", "tests", "config", "prompts", "schemas", "integrations",
           "design", "docs", "examples", "architecture", "evals", "data/manifests")
FILES = ("README.md", "AGENTS.md", "pyproject.toml", ".gitignore", "data/README.md")
SUFFIXES = {".py", ".js", ".mjs", ".css", ".html", ".json", ".md", ".sql"}


def release_files(root: Path) -> list[Path]:
    """An explicit source allowlist; never recursively package the workspace."""
    root = root.resolve()
    def checked(path: Path, boundary: Path) -> None:
        if not path.exists() and not path.is_symlink():
            return
        # Junctions are not symlinks on Windows/Python 3.10. Reject every
        # reparse point before descending, including links back into this root.
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
        if (path.is_symlink() or attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 1024)
                or not path.resolve().is_relative_to(boundary)):
            raise ValueError(f"Release path is a link or escapes its source folder: {path.relative_to(root)}")

    def walk(folder: Path):
        checked(folder, folder.absolute())
        if not folder.is_dir():
            return
        for path in sorted(folder.iterdir()):
            checked(path, folder.absolute())
            if path.name.startswith(".") or path.name in {"__pycache__", "node_modules"}:
                continue
            if path.is_dir():
                yield from walk(path)
            elif path.is_file():
                yield path

    candidates = [root / name for name in FILES]
    for name in FOLDERS:
        folder = root / name
        candidates.extend(walk(folder))
    result = []
    for path in sorted(set(candidates)):
        relative = path.relative_to(root)
        checked(path, root)
        if not path.is_file():
            continue
        if any(part.startswith(".") or part in {"__pycache__", "node_modules"}
               for part in relative.parts) and relative.as_posix() != ".gitignore":
            continue
        if path.suffix not in SUFFIXES and relative.as_posix() not in FILES:
            continue
        if any(word in path.name.lower() for word in ("credentials", "token")) and relative.as_posix() != "design/tokens.json":
            continue
        result.append(path)
    for name in (*FILES, "scripts/preview_ui.py", "design/prototype/index.html", "src/policytracker/local_server.py"):
        if root / name not in result:
            raise ValueError(f"Required release file is missing: {name}")
    return result


def build(root: Path, output: Path) -> tuple[int, str]:
    root = root.resolve()
    files = release_files(root)
    # Exclusive creation prevents silently replacing a package sent to testers.
    with output.open("xb") as target:
        with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in files:
                archive.write(path, "PolicyTracker/" + path.relative_to(root).as_posix())
    return len(files), hashlib.sha256(output.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New ZIP path; its parent must exist")
    args = parser.parse_args()
    try:
        count, digest = build(ROOT, args.output.resolve())
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Package not created: {exc}\n")
    print(f"Created {args.output.resolve()} ({count} source files)\nSHA-256: {digest}")
    print("No original PDFs, credentials, profiles, derived text, logs or virtual environment included.")


if __name__ == "__main__":
    main()

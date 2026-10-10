"""Start the local workspace, including session-bound AI connections."""
import sys
import importlib.util
from pathlib import Path


def check_environment():
    python = r".\.venv\Scripts\python" if sys.platform == "win32" else ".venv/bin/python"
    if sys.version_info < (3, 10):
        raise SystemExit(
            "PolicyTracker requires Python 3.10 or newer. "
            f"This command used Python {sys.version_info.major}.{sys.version_info.minor}.\n"
            f"From the project root, run: {python} scripts/preview_ui.py\n"
            "If the project environment does not exist, create .venv with Python 3.10+ first."
        )
    missing = [name for name in ("pypdf", "jsonschema") if importlib.util.find_spec(name) is None]
    if missing:
        raise SystemExit(
            "PolicyTracker dependencies are missing: " + ", ".join(missing) + ".\n"
            f"From the project root, install them with: {python} -m pip install -e .\n"
            f"Then run: {python} scripts/preview_ui.py"
        )


check_environment()
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from policytracker.local_server import main

if __name__ == "__main__":
    main()

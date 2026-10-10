from __future__ import annotations
import argparse
import json
from pathlib import Path
from .inventory import inventory


def main() -> None:
    parser = argparse.ArgumentParser(description="PolicyTracker local workspace")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2],
                        help="Workspace root (default: this project, independent of the current directory)")
    sub = parser.add_subparsers(dest="command", required=True)
    scan = sub.add_parser("inventory", help="Register PDFs in data/sources and optionally extract text")
    scan.add_argument("--extract", action="store_true")
    profile = sub.add_parser("profile", help="Check, save and export local Country Profiles; no model calls")
    actions = profile.add_subparsers(dest="action", required=True)
    actions.add_parser("demo", help="Save an explicitly synthetic example, outside real country counts")
    load = actions.add_parser("import", help="Freeze and check an existing output bundle")
    load.add_argument("file", type=Path)
    show = actions.add_parser("show", help="Show a country's selected local profile and history")
    show.add_argument("country")
    show.add_argument("--synthetic", action="store_true")
    export = actions.add_parser("export", help="Export a checked immutable profile")
    export.add_argument("id")
    export.add_argument("--format", choices=("json", "csv"), default="json")
    export.add_argument("--output", type=Path, required=True)
    select = actions.add_parser("select", help="Pin --id, or omit --id to follow latest checked inputs")
    select.add_argument("country")
    select.add_argument("--id")
    select.add_argument("--revision", type=int, required=True)
    select.add_argument("--synthetic", action="store_true")
    args = parser.parse_args()
    if args.command == "inventory":
        result = inventory(args.root.resolve(), args.extract)
        print(json.dumps(result["totals"], indent=2))
    elif args.command == "profile":
        from .profiles import ProfileStore, demo_bundle, read_json, register_csv
        try:
            with ProfileStore(args.root) as store:
                if args.action in ("demo", "import"):
                    bundle = demo_bundle(args.root) if args.action == "demo" else read_json(args.file)
                    run_id = store.prepare(bundle)
                    print(f"Prepared {run_id}", flush=True)
                    result = store.complete(run_id)
                    print(json.dumps({"id": result["id"], "synthetic": result["synthetic"],
                                      "status": "local_checks_passed", "model_run": False}, indent=2))
                elif args.action == "show":
                    print(json.dumps(store.country(args.country, args.synthetic), indent=2, ensure_ascii=False))
                elif args.action == "select":
                    print(json.dumps(store.select(args.country, args.id, args.revision, args.synthetic), indent=2))
                elif args.action == "export":
                    value = store.profile(args.id)
                    text = register_csv(value) if args.format == "csv" else json.dumps(value, indent=2, ensure_ascii=False)
                    with args.output.open("x", encoding="utf-8", newline="") as target:
                        target.write(text)
                    print(f"Exported {args.output}")
        except (ValueError, OSError) as exc:
            parser.exit(1, f"Profile not saved/exported: {exc}\n")


if __name__ == "__main__":
    main()

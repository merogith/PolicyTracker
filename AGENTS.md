# Working on PolicyTracker

Keep this a small, understandable local application. Prefer a direct change to the existing code over new services, frameworks, folders or process requirements.

## Where things belong

- Follow the layout in `README.md`. Python code goes in `src/policytracker/`, browser code in `design/prototype/`, reusable commands in `scripts/`, and tests in `tests/`.
- Original country documents live only in `data/sources/<country>/<NDC or NAP>/<document>/`, with their `Source.txt`. Preserve original bytes, filenames and stable document IDs. See `data/README.md` for updates.
- Use the corpus manifest's project-relative paths to find documents. Resolve paths from the project root; do not hardcode drive letters, user directories or the caller's working directory in reusable code.
- Keep generated page text in `data/derived/`, saved profiles/checkpoints in `data/local-profiles/`, and scratch files/logs in `tmp/`. These are local data, not source code. Never rewrite archived evidence or profiles to accommodate a code change.
- Edit authoritative `config/` and `prompts/` files, then regenerate their outputs. `docs/CUSTOMIZATION.md` maps sources to generated files. Do not hand-edit generated catalogs or schemas as the sole fix.
- Update the existing documentation closest to a change. Current behavior is described in `docs/METHODOLOGY.md` and `docs/ARCHITECTURE.md`; older design proposals are background, not mandatory implementation work.

## Change and check

1. Read the relevant code and check the working tree. Preserve unrelated changes and local data.
2. Make the smallest complete fix. When moving a file, update its producers, consumers, imports, links and documentation together. Preserve source fingerprints.
3. Rebuild after method/configuration changes with `python scripts/method_pack.py build`. Refresh inventory/UI assets after source changes as described in the data guide. Stop active country jobs before changing their inputs or method.
4. Run relevant checks. Before handing over a broad change, run `python scripts/check_project.py --local-data` when local sources are present, or omit `--local-data` for a code-only checkout. Use Python 3.10+ from the project environment and Node 24+; pass `--node <executable>` if needed.
5. Add regression coverage for a demonstrated behavior bug. Do not add tests that merely repeat implementation details, or extra maintenance machinery for simple document edits.
6. For UI changes, start `python scripts/preview_ui.py` and exercise affected views. Report what passed, what changed and any remaining limits. Synthetic tests do not establish real AI output quality.

Checks must not make live model calls, change credentials, publish, or generate real country profiles. Those are explicit operating actions, separate from software verification.

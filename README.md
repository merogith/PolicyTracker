# Regional Policy Tracker

Read climate and disaster policy evidence from national climate commitments (NDCs) and adaptation plans (NAPs) across Europe and Central Asia. This is a small local application: one Python server, a SQLite store and a browser interface.

## Find information

- **Regional picture:** see available coverage, find a country and open its profile. Document coverage is distinct from profile availability; neither establishes policy quality.
- **Country profile:** start with the Overview, search the Policy register, inspect Documents & translations, or open Version history. Findings and records link to original and English evidence.
- **Reports & analysis:** choose a task and documents, then **Generate**. Reading, difficult-page recovery, translation, extraction and publication run automatically. Options and saved presets are optional. **Method & output settings** saves defaults or saves and reruns; moderation is available after publication.
- **Guides & settings:** practical help, searchable definitions, current methods and prompts, configuration, AI connection and integration reference.

The supplied inventory has **18 country entries and 42 PDFs**, with documents for 17 countries. Real country profiles have not been generated as part of this update. The sample profile and report demonstrations use clearly labeled invented evidence and never enter country counts. Regional policy themes appear only when saved real profiles are available.

## Local development

The application requires Python 3.10+. Node 24+ is needed only to run the developer checks. Check the interpreter version before creating the environment; Windows may have an older `python` on PATH. For example, with Python 3.12 installed:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python -m pip install -e .
.\.venv\Scripts\python scripts/preview_ui.py
```

Open `http://127.0.0.1:8765/design/prototype/`. The preview serves only allowlisted application assets and session-authorized local data, including registered/archived original PDF downloads. It does not expose the database or credentials. AI connection tests and explicitly started country/analysis jobs make model calls, including image recovery for difficult pages. Browsing, saving settings, filtering and exporting do not. A completed result is published in this local workspace automatically; it can be unpublished without deleting its evidence.

On macOS/Linux use `python3.12 -m venv .venv`, then `.venv/bin/python -m pip install -e .` and `.venv/bin/python scripts/preview_ui.py`. Another installed Python 3.10+ can replace 3.12. Keep the terminal open while using the app; stop it with Ctrl+C after active work finishes. If the port is occupied, pass `--port 8767` and use the printed address. Open the HTTP address, not `index.html` directly.

After updating code, restart the running Python server as well as reloading the browser. An old server can serve new interface files while retaining old API routes. If source availability cannot be checked, the app shows registered counts as **availability unknown** and blocks generation until **Check local sources** succeeds; this does not mean the PDFs are missing. If AI reports a restricted environment, stop the idle preview and launch the project command above from a normal terminal. Then reconnect the existing ChatGPT account in each browser session.

## First local pilot

Extract the complete source ZIP into a writable folder and follow the setup above. Each tester has an independent local workspace. The package contains the document registry and invented examples; original PDFs, credentials and saved country results are distributed separately. The interface checks installed originals and shows missing or changed files explicitly. Browsing the sample requires no AI connection.

1. Open **Explore a sample profile**. Read the Overview, filter the Policy register, inspect bilingual evidence, and export a readable report. These records are invented and excluded from regional findings.
2. To use real documents, choose **Create analysis → Add a PDF**, or restore your original collection under `data/sources/` following the [data guide](data/README.md). Uploading an exact registered original restores its existing identity. New uploads preserve the rest of the registry. A new document is not a generated profile.
3. For generation, configure **Guides & settings → AI connection** with your own account or API key; follow the [connection guide](docs/15-ai-connections.md). Select documents and review the scope before Generate. A connection test and Generate use the chosen provider and can incur usage. Never send credentials with feedback. Install Poppler for difficult-page rendering; optional Tesseract improves local OCR. Missing recovery tools produce explicit coverage limits.
4. Read the first result against its original PDF, especially numbers, conditions, attribution and tables. Check the Policy register, original/English passages, version history and exports. Try an optional analysis and Stop/Resume with a deliberately small scope before longer runs. This is a user acceptance exercise, separate from offline software checks.
5. Send feedback to the person who supplied the package: OS/browser, package filename, country/document IDs, task, expected and actual behavior, and a screenshot or sanitized error. Include the saved run/version ID for an incorrect finding and its source page. Do not attach keys, credential files or the full local database.

For updates, stop the app and back up `data/sources/`, `data/manifests/`, `data/derived/`, `data/local-profiles/` and `data/methods/` together. Keep the prior folder until the new version opens successfully. Restore those folders into the new copy, then run the new copy's `python scripts/build_workspace_design.py` with its project Python to rebuild the document list from your preserved registry. Retain any customized `config/` and `prompts/` separately, and follow [CUSTOMIZATION.md](docs/CUSTOMIZATION.md) before reapplying changes. Existing evidence is never rewritten to match new code; incompatible stopped jobs need a new run.

To prepare a source package after verification:

```powershell
New-Item -ItemType Directory -Force dist
.\.venv\Scripts\python scripts/package_local.py --output dist/PolicyTracker-local-pilot.zip
```

The packager includes allowlisted source, tests, configuration, documentation and registry files, excludes local data, environments, logs, credentials and screenshots, and refuses to overwrite an existing ZIP. It prints a SHA-256 checksum. Test the extracted package before distributing it. Building a ZIP does not upload, publish or contact testers. The [readiness record](design/verification/project-checkup.md) distinguishes offline verification, browser checks and remaining live acceptance work.

Run the complete offline verification:

```powershell
.\.venv\Scripts\python scripts/check_project.py --local-data
```

Pass `--node "path/to/node.exe"` if Node on PATH is older. Omit `--local-data` in a checkout without the source collection. The check verifies source paths and fingerprints, local-store integrity, contracts, browser assets, HTTP serving, and Python/JavaScript tests. It makes no live model calls and generates no real country profiles. Synthetic checks do not establish analytical accuracy.

## Project layout

```text
PolicyTracker/
  src/policytracker/   Python application and local server
  design/             Browser interface (prototype/) and visual verification
  config/             Editable product settings, taxonomy and methodology
  prompts/            Model instructions; v2 is the current pipeline
  schemas/            Input/output contracts
  data/
    sources/          Original documents: country / NDC or NAP / document
    manifests/        Source inventory and preparation plans
    derived/          Regenerable page text and parser output (local)
    local-profiles/   Saved profiles, runs and checkpoints (local)
  docs/               Methodology, architecture and project decisions
  scripts/            Build, check and preview commands
  tests/              Python and JavaScript tests
  integrations/       API contracts, clients and UI fixtures
  examples/           Synthetic examples
  evals/              Evidence checks and design review probes
  architecture/       Reference storage blueprint; not the running database
  tmp/                Local scratch files and logs
```

## Change the application

Follow [AGENTS.md](AGENTS.md). Prefer direct changes in the existing application. The [customization guide](docs/CUSTOMIZATION.md) identifies authoritative sources for wording, labels, view defaults, styling and methods, with build commands and their effects.

After method/configuration edits, stop active country jobs and rebuild:

```powershell
python scripts/method_pack.py build
python scripts/check_project.py --local-data
```

Do not edit generated catalogs as the sole correction. Method changes affect future runs; incompatible jobs cannot resume under a changed fingerprint. Existing profiles retain their original method, labels, evidence and source bytes. A build does not regenerate evidence.

After updating original documents, follow the [data guide](data/README.md): refresh the manifest and derived pages with `python -m policytracker.cli inventory --extract`, then refresh UI inventory assets with `python scripts/build_workspace_design.py`. Original filenames, document IDs and bytes must be preserved.

## Practical and technical reference

| Question | Maintained guide |
|---|---|
| How do I read, explore and verify findings? | [Browser guide](design/prototype/README.md), [evidence reader](docs/16-evidence-experience.md) |
| How are documents turned into profiles? | [Methodology and exact prompt map](docs/METHODOLOGY.md) |
| How do I save, run, resume or export locally? | [Architecture and commands](docs/ARCHITECTURE.md) |
| Which task fits my question? | [Document tools and source requirements](docs/14-lean-tools-translations-and-configuration.md) |
| How do I change wording, labels or presentation? | [Customization](docs/CUSTOMIZATION.md) |
| How do AI connections work? | [Connection guide](docs/15-ai-connections.md) |
| What was actually verified? | [Pipeline checkup and bounded live results](design/verification/project-checkup.md), [usability review and screenshots](design/verification/usability-review.md), [workflow audit](design/verification/workflow-audit.md) |
| What can another application reuse? | [Integration contracts](integrations/README.md), [v2 schemas](schemas/v2/README.md) |

Documents 01–13 and `architecture/` retain earlier product/engineering proposals as background. Current behavior is described by the guides above; those proposals are not additional required implementation work. The legacy v1 composer and registry are reference code, separate from the working local profile runner.

## Data and capability limits

Source documents, derived page text, private runs, local profiles and credentials are excluded from Git. Back up local data separately. Original country files live only in `data/sources/` with their `Source.txt`; see the [data guide](data/README.md).

The local country worker prepares English text, extracts evidence, proposes source relationships, writes the Overview, checks and saves a profile. It preserves prior versions and pins after failure. Optional extraction, comparison, implementation-information review, briefing and translation have separate saved results and exports. Imported profiles retain unverified generation provenance; worker outputs retain actual requests/responses. Automated checks do not imply expert review.

Hosted publication, shared browser preferences, a batch scheduler and evidence-grounded chat are not implemented. Flagged pages use automatic OCR/image recovery; the legacy `scripts/prepare_document.py` remains an optional diagnostic tool. Remaining gaps are disclosed in coverage rather than requiring manual page review. Real provider acceptance and evidence quality require explicit country-by-country evaluation; automated checks do not certify semantic accuracy. No live model calls or real country generation formed part of the usability verification.

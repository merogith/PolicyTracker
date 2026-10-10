# AI connection verification — 9 October 2026

Implemented local runtime: `src/policytracker/ai_runtime.py` and `local_server.py`; UI: `design/prototype/ai-view.js`, `ai.css`, and shared analysis selectors. Setup and boundaries: [AI connections](../../docs/15-ai-connections.md).

## Live ChatGPT results

The existing local ChatGPT account connected through the official Codex app-server protocol. Its catalog exposed seven visible models and their model-specific effort lists; actual usage limits loaded from the account service.

| Selected model | Selected effort | Result | Reported tokens | Elapsed |
|---|---|---|---|---|
| `gpt-6-astra` | `xhigh` | Completed, requested phrase returned | 11,210 input / 7 output | 3.6 s |
| `gpt-6-luna` | `low` | Completed after changing both selectors | 11,210 input / 7 output | 2.1 s |
| `gpt-6-astra` | `xhigh` | Completed on final service; page reloaded while running and polling resumed | 11,210 input / 7 output | 3.1 s |

These were fixed connection prompts; no country PDFs or extracted source text were submitted. Catalog presence and successful connection tests do not establish accuracy of country analysis or future model availability.

## Browser verification

- Connected state, first-use notice, account usage and model/effort choices render correctly.
- Astra / Extra high defaults persisted after reload and populated a new analysis request.
- Selecting Luna / Low in an analysis request changed the preview and saved request. Opening AI settings and returning preserved the draft and three selected source IDs; no analysis was executed.
- Switching to an unconnected API route disables execution and shows separate-billing guidance, API key setup, prompt and output-limit controls.
- A 390 × 844 viewport had no horizontal document overflow; connection cards and model controls stack vertically. Viewport override was reset afterward.
- Final local preview: `http://127.0.0.1:8767/design/prototype/`. Port 8765 already had an older preview, so it was left alone. The new server uses exclusive binding to prevent two Windows processes sharing a listener.

Screenshots: [desktop](ai-connection-desktop.jpg), [mobile](ai-connection-mobile.jpg).

## Automated verification

62 Python tests and 22 JavaScript tests passed. `scripts/check_operations.py` passed. New regressions cover API dispatch, supported-effort validation, missing/expired credentials, failed/incomplete responses, terminal turn status, early notifications, account changes, matching/cancelled/expired sign-in, reload recovery, session isolation, CSRF/Origin/Host checks, static-file boundaries and exclusive port binding.

Python 3.12 and Node 24 from the bundled workspace runtime were used; existing local `tmp/python-deps` supplied jsonschema. JavaScript tests used `--test-isolation=none` because process spawning is restricted in the tool sandbox. The local live server needed ordinary access to the user's Codex state directory and was started through the approved permission mechanism.

## Remaining verification dependencies

No OpenAI API key was supplied. API behavior was verified using explicit fake transports and HTTP boundary tests; real API billing/inference remains unverified until a key is connected. The existing ChatGPT account was used, so completing a new browser OAuth ceremony or switching to another account was not exercised live; the protocol lifecycle has automated coverage. Document analysis, translation workers and automatic country publication remain separate pending work.

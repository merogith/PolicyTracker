# Local AI connections, model selection and usage

PolicyTracker now includes a running local AI connection service and an **AI connection** page. Start it with Python 3.10 or newer:

```powershell
python scripts/preview_ui.py
# Optional alternative port:
python scripts/preview_ui.py --port 8767
```

Open `http://127.0.0.1:8765/design/prototype/` and choose **AI connection** in the sidebar or **Connect AI** in the header. The server binds only to loopback. This implementation is for one local operator; it is not a hosted website login service.

If both ChatGPT initialization and API connectivity fail, check how the preview was launched. A preview started inside a coding tool's restricted environment inherits its network and filesystem restrictions. Its blocked proxy can prevent an API key from reaching OpenAI, while Codex can fail before sign-in starts. Restart the preview from a normal terminal with the project's Python environment and reopen the address it prints. For an isolated preview, preserve the same `--port` and `--profiles-path` options. Do not remove proxy or sandbox protections from inside the application. A network failure does not establish that a key is invalid; after restarting, enter it again directly in the API form.

Restart is also required after backend code updates: refreshing the browser alone can mix current JavaScript with an older API process. A failed `/api/ai/inventory` check means local document availability is unknown, not zero; restart the current workspace server and choose **Check local sources**. The application verifies original file hashes independently of AI. A server restart clears in-memory browser connections; choose **Use local ChatGPT account** again in the browser you will use, without switching accounts or copying credential files.

## ChatGPT

Install the official Codex CLI and make `codex` available on PATH. Run PolicyTracker as the same OS user that owns the Codex installation, with access to that user's Codex state directory.

If initialization fails with an access-denied error when the preview was started by a sandboxed coding tool, restart the preview from your normal terminal using the project environment (`.\.venv\Scripts\python scripts/preview_ui.py` on Windows). The server needs ordinary access to Codex's local state; changing your password or signing out does not fix a filesystem permission problem. Stop active country work before restarting.

- **Use local ChatGPT account** connects an already authenticated local Codex account to this browser session.
- **Continue with ChatGPT** starts the supported app-server browser sign-in flow. Open the returned sign-in page and complete it yourself. PolicyTracker waits for the matching login-completed notification, supports cancellation and expires pending sign-in after five minutes. Codex owns OAuth, callbacks, token storage and renewal; PolicyTracker does not read or copy credential files.
- **Disconnect** removes this browser session's permission to make new ChatGPT requests. It intentionally leaves the user's shared Codex login intact. Changing or signing out of that account in Codex invalidates the connection when checked again.
- Model and effort choices come from the installed app-server catalog. The catalog can be cached and does not prove entitlement. **Test connection** creates an ephemeral, read-only turn using the exact selected model and effort, with provider fallback disabled. The test uses a fixed, non-sensitive prompt. Only a completed turn with text is shown as verified. No source PDFs are sent by this test.
- Usage reads the account's actual rate-limit buckets. Missing metrics are unknown, not zero. The UI links to [ChatGPT usage settings](https://chatgpt.com/settings/usage). Tests consume plan usage.

Sign-in affects the local Codex account, so use a dedicated OS account/installation if other people share this computer. A hosted product needs its own registered and eligible identity/inference integration; do not expose this local server or reuse one operator's account for other users.

## OpenAI API

Enter a project API key directly in the UI. The backend validates it against `GET https://api.openai.com/v1/models`, then keeps it in memory for the browser session, up to eight hours or until disconnect/server restart. Credentials are never returned in status, saved to localStorage, included in logs, or written to project files. API billing is separate from ChatGPT.

The picker intersects the key's model list with reviewed Responses-compatible adapters: GPT-6 Astra, GPT-6.1 Sol, GPT-6 Luna, GPT-4.1/mini, GPT-4o/mini, and their dated snapshots. API model-list responses do not expose reasoning capabilities, so their effort rules live in `api_models` in `src/policytracker/ai_runtime.py`. Review this adapter when adding model families. Hidden/unknown/specialized models are not advertised as working text models.

**Test connection** sends a small real Responses request. An optional prompt allows a direct text request; choose an output cap between 256 and 8,192 tokens. The cap includes reasoning tokens. Requests use `store:false`. Incomplete responses, refusals without output, empty responses, invalid credentials, unavailable models and quota errors do not count as successful tests. Provider errors do not cause a route or model fallback. API requests are not retried automatically.

## Preferences and analysis requests

**Save as default** stores only the selected route, model and effort on this device. New analysis/translation requests inherit those choices. Their pickers use the same connection catalog, and their downloaded JSON contains the actual selection. Opening connection settings from a draft provides a return link without discarding the draft. Unsupported saved choices remain visible and require an explicit new choice.

The one-country worker now uses these connections for structured translation, extraction, reconciliation and Overview requests. Start it from a country page. Saving an optional operational request still does not execute it. Real country outputs have not been generated by the implementation tests; see [the local workflow and limits](ARCHITECTURE.md).

## Runtime contract and security

The local service lives in `policytracker.local_server`; provider orchestration is in `policytracker.ai_runtime`. `scripts/preview_ui.py` launches both the UI and service. These `/api/ai` endpoints are distinct from the future hosted OpenAPI blueprint:

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/ai/session` | GET | Establish an HttpOnly, SameSite=Strict browser session and CSRF token |
| `/api/ai/status` | GET | Sanitized connection status, catalogs and latest session request |
| `/api/ai/chatgpt/connect` | POST | Opt this session into the existing local account |
| `/api/ai/login/start`, `/login/cancel` | POST | Start/cancel Codex-managed browser sign-in |
| `/api/ai/login/status` | GET | Read matching sign-in completion |
| `/api/ai/api-key` | POST | Validate and connect an API key in server memory |
| `/api/ai/models` | POST | Refresh the selected route's model catalog |
| `/api/ai/usage` | GET | Read actual ChatGPT account usage limits |
| `/api/ai/disconnect` | POST | Remove a session connection |
| `/api/ai/jobs` | POST | Start an explicit connection test or API prompt |
| `/api/ai/jobs/{id}` | GET | Read this session's request status and response |

All mutations require JSON and a session CSRF header. Host/Origin checks reject cross-site and DNS-rebinding requests. The fixed API upstream rejects redirects. Source PDFs, private state, credentials, code and logs remain outside the static-file allowlist. Responses disable caching and framing. Jobs are session-isolated, with one active request per browser session and one ChatGPT inference at a time. Country jobs use durable SQLite checkpoints and block connection changes while active; they are not displayed as connection-test receipts. Completed history is capped at 20 requests in memory. Refreshing the page resumes polling the latest active request.

## Verification

```powershell
python -m unittest discover -s tests -v
node --test tests/ai-client.test.mjs tests/integration-client.test.mjs tests/operation-request.test.mjs
```

Use a recent Node version; sandboxed environments that restrict process spawning can add `--test-isolation=none`. Tests use explicit fake transports, never production mock fallbacks. They cover credential/session isolation, CSRF/Origin/Host boundaries, account switches, matching OAuth completion, exact model/effort dispatch, early notifications, incomplete/failed turns, and usage semantics. Live API verification requires a user-provided key.

Implementation references: [Codex app-server authentication and model protocol](https://learn.chatgpt.com/docs/app-server), [ChatGPT usage UX](https://developers.openai.com/siwc/ui-ux-guidelines), [API model list](https://developers.openai.com/api/reference/resources/models/methods/list), [Responses API](https://developers.openai.com/api/reference/resources/responses/methods/create), and [API model capabilities](https://developers.openai.com/api/docs/models).

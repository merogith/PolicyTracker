# LLM engineering and account access

Current local implementation: [AI connections, models and usage](15-ai-connections.md). The workspace now has Codex-managed ChatGPT sign-in, real connection tests, direct API text requests and live settings. The document-processing worker interface below remains the production design.

## Provider strategy

Use one task interface for every LLM feature: classification, translation, extraction, reconciliation, brief/report generation, comparison, quality checks and chat. A task specifies provider route, model, reasoning effort, prompt version, schema, input snapshot, limits and privacy scope. No feature may bypass this interface with a hard-coded model.

The first production profile requested by the user is `gpt-6-astra` with `xhigh` reasoning, using ChatGPT account access. `Extra High` is the display label. Never silently replace it with `high`, `max`, another model or an API-billed call. Record requested and confirmed settings separately; a model's self-description is not verification.

| Route | Use | Conditions |
|---|---|---|
| Local Codex with existing ChatGPT login | Operator-driven initial document production | The installed app/CLI owns credentials. Use its supported protocol; record successful turn completion. This does not create a login feature on the public website. |
| Sign in with ChatGPT for this application | User-operated local/open-source client or approved hosted integration | Implement the documented OAuth flow, consent, host identity and eligibility rules; identity-only login is not inference authorization. |
| OpenAI API | Later server or user-key operation | API credentials and billing are separate; keep the key server-side or in an OS keychain. Same evidence/prompt contracts, with provider-specific wire handling. |

As checked on 8 October 2026, official documentation describes ChatGPT-plan usage for open-source/local apps, with paid/remotely hosted availability subject to the published eligibility route. Do not promise that the Risk Analytics website can immediately offer plan-funded inference merely by adding a sign-in button. See [plan usage overview](https://developers.openai.com/siwc/token-sharing-open-source) and [quickstart](https://developers.openai.com/siwc/quickstart).

Keep authentication to PolicyTracker, permission to use a model, and authorization to publish Prime separate. A user may read shared Prime reports without running an LLM or having a provider account. Run ownership identifies whose quota or API budget is consumed. Signing out must stop new jobs using that credential; pending work stays resumable after reauthentication.

## Capability negotiation

Populate model/effort choices from the authenticated route's catalog where available. Treat catalogs as discoverability, not proof of entitlement. Run a small preflight inference with the selected model/effort; only a completed request establishes access for that request. Handle inaccessible models, revoked consent and quota exhaustion explicitly. Persist a capability snapshot and the verification time; do not claim future availability from one successful test.

The installed CLI was detected as 0.160.1 and its model catalog contains Astra with `xhigh`. Local account authentication was reported as ChatGPT. A catalog check is not a completed production run. See `data/manifests/provider-preflight.json` for the observed state.

The official [Astra model page](https://developers.openai.com/api/docs/models/gpt-6-astra) lists `xhigh`; account and API capabilities can differ. Never send a Codex-only effort string to the API just because it appears in a local picker.

## OAuth implementation checklist

For application-owned sign-in, follow the current registration guide rather than copying Codex's credential file. Use PKCE, state and nonce; validate issuer, audience, signature and expiry; bind callbacks to the initiating session; verify granted inference scopes; persist the stable host ID where that flow requires one. Store refresh tokens in a protected secret store, refresh through the documented route, and revoke/unlink explicitly. Do not place tokens in browser localStorage, URLs, logs or Git. Hosted integration eligibility and client registration are deployment dependencies, not items an LLM can assume completed.

Use the official [app-server integration](https://developers.openai.com/siwc/token-sharing-open-source/codex-app-server) if embedding Codex. Its model catalog may be bundled. Check terminal turn status and retain thread/run IDs for the correct user. Do not use one operator's ChatGPT login as a shared multi-user backend credential.

The ChatGPT-plan Responses route has a different request contract from ordinary API calls. Use an adapter and current capability flags. The documented preview requires HTTP streaming with `store:false`, does not provide ordinary persistent HTTP conversation continuation, and excludes several hosted tools/fields. Implement retrieval, document storage and conversation assembly in PolicyTracker so feature semantics can remain consistent. See [preview limitations](https://developers.openai.com/siwc/token-sharing-open-source/preview-limitations). Recheck that contract before implementation and deployment.

## Prompt composition

Version prompts like code. Each request combines:

1. The trusted shared evidence contract in `prompts/v1/00-evidence-contract.md`.
2. Exactly one task prompt, with explicit job purpose and a schema version.
3. The relevant taxonomy definitions and reviewed routing examples.
4. Structured task context: country/party scope, source authority, dates, requested output and immutable input IDs.
5. Untrusted source segments as JSON data, preserving their document/page/segment IDs.
6. Only the validated upstream records needed for the current task and their evidence.

Do not paste entire chat logs into Prime prompts. Do not let document text append or change the instruction layer. The task brief may customize audience/focus but cannot alter the truthfulness, evidence, geography or publication rules. Prompt hashing covers all included files and configuration, not just the main Markdown filename.

Use constrained structured output where the selected provider supports it, followed by local validation. Schema correctness is not factual correctness. Treat refusals, malformed JSON, incomplete streams and output-budget exhaustion as failed/incomplete jobs, not empty successful reports. Preserve raw response and errors privately; bounded repair prompts receive specific validation failures and original evidence. See [structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs).

## Context and extraction strategy

Use section/table-aware segments with neighboring context. Tokenize the actual request rather than estimating pages as a fixed number of tokens; multilingual PDFs and dense tables vary widely. Chunk overlap preserves context but duplicates are resolved through source IDs. Do not send only a running summary of earlier goals: it can cause later qualifications and contradictions to disappear.

Separate broad coverage extraction from short executive summaries. A page ledger accounts for all input material. A second pass examines unassigned sections, high-density tables and references to annexes. Target extraction must retain numeric basis and conditions even when the dashboard displays a short label.

Use embeddings only for retrieval and candidate matching if they improve measured quality. The older PDF's 85% similarity threshold is not a universal merge rule. For identity decisions compare action, responsible party, location, unit, baseline, deadline, scenario and scope. Preserve the difference between repeated phrasing, a translation, a stronger revision, a narrower measure and a conflicting target.

Ask the model for concise evidence-backed decision reasons, not hidden chain of thought. Each field should expose a checkable source phrase and any deterministic conversion; a numeric confidence badge is not proof. Prefer categorical review flags such as uncertain authority, ambiguous condition, unresolved table context and competing translations.

## Reuse and cost

Store parse, translation and extraction outputs independently. Summary, tracker and comparison reuse these artifacts. New country synthesis reads the relevant evidence corpus; the source PDFs need rereading only for changed inputs, validation or missing context. A changed prompt, taxonomy, parser, source relationship or approved correction marks affected downstream artifacts stale.

Store provider usage including reasoning tokens where exposed, cache usage, elapsed time, retries and pricing timestamp. API estimates distinguish input, cached input, visible and reasoning output, translation, QA and external services. If actual usage is unavailable, store `null` and an estimate label, not zero. Account usage has quotas and no assumed per-token dollar equivalent. Preflight the later $24 API sample separately.

## Automated quality checks and optional later evaluation

No staffed manual review is available for the initial delivery. Start with deterministic/adversarial fixtures and automated source-oriented challenge passes across document families, languages, prose/tables, targets, conditions and irrelevant content. If manual labelling becomes available later, a starting sample of approximately 150-200 passages can support calibration, with whole families held out, all topics where possible and rare cases included. It is neither a prerequisite for publication nor proof of corpus-wide accuracy.

Check numeric/condition fidelity, geography, source locators, translation numbers, duplicate merges, future-versus-observed confusion and summary support. Test omissions from the source side. Credible recall/precision metrics require a reference set; do not present LLM self-evaluation as measured accuracy. If reference labels become available, report sample counts, uncertainty and adjudication. Multiple model passes can share errors.

Automatic eligibility requires resolving published factual claims to evidence, checking headline numbers/scope/conditions, retaining supported variants, accounting for pages and disclosing unreadable or missing material. Repair or remove known unsupported claims and report the limitation; never guess to obtain a passing result. Technical corruption or unfinished tasks cannot pass. Source ambiguity and missing baseline fields can appear as explicit unknowns in a usable report. A system check can find errors but cannot certify perfect accuracy or recall. The draft PDF's >95% recall is an aspiration, not a measured result.

Successful eligible Prime runs publish automatically subject to pinning; optional audit never requires staffing before release. A later accepted correction creates a new version, invalidates affected summaries and requires rebuilding and automated checks before publication. Model/prompt upgrades are trialled on retained evaluation cases before replacing production defaults.

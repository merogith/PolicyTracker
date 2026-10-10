# Product decisions and feature scope

> Engineering/design background. Current navigation, task controls and editable-source ownership are defined in [METHODOLOGY.md](METHODOLOGY.md), [document 14](14-lean-tools-translations-and-configuration.md) and [CUSTOMIZATION.md](CUSTOMIZATION.md). Earlier three/five-view and audience/length proposals below are historical; the current profile has Overview and Policy register.

**Navigation/task update:** the [simple methodology](METHODOLOGY.md), [MVP contract](00-mvp-deliverable.md) and [current tool design](14-lean-tools-translations-and-configuration.md) supersede the five-function navigation below with two core views of one Country Profile. Risk/DRR and delivery stay in the narrative and register; comparison and bilingual documents are supporting tools. Publication, optional audit and pinning decisions here remain authoritative.

8 October 2026. This document records the user's clarified operating rules and the recommended feature scope for the supplied UNDP Istanbul Regional Hub assignment. Operating decisions below supersede the earlier human-approval-first proposal. Feature recommendations are product choices, not an institutional UNDP standard. This is a design update; the production runner and revised publication behavior are not yet implemented.

## Confirmed operating decisions

- Deliver usable, visible reports automatically after a successful run and automated checks. Human review is optional, can happen afterward, and never a required staffing dependency.
- Prime is a shared country report assembled from the explicitly selected official NDC/NAP collection and eligible annexes. Update it principally when a new document arrives; no recurring regeneration is required.
- By default, the newest eligible successful Prime run becomes the shared report. A user can explicitly pin any eligible historical country release; it remains selected until another is assigned or the pin is removed.
- Unpinning returns the country to automatic selection and immediately selects the newest eligible successful release. If none exists, show an explicit unavailable state.
- Initially every signed-in team member can start a Prime run, select/pin/unpin releases and use optional audit tools. A separate reviewer or publisher role is not required. Record who changed shared state. This does not grant anonymous visitors write access.
- Ad hoc reports have a separate history. Uploading support material, comparing countries or chatting cannot change the shared Prime pointer.
- Model, effort and account/API route are common settings for every LLM task. The requested initial production profile remains Astra / Extra High through the user's account, with no silent model or paid API fallback.

The system should remove human bottlenecks while preserving automated failure detection. A truncated model response, broken citations, missing artifacts or failed job is not a successful report. Failed runs stay visible in history with a reason and retry action; the last working Prime remains available. Where evidence is ambiguous, publish supported findings and explicit uncertainty rather than wait indefinitely for a reviewer or invent a fact.

## Mission translated into product behavior

The supplied assignment concerns analysis and structuring of climate and disaster resilience commitments, with consistency, comparability and interpretation across countries, sectors and languages. The primary product should therefore be a reusable evidence register with useful country reports. Do not make real-time progress tracking or full investment appraisal promises that the NDC/NAP collection alone cannot support.

Preserve mitigation commitments too, while allowing the default country overview to emphasize adaptation, disaster resilience and development implications. Prioritization must cite its basis and distinguish explicit national priority from an analytical choice. Absence from the selected documents is an evidence gap, not proof that the country has no policy or activity.

One important scope limit remains: NDCs and NAPs do not necessarily contain a country's full disaster risk reduction policy. National disaster strategies, ministry plans and implementation reports can add operational value through ad hoc analysis. Do not silently expand Prime beyond its stated NDC/NAP scope or describe it as a complete inventory of national resilience policy.

Where stated, link the chain **hazard or vulnerability → action → intended result → affected population/place → indicator**. Preserve poverty, livelihoods, inequality, gender and disability implications as source-supported context or explicit provisions, not automatically inferred benefits. A hazard description is contextual evidence, not a commitment; an intended result is not an observed impact.

The recommendation to retain governance, finance, implementation, inclusion and support information is consistent with [UNDP's NDC implementation lessons](https://www.undp.org/publications/nationally-determined-contribution-support-programme-achievements-and-lessons-learned-2017-2025). The [UNFCCC NAP process](https://unfccc.int/national-adaptation-plans) also addresses adaptation needs, resilience and integration into development planning. These sources support the breadth of extraction; they do not prescribe this interface or validate its outputs.

## Recommended Prime functions

All five functions belong to one immutable country release. They share evidence, generation provenance and publication state. They are not five full rereads of the PDFs.

| Function | Expert question and useful output | Initial release scope |
|---|---|---|
| 1. Country brief | What should I understand in five minutes? A concise English synthesis of priorities, important commitments, deadlines, conditions, resilience/development relevance, changes and evidence limitations. | Core. Every headline links to underlying records and original evidence. |
| 2. Commitments and policy register | What exactly is promised or proposed? Searchable quantitative targets, qualitative actions, milestones and explicit priorities with consistent labels. | Core. Filter by topic, objective, hazard, institution, date, conditionality, territorial scope, affected group and document version. Count canonical commitments separately from source mentions and variants. |
| 3. Implementation and support information | Who is named, what is needed and what could be monitored? Responsibility, sequencing, estimated costs, funding status, technology/capacity/data needs, indicators and documented barriers. | Core structured fields and report sections. Show what is stated or missing; no invented owner, funding gap, project feasibility or readiness score. Suggested UNDP follow-up questions are clearly labelled analysis. |
| 4. Changes and NDC–NAP alignment | What changed between revisions, and how do the country's documents relate? Cited before/after variants, retained/new/not-restated commitments, overlaps, explicit links and possible tensions. | Core within-country analysis. New wording does not prove greater ambition; omission does not prove repeal. A changed baseline may make numerical comparison invalid. |
| 5. Sources, English access and audit | Where did this come from, and how reliable is this extraction? Original/English passages, full English reading layer, page links, source/version list, quality flags, report history and downloads. | Core. Optional corrections create a new traceable version; audit status is separate from availability. |

The full report includes all five. Keep ordinary navigation to **Overview**, **Policy tracker**, and **Sources and changes**. Implementation/support information appears in the overview and expandable tracker fields. A reader moves from five-minute summary, to filtered records, to original passage without learning a second information system.

Do not label the whole report “draft” merely because nobody has audited it. Display **AI-generated · automated checks passed · not manually audited**, plus source date and any limitations. This accurately describes a usable published report without implying human endorsement or error-free content.

## Regional comparison decision

For the initial deliverable, make within-country revisions and NDC–NAP alignment part of Prime. Offer cross-country comparison as an ad hoc task. After country bundles exist, add a single regional evidence matrix that reuses them, with a frozen release-ID map. Filters can then show Kazakhstan alongside selected peers without rereading all source PDFs 18 times.

A regional narrative or country-versus-all narrative is optional later. If produced, all views reference one regional snapshot. When a country's Prime changes, label the old regional snapshot outdated; rebuild from the changed evidence instead of silently changing the other countries' releases. A pinned country contributes its selected Prime, not an unselected newer run.

Compare equivalent measures only. Preserve baseline, scenario, denominator, target year, geography, gases and accounting basis. Display non-comparable figures side by side with the reason rather than rank them. Do not award a country a better score for a longer document or more extracted mentions.

## Recommended ad hoc functions

Use four templates in one New report flow, with the same evidence pipeline. Each can operate on authorized Prime snapshots, selected official documents, support uploads or a mixture. Freeze the chosen source versions. Recommendations and proposed actions must remain visibly separate from source commitments.

| Template | Typical regional-team request | Output |
|---|---|---|
| Briefing | “Prepare a two-page meeting brief on drought resilience in these countries.” | Cited brief, selected commitments, institutions, caveats and discussion questions. |
| Focused analysis | “Find every early-warning action, financing condition and responsible institution in these materials.” | Complete relevant register plus thematic synthesis. Exhaustive requests use full scoped processing, not only a few retrieved passages. |
| Comparison | “Compare old and new NDCs”; “compare NDC and NAP”; “compare water commitments in three countries.” | User-visible groups, comparison matrix, supported similarities/differences, change evidence and explicit non-comparability. |
| Programme and monitoring preparation | “Turn the selected commitments into a support-needs table and candidate monitoring framework.” | Source-stated actors, needs, costs and indicators; separately labelled proposed activities/indicators and questions where source information is missing. No invented baseline, secured budget, attribution or expected impact. |

Chat is a follow-up capability on every report: explain a record, trace a number, refine the brief, ask for another view or save a new report version. It is not a separate Prime publisher or a source of policy evidence. If a chat request broadens the country/document scope, update the visible scope and run the necessary processing before claiming complete coverage.

Keep initial controls to **task, sources/groups, focus, audience and length**, with an optional instructions box. Model/effort/payment route live in one shared run-settings panel. Start with sensible defaults; do not demand an expert configuration form for routine work.

Example: Russian ministry paper + English translation + Russian Kazakhstan NDC produces an ad hoc KAZ analysis. It distinguishes editions from independent sources and preserves disagreements. Adding a Kyrgyz document makes it a mixed-country report with explicit groups. Both stay in My reports; neither becomes KAZ Prime.

## Automatic publication, pinning and histories

Use two separate axes:

| Axis | States / rule |
|---|---|
| Processing | queued, running, validating, complete, failed, cancelled, needs_input |
| Automated eligibility | pending, passed, passed_with_limitations, failed; stored receipt bound to the full immutable bundle |
| Optional audit | not_audited, annotated, corrected; audit events include person, time, evidence and scope |
| Shared selection | automatic (`latest_successful`) or pinned (`pinned`), one pointer for the country |
| Source availability | complete within the declared supplied scope, partial with named gaps, or no_documents_supplied |

Publish successful eligible Prime results immediately in Prime history. In automatic mode, advance the country pointer. In pinned mode, the new result is still visible in Prime history and can be opened/downloaded, but the country dashboard continues to show the pin. Ad hoc results appear in their own history only.

An audit annotation does not regenerate the report. An accepted correction creates a new immutable bundle, rebuilds affected views, and passes automated checks. It follows the same automatic/pinned selection rule; it never silently rewrites a pinned artifact. A reader can see that a correction exists. Withdrawal is an explicit team action with an event; in automatic mode choose the next eligible release, while a withdrawn pinned release shows an unavailable pointer until explicitly reassigned or unpinned.

Use monotonic run sequence allocated at submission, not finish time, to prevent an old slow job replacing a newer eligible result. Bind each run to a country corpus generation. A reanalysis of an older snapshot remains historical unless the user deliberately selects it. When the corpus changes, the old published report remains readable and is labelled as using the previous source set until a new successful report is available.

Pin/unpin/assignment uses compare-and-swap on the pointer revision. If someone pins while a job is running, completion respects the new pin. If two users change a pin concurrently, the later stale request sees a conflict and reloads the current selection. Uploading a source alone never erases or replaces a report.

## Quality without a staffed review gate

1. Parse and translate the full selected scope, preserving original versions and table context. Account separately for readable, unreadable, translated and excluded content.
2. Extract structured records with field-level evidence. Validate shapes, IDs, locators, numeric transformations, conditionality and geography. Schema validity alone is insufficient.
3. Run a source-oriented omission and contradiction challenge, including source sections with no extracted records. A second model pass is a useful check, not independent proof or a replacement for measured accuracy.
4. Repair bounded failures. If a disputed interpretation cannot be resolved, keep both supported statements or omit the unsupported interpretation and disclose the issue. Avoid ambiguous merges and unsupported headlines.
5. Verify the complete artifact bundle and publish automatically. Optional audit tools remain available afterward.

Technical corruption, unfinished tasks and unresolved false factual claims in the proposed published content fail the run or trigger repair. Source ambiguity, absent baselines and missing source documents can be reported explicitly without a human approval wait. An intentionally limited source outcome can publish as partial; it must not count as the completed full-scope report. A no-document country gets an availability entry, not an invented analysis.

There is no staffed manual benchmark available. Start with deterministic/adversarial fixtures, multilingual numerical cases and recorded automated challenge findings. Do not advertise measured recall/precision until a credible reference set exists. Optional future human labels can improve evaluation but are not required to operate the tool. LLM self-confidence does not establish an accuracy percentage.

## Cost and implementation focus

- Extract and translate each immutable source version once per compatible processing configuration. Reuse the resulting evidence for all five Prime functions and compatible ad hoc work.
- On a new NDC/NAP, process new or changed material, then recompute the country's reconciliation, change findings and brief. Reuse unchanged evidence with its original provenance.
- Deterministic filtering, reading reports, downloading exports and viewing original/English evidence need no LLM call.
- Preserve the requested Astra/xhigh settings for the initial production run. Measure actual usage on one country and difficult examples before estimating the whole corpus; no API spend is authorized by this design update.
- First implement one complete country bundle and static JSON integration. Then run the remaining supplied corpus, and add the four ad hoc templates and grounded chat. Full hosted login is a separate deployment dependency, not a reason to delay local account-funded production.

## What the review still found missing

The publication clarification resolves the earlier staffing question; it does not repair the six reproduced technical failures. Immutable source/artifact versioning, field support, omission detection, justified progress statuses, complete bundles and a trusted automated publication receipt remain priority work. The model transports, full translation/extraction worker and actual country report production also remain unfinished.

The local registry, tests and v1 manifest schema still encode the older approval-based reference design. Migrate them together to separate automatic eligibility from optional audit before using them for production. A renamed `approved` flag is not enough: the publisher must verify a receipt created by the validator, and the pin/race/old-corpus cases need regression coverage. The initial run profile and product specifications now state the clarified target behavior.

The inventory currently has 42 PDFs across 17 populated country folders and an empty Kosovo entry. That supports 17 substantive country reports plus one honest availability entry until source material for the missing entry is obtained; it does not support claiming 18 full evidence-based analyses.

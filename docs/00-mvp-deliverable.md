# Regional Policy Tracker — first MVP and delivery contract

The first deliverable is an **automated Regional Policy Tracker**, supported by **one published Country Profile for each country**. It extracts, translates, categorizes, labels, summarizes and presents NDC/NAP evidence consistently across the region. Optional user analyses are a second layer, not the definition of the MVP or a reason to delay its delivery.

## Names and hierarchy

| Level | User-facing name | Meaning |
|---|---|---|
| Product / first deliverable | Regional Policy Tracker | Region-wide country coverage, status and access |
| Main country deliverable | Country Profile | One coherent country evidence/report bundle |
| Version shown to everyone | Published version | One selected immutable profile release per country |
| Profile contents | Two core country views | Overview; Policy register |
| Supporting utilities | Documents & translations; Version history; Method & prompts | Reading, traceability and version selection |
| Updating | Generate / update Country Profile | Run the full country pipeline against the curated source snapshot |
| Historical record | Version history | Earlier runs/releases, selected version and pin/unpin events |
| Optional second layer | Analysis tools | Custom extraction, comparison, gap analysis and question-led briefs |

“Prime” remains an internal implementation term in existing schemas, database fields and API paths. It should not appear as several different reports or compete with the Country Profile in navigation. Keep wire identifiers stable for now; a label change must not silently break existing clients. “Summary”, “tracker”, “risk view” and “full report” are presentations or sections of the same profile version.

## What each Country Profile includes

1. **Overview:** five-minute brief and expandable thematic narrative on priorities, climate/disaster risks, adaptation, mitigation, responsibilities, support needs, inclusion and limitations.
2. **Policy register:** complete searchable evidence on quantitative targets, qualitative actions and risk context, with linked actors, finance, monitoring, baselines, deadlines, conditions and original/English citations. Sector, risk/DRR and delivery are filters/lenses rather than duplicate reports.
**Conditional evidence:** within-country NDC–NAP links and changes remain a subsection when eligible document pairs exist. With one source, cross-document comparison is not applicable. The optional Compare documents action opens a separate analysis request.

**Documents & translations** supplies the full English reading layer, preserved originals, document versions and coverage disclosures. English is not a standalone analytical feature. **Version history** and **Method & prompts** provide selection and transparency. See the short [methodology](METHODOLOGY.md) for what each view answers and its exact prompt files.

All views come from the same evidence snapshot. Each has an availability state and a reason where not applicable or limited. They do not have separate “main” selections or independent publication histories. The ten required narrative sections remain intact within the two core views. A full report download, dashboard, table export and API response retain the same release ID.

## Automated production path

Register and inspect the curated source versions → identify countries/instruments/editions/languages → parse/OCR all content → prepare full English alignment → extract and label structured evidence → reconcile duplicates, translations and revisions → assemble the Country Profile and deterministic views → run automated coverage/evidence/schema/bundle checks → publish automatically → update the regional tracker.

The initial batch covers all 18 country entries, with independent, resumable country jobs. Verify the requested Astra/Extra High account route before inference. One unavailable country's sources or one failed job must not block usable completed country profiles. No silent model/route fallback or API spending is introduced.

The default published version is the latest eligible successful result, ordered by corpus generation and run submission sequence. Pinning holds a selected version while newer results remain usable in version history. Failed/incomplete jobs never replace a working profile. Upload alone does not change it. When a new NDC/NAP is registered, rerun that country, reuse compatible unchanged extraction/translation and regenerate the affected profile sections. Reading/filtering/exporting uses no new LLM call.

Manual review is an optional audit utility, not a publication gate. Source uncertainty is reported explicitly; broken processing and unsupported claims require repair or failure. Documents cannot instruct the agent or grant publication authority.

## MVP acceptance

The MVP is complete only when the selected-model pipeline produces real profiles and the regional tracker exposes them. A well-designed interface or inventoried PDF is not enough.

| Required outcome | Acceptance evidence |
|---|---|
| Regional coverage | All 18 entries, accurate document counts, selected profile/version and section availability |
| Actual analysis | Every selected source accounted for, full English coverage or named limitations, structured evidence and canonical commitments |
| Useful country product | Two core views and bilingual sources available or explicitly limited/not applicable; full thematic report and structured export from the same bundle |
| Traceability | Every factual finding resolves to original/English evidence and a preserved source version/page |
| Automated operation | Resume/cancel/checkpoint, repeatable manifests, duplicate submission protection, model/effort/route provenance |
| Shared stability | One published version, automatic update/pin rules, immutable history, race/failure handling |
| Portability | Regional/profile JSON and evidence-linked exports; another website can render them without inference |

The current corpus has **17 countries with documents and one no-source entry (Kosovo)**. Until a source is supplied there, an honest availability entry is required; it cannot be counted as an eighteenth substantive analysis. The target remains all 18 country profiles, and the missing source remains an explicit delivery gap.

## What comes after the core delivery

Analysis tools reuse the same parsing, translation, evidence model, labels and model controls. They accept authorized policy/support documents, preserve their own histories and cannot alter the published Country Profiles. Four analysis tasks and independent full-document translation are specified in document 14, but completing a chat interface, support-only upload workflow or general-purpose comparison UI is not an acceptance dependency for the first country-profile batch.

## Repository and export structure

`config/product.json` is the product naming/scope contract. `config/v2/`, `prompts/v2/`, `schemas/v2/` and `data/manifests/initial-batch-plan.json` define the core country pipeline. `config/operations/`, `prompts/operations/` and `schemas/operations/` belong to the optional analysis layer. The prototype and integrations consume the same country/profile data, rather than own analysis logic.

Planned generated outputs (not yet produced):

```text
exports/regional-policy-tracker/
  regional-index.json                 Selected country release IDs and availability
  countries/<country-code>/
    published.json                    One selected release pointer
    releases/<release-id>/
      manifest.json                   Source snapshot, method/model versions, hashes
      country-profile.json            Full thematic report rendered through two core views
      country-profile.md              Readable rendering of the same profile
      dashboard.json                  Deterministic lightweight view
      commitments.jsonl               Canonical actions and target variants
      evidence.jsonl                  Original/English locators and support
      translations-manifest.json      Complete aligned reading-layer references
      sources.json                    Versions, families and source coverage
      coverage.json                   Dispositions, limitations and automated checks
```

Operational jobs, credentials and unpublished private artifacts stay outside public export paths. Do not create different primary outputs called “Prime summary”, “Prime comparison” or “Prime tracker.” Use one Country Profile with relevant sections and optional regional/ad hoc comparison views.

## Current delivery status

Prepared: corpus inventory/text, architecture, schemas, labels, prompts, batch plan, offline validators/composers, regional interface and integration contracts. **Not completed:** production OCR/translation/extraction execution, actual Country Profiles, automatic publication service or deployed API. The batch remains `planned_not_executed`. The old batch-plan requirement for `expert_acceptance` was removed to match automatic publication; this change does not claim the production runner exists.

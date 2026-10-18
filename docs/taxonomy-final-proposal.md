# PolicyTracker taxonomy: final proposal for review

**Purpose:** a practical, two-stage design for classifying information in NDCs, NAPs, national disaster risk reduction (NDRR) plans/reports, and then organizing the classified information into claims.

**Status:** proposal for review, not the active runtime configuration. Existing topic IDs are retained where possible. New topic suggestions are marked `NEW` and should be approved before being added to the runtime taxonomy.

## Recommendation in one minute

Use two distinct taxonomies and prompts:

1. **Label taxonomy + extraction/labeling prompt:** classify each source-grounded information item on its own. Subject labels use **Domain → Subdomain → Topic** with multiple paths allowed. Other facets cover statement type, information role, purpose, hazard, time, target, affected groups, stakeholders, place, finance, and evidence status. Never force every field to have a value.
2. **Relation taxonomy + organization prompt:** compare already extracted and labeled items, then propose links such as support, duplicate/restatement, revision, contradiction, or related-but-distinct. The prompt can group compatible items under a stable claim ID, or leave an item as a standalone claim. Preserve the input items and evidence; the grouping never replaces them.

Do not use the relation taxonomy to label source information, or the subject taxonomy to decide whether two records are the same claim. The two prompts solve different tasks and should have separate output schemas and validation.

```text
Prompt 1: one source-grounded information item
  ├─ one statement type, plus zero or more information roles
  ├─ zero or more subject paths: Domain → Subdomain → Topic
  ├─ zero or more purpose / risk / affected-group / stakeholder / place / instrument labels
  ├─ zero or more target objects, each with its own number, condition and period
  └─ exact source evidence and locator

Prompt 2: a candidate set of labeled information items
  ├─ zero or more typed relations between item pairs
  ├─ one or more proposed claim groups (single-item groups are valid)
  ├─ explanation and confidence for each merge or relation
  └─ preserved item IDs and evidence links
```

The subject hierarchy answers **“What is this about?”**. The facets answer other questions. This lets a flood-related irrigation action belong to both **Food & Agriculture** and **Water**, while also carrying **adaptation**, **flood**, a location, and its own target period.

## 1. Domains, subdomains, and topics

The list below is intentionally broad. Subdomains group related subjects; topics are the specific labels applied to source records. Topic mappings may have more than one parent path.

| Domain | Subdomain | Topic choices |
|---|---|---|
| **Climate** | Governance and enabling conditions | CLM-01 Climate planning and governance; CLM-02 Climate finance and support |
| **Climate** | Climate knowledge and monitoring | CLM-03 Climate information and risk assessment; CLM-05 Climate monitoring and reporting |
| **Climate** | Mitigation and carbon | CLM-06 Economy-wide emissions targets; CLM-07 Land carbon and removals |
| **Climate** | Loss and damage | **NEW:** Climate-related loss and damage; economic and non-economic loss; displacement and recovery support |
| **Disaster Risk & Emergency Management** | All-hazards risk and governance | CLM-08 Disaster risk and management |
| **Disaster Risk & Emergency Management** | Warning, preparedness and response | CLM-04 Early warning and disaster preparedness; CLM-08 Disaster risk and management (use the risk-function facet for the specific phase) |
| **Disaster Risk & Emergency Management** | Recovery and reconstruction | CLM-08 Disaster risk and management (use the risk-function facet for the specific phase) |
| **Food & Agriculture** | Agricultural production | AGR-02 Resilient crops and soils; AGR-03 Livestock and manure |
| **Food & Agriculture** | Farm water and irrigation | AGR-01 Irrigation efficiency (also Water & Sanitation) |
| **Food & Agriculture** | Food systems and fisheries | AGR-04 Food systems and farm livelihoods; **NEW:** Fisheries and aquaculture |
| **Water & Sanitation** | Water resources and access | WAT-01 Water supply and groundwater; WAT-02 River basins and drought management |
| **Water & Sanitation** | Water hazards and protection | WAT-03 Flood and coastal protection |
| **Water & Sanitation** | Water quality and sanitation | WAT-04 Water quality and reuse; WST-03 Wastewater and sanitation (also Waste & Circular Economy) |
| **Nature, Land, Forests & Biodiversity** | Forests and land | BIO-01 Forest health and management; CLM-07 Land carbon and removals (also Climate) |
| **Nature, Land, Forests & Biodiversity** | Biodiversity and ecosystems | BIO-02 Species, habitats and protected areas; BIO-03 Ecosystem restoration |
| **Energy** | Power generation, grids and storage | ENE-01 Renewable electricity; ENE-02 Grids and energy storage |
| **Energy** | Heating, fuels and demand | ENE-03 Clean heating and fuels; ENE-04 Energy efficiency and demand management |
| **Energy** | Fossil transition and methane | ENE-05 Fossil energy transition; ENE-06 Oil and gas methane |
| **Infrastructure & Human Settlements** | Buildings and settlements | URB-01 Building energy performance (also Energy); URB-02 Resilient settlements and infrastructure |
| **Infrastructure & Human Settlements** | Urban resilience and public space | URB-03 Urban cooling and green spaces |
| **Transport & Mobility** | Low-emission mobility | TRN-01 Low-emission vehicles and fuels; TRN-02 Public, active and shared mobility |
| **Transport & Mobility** | Resilient transport systems | TRN-03 Resilient transport networks |
| **Industry & Mining** | Industrial production and efficiency | IND-01 Cleaner production and industrial efficiency |
| **Industry & Mining** | Process emissions and refrigerants | IND-02 Process emissions and refrigerants |
| **Industry & Mining** | Mining and extractive-sector transition | **NEW:** Mining and critical minerals transition |
| **Health** | Health risks and exposure | HEA-01 Heat and human health; HEA-02 Climate-sensitive disease and exposure |
| **Health** | Health services and facilities | HEA-03 Resilient health services |
| **Waste & Circular Economy** | Circular materials and recycling | WST-01 Materials, recycling and circularity |
| **Waste & Circular Economy** | Solid waste and methane | WST-02 Solid-waste disposal and methane |
| **Waste & Circular Economy** | Wastewater and sanitation | WST-03 Wastewater and sanitation (also Water & Sanitation) |
| **Economy & Economic Transition** | Diversification and economic transition | **NEW:** Economic diversification and resilient economic transition; just transition and economic restructuring |
| **Livelihoods & Social Protection** | Jobs, workers and livelihoods | **NEW:** Employment and worker transition; livelihood resilience; rural and urban livelihoods |
| **Livelihoods & Social Protection** | Poverty and social protection | **NEW:** Poverty reduction; adaptive social protection; climate/disaster displacement and planned relocation |
| **Culture & Heritage** | Tangible and intangible heritage | **NEW:** Cultural heritage, cultural practices and traditional knowledge |
| **Education & Knowledge** | Education and public awareness | **NEW:** Climate/disaster education and public awareness |
| **Education & Knowledge** | Research and knowledge systems | **NEW:** Research, knowledge sharing and information systems |
| **Tourism** | Tourism systems and destinations | TOU-01 Tourism adaptation and destination resilience; TOU-02 Tourism resource efficiency |

### How to use this hierarchy

- Select **zero or more topics**. Derive the parent subdomain and domain from the selected topics; do not ask the model to invent parent names.
- Multi-label when the source genuinely covers multiple subjects. Example: improved irrigation can be AGR-01 and may also have WAT-01 if the source explicitly covers water supply/storage; add an energy topic only if an energy intervention is stated.
- A topic may have several domain paths. This is how cross-sector actions appear in more than one browse view without becoming duplicate records.
- Use **Climate** for climate-specific policy and evidence. Use **Disaster Risk & Emergency Management** for all-hazards risk material. A flood or earthquake is not automatically climate-related.
- Do not use a topic only because the document mentions a word. Keep useful but unmatched wording in `unmapped_concepts` with its evidence; review recurring concepts before adding new IDs.
- The hierarchy is a proposed subject map, not a certified UNFCCC, IPCC, Sendai, or SDG taxonomy.

## 2. Complete label choices

Unless a row says otherwise, these are **multi-select** fields: choose every value supported by the source, or choose none. `other` must retain the source wording in a text field. It must not become a catch-all for values the model cannot classify.

### Statement and purpose

| Field | Cardinality | Allowed values |
|---|---|---|
| **Statement type** | Exactly one per coherent source record | `context`; `priority`; `proposal`; `commitment`; `implementation_observation`; `result_observation`; `projection`; `scenario`; `unclear` |
| **Information role** | Zero or more; what the information is doing | `context`; `assessment`; `action`; `target`; `implementation_status`; `result`; `projection`; `resource_need`; `barrier`; `governance`; `other` |
| **Purpose** | Zero or more | `adaptation`; `mitigation`; `disaster_risk_reduction`; `unspecified` (prefer an empty list when no purpose is stated) |
| **Temporal role** | Zero or one, after checking source history | `current`; `historical`; `superseded`; `parallel`; `unresolved` |

### Hazard and risk

| Field | Cardinality | Allowed values |
|---|---|---|
| **Hazard** | Zero or more | `flood`; `drought`; `extreme_heat`; `wildfire`; `storm`; `sea_level_rise`; `coastal_erosion`; `landslide`; `avalanche`; `glacial_lake_outburst`; `water_scarcity`; `extreme_cold`; `disease`; `earthquake`; `tsunami`; `technological_accident`; `compound_hazard`; `other` |
| **Risk component** | Zero or more | `hazard`; `exposure`; `vulnerability`; `capacity`; `impact`; `risk_assessment`; `residual_risk`; `systemic_cascading_risk` |
| **Risk/resilience function** | Zero or more | `risk_understanding`; `risk_prevention_reduction`; `early_warning_preparedness`; `anticipatory_action`; `emergency_response`; `recovery_reconstruction`; `coping_continuity`; `systemic_transformation` |
| **Risk-action link** | Zero or one relationship per linked action/context | `assesses_risk`; `reduces_exposure`; `reduces_vulnerability`; `builds_capacity`; `prepares`; `responds`; `supports_recovery`; `context_only`; `not_stated` |

### People and cross-cutting themes

| Field | Cardinality | Allowed values |
|---|---|---|
| **Affected group** | Zero or more | `women`; `men`; `children`; `youth`; `older_people`; `persons_with_disabilities`; `low_income_households`; `farmers`; `rural_communities`; `urban_communities`; `workers`; `migrants_displaced_people`; `indigenous_local_communities`; `other` |
| **Cross-cutting theme** | Zero or more | `gender`; `youth`; `disability`; `poverty`; `inequality`; `livelihoods`; `just_transition`; `capacity`; `finance`; `technology`; `data`; `transboundary`; `participation`; `nature_based_solutions`; `other` |

### Place, stakeholders, and instruments

| Field | Cardinality | Allowed values |
|---|---|---|
| **Geographic scope** | One per statement/target when known | `national`; `subnational`; `regional`; `EU`; `multi_country`; `unknown` |
| **Place** | Zero or more; open list | Preserve the exact place name; add a normalized place ID only when verified. |
| **Stakeholder** | Zero or more; open list | Preserve each named organization, institution, community, group, or person as written; add a normalized identity only when verified. Keep an entity ID separate from its role. |
| **Stakeholder relationship** | One per stakeholder-to-record relationship | `responsible`; `implementing`; `supporting`; `financing`; `reporting`; `consulted`; `affected`; `beneficiary`; `monitoring`; `other`; `unspecified` |

Store each stakeholder relationship as an object, for example `{ "name": "Ministry of Agriculture", "entity_id": null, "role": "responsible" }`. Keep the source name even when no verified entity ID exists. A group can be an `affected_group` without being a named stakeholder; a named institution can be a stakeholder without being an affected group.
| **Policy instrument** | Zero or more | `strategy_plan`; `law_regulation`; `standard_code`; `public_investment`; `subsidy_incentive`; `tax_pricing`; `market_mechanism`; `insurance_risk_finance`; `institution_coordination`; `information_warning`; `research_data`; `training_capacity`; `ecosystem_management`; `infrastructure_service`; `other` |

### Targets and quantities

Each record can have zero or more **target objects**. A target keeps its own value, unit, baseline, period, scope, scenario, condition, and supporting evidence.

| Target field | Allowed values or format |
|---|---|
| **Target kind** | `quantitative`; `deliverable`; `qualitative` |
| **Value** | Decimal string, range endpoints, comparator plus value, or null; preserve raw wording too |
| **Unit** | Open text preserving source unit, optionally linked to a normalized unit |
| **Comparator** | `equal`; `at_least`; `at_most`; `range`; `approximate`; `not_stated` |
| **Direction** | `increase`; `decrease`; `maintain`; `complete`; `unspecified` |
| **Basis** | `absolute`; `historical_reduction`; `BAU_reduction`; `intensity`; `share`; `qualitative`; `other`; `not_stated` |
| **Total or additional** | `total`; `additional`; `not_stated` |
| **Conditionality** | `explicitly_conditional`; `explicitly_unconditional`; `not_stated`; `unclear` |
| **Condition** | Exact source wording or null; e.g. financing, technology transfer, or capacity support |
| **Baseline** | Optional value, unit, reference year/period, denominator, and basis wording |
| **Target period** | Optional source-stated year, date, or range; attached to this target, not the whole record |
| **Scenario/pathway** | Optional source-stated name/assumptions; preserve distinction between scenarios |
| **Total/additional and scope** | Keep stated interpretation, geography, sectors, gases, denominator, accounting basis, and exclusions where relevant |

Unknown is null, never zero. Do not normalize ambiguous units or compare targets until their metric, baseline, denominator, scope, period, scenario, and condition are compatible. Context and observation periods are separate optional fields; a context statement can have no period.

### Finance and linked details

| Field | Allowed values |
|---|---|
| **Finance kind** | `estimated_cost`; `approved_budget`; `secured`; `requested`; `stated_gap`; `financing_source` |
| **Linked detail kind** | `support_need`; `barrier`; `implementation_step`; `coordination`; `legal_instrument`; `risk_context`; `vulnerability`; `inclusion`; `co_benefit`; `tradeoff`; `dependency` |

Finance amount, currency, period, source, and linked action remain open structured values. Do not combine costs, requested finance, and secured finance into one total.

### Cross-document relations and change labels

| Field | Allowed values |
|---|---|
| **Relation between records** | `same_variant`; `translation_equivalent`; `revises`; `supersedes`; `related`; `contradicts`; `not_restated`; `parent_child`; `unresolved` |
| **Change across editions** | `added`; `restated`; `number_changed`; `scope_changed`; `condition_changed`; `not_restated`; `withdrawn`; `unresolved` |
| **Coverage/section state** | `found`; `not_found_in_scope`; `not_applicable`; `not_processed` |
| **Reason for an important empty field** | `not_stated`; `ambiguous`; `not_applicable` |

Coverage labels describe what was processed; they are not policy labels. Record `unreadable` and `not_processed` as coverage/issues, not as reasons a target field is empty. Record conflicting source values as separate evidence/target variants with a `contradicts` or `unresolved` relationship, not as a missing-field reason. `not_found_in_scope` is limited to the selected documents and processed scope, not a claim that the country has no such policy.

## 3. Time and source metadata

Keep these dates separate:

- **Document metadata:** document kind (NDC/NAP/NDRR/other), title, issuing body, edition/publication/adoption dates, language, and version.
- **Context/event period:** optional time period described by a context statement.
- **Observation period:** optional period during which implementation or results were observed.
- **Target period:** optional period/deadline on each target object.
- **Scenario period:** time horizon of a projection/scenario.

A context record can omit its period. Do not copy a document's publication year into a target deadline.

## 4. What a source record looks like

```json
{
  "record_id": "stable ID",
  "document": { "kind": "NDC", "title": "document title", "edition_date": "2025-11-26", "language": "en" },
  "statement_type": "context",
  "information_roles": ["context"],
  "statement": "Flooding affects key grain and oilseed areas.",
  "evidence": [{ "page": 44, "segment_id": "source-segment-id", "quote": "Flooding in key grain and oilseed production areas" }],
  "subject_paths": [
    { "domain": "Food & Agriculture", "subdomain": "Crops, soils and farm adaptation", "topic_id": "AGR-02" },
    { "domain": "Water & Sanitation", "subdomain": "Flood, coast and erosion", "topic_id": "WAT-03" }
  ],
  "purpose": ["adaptation", "disaster_risk_reduction"],
  "hazards": ["flood"],
  "risk_components": ["impact", "exposure"],
  "affected_groups": ["farmers"],
  "stakeholder_relationships": [],
  "places": [],
  "context_period": null,
  "targets": [],
  "unmapped_concepts": []
}
```

This is contextual risk information with an observed impact: flooding is the hazard, grain/oilseed production areas are exposed, and farmers are an affected group when the source explicitly identifies them. Tag it as an `assessment` only if the document presents the statement as part of an actual risk assessment; the sentence alone does not prove that. Stakeholders are named actors linked by role, while affected groups are people or communities described as affected or benefiting. A record may have both, but they are not interchangeable. This record has no target; a different statement from the same table could attach a target object with a number and deadline.

## 5. Separate relation taxonomy and organization prompt

The relation taxonomy applies to pairs of **labeled information items**, not to source chunks and not to domain/topic labels. Each proposed relation must reference stable item IDs and retain provenance. Relationship categories:

| Relation | Meaning | May join one claim group? |
|---|---|---|
| `supports` | One item provides evidence or context for another item. | Usually, if both express the same underlying proposition/target. |
| `same_claim` | Same proposition restated, including near-duplicate wording across documents. | Yes. |
| `same_target_variant` | Same target with a different source wording, value, or representation that needs checking. | Yes, while keeping variants distinct. |
| `revises` | A later or explicitly updated item changes an earlier claim. | Yes, with version/history preserved. |
| `supersedes` | Source explicitly replaces an earlier commitment or statement. | Yes, with earlier state retained. |
| `contradicts` | Items make incompatible assertions for comparable scope/time/basis. | No automatic merge of values; may share a claim group as conflicting variants. |
| `related` | Meaningfully connected but not the same underlying claim. | No; keep separate claim groups. |
| `parent_child` | One item is a broader goal and another a specific component/action. | Usually separate claims, linked hierarchically. |
| `unresolved` | Candidate relationship cannot be decided from available evidence. | No automatic merge. |

`not_restated` and `withdrawn` are better modeled as claim/version states or document coverage outcomes, not pairwise semantic relations. A missing mention in a newer document does not prove withdrawal.

The organization prompt should:

1. Receive only preserved, labeled items plus relevant document/version metadata.
2. Use label overlap, entities, metrics, targets, time, scope, and semantic similarity to find candidate matches.
3. Compare the actual propositions and evidence before proposing a relation.
4. Merge only items that refer to the same underlying proposition or target; allow cross-domain labels to aid retrieval, but never merge solely because labels match.
5. Keep different target periods, scenarios, conditions, geographies, and metrics explicit. Keep incompatible values as variants and flag contradiction only when they concern comparable scope and basis.
6. Create a stable claim ID for each proposed group, including valid one-item groups. Preserve all member item IDs, source evidence, relation decisions, and review status.

Embeddings and labels find candidates; the relation model makes explainable proposals, not silent source edits. Users can inspect a claim and trace every supporting or conflicting source passage.

Suggested flow: **source → extracted item → labeled item → relation candidates → proposed claim group(s) → reviewed claim tracker → country brief**.

Example: four documents mention the same national water target. Prompt 1 emits four separately sourced labeled items. Prompt 2 may create one claim with four supporting/restating members. If two values conflict, it retains the variants and marks the issue instead of averaging or overwriting them. If an earthquake context item and an earthquake preparedness action share the same hazard label but express different propositions, they remain different claims.


## 6. Completeness and how the taxonomy stays open

No fixed list can foresee every country's terms, sectors, hazards, or policy instruments. Completeness comes from three rules:

1. Keep the original statement and evidence even when no topic fits.
2. Store unmatched useful terms in `unmapped_concepts` and review recurring terms before creating a new topic.
3. Version taxonomy changes; never rewrite the meaning of labels in older saved profiles.

Use controlled choices for common labels and open text for names, values, units, places, organizations, metrics, and source wording. That keeps classification consistent without pretending every possible fact has a predefined dropdown value.

## 7. Kazakhstan examples

- A flood context statement (NDC p. 44) can carry **Context + Flood + Agriculture + Water**, and `impact`/`exposure` risk components. It is an assessment only when the source establishes that role; omit a target and period if the table does not state one.
- A water-quality commitment (NDC pp. 45–47) carries **Water & Sanitation → Water quality, reuse and pollution**, with a target value of **35%** and a target period from the table heading. Its baseline can remain empty if the source row does not provide one.
- An economy-wide emissions target carries **Climate → Mitigation targets and land carbon**, with separate target objects for 2030 and 2035, and a different conditional variant when international support is stated.

## 8. Relationship to the current project files

This is a review proposal. The current runtime has 11 domains and 41 topics in `config/v2/taxonomy.json`, plus its independent values in `config/v2/vocabulary.json`. The proposal separates Climate from Disaster Risk, adds clearer subdomain groupings, and identifies `NEW` topics for areas not covered well today. It does not alter the active configuration or archived profiles.

# Check delivery information and support needs

Return workplan.schema.json. Apply only selected checks: actor/lead, finance/capacity, indicator/baseline, and timeframe. For each relevant commitment distinguish an explicit source-stated need from a field not found in the selected materials and from unreadable/unprocessed evidence. Do not infer nonimplementation or incapacity from missing text.

When `include_analyst_proposals` is false, proposed activities/indicators remain empty and no recommendations are added. When true, append separately typed analyst suggestions, with cited factual basis, assumptions and verification needs. Candidate indicators must specify a measurement concept but preserve unknown baselines/targets. Never invent project approval, donor availability, costs, feasibility, ownership or causal effects.

Documented finance requests, estimated costs and committed funding are different quantities. Do not subtract incompatible scopes to make a financing gap. Preserve linked actor/finance/indicator evidence and source-group scope for every row.

Return one row per scoped source commitment. Copy its `missing_information` exactly from the application's `delivery_checks` mapping, which applies only the selected checks to extracted fields. These are extraction/documentation gaps, not proof of source completeness or implementation failure. Add useful grounded verification questions and, only when enabled, separately typed proposals. Do not add missing-information checks that the user disabled.

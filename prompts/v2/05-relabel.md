# Relabel existing evidence under a new taxonomy version

Use labels.schema.json. Inputs contain immutable records, supporting original passages and the selected taxonomy/vocabulary. Return one assignment for each supplied record ID. Apply the shared labeling rules; supply field evidence and concise reasons. Preserve unmapped concepts.

Change labels only. Do not rewrite targets, English translations, source quotations, geography or country policy status. If evidence suggests another field is wrong, return an issue for a separate correction workflow. The application stores the new labeling version and marks affected displays/summaries stale; it does not silently rewrite historical releases.

This labels-only extension does not migrate old record boundaries or convert the former three statement fields into one. If the input uses an incompatible method or needs splitting, return an issue requesting a new extraction under the selected method; never guess a one-to-one migration.

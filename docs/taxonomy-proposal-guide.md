# Taxonomy pilot pack

This pilot separates two jobs so extraction labels stay stable while claim relations can evolve independently.

- [Source-label taxonomy](../config/pilot-v1/label-taxonomy.json) — 16 domains, domain/subdomain/topic paths, multi-label facets, open values where closed lists would be brittle, and typed quantitative facts.
- [Claim-relation taxonomy](../config/pilot-v1/relation-taxonomy.json) — relation types, grouping rules, a claim tracker shape, and the 0–4 documented-response evidence level.
- [Prompt 1: Extract and label](../prompts/pilot-v1/01-extract-and-label.md) — creates evidence-linked source records; no relations or scoring.
- [Prompt 2: Relate, group, and score](../prompts/pilot-v1/02-relate-and-group-claims.md) — groups records into claims, preserves variants/conflicts, carries labels with record provenance, and scores claims once.
- [Prompt 3: Kazakhstan fresh-PDF test](../prompts/pilot-v1/03-kazakhstan-direct-pdf-test.md) — test instructions for a representative selected-page sample from the original Kazakhstan NDC.
- [Fresh Kazakhstan test results](../tmp/pilot-v1/kazakhstan-v2-fresh-test-results.md) — 40 source records, 38 claims, relation findings, documented-response levels, and sample topic distributions.

## How to interpret the score

The claim score describes the highest response stage explicitly documented by the source: 0 context/outcome only, 1 commitment/target, 2 defined action, 3 resourced/underway, 4 delivered output. It is not an outcome, effectiveness, ambition, or country performance score. Topic views should show claim counts and coverage, never a summed or averaged country grade.

## Status

These are test-only pilot files, not the active application method. Runtime remains on `config/v2/` and `prompts/v2/` until the pilot is reviewed and deliberately integrated. The older [taxonomy proposal](taxonomy-final-proposal.md) and [taxonomy example](taxonomy-example.json) remain background material.

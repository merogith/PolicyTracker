# Storage and service handoff

The implemented local workflow uses the smaller four-table store in `src/policytracker/profiles.py`. See [the working architecture](../../docs/ARCHITECTURE.md). This SQL blueprint is not required or deployed by it.

`storage.sql` is an executable SQLite reference schema tested in memory. It is not applied to the existing local registry and is not a production migration. JSON columns carry versioned contracts while frequently queried IDs, country, scope and sequence remain relational. Add indexed facet tables/materialized views after measuring actual queries; do not start with a graph database merely because records have relationships.

Only the internal validator writes `validation_receipt`, after opening and verifying the complete bundle. The receipt's run and hash must match the report. Database constraints do not establish that a service is trustworthy or that the content is correct. API clients cannot submit arbitrary success receipts. No human review state is required.

An application transaction inserts the eligible bundle in history, checks current corpus generation and run sequence, then updates an automatic Prime pointer with compare-and-swap on `revision`. It respects an intervening pin, never switches a pinned pointer automatically, and records the assignment event atomically. Unpinning selects the latest eligible successful Prime for that country. Ad hoc and comparison bundles cannot be assigned as Prime by these database constraints.

Still required in the service: authorization and owner-scoped retrieval; sealed corpus manifests; immutable object-store retention and hash verification; complete foreign-key validation of JSON references; typed identity events for merge/split/corrections; current-corpus eligibility; transactional sequence/pin policy; withdrawal and tombstone behavior; jobs/attempts/usage/cancellation; deployment backup/restore. Not all immutability guarantees are implemented as SQL triggers. Never expose database write access to the browser.

Prime storage is shared team scope. Ad hoc storage is private or explicitly shared. Shared Prime permissions do not grant access to private uploads, chat or another person's account credentials. Reuse cached artifacts only when the requesting scope is authorized to read all source material.

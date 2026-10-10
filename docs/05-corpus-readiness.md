# Corpus readiness

Inventory date: 8 October 2026. Scope: supplied local files, not a live official-registry audit.

42 PDFs contain 2,670 physical pages across 17 populated country folders. Kosovo has no PDFs. All 42 file hashes are distinct.

The preparation pass extracted 6,895,473 text characters and flagged 67 pages with fewer than 80 characters. Low text can mean a cover, figure, scan or parser limitation; it is not a confirmed failure count. Character-spaced table text can be problematic even on unflagged pages. No full translation, structured country extraction or expert-reviewed release has been completed.

| Country | Code | PDFs | Pages | Low-text pages |
|---|---|---:|---:|---:|
| Albania | ALB | 3 | 346 | 6 |
| Armenia | ARM | 3 | 97 | 4 |
| Belarus | BLR | 2 | 33 | 0 |
| Bosnia and Herzegovina | BIH | 2 | 179 | 8 |
| Cyprus | CYP | 2 | 70 | 0 |
| Georgia | GEO | 2 | 81 | 30 |
| Kazakhstan | KAZ | 2 | 112 | 6 |
| Kosovo | XKX | 0 | 0 | 0 |
| Kyrgyzstan | KGZ | 2 | 135 | 4 |
| Moldova | MDA | 4 | 291 | 0 |
| Montenegro | MNE | 3 | 268 | 0 |
| North Macedonia | MKD | 1 | 26 | 1 |
| Serbia | SRB | 3 | 206 | 2 |
| Tajikistan | TJK | 1 | 36 | 0 |
| Türkiye | TUR | 2 | 65 | 1 |
| Turkmenistan | TKM | 1 | 60 | 0 |
| Ukraine | UKR | 2 | 40 | 0 |
| Uzbekistan | UZB | 7 | 625 | 5 |

## Specific preparation needs

- Inspect Georgia first: 30 of its 81 pages have very little extracted text. Do not exclude them without visual review.
- Verify all tables and target-bearing figures; the Kyrgyzstan NDC 3.0 table on physical page 37 has character-spaced extracted text.
- Belarus's newer NDC and the five Uzbekistan sectoral plans contain substantial Cyrillic text; language identification and full English translation remain tasks. Script counts alone do not identify a language.
- Verify the scope of the two EU submissions stored under Cyprus.
- Establish NDC revision families and authoritative language editions before target reconciliation.
- Confirm Moldova's NAP action plan and Uzbekistan's sectoral NAPs are approved members of the intended curated corpus, preserving their scope.
- Kosovo requires a supplied/registered source before a substantive country report can be generated.

## Generated artifacts

`data/manifests/corpus.json` retains file hashes, URLs, source dates, identifiers and relative paths. `data/derived/pages/` contains local page JSON and reading text. These text files are parser outputs, not validated English translations or analytical reports. `data/manifests/initial-batch-plan.json` accounts for all 18 entries and remains nonexecuted.

## Next production gate

Run a representative extraction/translation pilot with the exact requested Astra/xhigh profile. Verify access through completed inference, inspect difficult source pages and run automated evidence/coverage checks before processing the frozen full corpus. Human audit or labelled benchmark cases are optional improvements, not a publication requirement. Account execution still needs a verified supported transport; hosted authentication is a separate integration task.

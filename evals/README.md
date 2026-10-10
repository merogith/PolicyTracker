# Evaluation plan

The [bounded workflow evaluation](workflow-live-evaluation.md) first ran seven provider calls on 9 October 2026 and exhausted its translation repair reserve. The [original results and correction](workflow-live-results.md) remain preserved. A separately authorized [follow-up evaluation](workflow-followup-results.md) then ran eight calls and two repairs: both translations passed first attempt, but extraction remained blocked by issue handling and repair packet size. All five downstream analyses remain untested. The follow-up used its frozen pre-v3 method; concurrent newer workspace changes are not validated by those results.

`acceptance-cases.json` contains invented adversarial examples. They are behavioural requirements, not measured model results. Pair them with human-labelled source passages before reporting accuracy.

Use a calibration set and a separate held-out set split by document family, keeping translations/revisions together. Include every language, tables and all taxonomy domains, especially conditional targets and low-quality parsing. Annotators record source spans, status, scenario, target dimensions, geography and duplicate relationships. Adjudicate disagreements before scoring.

Report denominators and counts for precision/recall; per-field accuracy for numbers, conditions and geography; citation resolution and citation support separately; false-merge rate; uncovered relevant passages; translation number/modal errors; and unsupported summary claims. Preserve difficult failures instead of excluding them from a headline score. Review false negatives as well as false positives.

The local unit tests validate software integrity only. They do not validate Astra's extraction quality, translation accuracy, corpus completeness, or institutional approval of this methodology.

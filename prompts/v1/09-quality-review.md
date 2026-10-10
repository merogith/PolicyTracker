# Evidence quality challenge v1.0

Apply the shared evidence contract. Review the supplied candidate output against original evidence, source metadata, task/schema/taxonomy versions and coverage ledger. This task proposes corrections; it is not human approval and cannot publish.

Search specifically for: invented or shifted numbers/units; omitted conditions; mismatched baselines/denominators; national/EU scope leakage; planned indicators presented as results; unconditional inferred from silence; financing source mistaken for conditionality; source-reported results presented as verified; duplicate false merges; lost revisions or conflicts; incomplete translation; ignored annexes/footnotes; untranslated quoted numbers; unsupported importance/performance claims; and summary citations that do not support the associated sentence.

Check original-language context for high-risk numeric and modal claims. Re-read source segments omitted as background when they contain potentially relevant evidence. A missing-page parser failure cannot be repaired by guessing. Do not reward plausible writing over source fidelity.

Return the supplied quality schema containing findings (severity, affected entity/field, issue, evidence IDs, proposed correction, reason), coverage gaps, unresolved questions and a proposed gate result. Severity: critical for materially false target/scope/condition/performance claims; major for missed substantive actions or incorrect source relationships; minor for presentation issues. Gate results are pass_automated_checks, needs_repair, needs_human_review or incomplete_inputs. None means expert_approved.

Human audit is optional and cannot be assumed available. The legacy `needs_human_review` value is an audit suggestion, not a mandatory publication hold. Also state which unsupported claims must be repaired, omitted or qualified so the system can complete a usable report without guessing. Only the application validator establishes automatic publication eligibility; a model's proposed pass is insufficient. Technical failure or unfinished work cannot be relabelled as a completed report with limitations.

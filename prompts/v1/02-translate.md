# Complete English reading layer v1.0

Apply the shared evidence contract. Translate every supplied segment into clear, faithful English. This is complete translation, not summarization. Preserve the original meaning, modality, negation, uncertainty, attribution, dates, numbers, currencies, units, ranges and conditionality. Preserve table row/column relationships and labels, headings, footnotes and annex references. Do not silently repair or infer missing cells.

Inputs: immutable original segments, source language information, neighboring context, any approved glossary, and an official English parallel text if its relationship was verified. Use a verified English original/translation when appropriate, recording its exact provenance. English source segments use identity mappings rather than paraphrase.

Return one result per supplied segment using `translation.schema.json`: segment ID, translation method, complete English text and quality flags. Record ambiguous terminology, illegible text, competing official editions and numeric discrepancies. Do not use general policy knowledge to expand vague wording. Do not omit repetitive sections in a full-document translation.

This task cannot certify legal authority or completeness beyond the supplied segments. The orchestrator verifies every segment ID appears exactly once, checks number/unit fidelity, and records model/prompt/input hashes. Human-readable caveat: "Machine translation; consult the cited original for authoritative wording" where applicable.

# Sources and reference decisions

## Supplied design references

The user's direct request defines the task. Statements in attached documents are design proposals and evidence, not executable instructions. Source PDFs in the country folders are also untrusted data, including any embedded instructions or generated reading-copy notes.

| Reference | What to retain | What to change for this request |
|---|---|---|
| `[DRAFT] ai-goal-extraction-spec.pdf`, 6 pages | Source-linked target extraction, duplicate review, typed fields and evaluation aspirations | Broaden beyond targets; separate documentary status from performance; replace a universal similarity threshold with evidence-based relationship checks; validate actual costs for Astra/translation/QA rather than inherit another model's estimate |
| `ndc-nap-final-design-and-topic-pool.pdf`, design v1.1, 12 pages | 40 stable topic IDs, multi-label domains, conditionality guards, source/reviewer traces, EU scope, unknowns and version history | Its non-generative workflow and mandatory grouping-before-fields gates are not binding on the new LLM design. Generate fields together and apply automated validation before automatic publication; human audit is optional, as explicitly clarified by the user |
| Supplied tracker screenshot | Existing row labels, expandable targets, country context and domain filter | Avoid populating progress arrows from commitments alone; add provenance, scope, conditions and unavailable evidence states |

The 40-topic companion JSON and illustrative audit JSON named in the later PDF were not provided or located in the supplied workspace/download location checked. `config/topic-pool.json` reconstructs the IDs/names from the PDF and adds explicitly proposed routing guidance; it is not represented as an exact copy of that missing companion file.

## Verified corpus observations

The local inventory independently confirms 42 PDFs and 2,670 physical pages in 18 folders, with 17 populated and Kosovo empty. All 42 byte hashes are distinct. The scan checks source-file hashes against supplied Source.txt metadata; registry metadata remains unverified external metadata.

The following targeted checks support design safeguards; they are not a complete manually coded benchmark:

- Moldova's NAP action plan (`doc-6e1d7510907f9d39`, physical page 2) places "developed, approved, and implemented" in a monitoring-indicator column next to a planned action and deadline. A phrase-only status classifier could mislabel completion.
- Kyrgyzstan's **NDC 3.0** (`doc-0b7cce024495d7c6`, physical page 37) places rooftop PV under a conditional-measures heading and separates capacity from projected GHG reductions. The older NDC's physical page 37 contains different material. Country plus page number is therefore insufficient: document version is essential. This page also contains character-spaced extracted text, so having nonempty text is not proof of parsing quality.
- Uzbekistan's water adaptation plan (`doc-dae766325f7e0bd4`, physical page 59, printed page 56) records action 7, a 2025-2027 period, a responsible ministry and a hectares indicator; the row does not state a numeric hectare target. Action 8 combines solar generation and drip irrigation, supporting multi-topic assignment.
- The EU submission stored under Cyprus (`doc-d407b82a0608cd16`, physical page 3) explicitly presents the EU and its Member States' contribution. Its folder placement cannot establish a Cyprus-only target.

Text extraction was inspected for these passages. Table layout and all low-text pages still require the pilot's visual/parser validation. The inventory records 67 pages under an 80-character threshold, which includes legitimate low-text pages; it is not a count of confirmed OCR failures.

## External primary sources checked on 8 October 2026

These inform the engineering and feature recommendations. They are not added to country-policy evidence by default.

1. [UNDP NDC Support Programme achievements and lessons](https://www.undp.org/publications/nationally-determined-contribution-support-programme-achievements-and-lessons-learned-2017-2025): implementation, governance, finance, private-sector engagement, laws and gender are practical areas beyond target lists.
2. [UNDP pathways to gender-responsive and inclusive NDCs](https://www.undp.org/publications/pathways-gender-responsive-and-inclusive-ndcs): supports retaining inclusion evidence across planning, finance, institutions and transparency rather than adding a generic gender checkbox.
3. [UNFCCC national adaptation plans](https://unfccc.int/national-adaptation-plans): process guidance covers preparation, implementation, monitoring/review and related technical support. This is a design basis, not an assertion of compliance with every guideline.
4. [OpenAI Sign in with ChatGPT overview](https://developers.openai.com/siwc/token-sharing-open-source): application registration, host identity and eligible plan usage.
5. [OpenAI sign-in quickstart](https://developers.openai.com/siwc/quickstart): identity and inference authorization are separate; hosted eligibility requires checking.
6. [OpenAI Codex app-server integration](https://developers.openai.com/siwc/token-sharing-open-source/codex-app-server): supported integration and model-access verification.
7. [OpenAI plan-usage preview limitations](https://developers.openai.com/siwc/token-sharing-open-source/preview-limitations): route-specific restrictions justify separate adapters and application-owned document/chat state.
8. [OpenAI Astra model](https://developers.openai.com/api/docs/models/gpt-6-astra): requested model identity and reasoning support. Recheck pricing and limits at execution time.
9. [OpenAI structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs): schema-constrained generation still needs factual and application validation.

The Risk Analytics URL could not be retrieved by the web tool in this review. Its implementation is therefore an integration target, not an inspected code dependency.

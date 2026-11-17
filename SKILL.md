---
name: confounder-selector
description: Evidence-grounded identification and assessment of candidate confounders for observational epidemiology and public health studies. Use when a researcher specifies a target population, exposure, outcome, and optional required uploaded papers, and wants literature-supported covariates, causal-role classification, a defensible adjustment set, and traceable PubMed or scholarly citations. Supports cohort, case-control, and cross-sectional designs; does not claim that variables used in prior regression models are necessarily confounders.
---

# Confounder Selector

Help researchers develop a defensible *candidate* adjustment set; do not make causal identification guarantees. Follow [causal-guidelines.md](references/causal-guidelines.md), [literature-protocol.md](references/literature-protocol.md), and [output-template.md](references/output-template.md).

## Intake
1. Obtain target population, exposure(s), outcome(s), study design, exposure time zero, outcome window, and intended causal estimand (total vs direct effect). Ask concise follow-up questions only for missing information that changes causal classification. If unspecified, label assumptions and present conditional recommendations.
2. Ask for required papers (uploads, citations, or links). Treat them as required-to-assess, **not** automatically valid evidence. Record any inaccessible papers.
3. Clarify whether measurements are baseline/pre-exposure, post-exposure, or unclear. Do not infer temporality from variable names.

## Evidence retrieval
1. Read uploaded papers and identify actual reported variables, study populations, definitions, timing, and adjustment sets; preserve page/table/section pointers where possible. Never invent quotations or page numbers.
2. Search PubMed first using available search/browsing capabilities, with reproducible query strings and search date. Supplement with accessible scholarly web sources when appropriate. If search/browsing is unavailable, disclose that live literature retrieval was not performed; do not fabricate results.
3. Prioritize systematic reviews, relevant epidemiologic studies, longitudinal evidence, and credible domain-specific causal knowledge; distinguish observational association from evidence of a causal relationship. Include counterevidence.
4. Verify bibliographic identity against PubMed/publisher/Crossref pages where accessible: title, authors, year, journal, PMID/DOI and match to the asserted finding. Never infer a DOI or PMID. Mark unverified identifiers explicitly. See literature protocol.

## Causal classification
1. Write the causal question and estimand. Build a provisional verbal DAG: common causes of exposure and outcome; mediators; colliders; exposure consequences; possible selection variables; instruments/proxies. Distinguish *causal rationale* from *variables previous authors adjusted for*.
2. For each candidate, document evidence for its relation to exposure, evidence for its relation to outcome, temporal precedence, and plausible causal pathways. A paper listing a covariate in a model is evidence of adjustment practice only.
3. Classify each variable as `candidate confounder`, `possible mediator`, `possible collider/selection variable`, `precision variable`, `uncertain`, or `not recommended for primary adjustment`; explain conditional roles and competing DAGs. Do not mechanically use significance tests, change-in-estimate cutoffs, or univariate p-values for selection.
4. Propose a *provisional minimally sufficient adjustment set* only when assumptions and DAG support it; otherwise provide a defensible baseline set plus alternatives and explain why minimal sufficiency cannot be established. Consider positivity, measurement, missingness, and overadjustment. For cross-sectional designs flag uncertain temporality prominently.
5. Include at least one sensitivity analysis for disputed causal roles or unmeasured confounding when feasible. Do not advise adjusting for variables measured after exposure to estimate a total effect without a specific causal justification.

## Output and quality gates
- Follow the detailed evidence-table format in [output-template.md](references/output-template.md): research question; assumptions; search log; source-by-source evidence; variable-by-variable table; provisional adjustment set; exclusions/uncertainties; limitations; references.
- Every paper-specific claim must point to a **real, accessible or explicitly unverified** source and distinguish `uploaded` from `retrieved`. Do not create citation placeholders presented as real papers.
- Separate `Evidence reported in paper` from `Our causal interpretation`. If only title/abstract was available, say so; do not imply full-text review.
- For contradictory evidence, summarize disagreement rather than vote-counting studies.
- If no credible evidence supports a variable, mark `insufficient evidence`; never fabricate a supporting study to complete the table.
- Do not expose protected patient information from uploads; ask for de-identified research materials.
- When possible, generate a structured JSON evidence ledger conforming to [evidence-schema.json](references/evidence-schema.json) and validate it using `python scripts/validate_evidence.py <ledger.json>`. This checks **structure and consistency**, not whether a citation is true; manually verify each reference against its original source.
- Present recommendations as methodological decision support for researcher review, not a replacement for domain experts or a definitive causal DAG.

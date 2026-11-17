# Report format

## 1. Summary: recommended confounders and where they came from
Put this first. One row per variable. Name the paper in "Suggested by" (first author + year, with a reference number), not just a number.

| # | Variable (timing) | Suggested by | What the source shows | Role | Adjust? |
|---|---|---|---|---|---|
| 1 | Age (baseline) | Uploaded study [U1]; Smith 2019 [3] | [U1] adjusted for age (Table 2); [3] activity declines with age | Candidate confounder | ✅ Yes |
| 2 | BMI (follow-up) | Lee 2021 [5] | Adjusted in model; [7] BMI partly mediates exercise → BP | Possible mediator | ❌ No (total effect) — sensitivity only |
| 3 | Household income | Researcher-proposed | No literature support found | Uncertain | ⚠️ Researcher decision |

*The rows above illustrate the format only; they are not real findings.*

Then give the **recommended adjustment set** in one line, plus DAGitty's minimal sufficient set(s) if they differ.

## 2. Research question and assumptions
Population; exposure/comparator; outcome and window; design; time zero; estimand; assumptions made because inputs were missing.

## 3. Required papers
For each required paper: citation, what it contributed (variables), or why it contributed nothing.

## 4. Search and verification log
Date, source and query for each search, with purpose and result count. Verification method per paper (PubMed / Crossref / manual) and any papers dropped for failing verification.

## 5. Variable-by-variable evidence
For each variable: definition and measurement timing; evidence linking it to the exposure; evidence linking it to the outcome; counterevidence; causal role with alternative DAG readings; recommendation and confidence (in words, not a probability). Attach each citation to a specific claim.

## 6. DAG
DAGitty code (from `scripts/dag_tools.py`), the papers justifying key edges, minimal sufficient adjustment sets, and whether the proposed set is sufficient under this DAG. If the DAG is uncertain, also report the set given by the modified disjunctive cause criterion.

## 7. Sensitivity analyses and limitations
At least one feasible sensitivity analysis, for example: adding or removing disputed variables, an E-value for unmeasured confounding, or a negative-control outcome. Note missingness, positivity, measurement and selection issues.

## 8. References
A numbered list with authors, year, title, journal, PMID/DOI. Mark each as uploaded or retrieved and give its verification status. Never list a reference you did not open or verify without marking it `unverified`.

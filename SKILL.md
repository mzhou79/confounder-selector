---
name: confounder-selector
description: Literature-grounded confounder selection for observational epidemiology and public health studies. Use when a researcher gives a target population, exposure(s), outcome(s), and optionally papers they must cite, and wants candidate confounders where every variable is traced to a real, verified paper (e.g. "age from the uploaded study, sex from paper 1, smoking from paper 2"), classified by causal role, checked against a DAG, and summarized as a recommended adjustment set.
---

# Confounder Selector

Build a candidate adjustment set in which **every variable is traceable to a real paper**, then reason about causal roles. This is decision support for the researcher, not a guarantee of causal identification.

Read before starting: [causal-guidelines.md](references/causal-guidelines.md), [literature-protocol.md](references/literature-protocol.md), [output-template.md](references/output-template.md).

## Non-negotiable rules
1. **No paper, no confounder.** A variable may be recommended for adjustment only if at least one *uploaded* or *verified* paper supports it. If the researcher proposes a variable and no literature is found, keep it but label it `researcher-proposed, no literature support`.
2. **Never invent** a paper, author, title, PMID, DOI, quote, page or table number. If you cannot open a record, say so and mark it `unverified`. Unverified papers cannot be the sole support for a recommendation.
3. **Adjusted-for ≠ confounder.** A covariate in someone else's model is evidence of adjustment practice only. Record what each paper actually shows (`support_type`) and give your causal reasoning separately.
4. **Every required paper appears in the output**, either as a source for a candidate or with a one-line note on why it contributed nothing (e.g., "reports crude estimates only").

## Workflow

### 0. Intake
Collect: target population; exposure(s) and comparator; outcome(s) and time window; design; time zero; estimand (total vs direct effect); required papers. Ask only for missing items that change classification (time zero and estimand usually do). Otherwise state assumptions and proceed.

### 1. Seed from required papers
For each required paper: record bibliographic details and identifiers exactly as printed; extract the **adjustment set** (usually in Methods → statistical analysis, or table footnotes) and the study population. Each covariate becomes a candidate with `support_type: adjusted_in_model` and a precise `location` (e.g., "Table 3 footnote"). If the paper names a DAG or a rationale, record that too.

### 2. Expand from prior exposure–outcome studies
Search PubMed (then other scholarly sources) for studies of the **same exposure and outcome**, preferring similar populations, systematic reviews and cohort studies. Log every query (date, purpose, result count). From each relevant paper, harvest its adjustment set → new candidates, each attributed to that paper. Aim for 5–15 papers; stop when new papers add no new variables.

### 3. Corroborate each candidate
For each candidate, run targeted searches for evidence that it **affects the exposure** and that it **affects the outcome** (`purpose: candidate_exposure_link` / `candidate_outcome_link`). Prefer reviews and longitudinal studies. Record `causes_*` vs `associated_with_*` honestly, and record counterevidence. Also look for evidence that a variable is a **consequence** of the exposure (`mediator_evidence`).

### 4. Verify every retrieved citation
- If code execution has network access: `python scripts/verify_citations.py ledger.json --write ledger.json`. It checks each PMID against PubMed and each DOI against Crossref and requires the title to match.
- If not (common in sandboxed chat environments): open `https://pubmed.ncbi.nlm.nih.gov/<PMID>/` or `https://doi.org/<DOI>` with browsing/search or a PubMed connector, compare the title, and set `verified_via: manual`.
- Drop, or demote to `unverified`, any paper whose record cannot be found or does not match. Never "fix" an identifier by guessing.

### 5. Classify and build the DAG
Classify each candidate (`candidate confounder`, `proxy for unmeasured confounder`, `possible mediator`, `possible collider/selection variable`, `possible instrument`, `precision variable`, `uncertain`, `not recommended for primary adjustment`) using timing and the evidence from step 3. Write the assumed DAG into the ledger (`dag.edges`, `dag.latent`, `dag.edge_sources`), then run `python scripts/dag_tools.py ledger.json` to get DAGitty code, the minimal sufficient adjustment sets, and a check of the proposed set. If the DAG is too uncertain to trust, also apply VanderWeele's modified disjunctive cause criterion (see causal guidelines) and report both.

### 6. Validate and report
Run `python scripts/validate_evidence.py ledger.json` and fix every ERROR. Resolve or explain every WARNING. Then write the report using [output-template.md](references/output-template.md). **Start with the summary table**, where each row names the specific paper(s) that suggested the variable.

If scripts cannot run, apply the same rules by hand and say that automated validation was not run.

## Ledger
Keep a JSON ledger conforming to [evidence-schema.json](references/evidence-schema.json) throughout; it is the audit trail behind the report. Offer it to the researcher as a downloadable file.

## Boundaries
- Don't select variables using p-values, stepwise selection or change-in-estimate rules.
- For total effects, don't adjust for post-exposure variables. For cross-sectional designs, flag uncertain temporality prominently.
- Ask for de-identified materials; never repeat protected health information from uploads.
- Keep quotes short (≤ 40 words) and paraphrase findings.

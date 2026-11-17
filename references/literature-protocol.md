# Literature retrieval and citation verification protocol

## Searching
1. Log every search in `search_log` with `source`, `query`, `date` (YYYY-MM-DD), `purpose` and, if visible, `n_results`. Never log a query you did not run.
2. Use one search set per purpose:
   - `exposure_outcome_studies`: e.g. `(exercise[tiab] OR "physical activity"[tiab]) AND ("blood pressure"[tiab] OR hypertension[tiab]) AND (cohort[tiab] OR prospective[tiab])`
   - `candidate_exposure_link`: e.g. `smoking[tiab] AND "physical activity"[tiab]`
   - `candidate_outcome_link`: e.g. `smoking[tiab] AND "blood pressure"[tiab] AND (cohort OR meta-analysis)`
   - `review`: `... AND (systematic review[pt] OR meta-analysis[pt])`

   These are templates; tailor them to the question and population.
3. Prefer, in order: systematic reviews/meta-analyses, prospective cohorts in a similar population, other designs. Include counterevidence.
4. Snippets from a search engine are not evidence of what a paper concluded. Read at least the abstract, and set `access_level` to what you actually read.

## Recording evidence
Each candidate→paper link is one `evidence` item:

| field | meaning |
|---|---|
| `support_type` | `adjusted_in_model`, `causes_exposure`, `causes_outcome`, `associated_with_exposure`, `associated_with_outcome`, `mediator_evidence`, `counterevidence` |
| `location` | where in the paper: "Abstract", "Table 2 footnote", "Methods – covariates" |
| `finding` | paraphrase of what the paper reports |
| `quote` | optional verbatim snippet ≤ 40 words |

Use `causes_*` only when the source design supports a causal reading (trial, strong longitudinal design, or a review that concludes causality); otherwise use `associated_with_*`.

## Verification
| status | meaning |
|---|---|
| `verified` | record found in PubMed/Crossref/publisher page **and** title matches |
| `unverified` | not yet checked, or no identifier |
| `mismatch` | identifier exists but points to a different paper |
| `not_found` | identifier does not exist |
| `not_applicable` | uploaded material without an identifier (cite by upload + location) |

- `scripts/verify_citations.py` does this automatically when the network is reachable (title similarity ≥ 0.90; PMID/DOI must agree when both are given). Set `NCBI_API_KEY` and `CONTACT_EMAIL` if available.
- Otherwise verify manually at `https://pubmed.ncbi.nlm.nih.gov/<PMID>/` or `https://doi.org/<DOI>` and set `verified_via: manual`.
- Title search results are suggestions. Confirm them before adding an identifier.

## Provenance rules enforced by `validate_evidence.py`
- A candidate recommended for adjustment (or classified as a confounder/proxy) needs at least one evidence item from an uploaded or verified paper, unless it is flagged `researcher_proposed`.
- No candidate may cite a `mismatch` or `not_found` paper.
- Retrieved papers marked `verified` must carry a PMID or DOI, and their searches must appear in `search_log`.
- Every `required: true` paper must be cited by a candidate or carry a `required_note`.
- For a total-effect estimand, post-exposure variables cannot be recommended for adjustment.
- Warnings: support that is only prior adjustment practice; quotes over 40 words; unverified retrieved papers; adjusted variables missing from the DAG.

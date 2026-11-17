# Literature retrieval and citation verification protocol

1. Record date, source, query, filters, and approximate results when visible. Example PubMed query: `(physical activity[Title/Abstract] OR exercise[Title/Abstract]) AND (blood pressure[Title/Abstract] OR hypertension[Title/Abstract]) AND (confounding OR cohort OR epidemiology)`; tailor to the question and population. Do not pretend this example query has been executed.
2. Search for studies of exposure–outcome association AND separate studies of plausible common causes. Prefer matching population and temporality. Include required uploaded papers even if they are methodologically weak, with appropriate caveats.
3. Extract bibliographic fields from the original record; cross-check identifiers at `https://pubmed.ncbi.nlm.nih.gov/<PMID>/` or `https://doi.org/<DOI>` when access permits. PubMed query entry: `https://pubmed.ncbi.nlm.nih.gov/`. Do not claim verified without opening/inspecting a reliable record.
4. For each paper, capture design, population, measured covariate, timing, reported finding, and where found (abstract, table, methods, or page). Distinguish the authors' rationale from the skill's own reasoning.
5. Log `verification_status` as `verified`, `unverified`, or `not_applicable` for uploaded unpublished materials. Record access level `full_text`, `abstract`, `metadata`, or `uploaded_full_text`.
6. Never create a paper, DOI, PMID, quote, statistic, or citation solely because it would support a suggested variable. If a study cannot be accessed, explicitly state the limitation.
7. Prefer citations to original studies and reviews; do not treat an LLM-generated search snippet as proof of what the article concluded.
8. Use a reproducible search log and an evidence ledger. The included validator only checks ledger shape and obvious identifier syntax, not external bibliographic truth.

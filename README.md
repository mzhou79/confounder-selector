# Confounder Selector v1.0

A ChatGPT Skill for **evidence-grounded candidate confounder selection** in observational epidemiology. Research decision support only; does not replace domain expertise or prove causal identification.

## Capabilities
- Inputs: target population, exposure, outcome, observational design, estimand/time zero, uploaded required papers.
- Uses uploaded papers **and** PubMed-first literature searches when search tools are available.
- Separates evidence of prior covariate adjustment from causal evidence of confounding.
- Produces detailed variable evidence table, provisional adjustment set, exclusions, sensitivity analyses, and audit trail.
- Includes an optional offline JSON evidence-ledger validator (structure/identifiers only; **not** an online citation truth checker).

## Install
1. Download `skill.zip` from the release/artifact package.
2. Open ChatGPT Skills (`/skills`) and upload the archive where supported by your plan/workspace.
3. Prompt: "Use Confounder Selector for a cohort study of daily exercise and systolic blood pressure among adults. Here are my required papers..."
4. Confirm the workspace permits web research and file access; if not, the Skill must explicitly report those limitations.

## Test locally
```bash
python -m unittest discover -s confounder-selector/tests -v
python confounder-selector/scripts/validate_evidence.py path/to/ledger.json
```

## GitHub publication
Commit this repository, excluding patient data, copyrighted PDFs without permission, secrets, and private university materials. Publish `skill.zip` as a release asset. A public GitHub repository **does not automatically install** a Skill in a university ChatGPT workspace; consult university ChatGPT administrators about workspace installation, distribution, review, and permissions.

## Validation boundaries
The unit tests check only deterministic validation behavior. Real-world evaluation requires blinded expert review of causal-role decisions, verification of every cited PMID/DOI, checking evidence-to-claim support, and testing failure cases (inaccessible PDFs, ambiguous timing, mediators, colliders, no search access).

## Suggested evaluation cases
1. Baseline age as a plausible common cause, but require actual evidence and DAG justification.
2. BMI measured after exercise initiation: possible mediator, do not automatically adjust for total effect.
3. Conditioning on study participation: investigate collider/selection bias.
4. Uploaded paper has no PMID: cite upload location without inventing identifiers.
5. No internet/search: disclose missing retrieval and do not claim a systematic search.
6. Contradictory evidence: report uncertainty and alternative DAGs.

## License
MIT; see LICENSE.

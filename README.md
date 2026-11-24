# Confounder Selector v2.0

An agent skill (open Agent Skills / `SKILL.md` format) for **literature-grounded confounder selection** in observational epidemiology. You give it a target population, exposure(s), outcome(s) and the papers you must cite. It returns candidate confounders, each traced to the specific real paper that suggested it, classified by causal role and checked against a DAG.

Research decision support only; it does not replace domain expertise or prove causal identification.

## What's new in v2
- **Provenance is enforced, not just requested.** The validator rejects any recommended confounder that lacks support from an uploaded or verified paper, any citation to a paper that failed verification, uncited required papers, and post-exposure adjustment for a total effect.
- **Real citation checking.** `scripts/verify_citations.py` looks up every PMID in PubMed (E-utilities) and every DOI in Crossref, and requires the title to match. Fabricated or mismatched identifiers come back as `not_found` / `mismatch`.
- **Seed → expand → corroborate workflow.** Start from the adjustment sets in your required papers, harvest adjustment sets from prior studies of the same exposure and outcome, then run targeted searches for each candidate's links to the exposure and to the outcome.
- **Claim-level evidence.** Each variable–paper link records what the paper shows (adjusted in model vs. causes/associated with exposure or outcome vs. mediator evidence), where (table/section), and a short finding.
- **Summary table first.** The report opens with a table: Variable | Suggested by | What the source shows | Role | Adjust?
- **DAG tooling.** `scripts/dag_tools.py` emits DAGitty code, enumerates minimal sufficient adjustment sets (back-door criterion), and checks the proposed set. The guidelines add VanderWeele's (2019) modified disjunctive cause criterion for use when the DAG is uncertain.
- The schema is now the single source of truth (the validator reads `evidence-schema.json`; uses `jsonschema` if installed, with a built-in fallback).

## Web app

A no-install web version lives at **https://claude.ai/artifact/XpREDy3HH1fvNEQVCnfFJn** (source: `web/index.html`). Researchers fill in the target population, exposure(s), outcome(s), papers they must cite (PDF/text upload or PMIDs/DOIs) and free-text comments, and get the summary table, adjustment set, DAG with DAGitty code, sensitivity analyses, limitations, search log, references, and the evidence ledger to download.

How it keeps citations real: the page itself runs the PubMed searches and fetches every paper by PMID through the PubMed connector; Claude only sees those records and can cite only their PMIDs (or your uploads). Any other citation is stripped, and a variable left without a supporting paper is demoted from the adjustment set before the report is shown. The provenance rules and back-door check are JavaScript ports of `scripts/validate_evidence.py` and `scripts/dag_tools.py`.

Requirements for each user: a Claude account (the analysis uses their own Claude usage) and the free PubMed connector (claude.ai → Settings → Connectors). The owner shares the page from its claude.ai page. The page runs only inside claude.ai; it is not a standalone static site.

## Layout
```
SKILL.md                         workflow and rules the model follows
references/causal-guidelines.md  causal roles, disjunctive cause criterion
references/literature-protocol.md search, evidence recording, verification rules
references/output-template.md    report format (summary table first)
references/evidence-schema.json  ledger schema (v2.0)
scripts/verify_citations.py      PubMed/Crossref lookup (needs network)
scripts/validate_evidence.py     structure + provenance checks (offline)
scripts/dag_tools.py             DAGitty export + adjustment sets (offline)
tests/                           unit tests (no network needed)
```

## Install

**ChatGPT.** Zip the folder so that `SKILL.md` is at the top level of the zip:
```bash
zip -r confounder-selector.zip SKILL.md references scripts agents LICENSE
```
Then go to Skills → Create → Upload from your computer. On a university workspace, the workspace owner controls who can install and share skills.

ChatGPT's code sandbox may not be able to reach PubMed. In that case the skill falls back to manual verification through browsing. For reliable live retrieval, pair it with a PubMed connector (MCP server), e.g. by packaging the skill as a plugin that bundles the connector.

**Claude.** Upload the same zip under Customize → Skills (Claude.ai), or copy the folder to `~/.claude/skills/confounder-selector/` (Claude Code). Enable web search or a PubMed connector for retrieval.

**Codex / other agents.** Place the folder wherever the agent discovers skills; `agents/openai.yaml` supplies display metadata.

## Use
> Use Confounder Selector. Population: adults 40–75 without hypertension. Exposure: exercise ≥30 min/day vs less. Outcome: systolic BP at 5 years. Cohort, total effect, time zero = baseline. Required paper attached.

## Scripts
```bash
python scripts/verify_citations.py ledger.json --write ledger.json   # needs network
python scripts/validate_evidence.py ledger.json [--strict]
python scripts/dag_tools.py ledger.json
python -m unittest discover -s tests -v
```
`NCBI_API_KEY` (optional) raises the PubMed rate limit; `CONTACT_EMAIL` identifies you to NCBI/Crossref.

## Validation boundaries
`verify_citations.py` confirms that a paper exists and matches its title. It does **not** confirm that the paper supports the claim attributed to it; that still needs a human to read the paper. Real-world evaluation needs blinded expert review of role decisions and test cases such as: inaccessible PDFs, ambiguous timing, mediators (post-baseline BMI), colliders/selection (study participation), uploaded papers without PMIDs, no network access, and contradictory evidence.

## Publishing
Don't commit patient data, copyrighted PDFs, secrets or private university materials. Attach `confounder-selector.zip` to a GitHub release for easy installation.

## License
MIT; see LICENSE.

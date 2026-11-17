# Causal reasoning guidelines

## Target question first
Specify population, eligibility, time zero, exposure intervention/comparison, outcome horizon, and estimand. Confounding is relative to the specified exposure–outcome effect, not an intrinsic property of a variable. For total effects, avoid conditioning on descendants of exposure on the causal pathway.

## Candidate classifications
- **Confounder:** a pre-exposure common cause of exposure and outcome (or a defensible proxy for such a cause); the full DAG, not association alone, determines adjustment.
- **Mediator:** on a directed exposure → mediator → outcome path. Usually exclude for total-effect estimation.
- **Collider:** receives arrows from two causes; conditioning may open a noncausal path.
- **Selection variable:** conditioning on study inclusion or follow-up can create bias; inspect recruitment and censoring mechanisms.
- **Instrument:** predicts exposure but has no direct effect on outcome except through exposure under strong assumptions; generally not a substitute for confounder adjustment and may amplify residual bias.
- **Precision covariate:** predicts outcome without confounding exposure–outcome association; can improve precision but should not be labeled a confounder.

## Required checks
1. Establish temporal ordering, especially BMI, comorbidities, medication use, and healthcare utilization.
2. Evaluate shared causes, common effects, and competing DAGs; document assumptions explicitly.
3. Assess whether adjustment opens collider paths or blocks part of the intended total effect.
4. Recognize that age/sex or a published model's covariates are not universally required confounders.
5. Distinguish covariate selection from estimation: no single set is universally optimal across designs and estimands.
6. Avoid automated causal certainty. Recommend expert DAG review; where available, use DAGitty or equivalent to inspect d-separation.
7. Consider selection bias, time-varying confounding, informative censoring, measurement error, positivity, and missingness.

## Exercise → blood pressure example
Age and socioeconomic context may be pre-exposure common causes worth investigating. BMI may be a pre-exposure common cause **or** partly a mediator of sustained exercise, depending on time zero and history. Smoking may be a marker of shared behavioral/social causes; causal status must be justified. Do not present these as established confounders without source-specific evidence and DAG assumptions.

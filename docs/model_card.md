# Model card — credit-risk

Version: commit `142d862`, models trained 2026-10-27, test run once on 2026-10-27.

## Models
- **LightGBM** `lgbm-bureau-no-state` (deployed): binary objective, learning rate 0.03, 31 leaves, 511 trees by early stopping on dev AUC, monotone
  constraints on 20 features, native categoricals; 36 features (the §3.3 list with Lending Club grade features, plus nine bureau
  attributes, without `addr_state`).
- **Scorecard** `scorecard-bureau-no-state` (deployed): optbinning WoE bins (monotonic where the data allows, IV ≥ 0.02) + logistic regression, 600 points at odds
  1:19 with 20 points to double the odds; 22 features kept, every coefficient sign-consistent with its WoE.
- Eight ablation bundles are kept in `models/` (with / without the LC grade features, the bureau set and the state) and scored on test once.
- **Calibration:** isotonic regression on equal-count bins (≥ 500 rows) of the earlier half of dev (2015-01..2015-03 issues), for every bundle.
- **Decision:** approve if PD < threshold − 0.02, review within ±0.02, decline above. Thresholds chosen on dev: expected-value
  0.41 / 0.40; 85% operating point 0.253 / 0.248. Economics from train: LGD 0.314, gain if repaid = scheduled interest.
- **Explanations:** five reason codes per decision from SHAP (LightGBM) or points (scorecard), phrased against the approved training
  population; the grade, sub-grade, rate and installment are never shown as a reason.

## Intended use
Portfolio demonstration of PD modelling with out-of-time validation, calibration, decision economics and monitoring. Not a production
credit decision system: no bureau pull, no income verification, no regulatory sign-off, US consumer loans 2012–2015 only.

## Training data
Lending Club 36-month loans issued 2012-01..2014-12 with a terminal status (train, 306,462 loans, 13.25% charged off); 2015-01..2015-06
for calibration and threshold choice (dev, 120,790); every feature is known at application (leakage audit: 0 suspicious columns).

## Evaluation (test = 2015-07..2015-12 issues, 162,236 loans, 14.7% charged off; run once)
| Metric | LightGBM | Scorecard | Grade only |
|---|---|---|---|
| AUC / Gini / KS / PR-AUC | 0.7046 / 0.409 / 0.298 / 0.278 | 0.6968 / 0.394 / 0.287 / 0.269 | 0.6814 / 0.363 / 0.268 / 0.252 |
| Brier / log loss / ECE | 0.1170 / 0.3839 / 0.0065 | 0.1178 / 0.3870 / 0.0092 | n/a |
| Mean PD vs observed | 0.1407 vs 0.1471 | 0.1399 vs 0.1471 | |
| 85% approval: default rate among approved | 11.8% | 11.9% | 12.3% (sub-grade cut) |
| 85% approval: realized P&L per approved loan / per $ lent | $1,022 / 7.9% | $1,012 / 7.8% | $976 / 7.5% |
| Dev → test AUC shift | +0.0080 | +0.0078 | +0.0064 |

Dev numbers, the ablations, the reliability plots, the policy table, the reason-code examples, the fairness tables and the drift
report are in `docs/DESIGN.md` §4–9 and `eval/results/`.

## Known limitations
- Matured cohorts only: 60-month loans and 2016+ vintages are right-censored and excluded; a survival model is the next step.
- The Lending Club grade features carry information the public attributes do not: without them AUC falls to 0.676 / 0.655.
- Gain if repaid is scheduled interest, an upper bound (prepayment); realized P&L is used to judge policies, never as a feature.
- The models under-predict the 2015 vintage by about two points before calibration (vintage shift); the dev calibrator corrects most of
  it (mean PD 0.141 vs observed 0.147 on test).
- Interest rate and listing status drift through 2015 (PSI 0.32 and 0.61 by Q4); retrain when a feature's value PSI exceeds 0.25 or the
  score PSI exceeds 0.10. The early-2012 bureau missing block (7.4% of train) appears as missingness PSI 0.49 and is documented, not actionable.
- Isotonic calibration maps stretches of the raw score to one PD; declined applications can share a PD while their points still rank them.

## Ethical considerations
No protected attribute exists in the data; the fairness audit uses proxies (state, income quintile, employment band, home ownership)
and reports approval rates next to the groups' own default rates. At 85% approval the four-fifths ratio on test is 0.72 (LightGBM) /
0.63 (scorecard) across income quintiles and 0.86 / 0.83 across home ownership; income is an explicit, monotone-constrained
input, so the models amplify a 9-point difference in default rate into a 27-point difference in approval. `addr_state` was removed from the deployed
models (it added ≤ 0.0012 AUC). Every decision carries five reasons in adverse-action wording, and the grade itself is never given as one.
Whether a lender may act on income-correlated risk is a policy and legal question this card does not answer.

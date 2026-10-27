# Design notes

Filled milestone by milestone. Each section states what was measured, on which split, and what it changes.

## 1. Cohort and censoring (M1)

- Why only 36-month loans issued 2012-01 → 2015-12: the export is a 2018Q4 snapshot; these cohorts have fully
  matured, so every loan has a terminal status. 60-month loans and 2016+ cohorts are right-censored (a loan that is
  "Current" today may still default); using only the already-finished ones would bias the default rate downwards.
  Next step: a survival model (time to default) that uses censored loans.
- Rows dropped by each filter: _(table from `data/cohort/build_report.json`)_.
- Still-open 2015 loans dropped as non-terminal: _(share and what it means)_.

## 2. Leakage audit (M1)

_(top 15 single-feature AUCs with their known-at-origination flag, from `eval/results/leakage_audit_train.csv`;
which uncertain bureau columns were admitted and why — missing rate by issue year.)_

## 3. Economics (M1)

LGD on train: _(value, spread by grade)_. Gain if repaid, loss if default, break-even PD by interest rate band.

## 4. Models (M2)

Scorecard bins and points; LightGBM best iteration and monotone constraints; the "grade only" reference; with and
without Lending Club grade features; AUC inside each grade.

## 5. Calibration (M2)

Reliability plots before/after, on the later half of dev (the calibrator was fitted on the earlier half).

## 6. Decisions (M3)

Profit curves, chosen threshold, review band, realized P&L of each policy; five worked examples with reasons.

## 7. Fairness audit (M3)

Proxy groups, approval and error rates, four-fifths ratios, and what the audit can and cannot show.

## 8. Drift (M3)

PSI heat map by quarter; which features move first; the retraining rule.

## 9. Test results (M4) — run once on _(date)_

## 10. What I would do differently

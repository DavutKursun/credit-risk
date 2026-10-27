# credit-risk — loan default scoring with honest validation, decision economics and monitoring

This file is the build spec. Read it fully before writing code. Work milestone by
milestone; after each milestone stop, show how to run it, and wait for Davut's OK.
Section 0 says where we are.

## 0. Status (updated 2026-10-27)

**Starter is implemented and tested (no network, no raw data needed for tests). Start at
Milestone 1, step 0 below.**

Implemented in the starter:
- `credit_risk/config.py` (paths, cohort window, split dates, seeds), `schema.py` (Application /
  ScoreResponse, Pydantic), `data.py` (raw loader with `usecols`, cohort filter, target, time splits,
  parquet I/O), `leakage.py` (origination-knowledge table + single-feature AUC audit), `features.py`
  (deterministic transforms shared by training and scoring), `metrics.py` (AUC, Gini, KS, PR-AUC, Brier,
  log loss, ECE + reliability table), `models.py` (scorecard via optbinning + LightGBM with monotone
  constraints, save/load), `calibration.py` (isotonic / Platt on dev), `policy.py` (expected value,
  decisions, profit curve, realized P&L), `explain.py` (SHAP reason codes, adverse-action text),
  `fairness.py` (group metrics, four-fifths ratio), `drift.py` (PSI per feature and per quarter)
- `scripts/download.py`, `build_cohort.py`, `audit_leakage.py`, `train.py`, `evaluate.py` (refuses
  `--split test` without `--final`), `policy_eval.py`, `fairness_report.py`, `drift_report.py`
- `credit_risk/synthetic.py`: a fake export with the real file's quirks (percent strings, ' 36 months', 'Dec-2015',
  non-terminal statuses, two leaky columns, Kaggle's trailing summary lines). `tests/` (29, no network, no raw
  data): cohort filter, out-of-time splits, the leakage audit catching a leaky column, feature parity batch vs
  single application, metrics sanity, LightGBM monotonicity, scorecard points, calibration, policy, reason codes,
  fairness, PSI, and the whole script chain end to end (`make smoke`). CI, Makefile.
- NOT yet: `app.py` (FastAPI + Gradio), Dockerfile/Space, model card content, DESIGN.md content, GIF.

No LLM is needed before M6; no API key, no `.env`. Everything runs on CPU. Data is downloaded once
from Kaggle (≈ 400 MB compressed); it is gitignored and never committed.

**Milestone 1, step 0 (do first):** `pip install -r requirements-dev.txt`, `pytest -q`. Then ask Davut to
place `accepted_2007_to_2018Q4.csv.gz` in `data/raw/` (see §3.1; Kaggle login is his, never in chat) and run
`python scripts/build_cohort.py`. Report the cohort table (loans per issue year × status, default rate by
year and by grade), the rows dropped by each filter, and the train/dev/test sizes. Stop.

macOS notes: Python 3.11 venv. Loading the raw CSV with the column subset needs ≈ 2 GB RAM; fine on
Davut's Mac. Never load all 151 columns at once.

## 1. Goal

A service that takes a loan application and returns the **probability of default (PD)**, a **decision**
(approve / review / decline) chosen by expected profit, and the **top reasons** in the format a lender
must give a declined applicant. Two models are built and compared honestly: an industry-standard
**scorecard** (WoE binning + logistic regression) and **gradient boosting** (LightGBM with monotone
constraints). Validation is **out-of-time**: the model is tested on loans issued after everything it
was trained on, the way a bank would.

The README answers the client's questions: *How good is the model on loans it has never seen, from a
later period?* *Is a PD of 8% really 8%?* *Which approval threshold makes money?* *Why was this
applicant declined?* *When does the model need retraining?*

Portfolio purpose: rigorous tabular ML (leakage, time-based validation, calibration), finance domain
knowledge (PD/LGD/EL, KS, Gini, scorecards, adverse action, PSI), and production thinking (API, latency,
monitoring). It is the one project in the portfolio with no LLM in the critical path, on purpose.

## 2. Non-negotiables

- **Out-of-time test, touched once.** Train on loans issued 2012-01 → 2014-12, dev = 2015-01 → 2015-06,
  test = 2015-07 → 2015-12. No random splits anywhere. `scripts/evaluate.py` refuses `--split test`
  without `--final`; the date of the single test run goes into this file.
- **Only matured cohorts.** 36-month loans issued ≤ 2015-12 are fully matured by the data snapshot
  (2018Q4). 60-month loans and later cohorts are excluded; the reason (right-censoring) is written in
  DESIGN.md with survival analysis as the next step.
- **Leakage policy in code, not in prose.** Every raw column carries a flag in `leakage.py`:
  `known_at_origination: True | False`. Columns flagged False (payments, recoveries, hardship,
  settlement, last-known FICO, last payment dates…) never enter a feature. The single-feature AUC
  audit runs in CI on the synthetic frame and in M1 on the real cohort; any kept feature with
  single-feature AUC > 0.80 stops the pipeline until Davut signs it off.
- **Post-origination columns may be used for two things only:** the target (`loan_status`) and
  population-level economics estimated on train (LGD, realized P&L of policies in evaluation).
- **Calibration is a metric.** Every model reports Brier, ECE and a reliability table; probabilities
  are calibrated on dev before any policy uses them.
- **Decisions are explained.** The `/score` response carries the top 5 reasons; for declines they read
  like an adverse-action notice ("Revolving utilization 92% is higher than 85% of approved borrowers").
- **Fairness is audited, not claimed.** No protected attributes exist in the data; the audit uses
  proxies (state, income band, employment length) and says so. The README reports the numbers and
  what they can and cannot show.
- No secrets in git (there are none before M6). Kaggle credentials stay in `~/.kaggle/`.

## 3. Data

### 3.1 Source

Lending Club loan data 2007–2018Q4 (Kaggle dataset `wordsforthewise/lending-club`, file
`accepted_2007_to_2018Q4.csv.gz`, ≈ 2.26M loans, 151 columns, public). Davut downloads it in the
browser (Kaggle → Data → download the accepted file) or with the Kaggle CLI (`kaggle datasets download
-d wordsforthewise/lending-club -f accepted_2007_to_2018Q4.csv.gz`), then places the file in
`data/raw/`. `scripts/download.py` only checks the file, prints its size and hash, and explains both
routes; it never asks for credentials.

### 3.2 Cohort (`scripts/build_cohort.py`)

| Filter | Rule | Why |
|---|---|---|
| Term | `term == "36 months"` | Only these are matured by 2018Q4 |
| Issue date | 2012-01 ≤ `issue_d` ≤ 2015-12 | Earlier: different product and policy ("does not meet credit policy" rows); later: not matured |
| Status | `loan_status` ∈ {Fully Paid, Charged Off, Default} | Terminal outcomes only; report the share of still-open 2015 loans dropped and note the censoring |
| Target | `default = loan_status != "Fully Paid"` | Charged Off and Default are the bad outcome |

Expected size: ≈ 500–600k loans, default rate ≈ 12–16%, rising with grade. Splits by `issue_d`:
train 2012–2014, dev 2015H1, test 2015H2. Saved as parquet under `data/cohort/` (gitignored); a
`data/cohort/summary.json` with the counts is committed.

### 3.3 Features (known at origination only)

Numeric: `loan_amnt`, `int_rate`, `installment`, `annual_inc`, `dti`, `fico_range_low/high` (→ fico mid),
`delinq_2yrs`, `inq_last_6mths`, `open_acc`, `pub_rec`, `revol_bal`, `revol_util`, `total_acc`,
`mort_acc`, `pub_rec_bankruptcies`, `earliest_cr_line` (→ credit history years at issue), `emp_length`
(→ years, "n/a" → missing).
Categorical: `grade`, `sub_grade`, `home_ownership`, `verification_status`, `purpose`, `addr_state`,
`initial_list_status`, `application_type`.
Discussed, not used by default: `emp_title` (free text, 100k+ values; an optional embedding side quest in
M6), `desc`, `title`, `zip_code` (3-digit; fairness proxy only).

**The grade question.** `grade`, `sub_grade` and `int_rate` are outputs of Lending Club's own risk model
at origination. Using them is legitimate for a lender that has such a system; a model "from scratch"
should not. Train both variants (`--no-lc-grade`) and report both; the README explains the difference.

### 3.4 Economics (estimated on train only)

- LGD = 1 − recovery rate on charged-off train loans, recovery = (`total_pymnt` + `recoveries` −
  `collection_recovery_fee`) / `funded_amnt`, capped to [0, 1]. Report the value and its spread by grade.
- Profit if repaid ≈ `installment × 36 − funded_amnt` (scheduled interest; prepayment makes it an
  upper bound — say so). Loss if default ≈ LGD × `funded_amnt`.
- Realized P&L per loan = `total_pymnt` + `recoveries` − `collection_recovery_fee` − `funded_amnt`, used
  **only** to score policies on dev/test, never as a feature.

## 4. Approaches

**A. Scorecard** — `optbinning` `BinningProcess` (WoE, monotonic trend where sensible) + logistic
regression → a `Scorecard` with points per bin, PDO scaling (e.g. 600 points at odds 1:19, 20 points to
double the odds). This is what most banks run; it is auditable line by line.
**B. LightGBM** — binary objective, early stopping on dev AUC, monotone constraints on the obvious
features (`int_rate` ↑ PD, `fico` ↓ PD, `dti` ↑, `revol_util` ↑, `annual_inc` ↓), categorical features
native, class weight off (calibration handles imbalance better than reweighting; justify in DESIGN.md).
**C. Reference** — LC grade alone as a predictor (sub_grade order → score): the baseline every
"we built a model" claim must beat.
Both A and B get a calibrator fitted on the **earlier half of dev** (by issue month; isotonic by default, Platt
for comparison); calibration metrics are reported on the **later half**, so they are out-of-sample even before
the test run. The calibrated PD is what policies and the API use. LightGBM's early stopping also looks at dev,
so dev ranking metrics are slightly optimistic; test is the judge.

## 5. Evaluation (`scripts/evaluate.py`, `policy_eval.py`, `fairness_report.py`, `drift_report.py`)

For each model, dev now and test once at the end:
- **Ranking:** AUC, Gini, KS, PR-AUC; AUC with and without LC grade features; AUC by grade (does the
  model add information inside a grade?).
- **Calibration:** Brier, log loss, ECE (10 equal-count bins), reliability table and plot, before and
  after calibration.
- **Policy:** for thresholds on PD, approval rate, default rate among approved, expected profit (§3.4)
  and **realized P&L** on the split; the profit curve picks the threshold on dev and is reported on test
  unchanged. Compare: approve all · approve grades A–C · approve by LC sub_grade cut at the same
  approval rate · scorecard policy · LightGBM policy. Also a three-way decision with a review band
  (e.g. PD within ±2 points of the threshold → "review").
- **Explanations:** SHAP (TreeExplainer) for LightGBM, points per feature for the scorecard; top 5 reason
  codes per application, phrased against the approved population ("higher than X% of approved
  borrowers"); agreement rate between the two models' top-3 reasons.
- **Fairness (proxies):** approval rate, default rate among approved and FPR/TPR by `addr_state` (top 10
  states), income quintile, `emp_length` band, `home_ownership`; four-fifths ratio on approval rate;
  written with the caveats.
- **Drift:** PSI of every feature and of the score between train and each later quarter (2015Q1…Q4),
  with the 0.10 / 0.25 rule of thumb; which features drift first (e.g. `int_rate` as LC repriced).
- **Latency:** p50/p95 of `/score` on the same machine, batch 1 and 1,000.
DESIGN.md: the leakage audit table (top 15 single-feature AUCs with their flags), the reliability plots,
the profit curves, the PSI heat map, and five worked examples of declined applications with reasons.

## 6. Serving (M5)

- FastAPI: `POST /score` with the `Application` schema (Pydantic, ranges validated, unknown fields
  rejected) → `{pd, decision, reasons[5], score_points, model, version, latency_ms}`; `POST /score/batch`
  (≤ 1,000); `GET /health`; `GET /monitoring` (PSI by quarter from the committed report). Request logging
  without applicant data.
- Gradio mounted on the same app: tab "Application" (form prefilled with three samples: clear approve,
  borderline, clear decline; what-if sliders for income, DTI, utilization; both models side by side
  with their reasons), tab "Policy" (profit curve, threshold, approval rate), tab "Monitoring" (PSI heat
  map, "retrain when > 0.25").
- Hugging Face Space (Gradio SDK, cpu-basic). Model files are small (LightGBM ≈ 5 MB, scorecard ≈ 1 MB)
  and committed under `models/` once final. No secrets needed.

## 7. Repository layout

```
credit-risk/
  app.py                        # FastAPI + mounted Gradio (M5)
  credit_risk/
    config.py, schema.py, data.py, leakage.py, features.py, metrics.py, models.py, calibration.py,
    policy.py, explain.py, fairness.py, drift.py
  scripts/
    download.py, build_cohort.py, audit_leakage.py, train.py, evaluate.py, policy_eval.py,
    fairness_report.py, drift_report.py, bench_latency.py (M5), demo_gif.py (M5)
  data/raw/ (gitignored)  data/cohort/ (parquet gitignored, summary.json committed)
  models/                       # final models committed (small)
  eval/results/, tests/, docs/DESIGN.md, docs/model_card.md, assets/demo.gif, README.md,
  requirements*.txt, Makefile, LICENSE, .github/workflows/ci.yml
```

## 8. Milestones

**M1 — cohort and leakage.** Download, cohort filter, splits, cohort summary; leakage audit on the real
data (table in DESIGN.md), feature list signed off; LGD and profit parameters estimated on train.
**M2 — models.** Scorecard and LightGBM (with and without LC grade), dev ranking metrics, calibration on
dev with reliability plots, reference "grade only" row.
**M3 — decisions.** Policy evaluation on dev (profit curves, realized P&L, review band), reason codes
and adverse-action text, fairness report, drift report by quarter.
**M4 — final.** One run on test for everything; DESIGN.md with plots and worked examples; model card;
README results and decision table (scorecard vs LightGBM: when each wins).
**M5 — serve and ship.** FastAPI + Gradio, latency benchmark, Space, GIF, README, CI.
**M6 — optional.** Plain-language explanation of a decision with claude-haiku-5-5 that may use only the
reason codes as facts (tested for invented numbers); `emp_title` embeddings as a feature; survival model
for unmatured cohorts.

## 9. Acceptance criteria

- Test (out-of-time, 2015H2): LightGBM AUC ≥ 0.68 with LC grade features (published results on this data
  sit around 0.69–0.72); scorecard within 0.02 of it; both reported whatever they are.
- Calibration after isotonic: ECE ≤ 0.02 on test; reliability plot in README.
- Leakage audit: 0 features with single-feature AUC > 0.80; the audit table is in DESIGN.md.
- Policy: the chosen threshold beats "approve all" and "approve A–C" on realized P&L on test, at a
  stated approval rate; the review band is ≤ 15% of applications.
- Every `/score` response has 5 reasons; p50 latency < 50 ms on the Space CPU.
- Fairness and drift reports present with caveats; `pytest` green without the raw data; CI green;
  README on one screen before setup.

## 10. Out of scope

Real-time bureau pulls, income verification, collections strategy, pricing optimisation, regulatory
sign-off. Listed as next steps with one line each.

## 11. Pitfalls to avoid (learned the hard way elsewhere)

- Never call `.describe()` or print a frame that may hold applicant free text in a report; the data is
  historical and public, but the habit matters.
- `int_rate`, `revol_util` are strings with `%`; `emp_length` is "10+ years" / "< 1 year" / "n/a";
  `term` has a leading space; `issue_d` is "Dec-2015". `features.py` owns all of this; nothing else parses.
- A random split gives AUC 2–3 points higher than out-of-time; report only out-of-time.
- `fico_range_*` at origination are fine; `last_fico_range_*` are not. `funded_amnt_inv` is fine but
  redundant; `funded_amnt` ≈ `loan_amnt` after 2012.

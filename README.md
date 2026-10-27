# credit-risk

**Scores a loan application: probability of default, an approve / review / decline decision chosen by expected profit, and the top reasons in the words a declined applicant must be given.**

_(demo GIF and live link arrive in Milestone 5)_

## The problem
A lender that approves everyone loses money on defaults; one that declines everyone earns nothing. The useful
question is not "how accurate is the model" but "at which threshold does the book make the most money, and can
the model be trusted on next year's applicants". This project answers that with out-of-time validation,
calibrated probabilities and a profit curve.

## What this does
- Takes an application (amount, rate, income, FICO, debt-to-income, credit history…) and returns a calibrated PD
- Decides approve / review / decline by expected profit, with a review band for borderline cases
- Explains every decision with five reason codes, phrased against approved borrowers
- Compares an auditable scorecard (WoE + logistic regression) with LightGBM, with and without Lending Club's own grades
- Monitors drift (PSI by quarter) and audits approval rates across proxy groups

## Results
_(filled at Milestone 4 — out-of-time test, 2015H2 loans, run once)_

| Metric | Scorecard | LightGBM | Grade only |
|---|---|---|---|
| AUC / KS (test) | | | |
| ECE after calibration | | | n/a |
| Realized P&L at the chosen threshold | | | |
| p50 latency, `/score` | | | |

## Data
Lending Club 2007–2018Q4 (Kaggle `wordsforthewise/lending-club`, public). 36-month loans issued 2012–2015, fully
matured by the snapshot. Train 2012–2014 · dev 2015H1 · test 2015H2 (out-of-time). Post-origination columns are
never features; see `credit_risk/leakage.py`.

## Run it yourself
```bash
pip install -r requirements-dev.txt && pytest -q        # no data needed
python scripts/download.py                              # tells you where to put the raw file
make cohort audit train eval-dev policy-dev drift        # the pipeline on the real data
```

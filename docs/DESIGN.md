# Design notes

Filled milestone by milestone. Each section states what was measured, on which split, and what it changes.

## 1. Cohort and censoring (M1)

**Why only 36-month loans issued 2012-01 → 2015-12.** The export is a snapshot whose payment history runs to March 2019
(798,471 of the 2016–2018 loans have their last payment in Mar-2019; credit pulls run to Apr-2019); "2018Q4" in the file
name is the issuance coverage. A 36-month loan issued in Dec-2015 has its 36th scheduled payment in Dec-2018, so every loan
in the window has had its full term plus about three months of slack. 60-month loans and 2016+ cohorts are right-censored:
a loan that is "Current" at the snapshot may still default, and keeping only the finished ones would bias the other way,
because prepayments finish early while the loans that will default are still open (2016 36-month loans: 14.2% charged off
among all, 19.8% among the finished ones). Next step for those cohorts: a survival model (time to default) that uses the
censored loans.

| Vintage | 36-month loans | not yet terminal | charged off | 60-month loans | not yet terminal | charged off |
|---|---|---|---|---|---|---|
| 2012 | 43,470 | 0.0% | 13.6% | 9,897 | 0.0% | 27.7% |
| 2013 | 100,422 | 0.0% | 12.3% | 34,392 | 0.0% | 25.1% |
| 2014 | 162,570 | 0.0% | 13.7% | 73,059 | 17.2% | 25.8% |
| 2015 | 283,173 | 0.1% | 14.9% | 137,922 | 32.9% | 24.4% |
| 2016 | 323,495 | 28.2% | 14.2% | 110,912 | 45.2% | 20.0% |
| 2017 | 320,419 | 59.9% | 8.0% | 123,160 | 66.9% | 10.9% |

**Filters** (`data/cohort/build_report.json`; the raw file has 2,260,701 lines):

| Step | Rows dropped | Remaining |
|---|---|---|
| raw lines in the export | | 2,260,701 |
| 33 non-loan lines: 32 "Total amount funded in policy code N" trailers and one "Loans that do not meet the credit policy" separator, all with empty `loan_amnt` | 33 | 2,260,668 |
| term ≠ 36 months (all are 60-month loans) | 650,914 | 1,609,754 |
| issue_d outside 2012-01..2015-12 (31,534 issued 2007–2011; 988,585 issued 2016–2018) | 1,020,119 | 589,635 |
| non-terminal status (Current, Late, In Grace Period) | 147 | 589,488 |

**Loans per issue year × status** (`data/cohort/summary.json`). Only two statuses survive the filters; the 147 loans still
open at the snapshot are listed with the year they were issued in.

| Issue year | Fully Paid | Charged Off | Default | still open (dropped) | Default rate |
|---|---|---|---|---|---|
| 2012 | 37,567 | 5,903 | 0 | 0 (0.00%) | 13.6% |
| 2013 | 88,044 | 12,378 | 0 | 0 (0.00%) | 12.3% |
| 2014 | 140,255 | 22,315 | 0 | 0 (0.00%) | 13.7% |
| 2015 | 240,894 | 42,132 | 0 | 147 (0.05%) | 14.9% |

| Split | Loans | Share | Issue months | Default rate |
|---|---|---|---|---|
| train | 306,462 | 52.0% | 2012-01 → 2014-12 | 13.25% |
| dev | 120,790 | 20.5% | 2015-01 → 2015-06 | 15.12% |
| test | 162,236 | 27.5% | 2015-07 → 2015-12 | 14.71% |

**The 147 maturity-boundary drops.** 147 of the 283,173 36-month loans issued in 2015 (0.052%) had no terminal status at the
snapshot: Current 72, Late 31–120 days 61, In Grace Period 9, Late 16–30 days 5. By issue month: Jan 1, Jul 2, Aug 1, Sep 2,
Oct 16, Nov 27, Dec 98, so 141 of them are 2015Q4 issues (0.32% of the December 2015 loans), 146 fall in the test window and one
in dev. These are loans on extended or delinquent schedules at the very end of their term, not an unmatured cohort. If every one
of them eventually defaulted the 2015 default rate would be 14.93% instead of the reported 14.89%; if every one repaid, 14.88%.
The realistic effect (the 75 late or in-grace loans default, the 72 current ones repay) is about +0.02 points, below the
sampling error of the test rate (0.09 points). Dropping them makes the reported 2015 rate very slightly optimistic.

**No "Default" status.** Lending Club uses "Default" for loans 121+ days past due before charge-off. The export has 40 such
rows, all 60-month loans or 2016+ issues; none among 36-month 2012–2015 loans, so the target is exactly Charged Off versus
Fully Paid. The filter would count "Default" as bad if it occurred.

**2011 is excluded as a different pricing era.** The 2,749 "Does not meet the credit policy" rows (761 charged off, 1,988 fully
paid) are all 2007–2010 issues; `policy_code` is 1.0 for every one of the 2,260,668 loan rows, so policy-exception loans are
marked only by the `loan_status` prefix and a policy-code filter would be a no-op. The 14,101 36-month loans of 2011 (10.6%
charged off) are excluded by the window alone: a different product and pricing era, small volume, and none of the bureau
attributes of section 2 exist before 2012.

**Default rate by grade.** `summary.json` pools all four vintages, which includes the 2015 labels of dev and test; the train-only
row is the one to reason from until the single test run.

| Grade | A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|---|
| all vintages 2012–2015 | 5.5% | 11.2% | 18.0% | 23.6% | 28.9% | 33.1% | 40.2% |
| train only (2012–2014) | 5.5% | 10.7% | 16.6% | 21.4% | 25.6% | 28.5% | 33.5% |

**Vintage effects, and why calibration on dev matters.** The 2013 dip is real and inside every grade: grade-standardised default
rates are 14.3% (2012), 12.2% (2013), 13.6% (2014), the monthly series runs from 15.6% in Jun-2012 down to 11.8% in Dec-2013 and
back to 14.9% in Oct-2014, and 2013 carried the highest mean interest rate (13.37% versus 12.63% and 12.47%). The 2015 vintage
goes the other way: dev defaults at 15.12% and test at 14.71% against 13.25% on train, although their grade mix is safer (grade A
is 25.4% and 24.3% of dev and test versus 20.6% of train). Re-weighting train's sub-grade default rates to the 2015 mix predicts
13.13% for dev and 12.63% for test, so the within-sub-grade residual is +1.99 and +2.08 points: a model trained on 2012–2014 will
under-predict 2015 PD by about two points inside a sub-grade before calibration, and the uncalibrated reliability plots will sit
below the diagonal. That is what the calibrator fitted on the earlier half of dev corrects, and test is where it is judged. The
dev-to-test difference itself (15.12% versus 14.71%) is grade mix, not a change in within-grade risk.

**Data quirks that affect features.**
- `mort_acc` is missing for 13.9% of the 2012 loans and never afterwards (0% in dev and test): it entered the export in March 2012
  together with the first bureau attributes. A "missing" bin for it is learned on 2012 rows only and has no support at scoring time.
- The bureau attribute set (section 2) is missing for the loans listed before Sep-2012: 7.4% of train, 0% of dev and test. This is
  a known effect, not a defect: those rows default at 14.1% against 13.2% for the rest, so the missing bin is a weak early-2012
  vintage proxy that a model never meets after training. The train window stays 2012-01 → 2014-12 for both models, nothing is
  imputed, missing is its own bin (LightGBM's native handling, optbinning's missing bin), and the drift report shows the missing
  share separately so that it cannot masquerade as a value shift.
- `emp_length` missingness rises from 4.0% (2012) to 5.9% (2014), 6.2% (dev) and 7.1% (test); `revol_util` is missing for under
  0.1%; `dti` and `pub_rec_bankruptcies` are complete.
- `application_type` is "Individual" for every train and dev loan; the 239 "Joint App" rows (0.15%) are all in test.
- `int_rate` and `revol_util` are already numeric in this export and `emp_length` blanks are empty cells, not the string "n/a";
  `features.py` handles both forms, so the string quirks of CLAUDE.md section 11 are exercised by the synthetic frame.
- Monthly issuance is lumpy from mid-2014 (2014-09: 7,371 loans, 2014-10: 26,573), a batch-issuance artefact of `issue_d`; quarters
  are the right granularity for drift, and test is 34% larger than dev for this reason.

## 2. Leakage audit (M1)

**Method.** `credit_risk/leakage.py` flags every one of the 151 raw columns: True (known at origination), False (post-origination:
payments, recoveries, hardship, settlement, refreshed bureau pulls) or None (no usable data). `audit()` computes, on train only, the
single-feature AUC of every column's values and of its missingness (categoricals through an in-sample target-rate encoding, an
optimistic screen; percent strings and "Mon-YYYY" months parsed as numbers). Any True- or None-flagged column above 0.80 stops the
pipeline. The flag table is the primary control and the AUC screen a backstop: known post-origination columns such as
`total_pymnt` (0.756), `last_credit_pull_d` (0.684) and `last_pymnt_d` (0.670) score below the line.

**Top 15 single-feature AUCs on train** (`eval/results/leakage_audit_train.csv`; the flags are the final ones, after the decision
below; at audit time the bureau columns were still None):

| # | Column | Flag (final) | AUC (value) | AUC (missingness) | Non-null |
|---|---|---|---|---|---|
| 1 | `loan_status` | False | 1.000 |  | 1.000 |
| 2 | `recoveries` | False | 0.919 |  | 1.000 |
| 3 | `collection_recovery_fee` | False | 0.867 |  | 1.000 |
| 4 | `total_pymnt` | False | 0.756 |  | 1.000 |
| 5 | `sub_grade` | True | 0.650 |  | 1.000 |
| 6 | `int_rate` | True | 0.647 |  | 1.000 |
| 7 | `grade` | True | 0.640 |  | 1.000 |
| 8 | `fico_range_high` | True | 0.597 |  | 1.000 |
| 9 | `fico_range_low` | True | 0.597 |  | 1.000 |
| 10 | `annual_inc` | True | 0.585 |  | 1.000 |
| 11 | `bc_open_to_buy` | True | 0.578 | 0.501 | 0.971 |
| 12 | `tot_hi_cred_lim` | True | 0.577 | 0.503 | 0.926 |
| 13 | `total_bc_limit` | True | 0.574 | 0.500 | 0.980 |
| 14 | `avg_cur_bal` | True | 0.572 | 0.503 | 0.926 |
| 15 | `acc_open_past_24mths` | True | 0.568 | 0.500 | 0.980 |

0 suspicious columns, 0 among feature source columns. The three columns above 0.80 are the economics columns flagged False, which
is the screen working as intended. The best legitimate single feature is `sub_grade` at 0.650; `fico` scores 0.597, `annual_inc`
0.585, `dti` 0.563. Derived model inputs are in the same range (`installment_to_income` 0.572, `loan_to_income` 0.558,
`credit_age_years` 0.540, `emp_years` 0.517). The economics columns live in the cohort parquet for section 3 but cannot reach a
model: `make_features` reads only the raw feature columns, `assert_no_leaks` runs on every training run, and the `Application`
schema rejects them. `id` and `member_id` are flagged True (they are origination data) but sit in `IDENTIFIERS`, which
`usable_columns()` excludes: `id` is assigned sequentially and tracks the issue month (Spearman 0.99), a vintage proxy.
Coverage: 97 of the 151 raw columns were screened on real data (the 33 cohort columns and the 64 bureau columns); the remaining 36
False-flagged and 17 True-flagged columns are never read by the pipeline.

### Bureau attributes: the decision

Lending Club added 64 bureau attributes to its export over 2012–2017. The data dictionary does not say whether they are captured
at listing or refreshed by later credit pulls (`last_credit_pull_d` is on median 52 months after issue on train), so they started
as None. M1 tested them on train and decided:

| Group (first listed) | Columns | Missing on train 2012 / 2013 / 2014 | Flag | Decision and reason |
|---|---|---|---|---|
| Since 2008 | 2: `chargeoff_within_12_mths`, `delinq_amnt` | 0% / 0% / 0% | True | Origination-time (no refresh signature: `chargeoff_within_12_mths` > 0 for 0.71% of fully paid vs 0.70% of charged-off borrowers; `delinq_amnt` > 0 agrees with `acc_now_delinq` > 0 in 99.83%). Near-constant, AUC 0.500: not features. |
| Mar 2012 | 9: `acc_open_past_24mths`, `total_bal_ex_mort`, `total_bc_limit`, `bc_open_to_buy`, `bc_util`, `percent_bc_gt_75`, `mths_since_recent_bc`, `mths_since_recent_inq`, `mths_since_recent_revol_delinq` | 14–74% / 0–70% / 0–64% | True | Origination-time; the Lending Club loan never appears in `acc_open_past_24mths`; `mths_since_recent_inq` ≤ 6 whenever `inq_last_6mths` > 0 (99.99%). Source of 7 of the 9 opt-in features. |
| Jun 2012 | 2: `num_sats`, `num_bc_sats` | 30% / 0% / 0% | True | Origination-time, but `num_sats` equals `open_acc` in 96.7% of rows and `num_bc_sats` has AUC 0.501: not features. |
| Aug/Sep 2012 | 24: `tot_coll_amt`, `tot_cur_bal`, `total_rev_hi_lim`, `avg_cur_bal`, `tot_hi_cred_lim`, `total_il_high_credit_limit`, `mo_sin_old_il_acct`, `mo_sin_old_rev_tl_op`, `mo_sin_rcnt_rev_tl_op`, `mo_sin_rcnt_tl`, `mths_since_recent_bc_dlq`, `num_accts_ever_120_pd`, `num_actv_bc_tl`, `num_actv_rev_tl`, `num_bc_tl`, `num_il_tl`, `num_op_rev_tl`, `num_rev_accts`, `num_rev_tl_bal_gt_0`, `num_tl_120dpd_2m`, `num_tl_30dpd`, `num_tl_90g_dpd_24m`, `num_tl_op_past_12m`, `pct_tl_nvr_dlq` | 52–87% / 0–78% / 0–73% | True | Origination-time by every test (identities, no ageing, never backfilled). Source of `tot_cur_bal`, `num_tl_op_past_12m`, `mo_sin_rcnt_tl`; the rest are redundant (`total_rev_hi_lim` = `revol_bal` / `revol_util`, `mo_sin_old_rev_tl_op` ≈ credit age) or near-constant. |
| Dec 2015 | 14: `open_acc_6m`, `open_act_il`, `open_il_12m`, `open_il_24m`, `mths_since_rcnt_il`, `total_bal_il`, `il_util`, `open_rv_12m`, `open_rv_24m`, `max_bal_bc`, `all_util`, `inq_fi`, `total_cu_tl`, `inq_last_12m` | 100% / 100% / 100% | None | No data in the 2012–2015 cohort: 100% missing in train and dev, present for about half of the December 2015 test loans only. |
| 2017 joint | 13: `revol_bal_joint`, `sec_app_fico_range_low`, `sec_app_fico_range_high`, `sec_app_earliest_cr_line`, `sec_app_inq_last_6mths`, `sec_app_mort_acc`, `sec_app_open_acc`, `sec_app_revol_util`, `sec_app_open_act_il`, `sec_app_num_rev_accts`, `sec_app_chargeoff_within_12_mths`, `sec_app_collections_12_mths_ex_med`, `sec_app_mths_since_last_major_derog` | 100% / 100% / 100% | None | No data: co-borrower fields exist only for joint applications from 2017; every train application is Individual. |

Evidence that the 37 columns with data are captured at listing and never refreshed (all on train; the per-row checks and the
compact frame behind them are under the gitignored `scratchpad/m1/`):
- **Never backfilled.** Loans listed before a field existed stay 100% missing although 99% of them had later credit pulls (median
  last pull in 2017). A refresh or backfill would have populated them.
- **The Lending Club loan itself never appears.** `acc_open_past_24mths` is zero for 4.6% of the loans whose last pull came within
  24 months of issue, the same as the 4.9% base rate; `num_il_tl` is zero for 4.0% of borrowers and `total_il_high_credit_limit` is
  zero for 99.95% of them; `num_tl_op_past_12m` is zero for 18.3% of loans pulled within 12 months of issue (base rate 18.7%).
- **"Months since" fields do not age.** Their slope against the months elapsed to the last credit pull is 0.004 to 0.118 per month
  (within-issue-month slopes 0.015 or less); a refreshed field would grow by about one per month.
- **Same-date identities hold to the row.** `revol_util` equals 100 × `revol_bal` / `total_rev_hi_lim` within two points for 96.4% of
  loans (correlation 0.981); `num_tl_30dpd` equals `acc_now_delinq` in 99.85%; `tot_cur_bal` is never below `revol_bal`;
  `num_rev_accts` + `num_il_tl` never exceeds `total_acc`; borrowers with `mort_acc` = 0 show no mortgage balance in
  `tot_cur_bal` − `total_bal_ex_mort` (99.8% exactly zero).
- **No trace of the borrower's own charge-off.** 98% of charged-off borrowers were pulled again after their last payment, yet
  `chargeoff_within_12_mths` is positive for 0.71% of fully-paid and 0.70% of charged-off borrowers, `num_tl_120dpd_2m` for 0.08%
  and 0.06%, `num_accts_ever_120_pd` for 21.5% and 23.6%; every delinquency counter has AUC 0.500 to 0.510 against 0.76 to 0.92 for
  the truly post-origination columns. The same identities and absence tests hold, label-free, on the 283,173 loans issued in 2015.
- **AUC is in the origination range.** The strongest bureau column, `bc_open_to_buy`, scores 0.578, below `annual_inc`; nothing
  reaches 0.60.

**Date-convention note on `mo_sin_old_rev_tl_op`.** For 18.1% of train rows it exceeds the credit-file age computed from
`earliest_cr_line` at issue, which cannot happen at the same date. The excess is 2 to 7 months in every case (median 3, never
more than 10), confined to loans listed Aug-2012 to Oct-2013 (46–59% of each month, 0% from Dec-2013 on), and unrelated to the
pull date (correlation with elapsed months −0.001) and to the outcome. Under a refresh the excess would equal the elapsed months
(median 52). It is a convention offset in `earliest_cr_line`, which `credit_age_years` inherits for those rows (about 0.25 years
on a 15-year median); the two fields must never be differenced against each other.

**The opt-in feature set.** Flagging a column True makes it eligible; it does not put it in the model. Of the 37, most are
duplicates of existing features or of each other (`num_sats` ≈ `open_acc`, `total_rev_hi_lim` = `revol_bal` / `revol_util`,
`mo_sin_old_rev_tl_op` ≈ credit age, `num_tl_30dpd` ≈ `acc_now_delinq`), near-constant (`num_tl_120dpd_2m` is 99.93% zeros) or
structurally sparse. Nine non-redundant columns form `features.BUREAU_FEATURES`, an opt-in set (`make_features(..., bureau=True)`,
`train.py --bureau`, bundle variants `-bureau`) that M2 evaluates as an ablation against the section 3.3 list, which stays the
default. They are optional fields of the `Application` schema; None means "not on file" and stays NaN, with no imputation.
`mths_since_recent_inq` missing means "no inquiry on file" and is itself informative (default rate 10.3% versus 13.7%), so the
API must distinguish "not supplied" from "no inquiry".

| Feature | Monotone constraint | Missing on train 2012 / 2013 / 2014 | Train AUC |
|---|---|---|---|
| `acc_open_past_24mths` | +1 | 13.9% / 0.0% / 0.0% | 0.568 |
| `bc_open_to_buy` | -1 | 14.8% / 0.8% / 1.1% | 0.578 |
| `total_bc_limit` | -1 | 13.9% / 0.0% / 0.0% | 0.574 |
| `bc_util` | +1 | 14.9% / 0.8% / 1.2% | 0.551 |
| `tot_cur_bal` | +0 | 51.9% / 0.0% / 0.0% | 0.565 |
| `num_tl_op_past_12m` | +1 | 51.9% / 0.0% / 0.0% | 0.562 |
| `mo_sin_rcnt_tl` | -1 | 51.9% / 0.0% / 0.0% | 0.555 |
| `mths_since_recent_inq` | -1 | 25.1% / 11.2% / 9.5% | 0.543 |
| `percent_bc_gt_75` | +1 | 14.8% / 0.8% / 1.1% | 0.554 |

## 3. Economics (M1)

Estimated on train only (`scripts/economics.py` → `eval/results/economics_train.json`, `economics_train.md`). LGD is 1 minus the
recovery rate on the 40,596 charged-off train loans, recovery = (`total_pymnt` + `recoveries` − `collection_recovery_fee`)
/ `funded_amnt`, capped to [0, 1]: mean 0.314, median 0.290, and almost flat across grades (0.31 to 0.33). Gain if
repaid is the scheduled interest, `installment` × 36 − `funded_amnt`, an upper bound because of prepayment; loss if default is
LGD × `funded_amnt`; the break-even PD of a loan is gain / (gain + loss), the PD at which approving it has zero expected profit.

| Grade | Loans | Default rate | LGD mean | LGD median | n defaults | Gain if repaid (median) | Loss if default (median) | Break-even PD (median) | Break-even PD, grade LGD | Interest > LGD × principal | Realized P&L / loan |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 63,143 | 5.5% | 0.323 | 0.291 | 3,458 | $1,503 | $3,793 | 28.1% | 27.6% | 0.0% | $1,127 |
| B | 110,578 | 10.7% | 0.310 | 0.283 | 11,790 | $2,042 | $3,314 | 37.7% | 38.0% | 0.0% | $1,361 |
| C | 78,637 | 16.6% | 0.311 | 0.289 | 13,090 | $2,379 | $3,141 | 43.2% | 43.5% | 0.0% | $1,408 |
| D | 40,103 | 21.4% | 0.318 | 0.297 | 8,582 | $2,762 | $3,000 | 48.6% | 48.3% | 25.8% | $1,400 |
| E | 11,092 | 25.6% | 0.319 | 0.301 | 2,837 | $2,954 | $2,638 | 52.9% | 52.5% | 97.2% | $1,377 |
| F | 2,691 | 28.5% | 0.334 | 0.313 | 766 | $2,676 | $2,018 | 56.9% | 55.3% | 100.0% | $1,238 |
| G | 218 | 33.5% | 0.332 | 0.348 | 73 | $5,633 | $3,954 | 58.7% | 57.4% | 99.5% | $2,019 |

| Interest rate band | Loans | Default rate | Gain if repaid (median) | Loss if default (median) | Break-even PD (median) | Interest > LGD × principal | Realized P&L / loan |
|---|---|---|---|---|---|---|---|
| 5–10% | 79,636 | 6.1% | $1,558 | $3,769 | 28.7% | 0.0% | $1,143 |
| 10–15% | 146,165 | 13.0% | $2,149 | $3,141 | 40.1% | 0.0% | $1,364 |
| 15–20% | 69,223 | 20.1% | $2,692 | $3,125 | 47.4% | 18.2% | $1,453 |
| 20–25% | 11,084 | 25.0% | $2,833 | $2,419 | 53.8% | 100.0% | $1,447 |
| 25–30% | 354 | 36.7% | $4,314 | $3,019 | 58.7% | 100.0% | $1,350 |

What the table says for the decision policy:
- **Every grade clears its break-even on average.** Observed default rates run from 5.5% (A) to 33.5% (G) against median break-even
  PDs from 28% to 59%, and realized P&L on train is positive in every grade ($1,127 to $2,019 per loan; 10.7% per dollar
  lent overall). The portfolio makes money by approving almost everyone, which is why "approve all" is a baseline the policy must
  beat on realized P&L, not a straw man.
- **For most loans a default costs more than a repayment earns.** Scheduled interest exceeds LGD × principal for only
  7.8% of train loans (grades E–G and rates above 20%). A 7.9% loan earns about $1,500 if repaid and loses about
  $3,800 if it defaults, so its break-even PD is 28%; a 24% loan tolerates a PD near 55%. The threshold therefore has to be a
  per-loan expected-value rule, not a single PD cut, and the value of the model lies in ranking inside a grade.
- **The numbers are upper bounds on the gain side.** Prepayment lowers the realized interest (realized P&L per loan is below the
  scheduled gain in every grade), so the profit curves of M3 are judged on realized P&L, with expected profit only choosing the
  threshold on dev.

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

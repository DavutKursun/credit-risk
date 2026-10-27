"""A small fake Lending Club export for tests and smoke runs (no real data needed).

Mimics the quirks the pipeline must survive: '13.5%' strings, ' 36 months' with a leading space, 'Dec-2015' months,
'10+ years', non-terminal statuses, 60-month loans, rows outside the cohort window, post-origination columns that
leak the outcome (`last_fico_range_low`, `total_rec_prncp`), the opt-in bureau attributes with their Sep-2012 introduction
block, and the summary lines Kaggle appends to the CSV.
Default depends on FICO, DTI, utilization, inquiries, income and rate through a logistic latent, so a model can learn.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .features import CATEGORY_LEVELS, RAW_BUREAU

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _month_str(year: int, month: int) -> str:
    return f"{MONTHS[month - 1]}-{year}"


def make_raw(n: int = 4000, seed: int = 7, start_year: int = 2011, end_year: int = 2016) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    months = rng.integers(0, (end_year - start_year + 1) * 12, n)
    issue_year, issue_month = start_year + months // 12, months % 12 + 1
    fico_low = np.clip(rng.normal(690, 30, n).round(), 660, 845).astype(int)
    fico_low = (fico_low // 5) * 5
    annual_inc = np.clip(rng.lognormal(11.0, 0.5, n), 12_000, 900_000).round(0)
    dti = np.clip(rng.normal(18, 8, n), 0, 45).round(2)
    revol_util = np.clip(rng.normal(52, 25, n), 0, 130).round(1)
    inq = rng.poisson(0.8, n)
    delinq = rng.poisson(0.2, n)
    sub_idx = np.clip(((760 - fico_low) / 100 * 12 + rng.normal(0, 4, n) + revol_util / 20).round(), 0, 34).astype(int)
    sub_grade = np.array(CATEGORY_LEVELS["sub_grade"])[sub_idx]
    grade = np.array([s[0] for s in sub_grade])
    int_rate = np.round(5.5 + sub_idx * 0.55 + rng.normal(0, 0.4, n), 2)
    term_60 = rng.random(n) < 0.25
    loan_amnt = (np.clip(rng.lognormal(9.3, 0.5, n), 1000, 40_000) / 25).round() * 25
    months_term = np.where(term_60, 60, 36)
    r = int_rate / 100 / 12
    installment = np.round(loan_amnt * r / (1 - (1 + r) ** (-months_term)), 2)
    latent = (-3.1 + 0.012 * (700 - fico_low) + 0.03 * (dti - 18) + 0.012 * (revol_util - 50) + 0.25 * inq + 0.25 * delinq
              - 0.35 * (np.log(annual_inc) - 11) + 0.06 * (int_rate - 12) + rng.normal(0, 0.6, n))
    p_default = 1 / (1 + np.exp(-latent))
    default = rng.random(n) < p_default

    # Statuses: matured 36-month loans are terminal; recent or 60-month loans may still be open.
    snapshot_months = (2018 - issue_year) * 12 + (12 - issue_month)
    matured = snapshot_months >= months_term
    status = np.where(default, "Charged Off", "Fully Paid").astype(object)
    # loans still open at the snapshot: most unmatured ones, and a few that matured within the last six months
    # (late payers whose final status is not settled yet) — the real export has both
    near_end = (snapshot_months - months_term) < 6
    open_loan = (~matured & (rng.random(n) < 0.7)) | (matured & near_end & (rng.random(n) < 0.15))
    status[open_loan & ~default] = "Current"
    status[open_loan & default] = "Late (31-120 days)"
    status[(issue_year <= 2010) & (rng.random(n) < 0.3)] = "Does not meet the credit policy. Status:Fully Paid"

    prepay = rng.uniform(0.80, 1.0, n)
    total_pymnt = np.where(default, installment * rng.uniform(2, 20, n), installment * months_term * prepay)
    total_pymnt = np.where(status == "Current", installment * rng.uniform(5, 30, n), total_pymnt).round(2)
    recoveries = np.where(default, loan_amnt * rng.uniform(0, 0.15, n), 0).round(2)
    emp_choices = np.array(["< 1 year", "1 year", "2 years", "3 years", "5 years", "7 years", "10+ years", "n/a"])
    earliest_year = issue_year - np.clip(rng.normal(14, 6, n), 2, 40).astype(int)

    df = pd.DataFrame({
        "id": np.arange(100_000, 100_000 + n),
        "loan_amnt": loan_amnt, "funded_amnt": loan_amnt, "term": np.where(term_60, " 60 months", " 36 months"),
        "int_rate": [f"{v:.2f}%" for v in int_rate], "installment": installment, "grade": grade, "sub_grade": sub_grade,
        "emp_length": rng.choice(emp_choices, n, p=[0.08, 0.07, 0.1, 0.1, 0.12, 0.08, 0.38, 0.07]),
        "home_ownership": rng.choice(["RENT", "OWN", "MORTGAGE"], n, p=[0.42, 0.1, 0.48]),
        "annual_inc": annual_inc, "verification_status": rng.choice(["Not Verified", "Source Verified", "Verified"], n),
        "issue_d": [_month_str(y, m) for y, m in zip(issue_year, issue_month, strict=True)], "loan_status": status,
        "purpose": rng.choice(["debt_consolidation", "credit_card", "home_improvement", "other", "major_purchase", "small_business", "car"], n,
                              p=[0.56, 0.22, 0.06, 0.06, 0.03, 0.03, 0.04]),
        "addr_state": rng.choice(["CA", "TX", "NY", "FL", "IL", "NJ", "PA", "OH", "GA", "VA", "NV"], n), "dti": dti, "delinq_2yrs": delinq,
        "earliest_cr_line": [_month_str(y, int(m)) for y, m in zip(earliest_year, rng.integers(1, 13, n), strict=True)],
        "fico_range_low": fico_low, "fico_range_high": fico_low + 4, "inq_last_6mths": inq, "open_acc": rng.poisson(11, n), "pub_rec": rng.poisson(0.15, n),
        "revol_bal": np.clip(rng.lognormal(9.3, 0.9, n), 0, 250_000).round(0), "revol_util": [f"{v:.1f}%" for v in revol_util],
        "total_acc": rng.poisson(24, n), "initial_list_status": rng.choice(["w", "f"], n), "application_type": "Individual",
        "mort_acc": rng.poisson(1.5, n).astype(float), "pub_rec_bankruptcies": rng.poisson(0.1, n).astype(float),
        "total_pymnt": total_pymnt, "recoveries": recoveries, "collection_recovery_fee": (recoveries * 0.1).round(2),
        # leaks: refreshed FICO and principal received depend on the outcome
        "last_fico_range_low": np.where(default, fico_low - rng.integers(60, 160, n), fico_low + rng.integers(-10, 25, n)),
        "total_rec_prncp": np.where(default, loan_amnt * rng.uniform(0.05, 0.6, n), loan_amnt).round(2),
    })
    # Opt-in bureau attributes (RAW_BUREAU), consistent with the origination columns at the same date, as in the real export
    bc_bal = (df["revol_bal"].to_numpy() * rng.uniform(0.5, 1.0, n)).round(0)
    bc_util_frac = np.clip(revol_util / 100 + rng.normal(0, 0.08, n), 0.01, 1.2)
    total_bc_limit = np.maximum((bc_bal / bc_util_frac / 100).round() * 100, bc_bal)
    total_bc_limit = np.where(total_bc_limit <= 0, 500.0, total_bc_limit)
    df["total_bc_limit"] = total_bc_limit
    df["bc_open_to_buy"] = np.maximum(total_bc_limit - bc_bal, 0)
    df["bc_util"] = np.round(100 * bc_bal / total_bc_limit, 1)
    df["percent_bc_gt_75"] = np.where(df["bc_util"] > 75, rng.uniform(50, 100, n), np.where(df["bc_util"] > 40, rng.uniform(0, 50, n), 0.0)).round(1)
    df["tot_cur_bal"] = (df["revol_bal"] + np.where(df["home_ownership"] == "MORTGAGE", rng.lognormal(11.8, 0.5, n), 0) + rng.lognormal(8.5, 1.0, n)).round(0)
    df["acc_open_past_24mths"] = rng.poisson(4, n)
    df["num_tl_op_past_12m"] = rng.binomial(df["acc_open_past_24mths"].to_numpy(), 0.5)
    df["mo_sin_rcnt_tl"] = np.where(df["num_tl_op_past_12m"] > 0, rng.integers(0, 12, n),
                                    np.where(df["acc_open_past_24mths"] > 0, rng.integers(12, 24, n), rng.integers(24, 120, n)))
    inq_months = np.where(inq > 0, rng.integers(0, 7, n), rng.integers(7, 60, n)).astype(float)
    inq_months[(inq == 0) & (rng.random(n) < 0.15)] = np.nan  # no inquiry on file: informative missing, as in the real data
    df["mths_since_recent_inq"] = inq_months
    # the bureau set was added to the export in Sep-2012; loans listed before that stay missing (never backfilled)
    df.loc[pd.to_datetime(df["issue_d"], format="%b-%Y") < pd.Timestamp("2012-09-01"), RAW_BUREAU] = np.nan
    # a few missing values where the real export has them
    df.loc[rng.random(n) < 0.02, "revol_util"] = np.nan
    df.loc[rng.random(n) < 0.05, "mort_acc"] = np.nan
    df.loc[rng.random(n) < 0.03, "emp_length"] = np.nan
    return df


def write_raw_csv(df: pd.DataFrame, path: Path) -> Path:
    """Write as gzip CSV with Kaggle's two trailing summary lines."""
    path.parent.mkdir(parents=True, exist_ok=True)
    csv = df.to_csv(index=False)
    csv += "Total amount funded in policy code 1: 12345\nTotal amount funded in policy code 2: 678\n"
    import gzip

    with gzip.open(path, "wt", encoding="utf-8") as f:
        f.write(csv)
    return path

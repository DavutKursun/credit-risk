"""Leakage policy in code: which raw Lending Club columns are known when the loan is applied for.

`KNOWN_AT_ORIGINATION[col]` is True (usable as a feature), False (post-origination: payments, recoveries,
hardship, settlement, refreshed bureau pulls — target and economics only) or None (the data dictionary is
ambiguous about when it is captured: excluded by default, listed for review). A column missing from the
table counts as None. `audit()` computes single-feature AUCs so that a mistake here shows up as a number.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

ORIGINATION = [
    "id", "member_id", "loan_amnt", "funded_amnt", "funded_amnt_inv", "term", "int_rate", "installment", "grade", "sub_grade",
    "emp_title", "emp_length", "home_ownership", "annual_inc", "verification_status", "issue_d", "purpose", "title", "zip_code",
    "addr_state", "dti", "delinq_2yrs", "earliest_cr_line", "fico_range_low", "fico_range_high", "inq_last_6mths",
    "mths_since_last_delinq", "mths_since_last_record", "open_acc", "pub_rec", "revol_bal", "revol_util", "total_acc",
    "initial_list_status", "collections_12_mths_ex_med", "mths_since_last_major_derog", "policy_code", "application_type",
    "annual_inc_joint", "dti_joint", "verification_status_joint", "acc_now_delinq", "mort_acc", "pub_rec_bankruptcies", "tax_liens",
    "desc", "disbursement_method",
]
POST_ORIGINATION = [
    "loan_status", "pymnt_plan", "url", "out_prncp", "out_prncp_inv", "total_pymnt", "total_pymnt_inv", "total_rec_prncp",
    "total_rec_int", "total_rec_late_fee", "recoveries", "collection_recovery_fee", "last_pymnt_d", "last_pymnt_amnt",
    "next_pymnt_d", "last_credit_pull_d", "last_fico_range_high", "last_fico_range_low", "hardship_flag", "hardship_type",
    "hardship_reason", "hardship_status", "deferral_term", "hardship_amount", "hardship_start_date", "hardship_end_date",
    "payment_plan_start_date", "hardship_length", "hardship_dpd", "hardship_loan_status", "orig_projected_additional_accrued_interest",
    "hardship_payoff_balance_amount", "hardship_last_payment_amount", "debt_settlement_flag", "debt_settlement_flag_date",
    "settlement_status", "settlement_date", "settlement_amount", "settlement_percentage", "settlement_term",
]
# Bureau attributes added to the export in 2015. The dictionary does not say whether they are refreshed by later credit pulls
# (`last_credit_pull_d` exists, so some fields are). Excluded until M1 checks their missing rate by issue year and their AUC.
UNCERTAIN = [
    "tot_coll_amt", "tot_cur_bal", "open_acc_6m", "open_act_il", "open_il_12m", "open_il_24m", "mths_since_rcnt_il", "total_bal_il",
    "il_util", "open_rv_12m", "open_rv_24m", "max_bal_bc", "all_util", "total_rev_hi_lim", "inq_fi", "total_cu_tl", "inq_last_12m",
    "acc_open_past_24mths", "avg_cur_bal", "bc_open_to_buy", "bc_util", "chargeoff_within_12_mths", "delinq_amnt",
    "mo_sin_old_il_acct", "mo_sin_old_rev_tl_op", "mo_sin_rcnt_rev_tl_op", "mo_sin_rcnt_tl", "mths_since_recent_bc",
    "mths_since_recent_bc_dlq", "mths_since_recent_inq", "mths_since_recent_revol_delinq", "num_accts_ever_120_pd", "num_actv_bc_tl",
    "num_actv_rev_tl", "num_bc_sats", "num_bc_tl", "num_il_tl", "num_op_rev_tl", "num_rev_accts", "num_rev_tl_bal_gt_0", "num_sats",
    "num_tl_120dpd_2m", "num_tl_30dpd", "num_tl_90g_dpd_24m", "num_tl_op_past_12m", "pct_tl_nvr_dlq", "percent_bc_gt_75",
    "tot_hi_cred_lim", "total_bal_ex_mort", "total_bc_limit", "total_il_high_credit_limit", "revol_bal_joint",
    "sec_app_fico_range_low", "sec_app_fico_range_high", "sec_app_earliest_cr_line", "sec_app_inq_last_6mths", "sec_app_mort_acc",
    "sec_app_open_acc", "sec_app_revol_util", "sec_app_open_act_il", "sec_app_num_rev_accts", "sec_app_chargeoff_within_12_mths",
    "sec_app_collections_12_mths_ex_med", "sec_app_mths_since_last_major_derog",
]

KNOWN_AT_ORIGINATION: dict[str, bool | None] = {**{c: True for c in ORIGINATION}, **{c: False for c in POST_ORIGINATION}, **{c: None for c in UNCERTAIN}}

# Post-origination columns that evaluation may read for population economics (never as features).
ECONOMICS_COLUMNS = ["funded_amnt", "total_pymnt", "recoveries", "collection_recovery_fee", "installment", "loan_status"]

SUSPICIOUS_AUC = 0.80


def flag(column: str) -> bool | None:
    return KNOWN_AT_ORIGINATION.get(column)


def usable_columns(columns) -> list[str]:
    """Columns a feature may be built from: flagged True. None and False are both out."""
    return [c for c in columns if flag(c) is True]


def _safe_auc(y: np.ndarray, s: np.ndarray) -> float:
    if len(np.unique(y)) < 2 or len(s) < 20:
        return float("nan")
    a = roc_auc_score(y, s)
    return float(max(a, 1 - a))


def _as_numeric_if_possible(s: pd.Series) -> pd.Series | None:
    """'13.5%' strings and 'Dec-2015' months become numbers so they are screened as such; anything else → None."""
    if pd.api.types.is_numeric_dtype(s) and not isinstance(s.dtype, pd.CategoricalDtype):
        return s.astype(float)
    if isinstance(s.dtype, pd.CategoricalDtype):
        return None
    txt = s.astype("string").str.strip()
    non_null = txt.notna().sum()
    if non_null == 0:
        return None
    pct = pd.to_numeric(txt.str.rstrip("%"), errors="coerce")
    if pct.notna().sum() >= 0.95 * non_null:
        return pct.astype(float)
    months = pd.to_datetime(txt, format="%b-%Y", errors="coerce")
    if months.notna().sum() >= 0.95 * non_null:
        return (months - pd.Timestamp("1970-01-01")).dt.days.astype(float)
    return None


def single_feature_auc(df: pd.DataFrame, column: str, target: str, max_levels: int = 60) -> tuple[float, float]:
    """(AUC of the column's values, AUC of its missingness). Values: numeric as is (percent strings and months parsed);
    categorical via target-rate encoding fitted on the same rows (optimistic, which is what a leakage screen wants)."""
    y_all = df[target].to_numpy().astype(int)
    s = df[column]
    miss = s.isna().to_numpy().astype(float)
    auc_missing = _safe_auc(y_all, miss) if 0 < miss.mean() < 1 else float("nan")
    ok = ~s.isna()
    y = y_all[ok.to_numpy()]
    num = _as_numeric_if_possible(s)
    if num is not None:
        v = num[ok].to_numpy()
        return _safe_auc(y, v), auc_missing
    levels = s[ok].astype(str)
    if levels.nunique() > max_levels:
        return float("nan"), auc_missing
    rate = pd.Series(y, index=levels.index).groupby(levels).mean()
    return _safe_auc(y, levels.map(rate).to_numpy().astype(float)), auc_missing


def audit(df: pd.DataFrame, target: str, columns=None, threshold: float = SUSPICIOUS_AUC) -> pd.DataFrame:
    """One row per column: flag, dtype, non-null rate, single-feature AUC, missingness AUC, and `suspicious` = usable (True) or
    unflagged (None) column whose AUC is above the threshold. Sorted by AUC so the leaks are at the top."""
    rows = []
    for c in columns or [c for c in df.columns if c != target]:
        if c in ("id", "member_id", "url"):
            continue  # identifiers, not features
        auc_v, auc_m = single_feature_auc(df, c, target)
        f = flag(c)
        best = np.nanmax([auc_v, auc_m]) if not (np.isnan(auc_v) and np.isnan(auc_m)) else float("nan")
        rows.append({"column": c, "known_at_origination": f, "dtype": str(df[c].dtype), "non_null_rate": round(float(df[c].notna().mean()), 4),
                     "auc_value": round(auc_v, 4) if not np.isnan(auc_v) else None, "auc_missing": round(auc_m, 4) if not np.isnan(auc_m) else None,
                     "suspicious": bool(f is not False and not np.isnan(best) and best > threshold)})
    out = pd.DataFrame(rows)
    out["sort_key"] = out[["auc_value", "auc_missing"]].max(axis=1).fillna(0)
    return out.sort_values("sort_key", ascending=False).drop(columns="sort_key").reset_index(drop=True)


def assert_no_leaks(audit_table: pd.DataFrame, feature_columns) -> None:
    """Raise if any column a feature is built from is flagged suspicious or is not flagged True."""
    bad_flag = [c for c in feature_columns if flag(c) is not True]
    if bad_flag:
        raise ValueError(f"features built from columns not flagged known-at-origination: {bad_flag}")
    sus = set(audit_table.loc[audit_table["suspicious"], "column"])
    hit = [c for c in feature_columns if c in sus]
    if hit:
        raise ValueError(f"single-feature AUC above {SUSPICIOUS_AUC} for feature source columns {hit}: review before training")

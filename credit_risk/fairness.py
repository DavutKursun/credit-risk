"""Group audit on proxies. The data has no protected attributes; state, income band, employment length and home
ownership are proxies that can show disparate treatment of a policy, not prove or disprove it. Say so in the README.

Per group: n, approval rate, default rate among approved, FPR (declined but would have repaid) and TPR (declined and
would have defaulted); four-fifths ratio = min approval rate / max approval rate across groups (≥ 0.8 is the
rule-of-thumb threshold used in US hiring law — illustrative here, not a legal test).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def income_band(annual_inc: pd.Series, q: int = 5) -> pd.Series:
    return pd.qcut(annual_inc.rank(method="first"), q, labels=[f"income_q{i}" for i in range(1, q + 1)]).astype(str)


def emp_band(emp_years: pd.Series) -> pd.Series:
    bins = pd.cut(emp_years.fillna(-1), [-2, -0.5, 1, 5, 9, 100], labels=["unknown", "0-1", "2-5", "6-9", "10+"])
    return bins.astype(str)


def group_report(y, decisions, group: pd.Series, min_n: int = 200) -> pd.DataFrame:
    y, d, g = np.asarray(y, dtype=int), np.asarray(decisions), group.astype(str).to_numpy()
    rows = []
    for level in pd.unique(g):
        m = g == level
        if m.sum() < min_n:
            continue
        appr = d[m] == "approve"
        yy = y[m]
        declined = ~appr
        rows.append({"group": level, "n": int(m.sum()), "approval_rate": round(float(appr.mean()), 4),
                     "default_rate_approved": round(float(yy[appr].mean()), 4) if appr.any() else None,
                     "fpr": round(float((declined & (yy == 0)).sum() / max((yy == 0).sum(), 1)), 4),
                     "tpr": round(float((declined & (yy == 1)).sum() / max((yy == 1).sum(), 1)), 4)})
    cols = ["group", "n", "approval_rate", "default_rate_approved", "fpr", "tpr"]
    return pd.DataFrame(rows, columns=cols).sort_values("n", ascending=False).reset_index(drop=True)


def four_fifths_ratio(report: pd.DataFrame) -> float | None:
    if report.empty or report["approval_rate"].max() == 0:
        return None
    return round(float(report["approval_rate"].min() / report["approval_rate"].max()), 4)


def audit(df: pd.DataFrame, y, decisions, X: pd.DataFrame, top_states: int = 10, min_n: int = 200) -> dict[str, pd.DataFrame]:
    """The standard set of proxy groups for this project."""
    states = df["addr_state"].astype(str)
    top = states.value_counts().index[:top_states]
    out = {
        "addr_state": group_report(y, decisions, states.where(states.isin(top), "other"), min_n),
        "income_band": group_report(y, decisions, income_band(X["annual_inc"]), min_n),
        "emp_band": group_report(y, decisions, emp_band(X["emp_years"]), min_n),
        "home_ownership": group_report(y, decisions, df["home_ownership"].astype(str), min_n),
    }
    return out

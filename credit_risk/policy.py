"""From a probability to a decision: expected value, thresholds, profit curves, realized P&L.

Economics (estimated on train only, see CLAUDE.md §3.4):
  gain if repaid  ≈ installment × 36 − funded_amnt     (scheduled interest; prepayment makes it an upper bound)
  loss if default ≈ LGD × funded_amnt                   (LGD = 1 − recovery rate on charged-off train loans)
  E[profit] = (1 − PD) × gain − PD × loss
Realized P&L = total_pymnt + recoveries − collection_recovery_fee − funded_amnt, read from post-origination columns
ONLY to score a policy on dev/test, never as a feature.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import REVIEW_BAND, SEED, TARGET

TERM_MONTHS = 36


def lgd_from_train(train: pd.DataFrame) -> dict:
    """LGD on charged-off train loans: 1 − (total_pymnt + recoveries − collection_recovery_fee) / funded_amnt, each capped to [0, 1].
    Returns the overall value, the count it rests on, and the value by grade."""
    bad = train[train[TARGET] == 1]
    if bad.empty:
        raise ValueError("no defaulted loans in train; cannot estimate LGD")
    recovery = ((bad["total_pymnt"].fillna(0) + bad["recoveries"].fillna(0) - bad["collection_recovery_fee"].fillna(0)) / bad["funded_amnt"]).clip(0, 1)
    lgd = 1 - recovery
    by_grade = {str(g): round(float(v), 4) for g, v in lgd.groupby(bad["grade"].astype("string")).mean().items()} if "grade" in bad else {}
    return {"lgd": round(float(lgd.mean()), 4), "lgd_median": round(float(lgd.median()), 4), "n_defaults": len(bad), "by_grade": by_grade}


def gain_if_repaid(funded_amnt, installment, term: int = TERM_MONTHS) -> np.ndarray:
    return np.asarray(installment, dtype=float) * term - np.asarray(funded_amnt, dtype=float)


def expected_profit(pd_, funded_amnt, installment, lgd: float, term: int = TERM_MONTHS) -> np.ndarray:
    pd_ = np.asarray(pd_, dtype=float)
    gain = gain_if_repaid(funded_amnt, installment, term)
    loss = lgd * np.asarray(funded_amnt, dtype=float)
    return (1 - pd_) * gain - pd_ * loss


def breakeven_pd(funded_amnt, installment, lgd: float, term: int = TERM_MONTHS) -> np.ndarray:
    """PD at which E[profit] = 0 for this loan: gain / (gain + loss). A per-loan threshold, because a 24% loan tolerates
    more risk than a 7% loan."""
    gain = gain_if_repaid(funded_amnt, installment, term)
    loss = lgd * np.asarray(funded_amnt, dtype=float)
    return np.where(gain + loss > 0, gain / (gain + loss), 0.0)


def decide(pd_, threshold: float, band: float = REVIEW_BAND) -> np.ndarray:
    """approve if PD < threshold − band; review if the PD is within ±band of the threshold; decline if PD ≥ threshold + band."""
    pd_ = np.asarray(pd_, dtype=float)
    out = np.where(pd_ < threshold - band, "approve", np.where(pd_ < threshold + band, "review", "decline"))
    return out.astype(object)


def realized_pnl(df: pd.DataFrame) -> np.ndarray:
    return (df["total_pymnt"].fillna(0) + df["recoveries"].fillna(0) - df["collection_recovery_fee"].fillna(0) - df["funded_amnt"]).to_numpy(dtype=float)


def profit_curve(y, pd_, funded_amnt, installment, lgd: float, realized: np.ndarray | None = None, thresholds=None) -> pd.DataFrame:
    """For each PD threshold: approval rate, default rate among approved, expected profit (sum, per approved loan) and, when
    realized P&L is given, the realized total of the approved set. The dev curve picks the threshold; test reports it unchanged."""
    y, pd_ = np.asarray(y, dtype=int), np.asarray(pd_, dtype=float)
    ev = expected_profit(pd_, funded_amnt, installment, lgd)
    thresholds = np.asarray(thresholds if thresholds is not None else np.round(np.arange(0.02, 0.60, 0.01), 2))
    rows = []
    for t in thresholds:
        appr = pd_ < t
        n = int(appr.sum())
        row = {"threshold": float(t), "approval_rate": round(n / len(pd_), 4), "default_rate_approved": round(float(y[appr].mean()), 4) if n else None,
               "expected_profit_total": round(float(ev[appr].sum()), 2), "expected_profit_per_approved": round(float(ev[appr].mean()), 2) if n else None}
        if realized is not None:
            row["realized_pnl_total"] = round(float(np.asarray(realized)[appr].sum()), 2)
            row["realized_pnl_per_approved"] = round(float(np.asarray(realized)[appr].mean()), 2) if n else None
        rows.append(row)
    return pd.DataFrame(rows)


def best_threshold(curve: pd.DataFrame, by: str = "expected_profit_total", min_approval_rate: float = 0.0) -> float:
    c = curve[curve["approval_rate"] >= min_approval_rate]
    return float(c.loc[c[by].idxmax(), "threshold"])


def policy_table(y, pd_, decisions, realized: np.ndarray | None = None, label: str = "policy") -> dict:
    """One policy summarised: approval / review / decline shares, default rate among approved, realized P&L of the approved set."""
    y, d = np.asarray(y, dtype=int), np.asarray(decisions)
    appr = d == "approve"
    out = {"policy": label, "n": len(y), "approve": round(float(appr.mean()), 4), "review": round(float((d == "review").mean()), 4),
           "decline": round(float((d == "decline").mean()), 4), "default_rate_approved": round(float(y[appr].mean()), 4) if appr.any() else None,
           "defaults_caught": round(float(1 - y[appr].sum() / max(y.sum(), 1)), 4)}
    if realized is not None:
        r = np.asarray(realized, dtype=float)
        out["realized_pnl_total"] = round(float(r[appr].sum()), 2)
        out["realized_pnl_per_approved"] = round(float(r[appr].mean()), 2) if appr.any() else None
    return out


def subgrade_cut(sub_grade_codes, rate: float, seed: int = SEED) -> np.ndarray:
    """Approve the lowest-risk `rate` share by Lending Club sub-grade (A1 first); ties inside the boundary sub-grade are broken at
    random with a fixed seed so the approval rate is exact. The comparison for a lender that already has the grades."""
    codes = np.asarray(sub_grade_codes, dtype=float)
    key = codes + np.random.default_rng(seed).random(len(codes)) * 0.5
    out = np.full(len(codes), "decline", dtype=object)
    out[np.argsort(key, kind="stable")[: round(rate * len(codes))]] = "approve"
    return out


def approve_at_rate(pd_, rate: float, tie_break=None) -> np.ndarray:
    """Approve exactly the lowest-PD `rate` share (ties broken by `tie_break`, e.g. the raw score)."""
    pd_ = np.asarray(pd_, dtype=float)
    order = np.lexsort((np.asarray(tie_break, dtype=float), pd_)) if tie_break is not None else np.argsort(pd_, kind="stable")
    out = np.full(len(pd_), "decline", dtype=object)
    out[order[: round(rate * len(pd_))]] = "approve"
    return out


def approve_grades(grade: pd.Series, allowed=("A", "B", "C")) -> np.ndarray:
    g = grade.astype("string")
    return np.where(g.isin(list(allowed)), "approve", "decline").astype(object)

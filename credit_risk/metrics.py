"""Ranking and calibration metrics for a probability of default.

Ranking: AUC, Gini (= 2·AUC − 1), KS (max distance between the cumulative distributions of goods and bads
along the score), PR-AUC. Calibration: Brier, log loss, ECE over equal-count bins and the reliability table.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score


def ks_statistic(y: np.ndarray, p: np.ndarray) -> float:
    order = np.argsort(-p)
    y = np.asarray(y)[order]
    bads = np.cumsum(y) / max(y.sum(), 1)
    goods = np.cumsum(1 - y) / max((1 - y).sum(), 1)
    return float(np.max(np.abs(bads - goods)))


def reliability_table(y, p, bins: int = 10) -> pd.DataFrame:
    """Equal-count bins by predicted PD: n, mean predicted, observed default rate, absolute gap."""
    y, p = np.asarray(y, dtype=float), np.asarray(p, dtype=float)
    edges = np.unique(np.quantile(p, np.linspace(0, 1, bins + 1)))
    if len(edges) < 2:  # constant predictions → one bin
        edges = np.array([edges[0], edges[0] + 1e-9])
    idx = np.clip(np.searchsorted(edges, p, side="right") - 1, 0, len(edges) - 2)
    rows = []
    for b in range(len(edges) - 1):
        m = idx == b
        if m.sum() == 0:
            continue
        rows.append({"bin": b, "n": int(m.sum()), "pd_low": float(edges[b]), "pd_high": float(edges[b + 1]),
                     "predicted": float(p[m].mean()), "observed": float(y[m].mean())})
    t = pd.DataFrame(rows)
    t["abs_gap"] = (t["predicted"] - t["observed"]).abs()
    return t


def expected_calibration_error(y, p, bins: int = 10) -> float:
    t = reliability_table(y, p, bins)
    return float((t["abs_gap"] * t["n"]).sum() / t["n"].sum())


def summary(y, p, bins: int = 10) -> dict:
    y, p = np.asarray(y, dtype=int), np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
    auc = float(roc_auc_score(y, p))
    return {
        "n": len(y), "default_rate": round(float(y.mean()), 4), "mean_pd": round(float(p.mean()), 4),
        "auc": round(auc, 4), "gini": round(2 * auc - 1, 4), "ks": round(ks_statistic(y, p), 4),
        "pr_auc": round(float(average_precision_score(y, p)), 4),
        "brier": round(float(brier_score_loss(y, p)), 5), "log_loss": round(float(log_loss(y, p)), 5),
        "ece": round(expected_calibration_error(y, p, bins), 5),
    }


def auc_by_group(y, p, group) -> pd.DataFrame:
    """Does the score still rank inside each group (e.g. within a Lending Club grade)?"""
    df = pd.DataFrame({"y": np.asarray(y), "p": np.asarray(p), "g": np.asarray(group).astype(str)})
    rows = []
    for g, part in df.groupby("g"):
        if part["y"].nunique() < 2 or len(part) < 50:
            continue
        rows.append({"group": g, "n": len(part), "default_rate": round(float(part["y"].mean()), 4), "auc": round(float(roc_auc_score(part["y"], part["p"])), 4)})
    return pd.DataFrame(rows)

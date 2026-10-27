"""Population stability index: has the applicant population (or the score) moved since training?

PSI = Σ (actual% − expected%) × ln(actual% / expected%) over bins fixed on the expected (training) distribution.
Rule of thumb: < 0.10 stable · 0.10–0.25 watch · > 0.25 act (retrain or investigate). Numeric features use equal-count
bins from train; categoricals use their levels; missing values are their own bin.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import PSI_ACT, PSI_WARN

EPS = 1e-4


def _shares(idx: np.ndarray, n_bins: int) -> np.ndarray:
    counts = np.bincount(idx, minlength=n_bins).astype(float)
    return np.clip(counts / max(counts.sum(), 1), EPS, None)


def psi_numeric(expected: pd.Series, actual: pd.Series, bins: int = 10) -> float:
    e, a = expected.astype(float), actual.astype(float)
    edges = np.unique(np.quantile(e.dropna(), np.linspace(0, 1, bins + 1)))
    if len(edges) < 2:
        return 0.0
    def bin_idx(s: pd.Series) -> np.ndarray:
        v = s.to_numpy()
        idx = np.clip(np.searchsorted(edges, v, side="right") - 1, 0, len(edges) - 2)
        idx = np.where(np.isnan(v), len(edges) - 1, idx)  # missing → last bin
        return idx
    n_bins = len(edges)
    pe, pa = _shares(bin_idx(e), n_bins), _shares(bin_idx(a), n_bins)
    return float(np.sum((pa - pe) * np.log(pa / pe)))


def psi_categorical(expected: pd.Series, actual: pd.Series) -> float:
    e, a = expected.astype(str).fillna("missing"), actual.astype(str).fillna("missing")
    levels = sorted(set(e.unique()) | set(a.unique()))
    pe = np.clip(e.value_counts(normalize=True).reindex(levels).fillna(0).to_numpy(), EPS, None)
    pa = np.clip(a.value_counts(normalize=True).reindex(levels).fillna(0).to_numpy(), EPS, None)
    return float(np.sum((pa - pe) * np.log(pa / pe)))


def psi(expected: pd.Series, actual: pd.Series, bins: int = 10) -> float:
    if isinstance(expected.dtype, pd.CategoricalDtype) or not pd.api.types.is_numeric_dtype(expected):
        return psi_categorical(expected, actual)
    return psi_numeric(expected, actual, bins)


def status(value: float) -> str:
    return "act" if value > PSI_ACT else "watch" if value > PSI_WARN else "stable"


def psi_table(expected: pd.DataFrame, actual: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    rows = [{"feature": c, "psi": round(psi(expected[c], actual[c]), 4)} for c in columns]
    t = pd.DataFrame(rows).sort_values("psi", ascending=False).reset_index(drop=True)
    t["status"] = t["psi"].map(status)
    return t


def psi_by_period(train: pd.DataFrame, later: pd.DataFrame, period: pd.Series, columns: list[str]) -> pd.DataFrame:
    """Feature × period matrix of PSI against train (period = e.g. later['issue_month'].dt.to_period('Q').astype(str))."""
    out = {}
    for p in sorted(period.unique()):
        part = later[period.to_numpy() == p]
        out[str(p)] = psi_table(train, part, columns).set_index("feature")["psi"]
    return pd.DataFrame(out).reindex(columns)

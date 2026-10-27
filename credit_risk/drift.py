"""Population stability index: has the applicant population (or the score) moved since training?

PSI = Σ (actual% − expected%) × ln(actual% / expected%) over bins fixed on the expected (training) distribution.
Rule of thumb: < 0.10 stable · 0.10–0.25 watch · > 0.25 act (retrain or investigate). Numeric features use equal-count
bins from train and categoricals their levels, both over NON-MISSING values. Missingness is measured separately as a
two-bin PSI (missing vs present): a field that is empty for one vintage and complete later (the 2012 bureau block, 7.4% of
train, 0% of dev/test) would otherwise swamp the value PSI. A feature's status uses the larger of the two.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import PSI_ACT, PSI_WARN

EPS = 1e-4
METRICS = ("psi", "missing_share_expected", "missing_share_actual", "psi_missing", "psi_max")


def _psi(pe: np.ndarray, pa: np.ndarray) -> float:
    pe, pa = np.clip(pe, EPS, None), np.clip(pa, EPS, None)
    return float(np.sum((pa - pe) * np.log(pa / pe)))


def _shares(idx: np.ndarray, n_bins: int) -> np.ndarray:
    counts = np.bincount(idx, minlength=n_bins).astype(float)
    return counts / max(counts.sum(), 1)


def psi_numeric(expected: pd.Series, actual: pd.Series, bins: int = 10) -> float:
    """PSI over non-missing values, equal-count bins fixed on `expected`."""
    e = pd.to_numeric(expected, errors="coerce").dropna().to_numpy(dtype=float)
    a = pd.to_numeric(actual, errors="coerce").dropna().to_numpy(dtype=float)
    if len(e) == 0 or len(a) == 0:
        return 0.0
    edges = np.unique(np.quantile(e, np.linspace(0, 1, bins + 1)))
    if len(edges) < 2:
        return 0.0
    n_bins = len(edges) - 1

    def bin_idx(v: np.ndarray) -> np.ndarray:
        return np.clip(np.searchsorted(edges, v, side="right") - 1, 0, n_bins - 1)

    return _psi(_shares(bin_idx(e), n_bins), _shares(bin_idx(a), n_bins))


def psi_categorical(expected: pd.Series, actual: pd.Series) -> float:
    """PSI over the levels seen on either side, non-missing values only."""
    e, a = expected[expected.notna()].astype(str), actual[actual.notna()].astype(str)
    levels = sorted(set(e.unique()) | set(a.unique()))
    if not levels or len(e) == 0 or len(a) == 0:
        return 0.0
    pe = e.value_counts(normalize=True).reindex(levels).fillna(0).to_numpy(dtype=float)
    pa = a.value_counts(normalize=True).reindex(levels).fillna(0).to_numpy(dtype=float)
    return _psi(pe, pa)


def psi(expected: pd.Series, actual: pd.Series, bins: int = 10) -> float:
    """Value PSI (non-missing values); see psi_missing() for the missingness part."""
    if isinstance(expected.dtype, pd.CategoricalDtype) or not pd.api.types.is_numeric_dtype(expected):
        return psi_categorical(expected, actual)
    return psi_numeric(expected, actual, bins)


def psi_missing(expected: pd.Series, actual: pd.Series) -> float:
    """Two-bin PSI of missing vs present."""
    me, ma = float(expected.isna().mean()), float(actual.isna().mean())
    return _psi(np.array([1 - me, me]), np.array([1 - ma, ma]))


def psi_detail(expected: pd.Series, actual: pd.Series, bins: int = 10) -> dict:
    """psi (values), missing shares on both sides, psi_missing, and psi_max = max(psi, psi_missing), which drives the status."""
    v, m = psi(expected, actual, bins), psi_missing(expected, actual)
    return {"psi": round(v, 4), "missing_share_expected": round(float(expected.isna().mean()), 4),
            "missing_share_actual": round(float(actual.isna().mean()), 4), "psi_missing": round(m, 4), "psi_max": round(max(v, m), 4)}


def status(value: float) -> str:
    return "act" if value > PSI_ACT else "watch" if value > PSI_WARN else "stable"


def psi_table(expected: pd.DataFrame, actual: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """One row per feature: psi, missing_share_expected, missing_share_actual, psi_missing, psi_max, status (from psi_max)."""
    rows = [{"feature": c, **psi_detail(expected[c], actual[c])} for c in columns]
    t = pd.DataFrame(rows).sort_values("psi_max", ascending=False).reset_index(drop=True)
    t["status"] = t["psi_max"].map(status)
    return t


def psi_by_period(train: pd.DataFrame, later: pd.DataFrame, period: pd.Series, columns: list[str], metric: str = "psi_max") -> pd.DataFrame:
    """Feature × period matrix of one PSI metric against train (period = e.g. later['issue_month'].dt.to_period('Q').astype(str))."""
    if metric not in METRICS:
        raise ValueError(f"metric must be one of {METRICS}")
    out = {}
    for p in sorted(period.unique()):
        part = later[period.to_numpy() == p]
        out[str(p)] = psi_table(train, part, columns).set_index("feature")[metric]
    return pd.DataFrame(out).reindex(columns)

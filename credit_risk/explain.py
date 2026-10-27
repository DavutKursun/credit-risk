"""Reason codes: why this PD, in words a declined applicant may be given.

LightGBM: per-feature SHAP contributions from `predict(pred_contrib=True)` (exact TreeSHAP, built into LightGBM, no extra
dependency). Scorecard: points per feature relative to the average approved applicant. Numeric reasons are phrased
against the approved training population ("higher than 90% of approved borrowers"); categorical reasons name the value. The
Lending Club grade, sub-grade, rate and installment never appear as a reason: they are a score, not something the applicant did.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .features import FEATURE_LABELS, FEATURE_UNITS, LC_GRADE_FEATURES
from .models import ModelBundle, _as_scorecard_frame
from .schema import Reason

TOP_K = 5
# Lending Club's own risk outputs (grade, sub_grade, int_rate, installment and the installment ratio) are a score, not a cause an
# applicant can act on. They stay in the model and in the contributions; the displayed reasons are the next underlying attributes.
NOT_A_REASON = tuple(LC_GRADE_FEATURES)


def _fmt(feature: str, value) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "missing"
    unit = FEATURE_UNITS.get(feature, "")
    if isinstance(value, (int, float, np.integer, np.floating)):
        v = float(value)
        if unit == "$":
            return f"${v:,.0f}"
        if unit == "%":
            return f"{v:.1f}%"
        if unit:
            return f"{v:.1f} {unit}"
        return f"{v:.2f}" if abs(v) < 10 and v != int(v) else f"{v:,.0f}"
    return str(value)


def _percentile_among_approved(feature: str, value: float, quantiles: dict) -> int | None:
    q = quantiles.get(feature)
    if not q or value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    pts = sorted((float(k), v) for k, v in q.items())
    below = [k for k, v in pts if value >= v]
    return int(round(100 * max(below))) if below else int(round(100 * pts[0][0]))


def _text(feature: str, value, direction: str, quantiles: dict) -> str:
    label = FEATURE_LABELS.get(feature, feature)
    shown = _fmt(feature, value)
    pct = _percentile_among_approved(feature, value if isinstance(value, (int, float, np.integer, np.floating)) else None, quantiles)
    if pct is not None and direction == "raises":
        side = "higher" if pct >= 50 else "lower"
        return f"{label} {shown} is {side} than {pct if side == 'higher' else 100 - pct}% of approved borrowers"
    if pct is not None:
        return f"{label} {shown} supports approval (better than {100 - pct if pct < 50 else pct}% of approved borrowers)"
    return f"{label}: {shown} ({'associated with more' if direction == 'raises' else 'associated with fewer'} defaults)"


def contributions(bundle: ModelBundle, X: pd.DataFrame) -> pd.DataFrame:
    """Per-row, per-feature contribution to the log-odds (LightGBM) or to the points (scorecard, negated so that + = more risk)."""
    X = X[bundle.features]
    if bundle.name == "lgbm":
        raw = np.asarray(bundle.estimator.predict(X, pred_contrib=True, num_iteration=bundle.estimator.best_iteration or None))
        return pd.DataFrame(raw[:, :-1], columns=bundle.features, index=X.index)  # last column = bias
    if bundle.name == "scorecard":
        card = bundle.estimator
        frame = _as_scorecard_frame(X)
        selected = list(card.binning_process_.get_support(names=True))
        woe = card.binning_process_.transform(frame[selected], metric="woe")
        coef = card.estimator_.coef_.ravel()
        contrib = pd.DataFrame(np.asarray(woe) * coef, columns=selected, index=X.index)
        for f in bundle.features:
            if f not in contrib:
                contrib[f] = 0.0
        return contrib[bundle.features]
    raise ValueError(f"no explanations for {bundle.name}")


def reason_codes(bundle: ModelBundle, X: pd.DataFrame, k: int = TOP_K, exclude: tuple[str, ...] = NOT_A_REASON,
                 contrib: pd.DataFrame | None = None) -> list[list[Reason]]:
    """Top-k reasons per row, strongest first, among the features not in `exclude` (by default the Lending Club-derived ones).
    Positive contribution = raises the PD. `contrib` lets a caller pass contributions it already computed."""
    contrib = contributions(bundle, X) if contrib is None else contrib
    shown = [f for f in contrib.columns if f not in exclude]
    out: list[list[Reason]] = []
    for i, idx in enumerate(X.index):
        row = contrib.loc[idx, shown]
        order = row.abs().sort_values(ascending=False).index[:k]
        reasons = []
        for f in order:
            c = float(row[f])
            val = X.loc[idx, f]
            if isinstance(val, pd.Categorical) or isinstance(X[f].dtype, pd.CategoricalDtype):
                val = None if pd.isna(val) else str(val)
            direction = "raises" if c > 0 else "lowers"
            reasons.append(Reason(feature=f, value=_fmt(f, val), direction=direction, text=_text(f, val, direction, bundle.approved_quantiles), contribution=round(c, 4)))
        out.append(reasons)
    return out


def adverse_action_text(reasons: list[Reason], max_items: int = 4) -> str:
    """The principal reasons for a decline, as a notice would list them (reasons that lower the PD are not listed)."""
    raising = [r for r in reasons if r.direction == "raises"][:max_items]
    if not raising:
        return "No principal adverse factors identified."
    return "Principal reasons for this decision: " + "; ".join(r.text for r in raising) + "."


def reason_agreement(a: list[list[Reason]], b: list[list[Reason]], top: int = 3) -> float:
    """Share of rows where the two models' top-`top` reasons overlap in at least one feature."""
    hits = 0
    for ra, rb in zip(a, b, strict=True):
        if {r.feature for r in ra[:top]} & {r.feature for r in rb[:top]}:
            hits += 1
    return round(hits / max(len(a), 1), 4)

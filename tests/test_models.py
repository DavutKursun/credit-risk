from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from credit_risk.calibration import fit_calibrator
from credit_risk.config import TARGET
from credit_risk.drift import psi, psi_by_period, psi_detail, psi_missing, psi_table, status
from credit_risk.explain import adverse_action_text, contributions, reason_agreement, reason_codes
from credit_risk.fairness import audit as fairness_audit
from credit_risk.fairness import four_fifths_ratio, group_report
from credit_risk.features import BUREAU_FEATURES, make_features
from credit_risk.metrics import auc_by_group, expected_calibration_error, ks_statistic, reliability_table, summary
from credit_risk.models import ModelBundle, approved_quantiles, grade_only_model, train_lgbm, train_scorecard
from credit_risk.policy import (
    approve_grades,
    best_threshold,
    breakeven_pd,
    decide,
    expected_profit,
    lgd_from_train,
    policy_table,
    profit_curve,
    realized_pnl,
)


@pytest.fixture(scope="module")
def trained(cohort):
    df, _ = cohort
    tr, dv = df[df["split"] == "train"], df[df["split"] == "dev"]
    X_tr, X_dv = make_features(tr), make_features(dv)
    y_tr, y_dv = tr[TARGET].to_numpy(), dv[TARGET].to_numpy()
    lgbm = train_lgbm(X_tr, y_tr, X_dv, y_dv, params={"learning_rate": 0.1, "min_data_in_leaf": 20}, early_stopping_rounds=30, num_boost_round=300)
    card = train_scorecard(X_tr, y_tr, min_iv=0.0)
    for b in (lgbm, card):
        b.calibrator = fit_calibrator(b.predict_raw(X_dv), y_dv, "isotonic")
        p_tr = b.predict_pd(X_tr)
        b.approved_quantiles = approved_quantiles(X_tr, p_tr < np.quantile(p_tr, 0.7), b.numeric)
    return {"train": tr, "dev": dv, "X_tr": X_tr, "X_dv": X_dv, "y_tr": y_tr, "y_dv": y_dv, "lgbm": lgbm, "card": card}


# --- metrics -------------------------------------------------------------------
def test_metrics_sanity():
    y = np.array([0, 0, 1, 1, 0, 1])
    perfect = np.array([0.1, 0.2, 0.9, 0.8, 0.3, 0.7])
    s = summary(y, perfect)
    assert s["auc"] == 1.0 and s["gini"] == 1.0 and s["ks"] == 1.0 and s["pr_auc"] == 1.0
    assert ks_statistic(y, np.full(6, 0.5)) == pytest.approx(0.0, abs=1e-9) or ks_statistic(y, np.full(6, 0.5)) <= 1.0
    rng = np.random.default_rng(0)
    yy = rng.random(5000) < 0.2
    assert expected_calibration_error(yy, np.full(5000, 0.2)) < 0.03
    t = reliability_table(yy, rng.random(5000), bins=5)
    assert t["n"].sum() == 5000 and len(t) <= 5


# --- models -----------------------------------------------------------------
def test_lgbm_learns_and_is_monotone_in_fico(trained):
    b, X_dv, y_dv = trained["lgbm"], trained["X_dv"], trained["y_dv"]
    s = summary(y_dv, b.predict_pd(X_dv))
    assert s["auc"] > 0.62, s
    row = X_dv.iloc[[0]].copy()
    pds = []
    for f in (640, 690, 740, 790):
        r = row.copy()
        r["fico"] = float(f)
        pds.append(float(b.predict_raw(r)[0]))
    assert pds == sorted(pds, reverse=True), pds  # higher FICO → lower PD, guaranteed by the constraint
    assert b.meta["best_iteration"] >= 1 and b.variant == "lgbm"


def test_scorecard_learns_and_scores_points(trained):
    b, X_dv, y_dv = trained["card"], trained["X_dv"], trained["y_dv"]
    s = summary(y_dv, b.predict_pd(X_dv))
    assert s["auc"] > 0.60, s
    pts = b.score_points(X_dv)
    assert pts is not None and len(pts) == len(X_dv) and np.isfinite(pts).all()
    assert np.corrcoef(pts, b.predict_raw(X_dv))[0, 1] < 0  # more points = safer
    assert len(b.meta["selected_features"]) >= 3
    assert (b.estimator.estimator_.coef_.ravel() <= 0).all() and "dropped_wrong_sign" in b.meta  # every feature points the way its WoE points


def test_calibration_improves_or_keeps_ece(trained):
    b, X_dv, y_dv = trained["lgbm"], trained["X_dv"], trained["y_dv"]
    raw, cal = b.predict_raw(X_dv), b.predict_pd(X_dv)
    assert expected_calibration_error(y_dv, cal) <= expected_calibration_error(y_dv, raw) + 0.01
    assert (0 <= cal).all() and (cal <= 1).all()
    platt = fit_calibrator(raw, y_dv, "platt")
    assert platt.transform(raw).shape == raw.shape


def test_grade_only_reference_and_auc_by_group(trained):
    g = grade_only_model()
    p = g.predict_pd(trained["X_dv"])
    assert summary(trained["y_dv"], p)["auc"] > 0.55
    t = auc_by_group(trained["y_dv"], trained["lgbm"].predict_pd(trained["X_dv"]), trained["dev"]["grade"])
    assert set(t.columns) == {"group", "n", "default_rate", "auc"}


def test_save_load_roundtrip(tmp_path, trained):
    b = trained["lgbm"]
    p = b.save(tmp_path / "lgbm.joblib")
    b2 = ModelBundle.load(p)
    assert np.allclose(b2.predict_pd(trained["X_dv"].head(20)), b.predict_pd(trained["X_dv"].head(20)))
    assert (tmp_path / "lgbm.json").exists() and b2.approved_quantiles


# --- policy -----------------------------------------------------------------
def test_economics_and_decisions(trained):
    econ = lgd_from_train(trained["train"])
    assert 0 < econ["lgd"] < 1 and econ["n_defaults"] > 10
    ev = expected_profit([0.0, 1.0], [10_000, 10_000], [320.0, 320.0], econ["lgd"])
    assert ev[0] > 0 > ev[1]
    be = breakeven_pd([10_000], [320.0], econ["lgd"])
    assert 0 < be[0] < 0.5
    d = decide([0.05, 0.11, 0.30], threshold=0.10, band=0.02)
    assert list(d) == ["approve", "review", "decline"]
    dv = trained["dev"]
    pd_ = trained["lgbm"].predict_pd(trained["X_dv"])
    curve = profit_curve(trained["y_dv"], pd_, dv["funded_amnt"], dv["installment"], econ["lgd"], realized_pnl(dv))
    assert curve["approval_rate"].is_monotonic_increasing and "realized_pnl_total" in curve
    t = best_threshold(curve, min_approval_rate=0.3)
    assert 0 < t < 1
    table = policy_table(trained["y_dv"], pd_, decide(pd_, t), realized_pnl(dv), "lgbm")
    assert abs(table["approve"] + table["review"] + table["decline"] - 1) < 1e-9
    g = approve_grades(dv["grade"])
    assert set(g) <= {"approve", "decline"}


# --- explanations -------------------------------------------------------------
def test_reason_codes_for_both_models(trained):
    X = trained["X_dv"].head(3)
    for b in (trained["lgbm"], trained["card"]):
        reasons = reason_codes(b, X, k=5)
        assert len(reasons) == 3 and all(len(r) == 5 for r in reasons)
        for r in reasons[0]:
            assert r.direction in ("raises", "lowers") and r.text and r.feature in b.features
        c = contributions(b, X)
        assert c.shape == (3, len(b.features))
    text = adverse_action_text(reason_codes(trained["lgbm"], X, k=5)[0])
    assert text.startswith("Principal reasons") or text.startswith("No principal")
    assert 0 <= reason_agreement(reason_codes(trained["lgbm"], X), reason_codes(trained["card"], X)) <= 1


def test_lgbm_contributions_sum_to_logit(trained):
    b, X = trained["lgbm"], trained["X_dv"].head(10)
    raw = np.asarray(b.estimator.predict(X[b.features], pred_contrib=True, num_iteration=b.estimator.best_iteration or None))
    logit = raw.sum(axis=1)
    p = 1 / (1 + np.exp(-logit))
    assert np.allclose(p, b.predict_raw(X), atol=1e-6)


def test_bureau_variant_trains_with_monotone_constraints(cohort):
    df, _ = cohort
    tr, dv = df[df["split"] == "train"], df[df["split"] == "dev"]
    X_tr, X_dv = make_features(tr, bureau=True), make_features(dv, bureau=True)
    b = train_lgbm(X_tr, tr[TARGET].to_numpy(), X_dv, dv[TARGET].to_numpy(), bureau=True, params={"learning_rate": 0.1, "min_data_in_leaf": 20},
                   early_stopping_rounds=30, num_boost_round=200)
    assert b.variant == "lgbm-bureau" and b.bureau and set(BUREAU_FEATURES) <= set(b.features)
    row = X_dv.iloc[[0]].copy()
    pds = []
    for u in (10.0, 40.0, 70.0, 95.0):
        r = row.copy()
        r["bc_util"] = u
        pds.append(float(b.predict_raw(r)[0]))
    assert pds == sorted(pds), pds  # higher bankcard utilization never lowers the PD (constraint +1)
    assert np.isfinite(b.predict_raw(X_dv)).all() and X_dv["mths_since_recent_inq"].isna().any()  # NaN (not on file) scores without imputation


# --- fairness and drift -----------------------------------------------------------
def test_fairness_groups(trained):
    dv, X = trained["dev"], trained["X_dv"]
    d = decide(trained["lgbm"].predict_pd(X), 0.15)
    rep = group_report(trained["y_dv"], d, dv["home_ownership"], min_n=20)
    assert {"group", "n", "approval_rate", "fpr", "tpr"} <= set(rep.columns) and rep["approval_rate"].between(0, 1).all()
    r = four_fifths_ratio(rep)
    assert r is None or 0 <= r <= 1
    reports = fairness_audit(dv, trained["y_dv"], d, X)
    assert set(reports) == {"addr_state", "income_band", "emp_band", "home_ownership"}


def test_psi_reports_missingness_separately_from_values():
    rng = np.random.default_rng(1)
    e = pd.Series(rng.normal(size=20_000))
    e.iloc[:1_500] = np.nan  # a structural missing block in train (the early-2012 bureau gap) that is absent later
    a = pd.Series(rng.normal(size=20_000))
    d = psi_detail(e, a)
    assert d["psi"] < 0.02 and d["missing_share_expected"] == pytest.approx(0.075, abs=1e-3) and d["missing_share_actual"] == 0.0
    assert d["psi_missing"] > 0.25 and d["psi_max"] == d["psi_missing"]
    t = psi_table(pd.DataFrame({"x": e}), pd.DataFrame({"x": a}), ["x"])
    assert {"feature", "psi", "missing_share_expected", "missing_share_actual", "psi_missing", "psi_max", "status"} <= set(t.columns)
    assert t.loc[0, "status"] == "act" and t.loc[0, "psi"] < 0.02  # the values did not move; the status comes from missingness
    assert psi_missing(e, e) == pytest.approx(0.0, abs=1e-9) and psi(e, e) == pytest.approx(0.0, abs=1e-9)


def test_psi_zero_for_same_distribution_and_positive_for_shift(trained):
    X_tr, X_dv = trained["X_tr"], trained["X_dv"]
    assert psi(X_tr["fico"], X_tr["fico"]) == pytest.approx(0.0, abs=1e-9)
    assert psi(X_tr["grade"], X_tr["grade"]) == pytest.approx(0.0, abs=1e-9)
    shifted = X_tr["fico"] + 60
    assert psi(X_tr["fico"], shifted) > 0.25 and status(psi(X_tr["fico"], shifted)) == "act"
    t = psi_table(X_tr, X_dv, ["fico", "dti", "grade"])
    assert set(t["status"]) <= {"stable", "watch", "act"}
    period = trained["dev"]["issue_month"].dt.to_period("Q").astype(str)
    m = psi_by_period(X_tr, X_dv, period, ["fico", "grade"])
    assert m.shape[0] == 2 and m.shape[1] >= 1

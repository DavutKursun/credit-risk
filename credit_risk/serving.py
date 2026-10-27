"""Serving core: load the deployed pair once, apply the policy in force, score one or many applications with reasons.

Only the two deployed bundles are loaded (`DEPLOYED`). The policy is chosen with the POLICY environment variable: `rate85`
(default) applies the thresholds of the 85% operating point chosen on dev; `ev` the expected-value thresholds; both with the
±REVIEW_BAND review band. Thresholds come from the committed `eval/results/policy_dev.json`, never from the test split.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from .config import MODELS, RESULTS, REVIEW_BAND, ROOT
from .drift import status as psi_status
from .explain import adverse_action_text, contributions, reason_codes
from .features import ALL_RAW_COLUMNS, make_features
from .models import ModelBundle, _as_scorecard_frame
from .policy import decide
from .schema import Application, ScoreResponse

DEPLOYED = {"lgbm": "lgbm-bureau-no-state", "scorecard": "scorecard-bureau-no-state"}
POLICIES = ("rate85", "ev")
DEFAULT_POLICY = "rate85"
TOP_K = 5


def version(root: Path = ROOT) -> str:
    """APP_VERSION env var, else a VERSION file (written into the Space tree at upload), else the git short hash, else 'dev'."""
    if os.environ.get("APP_VERSION"):
        return os.environ["APP_VERSION"]
    f = root / "VERSION"
    if f.exists():
        return f.read_text(encoding="utf-8").strip() or "dev"
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=root, capture_output=True, text=True, timeout=3, check=False).stdout.strip()
        return out or "dev"
    except (OSError, subprocess.SubprocessError):
        return "dev"


def load_thresholds(path: Path = RESULTS / "policy_dev.json") -> dict[str, dict[str, float]]:
    """{'ev': {variant: t}, 'rate85': {variant: t}} from the dev policy run (the 85% rows are the fixed-approval-rate thresholds)."""
    p = json.loads(Path(path).read_text(encoding="utf-8"))
    ev = {v: float(t) for v, t in p["thresholds"].items()}
    rate85 = {r["policy"].split("@")[0]: float(r["threshold"]) for r in p["policies"] if r["policy"].endswith("@85%") and r.get("threshold") is not None}
    return {"ev": ev, "rate85": rate85}


@dataclass
class CardFast:
    """One WoE transform per request for the scorecard: PD, points and contributions all follow from logit = intercept + coef · WoE,
    and pdo/odds scaling makes points = offset − factor × logit. Verified against optbinning's own predict_proba, score and the
    explain contributions at load; if anything differs the slow path stays."""

    selected: list[str]
    coef: np.ndarray
    intercept: float
    factor: float
    offset: float

    @classmethod
    def from_bundle(cls, b: ModelBundle) -> CardFast | None:
        card = b.estimator
        try:
            p = card.scaling_method_params
            factor = p["pdo"] / np.log(2)
            return cls(selected=list(card.binning_process_.get_support(names=True)), coef=np.asarray(card.estimator_.coef_).ravel(),
                       intercept=float(np.asarray(card.estimator_.intercept_).ravel()[0]), factor=factor, offset=p["scorecard_points"] - factor * np.log(p["odds"]))
        except (AttributeError, KeyError, TypeError):
            return None

    def run(self, b: ModelBundle, X: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, pd.DataFrame]:
        woe = np.asarray(b.estimator.binning_process_.transform(_as_scorecard_frame(X[self.selected]), metric="woe"), dtype=float)
        logit = self.intercept + woe @ self.coef
        raw = 1.0 / (1.0 + np.exp(-logit))
        points = self.offset - self.factor * logit
        contrib = pd.DataFrame(woe * self.coef, columns=self.selected, index=X.index)
        for f in b.features:
            if f not in contrib:
                contrib[f] = 0.0
        return raw, points, contrib[b.features]

    def verify(self, b: ModelBundle, X: pd.DataFrame, tol_pd: float = 1e-6, tol_points: float = 0.5) -> bool:
        raw, points, contrib = self.run(b, X)
        slow_raw, slow_points, slow_contrib = b.predict_raw(X), b.score_points(X), contributions(b, X)
        return bool(np.max(np.abs(raw - slow_raw)) < tol_pd and np.max(np.abs(points - slow_points)) < tol_points
                    and np.max(np.abs(contrib.to_numpy() - slow_contrib[b.features].to_numpy())) < tol_pd)


@dataclass
class LgbmFast:
    """One LightGBM call per request on a numpy matrix: the contributions give the logit (their sum) and the reasons, so predict()
    runs once instead of twice and skips the pandas-to-numpy conversion. Categorical codes follow the booster's stored category
    lists. Verified against predict_raw and the explain contributions at load; the slow path stays if anything differs."""

    categories: dict[str, list[str]]

    @classmethod
    def from_bundle(cls, b: ModelBundle) -> LgbmFast | None:
        pc = getattr(b.estimator, "pandas_categorical", None)
        if not pc or len(pc) != len(b.categorical):
            return None
        return cls(categories={f: list(c) for f, c in zip(b.categorical, pc, strict=True)})

    def matrix(self, b: ModelBundle, X: pd.DataFrame) -> np.ndarray:
        cols = [X[f].to_numpy(dtype=float) for f in b.numeric]
        for f in b.categorical:
            s = X[f]
            if isinstance(s.dtype, pd.CategoricalDtype) and list(s.cat.categories) == self.categories[f]:
                codes = s.cat.codes.to_numpy(dtype=float)
            else:
                codes = pd.Categorical(s.astype(object), categories=self.categories[f]).codes.astype(float)
            codes[codes < 0] = np.nan
            cols.append(codes)
        return np.column_stack(cols)

    def run(self, b: ModelBundle, X: pd.DataFrame) -> tuple[np.ndarray, pd.DataFrame]:
        contrib = np.asarray(b.estimator.predict(self.matrix(b, X), pred_contrib=True, num_iteration=b.estimator.best_iteration or None), dtype=float)
        raw = 1.0 / (1.0 + np.exp(-contrib.sum(axis=1)))
        return raw, pd.DataFrame(contrib[:, :-1], columns=b.features, index=X.index)

    def verify(self, b: ModelBundle, X: pd.DataFrame, tol: float = 1e-7) -> bool:
        raw, contrib = self.run(b, X)
        return bool(np.max(np.abs(raw - b.predict_raw(X))) < tol and np.max(np.abs(contrib.to_numpy() - contributions(b, X)[b.features].to_numpy())) < tol)


def applications_frame(apps: list[Application]) -> pd.DataFrame:
    rows = [a.model_dump() for a in apps]
    return pd.DataFrame([{c: r.get(c) for c in ALL_RAW_COLUMNS} for r in rows])


@dataclass
class Scorer:
    bundles: dict[str, ModelBundle]
    thresholds: dict[str, dict[str, float]]
    policy: str = DEFAULT_POLICY
    version: str = "dev"
    band: float = REVIEW_BAND
    results_dir: Path = RESULTS
    loaded_at: float = field(default_factory=time.time)
    card_fast: CardFast | None = None
    lgbm_fast: LgbmFast | None = None

    @classmethod
    def load(cls, models_dir: Path = MODELS, results_dir: Path = RESULTS, policy: str | None = None) -> Scorer:
        policy = policy or os.environ.get("POLICY", DEFAULT_POLICY)
        if policy not in POLICIES:
            raise ValueError(f"POLICY must be one of {POLICIES}, got {policy!r}")
        bundles = {k: ModelBundle.load(models_dir / f"{v}.joblib") for k, v in DEPLOYED.items()}
        scorer = cls(bundles=bundles, thresholds=load_thresholds(results_dir / "policy_dev.json"), policy=policy, version=version(), results_dir=results_dir)
        from .schema import SAMPLE_APPLICATIONS

        probe = applications_frame([Application(**a) for a in SAMPLE_APPLICATIONS.values()])
        card = CardFast.from_bundle(bundles["scorecard"])
        if card is not None:
            b = bundles["scorecard"]
            scorer.card_fast = card if card.verify(b, make_features(probe, b.use_lc_grade, b.bureau)) else None
        lgbm = LgbmFast.from_bundle(bundles["lgbm"])
        if lgbm is not None:
            b = bundles["lgbm"]
            scorer.lgbm_fast = lgbm if lgbm.verify(b, make_features(probe, b.use_lc_grade, b.bureau)) else None
        return scorer

    def threshold(self, model: str, policy: str | None = None) -> float:
        return self.thresholds[policy or self.policy][DEPLOYED[model]]

    def score_frame(self, model: str, frame: pd.DataFrame) -> list[ScoreResponse]:
        """Score raw application rows with one model: calibrated PD, decision under the policy in force, five reasons, notice for declines."""
        t0 = time.perf_counter()
        b = self.bundles[model]
        X = make_features(frame, b.use_lc_grade, b.bureau)
        if model == "scorecard" and self.card_fast is not None:
            raw, points, contrib = self.card_fast.run(b, X)
            pd_ = b.calibrator.transform(raw) if b.calibrator is not None else raw
            reasons = reason_codes(b, X, k=TOP_K, contrib=contrib)
        elif model == "lgbm" and self.lgbm_fast is not None:
            raw, contrib = self.lgbm_fast.run(b, X)
            pd_ = b.calibrator.transform(raw) if b.calibrator is not None else raw
            reasons = reason_codes(b, X, k=TOP_K, contrib=contrib)
            points = None
        else:
            pd_ = b.predict_pd(X)
            reasons = reason_codes(b, X, k=TOP_K)
            points = b.score_points(X)
        t = self.threshold(model)
        decisions = decide(pd_, t, self.band)
        per_row_ms = (time.perf_counter() - t0) * 1000 / max(len(frame), 1)
        out = []
        for i in range(len(frame)):
            d = str(decisions[i])
            out.append(ScoreResponse(pd=round(float(pd_[i]), 4), decision=d, reasons=reasons[i], adverse_action=adverse_action_text(reasons[i]) if d == "decline" else None,
                                     score_points=(round(float(points[i])) if points is not None else None), policy=self.policy, threshold=round(t, 4), review_band=self.band,
                                     model=DEPLOYED[model], version=self.version, latency_ms=round(per_row_ms, 2)))
        return out

    def score(self, model: str, app: Application) -> ScoreResponse:
        t0 = time.perf_counter()
        r = self.score_frame(model, applications_frame([app]))[0]
        r.latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        return r

    def score_many(self, model: str, apps: list[Application]) -> list[ScoreResponse]:
        return self.score_frame(model, applications_frame(apps))

    def health(self) -> dict:
        return {"status": "ok", "models": {k: {"variant": v, "features": len(self.bundles[k].features), "calibration": self.bundles[k].meta.get("calibration")} for k, v in DEPLOYED.items()},
                "policy": self.policy, "policies": {p: {k: self.thresholds[p][v] for k, v in DEPLOYED.items()} for p in POLICIES}, "review_band": self.band,
                "scorecard_fast_path": self.card_fast is not None, "lgbm_fast_path": self.lgbm_fast is not None,
                "version": self.version, "uptime_s": round(time.time() - self.loaded_at, 1)}

    def monitoring(self) -> dict:
        """PSI by quarter from the committed drift report: max(value, missingness) per feature with the 0.10 / 0.25 rule, plus both parts."""
        mx = pd.read_csv(self.results_dir / "psi_by_quarter.csv", index_col=0)
        val = pd.read_csv(self.results_dir / "psi_values_by_quarter.csv", index_col=0)
        mis = pd.read_csv(self.results_dir / "psi_missing_by_quarter.csv", index_col=0)
        feats = []
        for f in mx.index:
            worst = float(np.nanmax(mx.loc[f].to_numpy(dtype=float)))
            feats.append({"feature": f, "psi": {q: round(float(mx.loc[f, q]), 4) for q in mx.columns}, "psi_values": {q: round(float(val.loc[f, q]), 4) for q in val.columns} if f in val.index else None,
                          "psi_missing": {q: round(float(mis.loc[f, q]), 4) for q in mis.columns} if f in mis.index else None, "worst": round(worst, 4), "status": psi_status(worst),
                          "driven_by": ("missingness" if f in mis.index and f in val.index and float(mis.loc[f].max()) > float(val.loc[f].max()) else "values")})
        feats.sort(key=lambda r: -r["worst"])
        return {"reference": "train (loans issued 2012-01..2014-12)", "quarters": list(mx.columns), "rule": {"watch": 0.10, "act": 0.25},
                "retrain_when": "a feature's value PSI exceeds 0.25 for a quarter or the score PSI exceeds 0.10", "features": feats}

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
from .explain import adverse_action_text, reason_codes
from .features import ALL_RAW_COLUMNS, make_features
from .models import ModelBundle
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

    @classmethod
    def load(cls, models_dir: Path = MODELS, results_dir: Path = RESULTS, policy: str | None = None) -> Scorer:
        policy = policy or os.environ.get("POLICY", DEFAULT_POLICY)
        if policy not in POLICIES:
            raise ValueError(f"POLICY must be one of {POLICIES}, got {policy!r}")
        bundles = {k: ModelBundle.load(models_dir / f"{v}.joblib") for k, v in DEPLOYED.items()}
        return cls(bundles=bundles, thresholds=load_thresholds(results_dir / "policy_dev.json"), policy=policy, version=version(), results_dir=results_dir)

    def threshold(self, model: str, policy: str | None = None) -> float:
        return self.thresholds[policy or self.policy][DEPLOYED[model]]

    def score_frame(self, model: str, frame: pd.DataFrame) -> list[ScoreResponse]:
        """Score raw application rows with one model: calibrated PD, decision under the policy in force, five reasons, notice for declines."""
        t0 = time.perf_counter()
        b = self.bundles[model]
        X = make_features(frame, b.use_lc_grade, b.bureau)
        pd_ = b.predict_pd(X)
        t = self.threshold(model)
        decisions = decide(pd_, t, self.band)
        reasons = reason_codes(b, X, k=TOP_K)
        points = b.score_points(X)
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

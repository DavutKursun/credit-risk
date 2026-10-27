"""The two models and the reference score, behind one small interface.

* `scorecard` — optbinning BinningProcess (WoE bins, monotonic where the data allows) + logistic regression, scaled to
  points (600 at odds 1:19, 20 points to double the odds). Auditable line by line; what most lenders run.
* `lgbm` — LightGBM, binary objective, early stopping on dev AUC, monotone constraints on the obvious features, native
  categorical handling. No class weighting: the calibrator fixes the level, reweighting would distort it.
* `grade_only` — Lending Club sub-grade as the score (A1 best … G5 worst): the bar any "we built a model" claim must clear.

A trained model is a `ModelBundle`: the estimator, its feature lists, the calibrator fitted on dev (None until M2) and
the approved-population quantiles used for reason codes. Saved with joblib under models/.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from .config import SCORECARD_SCALE, SEED
from .features import CATEGORY_LEVELS, LC_GRADE_FEATURES, MONOTONE, feature_list

LGBM_PARAMS = dict(objective="binary", metric="auc", learning_rate=0.03, num_leaves=31, min_data_in_leaf=200, feature_fraction=0.8, bagging_fraction=0.8,
                   bagging_freq=1, lambda_l2=5.0, verbose=-1, seed=SEED, num_threads=0)
LGBM_ROUNDS = 3000


@dataclass
class ModelBundle:
    name: str  # "scorecard" | "lgbm" | "grade_only"
    use_lc_grade: bool
    numeric: list[str]
    categorical: list[str]
    estimator: object = None
    calibrator: object = None  # fitted on dev; see calibration.py
    approved_quantiles: dict = field(default_factory=dict)  # feature → {q: value} on approved train rows, for reason codes
    meta: dict = field(default_factory=dict)
    bureau: bool = False  # opt-in bureau attribute set (features.BUREAU_FEATURES); the M2 ablation variant

    @property
    def features(self) -> list[str]:
        return self.numeric + self.categorical

    @property
    def variant(self) -> str:
        return f"{self.name}{'' if self.use_lc_grade else '-no-lc-grade'}{'-bureau' if self.bureau else ''}"

    def predict_raw(self, X: pd.DataFrame) -> np.ndarray:
        """Uncalibrated PD (or, for grade_only, a monotone score in [0, 1])."""
        X = X[self.features]
        if self.name == "lgbm":
            return np.asarray(self.estimator.predict(X, num_iteration=self.estimator.best_iteration or None))
        if self.name == "scorecard":
            return self.estimator.predict_proba(_as_scorecard_frame(X))[:, 1]
        if self.name == "grade_only":
            codes = X["sub_grade"].cat.codes.to_numpy().astype(float)
            codes[codes < 0] = np.nan
            return np.nan_to_num(codes / (len(CATEGORY_LEVELS["sub_grade"]) - 1), nan=0.5)
        raise ValueError(self.name)

    def predict_pd(self, X: pd.DataFrame) -> np.ndarray:
        p = self.predict_raw(X)
        return self.calibrator.transform(p) if self.calibrator is not None else p

    def score_points(self, X: pd.DataFrame) -> np.ndarray | None:
        return self.estimator.score(_as_scorecard_frame(X[self.features])) if self.name == "scorecard" else None

    def save(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)
        (path.with_suffix(".json")).write_text(json.dumps({"variant": self.variant, "bureau": self.bureau, "numeric": self.numeric, "categorical": self.categorical, **self.meta}, indent=2, default=str), encoding="utf-8")
        return path

    @staticmethod
    def load(path: Path) -> ModelBundle:
        return joblib.load(path)


def _as_scorecard_frame(X: pd.DataFrame) -> pd.DataFrame:
    """optbinning wants plain object columns for categoricals, floats for numerics."""
    out = X.copy()
    for c in out.columns:
        if isinstance(out[c].dtype, pd.CategoricalDtype):
            out[c] = out[c].astype(object).where(out[c].notna(), None)
    return out


def _monotone_vector(numeric: list[str], categorical: list[str]) -> list[int]:
    return [MONOTONE.get(f, 0) for f in numeric] + [0] * len(categorical)


def train_lgbm(X_train: pd.DataFrame, y_train, X_dev: pd.DataFrame, y_dev, use_lc_grade: bool = True, params: dict | None = None,
               monotone: bool = True, early_stopping_rounds: int = 100, num_boost_round: int = LGBM_ROUNDS, bureau: bool = False) -> ModelBundle:
    """Native lightgbm.train (stable across versions): early stopping on dev AUC; pandas categoricals are stored in the model so
    scoring one Application uses the same codes."""
    import lightgbm as lgb

    numeric, categorical = feature_list(use_lc_grade, bureau)
    feats = numeric + categorical
    p = {**LGBM_PARAMS, **(params or {})}
    if monotone:
        p["monotone_constraints"] = _monotone_vector(numeric, categorical)
    d_train = lgb.Dataset(X_train[feats], label=np.asarray(y_train), categorical_feature=categorical, free_raw_data=False)
    d_dev = lgb.Dataset(X_dev[feats], label=np.asarray(y_dev), categorical_feature=categorical, reference=d_train, free_raw_data=False)
    booster = lgb.train(p, d_train, num_boost_round=num_boost_round, valid_sets=[d_dev], valid_names=["dev"],
                        callbacks=[lgb.early_stopping(early_stopping_rounds, verbose=False)])
    meta = {"best_iteration": int(booster.best_iteration or num_boost_round), "params": {k: v for k, v in p.items() if k != "monotone_constraints"},
            "monotone": monotone, "n_train": len(X_train), "n_dev": len(X_dev)}
    return ModelBundle("lgbm", use_lc_grade, numeric, categorical, booster, meta=meta, bureau=bureau)


def train_scorecard(X_train: pd.DataFrame, y_train, use_lc_grade: bool = True, min_iv: float = 0.02, scale: dict | None = None,
                    bureau: bool = False, max_sign_refits: int = 5) -> ModelBundle:
    """WoE binning + logistic regression, scaled to points. A scorecard must read the same way line by line, so every selected
    feature has to point the way its WoE points: a positive coefficient on WoE (points that fall as the bin gets safer, a
    collinearity artefact, e.g. int_rate next to sub_grade) is dropped and the card refitted until all coefficients are ≤ 0.
    The dropped features are recorded in meta['dropped_wrong_sign']."""
    from optbinning import BinningProcess, Scorecard
    from sklearn.linear_model import LogisticRegression

    numeric, categorical = feature_list(use_lc_grade, bureau)
    scale = scale or SCORECARD_SCALE
    dropped: list[str] = []
    for _ in range(max_sign_refits + 1):
        num = [f for f in numeric if f not in dropped]
        cat = [f for f in categorical if f not in dropped]
        feats = num + cat
        binning = BinningProcess(variable_names=feats, categorical_variables=cat, selection_criteria={"iv": {"min": min_iv}},
                                 binning_fit_params={f: {"monotonic_trend": "auto_asc_desc"} for f in num})
        card = Scorecard(binning_process=binning, estimator=LogisticRegression(C=1.0, max_iter=2000, solver="lbfgs"), scaling_method="pdo_odds",
                         scaling_method_params={"pdo": scale["pdo"], "odds": scale["target_odds"], "scorecard_points": scale["target_score"]})
        card.fit(_as_scorecard_frame(X_train[feats]), np.asarray(y_train))
        selected = [f for f, keep in zip(feats, card.binning_process_.get_support(), strict=True) if keep]  # Scorecard clones and fits its own copy
        wrong_sign = [f for f, c in zip(selected, card.estimator_.coef_.ravel(), strict=True) if c > 0]  # WoE > 0 = safer, so a consistent coefficient is < 0
        if not wrong_sign:
            break
        dropped += wrong_sign
    meta = {"selected_features": selected, "dropped_wrong_sign": dropped, "min_iv": min_iv, "scale": scale, "n_train": len(X_train)}
    return ModelBundle("scorecard", use_lc_grade, num, cat, card, meta=meta, bureau=bureau)


def grade_only_model() -> ModelBundle:
    return ModelBundle("grade_only", True, [], ["sub_grade"], None, meta={"note": "Lending Club sub_grade order as the score"})


def approved_quantiles(X: pd.DataFrame, approved_mask: np.ndarray, numeric: list[str], qs=(0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95)) -> dict:
    """Per numeric feature, quantiles among approved training applications; reason codes compare against these."""
    sub = X.loc[np.asarray(approved_mask, dtype=bool), numeric]
    return {f: {str(q): float(v) for q, v in sub[f].quantile(list(qs)).items()} for f in numeric}


def lc_grade_feature_names() -> list[str]:
    return list(LC_GRADE_FEATURES)

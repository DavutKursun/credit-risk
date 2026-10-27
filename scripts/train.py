"""Train the scorecard and/or LightGBM on train, calibrate on dev, save bundles and dev metrics.

Usage: python scripts/train.py [--model lgbm|scorecard|both] [--no-lc-grade] [--calibrate isotonic|platt|none]
                               [--approval-rate 0.7] [--cohort-dir data/cohort] [--models-dir models] [--out eval/results]
Never reads the test split.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from credit_risk.calibration import fit_calibrator
from credit_risk.config import COHORT, MODELS, RESULTS, TARGET
from credit_risk.data import load_split
from credit_risk.features import (
    RAW_FEATURE_COLUMNS,
    make_features,
)
from credit_risk.leakage import assert_no_leaks, audit
from credit_risk.metrics import reliability_table, summary
from credit_risk.models import approved_quantiles, train_lgbm, train_scorecard


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="both", choices=["lgbm", "scorecard", "both"])
    ap.add_argument("--no-lc-grade", action="store_true", help="drop grade, sub_grade, int_rate, installment (the 'from scratch' variant)")
    ap.add_argument("--calibrate", default="isotonic", choices=["isotonic", "platt", "none"])
    ap.add_argument("--calib-share", type=float, default=0.5, help="earliest share of dev (by issue month) used to fit the calibrator; "
                    "calibration metrics are reported on the remaining, later dev rows so they are out-of-sample")
    ap.add_argument("--approval-rate", type=float, default=0.7, help="share of lowest-PD train rows treated as 'approved' for reason-code quantiles")
    ap.add_argument("--cohort-dir", type=Path, default=COHORT)
    ap.add_argument("--models-dir", type=Path, default=MODELS)
    ap.add_argument("--out", type=Path, default=RESULTS)
    ap.add_argument("--skip-audit", action="store_true")
    a = ap.parse_args(argv)
    use_lc = not a.no_lc_grade

    train, dev = load_split("train", a.cohort_dir), load_split("dev", a.cohort_dir)
    if not a.skip_audit:
        assert_no_leaks(audit(train, TARGET, RAW_FEATURE_COLUMNS), RAW_FEATURE_COLUMNS)
    dev = dev.sort_values("issue_month", kind="stable").reset_index(drop=True)
    X_tr, X_dv = make_features(train, use_lc), make_features(dev, use_lc)
    y_tr, y_dv = train[TARGET].to_numpy(), dev[TARGET].to_numpy()
    n_cal = int(len(dev) * a.calib_share)  # earliest dev rows calibrate; the later ones measure it
    cal_idx, rep_idx = np.arange(n_cal), np.arange(n_cal, len(dev))
    print(f"train {len(X_tr)} rows ({y_tr.mean():.3%} default) | dev {len(X_dv)} rows ({y_dv.mean():.3%}; calibrate on first {n_cal}, report on last {len(rep_idx)}) "
          f"| lc-grade features {'on' if use_lc else 'off'}", flush=True)

    names = ["lgbm", "scorecard"] if a.model == "both" else [a.model]
    results = {}
    for name in names:
        t0 = time.time()
        bundle = train_lgbm(X_tr, y_tr, X_dv, y_dv, use_lc) if name == "lgbm" else train_scorecard(X_tr, y_tr, use_lc)
        fit_s = time.time() - t0
        raw_dv = bundle.predict_raw(X_dv)
        ranking = summary(y_dv, raw_dv)  # ranking on all of dev (early stopping saw it: still optimistic, test is the judge)
        before = summary(y_dv[rep_idx], raw_dv[rep_idx])
        if a.calibrate != "none" and len(cal_idx) > 0:
            bundle.calibrator = fit_calibrator(raw_dv[cal_idx], y_dv[cal_idx], a.calibrate)
        p_dv = bundle.predict_pd(X_dv)
        after = summary(y_dv[rep_idx], p_dv[rep_idx])
        p_tr = bundle.predict_pd(X_tr)
        cut = float(np.quantile(p_tr, a.approval_rate))
        bundle.approved_quantiles = approved_quantiles(X_tr, p_tr < cut, bundle.numeric)
        bundle.meta.update({"calibration": a.calibrate, "calib_share": a.calib_share, "fit_seconds": round(fit_s, 1), "dev_ranking": ranking,
                            "dev_late_before_calibration": before, "dev_late_after_calibration": after, "approved_quantiles_pd_cut": round(cut, 4)})
        path = bundle.save(a.models_dir / f"{bundle.variant}.joblib")
        a.out.mkdir(parents=True, exist_ok=True)
        reliability_table(y_dv[rep_idx], p_dv[rep_idx]).to_csv(a.out / f"reliability_dev_{bundle.variant}.csv", index=False)
        results[bundle.variant] = {"dev_ranking": ranking, "dev_late_before": before, "dev_late_after": after, "fit_seconds": round(fit_s, 1), "model_path": str(path),
                                  **{k: v for k, v in bundle.meta.items() if k in ("best_iteration", "selected_features")}}
        print(f"{bundle.variant}: fit {fit_s:.1f}s | dev AUC {ranking['auc']} KS {ranking['ks']} | late-dev Brier {before['brier']}→{after['brier']} "
              f"ECE {before['ece']}→{after['ece']}", flush=True)
    (a.out / f"train_dev{'' if use_lc else '_no_lc_grade'}.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

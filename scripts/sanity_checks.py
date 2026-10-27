"""Sanity checks on the dev-calibrated bundles, report only (exit 0 regardless):
  1. the three SAMPLE_APPLICATIONS through every bundle: calibrated PD and scorecard points; the order
     clear_approve < borderline < clear_decline must hold;
  2. one monotonicity probe per constrained feature on each LightGBM bundle (sweep the feature over dev quantiles on a fixed row);
  3. the bureau variants' dev AUC gain over their base variant (from eval/results/dev-summary.json); below 0.005 → "adds nothing on dev".

Usage: python scripts/sanity_checks.py [--models-dir models] [--cohort-dir data/cohort] [--out eval/results]
Writes eval/results/sanity_dev.json. Never reads the test split.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from credit_risk.config import COHORT, MODELS, RESULTS
from credit_risk.data import load_split
from credit_risk.features import MONOTONE, application_frame, make_features
from credit_risk.models import ModelBundle
from credit_risk.schema import SAMPLE_APPLICATIONS, Application

SAMPLE_ORDER = ("clear_approve", "borderline", "clear_decline")
BUREAU_GAIN_FLOOR = 0.005


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models-dir", type=Path, default=MODELS)
    ap.add_argument("--cohort-dir", type=Path, default=COHORT)
    ap.add_argument("--out", type=Path, default=RESULTS)
    a = ap.parse_args(argv)
    bundles = [ModelBundle.load(p) for p in sorted(a.models_dir.glob("*.joblib"))]
    out = {"samples": {}, "sample_order_ok": {}, "monotonicity": {}, "bureau_gain": {}}

    # 1. samples
    frames = {k: application_frame(Application(**v).model_dump()) for k, v in SAMPLE_APPLICATIONS.items()}
    for b in bundles:
        res = {}
        for k in SAMPLE_ORDER:
            X = make_features(frames[k], b.use_lc_grade, b.bureau)
            pd_ = float(b.predict_pd(X)[0])
            pts = b.score_points(X)
            res[k] = {"pd": round(pd_, 4), "points": (round(float(pts[0])) if pts is not None else None)}
        out["samples"][b.variant] = res
        out["sample_order_ok"][b.variant] = bool(res["clear_approve"]["pd"] < res["borderline"]["pd"] < res["clear_decline"]["pd"])
    print("samples (calibrated PD / scorecard points):")
    print(f"{'variant':24s} " + " ".join(f"{k:>22s}" for k in SAMPLE_ORDER) + "   order ok")
    for v, res in out["samples"].items():
        cells = [f"{res[k]['pd']:.3f}" + (f" ({res[k]['points']} pts)" if res[k]["points"] is not None else "") for k in SAMPLE_ORDER]
        print(f"{v:24s} " + " ".join(f"{c:>22s}" for c in cells) + f"   {out['sample_order_ok'][v]}")

    # 2. monotonicity probes on LightGBM (uncalibrated PD; the isotonic calibrator is monotone, so the order carries over)
    dev = load_split("dev", a.cohort_dir)
    X_all = make_features(dev, True, True)
    qs = np.array([0.02, 0.1, 0.25, 0.4, 0.5, 0.6, 0.75, 0.9, 0.98])
    for b in bundles:
        if b.name != "lgbm":
            continue
        base = make_features(frames["borderline"], b.use_lc_grade, b.bureau)
        probes = {}
        for f, sign in MONOTONE.items():
            if sign == 0 or f not in b.numeric:
                continue
            grid = np.unique(np.quantile(X_all[f].dropna().to_numpy(dtype=float), qs))
            pds = []
            for v in grid:
                r = base.copy()
                r[f] = float(v)
                pds.append(float(b.predict_raw(r)[0]))
            d = np.diff(pds)
            ok = bool(np.all(d >= -1e-12)) if sign > 0 else bool(np.all(d <= 1e-12))
            probes[f] = {"constraint": sign, "ok": ok, "grid_min": float(grid[0]), "grid_max": float(grid[-1]), "pd_at_min": round(pds[0], 4), "pd_at_max": round(pds[-1], 4),
                         "pd_range": round(float(max(pds) - min(pds)), 4)}
        out["monotonicity"][b.variant] = probes
        bad = [f for f, p in probes.items() if not p["ok"]]
        print(f"\nmonotonicity probes {b.variant}: {len(probes)} constrained features, violations: {bad or 'none'}")
        for f, p in probes.items():
            print(f"  {f:24s} {p['constraint']:+d}  PD {p['pd_at_min']:.3f} → {p['pd_at_max']:.3f} over [{p['grid_min']:,.1f}, {p['grid_max']:,.1f}]  {'ok' if p['ok'] else 'VIOLATION'}")

    # 3. bureau gain on dev
    summ_path = a.out / "dev-summary.json"
    if summ_path.exists():
        metrics = {r["model"]: r for r in json.loads(summ_path.read_text(encoding="utf-8"))["metrics"]}
        for base_name in ("lgbm", "scorecard", "lgbm-no-lc-grade", "scorecard-no-lc-grade"):
            bure = f"{base_name}-bureau" if "no-lc-grade" not in base_name else base_name.replace("-no-lc-grade", "-no-lc-grade-bureau")
            if base_name in metrics and bure in metrics:
                d = round(metrics[bure]["auc"] - metrics[base_name]["auc"], 4)
                out["bureau_gain"][bure] = {"base": base_name, "auc_base": metrics[base_name]["auc"], "auc_bureau": metrics[bure]["auc"], "delta_auc": d,
                                            "ks_delta": round(metrics[bure]["ks"] - metrics[base_name]["ks"], 4),
                                            "verdict": "the nine columns add nothing on dev" if d < BUREAU_GAIN_FLOOR else "the nine columns add signal on dev"}
        print("\nbureau ablation (dev AUC):")
        for v, g in out["bureau_gain"].items():
            print(f"  {v:24s} vs {g['base']:22s} AUC {g['auc_base']:.4f} → {g['auc_bureau']:.4f} (Δ {g['delta_auc']:+.4f}, KS Δ {g['ks_delta']:+.4f}): {g['verdict']}")
    else:
        print("\n(no dev-summary.json: run scripts/evaluate.py --split dev for the bureau ablation)")
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "sanity_dev.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

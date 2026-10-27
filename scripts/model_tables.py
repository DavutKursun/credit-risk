"""Scorecard points table and LightGBM feature importance from the saved bundles.

Usage: python scripts/model_tables.py [--models-dir models] [--out eval/results] [--top 10]
Writes eval/results/scorecard_table.md (feature, bin, count share, event rate, WoE, points for every scorecard variant, the LC-grade
one first) and eval/results/lgbm_importance.csv (top-N features by gain for every LightGBM variant).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from credit_risk.config import MODELS, RESULTS
from credit_risk.models import ModelBundle


def scorecard_markdown(b: ModelBundle) -> list[str]:
    card = b.estimator
    t = card.table(style="detailed")
    cols = [c for c in ("Variable", "Bin", "Count (%)", "Event rate", "WoE", "Points") if c in t.columns]
    scale = b.meta.get("scale", {})
    lines = [f"## {b.variant}", "",
             (f"{len(b.meta.get('selected_features', []))} of {len(b.features)} features selected (IV ≥ {b.meta.get('min_iv')}); "
              f"{scale.get('target_score')} points at odds 1:{scale.get('target_odds')}, {scale.get('pdo')} points to double the odds; "
              f"trained on {b.meta.get('n_train', 0):,} loans. More points = safer."), "",
             "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in t.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            if c == "Bin":
                cells.append(str(v).replace("|", "/"))
            elif c in ("Count (%)", "Event rate"):
                cells.append(f"{100 * float(v):.1f}%")
            elif c in ("WoE", "Points"):
                cells.append(f"{float(v):.2f}" if pd.notna(v) else "")
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return lines + [""]


def lgbm_importance(b: ModelBundle, top: int) -> pd.DataFrame:
    booster = b.estimator
    gain = np.asarray(booster.feature_importance(importance_type="gain"), dtype=float)
    split = np.asarray(booster.feature_importance(importance_type="split"), dtype=int)
    t = pd.DataFrame({"variant": b.variant, "feature": booster.feature_name(), "gain": gain.round(1), "gain_share": (gain / max(gain.sum(), 1e-12)).round(4), "splits": split})
    t = t.sort_values("gain", ascending=False).head(top).reset_index(drop=True)
    t.insert(1, "rank", np.arange(1, len(t) + 1))
    return t


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models-dir", type=Path, default=MODELS)
    ap.add_argument("--out", type=Path, default=RESULTS)
    ap.add_argument("--top", type=int, default=10)
    a = ap.parse_args(argv)
    bundles = [ModelBundle.load(p) for p in sorted(a.models_dir.glob("*.joblib"))]
    order = {"scorecard": 0, "scorecard-bureau": 1, "scorecard-no-lc-grade": 2}
    cards = sorted([b for b in bundles if b.name == "scorecard"], key=lambda b: order.get(b.variant, 9))
    lgbms = [b for b in bundles if b.name == "lgbm"]
    a.out.mkdir(parents=True, exist_ok=True)
    if cards:
        md = ["# Scorecard points tables (train fit, dev-calibrated bundles)", ""]
        for b in cards:
            md += scorecard_markdown(b)
        (a.out / "scorecard_table.md").write_text("\n".join(md), encoding="utf-8")
        print(f"scorecard_table.md: {len(cards)} variant(s)")
    if lgbms:
        imp = pd.concat([lgbm_importance(b, a.top) for b in lgbms], ignore_index=True)
        imp.to_csv(a.out / "lgbm_importance.csv", index=False)
        print(imp.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

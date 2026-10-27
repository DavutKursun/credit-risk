"""PSI of every feature and of each model's score, train vs each later quarter (dev + test issue months, scores only;
the target is never read here, so running it on test is allowed).

Usage: python scripts/drift_report.py [--models-dir models] [--out eval/results]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from credit_risk.config import COHORT, MODELS, RESULTS
from credit_risk.data import load_split
from credit_risk.drift import psi_by_period, status
from credit_risk.features import make_features
from credit_risk.models import ModelBundle


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models-dir", type=Path, default=MODELS)
    ap.add_argument("--cohort-dir", type=Path, default=COHORT)
    ap.add_argument("--out", type=Path, default=RESULTS)
    a = ap.parse_args(argv)
    train = load_split("train", a.cohort_dir)
    later = pd.concat([load_split("dev", a.cohort_dir), load_split("test", a.cohort_dir)], ignore_index=True)
    X_tr, X_lt = make_features(train, True), make_features(later, True)
    period = later["issue_month"].dt.to_period("Q").astype(str)
    table = psi_by_period(X_tr, X_lt, period, list(X_tr.columns))
    for p in sorted(a.models_dir.glob("*.joblib")):
        b = ModelBundle.load(p)
        s_tr = pd.Series(b.predict_pd(make_features(train, b.use_lc_grade)), name="score")
        s_lt = pd.Series(b.predict_pd(make_features(later, b.use_lc_grade)), name="score")
        row = psi_by_period(s_tr.to_frame(), s_lt.to_frame(), period, ["score"]).iloc[0]
        table.loc[f"score:{b.variant}"] = row
    a.out.mkdir(parents=True, exist_ok=True)
    table.round(4).to_csv(a.out / "psi_by_quarter.csv")
    worst = table.max(axis=1).sort_values(ascending=False)
    print(table.round(3).to_string())
    print("\nworst PSI per feature:", {k: f"{v:.3f} ({status(v)})" for k, v in worst.head(8).items()})
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(8, max(4, 0.3 * len(table))))
        im = ax.imshow(table.to_numpy(dtype=float), aspect="auto", cmap="YlOrRd", vmin=0, vmax=0.3)
        ax.set_xticks(range(table.shape[1]), table.columns)
        ax.set_yticks(range(table.shape[0]), table.index)
        fig.colorbar(im, ax=ax, label="PSI vs train")
        ax.set_title("Population stability by quarter (0.10 watch, 0.25 act)")
        fig.tight_layout()
        fig.savefig(a.out / "psi_by_quarter.png", dpi=120)
        print(f"heat map: {a.out / 'psi_by_quarter.png'}")
    except ImportError:
        print("matplotlib not installed; CSV only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

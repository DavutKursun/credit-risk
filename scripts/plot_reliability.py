"""Reliability (calibration) plots on the later half of dev, before and after calibration, one PNG per saved bundle.

The calibrator was fitted on the earlier half of dev (by issue month, share = bundle.meta['calib_share']); the plots and tables
use the remaining rows, so they are out-of-sample. Equal-count bins by predicted PD; the 45° line is perfect calibration.

Usage: python scripts/plot_reliability.py [--models-dir models] [--cohort-dir data/cohort] [--out eval/results] [--bins 10]
Writes eval/results/reliability_dev_<variant>.png, reliability_dev_<variant>_before.csv, reliability_dev_<variant>.csv (after)
and reliability_dev_summary.json. Never reads the test split.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from credit_risk.config import COHORT, MODELS, RESULTS, TARGET
from credit_risk.data import load_split
from credit_risk.features import make_features
from credit_risk.metrics import expected_calibration_error, reliability_table
from credit_risk.models import ModelBundle


def late_dev_index(n_dev: int, calib_share: float) -> np.ndarray:
    """Rows of the issue-month-sorted dev split that the calibrator did not see (same rule as scripts/train.py)."""
    return np.arange(int(n_dev * calib_share), n_dev)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models-dir", type=Path, default=MODELS)
    ap.add_argument("--cohort-dir", type=Path, default=COHORT)
    ap.add_argument("--out", type=Path, default=RESULTS)
    ap.add_argument("--bins", type=int, default=10)
    a = ap.parse_args(argv)
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    dev = load_split("dev", a.cohort_dir).sort_values("issue_month", kind="stable").reset_index(drop=True)
    y = dev[TARGET].to_numpy()
    a.out.mkdir(parents=True, exist_ok=True)
    summary = {}
    for p in sorted(a.models_dir.glob("*.joblib")):
        b = ModelBundle.load(p)
        X = make_features(dev, b.use_lc_grade, b.bureau)
        rep = late_dev_index(len(dev), float(b.meta.get("calib_share", 0.5)))
        raw, cal, yy = b.predict_raw(X)[rep], b.predict_pd(X)[rep], y[rep]
        before, after = reliability_table(yy, raw, a.bins), reliability_table(yy, cal, a.bins)
        before.to_csv(a.out / f"reliability_dev_{b.variant}_before.csv", index=False)
        after.to_csv(a.out / f"reliability_dev_{b.variant}.csv", index=False)
        ece_b, ece_a = expected_calibration_error(yy, raw, a.bins), expected_calibration_error(yy, cal, a.bins)
        lim = float(max(before[["predicted", "observed"]].max().max(), after[["predicted", "observed"]].max().max()) * 1.08)
        fig, ax = plt.subplots(figsize=(5.6, 5.6))
        ax.plot([0, lim], [0, lim], color="grey", linestyle="--", linewidth=1, label="perfect calibration")
        ax.plot(before["predicted"], before["observed"], marker="o", label=f"before calibration (ECE {ece_b:.3f})")
        ax.plot(after["predicted"], after["observed"], marker="s", label=f"after {b.meta.get('calibration', 'calibration')} (ECE {ece_a:.3f})")
        ax.set_xlabel("mean predicted PD per equal-count bin")
        ax.set_ylabel("observed default rate")
        ax.set_title(f"{b.variant} — later half of dev, n = {len(rep):,}")
        ax.set_xlim(0, lim)
        ax.set_ylim(0, lim)
        ax.grid(alpha=0.3)
        ax.legend(loc="upper left")
        fig.tight_layout()
        fig.savefig(a.out / f"reliability_dev_{b.variant}.png", dpi=120)
        plt.close(fig)
        summary[b.variant] = {"n_late_dev": len(rep), "observed_rate": round(float(yy.mean()), 4), "mean_pd_before": round(float(raw.mean()), 4),
                              "mean_pd_after": round(float(cal.mean()), 4), "ece_before": round(ece_b, 5), "ece_after": round(ece_a, 5),
                              "max_abs_gap_before": round(float(before["abs_gap"].max()), 4), "max_abs_gap_after": round(float(after["abs_gap"].max()), 4)}
        print(f"{b.variant}: late dev n={len(rep):,} observed {yy.mean():.4f} | mean PD {raw.mean():.4f} → {cal.mean():.4f} | ECE {ece_b:.4f} → {ece_a:.4f}")
    (a.out / "reliability_dev_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

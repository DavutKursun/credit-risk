"""Proxy-group audit of one model's decisions on a split (default dev). Writes one CSV per grouping and a JSON summary.

Usage: python scripts/fairness_report.py --model lgbm [--split dev] [--threshold T]  (threshold defaults to the dev policy run)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from credit_risk.config import COHORT, MODELS, RESULTS, REVIEW_BAND, TARGET
from credit_risk.data import load_split
from credit_risk.fairness import audit, four_fifths_ratio, gaps
from credit_risk.features import make_features
from credit_risk.models import ModelBundle
from credit_risk.policy import decide


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="lgbm", help="variant name, e.g. lgbm or scorecard-no-lc-grade")
    ap.add_argument("--split", default="dev", choices=["dev", "test"])
    ap.add_argument("--threshold", type=float, default=None)
    ap.add_argument("--min-n", type=int, default=200, help="smallest group reported")
    ap.add_argument("--tag", default="", help="suffix for the output files, e.g. '@85' for a fixed-approval-rate threshold")
    ap.add_argument("--models-dir", type=Path, default=MODELS)
    ap.add_argument("--cohort-dir", type=Path, default=COHORT)
    ap.add_argument("--out", type=Path, default=RESULTS)
    a = ap.parse_args(argv)
    b = ModelBundle.load(a.models_dir / f"{a.model}.joblib")
    df = load_split(a.split, a.cohort_dir)
    t = a.threshold
    if t is None:
        policy = json.loads((a.out / "policy_dev.json").read_text(encoding="utf-8"))
        if a.model not in policy["thresholds"]:
            print(f"no dev threshold for {a.model} in policy_dev.json; pass --threshold or run policy_eval.py --variants {a.model}")
            return 2
        t = policy["thresholds"][a.model]
    X = make_features(df, b.use_lc_grade, b.bureau)
    d = decide(b.predict_pd(X), t, REVIEW_BAND)
    reports = audit(df, df[TARGET].to_numpy(), d, make_features(df, True), min_n=a.min_n)
    summary = {"model": a.model, "split": a.split, "threshold": t, "tag": a.tag, "review_band": REVIEW_BAND, "four_fifths_ratio": {}, "gaps": {}, "groups": {}}
    for name, rep in reports.items():
        rep.to_csv(a.out / f"fairness_{a.split}_{a.model}{a.tag}_{name}.csv", index=False)
        summary["four_fifths_ratio"][name] = four_fifths_ratio(rep)
        summary["gaps"][name] = gaps(rep)
        summary["groups"][name] = rep.to_dict(orient="records")
        print(f"\n== {name} ==\n{rep.to_string(index=False)}")
    (a.out / f"fairness_{a.split}_{a.model}{a.tag}.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("\nfour-fifths ratios (min/max approval rate across groups):", summary["four_fifths_ratio"])
    print("gaps (max − min across groups):", json.dumps(summary["gaps"]))
    print("Caveat: proxies only — no protected attributes exist in the data; this shows disparate approval rates, not their cause. "
          "Compare the approval-rate gap with the default-rate gap of the same groups before reading it as treatment.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Ranking + calibration metrics for every saved model on one split. `--split test` needs `--final` (used once, at M4).

Usage: python scripts/evaluate.py --split dev [--models-dir models] [--cohort-dir data/cohort] [--out eval/results]
       python scripts/evaluate.py --split test --final
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from credit_risk.config import COHORT, MODELS, RESULTS, TARGET
from credit_risk.data import load_split
from credit_risk.features import make_features
from credit_risk.metrics import auc_by_group, reliability_table, summary
from credit_risk.models import ModelBundle, grade_only_model


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="dev", choices=["dev", "test"])
    ap.add_argument("--final", action="store_true", help="required for --split test; the run date is recorded in the results")
    ap.add_argument("--models-dir", type=Path, default=MODELS)
    ap.add_argument("--cohort-dir", type=Path, default=COHORT)
    ap.add_argument("--out", type=Path, default=RESULTS)
    a = ap.parse_args(argv)
    if a.split == "test" and not a.final:
        print("refusing: the test split is evaluated once, at Milestone 4, with --final. Use --split dev until then.")
        return 3
    df = load_split(a.split, a.cohort_dir)
    y = df[TARGET].to_numpy()
    bundles = [ModelBundle.load(p) for p in sorted(a.models_dir.glob("*.joblib"))]
    if not bundles:
        print(f"no models in {a.models_dir} — run scripts/train.py first")
        return 2
    rows, by_grade = [], {}
    for b in bundles + [grade_only_model()]:
        X = make_features(df, b.use_lc_grade) if b.name != "grade_only" else make_features(df, True)
        p = b.predict_pd(X)
        s = summary(y, p)
        if b.name == "grade_only":  # a rank score, not a probability: calibration metrics do not apply
            s.update({"mean_pd": None, "brier": None, "log_loss": None, "ece": None})
        rows.append({"model": b.variant, **s})
        if b.name != "grade_only":
            reliability_table(y, p).to_csv(a.out / f"reliability_{a.split}_{b.variant}.csv", index=False)
            by_grade[b.variant] = auc_by_group(y, p, df["grade"]).to_dict(orient="records")
    table = pd.DataFrame(rows)
    a.out.mkdir(parents=True, exist_ok=True)
    stamp = {"split": a.split, "run_date": str(date.today()), "n": len(df), "metrics": rows, "auc_by_grade": by_grade}
    (a.out / f"{a.split}-summary.json").write_text(json.dumps(stamp, indent=2), encoding="utf-8")
    md = [f"# {a.split} results — {len(df):,} loans, run {stamp['run_date']}", "", table.to_markdown(index=False), ""]
    (a.out / f"{a.split}-summary.md").write_text("\n".join(md), encoding="utf-8")
    print(table.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

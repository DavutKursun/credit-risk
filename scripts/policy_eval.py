"""Turn PDs into decisions and score the policies by expected profit and realized P&L.

LGD and the profit parameters are estimated on train. The threshold is chosen on dev (max expected profit); on test it is
applied unchanged (pass --threshold from the dev run). Policies compared: approve all · grades A–C · sub_grade cut at the
same approval rate · each model with the review band.

Usage: python scripts/policy_eval.py --split dev [--threshold T] [--min-approval-rate 0.5] [--final]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from credit_risk.config import COHORT, MODELS, RESULTS, REVIEW_BAND, TARGET
from credit_risk.data import load_split
from credit_risk.features import make_features
from credit_risk.models import ModelBundle
from credit_risk.policy import approve_grades, best_threshold, decide, lgd_from_train, policy_table, profit_curve, realized_pnl


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="dev", choices=["dev", "test"])
    ap.add_argument("--final", action="store_true")
    ap.add_argument("--threshold", type=float, default=None, help="fixed PD threshold (from the dev run) — required on test")
    ap.add_argument("--min-approval-rate", type=float, default=0.5, help="dev threshold search floor")
    ap.add_argument("--models-dir", type=Path, default=MODELS)
    ap.add_argument("--cohort-dir", type=Path, default=COHORT)
    ap.add_argument("--out", type=Path, default=RESULTS)
    a = ap.parse_args(argv)
    if a.split == "test" and (not a.final or a.threshold is None):
        print("refusing: test needs --final and the --threshold chosen on dev")
        return 3
    train, df = load_split("train", a.cohort_dir), load_split(a.split, a.cohort_dir)
    econ = lgd_from_train(train)
    y, realized = df[TARGET].to_numpy(), realized_pnl(df)
    funded, inst = df["funded_amnt"].to_numpy(dtype=float), df["installment"].to_numpy(dtype=float)
    out_rows = [policy_table(y, np.full(len(y), "approve", dtype=object), np.full(len(y), "approve", dtype=object), realized, "approve_all"),
                policy_table(y, None, approve_grades(df["grade"]), realized, "approve_grades_A-C")]
    curves, chosen = {}, {}
    for p in sorted(a.models_dir.glob("*.joblib")):
        b = ModelBundle.load(p)
        pd_ = b.predict_pd(make_features(df, b.use_lc_grade, b.bureau))
        curve = profit_curve(y, pd_, funded, inst, econ["lgd"], realized)
        curves[b.variant] = curve
        t = a.threshold if a.threshold is not None else best_threshold(curve, min_approval_rate=a.min_approval_rate)
        chosen[b.variant] = t
        d = decide(pd_, t, REVIEW_BAND)
        out_rows.append(policy_table(y, pd_, d, realized, f"{b.variant}@{t:.2f}"))
        # LC sub_grade cut at the same approval rate (the fair comparison for a lender that already has grades)
        rate = float((d == "approve").mean())
        label = f"sub_grade_cut@{rate:.0%}"
        if label not in {r["policy"] for r in out_rows}:
            order = make_features(df, True)["sub_grade"].cat.codes.to_numpy()
            cut = np.quantile(order, rate)
            out_rows.append(policy_table(y, None, np.where(order <= cut, "approve", "decline").astype(object), realized, label))
        curve.to_csv(a.out / f"profit_curve_{a.split}_{b.variant}.csv", index=False)
    table = pd.DataFrame(out_rows)
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / f"policy_{a.split}.json").write_text(json.dumps({"economics": econ, "thresholds": chosen, "review_band": REVIEW_BAND, "policies": out_rows}, indent=2), encoding="utf-8")
    print("economics (train):", json.dumps(econ))
    print("thresholds:", chosen)
    print(table.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

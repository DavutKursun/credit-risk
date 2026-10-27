"""Turn PDs into decisions and score the policies by expected profit and realized P&L (dev now; test once, at M4).

LGD and the profit parameters come from train. Per model: (a) the expected-value threshold chosen on the dev profit curve with a
minimum approval rate, applied with a review band of ±REVIEW_BAND (approve / review / decline); (b) fixed approval rates (80, 85,
90%) for the comparison a lender asks for. References: approve all, grades A–C, and the Lending Club sub-grade cut at the same
approval rate as each policy ("defaults avoided per 1,000 approvals" measures the model against that cut and against approve-all).
On test the dev thresholds are applied unchanged (--final --thresholds-from eval/results/policy_dev.json).

Usage: python scripts/policy_eval.py --split dev [--variants lgbm-bureau,scorecard-bureau] [--rates 0.8,0.85,0.9] [--min-approval-rate 0.5]
       python scripts/policy_eval.py --split test --final --thresholds-from eval/results/policy_dev.json --variants ...
Writes policy_<split>.json, policy_<split>.csv, profit_curve_<split>_<variant>.csv and .png.
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
from credit_risk.policy import (
    approve_at_rate,
    approve_grades,
    best_threshold,
    decide,
    expected_profit,
    lgd_from_train,
    policy_table,
    profit_curve,
    realized_pnl,
    subgrade_cut,
)


def _row(label: str, y, d, realized, funded, ev=None, threshold=None) -> dict:
    t = policy_table(y, None, d, realized, label)
    appr = np.asarray(d) == "approve"
    t["threshold"] = threshold
    t["realized_pnl_per_dollar_lent"] = round(float(realized[appr].sum() / max(funded[appr].sum(), 1.0)), 4) if appr.any() else None
    t["expected_profit_per_approved"] = round(float(ev[appr].mean()), 2) if ev is not None and appr.any() else None
    return t


def _plot_curve(curve: pd.DataFrame, t: float, variant: str, split: str, path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(curve["threshold"], curve["expected_profit_total"] / 1e6, label="expected profit of the approved set")
    if "realized_pnl_total" in curve:
        ax.plot(curve["threshold"], curve["realized_pnl_total"] / 1e6, label="realized P&L of the approved set")
    ax.axvline(t, color="grey", linestyle="--", linewidth=1)
    at = curve.loc[(curve["threshold"] - t).abs().idxmin()]
    ax.annotate(f"t = {t:.2f}\napproval {at['approval_rate']:.0%}", (t, ax.get_ylim()[1] * 0.92), fontsize=9, ha="left")
    ax.set_xlabel("PD threshold (approve below)")
    ax.set_ylabel("$ million")
    ax.set_title(f"{variant}: profit curve on {split}")
    ax.grid(alpha=0.3)
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="dev", choices=["dev", "test"])
    ap.add_argument("--final", action="store_true")
    ap.add_argument("--thresholds-from", type=Path, default=None, help="policy_dev.json with the thresholds chosen on dev — required on test")
    ap.add_argument("--min-approval-rate", type=float, default=0.5, help="dev threshold search floor")
    ap.add_argument("--rates", default="0.8,0.85,0.9", help="fixed approval rates to compare")
    ap.add_argument("--variants", default=None, help="comma-separated bundle variants (default: every bundle in --models-dir)")
    ap.add_argument("--models-dir", type=Path, default=MODELS)
    ap.add_argument("--cohort-dir", type=Path, default=COHORT)
    ap.add_argument("--out", type=Path, default=RESULTS)
    a = ap.parse_args(argv)
    if a.split == "test" and (not a.final or a.thresholds_from is None):
        print("refusing: test needs --final and --thresholds-from <policy_dev.json> with the thresholds chosen on dev")
        return 3
    train, df = load_split("train", a.cohort_dir), load_split(a.split, a.cohort_dir)
    econ = lgd_from_train(train)
    y, realized = df[TARGET].to_numpy(), realized_pnl(df)
    funded, inst = df["funded_amnt"].to_numpy(dtype=float), df["installment"].to_numpy(dtype=float)
    overall_dr = float(y.mean())
    codes = make_features(df, True)["sub_grade"].cat.codes.to_numpy()
    rates = [float(r) for r in a.rates.split(",")]
    fixed = json.loads(a.thresholds_from.read_text(encoding="utf-8"))["thresholds"] if a.thresholds_from else {}
    wanted = set(a.variants.split(",")) if a.variants else None
    bundles = [b for b in (ModelBundle.load(p) for p in sorted(a.models_dir.glob("*.joblib"))) if wanted is None or b.variant in wanted]

    rows = [_row("approve_all", y, np.full(len(y), "approve", dtype=object), realized, funded),
            _row("approve_grades_A-C", y, approve_grades(df["grade"]), realized, funded)]
    sub_at = {}
    for r in rates:
        row = _row(f"sub_grade_cut@{r:.0%}", y, subgrade_cut(codes, r), realized, funded)
        sub_at[r] = row
        rows.append(row)
    chosen, approval_at_t, review_at_t = {}, {}, {}
    a.out.mkdir(parents=True, exist_ok=True)
    for b in bundles:
        X = make_features(df, b.use_lc_grade, b.bureau)
        raw, pd_ = b.predict_raw(X), b.predict_pd(X)
        ev = expected_profit(pd_, funded, inst, econ["lgd"])
        curve = profit_curve(y, pd_, funded, inst, econ["lgd"], realized)
        t = float(fixed[b.variant]) if fixed else best_threshold(curve, min_approval_rate=a.min_approval_rate)
        chosen[b.variant] = t
        d = decide(pd_, t, REVIEW_BAND)
        row = _row(f"{b.variant}@ev", y, d, realized, funded, ev, round(t, 4))
        sub_same = subgrade_cut(codes, row["approve"])
        row["defaults_avoided_per_1000_vs_subgrade_cut"] = round(1000 * (float(y[sub_same == "approve"].mean()) - row["default_rate_approved"]), 1)
        row["defaults_avoided_per_1000_vs_approve_all"] = round(1000 * (overall_dr - row["default_rate_approved"]), 1)
        rows.append(row)
        approval_at_t[b.variant], review_at_t[b.variant] = row["approve"], row["review"]
        for r in rates:
            d = approve_at_rate(pd_, r, tie_break=raw)
            tr = float(np.max(pd_[d == "approve"])) if (d == "approve").any() else None
            row = _row(f"{b.variant}@{r:.0%}", y, d, realized, funded, ev, round(tr, 4) if tr is not None else None)
            row["defaults_avoided_per_1000_vs_subgrade_cut"] = round(1000 * (sub_at[r]["default_rate_approved"] - row["default_rate_approved"]), 1)
            row["defaults_avoided_per_1000_vs_approve_all"] = round(1000 * (overall_dr - row["default_rate_approved"]), 1)
            rows.append(row)
        curve.to_csv(a.out / f"profit_curve_{a.split}_{b.variant}.csv", index=False)
        try:
            _plot_curve(curve, t, b.variant, a.split, a.out / f"profit_curve_{a.split}_{b.variant}.png")
        except ImportError:
            pass
    table = pd.DataFrame(rows)
    cols = ["policy", "threshold", "approve", "review", "decline", "default_rate_approved", "realized_pnl_per_approved", "realized_pnl_per_dollar_lent",
            "realized_pnl_total", "expected_profit_per_approved", "defaults_caught", "defaults_avoided_per_1000_vs_subgrade_cut", "defaults_avoided_per_1000_vs_approve_all", "n"]
    table = table[[c for c in cols if c in table.columns]]
    table.to_csv(a.out / f"policy_{a.split}.csv", index=False)
    (a.out / f"policy_{a.split}.json").write_text(json.dumps({"split": a.split, "economics": econ, "thresholds": chosen, "approval_rate_at_threshold": approval_at_t,
                                                               "review_share_at_threshold": review_at_t, "review_band": REVIEW_BAND, "min_approval_rate": a.min_approval_rate,
                                                               "rates": rates, "policies": rows}, indent=2), encoding="utf-8")
    print("economics (train):", json.dumps(econ))
    print("thresholds:", chosen, "| approval at threshold:", approval_at_t, "| review share:", review_at_t)
    with pd.option_context("display.width", 250, "display.max_columns", 20):
        print(table.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

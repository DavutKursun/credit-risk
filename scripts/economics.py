"""Population economics on TRAIN only (CLAUDE.md §3.4): LGD, gain if repaid, loss if default, break-even PD.

LGD = 1 − recovery on charged-off train loans; gain if repaid = installment × 36 − funded_amnt (scheduled interest, an upper
bound because of prepayment); loss if default = LGD × funded_amnt; break-even PD = gain / (gain + loss). Realized P&L on train
is shown next to them as a sanity check of the parameters (it is never a feature). Never reads dev or test.

Usage: python scripts/economics.py [--cohort-dir data/cohort] [--out eval/results]
Writes eval/results/economics_train.json and economics_train.md.
"""

from __future__ import annotations

import argparse
import json
import sys
from itertools import pairwise
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from credit_risk.config import COHORT, RESULTS, TARGET
from credit_risk.data import load_split
from credit_risk.features import to_percent
from credit_risk.policy import TERM_MONTHS, breakeven_pd, gain_if_repaid, lgd_from_train, realized_pnl

RATE_BANDS = [5, 10, 15, 20, 25, 30]


def _agg(frame: pd.DataFrame, key: pd.Series) -> pd.DataFrame:
    g = frame.groupby(key, observed=True)
    out = pd.DataFrame({
        "n": g.size(), "default_rate": g[TARGET].mean(), "gain_if_repaid_median": g["gain"].median(), "loss_if_default_median": g["loss"].median(),
        "breakeven_pd_median": g["breakeven"].median(), "share_interest_exceeds_lgd_x_principal": g["interest_covers"].mean(),
        "realized_pnl_mean": g["realized"].mean(),
    })
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cohort-dir", type=Path, default=COHORT)
    ap.add_argument("--out", type=Path, default=RESULTS)
    a = ap.parse_args(argv)
    train = load_split("train", a.cohort_dir)
    econ = lgd_from_train(train)
    lgd = econ["lgd"]
    grade = train["grade"].astype("string")

    bad = train[train[TARGET] == 1]
    recovery = ((bad["total_pymnt"].fillna(0) + bad["recoveries"].fillna(0) - bad["collection_recovery_fee"].fillna(0)) / bad["funded_amnt"]).clip(0, 1)
    lgd_by_grade = (1 - recovery).groupby(bad["grade"].astype("string"), observed=True).agg(["mean", "median", "count"]).rename(columns={"count": "n_defaults"})

    funded, inst = train["funded_amnt"].to_numpy(dtype=float), train["installment"].to_numpy(dtype=float)
    frame = pd.DataFrame(index=train.index)
    frame[TARGET] = train[TARGET].to_numpy()
    frame["gain"] = gain_if_repaid(funded, inst)
    frame["loss"] = lgd * funded
    frame["breakeven"] = breakeven_pd(funded, inst, lgd)
    frame["interest_covers"] = frame["gain"] > frame["loss"]
    frame["realized"] = realized_pnl(train)
    lgd_grade_loan = grade.map(lgd_by_grade["mean"]).astype(float).to_numpy()
    frame["breakeven_grade_lgd"] = np.where(frame["gain"] + lgd_grade_loan * funded > 0, frame["gain"] / (frame["gain"] + lgd_grade_loan * funded), 0.0)

    by_grade = _agg(frame, grade).join(lgd_by_grade.rename(columns={"mean": "lgd_mean", "median": "lgd_median"}))
    by_grade["breakeven_pd_median_grade_lgd"] = frame.groupby(grade, observed=True)["breakeven_grade_lgd"].median()
    by_grade = by_grade[["n", "default_rate", "n_defaults", "lgd_mean", "lgd_median", "gain_if_repaid_median", "loss_if_default_median",
                         "breakeven_pd_median", "breakeven_pd_median_grade_lgd", "share_interest_exceeds_lgd_x_principal", "realized_pnl_mean"]]
    rate = to_percent(train["int_rate"])
    band = pd.cut(rate, bins=RATE_BANDS, right=False, labels=[f"{lo}–{hi}%" for lo, hi in pairwise(RATE_BANDS)])
    by_band = _agg(frame, band)

    overall = {"lgd": lgd, "lgd_median": econ["lgd_median"], "n_defaults": econ["n_defaults"], "n_train": len(train), "default_rate": round(float(frame[TARGET].mean()), 4),
               "gain_if_repaid_median": round(float(frame["gain"].median()), 2), "loss_if_default_median": round(float(frame["loss"].median()), 2),
               "breakeven_pd_median": round(float(frame["breakeven"].median()), 4), "share_interest_exceeds_lgd_x_principal": round(float(frame["interest_covers"].mean()), 4),
               "realized_pnl_mean": round(float(frame["realized"].mean()), 2), "realized_pnl_per_dollar_lent": round(float(frame["realized"].sum() / funded.sum()), 4),
               "term_months": TERM_MONTHS, "int_rate_min": round(float(rate.min()), 2), "int_rate_max": round(float(rate.max()), 2)}
    notes = ["All numbers from the train split (loans issued 2012-01..2014-12); dev and test never read.",
             "Gain if repaid = installment × 36 − funded_amnt is scheduled interest: an upper bound, prepayment lowers it.",
             "Loss if default = LGD × funded_amnt with the overall train LGD; breakeven_pd_median_grade_lgd uses the grade's own LGD.",
             "Realized P&L = total_pymnt + recoveries − collection_recovery_fee − funded_amnt, a post-origination quantity used here only as a population check."]
    result = {"overall": overall, "by_grade": {k: {c: (int(v) if c in ("n", "n_defaults") else round(float(v), 4)) for c, v in row.items()} for k, row in by_grade.iterrows()},
              "by_int_rate_band": {str(k): {c: (int(v) if c == "n" else round(float(v), 4)) for c, v in row.items()} for k, row in by_band.iterrows()}, "notes": notes}
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "economics_train.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    def pct(x: float) -> str:
        return f"{100 * x:.1f}%"

    def usd(x: float) -> str:
        return f"${x:,.0f}"

    g = by_grade
    md = [f"# Economics on train ({len(train):,} loans, 2012-01..2014-12)", "",
          (f"LGD on {econ['n_defaults']:,} charged-off loans: mean {lgd:.3f}, median {econ['lgd_median']:.3f}. "
           f"Median gain if repaid {usd(overall['gain_if_repaid_median'])}, median loss if default {usd(overall['loss_if_default_median'])}, "
           f"median break-even PD {pct(overall['breakeven_pd_median'])}; scheduled interest exceeds LGD × principal for "
           f"{pct(overall['share_interest_exceeds_lgd_x_principal'])} of loans. Realized P&L on train: {usd(overall['realized_pnl_mean'])} per loan, "
           f"{pct(overall['realized_pnl_per_dollar_lent'])} per dollar lent."), "",
          "| Grade | Loans | Default rate | LGD mean | LGD median | n defaults | Gain if repaid (median) | Loss if default (median) | Break-even PD (median) | Break-even PD, grade LGD | Interest > LGD × principal | Realized P&L / loan |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for k, r in g.iterrows():
        md.append(f"| {k} | {int(r['n']):,} | {pct(r['default_rate'])} | {r['lgd_mean']:.3f} | {r['lgd_median']:.3f} | {int(r['n_defaults']):,} | {usd(r['gain_if_repaid_median'])} | "
                  f"{usd(r['loss_if_default_median'])} | {pct(r['breakeven_pd_median'])} | {pct(r['breakeven_pd_median_grade_lgd'])} | "
                  f"{pct(r['share_interest_exceeds_lgd_x_principal'])} | {usd(r['realized_pnl_mean'])} |")
    md += ["", "| Interest rate band | Loans | Default rate | Gain if repaid (median) | Loss if default (median) | Break-even PD (median) | Interest > LGD × principal | Realized P&L / loan |",
           "|---|---|---|---|---|---|---|---|"]
    for k, r in by_band.iterrows():
        md.append(f"| {k} | {int(r['n']):,} | {pct(r['default_rate'])} | {usd(r['gain_if_repaid_median'])} | {usd(r['loss_if_default_median'])} | "
                  f"{pct(r['breakeven_pd_median'])} | {pct(r['share_interest_exceeds_lgd_x_principal'])} | {usd(r['realized_pnl_mean'])} |")
    md += ["", *[f"- {n}" for n in notes], ""]
    (a.out / "economics_train.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

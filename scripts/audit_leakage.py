"""Single-feature AUC audit of every raw column against the target, with the known-at-origination flag.

Runs on the train split by default (never on test). With --extra-columns every bureau column (ORIGINATION_BUREAU, flagged True in M1,
and the UNCERTAIN ones without cohort data) is read from the raw file too, with its missing rate by issue year.

Usage: python scripts/audit_leakage.py [--cohort-dir data/cohort] [--out eval/results] [--extra-columns] [--raw FILE]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from credit_risk.config import COHORT, ID_COL, RAW_FILE, RESULTS, TARGET
from credit_risk.data import load_raw, load_split
from credit_risk.features import ALL_RAW_COLUMNS
from credit_risk.leakage import ORIGINATION_BUREAU, UNCERTAIN, audit


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cohort-dir", type=Path, default=COHORT)
    ap.add_argument("--out", type=Path, default=RESULTS)
    ap.add_argument("--split", default="train", choices=["train", "dev"])
    ap.add_argument("--extra-columns", action="store_true", help="also audit the uncertain bureau columns (reads the raw file again)")
    ap.add_argument("--raw", type=Path, default=RAW_FILE)
    a = ap.parse_args(argv)
    df = load_split(a.split, a.cohort_dir)
    if a.extra_columns:
        bureau = [c for c in ORIGINATION_BUREAU + UNCERTAIN if c not in df.columns]  # the cohort parquet already carries RAW_BUREAU
        extra = load_raw(a.raw, columns=[ID_COL, "issue_d"] + bureau)
        extra = extra[extra[ID_COL].isin(df[ID_COL])]
        df = df.merge(extra.drop(columns=["issue_d"]), on=ID_COL, how="left")
        year = df["issue_month"].dt.year
        miss = df[ORIGINATION_BUREAU + UNCERTAIN].isna().groupby(year).mean().round(3).T
        miss.to_csv(a.out / "uncertain_missing_by_year.csv")
        print("missing rate by issue year for the bureau columns (a column that is empty for early years was added later):")
        print(miss.to_string())
    cols = [c for c in df.columns if c not in (TARGET, "issue_month", "split")]
    table = audit(df, TARGET, cols)
    a.out.mkdir(parents=True, exist_ok=True)
    table.to_csv(a.out / f"leakage_audit_{a.split}.csv", index=False)
    with pd.option_context("display.width", 200, "display.max_rows", 200):
        print(table.head(40).to_string(index=False))
    sus = table[table["suspicious"]]
    feature_hits = sus[sus["column"].isin(ALL_RAW_COLUMNS)]
    print(f"\n{len(sus)} suspicious column(s); {len(feature_hits)} among feature source columns.")
    if len(feature_hits):
        print("STOP: review these before training:", list(feature_hits["column"]))
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

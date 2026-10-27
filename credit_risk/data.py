"""Raw export → matured 36-month cohort → out-of-time splits → parquet.

Only the columns listed in RAW_COLUMNS are read (the export has 151). The cohort rules and split dates live in
config.py; this module applies them and reports what each filter dropped, so the numbers can go into DESIGN.md.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .config import COHORT, COHORT_RULES, ID_COL, SPLIT_RULES, TARGET, TIME_COL, Cohort, Splits
from .features import ALL_RAW_COLUMNS, parse_month
from .leakage import ECONOMICS_COLUMNS

RAW_COLUMNS = sorted(set([ID_COL, "term", "loan_status"] + ALL_RAW_COLUMNS + ECONOMICS_COLUMNS))  # incl. the opt-in bureau set
SPLITS = ("train", "dev", "test")


def load_raw(path: Path, columns: list[str] | None = None, nrows: int | None = None) -> pd.DataFrame:
    """Read the Kaggle CSV (gz) with a column subset. The export carries 33 non-loan lines (32 'Total amount funded in
    policy code N' trailers and one 'Loans that do not meet the credit policy' separator) whose `id` is text and
    `loan_amnt` empty; those rows are dropped. `loan_amnt` is always read for that and dropped again if not asked for."""
    cols = list(columns or RAW_COLUMNS)
    read = set(cols) | {"loan_amnt"}
    df = pd.read_csv(path, usecols=lambda c: c in read, nrows=nrows, low_memory=False)
    df = df[df["loan_amnt"].notna()]
    if "loan_amnt" not in cols:
        df = df.drop(columns="loan_amnt")
    return df.copy()


def build_cohort(df: pd.DataFrame, rules: Cohort = COHORT_RULES) -> tuple[pd.DataFrame, dict]:
    """Apply the cohort filters in order and return (cohort, report of rows dropped by each filter).
    Adds `issue_month` (Timestamp) and the binary target."""
    report: dict[str, int] = {"input_rows": len(df)}
    term = df["term"].astype("string").str.strip()
    keep = term == rules.term
    report["dropped_term"] = int((~keep).sum())
    df = df[keep].copy()

    df["issue_month"] = parse_month(df[TIME_COL])
    lo, hi = pd.Timestamp(rules.issue_from + "-01"), pd.Timestamp(rules.issue_to + "-01")
    keep = df["issue_month"].between(lo, hi)
    report["dropped_issue_window"] = int((~keep).sum())
    df = df[keep].copy()

    status = df["loan_status"].astype("string").str.strip()
    keep = status.isin(rules.terminal_statuses)
    report["dropped_non_terminal"] = int((~keep).sum())
    report["non_terminal_statuses"] = {k: int(v) for k, v in status[~keep].value_counts().items()}
    df = df[keep].copy()
    df["loan_status"] = status[keep]
    df[TARGET] = (df["loan_status"] != rules.good_status).astype(int)
    report["cohort_rows"] = len(df)
    report["default_rate"] = round(float(df[TARGET].mean()), 4) if len(df) else None
    return df, report


def assign_split(issue_month: pd.Series, rules: Splits = SPLIT_RULES) -> pd.Series:
    """train ≤ train_to < dev ≤ dev_to < test. Out-of-time by construction."""
    t_end, d_end = pd.Timestamp(rules.train_to + "-01"), pd.Timestamp(rules.dev_to + "-01")
    out = pd.Series("test", index=issue_month.index, dtype="object")
    out[issue_month <= d_end] = "dev"
    out[issue_month <= t_end] = "train"
    return out


def cohort_summary(df: pd.DataFrame) -> dict:
    """Counts a reviewer wants to see before any model: by issue year × status, default rate by year, by grade, per split."""
    year = df["issue_month"].dt.year
    by_year_status = df.groupby([year, "loan_status"]).size().unstack(fill_value=0)
    out = {
        "rows": len(df),
        "default_rate": round(float(df[TARGET].mean()), 4),
        "by_year_status": {int(y): {str(k): int(v) for k, v in row.items()} for y, row in by_year_status.iterrows()},
        "default_rate_by_year": {int(k): round(float(v), 4) for k, v in df.groupby(year)[TARGET].mean().items()},
        "default_rate_by_grade": {str(k): round(float(v), 4) for k, v in df.groupby(df["grade"].astype("string"))[TARGET].mean().items()},
    }
    if "split" in df.columns:
        out["splits"] = {s: {"rows": int((df["split"] == s).sum()), "default_rate": round(float(df.loc[df["split"] == s, TARGET].mean()), 4),
                             "issue_from": str(df.loc[df["split"] == s, "issue_month"].min().date()), "issue_to": str(df.loc[df["split"] == s, "issue_month"].max().date())}
                         for s in SPLITS if (df["split"] == s).any()}
    return out


def save_cohort(df: pd.DataFrame, out_dir: Path = COHORT) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    for s in SPLITS:
        part = df[df["split"] == s].drop(columns=["split"])
        part.to_parquet(out_dir / f"{s}.parquet", index=False)
    summary = cohort_summary(df)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def load_split(name: str, cohort_dir: Path = COHORT) -> pd.DataFrame:
    if name not in SPLITS:
        raise ValueError(f"split must be one of {SPLITS}")
    p = cohort_dir / f"{name}.parquet"
    if not p.exists():
        raise FileNotFoundError(f"{p} not found — run scripts/build_cohort.py first")
    return pd.read_parquet(p)

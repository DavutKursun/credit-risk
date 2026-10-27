"""Raw CSV → matured 36-month cohort → train/dev/test parquet + summary.json + build_report.json.

Usage: python scripts/build_cohort.py [--raw data/raw/accepted_2007_to_2018Q4.csv.gz] [--out data/cohort] [--nrows N]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from credit_risk.config import COHORT, RAW_FILE
from credit_risk.data import assign_split, build_cohort, load_raw, save_cohort


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", type=Path, default=RAW_FILE)
    ap.add_argument("--out", type=Path, default=COHORT)
    ap.add_argument("--nrows", type=int, default=None, help="read only the first N rows (smoke runs)")
    a = ap.parse_args(argv)
    if not a.raw.exists():
        print(f"raw file not found: {a.raw} — run scripts/download.py")
        return 2
    print(f"reading {a.raw} …", flush=True)
    raw = load_raw(a.raw, nrows=a.nrows)
    cohort, report = build_cohort(raw)
    cohort["split"] = assign_split(cohort["issue_month"])
    summary = save_cohort(cohort, a.out)
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "build_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("filters:", json.dumps(report, indent=2))
    print("by issue year × status:")
    for y, row in summary["by_year_status"].items():
        print(f"  {y}: {row}")
    print("default rate by year:", summary["default_rate_by_year"])
    print("default rate by grade:", summary["default_rate_by_grade"])
    print("splits:", json.dumps(summary["splits"], indent=2))
    print(f"written to {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Check the raw Lending Club file is in place; explain how to get it. Never asks for credentials.

Usage: python scripts/download.py
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from credit_risk.config import KAGGLE_DATASET, RAW_FILE

HOW = f"""
The raw file is not here: {RAW_FILE}

Two ways to get it (your Kaggle login, never shared in a chat):
  1) Browser: https://www.kaggle.com/datasets/{KAGGLE_DATASET} → Data → download
     `accepted_2007_to_2018Q4.csv.gz` → move it to data/raw/
  2) Kaggle CLI (needs ~/.kaggle/kaggle.json from Kaggle → Settings → API → Create New Token):
     pip install kaggle
     kaggle datasets download -d {KAGGLE_DATASET} -f accepted_2007_to_2018Q4.csv.gz -p data/raw/
     (if it arrives as a .zip, unzip it in data/raw/)
Then: python scripts/build_cohort.py
"""


def main() -> int:
    if not RAW_FILE.exists():
        print(HOW)
        return 2
    size_mb = RAW_FILE.stat().st_size / 1e6
    h = hashlib.sha256()
    with RAW_FILE.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    print(f"found {RAW_FILE.name}: {size_mb:.1f} MB, sha256 {h.hexdigest()[:16]}…")
    print("next: python scripts/build_cohort.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

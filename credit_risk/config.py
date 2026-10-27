"""Every knob lives here: paths, the cohort window, the time splits, seeds, model settings.

Nothing in this project reads an environment variable before M6; there is no .env.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
COHORT = DATA / "cohort"
MODELS = ROOT / "models"
RESULTS = ROOT / "eval" / "results"
DOCS = ROOT / "docs"

RAW_FILE = RAW / "accepted_2007_to_2018Q4.csv.gz"
KAGGLE_DATASET = "wordsforthewise/lending-club"

SEED = 7


@dataclass(frozen=True)
class Cohort:
    """36-month loans issued 2012-01..2015-12 are fully matured by the 2018Q4 snapshot (right-censoring is the
    reason later cohorts and 60-month loans are excluded; see DESIGN.md)."""

    term: str = "36 months"
    issue_from: str = "2012-01"
    issue_to: str = "2015-12"
    terminal_statuses: tuple[str, ...] = ("Fully Paid", "Charged Off", "Default")
    good_status: str = "Fully Paid"


@dataclass(frozen=True)
class Splits:
    """Out-of-time: everything in dev and test was issued after everything in train."""

    train_to: str = "2014-12"  # inclusive
    dev_to: str = "2015-06"  # inclusive; dev = (train_to, dev_to]
    # test = (dev_to, Cohort.issue_to]


COHORT_RULES = Cohort()
SPLIT_RULES = Splits()

TARGET = "default"
TIME_COL = "issue_d"
ID_COL = "id"

# Scorecard scaling: 600 points at odds 1:19 (PD 5%), 20 points to double the odds.
SCORECARD_SCALE = {"target_score": 600, "target_odds": 19, "pdo": 20}

# Three-way decision: PD more than REVIEW_BAND below the threshold → approve; within ±REVIEW_BAND of it → review; else decline.
REVIEW_BAND = 0.02

PSI_WARN, PSI_ACT = 0.10, 0.25

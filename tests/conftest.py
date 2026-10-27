from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from credit_risk.data import assign_split, build_cohort
from credit_risk.synthetic import make_raw


@pytest.fixture(scope="session")
def raw():
    return make_raw(n=4000, seed=7)


@pytest.fixture(scope="session")
def cohort(raw):
    df, report = build_cohort(raw)
    df["split"] = assign_split(df["issue_month"])
    return df, report

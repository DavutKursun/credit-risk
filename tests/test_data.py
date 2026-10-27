from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from credit_risk.config import COHORT_RULES, SPLIT_RULES, TARGET
from credit_risk.data import RAW_COLUMNS, assign_split, cohort_summary, load_raw, load_split, save_cohort
from credit_risk.features import (
    RAW_FEATURE_COLUMNS,
    application_frame,
    check_raw_columns_are_usable,
    emp_length_years,
    feature_list,
    make_features,
    parse_month,
    to_percent,
)
from credit_risk.leakage import ECONOMICS_COLUMNS, SUSPICIOUS_AUC, assert_no_leaks, audit, flag, usable_columns
from credit_risk.schema import SAMPLE_APPLICATIONS, Application
from credit_risk.synthetic import write_raw_csv


# --- cohort -----------------------------------------------------------------------
def test_cohort_filters_term_window_and_status(cohort, raw):
    df, report = cohort
    assert report["input_rows"] == len(raw)
    assert report["dropped_term"] > 0 and report["dropped_issue_window"] > 0 and report["dropped_non_terminal"] > 0
    assert set(df["loan_status"].unique()) <= set(COHORT_RULES.terminal_statuses)
    assert df["issue_month"].min() >= pd.Timestamp("2012-01-01") and df["issue_month"].max() <= pd.Timestamp("2015-12-01")
    assert df[TARGET].isin([0, 1]).all() and 0.05 < df[TARGET].mean() < 0.5
    assert report["cohort_rows"] == len(df) == report["input_rows"] - report["dropped_term"] - report["dropped_issue_window"] - report["dropped_non_terminal"]


def test_splits_are_out_of_time(cohort):
    df, _ = cohort
    tr, dv, te = (df[df["split"] == s]["issue_month"] for s in ("train", "dev", "test"))
    assert len(tr) and len(dv) and len(te)
    assert tr.max() < dv.min() <= dv.max() < te.min()
    assert tr.max() <= pd.Timestamp(SPLIT_RULES.train_to + "-01") and dv.max() <= pd.Timestamp(SPLIT_RULES.dev_to + "-01")
    s = cohort_summary(df)
    assert set(s["splits"]) == {"train", "dev", "test"} and s["rows"] == len(df)


def test_assign_split_boundaries():
    m = pd.Series(pd.to_datetime(["2014-12-01", "2015-01-01", "2015-06-01", "2015-07-01"]))
    assert list(assign_split(m)) == ["train", "dev", "dev", "test"]


def test_raw_csv_roundtrip_drops_kaggle_summary_lines(tmp_path, raw):
    p = write_raw_csv(raw.head(300), tmp_path / "accepted.csv.gz")
    df = load_raw(p)
    assert len(df) == 300 and set(RAW_COLUMNS) <= set(df.columns) | {"last_fico_range_low", "total_rec_prncp"}
    assert "last_fico_range_low" not in df.columns  # not in RAW_COLUMNS, so never read


def test_load_raw_subset_without_loan_amnt(tmp_path, raw):
    p = write_raw_csv(raw.head(50), tmp_path / "accepted.csv.gz")
    df = load_raw(p, columns=["id", "issue_d"])  # the audit's --extra-columns path reads a subset without loan_amnt
    assert set(df.columns) == {"id", "issue_d"} and len(df) == 50  # summary lines dropped, loan_amnt not kept


def test_save_and_load_cohort(tmp_path, cohort):
    df, _ = cohort
    summary = save_cohort(df, tmp_path)
    assert (tmp_path / "summary.json").exists() and summary["rows"] == len(df)
    tr = load_split("train", tmp_path)
    assert len(tr) == summary["splits"]["train"]["rows"] and "split" not in tr.columns
    with pytest.raises(FileNotFoundError):
        load_split("dev", tmp_path / "nope")


# --- leakage --------------------------------------------------------------------
def test_every_feature_source_is_flagged_known_at_origination():
    assert check_raw_columns_are_usable() == []
    assert flag("total_pymnt") is False and flag("last_fico_range_low") is False and flag("tot_cur_bal") is None and flag("made_up") is None
    assert usable_columns(["loan_amnt", "recoveries", "tot_cur_bal"]) == ["loan_amnt"]
    assert "loan_status" in ECONOMICS_COLUMNS


def test_audit_flags_leaky_columns_and_not_features(cohort, raw):
    df, _ = cohort  # built straight from the synthetic export, so the two leaky columns are still present
    assert {"last_fico_range_low", "total_rec_prncp"} <= set(df.columns)
    table = audit(df, TARGET, RAW_FEATURE_COLUMNS + ["last_fico_range_low", "total_rec_prncp", "total_pymnt"])
    top = table.set_index("column")
    assert top.loc["last_fico_range_low", "auc_value"] > SUSPICIOUS_AUC and top.loc["total_rec_prncp", "auc_value"] > SUSPICIOUS_AUC
    # flagged False → high AUC is expected, not suspicious; a feature column must never be suspicious on this data
    assert not top.loc["total_pymnt", "suspicious"] and not top.loc["last_fico_range_low", "suspicious"]
    assert not top.loc[RAW_FEATURE_COLUMNS, "suspicious"].any()
    assert_no_leaks(table, RAW_FEATURE_COLUMNS)
    with pytest.raises(ValueError):
        assert_no_leaks(table, RAW_FEATURE_COLUMNS + ["total_pymnt"])


def test_audit_catches_an_unflagged_leak(cohort):
    df, _ = cohort
    frame = df.copy()
    frame["mystery_score"] = frame[TARGET] * 10 + np.random.default_rng(0).normal(0, 1, len(frame))  # unknown column, leaks
    table = audit(frame, TARGET, ["mystery_score", "loan_amnt"])
    assert bool(table.set_index("column").loc["mystery_score", "suspicious"])
    with pytest.raises(ValueError):
        assert_no_leaks(table, ["mystery_score"])


# --- features -----------------------------------------------------------------
def test_parsers():
    assert to_percent(pd.Series(["13.56%", " 7.9% ", None])).round(2).tolist()[:2] == [13.56, 7.9]
    assert to_percent(pd.Series([1.5, 2.0])).tolist() == [1.5, 2.0]
    assert parse_month(pd.Series(["Dec-2015", "bad"])).tolist()[0] == pd.Timestamp("2015-12-01")
    assert parse_month(pd.Series(["Dec-2015", "bad"])).isna().tolist() == [False, True]
    e = emp_length_years(pd.Series(["< 1 year", "3 years", "10+ years", "n/a", None]))
    assert e.tolist()[:3] == [0.0, 3.0, 10.0] and e.isna().tolist()[3:] == [True, True]


def test_make_features_shapes_and_categories(cohort):
    df, _ = cohort
    X = make_features(df)
    num, cat = feature_list(True)
    assert list(X.columns) == num + cat and len(X) == len(df)
    assert X["fico"].between(300, 850).all() and (X["credit_age_years"].dropna() >= 0).all()
    assert isinstance(X["grade"].dtype, pd.CategoricalDtype) and list(X["grade"].cat.categories) == list("ABCDEFG")
    assert X["int_rate"].dtype == float and X["revol_util"].isna().sum() > 0  # NaN preserved, no fill here
    X2 = make_features(df, use_lc_grade=False)
    assert not {"grade", "sub_grade", "int_rate", "installment", "installment_to_income"} & set(X2.columns)


def test_single_application_matches_batch(cohort):
    df, _ = cohort
    X_batch = make_features(df.head(5))
    for i in range(5):
        row = df.iloc[i]
        app = {c: (None if pd.isna(row[c]) else row[c]) for c in RAW_FEATURE_COLUMNS}
        X_one = make_features(application_frame(app))
        for c in X_batch.columns:
            a, b = X_batch.iloc[i][c], X_one.iloc[0][c]
            assert (pd.isna(a) and pd.isna(b)) or a == b, (c, a, b)


def test_unknown_category_level_becomes_missing():
    app = dict(SAMPLE_APPLICATIONS["borderline"])
    frame = application_frame(app)
    frame["purpose"] = "yacht"
    X = make_features(frame)
    assert pd.isna(X["purpose"].iloc[0])


# --- schema -------------------------------------------------------------------
def test_application_schema_validates_samples_and_rejects_bad_input():
    for app in SAMPLE_APPLICATIONS.values():
        a = Application(**app)
        X = make_features(application_frame(a.model_dump()))
        assert X.shape == (1, len(feature_list(True)[0]) + len(feature_list(True)[1]))
    with pytest.raises(ValidationError):
        Application(**{**SAMPLE_APPLICATIONS["borderline"], "fico_range_low": 200})
    with pytest.raises(ValidationError):
        Application(**{**SAMPLE_APPLICATIONS["borderline"], "total_pymnt": 1000})  # post-origination field: rejected
    with pytest.raises(ValidationError):
        Application(**{**SAMPLE_APPLICATIONS["borderline"], "earliest_cr_line": "2001-08"})

"""Deterministic feature transforms shared by training (a DataFrame) and scoring (one Application).

Every string quirk of the Lending Club export is handled here and nowhere else: '13.5%' rates, '10+ years',
'Dec-2015' months, a leading space in ' 36 months'. Categorical levels are fixed lists so that LightGBM's native
categorical codes are identical in training and in the API.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .leakage import usable_columns

US_STATES = [
    "AK", "AL", "AR", "AZ", "CA", "CO", "CT", "DC", "DE", "FL", "GA", "HI", "IA", "ID", "IL", "IN", "KS", "KY", "LA", "MA", "MD", "ME", "MI",
    "MN", "MO", "MS", "MT", "NC", "ND", "NE", "NH", "NJ", "NM", "NV", "NY", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VA",
    "VT", "WA", "WI", "WV", "WY",
]
CATEGORY_LEVELS: dict[str, list[str]] = {
    "grade": list("ABCDEFG"),
    "sub_grade": [f"{g}{i}" for g in "ABCDEFG" for i in range(1, 6)],
    "home_ownership": ["RENT", "OWN", "MORTGAGE", "ANY", "OTHER", "NONE"],
    "verification_status": ["Not Verified", "Source Verified", "Verified"],
    "purpose": ["debt_consolidation", "credit_card", "home_improvement", "other", "major_purchase", "medical", "small_business", "car",
                "moving", "vacation", "house", "wedding", "renewable_energy", "educational"],
    "addr_state": US_STATES,
    "initial_list_status": ["w", "f"],
    "application_type": ["Individual", "Joint App"],
}

# Raw columns each feature set needs (all flagged True in leakage.py).
RAW_NUMERIC = ["loan_amnt", "int_rate", "installment", "annual_inc", "dti", "fico_range_low", "fico_range_high", "delinq_2yrs", "inq_last_6mths",
               "open_acc", "pub_rec", "revol_bal", "revol_util", "total_acc", "mort_acc", "pub_rec_bankruptcies"]
RAW_TEXTUAL = ["earliest_cr_line", "issue_d", "emp_length"]
RAW_CATEGORICAL = list(CATEGORY_LEVELS)
RAW_FEATURE_COLUMNS = RAW_NUMERIC + RAW_TEXTUAL + RAW_CATEGORICAL

NUMERIC_FEATURES = ["loan_amnt", "int_rate", "installment", "annual_inc", "dti", "fico", "delinq_2yrs", "inq_last_6mths", "open_acc", "pub_rec",
                    "revol_bal", "revol_util", "total_acc", "mort_acc", "pub_rec_bankruptcies", "credit_age_years", "emp_years",
                    "loan_to_income", "installment_to_income"]
CATEGORICAL_FEATURES = RAW_CATEGORICAL
# Outputs of Lending Club's own risk model at origination (int_rate is set from sub_grade; installment follows from it).
LC_GRADE_FEATURES = ["grade", "sub_grade", "int_rate", "installment", "installment_to_income"]

# LightGBM monotone constraints: +1 = PD rises with the feature, -1 = falls, 0 = free.
MONOTONE = {"int_rate": 1, "fico": -1, "dti": 1, "revol_util": 1, "annual_inc": -1, "inq_last_6mths": 1, "delinq_2yrs": 1, "credit_age_years": -1,
            "loan_to_income": 1, "installment_to_income": 1, "pub_rec": 1, "pub_rec_bankruptcies": 1}

FEATURE_LABELS = {
    "loan_amnt": "Loan amount", "int_rate": "Interest rate", "installment": "Monthly installment", "annual_inc": "Annual income",
    "dti": "Debt-to-income ratio", "fico": "FICO score", "delinq_2yrs": "Delinquencies in the last 2 years", "inq_last_6mths": "Credit inquiries in the last 6 months",
    "open_acc": "Open credit lines", "pub_rec": "Public records", "revol_bal": "Revolving balance", "revol_util": "Revolving utilization",
    "total_acc": "Total credit lines", "mort_acc": "Mortgage accounts", "pub_rec_bankruptcies": "Bankruptcies on record", "credit_age_years": "Credit history length",
    "emp_years": "Employment length", "loan_to_income": "Loan amount relative to income", "installment_to_income": "Installment relative to income",
    "grade": "Lending Club grade", "sub_grade": "Lending Club sub-grade", "home_ownership": "Home ownership", "verification_status": "Income verification",
    "purpose": "Loan purpose", "addr_state": "State", "initial_list_status": "Listing status", "application_type": "Application type",
}
FEATURE_UNITS = {"int_rate": "%", "dti": "%", "revol_util": "%", "annual_inc": "$", "loan_amnt": "$", "installment": "$", "revol_bal": "$",
                 "credit_age_years": "years", "emp_years": "years"}


def feature_list(use_lc_grade: bool = True) -> tuple[list[str], list[str]]:
    """(numeric, categorical) feature names for a model variant."""
    num = [f for f in NUMERIC_FEATURES if use_lc_grade or f not in LC_GRADE_FEATURES]
    cat = [f for f in CATEGORICAL_FEATURES if use_lc_grade or f not in LC_GRADE_FEATURES]
    return num, cat


def to_percent(s: pd.Series) -> pd.Series:
    """'13.56%' → 13.56; numbers pass through; blanks → NaN."""
    if pd.api.types.is_numeric_dtype(s):
        return s.astype(float)
    return pd.to_numeric(s.astype("string").str.strip().str.rstrip("%"), errors="coerce").astype(float)


def parse_month(s: pd.Series) -> pd.Series:
    """'Dec-2015' → Timestamp(2015-12-01). Unparseable → NaT."""
    if pd.api.types.is_datetime64_any_dtype(s):
        return s
    return pd.to_datetime(s.astype("string").str.strip(), format="%b-%Y", errors="coerce")


def emp_length_years(s: pd.Series) -> pd.Series:
    """'< 1 year' → 0, '3 years' → 3, '10+ years' → 10, 'n/a'/blank → NaN."""
    txt = s.astype("string").str.strip().str.lower()
    out = pd.Series(np.nan, index=s.index, dtype=float)
    out[txt == "< 1 year"] = 0.0
    digits = txt.str.extract(r"^(\d+)")[0]
    num = pd.to_numeric(digits, errors="coerce")
    out = out.where(txt == "< 1 year", num.astype(float))
    return out


def to_category(s: pd.Series, levels: list[str]) -> pd.Series:
    """Fixed-level categorical; unknown values become NaN (never a new code)."""
    vals = s.astype("string").str.strip()
    return pd.Categorical(vals.astype(object).where(vals.isin(levels), None), categories=levels)


def make_features(df: pd.DataFrame, use_lc_grade: bool = True) -> pd.DataFrame:
    """Raw rows (DataFrame with RAW_FEATURE_COLUMNS, extra columns ignored) → model matrix.
    Works on one Application row exactly as on the training frame."""
    missing = [c for c in RAW_FEATURE_COLUMNS if c not in df.columns]
    if missing:
        raise KeyError(f"raw columns missing: {missing}")
    out = pd.DataFrame(index=df.index)
    for c in RAW_NUMERIC:
        out[c] = to_percent(df[c]) if c in ("int_rate", "revol_util") else pd.to_numeric(df[c], errors="coerce").astype(float)
    out["fico"] = (out["fico_range_low"] + out["fico_range_high"]) / 2
    issued, opened = parse_month(df["issue_d"]), parse_month(df["earliest_cr_line"])
    out["credit_age_years"] = ((issued - opened).dt.days / 365.25).astype(float)
    out.loc[out["credit_age_years"] < 0, "credit_age_years"] = np.nan
    out["emp_years"] = emp_length_years(df["emp_length"])
    income = out["annual_inc"].clip(lower=1.0)
    out["loan_to_income"] = out["loan_amnt"] / income
    out["installment_to_income"] = out["installment"] * 12 / income
    for c, levels in CATEGORY_LEVELS.items():
        out[c] = to_category(df[c], levels)
    num, cat = feature_list(use_lc_grade)
    return out[num + cat]


def application_frame(app: dict) -> pd.DataFrame:
    """One Application (dict from the Pydantic model) → a one-row raw frame with every raw column present."""
    row = {c: app.get(c) for c in RAW_FEATURE_COLUMNS}
    return pd.DataFrame([row])


def check_raw_columns_are_usable() -> list[str]:
    """Guard for tests: every raw column a feature reads must be flagged known-at-origination."""
    return [c for c in RAW_FEATURE_COLUMNS if c not in usable_columns(RAW_FEATURE_COLUMNS)]

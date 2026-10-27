"""End to end on a synthetic export: build_cohort → audit → train → evaluate (dev; test refused) → reliability plots, model tables,
sanity checks → policy (dev, and test with the dev thresholds) → reasons → fairness → drift.
The same chain Claude Code runs on the real data, so the first real run is not the first run."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import audit_leakage
import build_cohort
import drift_report
import evaluate
import fairness_report
import model_tables
import plot_reliability
import policy_eval
import reasons_report
import sanity_checks
import train

from credit_risk.synthetic import make_raw, write_raw_csv


@pytest.fixture(scope="module")
def workspace(tmp_path_factory):
    base = tmp_path_factory.mktemp("ws")
    raw = write_raw_csv(make_raw(n=5000, seed=11), base / "raw" / "accepted.csv.gz")
    dirs = {"raw": raw, "cohort": base / "cohort", "models": base / "models", "out": base / "results"}
    for d in ("cohort", "models", "out"):
        dirs[d].mkdir(parents=True, exist_ok=True)
    return dirs


def test_build_cohort_script(workspace):
    assert build_cohort.main(["--raw", str(workspace["raw"]), "--out", str(workspace["cohort"])]) == 0
    summary = json.loads((workspace["cohort"] / "summary.json").read_text())
    assert set(summary["splits"]) == {"train", "dev", "test"} and (workspace["cohort"] / "build_report.json").exists()


def test_audit_script(workspace):
    assert audit_leakage.main(["--cohort-dir", str(workspace["cohort"]), "--out", str(workspace["out"])]) == 0
    assert (workspace["out"] / "leakage_audit_train.csv").exists()


def test_train_script(workspace):
    rc = train.main(["--model", "both", "--cohort-dir", str(workspace["cohort"]), "--models-dir", str(workspace["models"]), "--out", str(workspace["out"])])
    assert rc == 0
    res = json.loads((workspace["out"] / "train_dev.json").read_text())
    assert {"lgbm", "scorecard"} <= set(res) and res["lgbm"]["dev_ranking"]["auc"] > 0.6
    assert res["lgbm"]["dev_late_after"]["ece"] <= res["lgbm"]["dev_late_before"]["ece"] + 0.02  # out-of-sample calibration check
    assert (workspace["models"] / "lgbm.joblib").exists() and (workspace["models"] / "scorecard.joblib").exists()


def test_evaluate_refuses_test_without_final(workspace):
    assert evaluate.main(["--split", "test", "--models-dir", str(workspace["models"]), "--cohort-dir", str(workspace["cohort"]), "--out", str(workspace["out"])]) == 3
    assert evaluate.main(["--split", "dev", "--models-dir", str(workspace["models"]), "--cohort-dir", str(workspace["cohort"]), "--out", str(workspace["out"])]) == 0
    s = json.loads((workspace["out"] / "dev-summary.json").read_text())
    assert {r["model"] for r in s["metrics"]} == {"lgbm", "scorecard", "grade_only"}


def test_reliability_plots_model_tables_and_sanity_scripts(workspace):
    common = ["--models-dir", str(workspace["models"]), "--cohort-dir", str(workspace["cohort"]), "--out", str(workspace["out"])]
    assert plot_reliability.main(common) == 0
    assert (workspace["out"] / "reliability_dev_lgbm.png").exists() and (workspace["out"] / "reliability_dev_lgbm_before.csv").exists()
    assert model_tables.main(["--models-dir", str(workspace["models"]), "--out", str(workspace["out"])]) == 0
    assert (workspace["out"] / "scorecard_table.md").exists() and (workspace["out"] / "lgbm_importance.csv").exists()
    assert sanity_checks.main(common) == 0
    s = json.loads((workspace["out"] / "sanity_dev.json").read_text())
    assert {"lgbm", "scorecard"} <= set(s["samples"]) and all(p["ok"] for p in s["monotonicity"]["lgbm"].values())


def test_policy_fairness_drift_scripts(workspace):
    common = ["--models-dir", str(workspace["models"]), "--cohort-dir", str(workspace["cohort"]), "--out", str(workspace["out"])]
    assert policy_eval.main(["--split", "test", *common]) == 3  # no --final / --thresholds-from
    assert policy_eval.main(["--split", "dev", "--min-approval-rate", "0.3", *common]) == 0
    pol = json.loads((workspace["out"] / "policy_dev.json").read_text())
    assert "lgbm" in pol["thresholds"] and any(p["policy"] == "approve_all" for p in pol["policies"])
    names = {p["policy"] for p in pol["policies"]}
    assert {"lgbm@ev", "lgbm@80%", "lgbm@90%", "sub_grade_cut@85%", "approve_grades_A-C"} <= names
    fixed = next(p for p in pol["policies"] if p["policy"] == "lgbm@85%")
    assert abs(fixed["approve"] - 0.85) < 0.01 and "defaults_avoided_per_1000_vs_subgrade_cut" in fixed  # exact fixed approval rate
    assert (workspace["out"] / "profit_curve_dev_lgbm.png").exists() and (workspace["out"] / "policy_dev.csv").exists()
    assert policy_eval.main(["--split", "test", "--final", "--thresholds-from", str(workspace["out"] / "policy_dev.json"), *common]) == 0  # the M4 path
    assert reasons_report.main(["--variants", "lgbm,scorecard", "--n", "200", *common]) == 0
    rs = json.loads((workspace["out"] / "reasons_dev.json").read_text())
    assert rs["checks"]["reason_texts_clean"] and rs["checks"]["all_reasons_have_5_entries"] and len(rs["examples"]) == 7
    assert reasons_report.main(["--variants", "lgbm,scorecard", "--split", "test", *common]) == 3  # test refused without --final
    assert fairness_report.main(["--model", "lgbm", "--split", "dev", "--min-n", "20", *common]) == 0
    fr = json.loads((workspace["out"] / "fairness_dev_lgbm.json").read_text())
    assert "default_rate" in fr["groups"]["home_ownership"][0] and "approval_rate" in fr["gaps"]["home_ownership"]
    assert drift_report.main(common) == 0
    assert (workspace["out"] / "psi_by_quarter.csv").exists() and (workspace["out"] / "psi_missing_by_quarter.csv").exists()

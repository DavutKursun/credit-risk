"""The API through FastAPI's TestClient (no network): schema rejection, five reasons, decisions consistent with the policy, batch limit,
health, monitoring, the sample order, and the Gradio mount."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from credit_risk.config import REVIEW_BAND
from credit_risk.features import LC_GRADE_FEATURES
from credit_risk.schema import SAMPLE_APPLICATIONS

pytest.importorskip("lightgbm")
import app as app_module  # loads the deployed bundles from models/

client = TestClient(app_module.app)
BORDERLINE = SAMPLE_APPLICATIONS["borderline"]


def expected_decision(pd_: float, t: float, band: float) -> str:
    return "approve" if pd_ < t - band else "review" if pd_ < t + band else "decline"


@pytest.mark.parametrize("model", ["lgbm", "scorecard"])
def test_score_valid_application(model):
    r = client.post(f"/score?model={model}", json=BORDERLINE)
    assert r.status_code == 200, r.text
    body = r.json()
    assert 0 <= body["pd"] <= 1 and len(body["reasons"]) == 5 and body["policy"] == app_module.scorer.policy
    assert body["decision"] == expected_decision(body["pd"], body["threshold"], body["review_band"]) and body["review_band"] == REVIEW_BAND
    assert body["model"] == app_module.DEPLOYED[model] and isinstance(body["version"], str) and body["latency_ms"] > 0
    assert (body["score_points"] is not None) == (model == "scorecard")
    assert not any(x["feature"] in LC_GRADE_FEATURES for x in body["reasons"])
    for x in body["reasons"]:
        assert x["direction"] in ("raises", "lowers") and x["text"] and "nan" not in x["text"].lower()
    assert (body["adverse_action"] is not None) == (body["decision"] == "decline")


def test_invalid_range_and_unknown_field_are_rejected():
    assert client.post("/score", json={**BORDERLINE, "fico_range_low": 200}).status_code == 422
    assert client.post("/score", json={**BORDERLINE, "total_pymnt": 1000}).status_code == 422  # a post-origination field
    assert client.post("/score", json={**BORDERLINE, "made_up": 1}).status_code == 422
    assert client.post("/score?model=xgboost", json=BORDERLINE).status_code == 422


def test_batch_limit_and_results():
    r = client.post("/score/batch?model=scorecard", json={"applications": [SAMPLE_APPLICATIONS[k] for k in ("clear_approve", "borderline", "clear_decline")]})
    assert r.status_code == 200 and r.json()["n"] == 3 and all(len(x["reasons"]) == 5 for x in r.json()["results"])
    pds = [x["pd"] for x in r.json()["results"]]
    assert pds[0] < pds[1] < pds[2]
    assert client.post("/score/batch", json={"applications": [BORDERLINE] * 1001}).status_code == 422
    assert client.post("/score/batch", json={"applications": []}).status_code == 422


def test_health_and_monitoring():
    h = client.get("/health").json()
    assert h["status"] == "ok" and set(h["models"]) == {"lgbm", "scorecard"} and h["policy"] in ("rate85", "ev") and h["version"]
    assert set(h["policies"]) == {"rate85", "ev"} and 0 < h["policies"]["rate85"]["lgbm"] < h["policies"]["ev"]["lgbm"]
    m = client.get("/monitoring").json()
    assert m["rule"] == {"watch": 0.10, "act": 0.25} and len(m["quarters"]) == 4 and len(m["features"]) > 30
    assert {"feature", "psi", "worst", "status", "driven_by"} <= set(m["features"][0])


@pytest.mark.parametrize("model", ["lgbm", "scorecard"])
def test_samples_keep_their_order(model):
    pds = [client.post(f"/score?model={model}", json=SAMPLE_APPLICATIONS[k]).json()["pd"] for k in ("clear_approve", "borderline", "clear_decline")]
    assert pds[0] < pds[1] < pds[2], pds


def test_scorecard_fast_path_matches_optbinning():
    """One WoE transform per request must give exactly the PD, points and reasons of optbinning's own predict_proba / score / contributions."""
    import numpy as np

    from credit_risk.explain import contributions, reason_codes
    from credit_risk.features import make_features
    from credit_risk.schema import Application
    from credit_risk.serving import applications_frame

    scorer = app_module.scorer
    assert scorer.card_fast is not None  # verified at load on the three samples
    b = scorer.bundles["scorecard"]
    apps = [Application(**v) for v in SAMPLE_APPLICATIONS.values()] + [Application(**{**BORDERLINE, "annual_inc": 24_000, "dti": 34.0, "emp_length": "n/a", "revol_util": None})]
    X = make_features(applications_frame(apps), b.use_lc_grade, b.bureau)
    raw, points, contrib = scorer.card_fast.run(b, X)
    assert np.allclose(raw, b.predict_raw(X), atol=1e-9) and np.allclose(points, b.score_points(X), atol=0.5)
    assert np.allclose(contrib.to_numpy(), contributions(b, X)[b.features].to_numpy(), atol=1e-9)
    fast = reason_codes(b, X, k=5, contrib=contrib)
    slow = reason_codes(b, X, k=5)
    assert [[r.feature for r in row] for row in fast] == [[r.feature for r in row] for row in slow]
    assert client.get("/health").json()["scorecard_fast_path"] is True


def test_gradio_ui_is_mounted():
    r = client.get("/ui/")
    assert r.status_code == 200 and "gradio" in r.text.lower()
    cfg = client.get("/ui/config")
    assert cfg.status_code == 200 and "components" in cfg.json()

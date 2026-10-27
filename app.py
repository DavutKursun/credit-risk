"""credit-risk API + review UI: FastAPI on port 7860 with Gradio mounted at /ui.

POST /score?model=lgbm|scorecard   Application → {pd, decision, reasons[5], adverse_action, score_points, policy, threshold, model, version, latency_ms}
POST /score/batch                  {"applications": [...]} (≤ 1,000) → the same per row
GET  /health                       models loaded, policy in force, thresholds, version
GET  /monitoring                   PSI by quarter from the committed drift report
UI   /ui                           Application · Policy · Monitoring · About

Run: uvicorn app:app --port 7860        Policy: POLICY=rate85 (default) | ev
Requests are logged without any applicant field. Nothing is stored.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Literal

os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")  # no telemetry from the UI

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse

from credit_risk.schema import Application, BatchRequest, BatchResponse, ScoreResponse
from credit_risk.serving import DEPLOYED, Scorer

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("credit_risk.app")

scorer = Scorer.load()
app = FastAPI(title="credit-risk", version=scorer.version, description="Loan default scoring: calibrated PD, approve / review / decline by policy, five reasons.")
ModelName = Literal["lgbm", "scorecard"]


@app.middleware("http")
async def access_log(request: Request, call_next):
    t0 = time.perf_counter()
    response = await call_next(request)
    if not request.url.path.startswith("/ui"):
        log.info("%s %s → %s in %.1f ms", request.method, request.url.path, response.status_code, (time.perf_counter() - t0) * 1000)
    return response


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/ui")


@app.get("/health")
def health():
    return scorer.health()


@app.get("/monitoring")
def monitoring():
    return scorer.monitoring()


@app.post("/score", response_model=ScoreResponse)
def score(application: Application, model: ModelName = "lgbm"):
    r = scorer.score(model, application)
    log.info("score model=%s policy=%s decision=%s latency_ms=%.1f", model, scorer.policy, r.decision, r.latency_ms)
    return r


@app.post("/score/batch", response_model=BatchResponse)
def score_batch(batch: BatchRequest, model: ModelName = "lgbm"):
    t0 = time.perf_counter()
    results = scorer.score_many(model, batch.applications)
    ms = (time.perf_counter() - t0) * 1000
    log.info("score/batch model=%s policy=%s n=%d latency_ms=%.1f", model, scorer.policy, len(results), ms)
    return BatchResponse(n=len(results), results=results, model=DEPLOYED[model], policy=scorer.policy, version=scorer.version, latency_ms=round(ms, 1))


try:
    import gradio as gr

    from credit_risk.ui import build

    app = gr.mount_gradio_app(app, build(scorer), path="/ui")
except ImportError:  # the API works without the UI
    log.warning("gradio not installed; /ui is disabled")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=7860)

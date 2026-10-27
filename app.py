"""FastAPI + Gradio serving — built in Milestone 5. Until then this file only documents the planned routes.

POST /score        Application → {pd, decision, reasons[5], score_points, model, version, latency_ms}
POST /score/batch  up to 1,000 applications
GET  /health       model versions, thresholds, uptime
GET  /monitoring   PSI by quarter from eval/results/psi_by_quarter.csv
UI   /             Gradio: Application · Policy · Monitoring tabs
"""

from __future__ import annotations

if __name__ == "__main__":
    raise SystemExit("app.py is built in Milestone 5; run the scripts in scripts/ until then")

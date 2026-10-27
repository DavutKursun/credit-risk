.PHONY: setup setup-dev test cohort audit train train-no-grade eval-dev policy-dev fairness-dev drift smoke app

PY ?= python

setup:
	$(PY) -m pip install -r requirements.txt
setup-dev:
	$(PY) -m pip install -r requirements-dev.txt
test:
	$(PY) -m pytest -q
cohort:           ## raw CSV → matured 36-month cohort, out-of-time splits, summary.json
	$(PY) scripts/download.py && $(PY) scripts/build_cohort.py
audit:            ## single-feature AUC audit on train (+ uncertain bureau columns)
	$(PY) scripts/audit_leakage.py --extra-columns
train:            ## scorecard + LightGBM with LC grade features, calibrated on dev
	$(PY) scripts/train.py --model both
train-no-grade:   ## the 'from scratch' variant
	$(PY) scripts/train.py --model both --no-lc-grade
eval-dev:
	$(PY) scripts/evaluate.py --split dev
policy-dev:
	$(PY) scripts/policy_eval.py --split dev
fairness-dev:
	$(PY) scripts/fairness_report.py --model lgbm --split dev
drift:
	$(PY) scripts/drift_report.py
smoke:            ## the whole chain on a synthetic export (no real data)
	$(PY) -m pytest -q tests/test_scripts.py
app:
	$(PY) -m uvicorn app:app --port 7860

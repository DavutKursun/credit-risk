"""Calibrators fitted on dev, applied to raw model output.

Isotonic (default): monotone step function, flexible, needs a few thousand rows. Platt: logistic regression on the
logit, two parameters, safer on small sets. The reliability table before/after is the evidence that it worked.
"""

from __future__ import annotations

import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression


class IsotonicCalibrator:
    method = "isotonic"

    def __init__(self) -> None:
        # floor/ceiling at 0.1%: a calibrated PD of exactly 0 or 1 would make log loss explode on one surprise
        self._iso = IsotonicRegression(y_min=1e-3, y_max=1 - 1e-3, out_of_bounds="clip")

    def fit(self, p_raw, y) -> IsotonicCalibrator:
        self._iso.fit(np.asarray(p_raw, dtype=float), np.asarray(y, dtype=float))
        return self

    def transform(self, p_raw) -> np.ndarray:
        return self._iso.predict(np.asarray(p_raw, dtype=float))


class PlattCalibrator:
    method = "platt"

    def __init__(self) -> None:
        self._lr = LogisticRegression(C=1e6, max_iter=1000)

    @staticmethod
    def _logit(p):
        p = np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
        return np.log(p / (1 - p)).reshape(-1, 1)

    def fit(self, p_raw, y) -> PlattCalibrator:
        self._lr.fit(self._logit(p_raw), np.asarray(y, dtype=int))
        return self

    def transform(self, p_raw) -> np.ndarray:
        return self._lr.predict_proba(self._logit(p_raw))[:, 1]


def fit_calibrator(p_raw, y, method: str = "isotonic"):
    cal = IsotonicCalibrator() if method == "isotonic" else PlattCalibrator()
    return cal.fit(p_raw, y)

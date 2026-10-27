"""Calibrators fitted on dev, applied to raw model output.

Isotonic (default): a monotone function fitted on equal-count bins of the calibration rows (at least 500 rows per bin, weighted by
the bin size), flexible and immune to a handful of defaults in the tail. Platt: logistic regression on the logit, two parameters,
safer on small sets. The reliability table before/after is the evidence that it worked.
"""

from __future__ import annotations

import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression


class IsotonicCalibrator:
    """Isotonic regression on equal-count bins of the calibration rows, not on the raw points: each bin contributes its mean raw
    PD, its observed default rate and its row count as weight, so no step of the fitted function can rest on a handful of
    defaults in the tail (with raw points, two or three top-scored defaulters put the last step at 1.0). Bins hold at least
    `min_rows_per_bin` rows; a calibration set too small for `min_bins` such bins (fewer than 5,000 rows by default) is fitted on
    its raw points, the classic isotonic fit, because binning it would only coarsen the ranking."""

    method = "isotonic"

    def __init__(self, min_rows_per_bin: int = 500, min_bins: int = 10) -> None:
        # floor/ceiling at 0.1%: a calibrated PD of exactly 0 or 1 would make log loss explode on one surprise
        self._iso = IsotonicRegression(y_min=1e-3, y_max=1 - 1e-3, out_of_bounds="clip")
        self.min_rows_per_bin, self.min_bins = min_rows_per_bin, min_bins
        self.bins_: int | None = None

    def _binned(self, p_raw: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        order = np.argsort(p_raw, kind="stable")
        parts = np.array_split(order, max(len(p_raw) // self.min_rows_per_bin, 1))
        x = np.array([p_raw[i].mean() for i in parts])
        t = np.array([y[i].mean() for i in parts])
        w = np.array([len(i) for i in parts], dtype=float)
        return x, t, w

    def fit(self, p_raw, y) -> IsotonicCalibrator:
        p_raw, y = np.asarray(p_raw, dtype=float), np.asarray(y, dtype=float)
        if len(p_raw) < self.min_rows_per_bin * self.min_bins:
            self.bins_ = None  # too small to bin: raw-point isotonic fit
            self._iso.fit(p_raw, y)
            return self
        x, t, w = self._binned(p_raw, y)
        self.bins_ = len(x)
        self._iso.fit(x, t, sample_weight=w)
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

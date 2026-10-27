"""Unit tests for Phase 3: Calibrated ML Pipeline & Multi-Model Comparison."""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

_src = Path(__file__).resolve().parents[1] / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from confidence_pipeline.train import build_pipeline, train
from confidence_pipeline.evaluate import compute_ece, evaluate
from confidence_pipeline.data_generation import generate_synthetic_dataset


class TestModelCalibration:
    def test_build_pipeline_models(self):
        for m in ["logistic_regression", "random_forest", "gradient_boosting"]:
            pipe = build_pipeline(model_type=m, calibrate=False)
            assert pipe is not None
            assert "classifier" in pipe.named_steps

    def test_build_calibrated_pipeline(self):
        pipe = build_pipeline(model_type="logistic_regression", calibrate=True)
        assert pipe is not None
        assert hasattr(pipe.named_steps["classifier"], "estimator")

    def test_compute_ece_perfect(self):
        # Perfectly calibrated
        y_true = np.array([1, 1, 0, 0])
        y_prob = np.array([1.0, 1.0, 0.0, 0.0])
        ece = compute_ece(y_true, y_prob, n_bins=5)
        assert ece == pytest.approx(0.0, abs=1e-5)

    def test_compute_ece_miscalibrated(self):
        # Miscalibrated: predicts 1.0 with certainty, but true is 0
        y_true = np.array([0, 0, 0, 0])
        y_prob = np.array([1.0, 1.0, 1.0, 1.0])
        ece = compute_ece(y_true, y_prob, n_bins=5)
        assert ece == pytest.approx(1.0, abs=1e-5)

    def test_train_calibrated_model(self, tmp_path):
        df = generate_synthetic_dataset(n=100, seed=42)
        save_file = tmp_path / "model.joblib"
        pipe, _, test_meta = train(df, model_type="random_forest", calibrate=True, save_path=save_file)
        assert save_file.exists()
        preds = pipe.predict_proba(test_meta)[:, 1]
        assert len(preds) == len(test_meta)
        assert np.all(preds >= 0.0) and np.all(preds <= 1.0)

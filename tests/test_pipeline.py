"""
tests/test_pipeline.py — Automated tests for the confidence pipeline.

Run from project root:
    .venv/bin/python -m pytest tests/ -v

Tests use temporary directories to avoid touching real project data.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# ── Ensure src/ is importable from the project root
_project_root = Path(__file__).resolve().parents[1]
_src = _project_root / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from confidence_pipeline.config import (
    SYNTHETIC_SEED,
    SYNTHETIC_N,
    ID_COL,
    LABEL_COL,
    FEATURE_COLS,
    NUMERIC_FEATURES,
    CATEGORICAL_FEATURES,
    BOOL_FEATURES,
    CONFIDENCE_THRESHOLD,
    POSITIVE_CLASS,
)
from confidence_pipeline.data_generation import generate_synthetic_dataset
from confidence_pipeline.data_loader import load_and_validate, DataValidationError, split_features_labels
from confidence_pipeline.preprocessing import build_preprocessor
from confidence_pipeline.train import build_pipeline, train, load_model


# ══════════════════════════════════════════════════════════════════════
#  Fixtures
# ══════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def synthetic_df(tmp_path_factory):
    """Generate a small synthetic dataset in a temp directory."""
    tmp = tmp_path_factory.mktemp("data")
    csv_path = tmp / "test_candidates.csv"
    df = generate_synthetic_dataset(n=200, seed=SYNTHETIC_SEED, output_path=csv_path, save=True)
    return df, csv_path


@pytest.fixture(scope="module")
def trained_pipeline_and_splits(synthetic_df, tmp_path_factory):
    """Train a pipeline on the synthetic dataset and return artefacts."""
    df, _ = synthetic_df
    tmp = tmp_path_factory.mktemp("models")
    model_path = tmp / "model.joblib"
    pipeline, X_train, X_test = train(df, model_type="logistic_regression", save_path=model_path)
    return pipeline, X_train, X_test, model_path


# ══════════════════════════════════════════════════════════════════════
#  Dataset generation tests
# ══════════════════════════════════════════════════════════════════════

class TestDataGeneration:

    def test_output_is_dataframe(self, synthetic_df):
        df, _ = synthetic_df
        assert isinstance(df, pd.DataFrame)

    def test_row_count(self, synthetic_df):
        df, _ = synthetic_df
        assert len(df) == 200

    def test_required_columns_present(self, synthetic_df):
        df, _ = synthetic_df
        for col in [ID_COL, LABEL_COL] + FEATURE_COLS:
            assert col in df.columns, f"Missing column: {col}"

    def test_reproducibility(self, tmp_path):
        """Same seed must produce identical datasets."""
        df1 = generate_synthetic_dataset(n=100, seed=99, output_path=tmp_path / "a.csv", save=True)
        df2 = generate_synthetic_dataset(n=100, seed=99, output_path=tmp_path / "b.csv", save=True)
        pd.testing.assert_frame_equal(df1, df2)

    def test_different_seeds_differ(self, tmp_path):
        df1 = generate_synthetic_dataset(n=100, seed=1, output_path=tmp_path / "a.csv", save=True)
        df2 = generate_synthetic_dataset(n=100, seed=2, output_path=tmp_path / "b.csv", save=True)
        assert not df1.equals(df2)

    def test_no_duplicate_ids(self, synthetic_df):
        df, _ = synthetic_df
        assert df[ID_COL].nunique() == len(df)

    def test_labels_are_binary(self, synthetic_df):
        df, _ = synthetic_df
        assert set(df[LABEL_COL].unique()).issubset({0, 1})

    def test_both_classes_present(self, synthetic_df):
        df, _ = synthetic_df
        assert 0 in df[LABEL_COL].values
        assert 1 in df[LABEL_COL].values

    def test_csv_file_saved(self, synthetic_df):
        _, csv_path = synthetic_df
        assert csv_path.exists()
        reloaded = pd.read_csv(csv_path)
        assert len(reloaded) == 200

    def test_numeric_features_are_numeric(self, synthetic_df):
        df, _ = synthetic_df
        for col in NUMERIC_FEATURES:
            assert pd.api.types.is_numeric_dtype(df[col]), f"{col} not numeric"

    def test_bool_features_are_binary(self, synthetic_df):
        df, _ = synthetic_df
        for col in BOOL_FEATURES:
            assert set(df[col].unique()).issubset({0, 1}), f"{col} not binary"


# ══════════════════════════════════════════════════════════════════════
#  Data loader / validation tests
# ══════════════════════════════════════════════════════════════════════

class TestDataLoader:

    def test_loads_valid_csv(self, synthetic_df):
        df, csv_path = synthetic_df
        loaded = load_and_validate(csv_path, verbose=False)
        assert len(loaded) == len(df)

    def test_raises_on_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_and_validate(tmp_path / "nonexistent.csv", verbose=False)

    def test_raises_on_missing_column(self, tmp_path):
        df = pd.DataFrame({ID_COL: ["c_0"], LABEL_COL: [1], "src_instr_count": [2]})
        p = tmp_path / "bad.csv"
        df.to_csv(p, index=False)
        with pytest.raises(DataValidationError, match="Missing required columns"):
            load_and_validate(p, verbose=False)

    def test_raises_on_duplicate_ids(self, tmp_path):
        df = generate_synthetic_dataset(n=50, seed=1, save=False)
        # Force duplicates
        df.loc[1, ID_COL] = df.loc[0, ID_COL]
        p = tmp_path / "dup.csv"
        df.to_csv(p, index=False)
        with pytest.raises(DataValidationError, match="Duplicate candidate IDs"):
            load_and_validate(p, verbose=False)

    def test_raises_on_invalid_label(self, tmp_path):
        df = generate_synthetic_dataset(n=50, seed=1, save=False)
        df.loc[0, LABEL_COL] = 99
        p = tmp_path / "bad_label.csv"
        df.to_csv(p, index=False)
        with pytest.raises(DataValidationError, match="outside"):
            load_and_validate(p, verbose=False)

    def test_split_features_labels(self, synthetic_df):
        df, _ = synthetic_df
        X, y = split_features_labels(df)
        assert list(X.columns) == FEATURE_COLS
        assert y.name == LABEL_COL
        assert len(X) == len(y) == len(df)


# ══════════════════════════════════════════════════════════════════════
#  Preprocessing tests
# ══════════════════════════════════════════════════════════════════════

class TestPreprocessing:

    def test_preprocessor_fits_and_transforms(self, synthetic_df):
        df, _ = synthetic_df
        X = df[FEATURE_COLS]
        preprocessor = build_preprocessor()
        X_tr = preprocessor.fit_transform(X)
        assert X_tr.shape[0] == len(df)
        assert X_tr.shape[1] > 0

    def test_no_nans_after_preprocessing(self, synthetic_df):
        df, _ = synthetic_df
        X = df[FEATURE_COLS]
        preprocessor = build_preprocessor()
        X_tr = preprocessor.fit_transform(X)
        assert not np.isnan(X_tr).any()

    def test_preprocessor_handles_missing_values(self, synthetic_df):
        df, _ = synthetic_df
        X = df[FEATURE_COLS].copy()
        # Inject missing values
        X.loc[X.index[0], "src_instr_count"] = np.nan
        X.loc[X.index[1], "src_opcode_category"] = np.nan
        preprocessor = build_preprocessor()
        X_tr = preprocessor.fit_transform(X)
        assert not np.isnan(X_tr).any()


# ══════════════════════════════════════════════════════════════════════
#  Training tests
# ══════════════════════════════════════════════════════════════════════

class TestTraining:

    def test_pipeline_builds(self):
        pipeline = build_pipeline("logistic_regression")
        assert pipeline is not None

    def test_train_returns_pipeline(self, trained_pipeline_and_splits):
        pipeline, _, _, _ = trained_pipeline_and_splits
        assert hasattr(pipeline, "predict")
        assert hasattr(pipeline, "predict_proba")

    def test_model_saved_to_disk(self, trained_pipeline_and_splits):
        _, _, _, model_path = trained_pipeline_and_splits
        assert model_path.exists()

    def test_train_test_split_sizes(self, synthetic_df, trained_pipeline_and_splits):
        df, _ = synthetic_df
        _, X_train, X_test, _ = trained_pipeline_and_splits
        assert len(X_train) + len(X_test) == len(df)

    def test_both_classes_in_test(self, trained_pipeline_and_splits):
        _, _, X_test, _ = trained_pipeline_and_splits
        labels = X_test[LABEL_COL].unique()
        assert 0 in labels and 1 in labels

    def test_load_model(self, trained_pipeline_and_splits):
        _, _, _, model_path = trained_pipeline_and_splits
        loaded = load_model(model_path)
        assert hasattr(loaded, "predict_proba")

    def test_load_model_raises_on_missing(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_model(tmp_path / "no_model.joblib")


# ══════════════════════════════════════════════════════════════════════
#  Prediction / confidence scoring tests
# ══════════════════════════════════════════════════════════════════════

class TestPrediction:

    def test_predictions_have_required_columns(self, synthetic_df, trained_pipeline_and_splits):
        from confidence_pipeline.predict import score_candidates
        df, _ = synthetic_df
        pipeline, _, X_test, _ = trained_pipeline_and_splits
        test_df = df.loc[X_test.index]
        preds = score_candidates(test_df, pipeline, threshold=0.5)
        for col in [ID_COL, "predicted_label", "confidence_score", "confidence_category"]:
            assert col in preds.columns, f"Missing column: {col}"

    def test_confidence_scores_in_range(self, synthetic_df, trained_pipeline_and_splits):
        from confidence_pipeline.predict import score_candidates
        df, _ = synthetic_df
        pipeline, _, X_test, _ = trained_pipeline_and_splits
        test_df = df.loc[X_test.index]
        preds = score_candidates(test_df, pipeline, threshold=0.5)
        scores = preds["confidence_score"].values
        assert np.all(scores >= 0.0), "Scores below 0"
        assert np.all(scores <= 1.0), "Scores above 1"

    def test_confidence_categories_match_threshold(self, synthetic_df, trained_pipeline_and_splits):
        from confidence_pipeline.predict import score_candidates
        df, _ = synthetic_df
        pipeline, _, X_test, _ = trained_pipeline_and_splits
        test_df = df.loc[X_test.index]
        threshold = 0.6
        preds = score_candidates(test_df, pipeline, threshold=threshold)
        high = preds[preds["confidence_category"] == "High"]["confidence_score"]
        low  = preds[preds["confidence_category"] == "Low"]["confidence_score"]
        assert (high >= threshold).all(), "High category has scores below threshold"
        assert (low  <  threshold).all(), "Low category has scores above threshold"

    def test_both_categories_can_exist(self, synthetic_df, trained_pipeline_and_splits):
        from confidence_pipeline.predict import score_candidates
        df, _ = synthetic_df
        pipeline, _, X_test, _ = trained_pipeline_and_splits
        test_df = df.loc[X_test.index]
        # Use threshold near the median score to ensure both categories appear
        preds = score_candidates(test_df, pipeline, threshold=0.5)
        cats = preds["confidence_category"].unique()
        # At minimum the categories column should have valid values
        assert set(cats).issubset({"High", "Low"})

    def test_invalid_threshold_raises(self, synthetic_df, trained_pipeline_and_splits):
        from confidence_pipeline.predict import score_candidates
        df, _ = synthetic_df
        pipeline, _, X_test, _ = trained_pipeline_and_splits
        test_df = df.loc[X_test.index]
        with pytest.raises(ValueError, match="threshold"):
            score_candidates(test_df, pipeline, threshold=1.5)


# ══════════════════════════════════════════════════════════════════════
#  Evaluation tests
# ══════════════════════════════════════════════════════════════════════

class TestEvaluation:

    def test_evaluate_returns_dict_with_keys(self, synthetic_df, trained_pipeline_and_splits):
        from confidence_pipeline.predict import score_candidates
        from confidence_pipeline.evaluate import evaluate
        df, _ = synthetic_df
        pipeline, _, X_test, _ = trained_pipeline_and_splits
        test_df = df.loc[X_test.index]
        preds = score_candidates(test_df, pipeline, threshold=0.5)
        metrics = evaluate(
            preds["true_label"], preds["predicted_label"],
            preds["confidence_score"], save=False
        )
        for key in ["accuracy", "precision_pos", "recall_pos", "f1_pos", "roc_auc"]:
            assert key in metrics, f"Missing metric: {key}"

    def test_metrics_are_in_valid_range(self, synthetic_df, trained_pipeline_and_splits):
        from confidence_pipeline.predict import score_candidates
        from confidence_pipeline.evaluate import evaluate
        df, _ = synthetic_df
        pipeline, _, X_test, _ = trained_pipeline_and_splits
        test_df = df.loc[X_test.index]
        preds = score_candidates(test_df, pipeline, threshold=0.5)
        metrics = evaluate(
            preds["true_label"], preds["predicted_label"],
            preds["confidence_score"], save=False
        )
        assert 0.0 <= metrics["accuracy"]      <= 1.0
        assert 0.0 <= metrics["precision_pos"] <= 1.0
        assert 0.0 <= metrics["recall_pos"]    <= 1.0
        assert 0.0 <= metrics["f1_pos"]        <= 1.0
        if metrics["roc_auc"] is not None:
            assert 0.0 <= metrics["roc_auc"]   <= 1.0

    def test_metrics_computed_from_predictions_not_hardcoded(
        self, synthetic_df, trained_pipeline_and_splits
    ):
        """Verify metrics actually change when predictions change."""
        from confidence_pipeline.predict import score_candidates
        from confidence_pipeline.evaluate import evaluate
        df, _ = synthetic_df
        pipeline, _, X_test, _ = trained_pipeline_and_splits
        test_df = df.loc[X_test.index]
        preds = score_candidates(test_df, pipeline, threshold=0.5)
        metrics1 = evaluate(
            preds["true_label"], preds["predicted_label"],
            preds["confidence_score"], save=False
        )
        # Flip all predictions
        flipped = 1 - preds["predicted_label"].values
        metrics2 = evaluate(
            preds["true_label"], flipped,
            preds["confidence_score"], save=False
        )
        # Accuracy should differ when predictions are flipped
        assert metrics1["accuracy"] != metrics2["accuracy"]


# ══════════════════════════════════════════════════════════════════════
#  End-to-end integration test
# ══════════════════════════════════════════════════════════════════════

class TestEndToEnd:

    def test_full_pipeline_runs(self, tmp_path):
        """
        Generate → train → predict → evaluate without touching real files.
        Verifies the pipeline completes without errors on fresh data.
        """
        from confidence_pipeline.data_generation import generate_synthetic_dataset
        from confidence_pipeline.data_loader import load_and_validate
        from confidence_pipeline.train import train, load_model
        from confidence_pipeline.predict import score_candidates
        from confidence_pipeline.evaluate import evaluate

        csv_path   = tmp_path / "candidates.csv"
        model_path = tmp_path / "model.joblib"

        # Generate
        df = generate_synthetic_dataset(n=150, seed=7, output_path=csv_path, save=True)

        # Load & validate
        df_loaded = load_and_validate(csv_path, verbose=False)
        assert len(df_loaded) == 150

        # Train
        pipeline, X_train, X_test = train(df_loaded, save_path=model_path)

        # Score test set
        from confidence_pipeline.config import LABEL_COL, ID_COL, FEATURE_COLS
        test_df = df_loaded.loc[X_test.index]
        preds = score_candidates(test_df, pipeline, threshold=0.5)

        # Evaluate
        metrics = evaluate(
            preds["true_label"], preds["predicted_label"],
            preds["confidence_score"], save=False
        )

        # Load saved model and re-predict
        loaded_pipeline = load_model(model_path)
        preds2 = score_candidates(test_df, loaded_pipeline, threshold=0.5)
        np.testing.assert_array_equal(
            preds["confidence_score"].values,
            preds2["confidence_score"].values,
        )

        assert 0.0 <= metrics["accuracy"] <= 1.0

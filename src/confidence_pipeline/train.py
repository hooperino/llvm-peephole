"""
train.py — Model training and probability calibration for the confidence pipeline.

Models supported:
  - Logistic Regression (linear, fast, interpretable)
  - Random Forest (non-linear, ensemble of decision trees)
  - Gradient Boosting (boosting on tabular decision trees)

Probability Calibration:
  - Platt Scaling (sigmoid) or Isotonic Regression via CalibratedClassifierCV
  - Transforms raw heuristic margins / tree leaf fractions into true posterior probabilities P(verified=1 | features).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from confidence_pipeline.config import (
    MODELS_DIR,
    MODEL_PATH,
    TEST_SIZE,
    SPLIT_SEED,
    MODEL_SEED,
    MAX_ITER,
    LABEL_COL,
    ID_COL,
    FEATURE_COLS,
)
from confidence_pipeline.preprocessing import build_preprocessor


ModelType = Literal["logistic_regression", "random_forest", "gradient_boosting"]
CalibrationMethod = Literal["sigmoid", "isotonic"]


def build_pipeline(
    model_type: ModelType = "logistic_regression",
    calibrate: bool = False,
    calibration_method: CalibrationMethod = "sigmoid",
) -> Pipeline:
    """
    Return an unfitted sklearn Pipeline (preprocessor + classifier).

    Parameters
    ----------
    model_type:
        "logistic_regression", "random_forest", or "gradient_boosting".
    calibrate:
        If True, wrap the classifier in CalibratedClassifierCV (Platt scaling or isotonic).
    calibration_method:
        "sigmoid" (Platt scaling) or "isotonic".
    """
    preprocessor = build_preprocessor()

    if model_type == "logistic_regression":
        classifier = LogisticRegression(
            max_iter=MAX_ITER,
            random_state=MODEL_SEED,
            class_weight="balanced",
            solver="lbfgs",
            C=1.0,
        )
    elif model_type == "random_forest":
        classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=8,
            random_state=MODEL_SEED,
            class_weight="balanced",
        )
    elif model_type == "gradient_boosting":
        classifier = HistGradientBoostingClassifier(
            max_iter=100,
            max_depth=5,
            random_state=MODEL_SEED,
        )
    else:
        raise ValueError(f"Unknown model_type: {model_type!r}")

    if calibrate:
        final_classifier = CalibratedClassifierCV(
            estimator=classifier,
            method=calibration_method,
            cv=5,
        )
    else:
        final_classifier = classifier

    return Pipeline([
        ("preprocessor", preprocessor),
        ("classifier",   final_classifier),
    ])


def train(
    df: pd.DataFrame,
    model_type: ModelType = "logistic_regression",
    calibrate: bool = False,
    calibration_method: CalibrationMethod = "sigmoid",
    save_path: Path = MODEL_PATH,
) -> tuple[Pipeline, pd.DataFrame, pd.DataFrame]:
    """
    Split the dataset, train the pipeline, and save the fitted model.

    Parameters
    ----------
    df:
        Full validated dataframe (features + label).
    model_type:
        Which classifier to use.
    calibrate:
        Whether to apply probability calibration.
    calibration_method:
        "sigmoid" (Platt scaling) or "isotonic".
    save_path:
        Where to write the fitted pipeline artifact (.joblib).

    Returns
    -------
    (fitted_pipeline, X_train_meta, X_test_meta)
    """
    X = df[FEATURE_COLS]
    y = df[LABEL_COL]
    meta = df[[ID_COL, LABEL_COL]].copy()

    X_train, X_test, y_train, y_test, meta_train, meta_test = train_test_split(
        X, y, meta,
        test_size=TEST_SIZE,
        random_state=SPLIT_SEED,
        stratify=y,
    )

    calib_str = f" [calibrated:{calibration_method}]" if calibrate else ""
    print(
        f"[train] Split: {len(X_train)} train / {len(X_test)} test  "
        f"(seed={SPLIT_SEED}, stratified)"
    )
    print(f"[train] Training {model_type}{calib_str} …")

    pipeline = build_pipeline(
        model_type=model_type,
        calibrate=calibrate,
        calibration_method=calibration_method,
    )
    pipeline.fit(X_train, y_train)

    print("[train] Training complete.")

    # Save fitted pipeline
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, save_path)
    print(f"[train] Model saved → {save_path}")

    X_test_meta = X_test.copy()
    X_test_meta[ID_COL]    = meta_test[ID_COL].values
    X_test_meta[LABEL_COL] = meta_test[LABEL_COL].values

    X_train_meta = X_train.copy()
    X_train_meta[ID_COL]    = meta_train[ID_COL].values
    X_train_meta[LABEL_COL] = meta_train[LABEL_COL].values

    return pipeline, X_train_meta, X_test_meta


def load_model(model_path: Path = MODEL_PATH) -> Pipeline:
    """Load and return a previously saved pipeline artifact."""
    model_path = Path(model_path)
    if not model_path.exists():
        raise FileNotFoundError(
            f"No saved model found at {model_path}. "
            "Run the training step first."
        )
    pipeline = joblib.load(model_path)
    print(f"[train] Model loaded ← {model_path}")
    return pipeline

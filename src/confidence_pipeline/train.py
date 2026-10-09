"""
train.py — Model training for the confidence pipeline.

Primary model : Logistic Regression (lightweight, probability-calibrated)
Optional model: Random Forest (comparison baseline)

Both are wrapped in a full scikit-learn Pipeline:
    preprocessor  →  classifier

The fitted pipeline is saved as a single .joblib artifact so that
prediction and evaluation require no separate preprocessing step.

DISCLAIMER
----------
The confidence scores produced by Logistic Regression are the model's
estimated P(label=1 | features).  They reflect the model's belief about
the synthetic training label, NOT a guarantee that Alive2 will verify
the transformation.  The label semantics must be updated or validated
once real candidate data is available.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
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


ModelType = Literal["logistic_regression", "random_forest"]


def build_pipeline(model_type: ModelType = "logistic_regression") -> Pipeline:
    """
    Return an unfitted sklearn Pipeline (preprocessor + classifier).

    Parameters
    ----------
    model_type:
        "logistic_regression" (default / primary) or "random_forest".
    """
    preprocessor = build_preprocessor()

    if model_type == "logistic_regression":
        classifier = LogisticRegression(
            max_iter=MAX_ITER,
            random_state=MODEL_SEED,
            class_weight="balanced",   # handles mild class imbalance
            solver="lbfgs",
            C=1.0,
        )
    elif model_type == "random_forest":
        classifier = RandomForestClassifier(
            n_estimators=100,
            random_state=MODEL_SEED,
            class_weight="balanced",
        )
    else:
        raise ValueError(f"Unknown model_type: {model_type!r}")

    return Pipeline([
        ("preprocessor", preprocessor),
        ("classifier",   classifier),
    ])


def train(
    df: pd.DataFrame,
    model_type: ModelType = "logistic_regression",
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
    save_path:
        Where to write the fitted pipeline artifact (.joblib).

    Returns
    -------
    (fitted_pipeline, X_train, X_test_with_meta)
        X_test_with_meta includes candidate_id and label alongside features
        so that downstream evaluation can reference them.
    """
    X = df[FEATURE_COLS]
    y = df[LABEL_COL]
    meta = df[[ID_COL, LABEL_COL]].copy()   # keep IDs for reporting

    X_train, X_test, y_train, y_test, meta_train, meta_test = train_test_split(
        X, y, meta,
        test_size=TEST_SIZE,
        random_state=SPLIT_SEED,
        stratify=y,
    )

    print(
        f"[train] Split: {len(X_train)} train / {len(X_test)} test  "
        f"(seed={SPLIT_SEED}, stratified)"
    )
    print(f"[train] Training {model_type} …")

    pipeline = build_pipeline(model_type)
    pipeline.fit(X_train, y_train)

    print("[train] Training complete.")

    # Save fitted pipeline
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, save_path)
    print(f"[train] Model saved → {save_path}")

    # Attach meta columns to test split for downstream use
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

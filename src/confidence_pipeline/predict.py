"""
predict.py — Confidence scoring for peephole optimization candidates.

For every candidate, generates:
  - candidate_id
  - true_label (if available)
  - predicted_label
  - confidence_score  (P(label=1))
  - confidence_category  ("High" or "Low")

THRESHOLD
---------
The threshold controls the High / Low split.  It is configurable and
defaults to config.CONFIDENCE_THRESHOLD (0.50).  The threshold is a
baseline for demonstration; it is NOT a scientifically established optimum.
Threshold-sensitivity experiments (Section 14 of the project spec) will be
conducted in a later milestone.

DISCLAIMER
----------
confidence_score = P(label=1 | features) according to the trained model.
This is NOT a probability that Alive2 will verify the transformation, and
it does NOT constitute a guarantee of semantic correctness.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

from confidence_pipeline.config import (
    CONFIDENCE_THRESHOLD,
    ID_COL,
    LABEL_COL,
    FEATURE_COLS,
    RESULTS_DIR,
    PREDICTIONS_CSV,
    POSITIVE_CLASS,
)
from confidence_pipeline.train import load_model


def score_candidates(
    df: pd.DataFrame,
    pipeline: Pipeline,
    threshold: float = CONFIDENCE_THRESHOLD,
) -> pd.DataFrame:
    """
    Assign confidence scores and categories to every candidate in *df*.

    Parameters
    ----------
    df:
        DataFrame containing at least FEATURE_COLS (and optionally
        ID_COL and LABEL_COL).
    pipeline:
        A fitted sklearn Pipeline (preprocessor + classifier).
    threshold:
        Candidates with confidence_score >= threshold → "High".
        Candidates with confidence_score <  threshold → "Low".

    Returns
    -------
    pd.DataFrame
        One row per candidate with columns:
        candidate_id, true_label, predicted_label,
        confidence_score, confidence_category.
    """
    if threshold < 0.0 or threshold > 1.0:
        raise ValueError(f"threshold must be in [0, 1], got {threshold}")

    X = df[FEATURE_COLS]

    # Predicted class (0 or 1)
    y_pred = pipeline.predict(X)

    # Probability of positive class
    proba = pipeline.predict_proba(X)
    pos_idx = list(pipeline.classes_).index(POSITIVE_CLASS)
    confidence_scores = proba[:, pos_idx]

    result = pd.DataFrame({
        ID_COL:               df[ID_COL].values if ID_COL in df.columns else np.arange(len(df)),
        "true_label":         df[LABEL_COL].values if LABEL_COL in df.columns else np.nan,
        "predicted_label":    y_pred,
        "confidence_score":   confidence_scores.round(4),
        "confidence_category": np.where(
            confidence_scores >= threshold, "High", "Low"
        ),
    })

    return result


def save_predictions(
    predictions: pd.DataFrame,
    output_path: Path = PREDICTIONS_CSV,
    original_df: pd.DataFrame | None = None,
) -> None:
    """
    Save predictions CSV.  Optionally appends human-readable src/tgt columns.
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    out = predictions.copy()
    if original_df is not None:
        for col in ["src_repr", "tgt_repr"]:
            if col in original_df.columns:
                out[col] = original_df[col].values

    out.to_csv(output_path, index=False)
    print(f"[predict] Predictions saved → {output_path}")


def print_sample_predictions(
    predictions: pd.DataFrame,
    n: int = 10,
    threshold: float = CONFIDENCE_THRESHOLD,
) -> None:
    """Print a sample of scored candidates to stdout."""
    print(f"\n{'─'*70}")
    print(f"  Sample predictions  (threshold={threshold})")
    print(f"{'─'*70}")
    print(
        f"  {'ID':<12} {'True':>5} {'Pred':>5} {'Score':>8}  Category"
    )
    print(f"{'─'*70}")

    sample = predictions.sample(min(n, len(predictions)), random_state=42)
    sample = sample.sort_values("confidence_score", ascending=False)

    for _, row in sample.iterrows():
        true_str = str(int(row["true_label"])) if not np.isnan(row["true_label"]) else "?"
        print(
            f"  {row[ID_COL]:<12} {true_str:>5} {int(row['predicted_label']):>5} "
            f"  {row['confidence_score']:>6.4f}  {row['confidence_category']}"
        )
    print(f"{'─'*70}\n")


def predict_from_saved_model(
    csv_path: Path,
    model_path: Path | None = None,
    threshold: float = CONFIDENCE_THRESHOLD,
    output_path: Path = PREDICTIONS_CSV,
) -> pd.DataFrame:
    """
    Load a saved model and generate predictions for candidates in *csv_path*.

    This is the entry point for inference on new (possibly unlabelled) data.
    """
    from confidence_pipeline.data_loader import load_and_validate

    pipeline = load_model(model_path) if model_path else load_model()
    df = load_and_validate(csv_path, require_labels=False, verbose=True)
    predictions = score_candidates(df, pipeline, threshold=threshold)
    save_predictions(predictions, output_path=output_path, original_df=df)
    print_sample_predictions(predictions, threshold=threshold)
    return predictions

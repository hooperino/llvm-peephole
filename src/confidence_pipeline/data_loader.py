"""
data_loader.py — Dataset loading and validation.

Loads a candidate CSV file and validates it against the expected schema.
Designed so that the synthetic CSV and Person 1's real CSV can be loaded
through the same interface, provided the real CSV follows the documented
schema (see data/README.md).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from confidence_pipeline.config import (
    SYNTHETIC_CSV,
    ID_COL,
    LABEL_COL,
    FEATURE_COLS,
    NUMERIC_FEATURES,
    CATEGORICAL_FEATURES,
    BOOL_FEATURES,
)


class DataValidationError(ValueError):
    """Raised when the input CSV does not satisfy schema requirements."""


def load_and_validate(
    csv_path: Path = SYNTHETIC_CSV,
    require_labels: bool = True,
    verbose: bool = True,
) -> pd.DataFrame:
    """
    Load a candidate CSV and validate its schema.

    Parameters
    ----------
    csv_path:
        Path to the candidate CSV file.
    require_labels:
        If True, raise DataValidationError when LABEL_COL is absent.
        Set to False for inference-only mode (no ground truth needed).
    verbose:
        Print summary statistics after loading.

    Returns
    -------
    pd.DataFrame
        Validated dataframe ready for downstream processing.

    Raises
    ------
    FileNotFoundError
        If csv_path does not exist.
    DataValidationError
        If schema validation fails.
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Candidate CSV not found: {csv_path}\n"
            "Run `python -m confidence_pipeline.data_generation` to generate it."
        )

    df = pd.read_csv(csv_path)

    if verbose:
        print(f"[data_loader] Loaded {len(df)} rows from {csv_path}")

    # ── Required columns ──────────────────────────────────────────────
    required = [ID_COL] + FEATURE_COLS
    if require_labels:
        required = required + [LABEL_COL]

    missing_cols = [c for c in required if c not in df.columns]
    if missing_cols:
        raise DataValidationError(
            f"Missing required columns: {missing_cols}\n"
            f"Present columns: {list(df.columns)}"
        )

    # ── Duplicate candidate IDs ───────────────────────────────────────
    dup_ids = df[df[ID_COL].duplicated()][ID_COL].tolist()
    if dup_ids:
        raise DataValidationError(
            f"Duplicate candidate IDs found ({len(dup_ids)} duplicates): "
            f"{dup_ids[:10]}{'...' if len(dup_ids) > 10 else ''}"
        )

    # ── Label values ──────────────────────────────────────────────────
    if require_labels:
        invalid_labels = df[~df[LABEL_COL].isin([0, 1])][LABEL_COL].unique()
        if len(invalid_labels) > 0:
            raise DataValidationError(
                f"Label column '{LABEL_COL}' contains values outside {{0, 1}}: "
                f"{invalid_labels}"
            )
        class_counts = df[LABEL_COL].value_counts()
        if len(class_counts) < 2:
            raise DataValidationError(
                f"Only one class present in label column '{LABEL_COL}'. "
                "Both classes (0 and 1) are required for supervised training."
            )

    # ── Numeric feature types ─────────────────────────────────────────
    for col in NUMERIC_FEATURES:
        if col in df.columns:
            if not pd.api.types.is_numeric_dtype(df[col]):
                try:
                    df[col] = pd.to_numeric(df[col])
                except (ValueError, TypeError) as exc:
                    raise DataValidationError(
                        f"Column '{col}' cannot be cast to numeric: {exc}"
                    ) from exc

    # ── Boolean features: cast to int ────────────────────────────────
    for col in BOOL_FEATURES:
        if col in df.columns:
            df[col] = df[col].astype(int)

    # ── Missing values ────────────────────────────────────────────────
    missing_summary = df[FEATURE_COLS].isnull().sum()
    missing_cols_with_nulls = missing_summary[missing_summary > 0]
    if not missing_cols_with_nulls.empty:
        # Warn but do not raise — preprocessing handles imputation
        print(
            f"[data_loader] WARNING: missing values detected in feature columns:\n"
            f"{missing_cols_with_nulls.to_string()}\n"
            "These will be imputed during preprocessing."
        )

    if verbose:
        if require_labels:
            label_counts = df[LABEL_COL].value_counts()
            print(
                f"[data_loader] Label distribution:\n"
                f"  label=1 (expected-verifiable): {label_counts.get(1, 0)}\n"
                f"  label=0 (not-expected-verifiable): {label_counts.get(0, 0)}"
            )
        print(f"[data_loader] Feature columns: {FEATURE_COLS}")

    return df


def split_features_labels(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """
    Return (X, y) where X contains only training feature columns
    and y is the label series.

    The candidate ID, textual repr columns, and label are excluded from X.
    """
    X = df[FEATURE_COLS].copy()
    y = df[LABEL_COL].copy()
    return X, y

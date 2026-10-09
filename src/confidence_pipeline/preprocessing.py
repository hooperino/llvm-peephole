"""
preprocessing.py — Feature preprocessing using scikit-learn pipelines.

Builds a ColumnTransformer that handles:
  - Numeric features: median imputation + standard scaling
  - Categorical features: most-frequent imputation + one-hot encoding
  - Boolean features: treated as numeric (already 0/1 ints)

The transformer is always fit ONLY on training data to prevent leakage.
"""

from __future__ import annotations

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from confidence_pipeline.config import (
    NUMERIC_FEATURES,
    CATEGORICAL_FEATURES,
    BOOL_FEATURES,
)


def build_preprocessor() -> ColumnTransformer:
    """
    Return an unfitted ColumnTransformer for the candidate feature schema.

    Numeric pipeline  : median imputation → z-score scaling
    Boolean pipeline  : median imputation (booleans stored as 0/1 ints)
    Categorical pipeline: mode imputation → one-hot encoding

    The transformer is designed to be embedded inside a full sklearn Pipeline
    together with the classifier so that fit() is called only on training data.
    """

    numeric_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler",  StandardScaler()),
    ])

    bool_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        # No scaling needed for 0/1 booleans, but StandardScaler
        # doesn't hurt and keeps the output range consistent.
        ("scaler",  StandardScaler()),
    ])

    categorical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        (
            "encoder",
            OneHotEncoder(
                handle_unknown="ignore",   # unseen categories → all zeros
                sparse_output=False,
            ),
        ),
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("num",  numeric_pipeline,     NUMERIC_FEATURES),
            ("bool", bool_pipeline,        BOOL_FEATURES),
            ("cat",  categorical_pipeline, CATEGORICAL_FEATURES),
        ],
        remainder="drop",   # silently drop any extra columns
    )

    return preprocessor

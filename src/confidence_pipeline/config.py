"""
config.py — Central configuration for the confidence pipeline.

All tuneable parameters live here so that nothing important is
hard-coded across the rest of the codebase.
"""

from pathlib import Path

# ── Project root (this file is at src/confidence_pipeline/config.py)
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# ── Data paths
DATA_DIR          = PROJECT_ROOT / "data"
SYNTHETIC_CSV     = DATA_DIR / "synthetic_candidates.csv"

# ── Model / results paths
MODELS_DIR        = PROJECT_ROOT / "models"
RESULTS_DIR       = PROJECT_ROOT / "results"
PLOTS_DIR         = RESULTS_DIR / "plots"
MODEL_PATH        = MODELS_DIR / "confidence_model.joblib"
PREDICTIONS_CSV   = RESULTS_DIR / "predictions.csv"
METRICS_JSON      = RESULTS_DIR / "metrics.json"
REPORT_TXT        = RESULTS_DIR / "evaluation_report.txt"

# ── Dataset generation
SYNTHETIC_SEED    = 42          # fixed seed for reproducibility
SYNTHETIC_N       = 800         # number of synthetic candidate records

# ── Train / test split
TEST_SIZE         = 0.20        # 80 / 20 split
SPLIT_SEED        = 42

# ── Model
MODEL_SEED        = 42
MAX_ITER          = 1000        # max iterations for Logistic Regression

# ── Confidence threshold
#    Candidates with P(positive) >= CONFIDENCE_THRESHOLD → High
#    Candidates with P(positive) <  CONFIDENCE_THRESHOLD → Low
#    This is a configurable baseline; it is NOT a scientifically
#    established optimum.  See Section 14 of the project spec.
CONFIDENCE_THRESHOLD = 0.50

# ── Column names used throughout the pipeline
ID_COL         = "candidate_id"
LABEL_COL      = "label"           # binary target: 1 = expected-verifiable, 0 = not

# Numeric feature columns
NUMERIC_FEATURES = [
    "src_instr_count",
    "tgt_instr_count",
    "instr_count_reduction",
    "num_operands",
    "num_constants",
    "num_variables",
    "candidate_complexity",
]

# Categorical feature columns
CATEGORICAL_FEATURES = [
    "src_opcode_category",
    "tgt_opcode_category",
]

# Boolean features (will be cast to int)
BOOL_FEATURES = [
    "has_constant_operand",
    "instr_count_differs",
]

# All feature columns used for training (do NOT include ID_COL or LABEL_COL)
FEATURE_COLS = NUMERIC_FEATURES + CATEGORICAL_FEATURES + BOOL_FEATURES

# Columns excluded from model input
NON_FEATURE_COLS = [ID_COL, LABEL_COL, "src_repr", "tgt_repr"]

# Positive class label value
POSITIVE_CLASS = 1
POSITIVE_CLASS_LABEL = "expected-verifiable"
NEGATIVE_CLASS_LABEL = "not-expected-verifiable"

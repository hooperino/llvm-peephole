"""Unit tests for Phase 4: Comparative Benchmarks & Statistical Evaluation."""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

_src = Path(__file__).resolve().parents[1] / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from experiments.baselines import (
    evaluate_exhaustive,
    evaluate_random,
    evaluate_heuristic,
    evaluate_ml_gated,
)
from experiments.pareto import sweep_thresholds
from experiments.significance import run_statistical_significance


@pytest.fixture
def mock_dataset():
    """Create a synthetic dataset with known properties for testing."""
    n = 50
    return pd.DataFrame({
        "candidate_id": [f"c_{i}" for i in range(n)],
        "label": [1 if i % 2 == 0 else 0 for i in range(n)],  # 25 positive, 25 negative
        "verification_time_ms": [50.0] * n,
        "src_instr_count": [3 if i % 2 == 0 else 2 for i in range(n)],
        "tgt_instr_count": [2 if i % 2 == 0 else 2 for i in range(n)],
        "instr_count_reduction": [1 if i % 2 == 0 else 0 for i in range(n)],
        "num_operands": [4] * n,
        "num_constants": [1] * n,
        "num_variables": [3] * n,
        "candidate_complexity": [5.0] * n,
        "src_opcode_category": ["arithmetic"] * n,
        "tgt_opcode_category": ["arithmetic"] * n,
        "has_constant_operand": [1] * n,
        "instr_count_differs": [1 if i % 2 == 0 else 0 for i in range(n)],
    })


class TestBaselines:
    def test_evaluate_exhaustive(self, mock_dataset):
        res = evaluate_exhaustive(mock_dataset)
        assert res.candidates_verified == 50
        assert res.valid_retained == 25
        assert res.retention_rate_pct == 100.0
        assert res.time_saved_pct == 0.0
        assert res.speedup_factor == 1.0

    def test_evaluate_random(self, mock_dataset):
        res = evaluate_random(mock_dataset, budget_k=20, n_trials=10, seed=42)
        assert res.candidates_verified == 20
        assert res.fraction_candidates_verified == 20 / 50
        assert res.time_saved_pct > 0.0
        assert res.speedup_factor > 1.0

    def test_evaluate_heuristic(self, mock_dataset):
        res = evaluate_heuristic(mock_dataset, rule="instr_reduction")
        assert res.candidates_verified == 25
        assert res.valid_retained == 25
        assert res.retention_rate_pct == 100.0
        assert res.selection_precision_pct == 100.0

    def test_evaluate_ml_gated(self, mock_dataset):
        # Perfect scores for positives
        scores = np.array([0.9 if i % 2 == 0 else 0.1 for i in range(50)])
        res = evaluate_ml_gated(mock_dataset, scores, threshold=0.50)
        assert res.candidates_verified == 25
        assert res.valid_retained == 25
        assert res.selection_precision_pct == 100.0
        assert res.retention_rate_pct == 100.0
        assert res.time_saved_pct > 40.0


class TestPareto:
    def test_sweep_thresholds(self, mock_dataset):
        scores = np.array([0.9 if i % 2 == 0 else 0.1 for i in range(50)])
        sweep_df = sweep_thresholds(mock_dataset, scores, thresholds=np.array([0.2, 0.5, 0.8]))
        assert len(sweep_df) == 3
        assert "ML_Retention_Pct" in sweep_df.columns
        assert "ML_Time_Saved_Pct" in sweep_df.columns
        assert "Random_Retention_Pct" in sweep_df.columns


class TestSignificance:
    def test_run_statistical_significance(self, mock_dataset):
        sig = run_statistical_significance(mock_dataset, n_splits=3, threshold=0.50, seed=42)
        assert "hypothesis_tests" in sig
        assert "precision_advantage" in sig["hypothesis_tests"]
        assert "p_value" in sig["hypothesis_tests"]["precision_advantage"]

"""Experiments package for statistical comparative evaluation and baselines."""

from .baselines import (
    BaselineResult,
    evaluate_exhaustive,
    evaluate_random,
    evaluate_heuristic,
    evaluate_ml_gated,
)
from .pareto import sweep_thresholds, plot_pareto_curves
from .significance import run_statistical_significance

__all__ = [
    "BaselineResult",
    "evaluate_exhaustive",
    "evaluate_random",
    "evaluate_heuristic",
    "evaluate_ml_gated",
    "sweep_thresholds",
    "plot_pareto_curves",
    "run_statistical_significance",
]

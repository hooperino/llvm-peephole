"""Comparative execution baselines for peephole optimization verification.

Baselines implemented:
  1. Exhaustive Verification (All-Verify with Alive2): Formal gold standard.
  2. Random Selection (Equal-Budget Verifier): Evaluates random downsampling.
  3. Heuristic Gating: Rule-based verification (e.g. instruction count decrease).
  4. ML Confidence-Gated Verification: Prioritizes candidates with calibrated P(verified) >= tau.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd


@dataclass
class BaselineResult:
    """Encapsulates the quantitative performance of a candidate verification strategy."""

    strategy_name: str
    candidates_verified: int
    fraction_candidates_verified: float
    valid_retained: int
    total_valid_available: int
    retention_rate_pct: float     # Recall of valid optimizations
    selection_precision_pct: float # Precision of prioritized candidates
    total_time_ms: float          # SMT latency + ML inference latency
    time_saved_pct: float         # Percentage of exhaustive SMT time saved
    speedup_factor: float         # T_exhaustive / T_strategy
    cost_per_valid_ms: float      # Milliseconds of verification spent per retained valid optimization

    def to_dict(self) -> Dict[str, Any]:
        return {
            "Strategy": self.strategy_name,
            "Verified Count": self.candidates_verified,
            "% Candidates Sent": round(self.fraction_candidates_verified * 100, 2),
            "Valid Retained": self.valid_retained,
            "Total Valid": self.total_valid_available,
            "Retention Rate (%)": round(self.retention_rate_pct, 2),
            "Precision (%)": round(self.selection_precision_pct, 2),
            "Total Time (ms)": round(self.total_time_ms, 2),
            "Time Saved (%)": round(self.time_saved_pct, 2),
            "Speedup": round(self.speedup_factor, 2),
            "Cost / Valid (ms)": round(self.cost_per_valid_ms, 2),
        }


def evaluate_exhaustive(df: pd.DataFrame) -> BaselineResult:
    """Baseline 1: Formally verify 100% of candidates using Alive2."""
    n_total = len(df)
    n_valid = int(df["label"].sum())
    total_smt_time = float(df["verification_time_ms"].sum())

    cost_per_valid = total_smt_time / n_valid if n_valid > 0 else 0.0

    return BaselineResult(
        strategy_name="Exhaustive (Verify All)",
        candidates_verified=n_total,
        fraction_candidates_verified=1.0,
        valid_retained=n_valid,
        total_valid_available=n_valid,
        retention_rate_pct=100.0,
        selection_precision_pct=(n_valid / n_total) * 100.0 if n_total > 0 else 0.0,
        total_time_ms=total_smt_time,
        time_saved_pct=0.0,
        speedup_factor=1.0,
        cost_per_valid_ms=cost_per_valid,
    )


def evaluate_random(
    df: pd.DataFrame,
    budget_k: int,
    n_trials: int = 50,
    seed: int = 42,
) -> BaselineResult:
    """Baseline 2: Randomly select budget_k candidates for verification (averaged over n_trials)."""
    n_total = len(df)
    total_valid = int(df["label"].sum())
    t_exhaustive = float(df["verification_time_ms"].sum())

    if budget_k <= 0:
        return BaselineResult(
            strategy_name=f"Random Selection (k={budget_k})",
            candidates_verified=0,
            fraction_candidates_verified=0.0,
            valid_retained=0,
            total_valid_available=total_valid,
            retention_rate_pct=0.0,
            selection_precision_pct=0.0,
            total_time_ms=0.0,
            time_saved_pct=100.0,
            speedup_factor=float("inf"),
            cost_per_valid_ms=0.0,
        )

    rng = np.random.default_rng(seed)

    retained_counts = []
    times = []

    for _ in range(n_trials):
        idx = rng.choice(n_total, size=budget_k, replace=False)
        sample = df.iloc[idx]
        retained_counts.append(sample["label"].sum())
        times.append(sample["verification_time_ms"].sum())

    avg_retained = float(np.mean(retained_counts))
    avg_time = float(np.mean(times))

    retention_pct = (avg_retained / total_valid * 100.0) if total_valid > 0 else 0.0
    precision_pct = (avg_retained / budget_k * 100.0) if budget_k > 0 else 0.0
    time_saved_pct = ((t_exhaustive - avg_time) / t_exhaustive * 100.0) if t_exhaustive > 0 else 0.0
    speedup = (t_exhaustive / avg_time) if avg_time > 0 else 1.0
    cost_per_valid = (avg_time / avg_retained) if avg_retained > 0 else 0.0

    return BaselineResult(
        strategy_name=f"Random Selection (Budget={budget_k})",
        candidates_verified=budget_k,
        fraction_candidates_verified=budget_k / n_total,
        valid_retained=int(round(avg_retained)),
        total_valid_available=total_valid,
        retention_rate_pct=retention_pct,
        selection_precision_pct=precision_pct,
        total_time_ms=avg_time,
        time_saved_pct=time_saved_pct,
        speedup_factor=speedup,
        cost_per_valid_ms=cost_per_valid,
    )


def evaluate_heuristic(df: pd.DataFrame, rule: str = "instr_reduction") -> BaselineResult:
    """Baseline 3: Heuristic selection rules."""
    n_total = len(df)
    total_valid = int(df["label"].sum())
    t_exhaustive = float(df["verification_time_ms"].sum())

    if rule == "instr_reduction":
        name = "Heuristic (Δinstr > 0)"
        mask = df["instr_count_reduction"] > 0
    elif rule == "instr_reduction_and_const":
        name = "Heuristic (Δinstr > 0 & HasConst)"
        mask = (df["instr_count_reduction"] > 0) & (df["has_constant_operand"] == 1)
    else:
        raise ValueError(f"Unknown heuristic rule: {rule}")

    selected = df[mask]
    k_selected = len(selected)
    retained_valid = int(selected["label"].sum())
    total_time = float(selected["verification_time_ms"].sum())

    retention_pct = (retained_valid / total_valid * 100.0) if total_valid > 0 else 0.0
    precision_pct = (retained_valid / k_selected * 100.0) if k_selected > 0 else 0.0
    time_saved_pct = ((t_exhaustive - total_time) / t_exhaustive * 100.0) if t_exhaustive > 0 else 0.0
    speedup = (t_exhaustive / total_time) if total_time > 0 else 1.0
    cost_per_valid = (total_time / retained_valid) if retained_valid > 0 else 0.0

    return BaselineResult(
        strategy_name=name,
        candidates_verified=k_selected,
        fraction_candidates_verified=k_selected / n_total if n_total > 0 else 0.0,
        valid_retained=retained_valid,
        total_valid_available=total_valid,
        retention_rate_pct=retention_pct,
        selection_precision_pct=precision_pct,
        total_time_ms=total_time,
        time_saved_pct=time_saved_pct,
        speedup_factor=speedup,
        cost_per_valid_ms=cost_per_valid,
    )


def evaluate_ml_gated(
    df: pd.DataFrame,
    confidence_scores: np.ndarray,
    threshold: float = 0.50,
    model_name: str = "Calibrated ML",
    ml_inference_time_ms_per_cand: float = 0.13,
) -> BaselineResult:
    """Proposed Approach: ML Confidence-Gated Verification with threshold tau."""
    n_total = len(df)
    total_valid = int(df["label"].sum())
    t_exhaustive = float(df["verification_time_ms"].sum())

    mask = (confidence_scores >= threshold)
    selected = df[mask]
    k_selected = len(selected)
    retained_valid = int(selected["label"].sum())

    # Include total ML inference overhead for all candidates + SMT time for verified ones
    total_ml_overhead = n_total * ml_inference_time_ms_per_cand
    smt_time = float(selected["verification_time_ms"].sum())
    total_time = total_ml_overhead + smt_time

    retention_pct = (retained_valid / total_valid * 100.0) if total_valid > 0 else 0.0
    precision_pct = (retained_valid / k_selected * 100.0) if k_selected > 0 else 0.0
    time_saved_pct = ((t_exhaustive - total_time) / t_exhaustive * 100.0) if t_exhaustive > 0 else 0.0
    speedup = (t_exhaustive / total_time) if total_time > 0 else 1.0
    cost_per_valid = (total_time / retained_valid) if retained_valid > 0 else 0.0

    return BaselineResult(
        strategy_name=f"{model_name} (τ={threshold:.2f})",
        candidates_verified=k_selected,
        fraction_candidates_verified=k_selected / n_total if n_total > 0 else 0.0,
        valid_retained=retained_valid,
        total_valid_available=total_valid,
        retention_rate_pct=retention_pct,
        selection_precision_pct=precision_pct,
        total_time_ms=total_time,
        time_saved_pct=time_saved_pct,
        speedup_factor=speedup,
        cost_per_valid_ms=cost_per_valid,
    )

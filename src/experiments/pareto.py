"""Pareto frontier and trade-off analysis across confidence thresholds."""

from pathlib import Path
from typing import List, Tuple, Dict, Any
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .baselines import evaluate_ml_gated, evaluate_random, evaluate_exhaustive


def sweep_thresholds(
    df: pd.DataFrame,
    confidence_scores: np.ndarray,
    thresholds: Optional[np.ndarray] = None,
    model_name: str = "Calibrated Random Forest",
    ml_overhead_ms: float = 0.13,
) -> pd.DataFrame:
    """Sweep decision thresholds tau in [0.05, 0.95] to compute trade-off points."""
    if thresholds is None:
        thresholds = np.linspace(0.10, 0.90, 17)

    records = []
    total_valid = int(df["label"].sum())

    for tau in thresholds:
        # Proposed ML Gated
        res_ml = evaluate_ml_gated(
            df,
            confidence_scores,
            threshold=float(tau),
            model_name=model_name,
            ml_inference_time_ms_per_cand=ml_overhead_ms,
        )

        # Budget-matched Random Selection
        res_rand = evaluate_random(df, budget_k=res_ml.candidates_verified, n_trials=30, seed=42)

        records.append({
            "Threshold": round(tau, 2),
            "Verified_Count": res_ml.candidates_verified,
            "ML_Retention_Pct": round(res_ml.retention_rate_pct, 2),
            "ML_Precision_Pct": round(res_ml.selection_precision_pct, 2),
            "ML_Time_Saved_Pct": round(res_ml.time_saved_pct, 2),
            "ML_Speedup": round(res_ml.speedup_factor, 2),
            "ML_Cost_Per_Valid_ms": round(res_ml.cost_per_valid_ms, 2),
            "Random_Retention_Pct": round(res_rand.retention_rate_pct, 2),
            "Random_Time_Saved_Pct": round(res_rand.time_saved_pct, 2),
            "Random_Speedup": round(res_rand.speedup_factor, 2),
            "Random_Cost_Per_Valid_ms": round(res_rand.cost_per_valid_ms, 2),
        })

    return pd.DataFrame(records)


def plot_pareto_curves(pareto_df: pd.DataFrame, output_dir: Path) -> Tuple[Path, Path, Path]:
    """Plot publication-quality Pareto frontier and speedup curves."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Pareto Frontier: Verification Time Saved vs Retention Rate
    p1 = output_dir / "pareto_frontier.png"
    plt.figure(figsize=(7, 5.5))
    plt.plot(
        pareto_df["ML_Time_Saved_Pct"],
        pareto_df["ML_Retention_Pct"],
        marker="o",
        linewidth=2.0,
        color="#1f77b4",
        label="Confidence-Gated ML (Proposed)",
    )
    plt.plot(
        pareto_df["Random_Time_Saved_Pct"],
        pareto_df["Random_Retention_Pct"],
        marker="s",
        linestyle="--",
        linewidth=1.8,
        color="#ff7f0e",
        label="Equal-Budget Random Selection",
    )

    # Annotate select thresholds
    for _, row in pareto_df.iterrows():
        if row["Threshold"] in [0.20, 0.40, 0.50, 0.60, 0.80]:
            plt.annotate(
                f"τ={row['Threshold']:.2f}",
                (row["ML_Time_Saved_Pct"], row["ML_Retention_Pct"]),
                textcoords="offset points",
                xytext=(8, -4),
                fontsize=8,
                color="#0f4c81",
                fontweight="bold",
            )

    plt.xlabel("Verification Time Saved (% of SMT Cost)", fontsize=11)
    plt.ylabel("Retained Valid Optimizations (%)", fontsize=11)
    plt.title("Pareto Frontier: Verification Time Saved vs. Retention", fontsize=12)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(loc="lower left", fontsize=10)
    plt.tight_layout()
    plt.savefig(p1, dpi=130)
    plt.close()

    # 2. Speedup Factor vs Retention Rate
    p2 = output_dir / "speedup_vs_retention.png"
    plt.figure(figsize=(7, 5.5))
    plt.plot(
        pareto_df["ML_Speedup"],
        pareto_df["ML_Retention_Pct"],
        marker="^",
        linewidth=2.0,
        color="#2ca02c",
        label="Confidence-Gated ML",
    )
    plt.plot(
        pareto_df["Random_Speedup"],
        pareto_df["Random_Retention_Pct"],
        marker="x",
        linestyle="--",
        linewidth=1.8,
        color="#d62728",
        label="Random Selection",
    )
    plt.xlabel("Verification Speedup Factor (x)", fontsize=11)
    plt.ylabel("Retained Valid Optimizations (%)", fontsize=11)
    plt.title("Verification Speedup vs. Optimization Retention", fontsize=12)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(loc="lower left", fontsize=10)
    plt.tight_layout()
    plt.savefig(p2, dpi=130)
    plt.close()

    # 3. SMT Cost per Valid Optimization (Efficiency)
    p3 = output_dir / "cost_per_optimization.png"
    plt.figure(figsize=(7, 5.5))
    plt.plot(
        pareto_df["Threshold"],
        pareto_df["ML_Cost_Per_Valid_ms"],
        marker="o",
        linewidth=2.0,
        color="#9467bd",
        label="Confidence-Gated ML",
    )
    plt.plot(
        pareto_df["Threshold"],
        pareto_df["Random_Cost_Per_Valid_ms"],
        marker="s",
        linestyle="--",
        linewidth=1.8,
        color="#8c564b",
        label="Random Selection",
    )
    plt.xlabel("Confidence Decision Threshold (τ)", fontsize=11)
    plt.ylabel("SMT Cost per Valid Optimization (ms)", fontsize=11)
    plt.title("Verification Efficiency (Cost per Valid Rewrite)", fontsize=12)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(loc="upper left", fontsize=10)
    plt.tight_layout()
    plt.savefig(p3, dpi=130)
    plt.close()

    return p1, p2, p3

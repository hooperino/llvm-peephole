#!/usr/bin/env python3
"""
run_experiments.py — Phase 4: Comparative evaluation and statistical benchmarking.

Runs:
  1. Main Baseline Comparison (Exhaustive vs Random vs Heuristic vs ML-Gated across thresholds).
  2. Pareto Frontier Sweep (Verification Time Saved vs Retention across tau in [0.10, 0.90]).
  3. Statistical Significance Testing (5-Fold Cross-Validation Paired t-tests).
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

# Add src to path
_src = Path(__file__).resolve().parent
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from confidence_pipeline.config import (
    REAL_CANDIDATES_CSV,
    RESULTS_DIR,
    PLOTS_DIR,
    FEATURE_COLS,
    LABEL_COL,
    SPLIT_SEED,
    TEST_SIZE,
)
from confidence_pipeline.data_loader import load_and_validate
from confidence_pipeline.train import build_pipeline
from experiments.baselines import (
    evaluate_exhaustive,
    evaluate_random,
    evaluate_heuristic,
    evaluate_ml_gated,
)
from experiments.pareto import sweep_thresholds, plot_pareto_curves
from experiments.significance import run_statistical_significance


def run_full_benchmarks(csv_path: Path):
    print("=" * 80)
    print("  PHASE 4: COMPARATIVE BENCHMARKING & STATISTICAL EVALUATION")
    print("=" * 80)

    df = load_and_validate(csv_path)
    print(f"[experiment] Loaded {len(df)} candidates from {csv_path}")

    # Stratified Train/Test split for evaluation
    X = df[FEATURE_COLS]
    y = df[LABEL_COL]
    _, test_idx = train_test_split(
        np.arange(len(df)), test_size=TEST_SIZE, random_state=SPLIT_SEED, stratify=y
    )
    test_df = df.iloc[test_idx].copy()
    train_df = df.drop(index=test_idx).copy()

    print(f"[experiment] Training set: {len(train_df)} | Held-out test set: {len(test_df)}")

    # Train Calibrated Random Forest model
    print("[experiment] Training calibrated Random Forest model on training split...")
    model = build_pipeline(model_type="random_forest", calibrate=True)
    model.fit(train_df[FEATURE_COLS], train_df[LABEL_COL])

    # Predict posterior probabilities on test set
    test_proba = model.predict_proba(test_df[FEATURE_COLS])[:, 1]

    # -------------------------------------------------------------------------
    # 1. Main Baseline Comparison Table
    # -------------------------------------------------------------------------
    print("\n[experiment] Evaluating comparative verification strategies on test set...")
    comparison_results = []

    # Strategy 1: Exhaustive (Verify All)
    res_exh = evaluate_exhaustive(test_df)
    comparison_results.append(res_exh.to_dict())

    # Strategy 2: Heuristic 1 (Instruction reduction)
    res_h1 = evaluate_heuristic(test_df, rule="instr_reduction")
    comparison_results.append(res_h1.to_dict())

    # Strategy 3: Heuristic 2 (Reduction + Const)
    res_h2 = evaluate_heuristic(test_df, rule="instr_reduction_and_const")
    comparison_results.append(res_h2.to_dict())

    # Evaluate ML-gating across varied decision thresholds tau
    sample_thresholds = [0.20, 0.40, 0.50, 0.60, 0.75]

    for tau in sample_thresholds:
        res_ml = evaluate_ml_gated(test_df, test_proba, threshold=tau, model_name="Proposed ML-Gated")
        comparison_results.append(res_ml.to_dict())

        # Equal-budget random selection matched to this threshold
        res_rand = evaluate_random(test_df, budget_k=res_ml.candidates_verified, n_trials=50, seed=42)
        res_rand.strategy_name = f"Random (Matched k={res_ml.candidates_verified})"
        comparison_results.append(res_rand.to_dict())

    comparison_df = pd.DataFrame(comparison_results)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    comp_csv = RESULTS_DIR / "baseline_comparison.csv"
    comparison_df.to_csv(comp_csv, index=False)
    print(f"[experiment] Saved main comparison table → {comp_csv}")

    # -------------------------------------------------------------------------
    # 2. Pareto Frontier Sweep across Thresholds tau in [0.10, 0.90]
    # -------------------------------------------------------------------------
    print("\n[experiment] Computing Pareto Frontier trade-off curves...")
    thresholds_sweep = np.linspace(0.10, 0.90, 17)
    pareto_df = sweep_thresholds(test_df, test_proba, thresholds=thresholds_sweep)

    pareto_csv = RESULTS_DIR / "pareto_frontier.csv"
    pareto_df.to_csv(pareto_csv, index=False)
    print(f"[experiment] Saved Pareto data → {pareto_csv}")

    p1, p2, p3 = plot_pareto_curves(pareto_df, PLOTS_DIR)
    print(f"[experiment] Saved Pareto plots:")
    print(f"  - {p1}")
    print(f"  - {p2}")
    print(f"  - {p3}")

    # -------------------------------------------------------------------------
    # 3. Statistical Significance Testing (5-Fold Cross-Validation)
    # -------------------------------------------------------------------------
    print("\n[experiment] Running 5-fold cross-validation paired significance tests...")
    sig_results = run_statistical_significance(df, n_splits=5, threshold=0.50, seed=42)

    sig_json = RESULTS_DIR / "statistical_tests.json"
    with open(sig_json, "w") as f:
        json.dump(sig_results, f, indent=2)
    print(f"[experiment] Saved statistical hypothesis tests → {sig_json}")

    # Print publication summary tables to terminal
    print("\n" + "=" * 105)
    print("                     TABLE 1: VERIFICATION STRATEGY COMPARISON (TEST SET)")
    print("=" * 105)
    print(comparison_df.to_string(index=False))
    print("=" * 105)

    print("\n" + "=" * 70)
    print("           STATISTICAL SIGNIFICANCE HYPOTHESIS TESTS (5-FOLD CV)")
    print("=" * 70)
    prec_test = sig_results["hypothesis_tests"]["precision_advantage"]
    cost_test = sig_results["hypothesis_tests"]["cost_efficiency_advantage"]

    print(f"  1. Selection Precision Advantage:")
    print(f"     - ML Gating Mean   : {prec_test['ml_mean']}%")
    print(f"     - Random Mean      : {prec_test['rand_mean']}%")
    print(f"     - Paired t-stat    : {prec_test['t_statistic']:.4f}")
    print(f"     - p-value          : {prec_test['p_value']:.4e} (p < 0.01: {prec_test['statistically_significant_p01']})")
    print()
    print(f"  2. Verification Cost Efficiency Advantage:")
    print(f"     - ML Cost/Valid    : {cost_test['ml_mean']} ms")
    print(f"     - Random Cost/Valid: {cost_test['rand_mean']} ms")
    print(f"     - Paired t-stat    : {cost_test['t_statistic']:.4f}")
    print(f"     - p-value          : {cost_test['p_value']:.4e} (p < 0.05: {cost_test['statistically_significant_p05']})")
    print("=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Run Phase 4 comparative evaluation.")
    parser.add_argument(
        "--input",
        type=str,
        default="data/real_candidates.csv",
        help="Input candidate dataset CSV (default: data/real_candidates.csv)",
    )
    args = parser.parse_args()

    project_root = _src.parent
    in_path = project_root / args.input if not Path(args.input).is_absolute() else Path(args.input)

    run_full_benchmarks(in_path)


if __name__ == "__main__":
    main()

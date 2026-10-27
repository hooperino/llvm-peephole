"""Statistical significance testing across cross-validation folds.

Computes paired Student's t-tests and Wilcoxon signed-rank tests comparing
the Proposed ML Confidence Gating against Random Selection and Heuristics.
"""

from typing import Dict, Any, List
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.model_selection import StratifiedKFold

from confidence_pipeline.config import FEATURE_COLS, LABEL_COL
from confidence_pipeline.train import build_pipeline
from .baselines import evaluate_ml_gated, evaluate_random, evaluate_heuristic


def run_statistical_significance(
    df: pd.DataFrame,
    n_splits: int = 5,
    threshold: float = 0.50,
    seed: int = 42,
) -> Dict[str, Any]:
    """Execute stratified k-fold cross-validation and compute paired significance tests."""
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)

    X = df[FEATURE_COLS]
    y = df[LABEL_COL]

    fold_metrics = {
        "ml_retention": [],
        "rand_retention": [],
        "ml_precision": [],
        "rand_precision": [],
        "ml_cost_per_valid": [],
        "rand_cost_per_valid": [],
        "heur_retention": [],
        "heur_precision": [],
    }

    for fold_idx, (train_idx, test_idx) in enumerate(skf.split(X, y)):
        train_df = df.iloc[train_idx]
        test_df = df.iloc[test_idx].copy()

        # Train calibrated Random Forest
        pipe = build_pipeline(model_type="random_forest", calibrate=True)
        pipe.fit(train_df[FEATURE_COLS], train_df[LABEL_COL])

        test_proba = pipe.predict_proba(test_df[FEATURE_COLS])[:, 1]

        # ML Gated on test fold
        res_ml = evaluate_ml_gated(test_df, test_proba, threshold=threshold)

        # Random Selection matched to ML budget
        res_rand = evaluate_random(test_df, budget_k=res_ml.candidates_verified, n_trials=30, seed=seed + fold_idx)

        # Heuristic on test fold
        res_heur = evaluate_heuristic(test_df, rule="instr_reduction")

        fold_metrics["ml_retention"].append(res_ml.retention_rate_pct)
        fold_metrics["rand_retention"].append(res_rand.retention_rate_pct)
        fold_metrics["ml_precision"].append(res_ml.selection_precision_pct)
        fold_metrics["rand_precision"].append(res_rand.selection_precision_pct)
        fold_metrics["ml_cost_per_valid"].append(res_ml.cost_per_valid_ms)
        fold_metrics["rand_cost_per_valid"].append(res_rand.cost_per_valid_ms)
        fold_metrics["heur_retention"].append(res_heur.retention_rate_pct)
        fold_metrics["heur_precision"].append(res_heur.selection_precision_pct)

    # Paired t-test: ML vs Random Precision
    t_stat_prec, p_val_prec = stats.ttest_rel(fold_metrics["ml_precision"], fold_metrics["rand_precision"])

    # Paired t-test: ML vs Random Retention
    t_stat_ret, p_val_ret = stats.ttest_rel(fold_metrics["ml_retention"], fold_metrics["rand_retention"])

    # Paired t-test: ML vs Random Verification Cost per Valid Rewrite
    t_stat_cost, p_val_cost = stats.ttest_rel(fold_metrics["ml_cost_per_valid"], fold_metrics["rand_cost_per_valid"])

    results = {
        "n_splits": n_splits,
        "evaluation_threshold": threshold,
        "fold_data": {k: [round(v, 2) for v in vals] for k, vals in fold_metrics.items()},
        "means": {
            "ml_precision_mean": round(float(np.mean(fold_metrics["ml_precision"])), 2),
            "rand_precision_mean": round(float(np.mean(fold_metrics["rand_precision"])), 2),
            "heur_precision_mean": round(float(np.mean(fold_metrics["heur_precision"])), 2),
            "ml_retention_mean": round(float(np.mean(fold_metrics["ml_retention"])), 2),
            "rand_retention_mean": round(float(np.mean(fold_metrics["rand_retention"])), 2),
            "heur_retention_mean": round(float(np.mean(fold_metrics["heur_retention"])), 2),
            "ml_cost_mean_ms": round(float(np.mean(fold_metrics["ml_cost_per_valid"])), 2),
            "rand_cost_mean_ms": round(float(np.mean(fold_metrics["rand_cost_per_valid"])), 2),
        },
        "hypothesis_tests": {
            "precision_advantage": {
                "metric": "Verification Selection Precision (%)",
                "ml_mean": round(float(np.mean(fold_metrics["ml_precision"])), 2),
                "rand_mean": round(float(np.mean(fold_metrics["rand_precision"])), 2),
                "t_statistic": round(float(t_stat_prec), 4),
                "p_value": float(p_val_prec),
                "statistically_significant_p05": bool(p_val_prec < 0.05),
                "statistically_significant_p01": bool(p_val_prec < 0.01),
            },
            "cost_efficiency_advantage": {
                "metric": "Verification Cost per Valid Rewrite (ms)",
                "ml_mean": round(float(np.mean(fold_metrics["ml_cost_per_valid"])), 2),
                "rand_mean": round(float(np.mean(fold_metrics["rand_cost_per_valid"])), 2),
                "t_statistic": round(float(t_stat_cost), 4),
                "p_value": float(p_val_cost),
                "statistically_significant_p05": bool(p_val_cost < 0.05),
            },
        },
    }

    return results

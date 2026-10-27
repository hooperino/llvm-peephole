#!/usr/bin/env python3
"""
run_model_comparison.py — Multi-model benchmark and probability calibration suite.

Compares:
  1. Logistic Regression (Standard)
  2. Logistic Regression (Platt Calibrated)
  3. Random Forest (Standard)
  4. Random Forest (Platt Calibrated)
  5. Gradient Boosting (Calibrated)

Produces:
  - results/model_comparison.csv (Statistical comparison table)
  - results/plots/multi_model_roc.png (Comparative ROC curves)
  - results/plots/multi_model_calibration.png (Comparative Reliability diagrams)
  - results/plots/feature_importance.png (Relative importance of IR features)
"""

import argparse
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    brier_score_loss,
    roc_curve,
)
from sklearn.calibration import calibration_curve

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
from confidence_pipeline.evaluate import compute_ece


def benchmark_models(csv_path: Path):
    print(f"[benchmark] Loading dataset from: {csv_path}")
    df = load_and_validate(csv_path)

    X = df[FEATURE_COLS]
    y = df[LABEL_COL]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=SPLIT_SEED, stratify=y
    )
    print(f"[benchmark] Split: {len(X_train)} train / {len(X_test)} test (seed={SPLIT_SEED})")

    models_to_test = [
        ("Logistic Regression", "logistic_regression", False),
        ("Logistic Regression (Calibrated)", "logistic_regression", True),
        ("Random Forest", "random_forest", False),
        ("Random Forest (Calibrated)", "random_forest", True),
        ("Gradient Boosting (Calibrated)", "gradient_boosting", True),
    ]

    records = []
    roc_data = {}
    calib_data = {}

    for display_name, mtype, calibrate in models_to_test:
        print(f"[benchmark] Training & evaluating: {display_name}...")
        pipe = build_pipeline(model_type=mtype, calibrate=calibrate, calibration_method="sigmoid")
        pipe.fit(X_train, y_train)

        # Measure inference latency
        t0 = time.perf_counter()
        proba = pipe.predict_proba(X_test)[:, 1]
        inference_time_us = ((time.perf_counter() - t0) / len(X_test)) * 1_000_000

        pred = (proba >= 0.5).astype(int)

        acc = accuracy_score(y_test, pred)
        prec = precision_score(y_test, pred, zero_division=0)
        rec = recall_score(y_test, pred, zero_division=0)
        f1 = f1_score(y_test, pred, zero_division=0)
        auc = roc_auc_score(y_test, proba)
        brier = brier_score_loss(y_test, proba)
        ece = compute_ece(y_test.values, proba, n_bins=10)

        records.append({
            "Model": display_name,
            "Accuracy": round(acc, 4),
            "Precision": round(prec, 4),
            "Recall": round(rec, 4),
            "F1-Score": round(f1, 4),
            "ROC-AUC": round(auc, 4),
            "Brier Score": round(brier, 4),
            "ECE": round(ece, 4),
            "Latency (us/sample)": round(inference_time_us, 2),
        })

        # Save for plots
        fpr, tpr, _ = roc_curve(y_test, proba)
        roc_data[display_name] = (fpr, tpr, auc)

        prob_true, prob_pred = calibration_curve(y_test, proba, n_bins=8)
        calib_data[display_name] = (prob_pred, prob_true, ece)

    summary_df = pd.DataFrame(records)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    out_csv = RESULTS_DIR / "model_comparison.csv"
    summary_df.to_csv(out_csv, index=False)
    print(f"\n[benchmark] Saved comparison table → {out_csv}")

    # Plot 1: Comparative ROC
    plt.figure(figsize=(7, 6))
    for name, (fpr, tpr, auc) in roc_data.items():
        plt.plot(fpr, tpr, linewidth=1.5, label=f"{name} (AUC={auc:.3f})")
    plt.plot([0, 1], [0, 1], "k--", linewidth=0.8, label="Chance (AUC=0.50)")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("Comparative ROC Curves — Real LLVM Candidates")
    plt.legend(loc="lower right", fontsize=8)
    plt.tight_layout()
    roc_plot = PLOTS_DIR / "multi_model_roc.png"
    plt.savefig(roc_plot, dpi=130)
    plt.close()
    print(f"[benchmark] Saved plot → {roc_plot}")

    # Plot 2: Comparative Reliability Diagrams (Calibration)
    plt.figure(figsize=(7, 6))
    for name, (prob_pred, prob_true, ece) in calib_data.items():
        plt.plot(prob_pred, prob_true, marker="o", linewidth=1.5, label=f"{name} (ECE={ece:.3f})")
    plt.plot([0, 1], [0, 1], "k--", linewidth=0.8, label="Ideal Calibration")
    plt.xlabel("Mean Predicted Confidence")
    plt.ylabel("Observed Empirical Verifiability")
    plt.title("Reliability Diagrams (Probability Calibration)")
    plt.legend(loc="lower right", fontsize=8)
    plt.tight_layout()
    calib_plot = PLOTS_DIR / "multi_model_calibration.png"
    plt.savefig(calib_plot, dpi=130)
    plt.close()
    print(f"[benchmark] Saved plot → {calib_plot}")

    # Plot 3: Feature Importance Analysis (using Random Forest)
    print("[benchmark] Computing feature importances via Random Forest...")
    rf_pipe = build_pipeline(model_type="random_forest", calibrate=False)
    rf_pipe.fit(X_train, y_train)

    preprocessor = rf_pipe.named_steps["preprocessor"]
    rf_clf = rf_pipe.named_steps["classifier"]

    # Use get_feature_names_out from ColumnTransformer
    raw_feature_names = preprocessor.get_feature_names_out()
    cleaned_feature_names = [f.replace("num__", "").replace("cat__", "").replace("bool__", "") for f in raw_feature_names]

    importances = rf_clf.feature_importances_
    feat_df = pd.DataFrame({"Feature": cleaned_feature_names, "Importance": importances}).sort_values("Importance", ascending=True)

    plt.figure(figsize=(8, 7))
    plt.barh(feat_df["Feature"], feat_df["Importance"], color="teal", alpha=0.85)
    plt.xlabel("Feature Importance (Gini Impurity Reduction)")
    plt.title("LLVM IR Feature Importance for Verifiability Prediction")
    plt.tight_layout()
    feat_plot = PLOTS_DIR / "feature_importance.png"
    plt.savefig(feat_plot, dpi=130)
    plt.close()
    print(f"[benchmark] Saved plot → {feat_plot}")

    # Print terminal markdown table
    print("\n" + "=" * 90)
    print("                    STATISTICAL MODEL COMPARISON (TEST SET)")
    print("=" * 90)
    print(summary_df.to_string(index=False))
    print("=" * 90 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Multi-model benchmark & calibration evaluation.")
    parser.add_argument(
        "--input",
        type=str,
        default="data/real_candidates.csv",
        help="Input candidate dataset CSV (default: data/real_candidates.csv)",
    )
    args = parser.parse_args()

    project_root = _src.parent
    in_path = project_root / args.input if not Path(args.input).is_absolute() else Path(args.input)

    benchmark_models(in_path)


if __name__ == "__main__":
    main()

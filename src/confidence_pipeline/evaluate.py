"""
evaluate.py — Evaluation and reporting for the confidence pipeline.

Computes:
  - Accuracy, Precision, Recall, F1
  - Confusion matrix
  - ROC-AUC
  - Brier score (probability calibration)
  - High / Low confidence distribution

Saves:
  - results/metrics.json        (machine-readable)
  - results/evaluation_report.txt (human-readable summary)
  - results/plots/confusion_matrix.png
  - results/plots/roc_curve.png
  - results/plots/confidence_distribution.png

NOTE: All metrics are computed on the held-out TEST set, never on training data.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")   # non-interactive backend for headless WSL
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
    brier_score_loss,
    ConfusionMatrixDisplay,
    RocCurveDisplay,
)

from confidence_pipeline.config import (
    RESULTS_DIR,
    PLOTS_DIR,
    METRICS_JSON,
    REPORT_TXT,
    CONFIDENCE_THRESHOLD,
    POSITIVE_CLASS,
    POSITIVE_CLASS_LABEL,
    NEGATIVE_CLASS_LABEL,
)


def evaluate(
    y_true: np.ndarray | pd.Series,
    y_pred: np.ndarray | pd.Series,
    confidence_scores: np.ndarray | pd.Series,
    threshold: float = CONFIDENCE_THRESHOLD,
    model_name: str = "Logistic Regression",
    save: bool = True,
) -> dict:
    """
    Evaluate model predictions and save reports / plots.

    Parameters
    ----------
    y_true:
        Ground-truth labels (0 or 1) from the test split.
    y_pred:
        Predicted class labels.
    confidence_scores:
        P(label=1) for each test sample.
    threshold:
        Threshold used to assign High / Low categories.
    model_name:
        Human-readable model name for reports.
    save:
        If True, write metrics, report, and plots to disk.

    Returns
    -------
    dict
        All computed metrics in a flat dictionary.
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    confidence_scores = np.asarray(confidence_scores)

    # ── Core metrics ──────────────────────────────────────────────────
    acc    = accuracy_score(y_true, y_pred)
    report = classification_report(
        y_true, y_pred,
        target_names=[NEGATIVE_CLASS_LABEL, POSITIVE_CLASS_LABEL],
        output_dict=True,
    )
    cm = confusion_matrix(y_true, y_pred)

    roc_auc = None
    brier   = None
    try:
        roc_auc = roc_auc_score(y_true, confidence_scores)
        brier   = brier_score_loss(y_true, confidence_scores)
    except ValueError as exc:
        print(f"[evaluate] WARNING: Could not compute ROC-AUC / Brier: {exc}")

    # ── Confidence-category counts ────────────────────────────────────
    high_count = int((confidence_scores >= threshold).sum())
    low_count  = int((confidence_scores <  threshold).sum())
    total      = len(confidence_scores)

    # ── Assemble metrics dict ─────────────────────────────────────────
    metrics = {
        "model":           model_name,
        "threshold":       threshold,
        "n_test_samples":  total,
        "accuracy":        round(acc, 4),
        "precision_pos":   round(report[POSITIVE_CLASS_LABEL]["precision"], 4),
        "recall_pos":      round(report[POSITIVE_CLASS_LABEL]["recall"],    4),
        "f1_pos":          round(report[POSITIVE_CLASS_LABEL]["f1-score"],  4),
        "precision_neg":   round(report[NEGATIVE_CLASS_LABEL]["precision"], 4),
        "recall_neg":      round(report[NEGATIVE_CLASS_LABEL]["recall"],    4),
        "f1_neg":          round(report[NEGATIVE_CLASS_LABEL]["f1-score"],  4),
        "roc_auc":         round(roc_auc, 4) if roc_auc is not None else None,
        "brier_score":     round(brier,   4) if brier   is not None else None,
        "high_confidence_count": high_count,
        "low_confidence_count":  low_count,
        "confusion_matrix": cm.tolist(),
        "label_semantics": {
            "positive_class": POSITIVE_CLASS,
            "positive_label": POSITIVE_CLASS_LABEL,
            "negative_label": NEGATIVE_CLASS_LABEL,
            "note": (
                "Labels are SYNTHETIC simulation targets. "
                "A positive label does NOT mean Alive2 verified the transformation."
            ),
        },
    }

    if save:
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        PLOTS_DIR.mkdir(parents=True, exist_ok=True)
        _save_metrics_json(metrics)
        _save_report_txt(metrics, report, cm, model_name, threshold)
        _plot_confusion_matrix(cm, model_name)
        if roc_auc is not None:
            _plot_roc_curve(y_true, confidence_scores, roc_auc, model_name)
        _plot_confidence_distribution(confidence_scores, threshold)

    return metrics


def _save_metrics_json(metrics: dict) -> None:
    with open(METRICS_JSON, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"[evaluate] Metrics saved → {METRICS_JSON}")


def _save_report_txt(
    metrics: dict,
    report: dict,
    cm: np.ndarray,
    model_name: str,
    threshold: float,
) -> None:
    lines = [
        "=" * 70,
        "  CONFIDENCE PIPELINE — EVALUATION REPORT",
        f"  Model   : {model_name}",
        f"  Dataset : SYNTHETIC (not validated by Alive2)",
        f"  Threshold: {threshold}  (baseline; not scientifically optimised)",
        "=" * 70,
        "",
        "── Core Metrics (held-out test set) ─────────────────────────────",
        f"  Accuracy  : {metrics['accuracy']:.4f}",
        f"  ROC-AUC   : {metrics['roc_auc']}",
        f"  Brier score (calibration): {metrics['brier_score']}",
        "",
        f"  Positive class ({POSITIVE_CLASS_LABEL}):",
        f"    Precision : {metrics['precision_pos']:.4f}",
        f"    Recall    : {metrics['recall_pos']:.4f}",
        f"    F1        : {metrics['f1_pos']:.4f}",
        "",
        f"  Negative class ({NEGATIVE_CLASS_LABEL}):",
        f"    Precision : {metrics['precision_neg']:.4f}",
        f"    Recall    : {metrics['recall_neg']:.4f}",
        f"    F1        : {metrics['f1_neg']:.4f}",
        "",
        "── Confusion Matrix ──────────────────────────────────────────────",
        "  Rows = True label, Columns = Predicted label",
        f"  {cm}",
        "",
        "── Confidence-Category Counts ────────────────────────────────────",
        f"  High confidence (score >= {threshold}): {metrics['high_confidence_count']}",
        f"  Low  confidence (score <  {threshold}): {metrics['low_confidence_count']}",
        "",
        "── Disclaimer ────────────────────────────────────────────────────",
        "  All results are based on a SYNTHETIC dataset generated for",
        "  pipeline development (25% milestone).  Labels are simulation",
        "  targets, NOT formal verification outcomes from Alive2.",
        "  Reported metrics will change when Person 1 supplies real",
        "  LLVM peephole optimization candidates with verified labels.",
        "=" * 70,
    ]
    with open(REPORT_TXT, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[evaluate] Report saved → {REPORT_TXT}")


def _plot_confusion_matrix(cm: np.ndarray, model_name: str) -> None:
    fig, ax = plt.subplots(figsize=(5, 4))
    disp = ConfusionMatrixDisplay(
        confusion_matrix=cm,
        display_labels=[NEGATIVE_CLASS_LABEL[:6], POSITIVE_CLASS_LABEL[:6]],
    )
    disp.plot(ax=ax, colorbar=False, cmap="Blues")
    ax.set_title(f"Confusion Matrix — {model_name}\n(synthetic data, 25% milestone)")
    plt.tight_layout()
    path = PLOTS_DIR / "confusion_matrix.png"
    plt.savefig(path, dpi=120)
    plt.close()
    print(f"[evaluate] Plot saved → {path}")


def _plot_roc_curve(
    y_true: np.ndarray,
    scores: np.ndarray,
    auc: float,
    model_name: str,
) -> None:
    fig, ax = plt.subplots(figsize=(5, 4))
    RocCurveDisplay.from_predictions(y_true, scores, ax=ax, name=model_name)
    ax.plot([0, 1], [0, 1], "k--", linewidth=0.8, label="Random (AUC=0.50)")
    ax.set_title(f"ROC Curve (AUC={auc:.3f})\n(synthetic data, 25% milestone)")
    ax.legend(fontsize=8)
    plt.tight_layout()
    path = PLOTS_DIR / "roc_curve.png"
    plt.savefig(path, dpi=120)
    plt.close()
    print(f"[evaluate] Plot saved → {path}")


def _plot_confidence_distribution(
    scores: np.ndarray,
    threshold: float,
) -> None:
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(scores, bins=30, color="steelblue", edgecolor="white", alpha=0.85)
    ax.axvline(threshold, color="crimson", linestyle="--", linewidth=1.5,
               label=f"Threshold = {threshold}")
    ax.set_xlabel("Confidence Score  P(label=1)")
    ax.set_ylabel("Number of candidates")
    ax.set_title("Confidence Score Distribution\n(synthetic data, 25% milestone)")
    ax.legend()
    plt.tight_layout()
    path = PLOTS_DIR / "confidence_distribution.png"
    plt.savefig(path, dpi=120)
    plt.close()
    print(f"[evaluate] Plot saved → {path}")


def print_terminal_summary(
    metrics: dict,
    n_total: int,
    n_train: int,
    n_test: int,
    model_name: str,
    threshold: float,
) -> None:
    """Print the concise terminal summary required by the spec."""
    width = 68

    def row(text: str) -> str:
        return f"║  {text:<{width - 4}}  ║"

    roc_str = f"{metrics['roc_auc']:.4f}" if metrics['roc_auc'] is not None else "N/A"
    brier_str = f"{metrics['brier_score']:.4f}" if metrics['brier_score'] is not None else "N/A"

    lines = [
        "",
        "╔" + "═" * width + "╗",
        row("CONFIDENCE PIPELINE — 25% MILESTONE SUMMARY"),
        "╠" + "═" * width + "╣",
        row(f"Dataset         : SYNTHETIC ({n_total} records)"),
        row(f"Train / Test    : {n_train} / {n_test}"),
        row(f"Model           : {model_name}"),
        row(f"Threshold       : {threshold}"),
        "╠" + "═" * width + "╣",
        row(f"Accuracy        : {metrics['accuracy']:.4f}"),
        row(f"Precision (pos) : {metrics['precision_pos']:.4f}"),
        row(f"Recall    (pos) : {metrics['recall_pos']:.4f}"),
        row(f"F1-score  (pos) : {metrics['f1_pos']:.4f}"),
        row(f"ROC-AUC         : {roc_str}"),
        row(f"Brier score     : {brier_str}"),
        "╠" + "═" * width + "╣",
        row(f"High confidence : {metrics['high_confidence_count']}"),
        row(f"Low  confidence : {metrics['low_confidence_count']}"),
        "╠" + "═" * width + "╣",
        row("NOTE: Synthetic data only. Labels are simulation targets."),
        row("NOT validated by Alive2. See results/evaluation_report.txt"),
        "╚" + "═" * width + "╝",
        "",
    ]
    print("\n".join(lines))


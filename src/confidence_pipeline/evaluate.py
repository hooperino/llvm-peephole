"""
evaluate.py — Evaluation and reporting for the confidence pipeline.

Computes:
  - Accuracy, Precision, Recall, F1
  - Confusion matrix
  - ROC-AUC
  - Brier score (probability calibration loss)
  - Expected Calibration Error (ECE)
  - High / Low confidence distribution

Saves:
  - results/metrics.json        (machine-readable)
  - results/evaluation_report.txt (human-readable summary)
  - results/plots/confusion_matrix.png
  - results/plots/roc_curve.png
  - results/plots/confidence_distribution.png
  - results/plots/calibration_curve.png

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
from sklearn.calibration import calibration_curve

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


def compute_ece(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    """Compute Expected Calibration Error (ECE)."""
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    bin_indices = np.clip(np.digitize(y_prob, bins) - 1, 0, n_bins - 1)
    ece = 0.0
    n = len(y_true)
    for b in range(n_bins):
        mask = (bin_indices == b)
        if np.any(mask):
            bin_acc = np.mean(y_true[mask])
            bin_conf = np.mean(y_prob[mask])
            ece += (np.sum(mask) / n) * np.abs(bin_acc - bin_conf)
    return float(ece)


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
    ece     = None
    try:
        roc_auc = roc_auc_score(y_true, confidence_scores)
        brier   = brier_score_loss(y_true, confidence_scores)
        ece     = compute_ece(y_true, confidence_scores, n_bins=10)
    except ValueError as exc:
        print(f"[evaluate] WARNING: Could not compute ROC-AUC / Brier / ECE: {exc}")

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
        "ece":             round(ece,     4) if ece     is not None else None,
        "high_confidence_count": high_count,
        "low_confidence_count":  low_count,
        "confusion_matrix": cm.tolist(),
        "label_semantics": {
            "positive_class": POSITIVE_CLASS,
            "positive_label": POSITIVE_CLASS_LABEL,
            "negative_label": NEGATIVE_CLASS_LABEL,
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
        if ece is not None:
            _plot_calibration_curve(y_true, confidence_scores, ece, model_name)

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
        f"  Model    : {model_name}",
        f"  Threshold: {threshold}",
        "=" * 70,
        "",
        "── Core Metrics (held-out test set) ─────────────────────────────",
        f"  Accuracy  : {metrics['accuracy']:.4f}",
        f"  ROC-AUC   : {metrics['roc_auc']}",
        f"  Brier score (loss): {metrics['brier_score']}",
        f"  Expected Calibration Error (ECE): {metrics['ece']}",
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
        "── Confusion Matrix ─────────────────────────────────────────────",
        f"  [[TN={cm[0,0]:4d},  FP={cm[0,1]:4d}],",
        f"   [FN={cm[1,0]:4d},  TP={cm[1,1]:4d}]]",
        "",
        "── Confidence Gating (threshold = {threshold}) ──────────────────",
        f"  High confidence (prioritised for Alive2) : {metrics['high_confidence_count']}",
        f"  Low  confidence (skipped / deferred)     : {metrics['low_confidence_count']}",
        "",
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
    ax.set_title(f"Confusion Matrix — {model_name}")
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
    ax.set_title(f"ROC Curve (AUC={auc:.3f}) — {model_name}")
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
    ax.set_xlabel("Confidence Score  P(verified=1)")
    ax.set_ylabel("Number of candidates")
    ax.set_title("Confidence Score Distribution")
    ax.legend()
    plt.tight_layout()
    path = PLOTS_DIR / "confidence_distribution.png"
    plt.savefig(path, dpi=120)
    plt.close()
    print(f"[evaluate] Plot saved → {path}")


def _plot_calibration_curve(
    y_true: np.ndarray,
    scores: np.ndarray,
    ece: float,
    model_name: str,
) -> None:
    """Plot reliability diagram (calibration curve)."""
    fig, ax = plt.subplots(figsize=(5, 4))
    prob_true, prob_pred = calibration_curve(y_true, scores, n_bins=10)

    ax.plot(prob_pred, prob_true, marker="o", linewidth=1.5, label=f"{model_name} (ECE={ece:.3f})")
    ax.plot([0, 1], [0, 1], "k--", linewidth=0.8, label="Perfect Calibration")

    ax.set_xlabel("Mean Predicted Confidence")
    ax.set_ylabel("Fraction of Truly Verified")
    ax.set_title(f"Reliability Diagram (Calibration)")
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.0])
    ax.legend(fontsize=8, loc="lower right")
    plt.tight_layout()
    path = PLOTS_DIR / "calibration_curve.png"
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
    ece_str = f"{metrics['ece']:.4f}" if metrics['ece'] is not None else "N/A"

    lines = [
        "",
        "╔" + "═" * width + "╗",
        row("CONFIDENCE PIPELINE — EVALUATION SUMMARY"),
        "╠" + "═" * width + "╣",
        row(f"Dataset         : {n_total} records"),
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
        row(f"ECE (Calib. Err): {ece_str}"),
        "╠" + "═" * width + "╣",
        row(f"High confidence : {metrics['high_confidence_count']}"),
        row(f"Low  confidence : {metrics['low_confidence_count']}"),
        "╚" + "═" * width + "╝",
        "",
    ]
    print("\n".join(lines))

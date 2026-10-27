#!/usr/bin/env python3
"""
run_pipeline.py — Command-line entry point for the confidence pipeline.

Usage:
  python src/run_pipeline.py train --input data/real_candidates.csv --model random_forest --calibrate
  python src/run_pipeline.py evaluate --input data/real_candidates.csv
  python src/run_pipeline.py predict --input data/real_candidates.csv
  python src/run_pipeline.py all --input data/real_candidates.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# ── Ensure src/ is on the path when invoked from project root
_src = Path(__file__).resolve().parent
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from confidence_pipeline.config import (
    SYNTHETIC_CSV,
    REAL_CANDIDATES_CSV,
    MODEL_PATH,
    PREDICTIONS_CSV,
    CONFIDENCE_THRESHOLD,
)


def get_default_csv() -> Path:
    """Return REAL_CANDIDATES_CSV if it exists, otherwise SYNTHETIC_CSV."""
    if REAL_CANDIDATES_CSV.exists():
        return REAL_CANDIDATES_CSV
    return SYNTHETIC_CSV


def cmd_generate(args: argparse.Namespace) -> None:
    from confidence_pipeline.data_generation import generate_synthetic_dataset
    df = generate_synthetic_dataset()
    from confidence_pipeline.config import LABEL_COL
    counts = df[LABEL_COL].value_counts()
    print(f"Label distribution: {counts.to_dict()}")


def cmd_train(args: argparse.Namespace) -> None:
    from confidence_pipeline.data_loader import load_and_validate
    from confidence_pipeline.train import train

    csv_path = Path(args.input) if args.input else get_default_csv()
    df = load_and_validate(csv_path)
    train(df, model_type=args.model, calibrate=args.calibrate)


def cmd_evaluate(args: argparse.Namespace) -> None:
    from confidence_pipeline.data_loader import load_and_validate, split_features_labels
    from confidence_pipeline.train import train, load_model
    from confidence_pipeline.predict import score_candidates, save_predictions, print_sample_predictions
    from confidence_pipeline.evaluate import evaluate, print_terminal_summary
    from confidence_pipeline.config import (
        LABEL_COL, ID_COL, FEATURE_COLS, TEST_SIZE, SPLIT_SEED
    )
    from sklearn.model_selection import train_test_split
    import numpy as np

    csv_path = Path(args.input) if args.input else get_default_csv()
    df = load_and_validate(csv_path)

    # Re-create the same train/test split used during training
    X = df[FEATURE_COLS]
    y = df[LABEL_COL]
    _, X_test, _, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=SPLIT_SEED, stratify=y
    )
    test_df = df.loc[X_test.index].copy()

    pipeline = load_model(MODEL_PATH)
    threshold = args.threshold

    predictions = score_candidates(test_df, pipeline, threshold=threshold)
    save_predictions(predictions, original_df=test_df)
    print_sample_predictions(predictions, threshold=threshold)

    metrics = evaluate(
        y_true=predictions["true_label"],
        y_pred=predictions["predicted_label"],
        confidence_scores=predictions["confidence_score"],
        threshold=threshold,
        model_name=args.model,
        save=True,
    )

    n_total = len(df)
    n_train = n_total - len(test_df)
    n_test = len(test_df)

    print_terminal_summary(
        metrics=metrics,
        n_total=n_total,
        n_train=n_train,
        n_test=n_test,
        model_name=args.model,
        threshold=threshold,
    )


def cmd_predict(args: argparse.Namespace) -> None:
    from confidence_pipeline.data_loader import load_and_validate
    from confidence_pipeline.train import load_model
    from confidence_pipeline.predict import (
        score_candidates,
        save_predictions,
        print_sample_predictions,
    )

    if not args.input:
        print("Error: --input PATH is required for predict mode.")
        sys.exit(1)

    csv_path = Path(args.input)
    df = load_and_validate(csv_path, require_labels=False)

    pipeline = load_model(MODEL_PATH)
    output_path = Path(args.output) if args.output else PREDICTIONS_CSV

    predictions = score_candidates(df, pipeline, threshold=args.threshold)
    save_predictions(predictions, output_path=output_path, original_df=df)
    print_sample_predictions(predictions, threshold=args.threshold)


def cmd_all(args: argparse.Namespace) -> None:
    # Train
    cmd_train(args)
    # Evaluate
    cmd_evaluate(args)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Confidence Pipeline for LLVM Peephole Optimization Verification",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--model",
        choices=["logistic_regression", "random_forest", "gradient_boosting"],
        default="logistic_regression",
        help="ML model to use (default: logistic_regression)",
    )
    common.add_argument(
        "--calibrate",
        action="store_true",
        default=False,
        help="Apply probability calibration (Platt scaling)",
    )
    common.add_argument(
        "--threshold",
        type=float,
        default=CONFIDENCE_THRESHOLD,
        help=f"Confidence threshold for High/Low split (default: {CONFIDENCE_THRESHOLD})",
    )
    common.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to input candidate CSV",
    )
    common.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to write predictions CSV",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("generate",  parents=[common], help="Generate synthetic dataset")
    subparsers.add_parser("train",     parents=[common], help="Train the ML model")
    subparsers.add_parser("evaluate",  parents=[common], help="Evaluate on test set")
    subparsers.add_parser("predict",   parents=[common], help="Score a new candidate CSV")
    subparsers.add_parser("all",       parents=[common], help="Train → Evaluate")

    args = parser.parse_args()

    dispatch = {
        "generate": cmd_generate,
        "train":    cmd_train,
        "evaluate": cmd_evaluate,
        "predict":  cmd_predict,
        "all":      cmd_all,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()

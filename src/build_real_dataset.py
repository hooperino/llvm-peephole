#!/usr/bin/env python3
"""Build real candidate dataset by running Alive2 verification and IR feature extraction."""

import argparse
import sys
import time
import pandas as pd
from pathlib import Path

# Add src/ to path
_src = Path(__file__).resolve().parent
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from verification.alive_runner import AliveRunner
from feature_extraction.extractor import IRFeatureExtractor


def main():
    parser = argparse.ArgumentParser(description="Extract IR features and verify candidates with Alive2.")
    parser.add_argument(
        "--manifest",
        type=str,
        default="data/candidates_manifest.csv",
        help="Path to candidate manifest CSV (default: data/candidates_manifest.csv)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/real_candidates.csv",
        help="Output CSV path (default: data/real_candidates.csv)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of concurrent workers for Alive2 verification (default: 4)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of candidates to process (default: all)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Timeout in seconds for each Alive2 verification query (default: 30.0)",
    )

    args = parser.parse_args()

    project_root = _src.parent
    manifest_path = project_root / args.manifest
    output_path = project_root / args.output

    if not manifest_path.exists():
        print(f"Error: Manifest not found at {manifest_path}")
        print("Run `python src/generate_real_candidates.py` first to generate candidates.")
        sys.exit(1)

    print(f"[dataset_builder] Loading manifest from {manifest_path}...")
    manifest_df = pd.read_csv(manifest_path)
    if args.limit and args.limit > 0:
        manifest_df = manifest_df.head(args.limit)

    total_candidates = len(manifest_df)
    print(f"[dataset_builder] Processing {total_candidates} candidates...")

    # 1. Feature Extraction
    print("[dataset_builder] Extracting static LLVM IR features...")
    extractor = IRFeatureExtractor()
    feature_rows = []

    file_paths = []
    cids = []

    for _, row in manifest_df.iterrows():
        cid = str(row["candidate_id"])
        fpath = Path(row["file_path"])
        if not fpath.is_absolute():
            fpath = project_root / fpath

        file_paths.append(fpath)
        cids.append(cid)

        feats = extractor.extract_features_from_file(fpath, candidate_id=cid)
        feature_rows.append(feats)

    features_df = pd.DataFrame(feature_rows)
    print(f"[dataset_builder] Extracted features for {len(features_df)} candidates.")

    # 2. Formal Verification via Alive2
    print(f"[dataset_builder] Running formal verification via Alive2 (workers={args.workers}, timeout={args.timeout}s)...")
    runner = AliveRunner()
    start_time = time.perf_counter()

    alive_results = runner.batch_verify(
        file_paths=file_paths,
        candidate_ids=cids,
        max_workers=args.workers,
        timeout=args.timeout,
    )
    total_verify_time = time.perf_counter() - start_time
    print(f"[dataset_builder] Finished batch verification in {total_verify_time:.2f}s.")

    # 3. Merge Results
    verif_records = [res.to_dict() for res in alive_results]
    verif_df = pd.DataFrame(verif_records)

    # Rename 'verified' -> 'label' for standard pipeline compatibility
    verif_df["label"] = verif_df["verified"]

    merged_df = pd.merge(features_df, verif_df[["candidate_id", "label", "verification_time_ms", "status"]], on="candidate_id")

    # Save to disk
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged_df.to_csv(output_path, index=False)
    print(f"[dataset_builder] Saved curated dataset to {output_path} ({len(merged_df)} records).")

    # 4. Summary Statistics
    n_verified = (merged_df["label"] == 1).sum()
    n_failed = (merged_df["label"] == 0).sum()
    pct_verified = (n_verified / len(merged_df)) * 100
    mean_ms = merged_df["verification_time_ms"].mean()
    median_ms = merged_df["verification_time_ms"].median()
    p95_ms = merged_df["verification_time_ms"].quantile(0.95)

    print("\n" + "=" * 60)
    print("  PHASE 2: REAL DATASET CURATION SUMMARY")
    print("=" * 60)
    print(f"  Total Candidates Processed : {len(merged_df)}")
    print(f"  Alive2 Verified (label=1)  : {n_verified} ({pct_verified:.1f}%)")
    print(f"  Alive2 Failed   (label=0)  : {n_failed} ({100 - pct_verified:.1f}%)")
    print("-" * 60)
    print("  SMT Solver Latency Statistics:")
    print(f"    - Mean Latency           : {mean_ms:.2f} ms")
    print(f"    - Median Latency         : {median_ms:.2f} ms")
    print(f"    - 95th Percentile        : {p95_ms:.2f} ms")
    print(f"    - Total Wall-Clock Time  : {total_verify_time:.2f} s")
    print("-" * 60)
    print("  Opcode Category Distribution:")
    for cat, count in merged_df["src_opcode_category"].value_counts().items():
        print(f"    - {cat:<22} : {count}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()

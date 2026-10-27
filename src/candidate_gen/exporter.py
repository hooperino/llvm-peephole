"""Exporter for saving generated LLVM peephole candidates to disk."""

import csv
from pathlib import Path
from typing import List, Tuple
from .models import PeepholeCandidate


def export_candidates_to_disk(
    candidates: List[PeepholeCandidate],
    output_dir: Path,
    manifest_path: Path,
) -> Tuple[int, Path]:
    """Export candidates as individual .ll files and create a manifest CSV.

    Args:
        candidates: List of PeepholeCandidate instances.
        output_dir: Directory where .ll files will be written.
        manifest_path: CSV file path to record the candidate manifest.

    Returns:
        Tuple of (count_exported, manifest_path).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    manifest_rows = []

    for cand in candidates:
        ll_filename = f"{cand.candidate_id}.ll"
        ll_file_path = output_dir / ll_filename

        # Write .ll file
        with open(ll_file_path, "w", encoding="utf-8") as f:
            f.write(cand.to_llvm_module())

        manifest_rows.append({
            "candidate_id": cand.candidate_id,
            "name": cand.name,
            "category": cand.category,
            "bitwidth": cand.bitwidth,
            "intended_sound": int(cand.intended_sound),
            "mutation_rule": cand.mutation_rule,
            "file_path": str(ll_file_path),
            "description": cand.description,
        })

    # Write manifest CSV
    fieldnames = [
        "candidate_id",
        "name",
        "category",
        "bitwidth",
        "intended_sound",
        "mutation_rule",
        "file_path",
        "description",
    ]

    with open(manifest_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(manifest_rows)

    return len(candidates), manifest_path

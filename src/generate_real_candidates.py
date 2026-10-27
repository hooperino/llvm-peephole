#!/usr/bin/env python3
"""Script to extract LLVM peephole candidates from input source code and save to disk."""

import argparse
import sys
from pathlib import Path

# Add src to path
_src = Path(__file__).resolve().parent
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from candidate_gen.generator import CandidateGenerator
from candidate_gen.ir_extractor import IRExtractor
from candidate_gen.exporter import export_candidates_to_disk


def main():
    parser = argparse.ArgumentParser(description="Generate/Extract LLVM peephole candidates from input code.")
    parser.add_argument(
        "--input-code",
        type=str,
        default="data/input_code.txt",
        help="Path to input source code file (.txt, .ll, or .c) to extract candidates from",
    )
    parser.add_argument("--count", type=int, default=500, help="Number of candidates to generate (default: 500)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility (default: 42)")
    parser.add_argument("--sound-ratio", type=float, default=0.45, help="Ratio of intended sound candidates (default: 0.45)")
    parser.add_argument("--output-dir", type=str, default="data/candidates", help="Directory for candidate .ll files")
    parser.add_argument("--manifest", type=str, default="data/candidates_manifest.csv", help="Manifest CSV output path")

    args = parser.parse_args()

    project_root = _src.parent
    out_dir = project_root / args.output_dir
    manifest_path = project_root / args.manifest
    input_path = project_root / args.input_code if args.input_code else None

    if input_path and input_path.exists():
        print(f"[candidate_gen] Using custom input code from: {input_path}")
        extractor = IRExtractor(seed=args.seed)
        print(f"[candidate_gen] Loading / parsing IR from {input_path}...")
        ir_text = extractor.load_or_compile_ir(input_path)
        print(f"[candidate_gen] Extracting {args.count} candidates directly from input code instructions...")
        candidates = extractor.extract_candidates_from_ir(
            ir_text,
            max_candidates=args.count,
            sound_ratio=args.sound_ratio,
        )
    else:
        print(f"[candidate_gen] No custom input file provided or file not found. Falling back to synthetic pattern generation...")
        gen = CandidateGenerator(seed=args.seed)
        candidates = gen.generate_candidates(n_candidates=args.count, sound_ratio=args.sound_ratio)

    print(f"[candidate_gen] Exporting {len(candidates)} candidates to {out_dir}...")
    count, mpath = export_candidates_to_disk(candidates, out_dir, manifest_path)

    sound_count = sum(1 for c in candidates if c.intended_sound)
    unsound_count = count - sound_count

    print(f"[candidate_gen] Done! Exported {count} candidates derived from input code:")
    print(f"  - Sound:   {sound_count} ({sound_count/count*100:.1f}%)")
    print(f"  - Unsound: {unsound_count} ({unsound_count/count*100:.1f}%)")
    print(f"  - Manifest: {mpath}")


if __name__ == "__main__":
    main()

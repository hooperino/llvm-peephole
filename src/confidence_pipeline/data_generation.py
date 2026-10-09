"""
data_generation.py — Synthetic dataset generator for the 25% milestone.

PURPOSE
-------
This module generates a deterministic synthetic dataset of LLVM peephole
optimization candidates for use in pipeline development and testing.

IMPORTANT DISCLAIMERS
---------------------
- This dataset is SYNTHETIC.  Records do NOT represent real LLVM IR
  transformations and have NOT been validated by Alive2.
- Labels are assigned by an explicit simulation rule (documented below),
  NOT by formal verification.
- Do NOT interpret a positive label as a proof of semantic correctness.
- When Person 1 supplies a real candidate dataset, this module is
  superseded; the pipeline itself remains unchanged.

LABEL GENERATION RULE (simulation)
------------------------------------
A candidate is assigned label = 1 ("expected-verifiable") if ALL of:

  1. src_instr_count > tgt_instr_count   (optimisation reduces code)
  2. src_opcode_category in {"arithmetic", "bitwise", "comparison"}
  3. num_constants >= 1                   (constant-folding / identity ops)
  4. candidate_complexity <= 6.0

plus 15 % random positive-label noise is added (and 15 % negative-label
noise) to prevent any single feature from being a perfect predictor.

This rule is chosen to produce a plausible but imperfect dataset.
It is NOT a claim about which transformations Alive2 will verify.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from pathlib import Path

from confidence_pipeline.config import (
    SYNTHETIC_SEED,
    SYNTHETIC_N,
    SYNTHETIC_CSV,
    DATA_DIR,
    ID_COL,
    LABEL_COL,
)

# ── Opcode categories drawn from real LLVM IR instruction classes
OPCODE_CATEGORIES = [
    "arithmetic",   # add, sub, mul, sdiv, udiv
    "bitwise",      # and, or, xor, shl, lshr, ashr
    "comparison",   # icmp, fcmp
    "memory",       # load, store, alloca, getelementptr
    "control",      # br, ret, phi
    "conversion",   # zext, sext, trunc, bitcast
    "other",        # call, select, extractvalue, …
]

# Human-readable representative src → tgt templates per category
_SRC_TEMPLATES = {
    "arithmetic":  [
        "%r = add i32 %a, 0",
        "%r = sub i32 %a, 0",
        "%r = mul i32 %a, 1",
        "%r = add i32 %a, %b",
        "%r = sub i32 %a, %a",
    ],
    "bitwise": [
        "%r = and i32 %a, %a",
        "%r = or i32 %a, 0",
        "%r = xor i32 %a, 0",
        "%r = shl i32 %a, 0",
        "%r = lshr i32 %a, 0",
    ],
    "comparison": [
        "%r = icmp eq i32 %a, %a",
        "%r = icmp slt i32 %a, %a",
        "%r = icmp ne i32 %a, 0",
    ],
    "memory": [
        "%p = getelementptr i32, i32* %base, i32 0",
        "store i32 %v, i32* %p",
    ],
    "control": [
        "br i1 true, label %bb1, label %bb2",
        "ret i32 0",
    ],
    "conversion": [
        "%r = zext i1 %a to i32",
        "%r = trunc i64 %a to i32",
    ],
    "other": [
        "%r = select i1 true, i32 %a, i32 %b",
        "%r = call i32 @f(i32 %a)",
    ],
}
_TGT_TEMPLATES = {
    "arithmetic":  ["%r = %a", "%r = 0", "%r = add i32 %a, %b"],
    "bitwise":     ["%r = %a", "%r = 0"],
    "comparison":  ["%r = true", "%r = false", "%r = icmp ne i32 %a, 0"],
    "memory":      ["%p = %base"],
    "control":     ["br label %bb1", "ret i32 0"],
    "conversion":  ["%r = %a"],
    "other":       ["%r = %a", "%r = %b"],
}


def _pick(rng: np.random.Generator, items: list) -> object:
    return items[rng.integers(0, len(items))]


def generate_synthetic_dataset(
    n: int = SYNTHETIC_N,
    seed: int = SYNTHETIC_SEED,
    output_path: Path = SYNTHETIC_CSV,
    save: bool = True,
) -> pd.DataFrame:
    """
    Generate *n* synthetic peephole-optimization candidate records.

    Parameters
    ----------
    n:
        Number of records to generate.
    seed:
        Random seed (fixed for reproducibility).
    output_path:
        Where to save the CSV.  Ignored when *save* is False.
    save:
        Whether to write the CSV to disk.

    Returns
    -------
    pd.DataFrame
        The generated dataset.
    """
    rng = np.random.default_rng(seed)

    records = []
    for i in range(n):
        cid = f"cand_{i:04d}"

        src_cat = _pick(rng, OPCODE_CATEGORIES)
        tgt_cat = _pick(rng, OPCODE_CATEGORIES[:4])   # optimised tends to be simpler

        src_count = int(rng.integers(1, 8))
        # target usually ≤ source; can occasionally be equal or larger
        tgt_count = int(rng.integers(max(1, src_count - 3), src_count + 2))

        n_operands  = int(rng.integers(1, 5))
        n_constants = int(rng.integers(0, n_operands + 1))
        n_variables = n_operands - n_constants
        has_const   = bool(n_constants >= 1)
        count_diff  = bool(src_count != tgt_count)
        reduction   = src_count - tgt_count           # may be negative

        # complexity: weighted sum (arbitrary but plausible heuristic)
        complexity = round(
            0.5 * src_count + 0.3 * n_operands + 0.2 * abs(reduction), 2
        )

        src_repr = _pick(rng, _SRC_TEMPLATES[src_cat])
        tgt_repr = _pick(rng, _TGT_TEMPLATES.get(tgt_cat, _TGT_TEMPLATES["other"]))

        # ── Label simulation rule (see module docstring) ──────────────────
        base_positive = (
            src_count > tgt_count
            and src_cat in {"arithmetic", "bitwise", "comparison"}
            and n_constants >= 1
            and complexity <= 6.0
        )

        # Add 15 % label noise in each direction to prevent trivial datasets
        noise_val = rng.random()
        if base_positive:
            label = 0 if noise_val < 0.15 else 1
        else:
            label = 1 if noise_val < 0.15 else 0

        records.append({
            ID_COL:                   cid,
            "src_repr":               src_repr,
            "tgt_repr":               tgt_repr,
            "src_instr_count":        src_count,
            "tgt_instr_count":        tgt_count,
            "instr_count_reduction":  reduction,
            "src_opcode_category":    src_cat,
            "tgt_opcode_category":    tgt_cat,
            "num_operands":           n_operands,
            "num_constants":          n_constants,
            "num_variables":          n_variables,
            "has_constant_operand":   int(has_const),
            "instr_count_differs":    int(count_diff),
            "candidate_complexity":   complexity,
            LABEL_COL:                label,
        })

    df = pd.DataFrame(records)

    if save:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"[data_generation] Saved {len(df)} records → {output_path}")

    return df


if __name__ == "__main__":
    df = generate_synthetic_dataset()
    print(df.head())
    print(f"\nLabel distribution:\n{df[LABEL_COL].value_counts()}")

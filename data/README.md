# Data Directory

This directory holds candidate datasets for the confidence pipeline.

## Files

| File | Description | Status |
|---|---|---|
| `synthetic_candidates.csv` | Synthetic dataset for pipeline development | **SYNTHETIC — NOT real LLVM data** |

## Schema

Every candidate CSV (synthetic or real) must contain the following columns:

### Required columns

| Column | Type | Description |
|---|---|---|
| `candidate_id` | string | Unique identifier for each candidate |
| `src_instr_count` | int | Number of instructions in the source (original) form |
| `tgt_instr_count` | int | Number of instructions in the target (optimised) form |
| `instr_count_reduction` | int | `src_instr_count - tgt_instr_count` (positive = reduction) |
| `src_opcode_category` | string | Opcode category of the dominant source instruction |
| `tgt_opcode_category` | string | Opcode category of the dominant target instruction |
| `num_operands` | int | Total number of operands in the candidate |
| `num_constants` | int | Number of constant operands |
| `num_variables` | int | Number of variable (non-constant) operands |
| `has_constant_operand` | int (0/1) | 1 if at least one constant operand is present |
| `instr_count_differs` | int (0/1) | 1 if src and tgt instruction counts differ |
| `candidate_complexity` | float | Heuristic complexity measure |
| `label` | int (0/1) | Training target: 1 = expected-verifiable, 0 = not |

### Optional columns (not used as features)

| Column | Type | Description |
|---|---|---|
| `src_repr` | string | Human-readable source IR snippet |
| `tgt_repr` | string | Human-readable target IR snippet |

### Categorical value sets

`src_opcode_category` and `tgt_opcode_category` must be one of:
- `arithmetic`
- `bitwise`
- `comparison`
- `memory`
- `control`
- `conversion`
- `other`

Unseen categories at inference time are handled gracefully (mapped to an
all-zero one-hot vector).

## Label semantics

> **IMPORTANT:** The label column has different semantics depending on the data source.

### Synthetic dataset (current)
`label = 1` means the synthetic label-generation rule assigned this candidate
as "expected-verifiable". This is a simulation target defined in
`src/confidence_pipeline/data_generation.py`.  It does NOT mean Alive2
verified the transformation.

### Real dataset (Person 1 — future)
`label = 1` should indicate that Alive2 verified the transformation
(bounded translation validation — see project spec §9).  Candidates where
Alive2 could not be applied should be documented separately rather than
silently assigned a label.

## Missing value handling

- Numeric columns: median imputation (during preprocessing).
- Categorical columns: mode imputation (during preprocessing).
- If more than 20% of a feature column is missing, investigate before training.

## Replacing the synthetic dataset

To supply the real candidate dataset from Person 1:

1. Place the real CSV in this directory (e.g. `data/real_candidates.csv`).
2. Ensure the CSV follows the schema above.
3. Verify label semantics are aligned with Alive2 verification outcomes.
4. Run:
   ```
   python src/run_pipeline.py all --input data/real_candidates.csv
   ```

No source-code changes are required if the schema matches.

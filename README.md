# Confidence-Gated Machine Learning for Efficient LLVM Peephole Optimization Verification

**Type:** Compiler Design / Compiler Optimization / Machine Learning / Formal Verification  
**Scale:** BTech course project — 2-person team  
**Status:** 25% milestone — ML confidence pipeline (synthetic dataset)

---

## Project Overview

LLVM generates many peephole optimization candidates, but formally verifying
every one with [Alive2](https://github.com/AliveToolkit/alive2) is expensive.
This project explores a **confidence-gated selective verification** workflow:

```
LLVM IR input
    → Candidate generation
    → Feature extraction
    → Lightweight ML model (Logistic Regression)
    → Confidence score per candidate
    → Threshold gate
         → High confidence → Alive2 formal verification
         → Low confidence  → Skip / defer
    → Cost vs. retention evaluation
```

The central question is whether a lightweight ML model can reduce verification
workload while retaining most useful optimization opportunities.

---

## Repository Structure

```
llvm-peephole-project/
├── alive2/              # Alive2 formal verifier (built)
├── llvm-project/        # LLVM monorepo source
├── llvm-build/          # Compiled LLVM 21 toolchain
├── souper/              # Souper source (not used in current milestone)
├── .venv/               # Python 3.14 virtual environment
│
├── data/
│   ├── synthetic_candidates.csv   # Synthetic dataset (25% milestone)
│   └── README.md                  # Schema documentation
│
├── src/
│   ├── run_pipeline.py            # Main CLI entry point
│   └── confidence_pipeline/
│       ├── config.py              # All configuration / paths / seeds
│       ├── data_generation.py     # Synthetic dataset generator
│       ├── data_loader.py         # CSV loading + schema validation
│       ├── preprocessing.py       # sklearn ColumnTransformer
│       ├── train.py               # Model training + saving
│       ├── predict.py             # Confidence scoring
│       └── evaluate.py            # Metrics, plots, reports
│
├── models/
│   └── confidence_model.joblib    # Saved trained pipeline
│
├── results/
│   ├── predictions.csv            # Per-candidate scores
│   ├── metrics.json               # Machine-readable metrics
│   ├── evaluation_report.txt      # Human-readable report
│   └── plots/
│       ├── confusion_matrix.png
│       ├── roc_curve.png
│       └── confidence_distribution.png
│
├── tests/
│   └── test_pipeline.py           # pytest test suite
│
├── alive2-test.ll                 # Alive2 sanity-check IR
├── requirements.txt
└── README.md
```

---

## Quick Start

All commands run from the project root using the `.venv` Python interpreter.

### Full pipeline (generate → train → evaluate)

```bash
.venv/bin/python src/run_pipeline.py all
```

### Individual steps

```bash
# 1. Generate synthetic dataset
.venv/bin/python src/run_pipeline.py generate

# 2. Train the model
.venv/bin/python src/run_pipeline.py train

# 3. Evaluate on held-out test set
.venv/bin/python src/run_pipeline.py evaluate

# 4. Score a new candidate CSV using the saved model
.venv/bin/python src/run_pipeline.py predict --input data/my_candidates.csv
```

### Options

| Option | Default | Description |
|---|---|---|
| `--model` | `logistic_regression` | `logistic_regression` or `random_forest` |
| `--threshold` | `0.50` | High/Low confidence cutoff |
| `--input` | `data/synthetic_candidates.csv` | Input CSV |
| `--output` | `results/predictions.csv` | Output predictions CSV |

### Run tests

```bash
.venv/bin/python -m pytest tests/ -v
```

---

## Component Status (25% Milestone)

| Component | Status | Notes |
|---|---|---|
| LLVM environment | ✅ Done | LLVM 21, clang-21, opt |
| Alive2 build | ✅ Done | alive-tv, tv.so |
| Python environment | ✅ Done | Python 3.14, sklearn, numpy, pandas |
| Synthetic dataset | ✅ Done | 800 records, seed=42 |
| Feature extraction | ✅ Done | 9 numeric + 2 categorical + 2 boolean |
| Dataset loader + validation | ✅ Done | Schema checks, error reporting |
| ML model (Logistic Regression) | ✅ Done | sklearn Pipeline |
| Confidence scoring | ✅ Done | P(label=1), configurable threshold |
| Evaluation + plots | ✅ Done | Accuracy, F1, ROC-AUC, Brier, CM |
| pytest suite | ✅ Done | End-to-end + unit tests |
| Alive2 integration | 🔲 Pending | Next milestone |
| Threshold-sensitivity experiments | 🔲 Pending | Next milestone |
| Real candidate dataset | 🔲 Pending | Person 1 — candidate generation |
| Baseline comparisons | 🔲 Pending | Next milestone |
| Final trade-off analysis | 🔲 Pending | Final milestone |

---

## Dataset Schema

See [`data/README.md`](data/README.md) for the full schema.

**Replacing the synthetic dataset** with Person 1's real LLVM candidates:

```bash
.venv/bin/python src/run_pipeline.py all --input data/real_candidates.csv
```

No code changes required if the CSV follows the documented schema.

---

## Important Disclaimers

- The current dataset is **synthetic** — not generated from real LLVM IR.
- Labels are assigned by an **explicit simulation rule** (see `data_generation.py`).
- A positive label does **not** mean Alive2 verified the transformation.
- Confidence scores represent the model's estimated P(label=1) given features, **not** a guarantee of semantic correctness.
- Results will change substantially when real LLVM candidates with Alive2 labels are used.

---

## External Dependencies & Acquisition

The following third-party systems are excluded from this Git repository (`.gitignore`) to keep the repo lightweight. They should be cloned and built locally in the workspace if full compiler-level validation is required:

### 1. LLVM Project & Build
- **Source Repository:** [llvm/llvm-project](https://github.com/llvm/llvm-project)
- **Local Directory:** `llvm-project/` (source), `llvm-build/` (compiled binaries)
- **Acquisition & Build:**
  ```bash
  git clone https://github.com/llvm/llvm-project.git llvm-project
  mkdir -p llvm-build && cd llvm-build
  cmake -GNinja -DCMAKE_BUILD_TYPE=Release -DLLVM_ENABLE_PROJECTS="clang" -DLLVM_ENABLE_ASSERTIONS=ON ../llvm-project/llvm
  ninja clang opt
  ```

### 2. Alive2
- **Source Repository:** [AliveToolkit/alive2](https://github.com/AliveToolkit/alive2)
- **Local Directory:** `alive2/` (source + `alive2/build/` for binaries)
- **Acquisition & Build:**
  ```bash
  git clone https://github.com/AliveToolkit/alive2.git alive2
  mkdir -p alive2/build && cd alive2/build
  cmake -GNinja -DCMAKE_PREFIX_PATH=../../llvm-build -DBUILD_TV=1 -DCMAKE_BUILD_TYPE=Release ..
  ninja
  ```

### 3. Souper (Optional)
- **Source Repository:** [google/souper](https://github.com/google/souper)
- **Local Directory:** `souper/`
- **Acquisition:**
  ```bash
  git clone https://github.com/google/souper.git souper
  ```

---

## Infrastructure Summary

| Tool | Version / Source | Local Workspace Path | Git Tracked? |
|---|---|---|---|
| Python | 3.14.4 | `.venv/bin/python` | No (in `.gitignore`) |
| scikit-learn | 1.9.1 | `.venv` | No (via `requirements.txt`) |
| LLVM / clang | LLVM 21 (git) | `llvm-build/bin/` | No (in `.gitignore`) |
| Alive2 | v21.0 (git) | `alive2/build/alive-tv` | No (in `.gitignore`) |
| Souper | git | `souper/` | No (in `.gitignore`) |
| OS | Ubuntu 26.04 (WSL2) | — | — |

---

## Team Responsibilities

| Person | Area |
|---|---|
| Person 1 | LLVM input, candidate generation, feature extraction from real IR |
| Person 2 | ML pipeline, confidence scoring, evaluation (this milestone) |


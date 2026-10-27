"""Candidate generator engine for LLVM peephole optimizations."""

import random
from typing import List, Optional, Dict
from .models import PeepholeCandidate
from .rules import RULE_CATALOG, RuleFunc


class CandidateGenerator:
    """Generates synthetic and parameterized LLVM peephole transformation candidates."""

    def __init__(
        self,
        seed: int = 42,
        bitwidths: Optional[List[int]] = None,
        category_weights: Optional[Dict[str, float]] = None,
    ):
        self.seed = seed
        self.rng = random.Random(seed)
        self.bitwidths = bitwidths or [8, 16, 32, 64]
        self.category_weights = category_weights or {
            "algebraic": 0.25,
            "bitwise": 0.25,
            "shift_strength_reduction": 0.20,
            "comparison": 0.15,
            "poison_overflow_ub": 0.15,
        }

    def generate_candidates(
        self,
        n_candidates: int = 600,
        sound_ratio: float = 0.45,
    ) -> List[PeepholeCandidate]:
        """Generate N peephole candidates with controlled sound/unsound distribution.

        Args:
            n_candidates: Total number of candidates to produce.
            sound_ratio: Fraction of candidates that should be sound (intended_sound=True).

        Returns:
            List of generated PeepholeCandidate objects.
        """
        candidates: List[PeepholeCandidate] = []
        categories = list(self.category_weights.keys())
        weights = [self.category_weights[c] for c in categories]

        n_sound = int(n_candidates * sound_ratio)
        n_unsound = n_candidates - n_sound

        soundness_pool = [True] * n_sound + [False] * n_unsound
        self.rng.shuffle(soundness_pool)

        for i in range(n_candidates):
            cid = f"cand_{i+1:04d}"
            sound = soundness_pool[i]

            cat = self.rng.choices(categories, weights=weights, k=1)[0]
            rule_func: RuleFunc = self.rng.choice(RULE_CATALOG[cat])
            bw = self.rng.choice(self.bitwidths)

            src_ir, tgt_ir, name, desc = rule_func(bw, sound, self.rng)

            cand = PeepholeCandidate(
                candidate_id=cid,
                name=name,
                category=cat,
                bitwidth=bw,
                src_ir=src_ir,
                tgt_ir=tgt_ir,
                intended_sound=sound,
                mutation_rule=name,
                description=desc,
            )
            candidates.append(cand)

        return candidates

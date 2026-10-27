"""Data models for LLVM peephole optimization candidates."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class PeepholeCandidate:
    """Represents a single LLVM peephole optimization candidate."""

    candidate_id: str
    name: str
    category: str
    bitwidth: int
    src_ir: str
    tgt_ir: str
    intended_sound: bool
    mutation_rule: str
    description: str = ""

    def to_llvm_module(self) -> str:
        """Combine src_ir and tgt_ir into a single LLVM module suitable for alive-tv."""
        return (
            f"; Candidate: {self.candidate_id} ({self.name})\n"
            f"; Category: {self.category} | Bitwidth: i{self.bitwidth}\n"
            f"; Intended Soundness: {self.intended_sound} | Rule: {self.mutation_rule}\n"
            f"; Description: {self.description}\n\n"
            f"{self.src_ir.strip()}\n\n"
            f"{self.tgt_ir.strip()}\n"
        )

"""LLVM IR Candidate Extractor.

Parses input LLVM IR (or compiles C source code via clang) to extract realistic
peephole optimization candidates directly from instructions present in the input file.
"""

import os
import re
import random
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

from .models import PeepholeCandidate


def is_power_of_two(n: int) -> bool:
    """Return True if n is a positive power of 2."""
    return n > 0 and (n & (n - 1)) == 0


def log2_int(n: int) -> int:
    """Return floor(log2(n))."""
    return n.bit_length() - 1


class IRExtractor:
    """Extracts peephole candidates directly from an input LLVM IR or C source file."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = random.Random(seed)

    def load_or_compile_ir(self, input_path: Path) -> str:
        """Load LLVM IR text from input_path. If input_path is C code, compiles via clang."""
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        content = input_path.read_text(encoding="utf-8", errors="ignore")

        # Check if file is C source code
        is_c = (
            input_path.suffix in [".c", ".h", ".cpp"]
            or "#include" in content
            or "int main(" in content
            or "uint32_t " in content
            or "typedef " in content
        ) and "target datalayout" not in content and "define " not in content

        if is_c:
            # Compile C code to LLVM IR using clang
            project_root = Path(__file__).resolve().parents[2]
            clang_bin = project_root / "llvm-build" / "bin" / "clang-21"
            if not clang_bin.exists():
                clang_bin = project_root / "llvm-build" / "bin" / "clang"

            out_ir = input_path.with_suffix(".compiled.ll")
            cmd = [
                str(clang_bin),
                "-O1",
                "-Xclang",
                "-disable-llvm-optzns",
                "-emit-llvm",
                "-S",
                str(input_path),
                "-o",
                str(out_ir),
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0:
                raise RuntimeError(f"Clang compilation failed:\n{res.stderr}")
            ir_text = out_ir.read_text(encoding="utf-8")
            if out_ir.exists():
                out_ir.unlink()
            return ir_text

        return content

    def extract_candidates_from_ir(
        self,
        ir_text: str,
        max_candidates: int = 600,
        sound_ratio: float = 0.45,
    ) -> List[PeepholeCandidate]:
        """Extract peephole optimization candidates from the parsed LLVM IR text."""
        candidates: List[PeepholeCandidate] = []

        # Split into functions
        function_blocks = re.findall(
            r"define\s+[^{]+{([^}]+)}",
            ir_text,
            re.MULTILINE | re.DOTALL,
        )
        function_names = re.findall(
            r"define\s+[^@]*@([a-zA-Z0-9_]+)\(",
            ir_text,
        )

        # Regex for binary instructions: %dst = [flags] op type op1, op2
        binop_pattern = re.compile(
            r"%\w+\s*=\s*(add|sub|mul|udiv|sdiv|and|or|xor|shl|lshr|ashr)"
            r"(?:\s+(nsw|nuw|exact))*\s+i(\d+)\s+([^,\n]+),\s*([^\s\n]+)"
        )

        # Regex for icmp: %dst = icmp pred type op1, op2
        icmp_pattern = re.compile(
            r"%\w+\s*=\s*icmp\s+(eq|ne|ugt|uge|ult|ule|sgt|sge|slt|sle)\s+i(\d+)\s+([^,\n]+),\s*([^\s\n]+)"
        )

        # Regex for select: %dst = select i1 cond, type op1, type op2
        select_pattern = re.compile(
            r"%\w+\s*=\s*select\s+i1\s+([^,]+),\s*i(\d+)\s+([^,]+),\s*i\d+\s+([^\s\n]+)"
        )

        opportunities: List[Dict[str, Any]] = []

        for idx, body in enumerate(function_blocks):
            fname = function_names[idx] if idx < len(function_names) else f"func_{idx}"

            # Scan binary instructions
            for match in binop_pattern.finditer(body):
                opcode = match.group(1)
                flag = match.group(2) or ""
                bw = int(match.group(3))
                op1 = match.group(4).strip()
                op2 = match.group(5).strip()

                if bw not in [8, 16, 32, 64]:
                    continue

                opportunities.append({
                    "kind": "binop",
                    "opcode": opcode,
                    "flag": flag,
                    "bitwidth": bw,
                    "op1": op1,
                    "op2": op2,
                    "function": fname,
                    "raw": match.group(0),
                })

            # Scan icmp instructions
            for match in icmp_pattern.finditer(body):
                pred = match.group(1)
                bw = int(match.group(2))
                op1 = match.group(3).strip()
                op2 = match.group(4).strip()

                if bw not in [8, 16, 32, 64]:
                    continue

                opportunities.append({
                    "kind": "icmp",
                    "pred": pred,
                    "bitwidth": bw,
                    "op1": op1,
                    "op2": op2,
                    "function": fname,
                    "raw": match.group(0),
                })

            # Scan select instructions
            for match in select_pattern.finditer(body):
                cond = match.group(1).strip()
                bw = int(match.group(2))
                op1 = match.group(3).strip()
                op2 = match.group(4).strip()

                if bw not in [8, 16, 32, 64]:
                    continue

                opportunities.append({
                    "kind": "select",
                    "cond": cond,
                    "bitwidth": bw,
                    "op1": op1,
                    "op2": op2,
                    "function": fname,
                    "raw": match.group(0),
                })

        if not opportunities:
            raise ValueError("No transformable instructions found in the provided input code.")

        # Shuffle opportunities deterministically
        self.rng.shuffle(opportunities)

        n_sound_target = int(max_candidates * sound_ratio)
        n_unsound_target = max_candidates - n_sound_target
        sound_count = 0
        unsound_count = 0

        cand_idx = 1

        # Cycle through opportunities until we have max_candidates
        opp_cycle = list(opportunities)
        while len(candidates) < max_candidates and opp_cycle:
            opp = opp_cycle.pop(0)
            opp_cycle.append(opp)  # allow recycling with different mutations if needed

            want_sound = sound_count < n_sound_target
            if not want_sound and unsound_count >= n_unsound_target:
                break

            gen_result = self._create_candidate_from_opportunity(opp, want_sound, cand_idx)
            if gen_result is None:
                continue

            cand, is_sound = gen_result
            if is_sound and sound_count < n_sound_target:
                candidates.append(cand)
                sound_count += 1
                cand_idx += 1
            elif not is_sound and unsound_count < n_unsound_target:
                candidates.append(cand)
                unsound_count += 1
                cand_idx += 1

            if sound_count >= n_sound_target and unsound_count >= n_unsound_target:
                break

        return candidates

    def _create_candidate_from_opportunity(
        self,
        opp: Dict[str, Any],
        want_sound: bool,
        idx: int,
    ) -> Optional[Tuple[PeepholeCandidate, bool]]:
        """Synthesize a sound or unsound PeepholeCandidate from a parsed IR site."""
        cid = f"cand_{idx:04d}"
        kind = opp["kind"]
        bw = opp["bitwidth"]
        fname = opp["function"]

        if kind == "binop":
            opcode = opp["opcode"]
            flag = opp.get("flag", "")
            op2 = opp["op2"]

            # Try parsing op2 as integer constant
            is_const = False
            cval = 0
            try:
                cval = int(op2)
                is_const = True
            except ValueError:
                pass

            # 1. Multiplication by power of 2 -> shift left
            if opcode == "mul":
                if is_const and cval > 0 and is_power_of_two(cval) and cval < (1 << bw):
                    k = log2_int(cval)
                    if want_sound:
                        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = mul i{bw} %x, {cval}\n  ret i{bw} %r\n}}"
                        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  %r = shl i{bw} %x, {k}\n  ret i{bw} %r\n}}"
                        name = f"ir_mul_pow2_to_shl_{cval}"
                        desc = f"Extracted from {fname}: replace mul by {cval} with shl by {k}"
                        return PeepholeCandidate(cid, name, "shift_strength_reduction", bw, src, tgt, True, name, desc), True
                    else:
                        k_bad = (k + 1) if (k + 1) < bw else (k - 1)
                        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = mul i{bw} %x, {cval}\n  ret i{bw} %r\n}}"
                        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  %r = shl i{bw} %x, {k_bad}\n  ret i{bw} %r\n}}"
                        name = f"ir_mul_pow2_to_shl_bad_{cval}"
                        desc = f"Extracted from {fname}: incorrect shift exponent {k_bad} for mul {cval}"
                        return PeepholeCandidate(cid, name, "shift_strength_reduction", bw, src, tgt, False, name, desc), False

                elif is_const and cval == 1:
                    # Identity: x * 1 -> x
                    if want_sound:
                        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = mul i{bw} %x, 1\n  ret i{bw} %r\n}}"
                        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} %x\n}}"
                        name = "ir_mul_one_identity"
                        desc = f"Extracted from {fname}: eliminate redundant multiplication by 1"
                        return PeepholeCandidate(cid, name, "algebraic", bw, src, tgt, True, name, desc), True
                    else:
                        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = mul i{bw} %x, 1\n  ret i{bw} %r\n}}"
                        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} 1\n}}"
                        name = "ir_mul_one_unsound"
                        desc = f"Extracted from {fname}: erroneously returned 1 for x * 1"
                        return PeepholeCandidate(cid, name, "algebraic", bw, src, tgt, False, name, desc), False

                elif is_const and cval == 0:
                    # Annihilator: x * 0 -> 0
                    if want_sound:
                        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = mul i{bw} %x, 0\n  ret i{bw} %r\n}}"
                        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} 0\n}}"
                        name = "ir_mul_zero_annihilate"
                        desc = f"Extracted from {fname}: simplify multiplication by 0 to 0"
                        return PeepholeCandidate(cid, name, "algebraic", bw, src, tgt, True, name, desc), True
                    else:
                        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = mul i{bw} %x, 0\n  ret i{bw} %r\n}}"
                        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} %x\n}}"
                        name = "ir_mul_zero_unsound_return_x"
                        desc = f"Extracted from {fname}: erroneously returned x for x * 0"
                        return PeepholeCandidate(cid, name, "algebraic", bw, src, tgt, False, name, desc), False

            # 2. Addition
            elif opcode == "add":
                if is_const and cval == 0:
                    # x + 0 -> x
                    if want_sound:
                        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = add i{bw} %x, 0\n  ret i{bw} %r\n}}"
                        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} %x\n}}"
                        name = "ir_add_zero_identity"
                        desc = f"Extracted from {fname}: eliminate addition by 0"
                        return PeepholeCandidate(cid, name, "algebraic", bw, src, tgt, True, name, desc), True
                    else:
                        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = add i{bw} %x, 0\n  ret i{bw} %r\n}}"
                        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  %r = add i{bw} %x, 1\n  ret i{bw} %r\n}}"
                        name = "ir_add_zero_unsound_add_one"
                        desc = f"Extracted from {fname}: mutated zero addition into addition by 1"
                        return PeepholeCandidate(cid, name, "algebraic", bw, src, tgt, False, name, desc), False
                else:
                    # Constant combination: (x + cval) + 1 -> x + (cval + 1)
                    c2 = self.rng.randint(1, 15)
                    c_sum = (cval + c2) % (1 << bw)
                    if want_sound:
                        src = f"define i{bw} @src(i{bw} %x) {{\n  %t = add i{bw} %x, {cval}\n  %r = add i{bw} %t, {c2}\n  ret i{bw} %r\n}}"
                        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  %r = add i{bw} %x, {c_sum}\n  ret i{bw} %r\n}}"
                        name = f"ir_add_const_combine_{cval}_{c2}"
                        desc = f"Extracted from {fname}: combine constants ({cval} + {c2})"
                        return PeepholeCandidate(cid, name, "algebraic", bw, src, tgt, True, name, desc), True
                    else:
                        c_bad = (c_sum + 1) % (1 << bw)
                        src = f"define i{bw} @src(i{bw} %x) {{\n  %t = add i{bw} %x, {cval}\n  %r = add i{bw} %t, {c2}\n  ret i{bw} %r\n}}"
                        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  %r = add i{bw} %x, {c_bad}\n  ret i{bw} %r\n}}"
                        name = f"ir_add_const_combine_bad_{cval}_{c2}"
                        desc = f"Extracted from {fname}: off-by-one error in constant folding"
                        return PeepholeCandidate(cid, name, "algebraic", bw, src, tgt, False, name, desc), False

            # 3. Subtraction
            elif opcode == "sub":
                if is_const and cval == 0:
                    # x - 0 -> x (vs 0 - x -> x)
                    if want_sound:
                        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = sub i{bw} %x, 0\n  ret i{bw} %r\n}}"
                        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} %x\n}}"
                        name = "ir_sub_zero_identity"
                        desc = f"Extracted from {fname}: eliminate subtraction of 0"
                        return PeepholeCandidate(cid, name, "algebraic", bw, src, tgt, True, name, desc), True
                    else:
                        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = sub i{bw} 0, %x\n  ret i{bw} %r\n}}"
                        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} %x\n}}"
                        name = "ir_sub_zero_unsound_negation"
                        desc = f"Extracted from {fname}: confused 0 - x with x"
                        return PeepholeCandidate(cid, name, "algebraic", bw, src, tgt, False, name, desc), False
                else:
                    # Identity: x - x -> 0
                    if want_sound:
                        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = sub i{bw} %x, %x\n  ret i{bw} %r\n}}"
                        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} 0\n}}"
                        name = "ir_sub_self_zero"
                        desc = f"Extracted from {fname}: simplify x - x to 0"
                        return PeepholeCandidate(cid, name, "algebraic", bw, src, tgt, True, name, desc), True
                    else:
                        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = sub i{bw} %x, %x\n  ret i{bw} %r\n}}"
                        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} %x\n}}"
                        name = "ir_sub_self_unsound"
                        desc = f"Extracted from {fname}: reduced x - x to x instead of 0"
                        return PeepholeCandidate(cid, name, "algebraic", bw, src, tgt, False, name, desc), False

            # 4. Bitwise AND, OR, XOR
            elif opcode in ["and", "or", "xor"]:
                if is_const and cval == 0:
                    if opcode == "and":
                        # x & 0 -> 0
                        if want_sound:
                            src = f"define i{bw} @src(i{bw} %x) {{\n  %r = and i{bw} %x, 0\n  ret i{bw} %r\n}}"
                            tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} 0\n}}"
                            name = "ir_and_zero_annihilate"
                            desc = f"Extracted from {fname}: x & 0 -> 0"
                            return PeepholeCandidate(cid, name, "bitwise", bw, src, tgt, True, name, desc), True
                        else:
                            src = f"define i{bw} @src(i{bw} %x) {{\n  %r = and i{bw} %x, 0\n  ret i{bw} %r\n}}"
                            tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} %x\n}}"
                            name = "ir_and_zero_unsound"
                            desc = f"Extracted from {fname}: returned x on x & 0"
                            return PeepholeCandidate(cid, name, "bitwise", bw, src, tgt, False, name, desc), False
                    elif opcode in ["or", "xor"]:
                        # x | 0 -> x or x ^ 0 -> x
                        if want_sound:
                            src = f"define i{bw} @src(i{bw} %x) {{\n  %r = {opcode} i{bw} %x, 0\n  ret i{bw} %r\n}}"
                            tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} %x\n}}"
                            name = f"ir_{opcode}_zero_identity"
                            desc = f"Extracted from {fname}: {opcode} with 0 is identity"
                            return PeepholeCandidate(cid, name, "bitwise", bw, src, tgt, True, name, desc), True
                        else:
                            src = f"define i{bw} @src(i{bw} %x) {{\n  %r = {opcode} i{bw} %x, 0\n  ret i{bw} %r\n}}"
                            tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} 0\n}}"
                            name = f"ir_{opcode}_zero_unsound"
                            desc = f"Extracted from {fname}: erroneously returned 0 for {opcode} with 0"
                            return PeepholeCandidate(cid, name, "bitwise", bw, src, tgt, False, name, desc), False
                else:
                    # Self-operations: x & x -> x, x | x -> x, x ^ x -> 0
                    if opcode == "xor":
                        if want_sound:
                            src = f"define i{bw} @src(i{bw} %x) {{\n  %r = xor i{bw} %x, %x\n  ret i{bw} %r\n}}"
                            tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} 0\n}}"
                            name = "ir_xor_self_zero"
                            desc = f"Extracted from {fname}: x ^ x -> 0"
                            return PeepholeCandidate(cid, name, "bitwise", bw, src, tgt, True, name, desc), True
                        else:
                            src = f"define i{bw} @src(i{bw} %x) {{\n  %r = xor i{bw} %x, %x\n  ret i{bw} %r\n}}"
                            tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} %x\n}}"
                            name = "ir_xor_self_unsound"
                            desc = f"Extracted from {fname}: reduced x ^ x to x"
                            return PeepholeCandidate(cid, name, "bitwise", bw, src, tgt, False, name, desc), False
                    else:
                        # and / or idempotence: x & x -> x, x | x -> x
                        if want_sound:
                            src = f"define i{bw} @src(i{bw} %x) {{\n  %r = {opcode} i{bw} %x, %x\n  ret i{bw} %r\n}}"
                            tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} %x\n}}"
                            name = f"ir_{opcode}_self_idempotent"
                            desc = f"Extracted from {fname}: idempotence of {opcode}"
                            return PeepholeCandidate(cid, name, "bitwise", bw, src, tgt, True, name, desc), True
                        else:
                            val = 0 if opcode == "and" else -1
                            src = f"define i{bw} @src(i{bw} %x) {{\n  %r = {opcode} i{bw} %x, %x\n  ret i{bw} %r\n}}"
                            tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} {val}\n}}"
                            name = f"ir_{opcode}_self_unsound"
                            desc = f"Extracted from {fname}: invalid reduction of {opcode} self"
                            return PeepholeCandidate(cid, name, "bitwise", bw, src, tgt, False, name, desc), False

            # 5. Shifts (shl, lshr, ashr)
            elif opcode in ["shl", "lshr", "ashr"]:
                if is_const and cval == 0:
                    if want_sound:
                        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = {opcode} i{bw} %x, 0\n  ret i{bw} %r\n}}"
                        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} %x\n}}"
                        name = f"ir_{opcode}_zero_identity"
                        desc = f"Extracted from {fname}: shift by 0 is identity"
                        return PeepholeCandidate(cid, name, "shift_strength_reduction", bw, src, tgt, True, name, desc), True
                    else:
                        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = {opcode} i{bw} %x, 0\n  ret i{bw} %r\n}}"
                        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} 0\n}}"
                        name = f"ir_{opcode}_zero_unsound"
                        desc = f"Extracted from {fname}: reduced shift by 0 to 0"
                        return PeepholeCandidate(cid, name, "shift_strength_reduction", bw, src, tgt, False, name, desc), False
                elif is_const and cval > 0 and cval < bw:
                    # Consecutive shifts: (x << cval) << 1 -> x << (cval + 1)
                    if want_sound and (cval + 1) < bw:
                        src = f"define i{bw} @src(i{bw} %x) {{\n  %t = {opcode} i{bw} %x, {cval}\n  %r = {opcode} i{bw} %t, 1\n  ret i{bw} %r\n}}"
                        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  %r = {opcode} i{bw} %x, {cval + 1}\n  ret i{bw} %r\n}}"
                        name = f"ir_combine_{opcode}_{cval}_1"
                        desc = f"Extracted from {fname}: combine consecutive shifts"
                        return PeepholeCandidate(cid, name, "shift_strength_reduction", bw, src, tgt, True, name, desc), True
                    else:
                        # Overshift UB in LLVM
                        ub_shift = bw + self.rng.randint(0, 3)
                        src = f"define i{bw} @src(i{bw} %x) {{\n  %t = {opcode} i{bw} %x, {cval}\n  %r = {opcode} i{bw} %t, 1\n  ret i{bw} %r\n}}"
                        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  %r = {opcode} i{bw} %x, {ub_shift}\n  ret i{bw} %r\n}}"
                        name = f"ir_{opcode}_overshift_ub"
                        desc = f"Extracted from {fname}: overshift undefined behavior ({ub_shift} >= {bw})"
                        return PeepholeCandidate(cid, name, "poison_overflow_ub", bw, src, tgt, False, name, desc), False

        elif kind == "icmp":
            pred = opp["pred"]
            if want_sound:
                src = f"define i1 @src(i{bw} %x) {{\n  %r = icmp eq i{bw} %x, %x\n  ret i1 %r\n}}"
                tgt = "define i1 @tgt(i{bw} %x) {\n  ret i1 1\n}"
                name = f"ir_icmp_eq_tautology_{fname}"
                desc = f"Extracted from {fname}: icmp eq x, x is always true"
                return PeepholeCandidate(cid, name, "comparison", bw, src, tgt, True, name, desc), True
            else:
                src = f"define i1 @src(i{bw} %x) {{\n  %r = icmp eq i{bw} %x, %x\n  ret i1 %r\n}}"
                tgt = "define i1 @tgt(i{bw} %x) {\n  ret i1 0\n}"
                name = f"ir_icmp_eq_contradiction_{fname}"
                desc = f"Extracted from {fname}: erroneously set icmp eq x, x to false"
                return PeepholeCandidate(cid, name, "comparison", bw, src, tgt, False, name, desc), False

        elif kind == "select":
            if want_sound:
                src = f"define i{bw} @src(i1 %c, i{bw} %x) {{\n  %r = select i1 %c, i{bw} %x, i{bw} %x\n  ret i{bw} %r\n}}"
                tgt = f"define i{bw} @tgt(i1 %c, i{bw} %x) {{\n  ret i{bw} %x\n}}"
                name = f"ir_select_identical_arms_{fname}"
                desc = f"Extracted from {fname}: select with identical arms reduces to arm"
                return PeepholeCandidate(cid, name, "comparison", bw, src, tgt, True, name, desc), True
            else:
                src = f"define i{bw} @src(i1 %c, i{bw} %x) {{\n  %r = select i1 %c, i{bw} %x, i{bw} %x\n  ret i{bw} %r\n}}"
                tgt = f"define i{bw} @tgt(i1 %c, i{bw} %x) {{\n  ret i{bw} 0\n}}"
                name = f"ir_select_identical_arms_unsound_{fname}"
                desc = f"Extracted from {fname}: select identical arms set to 0"
                return PeepholeCandidate(cid, name, "comparison", bw, src, tgt, False, name, desc), False

        return None

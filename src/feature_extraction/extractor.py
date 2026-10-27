"""Static LLVM IR feature extraction engine.

Extracts structured compiler and syntactic features directly from LLVM IR
modules containing @src and @tgt functions.
"""

import re
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional


OPCODE_CATEGORIES: Dict[str, str] = {
    # Algebraic / arithmetic
    "add": "arithmetic",
    "sub": "arithmetic",
    "mul": "arithmetic",
    "sdiv": "arithmetic",
    "udiv": "arithmetic",
    "srem": "arithmetic",
    "urem": "arithmetic",
    # Bitwise
    "and": "bitwise",
    "or": "bitwise",
    "xor": "bitwise",
    # Shifts
    "shl": "shift",
    "lshr": "shift",
    "ashr": "shift",
    # Comparisons
    "icmp": "comparison",
    "fcmp": "comparison",
    # Control / Select
    "select": "control",
    "ret": "control",
    "br": "control",
    "switch": "control",
}


class IRFeatureExtractor:
    """Extracts machine learning features directly from LLVM IR candidate modules."""

    def __init__(self):
        self.src_fn_regex = re.compile(r"define\s+[^{]*@src\s*\([^)]*\)[^{]*{([^}]+)}", re.MULTILINE | re.DOTALL)
        self.tgt_fn_regex = re.compile(r"define\s+[^{]*@tgt\s*\([^)]*\)[^{]*{([^}]+)}", re.MULTILINE | re.DOTALL)

    def parse_function_body(self, fn_body: str) -> List[str]:
        """Split a function body into clean instruction lines."""
        instructions = []
        for line in fn_body.strip().splitlines():
            line = line.strip()
            # Strip comments
            if ";" in line:
                line = line.split(";", 1)[0].strip()
            # Skip empty lines and basic block labels
            if not line or line.endswith(":") or line.startswith("#"):
                continue
            instructions.append(line)
        return instructions

    def analyze_instructions(self, instructions: List[str]) -> Dict[str, Any]:
        """Analyze a list of instructions from a function body."""
        opcodes = []
        flags = []
        constants = []
        variables = []
        bitwidths = []

        for inst in instructions:
            # Check for flags
            for fl in ["nsw", "nuw", "exact"]:
                if re.search(rf"\b{fl}\b", inst):
                    flags.append(fl)

            # Check for bitwidths: i8, i16, i32, i64
            for bw_match in re.finditer(r"\bi(\d+)\b", inst):
                bitwidths.append(int(bw_match.group(1)))

            # Extract opcode
            # Case 1: %res = opcode [flags] ...
            assign_match = re.search(r"%\w+\s*=\s*([a-z]+)\b", inst)
            if assign_match:
                opcodes.append(assign_match.group(1))
            else:
                # Case 2: ret ... or br ...
                op_match = re.match(r"([a-z]+)\b", inst)
                if op_match:
                    opcodes.append(op_match.group(1))

            # Extract variable operands: %name or %0, %1
            var_matches = re.findall(r"%([a-zA-Z0-9_]+)", inst)
            variables.extend(var_matches)

            # Extract integer constants (e.g. , 0 or ret i32 1 or add i32 %x, 15)
            const_matches = re.findall(r"(?:,\s*|\bi\d+\s+)(-?\d+)\b", inst)
            constants.extend(const_matches)

        # Primary category
        primary_cat = "other"
        for op in opcodes:
            if op != "ret" and op in OPCODE_CATEGORIES:
                primary_cat = OPCODE_CATEGORIES[op]
                break
        if primary_cat == "other" and "ret" in opcodes:
            # If function only has a ret instruction
            if constants and not variables:
                primary_cat = "constant"
            else:
                primary_cat = "control"

        return {
            "instr_count": len(instructions),
            "opcodes": opcodes,
            "flags": flags,
            "constants": constants,
            "variables": variables,
            "bitwidths": bitwidths,
            "primary_category": primary_cat,
        }

    def extract_features_from_module(self, ll_text: str, candidate_id: str = "cand_0000") -> Dict[str, Any]:
        """Extract a structured feature dictionary from an LLVM module containing @src and @tgt."""
        src_match = self.src_fn_regex.search(ll_text)
        tgt_match = self.tgt_fn_regex.search(ll_text)

        src_body = src_match.group(1) if src_match else ""
        tgt_body = tgt_match.group(1) if tgt_match else ""

        src_insts = self.parse_function_body(src_body)
        tgt_insts = self.parse_function_body(tgt_body)

        src_analysis = self.analyze_instructions(src_insts)
        tgt_analysis = self.analyze_instructions(tgt_insts)

        src_count = src_analysis["instr_count"]
        tgt_count = tgt_analysis["instr_count"]
        reduction = src_count - tgt_count
        differs = int(src_count != tgt_count)

        all_constants = src_analysis["constants"] + tgt_analysis["constants"]
        all_variables = src_analysis["variables"] + tgt_analysis["variables"]
        total_operands = len(all_constants) + len(all_variables)
        num_constants = len(all_constants)
        num_variables = len(all_variables)
        has_const = int(num_constants > 0)

        # Complexity metric:
        # Base count + penalty for variables + multiplier for shifts/multiplication/sdiv
        heavy_ops = sum(1 for op in src_analysis["opcodes"] if op in ["mul", "sdiv", "udiv", "shl", "lshr", "ashr"])
        complexity = float(src_count + 0.5 * num_variables + 1.5 * heavy_ops)

        # Bitwidth
        all_bws = src_analysis["bitwidths"] + tgt_analysis["bitwidths"]
        bw = max(all_bws) if all_bws else 32

        # Readable representations
        src_repr = " ; ".join(src_insts)[:80]
        tgt_repr = " ; ".join(tgt_insts)[:80]

        return {
            "candidate_id": candidate_id,
            "src_instr_count": src_count,
            "tgt_instr_count": tgt_count,
            "instr_count_reduction": reduction,
            "num_operands": total_operands,
            "num_constants": num_constants,
            "num_variables": num_variables,
            "candidate_complexity": round(complexity, 2),
            "src_opcode_category": src_analysis["primary_category"],
            "tgt_opcode_category": tgt_analysis["primary_category"],
            "has_constant_operand": has_const,
            "instr_count_differs": differs,
            "bitwidth": bw,
            "has_ub_flags": int(len(src_analysis["flags"]) > 0 or len(tgt_analysis["flags"]) > 0),
            "src_repr": src_repr,
            "tgt_repr": tgt_repr,
        }

    def extract_features_from_file(self, file_path: Path, candidate_id: Optional[str] = None) -> Dict[str, Any]:
        """Extract features from a .ll file on disk."""
        cid = candidate_id or file_path.stem
        text = file_path.read_text(encoding="utf-8")
        return self.extract_features_from_module(text, candidate_id=cid)

"""Unit tests for Phase 2: Static IR Feature Extraction."""

import pytest
from pathlib import Path
import sys

_src = Path(__file__).resolve().parents[1] / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from feature_extraction.extractor import IRFeatureExtractor


class TestIRFeatureExtractor:
    @pytest.fixture
    def extractor(self):
        return IRFeatureExtractor()

    def test_parse_function_body(self, extractor):
        body = (
            "entry:\n"
            "  ; A comment line\n"
            "  %r = add i32 %x, 0\n"
            "  # Another comment or label\n"
            "  ret i32 %r\n"
        )
        insts = extractor.parse_function_body(body)
        assert len(insts) == 2
        assert insts[0] == "%r = add i32 %x, 0"
        assert insts[1] == "ret i32 %r"

    def test_analyze_instructions(self, extractor):
        insts = [
            "%t1 = mul i32 %x, 8",
            "%t2 = add nsw i32 %t1, 1",
            "ret i32 %t2",
        ]
        res = extractor.analyze_instructions(insts)
        assert res["instr_count"] == 3
        assert "mul" in res["opcodes"]
        assert "add" in res["opcodes"]
        assert "nsw" in res["flags"]
        assert 32 in res["bitwidths"]
        assert res["primary_category"] == "arithmetic"

    def test_extract_features_from_module(self, extractor):
        module_text = (
            "; Candidate cand_999\n"
            "define i32 @src(i32 %x) {\n"
            "  %r = mul i32 %x, 4\n"
            "  ret i32 %r\n"
            "}\n\n"
            "define i32 @tgt(i32 %x) {\n"
            "  %r = shl i32 %x, 2\n"
            "  ret i32 %r\n"
            "}\n"
        )
        feats = extractor.extract_features_from_module(module_text, candidate_id="cand_999")

        assert feats["candidate_id"] == "cand_999"
        assert feats["src_instr_count"] == 2
        assert feats["tgt_instr_count"] == 2
        assert feats["instr_count_reduction"] == 0
        assert feats["instr_count_differs"] == 0
        assert feats["src_opcode_category"] == "arithmetic"
        assert feats["tgt_opcode_category"] == "shift"
        assert feats["has_constant_operand"] == 1
        assert feats["num_constants"] >= 2  # 4 and 2
        assert feats["candidate_complexity"] > 0
        assert feats["bitwidth"] == 32

    def test_extract_features_reduction_case(self, extractor):
        module_text = (
            "define i32 @src(i32 %x) {\n"
            "  %t = add i32 %x, 0\n"
            "  ret i32 %t\n"
            "}\n"
            "define i32 @tgt(i32 %x) {\n"
            "  ret i32 %x\n"
            "}\n"
        )
        feats = extractor.extract_features_from_module(module_text, candidate_id="cand_red")
        assert feats["src_instr_count"] == 2
        assert feats["tgt_instr_count"] == 1
        assert feats["instr_count_reduction"] == 1
        assert feats["instr_count_differs"] == 1
        assert feats["src_opcode_category"] == "arithmetic"
        assert feats["tgt_opcode_category"] == "control"

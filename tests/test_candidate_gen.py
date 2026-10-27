"""Unit tests for Phase 1: Real LLVM Candidate Generation."""

import subprocess
import pytest
import random
import csv
from pathlib import Path
import sys

_src = Path(__file__).resolve().parents[1] / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from candidate_gen.models import PeepholeCandidate
from candidate_gen.rules import RULE_CATALOG
from candidate_gen.generator import CandidateGenerator
from candidate_gen.exporter import export_candidates_to_disk
from candidate_gen.ir_extractor import IRExtractor


class TestCandidateModels:
    def test_to_llvm_module_structure(self):
        cand = PeepholeCandidate(
            candidate_id="cand_test_01",
            name="add_zero_test",
            category="algebraic",
            bitwidth=32,
            src_ir="define i32 @src(i32 %x) {\n  ret i32 %x\n}",
            tgt_ir="define i32 @tgt(i32 %x) {\n  ret i32 %x\n}",
            intended_sound=True,
            mutation_rule="add_zero",
            description="Test description",
        )
        module_text = cand.to_llvm_module()
        assert "@src" in module_text
        assert "@tgt" in module_text
        assert "define i32 @src" in module_text
        assert "define i32 @tgt" in module_text
        assert "cand_test_01" in module_text


class TestRules:
    @pytest.mark.parametrize("category", list(RULE_CATALOG.keys()))
    def test_all_rules_execute_cleanly(self, category):
        rng = random.Random(42)
        rules = RULE_CATALOG[category]
        for rule_func in rules:
            for bw in [8, 16, 32, 64]:
                # Test sound variant
                src_s, tgt_s, name_s, desc_s = rule_func(bw, True, rng)
                assert "@src" in src_s
                assert "@tgt" in tgt_s
                assert f"i{bw}" in src_s
                assert len(name_s) > 0

                # Test unsound variant
                src_u, tgt_u, name_u, desc_u = rule_func(bw, False, rng)
                assert "@src" in src_u
                assert "@tgt" in tgt_u
                assert f"i{bw}" in src_u
                assert len(name_u) > 0


class TestGenerator:
    def test_generator_candidate_count(self):
        gen = CandidateGenerator(seed=123)
        cands = gen.generate_candidates(n_candidates=50, sound_ratio=0.40)
        assert len(cands) == 50

    def test_generator_no_duplicate_ids(self):
        gen = CandidateGenerator(seed=123)
        cands = gen.generate_candidates(n_candidates=100)
        ids = [c.candidate_id for c in cands]
        assert len(ids) == len(set(ids))

    def test_generator_reproducibility(self):
        gen1 = CandidateGenerator(seed=999)
        cands1 = gen1.generate_candidates(n_candidates=20)

        gen2 = CandidateGenerator(seed=999)
        cands2 = gen2.generate_candidates(n_candidates=20)

        for c1, c2 in zip(cands1, cands2):
            assert c1.candidate_id == c2.candidate_id
            assert c1.src_ir == c2.src_ir
            assert c1.tgt_ir == c2.tgt_ir
            assert c1.intended_sound == c2.intended_sound

    def test_generator_sound_ratio_respected(self):
        gen = CandidateGenerator(seed=42)
        cands = gen.generate_candidates(n_candidates=100, sound_ratio=0.50)
        sound_count = sum(1 for c in cands if c.intended_sound)
        assert sound_count == 50


class TestExporter:
    def test_export_to_disk(self, tmp_path):
        gen = CandidateGenerator(seed=42)
        cands = gen.generate_candidates(n_candidates=10)

        out_dir = tmp_path / "candidates"
        manifest = tmp_path / "manifest.csv"

        count, mpath = export_candidates_to_disk(cands, out_dir, manifest)
        assert count == 10
        assert mpath.exists()

        # Check .ll files
        for c in cands:
            cand_file = out_dir / f"{c.candidate_id}.ll"
            assert cand_file.exists()
            content = cand_file.read_text(encoding="utf-8")
            assert "@src" in content
            assert "@tgt" in content

        # Check manifest rows
        with open(manifest, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 10
            assert "candidate_id" in rows[0]
            assert "intended_sound" in rows[0]


class TestIRExtractor:
    def test_extractor_from_input_code_txt(self):
        project_root = Path(__file__).resolve().parents[1]
        input_file = project_root / "data" / "input_code.txt"
        if not input_file.exists():
            pytest.skip("data/input_code.txt not found")

        extractor = IRExtractor(seed=42)
        ir_text = extractor.load_or_compile_ir(input_file)
        assert len(ir_text) > 100

        cands = extractor.extract_candidates_from_ir(ir_text, max_candidates=20, sound_ratio=0.50)
        assert len(cands) == 20
        assert any(c.intended_sound for c in cands)
        assert any(not c.intended_sound for c in cands)
        assert all("Extracted from" in c.description for c in cands)


class TestAlive2Integration:
    @pytest.fixture
    def alive2_binary(self):
        project_root = Path(__file__).resolve().parents[1]
        binary = project_root / "alive2" / "build" / "alive-tv"
        if not binary.exists():
            pytest.skip("alive-tv binary not found")
        return binary

    def test_alive2_verifies_sound_candidate(self, tmp_path, alive2_binary):
        gen = CandidateGenerator(seed=42)
        cands = gen.generate_candidates(n_candidates=10, sound_ratio=1.0)
        sound_cand = cands[0]

        test_file = tmp_path / "sound_test.ll"
        test_file.write_text(sound_cand.to_llvm_module(), encoding="utf-8")

        res = subprocess.run(
            [str(alive2_binary), str(test_file)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert "Transformation seems to be correct!" in res.stdout

    def test_alive2_catches_unsound_candidate(self, tmp_path, alive2_binary):
        gen = CandidateGenerator(seed=42)
        cands = gen.generate_candidates(n_candidates=10, sound_ratio=0.0)
        unsound_cand = cands[0]

        test_file = tmp_path / "unsound_test.ll"
        test_file.write_text(unsound_cand.to_llvm_module(), encoding="utf-8")

        res = subprocess.run(
            [str(alive2_binary), str(test_file)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert (
            "Transformation doesn't verify!" in res.stdout
            or "ERROR:" in res.stdout
        )

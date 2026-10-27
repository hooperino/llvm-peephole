"""Unit tests for Phase 2: Alive2 Verification Engine."""

import pytest
from pathlib import Path
import sys

_src = Path(__file__).resolve().parents[1] / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from verification.alive_runner import AliveRunner, AliveResult


class TestAliveRunnerUnit:
    @pytest.fixture
    def runner(self):
        project_root = Path(__file__).resolve().parents[1]
        binary = project_root / "alive2" / "build" / "alive-tv"
        if not binary.exists():
            pytest.skip("alive-tv binary not found")
        return AliveRunner(alive_bin_path=binary)

    def test_parse_verified_output(self, runner):
        stdout = (
            "----------------------------------------\n"
            "define i32 @src(i32 %x) {\n"
            "  %r = add i32 %x, 0\n"
            "  ret i32 %r\n"
            "}\n"
            "=>\n"
            "define i32 @tgt(i32 %x) {\n"
            "  ret i32 %x\n"
            "}\n"
            "Transformation seems to be correct!\n"
        )
        res = runner.parse_alive_output(stdout, "", 0, 150.0, "cand_test")
        assert res.verified is True
        assert res.status == "verified"
        assert res.error_reason is None
        assert res.execution_time_ms == 150.0

    def test_parse_failed_value_mismatch(self, runner):
        stdout = (
            "Transformation doesn't verify!\n"
            "ERROR: Value mismatch\n"
            "Source value: 3\n"
            "Target value: 4\n"
        )
        res = runner.parse_alive_output(stdout, "", 0, 85.5, "cand_bad")
        assert res.verified is False
        assert res.status == "failed"
        assert "Value mismatch" in (res.error_reason or "")

    def test_parse_failed_poison_bug(self, runner):
        stdout = (
            "Transformation doesn't verify!\n"
            "ERROR: Target is more poisonous than source\n"
        )
        res = runner.parse_alive_output(stdout, "", 0, 60.0, "cand_poison")
        assert res.verified is False
        assert res.status == "failed"
        assert "poisonous" in (res.error_reason or "")

    def test_verify_module_str_sound(self, runner):
        module_ir = (
            "define i32 @src(i32 %x) {\n"
            "  %r = add i32 %x, 0\n"
            "  ret i32 %r\n"
            "}\n"
            "define i32 @tgt(i32 %x) {\n"
            "  ret i32 %x\n"
            "}\n"
        )
        res = runner.verify_module_str(module_ir, candidate_id="test_add_zero")
        assert res.verified is True
        assert res.status == "verified"
        assert res.execution_time_ms > 0

    def test_verify_module_str_unsound(self, runner):
        module_ir = (
            "define i32 @src(i32 %x) {\n"
            "  %r = add i32 %x, 0\n"
            "  ret i32 %r\n"
            "}\n"
            "define i32 @tgt(i32 %x) {\n"
            "  %r = add i32 %x, 1\n"
            "  ret i32 %r\n"
            "}\n"
        )
        res = runner.verify_module_str(module_ir, candidate_id="test_bad_add")
        assert res.verified is False
        assert res.status == "failed"

    def test_batch_verify_parallel(self, runner, tmp_path):
        f1 = tmp_path / "c1.ll"
        f1.write_text("define i32 @src(i32 %x) { ret i32 %x }\ndefine i32 @tgt(i32 %x) { ret i32 %x }")

        f2 = tmp_path / "c2.ll"
        f2.write_text("define i32 @src(i32 %x) { ret i32 %x }\ndefine i32 @tgt(i32 %x) { ret i32 0 }")

        results = runner.batch_verify([f1, f2], candidate_ids=["c1", "c2"], max_workers=2)
        assert len(results) == 2
        assert results[0].candidate_id == "c1"
        assert results[0].verified is True
        assert results[1].candidate_id == "c2"
        assert results[1].verified is False

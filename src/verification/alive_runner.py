"""Alive2 formal verification execution engine.

Executes alive-tv on LLVM IR candidate modules (@src vs @tgt) to obtain
mathematical ground truth (sound/verified vs counterexample) and measures
exact SMT solver execution latency.
"""

import os
import re
import time
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from concurrent.futures import ThreadPoolExecutor, as_completed


@dataclass
class AliveResult:
    """Represents the formal verification outcome of an Alive2 verification query."""

    candidate_id: str
    verified: bool
    status: str  # 'verified', 'failed', 'timeout', 'error'
    error_reason: Optional[str]
    execution_time_ms: float
    stdout: str
    stderr: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "verified": int(self.verified),
            "status": self.status,
            "error_reason": self.error_reason or "",
            "verification_time_ms": round(self.execution_time_ms, 2),
        }


class AliveRunner:
    """Harness to execute the Alive2 alive-tv binary on LLVM candidate modules."""

    def __init__(self, alive_bin_path: Optional[Path] = None):
        if alive_bin_path is None:
            # Default to built alive-tv binary in workspace
            project_root = Path(__file__).resolve().parents[2]
            alive_bin_path = project_root / "alive2" / "build" / "alive-tv"

        self.alive_bin = Path(alive_bin_path)
        if not self.alive_bin.exists():
            raise FileNotFoundError(
                f"Alive2 binary not found at: {self.alive_bin}. "
                "Ensure Alive2 has been compiled into alive2/build/alive-tv."
            )

    def parse_alive_output(self, stdout: str, stderr: str, retcode: int, duration_ms: float, cid: str) -> AliveResult:
        """Parse the text output of alive-tv to extract the verification result."""
        # Check for success
        if "Transformation seems to be correct!" in stdout:
            return AliveResult(
                candidate_id=cid,
                verified=True,
                status="verified",
                error_reason=None,
                execution_time_ms=duration_ms,
                stdout=stdout,
                stderr=stderr,
            )

        # Check for failure / counterexample
        if "Transformation doesn't verify!" in stdout or "ERROR:" in stdout:
            error_reason = "Unknown mismatch"
            err_match = re.search(r"ERROR:\s*([^\n]+)", stdout)
            if err_match:
                error_reason = err_match.group(1).strip()
            elif "Value mismatch" in stdout:
                error_reason = "Value mismatch"
            elif "Target is more poisonous" in stdout:
                error_reason = "Target is more poisonous than source"

            return AliveResult(
                candidate_id=cid,
                verified=False,
                status="failed",
                error_reason=error_reason,
                execution_time_ms=duration_ms,
                stdout=stdout,
                stderr=stderr,
            )

        # Other error
        return AliveResult(
            candidate_id=cid,
            verified=False,
            status="error",
            error_reason=stderr.strip() or "Alive2 exited without decision",
            execution_time_ms=duration_ms,
            stdout=stdout,
            stderr=stderr,
        )

    def verify_file(self, file_path: Path, candidate_id: Optional[str] = None, timeout: float = 30.0) -> AliveResult:
        """Run alive-tv on an individual .ll file."""
        cid = candidate_id or file_path.stem
        start_time = time.perf_counter()

        try:
            res = subprocess.run(
                [str(self.alive_bin), str(file_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return self.parse_alive_output(res.stdout, res.stderr, res.returncode, elapsed_ms, cid)

        except subprocess.TimeoutExpired as te:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            stdout = te.stdout.decode() if isinstance(te.stdout, bytes) else (te.stdout or "")
            stderr = te.stderr.decode() if isinstance(te.stderr, bytes) else (te.stderr or "")
            return AliveResult(
                candidate_id=cid,
                verified=False,
                status="timeout",
                error_reason=f"SMT solver timeout after {timeout}s",
                execution_time_ms=elapsed_ms,
                stdout=stdout,
                stderr=stderr,
            )
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return AliveResult(
                candidate_id=cid,
                verified=False,
                status="error",
                error_reason=str(e),
                execution_time_ms=elapsed_ms,
                stdout="",
                stderr=str(e),
            )

    def verify_module_str(self, module_ir: str, candidate_id: str = "temp_cand", timeout: float = 30.0) -> AliveResult:
        """Verify an LLVM IR module passed as a string (via a temporary file)."""
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".ll", delete=False, encoding="utf-8") as tmp:
            tmp.write(module_ir)
            tmp_path = Path(tmp.name)

        try:
            return self.verify_file(tmp_path, candidate_id=candidate_id, timeout=timeout)
        finally:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass

    def batch_verify(
        self,
        file_paths: List[Path],
        candidate_ids: Optional[List[str]] = None,
        max_workers: int = 4,
        timeout: float = 30.0,
    ) -> List[AliveResult]:
        """Verify multiple candidate files in parallel using a thread pool.

        Args:
            file_paths: List of Paths to .ll candidate files.
            candidate_ids: Optional list of candidate IDs matching file_paths.
            max_workers: Concurrency level for SMT solver execution.
            timeout: Per-candidate timeout in seconds.

        Returns:
            List of AliveResult objects matching the order of file_paths.
        """
        cids = candidate_ids or [p.stem for p in file_paths]
        results_map: Dict[str, AliveResult] = {}

        tasks = list(zip(file_paths, cids))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_cid = {
                executor.submit(self.verify_file, path, cid, timeout): cid
                for path, cid in tasks
            }

            for future in as_completed(future_to_cid):
                cid = future_to_cid[future]
                try:
                    res = future.result()
                    results_map[cid] = res
                except Exception as exc:
                    results_map[cid] = AliveResult(
                        candidate_id=cid,
                        verified=False,
                        status="error",
                        error_reason=str(exc),
                        execution_time_ms=0.0,
                        stdout="",
                        stderr=str(exc),
                    )

        # Return in original order
        return [results_map[cid] for cid in cids]

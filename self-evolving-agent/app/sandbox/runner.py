from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from app.app_utils.typing import SandboxResult

PYTHON = sys.executable

TIMEOUT_SECONDS = 30
MAX_OUTPUT_SIZE = 10_000


def run_code(code: str, timeout: int = TIMEOUT_SECONDS) -> SandboxResult:
    """Execute Python code in a subprocess with timeout."""
    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = Path(tmpdir) / "script.py"
        script_path.write_text(code)

        try:
            result = subprocess.run(
                [PYTHON, str(script_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=tmpdir,
            )
            return SandboxResult(
                success=result.returncode == 0,
                stdout=result.stdout[:MAX_OUTPUT_SIZE],
                stderr=result.stderr[:MAX_OUTPUT_SIZE],
            )
        except subprocess.TimeoutExpired:
            return SandboxResult(
                success=False,
                stderr=f"Execution timed out after {timeout} seconds.",
                timed_out=True,
            )


def run_tests(
    tool_code: str, test_code: str, timeout: int = TIMEOUT_SECONDS
) -> SandboxResult:
    """Run pytest tests for a tool in an isolated subprocess.

    Writes the tool code and test code to temp files, then runs pytest.
    The test file imports the tool function from the tool module.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        tool_module = tmpdir_path / "tool_module.py"
        tool_module.write_text(tool_code)

        full_test = (
            "from tool_module import *\n\n" + test_code
        )
        test_file = tmpdir_path / "test_tool.py"
        test_file.write_text(full_test)

        try:
            result = subprocess.run(
                [PYTHON, "-m", "pytest", str(test_file), "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=tmpdir,
            )
            return SandboxResult(
                success=result.returncode == 0,
                stdout=result.stdout[:MAX_OUTPUT_SIZE],
                stderr=result.stderr[:MAX_OUTPUT_SIZE],
            )
        except subprocess.TimeoutExpired:
            return SandboxResult(
                success=False,
                stderr=f"Tests timed out after {timeout} seconds.",
                timed_out=True,
            )

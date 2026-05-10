from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

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


def generate_smoke_tests(
    tool_name: str,
    test_cases: list[dict[str, Any]],
    expected_output_keys: list[str] | None = None,
) -> str:
    """Auto-generate smoke tests from the spec's test_cases.

    Each test calls the tool with the provided inputs and checks:
    1. The function doesn't crash
    2. The result is a dict
    3. The result contains the expected output keys
    """
    lines = ["import json", ""]

    for i, tc in enumerate(test_cases):
        inputs = tc.get("inputs", {})
        out_keys = tc.get("expected_output_keys", expected_output_keys or [])
        args = ", ".join(f"{k}={json.dumps(v)}" for k, v in inputs.items())

        lines.append(f"def test_smoke_{i}():")
        lines.append(f"    result = {tool_name}({args})")
        lines.append(f"    assert isinstance(result, dict), f'Expected dict, got {{type(result)}}'")
        for key in out_keys:
            lines.append(f"    assert {json.dumps(key)} in result, f'Missing key: {key}'")
        lines.append("")

    return "\n".join(lines)


def run_smoke_tests(
    tool_code: str,
    tool_name: str,
    test_cases: list[dict[str, Any]],
    expected_output_keys: list[str] | None = None,
    timeout: int = TIMEOUT_SECONDS,
) -> SandboxResult:
    """Run auto-generated smoke tests for a tool."""
    smoke_test_code = generate_smoke_tests(
        tool_name, test_cases, expected_output_keys,
    )
    return run_tests(tool_code, smoke_test_code, timeout)

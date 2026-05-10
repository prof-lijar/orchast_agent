from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


class TestCase(BaseModel):
    description: str
    inputs: dict[str, Any]
    expected_output_keys: list[str] = []


class ToolSpec(BaseModel):
    tool_name: str
    description: str
    inputs: dict[str, str]
    outputs: dict[str, str]
    dependencies: list[str] = []
    risk_level: Literal["low", "medium", "high"] = "low"
    test_cases: list[TestCase] = []


class RegistryEntry(BaseModel):
    name: str
    description: str
    module: str
    function: str
    input_schema: dict[str, str]
    output_schema: dict[str, str]
    risk_level: Literal["low", "medium", "high"] = "low"
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    version: int = 1


class SandboxResult(BaseModel):
    success: bool
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False

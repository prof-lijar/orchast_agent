import json
from pathlib import Path

from app.agent import execute_registered_tool
from app.registry import manager as registry_manager
from app.app_utils.typing import RegistryEntry

GENERATED_DIR = Path(__file__).resolve().parents[2] / "app" / "tools" / "generated"

_TEST_TOOL_CODE = """\
def _test_helper_tool(text: str) -> dict:
    return {"word_count": len(text.split())}
"""

_TEST_TOOL_NAME = "_test_helper_tool"


def _setup_test_tool():
    tool_file = GENERATED_DIR / f"{_TEST_TOOL_NAME}.py"
    tool_file.write_text(_TEST_TOOL_CODE)
    entry = RegistryEntry(
        name=_TEST_TOOL_NAME,
        description="Test helper",
        module=f"app.tools.generated.{_TEST_TOOL_NAME}",
        function=_TEST_TOOL_NAME,
        input_schema={"text": "string"},
        output_schema={"word_count": "integer"},
        risk_level="low",
        created_at="2026-01-01T00:00:00+00:00",
        version=1,
    )
    registry_manager.register_tool(entry)
    return tool_file


def _teardown_test_tool(tool_file):
    registry_manager.delete_tool(_TEST_TOOL_NAME)
    if tool_file.exists():
        tool_file.unlink()


def test_dynamic_import_execute():
    tool_file = _setup_test_tool()
    try:
        result = execute_registered_tool(
            _TEST_TOOL_NAME, '{"text": "hello world"}'
        )
        assert "word_count: 2" in result
    finally:
        _teardown_test_tool(tool_file)


def test_dynamic_import_missing_tool():
    result = execute_registered_tool("nonexistent_tool", '{"text": "hi"}')
    assert "not found" in result


def test_dynamic_import_bad_json():
    tool_file = _setup_test_tool()
    try:
        result = execute_registered_tool(_TEST_TOOL_NAME, "not json")
        assert "Invalid input JSON" in result
    finally:
        _teardown_test_tool(tool_file)

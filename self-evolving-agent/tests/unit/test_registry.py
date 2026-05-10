import json
from pathlib import Path

import pytest

from app.app_utils.typing import RegistryEntry
from app.registry.manager import (
    REGISTRY_PATH,
    find_tool,
    list_tools,
    load_registry,
    register_tool,
    save_registry,
    search_tools,
)


@pytest.fixture(autouse=True)
def clean_registry(tmp_path, monkeypatch):
    test_registry = tmp_path / "registry.json"
    test_registry.write_text("{}")
    monkeypatch.setattr("app.registry.manager.REGISTRY_PATH", test_registry)
    yield


def _make_entry(name: str = "test_tool", description: str = "A test tool") -> RegistryEntry:
    return RegistryEntry(
        name=name,
        description=description,
        module=f"app.tools.generated.{name}",
        function=name,
        input_schema={"text": "string"},
        output_schema={"result": "string"},
        risk_level="low",
    )


def test_load_empty_registry():
    registry = load_registry()
    assert registry == {}


def test_register_and_find():
    entry = _make_entry()
    assert register_tool(entry) is True
    found = find_tool("test_tool")
    assert found is not None
    assert found.name == "test_tool"
    assert found.description == "A test tool"


def test_register_duplicate_rejected():
    entry = _make_entry()
    assert register_tool(entry) is True
    assert register_tool(entry) is False


def test_find_nonexistent():
    assert find_tool("does_not_exist") is None


def test_search_tools():
    register_tool(_make_entry("word_count", "Counts words in text"))
    register_tool(_make_entry("char_count", "Counts characters in text"))
    register_tool(_make_entry("json_format", "Formats JSON data"))

    results = search_tools("count")
    assert len(results) == 2
    names = {r.name for r in results}
    assert names == {"word_count", "char_count"}


def test_list_tools():
    register_tool(_make_entry("tool_a"))
    register_tool(_make_entry("tool_b"))
    tools = list_tools()
    assert set(tools) == {"tool_a", "tool_b"}


def test_save_and_load_roundtrip():
    registry = {"my_tool": _make_entry("my_tool").model_dump()}
    save_registry(registry)
    loaded = load_registry()
    assert "my_tool" in loaded
    assert loaded["my_tool"]["name"] == "my_tool"

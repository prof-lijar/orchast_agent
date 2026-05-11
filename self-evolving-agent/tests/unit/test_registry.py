import json
from pathlib import Path

import pytest

from app.app_utils.typing import RegistryEntry
from app.registry.manager import (
    REGISTRY_PATH,
    delete_tool,
    find_tool,
    list_tools,
    load_registry,
    register_tool,
    save_registry,
    search_tools,
    update_tool,
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


def test_search_tools_multi_word_query():
    register_tool(_make_entry("word_count_tool", "Counts words in text"))
    register_tool(_make_entry("json_format_tool", "Formats JSON data"))

    results = search_tools("words in hello world")
    assert len(results) == 1
    assert results[0].name == "word_count_tool"


def test_search_tools_no_match():
    register_tool(_make_entry("word_count_tool", "Counts words in text"))
    results = search_tools("xyzzy gibberish")
    assert len(results) == 0


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


def test_update_existing_tool():
    entry = _make_entry("my_tool", "Original description")
    register_tool(entry)

    updated_entry = _make_entry("my_tool", "Updated description")
    assert update_tool(updated_entry) is True

    found = find_tool("my_tool")
    assert found.description == "Updated description"
    assert found.version == 2


def test_update_increments_version_from_current():
    entry = _make_entry("my_tool")
    register_tool(entry)

    update_tool(_make_entry("my_tool", "v2"))
    update_tool(_make_entry("my_tool", "v3"))

    found = find_tool("my_tool")
    assert found.version == 3
    assert found.description == "v3"


def test_update_nonexistent_returns_false():
    assert update_tool(_make_entry("ghost_tool")) is False


def test_delete_existing_tool():
    entry = _make_entry("doomed_tool")
    register_tool(entry)

    assert delete_tool("doomed_tool") is True
    assert find_tool("doomed_tool") is None
    assert "doomed_tool" not in list_tools()


def test_delete_nonexistent_returns_false():
    assert delete_tool("ghost_tool") is False


def test_delete_preserves_other_tools():
    register_tool(_make_entry("keep_me"))
    register_tool(_make_entry("delete_me"))

    delete_tool("delete_me")

    assert find_tool("keep_me") is not None
    assert find_tool("delete_me") is None

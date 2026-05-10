import json

from app.agent import execute_registered_tool
from app.tools.generated.word_count_tool import word_count_tool


def test_word_count_basic():
    result = word_count_tool("Hello world from agent")
    assert result == {"word_count": 4}


def test_word_count_empty():
    result = word_count_tool("")
    assert result == {"word_count": 0}


def test_word_count_single_word():
    result = word_count_tool("hello")
    assert result == {"word_count": 1}


def test_word_count_with_punctuation():
    result = word_count_tool("Hello, world! How are you?")
    assert result == {"word_count": 5}


def test_word_count_with_newlines():
    result = word_count_tool("line one\nline two\nline three")
    assert result == {"word_count": 6}


def test_dynamic_import_execute():
    result_json = execute_registered_tool(
        "word_count_tool", '{"text": "hello world"}'
    )
    result = json.loads(result_json)
    assert result["result"]["word_count"] == 2


def test_dynamic_import_missing_tool():
    result_json = execute_registered_tool("nonexistent_tool", '{"text": "hi"}')
    result = json.loads(result_json)
    assert "error" in result


def test_dynamic_import_bad_json():
    result_json = execute_registered_tool("word_count_tool", "not json")
    result = json.loads(result_json)
    assert "error" in result

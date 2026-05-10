from app.safety.policy import (
    check_imports,
    check_keywords,
    strip_code_fences,
    validate_code_safety,
)


def test_safe_code_passes():
    code = '''
import re

def word_count(text: str) -> dict:
    words = re.findall(r"\\b\\w+\\b", text)
    return {"word_count": len(words)}
'''
    is_safe, violations = validate_code_safety(code)
    assert is_safe is True
    assert violations == []


def test_blocked_import_os():
    code = "import os\nos.system('rm -rf /')"
    is_safe, violations = validate_code_safety(code)
    assert is_safe is False
    assert any("os" in v for v in violations)


def test_blocked_import_subprocess():
    code = "import subprocess\nsubprocess.run(['ls'])"
    is_safe, violations = validate_code_safety(code)
    assert is_safe is False
    assert any("subprocess" in v for v in violations)


def test_blocked_from_import():
    code = "from os.path import join"
    violations = check_imports(code)
    assert len(violations) > 0
    assert any("os" in v for v in violations)


def test_blocked_keyword_exec():
    code = "exec('print(1)')"
    violations = check_keywords(code)
    assert any("exec" in v for v in violations)


def test_blocked_keyword_eval():
    code = "result = eval('2+2')"
    violations = check_keywords(code)
    assert any("eval" in v for v in violations)


def test_blocked_keyword_open():
    code = "f = open('file.txt')"
    violations = check_keywords(code)
    assert any("open" in v for v in violations)


def test_syntax_error_code():
    code = "def broken(:\npass"
    is_safe, violations = validate_code_safety(code)
    assert is_safe is False
    assert any("syntax" in v.lower() for v in violations)


def test_strip_code_fences_python():
    text = '```python\ndef hello():\n    return "hi"\n```'
    result = strip_code_fences(text)
    assert result == 'def hello():\n    return "hi"'


def test_strip_code_fences_plain():
    text = '```\ndef hello():\n    return "hi"\n```'
    result = strip_code_fences(text)
    assert result == 'def hello():\n    return "hi"'


def test_strip_code_fences_no_fences():
    text = 'def hello():\n    return "hi"'
    result = strip_code_fences(text)
    assert text.strip() == result


def test_allowed_imports():
    code = "import re\nimport json\nimport math\nimport collections"
    is_safe, violations = validate_code_safety(code)
    assert is_safe is True
    assert violations == []

from app.sandbox.runner import run_code, run_tests


def test_run_safe_code():
    code = 'print("hello world")'
    result = run_code(code)
    assert result.success is True
    assert "hello world" in result.stdout


def test_run_code_with_error():
    code = "raise ValueError('test error')"
    result = run_code(code)
    assert result.success is False
    assert "ValueError" in result.stderr


def test_run_code_timeout():
    code = "import time; time.sleep(60)"
    result = run_code(code, timeout=2)
    assert result.success is False
    assert result.timed_out is True


def test_run_code_syntax_error():
    code = "def broken(:\npass"
    result = run_code(code)
    assert result.success is False
    assert "SyntaxError" in result.stderr


def test_run_tests_passing():
    tool_code = '''
def add_numbers(a: int, b: int) -> dict:
    return {"sum": a + b}
'''
    test_code = '''
def test_add():
    result = add_numbers(2, 3)
    assert result == {"sum": 5}

def test_add_zero():
    result = add_numbers(0, 0)
    assert result == {"sum": 0}
'''
    result = run_tests(tool_code, test_code)
    assert result.success is True
    assert "passed" in result.stdout


def test_run_tests_failing():
    tool_code = '''
def broken_tool(text: str) -> dict:
    return {"count": 999}
'''
    test_code = '''
def test_broken():
    result = broken_tool("hello")
    assert result["count"] == 1
'''
    result = run_tests(tool_code, test_code)
    assert result.success is False


def test_run_tests_timeout():
    tool_code = '''
import time
def slow_tool(text: str) -> dict:
    time.sleep(60)
    return {"result": text}
'''
    test_code = '''
def test_slow():
    result = slow_tool("hi")
    assert result["result"] == "hi"
'''
    result = run_tests(tool_code, test_code, timeout=2)
    assert result.success is False
    assert result.timed_out is True

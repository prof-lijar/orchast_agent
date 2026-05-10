import ast
from typing import Dict, Union

def python_syntax_detector_tool(code: str) -> Dict[str, Union[bool, str]]:
    """
    Checks a given string of Python code for syntax errors and provides diagnostic feedback.

    Uses the Abstract Syntax Tree (AST) parser to validate Python syntax without executing the code.

    Args:
        code: The string containing the Python code to check.

    Returns:
        A dictionary containing the validation result:
        - is_valid (bool): True if syntax is valid, False otherwise.
        - feedback (str): Diagnostic message detailing success or the specific error location.
    """
    if code is None:
        code = ""

    if not isinstance(code, str):
        return {
            "is_valid": False,
            "feedback": "Input 'code' must be a string."
        }

    try:
        # ast.parse attempts to parse the code string into an AST.
        # mode='exec' is used for general script parsing.
        ast.parse(code, filename='<string>', mode='exec')
        
        # If no exception is raised, the syntax is valid.
        return {
            "is_valid": True,
            "feedback": "Syntax is valid."
        }
        
    except SyntaxError as e:
        # A SyntaxError indicates a standard Python syntax issue.
        feedback = (
            f"Syntax Error detected: {e.msg}. "
            f"Line {e.lineno}, Column {e.offset}."
        )
        return {
            "is_valid": False,
            "feedback": feedback
        }
    except Exception as e:
        # Catch other potential parsing errors (e.g., memory issues, encoding problems, etc.)
        return {
            "is_valid": False,
            "feedback": f"An unexpected error occurred during parsing: {type(e).__name__}: {str(e)}"
        }

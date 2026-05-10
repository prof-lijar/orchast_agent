from __future__ import annotations

import ast
import re

BLOCKED_IMPORTS: frozenset[str] = frozenset({
    "os",
    "subprocess",
    "socket",
    "shutil",
    "pathlib",
    "requests",
    "httpx",
    "urllib",
    "paramiko",
    "ftplib",
    "smtplib",
    "sys",
    "ctypes",
})

BLOCKED_KEYWORDS: frozenset[str] = frozenset({
    "eval(",
    "exec(",
    "open(",
    "__import__(",
    "system(",
    "popen(",
    "compile(",
    "globals(",
    "locals(",
})


def check_imports(code: str) -> list[str]:
    """Find blocked imports using AST parsing.

    Returns list of violation descriptions.
    """
    violations = []
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return ["Code has syntax errors and cannot be analyzed."]

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top_module = alias.name.split(".")[0]
                if top_module in BLOCKED_IMPORTS:
                    violations.append(f"blocked import: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                top_module = node.module.split(".")[0]
                if top_module in BLOCKED_IMPORTS:
                    violations.append(f"blocked import: from {node.module}")

    return violations


def check_keywords(code: str) -> list[str]:
    """Scan source text for blocked keywords.

    Returns list of violation descriptions.
    """
    violations = []
    for keyword in BLOCKED_KEYWORDS:
        if keyword in code:
            violations.append(f"blocked keyword: {keyword.rstrip('(')}")
    return violations


def validate_code_safety(code: str) -> tuple[bool, list[str]]:
    """Run all safety checks on generated code.

    Returns (is_safe, list_of_violations).
    """
    violations = check_imports(code) + check_keywords(code)
    return (len(violations) == 0, violations)


def strip_code_fences(text: str) -> str:
    """Remove markdown code fences and LLM artifacts from output."""
    text = re.sub(r"<ctrl\d+>", "", text)
    pattern = r"```(?:python)?\s*\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()

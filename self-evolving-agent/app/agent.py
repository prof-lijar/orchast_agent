from __future__ import annotations

import importlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import google.auth
from google.adk.agents import Agent, SequentialAgent
from google.adk.apps import App
from google.adk.models import Gemini, LiteLlm
from google.adk.tools.tool_context import ToolContext
from google.genai import types

from app.app_utils.typing import RegistryEntry, ToolSpec
from app.registry import manager as registry_manager
from app.safety.policy import clean_code_syntax, strip_code_fences, validate_code_safety
from app.sandbox.runner import run_smoke_tests, run_tests

_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

_agent_model = os.environ.get("AGENT_MODEL")
_current_model_name = _agent_model or "gemini-flash-latest"

if _agent_model:
    _model = LiteLlm(
        model=f"openai/{_agent_model}",
        api_base="http://localhost:11434/v1",
        api_key="ollama",
        think=False,
        num_ctx=8192,
        repeat_penalty=1.2,
        temperature=0.7,
    )
else:
    _model = Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    )

_gemini_thinking_config = types.GenerateContentConfig(
    thinking_config=types.ThinkingConfig(thinking_budget=2048),
)


def get_current_model_name() -> str:
    return _current_model_name


def _make_ollama_model(name: str) -> LiteLlm:
    return LiteLlm(
        model=f"openai/{name}",
        api_base="http://localhost:11434/v1",
        api_key="ollama",
        think=False,
        num_ctx=8192,
        repeat_penalty=1.2,
        temperature=0.7,
    )


def switch_model(model_name: str) -> dict:
    global _model, _current_model_name, _agent_model
    previous = _current_model_name
    if model_name.startswith("gemini"):
        new_model = Gemini(
            model=model_name,
            retry_options=types.HttpRetryOptions(attempts=3),
        )
    else:
        new_model = _make_ollama_model(model_name)
    _model = new_model
    _current_model_name = model_name
    _agent_model = model_name

    all_agents = [
        root_agent,
        tool_spec_agent,
        tool_coder_agent,
        tool_test_agent,
        tool_registrar_agent,
        tool_review_fixer_agent,
    ]
    for agent in all_agents:
        agent.model = new_model

    root_agent.generate_content_config = (
        _gemini_thinking_config if model_name.startswith("gemini") else None
    )

    return {"success": True, "model": model_name, "previous": previous}


def switch_model_tool(model_name: str) -> str:
    """Switch all agents to a different LLM model at runtime.

    Args:
        model_name: The model to switch to, e.g. 'qwen2.5:7b', 'gemma3:12b', or 'gemini-flash-latest'.

    Returns:
        JSON string confirming the switch or describing the error.
    """
    try:
        result = switch_model(model_name)
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

GENERATED_TOOLS_DIR = Path(__file__).parent / "tools" / "generated"
OUTPUT_DIR = Path(__file__).parent / "output"


# ---------------------------------------------------------------------------
# Tool functions for the root agent
# ---------------------------------------------------------------------------


def search_registry(query: str) -> str:
    """Search the tool registry for existing tools matching a query.

    Args:
        query: Description of the capability needed, e.g. 'word count' or 'text stats'.

    Returns:
        JSON string with a list of matching tools including name, description,
        input_schema (parameter names and types), and output_schema.
    """
    results = registry_manager.search_tools(query)
    if not results:
        return json.dumps({"tools": [], "message": "No matching tools found."})
    tools = [
        {
            "name": r.name,
            "description": r.description,
            "input_schema": r.input_schema,
            "output_schema": r.output_schema,
        }
        for r in results
    ]
    return json.dumps({"tools": tools})


def list_available_tools() -> str:
    """List all tools currently registered in the tool registry.

    Returns:
        JSON string with list of all tools including name, description,
        input_schema (parameter names and types), and output_schema.
    """
    registry = registry_manager.load_registry()
    tools = [
        {
            "name": name,
            "description": data.get("description", ""),
            "input_schema": data.get("input_schema", {}),
            "output_schema": data.get("output_schema", {}),
        }
        for name, data in registry.items()
    ]
    return json.dumps({"tools": tools})


def execute_registered_tool(tool_name: str, input_data: str) -> str:
    """Execute a registered tool by name with the given input data.

    Args:
        tool_name: The exact name of the tool in the registry, e.g. 'word_count_tool'.
        input_data: JSON string of input parameters, e.g. '{"text": "hello world"}'.

    Returns:
        JSON string with the tool's output or an error message.
    """
    entry = registry_manager.find_tool(tool_name)
    if entry is None:
        return f"Tool '{tool_name}' not found in registry."

    try:
        inputs = json.loads(input_data)
    except json.JSONDecodeError as e:
        return f"Invalid input JSON for '{tool_name}': {e}"

    try:
        importlib.invalidate_caches()
        module = importlib.import_module(entry.module)
        func = getattr(module, entry.function)
        result = func(**inputs)

        if isinstance(result, dict) and "files" in result and isinstance(result["files"], dict):
            project_name = result.get("project_name", "project")
            project_dir = OUTPUT_DIR / project_name
            written = []
            for fpath, content in result["files"].items():
                full = project_dir / Path(fpath).name
                full.parent.mkdir(parents=True, exist_ok=True)
                full.write_text(str(content), encoding="utf-8")
                written.append(str(full))
            result = {k: v for k, v in result.items() if k != "files"}
            result["files_written"] = written
            result["output_directory"] = str(project_dir)

        if isinstance(result, dict):
            parts = [f"{k}: {v}" for k, v in result.items()]
            return f"Tool '{tool_name}' result — " + ", ".join(parts)
        return f"Tool '{tool_name}' result — {result}"
    except Exception as e:
        return f"Tool '{tool_name}' failed: {e}"



async def create_downloadable_file(
    filename: str,
    content: str,
    tool_context: ToolContext,
) -> str:
    """Create a downloadable file for the user. The file will appear in the artifacts panel of the chat UI.

    Args:
        filename: The filename with extension, e.g. 'diploma.md', 'report.txt', 'data.json'.
        content: The full text content of the file.

    Returns:
        JSON string confirming the file was created and is available for download.
    """
    artifact = types.Part.from_text(text=content)
    version = await tool_context.save_artifact(filename=filename, artifact=artifact)
    return json.dumps({
        "success": True,
        "filename": filename,
        "version": version,
        "message": f"File '{filename}' is now available for download in the artifacts panel.",
    })


def register_validated_tool(
    tool_context: ToolContext,
) -> str:
    """Validate, test, and register a new tool. Reads the tool spec, code, and \
tests from session state (output_keys: tool_spec, tool_code, tool_tests) \
set by the tool_creation_pipeline. Runs safety checks and sandbox tests \
before registration.

    Call this after tool_creation_pipeline completes. No arguments needed — \
everything is read from session state automatically.

    Returns:
        JSON string with registration result: success/failure and details.
    """
    state = tool_context.state

    review_output = state.get("review_fix_output", "")
    if review_output and "### TOOL_CODE_END ###" in review_output:
        parts = review_output.split("### TOOL_CODE_END ###", 1)
        state["tool_code"] = parts[0].strip()
        state["tool_tests"] = parts[1].strip()
        state["review_fix_output"] = ""

    spec_json = state.get("tool_spec", "")
    tool_code = state.get("tool_code", "")
    test_code = state.get("tool_tests", "")

    if not spec_json or not tool_code or not test_code:
        missing = [
            k for k, v in [("tool_spec", spec_json), ("tool_code", tool_code), ("tool_tests", test_code)]
            if not v
        ]
        return json.dumps({
            "success": False,
            "error": f"Missing pipeline outputs in session state: {missing}. Run tool_creation_pipeline first.",
        })

    tool_code = clean_code_syntax(strip_code_fences(tool_code))
    test_code = clean_code_syntax(strip_code_fences(test_code))
    state["tool_code"] = tool_code
    state["tool_tests"] = test_code

    try:
        spec = ToolSpec(**json.loads(strip_code_fences(spec_json)))
    except Exception as e:
        return json.dumps({"success": False, "error": f"Invalid spec: {e}"})

    tool_name = spec.tool_name

    if state.get("update_mode", False):
        original_name = state.get("update_tool_name", "")
        if original_name:
            spec_dict = json.loads(strip_code_fences(spec_json))
            spec_dict["tool_name"] = original_name
            state["tool_spec"] = json.dumps(spec_dict)
            return update_registered_tool(tool_context)

    if spec.risk_level != "low":
        return json.dumps({
            "success": False,
            "error": f"Risk level '{spec.risk_level}' not allowed. Only 'low' risk tools can be auto-registered.",
        })

    import ast as _ast
    try:
        _ast.parse(tool_code)
    except SyntaxError as e:
        first_lines = "\n".join(tool_code.splitlines()[:5])
        error_msg = f"Tool code has syntax errors after auto-fix: {e}. First 5 lines: {first_lines}"
        state["test_error"] = error_msg
        return json.dumps({
            "success": False,
            "error": error_msg,
        })

    try:
        _ast.parse(test_code)
    except SyntaxError:
        test_code = ""

    is_safe, violations = validate_code_safety(tool_code)
    if not is_safe:
        return json.dumps({
            "success": False,
            "error": f"Safety check failed: {'; '.join(violations)}",
        })

    smoke_cases = [tc.model_dump() for tc in spec.test_cases]
    llm_tests_passed = False

    if test_code:
        sandbox_result = run_tests(tool_code, test_code)
        llm_tests_passed = sandbox_result.success

    if not llm_tests_passed:
        smoke_result = run_smoke_tests(
            tool_code, tool_name, smoke_cases,
        )
        if smoke_result.success:
            pass
        else:
            error_detail = ""
            if test_code and not llm_tests_passed:
                error_detail = (sandbox_result.stdout + "\n" + sandbox_result.stderr).strip()
            smoke_detail = (smoke_result.stdout + "\n" + smoke_result.stderr).strip()
            combined_error = error_detail or smoke_detail
            state["test_error"] = combined_error[:3000]
            return json.dumps({
                "success": False,
                "error": f"Tests failed: {combined_error[:1500]}",
                "timed_out": False,
            })

    tool_file = GENERATED_TOOLS_DIR / f"{tool_name}.py"
    tool_file.write_text(tool_code + "\n")

    entry = RegistryEntry(
        name=tool_name,
        description=spec.description,
        module=f"app.tools.generated.{tool_name}",
        function=tool_name,
        input_schema=spec.inputs,
        output_schema=spec.outputs,
        risk_level=spec.risk_level,
        created_at=datetime.now(timezone.utc).isoformat(),
        version=1,
    )

    registered = registry_manager.register_tool(entry)
    if not registered:
        result = {"success": False, "error": f"Tool '{tool_name}' already exists in registry."}
        state["registration_result"] = json.dumps(result)
        return json.dumps(result)

    result = {
        "success": True,
        "message": f"Tool '{tool_name}' registered successfully.",
        "tool_name": tool_name,
    }
    state["registration_result"] = json.dumps(result)
    return json.dumps(result)


def update_registered_tool(
    tool_context: ToolContext,
) -> str:
    """Validate, test, and UPDATE an existing tool with new code. Reads the \
tool spec, code, and tests from session state (set by the tool_creation_pipeline). \
Runs safety checks and sandbox tests, then overwrites the existing registry \
entry and .py file. The version number is incremented automatically.

    Call this after tool_creation_pipeline completes for a tool update. \
No arguments needed — everything is read from session state automatically.

    Returns:
        JSON string with update result: success/failure and details.
    """
    state = tool_context.state

    review_output = state.get("review_fix_output", "")
    if review_output and "### TOOL_CODE_END ###" in review_output:
        parts = review_output.split("### TOOL_CODE_END ###", 1)
        state["tool_code"] = parts[0].strip()
        state["tool_tests"] = parts[1].strip()
        state["review_fix_output"] = ""

    spec_json = state.get("tool_spec", "")
    tool_code = state.get("tool_code", "")
    test_code = state.get("tool_tests", "")

    if not spec_json or not tool_code or not test_code:
        missing = [
            k for k, v in [("tool_spec", spec_json), ("tool_code", tool_code), ("tool_tests", test_code)]
            if not v
        ]
        return json.dumps({
            "success": False,
            "error": f"Missing pipeline outputs in session state: {missing}. Run tool_creation_pipeline first.",
        })

    tool_code = clean_code_syntax(strip_code_fences(tool_code))
    test_code = clean_code_syntax(strip_code_fences(test_code))
    state["tool_code"] = tool_code
    state["tool_tests"] = test_code

    try:
        spec = ToolSpec(**json.loads(strip_code_fences(spec_json)))
    except Exception as e:
        return json.dumps({"success": False, "error": f"Invalid spec: {e}"})

    tool_name = spec.tool_name

    existing = registry_manager.find_tool(tool_name)
    if existing is None:
        return json.dumps({
            "success": False,
            "error": f"Tool '{tool_name}' not found in registry. Use register_validated_tool for new tools.",
        })

    if spec.risk_level != "low":
        return json.dumps({
            "success": False,
            "error": f"Risk level '{spec.risk_level}' not allowed. Only 'low' risk tools can be auto-registered.",
        })

    import ast as _ast
    try:
        _ast.parse(tool_code)
    except SyntaxError as e:
        first_lines = "\n".join(tool_code.splitlines()[:5])
        error_msg = f"Tool code has syntax errors after auto-fix: {e}. First 5 lines: {first_lines}"
        state["test_error"] = error_msg
        return json.dumps({"success": False, "error": error_msg})

    try:
        _ast.parse(test_code)
    except SyntaxError:
        test_code = ""

    is_safe, violations = validate_code_safety(tool_code)
    if not is_safe:
        return json.dumps({
            "success": False,
            "error": f"Safety check failed: {'; '.join(violations)}",
        })

    smoke_cases = [tc.model_dump() for tc in spec.test_cases]
    llm_tests_passed = False

    if test_code:
        sandbox_result = run_tests(tool_code, test_code)
        llm_tests_passed = sandbox_result.success

    if not llm_tests_passed:
        smoke_result = run_smoke_tests(tool_code, tool_name, smoke_cases)
        if not smoke_result.success:
            error_detail = ""
            if test_code and not llm_tests_passed:
                error_detail = (sandbox_result.stdout + "\n" + sandbox_result.stderr).strip()
            smoke_detail = (smoke_result.stdout + "\n" + smoke_result.stderr).strip()
            combined_error = error_detail or smoke_detail
            state["test_error"] = combined_error[:3000]
            return json.dumps({
                "success": False,
                "error": f"Tests failed: {combined_error[:1500]}",
                "timed_out": False,
            })

    tool_file = GENERATED_TOOLS_DIR / f"{tool_name}.py"
    tool_file.write_text(tool_code + "\n")

    entry = RegistryEntry(
        name=tool_name,
        description=spec.description,
        module=f"app.tools.generated.{tool_name}",
        function=tool_name,
        input_schema=spec.inputs,
        output_schema=spec.outputs,
        risk_level=spec.risk_level,
        created_at=existing.created_at,
    )

    updated = registry_manager.update_tool(entry)
    if not updated:
        result = {"success": False, "error": f"Failed to update tool '{tool_name}'."}
        state["registration_result"] = json.dumps(result)
        return json.dumps(result)

    new_version = registry_manager.find_tool(tool_name).version
    result = {
        "success": True,
        "message": f"Tool '{tool_name}' updated successfully to version {new_version}.",
        "tool_name": tool_name,
        "version": new_version,
    }
    state["update_mode"] = False
    state["update_tool_name"] = ""
    state["update_tool_spec"] = ""
    state["registration_result"] = json.dumps(result)
    return json.dumps(result)


def delete_registered_tool(tool_name: str) -> str:
    """Delete a tool from the registry and remove its source file.

    Args:
        tool_name: The exact name of the tool to delete, e.g. 'word_count_tool'.

    Returns:
        JSON string with deletion result: success/failure and details.
    """
    entry = registry_manager.find_tool(tool_name)
    if entry is None:
        return f"Tool '{tool_name}' not found in registry."

    tool_file = GENERATED_TOOLS_DIR / f"{tool_name}.py"
    if tool_file.exists():
        tool_file.unlink()

    deleted = registry_manager.delete_tool(tool_name)
    if not deleted:
        return f"Failed to delete tool '{tool_name}' from registry."

    return f"Tool '{tool_name}' has been deleted successfully."


def set_update_mode(
    tool_name: str,
    tool_context: ToolContext,
) -> str:
    """Prepare session state for updating an existing tool. Must be called \
before transferring to tool_creation_pipeline for tool updates.

    Args:
        tool_name: The exact name of the existing tool to update, e.g. 'url_fetch_tool'.

    Returns:
        JSON string confirming update mode is set, or an error if the tool is not found.
    """
    existing = registry_manager.find_tool(tool_name)
    if existing is None:
        return json.dumps({
            "success": False,
            "error": f"Tool '{tool_name}' not found in registry. Cannot update.",
        })

    state = tool_context.state
    state["update_mode"] = True
    state["update_tool_name"] = tool_name
    state["update_tool_spec"] = json.dumps({
        "tool_name": existing.name,
        "description": existing.description,
        "inputs": existing.input_schema,
        "outputs": existing.output_schema,
    })

    return json.dumps({
        "success": True,
        "message": f"Update mode set for '{tool_name}'. Now transfer to tool_creation_pipeline.",
        "tool_name": tool_name,
    })


# ---------------------------------------------------------------------------
# Sub-agent instructions
# ---------------------------------------------------------------------------

TOOL_SPEC_INSTRUCTION = """\
You are a Tool Specification Agent. Your job is to convert a user's need \
into a formal, safe tool specification.

Given the user's request, produce a JSON object with exactly these fields:
- "tool_name": snake_case name for the tool (e.g. "sentence_count_tool")
- "description": one-sentence description of what the tool does
- "inputs": object mapping parameter names to their types (e.g. {"text": "string"})
- "outputs": object mapping output field names to their types (e.g. {"count": "integer"})
- "dependencies": list of allowed Python stdlib modules needed (e.g. ["re", "json"])
- "risk_level": must be "low" for text processing tools
- "test_cases": list of objects, each with "description", "inputs", and \
"expected_output_keys" fields. Include at least 3 test cases covering normal, \
edge, and boundary cases.

Rules:
- tool_name MUST be snake_case and end with "_tool"
- risk_level MUST be "low" for v0.1
- dependencies can include: re, json, math, string, collections, statistics, textwrap, itertools, requests, httpx, urllib, os, pathlib, shutil, csv, pandas
- Do NOT include subprocess, socket, sys, ctypes, paramiko, ftplib, smtplib

Output ONLY the JSON object, no explanation, no markdown fences.

Example output:
{
  "tool_name": "sentence_count_tool",
  "description": "Counts the number of sentences in a text string.",
  "inputs": {"text": "string"},
  "outputs": {"sentence_count": "integer"},
  "dependencies": ["re"],
  "risk_level": "low",
  "test_cases": [
    {"description": "Normal text", "inputs": {"text": "Hello. World."}, "expected_output_keys": ["sentence_count"]},
    {"description": "Empty text", "inputs": {"text": ""}, "expected_output_keys": ["sentence_count"]},
    {"description": "No period", "inputs": {"text": "Hello world"}, "expected_output_keys": ["sentence_count"]}
  ]
}
"""

TOOL_CODER_INSTRUCTION = """\
You are a Tool Coder Agent. Your job is to write safe Python code for a tool \
based on a specification.

Read the tool specification from the previous step:
{tool_spec}

Generate a complete Python function that implements the specification. Follow \
these rules strictly:

1. Write exactly ONE function with the name from tool_name in the spec
2. Use type hints for all parameters and return type
3. Include a Google-style docstring with Args and Returns sections
4. Return a dictionary matching the output schema
5. Allowed imports: re, json, math, string, collections, statistics, textwrap, itertools, requests, httpx, urllib, os, pathlib, shutil, csv, pandas
6. Do NOT import: subprocess, socket, sys, ctypes, paramiko, ftplib, smtplib
7. Do NOT use: eval(), exec(), open(), __import__(), system(), popen(), compile(), globals(), locals()
8. Handle edge cases gracefully (empty strings, None values)
9. When the spec includes network dependencies (requests, httpx, urllib), you MUST \
write REAL implementations that make actual HTTP calls. NEVER write placeholder, \
mock, or simulated implementations. The sandbox allows outbound network requests. \
For web search, use DuckDuckGo's HTML endpoint (https://html.duckduckgo.com/html/) \
which requires no API key.

Output ONLY the Python code, no explanation, no markdown fences. The code must \
be a complete, runnable Python file with imports at the top and the function \
definition.
"""

TOOL_TEST_INSTRUCTION = """\
You are a Tool Test Agent. Your job is to write pytest tests for a generated tool.

Read the tool specification:
{tool_spec}

Read the tool code:
{tool_code}

TESTING STRATEGY — follow these rules strictly:

CRITICAL: Every `assert` statement in your test MUST be a real assertion that \
you expect to PASS. NEVER write assert statements as documentation, comments, \
or to "show your work." For example, NEVER write:
  assert selected == "rain"  # rain is not in topic  <-- THIS WILL FAIL
If you want to document logic, use comments (#), NOT assert statements.

1. NEVER hardcode expected output values by manually tracing the code. \
You WILL get it wrong. Instead, use one of these two approaches:

   APPROACH A — Compute expected values in test code:
   Write a simple reference implementation or inline computation in your \
   test to derive the expected value. Example:
     input_text = "Hello World"
     result = my_tool(input_text)
     # Compute expected value programmatically:
     expected = "".join(c.lower() if i % 2 == 0 else c.upper() \
                        for i, c in enumerate(input_text))
     assert result["output"] == expected

   APPROACH B — Structural assertions:
   Check properties, types, lengths, invariants, and containment \
   instead of exact values. Example:
     result = my_tool("hello world")
     assert isinstance(result, dict)
     assert "output" in result
     assert len(result["output"]) == len("hello world")
     assert result["output"] != "hello world"  # was transformed

   The ONLY exception: exact value comparisons are OK for inputs of \
   1-3 characters where the answer is trivially obvious. Example:
     assert my_tool("Hi")["output"] == "hI"

   NEVER MIX both approaches in the same test — if you use a reference \
   function to compute expected values, do NOT also hardcode the same \
   expected value as a string literal. Pick one approach per assertion.

2. Write at least 4 test functions covering:
   - Normal input (use APPROACH A or B, NOT hand-traced values)
   - Empty input / missing input
   - Edge cases (single character, whitespace-only, special characters)
   - Output type and structure validation (dict, expected keys, value types)

3. Each test function name must start with "test_"
4. Test functions must take ZERO parameters: `def test_foo():` — NEVER \
`def test_foo(my_tool):`. The tool function is globally available via \
`from tool_module import *`, NOT as a pytest fixture.
5. Use plain assert statements
6. Do NOT import subprocess, socket, sys, ctypes, or paramiko
7. Do NOT use fixtures or conftest
8. Keep test inputs SIMPLE

Output ONLY the Python test code, no explanation, no markdown fences. The code \
must be a complete, runnable pytest file. Do NOT include an import statement for \
the tool function - it will be injected automatically.
"""


TOOL_REVIEW_FIXER_INSTRUCTION = """\
You are a Tool Review & Fix Agent. A tool failed registration. Your job is \
to diagnose the problem, determine whether the bug is in the TOOL CODE or \
the TEST CODE (or both), and fix it.

Tool specification:
{tool_spec}

Tool code:
{tool_code}

Test code (FAILED):
{tool_tests}

Error from test runner:
{test_error}

REVIEW PROCESS:
1. Read the error carefully. Identify WHICH test(s) failed and the exact \
assertion or error that caused the failure.

2. DIAGNOSE the root cause — is the bug in the test or the tool?
   - If the test asserts a wrong expected value → fix the TEST
   - If the test uses function parameters like `def test_foo(tool):` → fix \
     the TEST (must be `def test_foo():` with zero params)
   - If the test uses `assert` for documentation/comments instead of real \
     checks → fix the TEST (use # comments instead)
   - If the tool code has a syntax error or logic bug → fix the TOOL CODE
   - If the tool code has a bad import inside a function body → fix the \
     TOOL CODE (move import to top of file)

3. FIX the broken part(s). Rules for test fixes:
   - NEVER hardcode expected values by manually tracing code
   - For exact comparisons, use ONLY trivially short inputs (1-3 chars)
   - For longer inputs, compute expected values programmatically (Approach A) \
     or use structural assertions (Approach B)
   - All test functions MUST take ZERO parameters
   - Every `assert` must be a real assertion you expect to PASS

4. OUTPUT FORMAT — you must output EXACTLY two sections separated by the \
marker line `### TOOL_CODE_END ###`:

[Complete fixed tool code here — if no changes needed, copy it unchanged]
### TOOL_CODE_END ###
[Complete fixed test code here]

Output ONLY the code sections with the marker. No explanation, no markdown \
fences. Do NOT include an import statement for the tool function in the test \
section — it will be injected automatically.
"""


# ---------------------------------------------------------------------------
# Callback to save uploaded files to disk so file-path tools can use them
# ---------------------------------------------------------------------------

UPLOAD_DIR = Path(tempfile.gettempdir()) / "adk_uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


def _save_uploaded_files(callback_context, llm_request):
    """Detect inline file uploads and save them to disk.

    Appends a system hint with the saved file path so the model can pass it
    to file-based tools like csv_read_tool.
    """
    contents = llm_request.contents
    if not contents:
        return None
    last_user = None
    for content in reversed(contents):
        if content.role == "user":
            last_user = content
            break
    if not last_user or not last_user.parts:
        return None
    saved = []
    for part in last_user.parts:
        blob = getattr(part, "inline_data", None)
        if not blob:
            continue
        mime = getattr(blob, "mime_type", "") or ""
        data = getattr(blob, "data", None)
        if not data:
            continue
        ext = _mime_to_ext(mime)
        filename = f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
        filepath = UPLOAD_DIR / filename
        if isinstance(data, str):
            import base64
            data = base64.b64decode(data)
        filepath.write_bytes(data)
        saved.append(str(filepath))
    if saved:
        paths = ", ".join(saved)
        llm_request.contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(
                    text=f"[SYSTEM] The user uploaded file(s) saved at: {paths}\n"
                    f"Use this file path when calling tools that need a file_path parameter."
                )],
            )
        )
    return None


def _mime_to_ext(mime: str) -> str:
    mapping = {
        "text/csv": ".csv",
        "application/json": ".json",
        "text/plain": ".txt",
        "application/pdf": ".pdf",
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    }
    return mapping.get(mime, ".bin")


# ---------------------------------------------------------------------------
# Callback to prevent local models from looping on tool calls
# ---------------------------------------------------------------------------


def _limit_tool_loops(callback_context, llm_request):
    """Prevent small local models from looping on tool calls."""
    contents = llm_request.contents
    if not contents:
        return None
    recent_calls = []
    last_tool_result = ""
    for content in reversed(contents):
        if not content.parts:
            break
        calls = [p.function_call.name for p in content.parts if getattr(p, "function_call", None)]
        if calls:
            recent_calls.extend(calls)
        elif any(getattr(p, "function_response", None) for p in content.parts):
            for p in content.parts:
                fr = getattr(p, "function_response", None)
                if fr and hasattr(fr, "response"):
                    resp = fr.response
                    if isinstance(resp, dict):
                        last_tool_result = resp.get("result", str(resp))
                    else:
                        last_tool_result = str(resp)
                    break
            continue
        else:
            break
    should_strip = (
        len(recent_calls) >= 3
        or (len(recent_calls) >= 2 and recent_calls[0] == recent_calls[1])
    )
    if should_strip:
        llm_request.tools_dict = {}
        if llm_request.config and llm_request.config.tools:
            llm_request.config.tools = []
        hint = last_tool_result or "The tool already returned a result above."
        llm_request.contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(
                    text=f"[SYSTEM] The tool result is: {hint}\n"
                    f"Now tell the user the answer in plain language. "
                    f"Do NOT call any functions."
                )],
            )
        )
    return None


# ---------------------------------------------------------------------------
# Sub-agent definitions (Phases 7-9)
# ---------------------------------------------------------------------------


def _tool_spec_instruction(ctx):
    update_mode = ctx.state.get("update_mode", False)
    if not update_mode:
        return TOOL_SPEC_INSTRUCTION

    tool_name = ctx.state.get("update_tool_name", "")
    existing_spec = ctx.state.get("update_tool_spec", "")

    return TOOL_SPEC_INSTRUCTION + f"""

UPDATE MODE — You are UPDATING an existing tool, NOT creating a new one.

CRITICAL: The tool_name MUST be exactly "{tool_name}". Do NOT rename it.
Here is the current spec — improve it as the user requested:
{existing_spec}
"""


tool_spec_agent = Agent(
    name="tool_spec_agent",
    description="Designs a formal JSON specification for a new or updated tool based on the user's need",
    model=_model,
    instruction=_tool_spec_instruction,
    output_key="tool_spec",
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)

tool_coder_agent = Agent(
    name="tool_coder_agent",
    description="Generates safe Python code for a tool from its specification",
    model=_model,
    instruction=TOOL_CODER_INSTRUCTION,
    output_key="tool_code",
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)

tool_test_agent = Agent(
    name="tool_test_agent",
    description="Generates pytest tests for a tool from its specification and code",
    model=_model,
    instruction=TOOL_TEST_INSTRUCTION,
    output_key="tool_tests",
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)

TOOL_REGISTRAR_INSTRUCTION = """\
You are a Tool Registrar Agent. Follow these steps exactly:
1. Check the session state for "update_mode". If it is set to true, call \
`update_registered_tool` with no arguments. Otherwise, call \
`register_validated_tool` with no arguments.
2. After receiving the result, output EXACTLY one of these two lines and nothing else:
   - If success: REGISTRATION_SUCCESS: [tool_name]
   - If failure: REGISTRATION_FAILED: [error summary]
Do NOT explain, reason, or suggest next steps. Just call the tool and output the result line.
"""

LOCAL_TOOL_REGISTRAR_INSTRUCTION = """\
Check the session state for "update_mode". If it is set to true, call \
`update_registered_tool` with no arguments. Otherwise, call \
`register_validated_tool` with no arguments. \
Then output REGISTRATION_SUCCESS or REGISTRATION_FAILED. Nothing else.
"""

tool_registrar_agent = Agent(
    name="tool_registrar_agent",
    description="Automatically registers or updates the tool after tests are generated",
    model=_model,
    instruction=LOCAL_TOOL_REGISTRAR_INSTRUCTION if _agent_model else TOOL_REGISTRAR_INSTRUCTION,
    tools=[register_validated_tool, update_registered_tool],
    before_model_callback=_limit_tool_loops if _agent_model else None,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)

tool_creation_pipeline = SequentialAgent(
    name="tool_creation_pipeline",
    description=(
        "Creates and registers a new tool through a 4-step pipeline: "
        "specification, code generation, test generation, and registration. "
        "Transfer here when no existing tool matches the user's need."
    ),
    sub_agents=[tool_spec_agent, tool_coder_agent, tool_test_agent, tool_registrar_agent],
)

tool_review_fixer_agent = Agent(
    name="tool_review_fixer_agent",
    description=(
        "Reviews and fixes a failed tool. Diagnoses whether the bug is in "
        "the tool code or test code, fixes the broken part(s), and outputs "
        "both. Transfer here when register_validated_tool fails."
    ),
    model=_model,
    instruction=TOOL_REVIEW_FIXER_INSTRUCTION,
    output_key="review_fix_output",
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)


# ---------------------------------------------------------------------------
# Root agent (full version with creation pipeline)
# ---------------------------------------------------------------------------

ROOT_INSTRUCTION = """\
ABSOLUTE RULE — OBEY BEFORE ANYTHING ELSE:
You MUST NEVER say "I don't have", "I cannot", "I do not have a tool", \
"I'm not able to", or any similar denial of capability WITHOUT first calling \
`search_registry`. Your tool registry is DYNAMIC — users add tools you don't \
know about. If you claim you lack a capability without searching, you are \
WRONG and LYING to the user. ALWAYS SEARCH FIRST, THEN RESPOND.

You are the Self-Evolving Agent, an intelligent orchestrator that manages a \
dynamic registry of tools. You can both use existing tools and create new ones.

CRITICAL RULE: You are NOT a normal chatbot. You have a DYNAMIC tool registry \
that grows over time. NEVER assume you lack a capability — ALWAYS call \
`search_registry` first. Users create tools you don't know about. If the user \
mentions a tool by name or asks you to do something specific, SEARCH FIRST.

FIRST: Decide if the user's request needs a tool at all.
- Simple questions (math, greetings, general knowledge, opinions, explanations) \
→ answer directly. Do NOT search the registry or create tools for these.
- If the user mentions a specific tool by name (e.g. "use X tool", "run X") \
→ ALWAYS follow the TOOL WORKFLOW. NEVER say you don't have it without searching.
- ANY task that involves processing, transforming, analyzing, fetching, \
generating, or working with data → follow the TOOL WORKFLOW below.
  Examples: counting words, fetching URLs, formatting text, converting data, \
computing statistics, extracting patterns, web scraping, file operations.

TOOL WORKFLOW — follow these steps IN ORDER:

STEP 1 (REQUIRED FIRST): Call `search_registry` with SHORT keywords (1-2 words) \
extracted from the user's request. Examples:
  - "count the words in hello world" → search "word count"
  - "how many sentences" → search "sentence"
  - "format this JSON" → search "json format"
Do NOT pass the full user message as the query. Use only the core capability words. \
If the first search returns nothing, try a second search with a synonym.

STEP 2: Check the search results.
  - If a matching tool is found → call `execute_registered_tool` with the tool \
name and input data as a JSON string. Present the result to the user. DONE.
  - If NO matching tool is found → continue to Step 3.

STEP 3: Before creating a tool, make sure you have a CLEAR and SPECIFIC \
understanding of what the tool should do. If the user's request is vague or \
incomplete (e.g. "create a tool", "make a tool using pandas", "I need a new \
tool"), ask the user to clarify:
  - What specific task should the tool perform?
  - What input will it receive and what output should it produce?
Do NOT guess or assume what the user wants. Only proceed once you have enough \
detail to write a specification.

STEP 4: Call `transfer_to_agent` with agent name "tool_creation_pipeline" to \
create and register the new tool. The pipeline handles everything automatically: \
specification → code → tests → registration. Do NOT call `register_validated_tool` \
yourself — the pipeline does it.

STEP 5: After the pipeline returns, check if the last message contains \
"REGISTRATION_SUCCESS" or "REGISTRATION_FAILED":

  IF "REGISTRATION_SUCCESS": Tell the user the tool was created successfully. \
Show the tool name, description, inputs/outputs, and a usage example. \
If the user provided input data, call `execute_registered_tool` to demo it. DONE.

  IF "REGISTRATION_FAILED": Do NOT give up. IMMEDIATELY do the following:
    a) Call `transfer_to_agent` with agent name "tool_review_fixer_agent"
    b) After it finishes, call `register_validated_tool` (no arguments) to retry
    c) If it succeeds, tell the user the tool was created. DONE.
    d) If it fails again, repeat steps (a)-(c) up to 3 total attempts.
    e) Only after 3 failures, tell the user it failed and explain why.

You MUST ALWAYS communicate the final outcome to the user. NEVER end a turn \
silently after tool creation — the user must see either a success or failure \
message.

IMPORTANT: To transfer to any sub-agent, you MUST call `transfer_to_agent`. \
Do NOT use any other function name like TransferToAgentTool or transferToAgent.

Use `list_available_tools` when the user asks what tools are available. \
After listing, STOP — do NOT start creating, retrying, or fixing tools unless \
the user explicitly asks for it.

Use `switch_model_tool` when the user asks to change, switch, or use a \
different model. Pass the exact model name (e.g. 'qwen2.5:7b', \
'gemma3:12b', 'gemini-flash-latest'). Confirm the switch to the user.

UPDATE TOOL WORKFLOW — when the user asks to update, edit, fix, or improve \
an existing tool:

STEP U1: Confirm which tool to update. Call `search_registry` or \
`list_available_tools` to verify the tool exists and get its exact name.

STEP U2: Call `set_update_mode` with the exact tool name. This prepares \
the pipeline to preserve the original tool name. Then call \
`transfer_to_agent` with agent name "tool_creation_pipeline".

STEP U3: After the pipeline returns, check for "REGISTRATION_SUCCESS" or \
"REGISTRATION_FAILED". Handle the same way as new tool creation (retry loop \
with tool_review_fixer_agent if needed, up to 3 attempts).

STEP U4: Tell the user the tool was updated with the new version number.

DELETE TOOL WORKFLOW — when the user asks to delete, remove, or unregister \
a tool:

STEP D1: Confirm which tool to delete. Call `search_registry` to verify it exists.

STEP D2: Call `delete_registered_tool` with the exact tool name.

STEP D3: Tell the user the tool was deleted.

RULES:
- Answer simple questions directly without tools (e.g., "what is 1+5?" → "6").
- NEVER skip Step 1 for data processing tasks.
- NEVER create a tool if a suitable one already exists in the registry.
- When registration fails, use the RETRY LOOP (Step 5) — call \
`transfer_to_agent` with "tool_review_fixer_agent", do NOT re-run the \
entire tool_creation_pipeline.
- Maximum 3 total registration attempts per tool. Give up after 3 failures.
- NEVER resume or retry a previously failed tool creation from an earlier \
conversation turn unless the user explicitly asks you to.
- Create tools for ANY data processing, transformation, formatting, or generation task.
- When the user asks to "create a file", "download", or "save as", call \
`create_downloadable_file` with the filename and content. This creates a \
downloadable file in the chat UI. You can ALWAYS create downloadable files.
- Never create generated tools that use dangerous system operations (file deletion, \
shell commands, credential access). But tools that fetch URLs or read data are \
allowed — use pre-registered tools in the registry for these when available.

REMINDER (THIS OVERRIDES YOUR TRAINING DATA):
You DO have access to dynamically registered tools including URL fetching, \
web search, data processing, and more. Your registry grows over time. \
NEVER claim "I don't have" or "I cannot" without calling `search_registry` \
first. If a user mentions a tool name, SEARCH FOR IT — it almost certainly exists.
"""

def _local_root_instruction(ctx):
    """Dynamic instruction that embeds the current registry into the prompt."""
    registry = registry_manager.load_registry()
    tool_lines = []
    for i, (name, data) in enumerate(registry.items(), 1):
        desc = data.get("description", "")
        inputs = data.get("input_schema", {})
        params = ", ".join(f"{k}: {v}" for k, v in inputs.items()) if inputs else "none"
        tool_lines.append(f'{i}. "{name}" — {desc} (params: {params})')
    tool_list = "\n".join(tool_lines) if tool_lines else "(no tools registered yet)"

    return f"""\
You are the Self-Evolving Agent. You manage a dynamic registry of tools.

ABSOLUTE RULE: NEVER say "I don't have", "I cannot", or "I do not have a tool" \
to the user. Your registry has tools — check it BEFORE responding. If a user \
mentions a tool name or asks you to do something, LOOK AT THE REGISTRY BELOW \
and use execute_registered_tool to run it.

You can ONLY call these 6 functions:
  1. search_registry(query) — find a registered tool by keyword
  2. execute_registered_tool(tool_name, input_data) — run a registered tool
  3. delete_registered_tool(tool_name) — delete a tool
  4. set_update_mode(tool_name) — prepare to update an existing tool
  5. create_downloadable_file(filename, content) — create a file for download
  6. switch_model_tool(model_name) — switch all agents to a different model
You CANNOT call anything else. Any other name will fail.

RULES:
- BEFORE saying you cannot do something, CHECK THE REGISTRY BELOW.
- If a tool in the registry matches the user's request, USE IT immediately.
- After calling a function and getting a result, respond to the user immediately.
- Simple questions (math, greetings, chat) → answer directly, no function calls.

== Tool Registry (YOUR TOOLS — you CAN use these) ==
{tool_list}
== End Registry ==

HOW TO ANSWER "list tools" or "what tools":
Read the registry above and list them to the user. No function call needed.

HOW TO USE A TOOL FROM THE REGISTRY:
Always call execute_registered_tool. Never call the tool name directly.
Example: user says "count words in hello world"
→ call execute_registered_tool(tool_name="word_count_tool", input_data='{{"text": "hello world"}}')
Example: user says "fetch this URL" and url_fetch_tool is in registry
→ call execute_registered_tool(tool_name="url_fetch_tool", input_data='{{"url": "https://example.com"}}')

HOW TO CREATE A NEW TOOL:
Call transfer_to_agent(agent_name="tool_creation_pipeline").

HOW TO UPDATE AN EXISTING TOOL:
1. Call set_update_mode(tool_name="the_tool_name")
2. Call transfer_to_agent(agent_name="tool_creation_pipeline")
3. Tell the user the result.

HOW TO DELETE A TOOL:
Call delete_registered_tool(tool_name="the_tool_name").

REMEMBER: You HAVE the tools listed above. NEVER deny having them.
"""


_root_instruction = _local_root_instruction if _agent_model else ROOT_INSTRUCTION
_root_sub_agents = (
    [tool_creation_pipeline]
    if _agent_model
    else [tool_creation_pipeline, tool_review_fixer_agent]
)
def _root_before_model_local(callback_context, llm_request):
    _save_uploaded_files(callback_context, llm_request)
    return _limit_tool_loops(callback_context, llm_request)


_root_before_model = _root_before_model_local if _agent_model else None
_root_tools = [
    search_registry,
    execute_registered_tool,
    delete_registered_tool,
    set_update_mode,
    create_downloadable_file,
    switch_model_tool,
] if _agent_model else [
    search_registry,
    list_available_tools,
    execute_registered_tool,
    register_validated_tool,
    update_registered_tool,
    delete_registered_tool,
    set_update_mode,
    create_downloadable_file,
    switch_model_tool,
]

root_agent = Agent(
    name="root_agent",
    model=_model,
    instruction=_root_instruction,
    before_model_callback=_root_before_model,
    tools=_root_tools,
    sub_agents=_root_sub_agents,
    generate_content_config=_gemini_thinking_config if not _agent_model else None,
)

app = App(
    root_agent=root_agent,
    name="app",
)

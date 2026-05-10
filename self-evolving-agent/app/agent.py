from __future__ import annotations

import importlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import google.auth
from google.adk.agents import Agent, SequentialAgent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

from app.app_utils.typing import RegistryEntry, ToolSpec
from app.registry import manager as registry_manager
from app.safety.policy import strip_code_fences, validate_code_safety
from app.sandbox.runner import run_tests

_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

_model = Gemini(
    model="gemini-flash-latest",
    retry_options=types.HttpRetryOptions(attempts=3),
)

GENERATED_TOOLS_DIR = Path(__file__).parent / "tools" / "generated"


# ---------------------------------------------------------------------------
# Tool functions for the root agent
# ---------------------------------------------------------------------------


def search_registry(query: str) -> str:
    """Search the tool registry for existing tools matching a query.

    Args:
        query: Description of the capability needed, e.g. 'word count' or 'text stats'.

    Returns:
        JSON string with a list of matching tools (name + description), or empty list.
    """
    results = registry_manager.search_tools(query)
    if not results:
        return json.dumps({"tools": [], "message": "No matching tools found."})
    tools = [{"name": r.name, "description": r.description} for r in results]
    return json.dumps({"tools": tools})


def list_available_tools() -> str:
    """List all tools currently registered in the tool registry.

    Returns:
        JSON string with list of all tool names and descriptions.
    """
    registry = registry_manager.load_registry()
    tools = [
        {"name": name, "description": data.get("description", "")}
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
        return json.dumps({"error": f"Tool '{tool_name}' not found in registry."})

    try:
        inputs = json.loads(input_data)
    except json.JSONDecodeError as e:
        return json.dumps({"error": f"Invalid input JSON: {e}"})

    try:
        importlib.invalidate_caches()
        module = importlib.import_module(entry.module)
        func = getattr(module, entry.function)
        result = func(**inputs)
        return json.dumps({"result": result})
    except Exception as e:
        return json.dumps({"error": f"Tool execution failed: {e}"})


def register_validated_tool(
    tool_name: str,
    tool_code: str,
    test_code: str,
    spec_json: str,
) -> str:
    """Validate, test, and register a new tool. Runs safety checks and sandbox tests before registration.

    Args:
        tool_name: The name for the new tool (snake_case), e.g. 'sentence_count_tool'.
        tool_code: The Python source code of the tool function.
        test_code: The pytest test code for the tool.
        spec_json: JSON string of the tool specification with fields: tool_name, description, inputs, outputs, risk_level.

    Returns:
        JSON string with registration result: success/failure and details.
    """
    tool_code = strip_code_fences(tool_code)
    test_code = strip_code_fences(test_code)

    try:
        spec = ToolSpec(**json.loads(spec_json))
    except Exception as e:
        return json.dumps({"success": False, "error": f"Invalid spec: {e}"})

    if spec.risk_level != "low":
        return json.dumps({
            "success": False,
            "error": f"Risk level '{spec.risk_level}' not allowed. Only 'low' risk tools can be auto-registered.",
        })

    is_safe, violations = validate_code_safety(tool_code)
    if not is_safe:
        return json.dumps({
            "success": False,
            "error": f"Safety check failed: {'; '.join(violations)}",
        })

    sandbox_result = run_tests(tool_code, test_code)
    if not sandbox_result.success:
        error_detail = sandbox_result.stderr or sandbox_result.stdout
        return json.dumps({
            "success": False,
            "error": f"Tests failed: {error_detail[:500]}",
            "timed_out": sandbox_result.timed_out,
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
        return json.dumps({
            "success": False,
            "error": f"Tool '{tool_name}' already exists in registry.",
        })

    return json.dumps({
        "success": True,
        "message": f"Tool '{tool_name}' registered successfully.",
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
- dependencies can ONLY include: re, json, math, string, collections, statistics, textwrap, itertools
- Do NOT include os, subprocess, socket, requests, or any network/file/system imports

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
5. Only import from these allowed modules: re, json, math, string, collections, statistics, textwrap, itertools
6. Do NOT import: os, subprocess, socket, shutil, pathlib, requests, httpx, urllib, sys
7. Do NOT use: eval(), exec(), open(), __import__(), system(), popen(), compile(), globals(), locals()
8. Handle edge cases gracefully (empty strings, None values)

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

CRITICAL: You must carefully READ and UNDERSTAND the actual code implementation \
before writing tests. Your expected values MUST match what the code will actually \
return, not what you think the ideal behavior should be.

For example, if the code uses a simple regex like `re.split(r'[.!?]', text)` to \
count sentences, then "Dr. Smith went home." would count as 3 (split on every \
period), not 2. Your tests must match the CODE's behavior, not linguistic rules.

HOW TO DETERMINE EXPECTED VALUES:
1. Read the code line by line
2. Mentally trace the execution with your test input
3. Write the expected value based on what the code ACTUALLY returns
4. If in doubt, use simpler test inputs that have unambiguous results

Generate pytest test functions. Follow these rules:

1. The function name matches tool_name from the spec (it will be auto-imported)
2. Write at least 4 test functions covering:
   - Normal input with expected output (use simple, unambiguous inputs)
   - Empty input (empty string if text-based)
   - Edge cases (whitespace-only, single character)
   - Output type validation (result is a dict with expected keys)
3. Each test function name must start with "test_"
4. Use plain assert statements
5. Do NOT import os, subprocess, or any system modules
6. Do NOT use fixtures or conftest
7. Keep test inputs SIMPLE — avoid abbreviations, special punctuation, or \
ambiguous cases that depend on linguistic intelligence the code doesn't have

Output ONLY the Python test code, no explanation, no markdown fences. The code \
must be a complete, runnable pytest file. Do NOT include an import statement for \
the tool function - it will be injected automatically.
"""


# ---------------------------------------------------------------------------
# Sub-agent definitions (Phases 7-9)
# ---------------------------------------------------------------------------

tool_spec_agent = Agent(
    name="tool_spec_agent",
    description="Designs a formal JSON specification for a new tool based on the user's need",
    model=_model,
    instruction=TOOL_SPEC_INSTRUCTION,
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

tool_creation_pipeline = SequentialAgent(
    name="tool_creation_pipeline",
    description=(
        "Creates a new tool through a 3-step pipeline: specification, code "
        "generation, and test generation. Transfer here when no existing tool "
        "matches the user's need and a new tool should be created."
    ),
    sub_agents=[tool_spec_agent, tool_coder_agent, tool_test_agent],
)


# ---------------------------------------------------------------------------
# Root agent (full version with creation pipeline)
# ---------------------------------------------------------------------------

ROOT_INSTRUCTION = """\
You are the Self-Evolving Agent, an intelligent orchestrator that manages a \
dynamic registry of tools. You can both use existing tools and create new ones.

FIRST: Decide if the user's request needs a tool at all.
- Simple questions (math, greetings, general knowledge, opinions, explanations) \
→ answer directly. Do NOT search the registry or create tools for these.
- Data processing or text transformation tasks (counting words, formatting text, \
analyzing data) → follow the TOOL WORKFLOW below.

TOOL WORKFLOW — follow these steps IN ORDER:

STEP 1 (REQUIRED FIRST): Call `search_registry` with keywords from the user's \
request. You MUST do this before anything else. Never skip this step. \
Try multiple search queries if the first one returns no results (e.g., search \
"word count", then "count words", then "word").

STEP 2: Check the search results.
  - If a matching tool is found → call `execute_registered_tool` with the tool \
name and input data as a JSON string. Present the result to the user. DONE.
  - If NO matching tool is found → continue to Step 3.

STEP 3: Transfer to `tool_creation_pipeline` to create a new tool.

STEP 4: After tool_creation_pipeline completes, read the three outputs from \
the conversation (tool spec JSON, tool code Python, test code Python). \
Call `register_validated_tool` with:
  - tool_name: the tool_name from the spec JSON
  - tool_code: the Python code (raw code only, no markdown)
  - test_code: the test code (raw code only, no markdown)
  - spec_json: the full spec JSON string

STEP 5: If registration succeeds, call `execute_registered_tool` with the \
new tool name and the user's input data. Present the result.

STEP 6: If registration fails, tell the user what went wrong. \
Do NOT retry tool creation more than once. If the second attempt also fails, \
apologize and explain the failure clearly. Do NOT loop endlessly.

Use `list_available_tools` when the user asks what tools are available.

RULES:
- Answer simple questions directly without tools (e.g., "what is 1+5?" → "6").
- NEVER skip Step 1 for data processing tasks.
- NEVER create a tool if a suitable one already exists in the registry.
- NEVER retry failed tool creation more than once (max 2 total attempts).
- Only create tools for data processing / text transformation tasks.
- Never create tools that require file I/O, network access, or system commands.
"""

root_agent = Agent(
    name="root_agent",
    model=_model,
    instruction=ROOT_INSTRUCTION,
    tools=[
        search_registry,
        list_available_tools,
        execute_registered_tool,
        register_validated_tool,
    ],
    sub_agents=[tool_creation_pipeline],
)

app = App(
    root_agent=root_agent,
    name="app",
)

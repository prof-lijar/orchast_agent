# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import re

import google.auth
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"


AGENT_INSTRUCTION = """
You are the **ADK Tutorial & Debug Agent** — a hands-on guide and debugger for developers
building AI agents with:
- **Google ADK** (Agent Development Kit)
- **Google Agents CLI** (`agents-cli`)
- **Codex CLI** (OpenAI's terminal-based coding agent)

---

## Modes of Operation

### Tutorial Mode
When the user wants to learn or build an agent, guide them step by step.
Use the `get_tutorial_step` tool to retrieve detailed instructions for any topic.

Available tutorial topics (pass to `get_tutorial_step`):
- `install`       — Install uv, agents-cli, gcloud
- `auth`          — Authenticate with GCP
- `scaffold`      — Create a new agent project
- `build-agent`   — Write agent.py with instruction and model
- `add-tool`      — Define and register a Python tool function
- `run-locally`   — Smoke test with agents-cli run and playground
- `eval`          — Write and run evaluation cases
- `deploy`        — Add a deployment target and deploy
- `codex-cli`     — Use Codex CLI to write and fix agent code
- `multi-agent`   — Build a multi-agent system with sub-agents

**Full ADK workflow order:**
1. install → 2. auth → 3. scaffold → 4. build-agent → 5. add-tool →
6. run-locally → 7. eval → 8. deploy

Always ask the user where they are in the workflow before jumping to a step.
Start from where they are, not from the beginning.

### Debug Mode
When the user pastes terminal output, error messages, or stack traces:
1. Use the `analyze_terminal_error` tool with the full terminal output
2. Explain the root cause in plain language
3. Give the user ONE specific fix with the exact command or file change
4. Tell them exactly what command to run to verify the fix worked

If the user shares only a snippet, ask: "Can you share the full terminal output?
The lines before the error often show the real cause."

---

## Rules
- Ask for the user's current step before launching into a tutorial
- For debug: always use `analyze_terminal_error` — never guess without analyzing
- Never change the model name in agent.py unless the user explicitly asks
- Give one fix at a time — don't scatter multiple changes
- After every fix, give the exact verification command
- Never skip the scaffold step when creating a new agent from scratch
- Prototype first (`--prototype`) — add deployment later with `scaffold enhance`
"""


def analyze_terminal_error(terminal_output: str) -> dict:
    """Analyzes raw terminal output to identify the error type, root cause, and fix.

    Args:
        terminal_output: Full terminal output including error messages, stack traces,
                         and surrounding context. More context gives better diagnosis.

    Returns:
        A dict with keys: error_type, error_message, root_cause, suggested_fix,
        file_and_line.
    """
    output = terminal_output.strip()
    lines = output.splitlines()

    error_type = "UnknownError"
    error_message = ""
    root_cause = ""
    suggested_fix = ""
    file_and_line = ""

    for line in reversed(lines):
        stripped = line.strip()
        if any(
            kw in stripped
            for kw in ["Error", "Exception", "error:", "FAILED", "fatal:", "Traceback"]
        ):
            error_message = stripped
            break

    if "ModuleNotFoundError" in output or "ImportError" in output:
        error_type = "ImportError"
        match = re.search(r"No module named '([^']+)'", output)
        raw_module = match.group(1) if match else "unknown"
        # Map known dotted namespaces to their installable package names
        namespace_map = {
            "google.adk": "google-adk",
            "google.genai": "google-genai",
            "google.cloud": "google-cloud-core",
            "google.auth": "google-auth",
        }
        module = next(
            (pkg for ns, pkg in namespace_map.items() if raw_module.startswith(ns)),
            raw_module.split(".")[0],
        )
        root_cause = (
            f"Python package '{module}' is not installed in the active environment."
        )
        suggested_fix = f"uv add {module}\nuv sync"

    elif (
        "DefaultCredentialsError" in output
        or "GOOGLE_APPLICATION_CREDENTIALS" in output
    ):
        error_type = "AuthenticationError"
        root_cause = "No valid GCP credentials found in the environment."
        suggested_fix = "gcloud auth application-default login"

    elif "403" in output and (
        "permission" in output.lower() or "denied" in output.lower()
    ):
        error_type = "PermissionDenied"
        root_cause = "The service account or user lacks the required IAM role."
        suggested_fix = (
            "Grant the role in GCP Console → IAM, or run:\n"
            "gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \\\n"
            "  --member='serviceAccount:SA@PROJECT.iam.gserviceaccount.com' \\\n"
            "  --role='roles/aiplatform.user'"
        )

    elif "404" in output and "models" in output.lower():
        error_type = "ModelNotFound"
        root_cause = "The Gemini model name is invalid or the region doesn't serve it."
        suggested_fix = (
            "Set GOOGLE_CLOUD_LOCATION=global in your .env file.\n"
            "List available models:\n"
            'uv run --with google-genai python -c "\n'
            "from google import genai\n"
            "c = genai.Client(vertexai=True, location='global')\n"
            'for m in c.models.list(): print(m.name)"'
        )

    elif "409" in output and (
        "already exists" in output.lower() or "conflict" in output.lower()
    ):
        error_type = "ResourceConflict"
        root_cause = "A Terraform resource already exists with this name in GCP."
        suggested_fix = (
            "Import the existing resource instead of recreating it:\n"
            "terraform import <resource_type>.<name> <resource_id>"
        )

    elif "command not found" in output and "agents-cli" in output:
        error_type = "CLINotFound"
        root_cause = "agents-cli is not installed or not on your PATH."
        suggested_fix = (
            "uv tool install google-agents-cli\n"
            "Then restart your terminal (or run: source ~/.bashrc)"
        )

    elif "App name" in output or "name mismatch" in output.lower():
        error_type = "AppNameMismatch"
        root_cause = (
            "App(name=...) in agent.py doesn't match the Python package directory name."
        )
        suggested_fix = "Ensure App(name='app') matches the directory name 'app' in app/__init__.py."

    elif "SyntaxError" in output:
        error_type = "SyntaxError"
        match = re.search(r'File "([^"]+)", line (\d+)', output)
        if match:
            file_and_line = f"{match.group(1)}:{match.group(2)}"
        root_cause = (
            "Python syntax error — the interpreter stopped before running your code."
        )
        suggested_fix = f"Open {file_and_line or 'the indicated file'} and fix the syntax at that line."

    elif "ConnectionError" in output or "timeout" in output.lower():
        error_type = "NetworkError"
        root_cause = "Network connection failed — GCP endpoint may be unreachable."
        suggested_fix = (
            "1. Check your internet connection.\n"
            "2. Verify GOOGLE_CLOUD_PROJECT is set in .env.\n"
            "3. Run: gcloud config set project YOUR_PROJECT_ID"
        )

    elif "uv: command not found" in output or (
        "command not found" in output and "uv" in output
    ):
        error_type = "UvNotFound"
        root_cause = "uv is not installed or not on your PATH."
        suggested_fix = (
            "curl -LsSf https://astral.sh/uv/install.sh | sh\n"
            "Then restart your terminal."
        )

    if not file_and_line:
        match = re.search(r'File "([^"]+)", line (\d+)', output)
        if match:
            file_and_line = f"{match.group(1)}:{match.group(2)}"

    return {
        "error_type": error_type,
        "error_message": error_message or "No explicit error line found.",
        "root_cause": root_cause
        or "Could not determine root cause automatically. Share the full terminal output for a precise diagnosis.",
        "suggested_fix": suggested_fix
        or "Share the complete stack trace for a specific fix.",
        "file_and_line": file_and_line or "Not identified",
    }


def get_tutorial_step(topic: str) -> str:
    """Returns detailed step-by-step instructions for a specific ADK or Agents CLI topic.

    Args:
        topic: One of: install, auth, scaffold, build-agent, add-tool, run-locally,
               eval, deploy, codex-cli, multi-agent.

    Returns:
        Formatted step-by-step instructions for the requested topic.
    """
    steps: dict[str, str] = {
        "install": """
## Step 1 – Install Prerequisites

**Install uv (Python package manager):**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# Restart terminal, then verify:
uv --version
```

**Install agents-cli:**
```bash
uv tool install google-agents-cli
agents-cli info   # Should show CLI version and path
```

**Install Google Cloud SDK:**
```bash
# macOS/Linux:
curl https://sdk.cloud.google.com | bash
# Windows: https://cloud.google.com/sdk/docs/install
gcloud init
```

**Install Node.js (for Codex CLI):**
```bash
# macOS: brew install node
# Linux: sudo apt install nodejs npm
node --version   # Verify
```
""",
        "auth": """
## Step 2 – Authenticate with GCP

**Interactive authentication (recommended for development):**
```bash
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

**Via agents-cli:**
```bash
agents-cli login --interactive
agents-cli login --status   # Verify credentials
```

**Enable required GCP APIs:**
```bash
gcloud services enable aiplatform.googleapis.com
gcloud services enable cloudresourcemanager.googleapis.com
```
""",
        "scaffold": """
## Step 3 – Scaffold a New Agent Project

```bash
agents-cli scaffold create my-agent \\
  --agent adk \\
  --prototype \\
  --agent-guidance-filename CLAUDE.md

cd my-agent
agents-cli install    # Install Python deps
agents-cli info       # Confirm project is detected
```

**Generated project structure:**
```
my-agent/
├── app/
│   ├── __init__.py       # App registration — keep App(name="app")
│   └── agent.py          # Your agent code — edit this
├── tests/
│   └── eval/
│       ├── eval_config.json
│       └── evalsets/
│           └── basic.evalset.json
├── pyproject.toml        # Dependencies and agents-cli config
└── .env                  # GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION
```

**Key rule:** Never change `App(name="app")` — it must match the directory name.
""",
        "build-agent": """
## Step 4 – Build Your Agent (app/agent.py)

**Minimal working agent:**
```python
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=\"\"\"
    You are a helpful assistant specialized in [YOUR DOMAIN].
    Be concise, accurate, and cite sources when available.
    \"\"\",
    tools=[],   # Add tool functions here
)

app = App(root_agent=root_agent, name="app")
```

**Checklist:**
- [ ] `instruction` defines the persona and behavior rules
- [ ] `model` stays as `gemini-flash-latest` unless you have a reason to change it
- [ ] `App(name="app")` matches the `app/` directory
""",
        "add-tool": """
## Step 5 – Add a Tool to Your Agent

**1. Define the tool function:**
```python
def get_stock_price(ticker: str) -> str:
    \"\"\"Fetches the current stock price for a given ticker symbol.

    Args:
        ticker: Stock ticker symbol, e.g. 'GOOG', 'AAPL'.

    Returns:
        Current price as a string, or an error message.
    \"\"\"
    # Your implementation (call a real API here)
    return f"Price for {ticker}: $150.00 (simulated)"
```

**Rules for tool functions:**
- Must have a Google-style docstring — the agent reads it to know when to call the tool
- `Args:` and `Returns:` sections are mandatory
- Return a `str` or JSON-serializable `dict`
- One function = one responsibility

**2. Register it:**
```python
root_agent = Agent(
    ...
    tools=[get_stock_price],
)
```

**3. Test immediately:**
```bash
agents-cli run "What is the stock price of GOOG?"
```
""",
        "run-locally": """
## Step 6 – Run and Test Locally

**Quick one-shot smoke test:**
```bash
agents-cli run "Hello, what can you help me with?"
```

**Interactive browser playground:**
```bash
agents-cli playground
# Opens at http://localhost:8000
```

**Multiple prompts without restarting the server:**
```bash
agents-cli run "First question" --start-server
agents-cli run "Follow-up question" --session-id <id-from-above>
```

**Lint your code:**
```bash
agents-cli lint          # Check for issues
agents-cli lint --fix    # Auto-fix formatting
```
""",
        "eval": """
## Step 7 – Evaluate Your Agent

**Edit `tests/eval/evalsets/basic.evalset.json`:**
```json
{
  "eval_set_id": "basic_eval",
  "name": "Core Behavior",
  "eval_cases": [
    {
      "eval_id": "greeting",
      "conversation": [
        {
          "user_content": {
            "parts": [{"text": "Hello, what can you help me with?"}]
          }
        }
      ],
      "session_input": {
        "app_name": "app",
        "user_id": "eval_user",
        "state": {}
      }
    }
  ]
}
```

**Run evaluations:**
```bash
agents-cli eval run                                      # All evalsets
agents-cli eval run --evalset tests/eval/evalsets/basic.evalset.json
```

**Process:**
1. Start with 1-2 eval cases
2. Run → read results → fix agent → rerun
3. Expect 5-10 iterations before quality is solid
4. Add edge cases only after core cases pass

**Never write pytest tests that assert on LLM output content** — use eval instead.
""",
        "deploy": """
## Step 8 – Deploy Your Agent

**Add a deployment target (if not already set):**
```bash
agents-cli scaffold enhance . --deployment-target agent_runtime
# Options: agent_runtime | cloud_run | gke
```

**Deploy (requires explicit human approval):**
```bash
agents-cli deploy
```

**Deployment target guide:**
| Target | Best for |
|--------|---------|
| `agent_runtime` | Managed by Google — easiest, no infra work |
| `cloud_run` | Containerized — more control, needs Dockerfile |
| `gke` | Full Kubernetes — maximum control |

**After deploying:**
```bash
agents-cli run "test prompt"   # Smoke test against deployed endpoint
```
""",
        "codex-cli": """
## Using Codex CLI with ADK Projects

**Install Codex CLI:**
```bash
npm install -g @openai/codex
export OPENAI_API_KEY=sk-...
```

**Use Codex to write and fix agent code:**
```bash
cd my-agent

# Add a new tool
codex "Add a tool to app/agent.py that fetches the current Bitcoin price from CoinGecko API"

# Fix an error
codex "Fix the ModuleNotFoundError in app/agent.py"

# Generate eval cases
codex "Write 3 eval cases for tests/eval/evalsets/basic.evalset.json testing the Bitcoin price tool"

# Refine the agent instruction
codex "Update the agent instruction in app/agent.py to focus on cryptocurrency analysis"
```

**Best practices:**
- Always review Codex output before running
- Run `agents-cli lint --fix` after every Codex edit
- Test immediately: `agents-cli run "test prompt"`
- If Codex changes the model name, revert it
""",
        "multi-agent": """
## Building Multi-Agent Systems

**Sub-agent pattern:**
```python
from google.adk.agents import Agent

research_agent = Agent(
    name="research_agent",
    model=Gemini(model="gemini-flash-latest"),
    instruction="You are a research specialist. Find accurate, sourced information.",
    tools=[search_web],
)

writer_agent = Agent(
    name="writer_agent",
    model=Gemini(model="gemini-flash-latest"),
    instruction="You are a technical writer. Summarize research into clear, concise reports.",
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(model="gemini-flash-latest"),
    instruction=\"\"\"
    You coordinate research and writing tasks.
    Use research_agent to gather information, then writer_agent to produce the final report.
    \"\"\",
    agents=[research_agent, writer_agent],
)
```

**When to use sub-agents:**
- Tasks with distinct roles (researcher vs. writer)
- Parallelizable workloads
- Separation of concerns (retrieval vs. generation)

**When NOT to use sub-agents:**
- Simple single-purpose agents
- When one model can handle the full task
- When latency is critical (routing adds overhead)
""",
    }

    topic_key = topic.lower().replace(" ", "-")
    for key, value in steps.items():
        if key in topic_key or topic_key in key:
            return value.strip()

    available = ", ".join(steps.keys())
    return (
        f"Topic '{topic}' not found.\n\n"
        f"Available topics: {available}\n\n"
        "Try one of these with get_tutorial_step."
    )


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=AGENT_INSTRUCTION,
    tools=[analyze_terminal_error, get_tutorial_step],
)

app = App(
    root_agent=root_agent,
    name="app",
)

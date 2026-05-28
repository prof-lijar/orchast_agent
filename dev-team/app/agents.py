"""Dev-team agent definitions."""
from __future__ import annotations

import os
from pathlib import Path

os.environ["OPENAI_API_KEY"] = "ollama"
os.environ["OPENAI_BASE_URL"] = "http://localhost:11434/v1"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"

from google.adk.agents import Agent  # noqa: E402
from google.adk.models import LiteLlm  # noqa: E402

from config import Config  # noqa: E402

_config = Config.get()


def _load_initial_goals_markdown() -> str:
    if not _config.initial_goals_file:
        return ""
    try:
        content = _config.initial_goals_file.read_text(encoding="utf-8").strip()
    except Exception:
        return ""
    return content


def _inject_branch(instruction: str) -> str:
    return instruction.replace("__DEFAULT_BRANCH__", _config.default_branch)


def _with_goals(instruction: str, role: str) -> str:
    instruction = _inject_branch(instruction)
    goals_md = _load_initial_goals_markdown()
    if not goals_md:
        return instruction
    return (
        instruction
        + "\n\n"
        + "HUMAN-PROVIDED PROJECT GOALS (HIGHEST PRIORITY):\n"
        + f"- You are the `{role}` agent.\n"
        + "- The following goals are the source of truth for what to build.\n"
        + "- Do not invent a different product. Execute these goals and break them into actionable work.\n"
        + "- If details are missing, make minimal pragmatic assumptions consistent with these goals.\n\n"
        + goals_md
        + "\n"
    )


def _make_model() -> LiteLlm:
    return LiteLlm(
        model=f"openai/{_config.model_name}",
        api_base=_config.ollama_base_url,
        api_key=_config.ollama_api_key,
        think=_config.think_enabled,
        num_ctx=_config.num_ctx,
        repeat_penalty=1.2,
        temperature=_config.temperature,
    )


_model = _make_model()

# --- Tool imports ---
from app.tools.github import (  # noqa: E402
    add_label_to_pr,
    close_issue,
    comment_on_issue,
    create_issue,
    create_pull_request,
    list_closed_issues,
    list_issue_comments,
    list_open_issues,
    list_pull_requests,
    merge_pull_request,
    remove_label_from_pr,
    review_pull_request,
    view_issue,
    view_pull_request,
)
from app.tools.git import (  # noqa: E402
    git_abort_merge,
    git_cleanup_branches,
    git_cleanup_remote_branches,
    git_commit_and_push,
    git_create_branch,
    git_current_branch,
    git_delete_branch,
    git_list_branches,
    git_log,
    git_merge_branch,
    git_pull,
    git_resolve_conflict,
    git_show_conflicts,
    git_switch_branch,
    run_command,
)
from app.tools.files import (  # noqa: E402
    append_to_file,
    delete_file,
    list_directory,
    read_file,
    search_files,
    write_file,
)
from app.tools.project_state import get_project_status  # noqa: E402
from app.tools.web import (  # noqa: E402
    web_read,
    web_search,
    web_search_and_read,
)
from app.tools.skills import (  # noqa: E402
    install_skill,
    list_skills,
    run_skill,
    skill_info,
)
from app.tools.build import (  # noqa: E402
    run_build,
    run_lint,
    run_tests,
)

# --- Prompt imports ---
from app.prompts.pm import PM_INSTRUCTION  # noqa: E402
from app.prompts.architect import ARCHITECT_INSTRUCTION  # noqa: E402
from app.prompts.frontend import FRONTEND_INSTRUCTION  # noqa: E402
from app.prompts.backend import BACKEND_INSTRUCTION  # noqa: E402
from app.prompts.qa import QA_INSTRUCTION  # noqa: E402
from app.prompts.devops import DEVOPS_INSTRUCTION  # noqa: E402

# === SHARED TOOLS (all agents get these read-only tools) ===
_shared_tools = [
    list_open_issues, view_issue, list_issue_comments,
    list_pull_requests, view_pull_request,
    read_file, list_directory, search_files, get_project_status,
    git_log, git_current_branch,
    comment_on_issue,
    web_search, web_read, web_search_and_read,
    list_skills, skill_info,
    run_build, run_tests, run_lint,
]

# === PM AGENT ===
pm_agent = Agent(
    name="pm_agent",
    model=_model,
    instruction=_with_goals(PM_INSTRUCTION, "pm"),
    tools=[
        *_shared_tools,
        close_issue,
        create_issue, list_closed_issues,
        write_file,
        git_commit_and_push,
    ],
)

# === ARCHITECT AGENT ===
architect_agent = Agent(
    name="architect_agent",
    model=_model,
    instruction=_with_goals(ARCHITECT_INSTRUCTION, "architect"),
    tools=[
        *_shared_tools,
        write_file, append_to_file, delete_file,
        git_create_branch, git_switch_branch, git_delete_branch,
        git_list_branches, git_cleanup_branches, git_cleanup_remote_branches,
        git_commit_and_push, git_pull,
        git_merge_branch, git_show_conflicts, git_resolve_conflict, git_abort_merge,
        merge_pull_request, remove_label_from_pr,
        run_skill, install_skill, run_command,
    ],
)

# === FRONTEND AGENT ===
frontend_agent = Agent(
    name="frontend_agent",
    model=_model,
    instruction=_with_goals(FRONTEND_INSTRUCTION, "frontend"),
    tools=[
        *_shared_tools,
        close_issue,
        write_file, append_to_file, delete_file,
        git_create_branch, git_switch_branch, git_delete_branch,
        git_commit_and_push, git_pull,
        create_pull_request,
        run_skill,
    ],
)

# === BACKEND AGENT ===
backend_agent = Agent(
    name="backend_agent",
    model=_model,
    instruction=_with_goals(BACKEND_INSTRUCTION, "backend"),
    tools=[
        *_shared_tools,
        close_issue,
        write_file, append_to_file, delete_file,
        git_create_branch, git_switch_branch, git_delete_branch,
        git_commit_and_push, git_pull,
        create_pull_request,
        run_skill, run_command,
    ],
)

# === QA AGENT ===
qa_agent = Agent(
    name="qa_agent",
    model=_model,
    instruction=_with_goals(QA_INSTRUCTION, "qa"),
    tools=[
        *_shared_tools,
        close_issue,
        review_pull_request,
        add_label_to_pr, remove_label_from_pr,
        create_issue,
        write_file, append_to_file,
        git_create_branch, git_switch_branch, git_delete_branch,
        git_commit_and_push, git_pull,
        create_pull_request,
        run_skill,
    ],
)

# === DEVOPS AGENT ===
devops_agent = Agent(
    name="devops_agent",
    model=_model,
    instruction=_with_goals(DEVOPS_INSTRUCTION, "devops"),
    tools=[
        *_shared_tools,
        close_issue,
        create_issue,
        write_file, append_to_file, delete_file,
        git_create_branch, git_switch_branch, git_delete_branch,
        git_commit_and_push, git_pull,
        create_pull_request,
        run_skill, install_skill, run_command,
    ],
)

AGENTS = {
    "pm": pm_agent,
    "architect": architect_agent,
    "frontend": frontend_agent,
    "backend": backend_agent,
    "qa": qa_agent,
    "devops": devops_agent,
}

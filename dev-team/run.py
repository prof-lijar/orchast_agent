#!/usr/bin/env python3
"""Dev-team runner. Autonomous AI software engineering team."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import signal
import subprocess
import sys
import time
import urllib.request
import warnings

warnings.filterwarnings("ignore", module="opentelemetry")
warnings.filterwarnings("ignore", message=".*was created in a different Context.*")
from datetime import datetime, timezone
from pathlib import Path

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from config import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("dev-team")

for _noisy in ("LiteLLM", "litellm", "LiteLLM Proxy", "LiteLLM Router",
                "httpx", "httpcore", "openai", "opentelemetry",
                "opentelemetry.trace", "opentelemetry.context",
                "google.adk", "google.auth", "google.genai",
                "grpc", "urllib3"):
    logging.getLogger(_noisy).setLevel(logging.ERROR)

import litellm  # noqa: E402
litellm.suppress_debug_info = True
litellm.set_verbose = False


class _QuietFilter(logging.Filter):
    def filter(self, record):
        msg = record.getMessage()
        return "LiteLLM" not in msg and "litellm" not in msg


for _h in logging.getLogger().handlers:
    _h.addFilter(_QuietFilter())

_shutdown_requested = False
_shutdown_count = 0


def _handle_signal(sig, frame):
    global _shutdown_requested, _shutdown_count
    _shutdown_count += 1
    if _shutdown_count >= 2:
        logger.warning("Force quit. Exiting immediately.")
        import os
        os._exit(1)
    logger.info("Shutdown requested. Press Ctrl+C again to force quit.")
    _shutdown_requested = True


signal.signal(signal.SIGINT, _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)


def check_ollama(config: Config) -> bool:
    try:
        req = urllib.request.Request(
            config.ollama_base_url.replace("/v1", "/api/tags"),
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        model_names = [m.get("name", "") for m in data.get("models", [])]
        base_name = config.model_name.split(":")[0]
        found = any(base_name in name for name in model_names)
        if not found:
            logger.warning(
                "Model '%s' not found in Ollama. Available: %s",
                config.model_name, model_names,
            )
            logger.warning("Continuing anyway — Ollama may still serve it.")
        return True
    except Exception as e:
        logger.error("Cannot reach Ollama at %s: %s", config.ollama_base_url, e)
        return False


def ensure_product_repo_cloned(config: Config) -> None:
    if config.product_repo_dir.exists() and (config.product_repo_dir / ".git").exists():
        logger.info("Product repo already cloned at %s", config.product_repo_dir)
        return
    logger.info("Cloning product repo %s to %s ...", config.product_repo, config.product_repo_dir)
    config.product_repo_dir.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["gh", "repo", "clone", config.product_repo, str(config.product_repo_dir)],
        capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        logger.error("Failed to clone: %s", result.stderr.strip())
        sys.exit(1)
    logger.info("Product repo cloned successfully.")


def ensure_labels(config: Config) -> None:
    logger.info("Ensuring repo labels exist...")
    existing = set()
    result = subprocess.run(
        ["gh", "api", f"repos/{config.product_repo}/labels", "--jq", ".[].name"],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode == 0:
        existing = set(result.stdout.strip().split("\n"))

    role_colors = {
        "pm": "0e8a16", "architect": "1d76db", "designer": "e040fb",
        "frontend": "d93f0b", "backend": "5319e7", "qa": "fbca04",
        "devops": "c5def5",
    }
    for role, label_name in config.role_labels.items():
        if label_name in existing:
            continue
        color = role_colors.get(role, "ededed")
        subprocess.run(
            ["gh", "api", f"repos/{config.product_repo}/labels",
             "-f", f"name={label_name}", "-f", f"color={color}",
             "-f", f"description=Assigned to {role.upper()} agent"],
            capture_output=True, text=True, timeout=15,
        )

    for label_name in config.priority_labels:
        if label_name in existing:
            continue
        subprocess.run(
            ["gh", "api", f"repos/{config.product_repo}/labels",
             "-f", f"name={label_name}", "-f", "color=fbca04",
             "-f", f"description=Priority: {label_name}"],
            capture_output=True, text=True, timeout=15,
        )

    for label_name in config.status_labels:
        if label_name in existing:
            continue
        subprocess.run(
            ["gh", "api", f"repos/{config.product_repo}/labels",
             "-f", f"name={label_name}", "-f", "color=c5def5",
             "-f", f"description=Status: {label_name}"],
            capture_output=True, text=True, timeout=15,
        )

    review_labels = {
        "qa:approved": ("0e8a16", "QA has approved this PR for merging"),
        "qa:changes-requested": ("d93f0b", "QA has requested changes on this PR"),
    }
    for label_name, (color, desc) in review_labels.items():
        if label_name in existing:
            continue
        subprocess.run(
            ["gh", "api", f"repos/{config.product_repo}/labels",
             "-f", f"name={label_name}", "-f", f"color={color}",
             "-f", f"description={desc}"],
            capture_output=True, text=True, timeout=15,
        )
    logger.info("Labels ready.")


def bootstrap_repo(config: Config) -> None:
    result = subprocess.run(
        ["gh", "issue", "list", "--state", "all",
         "--json", "number", "--limit", "1", "-R", config.product_repo],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode == 0:
        issues = json.loads(result.stdout)
        if issues:
            logger.info("Repo already has issues. Skipping bootstrap.")
            return

    bootstrap_body = """\
## Project Genesis — Sprint 0

This is Sprint 0 of the dev-team project. No product has been defined yet.

### PM: Your Mission

You are the Product Manager. The team can build with ANY language and tech stack.
Your first job is to decide WHAT to build AND which tech stack to use.

#### Step 1: Research and Define the Product
1. Use `web_search` to research market opportunities
2. Focus on ideas that a small AI team can realistically build:
   - Web applications (SaaS tools, dashboards, content platforms)
   - APIs and microservices (data processing, aggregation)
   - CLI tools and developer utilities
   - Productivity apps (task managers, note-taking, automation)
   - Data visualization and analytics tools
3. Write `docs/vision.md` with: product name, description, target users, value proposition
4. Write `docs/product-spec.md` with: detailed feature list, user stories, acceptance criteria

#### Step 2: Choose the Tech Stack
1. Use `list_skills` to see what the team can build with
2. Choose the best stack for the product you've defined:
   - Web apps: Next.js/React, Vue/Nuxt, Python + FastAPI, Go + templates
   - APIs: Python (FastAPI), Go, Rust, Node.js (NestJS/Express)
   - CLI tools: Go, Rust, Python
   - Data: Python, Go
3. Write `docs/tech-stack.md` with: language, framework, deployment target, and WHY

#### Step 3: Create Issues for the Team
After defining the product and stack:
1. Create an issue for **Architect** (label: role:architect): Design the system architecture and initialize the project with the chosen stack
2. Create an issue for **DevOps** (label: role:devops): Set up deployment for the chosen stack

#### Step 4: Write the Work Plan
Write `work_plan.json` to activate only yourself this cycle (other agents wait for the vision).

### Constraints:
- Fully autonomous AI engineering team — no human intervention
- ANY programming language and framework is supported
- The product must be something AI agents can build with code
- Keep it achievable: focused scope, clean implementation, working deployment
- No payment processing, no OAuth, no external databases unless needed

Build something useful. Ship it to production.
"""
    subprocess.run(
        ["gh", "issue", "create",
         "--title", "[GENESIS] Sprint 0 — Define Product Vision",
         "--body", bootstrap_body,
         "--label", "role:pm,P0-critical,status:todo",
         "-R", config.product_repo],
        capture_output=True, text=True, timeout=30,
    )
    logger.info("Bootstrap complete: Genesis issue created in product repo.")


def merge_approved_prs(config: Config) -> int:
    """Merge all qa:approved PRs into main before agents start."""
    repo = config.product_repo
    cwd = str(config.product_repo_dir)

    result = subprocess.run(
        ["gh", "pr", "list", "--state", "open", "--label", "qa:approved",
         "--json", "number,title", "-R", repo],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return 0
    try:
        prs = json.loads(result.stdout)
    except json.JSONDecodeError:
        return 0

    merged = 0
    for pr in prs:
        num = pr["number"]
        merge = subprocess.run(
            ["gh", "pr", "merge", str(num), "--squash", "--delete-branch", "-R", repo],
            capture_output=True, text=True, timeout=60,
        )
        if merge.returncode == 0:
            merged += 1
            logger.info("Auto-merged PR #%d: %s", num, pr.get("title", ""))
        else:
            logger.warning("Could not auto-merge PR #%d: %s", num, merge.stderr.strip()[:200])

    if merged > 0:
        subprocess.run(
            ["git", "pull", "origin", config.default_branch],
            cwd=cwd, capture_output=True, text=True, timeout=60,
        )
        logger.info("Merged %d approved PR(s) into %s.", merged, config.default_branch)

    return merged


def has_open_prs(config: Config) -> bool:
    """Check if there are any open PRs in the product repo."""
    result = subprocess.run(
        ["gh", "pr", "list", "--state", "open",
         "--json", "number", "--limit", "1", "-R", config.product_repo],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        return False
    try:
        return len(json.loads(result.stdout)) > 0
    except (json.JSONDecodeError, TypeError):
        return False


def has_open_issues(config: Config, role: str) -> bool:
    """Check if an agent has open issues assigned to it."""
    label = config.role_labels.get(role, f"role:{role}")
    result = subprocess.run(
        ["gh", "issue", "list", "--state", "open", "--label", label,
         "--json", "number", "--limit", "1", "-R", config.product_repo],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        return False
    try:
        return len(json.loads(result.stdout)) > 0
    except (json.JSONDecodeError, TypeError):
        return False


def ensure_main_branch(config: Config) -> None:
    cwd = str(config.product_repo_dir)
    subprocess.run(
        ["git", "checkout", "."],
        cwd=cwd, capture_output=True, text=True, timeout=10,
    )
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=cwd, capture_output=True, text=True, timeout=10,
    )
    if result.returncode == 0:
        current = result.stdout.strip()
        if current != config.default_branch:
            logger.warning(
                "On branch '%s', switching to '%s'",
                current, config.default_branch,
            )
            subprocess.run(
                ["git", "checkout", config.default_branch],
                cwd=cwd, capture_output=True, text=True, timeout=30,
            )
    subprocess.run(
        ["git", "pull", "origin", config.default_branch],
        cwd=cwd, capture_output=True, text=True, timeout=60,
    )


async def run_agent_turn(
    runner: Runner,
    session_service: InMemorySessionService,
    role: str,
    config: Config,
    cycle_number: int,
    turn_number: int = 1,
    total_turns: int = 1,
) -> None:
    state = {
        "role": role,
        "product_repo": config.product_repo,
        "cycle_number": str(cycle_number),
        "turn_number": str(turn_number),
        "total_turns": str(total_turns),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    session = await session_service.create_session(
        app_name="dev-team",
        user_id=f"agent-{role}",
        state=state,
    )

    turn_info = f"Turn {turn_number}/{total_turns}. " if total_turns > 1 else ""

    prompt = (
        f"Cycle {cycle_number}. {turn_info}You are the {role.upper()} agent. "
        f"Current time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}. "
        f"Execute your duties now.\n\n"
        f"MANDATORY STEPS:\n"
        f"1. Call `list_open_issues` with label='role:{role}' to find your work.\n"
        f"2. Do the work: write files, commit, push, create PRs, etc.\n"
        f"3. AFTER completing work for an issue, you MUST call `close_issue` with the issue number.\n"
        f"   This is NOT optional. Every completed issue MUST be closed by calling the tool.\n"
        f"4. After writing files, call `git_commit_and_push` to save your work.\n"
        f"5. If you have NO assigned issues and nothing new to create, STOP immediately.\n\n"
        f"Do NOT just think about what you did — call the tools. Do NOT summarize — take ACTION or stop."
    )

    message = types.Content(
        role="user",
        parts=[types.Part.from_text(text=prompt)],
    )

    max_tool_calls = 30
    tool_call_count = 0
    consecutive_text_only = 0
    max_idle_rounds = 2

    async for event in runner.run_async(
        user_id=f"agent-{role}",
        session_id=session.id,
        new_message=message,
    ):
        if _shutdown_requested:
            logger.info("[%s] Shutdown requested, aborting turn.", role.upper())
            return

        if event.content and event.content.parts:
            has_tool_call = False
            for part in event.content.parts:
                if getattr(part, "thought", False) and part.text:
                    if config.stream_enabled:
                        thought = part.text.strip()
                        if thought:
                            for line in thought.split("\n")[:3]:
                                logger.info("[%s] 💭 %s", role.upper(), line[:200])
                elif part.text:
                    if config.stream_enabled:
                        text = part.text.strip()
                        if text:
                            for line in text.split("\n")[:5]:
                                logger.info("[%s] %s", role.upper(), line[:200])
                if getattr(part, "function_call", None):
                    fc = part.function_call
                    args_str = json.dumps(dict(fc.args), ensure_ascii=False)[:150] if fc.args else ""
                    logger.info("[%s] 🔧 %s(%s)", role.upper(), fc.name, args_str)
                    has_tool_call = True
                    tool_call_count += 1
                    consecutive_text_only = 0
                    if tool_call_count >= max_tool_calls:
                        logger.warning(
                            "[%s] Hit %d tool calls, ending turn.",
                            role.upper(), max_tool_calls,
                        )
                        return
                if getattr(part, "function_response", None):
                    if config.stream_enabled:
                        fr = part.function_response
                        resp_str = str(fr.response)[:150] if fr.response else ""
                        logger.info("[%s] ← %s: %s", role.upper(), fr.name, resp_str)

            if not has_tool_call and event.content.parts:
                has_real_text = any(
                    getattr(p, "text", None)
                    and p.text.strip()
                    and "<|im_start|>" not in p.text
                    and "<|im_end|>" not in p.text
                    for p in event.content.parts
                )
                has_garbage = any(
                    getattr(p, "text", None)
                    and ("<|im_start|>" in p.text or "<|im_end|>" in p.text)
                    for p in event.content.parts
                )
                if has_garbage:
                    logger.warning("[%s] Token leakage detected, ending turn.", role.upper())
                    return
                if has_real_text:
                    consecutive_text_only += 1
                    if consecutive_text_only >= max_idle_rounds:
                        logger.warning(
                            "[%s] Idle loop detected (%d text responses with no tool calls). Ending turn.",
                            role.upper(), consecutive_text_only,
                        )
                        return


def flush_and_push(config: Config, role: str) -> None:
    cwd = str(config.product_repo_dir)
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=cwd, capture_output=True, text=True, timeout=10,
    )
    if status.returncode != 0 or not status.stdout.strip():
        return

    subprocess.run(["git", "add", "."], cwd=cwd, capture_output=True, text=True, timeout=10)
    result = subprocess.run(
        ["git", "commit", "-m", f"[{role.upper()}] auto-push updates"],
        cwd=cwd, capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        return

    push = subprocess.run(
        ["git", "push", "origin", "HEAD"],
        cwd=cwd, capture_output=True, text=True, timeout=120,
    )
    if push.returncode == 0:
        logger.info("[%s] Pushed updates to GitHub.", role.upper())
    else:
        logger.warning("[%s] Push failed: %s", role.upper(), push.stderr.strip())


_DEVELOPER_ROLES = {"designer", "frontend", "backend", "devops"}


async def run_review_merge_cycle(
    runners: dict,
    session_service: InMemorySessionService,
    config: Config,
    cycle_number: int,
) -> None:
    """Run QA review + Architect merge to clear open PRs between developer turns."""
    if "qa" in runners:
        ensure_main_branch(config)
        logger.info("--- Review cycle | QA ---")
        try:
            await asyncio.wait_for(
                run_agent_turn(runners["qa"], session_service, "qa", config, cycle_number),
                timeout=config.agent_timeout_seconds,
            )
        except (asyncio.TimeoutError, GeneratorExit, ValueError):
            pass
        except Exception:
            logger.exception("[QA] Review cycle failed")
        flush_and_push(config, "qa")

    if "architect" in runners:
        ensure_main_branch(config)
        logger.info("--- Review cycle | ARCHITECT (merge) ---")
        try:
            await asyncio.wait_for(
                run_agent_turn(runners["architect"], session_service, "architect", config, cycle_number),
                timeout=config.agent_timeout_seconds,
            )
        except (asyncio.TimeoutError, GeneratorExit, ValueError):
            pass
        except Exception:
            logger.exception("[ARCHITECT] Review cycle failed")
        flush_and_push(config, "architect")

    ensure_main_branch(config)
    merged = merge_approved_prs(config)
    if merged:
        logger.info("Review cycle merged %d PR(s).", merged)


def read_work_plan(config: Config) -> list[dict]:
    """Read the PM's work plan for this cycle."""
    plan_path = config.product_repo_dir / "work_plan.json"
    if not plan_path.exists():
        logger.warning("No work_plan.json found. Falling back to all agents x1 turn.")
        return [{"role": r, "turns": 1} for r in config.agent_roles if r != "pm"]

    try:
        with open(plan_path) as f:
            plan = json.load(f)

        assignments = plan.get("assignments", [])
        reasoning = plan.get("cycle_reasoning", "")
        phase = plan.get("current_phase", "")
        if reasoning:
            logger.info("[PM PLAN] %s (phase: %s)", reasoning[:200], phase)

        valid = []
        for a in assignments:
            role = a.get("role", "")
            turns = a.get("turns", 0)
            if role in config.agent_roles and role != "pm" and turns > 0:
                turns = min(turns, 5)
                valid.append({"role": role, "turns": turns})

        if not valid:
            logger.warning("Work plan has no valid assignments. Falling back to architect x1.")
            return [{"role": "architect", "turns": 1}]

        return valid

    except (json.JSONDecodeError, KeyError) as e:
        logger.warning("Invalid work_plan.json: %s. Falling back.", e)
        return [{"role": r, "turns": 1} for r in config.agent_roles if r != "pm"]


async def run_cycle(
    runners: dict[str, Runner],
    session_service: InMemorySessionService,
    config: Config,
    cycle_number: int,
) -> None:
    if _shutdown_requested:
        return

    ensure_main_branch(config)
    logger.info("--- Cycle %d | PM (planning) ---", cycle_number)

    pm_start = time.time()
    try:
        await asyncio.wait_for(
            run_agent_turn(runners["pm"], session_service, "pm", config, cycle_number),
            timeout=config.agent_timeout_seconds,
        )
    except asyncio.TimeoutError:
        logger.warning("[PM] Timed out after %ds", config.agent_timeout_seconds)
    except (GeneratorExit, ValueError):
        pass
    except Exception:
        logger.exception("[PM] Failed")

    flush_and_push(config, "pm")
    logger.info("[PM] Done in %.1fs", time.time() - pm_start)

    ensure_main_branch(config)
    merged_count = merge_approved_prs(config)
    if merged_count:
        logger.info("Pre-cycle merge: %d PR(s) merged into %s", merged_count, config.default_branch)

    assignments = read_work_plan(config)

    total_agent_turns = sum(a["turns"] for a in assignments)
    agent_names = ", ".join(f"{a['role']}x{a['turns']}" for a in assignments)
    logger.info("Work plan: %s (%d total turns)", agent_names, total_agent_turns)

    for assignment in assignments:
        role = assignment["role"]
        turns = assignment["turns"]

        if _shutdown_requested:
            logger.info("Shutdown requested, stopping cycle.")
            return

        runner = runners.get(role)
        if not runner:
            logger.warning("No runner for role '%s', skipping.", role)
            continue

        for turn in range(1, turns + 1):
            if _shutdown_requested:
                break

            # Auto-merge approved PRs before every agent turn
            ensure_main_branch(config)
            merged = merge_approved_prs(config)
            if merged:
                logger.info("Pre-turn merge: %d PR(s) merged into %s", merged, config.default_branch)

            # Skip remaining turns if agent has no work
            if turn > 1 and not has_open_issues(config, role) and not (role == "architect" and has_open_prs(config)):
                logger.info("[%s] No open issues — skipping remaining %d turn(s).", role.upper(), turns - turn + 1)
                break

            logger.info("--- Cycle %d | %s (turn %d/%d) ---", cycle_number, role.upper(), turn, turns)

            start = time.time()
            try:
                await asyncio.wait_for(
                    run_agent_turn(
                        runner, session_service, role, config, cycle_number,
                        turn_number=turn, total_turns=turns,
                    ),
                    timeout=config.agent_timeout_seconds,
                )
            except asyncio.TimeoutError:
                logger.warning("[%s] Timed out after %ds", role, config.agent_timeout_seconds)
            except (GeneratorExit, ValueError):
                pass
            except Exception:
                logger.exception("[%s] Failed", role)

            flush_and_push(config, role)
            elapsed = time.time() - start
            logger.info("[%s] Turn %d/%d done in %.1fs", role.upper(), turn, turns, elapsed)

            if role in _DEVELOPER_ROLES and turn < turns and has_open_prs(config):
                logger.info(
                    "Open PRs after %s turn %d — running review-merge cycle before next turn",
                    role.upper(), turn,
                )
                await run_review_merge_cycle(
                    runners, session_service, config, cycle_number,
                )


def _normalize_repo(raw: str | list[str]) -> str:
    """Extract owner/name slug from a git URL or pass through as-is.

    Accepts a single string or a list (e.g. ["repo", "git@github.com:o/r.git"]).
    When given a list, picks the entry that looks like a valid repo identifier.
    """
    import re

    def _parse_one(val: str) -> str | None:
        m = re.match(r"git@github\.com:(.+?)(?:\.git)?$", val)
        if m:
            return m.group(1)
        m = re.match(r"https?://github\.com/(.+?)(?:\.git)?$", val)
        if m:
            return m.group(1)
        if "/" in val:
            return val
        return None

    if isinstance(raw, list):
        for entry in reversed(raw):
            result = _parse_one(entry)
            if result:
                return result
        return raw[-1]

    return _parse_one(raw) or raw


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="dev-team",
        description="Autonomous AI software engineering team. "
        "Point it at any GitHub repo and the team will plan, build, test, and deploy.",
    )
    parser.add_argument(
        "repo",
        nargs="+",
        help="GitHub repo slug (owner/name) or git URL. "
        "Examples: myorg/my-app, git@github.com:myorg/my-app.git, "
        "https://github.com/myorg/my-app.git",
    )
    parser.add_argument(
        "--model", "-m",
        help="Ollama model name (default: gemma4:31b).",
    )
    parser.add_argument(
        "--branch", "-b",
        help="Default branch (default: main).",
    )
    parser.add_argument(
        "--timeout", "-t",
        type=int,
        help="Per-agent timeout in seconds (default: 1800).",
    )
    parser.add_argument(
        "--interval", "-i",
        type=int,
        help="Seconds between cycles (default: 0 = continuous).",
    )
    parser.add_argument(
        "--cycles", "-n",
        type=int,
        default=0,
        help="Max cycles to run (default: 0 = unlimited).",
    )
    parser.add_argument(
        "--no-think",
        action="store_true",
        default=None,
        help="Disable model thinking mode for all agents.",
    )
    parser.add_argument(
        "--stream",
        action="store_true",
        default=None,
        help="Stream agent thought/text/tool activity live.",
    )
    parser.add_argument(
        "--goals",
        help="Path to a markdown file with initial product goals/requirements.",
    )
    parser.add_argument(
        "--repo-dir",
        help="Local path for cloning the product repo (default: ./repos/<repo-slug>).",
    )
    parser.add_argument(
        "--num-ctx",
        type=int,
        help="LLM context window size (default: 32768).",
    )
    parser.add_argument(
        "--skills-dir",
        help="Path to skills directory (default: ./skills).",
    )
    parser.add_argument(
        "--trusted-sources",
        help="Comma-separated trusted skill source URL prefixes.",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    config = Config.from_cli({
        "product_repo": _normalize_repo(args.repo),
        "model_name": args.model,
        "think_enabled": (False if args.no_think else None),
        "stream_enabled": (True if args.stream else None),
        "default_branch": args.branch,
        "agent_timeout_seconds": args.timeout,
        "cycle_interval_seconds": args.interval,
        "initial_goals_file": args.goals,
        "product_repo_dir": args.repo_dir,
        "num_ctx": args.num_ctx,
        "skills_dir": args.skills_dir,
        "trusted_skill_sources": args.trusted_sources,
    })

    logger.info("=" * 60)
    logger.info("  DEV-TEAM — Autonomous AI Engineering Team")
    logger.info("  Model: %s", config.model_name)
    logger.info("  Think mode: %s", "on" if config.think_enabled else "off")
    logger.info("  Stream logs: %s", "on" if config.stream_enabled else "off")
    logger.info("  Product Repo: %s", config.product_repo)
    logger.info("  Product Dir: %s", config.product_repo_dir)
    logger.info("  Cycle interval: %ds", config.cycle_interval_seconds)
    logger.info("  Agent timeout: %ds", config.agent_timeout_seconds)
    logger.info("  Skills: %s", config.skills_dir)
    if config.initial_goals_file:
        logger.info("  Initial goals: %s", config.initial_goals_file)
    logger.info("  Scheduling: PM-driven dynamic")
    logger.info("=" * 60)

    if config.initial_goals_file and not config.initial_goals_file.exists():
        logger.error("Initial goals file not found: %s", config.initial_goals_file)
        sys.exit(1)

    if not check_ollama(config):
        logger.error("Ollama is not running. Start it with: ollama serve")
        sys.exit(1)

    ensure_product_repo_cloned(config)
    ensure_labels(config)
    bootstrap_repo(config)

    # Ensure agents importing Config.from_env() see CLI-resolved values.
    os.environ["AGENT_MODEL"] = config.model_name
    os.environ["AGENT_THINK"] = "true" if config.think_enabled else "false"
    os.environ["AGENT_STREAM"] = "true" if config.stream_enabled else "false"
    os.environ["PRODUCT_REPO"] = config.product_repo
    os.environ["PRODUCT_REPO_DIR"] = str(config.product_repo_dir)
    if config.initial_goals_file:
        os.environ["INITIAL_GOALS_FILE"] = str(config.initial_goals_file)

    from app.agents import AGENTS

    session_service = InMemorySessionService()
    runners: dict[str, Runner] = {}

    for role, agent in AGENTS.items():
        runners[role] = Runner(
            agent=agent,
            app_name="dev-team",
            session_service=session_service,
        )

    max_cycles = args.cycles
    cycle_number = 1
    logger.info("Dev-team is online. Press Ctrl+C to shut down.")
    if max_cycles > 0:
        logger.info("Will run %d cycle(s) then stop.", max_cycles)

    while not _shutdown_requested:
        if max_cycles > 0 and cycle_number > max_cycles:
            logger.info("Reached max cycles (%d). Stopping.", max_cycles)
            break

        cycle_start = time.time()
        logger.info("===== CYCLE %d START =====", cycle_number)

        await run_cycle(runners, session_service, config, cycle_number)

        elapsed = time.time() - cycle_start
        logger.info("===== CYCLE %d END (%.1fs) =====", cycle_number, elapsed)

        remaining = max(0, config.cycle_interval_seconds - elapsed)
        if remaining > 0 and not _shutdown_requested:
            logger.info("Next cycle in %.0fs...", remaining)
        while remaining > 0 and not _shutdown_requested:
            await asyncio.sleep(min(5, remaining))
            remaining -= 5

        cycle_number += 1

    logger.info("Dev-team shut down after %d cycles. Goodbye!", cycle_number - 1)


if __name__ == "__main__":
    asyncio.run(main())

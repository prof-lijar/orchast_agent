#!/usr/bin/env python3
"""Multi-agent scientific paper writer using local Ollama models.

Usage:
    # Local spec file:
    python run_paper.py --spec paper-spec.json --model gemma4:31b

    # With streaming output:
    python run_paper.py --spec paper-spec.json --model gemma4:31b --stream

    # GitHub URL:
    python run_paper.py --spec https://github.com/user/repo/blob/main/paper/spec.json --model gemma4:31b

    # Resume after interruption:
    python run_paper.py --spec paper-spec.json --model gemma4:31b --resume
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

logger = logging.getLogger("scie_paper_writer")

LANGUAGE_NAMES = {
    "ar": "Arabic", "bn": "Bengali", "de": "German", "en": "English",
    "es": "Spanish", "fr": "French", "hi": "Hindi", "id": "Indonesian",
    "it": "Italian", "ja": "Japanese", "ko": "Korean", "ms": "Malay",
    "my": "Burmese (Myanmar)", "nl": "Dutch", "pl": "Polish",
    "pt": "Portuguese", "ru": "Russian", "sv": "Swedish", "th": "Thai",
    "tr": "Turkish", "uk": "Ukrainian", "vi": "Vietnamese", "zh": "Chinese",
}

AGENT_NAME_MAP = {
    "ingestion": "ingestion_agent",
    "outline": "outline_agent",
    "writer": "writer_agent",
    "reviewer": "reviewer_agent",
    "finalizer": "finalizer_agent",
}


def _language_name(code: str) -> str:
    return LANGUAGE_NAMES.get(code, code)


GITHUB_BLOB_RE = re.compile(
    r"https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/blob/(?P<branch>[^/]+)/(?P<path>.+)"
)


def resolve_github_spec(url: str, clone_base: str = "./repos") -> dict:
    import subprocess

    m = GITHUB_BLOB_RE.match(url)
    if not m:
        raise ValueError(
            f"Not a valid GitHub blob URL: {url}\n"
            "Expected: https://github.com/owner/repo/blob/branch/path/to/spec.json"
        )

    owner = m.group("owner")
    repo = m.group("repo")
    branch = m.group("branch")
    file_path = m.group("path")

    repo_url = f"https://github.com/{owner}/{repo}.git"
    repo_dir = Path(clone_base) / repo
    spec_path = repo_dir / file_path

    if (repo_dir / ".git").exists():
        logger.info("Repo already cloned at %s — pulling latest", repo_dir)
        subprocess.run(
            ["git", "pull", "origin", branch],
            cwd=str(repo_dir),
            check=True,
            timeout=120,
            capture_output=True,
        )
    else:
        logger.info("Cloning %s into %s", repo_url, repo_dir)
        repo_dir.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "clone", "-b", branch, repo_url, str(repo_dir)],
            check=True,
            timeout=120,
        )

    if not spec_path.exists():
        raise FileNotFoundError(f"Spec file not found at {spec_path}")

    return {
        "spec_path": str(spec_path),
        "repo_dir": str(repo_dir),
        "branch": branch,
        "repo_url": repo_url,
    }


def is_github_url(s: str) -> bool:
    return s.startswith("https://github.com/") or s.startswith("http://github.com/")


def setup_logging(output_dir: str) -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)

    logfile = logging.FileHandler(out / "scie_paper_writer.log")
    logfile.setFormatter(formatter)

    logger.setLevel(logging.INFO)
    logger.addHandler(console)
    logger.addHandler(logfile)


def check_ollama(model: str) -> bool:
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        available = [m["name"] for m in data.get("models", [])]
        matched = any(model in name or name.startswith(model) for name in available)
        if not matched:
            logger.error(
                "Model '%s' not found in Ollama. Available: %s",
                model,
                ", ".join(available),
            )
            logger.error("Pull it with: ollama pull %s", model)
            return False
        logger.info("Ollama OK — model '%s' available", model)
        return True
    except Exception as e:
        logger.error("Cannot reach Ollama at localhost:11434: %s", e)
        logger.error("Start Ollama with: ollama serve")
        return False


async def run_paper(
    runner: Runner,
    session_service: InMemorySessionService,
    spec: dict,
    source_materials: str,
    agent_order: list[str],
    stream: bool = False,
) -> str | None:
    lang = spec.get("language", "")
    if lang and lang.lower() != "en":
        lang_name = _language_name(lang)
        language_instruction = (
            f"\n\nIMPORTANT: You MUST write ALL content in {lang_name}. "
            f"Every sentence and paragraph must be in {lang_name}. "
            f"Do NOT write in English. Technical terms may remain in English, "
            f"but all explanatory text must be in {lang_name}."
        )
    else:
        language_instruction = ""

    guidelines = spec.get("writing_guidelines", [])
    if guidelines:
        lines = "\n".join(f"- {g}" for g in guidelines)
        writing_guidelines = f"\n\nWriting guidelines:\n{lines}"
    else:
        writing_guidelines = ""

    sections = spec.get("sections", [])
    sections_list = "\n".join(
        f"- {s['name']}: {s.get('description', '')}" for s in sections
    )

    authors = ", ".join(spec.get("authors", [])) or "Not specified"

    state = {
        "paper_title": spec["title"],
        "paper_description": spec.get("description", ""),
        "authors": authors,
        "sections_list": sections_list,
        "total_sections": str(len(sections)),
        "source_materials": source_materials,
        "target_word_count": spec.get("target_word_count", "5000-8000"),
        "language_instruction": language_instruction,
        "writing_guidelines": writing_guidelines,
    }

    session = await session_service.create_session(
        app_name="scie_paper_writer",
        user_id="scie_paper_writer",
        state=state,
    )

    prompt = (
        f"Write a research paper titled \"{spec['title']}\". "
        f"Use the provided source materials to write a complete, publication-ready paper."
    )

    message = types.Content(
        role="user",
        parts=[types.Part.from_text(text=prompt)],
    )

    last_agent = agent_order[-1] if agent_order else "finalizer_agent"

    run_config = None
    if stream:
        run_config = RunConfig(streaming_mode=StreamingMode.SSE)

    final_text = ""
    current_author = None
    async for event in runner.run_async(
        user_id="scie_paper_writer",
        session_id=session.id,
        new_message=message,
        run_config=run_config,
    ):
        if stream:
            if getattr(event, "turn_complete", False) and current_author:
                idx = agent_order.index(current_author) if current_author in agent_order else -1
                if idx >= 0 and idx + 1 < len(agent_order):
                    next_agent = agent_order[idx + 1]
                    print(f"\n[{current_author} done → {next_agent} starting...]", flush=True)
                else:
                    print(f"\n[{current_author} done]", flush=True)

            if event.content and event.content.parts:
                if event.author != current_author:
                    if current_author is not None:
                        print(flush=True)
                    current_author = event.author
                    print(f"\n[{event.author}]", flush=True)

                if getattr(event, "partial", False):
                    for part in event.content.parts:
                        if part.text:
                            print(part.text, end="", flush=True)

        if (
            event.content
            and event.content.parts
            and event.author == last_agent
            and not getattr(event, "partial", False)
        ):
            for part in event.content.parts:
                if part.text:
                    final_text = part.text

    if stream and current_author is not None:
        print(flush=True)

    if not final_text:
        session = await session_service.get_session(
            app_name="scie_paper_writer",
            user_id="scie_paper_writer",
            session_id=session.id,
        )
        output_keys = ["paper_final", "paper_revised", "paper_draft", "paper_outline", "research_context"]
        for key in output_keys:
            final_text = session.state.get(key, "")
            if final_text:
                break

    return final_text if final_text else None


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Multi-agent scientific paper writer",
        epilog=(
            "Examples:\n"
            "  python run_paper.py --spec paper-spec.json --model gemma4:31b\n"
            "  python run_paper.py --spec paper-spec.json --model gemma4:31b --stream\n"
            "  python run_paper.py --spec https://github.com/user/repo/blob/main/paper/spec.json --model gemma4:31b\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--spec", required=True,
        help="Path or GitHub URL to paper specification file (JSON/YAML)",
    )
    parser.add_argument("--output-dir", default="./paper", help="Output directory (default: ./paper)")
    parser.add_argument("--model", required=True, help="Ollama model name (e.g. gemma4:31b)")
    parser.add_argument("--clone-dir", default="./repos", help="Base directory for cloned repos (default: ./repos)")
    parser.add_argument("--retry", type=int, default=3, help="Retries on failure (default: 3)")
    parser.add_argument("--resume", action="store_true", help="Resume from progress")
    parser.add_argument("--timeout", type=int, default=1800, help="Timeout per agent in seconds (default: 1800)")
    parser.add_argument("--words", default=None, help="Target word count range override (e.g. 5000-8000)")
    parser.add_argument("--stream", action="store_true", help="Stream LLM output to console in real-time")
    parser.add_argument("--no-think", action="store_true", help="Disable model thinking")
    parser.add_argument("--num-ctx", type=int, default=32768, help="Context window size (default: 32768)")
    parser.add_argument("--repeat-penalty", type=float, default=1.2, help="Repetition penalty (default: 1.2)")
    parser.add_argument(
        "--agents", default="ingestion,outline,writer,reviewer,finalizer",
        help="Comma-separated pipeline stages (default: ingestion,outline,writer,reviewer,finalizer)",
    )
    parser.add_argument("--no-push", action="store_true", help="Skip git push (commit only)")
    parser.add_argument("--lang", default=None, help="Language override (e.g. ko, es, fr)")
    args = parser.parse_args()

    # Resolve spec path
    if is_github_url(args.spec):
        gh = resolve_github_spec(args.spec, clone_base=args.clone_dir)
        spec_path = gh["spec_path"]
    else:
        spec_path = args.spec

    setup_logging(args.output_dir)

    logger.info("SciePaperWriter starting — model: %s", args.model)

    if not check_ollama(args.model):
        sys.exit(1)

    from app.agent import build_pipeline
    from app.tools import (
        collect_sources,
        git_commit_and_push_sync,
        load_progress,
        parse_spec,
        save_paper_to_disk,
        save_progress,
    )

    spec = parse_spec(spec_path)

    if args.words:
        spec["target_word_count"] = args.words
    if args.lang:
        spec["language"] = args.lang

    requested_agents = [a.strip() for a in args.agents.split(",") if a.strip()]
    agent_order = [AGENT_NAME_MAP[a] for a in requested_agents if a in AGENT_NAME_MAP]

    logger.info("=" * 60)
    logger.info("Paper: %s", spec["title"])
    logger.info("Authors: %s", ", ".join(spec.get("authors", [])) or "Not specified")
    logger.info("Sections: %d", len(spec.get("sections", [])))
    logger.info("Structure: %s", spec.get("structure", "custom"))
    logger.info("Sources: %d", len(spec.get("sources", [])))
    logger.info("Pipeline: %s", " → ".join(requested_agents))
    logger.info("Model: %s (ctx=%d, repeat_penalty=%.1f, think=%s)",
                args.model, args.num_ctx, args.repeat_penalty, not args.no_think)
    logger.info("=" * 60)

    # Collect source materials
    logger.info("Collecting source materials...")
    source_materials = collect_sources(spec.get("sources", []), clone_dir=args.clone_dir)
    source_word_count = len(source_materials.split())
    logger.info("Source materials collected: %d words", source_word_count)

    # Check progress for resume
    progress = load_progress(args.output_dir)
    if args.resume and progress.get("completed_agents"):
        logger.info("Resuming — previously completed: %s", ", ".join(progress["completed_agents"]))

    # Build pipeline from CLI args
    pipeline = build_pipeline(
        model=args.model,
        num_ctx=args.num_ctx,
        repeat_penalty=args.repeat_penalty,
        timeout=args.timeout,
        no_think=args.no_think,
        agents=requested_agents,
    )

    session_service = InMemorySessionService()
    runner = Runner(
        agent=pipeline,
        app_name="scie_paper_writer",
        session_service=session_service,
    )

    start_time = time.time()
    content = None

    for attempt in range(1, args.retry + 1):
        try:
            logger.info("--- Attempt %d/%d ---", attempt, args.retry)

            content = await asyncio.wait_for(
                run_paper(runner, session_service, spec, source_materials, agent_order, stream=args.stream),
                timeout=args.timeout * len(requested_agents),
            )

            if content:
                elapsed = time.time() - start_time
                logger.info("Paper written in %.1f minutes", elapsed / 60)
                break
            else:
                logger.warning("Pipeline returned empty content")

        except asyncio.TimeoutError:
            logger.warning("Attempt %d timed out", attempt)
        except Exception:
            logger.exception("Attempt %d failed", attempt)

    if content:
        result = save_paper_to_disk(spec["title"], content, args.output_dir)
        logger.info("Saved: %s (%d words)", result["filename"], result["word_count"])

        progress["completed_agents"] = requested_agents
        progress["finished_at"] = datetime.now(timezone.utc).isoformat()
        save_progress(args.output_dir, progress)

        if not args.no_push:
            git_result = git_commit_and_push_sync(spec["title"], args.output_dir)
            if git_result["success"]:
                pushed = "pushed" if git_result.get("pushed") else "committed only"
                logger.info("Git: %s (%s)", git_result["message"], pushed)
            else:
                logger.warning("Git: %s", git_result["message"])

        elapsed_total = time.time() - start_time
        logger.info("=" * 60)
        logger.info("PAPER COMPLETE")
        logger.info("Title: %s", spec["title"])
        logger.info("Output: %s", result["file_path"])
        logger.info("Words: %d", result["word_count"])
        logger.info("Time: %.1f minutes", elapsed_total / 60)
        logger.info("=" * 60)
    else:
        logger.error("FAILED: Paper could not be generated after %d attempts", args.retry)
        progress["failed"] = {"reason": f"Failed after {args.retry} attempts"}
        save_progress(args.output_dir, progress)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

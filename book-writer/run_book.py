#!/usr/bin/env python3
"""Overnight book-writing runner.

Usage:
    python run_book.py --toc toc.json
    python run_book.py --toc toc.json --output-dir ./my-book --model gemma4:27b
    python run_book.py --toc toc.json --resume
    python run_book.py --toc toc.json --repo https://github.com/user/book.git
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.tools import (
    git_commit_and_push_sync,
    load_progress,
    parse_toc,
    save_chapter_to_disk,
    save_progress,
)

logger = logging.getLogger("book-writer")


def setup_logging(output_dir: str) -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)

    logfile = logging.FileHandler(out / "book-writer.log")
    logfile.setFormatter(formatter)

    logger.setLevel(logging.INFO)
    logger.addHandler(console)
    logger.addHandler(logfile)


def check_ollama(model: str) -> bool:
    """Verify Ollama is running and the model is available."""
    try:
        resp = httpx.get("http://localhost:11434/api/tags", timeout=10)
        resp.raise_for_status()
        available = [m["name"] for m in resp.json().get("models", [])]
        # Match with or without tag suffix
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


def setup_git_repo(output_dir: str, repo_url: str | None, branch: str) -> None:
    """Initialize or clone a git repo in the output directory."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    if (out / ".git").exists():
        logger.info("Git repo already exists at %s", out)
        return

    if repo_url:
        logger.info("Cloning %s into %s", repo_url, out)
        subprocess.run(
            ["git", "clone", repo_url, str(out)],
            check=True,
            timeout=120,
        )
    else:
        logger.info("Initializing new git repo at %s", out)
        subprocess.run(["git", "init"], cwd=str(out), check=True, timeout=30)
        subprocess.run(
            ["git", "checkout", "-b", branch],
            cwd=str(out),
            capture_output=True,
            timeout=30,
        )


async def run_chapter(
    runner: Runner,
    session_service: InMemorySessionService,
    toc: dict,
    chapter: dict,
) -> str | None:
    """Run the 4-phase pipeline for a single chapter. Returns the final content."""
    state = {
        "book_title": toc["title"],
        "book_description": toc.get("description", ""),
        "current_chapter_number": str(chapter["number"]),
        "current_chapter_title": chapter["title"],
        "current_chapter_description": chapter.get("description", ""),
        "total_chapters": str(len(toc["chapters"])),
    }

    session = await session_service.create_session(
        app_name="book-writer",
        user_id="book-writer",
        state=state,
    )

    prompt = (
        f"Write Chapter {chapter['number']}: {chapter['title']}. "
        f"Description: {chapter.get('description', 'No additional description.')}"
    )

    message = types.Content(
        role="user",
        parts=[types.Part.from_text(text=prompt)],
    )

    final_text = ""
    async for event in runner.run_async(
        user_id="book-writer",
        session_id=session.id,
        new_message=message,
    ):
        if (
            event.content
            and event.content.parts
            and event.author == "finalizer_agent"
        ):
            for part in event.content.parts:
                if part.text:
                    final_text = part.text

    if not final_text:
        session = await session_service.get_session(
            app_name="book-writer",
            user_id="book-writer",
            session_id=session.id,
        )
        final_text = session.state.get("chapter_final", "")

    if not final_text:
        final_text = session.state.get("chapter_review", "")
    if not final_text:
        final_text = session.state.get("chapter_draft", "")

    return final_text if final_text else None


async def main() -> None:
    parser = argparse.ArgumentParser(description="Overnight book writer")
    parser.add_argument("--toc", required=True, help="Path to table of contents file")
    parser.add_argument("--output-dir", default="./book", help="Output directory")
    parser.add_argument("--model", default=None, help="Ollama model name")
    parser.add_argument("--branch", default="main", help="Git branch")
    parser.add_argument("--repo", default=None, help="Git remote repo URL")
    parser.add_argument("--retry", type=int, default=3, help="Retries per chapter")
    parser.add_argument("--resume", action="store_true", help="Resume from progress")
    parser.add_argument(
        "--timeout", type=int, default=1800, help="Timeout per chapter (seconds)"
    )
    parser.add_argument(
        "--no-push", action="store_true", help="Skip git push (commit only)"
    )
    args = parser.parse_args()

    setup_logging(args.output_dir)

    if args.model:
        os.environ["AGENT_MODEL"] = args.model

    model_name = os.environ.get("AGENT_MODEL", "gemma4:31b")
    logger.info("Book Writer starting — model: %s", model_name)

    if not check_ollama(model_name):
        sys.exit(1)

    toc = parse_toc(args.toc)
    logger.info(
        "Loaded TOC: '%s' with %d chapters", toc["title"], len(toc["chapters"])
    )

    if args.repo or not args.no_push:
        setup_git_repo(args.output_dir, args.repo, args.branch)

    # Import agent after setting AGENT_MODEL env var
    from app.agent import chapter_pipeline

    session_service = InMemorySessionService()
    runner = Runner(
        agent=chapter_pipeline,
        app_name="book-writer",
        session_service=session_service,
    )

    progress = load_progress(args.output_dir) if args.resume else {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed": [],
        "failed": {},
        "in_progress": None,
    }

    completed = set(progress.get("completed", []))
    total_words = 0
    start_time = time.time()

    logger.info("=" * 60)
    logger.info("Starting book generation: %s", toc["title"])
    logger.info("Chapters: %d | Already done: %d", len(toc["chapters"]), len(completed))
    logger.info("=" * 60)

    for chapter in toc["chapters"]:
        ch_num = chapter["number"]

        if ch_num in completed:
            logger.info("Skipping Chapter %d (already complete)", ch_num)
            continue

        logger.info(
            "--- Chapter %d/%d: %s ---",
            ch_num,
            len(toc["chapters"]),
            chapter["title"],
        )

        progress["in_progress"] = ch_num
        save_progress(args.output_dir, progress)

        content = None
        for attempt in range(1, args.retry + 1):
            try:
                ch_start = time.time()
                logger.info("Attempt %d/%d", attempt, args.retry)

                content = await asyncio.wait_for(
                    run_chapter(runner, session_service, toc, chapter),
                    timeout=args.timeout,
                )

                if content:
                    elapsed = time.time() - ch_start
                    logger.info(
                        "Chapter %d written in %.1f minutes", ch_num, elapsed / 60
                    )
                    break
                else:
                    logger.warning("Chapter %d returned empty content", ch_num)

            except asyncio.TimeoutError:
                logger.warning(
                    "Chapter %d timed out after %ds (attempt %d)",
                    ch_num,
                    args.timeout,
                    attempt,
                )
            except Exception:
                logger.exception("Chapter %d failed (attempt %d)", ch_num, attempt)

        if content:
            result = save_chapter_to_disk(
                ch_num, chapter["title"], content, args.output_dir
            )
            logger.info(
                "Saved: %s (%d words)", result["filename"], result["word_count"]
            )
            total_words += result["word_count"]

            if not args.no_push:
                git_result = git_commit_and_push_sync(
                    ch_num, chapter["title"], args.output_dir, args.branch
                )
                if git_result["success"]:
                    pushed = "pushed" if git_result.get("pushed") else "committed only"
                    logger.info("Git: %s (%s)", git_result["message"], pushed)
                else:
                    logger.warning("Git: %s", git_result["message"])

            progress["completed"].append(ch_num)
            completed.add(ch_num)
        else:
            logger.error(
                "SKIPPING Chapter %d after %d failures", ch_num, args.retry
            )
            progress["failed"][str(ch_num)] = f"Failed after {args.retry} attempts"

        progress["in_progress"] = None
        save_progress(args.output_dir, progress)

    elapsed_total = time.time() - start_time
    logger.info("=" * 60)
    logger.info("BOOK GENERATION COMPLETE")
    logger.info("Title: %s", toc["title"])
    logger.info("Chapters completed: %d/%d", len(completed), len(toc["chapters"]))
    logger.info("Failed: %d", len(progress.get("failed", {})))
    logger.info("Total words: %d", total_words)
    logger.info("Total time: %.1f minutes", elapsed_total / 60)
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

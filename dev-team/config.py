"""Dev-team configuration. All tunables in one place."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


_instance: "Config | None" = None


@dataclass(frozen=True)
class Config:
    model_name: str = "gemma4:31b"
    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_api_key: str = "ollama"
    num_ctx: int = 32768
    temperature: float = 0.7
    think_enabled: bool = True
    stream_enabled: bool = False

    product_repo: str = "user/my-app"
    product_repo_dir: Path = field(
        default_factory=lambda: (Path(__file__).parent / "product-repo").resolve()
    )
    default_branch: str = "main"

    agent_repo_dir: Path = field(default_factory=lambda: Path(__file__).parent.resolve())

    skills_dir: Path = field(
        default_factory=lambda: (Path(__file__).parent / "skills").resolve()
    )
    trusted_skill_sources: list[str] = field(default_factory=list)
    initial_goals_file: Path | None = None

    cycle_interval_seconds: int = 0
    agent_timeout_seconds: int = 1800
    max_retries_per_agent: int = 2

    agent_roles: tuple[str, ...] = (
        "pm", "architect", "designer", "frontend", "backend", "qa", "devops",
    )

    role_labels: dict[str, str] = field(default_factory=lambda: {
        "pm": "role:pm",
        "architect": "role:architect",
        "designer": "role:designer",
        "frontend": "role:frontend",
        "backend": "role:backend",
        "qa": "role:qa",
        "devops": "role:devops",
    })
    priority_labels: tuple[str, ...] = ("P0-critical", "P1-high", "P2-medium", "P3-low")
    status_labels: tuple[str, ...] = ("status:todo", "status:in-progress", "status:done", "status:blocked")

    @classmethod
    def from_cli(cls, cli: dict) -> Config:
        global _instance

        product_repo = cli["product_repo"]

        repo_dir = cli.get("product_repo_dir")
        if repo_dir:
            product_repo_dir = Path(repo_dir).resolve()
        else:
            repo_slug = product_repo.replace("/", "-")
            product_repo_dir = (Path(__file__).parent / "repos" / repo_slug).resolve()

        trusted_raw = cli.get("trusted_skill_sources") or ""
        trusted = [s.strip() for s in trusted_raw.split(",") if s.strip()] if trusted_raw else []

        goals_raw = (cli.get("initial_goals_file") or "").strip()

        _instance = cls(
            model_name=cli.get("model_name") or cls.model_name,
            think_enabled=cli.get("think_enabled") if cli.get("think_enabled") is not None else cls.think_enabled,
            stream_enabled=cli.get("stream_enabled") if cli.get("stream_enabled") is not None else cls.stream_enabled,
            product_repo=product_repo,
            product_repo_dir=product_repo_dir,
            default_branch=cli.get("default_branch") or cls.default_branch,
            cycle_interval_seconds=cli.get("cycle_interval_seconds") or cls.cycle_interval_seconds,
            agent_timeout_seconds=cli.get("agent_timeout_seconds") or cls.agent_timeout_seconds,
            num_ctx=cli.get("num_ctx") or cls.num_ctx,
            skills_dir=Path(cli.get("skills_dir") or str((Path(__file__).parent / "skills").resolve())).resolve(),
            trusted_skill_sources=trusted,
            initial_goals_file=Path(goals_raw).resolve() if goals_raw else None,
        )
        return _instance

    @classmethod
    def get(cls) -> Config:
        if _instance is None:
            raise RuntimeError(
                "Config not initialized. Required argument missing.\n\n"
                "Usage: python run.py <repo> [options]\n\n"
                "  repo              GitHub repo slug (owner/name)\n\n"
                "Run 'python run.py --help' for all options."
            )
        return _instance

"""Dev-team configuration. All tunables in one place."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

_ENV_FILE = Path(__file__).parent / ".env"
if _ENV_FILE.exists():
    for line in _ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


@dataclass(frozen=True)
class Config:
    model_name: str = "gemma4:31b"
    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_api_key: str = "ollama"
    num_ctx: int = 32768
    temperature: float = 0.7

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

    cycle_interval_seconds: int = 0
    agent_timeout_seconds: int = 1800
    max_retries_per_agent: int = 2

    agent_roles: tuple[str, ...] = (
        "pm", "architect", "frontend", "backend", "qa", "devops",
    )

    role_labels: dict[str, str] = field(default_factory=lambda: {
        "pm": "role:pm",
        "architect": "role:architect",
        "frontend": "role:frontend",
        "backend": "role:backend",
        "qa": "role:qa",
        "devops": "role:devops",
    })
    priority_labels: tuple[str, ...] = ("P0-critical", "P1-high", "P2-medium", "P3-low")
    status_labels: tuple[str, ...] = ("status:todo", "status:in-progress", "status:done", "status:blocked")

    @classmethod
    def from_env(cls) -> Config:
        trusted_raw = os.environ.get("TRUSTED_SKILL_SOURCES", "")
        trusted = [s.strip() for s in trusted_raw.split(",") if s.strip()] if trusted_raw else []

        return cls(
            model_name=os.environ.get("AGENT_MODEL", cls.model_name),
            product_repo=os.environ.get("PRODUCT_REPO", cls.product_repo),
            product_repo_dir=Path(os.environ.get(
                "PRODUCT_REPO_DIR",
                str((Path(__file__).parent / "product-repo").resolve()),
            )).resolve(),
            default_branch=os.environ.get("DEFAULT_BRANCH", cls.default_branch),
            cycle_interval_seconds=int(os.environ.get("CYCLE_INTERVAL", str(cls.cycle_interval_seconds))),
            agent_timeout_seconds=int(os.environ.get("AGENT_TIMEOUT", str(cls.agent_timeout_seconds))),
            num_ctx=int(os.environ.get("NUM_CTX", str(cls.num_ctx))),
            skills_dir=Path(os.environ.get(
                "SKILLS_DIR",
                str((Path(__file__).parent / "skills").resolve()),
            )).resolve(),
            trusted_skill_sources=trusted,
        )

from __future__ import annotations

import json
from pathlib import Path

from app.app_utils.typing import RegistryEntry

REGISTRY_PATH = Path(__file__).parent / "registry.json"


def load_registry() -> dict[str, dict]:
    if not REGISTRY_PATH.exists():
        return {}
    text = REGISTRY_PATH.read_text()
    if not text.strip():
        return {}
    return json.loads(text)


def save_registry(registry: dict[str, dict]) -> None:
    REGISTRY_PATH.write_text(json.dumps(registry, indent=2) + "\n")


def find_tool(name: str) -> RegistryEntry | None:
    registry = load_registry()
    entry = registry.get(name)
    if entry is None:
        return None
    return RegistryEntry(**entry)


def search_tools(query: str) -> list[RegistryEntry]:
    registry = load_registry()
    query_lower = query.lower()
    results = []
    for entry_data in registry.values():
        name = entry_data.get("name", "").lower()
        desc = entry_data.get("description", "").lower()
        if query_lower in name or query_lower in desc:
            results.append(RegistryEntry(**entry_data))
    return results


def register_tool(entry: RegistryEntry) -> bool:
    registry = load_registry()
    if entry.name in registry:
        return False
    registry[entry.name] = entry.model_dump()
    save_registry(registry)
    return True


def list_tools() -> list[str]:
    registry = load_registry()
    return list(registry.keys())

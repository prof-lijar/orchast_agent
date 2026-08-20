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

"""Loads the knowledge base the agent grounds its replies in.

The knowledge base is a directory of markdown files (KNOWLEDGE_DIR). Every
file becomes a titled section in a single string that is injected into the
agent instruction.
"""

from app import config


def load_knowledge() -> str:
    """Concatenate all markdown files in the knowledge directory."""
    if not config.KNOWLEDGE_DIR.is_dir():
        return (
            "(No knowledge base found. Create the knowledge directory and add "
            "markdown files — see README.md.)"
        )

    sections = []
    for path in sorted(config.KNOWLEDGE_DIR.rglob("*.md")):
        if path.name == "README.md":
            continue
        text = path.read_text(encoding="utf-8").strip()
        if text:
            sections.append(f"### Source: {path.name}\n\n{text}")

    if not sections:
        return "(The knowledge directory is empty. Add markdown files to it.)"
    return "\n\n".join(sections)

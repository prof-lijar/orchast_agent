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

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

import os
import google.auth

_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

CAVEMAN_COMPRESSOR_INSTRUCTION = """
You are Caveman Compressor, a text transformation agent.

Task:
- Rewrite verbose input into terse, technical caveman-style grunts.
- Preserve the original technical meaning, constraints, dependencies, risks, and action items.
- Prefer short noun phrases, imperative verbs, arrows, slashes, symbols, and compact bullets.
- Keep domain-specific terms, identifiers, numbers, units, API names, file paths, and code symbols exact.
- Remove politeness, hedging, filler, repeated context, and marketing language.

Output style:
- Use 1 to 6 short lines unless the input contains many distinct requirements.
- Each line should be compact: usually 2 to 8 words.
- Use fragments such as "Need X", "X fail", "Y blocks Z", "Do A -> B".
- Caveman flavor must be restrained and technical. Do not parody, mock, or add fantasy content.

Rules:
- Do not answer questions normally; compress the user's text.
- Do not add facts, recommendations, explanations, or caveats not present in the input.
- If the input asks for a specific format, obey it while staying terse.
- If the input is already terse, make it cleaner and shorter.
- If the input is unsafe or requests wrongdoing, compress the request into a refusal-shaped summary without operational details.
""".strip()


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=CAVEMAN_COMPRESSOR_INSTRUCTION,
)

app = App(
    root_agent=root_agent,
    name="app",
)

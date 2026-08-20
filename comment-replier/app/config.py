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

"""Environment-driven configuration for the comment-replier agent.

All values are read from the process environment, with a `.env` file at the
project root loaded first. See README.md for the full variable reference.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")


def _env_bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


# Read-only access (fetching comments). Optional if OAuth is configured.
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "").strip()

# OAuth client secrets JSON (Desktop app credential). Required to post replies.
YOUTUBE_CLIENT_SECRETS_FILE = os.getenv(
    "YOUTUBE_CLIENT_SECRETS_FILE", str(PROJECT_ROOT / "client_secrets.json")
)

# Where the granted OAuth token is cached between runs.
YOUTUBE_TOKEN_FILE = os.getenv(
    "YOUTUBE_TOKEN_FILE", str(PROJECT_ROOT / ".youtube_token.json")
)

# The channel ID replies are posted as. Used to skip comments the owner
# already answered. Optional.
OWNER_CHANNEL_ID = os.getenv("OWNER_CHANNEL_ID", "").strip()

# Safety switch: when true (the default), post_reply only previews the reply
# instead of writing to YouTube.
DRY_RUN = _env_bool("COMMENT_REPLIER_DRY_RUN", True)

# Directory of markdown files the agent grounds its replies in.
KNOWLEDGE_DIR = Path(os.getenv("KNOWLEDGE_DIR", str(PROJECT_ROOT / "knowledge")))

# Default number of comment threads fetched per video.
MAX_COMMENTS = int(os.getenv("MAX_COMMENTS", "20"))

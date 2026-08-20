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

"""YouTube Data API v3 access: fetch comment threads and post replies.

Reading comments works with either an API key or OAuth credentials.
Posting replies requires OAuth (youtube.force-ssl scope). Run
`uv run python -m app.youtube_client login` once to pre-authorize so the
browser consent flow doesn't happen in the middle of an agent turn.
"""

import re
from pathlib import Path
from typing import Any

from app import config

SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

_VIDEO_ID_PATTERNS = (
    re.compile(r"(?:v=|/shorts/|/live/|youtu\.be/)([A-Za-z0-9_-]{11})"),
    re.compile(r"^([A-Za-z0-9_-]{11})$"),
)


def extract_video_id(video: str) -> str:
    """Accept a bare video ID or any common YouTube URL form."""
    video = video.strip()
    for pattern in _VIDEO_ID_PATTERNS:
        match = pattern.search(video)
        if match:
            return match.group(1)
    raise ValueError(f"Could not extract a YouTube video ID from: {video!r}")


def _load_oauth_credentials(required: bool):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    token_path = Path(config.YOUTUBE_TOKEN_FILE)
    creds = None
    if token_path.is_file():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_path.write_text(creds.to_json(), encoding="utf-8")

    if creds and creds.valid:
        return creds

    secrets_path = Path(config.YOUTUBE_CLIENT_SECRETS_FILE)
    if secrets_path.is_file():
        from google_auth_oauthlib.flow import InstalledAppFlow

        flow = InstalledAppFlow.from_client_secrets_file(str(secrets_path), SCOPES)
        creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json(), encoding="utf-8")
        return creds

    if required:
        raise RuntimeError(
            "Posting replies requires OAuth. Set YOUTUBE_CLIENT_SECRETS_FILE in "
            ".env to a Desktop-app OAuth client JSON and run "
            "`uv run python -m app.youtube_client login`. See README.md."
        )
    return None


def _get_service(write: bool):
    from googleapiclient.discovery import build

    creds = _load_oauth_credentials(required=write)
    if creds is not None:
        return build("youtube", "v3", credentials=creds, cache_discovery=False)
    if config.YOUTUBE_API_KEY:
        return build(
            "youtube",
            "v3",
            developerKey=config.YOUTUBE_API_KEY,
            cache_discovery=False,
        )
    raise RuntimeError(
        "No YouTube credentials configured. Set YOUTUBE_API_KEY (read-only) or "
        "OAuth variables in .env. See README.md."
    )


_owner_channel_id_cache: str | None = None


def _get_owner_channel_id() -> str:
    """Return the channel ID replies are posted as.

    Uses OWNER_CHANNEL_ID when set; otherwise auto-detects it once from the
    OAuth token (channels.list mine=true). Returns "" when undetectable.
    """
    global _owner_channel_id_cache
    if config.OWNER_CHANNEL_ID:
        return config.OWNER_CHANNEL_ID
    if _owner_channel_id_cache is not None:
        return _owner_channel_id_cache
    try:
        from googleapiclient.discovery import build

        creds = _load_oauth_credentials(required=False)
        if creds is None:
            _owner_channel_id_cache = ""
            return ""
        service = build("youtube", "v3", credentials=creds, cache_discovery=False)
        response = service.channels().list(part="id", mine=True).execute()
        items = response.get("items", [])
        _owner_channel_id_cache = items[0]["id"] if items else ""
    except Exception:
        _owner_channel_id_cache = ""
    return _owner_channel_id_cache


def _owner_has_replied(service, parent_comment_id: str, owner_id: str) -> bool:
    """Check every reply in a thread for one authored by the owner."""
    page_token = None
    while True:
        response = (
            service.comments()
            .list(
                part="snippet",
                parentId=parent_comment_id,
                maxResults=100,
                pageToken=page_token,
            )
            .execute()
        )
        for item in response.get("items", []):
            author = item["snippet"].get("authorChannelId", {}).get("value", "")
            if author == owner_id:
                return True
        page_token = response.get("nextPageToken")
        if not page_token:
            return False


def _thread_to_comment(item: dict, service, owner_id: str) -> dict[str, Any]:
    top = item["snippet"]["topLevelComment"]
    snippet = top["snippet"]
    reply_items = item.get("replies", {}).get("comments", [])
    reply_authors = [
        r["snippet"].get("authorChannelId", {}).get("value", "") for r in reply_items
    ]
    reply_count = item["snippet"].get("totalReplyCount", 0)

    owner_already_replied = bool(owner_id and owner_id in reply_authors)
    # commentThreads.list only embeds a few replies per thread; when the owner
    # wasn't in that partial list but more replies exist, check them all.
    if owner_id and not owner_already_replied and reply_count > len(reply_items):
        owner_already_replied = _owner_has_replied(service, top["id"], owner_id)

    return {
        "comment_id": top["id"],
        "author": snippet.get("authorDisplayName", ""),
        "author_channel_id": snippet.get("authorChannelId", {}).get("value", ""),
        "text": snippet.get("textOriginal", snippet.get("textDisplay", "")),
        "published_at": snippet.get("publishedAt", ""),
        "like_count": snippet.get("likeCount", 0),
        "reply_count": reply_count,
        "owner_already_replied": owner_already_replied,
    }


def fetch_comments(video: str, max_results: int = 0) -> dict:
    """Fetch top-level comment threads for a YouTube video.

    Args:
        video: A YouTube video ID or URL (watch, youtu.be, or shorts link).
        max_results: Maximum number of comment threads to return. Pass 0 to
            use the MAX_COMMENTS default from the environment.

    Returns:
        A dict with the resolved video_id and a list of comments. Each comment
        has comment_id, author, text, published_at, like_count, reply_count,
        and owner_already_replied (true when the channel owner has already
        answered that thread).
    """
    video_id = extract_video_id(video)
    limit = max_results or config.MAX_COMMENTS
    service = _get_service(write=False)
    owner_id = _get_owner_channel_id()

    comments: list[dict[str, Any]] = []
    page_token = None
    while len(comments) < limit:
        request = service.commentThreads().list(
            part="snippet,replies",
            videoId=video_id,
            maxResults=min(100, limit - len(comments)),
            order="time",
            textFormat="plainText",
            pageToken=page_token,
        )
        response = request.execute()
        comments.extend(
            _thread_to_comment(item, service, owner_id)
            for item in response.get("items", [])
        )
        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return {
        "video_id": video_id,
        "comment_count": len(comments),
        "comments": comments[:limit],
        "dry_run": config.DRY_RUN,
    }


def post_reply(parent_comment_id: str, reply_text: str) -> dict:
    """Post a reply to a top-level YouTube comment.

    In dry-run mode (COMMENT_REPLIER_DRY_RUN=true, the default) nothing is
    sent to YouTube; the reply is returned as a preview instead.

    Args:
        parent_comment_id: The comment_id of the top-level comment to reply to.
        reply_text: The reply text to post.

    Returns:
        A dict with status "dry_run" or "posted", plus the reply details.
    """
    reply_text = reply_text.strip()
    if not reply_text:
        return {"status": "error", "message": "reply_text is empty"}

    if config.DRY_RUN:
        return {
            "status": "dry_run",
            "parent_comment_id": parent_comment_id,
            "reply_text": reply_text,
            "message": (
                "Dry-run mode: nothing was posted. Set "
                "COMMENT_REPLIER_DRY_RUN=false in .env to post for real."
            ),
        }

    service = _get_service(write=True)

    # Hard guard against double-replying: never post into a thread the owner
    # already answered, regardless of what the model decided.
    owner_id = _get_owner_channel_id()
    if owner_id and _owner_has_replied(service, parent_comment_id, owner_id):
        return {
            "status": "skipped_already_replied",
            "parent_comment_id": parent_comment_id,
            "message": "The channel owner already replied in this thread; not posting.",
        }

    response = (
        service.comments()
        .insert(
            part="snippet",
            body={
                "snippet": {
                    "parentId": parent_comment_id,
                    "textOriginal": reply_text,
                }
            },
        )
        .execute()
    )
    return {
        "status": "posted",
        "parent_comment_id": parent_comment_id,
        "reply_id": response.get("id", ""),
        "reply_text": reply_text,
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "login":
        _load_oauth_credentials(required=True)
        print(f"OAuth token saved to {config.YOUTUBE_TOKEN_FILE}")
    else:
        print("Usage: python -m app.youtube_client login")

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

import pytest

from app import config
from app.knowledge import load_knowledge
from app.youtube_client import extract_video_id, post_reply


@pytest.mark.parametrize(
    "url",
    [
        "dQw4w9WgXcQ",
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ?t=42",
        "https://www.youtube.com/shorts/dQw4w9WgXcQ",
        "https://www.youtube.com/live/dQw4w9WgXcQ",
    ],
)
def test_extract_video_id(url):
    assert extract_video_id(url) == "dQw4w9WgXcQ"


def test_extract_video_id_rejects_garbage():
    with pytest.raises(ValueError):
        extract_video_id("not a video")


def test_load_knowledge_includes_sample_file():
    knowledge = load_knowledge()
    assert "channel_faq.md" in knowledge


def test_post_reply_dry_run_does_not_post(monkeypatch):
    monkeypatch.setattr(config, "DRY_RUN", True)
    result = post_reply("some-comment-id", "Thanks for watching!")
    assert result["status"] == "dry_run"
    assert result["reply_text"] == "Thanks for watching!"


def test_post_reply_rejects_empty_text(monkeypatch):
    monkeypatch.setattr(config, "DRY_RUN", True)
    result = post_reply("some-comment-id", "   ")
    assert result["status"] == "error"


def test_post_reply_refuses_when_owner_already_replied(monkeypatch):
    from app import youtube_client

    monkeypatch.setattr(config, "DRY_RUN", False)
    monkeypatch.setattr(youtube_client, "_get_service", lambda write: object())
    monkeypatch.setattr(youtube_client, "_get_owner_channel_id", lambda: "UCowner")
    monkeypatch.setattr(
        youtube_client, "_owner_has_replied", lambda service, parent, owner: True
    )
    result = youtube_client.post_reply("some-comment-id", "A reply")
    assert result["status"] == "skipped_already_replied"

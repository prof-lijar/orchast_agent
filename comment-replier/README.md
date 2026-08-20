# Comment Replier

An ADK agent that reads the comments on a YouTube video and replies to each
one on behalf of the channel owner, grounded strictly in a knowledge base you
provide (markdown files in `knowledge/`).

- Fetches top-level comment threads via the YouTube Data API v3
- Classifies each comment (reply vs. skip spam/trolls/already-answered)
- Drafts a reply per comment using only your knowledge base — no invented facts
- Posts replies via the API, with a **dry-run mode on by default** so nothing
  is published until you flip the switch

> **Note:** The YouTube Data API only exposes comments on **videos** (including
> Shorts and live streams). Comments on **community posts** are not accessible
> through the public API, so this agent cannot reply to those.

## Quick Start

```bash
cd comment-replier
uv sync

# 1. Fill in .env (see Configuration below) — at minimum GOOGLE_API_KEY
# 2. Add your knowledge as markdown files in knowledge/
# 3. (Posting only) authorize once:
uv run python -m app.youtube_client login

# Try it
agents-cli playground          # browser UI
# or one-shot:
agents-cli run "Reply to the comments on https://www.youtube.com/watch?v=VIDEO_ID"
```

While `COMMENT_REPLIER_DRY_RUN=true` (the default) the agent shows exactly
what it *would* post per comment. Review the previews, then set it to `false`
in `.env` to post for real.

## Configuration

All settings live in the `.env` file at the project root (loaded
automatically). `.env` is gitignored — never commit it.

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `GOOGLE_API_KEY` | yes | – | Google AI Studio key ([aistudio.google.com/apikey](https://aistudio.google.com/apikey)) for the agent's Gemini model. Free tier available; no GCP/Vertex setup needed. |
| `YOUTUBE_API_KEY` | one of the two auth options | – | Google Cloud API key with **YouTube Data API v3** enabled. Enough for *reading* comments only. |
| `YOUTUBE_CLIENT_SECRETS_FILE` | required to post | `client_secrets.json` | Path to an OAuth **Desktop app** client-secrets JSON. Required to *post* replies (scope `youtube.force-ssl`). |
| `YOUTUBE_TOKEN_FILE` | no | `.youtube_token.json` | Where the granted OAuth token is cached between runs. |
| `OWNER_CHANNEL_ID` | no | auto-detected | Your channel ID (`UC...`). Used to skip comments you already replied to; when empty it is detected from the OAuth token. `post_reply` also refuses to post into a thread the owner already answered. |
| `COMMENT_REPLIER_DRY_RUN` | no | `true` | Safety switch. `true` = preview replies only; `false` = actually post to YouTube. |
| `KNOWLEDGE_DIR` | no | `knowledge` | Directory of markdown files the agent grounds replies in. |
| `MAX_COMMENTS` | no | `20` | Default number of comment threads fetched per video. |

### Getting the credentials

1. In the [Google Cloud console](https://console.cloud.google.com/), enable
   **YouTube Data API v3** for your project.
2. *Read-only*: create an **API key** and set `YOUTUBE_API_KEY`.
3. *Posting*: create an **OAuth client ID** of type **Desktop app**, download
   the JSON, save it as `client_secrets.json` (or point
   `YOUTUBE_CLIENT_SECRETS_FILE` at it), then run
   `uv run python -m app.youtube_client login` and grant access **with the
   Google account that owns the channel** — replies are posted as that
   account.
The Google Cloud project here is only a credential container for the YouTube
API — it needs **no billing account and no IAM roles**. The YouTube Data API
is free (10,000 quota units/day). The Gemini model does not use GCP at all;
it runs on your `GOOGLE_API_KEY` from Google AI Studio.

### Quota note

Each posted reply (`comments.insert`) costs **50 quota units**; fetching a
page of comment threads costs 1. The default daily quota is 10,000 units, so
roughly 200 replies/day.

## Knowledge base

Put any number of `*.md` files in `knowledge/`. They are concatenated into
the agent's instruction at startup — facts, FAQ answers, links, and tone
guidance all belong there. A sample `channel_faq.md` is included; replace it
with your own content. Restart the playground after editing.

Rules the agent follows:

- Every reply addresses the commenter's specific point — no generic filler
- Channel-specific facts (schedule, links, prices, plans) come **only** from
  the knowledge base; if not covered, it acknowledges and promises follow-up
  instead of inventing channel facts
- General/topic questions ("explain more about AGI?") get a real, substantive
  answer from the model's knowledge, kept to a few sentences
- Skips spam, link drops, hostile comments, and threads the owner already
  answered (owner detected automatically from the OAuth token; `post_reply`
  also hard-refuses to double-reply)
- Replies in the commenter's language

## Testing

```bash
uv run pytest tests/unit          # no network needed
agents-cli eval run               # behavioral eval (drafting quality)
```

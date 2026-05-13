# Desktop

A zero-native desktop app for the Self-Evolving Agent. Provides a local GUI to chat with the agent and browse the tool registry, backed by the ADK dev server.

## Architecture

```
zero-native shell (system WebView)
  └── Svelte frontend (Vite dev server :5173)
        ├── ChatPanel   — send messages, view agent responses
        ├── RegistryPanel — browse registered tools
        └── StatusBar   — backend / bridge health
              │
              ▼  (Vite proxy)
        ADK dev server (:8001)
```

The frontend proxies `/apps`, `/run`, and `/list-apps` to the ADK backend so the browser never talks to a different origin.

## Prerequisites

- Node.js (v22+) and npm
- [zero-native](https://github.com/nicosql/zero-native) installed globally
- The Self-Evolving Agent backend running (`uv run adk web --port 8001` from the project root)

## Setup

```sh
npm install --prefix frontend
```

`zig build dev`, `zig build run`, and `zig build package` also install frontend dependencies automatically.

The build defaults to this zero-native framework path:

```text
/home/orchestor/.nvm/versions/node/v22.22.2/lib/node_modules/zero-native
```

Override with `-Dzero-native-path=/path/to/zero-native` if needed.

## Commands

```sh
# Start the ADK backend first
uv run adk web --port 8001

# Then launch the desktop app
zig build dev          # dev mode (hot-reload frontend + native shell)
zig build run          # production build
zig build test         # run tests
zig build package      # package for distribution
zero-native doctor --manifest app.zon   # check setup
```

`zig build dev` starts the Vite dev server, waits for it, and opens the native shell pointing at `http://localhost:5173/`.

## Frontend

| Detail | Value |
|--------|-------|
| Framework | Svelte 5 (runes mode) |
| Bundler | Vite |
| Dev URL | `http://localhost:5173/` |
| Production assets | `frontend/dist` |

### API layer (`frontend/src/lib/api.js`)

| Function | Endpoint | Purpose |
|----------|----------|---------|
| `createSession()` | `POST /apps/{app}/users/user/sessions` | Create a new ADK session |
| `sendMessage()` | `POST /run` | Send a message and get agent response |
| `checkBackendHealth()` | `GET /list-apps` | Health check (3 s timeout) |
| `listApps()` | `GET /list-apps` | List available ADK apps |

### Vite proxy (`frontend/vite.config.js`)

All API paths are proxied to the ADK backend at `http://127.0.0.1:8001`:

- `/apps` — session management
- `/run` — agent execution
- `/list-apps` — app listing and health

## Web Engines

Defaults to the system WebView. On macOS, switch to Chromium/CEF:

```sh
zero-native cef install
zig build run -Dplatform=macos -Dweb-engine=chromium
```

For one-command setup, use `-Dcef-auto-install=true`. Use `-Dcef-dir=/path/to/cef` for a custom CEF location.

```sh
zero-native doctor --web-engine chromium
```

## Diagnostics

- `ZERO_NATIVE_LOG_DIR` — override the platform log directory
- `ZERO_NATIVE_LOG_FORMAT=text|jsonl` — choose persistent log format

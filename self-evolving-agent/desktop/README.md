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
        ADK dev server (:8081)
```

The frontend proxies `/apps`, `/run`, and `/list-apps` to the ADK backend so the browser never talks to a different origin.

## Prerequisites

- Node.js (v22+) and npm
- [zero-native](https://github.com/nicosql/zero-native) installed globally (desktop mode only)
- The Self-Evolving Agent backend running (see below)

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

## Running

### Option A: Browser mode

Use this when you don't need the native desktop shell, or when accessing a remote server.

```sh
# Terminal 1 — Start the backend
cd /path/to/self-evolving-agent
ALLOW_ORIGINS=http://localhost:5173 uv run dev

# Terminal 2 — Start the Vite dev server
cd desktop/frontend
npm run dev
```

Open `http://localhost:5173` in your browser.

The `uv run dev` command runs the custom FastAPI app which includes both ADK routes and the model switcher API. Environment variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `PORT` | `8081` | Backend server port |
| `ALLOW_ORIGINS` | _(none)_ | Comma-separated allowed CORS origins |

Example with a custom port:

```sh
ALLOW_ORIGINS=http://localhost:5173 PORT=9000 uv run dev
```

> **Note:** If Vite picks a different port (e.g. `5174`, `5175`), update `ALLOW_ORIGINS` to match.

#### ADK-only mode

If you don't need the model switcher, you can use the plain ADK server instead:

```sh
uv run adk web --port 8081 --allow-origins "http://localhost:5173"
```

#### Remote server access

If the backend and frontend run on a remote server, forward the ports via SSH:

```sh
ssh -L 5174:localhost:5173 -L 8081:localhost:8081 user@remote-server
```

Then open `http://localhost:5174` on your local machine.

When accessing through a forwarded port (e.g. `localhost:5174`), include the forwarded origin in `--allow-origins`:

```sh
ALLOW_ORIGINS=http://localhost:5174 uv run dev
```

### Option B: Desktop mode (zero-native)

```sh
# Start the backend first
ALLOW_ORIGINS=http://localhost:5173 uv run dev

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
| `fetchModels()` | `GET /api/models` | List available models (requires `uv run dev`) |
| `fetchCurrentModel()` | `GET /api/models/current` | Get active model name |
| `switchModel()` | `POST /api/models/switch` | Switch all agents to a different model |

### Vite proxy (`frontend/vite.config.js`)

All API paths are proxied to the backend at `http://127.0.0.1:8081`:

- `/apps` — session management
- `/run` — agent execution
- `/list-apps` — app listing and health
- `/api` — model switcher (only available with `uv run dev`)

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

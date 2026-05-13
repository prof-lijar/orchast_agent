# Native Desktop Interface for Self-Evolving LLM Agents Using zero-native

**Mini Research Paper — May 2026**

---

## Abstract

Self-evolving agents — LLM-based systems that dynamically create, test, and register their own tools — are typically accessed through terminal CLIs or minimal chat web interfaces. These interfaces fail to expose the rich internal state of the agent: its tool registry, creation pipeline progress, sandbox execution results, and safety audit outcomes. This paper proposes a native desktop application for our self-evolving agent using **zero-native**, a Zig + WebView framework by Vercel Labs that produces sub-megabyte desktop binaries. We present a three-layer architecture — zero-native desktop shell, web frontend, and Python FastAPI backend — that wraps our existing Google ADK agent in a first-class desktop experience with native file system access, system tray presence, and real-time pipeline visualization, while preserving the full agent architecture unchanged.

---

## 1. Introduction

Our self-evolving agent, built on Google ADK, operates through a multi-agent pipeline that creates, tests, validates, and registers tools at runtime. The current interaction model is a chat interface — either the ADK playground (`agents-cli playground`) or a FastAPI-served web UI. While functional for development, this interface has fundamental limitations:

- **Opaque internals**: Users cannot observe the tool creation pipeline as it progresses through specification, coding, testing, and registration phases
- **No persistent workspace**: Each session starts fresh; there is no desktop-integrated environment for managing the tool registry
- **Limited file interaction**: Uploading files requires manual drag-and-drop; there are no native file dialogs or OS-level integrations
- **No background presence**: The agent has no system tray icon, no desktop notifications for completed tool creation, no OS-level integration

A native desktop application addresses these gaps by providing a persistent, integrated environment where the user can interact with the agent, browse and manage registered tools, monitor the creation pipeline in real-time, and receive native OS notifications — all while the agent backend runs locally.

### 1.1 Why a Desktop Application?

For a self-evolving agent that generates, tests, and stores executable code locally, a desktop application offers specific advantages over a pure web deployment:

1. **Local-first execution**: Generated tools run in a local sandbox. A desktop app co-located with the agent backend eliminates network latency and avoids exposing code execution endpoints over the network.
2. **File system integration**: Native file dialogs for importing data files, exporting generated tools, and browsing the tool registry on disk.
3. **Background operation**: System tray presence allows the agent to continue running and creating tools while the user works in other applications, with notifications on completion.
4. **Single-binary distribution**: A packaged desktop app is easier to distribute to research collaborators than a multi-step server setup.

### 1.2 System Context

Our self-evolving agent operates through the following pipeline:

```
User Request
    |
    v
Root Orchestrator  ──>  search_registry()  ──>  Tool Found? ──> execute_registered_tool()
    |                                               |
    | (no match)                                    v
    v                                           Return Result
Tool Creation Pipeline (SequentialAgent)
    |
    ├── tool_spec_agent      →  JSON specification
    ├── tool_coder_agent     →  Python implementation
    ├── tool_test_agent      →  Pytest test suite
    └── tool_registrar_agent →  Safety check + sandbox test + registration
    |
    v
Registry (registry.json)  +  Generated .py files (app/tools/generated/)
```

The agent is served via FastAPI (`app/fast_api_app.py`) on port 8001 with REST endpoints for session management, message passing, and artifact retrieval. This existing HTTP interface becomes the communication layer between the desktop frontend and the agent backend.

---

## 2. zero-native Framework

### 2.1 Overview

zero-native [1] is an open-source desktop application framework maintained by Vercel Labs. It combines a native backend written in **Zig** with a **WebView**-rendered frontend, producing lightweight desktop applications that avoid the ~150 MB overhead of Electron-style bundled browsers.

The core architecture separates concerns into three layers:

```
┌──────────────────────────────────────────┐
│            Web Frontend                  │
│      (React / Vue / Svelte / Next.js)    │
│                                          │
│   window.zero.invoke("cmd", payload)     │
│              ▲           │               │
└──────────────┼───────────┼───────────────┘
               │  JSON     │  JSON
               │  response │  request
┌──────────────┼───────────┼───────────────┐
│              │    Bridge  ▼               │
│         ┌────────────────────┐           │
│         │  Policy + Dispatch │           │
│         └────────────────────┘           │
│                                          │
│          Zig Native Runtime              │
│   (window mgmt, file I/O, system tray)  │
└──────────────────────────────────────────┘
```

### 2.2 Key Technical Properties

| Property | Detail |
|----------|--------|
| **Binary size** | Sub-megabyte with system WebView; ~80-120 MB with bundled Chromium (CEF) |
| **Web engine** | System WebView (WKWebView on macOS, WebKitGTK on Linux) or bundled Chromium/CEF |
| **Frontend** | Any web framework: React, Vue, Svelte, Next.js |
| **Bridge** | Bidirectional JSON messaging via `window.zero.invoke()` (JS → Zig) |
| **Security** | Default-deny: all native commands require explicit policy registration |
| **Platforms** | macOS 11+, Linux, Windows, iOS/Android (mobile via C ABI embedding) |
| **License** | Apache-2.0 |
| **Prerequisites** | Zig 0.16+, Node.js with npm |

### 2.3 Bridge Communication

The bridge is the central integration mechanism. JavaScript invokes native Zig handlers through a typed, permission-controlled channel:

**JavaScript side:**
```javascript
const result = await window.zero.invoke("agent.search_registry", {
    query: "text processing"
});
console.log(result);  // { tools: [...], count: 3 }
```

**Zig handler side:**
```zig
fn searchRegistry(context: *anyopaque, invocation: zero_native.bridge.Invocation,
                  output: []u8) anyerror![]const u8 {
    const self: *App = @ptrCast(@alignCast(context));
    // Forward request to Python FastAPI backend via HTTP
    const response = try self.http_client.get(
        "http://localhost:8001/api/registry/search?q=" ++ invocation.request.payload
    );
    return std.fmt.bufPrint(output, "{s}", .{response.body});
}
```

Communication constraints are well-defined:

| Limit | Value |
|-------|-------|
| Message payload | 16 KiB |
| Response payload | 16 KiB |
| Command name | 128 bytes |
| Request ID | 64 bytes |

### 2.4 Security Model

zero-native operates on a **default-deny** principle. The WebView is treated as untrusted. Every native command requires:

1. **Registration** in native Zig code
2. **Explicit policy** allowing the command, origin, and permissions

```zig
.bridge = .{
    .commands = .{
        .{ .name = "agent.search_registry",
           .permissions = .{ "network" },
           .origins = .{ "zero://app" } },
        .{ .name = "agent.execute_tool",
           .permissions = .{ "network", "filesystem" },
           .origins = .{ "zero://app" } },
    },
},
```

Available permission categories include: `window`, `filesystem`, `clipboard`, `network`, `camera`, `microphone`, `location`, `notifications`, and custom reverse-DNS permissions. This granular permission model aligns naturally with our agent's existing safety policy — tools classified as "medium" or "high" risk can be gated behind explicit desktop-level permissions.

### 2.5 Project Structure

A zero-native project initialized with `zero-native init agent_desktop --frontend react` generates:

```
agent_desktop/
├── build.zig              # Build configuration
├── build.zig.zon          # Package manifest (zero-native dependency)
├── app.zon                # App metadata: name, icons, permissions, security
├── src/
│   ├── main.zig           # App struct with app() and bridge() methods
│   └── runner.zig         # Platform initialization, logging, panic handling
├── assets/
│   └── icon.icns          # Application icon
└── frontend/              # React/Svelte project
    ├── package.json
    ├── src/
    └── public/
```

---

## 3. Proposed Architecture

### 3.1 Three-Layer Design

We propose a three-layer architecture where zero-native serves as the desktop shell, a web frontend provides the UI, and the existing Python FastAPI backend runs the agent:

```
┌─────────────────────────────────────────────────────────────────┐
│                     zero-native Desktop Shell                   │
│                         (Zig runtime)                           │
│                                                                 │
│  ┌───────────┐  ┌──────────────┐  ┌──────────────────────────┐ │
│  │  System    │  │  Process     │  │  Bridge Handlers         │ │
│  │  Tray      │  │  Manager     │  │                          │ │
│  │           │  │  (launches   │  │  agent.search_registry   │ │
│  │  - Status │  │   Python     │  │  agent.execute_tool      │ │
│  │  - Quick  │  │   backend)   │  │  agent.file_dialog       │ │
│  │    access │  │              │  │  agent.export_tool        │ │
│  └───────────┘  └──────────────┘  └──────────────────────────┘ │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    WebView (System)                          ││
│  │  ┌──────────────────────────────────────────────────────┐   ││
│  │  │              React / Svelte Frontend                  │   ││
│  │  │                                                      │   ││
│  │  │  ┌────────────┐ ┌──────────┐ ┌───────────────────┐  │   ││
│  │  │  │ Chat Panel │ │ Registry │ │ Pipeline Monitor  │  │   ││
│  │  │  │            │ │ Browser  │ │                   │  │   ││
│  │  │  │ - Messages │ │          │ │ - Spec phase      │  │   ││
│  │  │  │ - Tool     │ │ - Search │ │ - Code phase      │  │   ││
│  │  │  │   results  │ │ - Detail │ │ - Test phase      │  │   ││
│  │  │  │ - File     │ │ - Delete │ │ - Register phase  │  │   ││
│  │  │  │   uploads  │ │ - Export │ │ - Safety status   │  │   ││
│  │  │  └────────────┘ └──────────┘ └───────────────────┘  │   ││
│  │  │                                                      │   ││
│  │  │  ┌──────────────────┐  ┌──────────────────────────┐  │   ││
│  │  │  │ Sandbox Viewer   │  │ Tool Code Editor         │  │   ││
│  │  │  │                  │  │                           │  │   ││
│  │  │  │ - stdout/stderr  │  │ - Syntax highlighting    │  │   ││
│  │  │  │ - Test results   │  │ - Read-only view         │  │   ││
│  │  │  │ - Timeout status │  │ - Version history        │  │   ││
│  │  │  └──────────────────┘  └──────────────────────────┘  │   ││
│  │  └──────────────────────────────────────────────────────┘   ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              │
                    HTTP (localhost:8001)
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Python FastAPI Backend                           │
│                 (existing, unmodified)                           │
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────────────────────────┐│
│  │  ADK App         │  │  Agent Pipeline                      ││
│  │                  │  │                                      ││
│  │  POST /sessions  │  │  Root Orchestrator                   ││
│  │  POST /messages  │  │    ├── tool_spec_agent               ││
│  │  GET  /artifacts │  │    ├── tool_coder_agent              ││
│  │                  │  │    ├── tool_test_agent                ││
│  └──────────────────┘  │    ├── tool_registrar_agent          ││
│                        │    └── tool_review_fixer_agent        ││
│  ┌──────────────────┐  └──────────────────────────────────────┘│
│  │  Registry + Sandbox + Safety Policy                         │
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

**Key design principle**: The Python backend remains completely unchanged. The desktop shell is a presentation layer that communicates exclusively through the existing FastAPI HTTP endpoints. This means the agent can also be used headlessly, via the ADK playground, or through any other HTTP client.

### 3.2 Process Lifecycle

When the user launches the desktop application:

```
1. zero-native runtime starts
2. Zig process manager spawns Python backend:
     subprocess: "uv run uvicorn app.fast_api_app:app --host 127.0.0.1 --port 8001"
3. Zig health-checks http://127.0.0.1:8001/ until ready
4. WebView loads React frontend
5. Frontend connects to backend via localhost
6. System tray icon activates (agent status: ready)
```

On application close:

```
1. WebView closes
2. Zig sends SIGTERM to Python process
3. Graceful shutdown with 5-second timeout
4. System tray removed
```

### 3.3 Data Flow

A typical tool creation request flows through all three layers:

```
User types: "Create a tool that converts CSV to JSON"
    │
    ▼
[React Frontend]  ──POST──>  [FastAPI Backend]
                               │
                               ▼
                            Root Orchestrator
                               │
                               ├── search_registry("csv json") → no match
                               │
                               ▼
                            tool_creation_pipeline
                               │
    [Frontend polls status] <──┤── tool_spec_agent    ✓  → state["tool_spec"]
                               │
    [Frontend polls status] <──┤── tool_coder_agent   ✓  → state["tool_code"]
                               │
    [Frontend polls status] <──┤── tool_test_agent    ✓  → state["tool_tests"]
                               │
    [Frontend polls status] <──┤── tool_registrar_agent
                               │     ├── safety check  ✓
                               │     ├── sandbox test  ✓
                               │     └── register      ✓
                               │
    [Frontend receives]  <─────┘  "REGISTRATION_SUCCESS"
    [Desktop notification]        "csv_to_json_tool registered (v1)"
```

---

## 4. Integration Design

### 4.1 Bridge Commands

The Zig bridge exposes native desktop capabilities that the web frontend cannot access alone:

| Bridge Command | Permission | Purpose |
|----------------|------------|---------|
| `agent.file_dialog` | `filesystem` | Open native file picker for data import |
| `agent.export_tool` | `filesystem` | Save generated tool `.py` file to user-chosen location |
| `agent.notify` | `notifications` | Desktop notification on pipeline completion |
| `agent.tray_status` | `window` | Update system tray icon/tooltip with agent state |
| `agent.open_external` | `network` | Open tool documentation in default browser |

Example — native file dialog for importing data:

```javascript
// Frontend: user clicks "Import Data File"
async function importFile() {
    const result = await window.zero.invoke("agent.file_dialog", {
        title: "Select data file",
        filters: [
            { name: "Data Files", extensions: ["csv", "json", "txt"] },
            { name: "All Files", extensions: ["*"] }
        ]
    });
    if (result.path) {
        // Send file path to agent backend
        await fetch("http://localhost:8001/api/sessions/" + sessionId + "/messages", {
            method: "POST",
            body: JSON.stringify({
                message: `Process the file at ${result.path}`
            })
        });
    }
}
```

### 4.2 Frontend Components

The React/Svelte frontend is organized into five primary panels:

**1. Chat Panel** — Conversational interface with the root orchestrator. Displays messages, tool execution results, and supports file attachment via native file dialogs.

**2. Registry Browser** — Searchable list of all registered tools with metadata (name, description, version, risk level, creation date). Supports tool deletion and export to local filesystem.

**3. Pipeline Monitor** — Real-time visualization of the tool creation pipeline. Shows current phase (spec → code → test → register), intermediate outputs, and safety check results as the pipeline progresses.

**4. Sandbox Viewer** — Displays sandbox execution output (stdout/stderr), test results with pass/fail status, and timeout information. Critical for debugging failed tool creation attempts.

**5. Tool Code Editor** — Read-only syntax-highlighted view of generated tool source code. Shows version history when database-backed versioning is implemented.

### 4.3 Security Alignment

zero-native's default-deny security model maps naturally to our agent's safety policy:

| Agent Safety Layer | zero-native Equivalent |
|--------------------|-----------------------|
| Blocked imports (subprocess, socket, sys, ctypes) | Bridge commands cannot invoke shell; only HTTP to localhost |
| AST-based code validation | WebView treated as untrusted; native commands require registration |
| Sandbox execution with timeout | Bridge message size limits (16 KiB); handler timeouts |
| Risk classification (low/medium/high) | Permission categories (filesystem, network, custom) |
| Keyword scanning (eval, exec, open) | Origin checks prevent unauthorized command invocation |

The desktop shell adds an additional security boundary: even if the web frontend were compromised, it could only invoke explicitly registered bridge commands with pre-approved permissions. The Python backend's safety policy (AST analysis, sandboxing) remains the primary enforcement layer.

---

## 5. Implementation Roadmap

| Phase | Scope | Deliverable | Timeline |
|-------|-------|-------------|----------|
| **Phase 1: Shell** | zero-native project setup, Zig process manager for Python backend, basic WebView loading | Desktop app that launches agent backend and shows a blank page | 1 week |
| **Phase 2: Chat** | React frontend with chat panel, connected to FastAPI message endpoints | Functional chat with the agent inside a desktop window | 1-2 weeks |
| **Phase 3: Registry** | Registry browser panel, tool search, detail view, delete action | Browse, search, and manage registered tools | 1 week |
| **Phase 4: Pipeline** | Real-time pipeline monitor, sandbox output viewer, safety status display | Observe tool creation as it progresses through each phase | 1-2 weeks |
| **Phase 5: Native** | System tray, notifications, native file dialogs, tool export, bridge commands | Full native desktop integration | 1 week |
| **Phase 6: Package** | App bundling, code signing, installer for macOS/Linux | Distributable `.app` / `.deb` / `.AppImage` | 1 week |

**Total estimated timeline: 6-8 weeks**

---

## 6. Challenges and Considerations

### 6.1 Framework Maturity

zero-native is a pre-release project (v0.x). While backed by Vercel Labs and accumulating community adoption (3,000+ GitHub stars), it carries risks inherent to early-stage frameworks:

- **API instability**: Breaking changes may occur between releases
- **Documentation gaps**: Some advanced patterns (multi-window, custom protocols) are not yet fully documented
- **Ecosystem**: Fewer community plugins and examples compared to established frameworks

**Mitigation**: The thin integration layer (Zig shell is primarily a process manager and bridge dispatcher) limits exposure to API changes. The frontend is standard React/Svelte, portable to any framework. The Python backend is entirely decoupled.

### 6.2 Zig Learning Curve

Zig is a systems programming language less widely known than Rust or C++. The development team would need to acquire Zig proficiency for the native layer.

**Mitigation**: The Zig layer is intentionally minimal — process management, bridge handlers, and system tray integration. The bulk of the application logic resides in the web frontend (JavaScript/TypeScript) and the Python backend, both well-established in the team's skill set.

### 6.3 Bridge Payload Limits

The 16 KiB message limit on bridge communication means large data transfers (e.g., full tool source code, lengthy sandbox output) cannot pass through the bridge directly.

**Mitigation**: Large data flows bypass the bridge entirely, traveling directly between the frontend and the FastAPI backend over HTTP on localhost. The bridge is reserved for native-only operations: file dialogs, notifications, and system tray updates.

### 6.4 Cross-Platform Consistency

System WebView rendering varies across platforms (WebKit on macOS, WebKitGTK on Linux, WebView2 on Windows). UI inconsistencies may arise.

**Mitigation**: zero-native offers bundled Chromium (CEF) as an alternative web engine for consistent rendering, at the cost of larger binary size (~80-120 MB). For a research tool, system WebView is sufficient; CEF can be adopted if distribution to diverse environments becomes a requirement.

---

## 7. Conclusion

A native desktop application transforms the self-evolving agent from a developer-facing tool into a self-contained research environment. zero-native provides a modern, lightweight path to desktop integration without the resource overhead of Electron or the complexity of full native UI development. Its three key properties — sub-megabyte binaries, permission-controlled bridge communication, and framework-agnostic web frontends — align with the requirements of a locally-running, security-conscious AI agent system.

The proposed three-layer architecture (Zig desktop shell → web frontend → Python backend) preserves the existing agent infrastructure entirely while adding native desktop capabilities: system tray presence, file system integration, and OS-level notifications. The thin Zig integration layer minimizes the exposure to framework maturity risks while enabling full native desktop functionality.

This approach positions the self-evolving agent for use beyond the research lab — as a distributable desktop application that collaborators can install, launch, and use without configuring Python environments, starting servers, or navigating terminal interfaces.

---

## References

[1] zero-native, Vercel Labs, https://zero-native.dev, https://github.com/vercel-labs/zero-native, 2025.

[2] Z. Wang et al., "VOYAGER: An Open-Ended Embodied Agent with Large Language Models," arXiv:2305.16291, 2023.

[3] T. Cai et al., "Large Language Models as Tool Makers," arXiv:2305.17126, 2023.

[4] Google Agent Development Kit (ADK), https://google.github.io/adk-python/, 2025.

[5] Zig Programming Language, https://ziglang.org, 2024.

[6] WebView, https://developer.apple.com/documentation/webkit/wkwebview (macOS), https://webkitgtk.org (Linux), 2024.

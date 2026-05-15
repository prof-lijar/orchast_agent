<script>
  import { onMount } from "svelte";
  import { checkBackendHealth, createSession, fetchCurrentModel, switchModel as apiSwitchModel, getSession } from "./lib/api.js";
  import ChatPanel from "./lib/ChatPanel.svelte";
  import LeftSidebar from "./lib/LeftSidebar.svelte";
  import RegistryPanel from "./lib/RegistryPanel.svelte";
  import StatusBar from "./lib/StatusBar.svelte";

  let backendOnline = $state(false);
  let bridgeAvailable = $state(false);
  let sessionId = $state("");
  let userId = $state("user");
  let appName = $state("app");
  let currentModel = $state("");
  let healthInterval;
  let sessionMessages = $state([]);
  let sessionKey = $state(0);

  onMount(() => {
    bridgeAvailable = !!window.zero;
    connectToBackend();
    healthInterval = setInterval(pollHealth, 10000);
    return () => clearInterval(healthInterval);
  });

  async function connectToBackend() {
    backendOnline = await checkBackendHealth();
    if (backendOnline && !sessionId) {
      try {
        const session = await createSession(appName);
        sessionId = session.id;
      } catch {
        // session creation failed — user can still see the UI
      }
    }
    if (backendOnline) {
      try {
        const info = await fetchCurrentModel();
        currentModel = info.model;
      } catch { /* ignore */ }
    }
  }

  async function pollHealth() {
    const wasOnline = backendOnline;
    backendOnline = await checkBackendHealth();
    if (!wasOnline && backendOnline && !sessionId) {
      connectToBackend();
    }
    if (backendOnline) {
      try {
        const info = await fetchCurrentModel();
        currentModel = info.model;
      } catch { /* ignore */ }
    }
  }

  async function handleModelSwitch(modelName) {
    try {
      const result = await apiSwitchModel(modelName);
      if (result.success) {
        currentModel = result.model;
      }
    } catch (err) {
      console.error("Model switch failed:", err);
    }
  }

  async function handleSessionSelect(sid) {
    if (sid === sessionId) return;
    try {
      const session = await getSession(appName, userId, sid);
      const msgs = [];
      for (const event of session.events || []) {
        const parts = event?.content?.parts ?? [];
        const author = event?.author;
        for (const part of parts) {
          if (part.text) {
            msgs.push({ role: author === "user" ? "user" : "agent", text: part.text });
          }
        }
      }
      sessionId = sid;
      sessionMessages = msgs;
      sessionKey++;
    } catch (err) {
      console.error("Failed to load session:", err);
    }
  }

  async function handleNewSession() {
    try {
      const session = await createSession(appName);
      sessionId = session.id;
      sessionMessages = [];
      sessionKey++;
    } catch (err) {
      console.error("Failed to create session:", err);
    }
  }
</script>

<div class="app-layout">
  <header class="titlebar">
    <div class="logo">
      <span class="logo-icon">&#9670;</span>
      <span>Self-Evolving Agent</span>
    </div>
    <span class="version">v0.1.0</span>
  </header>

  <div class="main-content">
    <div class="left-panel">
      <LeftSidebar
        {backendOnline}
        {currentModel}
        activeSessionId={sessionId}
        {appName}
        {userId}
        onModelSwitch={handleModelSwitch}
        onSessionSelect={handleSessionSelect}
        onNewSession={handleNewSession}
      />
    </div>
    <div class="chat-area">
      {#key sessionKey}
        <ChatPanel {appName} {userId} {sessionId} initialMessages={sessionMessages} />
      {/key}
    </div>
    <div class="sidebar">
      <RegistryPanel {backendOnline} />
    </div>
  </div>

  <StatusBar {backendOnline} {bridgeAvailable} {sessionId} {currentModel} />
</div>

<style>
  .app-layout {
    display: flex;
    flex-direction: column;
    height: 100vh;
    overflow: hidden;
  }

  .titlebar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 20px;
    background: #0f172a;
    color: #f8fafc;
    -webkit-app-region: drag;
  }

  .logo {
    display: flex;
    align-items: center;
    gap: 10px;
    font-weight: 700;
    font-size: 0.95em;
  }

  .logo-icon {
    color: #3b82f6;
    font-size: 1.2em;
  }

  .version {
    font-size: 0.75em;
    color: #64748b;
    font-family: "SF Mono", "Cascadia Code", monospace;
  }

  .main-content {
    display: flex;
    flex: 1;
    min-height: 0;
  }

  .left-panel {
    width: 220px;
    flex-shrink: 0;
    border-right: 1px solid #1e293b;
  }

  .chat-area {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-width: 0;
  }

  .sidebar {
    width: 280px;
    flex-shrink: 0;
  }
</style>

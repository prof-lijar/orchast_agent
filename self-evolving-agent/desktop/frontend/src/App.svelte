<script>
  import { onMount } from "svelte";
  import { checkBackendHealth, createSession } from "./lib/api.js";
  import ChatPanel from "./lib/ChatPanel.svelte";
  import RegistryPanel from "./lib/RegistryPanel.svelte";
  import StatusBar from "./lib/StatusBar.svelte";

  let backendOnline = $state(false);
  let bridgeAvailable = $state(false);
  let sessionId = $state("");
  let userId = $state("user");
  let appName = $state("app");
  let healthInterval;

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
  }

  async function pollHealth() {
    const wasOnline = backendOnline;
    backendOnline = await checkBackendHealth();
    if (!wasOnline && backendOnline && !sessionId) {
      connectToBackend();
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
    <div class="chat-area">
      <ChatPanel {appName} {userId} {sessionId} />
    </div>
    <div class="sidebar">
      <RegistryPanel {backendOnline} />
    </div>
  </div>

  <StatusBar {backendOnline} {bridgeAvailable} {sessionId} />
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

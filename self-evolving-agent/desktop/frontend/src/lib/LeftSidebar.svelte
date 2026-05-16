<script>
  import { fetchModels, listSessions, deleteSession } from "./api.js";

  let {
    backendOnline = false,
    currentModel = "",
    activeSessionId = "",
    appName = "app",
    userId = "user",
    onModelSwitch = () => {},
    onSessionSelect = () => {},
    onNewSession = () => {},
  } = $props();

  let models = $state([]);
  let sessions = $state([]);
  let modelsOpen = $state(false);
  let switching = $state(false);
  let loadingSessions = $state(false);

  $effect(() => {
    if (backendOnline) {
      loadModels();
      loadSessions();
    }
  });

  $effect(() => {
    if (activeSessionId && backendOnline) {
      loadSessions();
    }
  });

  async function loadModels() {
    try {
      const data = await fetchModels();
      models = data.models || [];
    } catch {
      models = [];
    }
  }

  async function loadSessions() {
    if (!backendOnline) return;
    loadingSessions = true;
    try {
      const data = await listSessions(appName, userId);
      sessions = Array.isArray(data) ? data : [];
    } catch {
      sessions = [];
    } finally {
      loadingSessions = false;
    }
  }

  async function selectModel(name) {
    if (name === currentModel || switching) return;
    switching = true;
    modelsOpen = false;
    try {
      await onModelSwitch(name);
    } finally {
      switching = false;
    }
  }

  async function handleDelete(e, sid) {
    e.stopPropagation();
    try {
      await deleteSession(appName, userId, sid);
      sessions = sessions.filter((s) => s.id !== sid);
      if (sid === activeSessionId) {
        onNewSession();
      }
    } catch { /* ignore */ }
  }

  function sessionLabel(s) {
    const id = s.id || "";
    return id.slice(0, 12);
  }

  function handleClickOutside(e) {
    if (modelsOpen && !e.target.closest(".model-section")) {
      modelsOpen = false;
    }
  }
</script>

<svelte:window onclick={handleClickOutside} />

<div class="left-sidebar">
  <!-- Model Selector -->
  <div class="model-section">
    <div class="section-label">MODEL</div>
    <button
      class="model-btn"
      onclick={() => { if (backendOnline) modelsOpen = !modelsOpen; }}
      disabled={!backendOnline}
    >
      <span class="model-dot" class:active={!!currentModel}></span>
      <span class="model-text">{switching ? "Switching..." : currentModel || "no model"}</span>
      <span class="chevron">{modelsOpen ? "▴" : "▾"}</span>
    </button>
    {#if modelsOpen}
      <div class="model-list">
        {#each models as m}
          <button
            class="model-option"
            class:current={m.name === currentModel}
            onclick={() => selectModel(m.name)}
            disabled={switching}
          >
            <span class="badge" class:ollama={m.provider === "ollama"} class:gemini={m.provider === "gemini"}>
              {m.provider}
            </span>
            <span class="opt-name">{m.name}</span>
            {#if m.name === currentModel}
              <span class="check">&check;</span>
            {/if}
          </button>
        {/each}
        {#if models.length === 0}
          <div class="empty">No models found</div>
        {/if}
      </div>
    {/if}
  </div>

  <div class="divider"></div>

  <!-- Sessions -->
  <div class="sessions-section">
    <div class="sessions-header">
      <span class="section-label">SESSIONS</span>
      <button class="new-btn" onclick={onNewSession} disabled={!backendOnline} title="New session">+</button>
    </div>
    <div class="session-list">
      {#if loadingSessions}
        <div class="empty">Loading...</div>
      {:else if sessions.length === 0}
        <div class="empty">No sessions</div>
      {/if}
      {#each sessions as s}
        <div
          class="session-item"
          class:active={s.id === activeSessionId}
          role="button"
          tabindex="0"
          onclick={() => onSessionSelect(s.id)}
          onkeydown={(e) => { if (e.key === "Enter") onSessionSelect(s.id); }}
        >
          <span class="session-icon">&#9662;</span>
          <span class="session-label">{sessionLabel(s)}</span>
          <button
            class="delete-btn"
            onclick={(e) => handleDelete(e, s.id)}
            title="Delete session"
          >&times;</button>
        </div>
      {/each}
    </div>
  </div>
</div>

<style>
  .left-sidebar {
    display: flex;
    flex-direction: column;
    width: 100%;
    height: 100%;
    background: #0f172a;
    color: #cbd5e1;
    font-family: "SF Mono", "Cascadia Code", "Fira Code", monospace;
    font-size: 0.8em;
    overflow: hidden;
  }

  .section-label {
    font-size: 0.7em;
    font-weight: 700;
    letter-spacing: 0.08em;
    color: #64748b;
    padding: 12px 14px 6px;
  }

  .divider {
    height: 1px;
    background: #1e293b;
    margin: 4px 10px;
  }

  /* Model selector */
  .model-section {
    position: relative;
  }

  .model-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    width: calc(100% - 20px);
    margin: 0 10px 4px;
    padding: 8px 10px;
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 6px;
    color: #e2e8f0;
    cursor: pointer;
    font-family: inherit;
    font-size: inherit;
    text-align: left;
    transition: border-color 0.15s;
  }

  .model-btn:hover:not(:disabled) {
    border-color: #3b82f6;
  }

  .model-btn:disabled {
    opacity: 0.4;
    cursor: default;
  }

  .model-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #475569;
    flex-shrink: 0;
  }

  .model-dot.active {
    background: #22c55e;
  }

  .model-text {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .chevron {
    font-size: 0.7em;
    color: #64748b;
    flex-shrink: 0;
  }

  .model-list {
    margin: 0 10px 4px;
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 6px;
    max-height: 220px;
    overflow-y: auto;
  }

  .model-option {
    display: flex;
    align-items: center;
    gap: 8px;
    width: 100%;
    padding: 7px 10px;
    background: none;
    border: none;
    color: #cbd5e1;
    cursor: pointer;
    font-family: inherit;
    font-size: inherit;
    text-align: left;
  }

  .model-option:hover:not(:disabled) {
    background: #334155;
  }

  .model-option.current {
    background: rgba(59, 130, 246, 0.15);
  }

  .model-option:disabled {
    opacity: 0.5;
    cursor: default;
  }

  .badge {
    font-size: 0.8em;
    padding: 1px 5px;
    border-radius: 3px;
    font-weight: 600;
    flex-shrink: 0;
  }

  .badge.ollama {
    background: #1e3a5f;
    color: #60a5fa;
  }

  .badge.gemini {
    background: #1a3320;
    color: #4ade80;
  }

  .opt-name {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .check {
    color: #22c55e;
    flex-shrink: 0;
  }

  /* Sessions */
  .sessions-section {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
  }

  .sessions-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-right: 10px;
  }

  .new-btn {
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 5px;
    color: #94a3b8;
    font-size: 1.1em;
    cursor: pointer;
    line-height: 1;
  }

  .new-btn:hover:not(:disabled) {
    border-color: #3b82f6;
    color: #e2e8f0;
  }

  .new-btn:disabled {
    opacity: 0.4;
    cursor: default;
  }

  .session-list {
    flex: 1;
    overflow-y: auto;
    padding: 4px 6px;
  }

  .session-item {
    display: flex;
    align-items: center;
    gap: 8px;
    width: 100%;
    padding: 8px 10px;
    margin: 1px 0;
    background: none;
    border: none;
    border-radius: 6px;
    color: #94a3b8;
    cursor: pointer;
    font-family: inherit;
    font-size: inherit;
    text-align: left;
    transition: background 0.1s;
  }

  .session-item:hover {
    background: #1e293b;
    color: #cbd5e1;
  }

  .session-item.active {
    background: #1e293b;
    color: #e2e8f0;
    border-left: 2px solid #3b82f6;
  }

  .session-icon {
    font-size: 0.6em;
    color: #475569;
    flex-shrink: 0;
  }

  .session-label {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .delete-btn {
    display: none;
    background: none;
    border: none;
    color: #64748b;
    cursor: pointer;
    font-size: 1.1em;
    padding: 0 2px;
    line-height: 1;
    flex-shrink: 0;
  }

  .session-item:hover .delete-btn {
    display: block;
  }

  .delete-btn:hover {
    color: #ef4444;
  }

  .empty {
    padding: 16px;
    text-align: center;
    color: #475569;
    font-size: 0.9em;
  }
</style>

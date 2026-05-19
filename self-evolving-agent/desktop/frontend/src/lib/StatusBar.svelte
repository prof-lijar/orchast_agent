<script>
  let {
    backendOnline = false,
    bridgeAvailable = false,
    sessionId = "",
    currentModel = "",
  } = $props();
</script>

<div class="status-bar">
  <div class="left">
    <span class="indicator" class:online={backendOnline} class:offline={!backendOnline}></span>
    <span class="label">
      Backend: {backendOnline ? "connected" : "offline"}
    </span>
    <span class="separator">|</span>
    <span class="label">Bridge: {bridgeAvailable ? "active" : "N/A"}</span>
  </div>
  <div class="right">
    {#if currentModel}
      <span class="model-info">{currentModel}</span>
      <span class="separator">|</span>
    {/if}
    {#if sessionId}
      <span class="session">Session: {sessionId.slice(0, 8)}...</span>
    {:else}
      <span class="session">No session</span>
    {/if}
  </div>
</div>

<style>
  .status-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 16px;
    background: #f8fafc;
    border-top: 1px solid #e2e8f0;
    color: #64748b;
    font-size: 0.75em;
    font-family: "SF Mono", "Cascadia Code", "Fira Code", monospace;
  }

  .left, .right {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .indicator {
    width: 8px;
    height: 8px;
    border-radius: 50%;
  }

  .indicator.online { background: #22c55e; }
  .indicator.offline { background: #ef4444; }

  .separator { color: #cbd5e1; }
  .label { color: #475569; }
  .session { color: #94a3b8; }
  .model-info { color: #64748b; }
</style>

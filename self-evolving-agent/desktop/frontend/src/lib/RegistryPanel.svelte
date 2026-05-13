<script>
  let { backendOnline = false } = $props();

  let tools = $state([]);
  let searchQuery = $state("");
  let selectedTool = $state(null);
  let loading = $state(false);
  let error = $state("");

  const API_BASE = "http://127.0.0.1:8001";

  async function fetchRegistry() {
    if (!backendOnline) return;
    loading = true;
    error = "";
    try {
      const res = await fetch(`${API_BASE}/apps/app/users/user/sessions`, {
        signal: AbortSignal.timeout(5000),
      });
      if (res.ok) {
        loading = false;
      }
    } catch (err) {
      error = "Could not reach backend";
    } finally {
      loading = false;
    }
  }

  let filteredTools = $derived(
    tools.filter(
      (t) =>
        t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.description.toLowerCase().includes(searchQuery.toLowerCase())
    )
  );

  function selectTool(tool) {
    selectedTool = selectedTool?.name === tool.name ? null : tool;
  }
</script>

<div class="registry-panel">
  <div class="panel-header">
    <h3>Tool Registry</h3>
    <span class="count">{tools.length} tools</span>
  </div>

  <div class="search-bar">
    <input
      type="text"
      bind:value={searchQuery}
      placeholder="Search tools..."
    />
  </div>

  <div class="tool-list">
    {#if !backendOnline}
      <div class="status-msg">Backend offline</div>
    {:else if loading}
      <div class="status-msg">Loading...</div>
    {:else if error}
      <div class="status-msg error">{error}</div>
    {:else if filteredTools.length === 0}
      <div class="status-msg">
        {searchQuery ? "No matching tools" : "No tools registered yet"}
      </div>
    {/if}

    {#each filteredTools as tool}
      <button
        class="tool-item"
        class:selected={selectedTool?.name === tool.name}
        onclick={() => selectTool(tool)}
      >
        <span class="tool-name">{tool.name}</span>
        <span class="tool-risk" class:low={tool.risk_level === "low"} class:medium={tool.risk_level === "medium"}>
          {tool.risk_level}
        </span>
      </button>
    {/each}
  </div>

  {#if selectedTool}
    <div class="tool-detail">
      <h4>{selectedTool.name}</h4>
      <p>{selectedTool.description}</p>
      <div class="meta">
        <span>v{selectedTool.version}</span>
        <span>{selectedTool.risk_level} risk</span>
      </div>
    </div>
  {/if}
</div>

<style>
  .registry-panel {
    display: flex;
    flex-direction: column;
    height: 100%;
    min-height: 0;
    border-left: 1px solid #e2e8f0;
    background: #fafbfc;
  }

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    border-bottom: 1px solid #e2e8f0;
  }

  .panel-header h3 {
    margin: 0;
    font-size: 0.85em;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #475569;
  }

  .count {
    font-size: 0.75em;
    color: #94a3b8;
  }

  .search-bar {
    padding: 8px 12px;
    border-bottom: 1px solid #e2e8f0;
  }

  .search-bar input {
    width: 100%;
    padding: 8px 12px;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    font-size: 0.85em;
    outline: none;
    background: white;
    box-sizing: border-box;
  }

  .search-bar input:focus { border-color: #2563eb; }

  .tool-list {
    flex: 1;
    overflow-y: auto;
    padding: 4px 8px;
  }

  .status-msg {
    padding: 20px;
    text-align: center;
    color: #94a3b8;
    font-size: 0.85em;
  }

  .status-msg.error { color: #dc2626; }

  .tool-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
    padding: 10px 12px;
    margin: 2px 0;
    border: 1px solid transparent;
    border-radius: 8px;
    background: transparent;
    cursor: pointer;
    text-align: left;
    font-family: inherit;
  }

  .tool-item:hover { background: #f1f5f9; }
  .tool-item.selected { background: #eff6ff; border-color: #bfdbfe; }

  .tool-name {
    font-size: 0.85em;
    font-weight: 500;
    color: #0f172a;
  }

  .tool-risk {
    font-size: 0.7em;
    padding: 2px 8px;
    border-radius: 10px;
    font-weight: 600;
  }

  .tool-risk.low { background: #dcfce7; color: #166534; }
  .tool-risk.medium { background: #fef9c3; color: #854d0e; }

  .tool-detail {
    padding: 12px 16px;
    border-top: 1px solid #e2e8f0;
    background: white;
  }

  .tool-detail h4 {
    margin: 0 0 6px;
    font-size: 0.85em;
    color: #0f172a;
  }

  .tool-detail p {
    margin: 0 0 8px;
    font-size: 0.8em;
    color: #64748b;
    line-height: 1.4;
  }

  .meta {
    display: flex;
    gap: 12px;
    font-size: 0.75em;
    color: #94a3b8;
  }
</style>

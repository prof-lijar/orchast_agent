<script>
  import { sendMessageStream } from "./api.js";
  import { marked } from "marked";

  marked.setOptions({ breaks: true, gfm: true });

  let { appName = "app", userId = "user", sessionId = "", initialMessages = [] } = $props();

  // svelte-ignore state_referenced_locally
  let messages = $state([...initialMessages]);
  let input = $state("");
  let loading = $state(false);
  let chatContainer;
  let inputEl;
  let copiedIndex = $state(-1);
  let editingIndex = $state(-1);
  let abortCtrl = $state(null);

  function copyText(text, index) {
    navigator.clipboard.writeText(text);
    copiedIndex = index;
    setTimeout(() => { copiedIndex = -1; }, 5000);
  }

  function startEdit(text, index) {
    editingIndex = index;
    input = text;
    setTimeout(() => inputEl?.focus(), 60);
  }

  let scrollRAF = 0;
  function scrollToBottom() {
    if (scrollRAF || !chatContainer) return;
    scrollRAF = requestAnimationFrame(() => {
      chatContainer.scrollTop = chatContainer.scrollHeight;
      scrollRAF = 0;
    });
  }

  function stopStreaming() {
    abortCtrl?.abort();
    abortCtrl = null;
  }

  async function handleSend() {
    const text = input.trim();
    if (!text || loading || !sessionId) return;

    if (editingIndex >= 0) {
      messages = messages.slice(0, editingIndex);
      editingIndex = -1;
    }

    messages = [...messages, { role: "user", text }];
    input = "";
    loading = true;
    scrollToBottom();

    const placeholder = { role: "agent", text: "", streaming: true };
    messages = [...messages, placeholder];
    const idx = messages.length - 1;

    const ctrl = new AbortController();
    abortCtrl = ctrl;

    try {
      await sendMessageStream(appName, userId, sessionId, text, {
        onChunk(chunk) {
          messages[idx].text += chunk;
          scrollToBottom();
        },
        onError(err) {
          messages = [...messages, { role: "error", text: String(err) }];
        },
        onComplete() {
          messages[idx].streaming = false;
          if (!messages[idx].text) {
            messages.splice(idx, 1);
            messages = messages;
          }
        },
        signal: ctrl.signal,
      });
    } catch (err) {
      if (err.name !== "AbortError") {
        messages[idx].streaming = false;
        if (!messages[idx].text) messages.splice(idx, 1);
        messages = [...messages, { role: "error", text: err.message }];
      } else {
        messages[idx].streaming = false;
      }
    } finally {
      loading = false;
      abortCtrl = null;
      scrollToBottom();
      setTimeout(() => inputEl?.focus(), 60);
    }
  }

  function handleKeydown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }
</script>

<div class="chat-panel">
  <div class="chat-messages" bind:this={chatContainer}>
    {#if messages.length === 0}
      <div class="empty-state">
        <p>Start a conversation with the Self-Evolving Agent.</p>
        <p class="hint">Ask it to create, find, or use tools.</p>
      </div>
    {/if}
    {#each messages as msg, i}
      {#if msg.role === "agent"}
        <div class="message agent">
          <span class="label">Agent</span>
          <div class="content markdown-body">{@html marked.parse(msg.text || "")}{#if msg.streaming}<span class="cursor">|</span>{/if}</div>
          {#if !msg.streaming}
            <button class="copy-btn" onclick={() => copyText(msg.text, i)} title="Copy to clipboard">
              {#if copiedIndex === i}
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
              {:else}
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
              {/if}
            </button>
          {/if}
        </div>
      {:else if msg.role === "user"}
        <div class="message-wrap user">
          <div class="message user">
            <span class="label">You</span>
            <pre class="content">{msg.text}</pre>
          </div>
          <div class="user-actions">
            <button class="action-btn" onclick={() => copyText(msg.text, i)} title="Copy to clipboard">
              {#if copiedIndex === i}
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
              {:else}
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
              {/if}
            </button>
            <button class="action-btn" onclick={() => startEdit(msg.text, i)} title="Edit message" disabled={loading}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
            </button>
          </div>
        </div>
      {:else}
        <div class="message error">
          <span class="label">Error</span>
          <pre class="content">{msg.text}</pre>
        </div>
      {/if}
    {/each}
    {#if loading && !messages.some(m => m.streaming)}
      <div class="message agent">
        <span class="label">Agent</span>
        <span class="typing">Thinking...</span>
      </div>
    {/if}
  </div>

  <div class="chat-input">
    <textarea
      bind:this={inputEl}
      bind:value={input}
      onkeydown={handleKeydown}
      placeholder={sessionId ? "Message the agent..." : "Connecting..."}
      disabled={!sessionId || loading}
      rows="2"
    ></textarea>
    {#if abortCtrl}
      <button class="stop-btn" onclick={stopStreaming}>Stop</button>
    {:else}
      <button onclick={handleSend} disabled={!input.trim() || loading || !sessionId}>
        Send
      </button>
    {/if}
  </div>
</div>

<style>
  .chat-panel {
    display: flex;
    flex-direction: column;
    height: 100%;
    min-height: 0;
  }

  .chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    flex: 1;
    color: #64748b;
    text-align: center;
  }

  .empty-state p { margin: 4px 0; }
  .empty-state .hint { font-size: 0.85em; color: #94a3b8; }

  .message {
    max-width: 85%;
    padding: 10px 14px;
    border-radius: 12px;
    font-size: 0.9em;
    position: relative;
  }

  .message.user {
    align-self: flex-end;
    background: #2563eb;
    color: white;
  }

  .message.agent {
    align-self: flex-start;
    background: #f1f5f9;
    color: #0f172a;
    padding-bottom: 36px;
  }

  .message.error {
    align-self: flex-start;
    background: #fef2f2;
    color: #dc2626;
    border: 1px solid #fecaca;
  }

  .label {
    display: block;
    font-size: 0.75em;
    font-weight: 600;
    margin-bottom: 4px;
    opacity: 0.7;
  }

  .content {
    margin: 0;
    white-space: pre-wrap;
    word-break: break-word;
    font-family: inherit;
  }

  .markdown-body {
    white-space: normal;
  }

  .markdown-body :global(h1),
  .markdown-body :global(h2),
  .markdown-body :global(h3),
  .markdown-body :global(h4) {
    margin: 12px 0 6px;
    line-height: 1.3;
  }
  .markdown-body :global(h1) { font-size: 1.3em; }
  .markdown-body :global(h2) { font-size: 1.15em; }
  .markdown-body :global(h3) { font-size: 1.05em; }

  .markdown-body :global(p) {
    margin: 6px 0;
  }

  .markdown-body :global(ul),
  .markdown-body :global(ol) {
    margin: 6px 0;
    padding-left: 1.5em;
  }

  .markdown-body :global(li) {
    margin: 2px 0;
  }

  .markdown-body :global(code) {
    background: #e2e8f0;
    padding: 1px 5px;
    border-radius: 4px;
    font-family: "SF Mono", "Fira Code", "Cascadia Code", monospace;
    font-size: 0.88em;
  }

  .markdown-body :global(pre) {
    background: #1e293b;
    color: #e2e8f0;
    padding: 12px;
    border-radius: 8px;
    overflow-x: auto;
    margin: 8px 0;
  }

  .markdown-body :global(pre code) {
    background: none;
    padding: 0;
    color: inherit;
    font-size: 0.85em;
  }

  .markdown-body :global(blockquote) {
    border-left: 3px solid #94a3b8;
    margin: 8px 0;
    padding: 4px 12px;
    color: #475569;
  }

  .markdown-body :global(a) {
    color: #2563eb;
    text-decoration: underline;
  }

  .markdown-body :global(hr) {
    border: none;
    border-top: 1px solid #cbd5e1;
    margin: 12px 0;
  }

  .markdown-body :global(table) {
    border-collapse: collapse;
    margin: 8px 0;
    width: 100%;
    font-size: 0.88em;
  }

  .markdown-body :global(th),
  .markdown-body :global(td) {
    border: 1px solid #cbd5e1;
    padding: 6px 10px;
    text-align: left;
  }

  .markdown-body :global(th) {
    background: #e2e8f0;
    font-weight: 600;
  }

  .markdown-body :global(strong) {
    font-weight: 700;
  }

  .markdown-body :global(em) {
    font-style: italic;
  }

  .markdown-body :global(:first-child) {
    margin-top: 0;
  }

  .markdown-body :global(:last-child) {
    margin-bottom: 0;
  }

  .typing {
    color: #94a3b8;
    font-style: italic;
  }

  .message-wrap.user {
    align-self: flex-end;
    max-width: 85%;
    position: relative;
    padding-bottom: 28px;
  }

  .message-wrap.user .message {
    max-width: unset;
  }

  .user-actions {
    position: absolute;
    right: 0;
    bottom: 0;
    display: flex;
    gap: 4px;
  }

  .action-btn, .copy-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    padding: 0;
    background: transparent;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    color: #64748b;
    cursor: pointer;
    transition: all 0.15s ease;
    flex-shrink: 0;
  }

  .copy-btn {
    position: absolute;
    left: 8px;
    bottom: 6px;
  }

  .action-btn:hover, .copy-btn:hover { background: #334155; color: #ffffff; }
  .action-btn:disabled { opacity: 0.3; cursor: not-allowed; }

  .chat-input {
    display: flex;
    gap: 8px;
    padding: 12px 16px;
    border-top: 1px solid #e2e8f0;
    background: #ffffff;
  }

  textarea {
    flex: 1;
    padding: 10px 14px;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    font-family: inherit;
    font-size: 0.9em;
    resize: none;
    outline: none;
    background: #f8fafc;
  }

  textarea:focus { border-color: #2563eb; }
  textarea:disabled { opacity: 0.5; }

  button {
    padding: 10px 20px;
    background: #2563eb;
    color: white;
    border: none;
    border-radius: 10px;
    font-weight: 600;
    cursor: pointer;
    font-size: 0.9em;
  }

  button:hover:not(:disabled) { background: #1d4ed8; }
  button:disabled { opacity: 0.4; cursor: not-allowed; }

  .cursor {
    animation: blink 0.6s step-end infinite;
    color: #2563eb;
    font-weight: bold;
  }
  @keyframes blink { 50% { opacity: 0; } }

  .stop-btn {
    padding: 10px 20px;
    background: #dc2626;
    color: white;
    border: none;
    border-radius: 10px;
    font-weight: 600;
    cursor: pointer;
    font-size: 0.9em;
  }
  .stop-btn:hover { background: #b91c1c; }
</style>

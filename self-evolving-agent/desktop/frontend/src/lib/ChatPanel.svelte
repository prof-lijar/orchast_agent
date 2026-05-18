<script>
  import { sendMessage } from "./api.js";

  let { appName = "app", userId = "user", sessionId = "", initialMessages = [] } = $props();

  // svelte-ignore state_referenced_locally
  let messages = $state([...initialMessages]);
  let input = $state("");
  let loading = $state(false);
  let chatContainer;
  let inputEl;
  let copiedIndex = $state(-1);

  function copyText(text, index) {
    navigator.clipboard.writeText(text);
    copiedIndex = index;
    setTimeout(() => { copiedIndex = -1; }, 5000);
  }

  function scrollToBottom() {
    if (chatContainer) {
      setTimeout(() => {
        chatContainer.scrollTop = chatContainer.scrollHeight;
      }, 50);
    }
  }

  async function handleSend() {
    const text = input.trim();
    if (!text || loading || !sessionId) return;

    messages = [...messages, { role: "user", text }];
    input = "";
    loading = true;
    scrollToBottom();

    try {
      const response = await sendMessage(appName, userId, sessionId, text);
      const events = Array.isArray(response) ? response : [response];
      for (const event of events) {
        const parts = event?.content?.parts ?? [];
        for (const part of parts) {
          if (part.text) {
            messages = [...messages, { role: "agent", text: part.text }];
          }
        }
      }
    } catch (err) {
      messages = [...messages, { role: "error", text: err.message }];
    } finally {
      loading = false;
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
          <pre class="content">{msg.text}</pre>
          <button class="copy-btn" onclick={() => copyText(msg.text, i)} title="Copy to clipboard">
            {#if copiedIndex === i}
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
            {:else}
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
            {/if}
          </button>
        </div>
      {:else if msg.role === "user"}
        <div class="message-wrap user">
          <div class="message user">
            <span class="label">You</span>
            <pre class="content">{msg.text}</pre>
          </div>
          <button class="copy-btn user-copy" onclick={() => copyText(msg.text, i)} title="Copy to clipboard">
            {#if copiedIndex === i}
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
            {:else}
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
            {/if}
          </button>
        </div>
      {:else}
        <div class="message error">
          <span class="label">Error</span>
          <pre class="content">{msg.text}</pre>
        </div>
      {/if}
    {/each}
    {#if loading}
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
    <button onclick={handleSend} disabled={!input.trim() || loading || !sessionId}>
      Send
    </button>
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

  .user-copy {
    position: absolute;
    right: 0;
    bottom: 0;
  }

  .copy-btn {
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

  .copy-btn:not(.user-copy) {
    position: absolute;
    left: 8px;
    bottom: 6px;
  }

  .copy-btn:hover { background: #334155; color: #ffffff; }

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
</style>

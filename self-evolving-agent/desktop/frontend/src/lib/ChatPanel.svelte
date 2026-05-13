<script>
  import { sendMessage } from "./api.js";

  let { appName = "app", userId = "user", sessionId = "" } = $props();

  let messages = $state([]);
  let input = $state("");
  let loading = $state(false);
  let chatContainer;

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
    {#each messages as msg}
      <div class="message {msg.role}">
        <span class="label">{msg.role === "user" ? "You" : msg.role === "error" ? "Error" : "Agent"}</span>
        <pre class="content">{msg.text}</pre>
      </div>
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

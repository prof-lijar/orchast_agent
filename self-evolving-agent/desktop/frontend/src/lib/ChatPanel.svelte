<script>
  import { onMount } from "svelte";
  import { sendMessageStream } from "./api.js";
  import { marked } from "marked";

  marked.setOptions({ breaks: true, gfm: true });

  let { appName = "app", userId = "user", sessionId = "", initialMessages = [] } = $props();

  const MAX_FILE_SIZE = 10 * 1024 * 1024;
  const ACCEPTED_TYPES = ".csv,.json,.txt,.pdf,.png,.jpg,.jpeg,.xlsx,.xls";

  // svelte-ignore state_referenced_locally
  let messages = $state([...initialMessages]);
  let input = $state("");
  let loading = $state(false);
  let chatContainer;
  let inputEl;
  let fileInput;
  let copiedIndex = $state(-1);
  let editingIndex = $state(-1);
  let abortCtrl = $state(null);
  let attachedFiles = $state([]);
  let dragging = $state(false);
  let expanded = $state(false);

  onMount(() => { inputEl?.focus(); });

  function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  }

  function fileToBase64(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const bytes = new Uint8Array(reader.result);
        let binary = "";
        for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
        resolve(btoa(binary));
      };
      reader.onerror = reject;
      reader.readAsArrayBuffer(file);
    });
  }

  async function addFiles(fileList) {
    for (const file of fileList) {
      if (file.size > MAX_FILE_SIZE) {
        alert(`File "${file.name}" exceeds 10 MB limit.`);
        continue;
      }
      const base64 = await fileToBase64(file);
      const isImage = file.type.startsWith("image/");
      attachedFiles = [...attachedFiles, {
        name: file.name,
        size: file.size,
        mime: file.type || "application/octet-stream",
        base64,
        previewUrl: isImage ? URL.createObjectURL(file) : null,
      }];
    }
  }

  function handleFileSelect(e) {
    if (e.target.files?.length) addFiles(e.target.files);
    e.target.value = "";
  }

  function removeFile(index) {
    const f = attachedFiles[index];
    if (f.previewUrl) URL.revokeObjectURL(f.previewUrl);
    attachedFiles = attachedFiles.filter((_, i) => i !== index);
  }

  function handleDragOver(e) {
    e.preventDefault();
    dragging = true;
  }

  function handleDragLeave() {
    dragging = false;
  }

  function handleDrop(e) {
    e.preventDefault();
    dragging = false;
    if (e.dataTransfer?.files?.length) addFiles(e.dataTransfer.files);
  }

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
    const hasFiles = attachedFiles.length > 0;
    if ((!text && !hasFiles) || loading || !sessionId) return;

    if (editingIndex >= 0) {
      messages = messages.slice(0, editingIndex);
      editingIndex = -1;
    }

    const fileMeta = attachedFiles.map(f => ({ name: f.name, size: f.size, mime: f.mime, previewUrl: f.previewUrl }));
    const filesToSend = attachedFiles.map(f => ({ mime: f.mime, base64: f.base64 }));

    messages = [...messages, { role: "user", text: text || "(attached files)", files: fileMeta }];
    input = "";
    attachedFiles = [];
    loading = true;
    resetInputHeight();
    scrollToBottom();

    const placeholder = { role: "agent", text: "", thinking: "", streaming: true };
    messages = [...messages, placeholder];
    const idx = messages.length - 1;

    const ctrl = new AbortController();
    abortCtrl = ctrl;

    try {
      await sendMessageStream(appName, userId, sessionId, text || "User attached file(s). Describe what you see or process them.", filesToSend, {
        onThinking(chunk) {
          messages[idx].thinking += chunk;
          scrollToBottom();
        },
        onChunk(chunk) {
          messages[idx].text += chunk;
          scrollToBottom();
        },
        onError(err) {
          messages = [...messages, { role: "error", text: String(err) }];
        },
        onComplete() {
          messages[idx].streaming = false;
          if (!messages[idx].text && !messages[idx].thinking) {
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

  function autoResize() {
    if (!inputEl) return;
    inputEl.style.height = "auto";
    expanded = inputEl.scrollHeight > 40;
    inputEl.style.height = inputEl.scrollHeight + "px";
  }

  function resetInputHeight() {
    if (!inputEl) return;
    inputEl.style.height = "auto";
    expanded = false;
  }

  function handleKeydown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }
</script>

<div class="chat-panel" class:empty={messages.length === 0}>
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
          {#if msg.thinking}
            <details class="thinking-block" open={msg.streaming && !msg.text}>
              <summary>
                <svg class="thinking-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>
                {#if msg.streaming && !msg.text}<span class="thinking-pulse">Thinking...</span>{:else}Thought{/if}
              </summary>
              <div class="thinking-content">{msg.thinking}</div>
            </details>
          {/if}
          {#if msg.text || (msg.streaming && !msg.thinking)}
            <div class="content markdown-body">{@html marked.parse(msg.text || "")}{#if msg.streaming}<span class="cursor">|</span>{/if}</div>
          {/if}
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
            {#if msg.files?.length}
              <div class="message-files">
                {#each msg.files as f}
                  <div class="message-file-chip">
                    {#if f.previewUrl}
                      <img src={f.previewUrl} alt={f.name} />
                    {:else}
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                    {/if}
                    <span>{f.name}</span>
                  </div>
                {/each}
              </div>
            {/if}
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

  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div
    class="chat-input"
    class:drag-over={dragging}
    ondragover={handleDragOver}
    ondragleave={handleDragLeave}
    ondrop={handleDrop}
    role="region"
    aria-label="Message input with file drop"
  >
    {#if attachedFiles.length > 0}
      <div class="file-preview-strip">
        {#each attachedFiles as f, i}
          <div class="file-chip">
            {#if f.previewUrl}
              <img src={f.previewUrl} alt={f.name} />
            {:else}
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            {/if}
            <span class="file-chip-name">{f.name}</span>
            <span class="file-chip-size">{formatFileSize(f.size)}</span>
            <button class="file-chip-remove" onclick={() => removeFile(i)}>&times;</button>
          </div>
        {/each}
      </div>
    {/if}
    <input
      type="file"
      multiple
      accept={ACCEPTED_TYPES}
      bind:this={fileInput}
      onchange={handleFileSelect}
      style="display:none"
    />
    <div class="input-row" class:expanded>
      <button class="attach-btn" onclick={() => fileInput?.click()} disabled={loading} title="Attach file">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg>
      </button>
      <textarea
        bind:this={inputEl}
        bind:value={input}
        oninput={autoResize}
        onkeydown={handleKeydown}
        placeholder={sessionId ? "Message the agent..." : "Connecting..."}
        disabled={!sessionId || loading}
        rows="1"
      ></textarea>
      {#if abortCtrl}
        <button class="stop-btn" onclick={stopStreaming} title="Stop generating">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>
        </button>
      {:else}
        <button class="send-btn" onclick={handleSend} disabled={(!input.trim() && !attachedFiles.length) || loading || !sessionId}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12l7-7 7 7"/><path d="M12 19V5"/></svg>
        </button>
      {/if}
    </div>
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

  .chat-panel.empty {
    justify-content: center;
    align-items: center;
    gap: 24px;
  }

  .chat-panel.empty .chat-messages {
    flex: none;
    overflow: visible;
    padding: 0;
  }

  .chat-panel.empty .empty-state {
    flex: none;
  }

  .chat-panel.empty .chat-input {
    border-top: none;
    max-width: 680px;
    width: 100%;
    background: transparent;
  }

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

  .thinking-block {
    margin-bottom: 8px;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    background: #f8fafc;
    font-size: 0.85em;
  }

  .thinking-block summary {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 10px;
    cursor: pointer;
    color: #64748b;
    font-weight: 600;
    font-size: 0.9em;
    user-select: none;
    list-style: none;
  }

  .thinking-block summary::-webkit-details-marker { display: none; }

  .thinking-block summary::after {
    content: "▸";
    margin-left: auto;
    font-size: 0.8em;
    transition: transform 0.15s;
  }

  .thinking-block[open] summary::after {
    transform: rotate(90deg);
  }

  .thinking-icon {
    flex-shrink: 0;
    opacity: 0.6;
  }

  .thinking-pulse {
    animation: pulse 1.5s ease-in-out infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
  }

  .thinking-content {
    padding: 6px 10px 10px;
    color: #475569;
    white-space: pre-wrap;
    word-break: break-word;
    font-family: inherit;
    border-top: 1px solid #e2e8f0;
    line-height: 1.5;
    max-height: 200px;
    overflow-y: auto;
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
    flex-direction: column;
    gap: 0;
    padding: 12px 16px;
    border-top: 1px solid #e2e8f0;
    background: #ffffff;
    transition: border-color 0.15s;
  }

  .chat-input.drag-over {
    border-color: #2563eb;
    background: #eff6ff;
  }

  .input-row {
    display: grid;
    grid-template-columns: auto 1fr auto;
    grid-template-areas: "attach textarea send";
    align-items: center;
    border: 1px solid #e2e8f0;
    border-radius: 24px;
    background: #f8fafc;
    padding: 4px;
    transition: border-color 0.15s;
  }

  .input-row.expanded {
    grid-template-rows: 1fr auto;
    grid-template-areas:
      "textarea textarea textarea"
      "attach . send";
    border-radius: 20px;
  }

  .input-row:focus-within {
    border-color: #2563eb;
  }

  .file-preview-strip {
    display: flex;
    gap: 6px;
    padding: 6px 0 8px;
    overflow-x: auto;
    scrollbar-width: thin;
  }

  .file-chip {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 4px 8px;
    background: #f1f5f9;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    font-size: 0.78em;
    white-space: nowrap;
    flex-shrink: 0;
  }

  .file-chip img {
    width: 28px;
    height: 28px;
    object-fit: cover;
    border-radius: 4px;
  }

  .file-chip-name {
    max-width: 120px;
    overflow: hidden;
    text-overflow: ellipsis;
    color: #334155;
  }

  .file-chip-size {
    color: #94a3b8;
  }

  .file-chip-remove {
    padding: 0 4px;
    background: none;
    border: none;
    color: #94a3b8;
    font-size: 1.1em;
    cursor: pointer;
    line-height: 1;
  }
  .file-chip-remove:hover { color: #dc2626; }

  .attach-btn {
    grid-area: attach;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    padding: 0;
    background: transparent;
    border: none;
    border-radius: 50%;
    color: #94a3b8;
    cursor: pointer;
    transition: all 0.15s;
  }
  .attach-btn:hover:not(:disabled) { background: #e2e8f0; color: #2563eb; }
  .attach-btn:disabled { opacity: 0.4; cursor: not-allowed; }

  .message-files {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    margin-bottom: 6px;
  }

  .message-file-chip {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 3px 8px;
    background: rgba(255,255,255,0.15);
    border-radius: 6px;
    font-size: 0.78em;
  }

  .message-file-chip img {
    width: 24px;
    height: 24px;
    object-fit: cover;
    border-radius: 3px;
  }

  textarea {
    grid-area: textarea;
    padding: 6px 12px;
    border: none;
    font-family: inherit;
    font-size: 0.9em;
    line-height: 1.4;
    resize: none;
    outline: none;
    background: transparent;
    max-height: 150px;
    overflow-y: auto;
  }

  textarea:disabled { opacity: 0.5; }

  .send-btn {
    grid-area: send;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    padding: 0;
    background: #2563eb;
    color: white;
    border: none;
    border-radius: 50%;
    cursor: pointer;
    transition: all 0.15s;
  }
  .send-btn:hover:not(:disabled) { background: #1d4ed8; }
  .send-btn:disabled { opacity: 0.3; cursor: not-allowed; }

  .cursor {
    animation: blink 0.6s step-end infinite;
    color: #2563eb;
    font-weight: bold;
  }
  @keyframes blink { 50% { opacity: 0; } }

  .stop-btn {
    grid-area: send;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    padding: 0;
    background: #dc2626;
    color: white;
    border: none;
    border-radius: 50%;
    cursor: pointer;
    transition: all 0.15s;
  }
  .stop-btn:hover { background: #b91c1c; }
</style>

const API_BASE = "";

export async function createSession(appName = "app") {
  const res = await fetch(`${API_BASE}/apps/${appName}/users/user/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  if (!res.ok) throw new Error(`Failed to create session: ${res.status}`);
  return res.json();
}

export async function sendMessage(appName, userId, sessionId, message, files = []) {
  const parts = [{ text: message }];
  for (const f of files) {
    parts.push({ inlineData: { mimeType: f.mime, data: f.base64 } });
  }
  const res = await fetch(`${API_BASE}/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      app_name: appName,
      user_id: userId,
      session_id: sessionId,
      new_message: { role: "user", parts },
      streaming: false,
    }),
  });
  if (!res.ok) throw new Error(`Failed to send message: ${res.status}`);
  return res.json();
}

export async function sendMessageStream(appName, userId, sessionId, message, files = [], { onChunk, onThinking, onError, onComplete, signal }) {
  const parts = [{ text: message }];
  for (const f of files) {
    parts.push({ inlineData: { mimeType: f.mime, data: f.base64 } });
  }
  const res = await fetch(`${API_BASE}/run_sse`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      app_name: appName,
      user_id: userId,
      session_id: sessionId,
      new_message: { role: "user", parts },
      streaming: true,
    }),
    signal,
  });
  if (!res.ok) {
    throw new Error(`Stream failed: ${res.status}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buf += decoder.decode(value, { stream: true });
      const lines = buf.split("\n\n");
      buf = lines.pop();

      for (const block of lines) {
        const line = block.trim();
        if (!line.startsWith("data: ")) continue;
        try {
          const event = JSON.parse(line.slice(6));
          if (event.error) { onError?.(event.error); continue; }
          if (!event.partial) continue;
          const parts = event?.content?.parts;
          if (!parts) continue;
          for (const p of parts) {
            if (!p.text || p.functionCall) continue;
            if (p.thought) { onThinking?.(p.text); } else { onChunk?.(p.text); }
          }
        } catch {}
      }
    }
  } finally {
    reader.releaseLock();
    onComplete?.();
  }
}

export async function checkBackendHealth() {
  try {
    const res = await fetch(`${API_BASE}/list-apps`, { signal: AbortSignal.timeout(3000) });
    return res.ok;
  } catch {
    return false;
  }
}

export async function listApps() {
  const res = await fetch(`${API_BASE}/list-apps`);
  if (!res.ok) throw new Error(`Failed to list apps: ${res.status}`);
  return res.json();
}

export async function listSessions(appName = "app", userId = "user") {
  const res = await fetch(`${API_BASE}/apps/${appName}/users/${userId}/sessions`);
  if (!res.ok) throw new Error(`Failed to list sessions: ${res.status}`);
  return res.json();
}

export async function deleteSession(appName = "app", userId = "user", sessionId) {
  const res = await fetch(`${API_BASE}/apps/${appName}/users/${userId}/sessions/${sessionId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(`Failed to delete session: ${res.status}`);
}

export async function getSession(appName = "app", userId = "user", sessionId) {
  const res = await fetch(`${API_BASE}/apps/${appName}/users/${userId}/sessions/${sessionId}`);
  if (!res.ok) throw new Error(`Failed to get session: ${res.status}`);
  return res.json();
}

export async function truncateSession(appName = "app", userId = "user", sessionId, keepEventCount) {
  const session = await getSession(appName, userId, sessionId);
  const events = (session.events || []).slice(0, keepEventCount);
  await deleteSession(appName, userId, sessionId);
  const res = await fetch(`${API_BASE}/apps/${appName}/users/${userId}/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, state: session.state || {}, events }),
  });
  if (!res.ok) throw new Error(`Failed to recreate session: ${res.status}`);
  return res.json();
}

export async function fetchRegistry() {
  const res = await fetch(`${API_BASE}/api/registry`);
  if (!res.ok) return { tools: [] };
  return res.json();
}

export async function searchRegistry(query) {
  const res = await fetch(`${API_BASE}/api/registry/search?q=${encodeURIComponent(query)}`);
  if (!res.ok) return { tools: [] };
  return res.json();
}

export async function fetchModels() {
  const res = await fetch(`${API_BASE}/api/models`);
  if (!res.ok) return { models: [] };
  return res.json();
}

export async function fetchCurrentModel() {
  const res = await fetch(`${API_BASE}/api/models/current`);
  if (!res.ok) return { model: "" };
  return res.json();
}

export async function switchModel(modelName) {
  const res = await fetch(`${API_BASE}/api/models/switch`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model: modelName }),
  });
  if (!res.ok) throw new Error(`Failed to switch model: ${res.status}`);
  return res.json();
}

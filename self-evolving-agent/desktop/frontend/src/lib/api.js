const API_BASE = "http://127.0.0.1:8001";

export async function createSession(appName = "app") {
  const res = await fetch(`${API_BASE}/apps/${appName}/users/user/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  if (!res.ok) throw new Error(`Failed to create session: ${res.status}`);
  return res.json();
}

export async function sendMessage(appName, userId, sessionId, message) {
  const res = await fetch(
    `${API_BASE}/apps/${appName}/users/${userId}/sessions/${sessionId}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        app_name: appName,
        user_id: userId,
        session_id: sessionId,
        new_message: { role: "user", parts: [{ text: message }] },
        streaming: false,
      }),
    }
  );
  if (!res.ok) throw new Error(`Failed to send message: ${res.status}`);
  return res.json();
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

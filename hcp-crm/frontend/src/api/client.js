const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json();
}

export function sendChatMessage({ sessionId, message, currentForm, currentInteractionId }) {
  return request("/api/chat", {
    method: "POST",
    body: JSON.stringify({
      session_id: sessionId,
      message,
      current_form: currentForm,
      current_interaction_id: currentInteractionId,
    }),
  });
}

export function fetchInteractions(params = {}) {
  const qs = new URLSearchParams(params).toString();
  return request(`/api/interactions${qs ? `?${qs}` : ""}`);
}

export function fetchInteraction(id) {
  return request(`/api/interactions/${id}`);
}

export function updateInteraction(id, payload) {
  return request(`/api/interactions/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function searchHcps(q) {
  return request(`/api/hcps${q ? `?q=${encodeURIComponent(q)}` : ""}`);
}

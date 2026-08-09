// One small helper for talking to the FastAPI backend.
// Components just say api.list("notes") instead of writing fetch code everywhere.

const BASE_URL = "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const response = await fetch(BASE_URL + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) throw new Error(`Request failed: ${path}`);
  return response.json();
}

// Drop empty filters so we never send things like ?mood_id=undefined
function toQuery(params) {
  const filled = Object.entries(params).filter(([, value]) => value !== "" && value != null);
  return filled.length ? "?" + new URLSearchParams(filled) : "";
}

export const api = {
  list: (kind, params = {}) => request(`/${kind}${toQuery(params)}`),

  create: (kind, body) => request(`/${kind}`, { method: "POST", body: JSON.stringify(body) }),

  update: (kind, id, body) => request(`/${kind}/${id}`, { method: "PUT", body: JSON.stringify(body) }),

  remove: (kind, id) => request(`/${kind}/${id}`, { method: "DELETE" }),

  chat: (message, history) =>
    request("/chat", { method: "POST", body: JSON.stringify({ message, history }) }),

  explain: (trace) => request("/explain", { method: "POST", body: JSON.stringify({ trace }) }),
};

/* ============================================================
   api.js — the ONLY place that calls fetch() against the Python backend.
   No SQL, no direct DB access here — just HTTP calls to /api/*.
   ============================================================ */

/* The Python server serves this frontend and the API from the same address,
   so the API lives at /api. To point at a different server, define
   window.API_BASE_OVERRIDE = 'http://host:port/api' before this file loads. */
const API_BASE = (window.API_BASE_OVERRIDE || '/api').replace(/\/+$/, '');

async function apiRequest(path, { method = 'GET', body = null, query = null } = {}) {
  let url = API_BASE + path;
  if (query) {
    const qs = new URLSearchParams(Object.entries(query).filter(([, v]) => v !== null && v !== undefined && v !== ''));
    const s = qs.toString();
    if (s) url += '?' + s;
  }

  const opts = {
    method,
    credentials: 'include', // send the session cookie
    headers: {},
  };
  if (body !== null) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  }

  let res, json;
  try {
    res = await fetch(url, opts);
  } catch (err) {
    throw { message: 'Network error — is the Librix server running? (python app.py)', errors: null, status: 0 };
  }

  try {
    json = await res.json();
  } catch (err) {
    throw { message: 'Invalid server response.', errors: null, status: res.status };
  }

  if (res.status === 401 && !path.startsWith('/auth')) {
    // Session expired / not logged in — bounce to login.
    window.location.href = 'login.html';
    return;
  }

  if (!json.success) {
    throw { message: json.message || json.error || 'Request failed.', errors: json.errors || null, status: res.status };
  }
  return json.data;
}

const Api = {
  get: (path, query) => apiRequest(path, { method: 'GET', query }),
  post: (path, body) => apiRequest(path, { method: 'POST', body: body || {} }),
  put: (path, body) => apiRequest(path, { method: 'PUT', body: body || {} }),
  del: (path) => apiRequest(path, { method: 'DELETE' }),
};

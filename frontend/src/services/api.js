/*
 * Central client for all backend requests.
 * It uses the deployment-time API URL and automatically attaches the JWT after login.
 */
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

let token = localStorage.getItem('cropkeepai_token') || '';

export function setToken(nextToken) {
  // localStorage keeps the session across page refreshes in the same browser.
  token = nextToken || '';
  if (token) localStorage.setItem('cropkeepai_token', token);
  else localStorage.removeItem('cropkeepai_token');
}

export function getAssetUrl(path) {
  if (!path) return '';
  return path.startsWith('http') ? path : `${API_BASE_URL}${path}`;
}

async function request(path, options = {}) {
  // Add the Bearer token only when a user is logged in.
  const headers = options.headers || {};
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || 'Request failed');
  }
  return data;
}

export const api = {
  login: (payload) =>
    request('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),
  me: () => request('/api/auth/me'),
  users: () => request('/api/auth/users'),
  createUser: (payload) =>
    request('/api/auth/users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),
  updateUser: (id, payload) =>
    request(`/api/auth/users/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),
  resetUserPassword: (id, password) =>
    request(`/api/auth/users/${id}/reset-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password }),
    }),
  deleteUser: (id) => request(`/api/auth/users/${id}`, { method: 'DELETE' }),
  diagnose: (file) => {
    // FormData sends the image as multipart data, matching FastAPI's UploadFile input.
    const form = new FormData();
    form.append('image', file);
    return request('/api/diagnoses', { method: 'POST', body: form });
  },
  listDiagnoses: () => request('/api/diagnoses'),
  getDiagnosis: (id) => request(`/api/diagnoses/${id}`),
  chat: (diagnosisId, message) =>
    request('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ diagnosis_id: diagnosisId, message }),
    }),
  products: () => request('/api/catalog/products'),
  diseases: () => request('/api/catalog/diseases'),
  knowledge: () => request('/api/catalog/knowledge'),
};

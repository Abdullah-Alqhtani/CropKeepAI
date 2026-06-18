import { useState } from 'react';
import { Leaf, LogIn, Moon, Sun, UserPlus } from 'lucide-react';
import { api } from '../services/api.js';

export function AuthPage({ onAuth, theme, setTheme }) {
  const [mode, setMode] = useState('login');
  const [form, setForm] = useState({
    name: '',
    email: 'farmer@cropkeepai.local',
    password: 'password123',
    role: 'farmer',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setError('');
    setLoading(true);
    try {
      const payload =
        mode === 'login'
          ? { email: form.email, password: form.password }
          : { name: form.name, email: form.email, password: form.password, role: form.role };
      const auth = mode === 'login' ? await api.login(payload) : await api.register(payload);
      onAuth(auth);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth-layout">
      <button
        className="icon-button auth-theme"
        onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
        title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
        type="button"
      >
        {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
      </button>
      <section className="auth-panel">
        <div className="auth-heading">
          <Leaf size={38} />
          <div>
            <h1>CropKeepAI</h1>
            <p>Diagnose crop disease, retrieve treatment knowledge, and recommend crop protection products.</p>
          </div>
        </div>
        <div className="mode-switch" role="tablist">
          <button className={mode === 'login' ? 'active' : ''} onClick={() => setMode('login')} type="button">
            <LogIn size={16} /> Login
          </button>
          <button className={mode === 'register' ? 'active' : ''} onClick={() => setMode('register')} type="button">
            <UserPlus size={16} /> Register
          </button>
        </div>
        <form onSubmit={submit} className="form-grid">
          {mode === 'register' && (
            <label>
              Name
              <input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} required />
            </label>
          )}
          <label>
            Email
            <input
              type="email"
              value={form.email}
              onChange={(event) => setForm({ ...form, email: event.target.value })}
              required
            />
          </label>
          <label>
            Password
            <input
              type="password"
              value={form.password}
              onChange={(event) => setForm({ ...form, password: event.target.value })}
              required
            />
          </label>
          {mode === 'register' && (
            <label>
              Role
              <select value={form.role} onChange={(event) => setForm({ ...form, role: event.target.value })}>
                <option value="farmer">Farmer</option>
                <option value="expert">Expert</option>
                <option value="admin">Admin</option>
              </select>
            </label>
          )}
          {error && <div className="error-text">{error}</div>}
          <button className="primary-button" disabled={loading}>
            {loading ? 'Working...' : mode === 'login' ? 'Login' : 'Create account'}
          </button>
        </form>
      </section>
    </main>
  );
}

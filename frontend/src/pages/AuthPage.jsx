import { useState } from 'react';
import { Leaf, LogIn, Moon, Sun } from 'lucide-react';
import { api } from '../services/api.js';

export function AuthPage({ onAuth, theme, setTheme }) {
  const [form, setForm] = useState({
    email: 'admin@cropkeepai.local',
    password: 'password123',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setError('');
    setLoading(true);
    try {
      const auth = await api.login({ email: form.email, password: form.password });
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
        <form onSubmit={submit} className="form-grid">
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
          {error && <div className="error-text">{error}</div>}
          <button className="primary-button" disabled={loading}>
            <LogIn size={16} />
            {loading ? 'Working...' : 'Login'}
          </button>
        </form>
      </section>
    </main>
  );
}

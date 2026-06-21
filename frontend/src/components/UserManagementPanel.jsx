import { useEffect, useState } from 'react';
import { KeyRound, Power, PowerOff, Trash2, UserCog, UserPlus } from 'lucide-react';
import { api } from '../services/api.js';

const roles = ['farmer', 'expert', 'admin'];

export function UserManagementPanel({ currentUser }) {
  const [users, setUsers] = useState([]);
  const [form, setForm] = useState({ name: '', email: '', password: '', role: 'farmer' });
  const [resetPasswords, setResetPasswords] = useState({});
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [loading, setLoading] = useState(false);

  async function loadUsers() {
    const records = await api.users();
    setUsers(records);
  }

  useEffect(() => {
    loadUsers().catch((err) => setError(err.message));
  }, []);

  async function createUser(event) {
    event.preventDefault();
    setError('');
    setNotice('');
    setLoading(true);
    try {
      await api.createUser(form);
      setForm({ name: '', email: '', password: '', role: 'farmer' });
      setNotice('User created.');
      await loadUsers();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function updateUser(id, payload) {
    setError('');
    setNotice('');
    try {
      await api.updateUser(id, payload);
      setNotice('User updated.');
      await loadUsers();
    } catch (err) {
      setError(err.message);
    }
  }

  async function resetPassword(id) {
    const password = resetPasswords[id] || '';
    if (password.length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }
    setError('');
    setNotice('');
    try {
      await api.resetUserPassword(id, password);
      setResetPasswords({ ...resetPasswords, [id]: '' });
      setNotice('Password reset.');
    } catch (err) {
      setError(err.message);
    }
  }

  async function deleteUser(id) {
    setError('');
    setNotice('');
    try {
      await api.deleteUser(id);
      setNotice('User deleted.');
      await loadUsers();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section className="panel admin-panel">
      <div className="panel-title">
        <UserCog size={20} />
        <h2>User Management</h2>
      </div>

      <form className="admin-create-grid" onSubmit={createUser}>
        <label>
          Name
          <input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} required />
        </label>
        <label>
          Email
          <input type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} required />
        </label>
        <label>
          Password
          <input
            type="password"
            value={form.password}
            minLength={8}
            onChange={(event) => setForm({ ...form, password: event.target.value })}
            required
          />
        </label>
        <label>
          Role
          <select value={form.role} onChange={(event) => setForm({ ...form, role: event.target.value })}>
            {roles.map((role) => (
              <option key={role} value={role}>{role}</option>
            ))}
          </select>
        </label>
        <button className="primary-button" disabled={loading}>
          <UserPlus size={16} />
          Create
        </button>
      </form>

      {error && <div className="error-text">{error}</div>}
      {notice && <div className="success-text">{notice}</div>}

      <div className="user-list">
        {users.map((user) => {
          const isSelf = user.id === currentUser.id;
          return (
            <article className="user-row" key={user.id}>
              <div>
                <strong>{user.name}</strong>
                <span>{user.email}</span>
                <small>{user.is_active ? 'Active' : 'Disabled'}</small>
              </div>
              <select value={user.role} disabled={isSelf} onChange={(event) => updateUser(user.id, { role: event.target.value })}>
                {roles.map((role) => (
                  <option key={role} value={role}>{role}</option>
                ))}
              </select>
              <div className="password-reset">
                <input
                  type="password"
                  placeholder="New password"
                  minLength={8}
                  value={resetPasswords[user.id] || ''}
                  onChange={(event) => setResetPasswords({ ...resetPasswords, [user.id]: event.target.value })}
                />
                <button className="icon-button" type="button" title="Reset password" aria-label="Reset password" onClick={() => resetPassword(user.id)}>
                  <KeyRound size={16} />
                </button>
              </div>
              <div className="row-actions">
                <button
                  className="icon-button"
                  type="button"
                  disabled={isSelf}
                  title={user.is_active ? 'Disable user' : 'Enable user'}
                  aria-label={user.is_active ? 'Disable user' : 'Enable user'}
                  onClick={() => updateUser(user.id, { is_active: !user.is_active })}
                >
                  {user.is_active ? <PowerOff size={16} /> : <Power size={16} />}
                </button>
                <button
                  className="icon-button danger-button"
                  type="button"
                  disabled={isSelf}
                  title="Delete user"
                  aria-label="Delete user"
                  onClick={() => deleteUser(user.id)}
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}

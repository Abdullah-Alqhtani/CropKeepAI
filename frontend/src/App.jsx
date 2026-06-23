/*
 * Top-level React component for login state, theme, and the application shell.
 * It checks an existing JWT on startup and chooses either the login page or dashboard.
 */
import { useEffect, useState } from 'react';
import { Leaf, LogOut, Menu, Moon, Sprout, Sun, X } from 'lucide-react';
import { api, setToken } from './services/api.js';
import { AuthPage } from './pages/AuthPage.jsx';
import { DashboardPage } from './pages/DashboardPage.jsx';

export function App() {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(true);
  const [theme, setTheme] = useState(() => localStorage.getItem('cropkeepai_theme') || 'dark');
  const [menuOpen, setMenuOpen] = useState(false);

  // Save the selected theme so the same appearance is used after a browser refresh.
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem('cropkeepai_theme', theme);
  }, [theme]);

  // Validate a stored token before showing protected parts of the application.
  useEffect(() => {
    api
      .me()
      .then(setUser)
      .catch(() => setToken(''))
      .finally(() => setChecking(false));
  }, []);

  function handleAuth(auth) {
    // Save the JWT in the API service, then switch from login view to dashboard.
    setToken(auth.access_token);
    setUser(auth.user);
  }

  function logout() {
    // Removing the token makes future API calls unauthenticated.
    setToken('');
    setUser(null);
  }

  if (checking) {
    return (
      <main className="loading-screen">
        <Leaf size={34} />
        <span>CropKeepAI</span>
      </main>
    );
  }

  if (!user) return <AuthPage onAuth={handleAuth} theme={theme} setTheme={setTheme} />;

  return (
    <div className="app-shell">
      <header className="topbar">
        <button className="icon-button menu-button" onClick={() => setMenuOpen(true)} title="Open menu" aria-label="Open menu">
          <Menu size={20} />
        </button>
        <div className="brand">
          <Sprout size={28} />
          <div>
            <strong>CropKeepAI</strong>
            <span>Crop protection intelligence</span>
          </div>
        </div>
        <div className="account">
          <button
            className="icon-button"
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
          </button>
          <span>{user.name}</span>
          <small>{user.role}</small>
          <button className="icon-button" onClick={logout} title="Sign out" aria-label="Sign out">
            <LogOut size={18} />
          </button>
        </div>
      </header>
      {menuOpen && <button className="menu-backdrop" aria-label="Close menu" onClick={() => setMenuOpen(false)} />}
      <DashboardPage
        user={user}
        menuOpen={menuOpen}
        onCloseMenu={() => setMenuOpen(false)}
        menuCloseIcon={<X size={20} />}
      />
    </div>
  );
}

import { useEffect, useState } from 'react';
import { BookOpen, Database, History, ImageUp, LayoutDashboard, MessageSquare, PackageSearch } from 'lucide-react';
import { api } from '../services/api.js';
import { UploadPanel } from '../components/UploadPanel.jsx';
import { ResultPanel } from '../components/ResultPanel.jsx';
import { ChatPanel } from '../components/ChatPanel.jsx';
import { CatalogPanel } from '../components/CatalogPanel.jsx';
import { HistoryPanel } from '../components/HistoryPanel.jsx';

export function DashboardPage({ user, menuOpen, onCloseMenu, menuCloseIcon }) {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [diagnosis, setDiagnosis] = useState(null);
  const [history, setHistory] = useState([]);

  async function refreshHistory() {
    const records = await api.listDiagnoses();
    setHistory(records);
  }

  useEffect(() => {
    refreshHistory().catch(() => setHistory([]));
  }, []);

  async function handleDiagnosis(result) {
    setDiagnosis(result);
    await refreshHistory();
  }

  async function loadDiagnosis(id) {
    const result = await api.getDiagnosis(id);
    setDiagnosis(result);
    setActiveTab('diagnose');
  }

  const canReviewKnowledge = user.role === 'admin' || user.role === 'expert';
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: <LayoutDashboard size={18} /> },
    { id: 'diagnose', label: 'Diagnosis', icon: <ImageUp size={18} /> },
    { id: 'chat', label: 'Chat', icon: <MessageSquare size={18} /> },
    { id: 'history', label: 'History', icon: <History size={18} /> },
    { id: 'products', label: 'Catalog', icon: <PackageSearch size={18} /> },
  ];
  if (canReviewKnowledge) {
    navItems.push({ id: 'knowledge', label: 'Knowledge', icon: <Database size={18} /> });
  }

  function chooseTab(id) {
    setActiveTab(id);
    onCloseMenu();
  }

  return (
    <>
      <aside className={`side-menu ${menuOpen ? 'open' : ''}`} aria-label="Main menu">
        <div className="side-menu-head">
          <div>
            <strong>CropKeepAI</strong>
            <span>Workspace</span>
          </div>
          <button className="icon-button" onClick={onCloseMenu} title="Close menu" aria-label="Close menu">
            {menuCloseIcon}
          </button>
        </div>
        <nav className="side-nav">
          {navItems.map((item) => (
            <button key={item.id} className={activeTab === item.id ? 'active' : ''} onClick={() => chooseTab(item.id)}>
              {item.icon}
              {item.label}
            </button>
          ))}
        </nav>
      </aside>

      <main className="workspace">
      {activeTab === 'dashboard' && (
        <section className="dashboard-overview">
          <div className="page-heading">
            <span className="eyebrow">Dashboard</span>
            <h1>CropKeepAI Control Center</h1>
            <p>Upload plant images, review diagnosis history, chat with the assistant, and browse product recommendations.</p>
          </div>
          <div className="stat-grid">
            <button className="stat-card" onClick={() => setActiveTab('diagnose')}>
              <ImageUp size={22} />
              <strong>Start Diagnosis</strong>
              <span>Analyze a new crop image</span>
            </button>
            <button className="stat-card" onClick={() => setActiveTab('history')}>
              <History size={22} />
              <strong>{history.length} Records</strong>
              <span>Review previous diagnoses</span>
            </button>
            <button className="stat-card" onClick={() => setActiveTab('products')}>
              <BookOpen size={22} />
              <strong>Catalog</strong>
              <span>Explore crop protection products</span>
            </button>
          </div>
        </section>
      )}
      {activeTab === 'diagnose' && (
        <div className="diagnosis-grid">
          <UploadPanel onDiagnosis={handleDiagnosis} />
          {diagnosis && <ResultPanel diagnosis={diagnosis} />}
          {diagnosis && <ChatPanel diagnosisId={diagnosis.id} />}
        </div>
      )}

      {activeTab === 'chat' && (
        diagnosis ? (
          <ChatPanel diagnosisId={diagnosis.id} />
        ) : (
          <section className="panel empty-state">
            <MessageSquare size={28} />
            <h2>No active diagnosis</h2>
            <p>Run a diagnosis first, then return here to ask follow-up questions in context.</p>
            <button className="primary-button" onClick={() => setActiveTab('diagnose')}>Start diagnosis</button>
          </section>
        )
      )}
      {activeTab === 'history' && <HistoryPanel history={history} onSelect={loadDiagnosis} />}
      {activeTab === 'products' && <CatalogPanel type="products" />}
      {activeTab === 'knowledge' && canReviewKnowledge && <CatalogPanel type="knowledge" />}
    </main>
    </>
  );
}

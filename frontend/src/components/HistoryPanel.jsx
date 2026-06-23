/*
 * Show the current user's saved diagnosis history.
 * Selecting a row asks DashboardPage to load the full result from the backend.
 */
import { CalendarClock } from 'lucide-react';
import { getAssetUrl } from '../services/api.js';

export function HistoryPanel({ history, onSelect }) {
  return (
    <section className="panel wide-panel">
      <div className="panel-title">
        <CalendarClock size={20} />
        <h2>Diagnosis History</h2>
      </div>
      <div className="history-list">
        {history.length === 0 && <p className="muted">No diagnosis history yet.</p>}
        {history.map((item) => (
          // The parent owns navigation, so this component only reports the selected ID.
          <button className="history-row" key={item.id} onClick={() => onSelect(item.id)}>
            <img src={getAssetUrl(item.image_url)} alt="" />
            <span>
              <strong>{item.disease_name}</strong>
              <small>{item.crop_type} · {new Date(item.created_at).toLocaleString()}</small>
            </span>
            <em>{item.confidence}</em>
          </button>
        ))}
      </div>
    </section>
  );
}

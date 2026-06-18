import { useMemo, useState } from 'react';
import { ImageUp, Send, X } from 'lucide-react';
import { api } from '../services/api.js';

export function UploadPanel({ onDiagnosis }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const previewUrl = useMemo(() => (file ? URL.createObjectURL(file) : ''), [file]);

  async function submit(event) {
    event.preventDefault();
    if (!file) return;
    setError('');
    setLoading(true);
    try {
      const result = await api.diagnose(file);
      onDiagnosis(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel upload-panel">
      <div className="panel-title">
        <ImageUp size={20} />
        <h2>Image Upload</h2>
      </div>
      <form onSubmit={submit}>
        <label className="drop-zone">
          {previewUrl ? (
            <img src={previewUrl} alt="Crop preview" />
          ) : (
            <span>
              <ImageUp size={28} />
              JPG or PNG crop image
            </span>
          )}
          <input
            type="file"
            accept="image/jpeg,image/png"
            onChange={(event) => setFile(event.target.files?.[0] || null)}
          />
        </label>
        {file && (
          <div className="file-row">
            <span>{file.name}</span>
            <button className="icon-button" type="button" onClick={() => setFile(null)} title="Clear image">
              <X size={16} />
            </button>
          </div>
        )}
        {error && <div className="error-text">{error}</div>}
        <button className="primary-button" disabled={!file || loading}>
          <Send size={16} />
          {loading ? 'Diagnosing...' : 'Submit diagnosis'}
        </button>
      </form>
    </section>
  );
}

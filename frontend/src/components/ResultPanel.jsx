import { AlertTriangle, FlaskConical, Leaf, ShieldCheck } from 'lucide-react';
import { getAssetUrl } from '../services/api.js';

export function ResultPanel({ diagnosis }) {
  return (
    <section className="panel result-panel">
      <div className="result-header">
        <img src={getAssetUrl(diagnosis.image_url)} alt="Uploaded crop" />
        <div>
          <span className="eyebrow">Diagnosis</span>
          <h2>{diagnosis.disease_name}</h2>
          <p>{diagnosis.crop_type}</p>
          <div className="meta-row">
            <span>{diagnosis.confidence} confidence</span>
            <span>{diagnosis.severity} severity</span>
          </div>
        </div>
      </div>

      <div className="info-grid">
        <InfoBlock icon={<Leaf size={18} />} title="Description" text={diagnosis.description} />
        <InfoBlock icon={<AlertTriangle size={18} />} title="Causes" text={diagnosis.causes} />
        <InfoBlock icon={<ShieldCheck size={18} />} title="Symptoms & Impact" text={`${diagnosis.symptoms}\n${diagnosis.impact}`} />
        <InfoBlock icon={<FlaskConical size={18} />} title="Treatment" text={diagnosis.treatment_steps} />
        <InfoBlock icon={<ShieldCheck size={18} />} title="Prevention" text={diagnosis.preventive_actions} />
        <InfoBlock icon={<Leaf size={18} />} title="Environment" text={diagnosis.environmental_considerations} />
      </div>

      <div className="recommendations">
        <h3>Product Suggestions</h3>
        <div className="product-list">
          {diagnosis.recommendations.length > 0 ? (
            diagnosis.recommendations.map((item) => (
              <article className="product-item" key={item.id}>
                <strong>{item.product.name}</strong>
                <span>{item.product.active_ingredient}</span>
                <p>{item.reason}</p>
                <small>{item.product.safety_notes}</small>
              </article>
            ))
          ) : (
            <p className="empty-note">No specific product recommendation found for this diagnosis.</p>
          )}
        </div>
      </div>
    </section>
  );
}

function InfoBlock({ icon, title, text }) {
  return (
    <article className="info-block">
      <div>
        {icon}
        <strong>{title}</strong>
      </div>
      <p>{text || 'Not available.'}</p>
    </article>
  );
}

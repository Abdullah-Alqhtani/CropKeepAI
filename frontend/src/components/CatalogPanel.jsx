import { useEffect, useState } from 'react';
import { Database, PackageSearch } from 'lucide-react';
import { api } from '../services/api.js';

export function CatalogPanel({ type }) {
  const [items, setItems] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    const loader = type === 'products' ? api.products : api.knowledge;
    loader()
      .then(setItems)
      .catch((err) => setError(err.message));
  }, [type]);

  return (
    <section className="panel wide-panel">
      <div className="panel-title">
        {type === 'products' ? <PackageSearch size={20} /> : <Database size={20} />}
        <h2>{type === 'products' ? 'Product Database' : 'Knowledge Base'}</h2>
      </div>
      {error && <div className="error-text">{error}</div>}
      <div className="catalog-list">
        {items.map((item) =>
          type === 'products' ? (
            <article className="catalog-row" key={item.id}>
              <strong>{item.name}</strong>
              <span>{item.english_name || item.active_ingredient}</span>
              <small>{[item.product_code, item.product_type, item.specification].filter(Boolean).join(' · ')}</small>
              {item.crops && <p><b>Crops:</b> {item.crops}</p>}
              <p><b>Ingredient:</b> {item.active_ingredient}</p>
              <p>{item.usage_instructions}</p>
              <small>{item.safety_notes}</small>
            </article>
          ) : (
            <article className="catalog-row" key={item.id}>
              <strong>{item.title}</strong>
              <span>{item.disease}</span>
              <p>{item.content}</p>
              <small>{item.tags}</small>
            </article>
          ),
        )}
      </div>
    </section>
  );
}

import { useState } from 'react';

export default function DvarTorah({ data }) {
  const [open, setOpen] = useState(false);

  if (!data.dvar_torah) return null;

  return (
    <div className="dvar-torah-container area-dt">
      <button className="dt-btn" onClick={() => setOpen(!open)}>
        <span>📚 דבר תורה לשבת</span>
        <span>{open ? '▲' : '▼'}</span>
      </button>
      {open && (
        <div className="dt-content" style={{ display: 'block' }}>
          <div>{data.dvar_torah}</div>
          {data.dvar_source && (
            <div style={{ marginTop: 10, fontWeight: 'bold', color: '#666', fontSize: '0.9rem' }}>
              {data.dvar_source}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

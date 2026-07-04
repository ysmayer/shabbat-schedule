import { useState } from 'react';

export default function DvarTorah({ data }) {
  const [open, setOpen] = useState(false);

  if (!data.dvar_torah) return null;

  return (
    <div className="dvar-torah-container">
      <button className="dt-btn" onClick={() => setOpen(!open)} aria-expanded={open}>
        <span>📚 דבר תורה לשבת</span>
        <span className={open ? 'dt-arrow open' : 'dt-arrow'}>▼</span>
      </button>
      {open && (
        <div className="dt-content">
          <div>{data.dvar_torah}</div>
          {data.dvar_source && <div className="dt-source">{data.dvar_source}</div>}
        </div>
      )}
    </div>
  );
}

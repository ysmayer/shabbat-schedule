export default function Header({ data }) {
  return (
    <div className="header-card area-header">
      <div className="header-row">
        <div className="bsd">בס"ד</div>
        <div className="logo-area">
          <img
            src="logo.jpg"
            alt="Logo"
            className="logo-img"
            onError={(e) => { e.target.style.display = 'none'; }}
          />
        </div>
      </div>
      <div className="main-title">
        שבת קודש פרשת {data.parsha || 'השבוע'}
      </div>
      {data.description && (
        <div className="sub-title">{data.description}</div>
      )}
      {data.description && data.molad && (
        <div className="molad-text" style={{ display: 'block' }}>
          {data.molad}
        </div>
      )}
    </div>
  );
}

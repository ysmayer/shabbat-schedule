export default function Header({ data }) {
  return (
    <header className="hero">
      <div className="hero-top">
        <span className="bsd">בס"ד</span>
        <img
          src="logo.jpg"
          alt="Logo"
          className="logo-img"
          onError={(e) => { e.target.style.display = 'none'; }}
        />
      </div>

      <div className="hero-body">
        <h1 className="main-title">שבת קודש פרשת {data.parsha || 'השבוע'}</h1>
        <div className="hero-ornament" aria-hidden="true">✦</div>
        {data.description && <div className="sub-title">{data.description}</div>}
        {data.description && data.molad && (
          <div className="molad-text">{data.molad}</div>
        )}
        <div className="key-times">
          <span className="key-chip"><span className="anim-candle" aria-hidden="true">🕯️</span> הדלקת נרות <b className="key-time">{data.candles}</b></span>
          <span className="key-chip"><span className="anim-stars" aria-hidden="true">✨</span> צאת השבת <b className="key-time">{data.havdalah}</b></span>
        </div>
      </div>
    </header>
  );
}

export default function Header({ data }) {
  const imgSrc = data.image || 'kotel.jpg';
  const fallback = 'https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Jerusalem_Symbol.svg/600px-Jerusalem_Symbol.svg.png';

  return (
    <header className="hero">
      <div className="hero-media">
        <img
          src={imgSrc}
          alt="Shul Image"
          className="hero-img"
          onError={(e) => { e.target.src = fallback; }}
        />
        <div className="hero-overlay" />
      </div>

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
        {data.description && <div className="sub-title">{data.description}</div>}
        {data.description && data.molad && (
          <div className="molad-text">{data.molad}</div>
        )}
        <div className="key-times">
          <span className="key-chip">🕯️ הדלקת נרות <b className="key-time">{data.candles}</b></span>
          <span className="key-chip">✨ צאת השבת <b className="key-time">{data.havdalah}</b></span>
        </div>
      </div>
    </header>
  );
}

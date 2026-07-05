import { calculateMincha, calculateMinchaShabbat, calculateOrot, calculateArvit } from '../utils/timeCalc';

function Item({ time, label, icon, iconAnim, highlight }) {
  return (
    <div className={highlight ? 'tl-item highlight' : 'tl-item'}>
      <span className="time">{time}</span>
      {icon && <span className={`tl-icon ${iconAnim || ''}`} aria-hidden="true">{icon}</span>}
      <span className="desc">{label}</span>
    </div>
  );
}

export default function Timeline({ data }) {
  const isSummer = data.is_summer === true;
  const minchaErev = calculateMincha(data.candles);
  const minchaShabbat = calculateMinchaShabbat(data);
  const orot = calculateOrot(minchaShabbat);
  const arvit = calculateArvit(data.havdalah);

  const infoText = data.kidush?.trim()
    ? data.kidush
    : data.shiur_topic?.trim()
      ? `שיעור מאת הרב נתנאל ב${data.shiur_topic} לאחר התפילה`
      : null;
  const infoIsBold = !!(data.kidush?.trim());

  return (
    <div className="timeline-card">
      <section className="tl-section">
        <h3 className="section-header">ערב שבת</h3>
        <div className="tl-items">
          <Item time={data.candles} label="הדלקת נרות שבת" icon="🕯️" iconAnim="anim-candle" highlight />
          <Item time={minchaErev} label="מנחה, קבלת שבת וערבית" />
        </div>
      </section>

      <section className="tl-section">
        <h3 className="section-header">שבת קודש</h3>
        <div className="tl-items">
          <Item time={isSummer ? '8:00' : '7:45'} label="שחרית ומוסף" />
          {data.molad && (
            <div className="molad-note">
              <span className="molad-moon" aria-hidden="true">🌒</span>
              <span>{data.molad}</span>
            </div>
          )}
          <Item time={isSummer ? '9:30' : '9:15'} label="תפילת ילדים" />
          {infoText && (
            <div className="note-text" style={{ fontWeight: infoIsBold ? 'bold' : 'normal' }}>
              {infoText}
            </div>
          )}
          <Item time={orot} label='לימוד בספר "אורות"' />
          <Item time={minchaShabbat} label="מנחה של שבת" />
        </div>
      </section>

      <section className="tl-section">
        <h3 className="section-header">מוצאי שבת</h3>
        <div className="tl-items">
          <Item time={arvit} label="ערבית של מוצאי שבת" />
          <Item time={data.havdalah} label="צאת השבת" icon="✨" iconAnim="anim-stars" highlight />
        </div>
      </section>
    </div>
  );
}

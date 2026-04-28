import { calculateMinchaShabbat, calculateOrot, calculateArvit } from '../utils/timeCalc';

export default function ShabbatDayCard({ data }) {
  const isSummer = data.is_summer === true;
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
    <div className="shabbat-day-card area-day-times">
      <div className="section-header" style={{ marginBottom: 20, marginTop: 0 }}>שבת קודש</div>

      <div className="center-row">
        <span className="time">{isSummer ? '8:00' : '7:45'}</span>
        <span className="desc" style={{ flex: 'none' }}>שחרית ומוסף</span>
      </div>

      <div className="center-row">
        <span className="time">{isSummer ? '9:30' : '9:15'}</span>
        <span className="desc" style={{ flex: 'none' }}>תפילת ילדים</span>
      </div>

      {infoText && (
        <div
          className="note-text"
          style={{ display: 'block', fontWeight: infoIsBold ? 'bold' : 'normal' }}
        >
          {infoText}
        </div>
      )}

      <div className="center-row">
        <span className="time">{orot}</span>
        <span className="desc" style={{ flex: 'none' }}>לימוד בספר "אורות"</span>
      </div>

      <div className="center-row">
        <span className="time">{minchaShabbat}</span>
        <span className="desc" style={{ flex: 'none' }}>מנחה של שבת</span>
      </div>

      <div className="center-row">
        <span className="time">{arvit}</span>
        <span className="desc" style={{ flex: 'none' }}>ערבית של מוצאי שבת</span>
      </div>
    </div>
  );
}

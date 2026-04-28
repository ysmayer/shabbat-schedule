import { calculateMincha } from '../utils/timeCalc';

export default function TimesCard({ data }) {
  return (
    <div className="times-card area-top-times">
      <div className="time-row">
        <span className="time">{data.candles}</span>
        <span className="desc">הדלקת נרות שבת</span>
      </div>
      <div className="time-row">
        <span className="time">{data.havdalah}</span>
        <span className="desc">צאת השבת</span>
      </div>

      <div className="section-header">ערב שבת</div>
      <div className="time-row">
        <span className="time">{calculateMincha(data.candles)}</span>
        <span className="desc">מנחה, קבלת שבת וערבית</span>
      </div>
    </div>
  );
}

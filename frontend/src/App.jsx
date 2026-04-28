import { useState, useEffect } from 'react';
import Header from './components/Header';
import MessagesCard from './components/MessagesCard';
import TimesCard from './components/TimesCard';
import ShabbatDayCard from './components/ShabbatDayCard';
import ImagePanel from './components/ImagePanel';
import DvarTorah from './components/DvarTorah';
import PrintButton from './components/PrintButton';

export default function App() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    const timeout = setTimeout(() => {
      if (!data && !error) setError(true);
    }, 4000);

    fetch('data.json?t=' + Date.now())
      .then((r) => {
        if (!r.ok) throw new Error('Data file not found');
        return r.json();
      })
      .then(setData)
      .catch(() => setError(true));

    return () => clearTimeout(timeout);
  }, []);

  if (!data && !error) {
    return <div className="web-container"><div className="loader" /></div>;
  }

  if (error && !data) {
    return (
      <div className="web-container">
        <div className="layout-grid">
          <div className="header-card area-header" style={{ textAlign: 'center' }}>
            <div className="main-title">שגיאה בטעינת נתונים</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="web-container">
      <div className="layout-grid">
        <Header data={data} />
        <TimesCard data={data} />
        <ImagePanel data={data} />
        <ShabbatDayCard data={data} />
        <div className="area-footer">
          <div className="footer-shabbat" style={{ textAlign: 'center', marginTop: 30, fontWeight: 'bold', fontSize: '1.5rem' }}>
            שבת שלום!
          </div>
        </div>
        <MessagesCard messages={data.messages} />
        <DvarTorah data={data} />
        <PrintButton />
      </div>
    </div>
  );
}

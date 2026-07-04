import { useState, useEffect } from 'react';
import Header from './components/Header';
import Countdown from './components/Countdown';
import MessagesCard from './components/MessagesCard';
import Timeline from './components/Timeline';
import DvarTorah from './components/DvarTorah';
import ActionButtons from './components/ActionButtons';

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
        <div className="error-card">
          <div className="main-title">שגיאה בטעינת נתונים</div>
        </div>
      </div>
    );
  }

  return (
    <div className="web-container">
      <Header data={data} />
      <Countdown data={data} />
      <MessagesCard messages={data.messages} />
      <Timeline data={data} />
      <DvarTorah data={data} />
      <ActionButtons />
      <footer className="footer-shabbat">
        <span className="footer-orn">✦</span> שבת שלום! <span className="footer-orn">✦</span>
      </footer>
    </div>
  );
}

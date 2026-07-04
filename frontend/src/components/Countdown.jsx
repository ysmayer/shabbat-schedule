import { useState, useEffect } from 'react';

function atTime(baseDate, timeStr) {
  const d = new Date(baseDate);
  const [h, m] = timeStr.split(':').map(Number);
  d.setHours(h, m, 0, 0);
  return d;
}

// Returns { mode: 'before' | 'during', target: Date }
function getShabbatState(candles, havdalah, now) {
  const day = now.getDay(); // 0=Sunday ... 5=Friday, 6=Saturday
  if (day === 5) {
    const candleTime = atTime(now, candles);
    if (now < candleTime) return { mode: 'before', target: candleTime };
    const nextDay = new Date(now);
    nextDay.setDate(now.getDate() + 1);
    return { mode: 'during', target: atTime(nextDay, havdalah) };
  }
  if (day === 6) {
    const havdalahTime = atTime(now, havdalah);
    if (now < havdalahTime) return { mode: 'during', target: havdalahTime };
    const nextFriday = new Date(now);
    nextFriday.setDate(now.getDate() + 6);
    return { mode: 'before', target: atTime(nextFriday, candles) };
  }
  const friday = new Date(now);
  friday.setDate(now.getDate() + ((5 - day + 7) % 7));
  return { mode: 'before', target: atTime(friday, candles) };
}

function formatRemaining(ms) {
  const totalMinutes = Math.floor(ms / 60000);
  const days = Math.floor(totalMinutes / 1440);
  const hours = Math.floor((totalMinutes % 1440) / 60);
  const minutes = totalMinutes % 60;
  const parts = [];
  if (days > 0) parts.push(days === 1 ? 'יום אחד' : `${days} ימים`);
  if (hours > 0) parts.push(hours === 1 ? 'שעה אחת' : `${hours} שעות`);
  parts.push(minutes === 1 ? 'דקה אחת' : `${minutes} דקות`);
  return parts.join(' · ');
}

export default function Countdown({ data }) {
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 30000);
    return () => clearInterval(id);
  }, []);

  if (!data.candles || !data.havdalah) return null;

  const { mode, target } = getShabbatState(data.candles, data.havdalah, now);
  const remaining = target - now;
  if (remaining <= 0) return null;

  return (
    <div className="countdown-chip">
      {mode === 'during' ? (
        <>
          <span className="cd-label"><span className="anim-candle" aria-hidden="true">🕯️</span> שבת שלום! צאת השבת בעוד</span>
          <span className="cd-value">{formatRemaining(remaining)}</span>
        </>
      ) : (
        <>
          <span className="cd-label"><span className="anim-candle" aria-hidden="true">🕯️</span> שבת נכנסת בעוד</span>
          <span className="cd-value">{formatRemaining(remaining)}</span>
        </>
      )}
    </div>
  );
}

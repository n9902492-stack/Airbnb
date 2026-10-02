import { useEffect, useMemo, useState } from 'react';
import { CalendarDays } from 'lucide-react';
import { bookingApi } from '../lib/api';

function iso(date: Date) {
  return date.toISOString().slice(0, 10);
}

function addDays(date: Date, days: number) {
  const next = new Date(date);
  next.setDate(next.getDate() + days);
  return next;
}

export default function AvailabilityCalendar({
  propertyId,
  onChange,
}: {
  propertyId: number;
  onChange: (value: { checkIn: string; checkOut: string }) => void;
}) {
  const [blocked, setBlocked] = useState<Set<string>>(new Set());
  const [checkIn, setCheckIn] = useState('');
  const [checkOut, setCheckOut] = useState('');
  const [message, setMessage] = useState('');

  const today = useMemo(() => {
    const value = new Date();
    value.setHours(0, 0, 0, 0);
    return value;
  }, []);

  const days = useMemo(
    () => Array.from({ length: 60 }, (_, index) => addDays(today, index)),
    [today],
  );

  useEffect(() => {
    bookingApi.availability(propertyId, iso(today), 60)
      .then((result) => setBlocked(new Set(result.blocked_dates)))
      .catch(() => setMessage('Live availability could not be loaded.'));
  }, [propertyId, today]);

  function selectDate(value: string) {
    if (blocked.has(value)) return;

    if (!checkIn || checkOut) {
      setCheckIn(value);
      setCheckOut('');
      onChange({ checkIn: value, checkOut: '' });
      setMessage('');
      return;
    }

    if (value <= checkIn) {
      setCheckIn(value);
      setCheckOut('');
      onChange({ checkIn: value, checkOut: '' });
      return;
    }

    const start = new Date(checkIn + 'T00:00:00');
    const end = new Date(value + 'T00:00:00');
    let cursor = addDays(start, 1);
    while (cursor < end) {
      if (blocked.has(iso(cursor))) {
        setMessage('That range crosses unavailable dates. Choose another checkout date.');
        return;
      }
      cursor = addDays(cursor, 1);
    }

    setCheckOut(value);
    onChange({ checkIn, checkOut: value });
    setMessage('');
  }

  return (
    <section className="availability-calendar">
      <div className="availability-head">
        <div>
          <span className="eyebrow"><CalendarDays size={15}/>Live availability</span>
          <h3>Select your dates</h3>
        </div>
        <div className="availability-legend">
          <span><i className="available-dot"/>Available</span>
          <span><i className="blocked-dot"/>Unavailable</span>
        </div>
      </div>

      <div className="calendar-grid">
        {days.map((date) => {
          const value = iso(date);
          const isBlocked = blocked.has(value);
          const isSelected = value === checkIn || value === checkOut;
          const inRange = checkIn && checkOut && value > checkIn && value < checkOut;

          return (
            <button
              key={value}
              type="button"
              disabled={isBlocked}
              className={[
                'calendar-day',
                isBlocked ? 'blocked' : '',
                isSelected ? 'selected' : '',
                inRange ? 'in-range' : '',
              ].filter(Boolean).join(' ')}
              onClick={() => selectDate(value)}
            >
              <small>{date.toLocaleDateString('en-IN', { weekday: 'short' })}</small>
              <strong>{date.getDate()}</strong>
              <span>{date.toLocaleDateString('en-IN', { month: 'short' })}</span>
            </button>
          );
        })}
      </div>

      <div className="calendar-selection">
        <span>Check-in: <strong>{checkIn || 'Select date'}</strong></span>
        <span>Check-out: <strong>{checkOut || 'Select date'}</strong></span>
      </div>

      {message && <div className="auth-error">{message}</div>}
    </section>
  );
}

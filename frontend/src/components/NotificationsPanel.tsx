import { useEffect, useState } from 'react';
import { Bell } from 'lucide-react';

import { notificationApi, type NotificationItem } from '../lib/api';

export default function NotificationsPanel() {
  const [items, setItems] = useState<NotificationItem[]>([]);

  useEffect(() => {
    notificationApi.list().then(setItems).catch(() => setItems([]));
  }, []);

  async function markRead(item: NotificationItem) {
    if (item.is_read) return;
    await notificationApi.markRead(item.id).catch(() => undefined);
    setItems((current) =>
      current.map((entry) =>
        entry.id === item.id ? { ...entry, is_read: true } : entry
      )
    );
  }

  return (
    <section className="panel notifications-panel">
      <div className="section-head">
        <div>
          <h2>Notifications</h2>
          <p>Booking, payment, cancellation and message activity.</p>
        </div>
      </div>

      {items.length === 0 ? (
        <p>No notifications yet.</p>
      ) : (
        <div className="notification-list">
          {items.slice(0, 8).map((item) => (
            <button
              type="button"
              className={item.is_read ? 'notification-item' : 'notification-item unread'}
              key={item.id}
              onClick={() => void markRead(item)}
            >
              <Bell size={17}/>
              <span>
                <strong>{item.title}</strong>
                <small>{item.message}</small>
              </span>
              <time>{new Date(item.created_at).toLocaleDateString('en-IN')}</time>
            </button>
          ))}
        </div>
      )}
    </section>
  );
}

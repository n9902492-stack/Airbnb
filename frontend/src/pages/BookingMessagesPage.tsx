import { FormEvent, useEffect, useRef, useState } from 'react';
import { ArrowLeft, MessageCircle, Send } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';

import { authStore } from '../lib/auth';
import { messageApi, type BookingMessage } from '../lib/api';

export default function BookingMessagesPage() {
  const { bookingId } = useParams();
  const id = Number(bookingId);
  const user = authStore.getUser();
  const [messages, setMessages] = useState<BookingMessage[]>([]);
  const [body, setBody] = useState('');
  const [message, setMessage] = useState('');
  const endRef = useRef<HTMLDivElement | null>(null);

  async function refresh() {
    if (!id) return;
    try {
      setMessages(await messageApi.list(id));
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Unable to load conversation');
    }
  }

  useEffect(() => {
    void refresh();
    const timer = window.setInterval(() => void refresh(), 10000);
    return () => window.clearInterval(timer);
  }, [id]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function send(event: FormEvent) {
    event.preventDefault();
    const value = body.trim();
    if (!value) return;

    try {
      await messageApi.send(id, value);
      setBody('');
      await refresh();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Unable to send message');
    }
  }

  const back = user?.role === 'owner' ? '/owner' : user?.role === 'super_admin' ? '/super-admin' : '/user';

  return (
    <main className="messages-page">
      <header className="messages-header">
        <Link to={back} className="back"><ArrowLeft size={18}/>Back to dashboard</Link>
        <span className="brand">Nestora</span>
      </header>

      <section className="messages-shell">
        <div className="messages-title">
          <MessageCircle size={22}/>
          <div>
            <span className="eyebrow">Booking conversation</span>
            <h1>Booking #{id}</h1>
          </div>
        </div>

        {message && <div className="auth-error">{message}</div>}

        <div className="messages-thread">
          {messages.length === 0 ? (
            <div className="empty-state">
              <MessageCircle size={32}/>
              <h3>No messages yet</h3>
              <p>Use this conversation for arrival details, house questions, or check-in coordination.</p>
            </div>
          ) : (
            messages.map((item) => {
              const mine = item.sender_id === user?.id;
              return (
                <article className={mine ? 'message-bubble mine' : 'message-bubble'} key={item.id}>
                  <strong>{mine ? 'You' : item.sender_name}</strong>
                  <p>{item.body}</p>
                  <small>{new Date(item.created_at).toLocaleString('en-IN')}</small>
                </article>
              );
            })
          )}
          <div ref={endRef}/>
        </div>

        <form className="message-composer" onSubmit={send}>
          <textarea
            value={body}
            onChange={(event) => setBody(event.target.value)}
            placeholder="Write a message about this booking…"
            maxLength={3000}
          />
          <button className="primary inline" type="submit"><Send size={17}/>Send</button>
        </form>
      </section>
    </main>
  );
}

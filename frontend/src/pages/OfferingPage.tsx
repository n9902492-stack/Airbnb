import { useEffect, useState } from 'react';
import { ArrowLeft, CalendarDays, CheckCircle2, Clock3, MapPin, Users } from 'lucide-react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import { authStore } from '../lib/auth';
import { offeringApi, type MarketplaceOffering } from '../lib/api';
import { loadRazorpayCheckout, type RazorpaySuccess } from '../lib/razorpay';

export default function OfferingPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const user = authStore.getUser();
  const [item, setItem] = useState<MarketplaceOffering | null>(null);
  const [scheduledAt, setScheduledAt] = useState('');
  const [guests, setGuests] = useState(1);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    offeringApi.get(Number(id))
      .then(setItem)
      .catch((err) => setMessage(err instanceof Error ? err.message : 'Unable to load offering'));
  }, [id]);

  async function verifyRazorpay(
    bookingId: number,
    response: RazorpaySuccess,
  ) {
    const params = new URLSearchParams({
      razorpay_order_id: response.razorpay_order_id,
      razorpay_payment_id: response.razorpay_payment_id,
      razorpay_signature: response.razorpay_signature,
    });
    const token = localStorage.getItem('nestora_access_token');
    const base = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1';
    const res = await fetch(
      base + '/offerings/bookings/' + bookingId + '/verify-razorpay?' + params.toString(),
      {
        method: 'POST',
        credentials: 'include',
        headers: token ? { Authorization: 'Bearer ' + token } : {},
      },
    );
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail ?? 'Payment verification failed');
    }
    setMessage('Payment confirmed. This booking is now in your Trips.');
  }

  async function book() {
    if (!item) return;
    if (!user) {
      navigate('/auth');
      return;
    }
    if (!scheduledAt) {
      setMessage('Choose a date and time first.');
      return;
    }

    setBusy(true);
    setMessage('');
    try {
      const booking = await offeringApi.book(item.id, {
        scheduled_at: new Date(scheduledAt).toISOString(),
        guest_count: guests,
      });

      if (booking.status === 'requested') {
        setMessage(booking.message || 'Request sent to host.');
        return;
      }

      if (booking.provider === 'manual_demo') {
        await offeringApi.confirmDemo(booking.id);
        setMessage('Development payment confirmed. Added to your Trips.');
        return;
      }

      if (
        booking.provider === 'razorpay'
        && booking.razorpay_key_id
        && booking.provider_order_id
        && booking.amount_paise
      ) {
        await loadRazorpayCheckout();
        if (!window.Razorpay) throw new Error('Razorpay checkout unavailable');

        const checkout = new window.Razorpay({
          key: booking.razorpay_key_id,
          amount: booking.amount_paise,
          currency: booking.currency ?? 'INR',
          order_id: booking.provider_order_id,
          name: 'Nestora',
          description: item.title,
          handler: (response) => {
            void verifyRazorpay(booking.id, response)
              .catch((err) => setMessage(err instanceof Error ? err.message : 'Payment verification failed'));
          },
        });
        checkout.open();
      }
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Unable to book');
    } finally {
      setBusy(false);
    }
  }

  if (!item) {
    return <main className="detail-page"><div className="detail-top"><Link className="back" to="/"><ArrowLeft size={18}/>Back</Link><span className="brand">Nestora</span></div><p>{message || 'Loading…'}</p></main>;
  }

  const image = item.image_urls?.[0] || 'https://images.unsplash.com/photo-1528715471579-d1bcf0ba5e83?auto=format&fit=crop&w=1400&q=85';

  return (
    <main className="detail-page">
      <div className="detail-top">
        <Link className="back" to="/"><ArrowLeft size={18}/>Back</Link>
        <span className="brand">Nestora</span>
      </div>

      <div className="offering-hero">
        <img src={image} alt={item.title}/>
        <div>
          <span className="eyebrow">{item.kind} · {item.category}</span>
          <h1>{item.title}</h1>
          <p><MapPin size={17}/>{item.city}, {item.state}</p>
          <Link className="host-link" to={'/hosts/' + item.host_id}>View host profile</Link>
        </div>
      </div>

      <div className="detail-layout">
        <section>
          <div className="facts">
            <span><Clock3/> {item.duration_minutes} minutes</span>
            <span><Users/> up to {item.capacity}</span>
            <span><CalendarDays/> {item.instant_book ? 'Instant book' : 'Request to book'}</span>
          </div>
          <p className="lead">{item.description}</p>

          <h2>What’s included</h2>
          <div className="highlight-list">
            {item.included_items.length
              ? item.included_items.map((x)=><div key={x}><CheckCircle2 size={18}/><span>{x}</span></div>)
              : <p>Host will provide final details after booking.</p>}
          </div>

          {item.requirements.length > 0 && (
            <>
              <h2>Guest requirements</h2>
              <div className="amenity-grid">{item.requirements.map((x)=><span key={x}>{x}</span>)}</div>
            </>
          )}
        </section>

        <aside className="booking-card">
          <h3>₹{Number(item.price).toLocaleString('en-IN')} <span>/ {item.pricing_unit.replace('_',' ')}</span></h3>
          <label className="booking-guest-field">
            <small>Date & time</small>
            <input type="datetime-local" value={scheduledAt} onChange={(e)=>setScheduledAt(e.target.value)}/>
          </label>
          <label className="booking-guest-field">
            <small>Guests</small>
            <select value={guests} onChange={(e)=>setGuests(Number(e.target.value))}>
              {Array.from({ length:item.capacity },(_,i)=><option value={i+1} key={i+1}>{i+1}</option>)}
            </select>
          </label>
          {message && <div className={message.toLowerCase().includes('confirmed') ? 'auth-success' : 'auth-error'}>{message}</div>}
          <button className="primary" disabled={busy} onClick={()=>void book()}>
            {busy ? 'Processing…' : item.instant_book ? 'Book now' : 'Request'}
          </button>
        </aside>
      </div>
    </main>
  );
}

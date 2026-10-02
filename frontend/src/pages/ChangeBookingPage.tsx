import { FormEvent, useEffect, useState } from 'react';
import { ArrowLeft, CalendarDays, CreditCard, Users } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';

import { bookingApi, bookingChangeApi, type BookingChangeRequest } from '../lib/api';
import { loadRazorpayCheckout, type RazorpaySuccess } from '../lib/razorpay';

export default function ChangeBookingPage() {
  const { bookingId } = useParams();
  const id = Number(bookingId);
  const [trip, setTrip] = useState<Awaited<ReturnType<typeof bookingApi.myTrips>>[number] | null>(null);
  const [changes, setChanges] = useState<BookingChangeRequest[]>([]);
  const [checkIn, setCheckIn] = useState('');
  const [checkOut, setCheckOut] = useState('');
  const [guests, setGuests] = useState(1);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);

  async function load() {
    try {
      const [trips, items] = await Promise.all([
        bookingApi.myTrips(),
        bookingChangeApi.mine(),
      ]);
      const current = trips.find((x)=>x.id === id) ?? null;
      setTrip(current);
      setChanges(items.filter((x)=>x.booking_id === id));
      if (current) {
        setCheckIn(current.check_in);
        setCheckOut(current.check_out);
        setGuests(current.guest_count);
      }
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Unable to load reservation');
    }
  }

  useEffect(()=>{void load();},[id]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setMessage('');
    try {
      const result = await bookingChangeApi.create(id, {
        check_in:checkIn,
        check_out:checkOut,
        guest_count:guests,
      });
      setMessage(
        'Change request sent. New estimated total: ₹'
        + Number(result.new_total_amount).toLocaleString('en-IN')
        + (result.price_difference
          ? ' · Difference ' + (result.price_difference > 0 ? '+' : '') + '₹' + Number(result.price_difference).toLocaleString('en-IN')
          : ''),
      );
      await load();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Unable to request change');
    } finally {
      setBusy(false);
    }
  }

  async function verifyAdjustment(
    adjustmentId:number,
    response:RazorpaySuccess,
  ) {
    await bookingChangeApi.verifyAdjustment(adjustmentId,response);
    setMessage('Adjustment payment verified. Your reservation change is applied.');
    await load();
  }

  async function payAdjustment(change:BookingChangeRequest) {
    const adjustment = change.adjustment;
    if (!adjustment) return;

    if (adjustment.provider === 'manual_demo') {
      await bookingChangeApi.confirmDemoAdjustment(adjustment.id);
      setMessage('Development adjustment confirmed. Your reservation was updated.');
      await load();
      return;
    }

    if (!adjustment.razorpay_key_id || !adjustment.provider_order_id || !adjustment.amount_paise) {
      setMessage('Adjustment checkout is incomplete.');
      return;
    }

    await loadRazorpayCheckout();
    if (!window.Razorpay) {
      setMessage('Razorpay checkout is unavailable.');
      return;
    }

    const checkout = new window.Razorpay({
      key:adjustment.razorpay_key_id,
      amount:adjustment.amount_paise,
      currency:'INR',
      order_id:adjustment.provider_order_id,
      name:'Nestora',
      description:'Reservation change',
      handler:(response)=>void verifyAdjustment(adjustment.id,response)
        .catch((err)=>setMessage(err instanceof Error ? err.message : 'Adjustment verification failed')),
    });
    checkout.open();
  }

  if (!trip) {
    return <main className="profile-page"><div className="detail-top"><Link to="/user" className="back"><ArrowLeft size={18}/>My trips</Link><span className="brand">Nestora</span></div><div className="profile-shell">{message || 'Loading…'}</div></main>;
  }

  return (
    <main className="profile-page">
      <div className="detail-top">
        <Link to="/user" className="back"><ArrowLeft size={18}/>My trips</Link>
        <span className="brand">Nestora</span>
      </div>

      <section className="profile-shell">
        <div>
          <span className="eyebrow">Reservation change</span>
          <h1>{trip.property_title}</h1>
          <p>Request new dates or guest count. The host must approve, and any price difference is handled separately.</p>
        </div>

        <form className="panel" onSubmit={submit}>
          <div className="form-grid">
            <label><CalendarDays size={17}/>Check-in<input type="date" value={checkIn} onChange={(e)=>setCheckIn(e.target.value)} required/></label>
            <label><CalendarDays size={17}/>Check-out<input type="date" min={checkIn || undefined} value={checkOut} onChange={(e)=>setCheckOut(e.target.value)} required/></label>
            <label><Users size={17}/>Guests<input type="number" min="1" value={guests} onChange={(e)=>setGuests(Number(e.target.value))} required/></label>
          </div>
          {message && <div className="auth-success">{message}</div>}
          <button className="primary inline" disabled={busy}>{busy ? 'Checking…' : 'Request change'}</button>
        </form>

        <div className="panel">
          <h2>Change history</h2>
          <div className="support-list">
            {changes.length === 0 ? <p>No change requests yet.</p> : changes.map((change)=>(
              <article key={change.id}>
                <div>
                  <strong>{change.new_check_in} → {change.new_check_out}</strong>
                  <small>{change.new_guest_count} guests · New total ₹{Number(change.new_total_amount).toLocaleString('en-IN')}</small>
                  <p>Price difference: {change.price_difference > 0 ? '+' : ''}₹{Number(change.price_difference).toLocaleString('en-IN')}</p>
                </div>
                <span className={'booking-status ' + change.status}>{change.status.replaceAll('_',' ')}</span>
                {change.status === 'payment_required' && change.adjustment && (
                  <button className="primary inline" onClick={()=>void payAdjustment(change)}>
                    <CreditCard size={17}/>Pay ₹{Number(change.adjustment.amount).toLocaleString('en-IN')}
                  </button>
                )}
              </article>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}

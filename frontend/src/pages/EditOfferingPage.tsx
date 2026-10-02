import { FormEvent, useEffect, useState } from 'react';
import { ArrowLeft, CalendarDays, Clock3, Users } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';

import { offeringApi, type MarketplaceOffering } from '../lib/api';

export default function EditOfferingPage() {
  const { offeringId } = useParams();
  const id = Number(offeringId);
  const [item, setItem] = useState<MarketplaceOffering | null>(null);
  const [slots, setSlots] = useState<Awaited<ReturnType<typeof offeringApi.slots>>>([]);
  const [startsAt, setStartsAt] = useState('');
  const [endsAt, setEndsAt] = useState('');
  const [capacity, setCapacity] = useState(4);
  const [priceOverride, setPriceOverride] = useState<number | ''>('');
  const [privatePrice, setPrivatePrice] = useState<number | ''>('');
  const [privateAvailable, setPrivateAvailable] = useState(false);
  const [message, setMessage] = useState('');

  async function load() {
    try {
      const mine = await offeringApi.mine();
      const found = mine.find((x)=>x.id === id) ?? null;
      setItem(found);
      if (found) setSlots(await offeringApi.slots(id));
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Unable to load offering');
    }
  }

  useEffect(()=>{void load();},[id]);

  async function addSlot(event: FormEvent) {
    event.preventDefault();
    if (!startsAt || !endsAt) return;
    try {
      await offeringApi.createSlot(id, {
        starts_at:new Date(startsAt).toISOString(),
        ends_at:new Date(endsAt).toISOString(),
        capacity,
        price_override:priceOverride === '' ? null : priceOverride,
        private_group_price:privatePrice === '' ? null : privatePrice,
        is_private_available:privateAvailable,
      });
      setMessage('Availability slot published.');
      setStartsAt('');
      setEndsAt('');
      setSlots(await offeringApi.slots(id));
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Unable to add slot');
    }
  }

  if (!item) {
    return <main className="property-wizard"><div className="wizard-top"><Link className="back" to="/owner"><ArrowLeft size={18}/>Owner dashboard</Link><span className="brand">Nestora</span></div><div className="wizard-shell">{message || 'Loading…'}</div></main>;
  }

  return (
    <main className="property-wizard">
      <div className="wizard-top">
        <Link className="back" to="/owner"><ArrowLeft size={18}/>Owner dashboard</Link>
        <span className="brand">Nestora</span>
      </div>

      <section className="edit-property-shell">
        <div className="wizard-form">
          <span className="eyebrow">{item.kind} calendar</span>
          <h1>{item.title}</h1>
          <p>Publish bookable time slots. Guests can only reserve these times, and capacity is enforced server-side.</p>

          <div className="slot-list">
            {slots.length === 0 ? <p>No future availability yet.</p> : slots.map((slot)=>(
              <article className="slot-card" key={slot.id}>
                <CalendarDays size={18}/>
                <div>
                  <strong>{new Date(slot.starts_at).toLocaleString('en-IN')}</strong>
                  <small>to {new Date(slot.ends_at).toLocaleString('en-IN')}</small>
                </div>
                <span><Users size={15}/>{slot.capacity}</span>
                <span>{slot.price_override ? '₹' + Number(slot.price_override).toLocaleString('en-IN') : 'Base price'}</span>
                {slot.is_private_available && <span>Private group ₹{Number(slot.private_group_price ?? 0).toLocaleString('en-IN')}</span>}
              </article>
            ))}
          </div>
        </div>

        <aside className="owner-side-stack">
          <form className="owner-calendar-panel" onSubmit={addSlot}>
            <span className="eyebrow">Publish availability</span>
            <h2>Add a time slot</h2>
            <label>Starts<input type="datetime-local" value={startsAt} onChange={(e)=>setStartsAt(e.target.value)} required/></label>
            <label>Ends<input type="datetime-local" value={endsAt} onChange={(e)=>setEndsAt(e.target.value)} required/></label>
            <label>Capacity<input type="number" min="1" max="100" value={capacity} onChange={(e)=>setCapacity(Number(e.target.value))}/></label>
            <label>Price override (₹)<input type="number" min="1" value={priceOverride} placeholder="Use base price" onChange={(e)=>setPriceOverride(e.target.value ? Number(e.target.value) : '')}/></label>
            <label className="toggle-filter"><input type="checkbox" checked={privateAvailable} onChange={(e)=>setPrivateAvailable(e.target.checked)}/>Allow private groups</label>
            {privateAvailable && <label>Private group price (₹)<input type="number" min="1" value={privatePrice} onChange={(e)=>setPrivatePrice(e.target.value ? Number(e.target.value) : '')}/></label>}
            {message && <div className="auth-success">{message}</div>}
            <button className="primary inline"><Clock3 size={17}/>Publish slot</button>
          </form>
        </aside>
      </section>
    </main>
  );
}

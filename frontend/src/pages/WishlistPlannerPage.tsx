import { FormEvent, useEffect, useState } from 'react';
import { ArrowLeft, CalendarDays, Copy, ThumbsDown, ThumbsUp, Users } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';

import { collaborationApi } from '../lib/api';

type Detail = Awaited<ReturnType<typeof collaborationApi.wishlistDetail>>;

export default function WishlistPlannerPage() {
  const { id } = useParams();
  const collectionId = Number(id);
  const [detail, setDetail] = useState<Detail | null>(null);
  const [start, setStart] = useState('');
  const [end, setEnd] = useState('');
  const [guests, setGuests] = useState(2);
  const [notes, setNotes] = useState<Record<number,string>>({});
  const [message, setMessage] = useState('');

  async function load() {
    try {
      const value = await collaborationApi.wishlistDetail(collectionId);
      setDetail(value);
      setStart(value.proposed_start_date ?? '');
      setEnd(value.proposed_end_date ?? '');
      setGuests(value.guest_count ?? 2);
      setNotes(Object.fromEntries(value.items.map((item)=>[item.id,item.note ?? ''])));
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Unable to load shared wishlist');
    }
  }

  useEffect(()=>{ void load(); },[collectionId]);

  async function savePlan(event: FormEvent) {
    event.preventDefault();
    await collaborationApi.updateWishlist(collectionId, {
      proposed_start_date:start || null,
      proposed_end_date:end || null,
      guest_count:guests,
    });
    setMessage('Trip plan updated for everyone in this wishlist.');
    await load();
  }

  if (!detail) {
    return <main className="profile-page"><div className="detail-top"><Link to="/user" className="back"><ArrowLeft size={18}/>Trips</Link><span className="brand">Nestora</span></div><div className="profile-shell">{message || 'Loading…'}</div></main>;
  }

  return (
    <main className="profile-page">
      <div className="detail-top">
        <Link to="/user" className="back"><ArrowLeft size={18}/>Traveller dashboard</Link>
        <span className="brand">Nestora</span>
      </div>

      <section className="profile-shell">
        <div className="section-head">
          <div><span className="eyebrow">Collaborative wishlist</span><h1>{detail.name}</h1></div>
        </div>

        <form className="panel wishlist-plan-form" onSubmit={savePlan}>
          <h2>Plan this trip together</h2>
          <div className="form-grid">
            <label><CalendarDays size={17}/>Start date<input type="date" value={start} onChange={(e)=>setStart(e.target.value)}/></label>
            <label><CalendarDays size={17}/>End date<input type="date" min={start || undefined} value={end} onChange={(e)=>setEnd(e.target.value)}/></label>
            <label><Users size={17}/>Guests<input type="number" min="1" max="50" value={guests} onChange={(e)=>setGuests(Number(e.target.value))}/></label>
          </div>
          <button className="primary inline">Save trip plan</button>
        </form>

        {message && <div className="auth-success">{message}</div>}

        <div className="wishlist-planner-grid">
          {detail.items.map((item)=> {
            const image = item.image_urls?.[0]
              ? item.image_urls[0].startsWith('/uploads') ? 'http://localhost:8000' + item.image_urls[0] : item.image_urls[0]
              : 'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=700&q=80';
            return (
              <article className="wishlist-plan-card" key={item.id}>
                <Link to={'/stays/' + item.property_id}><img src={image} alt={item.title}/></Link>
                <div>
                  <Link to={'/stays/' + item.property_id}><strong>{item.title}</strong></Link>
                  <p>{item.city}, {item.state}</p>
                  <span>₹{Number(item.price_per_night).toLocaleString('en-IN')}/night</span>
                  <div className="wishlist-votes">
                    <button className="ghost dark" onClick={async()=>{await collaborationApi.voteWishlistItem(collectionId,item.id,1);await load();}}><ThumbsUp size={16}/></button>
                    <strong>{item.vote_score}</strong>
                    <button className="ghost dark" onClick={async()=>{await collaborationApi.voteWishlistItem(collectionId,item.id,-1);await load();}}><ThumbsDown size={16}/></button>
                  </div>
                  <textarea value={notes[item.id] ?? ''} onChange={(e)=>setNotes((current)=>({...current,[item.id]:e.target.value}))} placeholder="Add a note for your group…"/>
                  <button className="ghost dark" onClick={async()=>{await collaborationApi.updateWishlistNote(collectionId,item.id,notes[item.id] ?? '');setMessage('Note saved.');}}>Save note</button>
                </div>
              </article>
            );
          })}
        </div>

        {detail.items.length === 0 && <div className="empty-state"><h3>No stays added yet</h3><p>Add properties to this shared list from the discovery page.</p></div>}
      </section>
    </main>
  );
}

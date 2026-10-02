import { useEffect, useMemo, useState } from 'react';
import { Heart, Home, LogOut, Suitcase, UserRound } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

import { authStore } from '../lib/auth';
import { authApi, bookingApi, collaborationApi, invoiceApi, offeringApi, wishlistApi, type WishlistItem } from '../lib/api';
import NotificationsPanel from '../components/NotificationsPanel';

type Trip = Awaited<ReturnType<typeof bookingApi.myTrips>>[number];

export default function UserDashboard() {
  const navigate = useNavigate();
  const user = authStore.getUser();
  const [trips, setTrips] = useState<Trip[]>([]);
  const [message, setMessage] = useState('');
  const [wishlist, setWishlist] = useState<WishlistItem[]>([]);
  const [offeringTrips, setOfferingTrips] = useState<Awaited<ReturnType<typeof offeringApi.mineBookings>>>([]);
  const [specialOffers, setSpecialOffers] = useState<Awaited<ReturnType<typeof collaborationApi.specialOffers>>>([]);
  const [sharedWishlists, setSharedWishlists] = useState<Awaited<ReturnType<typeof collaborationApi.wishlists>>>([]);
  const [newWishlistName, setNewWishlistName] = useState('');
  const [joinToken, setJoinToken] = useState('');

  async function loadTrips() {
    try {
      const [tripItems, saved, activities, offers, collections] = await Promise.all([
        bookingApi.myTrips(),
        wishlistApi.list(),
        offeringApi.mineBookings(),
        collaborationApi.specialOffers(),
        collaborationApi.wishlists(),
      ]);
      setTrips(tripItems);
      setWishlist(saved);
      setOfferingTrips(activities);
      setSpecialOffers(offers);
      setSharedWishlists(collections);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Unable to load trips');
    }
  }

  useEffect(() => {
    void loadTrips();
  }, []);

  async function signOut() {
    await authApi.logout().catch(() => undefined);
    authStore.clear();
    navigate('/auth');
  }

  async function cancelTrip(bookingId: number) {
    try {
      const result = await bookingApi.cancel(bookingId);
      setMessage(
        result.refund_percent > 0
          ? `Booking cancelled. Refund: ₹${Number(result.refund_amount).toLocaleString('en-IN')} (${result.refund_percent}%).`
          : 'Booking cancelled. This cancellation is outside the refundable window.',
      );
      await loadTrips();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Unable to cancel booking');
    }
  }

  const stats = useMemo(() => {
    const today = new Date().toISOString().slice(0, 10);
    const upcoming = trips.filter((trip) =>
      ['pending', 'confirmed'].includes(trip.status) && trip.check_out >= today
    ).length;
    const completed = trips.filter((trip) => trip.status === 'completed').length;
    const pending = trips.filter((trip) => trip.status === 'pending').length;
    return { upcoming, completed, pending };
  }, [trips]);

  return (
    <main className="dashboard">
      <aside className="sidebar">
        <Link className="brand" to="/">Nestora</Link>
        <strong>Traveller</strong>
        <nav>
          <a className="selected"><Home />Overview</a>
          <a><Suitcase />Trips</a>
          <a><Heart />Wishlists</a>
          <Link to="/trust"><UserRound />Trust & support</Link>
          <button className="sidebar-button" onClick={signOut}><LogOut />Sign out</button>
        </nav>
      </aside>

      <section className="dash-content">
        <div className="dash-head">
          <div>
            <span className="eyebrow">Traveller dashboard</span>
            <h1>Welcome, {user?.full_name ?? 'Traveller'}</h1>
            <p>Your real PostgreSQL bookings, payment state and cancellation options are shown here.</p>
          </div>
        </div>

        <div className="stats">
          <div className="stat"><small>Upcoming trips</small><strong>{stats.upcoming}</strong></div>
          <div className="stat"><small>Pending payment</small><strong>{stats.pending}</strong></div>
          <div className="stat"><small>Completed trips</small><strong>{stats.completed}</strong></div>
          <div className="stat"><small>Total trips</small><strong>{trips.length}</strong></div>
        </div>

        {message && <div className="auth-success">{message}</div>}

        <div className="panel">
          <div className="section-head">
            <div>
              <h2>My trips</h2>
              <p>Pending holds expire automatically if payment is not completed.</p>
            </div>
          </div>

          {trips.length === 0 ? (
            <div className="empty-state">
              <Suitcase size={34}/>
              <h3>No trips yet</h3>
              <p>Browse stays and your reservations will appear here.</p>
              <Link className="primary inline" to="/">Explore stays</Link>
            </div>
          ) : (
            <div className="trip-grid">
              {trips.map((trip) => (
                <article className="trip-card" key={trip.id}>
                  <div className="trip-card-head">
                    <div>
                      <strong>{trip.property_title}</strong>
                      <small>Booking #{trip.id}</small>
                    </div>
                    <span className={'booking-status ' + trip.status}>{trip.status}</span>
                  </div>

                  <div className="trip-details">
                    <span><small>Check-in</small><strong>{trip.check_in}</strong></span>
                    <span><small>Check-out</small><strong>{trip.check_out}</strong></span>
                    <span><small>Guests</small><strong>{trip.guest_count}</strong></span>
                    <span><small>Stay total</small><strong>₹{Number(trip.total_amount).toLocaleString('en-IN')}</strong></span>
                  </div>

                  <div className="trip-payment">
                    Payment: <strong>{trip.payment_status ?? 'not started'}</strong>
                  </div>

                  {trip.status === 'pending' && trip.expires_at && (
                    <p className="trip-hold-note">Payment hold expires at {new Date(trip.expires_at).toLocaleString('en-IN')}.</p>
                  )}

                  <div className="trip-actions">
                    <Link className="ghost dark" to={'/messages/' + trip.id}>Message host</Link>
                    {trip.payment_status === 'paid' && (
                      <button className="ghost dark" onClick={async()=>{
                        try {
                          const invoice = await invoiceApi.get(trip.id);
                          setMessage('Invoice ' + invoice.invoice_number + ' · Total ₹' + Number(invoice.total_amount).toLocaleString('en-IN') + (invoice.gst_amount ? ' · GST ₹' + Number(invoice.gst_amount).toLocaleString('en-IN') : ''));
                        } catch (err) {
                          setMessage(err instanceof Error ? err.message : 'Invoice unavailable');
                        }
                      }}>View invoice</button>
                    )}
                    {trip.status === 'pending' && (
                      <Link className="primary inline" to={'/checkout/' + trip.id}>Continue payment</Link>
                    )}
                    {['pending', 'confirmed'].includes(trip.status) && (
                      <button className="ghost dark" onClick={() => void cancelTrip(trip.id)}>Cancel booking</button>
                    )}
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>


        <div className="panel">
          <div className="section-head"><div><h2>Services & experiences</h2><p>Your booked activities and services appear in the same itinerary.</p></div></div>
          {offeringTrips.length === 0 ? <p>No services or experiences booked yet.</p> : (
            <div className="trip-grid">
              {offeringTrips.map((trip)=>(
                <article className="trip-card" key={'offering-trip-' + trip.id}>
                  <div className="trip-card-head">
                    <div><strong>{trip.title}</strong><small>{trip.kind} booking #{trip.id}</small></div>
                    <span className={'booking-status ' + trip.status}>{trip.status}</span>
                  </div>
                  <div className="trip-details">
                    <span><small>When</small><strong>{new Date(trip.scheduled_at).toLocaleString('en-IN')}</strong></span>
                    <span><small>Guests</small><strong>{trip.guest_count}</strong></span>
                    <span><small>Total</small><strong>₹{Number(trip.total_amount).toLocaleString('en-IN')}</strong></span>
                    <span><small>Payment</small><strong>{trip.payment_status}</strong></span>
                  </div>
                  <div className="trip-actions"><Link className="ghost dark" to={'/offerings/' + trip.offering_id}>View details</Link></div>
                </article>
              ))}
            </div>
          )}
        </div>

        <div className="panel">
          <div className="section-head"><div><h2>Special offers</h2><p>Host offers expire automatically and become normal checkout reservations when accepted.</p></div></div>
          {specialOffers.filter((x)=>x.status === 'pending').length === 0 ? <p>No active special offers.</p> : (
            <div className="trip-grid">
              {specialOffers.filter((x)=>x.status === 'pending').map((offer)=>(
                <article className="trip-card" key={'offer-' + offer.id}>
                  <div className="trip-card-head"><div><strong>{offer.property_title}</strong><small>Special offer</small></div><span className="booking-status pending">pending</span></div>
                  <div className="trip-details">
                    <span><small>Check-in</small><strong>{offer.check_in}</strong></span>
                    <span><small>Check-out</small><strong>{offer.check_out}</strong></span>
                    <span><small>Guests</small><strong>{offer.guest_count}</strong></span>
                    <span><small>Offer</small><strong>₹{Number(offer.total_price).toLocaleString('en-IN')}</strong></span>
                  </div>
                  <div className="trip-actions">
                    <button className="primary inline" onClick={async()=>{
                      const result = await collaborationApi.acceptSpecialOffer(offer.id);
                      navigate('/checkout/' + result.booking_id);
                    }}>Accept offer</button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>


        <div className="panel">
          <div className="section-head"><div><h2>Shared trip wishlists</h2><p>Invite people, set dates and guest count, add notes and vote on stays together.</p></div></div>
          <div className="collaboration-create">
            <input value={newWishlistName} onChange={(e)=>setNewWishlistName(e.target.value)} placeholder="Weekend in Manali"/>
            <button className="primary inline" onClick={async()=>{
              const name = newWishlistName.trim();
              if (!name) return;
              await collaborationApi.createWishlist(name);
              setNewWishlistName('');
              setSharedWishlists(await collaborationApi.wishlists());
            }}>Create wishlist</button>
            <input value={joinToken} onChange={(e)=>setJoinToken(e.target.value)} placeholder="Paste shared token"/>
            <button className="ghost dark" onClick={async()=>{
              const token = joinToken.trim();
              if (!token) return;
              await collaborationApi.joinWishlist(token);
              setJoinToken('');
              setSharedWishlists(await collaborationApi.wishlists());
            }}>Join shared list</button>
          </div>
          <div className="shared-wishlist-grid">
            {sharedWishlists.length === 0 ? <p>No collaborative wishlists yet.</p> : sharedWishlists.map((list)=>(
              <Link className="shared-wishlist-card" to={'/wishlists/' + list.id} key={list.id}>
                <strong>{list.name}</strong>
                <small>{list.proposed_start_date && list.proposed_end_date ? list.proposed_start_date + ' → ' + list.proposed_end_date : 'Dates not chosen'}</small>
                <span>{list.guest_count ? list.guest_count + ' guests' : 'Guest count open'}</span>
                {list.share_token && <code>{list.share_token}</code>}
              </Link>
            ))}
          </div>
        </div>

        <div className="panel">
          <div className="section-head">
            <div><h2>Saved stays</h2><p>Your wishlist stays connected to live properties.</p></div>
          </div>
          <div className="saved-grid">
            {wishlist.length === 0 ? <p>No saved stays yet.</p> : wishlist.map((item) => (
              <Link className="saved-card" to={'/stays/' + item.property_id} key={item.id}>
                {item.image_urls?.[0] && <img src={item.image_urls[0].startsWith('/uploads') ? 'http://localhost:8000' + item.image_urls[0] : item.image_urls[0]} alt={item.title}/>}
                <div><strong>{item.title}</strong><small>{item.city}, {item.state}</small><span>₹{Number(item.price_per_night).toLocaleString('en-IN')}/night</span></div>
              </Link>
            ))}
          </div>
        </div>

        <NotificationsPanel />
      </section>
    </main>
  );
}

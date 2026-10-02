import { useEffect, useMemo, useState } from 'react';
import { Heart, Home, LogOut, Suitcase, UserRound } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

import { authStore } from '../lib/auth';
import { bookingApi } from '../lib/api';

type Trip = Awaited<ReturnType<typeof bookingApi.myTrips>>[number];

export default function UserDashboard() {
  const navigate = useNavigate();
  const user = authStore.getUser();
  const [trips, setTrips] = useState<Trip[]>([]);
  const [message, setMessage] = useState('');

  async function loadTrips() {
    try {
      setTrips(await bookingApi.myTrips());
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Unable to load trips');
    }
  }

  useEffect(() => {
    void loadTrips();
  }, []);

  function signOut() {
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
          <a><UserRound />Profile</a>
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
      </section>
    </main>
  );
}

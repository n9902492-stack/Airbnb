import { useEffect, useState } from 'react';
import { Building2, Flag, LayoutDashboard, Shield, Users } from 'lucide-react';
import { Link } from 'react-router-dom';
import { adminApi, adminBookingApi, type AdminBooking, type PendingProperty } from '../lib/api';

export default function SuperAdminDashboard() {
  const [overview, setOverview] = useState({ users: 0, owners: 0, listings: 0, bookings: 0 });
  const [pending, setPending] = useState<PendingProperty[]>([]);
  const [reason, setReason] = useState<Record<number, string>>({});
  const [message, setMessage] = useState('');
  const [bookings, setBookings] = useState<AdminBooking[]>([]);

  async function refresh() {
    const [summary, items, bookingItems] = await Promise.all([
      adminApi.overview(),
      adminApi.pendingProperties(),
      adminBookingApi.list(),
    ]);
    setOverview(summary);
    setPending(items);
    setBookings(bookingItems);
  }

  useEffect(() => {
    void refresh().catch((err) => setMessage(err instanceof Error ? err.message : 'Unable to load moderation data'));
  }, []);

  async function approve(id: number) {
    try {
      await adminApi.approveProperty(id);
      setMessage('Listing approved and moved live.');
      await refresh();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Unable to approve listing');
    }
  }

  async function reject(id: number) {
    const value = reason[id]?.trim();
    if (!value) {
      setMessage('Add a rejection reason first.');
      return;
    }
    try {
      await adminApi.rejectProperty(id, value);
      setMessage('Listing rejected with owner feedback.');
      await refresh();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Unable to reject listing');
    }
  }

  return (
    <main className="dashboard admin-theme">
      <aside className="sidebar">
        <Link className="brand" to="/">Nestora</Link>
        <strong>Super Admin</strong>
        <nav>
          <a className="selected"><LayoutDashboard />Overview</a>
          <a><Users />Users & owners</a>
          <a><Building2 />Listings</a>
          <a><Flag />Reports</a>
          <a><Shield />Platform controls</a>
        </nav>
      </aside>

      <section className="dash-content">
        <div className="dash-head">
          <div>
            <span className="eyebrow">Platform control centre</span>
            <h1>Super Admin overview</h1>
            <p>All numbers and pending listings below are loaded from PostgreSQL.</p>
          </div>
        </div>

        <div className="stats">
          <div className="stat"><small>Total users</small><strong>{overview.users}</strong></div>
          <div className="stat"><small>Owners</small><strong>{overview.owners}</strong></div>
          <div className="stat"><small>Total listings</small><strong>{overview.listings}</strong></div>
          <div className="stat"><small>Bookings</small><strong>{overview.bookings}</strong></div>
        </div>

        {message && <div className="auth-success">{message}</div>}

        <div className="panel">
          <div className="section-head">
            <div>
              <h2>Pending listing moderation</h2>
              <p>{pending.length} listing{pending.length === 1 ? '' : 's'} currently need review.</p>
            </div>
          </div>

          {pending.length === 0 ? (
            <p>No listings are awaiting moderation.</p>
          ) : (
            <div className="admin-moderation-grid">
              {pending.map((item) => {
                const image = item.image_urls?.[0];
                return (
                  <article className="admin-listing-card" key={item.id}>
                    {image && <img src={image.startsWith('/uploads') ? 'http://localhost:8000' + image : image} alt={item.title} />}
                    <div>
                      <strong>{item.title}</strong>
                      <p>{item.city}, {item.state} · ₹{Number(item.price_per_night).toLocaleString('en-IN')}/night</p>
                      <small>Owner ID #{item.owner_id}</small>
                    </div>
                    <textarea
                      placeholder="Reason if rejecting"
                      value={reason[item.id] ?? ''}
                      onChange={(e) => setReason((current) => ({ ...current, [item.id]: e.target.value }))}
                    />
                    <div className="moderation-actions">
                      <button className="primary inline" onClick={() => void approve(item.id)}>Approve</button>
                      <button className="ghost dark" onClick={() => void reject(item.id)}>Reject</button>
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </div>

        <div className="panel admin-bookings-panel">
          <div className="section-head"><div><h2>Booking controls</h2><p>Recent reservations, payment state and platform cancellation control.</p></div></div>
          <div className="reservation-table-wrap">
            <table>
              <thead><tr><th>Property</th><th>Guest</th><th>Dates</th><th>Booking</th><th>Payment</th><th>Total</th><th></th></tr></thead>
              <tbody>
                {bookings.map((booking) => (
                  <tr key={booking.booking_id}>
                    <td>{booking.property_title}</td>
                    <td>{booking.guest_name}</td>
                    <td>{booking.check_in} → {booking.check_out}</td>
                    <td><span className={'booking-status ' + booking.status}>{booking.status}</span></td>
                    <td>{booking.payment_status ?? 'not started'}{booking.refund_amount ? ' · refund ₹' + booking.refund_amount : ''}</td>
                    <td>₹{Number(booking.total_amount).toLocaleString('en-IN')}</td>
                    <td>{['pending','confirmed'].includes(booking.status) && <button className="ghost dark" onClick={async()=>{await adminBookingApi.cancel(booking.booking_id); await refresh();}}>Cancel</button>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </main>
  );
}

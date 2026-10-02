import { useEffect, useMemo, useState } from 'react';
import { BarChart3, CalendarDays, Home, Plus, Star, WalletCards } from 'lucide-react';
import { Link } from 'react-router-dom';
import { authStore } from '../lib/auth';
import { earningsApi, offeringApi, ownerApi, ownerManagementApi, type MarketplaceOffering, type OwnerEarnings, type OwnerProperty } from '../lib/api';
import NotificationsPanel from '../components/NotificationsPanel';

const examples: OwnerProperty[] = [
  {
    id: 901,
    title: 'Cedar Glass House',
    city: 'Manali',
    state: 'Himachal Pradesh',
    price_per_night: 7200,
    status: 'live',
    image_urls: ['https://images.unsplash.com/photo-1601918774946-25832a4be0d6?auto=format&fit=crop&w=500&q=80'],
  },
  {
    id: 902,
    title: 'Pine Ridge Cabin',
    city: 'Kasol',
    state: 'Himachal Pradesh',
    price_per_night: 5600,
    status: 'pending',
    image_urls: ['https://images.unsplash.com/photo-1510798831971-661eb04b3739?auto=format&fit=crop&w=500&q=80'],
  },
];

export default function OwnerDashboard() {
  const user = authStore.getUser();
  const [listings, setListings] = useState<OwnerProperty[]>([]);
  const [loading, setLoading] = useState(true);
  const [reservations, setReservations] = useState<Awaited<ReturnType<typeof ownerManagementApi.reservations>>>([]);
  const [earnings, setEarnings] = useState<OwnerEarnings>({ gross: 0, refunded: 0, net: 0, transactions: [] });
  const [payouts, setPayouts] = useState<{ pending: number; paid: number; commission: number; payouts: Array<{ id:number; booking_id:number; owner_amount:number; status:string }> }>({ pending: 0, paid: 0, commission: 0, payouts: [] });
  const [payoutAccount, setPayoutAccount] = useState<{ configured:boolean; provider:string; linked_account_id?:string; status?:string }>({ configured:false, provider:'razorpay_route' });
  const [offerings, setOfferings] = useState<MarketplaceOffering[]>([]);
  const [offeringBookings, setOfferingBookings] = useState<Awaited<ReturnType<typeof offeringApi.hostBookings>>>([]);

  useEffect(() => {
    Promise.all([
      ownerApi.listProperties().then(setListings).catch(() => setListings([])),
      ownerManagementApi.reservations().then(setReservations).catch(() => setReservations([])),
      earningsApi.owner().then(setEarnings).catch(() => undefined),
      ownerManagementApi.payouts().then(setPayouts).catch(() => undefined),
      ownerManagementApi.payoutAccount().then(setPayoutAccount).catch(() => undefined),
      offeringApi.mine().then(setOfferings).catch(() => setOfferings([])),
      offeringApi.hostBookings().then(setOfferingBookings).catch(() => setOfferingBookings([])),
    ]).finally(() => setLoading(false));
  }, []);

  const visibleListings = listings.length ? listings : examples;
  const liveCount = visibleListings.filter((item) => item.status === 'live').length;
  const pendingCount = visibleListings.filter((item) => item.status === 'pending').length;

  const stats = useMemo(() => [
    ['Live listings', String(liveCount)],
    ['Pending review', String(pendingCount)],
    ['Reservations', String(reservations.length)],
    ['Avg. rating', '4.91'],
  ], [liveCount, pendingCount, reservations.length]);

  return (
    <main className="dashboard">
      <aside className="sidebar">
        <Link className="brand" to="/">Nestora</Link>
        <strong>Owner Studio</strong>
        <nav>
          <a className="selected"><Home />Overview</a>
          <a><CalendarDays />Reservations</a>
          <a><BarChart3 />Performance</a>
          <a><WalletCards />Earnings</a>
        </nav>
      </aside>

      <section className="dash-content">
        <div className="dash-head">
          <div>
            <span className="eyebrow">Owner dashboard</span>
            <h1>Good morning, {user?.full_name ?? 'Owner'}</h1>
            <p>Manage listing quality, moderation status, pricing and guest trust from one place.</p>
          </div>
          <div className="dash-actions">
            <Link to="/owner/properties/new" className="primary inline"><Plus />Add property</Link>
            <Link to="/owner/offerings/new" className="ghost dark"><Plus />Add service / experience</Link>
          </div>
        </div>

        <div className="stats">
          {stats.map(([label, value]) => (
            <div className="stat" key={label}>
              <small>{label}</small>
              <strong>{value}</strong>
            </div>
          ))}
        </div>

        <div className="panel">
          <div className="section-head">
            <div>
              <h2>Your listings</h2>
              <p>{loading ? 'Loading your properties…' : listings.length ? 'Loaded from PostgreSQL.' : 'Showing example listings until you add your first property.'}</p>
            </div>
          </div>

          <div className="owner-listing-grid">
            {visibleListings.map((item, index) => {
              const rawImage = item.image_urls?.[0];
              const image = rawImage
                ? rawImage.startsWith('/uploads') ? 'http://localhost:8000' + rawImage : rawImage
                : 'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=500&q=80';

              return (
                <article className="owner-listing-card" key={item.id}>
                  <img src={image} alt={item.title} />
                  <div>
                    <div className="owner-listing-title">
                      <div>
                        <strong>{item.title}</strong>
                        <small>{item.city}, {item.state}</small>
                      </div>
                      <span className={'listing-status ' + item.status}>{item.status}</span>
                    </div>
                    <div className="owner-listing-meta">
                      <span>₹{Number(item.price_per_night).toLocaleString('en-IN')}/night</span>
                      <span><Star size={14} fill="currentColor"/> {index === 0 ? '4.93' : 'New'}</span>
                      <span>{index === 0 ? '184 reviews' : 'Awaiting approval'}</span>
                    </div>
                    {item.rejection_reason && <div className="auth-error">{item.rejection_reason}</div>}
                    <div className="owner-listing-actions">
                      <Link className="ghost dark" to={'/owner/properties/' + item.id + '/edit'}>Edit details</Link>
                      <Link className="ghost dark" to={'/owner/properties/' + item.id + '/edit'}>Manage photos</Link>
                      <Link className="ghost dark" to={'/owner/properties/' + item.id + '/edit'}>Availability</Link>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        </div>

        <div className="panel owner-reservations-panel">
          <div className="section-head">
            <div>
              <h2>Reservations</h2>
              <p>Upcoming and recent reservations across your PostgreSQL listings.</p>
            </div>
          </div>

          {reservations.length === 0 ? (
            <p>No reservations yet.</p>
          ) : (
            <div className="reservation-table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Property</th>
                    <th>Guest</th>
                    <th>Dates</th>
                    <th>Guests</th>
                    <th>Status</th>
                    <th>Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {reservations.map((reservation) => (
                    <tr key={reservation.booking_id}>
                      <td>{reservation.property_title}</td>
                      <td>{reservation.guest_name}</td>
                      <td>{reservation.check_in} → {reservation.check_out}</td>
                      <td>{reservation.guest_count}</td>
                      <td>
                        <span className={'booking-status ' + reservation.status}>{reservation.status}</span>
                        {reservation.status === 'requested' && (
                          <div className="table-request-actions">
                            <button className="primary inline" onClick={async()=>{await ownerManagementApi.acceptBookingRequest(reservation.booking_id); window.location.reload();}}>Accept</button>
                            <button className="ghost dark" onClick={async()=>{await ownerManagementApi.declineBookingRequest(reservation.booking_id); window.location.reload();}}>Decline</button>
                          </div>
                        )}
                      </td>
                      <td>₹{Number(reservation.total_amount).toLocaleString('en-IN')}<br/><Link className="table-link" to={'/messages/' + reservation.booking_id}>Message guest</Link></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>


        <div className="panel">
          <div className="section-head">
            <div><h2>Services & experiences</h2><p>Host-led inventory uses the same moderation and request/instant-book model.</p></div>
            <Link className="ghost dark" to="/owner/offerings/new">Create new</Link>
          </div>
          {offerings.length === 0 ? <p>No services or experiences yet.</p> : (
            <div className="owner-listing-grid">
              {offerings.map((item) => {
                const raw = item.image_urls?.[0];
                const image = raw ? (raw.startsWith('/uploads') ? 'http://localhost:8000' + raw : raw) : 'https://images.unsplash.com/photo-1528715471579-d1bcf0ba5e83?auto=format&fit=crop&w=500&q=80';
                return (
                  <article className="owner-listing-card" key={'offering-' + item.id}>
                    <img src={image} alt={item.title}/>
                    <div>
                      <div className="owner-listing-title">
                        <div><strong>{item.title}</strong><small>{item.kind} · {item.city}, {item.state}</small></div>
                        <span className={'listing-status ' + item.status}>{item.status}</span>
                      </div>
                      <div className="owner-listing-meta">
                        <span>₹{Number(item.price).toLocaleString('en-IN')} / {item.pricing_unit.replace('_',' ')}</span>
                        <span>{item.duration_minutes} min</span>
                        <span>{item.instant_book ? 'Instant book' : 'Request to book'}</span>
                      </div>
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </div>

        <div className="panel">
          <div className="section-head"><div><h2>Service & experience reservations</h2><p>Accept or decline host-approval requests here.</p></div></div>
          {offeringBookings.length === 0 ? <p>No reservations yet.</p> : (
            <div className="reservation-table-wrap">
              <table>
                <thead><tr><th>Offering</th><th>Guest</th><th>When</th><th>Status</th><th>Payment</th><th>Total</th><th></th></tr></thead>
                <tbody>
                  {offeringBookings.map((booking)=>(
                    <tr key={'ob-' + booking.id}>
                      <td>{booking.title}<br/><small>{booking.kind}</small></td>
                      <td>{booking.guest_name}</td>
                      <td>{new Date(booking.scheduled_at).toLocaleString('en-IN')}</td>
                      <td><span className={'booking-status ' + booking.status}>{booking.status}</span></td>
                      <td>{booking.payment_status}</td>
                      <td>₹{Number(booking.total_amount).toLocaleString('en-IN')}</td>
                      <td>{booking.status === 'requested' && (
                        <div className="moderation-actions">
                          <button className="primary inline" onClick={async()=>{await offeringApi.acceptRequest(booking.id); window.location.reload();}}>Accept</button>
                          <button className="ghost dark" onClick={async()=>{await offeringApi.declineRequest(booking.id); window.location.reload();}}>Decline</button>
                        </div>
                      )}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="panel">
          <div className="section-head"><div><h2>Earnings</h2><p>Paid booking revenue minus recorded refunds.</p></div></div>
          <div className="earnings-summary">
            <div><small>Gross</small><strong>₹{Number(earnings.gross).toLocaleString('en-IN')}</strong></div>
            <div><small>Refunded</small><strong>₹{Number(earnings.refunded).toLocaleString('en-IN')}</strong></div>
            <div><small>Net</small><strong>₹{Number(earnings.net).toLocaleString('en-IN')}</strong></div>
          </div>
        </div>

        <div className="panel">
          <div className="section-head"><div><h2>Payout account</h2><p>Razorpay Route destination used for automatic owner-bank settlement.</p></div></div>
          <div className={payoutAccount.configured ? "auth-success" : "auth-error"}>
            {payoutAccount.configured
              ? 'Connected to ' + payoutAccount.provider + ' · ' + payoutAccount.linked_account_id
              : 'Not connected. Complete Razorpay Route linked-account onboarding before automatic payouts can be sent.'}
          </div>
        </div>

        <div className="panel">
          <div className="section-head"><div><h2>Owner payouts</h2><p>Accommodation revenue after Nestora commission and refund adjustments.</p></div></div>
          <div className="earnings-summary">
            <div><small>Awaiting payout</small><strong>₹{Number(payouts.pending).toLocaleString('en-IN')}</strong></div>
            <div><small>Paid out</small><strong>₹{Number(payouts.paid).toLocaleString('en-IN')}</strong></div>
            <div><small>Platform commission</small><strong>₹{Number(payouts.commission).toLocaleString('en-IN')}</strong></div>
          </div>
        </div>

        <NotificationsPanel />
      </section>
    </main>
  );
}

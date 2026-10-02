import { useEffect, useMemo, useState } from 'react';
import { BarChart3, CalendarDays, Home, Plus, Star, WalletCards } from 'lucide-react';
import { Link } from 'react-router-dom';
import { authStore } from '../lib/auth';
import { ownerApi, type OwnerProperty } from '../lib/api';

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

  useEffect(() => {
    ownerApi.listProperties()
      .then(setListings)
      .catch(() => setListings([]))
      .finally(() => setLoading(false));
  }, []);

  const visibleListings = listings.length ? listings : examples;
  const liveCount = visibleListings.filter((item) => item.status === 'live').length;
  const pendingCount = visibleListings.filter((item) => item.status === 'pending').length;

  const stats = useMemo(() => [
    ['Live listings', String(liveCount)],
    ['Pending review', String(pendingCount)],
    ['Example bookings', '14'],
    ['Avg. rating', '4.91'],
  ], [liveCount, pendingCount]);

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
          <Link to="/owner/properties/new" className="primary inline"><Plus />Add property</Link>
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
      </section>
    </main>
  );
}

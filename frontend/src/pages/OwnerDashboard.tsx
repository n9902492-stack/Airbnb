import { BarChart3, CalendarDays, Home, Plus, WalletCards } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function OwnerDashboard() {
  const stats = [
    ['Active listings', '6'],
    ['Upcoming stays', '14'],
    ['This month', '₹1,84,200'],
    ['Avg. rating', '4.91'],
  ];

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
            <h1>Good morning, Aarav</h1>
            <p>Manage your homes, reservations and guest experience from one place.</p>
          </div>
          <button className="primary inline"><Plus />Add property</button>
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
              <p>Keep property details complete to build guest trust.</p>
            </div>
          </div>
          <table>
            <thead>
              <tr><th>Property</th><th>Status</th><th>Next booking</th><th>Occupancy</th></tr>
            </thead>
            <tbody>
              <tr><td>Cedar Glass House</td><td><span className="status">Live</span></td><td>8 Oct 2026</td><td>82%</td></tr>
              <tr><td>Pine Ridge Cabin</td><td><span className="status">Live</span></td><td>11 Oct 2026</td><td>74%</td></tr>
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
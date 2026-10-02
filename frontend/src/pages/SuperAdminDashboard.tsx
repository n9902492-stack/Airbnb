import { Building2, Flag, LayoutDashboard, Shield, Users } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function SuperAdminDashboard() {
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
            <p>Moderate the marketplace, protect users and keep operations healthy.</p>
          </div>
        </div>
        <div className="stats">
          <div className="stat"><small>Total users</small><strong>12,480</strong></div>
          <div className="stat"><small>Verified owners</small><strong>1,286</strong></div>
          <div className="stat"><small>Live listings</small><strong>3,942</strong></div>
          <div className="stat"><small>Open reports</small><strong>18</strong></div>
        </div>
        <div className="panel">
          <h2>Needs attention</h2>
          <div className="moderation-row">
            <div><strong>7 listings awaiting approval</strong><p>New property submissions need moderation.</p></div>
            <button className="ghost dark">Review</button>
          </div>
          <div className="moderation-row">
            <div><strong>4 identity checks flagged</strong><p>Manual verification is required before owner activation.</p></div>
            <button className="ghost dark">Open</button>
          </div>
        </div>
      </section>
    </main>
  );
}
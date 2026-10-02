import { Heart, Home, LogOut, Suitcase, UserRound } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { authStore } from '../lib/auth';

export default function UserDashboard() {
  const navigate = useNavigate();
  const user = authStore.getUser();

  function signOut() {
    authStore.clear();
    navigate('/auth');
  }

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
            <p>Your trips, saved stays and account details will live here.</p>
          </div>
        </div>
        <div className="stats">
          <div className="stat"><small>Upcoming trips</small><strong>0</strong></div>
          <div className="stat"><small>Saved homes</small><strong>0</strong></div>
          <div className="stat"><small>Completed trips</small><strong>0</strong></div>
          <div className="stat"><small>Reviews</small><strong>0</strong></div>
        </div>
      </section>
    </main>
  );
}

import { FormEvent, useEffect, useMemo, useState } from 'react';
import { Heart, Menu, Search, ShieldCheck, Sparkles, UserRound } from 'lucide-react';
import { Link } from 'react-router-dom';

import { authStore } from '../lib/auth';
import { propertyApi, wishlistApi, type PublicProperty } from '../lib/api';

const categories = ['All stays','Mountain','Tropical','City','Countryside','Design homes'];

export default function HomePage() {
  const user = authStore.getUser();
  const [properties, setProperties] = useState<PublicProperty[]>([]);
  const [wishlist, setWishlist] = useState<Set<number>>(new Set());
  const [query, setQuery] = useState('');
  const [guests, setGuests] = useState(1);
  const [category, setCategory] = useState('All stays');
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');

  async function load(searchQuery = query, selectedCategory = category) {
    setLoading(true);
    setMessage('');
    try {
      const items = await propertyApi.search({
        q: searchQuery || undefined,
        category: selectedCategory === 'All stays' ? undefined : selectedCategory.replace('Design homes', 'Design home'),
        guests,
      });
      setProperties(items);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Unable to load stays');
      setProperties([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load('', 'All stays');
    if (user?.role === 'user') {
      wishlistApi.list()
        .then((items) => setWishlist(new Set(items.map((item) => item.property_id))))
        .catch(() => setWishlist(new Set()));
    }
  }, []);

  async function search(event: FormEvent) {
    event.preventDefault();
    await load();
    document.getElementById('stays')?.scrollIntoView({ behavior: 'smooth' });
  }

  async function chooseCategory(next: string) {
    setCategory(next);
    await load(query, next);
  }

  async function toggleWishlist(propertyId: number) {
    if (!user) {
      window.location.href = '/auth';
      return;
    }
    if (user.role !== 'user') return;

    const next = new Set(wishlist);
    if (next.has(propertyId)) {
      await wishlistApi.remove(propertyId);
      next.delete(propertyId);
    } else {
      await wishlistApi.add(propertyId);
      next.add(propertyId);
    }
    setWishlist(next);
  }

  const title = useMemo(
    () => query ? 'Search results' : 'Homes worth travelling for',
    [query],
  );

  return <main>
    <header className="topbar">
      <Link to="/" className="brand">Nestora</Link>
      <nav className="navlinks">
        <a href="#stays">Stays</a>
        <a href="#why">Why Nestora</a>
        <Link to="/owner">List your home</Link>
      </nav>
      <div className="header-actions">
        <button className="ghost">₹ INR</button>
        <Link to={user ? (user.role === 'owner' ? '/owner' : user.role === 'super_admin' ? '/super-admin' : '/user') : '/auth'} className="profile-btn">
          <Menu size={18}/><UserRound size={20}/>
        </Link>
      </div>
    </header>

    <section className="hero">
      <div className="hero-copy">
        <span className="eyebrow"><Sparkles size={16}/> Curated stays, made personal</span>
        <h1>Find a place that feels less like a booking, more like a memory.</h1>
        <p>Discover verified homes with richer details, transparent pricing and hosts who show you exactly what to expect.</p>
      </div>

      <form className="search-shell search-live" onSubmit={search}>
        <label>
          <small>Where</small>
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="City, state or property" />
        </label>
        <label>
          <small>Guests</small>
          <select value={guests} onChange={(e) => setGuests(Number(e.target.value))}>
            {Array.from({length:12},(_,i)=><option value={i+1} key={i+1}>{i+1} guest{i ? 's' : ''}</option>)}
          </select>
        </label>
        <div><small>Check in</small><strong>Select on property</strong></div>
        <div><small>Check out</small><strong>Select on property</strong></div>
        <button className="search-btn" type="submit"><Search size={20}/></button>
      </form>
    </section>

    <section className="category-row">
      {categories.map((item) => (
        <button
          className={category === item ? 'active-chip' : 'chip'}
          key={item}
          onClick={() => void chooseCategory(item)}
        >
          {item}
        </button>
      ))}
    </section>

    <section id="stays" className="section">
      <div className="section-head">
        <div><span className="eyebrow">Live marketplace</span><h2>{title}</h2></div>
        <span>{loading ? 'Loading…' : properties.length + ' stays'}</span>
      </div>

      {message && <div className="auth-error">{message}</div>}

      {properties.length === 0 && !loading ? (
        <div className="empty-state">
          <Search size={34}/>
          <h3>No live stays match this search</h3>
          <p>Try another place, category or guest count.</p>
        </div>
      ) : (
        <div className="property-grid">
          {properties.map((p) => {
            const image = p.image_urls?.[0]
              ? p.image_urls[0].startsWith('/uploads')
                ? 'http://localhost:8000' + p.image_urls[0]
                : p.image_urls[0]
              : 'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=900&q=80';

            return (
              <article className="card" key={p.id}>
                <div className="card-image">
                  <Link to={'/stays/' + p.id}><img src={image} alt={p.title}/></Link>
                  <span className="pill">{p.category}</span>
                  <button
                    className={wishlist.has(p.id) ? 'wishlist-button active' : 'wishlist-button'}
                    onClick={() => void toggleWishlist(p.id)}
                    aria-label="Save property"
                  >
                    <Heart size={18} fill={wishlist.has(p.id) ? 'currentColor' : 'none'}/>
                  </button>
                </div>
                <Link className="card-body" to={'/stays/' + p.id}>
                  <div className="card-title-row"><h3>{p.title}</h3><span>Verified</span></div>
                  <p>{p.city}, {p.state}</p>
                  <strong>₹{Number(p.price_per_night).toLocaleString('en-IN')} <span>/ night</span></strong>
                </Link>
              </article>
            );
          })}
        </div>
      )}
    </section>

    <section id="why" className="feature-band">
      <div><ShieldCheck/><h3>Verified details</h3><p>Owners provide room-by-room information, amenities, house rules, access notes and clear photos.</p></div>
      <div><Sparkles/><h3>Better discovery</h3><p>Search live PostgreSQL listings by destination, category and guest capacity.</p></div>
      <div><UserRound/><h3>Three focused panels</h3><p>Separate experiences for travellers, property owners and the platform super admin.</p></div>
    </section>
  </main>;
}

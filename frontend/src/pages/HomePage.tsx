import { Link } from 'react-router-dom';
import { Menu, Search, ShieldCheck, Sparkles, Star, UserRound } from 'lucide-react';
import { properties } from '../data';

const categories = ['All stays','Mountain','Tropical','City','Countryside','Design homes'];

export default function HomePage() {
  return <main>
    <header className="topbar">
      <Link to="/" className="brand">Nestora</Link>
      <nav className="navlinks"><a href="#stays">Stays</a><a href="#why">Why Nestora</a><Link to="/owner">List your home</Link></nav>
      <div className="header-actions"><button className="ghost">₹ INR</button><Link to="/auth" className="profile-btn"><Menu size={18}/><UserRound size={20}/></Link></div>
    </header>

    <section className="hero">
      <div className="hero-copy">
        <span className="eyebrow"><Sparkles size={16}/> Curated stays, made personal</span>
        <h1>Find a place that feels less like a booking, more like a memory.</h1>
        <p>Discover verified homes with richer details, transparent pricing and hosts who show you exactly what to expect.</p>
      </div>
      <div className="search-shell">
        <div><small>Where</small><strong>Search destinations</strong></div>
        <div><small>Check in</small><strong>Add dates</strong></div>
        <div><small>Check out</small><strong>Add dates</strong></div>
        <div><small>Guests</small><strong>Add guests</strong></div>
        <button className="search-btn"><Search size={20}/></button>
      </div>
    </section>

    <section className="category-row">{categories.map((c,i)=><button className={i===0?'active-chip':'chip'} key={c}>{c}</button>)}</section>

    <section id="stays" className="section">
      <div className="section-head"><div><span className="eyebrow">Handpicked</span><h2>Homes worth travelling for</h2></div><a href="#">Explore all</a></div>
      <div className="property-grid">
        {properties.map(p => <Link className="card" to={`/stays/${p.id}`} key={p.id}>
          <div className="card-image"><img src={p.image} alt={p.title}/><span className="pill">{p.category}</span></div>
          <div className="card-body"><div className="card-title-row"><h3>{p.title}</h3><span><Star size={15} fill="currentColor"/> {p.rating}</span></div><p>{p.location}</p><strong>₹{p.pricePerNight.toLocaleString('en-IN')} <span>/ night</span></strong></div>
        </Link>)}
      </div>
    </section>

    <section id="why" className="feature-band">
      <div><ShieldCheck/><h3>Verified details</h3><p>Owners provide room-by-room information, amenities, house rules, access notes and clear photos.</p></div>
      <div><Sparkles/><h3>Better discovery</h3><p>Search by trip mood and property character, not only city and price.</p></div>
      <div><UserRound/><h3>Three focused panels</h3><p>Separate experiences for travellers, property owners and the platform super admin.</p></div>
    </section>
  </main>
}
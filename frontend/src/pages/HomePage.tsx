import { FormEvent, useEffect, useMemo, useState } from 'react';
import {
  Heart,
  Home,
  MapPin,
  Menu,
  Search,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  UserRound,
} from 'lucide-react';
import { Link } from 'react-router-dom';

import SearchMap from '../components/SearchMap';
import { authStore } from '../lib/auth';
import {
  offeringApi,
  propertyApi,
  wishlistApi,
  type MarketplaceOffering,
  type PublicProperty,
} from '../lib/api';

type DiscoveryTab = 'homes' | 'services' | 'experiences';

const homeCategories = ['All stays', 'Mountain', 'Tropical', 'City', 'Countryside', 'Design homes'];
const serviceCategories = ['All services', 'Chef', 'Photography', 'Massage', 'Wellness', 'Beauty'];
const experienceCategories = ['All experiences', 'Food', 'Culture', 'Outdoors', 'Tours', 'Workshops'];

export default function HomePage() {
  const user = authStore.getUser();
  const [tab, setTab] = useState<DiscoveryTab>('homes');
  const [properties, setProperties] = useState<PublicProperty[]>([]);
  const [offerings, setOfferings] = useState<MarketplaceOffering[]>([]);
  const [wishlist, setWishlist] = useState<Set<number>>(new Set());
  const [query, setQuery] = useState('');
  const [guests, setGuests] = useState(1);
  const [category, setCategory] = useState('All stays');
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [showMap, setShowMap] = useState(false);

  const [minPrice, setMinPrice] = useState<number | ''>('');
  const [maxPrice, setMaxPrice] = useState<number | ''>('');
  const [bedrooms, setBedrooms] = useState<number | ''>('');
  const [beds, setBeds] = useState<number | ''>('');
  const [bathrooms, setBathrooms] = useState<number | ''>('');
  const [propertyType, setPropertyType] = useState('');
  const [instantBook, setInstantBook] = useState(false);
  const [guestFavorite, setGuestFavorite] = useState(false);
  const [amenities, setAmenities] = useState<string[]>([]);

  const categories = tab === 'homes'
    ? homeCategories
    : tab === 'services'
      ? serviceCategories
      : experienceCategories;

  async function load(
    searchQuery = query,
    selectedCategory = category,
    bounds?: { min_lat:number; max_lat:number; min_lng:number; max_lng:number },
  ) {
    setLoading(true);
    setMessage('');

    try {
      if (tab === 'homes') {
        const items = await propertyApi.search({
          q: searchQuery || undefined,
          category: selectedCategory === 'All stays'
            ? undefined
            : selectedCategory.replace('Design homes', 'Design home'),
          guests,
          bedrooms: bedrooms === '' ? undefined : bedrooms,
          beds: beds === '' ? undefined : beds,
          bathrooms: bathrooms === '' ? undefined : bathrooms,
          property_type: propertyType || undefined,
          instant_book: instantBook || undefined,
          guest_favorite: guestFavorite || undefined,
          amenities: amenities.length ? amenities : undefined,
          min_price: minPrice === '' ? undefined : minPrice,
          max_price: maxPrice === '' ? undefined : maxPrice,
          ...bounds,
        });
        setProperties(items);
        setOfferings([]);
      } else {
        const kind = tab === 'services' ? 'service' : 'experience';
        const allLabel = tab === 'services' ? 'All services' : 'All experiences';
        const items = await offeringApi.list({
          kind,
          q: searchQuery || undefined,
          category: selectedCategory === allLabel ? undefined : selectedCategory,
        });
        setOfferings(items);
        setProperties([]);
      }
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Unable to load marketplace');
      setProperties([]);
      setOfferings([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load('', tab === 'homes' ? 'All stays' : tab === 'services' ? 'All services' : 'All experiences');
    if (user?.role === 'user') {
      wishlistApi.list()
        .then((items) => setWishlist(new Set(items.map((item) => item.property_id))))
        .catch(() => setWishlist(new Set()));
    }
  }, [tab]);

  function switchTab(next: DiscoveryTab) {
    setTab(next);
    setCategory(
      next === 'homes'
        ? 'All stays'
        : next === 'services'
          ? 'All services'
          : 'All experiences',
    );
    setShowFilters(false);
    setShowMap(false);
  }

  async function search(event: FormEvent) {
    event.preventDefault();
    await load();
    document.getElementById('marketplace-results')?.scrollIntoView({ behavior: 'smooth' });
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

  const title = useMemo(() => {
    if (query) return 'Search results';
    if (tab === 'services') return 'Services that come to you';
    if (tab === 'experiences') return 'Experiences worth making time for';
    return 'Homes worth travelling for';
  }, [query, tab]);

  const resultCount = tab === 'homes' ? properties.length : offerings.length;

  return <main>
    <header className="topbar marketplace-topbar">
      <Link to="/" className="brand">Nestora</Link>

      <nav className="marketplace-tabs" aria-label="Marketplace">
        <button className={tab === 'homes' ? 'active' : ''} onClick={() => switchTab('homes')}>
          <Home size={18}/>Homes
        </button>
        <button className={tab === 'services' ? 'active' : ''} onClick={() => switchTab('services')}>
          <ShieldCheck size={18}/>Services
        </button>
        <button className={tab === 'experiences' ? 'active' : ''} onClick={() => switchTab('experiences')}>
          <Sparkles size={18}/>Experiences
        </button>
      </nav>

      <div className="header-actions">
        <Link className="host-entry-link" to={user?.role === 'owner' || user?.role === 'super_admin' ? '/owner' : '/auth'}>
          Become a host
        </Link>
        <button className="ghost">₹ INR</button>
        <Link
          to={user ? (user.role === 'owner' ? '/owner' : user.role === 'super_admin' ? '/super-admin' : '/user') : '/auth'}
          className="profile-btn"
        >
          <Menu size={18}/><UserRound size={20}/>
        </Link>
      </div>
    </header>

    <section className="hero marketplace-hero">
      <div className="hero-copy">
        <span className="eyebrow"><Sparkles size={16}/> One trip, one connected marketplace</span>
        <h1>
          {tab === 'homes'
            ? 'Stay somewhere with a story.'
            : tab === 'services'
              ? 'Bring trusted local services into your trip.'
              : 'Do something you’ll remember after checkout.'}
        </h1>
        <p>
          {tab === 'homes'
            ? 'Discover verified homes, transparent prices, rich room details and hosts you can understand before booking.'
            : tab === 'services'
              ? 'Book curated chefs, photographers, wellness and other host-led services.'
              : 'Explore host-led activities, culture, food, workshops and outdoor experiences.'}
        </p>
      </div>

      <form className="search-shell search-live marketplace-search" onSubmit={search}>
        <label>
          <small>Where</small>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={tab === 'homes' ? 'City, state or property' : 'City or activity'}
          />
        </label>
        <label>
          <small>Guests</small>
          <select value={guests} onChange={(e) => setGuests(Number(e.target.value))}>
            {Array.from({ length: 12 }, (_, i) => (
              <option value={i + 1} key={i + 1}>{i + 1} guest{i ? 's' : ''}</option>
            ))}
          </select>
        </label>
        <div>
          <small>{tab === 'homes' ? 'Dates' : 'When'}</small>
          <strong>{tab === 'homes' ? 'Choose on listing' : 'Choose after opening'}</strong>
        </div>
        <button className="search-btn" type="submit"><Search size={20}/></button>
      </form>
    </section>

    <section className="category-toolbar">
      <div className="category-row marketplace-category-row">
        {categories.map((item) => (
          <button
            className={category === item ? 'active-chip' : 'chip'}
            key={item}
            onClick={() => void chooseCategory(item)}
          >
            {item}
          </button>
        ))}
      </div>

      {tab === 'homes' && (
        <div className="discovery-controls">
          <button className="filter-button" onClick={() => setShowFilters((v) => !v)}>
            <SlidersHorizontal size={17}/>Filters
          </button>
          <button className="filter-button" onClick={() => setShowMap((v) => !v)}>
            <MapPin size={17}/>{showMap ? 'Show list' : 'Show map'}
          </button>
        </div>
      )}
    </section>

    {tab === 'homes' && showFilters && (
      <section className="advanced-filters">
        <label>Min price<input type="number" value={minPrice} onChange={(e) => setMinPrice(e.target.value ? Number(e.target.value) : '')}/></label>
        <label>Max price<input type="number" value={maxPrice} onChange={(e) => setMaxPrice(e.target.value ? Number(e.target.value) : '')}/></label>
        <label>Bedrooms<input type="number" min="0" value={bedrooms} onChange={(e) => setBedrooms(e.target.value ? Number(e.target.value) : '')}/></label>
        <label>Beds<input type="number" min="1" value={beds} onChange={(e) => setBeds(e.target.value ? Number(e.target.value) : '')}/></label>
        <label>Bathrooms<input type="number" min="1" value={bathrooms} onChange={(e) => setBathrooms(e.target.value ? Number(e.target.value) : '')}/></label>
        <label>Property type
          <select value={propertyType} onChange={(e) => setPropertyType(e.target.value)}>
            <option value="">Any</option>
            <option>Entire home</option>
            <option>Private room</option>
            <option>Villa</option>
            <option>Cabin</option>
            <option>Apartment</option>
          </select>
        </label>

        <label className="toggle-filter"><input type="checkbox" checked={instantBook} onChange={(e)=>setInstantBook(e.target.checked)}/>Instant Book</label>
        <label className="toggle-filter"><input type="checkbox" checked={guestFavorite} onChange={(e)=>setGuestFavorite(e.target.checked)}/>Guest Favorite</label>

        {['Wi-Fi','Kitchen','Parking','Pool','Air conditioning'].map((item)=>(
          <label className="toggle-filter" key={item}>
            <input
              type="checkbox"
              checked={amenities.includes(item)}
              onChange={(e)=>setAmenities((current)=>e.target.checked ? [...current,item] : current.filter((x)=>x!==item))}
            />
            {item}
          </label>
        ))}

        <button className="primary inline" onClick={()=>void load()}>Apply filters</button>
      </section>
    )}

    <section id="marketplace-results" className={showMap && tab === 'homes' ? 'section discovery-map-layout' : 'section'}>
      <div className="results-column">
        <div className="section-head">
          <div><span className="eyebrow">Live marketplace</span><h2>{title}</h2></div>
          <span>{loading ? 'Loading…' : resultCount + ' results'}</span>
        </div>

        {message && <div className="auth-error">{message}</div>}

        {resultCount === 0 && !loading ? (
          <div className="empty-state">
            <Search size={34}/>
            <h3>No matches yet</h3>
            <p>Try another place, category or filter.</p>
          </div>
        ) : tab === 'homes' ? (
          <div className={showMap ? 'property-grid compact-property-grid' : 'property-grid'}>
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
                    <div className="card-badge-stack">
                      {p.guest_favorite && <span className="pill favorite-pill">Guest Favorite</span>}
                      <span className="pill">{p.booking_mode === 'request' ? 'Request to book' : 'Instant book'}</span>
                    </div>
                    <button
                      className={wishlist.has(p.id) ? 'wishlist-button active' : 'wishlist-button'}
                      onClick={() => void toggleWishlist(p.id)}
                      aria-label="Save property"
                    >
                      <Heart size={18} fill={wishlist.has(p.id) ? 'currentColor' : 'none'}/>
                    </button>
                  </div>
                  <Link className="card-body" to={'/stays/' + p.id}>
                    <div className="card-title-row"><h3>{p.title}</h3><span>{p.category}</span></div>
                    <p>{p.city}, {p.state}</p>
                    <small>{p.bedrooms} bedrooms · {p.beds} beds · {p.bathrooms} baths</small>
                    <strong>₹{Number(p.price_per_night).toLocaleString('en-IN')} <span>/ night</span></strong>
                  </Link>
                </article>
              );
            })}
          </div>
        ) : (
          <div className="offering-grid">
            {offerings.map((item) => {
              const image = item.image_urls?.[0] || 'https://images.unsplash.com/photo-1528715471579-d1bcf0ba5e83?auto=format&fit=crop&w=900&q=80';
              return (
                <article className="offering-card" key={item.id}>
                  <Link to={'/offerings/' + item.id} className="offering-card-image">
                    <img src={image} alt={item.title}/>
                    <span className="pill">{item.instant_book ? 'Instant book' : 'Request'}</span>
                  </Link>
                  <Link to={'/offerings/' + item.id} className="card-body">
                    <span className="eyebrow">{item.category}</span>
                    <h3>{item.title}</h3>
                    <p>{item.city}, {item.state}</p>
                    <small>{item.duration_minutes} min · up to {item.capacity} guests</small>
                    <strong>₹{Number(item.price).toLocaleString('en-IN')} <span>/ {item.pricing_unit.replace('_',' ')}</span></strong>
                  </Link>
                </article>
              );
            })}
          </div>
        )}
      </div>

      {showMap && tab === 'homes' && (
        <aside className="map-column">
          <SearchMap
            properties={properties}
            onBoundsChange={(bounds) => void load(query, category, bounds)}
          />
        </aside>
      )}
    </section>

    <section id="why" className="feature-band">
      <div><ShieldCheck/><h3>Verified marketplace</h3><p>Listings and host-led offerings pass through Super Admin moderation before going live.</p></div>
      <div><Sparkles/><h3>Flexible booking</h3><p>Inventory can use Instant Book or host approval while staying on the same payment pipeline.</p></div>
      <div><UserRound/><h3>Connected trip</h3><p>Homes, optional transfers, services, experiences, messages, invoices and payouts stay tied to one account.</p></div>
    </section>
  </main>;
}

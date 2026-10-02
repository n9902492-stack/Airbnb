import { ArrowLeft, BedDouble, House, MapPin, ShieldCheck, Star, Users } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import { properties } from '../data';

export default function PropertyPage() {
  const { id } = useParams();
  const p = properties.find(x => x.id === Number(id)) ?? properties[0];
  return <main className="detail-page">
    <div className="detail-top"><Link to="/" className="back"><ArrowLeft size={18}/> Back to stays</Link><span className="brand">Nestora</span></div>
    <div className="detail-heading"><div><span className="eyebrow">Hosted by {p.host}</span><h1>{p.title}</h1><p><MapPin size={17}/>{p.location}</p></div><div className="rating"><Star fill="currentColor" size={18}/> {p.rating} · {p.reviews} reviews</div></div>
    <div className="gallery"><img className="main-photo" src={p.images[0]} alt=""/>{p.images.slice(1).map((x,i)=><img key={i} src={x} alt=""/>)}</div>
    <div className="detail-layout">
      <section>
        <div className="facts"><span><Users/> {p.guests} guests</span><span><House/> {p.bedrooms} bedrooms</span><span><BedDouble/> {p.beds} beds</span></div>
        <p className="lead">{p.description}</p>
        <hr/>
        <h2>What makes this home special</h2>
        <div className="highlight-list">{p.highlights.map(x=><div key={x}><ShieldCheck size={19}/><span>{x}</span></div>)}</div>
        <h2>Amenities</h2>
        <div className="amenity-grid">{p.amenities.map(x=><span key={x}>{x}</span>)}</div>
      </section>
      <aside className="booking-card"><h3>₹{p.pricePerNight.toLocaleString('en-IN')} <span>/ night</span></h3><div className="booking-fields"><div><small>Check in</small><strong>Add date</strong></div><div><small>Check out</small><strong>Add date</strong></div><div className="wide"><small>Guests</small><strong>1 guest</strong></div></div><button className="primary">Reserve</button><small>You won't be charged yet</small></aside>
    </div>
  </main>
}
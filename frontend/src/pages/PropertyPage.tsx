import { FormEvent, useState } from 'react';
import { ArrowLeft, Bath, BedDouble, House, MapPin, ShieldCheck, Star, Users } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import { properties } from '../data';
import { authStore } from '../lib/auth';
import { reviewApi, type ReviewableBooking } from '../lib/api';

export default function PropertyPage() {
  const { id } = useParams();
  const p = properties.find((x) => x.id === Number(id)) ?? properties[0];
  const user = authStore.getUser();
  const [reviewText, setReviewText] = useState('');
  const [reviewRating, setReviewRating] = useState(5);
  const [notice, setNotice] = useState('');
  const [reviewable, setReviewable] = useState<ReviewableBooking[]>([]);
  const [selectedBooking, setSelectedBooking] = useState<number | null>(null);

  async function loadReviewable() {
    if (!user) return;
    try {
      const items = await reviewApi.reviewableBookings();
      const matches = items.filter((item) => item.property_id === p.id);
      setReviewable(matches);
      setSelectedBooking(matches[0]?.id ?? null);
    } catch {
      setReviewable([]);
    }
  }

  async function submitReview(event: FormEvent) {
    event.preventDefault();
    if (!user) {
      setNotice('Sign in first to review a completed stay.');
      return;
    }

    if (!selectedBooking) {
      await loadReviewable();
      setNotice('No completed, unreviewed booking is currently available for this property.');
      return;
    }

    try {
      await reviewApi.create(p.id, {
        booking_id: selectedBooking,
        rating: reviewRating,
        comment: reviewText,
      });
      setNotice('Thanks. Your verified-stay review was published.');
      setReviewText('');
      setReviewable((current) => current.filter((item) => item.id !== selectedBooking));
      setSelectedBooking(null);
    } catch (err) {
      setNotice(err instanceof Error ? err.message : 'Unable to publish review');
    }
  }

  return (
    <main className="detail-page">
      <div className="detail-top">
        <Link to="/" className="back"><ArrowLeft size={18}/> Back to stays</Link>
        <span className="brand">Nestora</span>
      </div>

      <div className="detail-heading">
        <div>
          <span className="eyebrow">Hosted by {p.host}</span>
          <h1>{p.title}</h1>
          <p><MapPin size={17}/>{p.location}</p>
        </div>
        <div className="rating"><Star fill="currentColor" size={18}/> {p.rating} · {p.reviews} reviews</div>
      </div>

      <div className="room-gallery">
        {p.photos.map((photo, index) => (
          <figure className={index === 0 ? 'room-photo room-photo-main' : 'room-photo'} key={photo.label}>
            <img src={photo.url} alt={photo.label + ' at ' + p.title}/>
            <figcaption>{photo.label}</figcaption>
          </figure>
        ))}
      </div>

      <div className="detail-layout">
        <section>
          <div className="facts">
            <span><Users/> {p.guests} guests</span>
            <span><House/> {p.bedrooms} bedrooms</span>
            <span><BedDouble/> {p.beds} beds</span>
            <span><Bath/> {p.baths} bathrooms</span>
          </div>

          <p className="lead">{p.description}</p>
          <hr/>

          <h2>What makes this home special</h2>
          <div className="highlight-list">
            {p.highlights.map((x) => <div key={x}><ShieldCheck size={19}/><span>{x}</span></div>)}
          </div>

          <h2>Amenities</h2>
          <div className="amenity-grid">{p.amenities.map((x) => <span key={x}>{x}</span>)}</div>

          <section className="reviews-section">
            <div className="reviews-head">
              <div>
                <span className="eyebrow">Guest feedback</span>
                <h2><Star fill="currentColor" size={22}/> {p.rating} from {p.reviews} reviews</h2>
              </div>
              <span className="verified-stay-badge">Reviews from completed stays</span>
            </div>

            <div className="review-grid">
              {p.customerReviews.map((review) => (
                <article className="review-card" key={review.id}>
                  <div className="review-card-top">
                    <div className="review-avatar">{review.guestName.charAt(0)}</div>
                    <div>
                      <strong>{review.guestName}</strong>
                      <small>{review.date}</small>
                    </div>
                  </div>
                  <div className="review-stars">
                    {Array.from({ length: 5 }).map((_, index) => (
                      <Star key={index} size={15} fill={index < review.rating ? 'currentColor' : 'none'}/>
                    ))}
                  </div>
                  <p>{review.comment}</p>
                </article>
              ))}
            </div>

            <form className="review-form" onSubmit={submitReview} onFocus={() => void loadReviewable()}>
              <h3>Write a review</h3>
              <p>Only guests with a completed booking will be allowed to publish.</p>
              {user && reviewable.length > 0 && (
                <label>
                  Completed stay
                  <select
                    value={selectedBooking ?? ''}
                    onChange={(e) => setSelectedBooking(Number(e.target.value))}
                  >
                    {reviewable.map((booking) => (
                      <option key={booking.id} value={booking.id}>
                        {booking.check_in} to {booking.check_out}
                      </option>
                    ))}
                  </select>
                </label>
              )}
              <label>
                Rating
                <select value={reviewRating} onChange={(e) => setReviewRating(Number(e.target.value))}>
                  <option value={5}>5 - Excellent</option>
                  <option value={4}>4 - Very good</option>
                  <option value={3}>3 - Good</option>
                  <option value={2}>2 - Fair</option>
                  <option value={1}>1 - Poor</option>
                </select>
              </label>
              <label>
                Your experience
                <textarea value={reviewText} onChange={(e) => setReviewText(e.target.value)} minLength={10} required />
              </label>
              {notice && <div className="auth-success">{notice}</div>}
              <button className="primary inline" type="submit">Submit review</button>
            </form>
          </section>
        </section>

        <aside className="booking-card">
          <h3>₹{p.pricePerNight.toLocaleString('en-IN')} <span>/ night</span></h3>
          <div className="booking-fields">
            <div><small>Check in</small><strong>Add date</strong></div>
            <div><small>Check out</small><strong>Add date</strong></div>
            <div className="wide"><small>Guests</small><strong>1 guest</strong></div>
          </div>
          <button className="primary">Reserve</button>
          <small>You won't be charged yet</small>
        </aside>
      </div>
    </main>
  );
}

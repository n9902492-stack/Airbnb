import { FormEvent, useEffect, useState } from 'react';
import { ArrowLeft, Bath, BedDouble, House, MapPin, ShieldCheck, Star, Users } from 'lucide-react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import AvailabilityCalendar from '../components/AvailabilityCalendar';
import TransferOption from '../components/TransferOption';
import { properties as demoProperties } from '../data';
import { authStore } from '../lib/auth';
import {
  bookingApi,
  propertyApi,
  reviewApi,
  transferApi,
  type PublicProperty,
  type ReviewableBooking,
} from '../lib/api';

type ReviewView = {
  id: number;
  guestName: string;
  rating: number;
  date: string;
  comment: string;
};

type PropertyView = {
  id: number;
  title: string;
  location: string;
  pricePerNight: number;
  rating: number;
  reviews: number;
  guests: number;
  bedrooms: number;
  beds: number;
  baths: number;
  photos: Array<{ label: string; url: string }>;
  description: string;
  amenities: string[];
  highlights: string[];
  host: string;
  hostId: number;
  bookingMode: 'instant' | 'request';
  guestFavorite: boolean;
  customerReviews: ReviewView[];
  latitude: number | null;
  longitude: number | null;
};

function normalizeLiveProperty(
  property: PublicProperty,
  reviewSummary: Awaited<ReturnType<typeof reviewApi.list>>,
): PropertyView {
  const labels = ['Exterior', 'Living room', 'Bedroom', 'Bathroom', 'Kitchen'];
  const fallbackImage =
    'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=85';

  const images = property.image_urls?.length ? property.image_urls : [fallbackImage];

  return {
    id: property.id,
    title: property.title,
    location: property.city + ', ' + property.state,
    pricePerNight: Number(property.price_per_night),
    rating: reviewSummary.average_rating || 0,
    reviews: reviewSummary.review_count,
    guests: property.guests,
    bedrooms: property.bedrooms,
    beds: property.beds,
    baths: property.bathrooms,
    photos: images.map((url, index) => ({
      label: labels[index] ?? 'Property photo',
      url: url.startsWith('/uploads') ? 'http://localhost:8000' + url : url,
    })),
    description: property.description,
    amenities: property.amenities ?? [],
    highlights: [
      'Verified listing details',
      'Owner-managed availability',
      'Secure Nestora booking',
    ],
    host: 'Verified Nestora host',
    hostId: property.owner_id,
    bookingMode: property.booking_mode,
    guestFavorite: property.guest_favorite,
    customerReviews: reviewSummary.reviews.map((review) => ({
      id: review.id,
      guestName: review.guest_name ?? 'Verified guest',
      rating: review.rating,
      date: new Date(review.created_at).toLocaleDateString('en-IN', {
        month: 'long',
        year: 'numeric',
      }),
      comment: review.comment,
    })),
    latitude: property.latitude ?? null,
    longitude: property.longitude ?? null,
  };
}

function normalizeDemoProperty(id: number): PropertyView | null {
  const p = demoProperties.find((item) => item.id === id);
  if (!p) return null;

  return {
    id: p.id,
    title: p.title,
    location: p.location,
    pricePerNight: p.pricePerNight,
    rating: p.rating,
    reviews: p.reviews,
    guests: p.guests,
    bedrooms: p.bedrooms,
    beds: p.beds,
    baths: p.baths,
    photos: p.photos,
    description: p.description,
    amenities: p.amenities,
    highlights: p.highlights,
    host: p.host,
    hostId: 0,
    bookingMode: 'instant',
    guestFavorite: false,
    customerReviews: p.customerReviews,
    latitude: p.latitude,
    longitude: p.longitude,
  };
}

export default function PropertyPage() {
  const { id } = useParams();
  const propertyId = Number(id);
  const navigate = useNavigate();
  const user = authStore.getUser();

  const [p, setProperty] = useState<PropertyView | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadMessage, setLoadMessage] = useState('');

  const [reviewText, setReviewText] = useState('');
  const [reviewRating, setReviewRating] = useState(5);
  const [notice, setNotice] = useState('');
  const [reviewable, setReviewable] = useState<ReviewableBooking[]>([]);
  const [selectedBooking, setSelectedBooking] = useState<number | null>(null);
  const [checkIn, setCheckIn] = useState('');
  const [checkOut, setCheckOut] = useState('');
  const [guestCount, setGuestCount] = useState(1);
  const [bookingMessage, setBookingMessage] = useState('');
  const [bookingBusy, setBookingBusy] = useState(false);

  async function loadProperty() {
    setLoading(true);
    setLoadMessage('');

    try {
      const [property, summary] = await Promise.all([
        propertyApi.get(propertyId),
        reviewApi.list(propertyId),
      ]);
      setProperty(normalizeLiveProperty(property, summary));
    } catch (err) {
      const fallback = normalizeDemoProperty(propertyId);
      if (fallback) {
        setProperty(fallback);
        setLoadMessage('Showing the original demo listing because this sample is not stored in PostgreSQL.');
      } else {
        setProperty(null);
        setLoadMessage(err instanceof Error ? err.message : 'Property not found');
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadProperty();
  }, [propertyId]);

  async function loadReviewable() {
    if (!user || !p) return;

    try {
      const items = await reviewApi.reviewableBookings();
      const matches = items.filter((item) => item.property_id === p.id);
      setReviewable(matches);
      setSelectedBooking(matches[0]?.id ?? null);
    } catch {
      setReviewable([]);
    }
  }

  async function reserveStay() {
    if (!p) return;

    if (!user) {
      navigate('/auth');
      return;
    }

    if (user.role !== 'user') {
      setBookingMessage('Traveller accounts can create reservations.');
      return;
    }

    if (!checkIn || !checkOut) {
      setBookingMessage('Select available check-in and check-out dates first.');
      return;
    }

    setBookingBusy(true);
    setBookingMessage('');

    try {
      const booking = await bookingApi.create({
        property_id: p.id,
        check_in: checkIn,
        check_out: checkOut,
        guest_count: guestCount,
      });

      const rawTransfer = localStorage.getItem('nestora_transfer_selection');
      if (rawTransfer) {
        try {
          const transfer = JSON.parse(rawTransfer);
          if (transfer.propertyId === p.id) {
            await transferApi.createForBooking({
              booking_id: booking.id,
              property_id: p.id,
              direction: transfer.direction,
              place_type: transfer.place_type,
              place_name: transfer.place_name,
              latitude: transfer.latitude,
              longitude: transfer.longitude,
            });
            localStorage.removeItem('nestora_transfer_selection');
          }
        } catch {
          localStorage.removeItem('nestora_transfer_selection');
        }
      }

      if (booking.status === 'requested') {
        setBookingMessage('Request sent to the host. You will be notified if it is accepted, then you can complete payment.');
        return;
      }

      navigate('/checkout/' + booking.id);
    } catch (err) {
      setBookingMessage(err instanceof Error ? err.message : 'Unable to reserve these dates');
    } finally {
      setBookingBusy(false);
    }
  }

  async function submitReview(event: FormEvent) {
    event.preventDefault();
    if (!p) return;

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
      await loadProperty();
    } catch (err) {
      setNotice(err instanceof Error ? err.message : 'Unable to publish review');
    }
  }

  if (loading) {
    return <main className="detail-page"><div className="detail-top"><Link to="/" className="back"><ArrowLeft size={18}/>Back to stays</Link><span className="brand">Nestora</span></div><p>Loading property…</p></main>;
  }

  if (!p) {
    return <main className="detail-page"><div className="detail-top"><Link to="/" className="back"><ArrowLeft size={18}/>Back to stays</Link><span className="brand">Nestora</span></div><div className="auth-error">{loadMessage || 'Property not found'}</div></main>;
  }

  return (
    <main className="detail-page">
      <div className="detail-top">
        <Link to="/" className="back"><ArrowLeft size={18}/> Back to stays</Link>
        <span className="brand">Nestora</span>
      </div>

      {loadMessage && <div className="auth-success">{loadMessage}</div>}

      <div className="detail-heading">
        <div>
          <span className="eyebrow">
            Hosted by {p.host}
            {p.hostId ? <> · <Link className="host-link" to={'/hosts/' + p.hostId}>View profile</Link></> : null}
          </span>
          <h1>{p.title}</h1>
          <p><MapPin size={17}/>{p.location}</p>
        </div>
        <div className="rating">
          {p.guestFavorite && <span className="verified-stay-badge">Guest Favorite</span>}
          <Star fill="currentColor" size={18}/>
          {p.reviews ? p.rating.toFixed(2) + ' · ' + p.reviews + ' reviews' : 'New listing'}
        </div>
      </div>

      <div className="room-gallery">
        {p.photos.slice(0, 5).map((photo, index) => (
          <figure className={index === 0 ? 'room-photo room-photo-main' : 'room-photo'} key={photo.url + index}>
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
            {p.highlights.map((item) => <div key={item}><ShieldCheck size={19}/><span>{item}</span></div>)}
          </div>

          <h2>Amenities</h2>
          <div className="amenity-grid">{p.amenities.map((item) => <span key={item}>{item}</span>)}</div>

          <AvailabilityCalendar
            propertyId={p.id}
            onChange={({ checkIn: nextIn, checkOut: nextOut }) => {
              setCheckIn(nextIn);
              setCheckOut(nextOut);
            }}
          />

          {p.latitude !== null && p.longitude !== null ? (
            <TransferOption
              propertyId={p.id}
              propertyName={p.title}
              latitude={p.latitude}
              longitude={p.longitude}
            />
          ) : (
            <div className="transfer-option">
              <span className="eyebrow">Optional paid transfer</span>
              <h2>Transfer route unavailable</h2>
              <p>The owner must finish the property's map location before pickup/drop-off quotes can be calculated.</p>
            </div>
          )}

          <section className="reviews-section">
            <div className="reviews-head">
              <div>
                <span className="eyebrow">Guest feedback</span>
                <h2>
                  <Star fill="currentColor" size={22}/>
                  {p.reviews ? p.rating.toFixed(2) + ' from ' + p.reviews + ' reviews' : 'No reviews yet'}
                </h2>
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
                    onChange={(event) => setSelectedBooking(Number(event.target.value))}
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
                <select value={reviewRating} onChange={(event) => setReviewRating(Number(event.target.value))}>
                  <option value={5}>5 - Excellent</option>
                  <option value={4}>4 - Very good</option>
                  <option value={3}>3 - Good</option>
                  <option value={2}>2 - Fair</option>
                  <option value={1}>1 - Poor</option>
                </select>
              </label>

              <label>
                Your experience
                <textarea
                  value={reviewText}
                  onChange={(event) => setReviewText(event.target.value)}
                  minLength={10}
                  required
                />
              </label>

              {notice && <div className="auth-success">{notice}</div>}
              <button className="primary inline" type="submit">Submit review</button>
            </form>
          </section>
        </section>

        <aside className="booking-card">
          <h3>₹{p.pricePerNight.toLocaleString('en-IN')} <span>/ night</span></h3>
          <div className="booking-fields">
            <div><small>Check in</small><strong>{checkIn || 'Select date'}</strong></div>
            <div><small>Check out</small><strong>{checkOut || 'Select date'}</strong></div>
            <label className="wide booking-guest-field">
              <small>Guests</small>
              <select value={guestCount} onChange={(event) => setGuestCount(Number(event.target.value))}>
                {Array.from({ length: p.guests }, (_, index) => (
                  <option key={index + 1} value={index + 1}>
                    {index + 1} guest{index ? 's' : ''}
                  </option>
                ))}
              </select>
            </label>
          </div>

          {bookingMessage && <div className="auth-error">{bookingMessage}</div>}
          <button className="primary" disabled={bookingBusy} onClick={() => void reserveStay()}>
            {bookingBusy ? 'Checking…' : p.bookingMode === 'request' ? 'Request to book' : 'Reserve'}
          </button>
          <small>
            {p.bookingMode === 'request'
              ? 'The host must accept your request before payment opens.'
              : 'You won’t be charged until checkout.'}
          </small>
        </aside>
      </div>
    </main>
  );
}

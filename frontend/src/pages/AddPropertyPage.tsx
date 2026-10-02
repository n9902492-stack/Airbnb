import { FormEvent, useState } from 'react';
import { ArrowLeft, ArrowRight, CheckCircle2 } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { ownerApi } from '../lib/api';

type FormState = {
  title: string;
  description: string;
  property_type: string;
  category: string;
  address_line: string;
  city: string;
  state: string;
  country: string;
  postal_code: string;
  guests: number;
  bedrooms: number;
  beds: number;
  bathrooms: number;
  price_per_night: number;
  cleaning_fee: number;
  amenities: string;
  house_rules: string;
  image_urls: string;
  check_in_time: string;
  check_out_time: string;
};

const initial: FormState = {
  title: '',
  description: '',
  property_type: 'Entire home',
  category: 'Mountain',
  address_line: '',
  city: '',
  state: '',
  country: 'India',
  postal_code: '',
  guests: 2,
  bedrooms: 1,
  beds: 1,
  bathrooms: 1,
  price_per_night: 3000,
  cleaning_fee: 0,
  amenities: 'Wi-Fi, Kitchen',
  house_rules: 'No smoking',
  image_urls: '',
  check_in_time: '14:00',
  check_out_time: '11:00',
};

export default function AddPropertyPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [form, setForm] = useState<FormState>(initial);
  const [error, setError] = useState('');
  const [uploading, setUploading] = useState(false);

  const update = (key: keyof FormState, value: string | number) =>
    setForm((current) => ({ ...current, [key]: value }));

  async function uploadImages(files: FileList | null) {
    if (!files?.length) return;
    setUploading(true);
    setError('');
    try {
      const uploaded: string[] = [];
      for (const file of Array.from(files)) {
        const result = await ownerApi.uploadImage(file);
        uploaded.push(result.url);
      }
      const current = form.image_urls
        .split(',')
        .map((x) => x.trim())
        .filter(Boolean);
      update('image_urls', [...current, ...uploaded].join(','));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to upload images');
    } finally {
      setUploading(false);
    }
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError('');
    try {
      await ownerApi.createProperty({
        ...form,
        amenities: form.amenities.split(',').map((x) => x.trim()).filter(Boolean),
        house_rules: form.house_rules.split(',').map((x) => x.trim()).filter(Boolean),
        image_urls: form.image_urls.split(',').map((x) => x.trim()).filter(Boolean),
      });
      navigate('/owner');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to create property');
    }
  }

  return (
    <main className="property-wizard">
      <div className="wizard-top">
        <Link to="/owner" className="back"><ArrowLeft size={18}/>Owner dashboard</Link>
        <span className="brand">Nestora</span>
      </div>

      <section className="wizard-shell">
        <aside className="wizard-steps">
          {[1,2,3,4].map((item) => (
            <div key={item} className={step >= item ? 'wizard-step active' : 'wizard-step'}>
              <span>{step > item ? <CheckCircle2 size={18}/> : item}</span>
              <div>
                <strong>{['Basics','Location & capacity','Pricing & rules','Photos & review'][item - 1]}</strong>
                <small>Step {item} of 4</small>
              </div>
            </div>
          ))}
        </aside>

        <form className="wizard-form" onSubmit={submit}>
          {step === 1 && <>
            <span className="eyebrow">Property basics</span>
            <h1>Tell guests what makes this place special.</h1>
            <label>Property title<input value={form.title} onChange={(e)=>update('title',e.target.value)} required /></label>
            <label>Description<textarea value={form.description} onChange={(e)=>update('description',e.target.value)} required /></label>
            <div className="form-grid">
              <label>Property type<select value={form.property_type} onChange={(e)=>update('property_type',e.target.value)}><option>Entire home</option><option>Private room</option><option>Villa</option><option>Cabin</option><option>Apartment</option></select></label>
              <label>Category<select value={form.category} onChange={(e)=>update('category',e.target.value)}><option>Mountain</option><option>Tropical</option><option>City</option><option>Countryside</option><option>Design home</option></select></label>
            </div>
          </>}

          {step === 2 && <>
            <span className="eyebrow">Location & capacity</span>
            <h1>Give guests the exact details they need.</h1>
            <label>Address<input value={form.address_line} onChange={(e)=>update('address_line',e.target.value)} required /></label>
            <div className="form-grid">
              <label>City<input value={form.city} onChange={(e)=>update('city',e.target.value)} required /></label>
              <label>State<input value={form.state} onChange={(e)=>update('state',e.target.value)} required /></label>
              <label>Postal code<input value={form.postal_code} onChange={(e)=>update('postal_code',e.target.value)} required /></label>
              <label>Country<input value={form.country} onChange={(e)=>update('country',e.target.value)} required /></label>
            </div>
            <div className="form-grid">
              <label>Guests<input type="number" min="1" value={form.guests} onChange={(e)=>update('guests',Number(e.target.value))}/></label>
              <label>Bedrooms<input type="number" min="0" value={form.bedrooms} onChange={(e)=>update('bedrooms',Number(e.target.value))}/></label>
              <label>Beds<input type="number" min="1" value={form.beds} onChange={(e)=>update('beds',Number(e.target.value))}/></label>
              <label>Bathrooms<input type="number" min="1" value={form.bathrooms} onChange={(e)=>update('bathrooms',Number(e.target.value))}/></label>
            </div>
          </>}

          {step === 3 && <>
            <span className="eyebrow">Pricing & rules</span>
            <h1>Set transparent pricing and expectations.</h1>
            <div className="form-grid">
              <label>Price per night (₹)<input type="number" min="1" value={form.price_per_night} onChange={(e)=>update('price_per_night',Number(e.target.value))}/></label>
              <label>Cleaning fee (₹)<input type="number" min="0" value={form.cleaning_fee} onChange={(e)=>update('cleaning_fee',Number(e.target.value))}/></label>
              <label>Check-in<input type="time" value={form.check_in_time} onChange={(e)=>update('check_in_time',e.target.value)}/></label>
              <label>Check-out<input type="time" value={form.check_out_time} onChange={(e)=>update('check_out_time',e.target.value)}/></label>
            </div>
            <label>Amenities <small>Comma separated</small><textarea value={form.amenities} onChange={(e)=>update('amenities',e.target.value)} /></label>
            <label>House rules <small>Comma separated</small><textarea value={form.house_rules} onChange={(e)=>update('house_rules',e.target.value)} /></label>
          </>}

          {step === 4 && <>
            <span className="eyebrow">Photos & submit</span>
            <h1>Add clear photos before moderation.</h1>
            <label>
              Upload property photos
              <small>Add clear exterior, living room, bedroom, bathroom and kitchen photos. JPEG, PNG or WebP, up to 8 MB each.</small>
              <input type="file" accept="image/jpeg,image/png,image/webp" multiple onChange={(e)=>void uploadImages(e.target.files)} />
            </label>
            {uploading && <div className="auth-success">Uploading photos…</div>}
            <div className="upload-preview-grid">
              {form.image_urls.split(',').map((x)=>x.trim()).filter(Boolean).map((url,index)=>(
                <figure key={url + index}>
                  <img src={url.startsWith('/uploads') ? 'http://localhost:8000' + url : url} alt={'Property upload ' + (index + 1)} />
                  <figcaption>{['Exterior','Living room','Bedroom','Bathroom','Kitchen'][index] ?? 'Extra photo'}</figcaption>
                </figure>
              ))}
            </div>
            <div className="review-box">
              <strong>{form.title || 'Untitled property'}</strong>
              <p>{form.city || 'City'}, {form.state || 'State'} · {form.guests} guests · ₹{form.price_per_night}/night</p>
              <small>Submitting sends the listing to Super Admin for approval. It will not go live automatically.</small>
            </div>
          </>}

          {error && <div className="auth-error">{error}</div>}

          <div className="wizard-actions">
            {step > 1 && <button type="button" className="ghost dark" onClick={()=>setStep(step-1)}>Back</button>}
            {step < 4
              ? <button type="button" className="primary inline" onClick={()=>setStep(step+1)}>Continue <ArrowRight size={18}/></button>
              : <button type="submit" className="primary inline">Submit for approval</button>}
          </div>
        </form>
      </section>
    </main>
  );
}

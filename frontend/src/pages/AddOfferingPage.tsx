import { FormEvent, useState } from 'react';
import { ArrowLeft } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

import { offeringApi, ownerApi } from '../lib/api';

export default function AddOfferingPage() {
  const navigate = useNavigate();
  const [kind, setKind] = useState<'service' | 'experience'>('service');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('');
  const [city, setCity] = useState('');
  const [state, setState] = useState('');
  const [price, setPrice] = useState(1500);
  const [pricingUnit, setPricingUnit] = useState<'per_guest' | 'per_group' | 'per_session'>('per_guest');
  const [durationMinutes, setDurationMinutes] = useState(60);
  const [capacity, setCapacity] = useState(4);
  const [instantBook, setInstantBook] = useState(true);
  const [included, setIncluded] = useState('');
  const [requirements, setRequirements] = useState('');
  const [images, setImages] = useState<string[]>([]);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);

  async function upload(files: FileList | null) {
    if (!files?.length) return;
    setBusy(true);
    try {
      const next = [...images];
      for (const file of Array.from(files)) {
        const result = await ownerApi.uploadImage(file);
        next.push(result.url);
      }
      setImages(next);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Unable to upload image');
    } finally {
      setBusy(false);
    }
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setMessage('');
    try {
      await offeringApi.create({
        kind,
        title,
        description,
        category,
        city,
        state,
        country: 'India',
        price,
        pricing_unit: pricingUnit,
        duration_minutes: durationMinutes,
        capacity,
        image_urls: images,
        included_items: included.split(',').map((x)=>x.trim()).filter(Boolean),
        requirements: requirements.split(',').map((x)=>x.trim()).filter(Boolean),
        instant_book: instantBook,
      });
      navigate('/owner');
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Unable to submit offering');
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="property-wizard">
      <div className="wizard-top">
        <Link to="/owner" className="back"><ArrowLeft size={18}/>Owner dashboard</Link>
        <span className="brand">Nestora</span>
      </div>

      <section className="wizard-shell single-wizard">
        <form className="wizard-form" onSubmit={submit}>
          <span className="eyebrow">Host-led marketplace</span>
          <h1>Create a service or experience.</h1>

          <div className="account-type-grid">
            <button type="button" className={kind === 'service' ? 'account-type active' : 'account-type'} onClick={()=>setKind('service')}>
              <strong>Service</strong>
              <small>Chef, photography, wellness, beauty and more.</small>
            </button>
            <button type="button" className={kind === 'experience' ? 'account-type active' : 'account-type'} onClick={()=>setKind('experience')}>
              <strong>Experience</strong>
              <small>Food, culture, tours, outdoors, workshops and more.</small>
            </button>
          </div>

          <label>Title<input value={title} onChange={(e)=>setTitle(e.target.value)} required/></label>
          <label>Description<textarea value={description} onChange={(e)=>setDescription(e.target.value)} required minLength={20}/></label>

          <div className="form-grid">
            <label>Category<input value={category} onChange={(e)=>setCategory(e.target.value)} required placeholder={kind === 'service' ? 'Photography' : 'Food'}/></label>
            <label>City<input value={city} onChange={(e)=>setCity(e.target.value)} required/></label>
            <label>State<input value={state} onChange={(e)=>setState(e.target.value)} required/></label>
            <label>Price (₹)<input type="number" min="1" value={price} onChange={(e)=>setPrice(Number(e.target.value))}/></label>
            <label>Pricing unit
              <select value={pricingUnit} onChange={(e)=>setPricingUnit(e.target.value as typeof pricingUnit)}>
                <option value="per_guest">Per guest</option>
                <option value="per_group">Per group</option>
                <option value="per_session">Per session</option>
              </select>
            </label>
            <label>Duration (minutes)<input type="number" min="15" value={durationMinutes} onChange={(e)=>setDurationMinutes(Number(e.target.value))}/></label>
            <label>Capacity<input type="number" min="1" max="100" value={capacity} onChange={(e)=>setCapacity(Number(e.target.value))}/></label>
          </div>

          <label className="toggle-filter">
            <input type="checkbox" checked={instantBook} onChange={(e)=>setInstantBook(e.target.checked)}/>
            Allow instant booking
          </label>

          <label>What’s included <small>Comma separated</small><textarea value={included} onChange={(e)=>setIncluded(e.target.value)}/></label>
          <label>Guest requirements <small>Comma separated</small><textarea value={requirements} onChange={(e)=>setRequirements(e.target.value)}/></label>

          <label>
            Photos
            <input type="file" accept="image/jpeg,image/png,image/webp" multiple onChange={(e)=>void upload(e.target.files)}/>
          </label>

          <div className="upload-preview-grid">
            {images.map((url,index)=>(
              <figure key={url+index}>
                <img src={url.startsWith('/uploads') ? 'http://localhost:8000' + url : url} alt={'Offering photo ' + (index+1)}/>
                <figcaption>Photo {index+1}</figcaption>
              </figure>
            ))}
          </div>

          {message && <div className="auth-error">{message}</div>}
          <button className="primary inline" disabled={busy} type="submit">
            {busy ? 'Submitting…' : 'Submit for approval'}
          </button>
        </form>
      </section>
    </main>
  );
}

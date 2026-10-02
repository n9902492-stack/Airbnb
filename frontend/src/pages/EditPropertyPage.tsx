import { FormEvent, useEffect, useState } from 'react';
import { ArrowLeft, ImagePlus, Save } from 'lucide-react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { ownerApi, ownerManagementApi, type OwnerProperty } from '../lib/api';

export default function EditPropertyPage() {
  const { propertyId } = useParams();
  const navigate = useNavigate();
  const id = Number(propertyId);

  const [property, setProperty] = useState<OwnerProperty | null>(null);
  const [title, setTitle] = useState('');
  const [price, setPrice] = useState(0);
  const [images, setImages] = useState<string[]>([]);
  const [blockStart, setBlockStart] = useState('');
  const [blockEnd, setBlockEnd] = useState('');
  const [message, setMessage] = useState('');
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    ownerManagementApi.getProperties().then((items) => {
      const found = items.find((item) => item.id === id) ?? null;
      setProperty(found);
      if (found) {
        setTitle(found.title);
        setPrice(Number(found.price_per_night));
        setImages(found.image_urls ?? []);
      }
    }).catch((err) => setMessage(err instanceof Error ? err.message : 'Unable to load property'));
  }, [id]);

  async function save(event: FormEvent) {
    event.preventDefault();
    try {
      await ownerManagementApi.updateProperty(id, {
        title,
        price_per_night: price,
        image_urls: images,
      });
      setMessage('Listing updated successfully.');
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Unable to update listing');
    }
  }

  async function upload(files: FileList | null) {
    if (!files?.length) return;
    setUploading(true);
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
      setUploading(false);
    }
  }

  async function blockDates() {
    if (!blockStart || !blockEnd) return;
    try {
      await ownerManagementApi.blockDates(id, {
        start_date: blockStart,
        end_date: blockEnd,
        reason: 'Owner unavailable',
      });
      setMessage('Dates blocked successfully.');
      setBlockStart('');
      setBlockEnd('');
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Unable to block dates');
    }
  }

  if (!property) {
    return <main className="property-wizard"><div className="wizard-top"><Link to="/owner" className="back"><ArrowLeft size={18}/>Owner dashboard</Link><span className="brand">Nestora</span></div><div className="wizard-shell"><p>{message || 'Loading property…'}</p></div></main>;
  }

  return (
    <main className="property-wizard">
      <div className="wizard-top">
        <Link to="/owner" className="back"><ArrowLeft size={18}/>Owner dashboard</Link>
        <span className="brand">Nestora</span>
      </div>

      <section className="edit-property-shell">
        <form className="wizard-form" onSubmit={save}>
          <span className="eyebrow">Edit listing</span>
          <h1>{property.title}</h1>

          <label>Listing title<input value={title} onChange={(e) => setTitle(e.target.value)} required /></label>
          <label>Nightly price (₹)<input type="number" min="1" value={price} onChange={(e) => setPrice(Number(e.target.value))} required /></label>

          <label>
            Add photos
            <input type="file" accept="image/jpeg,image/png,image/webp" multiple onChange={(e) => void upload(e.target.files)} />
            <small>{uploading ? 'Uploading…' : 'New uploads are appended to the gallery.'}</small>
          </label>

          <div className="upload-preview-grid">
            {images.map((url, index) => (
              <figure key={url + index}>
                <img src={url.startsWith('/uploads') ? 'http://localhost:8000' + url : url} alt={'Property photo ' + (index + 1)} />
                <figcaption>
                  Photo {index + 1}
                  <button type="button" className="remove-photo" onClick={() => setImages(images.filter((_, i) => i !== index))}>Remove</button>
                </figcaption>
              </figure>
            ))}
          </div>

          {message && <div className="auth-success">{message}</div>}
          <button className="primary inline" type="submit"><Save size={18}/>Save changes</button>
        </form>

        <aside className="owner-calendar-panel">
          <span className="eyebrow">Availability</span>
          <h2>Block dates</h2>
          <p>Use this when the property is unavailable for maintenance, personal use or another reservation source.</p>
          <label>From<input type="date" value={blockStart} onChange={(e) => setBlockStart(e.target.value)} /></label>
          <label>Until<input type="date" value={blockEnd} onChange={(e) => setBlockEnd(e.target.value)} /></label>
          <button className="ghost dark" type="button" onClick={() => void blockDates()}>Block selected dates</button>
          <div className="owner-calendar-note"><ImagePlus size={18}/>Guest bookings and owner blocks both feed the same availability API.</div>
        </aside>
      </section>
    </main>
  );
}

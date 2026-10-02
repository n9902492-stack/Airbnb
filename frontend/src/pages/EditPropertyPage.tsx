import { FormEvent, useEffect, useState } from 'react';
import { ArrowLeft, ImagePlus, Save, Trash2 } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import { collaborationApi, ownerApi, ownerManagementApi, type OwnerProperty } from '../lib/api';

type PricingRule = Awaited<ReturnType<typeof ownerManagementApi.pricingRules>>[number];

export default function EditPropertyPage() {
  const { propertyId } = useParams();
  const id = Number(propertyId);

  const [property, setProperty] = useState<OwnerProperty | null>(null);
  const [title, setTitle] = useState('');
  const [price, setPrice] = useState(0);
  const [weekendPrice, setWeekendPrice] = useState<number | ''>('');
  const [minimumStay, setMinimumStay] = useState(1);
  const [maximumStay, setMaximumStay] = useState<number | ''>('');
  const [images, setImages] = useState<string[]>([]);
  const [blockStart, setBlockStart] = useState('');
  const [blockEnd, setBlockEnd] = useState('');
  const [rules, setRules] = useState<PricingRule[]>([]);
  const [ruleName, setRuleName] = useState('');
  const [ruleStart, setRuleStart] = useState('');
  const [ruleEnd, setRuleEnd] = useState('');
  const [ruleRate, setRuleRate] = useState(0);
  const [ruleMinimumStay, setRuleMinimumStay] = useState<number | ''>('');
  const [message, setMessage] = useState('');
  const [cohosts, setCohosts] = useState<Awaited<ReturnType<typeof collaborationApi.cohosts>>>([]);
  const [cohostEmail, setCohostEmail] = useState('');
  const [cohostPermission, setCohostPermission] = useState<'calendar'|'messages'|'full'>('calendar');
  const [uploading, setUploading] = useState(false);

  async function load() {
    try {
      const [items, pricingRules, cohostItems] = await Promise.all([
        ownerManagementApi.getProperties(),
        ownerManagementApi.pricingRules(id),
        collaborationApi.cohosts(id).catch(() => []),
      ]);
      setCohosts(cohostItems);
      const found = items.find((item) => item.id === id) ?? null;
      setProperty(found);
      setRules(pricingRules);

      if (found) {
        setTitle(found.title);
        setPrice(Number(found.price_per_night));
        setWeekendPrice(found.weekend_price_per_night ? Number(found.weekend_price_per_night) : '');
        setMinimumStay(found.minimum_stay_nights ?? 1);
        setMaximumStay(found.maximum_stay_nights ? Number(found.maximum_stay_nights) : '');
        setImages(found.image_urls ?? []);
      }
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Unable to load property');
    }
  }

  useEffect(() => {
    void load();
  }, [id]);

  async function save(event: FormEvent) {
    event.preventDefault();
    try {
      await ownerManagementApi.updateProperty(id, {
        title,
        price_per_night: price,
        weekend_price_per_night: weekendPrice === '' ? null : weekendPrice,
        minimum_stay_nights: minimumStay,
        maximum_stay_nights: maximumStay === '' ? null : maximumStay,
        image_urls: images,
      });
      setMessage('Listing pricing and details updated successfully.');
      await load();
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

  async function addPricingRule() {
    if (!ruleName || !ruleStart || !ruleEnd || ruleRate <= 0) {
      setMessage('Complete the seasonal pricing fields first.');
      return;
    }

    try {
      await ownerManagementApi.createPricingRule(id, {
        name: ruleName,
        start_date: ruleStart,
        end_date: ruleEnd,
        nightly_rate: ruleRate,
        minimum_stay_nights: ruleMinimumStay === '' ? null : ruleMinimumStay,
      });
      setRuleName('');
      setRuleStart('');
      setRuleEnd('');
      setRuleRate(0);
      setRuleMinimumStay('');
      setMessage('Seasonal pricing rule added.');
      await load();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Unable to add pricing rule');
    }
  }

  async function removePricingRule(ruleId: number) {
    await ownerManagementApi.deletePricingRule(id, ruleId);
    setRules((current) => current.filter((rule) => rule.id !== ruleId));
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
          <span className="eyebrow">Listing & pricing</span>
          <h1>{property.title}</h1>

          <label>Listing title<input value={title} onChange={(e) => setTitle(e.target.value)} required /></label>

          <div className="form-grid">
            <label>Base nightly price (₹)<input type="number" min="1" value={price} onChange={(e) => setPrice(Number(e.target.value))} required /></label>
            <label>Weekend nightly price (₹)<input type="number" min="1" value={weekendPrice} placeholder="Use base price" onChange={(e) => setWeekendPrice(e.target.value ? Number(e.target.value) : '')} /></label>
            <label>Minimum stay<input type="number" min="1" max="90" value={minimumStay} onChange={(e) => setMinimumStay(Number(e.target.value))} /></label>
            <label>Maximum stay<input type="number" min="1" max="365" value={maximumStay} placeholder="No maximum" onChange={(e) => setMaximumStay(e.target.value ? Number(e.target.value) : '')} /></label>
          </div>

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
          <button className="primary inline" type="submit"><Save size={18}/>Save listing</button>
        </form>

        <div className="owner-side-stack">
          <aside className="owner-calendar-panel">
            <span className="eyebrow">Availability</span>
            <h2>Block dates</h2>
            <p>Block the property for maintenance, personal use or external reservations.</p>
            <label>From<input type="date" value={blockStart} onChange={(e) => setBlockStart(e.target.value)} /></label>
            <label>Until<input type="date" value={blockEnd} onChange={(e) => setBlockEnd(e.target.value)} /></label>
            <button className="ghost dark" type="button" onClick={() => void blockDates()}>Block selected dates</button>
            <div className="owner-calendar-note"><ImagePlus size={18}/>Guest bookings and owner blocks feed the same availability API.</div>
          </aside>


          <aside className="owner-calendar-panel">
            <span className="eyebrow">Co-host team</span>
            <h2>Share hosting work</h2>
            <p>Add an existing Nestora user and choose what they can manage.</p>
            <label>Email<input type="email" value={cohostEmail} onChange={(e)=>setCohostEmail(e.target.value)} placeholder="cohost@example.com"/></label>
            <label>Permission
              <select value={cohostPermission} onChange={(e)=>setCohostPermission(e.target.value as typeof cohostPermission)}>
                <option value="calendar">Calendar only</option>
                <option value="messages">Calendar & messages</option>
                <option value="full">Full access</option>
              </select>
            </label>
            <button className="primary inline" type="button" onClick={async()=>{
              const email = cohostEmail.trim();
              if (!email) return;
              await collaborationApi.addCohost(id,email,cohostPermission);
              setCohostEmail('');
              setCohosts(await collaborationApi.cohosts(id));
              setMessage('Co-host access updated.');
            }}>Add co-host</button>
            <div className="cohost-list">
              {cohosts.map((cohost)=>(
                <div key={cohost.id}>
                  <span><strong>{cohost.name}</strong><small>{cohost.email} · {cohost.permission}</small></span>
                  <button type="button" className="ghost dark" onClick={async()=>{
                    await collaborationApi.removeCohost(id,cohost.id);
                    setCohosts((current)=>current.filter((x)=>x.id!==cohost.id));
                  }}>Remove</button>
                </div>
              ))}
            </div>
          </aside>

          <aside className="owner-calendar-panel">
            <span className="eyebrow">Seasonal pricing</span>
            <h2>Special date rates</h2>
            <label>Rule name<input value={ruleName} onChange={(e) => setRuleName(e.target.value)} placeholder="Christmas / New Year" /></label>
            <label>From<input type="date" value={ruleStart} onChange={(e) => setRuleStart(e.target.value)} /></label>
            <label>Until<input type="date" value={ruleEnd} onChange={(e) => setRuleEnd(e.target.value)} /></label>
            <label>Nightly rate (₹)<input type="number" min="1" value={ruleRate || ''} onChange={(e) => setRuleRate(Number(e.target.value))} /></label>
            <label>Minimum stay<input type="number" min="1" value={ruleMinimumStay} placeholder="Property default" onChange={(e) => setRuleMinimumStay(e.target.value ? Number(e.target.value) : '')} /></label>
            <button className="primary inline" type="button" onClick={() => void addPricingRule()}>Add pricing rule</button>

            <div className="pricing-rule-list">
              {rules.map((rule) => (
                <div className="pricing-rule-card" key={rule.id}>
                  <div><strong>{rule.name}</strong><small>{rule.start_date} → {rule.end_date}</small><span>₹{Number(rule.nightly_rate).toLocaleString('en-IN')}/night</span></div>
                  <button type="button" onClick={() => void removePricingRule(rule.id)} aria-label="Delete pricing rule"><Trash2 size={16}/></button>
                </div>
              ))}
            </div>
          </aside>
        </div>
      </section>
    </main>
  );
}

import { FormEvent, useEffect, useState } from 'react';
import { ArrowLeft, BadgeCheck, CircleHelp, ShieldCheck, WalletCards } from 'lucide-react';
import { Link } from 'react-router-dom';

import { authStore } from '../lib/auth';
import { trustApi } from '../lib/api';

export default function TrustCenterPage() {
  const user = authStore.getUser();
  const [identity, setIdentity] = useState<Awaited<ReturnType<typeof trustApi.identity>> | null>(null);
  const [cases, setCases] = useState<Awaited<ReturnType<typeof trustApi.mySupport>>>([]);
  const [claims, setClaims] = useState<Awaited<ReturnType<typeof trustApi.myClaims>>>([]);
  const [documentType, setDocumentType] = useState('national_id');
  const [caseType, setCaseType] = useState('reservation_issue');
  const [bookingId, setBookingId] = useState('');
  const [subject, setSubject] = useState('');
  const [description, setDescription] = useState('');
  const [message, setMessage] = useState('');
  const [claimBookingId, setClaimBookingId] = useState('');
  const [claimAmount, setClaimAmount] = useState<number | ''>('');
  const [claimReason, setClaimReason] = useState('');

  async function load() {
    try {
      const [identityData, supportData, claimData] = await Promise.all([
        trustApi.identity(),
        trustApi.mySupport(),
        trustApi.myClaims(),
      ]);
      setIdentity(identityData);
      setCases(supportData);
      setClaims(claimData);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Unable to load Trust Center');
    }
  }

  useEffect(()=>{void load();},[]);

  async function submitSupport(event: FormEvent) {
    event.preventDefault();
    try {
      await trustApi.createSupport({
        booking_id: bookingId ? Number(bookingId) : null,
        case_type: caseType,
        subject,
        description,
        priority: caseType === 'safety' ? 'urgent' : 'normal',
      });
      setSubject('');
      setDescription('');
      setMessage('Support case created.');
      await load();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Unable to create support case');
    }
  }

  return (
    <main className="profile-page">
      <div className="detail-top">
        <Link to={user?.role === 'owner' ? '/owner' : user?.role === 'super_admin' ? '/super-admin' : '/user'} className="back"><ArrowLeft size={18}/>Dashboard</Link>
        <span className="brand">Nestora</span>
      </div>

      <section className="profile-shell">
        <div><span className="eyebrow">Safety, verification & resolutions</span><h1>Trust Center</h1><p>Manage verification, get reservation help, report safety issues and follow Resolution Center requests.</p></div>

        {message && <div className="auth-success">{message}</div>}

        <div className="trust-grid">
          <div className="panel">
            <h2><BadgeCheck size={20}/> Identity verification</h2>
            <p>Status: <strong>{identity?.status ?? 'loading'}</strong></p>
            {identity?.verified ? (
              <div className="auth-success"><ShieldCheck size={18}/>Identity verified</div>
            ) : (
              <>
                <label>Document type
                  <select value={documentType} onChange={(e)=>setDocumentType(e.target.value)}>
                    <option value="national_id">National ID</option>
                    <option value="passport">Passport</option>
                    <option value="driving_license">Driving licence</option>
                    <option value="other">Other</option>
                  </select>
                </label>
                <p className="trust-note">Nestora records verification status only. Connect an approved KYC provider before accepting real identity documents.</p>
                <button className="primary inline" onClick={async()=>{await trustApi.startIdentity(documentType);setMessage('Identity review started.');await load();}}>Start verification</button>
              </>
            )}
          </div>

          <form className="panel" onSubmit={submitSupport}>
            <h2><CircleHelp size={20}/> Get help</h2>
            <label>Issue type
              <select value={caseType} onChange={(e)=>setCaseType(e.target.value)}>
                <option value="reservation_issue">Reservation issue</option>
                <option value="refund">Refund</option>
                <option value="safety">Safety issue</option>
                <option value="damage">Damage</option>
                <option value="account">Account</option>
                <option value="other">Other</option>
              </select>
            </label>
            <label>Booking ID (optional)<input value={bookingId} onChange={(e)=>setBookingId(e.target.value.replace(/\D/g,''))}/></label>
            <label>Subject<input value={subject} onChange={(e)=>setSubject(e.target.value)} required/></label>
            <label>Description<textarea value={description} onChange={(e)=>setDescription(e.target.value)} minLength={10} required/></label>
            <button className="primary inline">Create case</button>
          </form>
        </div>

        <div className="panel">
          <h2>Support cases</h2>
          <div className="support-list">
            {cases.length === 0 ? <p>No support cases.</p> : cases.map((item)=>(
              <article key={item.id}><div><strong>#{item.id} · {item.subject}</strong><small>{item.case_type} · {item.priority}</small></div><span className={'booking-status ' + item.status}>{item.status}</span>{item.resolution && <p>{item.resolution}</p>}</article>
            ))}
          </div>
        </div>


        <form className="panel" onSubmit={async(event)=>{
          event.preventDefault();
          if (!claimBookingId || claimAmount === '' || !claimReason.trim()) return;
          try {
            await trustApi.createClaim({
              booking_id:Number(claimBookingId),
              amount:Number(claimAmount),
              reason:claimReason,
              evidence_urls:[],
            });
            setClaimBookingId('');
            setClaimAmount('');
            setClaimReason('');
            setMessage('Resolution Center request sent to the other reservation participant.');
            await load();
          } catch (err) {
            setMessage(err instanceof Error ? err.message : 'Unable to create claim');
          }
        }}>
          <h2><WalletCards size={20}/> Request money / report damage</h2>
          <p>Use this for reservation-related reimbursement or damage requests. You must be a guest or host on the booking.</p>
          <div className="form-grid">
            <label>Booking ID<input inputMode="numeric" value={claimBookingId} onChange={(e)=>setClaimBookingId(e.target.value.replace(/\D/g,''))} required/></label>
            <label>Amount (₹)<input type="number" min="1" value={claimAmount} onChange={(e)=>setClaimAmount(e.target.value ? Number(e.target.value) : '')} required/></label>
          </div>
          <label>Reason<textarea value={claimReason} onChange={(e)=>setClaimReason(e.target.value)} minLength={10} required/></label>
          <button className="primary inline">Send request</button>
        </form>

        <div className="panel">
          <h2><WalletCards size={20}/> Resolution Center</h2>
          <div className="support-list">
            {claims.length === 0 ? <p>No money requests or damage claims.</p> : claims.map((claim)=>(
              <article key={claim.id}><div><strong>Claim #{claim.id} · ₹{Number(claim.amount).toLocaleString('en-IN')}</strong><small>Booking #{claim.booking_id}</small><p>{claim.reason}</p></div><span className={'booking-status ' + claim.status}>{claim.status}</span>
                {claim.respondent_id === user?.id && claim.status === 'requested' && (
                  <div className="moderation-actions">
                    <button className="primary inline" onClick={async()=>{try{await trustApi.respondClaim(claim.id,'accepted');await load();}catch{}}}>Accept</button>
                    <button className="ghost dark" onClick={async()=>{try{await trustApi.respondClaim(claim.id,'declined');await load();}catch{}}}>Decline</button>
                  </div>
                )}
              </article>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}

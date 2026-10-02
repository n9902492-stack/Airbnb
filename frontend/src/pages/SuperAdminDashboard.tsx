import { useEffect, useState } from 'react';
import { Building2, Flag, LayoutDashboard, Shield, Users } from 'lucide-react';
import { Link } from 'react-router-dom';
import { adminApi, adminBookingApi, financeApi, promotionApi, trustApi, type AdminBooking, type AdminFinance, type PendingProperty } from '../lib/api';

export default function SuperAdminDashboard() {
  const [overview, setOverview] = useState({ users: 0, owners: 0, listings: 0, bookings: 0 });
  const [pending, setPending] = useState<PendingProperty[]>([]);
  const [reason, setReason] = useState<Record<number, string>>({});
  const [message, setMessage] = useState('');
  const [bookings, setBookings] = useState<AdminBooking[]>([]);
  const [finance, setFinance] = useState<AdminFinance>({ collected: 0, refunds: 0, platform_commission: 0, owner_payable: 0, owner_paid: 0, payouts: [] });
  const [linkedAccounts, setLinkedAccounts] = useState<Record<number,string>>({});
  const [auditLogs, setAuditLogs] = useState<Awaited<ReturnType<typeof adminApi.auditLogs>>>([]);
  const [pendingOfferings, setPendingOfferings] = useState<Awaited<ReturnType<typeof adminApi.pendingOfferings>>>([]);
  const [pendingIdentity, setPendingIdentity] = useState<Awaited<ReturnType<typeof trustApi.pendingIdentity>>>([]);
  const [supportCases, setSupportCases] = useState<Awaited<ReturnType<typeof trustApi.adminSupport>>>([]);
  const [promotions, setPromotions] = useState<Awaited<ReturnType<typeof promotionApi.list>>>([]);
  const [promoCode, setPromoCode] = useState('');
  const [promoValue, setPromoValue] = useState(10);
  const [promoType, setPromoType] = useState<'percent'|'fixed'>('percent');

  async function refresh() {
    const [summary, items, bookingItems, financeData, auditItems, offeringItems, identityItems, supportItems, promoItems] = await Promise.all([
      adminApi.overview(),
      adminApi.pendingProperties(),
      adminBookingApi.list(),
      financeApi.admin(),
      adminApi.auditLogs(),
      adminApi.pendingOfferings(),
      trustApi.pendingIdentity(),
      trustApi.adminSupport(),
      promotionApi.list(),
    ]);
    setOverview(summary);
    setPending(items);
    setBookings(bookingItems);
    setFinance(financeData);
    setAuditLogs(auditItems);
    setPendingOfferings(offeringItems);
    setPendingIdentity(identityItems);
    setSupportCases(supportItems);
    setPromotions(promoItems);
  }

  useEffect(() => {
    void refresh().catch((err) => setMessage(err instanceof Error ? err.message : 'Unable to load moderation data'));
  }, []);

  async function approve(id: number) {
    try {
      await adminApi.approveProperty(id);
      setMessage('Listing approved and moved live.');
      await refresh();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Unable to approve listing');
    }
  }

  async function reject(id: number) {
    const value = reason[id]?.trim();
    if (!value) {
      setMessage('Add a rejection reason first.');
      return;
    }
    try {
      await adminApi.rejectProperty(id, value);
      setMessage('Listing rejected with owner feedback.');
      await refresh();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Unable to reject listing');
    }
  }

  return (
    <main className="dashboard admin-theme">
      <aside className="sidebar">
        <Link className="brand" to="/">Nestora</Link>
        <strong>Super Admin</strong>
        <nav>
          <a className="selected"><LayoutDashboard />Overview</a>
          <a><Users />Users & owners</a>
          <a><Building2 />Listings</a>
          <a><Flag />Reports</a>
          <a><Shield />Platform controls</a>
        </nav>
      </aside>

      <section className="dash-content">
        <div className="dash-head">
          <div>
            <span className="eyebrow">Platform control centre</span>
            <h1>Super Admin overview</h1>
            <p>All numbers and pending listings below are loaded from PostgreSQL.</p>
          </div>
        </div>

        <div className="stats">
          <div className="stat"><small>Total users</small><strong>{overview.users}</strong></div>
          <div className="stat"><small>Owners</small><strong>{overview.owners}</strong></div>
          <div className="stat"><small>Total listings</small><strong>{overview.listings}</strong></div>
          <div className="stat"><small>Bookings</small><strong>{overview.bookings}</strong></div>
        </div>

        {message && <div className="auth-success">{message}</div>}

        <div className="panel">
          <div className="section-head">
            <div>
              <h2>Pending listing moderation</h2>
              <p>{pending.length} listing{pending.length === 1 ? '' : 's'} currently need review.</p>
            </div>
          </div>

          {pending.length === 0 ? (
            <p>No listings are awaiting moderation.</p>
          ) : (
            <div className="admin-moderation-grid">
              {pending.map((item) => {
                const image = item.image_urls?.[0];
                return (
                  <article className="admin-listing-card" key={item.id}>
                    {image && <img src={image.startsWith('/uploads') ? 'http://localhost:8000' + image : image} alt={item.title} />}
                    <div>
                      <strong>{item.title}</strong>
                      <p>{item.city}, {item.state} · ₹{Number(item.price_per_night).toLocaleString('en-IN')}/night</p>
                      <small>Owner ID #{item.owner_id}</small>
                    </div>
                    <textarea
                      placeholder="Reason if rejecting"
                      value={reason[item.id] ?? ''}
                      onChange={(e) => setReason((current) => ({ ...current, [item.id]: e.target.value }))}
                    />
                    <div className="moderation-actions">
                      <button className="primary inline" onClick={() => void approve(item.id)}>Approve</button>
                      <button className="ghost dark" onClick={() => void reject(item.id)}>Reject</button>
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </div>


        <div className="panel">
          <div className="section-head"><div><h2>Services & experiences moderation</h2><p>{pendingOfferings.length} host-led offering{pendingOfferings.length === 1 ? '' : 's'} awaiting review.</p></div></div>
          {pendingOfferings.length === 0 ? <p>No services or experiences are awaiting moderation.</p> : (
            <div className="admin-moderation-grid">
              {pendingOfferings.map((item)=> {
                const image = item.image_urls?.[0];
                return (
                  <article className="admin-listing-card" key={'offering-admin-' + item.id}>
                    {image && <img src={image.startsWith('/uploads') ? 'http://localhost:8000' + image : image} alt={item.title}/>}
                    <div><strong>{item.title}</strong><p>{item.kind} · {item.category} · {item.city}, {item.state}</p><small>Host #{item.host_id} · ₹{Number(item.price).toLocaleString('en-IN')}</small></div>
                    <textarea placeholder="Reason if rejecting" value={reason[1000000 + item.id] ?? ''} onChange={(e)=>setReason((current)=>({...current,[1000000 + item.id]:e.target.value}))}/>
                    <div className="moderation-actions">
                      <button className="primary inline" onClick={async()=>{await adminApi.approveOffering(item.id); setMessage('Offering approved.'); await refresh();}}>Approve</button>
                      <button className="ghost dark" onClick={async()=>{
                        const value = reason[1000000 + item.id]?.trim();
                        if (!value) { setMessage('Add a rejection reason first.'); return; }
                        await adminApi.rejectOffering(item.id, value); setMessage('Offering rejected.'); await refresh();
                      }}>Reject</button>
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </div>


        <div className="panel">
          <div className="section-head"><div><h2>Identity verification</h2><p>Review KYC/provider references without storing raw identity documents in Nestora.</p></div></div>
          {pendingIdentity.length === 0 ? <p>No identity submissions awaiting review.</p> : (
            <div className="support-list">
              {pendingIdentity.map((item)=>(
                <article key={'identity-' + item.id}>
                  <div><strong>{item.name}</strong><small>{item.email} · {item.document_type ?? 'document'} · {item.provider}</small>{item.provider_reference && <code>{item.provider_reference}</code>}</div>
                  <div className="moderation-actions">
                    <button className="primary inline" onClick={async()=>{await trustApi.approveIdentity(item.id);setMessage('Identity approved.');await refresh();}}>Verify</button>
                    <button className="ghost dark" onClick={async()=>{const reason=window.prompt('Reason for rejection?')?.trim();if(reason){await trustApi.rejectIdentity(item.id,reason);await refresh();}}}>Reject</button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>

        <div className="panel">
          <div className="section-head"><div><h2>Support & safety queue</h2><p>Reservation, refund, damage and urgent safety cases in one queue.</p></div></div>
          {supportCases.length === 0 ? <p>No support cases.</p> : (
            <div className="support-list">
              {supportCases.map((item)=>(
                <article key={'support-' + item.id}>
                  <div><strong>#{item.id} · {item.subject}</strong><small>{item.reporter_name} · {item.case_type} · {item.priority}</small>{item.booking_id && <span>Booking #{item.booking_id}</span>}</div>
                  <div className="moderation-actions">
                    <button className="ghost dark" onClick={async()=>{await trustApi.updateSupport(item.id,'in_progress');await refresh();}}>Start</button>
                    <button className="primary inline" onClick={async()=>{const resolution=window.prompt('Resolution note') ?? '';await trustApi.updateSupport(item.id,'resolved',resolution);await refresh();}}>Resolve</button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>

        <div className="panel">
          <div className="section-head"><div><h2>Promotions</h2><p>Create platform-funded checkout discounts with usage limits and server-side validation.</p></div></div>
          <div className="collaboration-create">
            <input value={promoCode} onChange={(e)=>setPromoCode(e.target.value.toUpperCase())} placeholder="NESTORA10"/>
            <select value={promoType} onChange={(e)=>setPromoType(e.target.value as typeof promoType)}>
              <option value="percent">Percent</option>
              <option value="fixed">Fixed ₹</option>
            </select>
            <input type="number" min="1" value={promoValue} onChange={(e)=>setPromoValue(Number(e.target.value))}/>
            <button className="primary inline" onClick={async()=>{
              if(!promoCode.trim()) return;
              await promotionApi.create({
                code:promoCode.trim(),
                discount_type:promoType,
                discount_value:promoValue,
                minimum_spend:0,
              });
              setPromoCode('');
              setPromotions(await promotionApi.list());
            }}>Create promotion</button>
          </div>
          <div className="promotion-grid">
            {promotions.map((promo)=>(
              <article key={'promo-' + promo.id}>
                <strong>{promo.code}</strong>
                <span>{promo.discount_type === 'percent' ? promo.discount_value + '%' : '₹' + Number(promo.discount_value).toLocaleString('en-IN')} off</span>
                <small>{promo.used_count}{promo.max_uses ? ' / ' + promo.max_uses : ''} uses</small>
                <button className="ghost dark" onClick={async()=>{await promotionApi.toggle(promo.id);setPromotions(await promotionApi.list());}}>{promo.active ? 'Disable' : 'Enable'}</button>
              </article>
            ))}
          </div>
        </div>

        <div className="panel">
          <div className="section-head"><div><h2>Platform finance</h2><p>Customer collections, refunds, Nestora commission and owner payout liability.</p></div></div>
          <div className="finance-grid">
            <div><small>Collected</small><strong>₹{Number(finance.collected).toLocaleString('en-IN')}</strong></div>
            <div><small>Refunded</small><strong>₹{Number(finance.refunds).toLocaleString('en-IN')}</strong></div>
            <div><small>Commission</small><strong>₹{Number(finance.platform_commission).toLocaleString('en-IN')}</strong></div>
            <div><small>Owners payable</small><strong>₹{Number(finance.owner_payable).toLocaleString('en-IN')}</strong></div>
            <div><small>Owners paid</small><strong>₹{Number(finance.owner_paid).toLocaleString('en-IN')}</strong></div>
          </div>
          <div className="payout-admin-list">
            {finance.payouts.filter((payout) => payout.status === 'ready').map((payout) => (
              <div key={payout.id}>
                <span>Booking #{payout.booking_id} · Owner #{payout.owner_id}</span>
                <strong>₹{Number(payout.owner_amount).toLocaleString('en-IN')}</strong>
                <input
                  placeholder="acc_..."
                  value={linkedAccounts[payout.owner_id] ?? ''}
                  onChange={(e)=>setLinkedAccounts((current)=>({...current,[payout.owner_id]:e.target.value}))}
                />
                <button className="ghost dark" onClick={async()=>{
                  const accountId = linkedAccounts[payout.owner_id]?.trim();
                  if (accountId) {
                    await financeApi.setOwnerPayoutAccount(payout.owner_id, accountId);
                    setMessage('Verified Razorpay Route linked account saved. Automatic payout worker will handle READY payouts.');
                    await refresh();
                  }
                }}>Save payout account</button>
              </div>
            ))}
          </div>
        </div>

        <div className="panel">
          <div className="section-head"><div><h2>Audit trail</h2><p>Recent privileged platform changes with actor and request identifiers.</p></div></div>
          <div className="reservation-table-wrap">
            <table>
              <thead><tr><th>Time</th><th>Action</th><th>Actor</th><th>Entity</th><th>Request ID</th></tr></thead>
              <tbody>
                {auditLogs.map((item) => (
                  <tr key={item.id}>
                    <td>{new Date(item.created_at).toLocaleString('en-IN')}</td>
                    <td>{item.action}</td>
                    <td>{item.actor_user_id ? '#' + item.actor_user_id : 'system'}</td>
                    <td>{item.entity_type ?? '—'} {item.entity_id ? '#' + item.entity_id : ''}</td>
                    <td><small>{item.request_id ?? '—'}</small></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="panel admin-bookings-panel">
          <div className="section-head"><div><h2>Booking controls</h2><p>Recent reservations, payment state and platform cancellation control.</p></div></div>
          <div className="reservation-table-wrap">
            <table>
              <thead><tr><th>Property</th><th>Guest</th><th>Dates</th><th>Booking</th><th>Payment</th><th>Total</th><th></th></tr></thead>
              <tbody>
                {bookings.map((booking) => (
                  <tr key={booking.booking_id}>
                    <td>{booking.property_title}</td>
                    <td>{booking.guest_name}</td>
                    <td>{booking.check_in} → {booking.check_out}</td>
                    <td><span className={'booking-status ' + booking.status}>{booking.status}</span></td>
                    <td>{booking.payment_status ?? 'not started'}{booking.refund_amount ? ' · refund ₹' + booking.refund_amount : ''}</td>
                    <td>₹{Number(booking.total_amount).toLocaleString('en-IN')}</td>
                    <td>{['pending','confirmed'].includes(booking.status) && <button className="ghost dark" onClick={async()=>{await adminBookingApi.cancel(booking.booking_id); await refresh();}}>Cancel</button>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </main>
  );
}

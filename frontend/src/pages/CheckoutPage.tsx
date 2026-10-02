import { useEffect, useState } from 'react';
import { ArrowLeft, CheckCircle2, CreditCard, ShieldCheck } from 'lucide-react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { paymentApi, type CheckoutPreview, type PaymentResult } from '../lib/api';

export default function CheckoutPage() {
  const { bookingId } = useParams();
  const navigate = useNavigate();
  const id = Number(bookingId);

  const [preview, setPreview] = useState<CheckoutPreview | null>(null);
  const [payment, setPayment] = useState<PaymentResult | null>(null);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!id) return;
    paymentApi.preview(id)
      .then(setPreview)
      .catch((err) => setMessage(err instanceof Error ? err.message : 'Unable to load checkout'));
  }, [id]);

  async function createPayment() {
    setBusy(true);
    setMessage('');
    try {
      const result = await paymentApi.create(id);
      setPayment(result);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Unable to create payment');
    } finally {
      setBusy(false);
    }
  }

  async function confirmDemoPayment() {
    if (!payment) return;
    setBusy(true);
    try {
      const result = await paymentApi.demoConfirm(payment.id);
      setPayment(result);
      setMessage('Payment confirmed in development mode. Your reservation is now confirmed.');
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Unable to confirm payment');
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="checkout-page">
      <div className="checkout-topbar">
        <Link to="/" className="back"><ArrowLeft size={18}/>Back</Link>
        <span className="brand">Nestora</span>
      </div>

      <section className="checkout-shell">
        <div>
          <span className="eyebrow">Secure checkout</span>
          <h1>Review and confirm your reservation</h1>
          <p>Your selected stay and optional transfer are combined here before payment.</p>

          <div className="checkout-trust">
            <div><ShieldCheck size={19}/><span>Server-calculated pricing</span></div>
            <div><CheckCircle2 size={19}/><span>Dates are rechecked before booking</span></div>
          </div>

          {message && <div className={payment?.status === 'paid' ? 'auth-success' : 'auth-error'}>{message}</div>}

          {payment?.status === 'paid' ? (
            <div className="checkout-success">
              <CheckCircle2 size={44}/>
              <h2>Reservation confirmed</h2>
              <p>Your booking is confirmed and the selected dates are blocked from other guests.</p>
              <button className="primary inline" onClick={() => navigate('/user')}>Go to my trips</button>
            </div>
          ) : (
            <div className="payment-card">
              <CreditCard size={24}/>
              <div>
                <strong>Payment</strong>
                <p>Live gateway integration is provider-ready. Development mode currently uses a safe demo confirmation.</p>
              </div>

              {!payment ? (
                <button className="primary" disabled={busy || !preview} onClick={() => void createPayment()}>
                  {busy ? 'Preparing…' : 'Continue to payment'}
                </button>
              ) : (
                <button className="primary" disabled={busy} onClick={() => void confirmDemoPayment()}>
                  {busy ? 'Confirming…' : 'Confirm demo payment'}
                </button>
              )}
            </div>
          )}
        </div>

        <aside className="checkout-summary">
          <h2>Price details</h2>
          {!preview ? (
            <p>Loading…</p>
          ) : (
            <>
              <div><span>Stay subtotal</span><strong>₹{Number(preview.stay_subtotal).toLocaleString('en-IN')}</strong></div>
              <div><span>Service fee</span><strong>₹{Number(preview.service_fee).toLocaleString('en-IN')}</strong></div>
              <div><span>Optional transfer</span><strong>₹{Number(preview.transfer_fee).toLocaleString('en-IN')}</strong></div>
              <hr/>
              <div className="checkout-total">
                <span>Total</span>
                <strong>₹{Number(preview.grand_total).toLocaleString('en-IN')}</strong>
              </div>
            </>
          )}
        </aside>
      </section>
    </main>
  );
}

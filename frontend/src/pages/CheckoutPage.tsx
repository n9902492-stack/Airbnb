import { useEffect, useState } from 'react';
import { ArrowLeft, CheckCircle2, CreditCard, ShieldCheck } from 'lucide-react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import {
  paymentApi,
  type CheckoutPreview,
  type PaymentResult,
  type PaymentSession,
} from '../lib/api';
import { loadRazorpayCheckout, type RazorpaySuccess } from '../lib/razorpay';

export default function CheckoutPage() {
  const { bookingId } = useParams();
  const navigate = useNavigate();
  const id = Number(bookingId);

  const [preview, setPreview] = useState<CheckoutPreview | null>(null);
  const [payment, setPayment] = useState<PaymentResult | null>(null);
  const [session, setSession] = useState<PaymentSession | null>(null);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!id) return;
    paymentApi.preview(id)
      .then(setPreview)
      .catch((err) => setMessage(err instanceof Error ? err.message : 'Unable to load checkout'));
  }, [id]);

  async function verifyRazorpay(response: RazorpaySuccess, paymentSession: PaymentSession) {
    setBusy(true);
    try {
      const verified = await paymentApi.verifyRazorpay(paymentSession.id, response);
      setPayment(verified);
      setMessage(
        verified.status === 'refunded'
          ? 'The booking hold expired before confirmation, so the captured payment was refunded.'
          : 'Payment verified. Your reservation is confirmed.',
      );
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Payment verification failed');
    } finally {
      setBusy(false);
    }
  }

  async function beginPayment() {
    setBusy(true);
    setMessage('');

    try {
      const created = await paymentApi.create(id);
      setSession(created);

      if (created.provider === 'manual_demo') {
        setBusy(false);
        return;
      }

      if (!created.razorpay_key_id || !created.provider_order_id || !created.amount_paise) {
        throw new Error('Razorpay checkout session is incomplete');
      }

      await loadRazorpayCheckout();

      if (!window.Razorpay) {
        throw new Error('Razorpay checkout is unavailable');
      }

      const checkout = new window.Razorpay({
        key: created.razorpay_key_id,
        amount: created.amount_paise,
        currency: created.currency,
        order_id: created.provider_order_id,
        name: 'Nestora',
        description: 'Stay reservation',
        handler: (response) => void verifyRazorpay(response, created),
        modal: {
          ondismiss: () => setMessage('Payment window closed. Your booking remains held temporarily.'),
        },
        theme: { color: '#17352d' },
      });

      checkout.open();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Unable to start payment');
    } finally {
      setBusy(false);
    }
  }

  async function confirmDemoPayment() {
    if (!session) return;
    setBusy(true);
    try {
      const result = await paymentApi.demoConfirm(session.id);
      setPayment(result);
      setMessage('Payment confirmed in development mode. Your reservation is now confirmed.');
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Unable to confirm payment');
    } finally {
      setBusy(false);
    }
  }

  const isPaid = payment?.status === 'paid';

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
            <div><CheckCircle2 size={19}/><span>Payment signature verified on the backend</span></div>
          </div>

          {message && (
            <div className={isPaid ? 'auth-success' : 'auth-error'}>{message}</div>
          )}

          {isPaid ? (
            <div className="checkout-success">
              <CheckCircle2 size={44}/>
              <h2>Reservation confirmed</h2>
              <p>Your payment is recorded and these dates remain blocked for other guests.</p>
              <button className="primary inline" onClick={() => navigate('/user')}>
                Go to my trips
              </button>
            </div>
          ) : (
            <div className="payment-card">
              <CreditCard size={24}/>
              <div>
                <strong>{session?.provider === 'razorpay' ? 'Razorpay secure checkout' : 'Payment'}</strong>
                <p>
                  {session?.provider === 'manual_demo'
                    ? 'Development mode is active. Use demo confirmation below.'
                    : 'When Razorpay is configured, cards, UPI and other enabled methods open in the secure checkout overlay.'}
                </p>
              </div>

              {!session ? (
                <button className="primary" disabled={busy || !preview} onClick={() => void beginPayment()}>
                  {busy ? 'Preparing…' : 'Continue to payment'}
                </button>
              ) : session.provider === 'manual_demo' ? (
                <button className="primary" disabled={busy} onClick={() => void confirmDemoPayment()}>
                  {busy ? 'Confirming…' : 'Confirm demo payment'}
                </button>
              ) : (
                <button className="primary" disabled={busy} onClick={() => void beginPayment()}>
                  {busy ? 'Opening…' : 'Open Razorpay checkout again'}
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
              {Number(preview.gst_amount) > 0 && (
                <div><span>GST ({Number(preview.gst_rate)}%)</span><strong>₹{Number(preview.gst_amount).toLocaleString('en-IN')}</strong></div>
              )}
              <hr/>
              <div className="checkout-total">
                <span>Total</span>
                <strong>₹{Number(preview.grand_total).toLocaleString('en-IN')}</strong>
              </div>
              <small>Unpaid reservations are held for 15 minutes and then released automatically.</small>
            </>
          )}
        </aside>
      </section>
    </main>
  );
}

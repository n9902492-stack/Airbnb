import { FormEvent, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authApi } from '../lib/api';

type Mode = 'signin' | 'signup' | 'verify' | 'forgot' | 'reset';

const isStrongPassword = (value: string) =>
  value.length >= 10 &&
  /[A-Z]/.test(value) &&
  /[a-z]/.test(value) &&
  /\d/.test(value) &&
  /[^A-Za-z0-9]/.test(value);

export default function AuthPage() {
  const navigate = useNavigate();
  const [mode, setMode] = useState<Mode>('signin');
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [otp, setOtp] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError('');
    setMessage('');

    try {
      if (mode === 'signup') {
        if (!isStrongPassword(password)) {
          setError('Use at least 10 characters with uppercase, lowercase, number and special character.');
          return;
        }
        await authApi.register({ full_name: fullName, email, password });
        setMode('verify');
        setMessage('A 6-digit OTP was sent to your email.');
        return;
      }

      if (mode === 'verify') {
        const result = await authApi.verifyEmail({ email, otp });
        setMessage(result.message);
        setMode('signin');
        return;
      }

      if (mode === 'signin') {
        const result = await authApi.login(email, password);
        localStorage.setItem('nestora_access_token', result.access_token);
        navigate('/');
        return;
      }

      if (mode === 'forgot') {
        const result = await authApi.forgotPassword(email);
        setMessage(result.message);
        setMode('reset');
        return;
      }

      if (mode === 'reset') {
        if (!isStrongPassword(password)) {
          setError('New password must be strong: 10+ characters, uppercase, lowercase, number and special character.');
          return;
        }
        const result = await authApi.resetPassword({ email, otp, new_password: password });
        setMessage(result.message);
        setMode('signin');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    }
  }

  const title = {
    signin: 'Welcome back',
    signup: 'Create your account',
    verify: 'Verify your email',
    forgot: 'Reset your password',
    reset: 'Choose a new password',
  }[mode];

  return (
    <main className="auth-page">
      <section className="auth-card">
        <Link to="/" className="brand">Nestora</Link>
        <span className="eyebrow">Secure account access</span>
        <h1>{title}</h1>

        <form onSubmit={submit} className="auth-form">
          {mode === 'signup' && (
            <label>
              Full name
              <input value={fullName} onChange={(e) => setFullName(e.target.value)} required />
            </label>
          )}

          <label>
            Email
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </label>

          {(mode === 'signin' || mode === 'signup' || mode === 'reset') && (
            <label>
              {mode === 'reset' ? 'New password' : 'Password'}
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
              {(mode === 'signup' || mode === 'reset') && (
                <small>10+ characters, uppercase, lowercase, number and special character.</small>
              )}
            </label>
          )}

          {(mode === 'verify' || mode === 'reset') && (
            <label>
              6-digit OTP
              <input
                inputMode="numeric"
                maxLength={6}
                value={otp}
                onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                required
              />
            </label>
          )}

          {error && <div className="auth-error">{error}</div>}
          {message && <div className="auth-success">{message}</div>}

          <button className="primary" type="submit">
            {mode === 'signin' && 'Sign in'}
            {mode === 'signup' && 'Create account'}
            {mode === 'verify' && 'Verify email'}
            {mode === 'forgot' && 'Send reset OTP'}
            {mode === 'reset' && 'Change password'}
          </button>
        </form>

        {mode === 'signin' && (
          <button className="auth-link" onClick={() => setMode('forgot')}>Forgot password?</button>
        )}

        {mode === 'verify' && (
          <button
            className="auth-link"
            onClick={() => authApi.resendOtp(email).then((r) => setMessage(r.message)).catch((e) => setError(e.message))}
          >
            Resend OTP
          </button>
        )}

        <button className="auth-link" onClick={() => setMode(mode === 'signup' ? 'signin' : 'signup')}>
          {mode === 'signup' ? 'Already have an account? Sign in' : 'New to Nestora? Create account'}
        </button>
      </section>
    </main>
  );
}

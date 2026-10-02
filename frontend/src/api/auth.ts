import type { CurrentUser } from '../lib/auth';
import { API_BASE_URL, apiRequest, authHeaders } from './client';

export const authApi = {
  register: (payload: {
    full_name: string;
    email: string;
    password: string;
    account_type: 'user' | 'owner';
  }) =>
    apiRequest('/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  verifyEmail: (payload: { email: string; otp: string }) =>
    apiRequest<{ message: string }>('/auth/verify-email', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  resendOtp: (email: string) =>
    apiRequest<{ message: string }>('/auth/resend-verification-otp', {
      method: 'POST',
      body: JSON.stringify({ email }),
    }),

  login: async (email: string, password: string) => {
    const response = await fetch(API_BASE_URL + '/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ username: email, password }),
      credentials: 'include',
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail ?? 'Unable to sign in');
    }

    return data as { access_token: string; token_type: string };
  },

  logout: () =>
    apiRequest<{ ok: boolean }>('/auth/logout', {
      method: 'POST',
    }),

  me: () =>
    apiRequest<CurrentUser>('/auth/me', {
      headers: authHeaders(),
    }),

  forgotPassword: (email: string) =>
    apiRequest<{ message: string }>('/auth/forgot-password', {
      method: 'POST',
      body: JSON.stringify({ email }),
    }),

  resetPassword: (payload: {
    email: string;
    otp: string;
    new_password: string;
  }) =>
    apiRequest<{ message: string }>('/auth/reset-password', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};

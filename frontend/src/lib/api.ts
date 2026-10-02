import type { CurrentUser } from './auth';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1';

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(API_BASE + path, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...(options.headers ?? {}) },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail ?? 'Something went wrong');
  return data as T;
}

function authHeaders() {
  const token = localStorage.getItem('nestora_access_token');
  if (!token) throw new Error('Please sign in first');
  return { Authorization: `Bearer ${token}` };
}

export const authApi = {
  register: (payload: { full_name: string; email: string; password: string; account_type: 'user' | 'owner' }) =>
    request('/auth/register', { method: 'POST', body: JSON.stringify(payload) }),

  verifyEmail: (payload: { email: string; otp: string }) =>
    request<{ message: string }>('/auth/verify-email', { method: 'POST', body: JSON.stringify(payload) }),

  resendOtp: (email: string) =>
    request<{ message: string }>('/auth/resend-verification-otp', {
      method: 'POST',
      body: JSON.stringify({ email }),
    }),

  login: async (email: string, password: string) => {
    const response = await fetch(API_BASE + '/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ username: email, password }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail ?? 'Unable to sign in');
    return data as { access_token: string; token_type: string };
  },

  me: () =>
    request<CurrentUser>('/auth/me', {
      headers: authHeaders(),
    }),

  forgotPassword: (email: string) =>
    request<{ message: string }>('/auth/forgot-password', {
      method: 'POST',
      body: JSON.stringify({ email }),
    }),

  resetPassword: (payload: { email: string; otp: string; new_password: string }) =>
    request<{ message: string }>('/auth/reset-password', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};

export type OwnerProperty = {
  id: number;
  title: string;
  city: string;
  state: string;
  price_per_night: number;
  status: 'draft' | 'pending' | 'live' | 'rejected' | 'paused';
  image_urls: string[];
  rejection_reason?: string | null;
};

export const ownerApi = {
  listProperties: () =>
    request<OwnerProperty[]>('/owner/properties', {
      headers: authHeaders(),
    }),

  uploadImage: async (file: File) => {
    const token = localStorage.getItem('nestora_access_token');
    if (!token) throw new Error('Please sign in first');

    const body = new FormData();
    body.append('file', file);

    const response = await fetch(API_BASE + '/owner/uploads/images', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body,
    });

    const data = await response.json();
    if (!response.ok) throw new Error(data.detail ?? 'Image upload failed');
    return data as { url: string };
  },

  createProperty: (payload: unknown) =>
    request('/owner/properties', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(payload),
    }),
};

export type ReviewableBooking = {
  id: number;
  property_id: number;
  check_in: string;
  check_out: string;
};

export const reviewApi = {
  reviewableBookings: () =>
    request<ReviewableBooking[]>('/bookings/reviewable', {
      headers: authHeaders(),
    }),

  create: (propertyId: number, payload: { booking_id: number; rating: number; comment: string }) =>
    request('/reviews/properties/' + propertyId, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(payload),
    }),
};


export type TransferPlace = {
  name: string;
  full_address: string;
  latitude: number;
  longitude: number;
};

export type TransferQuote = {
  property_id: number;
  direction: 'pickup_to_stay' | 'stay_to_dropoff';
  place_type: 'airport' | 'railway' | 'bus_stand' | 'custom';
  place_name: string;
  latitude: number;
  longitude: number;
  distance_km: number;
  duration_minutes: number;
  estimated_fare: number;
  currency: string;
  route_geometry: { type: 'LineString'; coordinates: number[][] };
  pricing_note: string;
};

export const transferApi = {
  searchPlaces: (query: string, propertyId: number) =>
    request<TransferPlace[]>('/transfers/places?q=' + encodeURIComponent(query) + '&property_id=' + propertyId),

  quote: (payload: {
    property_id: number;
    direction: 'pickup_to_stay' | 'stay_to_dropoff';
    place_type: 'airport' | 'railway' | 'bus_stand' | 'custom';
    place_name: string;
    latitude: number;
    longitude: number;
    stay_latitude?: number;
    stay_longitude?: number;
  }) =>
    request<TransferQuote>('/transfers/quote', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};

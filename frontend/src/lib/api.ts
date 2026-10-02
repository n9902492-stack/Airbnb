import type { CurrentUser } from './auth';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1';

async function refreshAccessToken(): Promise<string | null> {
  const response = await fetch(API_BASE + '/auth/refresh', {
    method: 'POST',
    credentials: 'include',
  });
  if (!response.ok) return null;
  const data = await response.json() as { access_token: string };
  localStorage.setItem('nestora_access_token', data.access_token);
  return data.access_token;
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  retry = true,
): Promise<T> {
  const response = await fetch(API_BASE + path, {
    ...options,
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...(options.headers ?? {}) },
  });

  if (response.status === 401 && retry && path !== '/auth/refresh') {
    const token = await refreshAccessToken();
    if (token) {
      const headers = new Headers(options.headers ?? {});
      headers.set('Authorization', 'Bearer ' + token);
      return request<T>(path, { ...options, headers }, false);
    }
  }

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
      credentials: 'include',
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail ?? 'Unable to sign in');
    return data as { access_token: string; token_type: string };
  },

  logout: () =>
    request<{ ok: boolean }>('/auth/logout', {
      method: 'POST',
    }),

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
  weekend_price_per_night?: number | null;
  minimum_stay_nights?: number;
  maximum_stay_nights?: number | null;
  status: 'draft' | 'pending' | 'live' | 'rejected' | 'paused';
  booking_mode?: 'instant' | 'request';
  guest_favorite?: boolean;
  image_urls: string[];
  rejection_reason?: string | null;
};

export const ownerApi = {
  listProperties: () =>
    request<OwnerProperty[]>('/owner/properties', {
      headers: authHeaders(),
    }),

  uploadImage: async (file: File) => {
    let token = localStorage.getItem('nestora_access_token');
    if (!token) throw new Error('Please sign in first');

    const upload = () => {
      const body = new FormData();
      body.append('file', file);
      return fetch(API_BASE + '/owner/uploads/images', {
        method: 'POST',
        credentials: 'include',
        headers: { Authorization: `Bearer ${token}` },
        body,
      });
    };

    let response = await upload();
    if (response.status === 401) {
      const refreshed = await refreshAccessToken();
      if (refreshed) {
        token = refreshed;
        response = await upload();
      }
    }

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
  list: (propertyId: number) =>
    request<{
      average_rating: number;
      review_count: number;
      reviews: Array<{
        id: number;
        property_id: number;
        booking_id: number;
        guest_id: number;
        rating: number;
        comment: string;
        created_at: string;
        guest_name?: string | null;
      }>;
    }>('/reviews/properties/' + propertyId),

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
  createForBooking: (payload: {
    booking_id: number;
    property_id: number;
    direction: 'pickup_to_stay' | 'stay_to_dropoff';
    place_type: 'airport' | 'railway' | 'bus_stand' | 'custom';
    place_name: string;
    latitude: number;
    longitude: number;
  }) =>
    request('/transfers', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(payload),
    }),

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


export type AvailabilityResponse = {
  property_id: number;
  blocked_dates: string[];
};

export type BookingResult = {
  id: number;
  property_id: number;
  guest_id: number;
  check_in: string;
  check_out: string;
  guest_count: number;
  subtotal: number;
  service_fee: number;
  total_amount: number;
  status: 'requested' | 'pending' | 'confirmed' | 'cancelled' | 'completed';
};

export const bookingApi = {
  availability: (propertyId: number, start: string, days = 180) =>
    request<AvailabilityResponse>(
      '/availability/properties/' + propertyId + '?start=' + encodeURIComponent(start) + '&days=' + days
    ),

  create: (payload: { property_id: number; check_in: string; check_out: string; guest_count: number }) =>
    request<BookingResult>('/bookings', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(payload),
    }),

  myTrips: () =>
    request<Array<{
      id: number;
      property_id: number;
      property_title: string;
      check_in: string;
      check_out: string;
      guest_count: number;
      total_amount: number;
      status: string;
      expires_at?: string | null;
      payment_status?: string | null;
    }>>('/bookings/my-trips', {
      headers: authHeaders(),
    }),

  cancel: (bookingId: number, reason = 'Guest cancelled') =>
    request<{
      booking_id: number;
      status: string;
      refund_amount: number;
      refund_percent: number;
      message: string;
    }>('/bookings/' + bookingId + '/cancel?reason=' + encodeURIComponent(reason), {
      method: 'POST',
      headers: authHeaders(),
    }),
};

export type CheckoutPreview = {
  booking_id: number;
  stay_subtotal: number;
  service_fee: number;
  transfer_fee: number;
  gst_rate: number;
  gst_amount: number;
  grand_total: number;
  currency: string;
};

export type PaymentResult = {
  id: number;
  booking_id: number;
  amount: number;
  currency: string;
  status: string;
};

export type PaymentSession = PaymentResult & {
  provider: 'razorpay' | 'manual_demo';
  razorpay_key_id?: string | null;
  provider_order_id?: string | null;
  amount_paise?: number | null;
};

export const paymentApi = {
  preview: (bookingId: number) =>
    request<CheckoutPreview>('/payments/checkout/' + bookingId, {
      headers: authHeaders(),
    }),

  create: (bookingId: number) =>
    request<PaymentSession>('/payments/checkout/' + bookingId, {
      method: 'POST',
      headers: authHeaders(),
    }),

  verifyRazorpay: (
    paymentId: number,
    payload: {
      razorpay_order_id: string;
      razorpay_payment_id: string;
      razorpay_signature: string;
    },
  ) =>
    request<PaymentResult>('/payments/' + paymentId + '/verify-razorpay', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(payload),
    }),

  demoConfirm: (paymentId: number) =>
    request<PaymentResult>('/payments/' + paymentId + '/demo-confirm', {
      method: 'POST',
      headers: authHeaders(),
    }),
};

export type PendingProperty = {
  id: number;
  title: string;
  owner_id: number;
  city: string;
  state: string;
  price_per_night: number;
  image_urls: string[];
  created_at: string;
};

export const adminApi = {
  auditLogs: (limit = 50) =>
    request<Array<{
      id: number;
      actor_user_id?: number | null;
      action: string;
      entity_type?: string | null;
      entity_id?: string | null;
      request_id?: string | null;
      ip_address?: string | null;
      metadata: Record<string, unknown>;
      created_at: string;
    }>>('/super-admin/audit-logs?limit=' + limit, {
      headers: authHeaders(),
    }),

  overview: () =>
    request<{ users: number; owners: number; listings: number; bookings: number }>('/super-admin/overview', {
      headers: authHeaders(),
    }),

  pendingOfferings: () =>
    request<Array<{
      id:number;
      host_id:number;
      kind:string;
      title:string;
      category:string;
      city:string;
      state:string;
      price:number;
      image_urls:string[];
    }>>('/super-admin/offerings/pending', {
      headers: authHeaders(),
    }),

  approveOffering: (id: number) =>
    request('/super-admin/offerings/' + id + '/approve', {
      method: 'POST',
      headers: authHeaders(),
    }),

  rejectOffering: (id: number, reason: string) =>
    request('/super-admin/offerings/' + id + '/reject?reason=' + encodeURIComponent(reason), {
      method: 'POST',
      headers: authHeaders(),
    }),

  pendingProperties: () =>
    request<PendingProperty[]>('/super-admin/properties/pending', {
      headers: authHeaders(),
    }),

  approveProperty: (propertyId: number) =>
    request('/super-admin/properties/' + propertyId + '/approve', {
      method: 'POST',
      headers: authHeaders(),
    }),

  rejectProperty: (propertyId: number, reason: string) =>
    request('/super-admin/properties/' + propertyId + '/reject?reason=' + encodeURIComponent(reason), {
      method: 'POST',
      headers: authHeaders(),
    }),
};

export const ownerManagementApi = {
  getProperties: () => ownerApi.listProperties(),

  updateProperty: (propertyId: number, payload: unknown) =>
    request<OwnerProperty>('/owner/properties/' + propertyId, {
      method: 'PATCH',
      headers: authHeaders(),
      body: JSON.stringify(payload),
    }),

  blockDates: (propertyId: number, payload: { start_date: string; end_date: string; reason: string }) =>
    request('/owner/properties/' + propertyId + '/availability-blocks', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(payload),
    }),

  pricingRules: (propertyId: number) =>
    request<Array<{
      id: number;
      name: string;
      start_date: string;
      end_date: string;
      nightly_rate: number;
      minimum_stay_nights?: number | null;
    }>>('/owner/properties/' + propertyId + '/pricing-rules', {
      headers: authHeaders(),
    }),

  createPricingRule: (
    propertyId: number,
    payload: {
      name: string;
      start_date: string;
      end_date: string;
      nightly_rate: number;
      minimum_stay_nights?: number | null;
    },
  ) =>
    request('/owner/properties/' + propertyId + '/pricing-rules', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(payload),
    }),

  deletePricingRule: (propertyId: number, ruleId: number) =>
    request('/owner/properties/' + propertyId + '/pricing-rules/' + ruleId, {
      method: 'DELETE',
      headers: authHeaders(),
    }),

  payoutAccount: () =>
    request<{
      configured: boolean;
      provider: string;
      linked_account_id?: string;
      status?: string;
    }>('/owner/payout-account', {
      headers: authHeaders(),
    }),

  payouts: () =>
    request<{
      pending: number;
      paid: number;
      commission: number;
      payouts: Array<{
        id: number;
        booking_id: number;
        gross_amount: number;
        platform_commission: number;
        owner_amount: number;
        refund_adjustment: number;
        status: string;
        created_at: string;
        paid_at?: string | null;
      }>;
    }>('/owner/payouts', {
      headers: authHeaders(),
    }),

  acceptBookingRequest: (bookingId: number) =>
    request('/owner/booking-requests/' + bookingId + '/accept', {
      method: 'POST',
      headers: authHeaders(),
    }),

  declineBookingRequest: (bookingId: number) =>
    request('/owner/booking-requests/' + bookingId + '/decline', {
      method: 'POST',
      headers: authHeaders(),
    }),

  reservations: () =>
    request<Array<{
      booking_id: number;
      property_id: number;
      property_title: string;
      guest_id: number;
      guest_name: string;
      check_in: string;
      check_out: string;
      guest_count: number;
      total_amount: number;
      status: string;
    }>>('/owner/reservations', {
      headers: authHeaders(),
    }),
};


export type PublicProperty = {
  id: number;
  owner_id: number;
  title: string;
  description: string;
  property_type: string;
  category: string;
  address_line: string;
  city: string;
  state: string;
  country: string;
  postal_code: string;
  latitude?: number | null;
  longitude?: number | null;
  guests: number;
  bedrooms: number;
  beds: number;
  bathrooms: number;
  price_per_night: number;
  cleaning_fee: number;
  weekend_price_per_night?: number | null;
  minimum_stay_nights?: number;
  maximum_stay_nights?: number | null;
  amenities: string[];
  house_rules: string[];
  image_urls: string[];
  check_in_time: string;
  check_out_time: string;
  status: string;
  rejection_reason?: string | null;
  booking_mode: 'instant' | 'request';
  guest_favorite: boolean;
};

export const propertyApi = {
  search: (params: {
    q?: string;
    city?: string;
    category?: string;
    guests?: number;
    bedrooms?: number;
    beds?: number;
    bathrooms?: number;
    property_type?: string;
    instant_book?: boolean;
    guest_favorite?: boolean;
    amenities?: string[];
    min_price?: number;
    max_price?: number;
    min_lat?: number;
    max_lat?: number;
    min_lng?: number;
    max_lng?: number;
  } = {}) => {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== '' && value !== null) {
        if (Array.isArray(value)) {
          value.forEach((item) => qs.append(key, String(item)));
        } else {
          qs.set(key, String(value));
        }
      }
    });
    const suffix = qs.toString() ? '?' + qs.toString() : '';
    return request<PublicProperty[]>('/properties' + suffix);
  },

  get: (propertyId: number) =>
    request<PublicProperty>('/properties/' + propertyId),
};

export type WishlistItem = {
  id: number;
  property_id: number;
  title: string;
  city: string;
  state: string;
  price_per_night: number;
  image_urls: string[];
};

export const wishlistApi = {
  list: () =>
    request<WishlistItem[]>('/wishlist', {
      headers: authHeaders(),
    }),

  add: (propertyId: number) =>
    request('/wishlist/' + propertyId, {
      method: 'POST',
      headers: authHeaders(),
    }),

  remove: (propertyId: number) =>
    request('/wishlist/' + propertyId, {
      method: 'DELETE',
      headers: authHeaders(),
    }),
};

export type BookingMessage = {
  id: number;
  booking_id: number;
  sender_id: number;
  sender_name: string;
  body: string;
  created_at: string;
};

export const messageApi = {
  list: (bookingId: number) =>
    request<BookingMessage[]>('/messages/' + bookingId, {
      headers: authHeaders(),
    }),

  send: (bookingId: number, body: string) =>
    request<BookingMessage>('/messages/' + bookingId, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ body }),
    }),
};

export type NotificationItem = {
  id: number;
  kind: string;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
};

export const notificationApi = {
  list: () =>
    request<NotificationItem[]>('/notifications', {
      headers: authHeaders(),
    }),

  markRead: (notificationId: number) =>
    request('/notifications/' + notificationId + '/read', {
      method: 'POST',
      headers: authHeaders(),
    }),
};

export type OwnerEarnings = {
  gross: number;
  refunded: number;
  net: number;
  transactions: Array<{
    booking_id: number;
    property_title: string;
    amount: number;
    refund_amount: number;
    net_amount: number;
    status: string;
    created_at: string;
  }>;
};

export const earningsApi = {
  owner: () =>
    request<OwnerEarnings>('/owner/earnings', {
      headers: authHeaders(),
    }),
};

export type AdminBooking = {
  booking_id: number;
  property_title: string;
  guest_name: string;
  check_in: string;
  check_out: string;
  status: string;
  total_amount: number;
  payment_status?: string | null;
  refund_amount: number;
};

export const adminBookingApi = {
  list: () =>
    request<AdminBooking[]>('/super-admin/bookings', {
      headers: authHeaders(),
    }),

  cancel: (bookingId: number, reason = 'Cancelled by platform administrator') =>
    request('/super-admin/bookings/' + bookingId + '/cancel?reason=' + encodeURIComponent(reason), {
      method: 'POST',
      headers: authHeaders(),
    }),
};


export type AdminFinance = {
  collected: number;
  refunds: number;
  platform_commission: number;
  owner_payable: number;
  owner_paid: number;
  payouts: Array<{
    id: number;
    booking_id: number;
    owner_id: number;
    owner_amount: number;
    platform_commission: number;
    status: string;
  }>;
};

export const financeApi = {
  setOwnerPayoutAccount: (ownerId: number, linkedAccountId: string) =>
    request('/super-admin/owners/' + ownerId + '/payout-account', {
      method: 'PUT',
      headers: authHeaders(),
      body: JSON.stringify({ linked_account_id: linkedAccountId }),
    }),

  admin: () =>
    request<AdminFinance>('/super-admin/finance', {
      headers: authHeaders(),
    }),

  markPayoutPaid: (payoutId: number, providerReference?: string) => {
    const suffix = providerReference
      ? '?provider_reference=' + encodeURIComponent(providerReference)
      : '';
    return request('/super-admin/payouts/' + payoutId + '/mark-paid' + suffix, {
      method: 'POST',
      headers: authHeaders(),
    });
  },
};


export const invoiceApi = {
  get: (bookingId: number) =>
    request<{
      invoice_number: string;
      booking_id: number;
      taxable_amount: number;
      gst_rate: number;
      gst_amount: number;
      total_amount: number;
      currency: string;
      issued_at: string;
    }>('/invoices/' + bookingId, {
      headers: authHeaders(),
    }),
};


export type MarketplaceOffering = {
  id: number;
  host_id: number;
  kind: 'service' | 'experience';
  title: string;
  description: string;
  category: string;
  city: string;
  state: string;
  country: string;
  latitude?: number | null;
  longitude?: number | null;
  price: number;
  pricing_unit: 'per_guest' | 'per_group' | 'per_session';
  duration_minutes: number;
  capacity: number;
  image_urls: string[];
  included_items: string[];
  requirements: string[];
  instant_book: boolean;
  status: string;
};

export const offeringApi = {
  list: (params: { kind?: 'service' | 'experience'; q?: string; city?: string; category?: string } = {}) => {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value) qs.set(key, String(value));
    });
    return request<MarketplaceOffering[]>('/offerings' + (qs.toString() ? '?' + qs.toString() : ''));
  },

  get: (id: number) => request<MarketplaceOffering>('/offerings/' + id),

  create: (payload: unknown) =>
    request<MarketplaceOffering>('/offerings', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(payload),
    }),

  mine: () =>
    request<MarketplaceOffering[]>('/offerings/host/mine', {
      headers: authHeaders(),
    }),

  book: (id: number, payload: { scheduled_at: string; guest_count: number }) =>
    request<{
      id: number;
      status: string;
      payment_status: string;
      message?: string;
      amount?: number;
      currency?: string;
      provider?: 'razorpay' | 'manual_demo';
      provider_order_id?: string | null;
      razorpay_key_id?: string | null;
      amount_paise?: number;
    }>('/offerings/' + id + '/book', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(payload),
    }),

  confirmDemo: (bookingId: number) =>
    request('/offerings/bookings/' + bookingId + '/demo-confirm', {
      method: 'POST',
      headers: authHeaders(),
    }),

  mineBookings: () =>
    request<Array<{
      id: number;
      offering_id: number;
      title: string;
      kind: string;
      scheduled_at: string;
      guest_count: number;
      total_amount: number;
      status: string;
      payment_status: string;
    }>>('/offerings/bookings/mine', {
      headers: authHeaders(),
    }),
};

export const hostApi = {
  get: (id: number) =>
    request<{
      id: number;
      full_name: string;
      joined_at: string;
      bio?: string | null;
      avatar_url?: string | null;
      languages: string[];
      interests: string[];
      work?: string | null;
      verified_identity: boolean;
      response_rate: number;
      response_time_label: string;
      live_listings: number;
      average_rating: number;
    }>('/hosts/' + id),

  updateMine: (payload: unknown) =>
    request('/hosts/me/profile', {
      method: 'PUT',
      headers: authHeaders(),
      body: JSON.stringify(payload),
    }),
};

export const collaborationApi = {
  cohosts: (propertyId: number) =>
    request<Array<{ id:number; user_id:number; name:string; email:string; permission:string }>>(
      '/collaboration/properties/' + propertyId + '/cohosts',
      { headers: authHeaders() },
    ),

  addCohost: (propertyId: number, email: string, permission: 'calendar' | 'messages' | 'full') =>
    request('/collaboration/properties/' + propertyId + '/cohosts', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ email, permission }),
    }),

  removeCohost: (propertyId: number, cohostId: number) =>
    request('/collaboration/properties/' + propertyId + '/cohosts/' + cohostId, {
      method: 'DELETE',
      headers: authHeaders(),
    }),

  createWishlist: (name: string) =>
    request<{ id:number; name:string; share_token:string }>('/collaboration/wishlists', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ name }),
    }),

  wishlists: () =>
    request<Array<{ id:number; name:string; share_token?:string | null; owner_user_id:number }>>(
      '/collaboration/wishlists',
      { headers: authHeaders() },
    ),

  addWishlistItem: (collectionId: number, propertyId: number) =>
    request('/collaboration/wishlists/' + collectionId + '/items', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ property_id: propertyId }),
    }),

  joinWishlist: (shareToken: string) =>
    request('/collaboration/wishlists/join/' + encodeURIComponent(shareToken), {
      method: 'POST',
      headers: authHeaders(),
    }),

  specialOffers: () =>
    request<Array<{
      id:number;
      property_id:number;
      property_title:string;
      check_in:string;
      check_out:string;
      guest_count:number;
      total_price:number;
      status:string;
      expires_at:string;
    }>>('/collaboration/special-offers/mine', {
      headers: authHeaders(),
    }),

  acceptSpecialOffer: (offerId: number) =>
    request<{ booking_id:number; status:string }>('/collaboration/special-offers/' + offerId + '/accept', {
      method: 'POST',
      headers: authHeaders(),
    }),
};

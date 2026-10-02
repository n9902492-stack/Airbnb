import {
  apiRequest as request,
  authHeaders,
  uploadFileWithAuth,
} from '../api/client';

export { authApi } from '../api/auth';
export { bookingApi } from '../api/bookings';
export type { AvailabilityResponse, BookingResult } from '../api/bookings';
export { propertyApi } from '../api/property';
export type { PublicProperty, PropertySearchParams } from '../api/property';

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

  uploadImage: (file: File) =>
    uploadFileWithAuth<{ url: string }>('/owner/uploads/images', file),

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


export type CheckoutPreview = {
  booking_id: number;
  stay_subtotal: number;
  service_fee: number;
  transfer_fee: number;
  discount_amount: number;
  promo_code?: string | null;
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
  preview: (bookingId: number, promoCode?: string) => {
    const suffix = promoCode ? '?promo_code=' + encodeURIComponent(promoCode) : '';
    return request<CheckoutPreview>('/payments/checkout/' + bookingId + suffix, {
      headers: authHeaders(),
    });
  },

  create: (bookingId: number, promoCode?: string) => {
    const suffix = promoCode ? '?promo_code=' + encodeURIComponent(promoCode) : '';
    return request<PaymentSession>('/payments/checkout/' + bookingId + suffix, {
      method: 'POST',
      headers: authHeaders(),
    });
  },

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
  attachment_url?: string | null;
  read_at?: string | null;
  created_at: string;
};

export const messageApi = {
  list: (bookingId: number) =>
    request<BookingMessage[]>('/messages/' + bookingId, {
      headers: authHeaders(),
    }),

  send: (bookingId: number, body: string, attachmentUrl?: string | null) =>
    request<BookingMessage>('/messages/' + bookingId, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ body, attachment_url: attachmentUrl ?? null }),
    }),

  markRead: (bookingId: number) =>
    request('/messages/' + bookingId + '/read', {
      method: 'POST',
      headers: authHeaders(),
    }),

  uploadImage: (file: File) =>
    uploadFileWithAuth<{ url: string }>('/messages/uploads/image', file),
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

  get: (id: number) => request<MarketplaceOffering>('/offerings/items/' + id),

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

  hostBookings: () =>
    request<Array<{
      id:number;
      offering_id:number;
      title:string;
      kind:string;
      guest_id:number;
      guest_name:string;
      scheduled_at:string;
      guest_count:number;
      total_amount:number;
      status:string;
      payment_status:string;
    }>>('/offerings/host/bookings', {
      headers: authHeaders(),
    }),

  acceptRequest: (bookingId: number) =>
    request('/offerings/bookings/' + bookingId + '/accept', {
      method: 'POST',
      headers: authHeaders(),
    }),

  declineRequest: (bookingId: number) =>
    request('/offerings/bookings/' + bookingId + '/decline', {
      method: 'POST',
      headers: authHeaders(),
    }),

  book: (id: number, payload: { slot_id?: number; scheduled_at?: string; guest_count: number; private_group?: boolean }) =>
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
    }>('/offerings/items/' + id + '/book', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(payload),
    }),

  confirmDemo: (bookingId: number) =>
    request('/offerings/bookings/' + bookingId + '/demo-confirm', {
      method: 'POST',
      headers: authHeaders(),
    }),

  slots: (id: number) =>
    request<Array<{
      id:number;
      starts_at:string;
      ends_at:string;
      capacity:number;
      price_override?:number|null;
      private_group_price?:number|null;
      is_private_available:boolean;
    }>>('/offerings/items/' + id + '/slots'),

  createSlot: (id: number, payload: unknown) =>
    request('/offerings/items/' + id + '/slots', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(payload),
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

  createWishlist: (
    name: string,
    planning?: { proposed_start_date?: string; proposed_end_date?: string; guest_count?: number },
  ) =>
    request<{ id:number; name:string; share_token:string }>('/collaboration/wishlists', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ name, ...(planning ?? {}) }),
    }),

  wishlists: () =>
    request<Array<{
      id:number; name:string; share_token?:string | null; owner_user_id:number;
      proposed_start_date?:string|null; proposed_end_date?:string|null; guest_count?:number|null;
    }>>(
      '/collaboration/wishlists',
      { headers: authHeaders() },
    ),

  wishlistDetail: (collectionId: number) =>
    request<{
      id:number; name:string; proposed_start_date?:string|null; proposed_end_date?:string|null;
      guest_count?:number|null; items:Array<{
        id:number; property_id:number; title:string; city:string; state:string;
        image_urls:string[]; price_per_night:number; note?:string|null; vote_score:number;
      }>;
    }>('/collaboration/wishlists/' + collectionId, { headers:authHeaders() }),

  updateWishlist: (collectionId:number, payload:unknown) =>
    request('/collaboration/wishlists/' + collectionId, {
      method:'PATCH', headers:authHeaders(), body:JSON.stringify(payload),
    }),

  addWishlistItem: (collectionId: number, propertyId: number, note?:string) =>
    request('/collaboration/wishlists/' + collectionId + '/items', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ property_id: propertyId, note:note ?? null }),
    }),

  updateWishlistNote: (collectionId:number, itemId:number, note:string) =>
    request('/collaboration/wishlists/' + collectionId + '/items/' + itemId + '/note', {
      method:'PATCH', headers:authHeaders(), body:JSON.stringify({note}),
    }),

  voteWishlistItem: (collectionId:number, itemId:number, value:-1|0|1) =>
    request('/collaboration/wishlists/' + collectionId + '/items/' + itemId + '/vote', {
      method:'POST', headers:authHeaders(), body:JSON.stringify({value}),
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


export const trustApi = {
  identity: () =>
    request<{
      status:string;
      verified:boolean;
      provider?:string;
      document_type?:string|null;
      rejection_reason?:string|null;
      submitted_at?:string|null;
      verified_at?:string|null;
    }>('/trust/identity', { headers: authHeaders() }),

  startIdentity: (documentType: string, providerReference?: string) =>
    request('/trust/identity/start', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        document_type: documentType,
        provider_reference: providerReference ?? null,
      }),
    }),

  mySupport: () =>
    request<Array<{
      id:number; booking_id?:number|null; case_type:string; subject:string;
      description:string; status:string; priority:string; resolution?:string|null; created_at:string;
    }>>('/trust/support/mine', { headers: authHeaders() }),

  createSupport: (payload: unknown) =>
    request('/trust/support', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(payload),
    }),

  myClaims: () =>
    request<Array<{
      id:number; booking_id:number; claimant_id:number; respondent_id:number;
      amount:number; reason:string; evidence_urls:string[]; status:string;
      response_note?:string|null; created_at:string;
    }>>('/trust/claims/mine', { headers: authHeaders() }),

  createClaim: (payload: unknown) =>
    request('/trust/claims', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(payload),
    }),

  respondClaim: (claimId: number, status: 'accepted'|'declined', responseNote?: string) =>
    request('/trust/claims/' + claimId + '/respond', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ status, response_note: responseNote ?? null }),
    }),

  pendingIdentity: () =>
    request<Array<{
      id:number; user_id:number; name:string; email:string; document_type?:string|null;
      provider:string; provider_reference?:string|null; submitted_at?:string|null;
    }>>('/trust/admin/identity', { headers: authHeaders() }),

  approveIdentity: (id:number) =>
    request('/trust/admin/identity/' + id + '/approve', {
      method:'POST', headers:authHeaders(),
    }),

  rejectIdentity: (id:number, reason:string) =>
    request('/trust/admin/identity/' + id + '/reject?reason=' + encodeURIComponent(reason), {
      method:'POST', headers:authHeaders(),
    }),

  adminSupport: () =>
    request<Array<{
      id:number; reporter_id:number; reporter_name:string; booking_id?:number|null;
      case_type:string; subject:string; status:string; priority:string; created_at:string;
    }>>('/trust/admin/support', { headers:authHeaders() }),

  updateSupport: (id:number, status:string, resolution?:string) =>
    request('/trust/admin/support/' + id, {
      method:'PATCH', headers:authHeaders(),
      body:JSON.stringify({ status, resolution:resolution ?? null }),
    }),
};

export const promotionApi = {
  list: () =>
    request<Array<{
      id:number; code:string; discount_type:string; discount_value:number;
      minimum_spend:number; valid_from?:string|null; valid_until?:string|null;
      max_uses?:number|null; used_count:number; active:boolean;
    }>>('/promotions', { headers:authHeaders() }),

  create: (payload: unknown) =>
    request('/promotions', {
      method:'POST', headers:authHeaders(), body:JSON.stringify(payload),
    }),

  toggle: (id:number) =>
    request('/promotions/' + id + '/toggle', {
      method:'POST', headers:authHeaders(),
    }),
};

export const messageToolsApi = {
  templates: () =>
    request<Array<{id:number;title:string;body:string}>>('/message-tools/templates', {
      headers:authHeaders(),
    }),
  createTemplate: (title:string, body:string) =>
    request('/message-tools/templates', {
      method:'POST', headers:authHeaders(), body:JSON.stringify({title,body}),
    }),
  schedule: (bookingId:number, body:string, sendAt:string) =>
    request('/message-tools/scheduled', {
      method:'POST', headers:authHeaders(),
      body:JSON.stringify({booking_id:bookingId,body,send_at:sendAt}),
    }),
};


export type BookingChangeRequest = {
  id:number;
  booking_id:number;
  new_check_in:string;
  new_check_out:string;
  new_guest_count:number;
  old_total_amount:number;
  new_total_amount:number;
  price_difference:number;
  status:string;
  adjustment?: {
    id:number;
    amount:number;
    provider:'razorpay'|'manual_demo';
    status:string;
    provider_order_id?:string|null;
    razorpay_key_id?:string|null;
    amount_paise?:number;
  } | null;
};

export const bookingChangeApi = {
  create: (bookingId:number, payload:{check_in:string;check_out:string;guest_count:number}) =>
    request<{id:number;status:string;new_total_amount:number;price_difference:number}>(
      '/booking-changes/' + bookingId,
      { method:'POST', headers:authHeaders(), body:JSON.stringify(payload) },
    ),

  mine: () =>
    request<BookingChangeRequest[]>('/booking-changes/mine/requests', {
      headers:authHeaders(),
    }),

  host: () =>
    request<Array<{
      id:number; booking_id:number; property_title:string; guest_name:string;
      new_check_in:string; new_check_out:string; new_guest_count:number; price_difference:number;
    }>>('/booking-changes/host/requests', { headers:authHeaders() }),

  accept: (id:number) =>
    request<{
      id:number;status:string;adjustment_payment_id?:number;amount?:number;
      provider?:'razorpay'|'manual_demo';provider_order_id?:string|null;
      razorpay_key_id?:string|null;amount_paise?:number;
    }>('/booking-changes/' + id + '/accept', {
      method:'POST', headers:authHeaders(),
    }),

  decline: (id:number) =>
    request('/booking-changes/' + id + '/decline', {
      method:'POST', headers:authHeaders(),
    }),

  confirmDemoAdjustment: (id:number) =>
    request('/booking-changes/adjustments/' + id + '/demo-confirm', {
      method:'POST', headers:authHeaders(),
    }),

  verifyAdjustment: (
    id:number,
    payload:{razorpay_order_id:string;razorpay_payment_id:string;razorpay_signature:string},
  ) =>
    request('/booking-changes/adjustments/' + id + '/verify-razorpay', {
      method:'POST', headers:authHeaders(), body:JSON.stringify(payload),
    }),
};

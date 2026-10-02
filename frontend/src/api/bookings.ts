import { apiRequest, authHeaders } from './client';

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
    apiRequest<AvailabilityResponse>(
      '/availability/properties/' +
        propertyId +
        '?start=' +
        encodeURIComponent(start) +
        '&days=' +
        days,
    ),

  create: (payload: {
    property_id: number;
    check_in: string;
    check_out: string;
    guest_count: number;
  }) =>
    apiRequest<BookingResult>('/bookings', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(payload),
    }),

  myTrips: () =>
    apiRequest<
      Array<{
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
      }>
    >('/bookings/my-trips', {
      headers: authHeaders(),
    }),

  cancel: (bookingId: number, reason = 'Guest cancelled') =>
    apiRequest<{
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

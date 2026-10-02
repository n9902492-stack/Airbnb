import { apiRequest } from './client';

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

export type PropertySearchParams = {
  q?: string;
  city?: string;
  check_in?: string;
  check_out?: string;
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
};

export const propertyApi = {
  search: (params: PropertySearchParams = {}) => {
    const query = new URLSearchParams();

    Object.entries(params).forEach(([key, value]) => {
      if (value === undefined || value === '' || value === null) return;

      if (Array.isArray(value)) {
        value.forEach((item) => query.append(key, String(item)));
      } else {
        query.set(key, String(value));
      }
    });

    const suffix = query.toString() ? '?' + query.toString() : '';
    return apiRequest<PublicProperty[]>('/properties' + suffix);
  },

  get: (propertyId: number) =>
    apiRequest<PublicProperty>('/properties/' + propertyId),
};

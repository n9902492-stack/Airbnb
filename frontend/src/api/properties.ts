import { apiRequest } from './client';

export type ApiProperty = {
  id: number;
  owner_id: number;
  title: string;
  description: string;
  property_type: string;
  category: string;
  city: string;
  state: string;
  country: string;
  guests: number;
  bedrooms: number;
  beds: number;
  bathrooms: number;
  price_per_night: string;
  cleaning_fee: string;
  amenities: string[];
  house_rules: string[];
  image_urls: string[];
  check_in_time: string;
  check_out_time: string;
  status: string;
};

export function getProperties() {
  return apiRequest<ApiProperty[]>('/properties');
}

export function getProperty(propertyId: number) {
  return apiRequest<ApiProperty>(`/properties/${propertyId}`);
}

export type PropertyPhoto = {
  label: 'Exterior' | 'Living room' | 'Bedroom' | 'Bathroom' | 'Kitchen' | 'View';
  url: string;
};

export type CustomerReview = {
  id: number;
  guestName: string;
  rating: number;
  date: string;
  comment: string;
};

export type Property = {
  id: number;
  title: string;
  location: string;
  country: string;
  pricePerNight: number;
  rating: number;
  reviews: number;
  guests: number;
  bedrooms: number;
  beds: number;
  baths: number;
  image: string;
  images: string[];
  photos: PropertyPhoto[];
  category: string;
  description: string;
  host: string;
  amenities: string[];
  highlights: string[];
  customerReviews: CustomerReview[];
};

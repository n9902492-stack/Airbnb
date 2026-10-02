import type { Property } from './types';

export const properties: Property[] = [
  {
    id: 1,
    title: 'Cedar Glass House',
    location: 'Manali, Himachal Pradesh',
    country: 'India',
    pricePerNight: 7200,
    rating: 4.93,
    reviews: 184,
    guests: 6,
    bedrooms: 3,
    beds: 3,
    baths: 2,
    category: 'Mountain',
    host: 'Aarav',
    image: 'https://images.unsplash.com/photo-1601918774946-25832a4be0d6?auto=format&fit=crop&w=1200&q=80',
    images: [
      'https://images.unsplash.com/photo-1601918774946-25832a4be0d6?auto=format&fit=crop&w=1200&q=80',
      'https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?auto=format&fit=crop&w=900&q=80',
      'https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?auto=format&fit=crop&w=900&q=80',
      'https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea?auto=format&fit=crop&w=900&q=80',
    ],
    description: 'A warm, design-led mountain home with floor-to-ceiling valley views, a fireplace and quiet outdoor deck.',
    amenities: ['Mountain view', 'Fast Wi-Fi', 'Indoor fireplace', 'Kitchen', 'Free parking', 'Heating'],
    highlights: ['Self check-in', 'Valley-facing deck', 'Dedicated workspace']
  },
  {
    id: 2,
    title: 'Palm Courtyard Villa',
    location: 'Assagao, Goa',
    country: 'India',
    pricePerNight: 9800,
    rating: 4.88,
    reviews: 96,
    guests: 8,
    bedrooms: 4,
    beds: 4,
    baths: 4,
    category: 'Tropical',
    host: 'Mira',
    image: 'https://images.unsplash.com/photo-1613490493576-7fde63acd811?auto=format&fit=crop&w=1200&q=80',
    images: [
      'https://images.unsplash.com/photo-1613490493576-7fde63acd811?auto=format&fit=crop&w=1200&q=80',
      'https://images.unsplash.com/photo-1600607687920-4e2a09cf159d?auto=format&fit=crop&w=900&q=80',
      'https://images.unsplash.com/photo-1600566753051-f0b89df2dd90?auto=format&fit=crop&w=900&q=80',
      'https://images.unsplash.com/photo-1600607688969-a5bfcd646154?auto=format&fit=crop&w=900&q=80'
    ],
    description: 'A private tropical courtyard home made for slow mornings, long pool days and relaxed group stays.',
    amenities: ['Private pool', 'Breakfast', 'Air conditioning', 'Kitchen', 'Housekeeping', 'Garden'],
    highlights: ['Private chef available', 'Quiet neighbourhood', 'Poolside dining']
  },
  {
    id: 3,
    title: 'Old Town Loft',
    location: 'Jaipur, Rajasthan',
    country: 'India',
    pricePerNight: 4600,
    rating: 4.91,
    reviews: 211,
    guests: 3,
    bedrooms: 1,
    beds: 2,
    baths: 1,
    category: 'City',
    host: 'Kabir',
    image: 'https://images.unsplash.com/photo-1615874694520-474822394e73?auto=format&fit=crop&w=1200&q=80',
    images: [
      'https://images.unsplash.com/photo-1615874694520-474822394e73?auto=format&fit=crop&w=1200&q=80',
      'https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?auto=format&fit=crop&w=900&q=80',
      'https://images.unsplash.com/photo-1600607688960-e095ff83135c?auto=format&fit=crop&w=900&q=80',
      'https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=900&q=80'
    ],
    description: 'An art-filled loft near Jaipur’s old city with handcrafted furniture and a calm rooftop breakfast corner.',
    amenities: ['Rooftop', 'Wi-Fi', 'Air conditioning', 'Breakfast', 'Workspace', 'Washer'],
    highlights: ['Walkable old city', 'Local design', 'Hosted breakfast']
  }
];
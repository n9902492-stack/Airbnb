import { useEffect, useRef } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

import type { PublicProperty } from '../lib/api';

export default function SearchMap({
  properties,
  onBoundsChange,
}: {
  properties: PublicProperty[];
  onBoundsChange?: (bounds: {
    min_lat: number;
    max_lat: number;
    min_lng: number;
    max_lng: number;
  }) => void;
}) {
  const container = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const markersRef = useRef<mapboxgl.Marker[]>([]);

  useEffect(() => {
    if (!container.current || mapRef.current) return;
    const token = import.meta.env.VITE_MAPBOX_ACCESS_TOKEN;
    if (!token) return;

    mapboxgl.accessToken = token;
    const first = properties.find((p) => p.latitude != null && p.longitude != null);
    const map = new mapboxgl.Map({
      container: container.current,
      style: 'mapbox://styles/mapbox/streets-v12',
      center: first ? [Number(first.longitude), Number(first.latitude)] : [77.2, 28.6],
      zoom: first ? 9 : 4,
    });

    map.addControl(new mapboxgl.NavigationControl({ showCompass: false }), 'top-right');
    map.on('moveend', () => {
      const b = map.getBounds();
      onBoundsChange?.({
        min_lat: b.getSouth(),
        max_lat: b.getNorth(),
        min_lng: b.getWest(),
        max_lng: b.getEast(),
      });
    });

    mapRef.current = map;
    return () => {
      markersRef.current.forEach((marker) => marker.remove());
      markersRef.current = [];
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    markersRef.current.forEach((marker) => marker.remove());
    markersRef.current = [];

    const points = properties.filter((p) => p.latitude != null && p.longitude != null);
    const bounds = new mapboxgl.LngLatBounds();

    points.forEach((property) => {
      const el = document.createElement('button');
      el.className = 'price-map-pin';
      el.textContent = '₹' + Number(property.price_per_night).toLocaleString('en-IN');
      el.onclick = () => {
        window.location.href = '/stays/' + property.id;
      };

      const lngLat: [number, number] = [
        Number(property.longitude),
        Number(property.latitude),
      ];
      bounds.extend(lngLat);
      const marker = new mapboxgl.Marker({ element: el })
        .setLngLat(lngLat)
        .addTo(map);
      markersRef.current.push(marker);
    });

    if (points.length > 1) {
      map.fitBounds(bounds, { padding: 70, maxZoom: 12 });
    } else if (points.length === 1) {
      map.easeTo({
        center: [Number(points[0].longitude), Number(points[0].latitude)],
        zoom: 10,
      });
    }
  }, [properties]);

  if (!import.meta.env.VITE_MAPBOX_ACCESS_TOKEN) {
    return (
      <div className="search-map-placeholder">
        Add <code>VITE_MAPBOX_ACCESS_TOKEN</code> to enable map discovery.
      </div>
    );
  }

  return <div ref={container} className="search-map" aria-label="Stay search map"/>;
}

import { useEffect, useRef, useState } from 'react';
import { Bus, CarFront, MapPin, Plane, Search, TrainFront } from 'lucide-react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

import { transferApi, type TransferPlace, type TransferQuote } from '../lib/api';

type Direction = 'pickup_to_stay' | 'stay_to_dropoff';
type PlaceType = 'airport' | 'railway' | 'bus_stand' | 'custom';

const typeOptions: { value: PlaceType; label: string; icon: typeof Plane }[] = [
  { value: 'airport', label: 'Airport', icon: Plane },
  { value: 'railway', label: 'Railway station', icon: TrainFront },
  { value: 'bus_stand', label: 'Bus stand', icon: Bus },
  { value: 'custom', label: 'Other place', icon: MapPin },
];

export default function TransferOption({
  propertyId,
  propertyName,
  latitude,
  longitude,
}: {
  propertyId: number;
  propertyName: string;
  latitude: number;
  longitude: number;
}) {
  const mapContainer = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);

  const [enabled, setEnabled] = useState(false);
  const [direction, setDirection] = useState<Direction>('pickup_to_stay');
  const [placeType, setPlaceType] = useState<PlaceType>('airport');
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<TransferPlace[]>([]);
  const [selected, setSelected] = useState<TransferPlace | null>(null);
  const [quote, setQuote] = useState<TransferQuote | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [saved, setSaved] = useState(false);

  async function searchPlaces() {
    if (query.trim().length < 2) return;
    setLoading(true);
    setMessage('');
    try {
      const items = await transferApi.searchPlaces(query.trim(), propertyId);
      setResults(items);
      if (!items.length) setMessage('No matching place found. Try a more specific name.');
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Unable to search places');
    } finally {
      setLoading(false);
    }
  }

  async function choosePlace(place: TransferPlace) {
    setSelected(place);
    setResults([]);
    setQuery(place.name);
    setLoading(true);
    setMessage('');

    try {
      const value = await transferApi.quote({
        property_id: propertyId,
        direction,
        place_type: placeType,
        place_name: place.name,
        latitude: place.latitude,
        longitude: place.longitude,
        stay_latitude: latitude,
        stay_longitude: longitude,
      });
      setQuote(value);
    } catch (err) {
      setQuote(null);
      setMessage(err instanceof Error ? err.message : 'Unable to calculate route');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!quote || !selected || !enabled || !mapContainer.current) return;

    const token = import.meta.env.VITE_MAPBOX_ACCESS_TOKEN;
    if (!token) return;

    mapboxgl.accessToken = token;

    if (mapRef.current) {
      mapRef.current.remove();
      mapRef.current = null;
    }

    const map = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/streets-v12',
      center: [longitude, latitude],
      zoom: 10,
    });

    const stayCoordinates: [number, number] = [longitude, latitude];
    const selectedCoordinates: [number, number] = [selected.longitude, selected.latitude];

    const origin = direction === 'pickup_to_stay' ? selectedCoordinates : stayCoordinates;
    const destination = direction === 'pickup_to_stay' ? stayCoordinates : selectedCoordinates;

    map.on('load', () => {
      map.addSource('transfer-route', {
        type: 'geojson',
        data: {
          type: 'Feature',
          properties: {},
          geometry: quote.route_geometry,
        },
      });

      map.addLayer({
        id: 'transfer-route-line',
        type: 'line',
        source: 'transfer-route',
        layout: { 'line-cap': 'round', 'line-join': 'round' },
        paint: { 'line-color': '#17352d', 'line-width': 5 },
      });

      new mapboxgl.Marker({ color: '#c86443' })
        .setLngLat(origin)
        .setPopup(new mapboxgl.Popup().setText(direction === 'pickup_to_stay' ? selected.name : propertyName))
        .addTo(map);

      new mapboxgl.Marker({ color: '#17352d' })
        .setLngLat(destination)
        .setPopup(new mapboxgl.Popup().setText(direction === 'pickup_to_stay' ? propertyName : selected.name))
        .addTo(map);

      const bounds = new mapboxgl.LngLatBounds();
      quote.route_geometry.coordinates.forEach(([lng, lat]) => bounds.extend([lng, lat]));
      map.fitBounds(bounds, { padding: 55, maxZoom: 14 });
    });

    map.addControl(new mapboxgl.NavigationControl({ showCompass: false }), 'top-right');
    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [quote, selected, enabled, direction, latitude, longitude, propertyName]);

  async function recalculate(nextDirection: Direction, nextType: PlaceType) {
    setDirection(nextDirection);
    setPlaceType(nextType);
    if (!selected) return;

    try {
      const value = await transferApi.quote({
        property_id: propertyId,
        direction: nextDirection,
        place_type: nextType,
        place_name: selected.name,
        latitude: selected.latitude,
        longitude: selected.longitude,
        stay_latitude: latitude,
        stay_longitude: longitude,
      });
      setQuote(value);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Unable to recalculate transfer');
    }
  }

  return (
    <section className="transfer-option">
      <div className="transfer-heading">
        <div>
          <span className="eyebrow"><CarFront size={15}/> Optional paid transfer</span>
          <h2>Need a pickup or drop-off?</h2>
          <p>Add a private transfer from an airport, railway station, bus stand or another place.</p>
        </div>
        <label className="transfer-toggle">
          <input
            type="checkbox"
            checked={enabled}
            onChange={(event) => {
              setEnabled(event.target.checked);
              if (!event.target.checked) {
                setQuote(null);
                setSelected(null);
                setResults([]);
              }
            }}
          />
          <span>{enabled ? 'Added' : 'Optional'}</span>
        </label>
      </div>

      {enabled && (
        <div className="transfer-body">
          <div className="transfer-direction">
            <button
              type="button"
              className={direction === 'pickup_to_stay' ? 'transfer-choice active' : 'transfer-choice'}
              onClick={() => void recalculate('pickup_to_stay', placeType)}
            >
              <strong>Pickup to stay</strong>
              <small>Station / airport → {propertyName}</small>
            </button>
            <button
              type="button"
              className={direction === 'stay_to_dropoff' ? 'transfer-choice active' : 'transfer-choice'}
              onClick={() => void recalculate('stay_to_dropoff', placeType)}
            >
              <strong>Drop-off from stay</strong>
              <small>{propertyName} → destination</small>
            </button>
          </div>

          <div className="transfer-types">
            {typeOptions.map(({ value, label, icon: Icon }) => (
              <button
                type="button"
                key={value}
                className={placeType === value ? 'transfer-type active' : 'transfer-type'}
                onClick={() => void recalculate(direction, value)}
              >
                <Icon size={18}/>
                {label}
              </button>
            ))}
          </div>

          <div className="transfer-search">
            <div className="transfer-search-box">
              <Search size={18}/>
              <input
                value={query}
                onChange={(event) => {
                  setQuery(event.target.value);
                  setSelected(null);
                  setQuote(null);
                }}
                placeholder={
                  placeType === 'airport'
                    ? 'Search airport'
                    : placeType === 'railway'
                      ? 'Search railway station'
                      : placeType === 'bus_stand'
                        ? 'Search bus stand'
                        : 'Search any pickup or drop-off place'
                }
                onKeyDown={(event) => {
                  if (event.key === 'Enter') {
                    event.preventDefault();
                    void searchPlaces();
                  }
                }}
              />
              <button type="button" onClick={() => void searchPlaces()} disabled={loading}>
                {loading ? 'Searching…' : 'Search'}
              </button>
            </div>

            {results.length > 0 && (
              <div className="transfer-results">
                {results.map((place) => (
                  <button
                    type="button"
                    key={place.name + place.latitude + place.longitude}
                    onClick={() => void choosePlace(place)}
                  >
                    <MapPin size={17}/>
                    <span>
                      <strong>{place.name}</strong>
                      <small>{place.full_address}</small>
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {message && <div className="auth-error">{message}</div>}

          {quote && selected && (
            <>
              <div className="transfer-summary">
                <div>
                  <small>Driving distance</small>
                  <strong>{quote.distance_km} km</strong>
                </div>
                <div>
                  <small>Estimated time</small>
                  <strong>{quote.duration_minutes} min</strong>
                </div>
                <div>
                  <small>Transfer estimate</small>
                  <strong>₹{quote.estimated_fare.toLocaleString('en-IN')}</strong>
                </div>
              </div>

              <div className="transfer-route-label">
                <MapPin size={17}/>
                <span>
                  {direction === 'pickup_to_stay'
                    ? `${selected.name} → ${propertyName}`
                    : `${propertyName} → ${selected.name}`}
                </span>
              </div>

              {import.meta.env.VITE_MAPBOX_ACCESS_TOKEN ? (
                <div ref={mapContainer} className="transfer-map" aria-label="Driving route map"/>
              ) : (
                <div className="transfer-map-placeholder">
                  Add <code>VITE_MAPBOX_ACCESS_TOKEN</code> to show the interactive route map.
                </div>
              )}

              <p className="transfer-pricing-note">{quote.pricing_note}</p>
              <button
                type="button"
                className="primary"
                onClick={() => {
                  localStorage.setItem(
                    'nestora_transfer_selection',
                    JSON.stringify({ propertyId, ...quote }),
                  );
                  setSaved(true);
                }}
              >
                {saved ? 'Transfer selected' : 'Add transfer · ₹' + quote.estimated_fare.toLocaleString('en-IN')}
              </button>
              <small className="transfer-skip">
                {saved ? 'This transfer will be carried into checkout.' : 'You can skip this and book only the stay.'}
              </small>
            </>
          )}
        </div>
      )}
    </section>
  );
}

from math import ceil

import httpx

from src.core.config import settings
from src.models.transfer import TransferPlaceType


class MapService:
    SEARCH_URL = "https://api.mapbox.com/search/geocode/v6/forward"
    DIRECTIONS_URL = "https://api.mapbox.com/directions/v5/mapbox/driving"

    @staticmethod
    def _require_token() -> str:
        if not settings.mapbox_access_token:
            raise ValueError("Map provider is not configured")
        return settings.mapbox_access_token

    @classmethod
    async def geocode(cls, query: str, proximity: tuple[float, float] | None = None):
        token = cls._require_token()
        params = {
            "q": query,
            "access_token": token,
            "limit": 6,
            "country": "in",
            "language": "en",
            "autocomplete": "true",
        }
        if proximity:
            params["proximity"] = f"{proximity[1]},{proximity[0]}"

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(cls.SEARCH_URL, params=params)
            response.raise_for_status()
            payload = response.json()

        results = []
        for feature in payload.get("features", []):
            coordinates = feature.get("geometry", {}).get("coordinates", [])
            if len(coordinates) < 2:
                continue
            props = feature.get("properties", {})
            results.append(
                {
                    "name": props.get("name_preferred") or props.get("name") or query,
                    "full_address": props.get("full_address")
                    or feature.get("place_name")
                    or props.get("place_formatted")
                    or query,
                    "longitude": float(coordinates[0]),
                    "latitude": float(coordinates[1]),
                }
            )
        return results

    @classmethod
    async def route(
        cls,
        origin: tuple[float, float],
        destination: tuple[float, float],
    ):
        token = cls._require_token()
        coordinates = (
            f"{origin[1]},{origin[0]};"
            f"{destination[1]},{destination[0]}"
        )
        url = f"{cls.DIRECTIONS_URL}/{coordinates}"
        params = {
            "access_token": token,
            "geometries": "geojson",
            "overview": "full",
            "steps": "false",
        }

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            payload = response.json()

        routes = payload.get("routes", [])
        if not routes:
            raise ValueError("No driving route was found for these locations")

        route = routes[0]
        return {
            "distance_km": round(route["distance"] / 1000, 1),
            "duration_minutes": max(1, round(route["duration"] / 60)),
            "route_geometry": route["geometry"],
        }

    @staticmethod
    def calculate_fare(distance_km: float, place_type: TransferPlaceType) -> int:
        surcharge = {
            TransferPlaceType.AIRPORT: settings.transfer_airport_surcharge,
            TransferPlaceType.RAILWAY: settings.transfer_railway_surcharge,
            TransferPlaceType.BUS_STAND: settings.transfer_bus_surcharge,
            TransferPlaceType.CUSTOM: 0,
        }[place_type]

        raw = (
            settings.transfer_base_fare
            + distance_km * settings.transfer_per_km_rate
            + surcharge
        )
        fare = max(settings.transfer_minimum_fare, raw)
        return int(ceil(fare / 10.0) * 10)

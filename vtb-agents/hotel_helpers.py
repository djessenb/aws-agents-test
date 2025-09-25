import os
import json
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple
from difflib import SequenceMatcher

import requests


def get_airtrotter_api_key() -> str:
    api_key = os.environ.get("AIRTROTTER_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "AIRTROTTER_API_KEY is not set. Add it to environment or .env file."
        )
    return api_key


def normalize_name(value: Optional[str]) -> str:
    if not value:
        return ""
    return " ".join(value.lower().strip().split())


def score_name_match(term: str, candidate: str) -> float:
    term_norm = normalize_name(term)
    cand_norm = normalize_name(candidate)
    if not term_norm or not cand_norm:
        return 0.0
    return SequenceMatcher(None, term_norm, cand_norm).ratio()


def extract_hotel_tuple(item: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[float], Optional[float]]:
    name = item.get("name") or item.get("hotel_name") or item.get("title")
    hotel_id = item.get("hotel_id") or item.get("id") or item.get("hotelId")

    lat: Optional[float] = None
    lon: Optional[float] = None
    location = item.get("location") or {}
    if isinstance(location, dict):
        lat = location.get("lat") or location.get("latitude")
        lon = location.get("lon") or location.get("lng") or location.get("longitude")
    else:
        lat = item.get("lat") or item.get("latitude")
        lon = item.get("lon") or item.get("lng") or item.get("longitude")
    try:
        lat = float(lat) if lat is not None else None
    except Exception:
        lat = None
    try:
        lon = float(lon) if lon is not None else None
    except Exception:
        lon = None

    return (
        name if isinstance(name, str) else None,
        hotel_id if isinstance(hotel_id, str) else (str(hotel_id) if hotel_id is not None else None),
        lat,
        lon,
    )


def format_date(dt: date) -> str:
    return dt.strftime("%Y-%m-%d")


def availability_by_city(
    latitude: float,
    longitude: float,
    rooms: int = 1,
    guests: str = "A,A",
    checkin: Optional[str] = None,
    checkout: Optional[str] = None,
    radius: str = "1",
    language: Optional[str] = None,
) -> Dict[str, Any]:
    api_key = get_airtrotter_api_key()
    today = date.today()
    checkin_str = checkin or format_date(today + timedelta(days=30))
    checkout_str = checkout or format_date(today + timedelta(days=31))
    lang = (language or os.environ.get("AIRTROTTER_LANGUAGE") or "en").strip()

    url = "https://airtrotterapi.com/rest/accommodations/hotelAvailabilityByCity"
    headers = {"client-access-key": api_key}
    params = {
        "rooms": rooms,
        "guests": guests,
        "checkin": checkin_str,
        "checkout": checkout_str,
        "language": lang,
        "rows": 200,
        "force_radius": radius,
        "latitude": latitude,
        "longitude": longitude,
    }
    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def flatten_candidates(container: Any) -> List[Dict[str, Any]]:
    if isinstance(container, list):
        return [i for i in container if isinstance(i, dict)]
    if isinstance(container, dict):
        for key in ("data", "results", "items", "hotels", "accommodations"):
            val = container.get(key)
            if isinstance(val, list):
                return [i for i in val if isinstance(i, dict)]
    return []


def string_contains(hay: Dict[str, Any], needle: str) -> bool:
    try:
        return needle in json.dumps(hay, ensure_ascii=False)
    except Exception:
        return False



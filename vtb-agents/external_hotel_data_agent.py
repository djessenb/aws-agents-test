#!/usr/bin/env python3
"""
External Hotel Data Agent

Creates a Strands agent that can search Airtrotter for hotel/property
autocomplete results based on a user query. The agent uses an API key
provided via environment variable AIRTROTTER_API_KEY (optionally loaded
from a .env file if present).

Usage:
  python external_hotel_data_agent.py "search term"

Outputs a list of matching properties (raw JSON items) to stdout.
"""

import os
import sys
import json
from typing import Any, Dict, List, Optional, Tuple
from datetime import date, timedelta
from difflib import SequenceMatcher

try:
    # Load environment variables from .env if available (optional dependency)
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()  # harmless if .env absent
except Exception:
    # Proceed without .env loading if package is not installed
    pass

import requests
from strands import Agent, tool
from strands.models import BedrockModel
from vtb_agents.hotel_helpers import (
    normalize_name,
    score_name_match,
    extract_hotel_tuple,
    flatten_candidates,
    string_contains,
)


def _get_airtrotter_api_key() -> str:
    api_key = os.environ.get("AIRTROTTER_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("AIRTROTTER_API_KEY is not set. Add it to environment or .env file.")
    return api_key


@tool
def search_airtrotter(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    api_key = _get_airtrotter_api_key()
    url = "https://airtrotterapi.com/rest/autocomplete/searchProperties"
    headers = {"client-access-key": api_key}
    params = {"query": query, "provider": 3}
    response = requests.get(url, headers=headers, params=params, timeout=20)
    response.raise_for_status()
    data = response.json()

    # The API may return a list or an object containing a list; handle both.
    items: List[Dict[str, Any]] = []
    if isinstance(data, list):
        items = [i for i in data if isinstance(i, dict)]
    elif isinstance(data, dict):
        # Common container keys to check without hard-coding a single schema
        for key in ("data", "results", "items", "properties"):
            value = data.get(key)
            if isinstance(value, list):
                items = [i for i in value if isinstance(i, dict)]
                break

    if limit > 0:
        return items[:limit]
    return items


def _select_best_match(results: List[Dict[str, Any]], search_term: str) -> Optional[Dict[str, Any]]:
    best_item: Optional[Dict[str, Any]] = None
    best_score = -1.0
    for item in results:
        name, _hid, _lat, _lon = extract_hotel_tuple(item)
        score = score_name_match(search_term, name or "")
        if score > best_score:
            best_score = score
            best_item = item
    return best_item


def _availability_by_city(
    latitude: float,
    longitude: float,
    rooms: int = 1,
    guests: str = "A,A",
    checkin: Optional[str] = None,
    checkout: Optional[str] = None,
    radius: str = "1",
    language: Optional[str] = None,
) -> Dict[str, Any]:
    api_key = _get_airtrotter_api_key()
    today = date.today()
    checkin_str = checkin or (today + timedelta(days=30)).strftime("%Y-%m-%d")
    checkout_str = checkout or (today + timedelta(days=31)).strftime("%Y-%m-%d")
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


@tool
def airtrotter_availability_by_city_tool(
    latitude: float,
    longitude: float,
    rooms: int = 1,
    guests: str = "A,A",
    checkin: Optional[str] = None,
    checkout: Optional[str] = None,
    radius: str = "1",
    language: Optional[str] = None,
) -> Dict[str, Any]:
    """Tool: Fetch availability for accommodations near given coordinates."""
    api_key = os.environ.get("AIRTROTTER_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("AIRTROTTER_API_KEY is not set. Add it to environment or .env file.")

    today = date.today()
    checkin_str = checkin or (today + timedelta(days=30)).strftime("%Y-%m-%d")
    checkout_str = checkout or (today + timedelta(days=31)).strftime("%Y-%m-%d")
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

@tool
def airtrotter_hotel_availability_tool(
    latitude: float,
    longitude: float,
    rooms: int = 1,
    guests: str = "A,A",
    checkin: Optional[str] = None,
    checkout: Optional[str] = None,
    radius: str = "1",
    language: Optional[str] = None,
    hotel_id: Optional[str] = None,
    block_id: Optional[str] = None,
    currency: Optional[str] = None,
) -> Dict[str, Any]:
    """Tool: Fetch availability by city and filter to a given hotel/block/currency.

    If hotel_id is provided, results are filtered to that hotel. If block_id is
    provided, tries to keep only entries referencing that block. If currency is
    provided, filters to entries where a currency field matches.
    """
    # Inline availability-by-city request
    api_key = os.environ.get("AIRTROTTER_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("AIRTROTTER_API_KEY is not set. Add it to environment or .env file.")
    today = date.today()
    checkin_str = checkin or (today + timedelta(days=30)).strftime("%Y-%m-%d")
    checkout_str = checkout or (today + timedelta(days=31)).strftime("%Y-%m-%d")
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
    raw = resp.json()

    candidates = flatten_candidates(raw)
    filtered = candidates

    def matches_hotel(item: Dict[str, Any]) -> bool:
        if not hotel_id:
            return True
        iid = item.get("hotel_id") or item.get("id") or item.get("hotelId")
        return str(iid) == str(hotel_id)

    def matches_block(item: Dict[str, Any]) -> bool:
        if not block_id:
            return True
        return string_contains(item, str(block_id))

    def matches_currency(item: Dict[str, Any]) -> bool:
        if not currency:
            return True
        # Try common currency fields
        for key in ("currency", "price_currency", "purchaseCurrency"):
            val = item.get(key)
            if isinstance(val, str) and val.upper() == currency.upper():
                return True
        # Fallback: substring anywhere
        return string_contains(item, str(currency))

    filtered = [i for i in filtered if matches_hotel(i) and matches_block(i) and matches_currency(i)]

    return {
        "raw": raw,
        "filtered": filtered,
        "filters": {
            "hotel_id": hotel_id,
            "block_id": block_id,
            "currency": currency,
            "latitude": latitude,
            "longitude": longitude,
            "rooms": rooms,
            "guests": guests,
            "checkin": checkin,
            "checkout": checkout,
            "radius": radius,
            "language": language,
        },
    }

def external_hotel_best_match_availability(
    search_term: str,
    rooms: int = 1,
    guests: str = "A,A",
    checkin: Optional[str] = None,
    checkout: Optional[str] = None,
    radius: str = "1",
    language: Optional[str] = None,
) -> Dict[str, Any]:
    """Search properties, pick best name match, and fetch availability near it."""
    results = search_airtrotter(search_term, limit=25)
    best = _select_best_match(results, search_term)
    if not best:
        return {"results": results, "best_match": None, "availability": None}

    name, hotel_id, lat, lon = extract_hotel_tuple(best)
    if lat is None or lon is None:
        return {"results": results, "best_match": best, "availability": None}

    availability = _availability_by_city(
        latitude=lat,
        longitude=lon,
        rooms=rooms,
        guests=guests,
        checkin=checkin,
        checkout=checkout,
        radius=radius,
        language=language,
    )

    return {
        "results": results,
        "best_match": {
            "name": name,
            "hotel_id": hotel_id,
            "latitude": lat,
            "longitude": lon,
            "raw": best,
        },
        "availability": availability,
    }


def external_hotel_data_agent(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Run the external hotel data agent to fetch Airtrotter results for a query.

    Parameters
    - query: search query for properties
    - limit: maximum number of results to return (default 10)
    """

    bedrock_model = BedrockModel(
        model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
        temperature=0.3,
    )
    # Minimal agent using a callable tool via closure
    agent = Agent(
        tools=[
            search_airtrotter,
            airtrotter_availability_by_city_tool,
            airtrotter_hotel_availability_tool,
        ],
        model=bedrock_model,
    )

    # Let the Agent invoke the tool instead of calling it directly
    result = agent(query)
    if isinstance(result, list):
        return result
    try:
        return list(result)
    except Exception:
        return [result] if isinstance(result, dict) else []


def _print_results(results: List[Dict[str, Any]]) -> None:
    for item in results:
        print(json.dumps(item, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage: python external_hotel_data_agent.py \"search term\" [--list | --debug | --city LAT LON | --hotel LAT LON HOTEL_ID [BLOCK_ID] [CURRENCY]]"
        )
        sys.exit(1)
    query_arg = sys.argv[1]
    flag = sys.argv[2] if len(sys.argv) >= 3 else None
    try:
        if flag == "--list":
            # Explicit list of autocomplete results (legacy behavior)
            results_list = external_hotel_data_agent(query_arg)
            _print_results(results_list)
        elif flag == "--debug":
            # Full structure including initial results for troubleshooting
            result = external_hotel_best_match_availability(query_arg)
            print(json.dumps(result, ensure_ascii=False))
        elif flag == "--city":
            lat = float(sys.argv[3])
            lon = float(sys.argv[4])
            result = airtrotter_availability_by_city_tool(latitude=lat, longitude=lon)
            print(json.dumps(result, ensure_ascii=False))
        elif flag == "--hotel":
            lat = float(sys.argv[3])
            lon = float(sys.argv[4])
            hotel_id = sys.argv[5]
            block_id = sys.argv[6] if len(sys.argv) >= 7 else None
            currency = sys.argv[7] if len(sys.argv) >= 8 else None
            result = airtrotter_hotel_availability_tool(
                latitude=lat,
                longitude=lon,
                hotel_id=hotel_id,
                block_id=block_id,
                currency=currency,
            )
            print(json.dumps(result, ensure_ascii=False))
        else:
            # Default: only print best_match and availability
            result = external_hotel_best_match_availability(query_arg)
            slim = {
                "best_match": result.get("best_match"),
                "availability": result.get("availability"),
            }
            print(json.dumps(slim, ensure_ascii=False))
    except Exception as err:
        print(f"Error: {err}")
        sys.exit(2)



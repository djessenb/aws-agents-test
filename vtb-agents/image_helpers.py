import os
from typing import List
import requests


def get_unsplash_api_key() -> str:
    api_key = os.environ.get("UNSPLASH_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "UNSPLASH_API_KEY is not set. Add it to environment or .env file."
        )
    return api_key


def search_unsplash(query: str, per_page: int = 10) -> List[str]:
    api_key = get_unsplash_api_key()
    url = "https://api.unsplash.com/search/photos"
    headers = {"Accept-Version": "v1", "Authorization": f"Client-ID {api_key}"}
    params = {"query": query, "per_page": per_page}
    response = requests.get(url, headers=headers, params=params, timeout=20)
    response.raise_for_status()
    data = response.json()
    results = data.get("results", [])
    urls: List[str] = []
    for item in results:
        url_full = (item.get("urls", {}) or {}).get("full")
        url_regular = (item.get("urls", {}) or {}).get("regular")
        if url_full:
            urls.append(url_full)
        elif url_regular:
            urls.append(url_regular)
    return urls



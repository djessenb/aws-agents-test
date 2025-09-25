#!/usr/bin/env python3
"""
External Images Agent

Creates a Strands agent that can search Unsplash for images based on a
user query. The agent uses an API key provided via environment variable
UNSPLASH_API_KEY (optionally loaded from a .env file if present).

Usage:
  python external_images_agent.py "search term"

Outputs a list of image results (urls and attribution) to stdout.
"""

import os
import sys
from typing import Any, Dict, List

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
from vtb_agents.image_helpers import get_unsplash_api_key


def _search_unsplash(query: str, per_page: int = 10) -> List[str]:
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


@tool
def unsplash_search_tool(query: str, per_page: int = 10) -> List[str]:
    """Tool: Search Unsplash for images matching a query and return image URLs."""
    return _search_unsplash(query, per_page)


def external_images_agent(query: str, per_page: int = 10) -> List[str]:
    """Run the external images agent to fetch Unsplash results for a query.

    Parameters
    - query: search query for images
    - per_page: number of results to fetch (default 10)
    """

    bedrock_model = BedrockModel(
        model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
        temperature=0.3,
    )
    # Minimal agent that can invoke the registered tool
    agent = Agent(
        tools=[unsplash_search_tool],
        model=bedrock_model,
    )

    # Let the Agent invoke the tool instead of calling it directly
    result = agent(query)
    return list(result) if isinstance(result, list) else [str(result)]


def _print_results(results: List[str]) -> None:
    for url in results:
        print(url)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python external_images_agent.py \"search term\"")
        sys.exit(1)
    query_arg = sys.argv[1]
    try:
        results_list = external_images_agent(query_arg)
        _print_results(results_list)
    except Exception as err:
        print(f"Error: {err}")
        sys.exit(2)



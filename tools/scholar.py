"""
tools/scholar.py
Searches Google Scholar via the SerpAPI.
Docs: https://serpapi.com/google-scholar-api"""

import os

import httpx

from agent.state import SearchResult

BASE_URL = "https://serpapi.com/search.json"
MAX_RESULTS = 5


async def search_scholar(query: str, keywords: list[str]) -> list[SearchResult]:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            BASE_URL,
            params={
                "engine": "google_scholar",
                "q": query,
                "num": MAX_RESULTS,
                "api_key": os.getenv("SERPAPI_API_KEY", ""),
            },
        )
        resp.raise_for_status()
        data = resp.json()

    results = []
    for item in data.get("organic_results", []):
        title = item.get("title") or "No title"
        snippet = item.get("snippet") or "No snippet available."
        url = item.get("link") or "https://scholar.google.com"
        authors_info = item.get("publication_info", {}).get("summary", "")
        year = item.get("publication_info", {}).get("year", "")

        results.append(
            SearchResult(
                source="Google Scholar",
                title=title,
                url=url,
                snippet=f"{authors_info} ({year}). {snippet}",
                metadata={"year": year},
            )
        )
    return results

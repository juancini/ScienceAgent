"""
tools/loc.py
Searches the Library of Congress via its public REST API.
Docs: https://www.loc.gov/apis/
No API key required.
"""

import httpx
from agent.state import SearchResult

BASE_URL = "https://www.loc.gov/search/"
MAX_RESULTS = 5


async def search_loc(query: str, keywords: list[str]) -> list[SearchResult]:
    async with httpx.AsyncClient(
        timeout=15, headers={"Accept": "application/json"}
    ) as client:
        resp = await client.get(
            BASE_URL,
            params={
                "q": query,
                "fo": "json",
                "c": MAX_RESULTS,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    results = []
    for item in data.get("results", []):
        title = item.get("title") or "No title"
        description = item.get("description") or []
        snippet = (
            " ".join(description[:2])[:500]
            if description
            else "No description available."
        )
        url = item.get("url") or item.get("id") or "https://www.loc.gov"
        date = item.get("date") or ""

        results.append(
            SearchResult(
                source="Library of Congress",
                title=title,
                url=url,
                snippet=snippet,
                metadata={"date": date, "type": item.get("type", "")},
            )
        )

    return results

"""
tools/semantic_scholar.py
Searches the Semantic Scholar Academic Graph API.
Docs: https://api.semanticscholar.org/api-docs/
Free API key at https://www.semanticscholar.org/product/api
"""

import os
import httpx
from agent.state import SearchResult

BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
MAX_RESULTS = 5
FIELDS = "paperId,title,year,authors,abstract,externalIds,url"


async def search_semantic_scholar(
    query: str, keywords: list[str]
) -> list[SearchResult]:
    headers = {}
    api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")
    if api_key:
        headers["x-api-key"] = api_key

    async with httpx.AsyncClient(timeout=15, headers=headers) as client:
        resp = await client.get(
            BASE_URL,
            params={
                "query": query,
                "limit": MAX_RESULTS,
                "fields": FIELDS,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    results = []
    for paper in data.get("data", []):
        title = paper.get("title") or "No title"
        abstract = (paper.get("abstract") or "")[:500]
        year = paper.get("year") or ""
        url = (
            paper.get("url")
            or f"https://www.semanticscholar.org/paper/{paper.get('paperId', '')}"
        )
        authors = ", ".join(a.get("name", "") for a in (paper.get("authors") or [])[:3])

        results.append(
            SearchResult(
                source="Semantic Scholar",
                title=title,
                url=url,
                snippet=f"{authors} ({year}). {abstract}",
                metadata={"year": year, "paperId": paper.get("paperId")},
            )
        )

    return results

"""
tools/openalex.py
Searches OpenAlex — a fully open index of 250M+ scholarly works.
Docs: https://docs.openalex.org/
No API key required (polite pool with email header is recommended).
"""

import httpx
from agent.state import SearchResult

BASE_URL = "https://api.openalex.org/works"
MAX_RESULTS = 5
POLITE_EMAIL = (
    "research-agent@example.com"  # Replace with your email for the polite pool
)


async def search_openalex(query: str, keywords: list[str]) -> list[SearchResult]:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            BASE_URL,
            params={
                "search": query,
                "per-page": MAX_RESULTS,
                "select": "id,title,doi,publication_year,authorships,abstract_inverted_index,primary_location",
                "mailto": POLITE_EMAIL,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    results = []
    for work in data.get("results", []):
        title = work.get("title") or "No title"
        doi = work.get("doi") or ""
        year = work.get("publication_year") or ""
        url = doi if doi else work.get("id", "https://openalex.org")

        # Reconstruct abstract from inverted index
        inv_idx = work.get("abstract_inverted_index") or {}
        snippet = (
            _reconstruct_abstract(inv_idx)[:500] if inv_idx else f"Published {year}."
        )

        # Authors
        authors = [
            a.get("author", {}).get("display_name", "")
            for a in (work.get("authorships") or [])[:3]
        ]
        author_str = ", ".join(a for a in authors if a)

        results.append(
            SearchResult(
                source="OpenAlex",
                title=title,
                url=url,
                snippet=f"{author_str} ({year}). {snippet}",
                metadata={"doi": doi, "year": year},
            )
        )

    return results


def _reconstruct_abstract(inverted_index: dict) -> str:
    """OpenAlex stores abstracts as word→[positions]. Reconstruct to string."""
    if not inverted_index:
        return ""
    positions: list[tuple[int, str]] = []
    for word, idxs in inverted_index.items():
        for idx in idxs:
            positions.append((idx, word))
    positions.sort()
    return " ".join(word for _, word in positions)

"""
tools/wayback.py
Searches the Internet Archive / Wayback Machine via the CDX Server API.
Docs: https://github.com/internetarchive/wayback/tree/master/wayback-cdx-server
No API key required.
"""

import httpx
from agent.state import SearchResult

CDX_URL = "http://web.archive.org/cdx/search/cdx"
FT_SEARCH = "https://archive.org/advancedsearch.php"
MAX_RESULTS = 5


async def search_wayback(query: str, keywords: list[str]) -> list[SearchResult]:
    """
    Uses Archive.org full-text search for texts/books in the open library,
    then falls back to CDX for URL snapshots if nothing is found.
    """
    results = await _search_archive_texts(query)
    if not results:
        results = await _search_cdx(query, keywords)
    return results[:MAX_RESULTS]


async def _search_archive_texts(query: str) -> list[SearchResult]:
    """Search Archive.org's text/book collection."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            FT_SEARCH,
            params={
                "q": query,
                "fl[]": "identifier,title,description,date,creator",
                "rows": MAX_RESULTS,
                "page": 1,
                "output": "json",
                "mediatype": "texts",
            },
        )
        resp.raise_for_status()
        data = resp.json()

    results = []
    for doc in data.get("response", {}).get("docs", []):
        identifier = doc.get("identifier", "")
        title = doc.get("title", "No title")
        description = doc.get("description") or ""
        if isinstance(description, list):
            description = " ".join(description)
        snippet = description[:500] or "No description."
        year = str(doc.get("date", ""))[:4]
        creator = doc.get("creator") or ""
        if isinstance(creator, list):
            creator = ", ".join(creator[:2])

        results.append(
            SearchResult(
                source="Internet Archive",
                title=title,
                url=f"https://archive.org/details/{identifier}",
                snippet=f"{creator} ({year}). {snippet}".strip(". "),
                metadata={"identifier": identifier, "year": year},
            )
        )

    return results


async def _search_cdx(query: str, keywords: list[str]) -> list[SearchResult]:
    """Fallback: search CDX for URL snapshots matching keywords."""
    kw = (keywords[0] if keywords else query).replace(" ", "-")
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            CDX_URL,
            params={
                "url": f"*{kw}*",
                "output": "json",
                "limit": MAX_RESULTS,
                "fl": "original,timestamp,statuscode,mimetype",
                "filter": "statuscode:200",
                "collapse": "urlkey",
            },
        )
        resp.raise_for_status()
        rows = resp.json()

    results = []
    for row in rows[1:]:  # First row is the field names
        original, timestamp, _, _ = row
        wb_url = f"https://web.archive.org/web/{timestamp}/{original}"
        results.append(
            SearchResult(
                source="Wayback Machine",
                title=original,
                url=wb_url,
                snippet=f"Archived snapshot from {timestamp[:8]}.",
                metadata={"timestamp": timestamp},
            )
        )

    return results

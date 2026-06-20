"""
tools/wikipedia.py
Searches Wikipedia via the MediaWiki REST API.
Docs: https://www.mediawiki.org/wiki/API:REST_API
No API key required.
"""

import httpx

from agent.state import SearchResult


SEARCH_URL = "https://en.wikipedia.org/w/rest.php/v1/search/page"
MAX_RESULT = 3


def _strip_tags(text: str) -> str:
    """Minimal HTML tag stripper — avoids importing BeautifulSoup."""
    import re

    return re.sub(r"<[^>]+>", "", text)


async def search_wikipedia(query: str, keywords: list[str]) -> list[SearchResult]:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            SEARCH_URL, params={"q": query, "limit": MAX_RESULT}
        )
        response.raise_for_status()
        data = response.json()

    results = []
    for page in data.get("pages", []):
        title = page.get("title", "No Title")
        excerpt = page.get("excerpt", "")
        # Strip basic HTML tags from excerpt
        excerpt = _strip_tags(excerpt)[:500]
        key = page.get("key", title.replace(" ", "_"))
        url = f"https://en.wikipedia.org/wiki/{key}"

        results.append(
            SearchResult(
                source="Wikipedia",
                title=title,
                url=url,
                snippet=excerpt,
                metadata={"key": key},
            )
        )
    return results

"""
tools/arxiv.py
Searches arXiv preprints via the arXi API.
Docs: https://info.arxiv.org/help/api/index.html
No API key required.
"""

import httpx

from agent.state import SearchResult


BASE_URL = "http://export.arxiv.org/api/query"
NS = {"atom": "http://www.w3.org/2005/Atom"}
MAX_RESULTS = 5


def _text(element: ET.Element, tag: str) -> str:
    child = element.find(tag, {"atom": "http://www.w3.org/2005/Atom"})
    return (child.text or "").strip() if child is not None else ""


async def search_arxiv(query: str, keywords: list[str]) -> list[SearchResult]:
    async with httpx.AsyncClient() as client:
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": MAX_RESULTS,
            "sortBy": "relevance",
        }
        response = await client.get(BASE_URL, params=params)
        response.raise_for_status()

    root = ET.fromstring(response.text)
    results = []
    for entry in root.findall("atom:entry", NS):
        title = _text(entry, "atom:title").replace("\n", " ").strip()
        summary = _text(entry, "atom:summary").replace("\n", " ").strip()[:500]
        url = _text(entry, "atom:id")
        year = _text(entry, "atom:published")[:4]

        authors = [_text(a, "atom:name") for a in entry.findall("atom:author", NS)[:3]]
        author_str = ", ".join(authors)

        results.append(
            SearchResult(
                source="arXiv",
                title=title,
                url=url,
                snippet=f"{author_str} ({year}): {summary}",
                metadata={"authors": authors, "year": year},
            )
        )
    return results

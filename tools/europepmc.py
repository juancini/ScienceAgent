"""
tools/europepmc.py
Searches Europe PubMed Central — broader than PubMed, includes preprints.
Docs: https://europepmc.org/RestfulWebService
No API key required.
"""

import httpx

from agent.state import SearchResult

BASE_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
MAX_RESULTS = 5


async def search_europepmc(query: str, keywords: list[str]) -> list[SearchResult]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            BASE_URL,
            params={
                "query": query,
                "resultType": "core",
                "pageSize": MAX_RESULTS,
                "format": "json",
                "sort": "CITED desc",
            },
        )
        resp.raise_for_status()
        data = resp.json()

    results = []
    for article in data.get("resultList", {}).get("result", []):
        title = article.get("title", "No title")
        abstract = (article.get("abstractText") or "")[:500]
        pmid = article.get("pmid") or article.get("id") or ""
        doi = article.get("doi") or ""
        year = str(article.get("pubYear") or "")
        authors = article.get("authorString") or ""

        if doi:
            url = f"https://doi.org/{doi}"
        elif pmid:
            url = f"https://europepmc.org/article/MED/{pmid}"
        else:
            url = "https://europepmc.org"

        results.append(
            SearchResult(
                source="Europe PMC",
                title=title,
                url=url,
                snippet=f"{authors} ({year}). {abstract}",
                metadata={"pmid": pmid, "doi": doi, "year": year},
            )
        )

    return results

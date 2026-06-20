"""
tools/pubmed.py
Searches PubMed via the NCBI Entrez API (free, no key required but key raises rate limits).
Docs: https://www.ncbi.nlm.nih.gov/books/NBK25499/
"""

import os
import httpx
from agent.state import SearchResult

BASE_SEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
BASE_FETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
BASE_SUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

MAX_RESULTS = 5


async def search_pubmed(query: str, keywords: list[str]) -> list[SearchResult]:
    api_key = os.getenv("NCBI_API_KEY", "")
    params_base = {"api_key": api_key} if api_key else {}

    async with httpx.AsyncClient(timeout=15) as client:
        # Step 1 — get PMIDs
        search_resp = await client.get(
            BASE_SEARCH,
            params={
                **params_base,
                "db": "pubmed",
                "term": query,
                "retmax": MAX_RESULTS,
                "retmode": "json",
                "sort": "relevance",
            },
        )
        search_resp.raise_for_status()
        pmids = search_resp.json().get("esearchresult", {}).get("idlist", [])

        if not pmids:
            return []

        # Step 2 — fetch summaries for those PMIDs
        summary_resp = await client.get(
            BASE_SUMMARY,
            params={
                **params_base,
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "json",
            },
        )
        summary_resp.raise_for_status()
        uids_data = summary_resp.json().get("result", {})

    results = []
    for pmid in pmids:
        doc = uids_data.get(pmid, {})
        if not doc:
            continue

        title = doc.get("title", "No title")
        authors = ", ".join(a.get("name", "") for a in doc.get("authors", [])[:3])
        year = doc.get("pubdate", "")[:4]
        source = doc.get("source", "")
        snippet = f"{authors} ({year}). {source}." if authors else year

        results.append(
            SearchResult(
                source="PubMed",
                title=title,
                url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                snippet=snippet,
                metadata={"pmid": pmid, "year": year, "journal": source},
            )
        )

    return results

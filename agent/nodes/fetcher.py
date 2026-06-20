# The registry of sources and their corresponding search functions
# Each function type is async (query: str, keywords: list[str]) -> list[dict]
import asyncio

from agent.state import AgentState, SearchResult
from tools.arxiv import search_arxiv
from tools.europepmc import search_europepmc
from tools.loc import search_loc
from tools.openalex import search_openalex
from tools.pubmed import search_pubmed
from tools.scholar import search_scholar
from tools.semantic_scholar import search_semantic_scholar
from tools.wayback import search_wayback
from tools.wikipedia import search_wikipedia


SOURCE_REGISTRY = {
    "pubmed": search_pubmed,
    "openalex": search_openalex,
    "semantic_scholar": search_semantic_scholar,
    "wikipedia": search_wikipedia,
    "arXiv": search_arxiv,
    "loc": search_loc,
    "wayback": search_wayback,
    "europepmc": search_europepmc,
    "Google Scholar": search_scholar,
}


async def _fetch_all(
    query: str, keywords: list[str], sources: list[str]
) -> list[SearchResult]:
    """Fetch results from all selected sources in parallel."""
    tasks = []
    source_names = []
    for source in sources:
        search_fn = SOURCE_REGISTRY.get(source)
        if search_fn:
            tasks.append(search_fn(query, keywords))
            source_names.append(source)
        else:
            print(f"Warning: No search function registered for source '{source}'")

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter out exceptions, flatten results, and filter out empty responses
    final_results = []
    for source_name, result in zip(source_names, results):
        if isinstance(result, Exception):
            print(f"Warning: Error fetching from '{source_name}': {result}")
        else:
            final_results.extend([item for item in result if item])
    return final_results


def fetch_results(state: AgentState) -> AgentState:
    """Synchronous wrapper as LangGraph nodes must be sync."""
    results = asyncio.run(
        _fetch_all(
            state["query"], state.get("sub_topics", []), state["selected_sources"]
        )
    )
    state["raw_results"] = results
    print(f"Fetched {len(results)} results from sources: {state['selected_sources']}")
    return state

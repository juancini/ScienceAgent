# The registry of sources and their corresponding search functions
# Each function type is async (query: str, keywords: list[str]) -> list[dict]
import asyncio

from agent.state import AgentState, SearchResult


SOURCE_REGISTRY = {
    "pubmed": search_pubmed,
    "openalex": search_openalex,
    "semantic_scholar": search_semantic_scholar,
    "wikipedia": search_wikipedia,
    "arxiv": search_arxiv,
    "loc": search_loc,
    "wayback": search_wayback,
    "europepmc": search_europepmc,
}


async def _fetch_all(
    query: str, keywords: list[str], sources: list[str]
) -> list[SearchResult]:
    """Fetch results from all selected sources in parallel."""
    tasks = []
    for source in sources:
        search_fn = SOURCE_REGISTRY.get(source)
        if search_fn:
            tasks.append(search_fn(query, keywords))
        else:
            print(f"Warning: No search function registered for source '{source}'")
    results = await asyncio.gather(*tasks, return_exceptions=True)
    # Nested comprehension list that flattens results and filter out empty responses
    return [item for sublist in results for item in sublist if item]


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

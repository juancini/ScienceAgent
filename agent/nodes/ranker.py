# How many top results to pass to the synthesizer for final answer generation
from agent.state import AgentState


TOP_K = 5

# Source credibility weights (tweak as needed)
SOURCE_WEIGHTS = {
    "pubmed": 1.0,
    "europepmc": 0.95,
    "openalex": 0.9,
    "semantic_scholar": 0.9,
    "arxiv": 0.85,
    "loc": 0.85,
    "wikipedia": 0.75,
    "wayback": 0.6,
}


def _keyword_overlap(text: str, keywords: list[str]) -> float:
    """Simple keyword overlap count."""
    if not keywords:
        return 0.5
    text_lower = text.lower()
    hits = sum(1 for kw in keywords if kw.lower() in text_lower)
    return hits / len(keywords)


def rank_results(state: AgentState) -> AgentState:
    """Score each result and keep only the top K."""
    results = state.get("raw_results", [])
    keywords = state.get("sub_topics", [])

    # Score each result
    scored_results = []
    for result in results:
        keyword_score = _keyword_overlap(f"{result.title} {result.snippet}", keywords)
        source_weight = SOURCE_WEIGHTS.get(result.source.lower(), 0.5)
        result.score = round(0.7 * keyword_score + 0.3 * source_weight, 4)

    # Sort by score and keep top K
    ranked = sorted(results, key=lambda r: r.score, reverse=True)[:TOP_K]
    state["ranked_results"] = ranked[:TOP_K]

    print(
        f"Ranked top {len(ranked)} results based on keyword overlap and source credibility."
    )
    for r in state["ranked_results"]:
        print(f"Source: {r.source}, Title: {r.title[:60]}, Score: {r.score:.2f}")
    return state

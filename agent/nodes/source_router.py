"""
agent/nodes/source_router.py
Maps the classified domain and sub-topics to specific sources to query for information.
"""

# Source priority lists per domain.
# Order matters - used as a fallback chain if top sources return nothing.
from agent.state import AgentState


DOMAIN_SOURCE_MAP: dict[str, list[str]] = {
    "medical": [
        "PubMed",
        "ClinicalTrials.gov",
        "WebMD",
        "Mayo Clinic",
        "europepmc",
        "wikipedia",
        "semanticscholar",
    ],
    "scientific": [
        "Google Scholar",
        "arXiv",
        "ScienceDirect",
        "IEEE Xplore",
        "wikipedia",
    ],
    "historical": [
        "JSTOR",
        "National Archives",
        "Google Books",
        "History Today",
        "wikipedia",
    ],
    "legal": ["LexisNexis", "Westlaw", "Justia", "SCOTUSblog"],
    "general": [
        "Google Search",
        "Wikipedia",
        "Encyclopedia Britannica",
        "DuckDuckGo",
        "loc",
    ],
}

# Max number of sources to hit in parallel per query - to control costs and latency
MAX_SOURCES = 3


def route_sources(state: AgentState) -> AgentState:
    """Select sources to query based on classified domain and sub-topics."""
    domain = state.get("domain", "general")
    candidates = DOMAIN_SOURCE_MAP.get(domain, DOMAIN_SOURCE_MAP["general"])
    state["selected_sources"] = candidates[:MAX_SOURCES]

    print(
        f"Routing query to sources: {state['selected_sources']} based on domain: {domain}"
    )
    return state

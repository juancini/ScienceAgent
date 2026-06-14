"""
agent/state.py
Shared state that flows through every node in the LangGraph graph.
"""

from typing import List, Optional, TypedDict
from pydantic import BaseModel


class SearchResult(BaseModel):
    """A single result returned from a source"""

    source: str
    title: str
    url: str
    snippet: str
    score: float = 0.0
    metadata: dict = {}


class AgentState(TypedDict):
    """The state that flows through the graph"""

    # --- Input ---
    query: str

    # --- Classifier Output ---
    domain: Optional[str]
    sub_topics: List[str]

    # --- Source Router Output ---
    selected_sources: List[str]

    # --- Fetcher Output ---
    raw_results: List[SearchResult]

    # --- Ranker Output ---
    ranked_results: List[SearchResult]

    # --- Synthesizer Output ---
    answer: Optional[str]
    error: Optional[str]

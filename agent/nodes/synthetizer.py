"""
agent/nodes/synthetizer.py
LLM node - takes the ranked results and synthesizes a final answer with citations.
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from agent.state import AgentState, AgentState, SearchResult


llm = ChatOpenAI(model="gpt-4-0613", temperature=0.2)

SYSTEM_PROMPT = """You are a research assistant synthesizing an answer from verified sources.

Rules:
1. Base your answer ONLY on the provided sources — do not add outside knowledge.
2. Cite every claim with [N] where N is the source number.
3. After the answer, list every reference with its title, source, and URL.
4. If sources conflict, mention the disagreement explicitly.
5. If sources don't contain enough information, say so clearly.
6. Be concise but complete. Prefer bullet points for multi-part answers."""


def _format_sources(results: list[SearchResult]) -> str:
    """Format the ranked results into a string for the LLM prompt."""

    lines = []
    for i, r in enumerate(results, 1):
        lines.append(
            f"[{i}] Source: {r.source}\n"
            f"    Title: {r.title}\n"
            f"    URL: {r.url}\n"
            f"    Excerpt: {r.snippet}\n"
        )
    return "\n".join(lines)


def synthesize_answer(state: AgentState) -> AgentState:
    """Generate a final answer based on the ranked results."""
    results = state.get("ranked_results", [])
    if not results:
        state["answer"] = "No relevant information found in the sources."
        return state

    sources_text = _format_sources(results)
    user_message = (
        f"Research question: {state['query']}\n\n"
        f"Sources:\n{sources_text}\n\n"
        "Please synthesize a comprehensive answer with citations as per the rules."
    )
    response = llm.invoke(
        [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_message)]
    )

    # TODO the typing here hints that it may break. Check if it breaks
    state["answer"] = response.content
    return state

"""
agent/graph.py
defines, builds and manages the graph of nodes and edges that represent the agent's knowledge and reasoning process.
"""

from langgraph.graph import StateGraph, END

from agent.nodes.classifier import classify_query
from agent.nodes.fetcher import fetch_results
from agent.nodes.ranker import rank_results
from agent.nodes.source_router import route_sources
from agent.nodes.synthetizer import synthesize_answer
from agent.state import AgentState


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    # --- Register Nodes ------------------------
    graph.add_node("classifier", classify_query)
    graph.add_node("source_router", route_sources)
    graph.add_node("fetcher", fetch_results)
    graph.add_node("ranker", rank_results)
    graph.add_node("synthesizer", synthesize_answer)

    # --- Register Edges ------------------------
    graph.set_entry_point("classifier")
    graph.add_edge("classifier", "source_router")
    graph.add_edge("source_router", "fetcher")
    graph.add_edge("fetcher", "ranker")
    graph.add_edge("ranker", "synthesizer")
    graph.add_edge("synthesizer", END)

    return graph.compile()


# Singleton — import this in main.py
science_agent = build_graph()

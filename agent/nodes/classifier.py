"""
agent/nodes/classifier.py
LLM node - classifies the query into a scientific domain and identifies relevant sub-topics.
"""

# To be replaced with swapping LLMs in the future
import json

from agent.state import AgentState, SearchResult
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage


llm = ChatOpenAI(model="gpt-4-0613", temperature=0.0)

SYSTEM_PROMPT = """You are a research query classifier.
Given a user's research question, respond with a JSON object with exactly these fields:
{
  "domain": "<one of: medical, scientific, historical, legal, general>",
  "sub_topics": ["keyword1", "keyword2", "keyword3"]
}

Domain definitions:
- medical: medicine, drugs, diseases, clinical trials, anatomy, pharmacology
- scientific: physics, chemistry, biology, mathematics, computer science, engineering
- historical: history, archives, primary sources, government documents
- legal: law, legislation, court decisions
- general: encyclopedic, mixed, or unclear

Return ONLY the JSON object, no other text."""


def classify_query(state: AgentState) -> AgentState:
    """Classify the query and extract keywords."""
    response = llm.invoke(
        [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=state["query"])]
    )

    try:
        parsed = json.loads(response.content)
        state["domain"] = parsed.get("domain")
        state["sub_topics"] = parsed.get("sub_topics", [])
    except json.JSONDecodeError:
        state["domain"] = "general"
        state["sub_topics"] = state["query"].split()[
            :5
        ]  # Fallback: take first 3 words as keywords

    print(f"Classified domain: {state['domain']}, sub_topics: {state['sub_topics']}")
    return state

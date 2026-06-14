"""
main.py
Entry point for the Science Agent
"""

import argparse
import textwrap


def run_query(query: str) -> None:
    print("=" * 60)
    print(f"Query: {query}")
    print("=" * 60)

    initial_state: AgentState = {
        "query": query,
        "domain": None,
        "sub_topics": [],
        "selected_sources": [],
        "raw_results": [],
        "ranked_results": [],
        "answer": None,
        "error": None,
    }

    final_state = science_agent(initial_state)

    print("=" * 60)
    print("Answer")
    print("=" * 60)
    print(textwrap.fill(final_state["answer"] or "No answer generated", width=80))


def main() -> None:
    """
    Main function to run the Science Agent
    """
    parser = argparse.ArgumentParser(
        description="Science Agent - AI Powered Research Assistant"
    )
    parser.add_argument(
        "--query",
        type=str,
        help="The research query to be processed by the Science Agent",
    )
    args = parser.parse_args()

    if args.query:
        run_query(args.query)
    else:
        print("Science Agent (Type 'quit' to exit)\n")
        while True:
            try:
                query = input("Query › ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nBye!")
                break
            if not query:
                continue
            if query.lower() in {"quit", "exit", "q"}:
                print("Bye!")
                break
            run_query(query)


if __name__ == "__main__":
    main()

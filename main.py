"""Interface CLI de l'agent marché public (Togo)."""

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent conversationnel marché public")
    parser.add_argument(
        "--init",
        action="store_true",
        help="Scrape le portail et indexe les offres dans la base RAG avant de lancer le chat",
    )
    args = parser.parse_args()

    if args.init:
        from tools import indexer_marches

        print("Indexation des offres en cours...")
        print(indexer_marches.invoke({}))

    from agent import agent
    from langchain_core.messages import AIMessageChunk, ToolMessage

    print("\nAgent marché public (gemma4 + Tavily + RAG). Tapez 'quit' pour sortir.\n")

    history = []
    while True:
        try:
            user_input = input("Vous> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if user_input.lower() in {"quit", "exit", "q"}:
            break
        if not user_input:
            continue

        history.append(("user", user_input))
        config = {"recursion_limit": 30}

        answer = ""
        for chunk, metadata in agent.stream(
            {"messages": history}, config=config, stream_mode="messages"
        ):
            node = metadata.get("langgraph_node")
            if node == "tools" and isinstance(chunk, ToolMessage):
                print(f"  [outil] {chunk.name}")
            elif node == "agent" and isinstance(chunk, AIMessageChunk) and chunk.tool_calls:
                for tc in chunk.tool_calls:
                    print(f"  [appel] {tc['name']}")
            elif chunk.content:
                answer += chunk.content
                print(chunk.content, end="", flush=True)

        if answer:
            history.append(("assistant", answer))
        print()


if __name__ == "__main__":
    main()

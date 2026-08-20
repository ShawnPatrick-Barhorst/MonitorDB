import argparse
import asyncio

from dotenv import load_dotenv

from monitordb.llm.agent import build_agent
from monitordb.llm.io_sockets import run_json_stdio

load_dotenv()


def main():
    parser = argparse.ArgumentParser(description="MonitorDB Runner")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Run in headless NDJSON mode for Bubble Tea",
    )
    args = parser.parse_args()

    agent = build_agent("google:gemini-3.5-flash")

    if args.json:
        asyncio.run(run_json_stdio(agent))
    # else:
    #     asyncio.run(run_interactive_repl(agent))


if __name__ == "__main__":
    main()

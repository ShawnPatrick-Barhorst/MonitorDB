import argparse

from dotenv import load_dotenv

from monitordb.io_sockets import (
    GeminiEngine,
    run_interactive_repl,
    run_json_stdio,
)

load_dotenv()


def main():
    parser = argparse.ArgumentParser(description="MonitorDB Runner")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Run in headless NDJSON mode for Bubble Tea",
    )
    args = parser.parse_args()

    engine = GeminiEngine()

    if args.json:
        run_json_stdio(engine)
    else:
        run_interactive_repl(engine)


if __name__ == "__main__":
    main()

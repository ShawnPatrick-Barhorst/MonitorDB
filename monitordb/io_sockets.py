import sys

from monitordb.llm_engine import GeminiEngine, PromptPayload, ResponsePayload


def run_interactive_repl(engine: GeminiEngine):
    session_id = "cli-session"
    print("Gemini CLI ready. Type 'exit' or 'quit' to stop.\n" + "-" * 50)

    while True:
        try:
            user_input = input("\nYou: ").strip()
            if not user_input or user_input.lower() in ("exit", "quit"):
                break

            payload = PromptPayload(prompt=user_input, session_id=session_id)
            response = engine.step_interaction(payload)

            print(f"\nModel: {response.content}")
        except (KeyboardInterrupt, EOFError):
            break


def run_json_stdio(engine: GeminiEngine):
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            payload = PromptPayload.model_validate_json(line)
            response = engine.step_interaction(payload)
            sys.stdout.write(response.model_dump_json() + "\n")
            sys.stdout.flush()
        except Exception as e:
            err_res = ResponsePayload(
                session_id="error",
                type="tool_result",
                content=f"Error: {e!s}",
            )
            sys.stdout.write(err_res.model_dump_json() + "\n")
            sys.stdout.flush()

import sys

from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage

from monitordb.llm.payloads import PromptPayload, ResponsePayload

# def run_interactive_repl(engine: GeminiEngine):
#     session_id = "cli-session"
#     print("Gemini CLI ready. Type 'exit' or 'quit' to stop.\n" + "-" * 50)

#     while True:
#         try:
#             user_input = input("\nYou: ").strip()
#             if not user_input or user_input.lower() in ("exit", "quit"):
#                 break

#             payload = PromptPayload(prompt=user_input, session_id=session_id)
#             response = engine.step_interaction(payload)

#             print(f"\nModel: {response.content}")
#         except (KeyboardInterrupt, EOFError):
#             break


async def run_json_stdio(agent: Agent):
    sessions: dict[str, list[ModelMessage]] = {}
    async with agent:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                payload = PromptPayload.model_validate_json(line)
                history = sessions.get(payload.session_id, [])

                result = await agent.run(payload.prompt, message_history=history)
                sessions[payload.session_id] = result.all_messages()

                response = ResponsePayload(
                    type="model_output", content_type="text", content=result.output
                )

            except Exception as e:
                response = ResponsePayload(
                    type="tool_result",
                    content_type="text",
                    content=f"Error: {e!s}",
                )
            sys.stdout.write(response.model_dump_json() + "\n")
            sys.stdout.flush()

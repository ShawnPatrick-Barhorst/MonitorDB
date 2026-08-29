import json
import sqlite3
import sys
from dataclasses import dataclass, field

from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage
from pydantic_ai.run import AgentRunResult

from monitordb.config import DB_PATH, USER_ID
from monitordb.db.connection import build_conn
from monitordb.llm.payloads import ActionPayload, PromptPayload, ResponsePayload
from monitordb.llm.store import (
    append_messages,
    load_history,
    load_sessions,
    upsert_session,
)


@dataclass
class SessionState:
    conn: sqlite3.Connection
    user_id: int
    session_id: str | None = None
    scratch: list[ModelMessage] = field(default_factory=list)

    def history(self) -> list[ModelMessage]:
        if self.session_id is None:
            return self.scratch

        return load_history(self.conn, self.user_id, self.session_id)

    def record(self, result: AgentRunResult):
        if self.session_id is None:
            self.scratch = result.all_messages()
            return

        upsert_session(self.conn, self.user_id, self.session_id)
        append_messages(self.conn, self.user_id, self.session_id, result.new_messages())

    def switch_session(self, session_id: str | None):
        if session_id == self.session_id:
            return

        self.session_id = session_id
        self.scratch = []


def _handle_action(
    conn: sqlite3.Connection, user_id: str, payload: ActionPayload, current_session: str
):

    command = payload.command
    args = payload.args

    if command == "sessions":
        sessions = load_sessions(conn, user_id)

        if not sessions:
            return ResponsePayload(
                type="command_result",
                content="No sessions yet. Use `/new <name>` to start one.",
            ), current_session
        else:
            content = "\n".join(f"- {session_id}" for session_id in sessions)
            return ResponsePayload(
                type="command_result", content_type="text", content=content
            ), current_session

    elif command == "open":
        sessions = load_sessions(conn, user_id)

        if args in sessions:
            return ResponsePayload(
                type="command_result",
                content_type="text",
                content=f"Loaded session: {args}.",
            ), args

        else:
            return ResponsePayload(
                type="error",
                content="Session doesn't exist yet. Use `/new <name>` to start a new session.",
            ), current_session

    elif command == "new":
        sessions = load_sessions(conn, user_id)

        if args in sessions:
            return ResponsePayload(
                type="command_result",
                content_type="text",
                content="Session already exists.",
            ), current_session
        else:
            return ResponsePayload(
                type="command_result",
                content_type="text",
                content=f"Created new session {args}",
            ), args


async def run_json_stdio(agent: Agent, testing: bool = False):
    conn = build_conn(DB_PATH)
    state = SessionState(conn=conn, user_id=USER_ID)

    async with agent:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                # Handle action or prompt
                if "command" in data:
                    payload = ActionPayload.model_validate(data)
                    response, new_session = _handle_action(
                        conn, USER_ID, payload, state.session_id
                    )
                    state.switch_session(new_session)
                else:
                    payload = PromptPayload.model_validate(data)

                    result = await agent.run(
                        payload.prompt, message_history=state.history()
                    )
                    state.record(result)

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

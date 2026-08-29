import sqlite3

from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter


def upsert_session(conn: sqlite3.Connection, user_id: int, session_id: str):

    cur = conn.cursor()

    cur.execute(
        """
            INSERT INTO session_history(
                session_id,
                user_id
            )
            VALUES (?, ?)
            ON CONFLICT (session_id, user_id) DO UPDATE SET
                updated_epoch = unixepoch()
        """,
        (session_id, user_id),
    )

    conn.commit()


def append_messages(
    conn: sqlite3.Connection, user_id, session_id, model_messages: list[ModelMessage]
):

    cur = conn.cursor()

    sequence_start = cur.execute(
        "SELECT coalesce(max(sequence), -1) + 1 FROM message_history WHERE session_id = ? AND user_id = ?",
        (session_id, user_id),
    ).fetchone()[0]

    rows = []
    for offset, message in enumerate(model_messages):
        part = message.parts[0]

        rows.append(
            (
                session_id,
                user_id,
                sequence_start + offset,
                message.kind,
                part.part_kind,
                str(getattr(part, "content", None) or getattr(part, "args", "")),
                ModelMessagesTypeAdapter.dump_json([message]).decode(),
            )
        )

    cur.executemany(
        """
        INSERT INTO message_history(
            session_id,
            user_id,
            sequence,
            kind,
            content_type,
            text_content,
            message_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        rows,
    )

    cur.execute(
        "UPDATE session_history SET updated_epoch = unixepoch() WHERE session_id = ? AND user_id = ?",
        (session_id, user_id),
    )

    conn.commit()


def load_history(
    conn: sqlite3.Connection, user_id: int, session_id: str
) -> list[ModelMessage]:

    cur = conn.cursor()

    rows = cur.execute(
        """
            SELECT message_json FROM message_history
            WHERE user_id = ? and session_id = ?
            ORDER BY sequence ASC
        """,
        (user_id, session_id),
    ).fetchall()

    return [
        ModelMessagesTypeAdapter.validate_json(message_json)[0]
        for (message_json,) in rows
    ]

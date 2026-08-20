import sqlite3

from monitordb.integrations.google_health_connect.models import (
    SleepSessionItem,
)


def update_sleep_logs(
    conn: sqlite3.Connection, user_id: int, sleep_session_items: list[SleepSessionItem]
) -> dict[str, int]:

    cur = conn.cursor()
    for session in sleep_session_items:
        end_epoch = int(session.session_end_time.timestamp())
        start_epoch = end_epoch - session.duration_seconds

        cur.execute(
            """
            INSERT INTO sleep_sessions (user_id, session_start_epoch, session_end_epoch, duration)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, session_end_epoch) DO UPDATE SET
                session_start_epoch = excluded.session_start_epoch,
                duration = excluded.duration
            RETURNING session_id;
            """,
            (user_id, start_epoch, end_epoch, session.duration_seconds),
        )

        session_id = cur.fetchone()[0]

        # Clear old stages
        cur.execute(
            """
                DELETE FROM sleep_stages WHERE session_id = ?;
            """,
            (session_id,),
        )

        stage_rows = [
            (
                session_id,
                int(stage.start_time.timestamp()),
                int(stage.end_time.timestamp()),
                stage.duration_seconds,
                stage.stage,
                stage.stage_name,
            )
            for stage in session.stages
        ]

        # Re-insert stages
        cur.executemany(
            """
            INSERT INTO sleep_stages (
            session_id, stage_start_epoch, stage_end_epoch, duration, stage, stage_name
            ) VALUES (?, ?, ?, ?, ?, ?);
        """,
            stage_rows,
        )

    return {"status": "success"}

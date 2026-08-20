import sqlite3
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from fastmcp import FastMCP

from monitordb.config import DB_PATH, TIMEZONE, USER_ID
from monitordb.db.connection import build_conn

TZ = ZoneInfo(TIMEZONE)
MAX_ROWS = 90


health_connect_mcp = FastMCP("health-connect")


def _format_datetime(epoch: int) -> str:
    return datetime.fromtimestamp(epoch, tz=TZ).isoformat(timespec="minutes")


@health_connect_mcp.tool
def list_sleep_sessions(days: int = 7) -> list[dict[str, Any]]:
    """List sleep sessions from the last N days, most recent first.

    Returns one row per night with start/end times and total duration in hours.
    """

    conn = build_conn(DB_PATH)
    conn.row_factory = sqlite3.Row

    end_datetime = datetime.now(tz=TZ)
    start_datetime = end_datetime - timedelta(days=days)

    try:
        rows = conn.execute(
            """
            SELECT session_id, session_start_epoch, session_end_epoch, duration
            FROM sleep_sessions
            WHERE user_id = ? AND session_end_epoch BETWEEN ? AND ?
            ORDER BY session_end_epoch DESC
            LIMIT ?;
        """,
            (
                USER_ID,
                int(start_datetime.timestamp()),
                int(end_datetime.timestamp()),
                MAX_ROWS,
            ),
        ).fetchall()

    finally:
        conn.close()

    return [
        {
            "session_id": row["session_id"],
            "start": _format_datetime(row["session_start_epoch"]),
            "end": _format_datetime(row["session_end_epoch"]),
            "duration_hrs": round((row["duration"] or 0) / 3600, 2),
        }
        for row in rows
    ]

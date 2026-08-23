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

    Returns one row per night with start/end times, total duration in hours, and the percentage of time.
    """

    conn = build_conn(DB_PATH)
    conn.row_factory = sqlite3.Row

    end_datetime = datetime.now(tz=TZ)
    start_datetime = end_datetime - timedelta(days=days)

    try:
        rows = conn.execute(
            """
            SELECT 
                s.session_id,
                s.session_start_epoch,
                s.session_end_epoch,
                s.duration,
                COUNT(st.stage) AS stage_count,
                ROUND(100.0 * SUM(CASE WHEN st.stage_name = 'Deep Sleep'  THEN (st.stage_end_epoch - st.stage_start_epoch) ELSE 0 END) / NULLIF(SUM(st.stage_end_epoch - st.stage_start_epoch), 0), 1) AS pct_deep_sleep,
                ROUND(100.0 * SUM(CASE WHEN st.stage_name = 'Light Sleep' THEN (st.stage_end_epoch - st.stage_start_epoch) ELSE 0 END) / NULLIF(SUM(st.stage_end_epoch - st.stage_start_epoch), 0), 1) AS pct_light_sleep,
                ROUND(100.0 * SUM(CASE WHEN st.stage_name = 'REM Sleep'   THEN (st.stage_end_epoch - st.stage_start_epoch) ELSE 0 END) / NULLIF(SUM(st.stage_end_epoch - st.stage_start_epoch), 0), 1) AS pct_rem_sleep,
                ROUND(100.0 * SUM(CASE WHEN st.stage_name = 'Awake'       THEN (st.stage_end_epoch - st.stage_start_epoch) ELSE 0 END) / NULLIF(SUM(st.stage_end_epoch - st.stage_start_epoch), 0), 1) AS pct_awake
            FROM sleep_sessions s
            JOIN sleep_stages st ON s.session_id = st.session_id
            WHERE s.user_id = ? 
            AND s.session_end_epoch BETWEEN ? AND ?
            GROUP BY 
                s.session_id, 
                s.session_start_epoch, 
                s.session_end_epoch, 
                s.duration
            ORDER BY s.session_end_epoch DESC
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
            "pct_deep_sleep": row["pct_deep_sleep"],
            "pct_light_sleep": row["pct_light_sleep"],
            "pct_rem_sleep": row["pct_rem_sleep"],
            "pct_awake": row["pct_awake"],
        }
        for row in rows
    ]


@health_connect_mcp.tool
def get_heart_rate_summary(
    start_datetime: datetime, end_datetime: datetime
) -> dict[str, Any]:
    """Retrieve an analysis of heart_rate within a time window between start_datetime and end_datetime.

    Returns a single dictionary with the average bpm, and a count of bpm spikes
    """

    conn = build_conn(DB_PATH)
    conn.row_factory = sqlite3.Row

    if start_datetime.tzinfo is None:
        start_datetime = start_datetime.replace(tzinfo=TZ)
    if end_datetime.tzinfo is None:
        end_datetime = end_datetime.replace(tzinfo=TZ)

    start_epoch = int(start_datetime.timestamp())
    end_epoch = int(end_datetime.timestamp())

    try:
        report = conn.execute(
            """
            WITH deltas AS (
                SELECT
                    record_epoch,
                    bpm,
                    bpm - LAG(bpm, 1) OVER (ORDER BY record_epoch) AS bpm_delta
                FROM heart_rate_log
                WHERE user_id = ? AND record_epoch BETWEEN ? AND ?
            )
            SELECT
                AVG(bpm) AS avg_bpm,
                COUNT(CASE WHEN bpm_delta >= 20 THEN 1 END) AS spike_count
            FROM deltas;
            """,
            (USER_ID, start_epoch, end_epoch),
        ).fetchone()
    finally:
        conn.close()

    return {
        "average_bpm": round(report["avg_bpm"], 1),
        "spike_count": report["spike_count"],
    }


@health_connect_mcp.tool
def get_nutrition_summary(
    start_datetime: datetime, end_datetime: datetime
) -> list[dict[str, Any]]:
    conn = build_conn(DB_PATH)
    conn.row_factory = sqlite3.Row

    if start_datetime.tzinfo is None:
        start_datetime = start_datetime.replace(tzinfo=TZ)
    if end_datetime.tzinfo is None:
        end_datetime = end_datetime.replace(tzinfo=TZ)

    start_epoch = int(start_datetime.timestamp())
    end_epoch = int(end_datetime.timestamp())

    try:
        report = conn.execute(
            """
            SELECT user_id, meal_name, calories, protein_grams, carbs_grams, fat_grams, sugar_grams, sodium_grams, dietary_fiber_grams, start_epoch 
            FROM nutrition_logs
            WHERE user_id = ? AND start_epoch BETWEEN ? AND ?;
            """,
            (USER_ID, start_epoch, end_epoch),
        ).fetchall()
    finally:
        conn.close()

    return [
        {
            "date": datetime.fromtimestamp(row["start_epoch"], tz=TZ)
            .date()
            .isoformat(),
            "meal": row["meal_name"],
            "calories": row["calories"],
            "protein_grams": row["protein_grams"],
            "carbs_grams": row["carbs_grams"],
            "fat_grams": row["fat_grams"],
            "sugar_grams": row["sugar_grams"],
            "sodium_grams": row["sodium_grams"],
            "dietary_fiber_grams": row["dietary_fiber_grams"],
        }
        for row in report
    ]


@health_connect_mcp.tool
def get_steps_summary(
    user_id: int, start_datetime: datetime, end_datetime: datetime
) -> list[dict[str, Any]]:
    """
    Retrieve daily step counts for a specific user within a date range.

    Args:
        user_id: The unique integer ID of the user.
        start_datetime: Inclusive start time in ISO 8601 format (e.g., '2026-08-15T00:00:00-04:00').
        end_datetime: Exclusive end time in ISO 8601 format (e.g., '2026-08-22T00:00:00-04:00').

    Returns:
        A list of daily records, ordered chronologically:
        [
            {"date": "2026-08-15", "count": 1916},
            {"date": "2026-08-16", "count": 4250}
        ]
    """

    if start_datetime.tzinfo is None:
        start_datetime = start_datetime.replace(tzinfo=TZ)
    if end_datetime.tzinfo is None:
        end_datetime = end_datetime.replace(tzinfo=TZ)

    start_epoch = int(start_datetime.timestamp())
    end_epoch = int(end_datetime.timestamp())

    conn = build_conn(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        report = conn.execute(
            """
            SELECT user_id, start_epoch, end_epoch, count 
            FROM step_logs
            WHERE user_id = ? AND start_epoch BETWEEN ? AND ?
        """,
            (user_id, start_epoch, end_epoch),
        ).fetchall()
    finally:
        conn.close()

    return [
        {
            "date": datetime.fromtimestamp(row["start_epoch"], tz=TZ)
            .date()
            .isoformat(),
            "count": row["count"],
        }
        for row in report
    ]


@health_connect_mcp.tool
def get_oxygen_saturation(
    user_id: int, start_datetime: datetime, end_datetime: datetime
) -> list[dict[str, Any]]:
    """
    Retrieve time-series blood oxygen saturation (SpO2) readings for a user within a specified time range.

    Use this tool to analyze blood oxygen levels during sleep sessions, detect nocturnal hypoxemic dips
    (readings below 90-95%), or review daytime spot-check vitals.

    Args:
        user_id: The unique integer ID of the user.
        start_datetime: Inclusive start timestamp. Can be an ISO 8601 string (e.g., '2026-08-21T23:00:00-04:00')
            or a datetime object.
        end_datetime: Inclusive end timestamp. Can be an ISO 8601 string (e.g., '2026-08-22T08:00:00-04:00')
            or a datetime object.

    Returns:
        A list of chronological SpO2 records containing:
        - "datetime": ISO 8601 formatted timestamp string in the local timezone.
        - "percentage": Blood oxygen saturation level (0.0 - 100.0).

        Example:
        [
            {"datetime": "2026-08-22T02:15:00-04:00", "percentage": 97.5},
            {"datetime": "2026-08-22T02:16:00-04:00", "percentage": 96.0}
        ]
    """
    if start_datetime.tzinfo is None:
        start_datetime = start_datetime.replace(tzinfo=TZ)
    if end_datetime.tzinfo is None:
        end_datetime = end_datetime.replace(tzinfo=TZ)

    start_epoch = int(start_datetime.timestamp())
    end_epoch = int(end_datetime.timestamp())

    conn = build_conn(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        report = conn.execute(
            """
        SELECT user_id, epoch, percentage 
        FROM oxygen_saturation_logs
        WHERE user_id = ? AND epoch BETWEEN ? AND ?
        
        """,
            (user_id, start_epoch, end_epoch),
        ).fetchall()

    finally:
        conn.close()

    return [
        {
            "datetime": datetime.fromtimestamp(row["epoch"], tz=TZ).isoformat(),
            "percentage": row["percentage"],
        }
        for row in report
    ]

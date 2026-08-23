import sqlite3
from datetime import datetime
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


def _format_date(epoch: int) -> str:
    return datetime.fromtimestamp(epoch, tz=TZ).date().isoformat()


@health_connect_mcp.tool
def list_sleep_sessions(
    start_datetime: datetime, end_datetime: datetime
) -> list[dict[str, Any]]:
    """
    List sleep sessions and sleep statistics within a time window between start_datetime and end_datetime

    Args:
        start_datetime (ISO-8601): The beginning of the time window to search.
            If no timezone is provided, the user's local timezone is assumed.
        end_datetime (ISO-8601): The end of the time window to search.
            If no timezone is provided, the user's local timezone is assumed.

    Returns:
        List of dictionaries containing features for each sleep session:
        - start (str): start datetime of sleep session
        - end (str): end_datetime of sleep session
        - duration_hrs (int): duration of sleep in hours
        - pct_deep_sleep (float): percentage of sleep spent in deep sleep
        - pct_light_sleep (float): percentage of sleep spent in light sleep
        - pct_rem_sleep (float): percentage of sleep spent in rem sleep
        - pct_awake (float): percentage of sleep spent awake


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
                start_epoch,
                end_epoch,
                MAX_ROWS,
            ),
        ).fetchall()

    finally:
        conn.close()

    return [
        {
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
    """
    Retrieve an analysis of heart_rate within a time window between start_datetime and end_datetime.

    Args:
        start_datetime (ISO-8601): The beginning of the time window to search.
            If no timezone is provided, the user's local timezone is assumed.
        end_datetime (ISO-8601): The end of the time window to search.
            If no timezone is provided, the user's local timezone is assumed.

    Returns:
        Dictionary containing:
        - average_bpm (float): Mean heart rate across the window.
        - spike_count (int): Count of rapid heart rate surges >=threshold.
        - start_datetime (str): Window start datetime.
        - end_datetime (str): Window end datetime.
        - sample_count (int): Number of data points analyzed.
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
                COUNT(CASE WHEN bpm_delta >= 20 THEN 1 END) AS spike_count,
                COUNT(bpm) AS sample_count
            FROM deltas;
            """,
            (USER_ID, start_epoch, end_epoch),
        ).fetchone()
    finally:
        conn.close()

    return {
        "average_bpm": round(report["avg_bpm"], 1)
        if report["avg_bpm"] is not None
        else None,
        "spike_count": report["spike_count"],
        "start_datetime": start_datetime.isoformat(timespec="minutes"),
        "end_datetime": end_datetime.isoformat(timespec="minutes"),
        "sample_count": report["sample_count"],
    }


@health_connect_mcp.tool
def get_nutrition_summary(
    start_datetime: datetime, end_datetime: datetime
) -> list[dict[str, Any]]:
    """
    Retrieve logged meal details and macronutrient breakdowns for a specific time range.

    Use this tool whenever the user asks about what they ate, their calorie intake,
    or specific nutrient consumption (protein, carbs, fat, sugar, sodium, fiber)
    over a day, week, or custom date range.

    Args:
        start_datetime (ISO-8601): The beginning of the time window to search.
            If no timezone is provided, the user's local timezone is assumed.
        end_datetime (ISO-8601): The end of the time window to search.
            If no timezone is provided, the user's local timezone is assumed.

    Returns:
        list[dict[str, Any]]: List by day and meal; sum of nutrition information per meal:
        - date (str): Date meal occured
        - meal (str): Name of meal e.g.("Dinner", "Snack", etc)
        - calories (int): Calorie count of meal
        - protein_grams (int): Protein count in grams
        - carbs_grams (int): Carb count in grams
        - fat_grams (int): Fat count in grams
        - sugar_grams (int): Sugar count in grams
        - sodium_grams (int): Sodium count in grams
        - dietary_fiber_grams (int): Fiber count in grams
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
            "date": _format_date(row["start_epoch"]),
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
    start_datetime: datetime, end_datetime: datetime
) -> list[dict[str, Any]]:
    """
    Retrieve daily step counts for a specific user within a date range.

    Use this tool whenever the user asks about daily activity, or daily steps.

    Args:
        start_datetime (ISO-8601): The beginning of the time window to search.
            If no timezone is provided, the user's local timezone is assumed.
        end_datetime (ISO-8601): The end of the time window to search.
            If no timezone is provided, the user's local timezone is assumed.

    Returns:
        A list of daily records, ordered chronologically:
        - date: date of record
        - count: number of steps
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
            (USER_ID, start_epoch, end_epoch),
        ).fetchall()
    finally:
        conn.close()

    return [
        {
            "date": _format_date(row["start_epoch"]),
            "count": row["count"],
        }
        for row in report
    ]


@health_connect_mcp.tool
def get_oxygen_saturation(
    start_datetime: datetime, end_datetime: datetime
) -> list[dict[str, Any]]:
    """
    Retrieve time-series blood oxygen saturation (SpO2) readings for a user within a specified time range.

    Use this tool to analyze blood oxygen levels during sleep sessions, detect nocturnal hypoxemic dips
    (readings below 90-95%), or review daytime spot-check vitals.

    Args:
        start_datetime (ISO-8601): The beginning of the time window to search.
            If no timezone is provided, the user's local timezone is assumed.
        end_datetime (ISO-8601): The end of the time window to search.
            If no timezone is provided, the user's local timezone is assumed.

    Returns:
        A list of chronological SpO2 records containing:
        - datetime: ISO 8601 formatted timestamp string in the local timezone.
        - percentage: Blood oxygen saturation level (0.0 - 100.0).
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
        ORDER BY epoch ASC
        
        """,
            (USER_ID, start_epoch, end_epoch),
        ).fetchall()

    finally:
        conn.close()

    return [
        {
            "datetime": _format_datetime(row["epoch"]),
            "percentage": row["percentage"],
        }
        for row in report
    ]

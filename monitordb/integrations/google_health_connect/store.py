import sqlite3

from monitordb.integrations.google_health_connect.models import (
    HeartRateItem,
    NutritionLogItem,
    SleepSessionItem,
    StepsItem,
)
from monitordb.logging_utils import logged


@logged
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

    return {"status": "success", "count": len(sleep_session_items)}


@logged
def update_heart_rate_logs(
    conn: sqlite3.Connection, user_id: int, heart_rate_items: list[HeartRateItem]
) -> dict[str, int]:
    cur = conn.cursor()
    for heart_rate_record in heart_rate_items:
        record_epoch = int(heart_rate_record.time.timestamp())

        cur.execute(
            """
            INSERT INTO heart_rate_log (user_id, record_epoch, bpm)
            VALUES(?, ?, ?)
            ON CONFLICT(user_id, record_epoch) DO UPDATE SET
                bpm = excluded.bpm
            RETURNING record_epoch
        """,
            (user_id, record_epoch, heart_rate_record.bpm),
        )

    return {"status": "success", "count": len(heart_rate_items)}


@logged
def update_nutrition_log(
    conn: sqlite3.Connection, user_id: int, nutrition_log_items: list[NutritionLogItem]
) -> dict[str, int]:

    cur = conn.cursor()
    for nutrition_log in nutrition_log_items:
        start_epoch = int(nutrition_log.start_time.timestamp())
        end_epoch = int(nutrition_log.end_time.timestamp())

        cur.execute(
            """
        INSERT INTO nutrition_logs (user_id, calories, protein_grams, carbs_grams, fat_grams, sugar_grams, sodium_grams, dietary_fiber_grams, meal_name, start_epoch, end_epoch)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, start_epoch) DO UPDATE SET
            calories = excluded.calories,
            protein_grams = excluded.protein_grams,
            carbs_grams = excluded.carbs_grams,
            fat_grams = excluded.fat_grams,
            sugar_grams = excluded.sugar_grams,
            sodium_grams = excluded.sodium_grams,
            dietary_fiber_grams = excluded.dietary_fiber_grams,
            meal_name = excluded.meal_name,
            end_epoch = excluded.end_epoch
        """,
            (
                user_id,
                float(nutrition_log.calories),
                float(nutrition_log.protein_grams),
                float(nutrition_log.carbs_grams),
                float(nutrition_log.fat_grams),
                float(nutrition_log.sugar_grams),
                float(nutrition_log.sodium_grams),
                float(nutrition_log.dietary_fiber_grams),
                nutrition_log.name,
                start_epoch,
                end_epoch,
            ),
        )

    return {"status": "success", "count": len(nutrition_log_items)}


@logged
def update_step_log(
    conn: sqlite3.Connection, user_id: int, steps_items: list[StepsItem]
) -> dict[str, int]:

    cur = conn.cursor()
    for step_record in steps_items:
        start_epoch = int(step_record.start_time.timestamp())
        end_epoch = int(step_record.end_time.timestamp())

        cur.execute(
            """
            INSERT INTO step_logs (user_id, start_epoch, end_epoch, count)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, start_epoch) DO UPDATE SET
                end_epoch = excluded.end_epoch,
                count = excluded.count
            """,
            (user_id, start_epoch, end_epoch, step_record.count),
        )

    return {"status": "success", "count": len(steps_items)}

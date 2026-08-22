from monitordb.config import DB_PATH, USER_ID
from monitordb.db.connection import build_conn
from monitordb.integrations.google_health_connect.store import (
    update_heart_rate_logs,
    update_nutrition_log,
    update_sleep_logs,
    update_step_log,
)
from monitordb.integrations.google_health_connect.transform import (
    parse_heart_rate,
    parse_nutrition_log,
    parse_sleep_sessions,
    parse_steps,
)

HEALTH_CONNECT_HANDLERS = {
    "sleep": (parse_sleep_sessions, update_sleep_logs),
    "heart_rate": (parse_heart_rate, update_heart_rate_logs),
    "nutrition": (parse_nutrition_log, update_nutrition_log),
    "steps": (parse_steps, update_step_log),
}


def health_connect_sync(payload: dict) -> dict:

    conn = build_conn(DB_PATH)
    results = {}

    try:
        for section_name, (parse, store) in HEALTH_CONNECT_HANDLERS.items():
            section = payload.get(section_name)

            if not section:
                continue

            section_items = parse(section)
            results[section_name] = store(conn, USER_ID, section_items)
        conn.commit()
    finally:
        conn.close()
    return results

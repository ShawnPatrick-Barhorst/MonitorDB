from monitordb.config import DB_PATH, USER_ID
from monitordb.db.connection import build_conn
from monitordb.integrations.google_health_connect.store import update_sleep_logs
from monitordb.integrations.google_health_connect.transform import (
    parse_sleep_sessions,
)


def health_connect_sync(payload: list[dict]):

    conn = build_conn(DB_PATH)
    result = {}

    sleep_section = payload.get("sleep")

    try:
        sleep_section = payload.get("sleep")
        if sleep_section:
            sleep_session_items = parse_sleep_sessions(sleep_section)
            result["sleep"] = update_sleep_logs(conn, USER_ID, sleep_session_items)
        conn.commit()
    finally:
        conn.close()
    return result

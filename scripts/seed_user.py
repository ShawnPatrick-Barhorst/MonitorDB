import json
from pathlib import Path

from monitordb.config import DB_PATH, PROJECT_ROOT
from monitordb.db.connection import build_conn
from monitordb.db.repository import upsert_user

USER_JSON_PATH = PROJECT_ROOT / "example_user.json"


def main():
    json_file = Path(USER_JSON_PATH)
    if not json_file.exists():
        raise FileNotFoundError(f"Configuration file '{USER_JSON_PATH}' not found.")

    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Flatten top-level user config + profile details
    user_payload = {
        "user_id": data.get("user_id", 1),
        "is_active": data.get("is_active", 1),
        **data.get("profile", {}),
    }

    conn = build_conn(str(DB_PATH))
    user_id = upsert_user(conn, user_payload)
    print(f"Successfully upserted user ID: {user_id}")

    conn.close()


if __name__ == "__main__":
    main()

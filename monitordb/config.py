import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DB_PATH = Path(
    os.environ.get("MONITORDB_PATH", PROJECT_ROOT / "database" / "user_monitor.db")
)
USER_ID = int(os.environ.get("MONITORDB_USER_ID", 1))
TIMEZONE = LOCAL_TZ = "America/New_York"

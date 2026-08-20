import sqlite3
from pathlib import Path


def build_conn(url: str) -> sqlite3.Connection:
    Path(url).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(url)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

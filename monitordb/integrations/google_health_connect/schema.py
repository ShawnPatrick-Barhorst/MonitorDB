import sqlite3


def init_health_connect_tables(conn: sqlite3):
    build_heart_rate_log(conn)
    build_sleep_log(conn)
    build_nutrition_log(conn)
    build_steps_log(conn)
    build_oxygen_saturation_log(conn)


def build_heart_rate_log(conn: sqlite3.Connection):

    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS heart_rate_log(
            user_id INTEGER NOT NULL,
            record_epoch INTEGER NOT NULL,
            bpm INTEGER NOT NULL,
            PRIMARY KEY (user_id, record_epoch),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """
    )

    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_hr_user_time ON heart_rate_log(user_id, record_epoch DESC);"
    )

    conn.commit()


def build_sleep_log(conn: sqlite3.Connection):

    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sleep_sessions(
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_start_epoch INTEGER,
            session_end_epoch INTEGER,
            duration INTEGER,

            FOREIGN KEY (user_id) REFERENCES users(user_id)
            UNIQUE(user_id, session_end_epoch)
        );
    """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sleep_stages(
            stage_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            stage_start_epoch INTEGER,
            stage_end_epoch INTEGER,
            duration INTEGER,
            stage INTEGER,
            stage_name TEXT,

            FOREIGN KEY (session_id) REFERENCES sleep_sessions(session_id)
        );
        """
    )

    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_sleep_session_user_start ON sleep_sessions(user_id, session_start_epoch DESC);"
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_sleep_stages_id ON sleep_stages(session_id);"
    )

    conn.commit()


def build_nutrition_log(conn: sqlite3):

    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS nutrition_logs(
            user_id INTEGER NOT NULL,
            meal_name TEXT,
            calories REAL,
            protein_grams REAL,
            carbs_grams REAL,
            fat_grams REAL,
            sugar_grams REAL,
            sodium_grams REAL,
            dietary_fiber_grams REAL,
            start_epoch INT,
            end_epoch INT,

            FOREIGN KEY (user_id) REFERENCES users(user_id)
            UNIQUE(user_id, start_epoch)
        );
        """
    )
    conn.commit()


def build_steps_log(conn: sqlite3.Connection):
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS step_logs(
            user_id INTEGER NOT NULL,
            start_epoch INTEGER NOT NULL,
            end_epoch INTEGER NOT NULL,
            count INTEGER NOT NULL,

            FOREIGN KEY (user_id) REFERENCES users(user_id)
            UNIQUE(user_id, start_epoch)
        );
        """
    )
    conn.commit()


def build_oxygen_saturation_log(conn: sqlite3.Connection):
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS oxygen_saturation_logs(
            user_id INTEGER NOT NULL,
            epoch INTEGER NOT NULL,
            percentage INTEGER NOT NULL,

            FOREIGN KEY (user_id) REFERENCES users(user_id),
            UNIQUE(user_id, epoch)
        );
        """
    )
    conn.commit()

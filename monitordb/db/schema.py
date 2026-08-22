import sqlite3

from monitordb.db.connection import build_conn


def init_tables(url: str):
    conn = build_conn(url)
    build_user_table(conn)
    build_psych_evaluation_table(conn)
    build_subjective_state_table(conn)
    build_calendar_events_table(conn)
    build_heart_rate_log(conn)
    build_sleep_log(conn)
    build_nutrition_log(conn)


def build_user_table(conn: sqlite3.Connection):

    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY,
            is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0, 1)),
            first_name TEXT,
            last_name TEXT,
            gender TEXT,
            date_of_birth INTEGER,
            height_cm INTEGER,
            weight_lb INTEGER,
            prescriptions TEXT,
            profession TEXT,
            relationship_status TEXT,
            sexual_orientation TEXT,
            nationality TEXT,
            address TEXT
        );
    """)

    cur.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);
    """
    )

    conn.commit()


def build_psych_evaluation_table(conn: sqlite3.Connection):

    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS psych_evaluations (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            evaluated_at INTEGER NOT NULL DEFAULT (unixepoch()),
            evaluator_source TEXT NOT NULL,
            
            -- Typologies
            mbti TEXT CHECK(length(mbti) = 4),
            enneagram TEXT,
            chronotype TEXT,
            attachment_style TEXT,

            -- Big Five / OCEAN (0.0 to 1.0)
            ocean_openness REAL CHECK(ocean_openness BETWEEN 0.0 AND 1.0),
            ocean_conscientiousness REAL CHECK(ocean_conscientiousness BETWEEN 0.0 AND 1.0),
            ocean_extraversion REAL CHECK(ocean_extraversion BETWEEN 0.0 AND 1.0),
            ocean_agreeableness REAL CHECK(ocean_agreeableness BETWEEN 0.0 AND 1.0),
            ocean_neuroticism REAL CHECK(ocean_neuroticism BETWEEN 0.0 AND 1.0),

            -- Cognitive & Behavioral Dimensions
            locus_of_control TEXT,
            risk_tolerance REAL CHECK(risk_tolerance BETWEEN 0.0 AND 1.0),
            ambiguity_tolerance REAL CHECK(ambiguity_tolerance BETWEEN 0.0 AND 1.0),
            frustration_tolerance REAL CHECK(frustration_tolerance BETWEEN 0.0 AND 1.0),
            conflict_style TEXT,
            learning_style TEXT,

            -- Stress & Drive
            core_motivators TEXT,
            stress_manifestation TEXT,
            burnout_risk_score REAL CHECK(burnout_risk_score BETWEEN 0.0 AND 1.0),

            -- Synthesis & Metadata
            summary_markdown TEXT NOT NULL,
            raw_eval_json TEXT,

            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_psych_user_time 
        ON psych_evaluations(user_id, evaluated_at DESC);
    """)

    conn.commit()


def build_subjective_state_table(conn: sqlite3.Connection):

    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS subjective_state(

            -- Subjective & Qualitative Scales
            user_id INTEGER NOT NULL,
            entered_epoch INTEGER NOT NULL,
            focus_depth INTEGER CHECK(focus_depth BETWEEN 1 AND 5),
            mental_energy INTEGER CHECK(mental_energy BETWEEN 1 AND 5),
            perceived_strain INTEGER CHECK(perceived_strain BETWEEN 1 AND 5),
            mood_valence INTEGER CHECK(mood_valence BETWEEN 1 AND 5),
            arousal_level INTEGER CHECK(arousal_level BETWEEN 1 AND 5),
            physical_level INTEGER CHECK(physical_level BETWEEN 1 AND 5),
            PRIMARY KEY (user_id, entered_epoch),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """
    )

    conn.commit()


def build_calendar_events_table(conn: sqlite3.Connection):

    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS calendar_events(
            event_id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,

            start_epoch INTEGER NOT NULL,
            end_epoch INTEGER,

            summary TEXT,
            description TEXT,
            location TEXT,
            event_type TEXT DEFAULT 'default',
            status TEXT,
            is_recurring BOOLEAN,

            created_by TEXT,
            is_creator BOOLEAN,
            organized_by TEXT,
            is_organizer BOOLEAN,

            created_on TEXT,
            updated_on TEXT,

            synced_at INTEGER DEFAULT (unixepoch()),

            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_calendar_events_time
        ON calendar_events(user_id, start_epoch ASC, end_epoch ASC)
    """)

    conn.commit()


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

import sqlite3


def build_conn(url: str) -> sqlite3.Connection:
    conn = sqlite3.connect(url)
    return conn


def build_user_table(conn: sqlite3.Connection):

    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY,
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

    conn.commit()
    conn.close()


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


def build_subjective_state_table(conn: sqlite3.Connections):

    cur = conn.cursor()

    cur.exectue(
        """
        CREATE TABLE IF NOT EXISTS subjective_state(

            -- Subjective & Qualitative Scales
            focus_depth INTEGER CHECK(focus_depth BETWEEN 1 AND 5),
            mental_energy INTERGER CHECK(mental_energy BETWEEN 1 AND 5),
            perceived_strain INTEGER CHECK(percieved_strain BETWEEN 1 AND 5),
            mood_valence INTEGER CHECK(mood_valence BETWEEN 1 AND 5),
            arousal_level INTEGER CHECK(arousal_level BETWEEN 1 AND 5),
            physical_level INTEGER CHECK(physical_level BETWEEN 1 AND 5),
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

            start_datetime TEXT NOT NULL,
            end_datetime TEXT NOT NULL,

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

            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_calendar_events_time
        ON calendar_events(user_id, start_datetime ASC, end_datetime ASC)
    """)

    conn.commit()


def build_heart_rate_log(conn: sqlite3.Connection):

    cur = conn.cursor

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS heart_rate_log(
            timestamp_epoch INTEGER PRIMARY KEY,
            bpm INTEGER NOT NULL,
            source TEXT
        )
    """
    )

    conn.commit()


def build_sleep_log(conn: sqlite3.Connection):
    return


def build_intake_log(conn: sqlite3.Connection):
    return


def build_fitness_log(conn: sqlite3.Connection):
    return


def build_banking_log(conn: sqlite3.Connection):
    return

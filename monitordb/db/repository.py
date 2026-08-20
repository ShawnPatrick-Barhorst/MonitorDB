import sqlite3

from monitordb.db.models import UserProfile


def upsert_user(conn: sqlite3.Connection, user: dict[str, any]) -> int:
    """Upserts a validated UserProfile instance into the users table."""

    user = UserProfile.model_validate(user)

    query = """
        INSERT INTO users (
            user_id,
            is_active,
            first_name,
            last_name,
            gender,
            date_of_birth,
            height_cm,
            weight_lb,
            prescriptions,
            profession,
            relationship_status,
            sexual_orientation,
            nationality,
            address
        ) VALUES (
            :user_id,
            :is_active,
            :first_name,
            :last_name,
            :gender,
            :date_of_birth,
            :height_cm,
            :weight_lb,
            :prescriptions,
            :profession,
            :relationship_status,
            :sexual_orientation,
            :nationality,
            :address
        )
        ON CONFLICT(user_id) DO UPDATE SET
            is_active = coalesce(excluded.is_active, users.is_active),
            first_name = coalesce(excluded.first_name, users.first_name),
            last_name = coalesce(excluded.last_name, users.last_name),
            gender = coalesce(excluded.gender, users.gender),
            date_of_birth = coalesce(excluded.date_of_birth, users.date_of_birth),
            height_cm = coalesce(excluded.height_cm, users.height_cm),
            weight_lb = coalesce(excluded.weight_lb, users.weight_lb),
            prescriptions = coalesce(excluded.prescriptions, users.prescriptions),
            profession = coalesce(excluded.profession, users.profession),
            relationship_status = coalesce(excluded.relationship_status, users.relationship_status),
            sexual_orientation = coalesce(excluded.sexual_orientation, users.sexual_orientation),
            nationality = coalesce(excluded.nationality, users.nationality),
            address = coalesce(excluded.address, users.address)
        RETURNING user_id;
    """

    # model_dump() turns all fields into a dict matching the SQL :named_params
    cur = conn.execute(query, user.model_dump())
    row = cur.fetchone()
    conn.commit()
    return row[0]

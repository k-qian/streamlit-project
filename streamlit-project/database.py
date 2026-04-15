import sqlite3
import os
import uuid

import bcrypt

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "app.db")


def get_connection() -> sqlite3.Connection:
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES users(username)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS health_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            log_date DATE NOT NULL DEFAULT (DATE('now')),
            pregnancy_week INTEGER NOT NULL CHECK(pregnancy_week BETWEEN 1 AND 42),
            weight REAL,
            height REAL,
            heart_rate INTEGER,
            mood TEXT,
            sleep_quality TEXT,
            exercise TEXT,
            symptoms TEXT,
            notes TEXT,
            ai_advice TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES users(username)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES users(username)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS childcare_centers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            name TEXT NOT NULL,
            address TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS exercise_videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS music_recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


def seed_default_user() -> None:
    conn = get_connection()
    cursor = conn.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        hashed = bcrypt.hashpw(b"admin123", bcrypt.gensalt())
        conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            ("admin", hashed.decode("utf-8")),
        )
        conn.commit()
    conn.close()


def verify_user(username: str, password: str) -> bool:
    conn = get_connection()
    row = conn.execute(
        "SELECT password_hash FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    if row is None:
        return False
    stored_hash = row["password_hash"].encode("utf-8")
    return bcrypt.checkpw(password.encode("utf-8"), stored_hash)


def create_user(username: str, password: str) -> bool:
    conn = get_connection()
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, hashed.decode("utf-8")),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_user_count() -> int:
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    return count


def create_session(username: str) -> str:
    token = str(uuid.uuid4())
    conn = get_connection()
    conn.execute(
        "INSERT INTO sessions (token, username) VALUES (?, ?)",
        (token, username),
    )
    conn.commit()
    conn.close()
    return token


def validate_session(token: str) -> str | None:
    if not token:
        return None
    conn = get_connection()
    row = conn.execute(
        "SELECT username FROM sessions WHERE token = ?", (token,)
    ).fetchone()
    conn.close()
    if row is None:
        return None
    return row["username"]


def delete_session(token: str) -> None:
    if not token:
        return
    conn = get_connection()
    conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()
    conn.close()


# ── Health Logs ──────────────────────────────────────────────


def save_health_log(
    username: str,
    pregnancy_week: int,
    weight: float | None,
    height: float | None,
    heart_rate: int | None,
    mood: str | None,
    sleep_quality: str | None,
    exercise: str | None,
    symptoms_json: str | None,
    notes: str | None,
) -> int:
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO health_logs
           (username, pregnancy_week, weight, height, heart_rate,
            mood, sleep_quality, exercise, symptoms, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (username, pregnancy_week, weight, height, heart_rate,
         mood, sleep_quality, exercise, symptoms_json, notes),
    )
    conn.commit()
    row_id = cursor.lastrowid
    conn.close()
    return row_id


def update_health_log_ai_advice(log_id: int, advice: str) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE health_logs SET ai_advice = ? WHERE id = ?",
        (advice, log_id),
    )
    conn.commit()
    conn.close()


def get_health_logs(username: str, limit: int | None = None) -> list[sqlite3.Row]:
    conn = get_connection()
    query = "SELECT * FROM health_logs WHERE username = ? ORDER BY created_at DESC"
    if limit:
        query += f" LIMIT {int(limit)}"
    rows = conn.execute(query, (username,)).fetchall()
    conn.close()
    return rows


def get_latest_health_log(username: str) -> sqlite3.Row | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM health_logs WHERE username = ? ORDER BY created_at DESC LIMIT 1",
        (username,),
    ).fetchone()
    conn.close()
    return row


def get_health_log_count(username: str) -> int:
    conn = get_connection()
    count = conn.execute(
        "SELECT COUNT(*) FROM health_logs WHERE username = ?", (username,)
    ).fetchone()[0]
    conn.close()
    return count


def get_health_logs_in_range(username: str, days: int) -> list[sqlite3.Row]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT * FROM health_logs
           WHERE username = ? AND log_date >= DATE('now', ?)
           ORDER BY created_at DESC""",
        (username, f"-{days} days"),
    ).fetchall()
    conn.close()
    return rows


# ── Notifications ────────────────────────────────────────────


def get_unread_notification_count(username: str) -> int:
    conn = get_connection()
    count = conn.execute(
        "SELECT COUNT(*) FROM notifications WHERE username = ? AND is_read = 0",
        (username,),
    ).fetchone()[0]
    conn.close()
    return count


def get_notifications(username: str) -> list[sqlite3.Row]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM notifications WHERE username = ? ORDER BY created_at DESC",
        (username,),
    ).fetchall()
    conn.close()
    return rows


def mark_notifications_read(username: str) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE notifications SET is_read = 1 WHERE username = ? AND is_read = 0",
        (username,),
    )
    conn.commit()
    conn.close()


def get_notifications_by_status(username: str, is_read: int) -> list[sqlite3.Row]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM notifications WHERE username = ? AND is_read = ? ORDER BY created_at DESC",
        (username, is_read),
    ).fetchall()
    conn.close()
    return rows


def mark_single_notification_read(id_: int) -> None:
    conn = get_connection()
    conn.execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (id_,))
    conn.commit()
    conn.close()


def delete_notification(id_: int) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM notifications WHERE id = ?", (id_,))
    conn.commit()
    conn.close()


def create_notification(username: str, title: str, message: str) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT INTO notifications (username, title, message) VALUES (?, ?, ?)",
        (username, title, message),
    )
    conn.commit()
    conn.close()


# ── Childcare Centers ───────────────────────────────────────


def get_childcare_centers() -> list[sqlite3.Row]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM childcare_centers ORDER BY id"
    ).fetchall()
    conn.close()
    return rows


def add_childcare_center(type_: str, name: str, address: str, phone: str) -> int:
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO childcare_centers (type, name, address, phone) VALUES (?, ?, ?, ?)",
        (type_, name, address, phone),
    )
    conn.commit()
    row_id = cursor.lastrowid
    conn.close()
    return row_id


def update_childcare_center(id_: int, type_: str, name: str, address: str, phone: str) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE childcare_centers SET type=?, name=?, address=?, phone=? WHERE id=?",
        (type_, name, address, phone, id_),
    )
    conn.commit()
    conn.close()


def delete_childcare_center(id_: int) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM childcare_centers WHERE id=?", (id_,))
    conn.commit()
    conn.close()


def bulk_insert_childcare_centers(rows: list[tuple], clear_first: bool = False) -> int:
    conn = get_connection()
    if clear_first:
        conn.execute("DELETE FROM childcare_centers")
    conn.executemany(
        "INSERT INTO childcare_centers (type, name, address, phone) VALUES (?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    count = len(rows)
    conn.close()
    return count


# ── Exercise Videos ─────────────────────────────────────────


def get_exercise_videos() -> list[sqlite3.Row]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM exercise_videos ORDER BY id"
    ).fetchall()
    conn.close()
    return rows


def add_exercise_video(title: str, url: str) -> int:
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO exercise_videos (title, url) VALUES (?, ?)",
        (title, url),
    )
    conn.commit()
    row_id = cursor.lastrowid
    conn.close()
    return row_id


def update_exercise_video(id_: int, title: str, url: str) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE exercise_videos SET title=?, url=? WHERE id=?",
        (title, url, id_),
    )
    conn.commit()
    conn.close()


def delete_exercise_video(id_: int) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM exercise_videos WHERE id=?", (id_,))
    conn.commit()
    conn.close()


def bulk_insert_exercise_videos(rows: list[tuple], clear_first: bool = False) -> int:
    conn = get_connection()
    if clear_first:
        conn.execute("DELETE FROM exercise_videos")
    conn.executemany(
        "INSERT INTO exercise_videos (title, url) VALUES (?, ?)",
        rows,
    )
    conn.commit()
    count = len(rows)
    conn.close()
    return count


# --- Music recommendations ---

def get_music_recommendations() -> list[sqlite3.Row]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM music_recommendations ORDER BY id"
    ).fetchall()
    conn.close()
    return rows


def add_music_recommendation(title: str, url: str) -> int:
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO music_recommendations (title, url) VALUES (?, ?)",
        (title, url),
    )
    conn.commit()
    row_id = cursor.lastrowid
    conn.close()
    return row_id


def update_music_recommendation(id_: int, title: str, url: str) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE music_recommendations SET title=?, url=? WHERE id=?",
        (title, url, id_),
    )
    conn.commit()
    conn.close()


def delete_music_recommendation(id_: int) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM music_recommendations WHERE id=?", (id_,))
    conn.commit()
    conn.close()


def bulk_insert_music_recommendations(rows: list[tuple], clear_first: bool = False) -> int:
    conn = get_connection()
    if clear_first:
        conn.execute("DELETE FROM music_recommendations")
    conn.executemany(
        "INSERT INTO music_recommendations (title, url) VALUES (?, ?)",
        rows,
    )
    conn.commit()
    count = len(rows)
    conn.close()
    return count

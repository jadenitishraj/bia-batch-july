"""SQLite remembers emails, progress, and chat notifications."""
import sqlite3
import time
from backend.settings import DATABASE


def connect():
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def setup():
    with connect() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS settings (name TEXT PRIMARY KEY, value REAL);
            CREATE TABLE IF NOT EXISTS requests (
                id TEXT PRIMARY KEY, subject TEXT, status TEXT,
                meeting_time TEXT, error TEXT, received_at REAL
            );
            CREATE TABLE IF NOT EXISTS notices (
                id TEXT PRIMARY KEY, text TEXT, created REAL
            );
        """)
        # Keep this cutoff after restart. Old emails must not create meetings.
        db.execute("INSERT OR IGNORE INTO settings VALUES ('since', ?)", (time.time(),))


def first_start():
    with connect() as db:
        return db.execute("SELECT value FROM settings WHERE name='since'").fetchone()[0]


def remember(email):
    with connect() as db:
        db.execute("INSERT OR IGNORE INTO requests VALUES (?, ?, 'received', NULL, '', ?)",
                   (email["id"], email["subject"], email["received_at"]))


def request(message_id):
    with connect() as db:
        row = db.execute("SELECT * FROM requests WHERE id=?", (message_id,)).fetchone()
        return dict(row) if row else None


def save_status(message_id, status, meeting_time=None, error=""):
    with connect() as db:
        db.execute("UPDATE requests SET status=?, meeting_time=COALESCE(?, meeting_time), error=? WHERE id=?",
                   (status, meeting_time, error, message_id))


def add_notice(notice_id, text):
    with connect() as db:
        db.execute("INSERT OR IGNORE INTO notices VALUES (?, ?, ?)", (notice_id, text, time.time()))


def snapshot():
    with connect() as db:
        requests = [dict(row) for row in db.execute("SELECT * FROM requests ORDER BY received_at DESC")]
        notices = [dict(row) for row in db.execute("SELECT * FROM notices ORDER BY created")]
    return {"requests": requests, "notices": notices}

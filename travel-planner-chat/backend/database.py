"""SQLite storage for the classroom app with per-account ownership."""
import sqlite3
from contextlib import closing
from pathlib import Path

DEFAULT_DATABASE = Path(__file__).parent / 'data' / 'travel_planner.db'
FIELDS = ('title', 'destination', 'days', 'travelers', 'budget', 'plan')


def connect(path):
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def initialize(path=DEFAULT_DATABASE):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with closing(connect(path)) as connection, connection:
        connection.execute('''CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL, destination TEXT NOT NULL,
            days INTEGER NOT NULL CHECK(days BETWEEN 1 AND 365),
            travelers INTEGER NOT NULL CHECK(travelers BETWEEN 1 AND 100),
            budget INTEGER NOT NULL CHECK(budget >= 0), plan TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
        )''')
        connection.execute('''CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY, email TEXT NOT NULL UNIQUE,
            salt TEXT NOT NULL, password_hash TEXT NOT NULL)''')
        columns = {row['name'] for row in connection.execute('PRAGMA table_info(trips)')}
        if 'owner_id' not in columns:
            connection.execute('ALTER TABLE trips ADD COLUMN owner_id TEXT REFERENCES users(id)')
        connection.execute('CREATE INDEX IF NOT EXISTS trips_owner ON trips(owner_id)')


def list_trips(path, owner_id):
    with closing(connect(path)) as connection:
        return [dict(row) for row in connection.execute(
            'SELECT * FROM trips WHERE owner_id=? ORDER BY updated_at DESC, id DESC', (owner_id,))]


def get_trip(path, trip_id, owner_id):
    with closing(connect(path)) as connection:
        row = connection.execute('SELECT * FROM trips WHERE id = ? AND owner_id = ?', (trip_id, owner_id)).fetchone()
        return dict(row) if row else None


def save_trip(path, values, owner_id, trip_id=None):
    with closing(connect(path)) as connection, connection:
        parameters = tuple(values[field] for field in FIELDS)
        if trip_id is None:
            cursor = connection.execute(
                'INSERT INTO trips (title,destination,days,travelers,budget,plan,owner_id) VALUES (?,?,?,?,?,?,?)',
                parameters + (owner_id,))
            trip_id = cursor.lastrowid
        else:
            cursor = connection.execute('''UPDATE trips SET title=?, destination=?, days=?,
                travelers=?, budget=?, plan=?, updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')
                WHERE id=? AND owner_id=?''', parameters + (trip_id, owner_id))
            if cursor.rowcount == 0:
                return None
        return dict(connection.execute('SELECT * FROM trips WHERE id=?', (trip_id,)).fetchone())


def delete_trip(path, trip_id, owner_id):
    with closing(connect(path)) as connection, connection:
        return connection.execute('DELETE FROM trips WHERE id=? AND owner_id=?', (trip_id, owner_id)).rowcount > 0

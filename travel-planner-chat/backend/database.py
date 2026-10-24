"""SQLite storage for the single-user classroom app."""
from contextlib import closing
from pathlib import Path
import sqlite3

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


def list_trips(path):
    with closing(connect(path)) as connection:
        return [dict(row) for row in connection.execute(
            'SELECT * FROM trips ORDER BY updated_at DESC, id DESC')]


def get_trip(path, trip_id):
    with closing(connect(path)) as connection:
        row = connection.execute('SELECT * FROM trips WHERE id = ?', (trip_id,)).fetchone()
        return dict(row) if row else None


def save_trip(path, values, trip_id=None):
    with closing(connect(path)) as connection, connection:
        parameters = tuple(values[field] for field in FIELDS)
        if trip_id is None:
            cursor = connection.execute(
                'INSERT INTO trips (title,destination,days,travelers,budget,plan) VALUES (?,?,?,?,?,?)',
                parameters)
            trip_id = cursor.lastrowid
        else:
            cursor = connection.execute('''UPDATE trips SET title=?, destination=?, days=?,
                travelers=?, budget=?, plan=?, updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')
                WHERE id=?''', parameters + (trip_id,))
            if cursor.rowcount == 0:
                return None
        return dict(connection.execute('SELECT * FROM trips WHERE id=?', (trip_id,)).fetchone())


def delete_trip(path, trip_id):
    with closing(connect(path)) as connection, connection:
        return connection.execute('DELETE FROM trips WHERE id=?', (trip_id,)).rowcount > 0

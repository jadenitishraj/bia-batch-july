import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import database
from tokens import signing_key


class AuthStorageTests(unittest.TestCase):
    def test_migration_preserves_existing_unowned_trips_without_claiming_them(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'trips.db'
            with sqlite3.connect(path) as connection:
                connection.execute('''CREATE TABLE trips (id INTEGER PRIMARY KEY, title TEXT,
                    destination TEXT, days INTEGER, travelers INTEGER, budget INTEGER,
                    plan TEXT, updated_at TEXT)''')
                connection.execute("INSERT INTO trips VALUES (1,'Legacy','City',1,1,0,'Plan','now')")
            database.initialize(path)
            database.initialize(path)
            self.assertEqual(database.list_trips(path, 'new-user'), [])
            with sqlite3.connect(path) as connection:
                self.assertEqual(connection.execute('SELECT title,owner_id FROM trips').fetchone(),
                                 ('Legacy', None))

    def test_signing_key_persists_and_rejects_invalid_configuration(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            path = Path(directory) / 'test.db'
            key = signing_key(path)
            self.assertEqual(key, signing_key(path))
            self.assertEqual(path.with_suffix('.jwt-key').stat().st_mode & 0o777, 0o600)
            path.with_suffix('.jwt-key').write_text('short')
            with self.assertRaises(ValueError):
                signing_key(path)
            with patch.dict(os.environ, {'JWT_SECRET': 'a' * 32}):
                self.assertEqual(signing_key(path), 'a' * 32)
            with patch.dict(os.environ, {'JWT_SECRET': 'short'}):
                with self.assertRaises(ValueError):
                    signing_key(path)

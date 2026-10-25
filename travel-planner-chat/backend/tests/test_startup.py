import argparse
import runpy
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class StartupTests(unittest.TestCase):
    def test_cli_initializes_sqlite_and_closes_on_keyboard_interrupt(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / 'demo.db'
            options = argparse.Namespace(port=0, database=database)
            # Use a real server/socket/database, but simulate Ctrl+C rather than blocking.
            with patch('argparse.ArgumentParser.parse_args', return_value=options), patch(
                'http.server.ThreadingHTTPServer.serve_forever', side_effect=KeyboardInterrupt
            ) as serve:
                state = runpy.run_path(str(ROOT / 'app.py'), run_name='__main__')
            serve.assert_called_once()
            self.assertEqual(state['server'].socket.fileno(), -1)
            with sqlite3.connect(database) as connection:
                tables = connection.execute("SELECT name FROM sqlite_master WHERE name='trips'").fetchone()
                self.assertEqual(tables, ('trips',))

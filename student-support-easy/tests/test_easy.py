"""Small tests with fake Google calls. These never send real email."""
import asyncio
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, Mock
from backend import database, workflow, gmail, calendar, live


class EasyTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.path = patch.object(database, "DATABASE", Path(self.folder.name) / "test.sqlite3")
        self.path.start()
        database.setup()
        self.email = {"id": "email-one", "subject": "BIA Python help", "sender": "student@example.test",
                      "parent": "<original@example.test>", "thread": "thread-one", "received_at": 100}

    def tearDown(self):
        self.path.stop()
        self.folder.cleanup()

    def test_sqlite_remembers_one_request_and_cutoff_after_restart(self):
        cutoff = database.first_start()
        database.remember(self.email)
        database.remember(self.email)
        database.setup()
        self.assertEqual(database.first_start(), cutoff)
        self.assertEqual(len(database.snapshot()["requests"]), 1)

    def test_workflow_saves_before_publishing_and_does_not_repeat(self):
        saved_states = []
        async def broadcast():
            saved_states.append(database.request("email-one")["status"])
        event = {"start": {"dateTime": "2026-11-23T16:00:00+05:30"}}
        with patch.object(calendar, "find_or_create", return_value=event) as book, \
             patch.object(live, "broadcast", side_effect=broadcast), \
             patch.object(gmail, "send_confirmation") as send:
            asyncio.run(workflow.handle(self.email, object(), object()))
            asyncio.run(workflow.handle(self.email, object(), object()))
        self.assertEqual(saved_states, ["received", "scheduled", "done"])
        self.assertEqual(book.call_count, 1)
        self.assertEqual(send.call_count, 1)
        self.assertIn("04:00 PM IST", database.request("email-one")["meeting_time"])

    def test_uncertain_send_stops_instead_of_sending_twice(self):
        async def broadcast(): pass
        event = {"start": {"dateTime": "2026-11-23T16:00:00+05:30"}}
        with patch.object(calendar, "find_or_create", return_value=event), \
             patch.object(live, "broadcast", side_effect=broadcast), \
             patch.object(gmail, "send_confirmation", side_effect=TimeoutError()) as send:
            asyncio.run(workflow.handle(self.email, object(), object()))
            asyncio.run(workflow.handle(self.email, object(), object()))
        self.assertEqual(database.request("email-one")["status"], "needs review")
        self.assertEqual(send.call_count, 1)

    def test_restart_leaves_an_interrupted_request_for_manual_inspection(self):
        database.remember(self.email)
        database.save_status("email-one", "scheduled", "Saved meeting time")
        with patch.object(calendar, "find_or_create") as book, \
             patch.object(gmail, "send_confirmation") as send:
            asyncio.run(workflow.handle(self.email, object(), object()))
        self.assertEqual(database.request("email-one")["status"], "scheduled")
        book.assert_not_called()
        send.assert_not_called()

    def test_calendar_avoids_busy_time_and_respects_business_hours(self):
        client = Mock()
        client.freebusy().query().execute.return_value = {"calendars": {"primary": {"busy": [
            {"start": "2026-11-22T09:00:00+05:30", "end": "2026-11-22T11:00:00+05:30"}
        ]}}}
        start, end = calendar.next_free_time(client, datetime(2026, 11, 22, 9, 30, tzinfo=calendar.ZONE))
        self.assertEqual((start.hour, start.minute, end.minute), (11, 0, 30))
        start, end = calendar.next_free_time(client, datetime(2026, 11, 22, 16, 50, tzinfo=calendar.ZONE))
        self.assertEqual((start.day, start.hour, end.hour), (23, 9, 9))

    def test_gmail_matches_bia_without_label_and_ignores_automatic_or_old_mail(self):
        client = Mock()
        client.users().messages().list().execute.return_value = {"messages": [{"id": str(n)} for n in range(4)]}
        def message(number, subject, extra=None, received=200000):
            headers = [{"name": "Subject", "value": subject}, {"name": "From", "value": "student@example.test"},
                       {"name": "Message-ID", "value": "<original@example.test>"}]
            headers += extra or []
            return {"id": str(number), "threadId": "thread", "internalDate": str(received), "labelIds": ["INBOX"], "payload": {"headers": headers}}
        messages = [message(0, "bia help"), message(1, "Other lesson"),
                    message(2, "BIA automatic", [{"name": "X-BIA-Easy", "value": "yes"}]),
                    message(3, "BIA old", received=1000)]
        client.users().messages().get().execute.side_effect = messages
        self.assertEqual([email["id"] for email in gmail.new_emails(client, 100)], ["0"])


if __name__ == "__main__":
    unittest.main()

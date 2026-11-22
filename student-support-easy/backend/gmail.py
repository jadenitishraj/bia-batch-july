"""Read email headers. Send one short reply. Do not read message bodies."""
import base64
from email.message import EmailMessage
from email.utils import getaddresses
from backend.settings import SUBJECT_WORD


def new_emails(gmail, since):
    emails = []
    page = None
    while True:
        result = gmail.users().messages().list(userId="me", q=f"after:{int(since)} -in:spam -in:trash",
                                               pageToken=page, maxResults=100).execute()
        for item in result.get("messages", []):
            message = gmail.users().messages().get(userId="me", id=item["id"], format="metadata",
                metadataHeaders=["Subject", "From", "Message-ID", "Auto-Submitted", "X-BIA-Easy"]).execute()
            headers = {h["name"].lower(): h["value"] for h in message.get("payload", {}).get("headers", [])}
            subject = headers.get("subject", "")
            senders = getaddresses([headers.get("from", "")])
            sender = senders[0][1] if len(senders) == 1 else ""
            received = int(message.get("internalDate", 0)) / 1000
            # Ignore our own automatic reply and Calendar-generated messages.
            automatic = headers.get("x-bia-easy") or headers.get("auto-submitted", "no").lower() != "no"
            outgoing = "SENT" in message.get("labelIds", []) and "INBOX" not in message.get("labelIds", [])
            if automatic or outgoing or sender == "calendar-notification@google.com":
                continue
            if SUBJECT_WORD.lower() in subject.lower() and received >= since:
                emails.append({"id": item["id"], "subject": subject, "sender": sender,
                               "thread": message["threadId"], "parent": headers.get("message-id", ""),
                               "received_at": received})
        page = result.get("nextPageToken")
        if not page:
            return emails


def send_confirmation(gmail, email, meeting_time):
    message = EmailMessage()
    message["To"] = email["sender"]
    message["Subject"] = "Re: " + email["subject"]
    message["In-Reply-To"] = email["parent"]
    message["References"] = email["parent"]
    message["X-BIA-Easy"] = "yes"
    message["Auto-Submitted"] = "auto-replied"
    message.set_content(f"We received your BIA support request. Your 30-minute tutoring session is scheduled for {meeting_time}. A Calendar invitation has been requested for this address.\n\nBIA Classroom Support")
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    gmail.users().messages().send(userId="me", body={"threadId": email["thread"], "raw": raw}).execute()

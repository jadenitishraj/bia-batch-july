"""Change these few settings for your classroom."""
import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT = Path(__file__).resolve().parents[1]
REPOSITORY = PROJECT.parent
load_dotenv(PROJECT / ".env")
DATABASE = Path(os.getenv("EASY_DATABASE", PROJECT / ".local/easy.sqlite3"))
GOOGLE_TOKEN = Path(os.getenv("EASY_GOOGLE_TOKEN", REPOSITORY / "live-student-support-dashboard/.local/google-automation-token.json"))
GEMINI_ENV = Path(os.getenv("GEMINI_ENV_FILE", PROJECT / ".env"))
CALENDAR = "primary"
SUBJECT_WORD = "BIA"
POLL_SECONDS = 15
TIMEZONE = "Asia/Kolkata"

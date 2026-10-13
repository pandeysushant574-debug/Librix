"""Central configuration. Everything can be overridden with environment variables."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT / "frontend"
SCHEMA_FILE = ROOT / "database" / "schema.sql"
SEED_FILE = ROOT / "database" / "seed_data.json"

# The whole database is one file. Delete it (or run `python app.py --reset`) to start fresh.
DB_PATH = Path(os.environ.get("LIBRIX_DB", ROOT / "database" / "librix.db"))

HOST = os.environ.get("LIBRIX_HOST", "127.0.0.1")
PORT = int(os.environ.get("LIBRIX_PORT", "8000"))

SESSION_COOKIE = "LIBRIX_SESSION"
SESSION_TTL_SECONDS = 12 * 60 * 60  # 12 hours of inactivity

DEFAULT_PASSWORDS = {
    "admin": "Admin@123",
    "librarian": "Librarian@123",
    "assistant": "Assistant@123",
}

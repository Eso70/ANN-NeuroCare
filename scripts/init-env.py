"""Create local configuration with a hidden PostgreSQL password prompt; never overwrite."""
import getpass
import secrets
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / ".env"
if path.exists():
    raise SystemExit(".env already exists; preserved. Edit it manually if necessary.")
if not sys.stdin.isatty():
    raise SystemExit("Run in an interactive terminal to enter the existing postgres password securely.")
password = getpass.getpass("Existing PostgreSQL postgres password (hidden): ")
if not password:
    raise SystemExit("A postgres password is required. No file was created.")
quoted_password = "'" + password.replace("\\", "\\\\").replace("'", "\\'") + "'"
path.write_text(
    f"# Application\nAPP_ENV=development\nSECRET_KEY={secrets.token_hex(32)}\n"
    f"FRONTEND_URL=http://localhost:5173\n\n"
    f"# PostgreSQL: existing local service; postgres account selected for this workspace\n"
    f"DB_HOST=127.0.0.1\nDB_PORT=5432\nDB_NAME=neurocare_db\n"
    f"DB_USER=postgres\nDB_PASSWORD={quoted_password}\n\n"
    f"# Model: path relative to the project root or absolute; blank disables inference\nMODEL_DIR=\n",
    encoding="utf-8",
)
print("Created local .env. Keep it out of version control.")

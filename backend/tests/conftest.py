"""Ensure isolated unit-test config when no local development .env exists."""
import os
from pathlib import Path

if not (Path(__file__).resolve().parents[2] / ".env").exists():
    os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://unused:unused@localhost/unused")
    os.environ.setdefault("SECRET_KEY", "test-only-secret-key-at-least-32-characters")

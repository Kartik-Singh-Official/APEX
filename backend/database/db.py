"""Database Connection and Migration Management for APEX."""
import sqlite3
import aiosqlite
from typing import Optional
from backend.core.config import settings
from backend.database.schema import CREATE_TABLES_SQL


def init_db():
    """Synchronous database schema initialization."""
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(settings.db_path) as conn:
        conn.executescript(CREATE_TABLES_SQL)
        conn.commit()


async def get_db():
    """Async generator providing an aiosqlite connection."""
    async with aiosqlite.connect(settings.db_path) as db:
        db.row_factory = aiosqlite.Row
        yield db


def get_sync_db() -> sqlite3.Connection:
    """Synchronous SQLite connection helper."""
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    return conn

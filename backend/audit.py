"""SQLite-Audit-Log fuer GET/WALK/Portscan-Aufrufe."""

from datetime import datetime, timezone
from pathlib import Path

import aiosqlite

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "snmpweb.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    username TEXT NOT NULL,
    action TEXT NOT NULL,
    host TEXT,
    target TEXT,
    success INTEGER NOT NULL,
    detail TEXT
);
"""


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(_SCHEMA)
        await db.commit()


async def log_action(
    username: str, action: str, host: str, target: str, success: bool, detail: str = ""
) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO audit_log (ts, username, action, host, target, success, detail) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
                username,
                action,
                host,
                target,
                int(success),
                detail,
            ),
        )
        await db.commit()


async def recent(limit: int = 200) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT ts, username, action, host, target, success, detail "
            "FROM audit_log ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

"""Simple SQLite persistence so room messages survive a server restart."""

import aiosqlite
import os
from typing import List, Dict, Any

DB_PATH = os.path.join(os.path.dirname(__file__), "rooms.db")


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                user_name TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                reply_to_user_id TEXT,
                created_at REAL NOT NULL
            )
            """
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_messages_room ON messages(room_id, id)"
        )
        await db.commit()


async def save_message(
    room_id: str,
    user_id: str,
    user_name: str,
    role: str,
    content: str,
    created_at: float,
    reply_to_user_id: str | None = None,
) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO messages
            (room_id, user_id, user_name, role, content, reply_to_user_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (room_id, user_id, user_name, role, content, reply_to_user_id, created_at),
        )
        await db.commit()
        return cursor.lastrowid or 0


async def load_room_messages(room_id: str, limit: int = 200) -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT id, room_id, user_id, user_name, role, content,
                   reply_to_user_id, created_at
            FROM messages
            WHERE room_id = ?
            ORDER BY id ASC
            LIMIT ?
            """,
            (room_id, limit),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

"""SQLite storage for conversion history."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator

from config import settings


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS history (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   query TEXT NOT NULL,
                   display TEXT NOT NULL,
                   category TEXT NOT NULL,
                   created_at TEXT NOT NULL DEFAULT (datetime('now'))
               )"""
        )


def add_history(query: str, display: str, category: str) -> int:
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO history (query, display, category) VALUES (?, ?, ?)",
            (query, display, category),
        )
        return int(cur.lastrowid)


def list_history(limit: int) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, query, display, category, created_at FROM history "
            "ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def clear_history() -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM history")

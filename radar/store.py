"""SQLite persistence: what we have already shown, and run history."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .models import Signal, url_hash


class Store:
    def __init__(self, path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.execute(
            """CREATE TABLE IF NOT EXISTS seen (
                   id TEXT PRIMARY KEY,
                   url TEXT,
                   title TEXT,
                   source TEXT,
                   first_seen TEXT
               )"""
        )
        self.conn.execute(
            """CREATE TABLE IF NOT EXISTS runs (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   ran_at TEXT,
                   fetched INTEGER,
                   stories INTEGER,
                   top_score REAL
               )"""
        )
        self.conn.commit()

    def is_seen(self, signal: Signal) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM seen WHERE id = ?", (url_hash(signal.url),)
        ).fetchone()
        return row is not None

    def mark_seen(self, signal: Signal) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO seen (id, url, title, source, first_seen) VALUES (?,?,?,?,?)",
            (
                url_hash(signal.url),
                signal.url,
                signal.title[:500],
                signal.source,
                datetime.now(timezone.utc).isoformat(),
            ),
        )

    def log_run(self, fetched: int, stories: int, top_score: float) -> None:
        self.conn.execute(
            "INSERT INTO runs (ran_at, fetched, stories, top_score) VALUES (?,?,?,?)",
            (
                datetime.now(timezone.utc).isoformat(),
                fetched,
                stories,
                top_score,
            ),
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

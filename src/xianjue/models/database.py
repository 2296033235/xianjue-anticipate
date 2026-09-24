"""SQLite database layer for vocabulary, history, and SRS state."""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Optional

_DB_PATH = Path.home() / ".xianjue" / "data.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS vocabulary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT NOT NULL UNIQUE,
    lemma TEXT NOT NULL,
    definition TEXT DEFAULT '',
    context_sentence TEXT DEFAULT '',
    source TEXT DEFAULT 'manual',
    marked_at REAL NOT NULL,
    -- SM-2 state
    ease_factor REAL DEFAULT 2.5,
    interval_days INTEGER DEFAULT 0,
    repetitions INTEGER DEFAULT 0,
    next_review REAL DEFAULT 0,
    last_reviewed REAL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_text TEXT NOT NULL,
    target_text TEXT NOT NULL,
    source_lang TEXT NOT NULL,
    target_lang TEXT NOT NULL,
    engine TEXT NOT NULL,
    created_at REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_history_time ON history(created_at);
CREATE INDEX IF NOT EXISTS idx_vocab_next_review ON vocabulary(next_review);

CREATE TABLE IF NOT EXISTS settings_cache (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""


class Database:
    """Thread-safe SQLite wrapper for the app."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = db_path or _DB_PATH
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
        self._lock = __import__("threading").Lock()

    def _ensure_connection(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.executescript(_SCHEMA)
        return self._conn

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    # --- vocabulary -----------------------------------------------------------

    def add_word(self, word: str, lemma: str, context_sentence: str = "", source: str = "manual") -> bool:
        """Add a word. Returns True if added, False if already exists."""
        with self._lock:
            conn = self._ensure_connection()
            try:
                conn.execute(
                    "INSERT INTO vocabulary (word, lemma, context_sentence, source, marked_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (word.strip(), lemma.strip(), context_sentence, source, time.time()),
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def get_word(self, word: str) -> Optional[dict]:
        conn = self._ensure_connection()
        row = conn.execute(
            "SELECT * FROM vocabulary WHERE word = ? OR lemma = ?", (word, word)
        ).fetchone()
        if row is None:
            return None
        return self._row_to_dict(row)

    def get_all_words(self) -> list[dict]:
        conn = self._ensure_connection()
        rows = conn.execute(
            "SELECT * FROM vocabulary ORDER BY marked_at DESC"
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def delete_word(self, word: str) -> bool:
        conn = self._ensure_connection()
        cursor = conn.execute("DELETE FROM vocabulary WHERE word = ? OR lemma = ?", (word, word))
        conn.commit()
        return cursor.rowcount > 0

    def get_due_words(self, limit: int = 50) -> list[dict]:
        """Words due for review, ordered by priority (earliest next_review first)."""
        conn = self._ensure_connection()
        now = time.time()
        rows = conn.execute(
            "SELECT * FROM vocabulary WHERE next_review <= ? ORDER BY next_review ASC LIMIT ?",
            (now, limit),
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def count_due(self) -> int:
        conn = self._ensure_connection()
        now = time.time()
        row = conn.execute(
            "SELECT COUNT(*) FROM vocabulary WHERE next_review <= ?", (now,)
        ).fetchone()
        return row[0] if row else 0

    def count_total(self) -> int:
        conn = self._ensure_connection()
        row = conn.execute("SELECT COUNT(*) FROM vocabulary").fetchone()
        return row[0]

    # --- SM-2 -------------------------------------------------------------------

    def review_word(self, word: str, quality: int) -> dict:
        """Update SM-2 state after a review.

        Args:
            word: the word (matches word or lemma).
            quality: 0-5 (0=complete blackout, 5=perfect recall).

        Returns the updated word entry.
        """
        entry = self.get_word(word)
        if entry is None:
            raise ValueError(f"Word not found: {word}")

        ef = entry.get("ease_factor", 2.5)
        interval = entry.get("interval_days", 0)
        reps = entry.get("repetitions", 0)

        if quality < 3:
            reps = 0
            interval = 0
        else:
            reps += 1
            if reps == 1:
                interval = 1
            elif reps == 2:
                interval = 3
            else:
                interval = round(interval * ef)

        # SM-2 ease factor update.
        ef = ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        ef = max(1.3, ef)

        now = time.time()
        next_review = now + interval * 86400  # seconds

        conn = self._ensure_connection()
        conn.execute(
            "UPDATE vocabulary SET ease_factor=?, interval_days=?, repetitions=?, "
            "next_review=?, last_reviewed=? WHERE id=?",
            (ef, interval, reps, next_review, now, entry["id"]),
        )
        conn.commit()
        return self.get_word(word)

    # --- history ----------------------------------------------------------------

    def add_history(
        self, source: str, target: str, source_lang: str, target_lang: str, engine: str
    ) -> None:
        try:
            conn = self._ensure_connection()
            conn.execute(
                "INSERT INTO history (source_text, target_text, source_lang, target_lang, engine, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (source, target, source_lang, target_lang, engine, time.time()),
            )
            conn.commit()
            # Cap at 1000 entries.
            conn.execute(
                "DELETE FROM history WHERE id NOT IN "
                "(SELECT id FROM history ORDER BY created_at DESC LIMIT 1000)"
            )
            conn.commit()
        except Exception:
            pass

    def get_history(self, limit: int = 50) -> list[dict]:
        conn = self._ensure_connection()
        rows = conn.execute(
            "SELECT * FROM history ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(zip(
            ["id", "source_text", "target_text", "source_lang", "target_lang", "engine", "created_at"],
            row,
        )) for row in rows]

    # --- stats -------------------------------------------------------------------

    def get_streak(self) -> int:
        """Consecutive days with at least one translation."""
        conn = self._ensure_connection()
        today = time.time() // 86400
        rows = conn.execute(
            "SELECT DISTINCT CAST(created_at/86400 AS INTEGER) AS day FROM history ORDER BY day DESC LIMIT 30"
        ).fetchall()
        streak = 0
        for i, (day,) in enumerate(rows):
            if day == today - i:
                streak += 1
            else:
                break
        return streak

    # --- helpers ----------------------------------------------------------------

    @staticmethod
    def _row_to_dict(row) -> dict:
        return dict(zip(
            ["id", "word", "lemma", "definition", "context_sentence", "source",
             "marked_at", "ease_factor", "interval_days", "repetitions",
             "next_review", "last_reviewed"],
            row,
        ))

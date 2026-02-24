"""VOX Awareness Layer — SQLite-backed workspace context tracking.

Tracks page visits, errors, and session context so VOX knows what
the user is doing and can provide contextually relevant responses.
"""
import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Optional


DB_PATH = Path(__file__).parent.parent / "vox_awareness.db"


class VoxAwareness:
    """Workspace awareness service for VOX context injection."""

    def __init__(self, db_path: str = str(DB_PATH)):
        self.db_path = db_path
        self._init_db()
        self._session_start = time.time()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self):
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS page_visits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                page TEXT NOT NULL,
                timestamp REAL NOT NULL,
                duration REAL DEFAULT 0,
                metadata TEXT DEFAULT '{}'
            );
            CREATE TABLE IF NOT EXISTS error_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error_type TEXT NOT NULL,
                message TEXT NOT NULL,
                page TEXT DEFAULT '',
                timestamp REAL NOT NULL,
                resolved INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS session_context (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_page_visits_ts ON page_visits(timestamp);
            CREATE INDEX IF NOT EXISTS idx_error_log_ts ON error_log(timestamp);
        """)
        conn.commit()
        conn.close()

    def log_page_visit(self, page: str, metadata: Optional[dict] = None) -> int:
        """Track a page navigation event. Returns visit ID."""
        conn = self._get_conn()
        now = time.time()

        # Update duration of previous visit
        prev = conn.execute(
            "SELECT id, timestamp FROM page_visits ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if prev:
            conn.execute(
                "UPDATE page_visits SET duration = ? WHERE id = ?",
                (now - prev["timestamp"], prev["id"]),
            )

        cursor = conn.execute(
            "INSERT INTO page_visits (page, timestamp, metadata) VALUES (?, ?, ?)",
            (page, now, json.dumps(metadata or {})),
        )
        conn.commit()
        visit_id = cursor.lastrowid
        conn.close()
        return visit_id

    def log_error(self, error_type: str, message: str, page: str = "") -> int:
        """Track a workspace error. Returns error ID."""
        conn = self._get_conn()
        cursor = conn.execute(
            "INSERT INTO error_log (error_type, message, page, timestamp) VALUES (?, ?, ?, ?)",
            (error_type, message, page, time.time()),
        )
        conn.commit()
        error_id = cursor.lastrowid
        conn.close()
        return error_id

    def resolve_error(self, error_id: int):
        """Mark an error as resolved."""
        conn = self._get_conn()
        conn.execute("UPDATE error_log SET resolved = 1 WHERE id = ?", (error_id,))
        conn.commit()
        conn.close()

    def set_context(self, key: str, value: Any):
        """Store arbitrary session context."""
        conn = self._get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO session_context (key, value, updated_at) VALUES (?, ?, ?)",
            (key, json.dumps(value) if not isinstance(value, str) else value, time.time()),
        )
        conn.commit()
        conn.close()

    def get_context(self, key: str) -> Optional[str]:
        """Retrieve a context value."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT value FROM session_context WHERE key = ?", (key,)
        ).fetchone()
        conn.close()
        return row["value"] if row else None

    def get_recent_pages(self, limit: int = 5) -> list[dict]:
        """Get recent page visits."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT page, timestamp, duration FROM page_visits ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_unresolved_errors(self, limit: int = 3) -> list[dict]:
        """Get recent unresolved errors."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT id, error_type, message, page, timestamp FROM error_log "
            "WHERE resolved = 0 ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_page_stats(self) -> dict[str, int]:
        """Get page visit frequency for guided tours."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT page, COUNT(*) as visits FROM page_visits GROUP BY page ORDER BY visits DESC"
        ).fetchall()
        conn.close()
        return {r["page"]: r["visits"] for r in rows}

    def build_awareness_prompt(self) -> str:
        """Generate context injection string for VOX system prompt."""
        parts = []

        # Current page
        recent = self.get_recent_pages(1)
        if recent:
            current = recent[0]
            duration = current.get("duration", 0)
            if duration == 0:
                duration = time.time() - current["timestamp"]
            parts.append(f"Current page: {current['page']} (on page for {int(duration)}s)")

        # Recent page history
        history = self.get_recent_pages(5)
        if len(history) > 1:
            pages = [h["page"] for h in history[1:]]
            parts.append(f"Recent pages: {' -> '.join(reversed(pages))}")

        # Unresolved errors
        errors = self.get_unresolved_errors(3)
        if errors:
            error_strs = [f"[{e['error_type']}] {e['message'][:80]}" for e in errors]
            parts.append(f"Recent errors ({len(errors)} unresolved): " + "; ".join(error_strs))

        # Active project context
        active_project = self.get_context("active_project")
        if active_project:
            parts.append(f"Active project: {active_project}")

        active_kg = self.get_context("active_kg")
        if active_kg:
            parts.append(f"Active KG: {active_kg}")

        # Session stats
        session_duration = int(time.time() - self._session_start)
        parts.append(f"Session duration: {session_duration // 60}m {session_duration % 60}s")

        # Page visit stats
        stats = self.get_page_stats()
        if stats:
            top3 = list(stats.items())[:3]
            parts.append(f"Most visited: {', '.join(f'{p}({c})' for p, c in top3)}")

        return "\n".join(parts) if parts else "No context available yet."

    def cleanup_old_data(self, max_age_hours: int = 24):
        """Remove data older than max_age_hours."""
        cutoff = time.time() - (max_age_hours * 3600)
        conn = self._get_conn()
        conn.execute("DELETE FROM page_visits WHERE timestamp < ?", (cutoff,))
        conn.execute("DELETE FROM error_log WHERE timestamp < ?", (cutoff,))
        conn.commit()
        conn.close()


# Singleton
vox_awareness = VoxAwareness()

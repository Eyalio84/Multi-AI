"""Workflow persistence — SQLite-backed CRUD for saved workflows."""
import sqlite3
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "workflows.db"


def _get_conn() -> sqlite3.Connection:
    """Return a connection with row_factory set to sqlite3.Row."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _row_to_dict(row: sqlite3.Row | None) -> dict | None:
    """Convert a sqlite3.Row to a plain dict, parsing the steps JSON column."""
    if row is None:
        return None
    d = dict(row)
    if "steps" in d and isinstance(d["steps"], str):
        try:
            d["steps"] = json.loads(d["steps"])
        except (json.JSONDecodeError, TypeError):
            pass
    return d


def init_db():
    """Create the workflows table if it does not exist."""
    conn = _get_conn()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS workflows (
                id          TEXT PRIMARY KEY,
                name        TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                goal        TEXT NOT NULL DEFAULT '',
                steps       TEXT NOT NULL DEFAULT '[]',
                created_at  TEXT NOT NULL,
                updated_at  TEXT NOT NULL
            )
        """)
        conn.commit()
    finally:
        conn.close()


init_db()


def create_workflow(name: str, description: str, goal: str, steps: list[dict]) -> dict:
    """Create a new saved workflow and return it."""
    workflow_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    conn = _get_conn()
    try:
        conn.execute(
            "INSERT INTO workflows (id, name, description, goal, steps, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (workflow_id, name, description, goal, json.dumps(steps), now, now),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM workflows WHERE id = ?", (workflow_id,)).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


def list_workflows() -> list[dict]:
    """Return all saved workflows ordered by creation date descending."""
    conn = _get_conn()
    try:
        rows = conn.execute("SELECT * FROM workflows ORDER BY created_at DESC").fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()


def get_workflow(workflow_id: str) -> dict | None:
    """Return a single workflow by ID, or None if not found."""
    conn = _get_conn()
    try:
        row = conn.execute("SELECT * FROM workflows WHERE id = ?", (workflow_id,)).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


def update_workflow(workflow_id: str, data: dict) -> dict | None:
    """Update a workflow's fields. Returns the updated workflow or None."""
    conn = _get_conn()
    try:
        existing = conn.execute("SELECT * FROM workflows WHERE id = ?", (workflow_id,)).fetchone()
        if existing is None:
            return None

        now = datetime.now(timezone.utc).isoformat()
        name = data.get("name", existing["name"])
        description = data.get("description", existing["description"])
        goal = data.get("goal", existing["goal"])
        steps = data.get("steps")
        steps_json = json.dumps(steps) if steps is not None else existing["steps"]

        conn.execute(
            "UPDATE workflows SET name = ?, description = ?, goal = ?, steps = ?, updated_at = ? WHERE id = ?",
            (name, description, goal, steps_json, now, workflow_id),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM workflows WHERE id = ?", (workflow_id,)).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


def delete_workflow(workflow_id: str) -> bool:
    """Delete a workflow by ID. Returns True if a row was deleted."""
    conn = _get_conn()
    try:
        cursor = conn.execute("DELETE FROM workflows WHERE id = ?", (workflow_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()

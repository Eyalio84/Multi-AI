"""Studio project persistence — SQLite-backed CRUD for projects and versions."""
import sqlite3
import json
import uuid
import io
import zipfile
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "studio_projects.db"


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def _get_conn() -> sqlite3.Connection:
    """Return a connection with row_factory set to sqlite3.Row."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


_JSON_COLUMNS = {"settings", "files", "chat_history"}

def _row_to_dict(row: sqlite3.Row | None) -> dict | None:
    """Convert a sqlite3.Row to a plain dict, parsing JSON columns."""
    if row is None:
        return None
    d = dict(row)
    for col in _JSON_COLUMNS:
        if col in d and isinstance(d[col], str):
            try:
                d[col] = json.loads(d[col])
            except (json.JSONDecodeError, TypeError):
                pass
    return d


def init_db():
    """Create tables if they do not exist."""
    conn = _get_conn()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS studio_projects (
                id              TEXT PRIMARY KEY,
                name            TEXT NOT NULL DEFAULT 'Untitled Project',
                description     TEXT NOT NULL DEFAULT '',
                settings        TEXT NOT NULL DEFAULT '{}',
                files           TEXT NOT NULL DEFAULT '{}',
                chat_history    TEXT NOT NULL DEFAULT '[]',
                current_version INTEGER NOT NULL DEFAULT 0,
                created_at      TEXT NOT NULL,
                updated_at      TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS studio_versions (
                id              TEXT PRIMARY KEY,
                project_id      TEXT NOT NULL,
                version_number  INTEGER NOT NULL,
                files           TEXT NOT NULL DEFAULT '{}',
                message         TEXT NOT NULL DEFAULT '',
                timestamp       TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES studio_projects(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_versions_project
                ON studio_versions(project_id, version_number);
        """)
        conn.commit()
    finally:
        conn.close()


# Auto-initialize on import
init_db()


# ---------------------------------------------------------------------------
# Project CRUD
# ---------------------------------------------------------------------------

def create_project(name: str, description: str = "") -> dict:
    """Create a new Studio project and return it as a dict."""
    project_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    conn = _get_conn()
    try:
        conn.execute(
            """INSERT INTO studio_projects
               (id, name, description, settings, files, chat_history, current_version, created_at, updated_at)
               VALUES (?, ?, ?, '{}', '{}', '[]', 0, ?, ?)""",
            (project_id, name, description, now, now),
        )
        conn.commit()
        return {
            "id": project_id,
            "name": name,
            "description": description,
            "settings": {},
            "files": {},
            "chat_history": [],
            "current_version": 0,
            "created_at": now,
            "updated_at": now,
        }
    finally:
        conn.close()


def list_projects() -> list[dict]:
    """Return a list of project summaries (without full file contents)."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            """SELECT id, name, description, current_version, created_at, updated_at
               FROM studio_projects
               ORDER BY updated_at DESC"""
        ).fetchall()
        results = []
        for row in rows:
            d = dict(row)
            # Add a file count for the summary
            full = conn.execute(
                "SELECT files FROM studio_projects WHERE id = ?", (d["id"],)
            ).fetchone()
            if full:
                try:
                    d["file_count"] = len(json.loads(full["files"] or "{}"))
                except (json.JSONDecodeError, TypeError):
                    d["file_count"] = 0
            else:
                d["file_count"] = 0
            results.append(d)
        return results
    finally:
        conn.close()


def get_project(project_id: str) -> dict | None:
    """Return the full project row as a dict, or None if not found."""
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM studio_projects WHERE id = ?", (project_id,)
        ).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


def update_project(project_id: str, data: dict) -> bool:
    """Update specified fields on a project. Returns True if a row was updated."""
    if not data:
        return False

    allowed_fields = {"name", "description", "settings", "files", "chat_history", "current_version"}
    updates = {k: v for k, v in data.items() if k in allowed_fields}
    if not updates:
        return False

    # JSON-serialize dict/list values for SQLite TEXT columns
    json_fields = {"settings", "files", "chat_history"}
    for k in updates:
        if k in json_fields and isinstance(updates[k], (dict, list)):
            updates[k] = json.dumps(updates[k])

    updates["updated_at"] = datetime.now(timezone.utc).isoformat()

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [project_id]

    conn = _get_conn()
    try:
        cursor = conn.execute(
            f"UPDATE studio_projects SET {set_clause} WHERE id = ?",
            values,
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def delete_project(project_id: str) -> bool:
    """Delete a project and its versions. Returns True if deleted."""
    conn = _get_conn()
    try:
        # Versions are cascade-deleted via FK, but be explicit just in case
        conn.execute("DELETE FROM studio_versions WHERE project_id = ?", (project_id,))
        cursor = conn.execute("DELETE FROM studio_projects WHERE id = ?", (project_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Version management
# ---------------------------------------------------------------------------

def save_version(project_id: str, message: str = "Manual save") -> dict:
    """Snapshot the current project files as a new version."""
    conn = _get_conn()
    try:
        project = conn.execute(
            "SELECT files, current_version FROM studio_projects WHERE id = ?",
            (project_id,),
        ).fetchone()
        if project is None:
            raise ValueError(f"Project {project_id} not found")

        new_version = project["current_version"] + 1
        version_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        conn.execute(
            """INSERT INTO studio_versions
               (id, project_id, version_number, files, message, timestamp)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (version_id, project_id, new_version, project["files"], message, now),
        )
        conn.execute(
            "UPDATE studio_projects SET current_version = ?, updated_at = ? WHERE id = ?",
            (new_version, now, project_id),
        )
        conn.commit()
        return {
            "id": version_id,
            "project_id": project_id,
            "version_number": new_version,
            "message": message,
            "timestamp": now,
        }
    finally:
        conn.close()


def list_versions(project_id: str) -> list[dict]:
    """List all versions for a project, ordered newest first."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            """SELECT id, project_id, version_number, message, timestamp
               FROM studio_versions
               WHERE project_id = ?
               ORDER BY version_number DESC""",
            (project_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_version(project_id: str, version_number: int) -> dict | None:
    """Get a specific version snapshot."""
    conn = _get_conn()
    try:
        row = conn.execute(
            """SELECT * FROM studio_versions
               WHERE project_id = ? AND version_number = ?""",
            (project_id, version_number),
        ).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


def restore_version(project_id: str, version_number: int) -> bool:
    """Restore project files from a version snapshot.

    This copies the version's files back to the project's current files
    and bumps current_version.
    """
    conn = _get_conn()
    try:
        version = conn.execute(
            """SELECT files FROM studio_versions
               WHERE project_id = ? AND version_number = ?""",
            (project_id, version_number),
        ).fetchone()
        if version is None:
            raise ValueError(f"Version {version_number} not found for project {project_id}")

        now = datetime.now(timezone.utc).isoformat()

        # Save current state as a new version before restoring
        project = conn.execute(
            "SELECT files, current_version FROM studio_projects WHERE id = ?",
            (project_id,),
        ).fetchone()
        if project is None:
            raise ValueError(f"Project {project_id} not found")

        pre_restore_version = project["current_version"] + 1
        pre_restore_id = str(uuid.uuid4())
        conn.execute(
            """INSERT INTO studio_versions
               (id, project_id, version_number, files, message, timestamp)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (pre_restore_id, project_id, pre_restore_version,
             project["files"], f"Auto-save before restoring v{version_number}", now),
        )

        # Now restore
        new_version = pre_restore_version + 1
        conn.execute(
            """UPDATE studio_projects
               SET files = ?, current_version = ?, updated_at = ?
               WHERE id = ?""",
            (version["files"], new_version, now, project_id),
        )
        conn.commit()
    finally:
        conn.close()

    # Return the updated project
    return get_project(project_id)


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def export_project_zip(project_id: str, scope: str = "all") -> bytes | None:
    """Generate a ZIP archive of project files. Returns bytes or None."""
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT name, files FROM studio_projects WHERE id = ?",
            (project_id,),
        ).fetchone()
        if row is None:
            return None

        files = json.loads(row["files"] or "{}")
        project_name = row["name"].replace(" ", "-").lower()

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for path, file_data in files.items():
                # file_data can be a string or a dict {path, content, language}
                content = file_data["content"] if isinstance(file_data, dict) else file_data
                # Normalise path: strip leading slash
                clean_path = path.lstrip("/")

                # Scope filtering
                if scope == "frontend":
                    # Only include src/, public/, package.json, index.html, etc.
                    frontend_prefixes = (
                        "src/", "public/", "App", "index", "package",
                        "components/", "hooks/", "utils/", "styles/",
                    )
                    if not any(clean_path.startswith(p) or clean_path == p for p in frontend_prefixes):
                        # Also include root-level JS/JSX/TS/TSX files
                        if not clean_path.endswith((".js", ".jsx", ".ts", ".tsx", ".json", ".html", ".css")):
                            continue
                elif scope == "backend":
                    backend_prefixes = ("api/", "server/", "backend/", "routes/", "models/", "services/")
                    if not any(clean_path.startswith(p) for p in backend_prefixes):
                        if not clean_path.endswith(".py"):
                            continue

                archive_path = f"{project_name}/{clean_path}"
                zf.writestr(archive_path, content)

            # Add a basic package.json if not present
            if "package.json" not in files and "/package.json" not in files:
                pkg = {
                    "name": project_name,
                    "version": "0.1.0",
                    "private": True,
                    "dependencies": {
                        "react": "^18.2.0",
                        "react-dom": "^18.2.0",
                    },
                }
                zf.writestr(f"{project_name}/package.json", json.dumps(pkg, indent=2))

        return buf.getvalue()
    finally:
        conn.close()

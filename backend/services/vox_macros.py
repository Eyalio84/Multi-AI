"""VOX Voice Macros — user-definable multi-step command sequences with pipe chaining.

Macros let users create reusable voice-triggered workflows that chain
multiple VOX functions together, with optional output piping between steps.
"""
import json
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Optional


from services.vox_service import build_function_declarations

DB_PATH = Path(__file__).parent.parent / "vox_macros.db"

# Build a lookup of function declarations keyed by name
_FUNCTION_DECLS: dict[str, dict] = {}


def _get_function_decls() -> dict[str, dict]:
    """Lazy-load function declarations into a name-keyed lookup."""
    if not _FUNCTION_DECLS:
        for fn in build_function_declarations():
            _FUNCTION_DECLS[fn["name"]] = fn
    return _FUNCTION_DECLS


def _validate_step_args(function_name: str, args: dict) -> tuple[bool, str | None]:
    """Validate that required parameters are present for a VOX function.

    Returns:
        (valid, error) — True/None if valid, False/message if not.
    """
    decls = _get_function_decls()
    decl = decls.get(function_name)
    if not decl:
        return False, f"Unknown function: {function_name}"

    params_schema = decl.get("parameters", {})
    required = params_schema.get("required", [])
    missing = [r for r in required if r not in args]
    if missing:
        return False, f"Missing required args for {function_name}: {', '.join(missing)}"

    return True, None


class VoxMacroService:
    """SQLite-backed macro system for VOX voice commands."""

    def __init__(self, db_path: str = str(DB_PATH)):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self):
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS macros (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                trigger_phrase TEXT NOT NULL,
                steps TEXT NOT NULL,
                error_policy TEXT DEFAULT 'abort',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_macros_trigger
            ON macros(trigger_phrase)
        """)
        conn.commit()
        conn.close()

    def create_macro(
        self,
        name: str,
        trigger_phrase: str,
        steps: list[dict],
        error_policy: str = "abort",
    ) -> dict:
        """Create a new voice macro.

        Args:
            name: Human-readable macro name
            trigger_phrase: Voice trigger, e.g. "morning routine"
            steps: List of {function, args, pipe_from?} dicts
            error_policy: "abort" | "skip" | "retry"

        Returns:
            Created macro dict
        """
        macro_id = str(uuid.uuid4())[:8]
        now = time.time()
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO macros (id, name, trigger_phrase, steps, error_policy, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (macro_id, name, trigger_phrase.lower(), json.dumps(steps), error_policy, now, now),
        )
        conn.commit()
        conn.close()
        return {
            "id": macro_id,
            "name": name,
            "trigger_phrase": trigger_phrase.lower(),
            "steps": steps,
            "error_policy": error_policy,
            "created_at": now,
            "updated_at": now,
        }

    def list_macros(self) -> list[dict]:
        """List all saved macros."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT id, name, trigger_phrase, steps, error_policy, created_at, updated_at "
            "FROM macros ORDER BY updated_at DESC"
        ).fetchall()
        conn.close()
        return [
            {
                "id": r["id"],
                "name": r["name"],
                "trigger_phrase": r["trigger_phrase"],
                "steps": json.loads(r["steps"]),
                "error_policy": r["error_policy"],
                "step_count": len(json.loads(r["steps"])),
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            }
            for r in rows
        ]

    def get_macro(self, macro_id: str) -> Optional[dict]:
        """Get a macro by ID."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT id, name, trigger_phrase, steps, error_policy, created_at, updated_at "
            "FROM macros WHERE id = ?",
            (macro_id,),
        ).fetchone()
        conn.close()
        if not row:
            return None
        return {
            "id": row["id"],
            "name": row["name"],
            "trigger_phrase": row["trigger_phrase"],
            "steps": json.loads(row["steps"]),
            "error_policy": row["error_policy"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def find_by_trigger(self, phrase: str) -> Optional[dict]:
        """Find a macro by trigger phrase (fuzzy match)."""
        conn = self._get_conn()
        # Exact match first
        row = conn.execute(
            "SELECT id, name, trigger_phrase, steps, error_policy, created_at, updated_at "
            "FROM macros WHERE trigger_phrase = ?",
            (phrase.lower(),),
        ).fetchone()
        if not row:
            # Partial match
            row = conn.execute(
                "SELECT id, name, trigger_phrase, steps, error_policy, created_at, updated_at "
                "FROM macros WHERE trigger_phrase LIKE ? OR name LIKE ?",
                (f"%{phrase.lower()}%", f"%{phrase.lower()}%"),
            ).fetchone()
        conn.close()
        if not row:
            return None
        return {
            "id": row["id"],
            "name": row["name"],
            "trigger_phrase": row["trigger_phrase"],
            "steps": json.loads(row["steps"]),
            "error_policy": row["error_policy"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def update_macro(self, macro_id: str, **kwargs) -> Optional[dict]:
        """Update a macro's fields."""
        macro = self.get_macro(macro_id)
        if not macro:
            return None

        conn = self._get_conn()
        updates = []
        params = []
        for key in ("name", "trigger_phrase", "error_policy"):
            if key in kwargs:
                updates.append(f"{key} = ?")
                val = kwargs[key].lower() if key == "trigger_phrase" else kwargs[key]
                params.append(val)
        if "steps" in kwargs:
            updates.append("steps = ?")
            params.append(json.dumps(kwargs["steps"]))

        if updates:
            updates.append("updated_at = ?")
            params.append(time.time())
            params.append(macro_id)
            conn.execute(
                f"UPDATE macros SET {', '.join(updates)} WHERE id = ?",
                params,
            )
            conn.commit()

        conn.close()
        return self.get_macro(macro_id)

    def delete_macro(self, macro_id: str) -> bool:
        """Delete a macro by ID."""
        conn = self._get_conn()
        cursor = conn.execute("DELETE FROM macros WHERE id = ?", (macro_id,))
        conn.commit()
        conn.close()
        return cursor.rowcount > 0

    async def execute_macro(
        self,
        macro_id: str,
        execute_fn: Callable,
    ) -> list[dict]:
        """Execute a macro's steps sequentially with pipe chaining.

        Args:
            macro_id: Macro ID or trigger phrase to execute
            execute_fn: async function(name, args) -> dict that executes a single function

        Returns:
            List of step results
        """
        macro = self.get_macro(macro_id)
        if not macro:
            macro = self.find_by_trigger(macro_id)
        if not macro:
            return [{"step": 0, "success": False, "error": f"Macro not found: {macro_id}"}]

        results = []
        error_policy = macro.get("error_policy", "abort")

        for i, step in enumerate(macro["steps"]):
            fn_name = step.get("function", "")
            fn_args = dict(step.get("args", {}))

            # Pipe chaining: inject output from a previous step
            pipe_from = step.get("pipe_from")
            if pipe_from is not None and isinstance(pipe_from, int):
                if 0 <= pipe_from < len(results) and results[pipe_from].get("success"):
                    prev_result = results[pipe_from].get("result", {})
                    # Auto-inject useful fields from previous result
                    if isinstance(prev_result, dict):
                        # Common patterns: database_id from list_kgs, tool_id from list_tools, etc.
                        if "databases" in prev_result and "database_id" not in fn_args:
                            dbs = prev_result["databases"]
                            if dbs:
                                fn_args["database_id"] = dbs[0].get("id", "")
                        elif "tools" in prev_result and "tool_id" not in fn_args:
                            tools = prev_result["tools"]
                            if tools:
                                fn_args["tool_id"] = tools[0].get("id", "")
                        elif "result" in prev_result:
                            fn_args["_piped_input"] = prev_result["result"]

            # Validate step arguments against function declaration
            valid, validation_error = _validate_step_args(fn_name, fn_args)
            if not valid:
                results.append({
                    "step": i,
                    "function": fn_name,
                    "success": False,
                    "error": validation_error,
                })
                if error_policy == "abort":
                    break
                continue

            try:
                result = await execute_fn(fn_name, fn_args)
                success = result.get("success", False) if isinstance(result, dict) else True
                results.append({
                    "step": i,
                    "function": fn_name,
                    "success": success,
                    "result": result,
                })

                if not success and error_policy == "abort":
                    results.append({
                        "step": i + 1,
                        "function": "macro_aborted",
                        "success": False,
                        "error": f"Step {i} ({fn_name}) failed, aborting macro",
                    })
                    break

            except Exception as e:
                results.append({
                    "step": i,
                    "function": fn_name,
                    "success": False,
                    "error": str(e),
                })
                if error_policy == "abort":
                    break

        return results


# Singleton
vox_macro_service = VoxMacroService()

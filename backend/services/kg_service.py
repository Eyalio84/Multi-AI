"""Knowledge Graph service — schema auto-detection, lazy connections, read/write ops."""
import sqlite3
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from config import KGS_DIR


# ── Schema profiles ────────────────────────────────────────────────
PROFILES = {
    "unified": {
        "node_table": "unified_nodes",
        "edge_table": "unified_edges",
        "node_id": "node_id",
        "node_name": "name",
        "node_type": "node_type",
        "edge_id": "edge_id",
        "edge_source": "source_node_id",
        "edge_target": "target_node_id",
        "edge_type": "edge_type",
    },
    "standard": {
        "node_table": "nodes",
        "edge_table": "edges",
        "node_id": "id",
        "node_name": "name",
        "node_type": "type",
        "edge_id": "id",
        "edge_source": "source",
        "edge_target": "target",
        "edge_type": "type",
    },
    "claude": {
        "node_table": "nodes",
        "edge_table": "edges",
        "node_id": "node_id",
        "node_name": "name",
        "node_type": "node_type",
        "edge_id": "edge_id",
        "edge_source": "source_node_id",
        "edge_target": "target_node_id",
        "edge_type": "edge_type",
    },
    "hal": {
        "node_table": "nodes",
        "edge_table": "edges",
        "node_id": "id",
        "node_name": "name",
        "node_type": "type",
        "edge_id": "id",
        "edge_source": "source_id",
        "edge_target": "target_id",
        "edge_type": "edge_type",
    },
    "from_node": {
        "node_table": "nodes",
        "edge_table": "edges",
        "node_id": "id",
        "node_name": "name",
        "node_type": "type",
        "edge_id": "id",
        "edge_source": "from_node",
        "edge_target": "to_node",
        "edge_type": "type",
    },
    "entities": {
        "node_table": "entities",
        "edge_table": "relations",
        "node_id": "id",
        "node_name": "name",
        "node_type": "type",
        "edge_id": "id",
        "edge_source": "source_id",
        "edge_target": "target_id",
        "edge_type": "relation_type",
    },
}

# Standard schema used for new databases
STANDARD_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS nodes (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL DEFAULT 'entity',
    properties TEXT DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS edges (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL REFERENCES nodes(id),
    target TEXT NOT NULL REFERENCES nodes(id),
    type TEXT NOT NULL DEFAULT 'relates_to',
    properties TEXT DEFAULT '{}',
    weight REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(type);
CREATE INDEX IF NOT EXISTS idx_nodes_name ON nodes(name);
CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source);
CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target);
CREATE INDEX IF NOT EXISTS idx_edges_type ON edges(type);
CREATE VIRTUAL TABLE IF NOT EXISTS nodes_fts USING fts5(
    name, type, properties, content=nodes, content_rowid=rowid
);
CREATE TRIGGER IF NOT EXISTS nodes_ai AFTER INSERT ON nodes BEGIN
    INSERT INTO nodes_fts(rowid, name, type, properties)
    VALUES (new.rowid, new.name, new.type, new.properties);
END;
CREATE TRIGGER IF NOT EXISTS nodes_ad AFTER DELETE ON nodes BEGIN
    INSERT INTO nodes_fts(nodes_fts, rowid, name, type, properties)
    VALUES ('delete', old.rowid, old.name, old.type, old.properties);
END;
CREATE TRIGGER IF NOT EXISTS nodes_au AFTER UPDATE ON nodes BEGIN
    INSERT INTO nodes_fts(nodes_fts, rowid, name, type, properties)
    VALUES ('delete', old.rowid, old.name, old.type, old.properties);
    INSERT INTO nodes_fts(rowid, name, type, properties)
    VALUES (new.rowid, new.name, new.type, new.properties);
END;
"""


class KGService:
    """Manages access to multiple SQLite-based knowledge graphs."""

    def __init__(self, kgs_dir: str | Path | None = None):
        self.kgs_dir = Path(kgs_dir) if kgs_dir else KGS_DIR
        self._connections: dict[str, sqlite3.Connection] = {}
        self._profiles: dict[str, dict] = {}

    def close_all(self):
        for conn in self._connections.values():
            conn.close()
        self._connections.clear()

    # ── Database discovery ──────────────────────────────────────────
    def list_databases(self) -> list[dict]:
        dbs = []
        if not self.kgs_dir.exists():
            return dbs
        for p in sorted(self.kgs_dir.rglob("*.db")):
            stat = p.stat()
            entry = {
                "id": p.stem,
                "filename": p.name,
                "path": str(p.relative_to(self.kgs_dir)),
                "size_bytes": stat.st_size,
                "size_mb": round(stat.st_size / 1_048_576, 2),
            }
            # Probe whether this is a valid KG database
            try:
                self._detect_profile(p.stem)
                entry["is_kg"] = True
            except (ValueError, Exception):
                entry["is_kg"] = False
            dbs.append(entry)
        return dbs

    # ── Connection management ───────────────────────────────────────
    def _get_conn(self, db_id: str) -> sqlite3.Connection:
        if db_id in self._connections:
            return self._connections[db_id]
        db_path = self._resolve_path(db_id)
        if not db_path:
            raise FileNotFoundError(f"Database not found: {db_id}")
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        self._connections[db_id] = conn
        return conn

    def _resolve_path(self, db_id: str) -> Path | None:
        # Try exact filename match first
        for p in self.kgs_dir.rglob("*.db"):
            if p.stem == db_id or p.name == db_id:
                return p
        return None

    # ── Schema auto-detection ───────────────────────────────────────
    def _detect_profile(self, db_id: str) -> dict:
        if db_id in self._profiles:
            return self._profiles[db_id]
        conn = self._get_conn(db_id)
        tables = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}

        # Try each known profile — verify both node and edge columns match
        for name, profile in PROFILES.items():
            if profile["node_table"] in tables:
                cols = {r[1] for r in conn.execute(
                    f"PRAGMA table_info({profile['node_table']})"
                ).fetchall()}
                if profile["node_id"] in cols and profile["node_name"] in cols:
                    if profile["edge_table"] in tables:
                        ecols = {r[1] for r in conn.execute(
                            f"PRAGMA table_info({profile['edge_table']})"
                        ).fetchall()}
                        if (profile["edge_source"] in ecols and
                                profile["edge_target"] in ecols and
                                profile["edge_type"] in ecols):
                            result = {**profile, "profile_name": name}
                            self._profiles[db_id] = result
                            return result

        # Heuristic fallback — find a suitable node table and probe edge columns
        skip = {"sqlite_", "_fts", "_config", "_content", "_data", "_idx", "_docsize"}
        for t in sorted(tables):
            if any(t.startswith(s) or t.endswith(s) for s in skip):
                continue
            cols = {r[1] for r in conn.execute(f"PRAGMA table_info({t})").fetchall()}
            id_col = next((c for c in ("id", "node_id", "entity_id") if c in cols), None)
            name_col = next((c for c in ("name", "node_name", "title") if c in cols), None)
            if not id_col or not name_col:
                continue
            type_col = next((c for c in ("type", "node_type", "entity_type", "category") if c in cols), None) or "type"
            # Find the edge table
            edge_table = None
            for et in ("edges", "relations", "links", "unified_edges"):
                if et in tables:
                    edge_table = et
                    break
            if not edge_table:
                edge_table = next((e for e in tables if "edge" in e.lower() or "relation" in e.lower() or "link" in e.lower()), None)
            edge_id = "id"
            edge_src = "source"
            edge_tgt = "target"
            edge_type = "type"
            if edge_table:
                ecols = {r[1] for r in conn.execute(f"PRAGMA table_info({edge_table})").fetchall()}
                edge_id = next((c for c in ("edge_id", "id", "rowid") if c in ecols), "id")
                edge_src = next((c for c in ("source_node_id", "from_node", "source_id", "source") if c in ecols), "source")
                edge_tgt = next((c for c in ("target_node_id", "to_node", "target_id", "target") if c in ecols), "target")
                edge_type = next((c for c in ("edge_type", "relation_type", "relation", "type") if c in ecols), "type")
            result = {
                "node_table": t,
                "edge_table": edge_table or "edges",
                "node_id": id_col,
                "node_name": name_col,
                "node_type": type_col,
                "edge_id": edge_id,
                "edge_source": edge_src,
                "edge_target": edge_tgt,
                "edge_type": edge_type,
                "profile_name": "heuristic",
            }
            self._profiles[db_id] = result
            return result

        raise ValueError(f"Cannot detect schema for {db_id}. Tables found: {tables}")

    def _has_fts(self, db_id: str) -> bool:
        conn = self._get_conn(db_id)
        tables = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
        p = self._detect_profile(db_id)
        return f"{p['node_table']}_fts" in tables

    # ── Property helpers ────────────────────────────────────────────
    def _node_row_to_dict(self, row: sqlite3.Row, profile: dict) -> dict:
        d = dict(row)
        node_id = str(d.get(profile["node_id"], ""))
        name = d.get(profile["node_name"], "")
        node_type = d.get(profile["node_type"], "entity")
        # Collect extra columns as properties
        skip = {profile["node_id"], profile["node_name"], profile["node_type"],
                "created_at", "updated_at", "rowid"}
        props = {}
        for k, v in d.items():
            if k not in skip:
                if k == "properties" and isinstance(v, str):
                    try:
                        props.update(json.loads(v))
                    except (json.JSONDecodeError, TypeError):
                        props[k] = v
                else:
                    props[k] = v
        return {
            "id": node_id,
            "name": str(name),
            "type": str(node_type) if node_type else "entity",
            "properties": props,
        }

    def _edge_row_to_dict(self, row: sqlite3.Row, profile: dict) -> dict:
        d = dict(row)
        eid_col = profile.get("edge_id", "id")
        edge_id = str(d.get(eid_col, d.get("id", d.get("edge_id", d.get("rowid", "")))))
        source = str(d.get(profile["edge_source"], ""))
        target = str(d.get(profile["edge_target"], ""))
        edge_type = str(d.get(profile["edge_type"], "relates_to"))
        skip = {"id", "edge_id", "rowid", eid_col, profile["edge_source"],
                profile["edge_target"], profile["edge_type"],
                "created_at", "updated_at"}
        props = {}
        for k, v in d.items():
            if k not in skip:
                if k == "properties" and isinstance(v, str):
                    try:
                        props.update(json.loads(v))
                    except (json.JSONDecodeError, TypeError):
                        props[k] = v
                else:
                    props[k] = v
        return {
            "id": edge_id,
            "source": source,
            "target": target,
            "type": edge_type,
            "properties": props,
        }

    # ── Read operations ─────────────────────────────────────────────
    def get_database_stats(self, db_id: str) -> dict:
        conn = self._get_conn(db_id)
        p = self._detect_profile(db_id)
        node_count = conn.execute(f"SELECT COUNT(*) FROM {p['node_table']}").fetchone()[0]
        edge_count = 0
        try:
            edge_count = conn.execute(f"SELECT COUNT(*) FROM {p['edge_table']}").fetchone()[0]
        except sqlite3.OperationalError:
            pass

        node_types = []
        try:
            rows = conn.execute(
                f"SELECT {p['node_type']}, COUNT(*) as cnt FROM {p['node_table']} "
                f"GROUP BY {p['node_type']} ORDER BY cnt DESC"
            ).fetchall()
            node_types = [{"type": r[0], "count": r[1]} for r in rows]
        except sqlite3.OperationalError:
            pass

        edge_types = []
        try:
            rows = conn.execute(
                f"SELECT {p['edge_type']}, COUNT(*) as cnt FROM {p['edge_table']} "
                f"GROUP BY {p['edge_type']} ORDER BY cnt DESC"
            ).fetchall()
            edge_types = [{"type": r[0], "count": r[1]} for r in rows]
        except sqlite3.OperationalError:
            pass

        return {
            "db_id": db_id,
            "profile": p.get("profile_name", "unknown"),
            "node_count": node_count,
            "edge_count": edge_count,
            "node_types": node_types,
            "edge_types": edge_types,
            "has_fts": self._has_fts(db_id),
        }

    def get_nodes(self, db_id: str, node_type: str | None = None,
                  search: str | None = None, limit: int = 100,
                  offset: int = 0) -> dict:
        conn = self._get_conn(db_id)
        p = self._detect_profile(db_id)
        t = p["node_table"]

        conditions = []
        params: list[Any] = []

        if node_type:
            conditions.append(f"{p['node_type']} = ?")
            params.append(node_type)

        if search:
            if self._has_fts(db_id):
                fts_table = f"{t}_fts"
                fts_q = search.replace('"', '""')
                conditions.append(
                    f"rowid IN (SELECT rowid FROM {fts_table} WHERE {fts_table} MATCH ?)"
                )
                params.append(f'"{fts_q}"')
            else:
                conditions.append(f"({p['node_name']} LIKE ? OR {p['node_type']} LIKE ?)")
                params.extend([f"%{search}%", f"%{search}%"])

        where = f" WHERE {' AND '.join(conditions)}" if conditions else ""

        total = conn.execute(f"SELECT COUNT(*) FROM {t}{where}", params).fetchone()[0]
        rows = conn.execute(
            f"SELECT * FROM {t}{where} LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()

        return {
            "nodes": [self._node_row_to_dict(r, p) for r in rows],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def get_node(self, db_id: str, node_id: str) -> dict | None:
        conn = self._get_conn(db_id)
        p = self._detect_profile(db_id)
        row = conn.execute(
            f"SELECT * FROM {p['node_table']} WHERE {p['node_id']} = ?",
            (node_id,),
        ).fetchone()
        return self._node_row_to_dict(row, p) if row else None

    def get_neighbors(self, db_id: str, node_id: str, depth: int = 1,
                      limit: int = 50) -> dict:
        """Return subgraph around node_id up to given depth."""
        p = self._detect_profile(db_id)
        conn = self._get_conn(db_id)

        visited_ids: set[str] = set()
        edge_set: set[str] = set()
        frontier = {str(node_id)}
        all_nodes: list[dict] = []
        all_edges: list[dict] = []

        for _ in range(depth):
            if not frontier or len(visited_ids) >= limit:
                break
            placeholders = ",".join("?" for _ in frontier)
            # Outgoing
            try:
                rows = conn.execute(
                    f"SELECT * FROM {p['edge_table']} WHERE {p['edge_source']} IN ({placeholders})",
                    list(frontier),
                ).fetchall()
                for r in rows:
                    ed = self._edge_row_to_dict(r, p)
                    if ed["id"] not in edge_set:
                        all_edges.append(ed)
                        edge_set.add(ed["id"])
            except sqlite3.OperationalError:
                pass
            # Incoming
            try:
                rows = conn.execute(
                    f"SELECT * FROM {p['edge_table']} WHERE {p['edge_target']} IN ({placeholders})",
                    list(frontier),
                ).fetchall()
                for r in rows:
                    ed = self._edge_row_to_dict(r, p)
                    if ed["id"] not in edge_set:
                        all_edges.append(ed)
                        edge_set.add(ed["id"])
            except sqlite3.OperationalError:
                pass

            visited_ids.update(frontier)
            next_frontier: set[str] = set()
            for e in all_edges:
                if e["source"] not in visited_ids:
                    next_frontier.add(e["source"])
                if e["target"] not in visited_ids:
                    next_frontier.add(e["target"])
            frontier = next_frontier

        # Collect all referenced node IDs
        all_ids = visited_ids | frontier
        for e in all_edges:
            all_ids.add(e["source"])
            all_ids.add(e["target"])

        # Fetch node data in batches
        all_id_list = list(all_ids)[:limit]
        for i in range(0, len(all_id_list), 50):
            batch = all_id_list[i:i + 50]
            placeholders = ",".join("?" for _ in batch)
            rows = conn.execute(
                f"SELECT * FROM {p['node_table']} WHERE {p['node_id']} IN ({placeholders})",
                batch,
            ).fetchall()
            for r in rows:
                all_nodes.append(self._node_row_to_dict(r, p))

        return {"nodes": all_nodes, "edges": all_edges}

    def get_edges(self, db_id: str, edge_type: str | None = None,
                  limit: int = 100, offset: int = 0) -> dict:
        conn = self._get_conn(db_id)
        p = self._detect_profile(db_id)
        t = p["edge_table"]

        conditions = []
        params: list[Any] = []
        if edge_type:
            conditions.append(f"{p['edge_type']} = ?")
            params.append(edge_type)

        where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
        total = conn.execute(f"SELECT COUNT(*) FROM {t}{where}", params).fetchone()[0]
        rows = conn.execute(
            f"SELECT * FROM {t}{where} LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()
        return {
            "edges": [self._edge_row_to_dict(r, p) for r in rows],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def get_types(self, db_id: str) -> dict:
        conn = self._get_conn(db_id)
        p = self._detect_profile(db_id)
        node_types = []
        edge_types = []
        try:
            rows = conn.execute(
                f"SELECT {p['node_type']}, COUNT(*) as cnt FROM {p['node_table']} "
                f"GROUP BY {p['node_type']} ORDER BY cnt DESC"
            ).fetchall()
            node_types = [{"type": r[0], "count": r[1]} for r in rows]
        except sqlite3.OperationalError:
            pass
        try:
            rows = conn.execute(
                f"SELECT {p['edge_type']}, COUNT(*) as cnt FROM {p['edge_table']} "
                f"GROUP BY {p['edge_type']} ORDER BY cnt DESC"
            ).fetchall()
            edge_types = [{"type": r[0], "count": r[1]} for r in rows]
        except sqlite3.OperationalError:
            pass
        return {"node_types": node_types, "edge_types": edge_types}

    # ── Write operations (Phase C) ──────────────────────────────────
    def create_database(self, name: str) -> dict:
        safe_name = "".join(c for c in name if c.isalnum() or c in "-_").strip()
        if not safe_name:
            raise ValueError("Invalid database name")
        db_path = self.kgs_dir / f"{safe_name}.db"
        if db_path.exists():
            raise FileExistsError(f"Database already exists: {safe_name}")
        self.kgs_dir.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path))
        conn.executescript(STANDARD_CREATE_SQL)
        conn.close()
        return {"id": safe_name, "filename": f"{safe_name}.db", "path": f"{safe_name}.db"}

    @staticmethod
    def _make_node_id(name: str, node_type: str) -> str:
        return hashlib.md5(f"{node_type}:{name}".encode()).hexdigest()[:16]

    @staticmethod
    def _make_edge_id(source: str, target: str, edge_type: str) -> str:
        return hashlib.md5(f"{source}:{edge_type}:{target}".encode()).hexdigest()[:16]

    def create_node(self, db_id: str, name: str, node_type: str = "entity",
                    properties: dict | None = None) -> dict:
        conn = self._get_conn(db_id)
        p = self._detect_profile(db_id)
        node_id = self._make_node_id(name, node_type)
        props_json = json.dumps(properties or {})

        # Check if the table has a properties column
        cols = {r[1] for r in conn.execute(f"PRAGMA table_info({p['node_table']})").fetchall()}
        has_props = "properties" in cols

        col_names = [p["node_id"], p["node_name"], p["node_type"]]
        col_vals: list[Any] = [node_id, name, node_type]
        if has_props:
            col_names.append("properties")
            col_vals.append(props_json)

        placeholders = ",".join("?" for _ in col_names)
        conn.execute(
            f"INSERT OR REPLACE INTO {p['node_table']} ({','.join(col_names)}) VALUES ({placeholders})",
            col_vals,
        )
        conn.commit()
        return {"id": node_id, "name": name, "type": node_type, "properties": properties or {}}

    def update_node(self, db_id: str, node_id: str, name: str | None = None,
                    node_type: str | None = None, properties: dict | None = None) -> dict | None:
        conn = self._get_conn(db_id)
        p = self._detect_profile(db_id)
        sets = []
        params: list[Any] = []
        if name is not None:
            sets.append(f"{p['node_name']} = ?")
            params.append(name)
        if node_type is not None:
            sets.append(f"{p['node_type']} = ?")
            params.append(node_type)
        if properties is not None:
            sets.append("properties = ?")
            params.append(json.dumps(properties))
        if not sets:
            return self.get_node(db_id, node_id)
        params.append(node_id)
        conn.execute(
            f"UPDATE {p['node_table']} SET {', '.join(sets)} WHERE {p['node_id']} = ?",
            params,
        )
        conn.commit()
        return self.get_node(db_id, node_id)

    def delete_node(self, db_id: str, node_id: str) -> bool:
        conn = self._get_conn(db_id)
        p = self._detect_profile(db_id)
        # Delete connected edges first
        try:
            conn.execute(
                f"DELETE FROM {p['edge_table']} WHERE {p['edge_source']} = ? OR {p['edge_target']} = ?",
                (node_id, node_id),
            )
        except sqlite3.OperationalError:
            pass
        cur = conn.execute(
            f"DELETE FROM {p['node_table']} WHERE {p['node_id']} = ?", (node_id,)
        )
        conn.commit()
        return cur.rowcount > 0

    def create_edge(self, db_id: str, source: str, target: str,
                    edge_type: str = "relates_to", properties: dict | None = None) -> dict:
        conn = self._get_conn(db_id)
        p = self._detect_profile(db_id)
        eid_col = p.get("edge_id", "id")
        props_json = json.dumps(properties or {})

        # Check if edge_id is INTEGER (auto-increment) — if so, omit it from INSERT
        ecol_info = conn.execute(f"PRAGMA table_info({p['edge_table']})").fetchall()
        eid_is_int = False
        has_props_col = False
        for col in ecol_info:
            if col[1] == eid_col and col[2].upper() in ("INTEGER", "INT"):
                eid_is_int = True
            if col[1] == "properties":
                has_props_col = True

        if eid_is_int:
            # Let SQLite auto-generate the integer PK
            col_names = [p["edge_source"], p["edge_target"], p["edge_type"]]
            col_vals: list[Any] = [source, target, edge_type]
            if has_props_col:
                col_names.append("properties")
                col_vals.append(props_json)
            placeholders = ",".join("?" for _ in col_names)
            cur = conn.execute(
                f"INSERT INTO {p['edge_table']} ({','.join(col_names)}) VALUES ({placeholders})",
                col_vals,
            )
            conn.commit()
            edge_id = str(cur.lastrowid)
        else:
            edge_id = self._make_edge_id(source, target, edge_type)
            col_names = [eid_col, p["edge_source"], p["edge_target"], p["edge_type"]]
            col_vals = [edge_id, source, target, edge_type]
            if has_props_col:
                col_names.append("properties")
                col_vals.append(props_json)
            placeholders = ",".join("?" for _ in col_names)
            conn.execute(
                f"INSERT OR REPLACE INTO {p['edge_table']} ({','.join(col_names)}) VALUES ({placeholders})",
                col_vals,
            )
            conn.commit()

        return {"id": edge_id, "source": source, "target": target, "type": edge_type, "properties": properties or {}}

    def update_edge(self, db_id: str, edge_id: str, edge_type: str | None = None,
                    properties: dict | None = None) -> dict | None:
        conn = self._get_conn(db_id)
        p = self._detect_profile(db_id)
        eid_col = p.get("edge_id", "id")
        sets = []
        params: list[Any] = []
        if edge_type is not None:
            sets.append(f"{p['edge_type']} = ?")
            params.append(edge_type)
        if properties is not None:
            sets.append("properties = ?")
            params.append(json.dumps(properties))
        if not sets:
            return None
        params.append(edge_id)
        conn.execute(
            f"UPDATE {p['edge_table']} SET {', '.join(sets)} WHERE {eid_col} = ?", params,
        )
        conn.commit()
        row = conn.execute(f"SELECT * FROM {p['edge_table']} WHERE {eid_col} = ?", (edge_id,)).fetchone()
        return self._edge_row_to_dict(row, p) if row else None

    def delete_edge(self, db_id: str, edge_id: str) -> bool:
        conn = self._get_conn(db_id)
        p = self._detect_profile(db_id)
        eid_col = p.get("edge_id", "id")
        cur = conn.execute(f"DELETE FROM {p['edge_table']} WHERE {eid_col} = ?", (edge_id,))
        conn.commit()
        return cur.rowcount > 0

    def bulk_create(self, db_id: str, nodes: list[dict], edges: list[dict]) -> dict:
        created_nodes = []
        created_edges = []
        for n in nodes:
            created_nodes.append(self.create_node(
                db_id, n["name"], n.get("type", "entity"), n.get("properties"),
            ))
        for e in edges:
            created_edges.append(self.create_edge(
                db_id, e["source"], e["target"], e.get("type", "relates_to"), e.get("properties"),
            ))
        return {"nodes_created": len(created_nodes), "edges_created": len(created_edges),
                "nodes": created_nodes, "edges": created_edges}

    # ── Batch operations (Phase D) ──────────────────────────────────
    def batch_delete_by_type(self, db_id: str, node_type: str) -> int:
        conn = self._get_conn(db_id)
        p = self._detect_profile(db_id)
        # Get IDs first to delete edges
        ids = [r[0] for r in conn.execute(
            f"SELECT {p['node_id']} FROM {p['node_table']} WHERE {p['node_type']} = ?",
            (node_type,),
        ).fetchall()]
        if ids:
            placeholders = ",".join("?" for _ in ids)
            try:
                conn.execute(
                    f"DELETE FROM {p['edge_table']} WHERE {p['edge_source']} IN ({placeholders}) OR {p['edge_target']} IN ({placeholders})",
                    ids + ids,
                )
            except sqlite3.OperationalError:
                pass
            conn.execute(
                f"DELETE FROM {p['node_table']} WHERE {p['node_type']} = ?", (node_type,),
            )
            conn.commit()
        return len(ids)

    def batch_retype(self, db_id: str, old_type: str, new_type: str) -> int:
        conn = self._get_conn(db_id)
        p = self._detect_profile(db_id)
        cur = conn.execute(
            f"UPDATE {p['node_table']} SET {p['node_type']} = ? WHERE {p['node_type']} = ?",
            (new_type, old_type),
        )
        conn.commit()
        return cur.rowcount


# Singleton
kg_service = KGService()

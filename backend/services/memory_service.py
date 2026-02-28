"""Persistent conversation memory stored as a KG, searchable with hybrid retrieval."""
import json
import re
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


MEMORY_DB_PATH = Path(__file__).parent.parent / "workspace_memory.db"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS nodes (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL DEFAULT 'memory',
    properties TEXT DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS edges (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    target TEXT NOT NULL,
    type TEXT NOT NULL DEFAULT 'relates_to',
    properties TEXT DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(type);
CREATE INDEX IF NOT EXISTS idx_nodes_name ON nodes(name);
CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source);
CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target);

CREATE VIRTUAL TABLE IF NOT EXISTS nodes_fts USING fts5(
    name, type, properties, content=nodes, content_rowid=rowid
);

-- Keep FTS in sync
CREATE TRIGGER IF NOT EXISTS nodes_ai AFTER INSERT ON nodes BEGIN
    INSERT INTO nodes_fts(rowid, name, type, properties)
    VALUES (new.rowid, new.name, new.type, new.properties);
END;
CREATE TRIGGER IF NOT EXISTS nodes_ad AFTER DELETE ON nodes BEGIN
    INSERT INTO nodes_fts(nodes_fts, rowid, name, type, properties)
    VALUES('delete', old.rowid, old.name, old.type, old.properties);
END;
CREATE TRIGGER IF NOT EXISTS nodes_au AFTER UPDATE ON nodes BEGIN
    INSERT INTO nodes_fts(nodes_fts, rowid, name, type, properties)
    VALUES('delete', old.rowid, old.name, old.type, old.properties);
    INSERT INTO nodes_fts(rowid, name, type, properties)
    VALUES (new.rowid, new.name, new.type, new.properties);
END;

CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    mode TEXT NOT NULL DEFAULT 'chat',
    source TEXT DEFAULT 'web',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_message_at TIMESTAMP,
    message_count INTEGER DEFAULT 0,
    summary TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    author TEXT NOT NULL,
    content TEXT NOT NULL,
    provider TEXT,
    model TEXT,
    metadata TEXT DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id);

CREATE TABLE IF NOT EXISTS memory_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    memory_node_id TEXT NOT NULL,
    conversation_id TEXT NOT NULL,
    was_useful BOOLEAN,
    feedback_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS integrations (
    id TEXT PRIMARY KEY,
    platform TEXT NOT NULL,
    config TEXT NOT NULL DEFAULT '{}',
    enabled BOOLEAN DEFAULT 0,
    user_label TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS integration_messages (
    id TEXT PRIMARY KEY,
    integration_id TEXT NOT NULL,
    conversation_id TEXT,
    direction TEXT NOT NULL,
    platform_message_id TEXT,
    content TEXT NOT NULL,
    metadata TEXT DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# Regex patterns for Python-based memory extraction
DECISION_PATTERNS = [
    re.compile(r"(?:I |we |let'?s |decided to |chose to |should |will |going to )(.{10,120})", re.I),
    re.compile(r"(?:use |using |switch to |migrate to |adopt )(\S+(?:\s+\S+){0,5})", re.I),
]
ENTITY_PATTERNS = [
    re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b"),  # Title Case names
    re.compile(r"`([^`]{2,60})`"),  # Code references
    re.compile(r"(?:called |named |library |framework |tool )(\S+)", re.I),
]
FACT_PATTERNS = [
    re.compile(r"(.{5,80})\s+(?:is|are|means|equals|works by)\s+(.{5,120})", re.I),
    re.compile(r"(?:the |this )(.{5,60})\s+(?:has|contains|supports|requires)\s+(.{5,80})", re.I),
]


class MemoryService:
    """Persistent workspace memory with conversation tracking and KG storage."""

    MEMORY_DB_ID = "__workspace_memory__"

    def __init__(self):
        self._conn: Optional[sqlite3.Connection] = None
        self._registered = False

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(MEMORY_DB_PATH))
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
            self._conn.executescript(SCHEMA_SQL)
        return self._conn

    def _register_with_kg_service(self):
        """Register memory KG so embedding_service.search() works on it."""
        if self._registered:
            return
        try:
            from services.kg_service import kg_service
            # Add to connections cache directly
            kg_service._connections[self.MEMORY_DB_ID] = self._get_conn()
            kg_service._profiles[self.MEMORY_DB_ID] = {
                "node_table": "nodes",
                "edge_table": "edges",
                "node_id": "id",
                "node_name": "name",
                "node_type": "type",
                "edge_id": "id",
                "edge_source": "source",
                "edge_target": "target",
                "edge_type": "type",
                "profile_name": "standard",
            }
            self._registered = True
        except Exception:
            pass

    # ── Conversation persistence ─────────────────────────────────────

    def create_conversation(self, mode: str = "chat", source: str = "web") -> str:
        conn = self._get_conn()
        cid = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        conn.execute(
            "INSERT INTO conversations (id, mode, source, started_at, last_message_at) VALUES (?, ?, ?, ?, ?)",
            (cid, mode, source, now, now),
        )
        conn.commit()
        return cid

    def log_message(
        self,
        conversation_id: str,
        author: str,
        content: str,
        provider: str = None,
        model: str = None,
        metadata: dict = None,
    ) -> str:
        conn = self._get_conn()
        mid = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        conn.execute(
            "INSERT INTO messages (id, conversation_id, author, content, provider, model, metadata, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (mid, conversation_id, author, content, provider, model, json.dumps(metadata or {}), now),
        )
        conn.execute(
            "UPDATE conversations SET last_message_at = ?, message_count = message_count + 1 WHERE id = ?",
            (now, conversation_id),
        )
        conn.commit()
        return mid

    def get_conversation_messages(self, conversation_id: str, limit: int = 50, offset: int = 0) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC LIMIT ? OFFSET ?",
            (conversation_id, limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]

    def list_conversations(self, mode: str = None, source: str = None, limit: int = 20) -> list[dict]:
        conn = self._get_conn()
        q = "SELECT * FROM conversations"
        params = []
        conditions = []
        if mode:
            conditions.append("mode = ?")
            params.append(mode)
        if source:
            conditions.append("source = ?")
            params.append(source)
        if conditions:
            q += " WHERE " + " AND ".join(conditions)
        q += " ORDER BY last_message_at DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(q, params).fetchall()
        return [dict(r) for r in rows]

    def get_conversation(self, conversation_id: str) -> Optional[dict]:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,)).fetchone()
        if not row:
            return None
        result = dict(row)
        result["messages"] = self.get_conversation_messages(conversation_id)
        return result

    def delete_conversation(self, conversation_id: str) -> bool:
        conn = self._get_conn()
        conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
        cur = conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
        conn.commit()
        return cur.rowcount > 0

    # ── Memory extraction ────────────────────────────────────────────

    def extract_and_store(
        self,
        conversation_id: str,
        user_msg: str,
        assistant_msg: str,
        use_llm: bool = False,
    ) -> list[dict]:
        """Extract key facts/decisions from a conversation turn and store as KG nodes."""
        if use_llm:
            return self._extract_with_llm(conversation_id, user_msg, assistant_msg)
        return self._extract_with_regex(conversation_id, user_msg, assistant_msg)

    def _extract_with_regex(self, conversation_id: str, user_msg: str, assistant_msg: str) -> list[dict]:
        combined = f"{user_msg}\n{assistant_msg}"
        extracted = []

        # Decisions
        for pattern in DECISION_PATTERNS:
            for match in pattern.finditer(combined):
                text = match.group(1).strip().rstrip(".")
                if len(text) > 10:
                    extracted.append({"name": text, "type": "decision"})

        # Entities
        for pattern in ENTITY_PATTERNS:
            for match in pattern.finditer(combined):
                text = match.group(1).strip()
                if len(text) > 2 and text not in ("The", "This", "That", "What", "How"):
                    extracted.append({"name": text, "type": "entity"})

        # Facts
        for pattern in FACT_PATTERNS:
            for match in pattern.finditer(combined):
                subject = match.group(1).strip()
                predicate = match.group(2).strip().rstrip(".")
                if len(subject) > 3 and len(predicate) > 5:
                    extracted.append({"name": f"{subject}: {predicate}", "type": "fact"})

        # Deduplicate by name
        seen = set()
        unique = []
        for item in extracted:
            key = item["name"].lower()
            if key not in seen:
                seen.add(key)
                unique.append(item)

        # Limit per turn to avoid noise
        unique = unique[:8]

        # Store as KG nodes + edges
        stored = []
        conn = self._get_conn()
        import hashlib

        for item in unique:
            node_id = hashlib.md5(f"{item['type']}:{item['name']}".encode()).hexdigest()[:16]
            props = json.dumps({
                "conversation_id": conversation_id,
                "extracted_at": datetime.utcnow().isoformat(),
                "source": "regex",
            })
            conn.execute(
                "INSERT OR REPLACE INTO nodes (id, name, type, properties) VALUES (?, ?, ?, ?)",
                (node_id, item["name"], item["type"], props),
            )
            stored.append({"id": node_id, "name": item["name"], "type": item["type"]})

        conn.commit()
        self._register_with_kg_service()
        return stored

    def _extract_with_llm(self, conversation_id: str, user_msg: str, assistant_msg: str) -> list[dict]:
        """Use Gemini Flash for extraction (optional, higher quality)."""
        try:
            from services import gemini_service
            prompt = (
                "Extract key facts, decisions, and entities from this conversation turn. "
                "Return JSON array: [{\"name\": \"...\", \"type\": \"decision|fact|entity|topic\"}]\n\n"
                f"User: {user_msg[:2000]}\nAssistant: {assistant_msg[:2000]}"
            )
            raw = gemini_service.generate_content(
                prompt,
                model="gemini-2.5-flash",
                response_mime_type="application/json",
            )
            items = json.loads(raw)
            if not isinstance(items, list):
                return []

            stored = []
            conn = self._get_conn()
            import hashlib

            for item in items[:10]:
                name = item.get("name", "").strip()
                mtype = item.get("type", "fact")
                if not name or len(name) < 3:
                    continue
                node_id = hashlib.md5(f"{mtype}:{name}".encode()).hexdigest()[:16]
                props = json.dumps({
                    "conversation_id": conversation_id,
                    "extracted_at": datetime.utcnow().isoformat(),
                    "source": "llm",
                })
                conn.execute(
                    "INSERT OR REPLACE INTO nodes (id, name, type, properties) VALUES (?, ?, ?, ?)",
                    (node_id, name, mtype, props),
                )
                stored.append({"id": node_id, "name": name, "type": mtype})

            conn.commit()
            self._register_with_kg_service()
            return stored
        except Exception:
            # Fall back to regex
            return self._extract_with_regex(conversation_id, user_msg, assistant_msg)

    # ── Memory recall ────────────────────────────────────────────────

    def recall(self, query: str, limit: int = 5, min_score: float = 0.1,
               intent_hint: str | None = None) -> list[dict]:
        """Search memory KG using hybrid retrieval with optional intent hint."""
        self._register_with_kg_service()
        try:
            from services.embedding_service import embedding_service
            results = embedding_service.search(
                self.MEMORY_DB_ID, query, mode="hybrid", limit=limit,
                intent=intent_hint,
            )
            memories = []
            for r in results.get("results", []):
                if r["score"] >= min_score:
                    memories.append({
                        "id": r["node"]["id"],
                        "name": r["node"]["name"],
                        "type": r["node"]["type"],
                        "score": r["score"],
                        "properties": r["node"].get("properties", {}),
                    })
            return memories
        except Exception:
            # Fallback: simple FTS search
            return self._fts_recall(query, limit)

    def _fts_recall(self, query: str, limit: int) -> list[dict]:
        conn = self._get_conn()
        try:
            fts_q = query.replace('"', '""')
            rows = conn.execute(
                'SELECT rowid, rank FROM nodes_fts WHERE nodes_fts MATCH ? ORDER BY rank LIMIT ?',
                (f'"{fts_q}"', limit),
            ).fetchall()
            results = []
            for r in rows:
                node = conn.execute("SELECT * FROM nodes WHERE rowid = ?", (r[0],)).fetchone()
                if node:
                    results.append({
                        "id": node["id"],
                        "name": node["name"],
                        "type": node["type"],
                        "score": abs(r[1]),
                        "properties": json.loads(node["properties"]) if node["properties"] else {},
                    })
            return results
        except Exception:
            return []

    def format_memories_for_prompt(self, memories: list[dict], max_tokens: int = 500) -> str:
        """Format recalled memories for system prompt injection."""
        if not memories:
            return ""
        lines = ["[Recalled memories]"]
        char_budget = max_tokens * 4  # ~4 chars per token
        used = len(lines[0])
        for m in memories:
            line = f"- [{m['type']}] {m['name']}"
            if used + len(line) > char_budget:
                break
            lines.append(line)
            used += len(line)
        return "\n".join(lines)

    # ── Feedback + decay ─────────────────────────────────────────────

    def record_feedback(self, memory_node_id: str, conversation_id: str, was_useful: bool):
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO memory_feedback (memory_node_id, conversation_id, was_useful) VALUES (?, ?, ?)",
            (memory_node_id, conversation_id, was_useful),
        )
        conn.commit()

    def decay_unused_memories(self, days_threshold: int = 30):
        """Remove memory nodes not referenced in feedback for N days."""
        conn = self._get_conn()
        cutoff = (datetime.utcnow() - timedelta(days=days_threshold)).isoformat()
        conn.execute(
            "DELETE FROM nodes WHERE id NOT IN "
            "(SELECT DISTINCT memory_node_id FROM memory_feedback WHERE feedback_at > ?) "
            "AND created_at < ?",
            (cutoff, cutoff),
        )
        conn.commit()

    # ── Stats ────────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        conn = self._get_conn()
        node_count = conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
        conv_count = conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
        msg_count = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
        type_dist = conn.execute(
            "SELECT type, COUNT(*) as cnt FROM nodes GROUP BY type ORDER BY cnt DESC"
        ).fetchall()
        return {
            "memory_nodes": node_count,
            "conversations": conv_count,
            "messages": msg_count,
            "node_types": [{"type": r[0], "count": r[1]} for r in type_dist],
        }


# Singleton
memory_service = MemoryService()

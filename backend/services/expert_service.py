"""Expert Service — CRUD, conversation management, and KG-OS-backed expert execution."""
import json
import sqlite3
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "experts.db"


class ExpertService:
    """Expert agents backed by structured knowledge graphs with intent-driven retrieval."""

    def __init__(self):
        self._conn: sqlite3.Connection | None = None

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._init_schema()
        return self._conn

    def _init_schema(self):
        conn = self._conn
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS experts (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                kg_db_id TEXT NOT NULL,
                kg_db_ids TEXT DEFAULT '[]',
                persona_name TEXT DEFAULT 'Expert',
                persona_instructions TEXT DEFAULT '',
                persona_style TEXT DEFAULT 'professional',
                retrieval_methods TEXT DEFAULT '["hybrid","intent"]',
                retrieval_alpha REAL DEFAULT 0.35,
                retrieval_beta REAL DEFAULT 0.40,
                retrieval_gamma REAL DEFAULT 0.15,
                retrieval_delta REAL DEFAULT 0.10,
                retrieval_limit INTEGER DEFAULT 10,
                dimension_filters TEXT DEFAULT '{}',
                playbook_skills TEXT DEFAULT '[]',
                custom_goal_mappings TEXT DEFAULT '{}',
                icon TEXT DEFAULT 'brain',
                color TEXT DEFAULT '#0ea5e9',
                is_public BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS expert_conversations (
                id TEXT PRIMARY KEY,
                expert_id TEXT NOT NULL REFERENCES experts(id) ON DELETE CASCADE,
                title TEXT DEFAULT '',
                message_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_message_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS expert_messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL REFERENCES expert_conversations(id) ON DELETE CASCADE,
                author TEXT NOT NULL,
                content TEXT NOT NULL,
                sources TEXT DEFAULT '[]',
                retrieval_meta TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()

    def _row_to_dict(self, row: sqlite3.Row | None) -> dict | None:
        if row is None:
            return None
        d = dict(row)
        for key in ("kg_db_ids", "retrieval_methods", "dimension_filters",
                     "playbook_skills", "custom_goal_mappings", "sources", "retrieval_meta"):
            if key in d and isinstance(d[key], str):
                try:
                    d[key] = json.loads(d[key])
                except (json.JSONDecodeError, TypeError):
                    pass
        return d

    # ── Expert CRUD ──────────────────────────────────────────────────

    def create_expert(self, data: dict) -> dict:
        conn = self._get_conn()
        expert_id = str(uuid.uuid4())[:8]
        now = datetime.utcnow().isoformat()

        conn.execute(
            """INSERT INTO experts (id, name, description, kg_db_id, kg_db_ids,
                persona_name, persona_instructions, persona_style,
                retrieval_methods, retrieval_alpha, retrieval_beta, retrieval_gamma, retrieval_delta,
                retrieval_limit, dimension_filters, playbook_skills, custom_goal_mappings,
                icon, color, is_public, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                expert_id,
                data.get("name", "New Expert"),
                data.get("description", ""),
                data.get("kg_db_id", ""),
                json.dumps(data.get("kg_db_ids", [])),
                data.get("persona_name", "Expert"),
                data.get("persona_instructions", ""),
                data.get("persona_style", "professional"),
                json.dumps(data.get("retrieval_methods", ["hybrid", "intent"])),
                data.get("retrieval_alpha", 0.35),
                data.get("retrieval_beta", 0.40),
                data.get("retrieval_gamma", 0.15),
                data.get("retrieval_delta", 0.10),
                data.get("retrieval_limit", 10),
                json.dumps(data.get("dimension_filters", {})),
                json.dumps(data.get("playbook_skills", [])),
                json.dumps(data.get("custom_goal_mappings", {})),
                data.get("icon", "brain"),
                data.get("color", "#0ea5e9"),
                data.get("is_public", True),
                now, now,
            ),
        )
        conn.commit()
        return self.get_expert(expert_id)

    def get_expert(self, expert_id: str) -> dict | None:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM experts WHERE id = ?", (expert_id,)).fetchone()
        return self._row_to_dict(row)

    def list_experts(self) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM experts ORDER BY updated_at DESC").fetchall()
        return [self._row_to_dict(r) for r in rows]

    def update_expert(self, expert_id: str, data: dict) -> dict | None:
        conn = self._get_conn()
        existing = self.get_expert(expert_id)
        if not existing:
            return None

        # Build SET clause dynamically for provided fields
        updatable = [
            "name", "description", "kg_db_id", "persona_name",
            "persona_instructions", "persona_style", "retrieval_alpha",
            "retrieval_beta", "retrieval_gamma", "retrieval_delta",
            "retrieval_limit", "icon", "color", "is_public",
        ]
        json_fields = ["kg_db_ids", "retrieval_methods", "dimension_filters",
                        "playbook_skills", "custom_goal_mappings"]

        sets = []
        params = []
        for field in updatable:
            if field in data:
                sets.append(f"{field} = ?")
                params.append(data[field])
        for field in json_fields:
            if field in data:
                sets.append(f"{field} = ?")
                params.append(json.dumps(data[field]))

        if not sets:
            return existing

        sets.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())
        params.append(expert_id)

        conn.execute(f"UPDATE experts SET {', '.join(sets)} WHERE id = ?", params)
        conn.commit()
        return self.get_expert(expert_id)

    def delete_expert(self, expert_id: str) -> bool:
        conn = self._get_conn()
        conn.execute("DELETE FROM expert_messages WHERE conversation_id IN (SELECT id FROM expert_conversations WHERE expert_id = ?)", (expert_id,))
        conn.execute("DELETE FROM expert_conversations WHERE expert_id = ?", (expert_id,))
        conn.execute("DELETE FROM experts WHERE id = ?", (expert_id,))
        conn.commit()
        return True

    def duplicate_expert(self, expert_id: str) -> dict | None:
        existing = self.get_expert(expert_id)
        if not existing:
            return None
        data = {k: v for k, v in existing.items() if k not in ("id", "created_at", "updated_at")}
        data["name"] = f"{data['name']} (Copy)"
        return self.create_expert(data)

    # ── Conversation Management ──────────────────────────────────────

    def create_conversation(self, expert_id: str, title: str = "") -> dict:
        conn = self._get_conn()
        conv_id = str(uuid.uuid4())[:12]
        now = datetime.utcnow().isoformat()
        conn.execute(
            "INSERT INTO expert_conversations (id, expert_id, title, created_at, last_message_at) VALUES (?, ?, ?, ?, ?)",
            (conv_id, expert_id, title, now, now),
        )
        conn.commit()
        return {"id": conv_id, "expert_id": expert_id, "title": title, "message_count": 0, "created_at": now}

    def list_conversations(self, expert_id: str) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM expert_conversations WHERE expert_id = ? ORDER BY last_message_at DESC",
            (expert_id,),
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def get_conversation(self, conversation_id: str) -> dict | None:
        conn = self._get_conn()
        conv = conn.execute("SELECT * FROM expert_conversations WHERE id = ?", (conversation_id,)).fetchone()
        if not conv:
            return None
        result = self._row_to_dict(conv)
        messages = conn.execute(
            "SELECT * FROM expert_messages WHERE conversation_id = ? ORDER BY created_at",
            (conversation_id,),
        ).fetchall()
        result["messages"] = [self._row_to_dict(m) for m in messages]
        return result

    def delete_conversation(self, conversation_id: str) -> bool:
        conn = self._get_conn()
        conn.execute("DELETE FROM expert_messages WHERE conversation_id = ?", (conversation_id,))
        conn.execute("DELETE FROM expert_conversations WHERE id = ?", (conversation_id,))
        conn.commit()
        return True

    def _log_message(self, conversation_id: str, author: str, content: str,
                     sources: list | None = None, retrieval_meta: dict | None = None):
        conn = self._get_conn()
        msg_id = str(uuid.uuid4())[:12]
        now = datetime.utcnow().isoformat()
        conn.execute(
            "INSERT INTO expert_messages (id, conversation_id, author, content, sources, retrieval_meta, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (msg_id, conversation_id, author, content, json.dumps(sources or []), json.dumps(retrieval_meta or {}), now),
        )
        conn.execute(
            "UPDATE expert_conversations SET message_count = message_count + 1, last_message_at = ? WHERE id = ?",
            (now, conversation_id),
        )
        conn.commit()

    # ── Expert Execution ─────────────────────────────────────────────

    async def execute(
        self,
        expert_id: str,
        query: str,
        conversation_id: str | None = None,
        history: list[dict] | None = None,
    ) -> AsyncGenerator[str, None]:
        """Execute an expert query: KG-OS retrieval → context assembly → LLM stream → persist."""
        from services.kgos_query_engine import kgos_query_engine

        expert = self.get_expert(expert_id)
        if not expert:
            yield json.dumps({"type": "error", "content": "Expert not found"})
            return

        # Create or reuse conversation
        if not conversation_id:
            conv = self.create_conversation(expert_id, title=query[:100])
            conversation_id = conv["id"]

        yield json.dumps({"type": "conversation_id", "id": conversation_id})

        # Log user message
        self._log_message(conversation_id, "user", query)

        # ── Step 1: KG-OS Retrieval ──────────────────────────────────
        db_id = expert["kg_db_id"]
        source_nodes = []
        context_parts = []
        retrieval_meta = {}

        if db_id:
            try:
                search_results = kgos_query_engine.intent_search(
                    db_id=db_id,
                    query=query,
                    alpha=expert.get("retrieval_alpha", 0.35),
                    beta=expert.get("retrieval_beta", 0.40),
                    gamma=expert.get("retrieval_gamma", 0.15),
                    delta=expert.get("retrieval_delta", 0.10),
                    limit=expert.get("retrieval_limit", 10),
                    methods=expert.get("retrieval_methods", ["hybrid", "intent"]),
                )

                for r in search_results.get("results", []):
                    node = r["node"]
                    source_nodes.append({
                        "id": node["id"],
                        "name": node["name"],
                        "type": node["type"],
                        "score": r["score"],
                        "method": r["method"],
                    })
                    props_str = ""
                    props = node.get("properties", {})
                    if props:
                        clean = {k: v for k, v in props.items()
                                 if k not in ("embedding", "vector") and len(str(v)) < 500}
                        if clean:
                            props_str = f" | {json.dumps(clean)}"
                    context_parts.append(f"- [{node['type']}] {node['name']}{props_str}")

                retrieval_meta = {
                    "intent": search_results.get("intent", ""),
                    "weights": search_results.get("weights", {}),
                    "total_results": search_results.get("total", 0),
                    "db_id": db_id,
                }

                # Expand top 3 with graph neighbors
                from services.kg_service import kg_service
                for r in search_results.get("results", [])[:3]:
                    try:
                        neighbors = kg_service.get_neighbors(db_id, r["node"]["id"], depth=1, limit=10)
                        for edge in neighbors.get("edges", []):
                            src_name = next((n["name"] for n in neighbors["nodes"] if n["id"] == edge["source"]), edge["source"])
                            tgt_name = next((n["name"] for n in neighbors["nodes"] if n["id"] == edge["target"]), edge["target"])
                            context_parts.append(f"  Relation: {src_name} --{edge['type']}--> {tgt_name}")
                    except Exception:
                        pass

            except Exception as e:
                logger.warning(f"KG-OS retrieval failed for expert {expert_id}: {e}")
                context_parts.append(f"(KG retrieval encountered an issue: {e})")

        # Also search additional KGs if configured
        extra_db_ids = expert.get("kg_db_ids", [])
        if isinstance(extra_db_ids, list):
            for extra_db in extra_db_ids:
                if extra_db and extra_db != db_id:
                    try:
                        extra_results = kgos_query_engine.intent_search(
                            db_id=extra_db, query=query, limit=5,
                            alpha=expert.get("retrieval_alpha", 0.35),
                            beta=expert.get("retrieval_beta", 0.40),
                            gamma=expert.get("retrieval_gamma", 0.15),
                            delta=expert.get("retrieval_delta", 0.10),
                        )
                        for r in extra_results.get("results", []):
                            node = r["node"]
                            source_nodes.append({
                                "id": node["id"], "name": node["name"],
                                "type": node["type"], "score": r["score"],
                                "method": r["method"], "db_id": extra_db,
                            })
                            context_parts.append(f"- [{node['type']}] {node['name']} (from {extra_db})")
                    except Exception:
                        pass

        # Emit sources
        yield json.dumps({"type": "sources", "nodes": source_nodes})

        # ── Step 2: Context Assembly ─────────────────────────────────
        kg_context = "\n".join(context_parts) if context_parts else "No relevant knowledge found."

        persona_instructions = expert.get("persona_instructions", "")
        persona_name = expert.get("persona_name", "Expert")
        persona_style = expert.get("persona_style", "professional")

        system_prompt = f"""You are {persona_name}, a specialized AI expert.

{persona_instructions}

Communication style: {persona_style}

Knowledge Graph Context (retrieved via KG-OS with intent: {retrieval_meta.get('intent', 'unknown')}):
{kg_context}

When answering:
- Use the provided knowledge graph context to inform your responses
- Cite specific entities and relationships when relevant (use [NodeName] notation)
- If the context doesn't contain enough information, say so honestly
- Stay in character as {persona_name}
"""

        # Inject playbook skills if configured
        playbook_skills = expert.get("playbook_skills", [])
        if playbook_skills:
            try:
                from services.skill_injector import skill_injector
                skill_context = await skill_injector.get_relevant_context(query, "chat")
                if skill_context:
                    system_prompt += f"\n\nPlaybook Skills:\n{skill_context}"
            except Exception:
                pass

        # ── Step 3: LLM Generation (streaming) ──────────────────────
        from config import GEMINI_API_KEY
        if not GEMINI_API_KEY:
            yield json.dumps({"type": "error", "content": "GEMINI_API_KEY not configured"})
            return

        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)

        # Build conversation history
        messages = []
        if history:
            for msg in history[-10:]:
                role = msg.get("role", msg.get("author", "user"))
                content = msg.get("content", "")
                if role in ("user", "model"):
                    messages.append({"role": role, "parts": [{"text": content}]})
        messages.append({"role": "user", "parts": [{"text": query}]})

        accumulated_text = ""
        try:
            response = client.models.generate_content_stream(
                model="gemini-2.5-flash",
                contents=messages,
                config={
                    "system_instruction": system_prompt,
                    "temperature": 0.7,
                    "max_output_tokens": 4096,
                },
            )
            for chunk in response:
                if chunk.text:
                    accumulated_text += chunk.text
                    yield json.dumps({"type": "content", "text": chunk.text})
        except Exception as e:
            error_msg = f"Generation error: {str(e)}"
            accumulated_text = error_msg
            yield json.dumps({"type": "error", "content": error_msg})

        # ── Step 4: Persist ──────────────────────────────────────────
        if accumulated_text:
            self._log_message(
                conversation_id, "assistant", accumulated_text,
                sources=source_nodes, retrieval_meta=retrieval_meta,
            )

        yield json.dumps({"type": "done"})


# Singleton
expert_service = ExpertService()

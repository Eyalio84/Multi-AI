#!/usr/bin/env python3
"""
FORGE-AI Sonnet Agent - Persistent Cross-Provider Expert
=========================================================

A persistent Sonnet 4.5 expert agent with SQLite conversation history,
26-playbook knowledge base, and smart context management. Designed as
the Claude↔Gemini translation bridge for FORGE-AI methodology.

Architecture:
  - SQLite persistence (conversation history across sessions)
  - 26 playbooks pre-loaded as knowledge base (KNOWLEDGE/REASONING/AGENT/FOUNDATION)
  - Topic-based context management (loads relevant playbooks per query)
  - Anthropic API integration (Sonnet 4.5)
  - CLI modes: --ask, --chat, --context, --playbooks, --sessions, --export

Created: February 6, 2026
Phase: 8.5 - FORGE-AI Cross-Provider Reproducibility
NLKE Version: 7.5
"""

import os
import sys
import json
import re
import sqlite3
import hashlib
import argparse
import readline
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


# =============================================================================
# Constants
# =============================================================================

VERSION = "1.0.0"
AGENT_NAME = "FORGE-AI Sonnet Agent"

# Default paths
DEFAULT_DB_DIR = os.path.expanduser("~/.forge-ai")
DEFAULT_DB_PATH = os.path.join(DEFAULT_DB_DIR, "sonnet-agent.db")

# Playbook directory
PLAYBOOKS_V2_DIR = "/storage/emulated/0/Download/gemini-3-pro/playbooks/playbooks-v2"

# The 26 target playbooks organized by category
TARGET_PLAYBOOKS = {
    "KNOWLEDGE": [
        "KNOWLEDGE-graph-engineering.pb",
        "KNOWLEDGE-advanced-rag-fusion.pb",
        "KNOWLEDGE-advanced-graph-reasoning.pb",
        "KNOWLEDGE-bidirectional-path-indexing.pb",
        "KNOWLEDGE-embedding-systems.pb",
        "KNOWLEDGE-graph-traversal.pb",
        "KNOWLEDGE-perception-enhancement.pb",
        "KNOWLEDGE-rag-retrieval-query-hybrid-methodology.pb",
        "KNOWLEDGE-semantic-embeddings.pb",
    ],
    "REASONING": [
        "REASONING-engine.pb",
        "REASONING-metacognition-workflows.pb",
        "REASONING-oracle-construction.pb",
        "REASONING-patterns.pb",
        "REASONING-context-window-mgmt.pb",
        "REASONING-high-depth-insights.pb",
        "REASONING-meta-optimization.pb",
    ],
    "AGENT": [
        "AGENT-conversation-tools-reasoning.pb",
        "AGENT-conversation-tools-synthesis.pb",
        "AGENT-session-continuity.pb",
        "AGENT-session-handoff.pb",
        "AGENT-plan-mode-patterns.pb",
    ],
    "FOUNDATION": [
        "FOUNDATION-cost-optimization.pb",
        "FOUNDATION-extended-thinking.pb",
        "FOUNDATION-playbook-system.pb",
        "FOUNDATION-opus-advisor.pb",
        "FOUNDATION-haiku-delegation.pb",
    ],
}

# Topic keyword → playbook mapping for smart context loading
TOPIC_KEYWORDS = {
    # Knowledge Graph topics
    "knowledge graph": ["KNOWLEDGE-graph-engineering.pb", "KNOWLEDGE-advanced-graph-reasoning.pb", "KNOWLEDGE-graph-traversal.pb"],
    "kg": ["KNOWLEDGE-graph-engineering.pb", "KNOWLEDGE-advanced-graph-reasoning.pb"],
    "entity extraction": ["KNOWLEDGE-graph-engineering.pb", "KNOWLEDGE-perception-enhancement.pb"],
    "graph": ["KNOWLEDGE-graph-engineering.pb", "KNOWLEDGE-graph-traversal.pb", "KNOWLEDGE-advanced-graph-reasoning.pb"],
    "node": ["KNOWLEDGE-graph-engineering.pb", "KNOWLEDGE-graph-traversal.pb"],
    "edge": ["KNOWLEDGE-graph-engineering.pb", "KNOWLEDGE-graph-traversal.pb"],
    "traversal": ["KNOWLEDGE-graph-traversal.pb", "KNOWLEDGE-bidirectional-path-indexing.pb"],
    "path": ["KNOWLEDGE-bidirectional-path-indexing.pb", "KNOWLEDGE-graph-traversal.pb"],

    # RAG & Retrieval topics
    "rag": ["KNOWLEDGE-advanced-rag-fusion.pb", "KNOWLEDGE-rag-retrieval-query-hybrid-methodology.pb"],
    "retrieval": ["KNOWLEDGE-advanced-rag-fusion.pb", "KNOWLEDGE-rag-retrieval-query-hybrid-methodology.pb"],
    "search": ["KNOWLEDGE-rag-retrieval-query-hybrid-methodology.pb", "KNOWLEDGE-semantic-embeddings.pb"],
    "query": ["KNOWLEDGE-rag-retrieval-query-hybrid-methodology.pb"],
    "fusion": ["KNOWLEDGE-advanced-rag-fusion.pb"],

    # Embedding topics
    "embedding": ["KNOWLEDGE-embedding-systems.pb", "KNOWLEDGE-semantic-embeddings.pb"],
    "semantic": ["KNOWLEDGE-semantic-embeddings.pb", "KNOWLEDGE-embedding-systems.pb"],
    "vector": ["KNOWLEDGE-embedding-systems.pb", "KNOWLEDGE-semantic-embeddings.pb"],

    # Reasoning topics
    "reasoning": ["REASONING-engine.pb", "REASONING-patterns.pb"],
    "thinking": ["REASONING-engine.pb", "FOUNDATION-extended-thinking.pb"],
    "metacognition": ["REASONING-metacognition-workflows.pb"],
    "oracle": ["REASONING-oracle-construction.pb"],
    "pattern": ["REASONING-patterns.pb"],
    "context window": ["REASONING-context-window-mgmt.pb"],
    "context management": ["REASONING-context-window-mgmt.pb"],
    "depth": ["REASONING-high-depth-insights.pb"],
    "insight": ["REASONING-high-depth-insights.pb"],
    "optimization": ["REASONING-meta-optimization.pb", "FOUNDATION-cost-optimization.pb"],
    "meta": ["REASONING-meta-optimization.pb", "REASONING-metacognition-workflows.pb"],

    # Agent topics
    "agent": ["AGENT-conversation-tools-reasoning.pb", "AGENT-conversation-tools-synthesis.pb", "AGENT-plan-mode-patterns.pb"],
    "conversation": ["AGENT-conversation-tools-reasoning.pb", "AGENT-conversation-tools-synthesis.pb"],
    "synthesis": ["AGENT-conversation-tools-synthesis.pb"],
    "session": ["AGENT-session-continuity.pb", "AGENT-session-handoff.pb"],
    "continuity": ["AGENT-session-continuity.pb"],
    "handoff": ["AGENT-session-handoff.pb"],
    "plan": ["AGENT-plan-mode-patterns.pb"],

    # Foundation topics
    "cost": ["FOUNDATION-cost-optimization.pb"],
    "cache": ["FOUNDATION-cost-optimization.pb"],
    "batch": ["FOUNDATION-cost-optimization.pb"],
    "extended thinking": ["FOUNDATION-extended-thinking.pb"],
    "playbook": ["FOUNDATION-playbook-system.pb"],
    "opus": ["FOUNDATION-opus-advisor.pb"],
    "haiku": ["FOUNDATION-haiku-delegation.pb"],
    "delegation": ["FOUNDATION-haiku-delegation.pb"],
    "model selection": ["FOUNDATION-opus-advisor.pb", "FOUNDATION-haiku-delegation.pb", "FOUNDATION-cost-optimization.pb"],

    # Cross-provider topics
    "gemini": ["FOUNDATION-cost-optimization.pb", "REASONING-engine.pb", "AGENT-plan-mode-patterns.pb"],
    "claude": ["FOUNDATION-cost-optimization.pb", "FOUNDATION-extended-thinking.pb", "REASONING-engine.pb"],
    "api": ["FOUNDATION-cost-optimization.pb", "REASONING-context-window-mgmt.pb"],
    "translate": ["REASONING-patterns.pb", "AGENT-conversation-tools-reasoning.pb"],
    "compare": ["REASONING-patterns.pb", "FOUNDATION-cost-optimization.pb"],
}

# Token budget management
MAX_CONTEXT_TOKENS = 180000  # Conservative limit for Sonnet 4.5
PLAYBOOK_SUMMARY_TOKENS = 500  # Approximate tokens per playbook summary
FULL_PLAYBOOK_MAX_CHARS = 15000  # Max chars to include from a single playbook
MAX_PLAYBOOKS_FULL = 3  # Max playbooks to include in full
MAX_PLAYBOOKS_SUMMARY = 8  # Max playbook summaries to include
MAX_HISTORY_MESSAGES = 20  # Max conversation history messages to include

# System prompt
SYSTEM_PROMPT = """You are the FORGE-AI Sonnet Agent, a persistent expert on Claude API, knowledge engineering, and cross-provider AI translation.

## Your Expertise
- **Claude API:** Anthropic API, prompt caching, extended thinking, batch API, structured output, citations, tools/function calling, model selection (Opus/Sonnet/Haiku)
- **Knowledge Engineering:** Knowledge graph construction (SQLite), entity extraction, relationship mapping, semantic search, RAG architectures, embedding systems
- **FORGE-AI Methodology:** The Framework for Ontology, Retrieval & Generation Engineering with AI - an LLM-driven knowledge engineering system
- **Playbook System:** 26+ playbooks covering KNOWLEDGE, REASONING, AGENT, and FOUNDATION domains
- **Cross-Provider Translation:** Claude↔Gemini concept mapping, API differences, capability equivalences

## Your Role
When a user (or Gemini CLI) asks you a question:
1. Draw on your loaded playbook knowledge to give deep, expert answers
2. Translate between Claude and Gemini concepts when needed
3. Provide concrete code examples when helpful
4. Reference specific playbooks for deeper reading
5. Maintain conversation context across messages (you have persistent memory)

## Response Style
- Be direct and technical
- Include code examples when relevant
- Reference specific playbooks by name (e.g., "See KNOWLEDGE-graph-engineering.pb for details")
- When translating between providers, show both sides clearly
- Flag important differences between Claude and Gemini approaches

## Loaded Knowledge
{playbook_context}
"""


# =============================================================================
# Database Layer
# =============================================================================

class ConversationDB:
    """SQLite-backed conversation persistence."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        """Create tables if they don't exist."""
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                message_count INTEGER DEFAULT 0,
                summary TEXT DEFAULT '',
                metadata TEXT DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                token_estimate INTEGER DEFAULT 0,
                playbooks_used TEXT DEFAULT '[]',
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            );

            CREATE TABLE IF NOT EXISTS playbook_cache (
                filename TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                title TEXT DEFAULT '',
                summary TEXT DEFAULT '',
                keywords TEXT DEFAULT '[]',
                char_count INTEGER DEFAULT 0,
                content_hash TEXT DEFAULT '',
                loaded_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
            CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
            CREATE INDEX IF NOT EXISTS idx_sessions_updated ON sessions(updated_at);
        """)
        self.conn.commit()

    def create_session(self, name: str = "default") -> str:
        """Create a new conversation session. Returns session ID."""
        session_id = hashlib.sha256(
            f"{name}-{datetime.now(timezone.utc).isoformat()}".encode()
        ).hexdigest()[:16]
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            "INSERT INTO sessions (id, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (session_id, name, now, now)
        )
        self.conn.commit()
        return session_id

    def get_session(self, name: str) -> Optional[Dict]:
        """Get most recent session by name."""
        row = self.conn.execute(
            "SELECT * FROM sessions WHERE name = ? ORDER BY updated_at DESC LIMIT 1",
            (name,)
        ).fetchone()
        return dict(row) if row else None

    def get_session_by_id(self, session_id: str) -> Optional[Dict]:
        """Get session by ID."""
        row = self.conn.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_sessions(self, limit: int = 20) -> List[Dict]:
        """List all sessions, most recent first."""
        rows = self.conn.execute(
            "SELECT * FROM sessions ORDER BY updated_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def add_message(self, session_id: str, role: str, content: str,
                    playbooks_used: List[str] = None) -> int:
        """Add a message to a session. Returns message ID."""
        now = datetime.now(timezone.utc).isoformat()
        token_estimate = len(content) // 4  # rough estimate
        cursor = self.conn.execute(
            """INSERT INTO messages (session_id, role, content, timestamp, token_estimate, playbooks_used)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (session_id, role, content, now, token_estimate,
             json.dumps(playbooks_used or []))
        )
        # Update session
        self.conn.execute(
            """UPDATE sessions SET updated_at = ?,
               message_count = (SELECT COUNT(*) FROM messages WHERE session_id = ?)
               WHERE id = ?""",
            (now, session_id, session_id)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_messages(self, session_id: str, limit: int = MAX_HISTORY_MESSAGES) -> List[Dict]:
        """Get recent messages for a session."""
        rows = self.conn.execute(
            """SELECT * FROM messages WHERE session_id = ?
               ORDER BY timestamp DESC LIMIT ?""",
            (session_id, limit)
        ).fetchall()
        return [dict(r) for r in reversed(rows)]

    def get_message_count(self, session_id: str) -> int:
        """Get total message count for a session."""
        row = self.conn.execute(
            "SELECT COUNT(*) as cnt FROM messages WHERE session_id = ?",
            (session_id,)
        ).fetchone()
        return row["cnt"]

    def update_session_summary(self, session_id: str, summary: str):
        """Update the session summary."""
        self.conn.execute(
            "UPDATE sessions SET summary = ? WHERE id = ?",
            (summary, session_id)
        )
        self.conn.commit()

    def delete_session(self, session_id: str):
        """Delete a session and its messages."""
        self.conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        self.conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        self.conn.commit()

    def cache_playbook(self, filename: str, category: str, title: str,
                       summary: str, keywords: List[str], char_count: int,
                       content_hash: str):
        """Cache playbook metadata."""
        self.conn.execute(
            """INSERT OR REPLACE INTO playbook_cache
               (filename, category, title, summary, keywords, char_count, content_hash, loaded_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (filename, category, title, summary, json.dumps(keywords),
             char_count, content_hash, datetime.now(timezone.utc).isoformat())
        )
        self.conn.commit()

    def get_cached_playbooks(self) -> List[Dict]:
        """Get all cached playbook metadata."""
        rows = self.conn.execute("SELECT * FROM playbook_cache ORDER BY category, filename").fetchall()
        return [dict(r) for r in rows]

    def export_session(self, session_id: str) -> Dict:
        """Export a session with all messages as JSON."""
        session = self.get_session_by_id(session_id)
        if not session:
            return {}
        messages = self.conn.execute(
            "SELECT * FROM messages WHERE session_id = ? ORDER BY timestamp",
            (session_id,)
        ).fetchall()
        return {
            "session": session,
            "messages": [dict(m) for m in messages],
            "exported_at": datetime.now(timezone.utc).isoformat(),
        }

    def close(self):
        """Close database connection."""
        self.conn.close()


# =============================================================================
# Playbook Loader
# =============================================================================

class PlaybookLoader:
    """Loads and indexes .pb playbook files for context injection."""

    def __init__(self, pb_dir: str = PLAYBOOKS_V2_DIR):
        self.pb_dir = pb_dir
        self.playbooks: Dict[str, Dict] = {}  # filename -> {title, category, summary, content, keywords, ...}
        self.loaded = False

    def load_all(self, target_playbooks: Dict[str, List[str]] = None) -> int:
        """Load target playbooks from disk. Returns count loaded."""
        targets = target_playbooks or TARGET_PLAYBOOKS
        count = 0

        for category, filenames in targets.items():
            for filename in filenames:
                filepath = os.path.join(self.pb_dir, filename)
                if not os.path.exists(filepath):
                    print(f"  WARNING: Playbook not found: {filename}", file=sys.stderr)
                    continue

                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()

                    pb_data = self._parse_playbook(filename, category, content)
                    self.playbooks[filename] = pb_data
                    count += 1
                except Exception as e:
                    print(f"  WARNING: Failed to load {filename}: {e}", file=sys.stderr)

        self.loaded = True
        return count

    def _parse_playbook(self, filename: str, category: str, content: str) -> Dict:
        """Parse a .pb file into structured data."""
        lines = content.split("\n")

        # Extract title from first heading
        title = filename.replace(".pb", "").replace("-", " ")
        for line in lines[:10]:
            if line.startswith("# "):
                title = line.lstrip("# ").strip()
                break

        # Extract metadata from header
        metadata = {}
        for line in lines[:30]:
            if line.startswith("**") and ":**" in line:
                key_match = re.match(r'\*\*(.+?):\*\*\s*(.*)', line)
                if key_match:
                    metadata[key_match.group(1).lower().strip()] = key_match.group(2).strip()

        # Build summary (first 2-3 meaningful paragraphs)
        summary_parts = []
        in_header = True
        for line in lines:
            if in_header and (line.startswith("**") or line.startswith("---") or not line.strip()):
                if line.startswith("---"):
                    in_header = False
                continue
            in_header = False
            if line.startswith("## "):
                if len(summary_parts) >= 2:
                    break
                summary_parts.append(line.lstrip("# ").strip())
            elif line.strip() and not line.startswith("```") and not line.startswith("|"):
                summary_parts.append(line.strip())
                if len(" ".join(summary_parts)) > 500:
                    break

        summary = " ".join(summary_parts)[:600]

        # Extract section headers for indexing
        sections = []
        for line in lines:
            if line.startswith("## "):
                sections.append(line.lstrip("# ").strip())

        # Extract keywords from title, sections, and content
        keywords = self._extract_keywords(title, sections, content)

        # Content hash for cache invalidation
        content_hash = hashlib.md5(content.encode()).hexdigest()[:12]

        return {
            "filename": filename,
            "category": category,
            "title": title,
            "summary": summary,
            "sections": sections,
            "keywords": keywords,
            "metadata": metadata,
            "content": content,
            "char_count": len(content),
            "content_hash": content_hash,
        }

    def _extract_keywords(self, title: str, sections: List[str], content: str) -> List[str]:
        """Extract searchable keywords from playbook content."""
        text = f"{title} {' '.join(sections)}".lower()
        # Common technical terms to look for
        tech_terms = [
            "knowledge graph", "entity extraction", "rag", "retrieval", "embedding",
            "semantic", "vector", "reasoning", "thinking", "metacognition", "oracle",
            "pattern", "context", "cache", "batch", "cost", "optimization",
            "agent", "session", "playbook", "handoff", "continuity", "plan",
            "graph", "node", "edge", "traversal", "path", "search", "query",
            "delegation", "haiku", "sonnet", "opus", "model", "api",
            "fusion", "hybrid", "index", "schema", "validation",
        ]
        found = [term for term in tech_terms if term in text]
        return found

    def get_relevant_playbooks(self, query: str, max_full: int = MAX_PLAYBOOKS_FULL,
                                max_summary: int = MAX_PLAYBOOKS_SUMMARY) -> Tuple[List[Dict], List[Dict]]:
        """Get playbooks relevant to a query. Returns (full_playbooks, summary_playbooks)."""
        if not self.loaded:
            return [], []

        query_lower = query.lower()
        scores: Dict[str, float] = {}

        # Score by keyword matches from TOPIC_KEYWORDS
        for keyword, pb_files in TOPIC_KEYWORDS.items():
            if keyword in query_lower:
                for pb_file in pb_files:
                    if pb_file in self.playbooks:
                        scores[pb_file] = scores.get(pb_file, 0) + 2.0

        # Score by playbook keyword overlap
        query_words = set(query_lower.split())
        for filename, pb_data in self.playbooks.items():
            for kw in pb_data["keywords"]:
                if kw in query_lower:
                    scores[filename] = scores.get(filename, 0) + 1.0
            # Partial word matching
            for word in query_words:
                if len(word) >= 4:
                    if word in pb_data["title"].lower():
                        scores[filename] = scores.get(filename, 0) + 0.5
                    if word in pb_data["summary"].lower():
                        scores[filename] = scores.get(filename, 0) + 0.3

        # Sort by score
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        # Split into full (top N) and summary (next M)
        full_playbooks = []
        summary_playbooks = []

        for filename, score in ranked:
            if score < 0.3:
                continue
            pb = self.playbooks[filename]
            if len(full_playbooks) < max_full:
                full_playbooks.append(pb)
            elif len(summary_playbooks) < max_summary:
                summary_playbooks.append(pb)
            else:
                break

        # If no matches, include category-level defaults
        if not full_playbooks and not summary_playbooks:
            # Include one from each category as fallback
            for cat_files in TARGET_PLAYBOOKS.values():
                if cat_files[0] in self.playbooks:
                    summary_playbooks.append(self.playbooks[cat_files[0]])
                    if len(summary_playbooks) >= 4:
                        break

        return full_playbooks, summary_playbooks

    def get_all_summaries(self) -> str:
        """Get a compact summary of all loaded playbooks."""
        lines = []
        for category in ["KNOWLEDGE", "REASONING", "AGENT", "FOUNDATION"]:
            lines.append(f"\n### {category}")
            for filename, pb_data in sorted(self.playbooks.items()):
                if pb_data["category"] == category:
                    lines.append(f"- **{pb_data['title']}** ({filename}): {pb_data['summary'][:120]}...")
        return "\n".join(lines)

    def format_context(self, full_playbooks: List[Dict],
                       summary_playbooks: List[Dict]) -> str:
        """Format playbook context for system prompt injection."""
        parts = []

        if full_playbooks:
            parts.append("## Detailed Playbook Knowledge (loaded for this query)")
            for pb in full_playbooks:
                content = pb["content"]
                if len(content) > FULL_PLAYBOOK_MAX_CHARS:
                    content = content[:FULL_PLAYBOOK_MAX_CHARS] + "\n\n[... truncated for context budget ...]"
                parts.append(f"\n### {pb['title']} [{pb['filename']}]")
                parts.append(content)

        if summary_playbooks:
            parts.append("\n## Additional Playbook Summaries (available for reference)")
            for pb in summary_playbooks:
                parts.append(f"- **{pb['title']}** ({pb['filename']}): {pb['summary'][:200]}")
                if pb.get("sections"):
                    parts.append(f"  Sections: {', '.join(pb['sections'][:8])}")

        if not full_playbooks and not summary_playbooks:
            parts.append("\n## General Knowledge Base")
            parts.append("26 playbooks loaded across KNOWLEDGE, REASONING, AGENT, and FOUNDATION domains.")
            parts.append("Ask about specific topics for targeted playbook context.")

        return "\n".join(parts)

    def list_loaded(self) -> str:
        """List all loaded playbooks with stats."""
        lines = [f"Loaded Playbooks: {len(self.playbooks)}/{sum(len(v) for v in TARGET_PLAYBOOKS.values())}"]
        lines.append(f"Playbook Directory: {self.pb_dir}")
        lines.append("")

        total_chars = 0
        for category in ["KNOWLEDGE", "REASONING", "AGENT", "FOUNDATION"]:
            cat_pbs = [(f, d) for f, d in self.playbooks.items() if d["category"] == category]
            if cat_pbs:
                lines.append(f"  {category} ({len(cat_pbs)}):")
                for filename, data in sorted(cat_pbs):
                    size_kb = data["char_count"] / 1024
                    total_chars += data["char_count"]
                    lines.append(f"    {filename} ({size_kb:.1f} KB) - {data['title'][:50]}")

        lines.append(f"\n  Total: {total_chars / 1024:.0f} KB across {len(self.playbooks)} playbooks")
        return "\n".join(lines)


# =============================================================================
# Sonnet Agent Core
# =============================================================================

class AnthropicClient:
    """Lightweight Anthropic API client using requests (no SDK dependency)."""

    API_URL = "https://api.anthropic.com/v1/messages"
    API_VERSION = "2023-06-01"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "x-api-key": api_key,
            "anthropic-version": self.API_VERSION,
            "content-type": "application/json",
        })

    def create_message(self, model: str, max_tokens: int,
                       system: list, messages: list) -> Dict:
        """Call the Messages API. Returns parsed response dict."""
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": messages,
        }

        resp = self.session.post(self.API_URL, json=payload, timeout=120)

        if resp.status_code != 200:
            error_body = resp.text
            try:
                error_json = resp.json()
                error_body = error_json.get("error", {}).get("message", resp.text)
            except Exception:
                pass
            raise RuntimeError(f"Anthropic API error ({resp.status_code}): {error_body}")

        return resp.json()


class SonnetAgent:
    """The main agent: Anthropic API + playbooks + persistence."""

    def __init__(self, api_key: str = None, db_path: str = DEFAULT_DB_PATH,
                 pb_dir: str = PLAYBOOKS_V2_DIR, model: str = "claude-sonnet-4-5-20250929"):
        if not HAS_REQUESTS:
            raise ValueError(
                "'requests' package not installed. Install with:\n"
                "  pip install requests"
            )

        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found. Set it via:\n"
                "  export ANTHROPIC_API_KEY='your-key-here'\n"
                "  or pass --api-key <key>"
            )

        self.client = AnthropicClient(api_key=self.api_key)
        self.model = model
        self.db = ConversationDB(db_path)
        self.loader = PlaybookLoader(pb_dir)
        self.current_session_id: Optional[str] = None

        # Load playbooks
        print(f"Loading playbooks from {pb_dir}...", file=sys.stderr)
        count = self.loader.load_all()
        print(f"  {count} playbooks loaded.", file=sys.stderr)

        # Cache playbook metadata in DB
        for filename, pb in self.loader.playbooks.items():
            self.db.cache_playbook(
                filename=filename,
                category=pb["category"],
                title=pb["title"],
                summary=pb["summary"],
                keywords=pb["keywords"],
                char_count=pb["char_count"],
                content_hash=pb["content_hash"],
            )

    def _build_system_prompt(self, query: str) -> str:
        """Build system prompt with relevant playbook context."""
        full_pbs, summary_pbs = self.loader.get_relevant_playbooks(query)
        context = self.loader.format_context(full_pbs, summary_pbs)

        playbook_names = [pb["filename"] for pb in full_pbs + summary_pbs]

        return SYSTEM_PROMPT.format(playbook_context=context), playbook_names

    def _build_messages(self, query: str, session_id: str = None) -> List[Dict]:
        """Build message array with conversation history."""
        messages = []

        if session_id:
            history = self.db.get_messages(session_id, limit=MAX_HISTORY_MESSAGES)
            for msg in history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"],
                })

        messages.append({"role": "user", "content": query})
        return messages

    def ask(self, query: str, session_name: str = None) -> str:
        """Send a query and get a response. Optionally within a named session."""
        # Resolve or create session
        session_id = None
        if session_name:
            session = self.db.get_session(session_name)
            if session:
                session_id = session["id"]
            else:
                session_id = self.db.create_session(session_name)

        # Build prompt with relevant playbooks
        system_prompt, playbooks_used = self._build_system_prompt(query)
        messages = self._build_messages(query, session_id)

        # Call Anthropic API
        try:
            response = self.client.create_message(
                model=self.model,
                max_tokens=8192,
                system=[{
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }],
                messages=messages,
            )
        except Exception as e:
            return f"API Error: {e}"

        assistant_text = response["content"][0]["text"]

        # Persist messages
        if session_id:
            self.db.add_message(session_id, "user", query, playbooks_used)
            self.db.add_message(session_id, "assistant", assistant_text, playbooks_used)

        # Usage stats
        usage = response.get("usage", {})
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        cache_read = usage.get("cache_read_input_tokens", 0)
        cache_create = usage.get("cache_creation_input_tokens", 0)

        stats = (
            f"\n--- Usage: {input_tokens} in / {output_tokens} out"
            f" | Cache: {cache_read} read, {cache_create} created"
            f" | Playbooks: {len(playbooks_used)} loaded ---"
        )

        return assistant_text + stats

    def chat(self, session_name: str = "default"):
        """Interactive chat mode with persistent session."""
        # Resolve or create session
        session = self.db.get_session(session_name)
        if session:
            session_id = session["id"]
            msg_count = self.db.get_message_count(session_id)
            print(f"Resuming session '{session_name}' ({msg_count} messages)")
        else:
            session_id = self.db.create_session(session_name)
            print(f"New session '{session_name}' created")

        self.current_session_id = session_id

        print(f"FORGE-AI Sonnet Agent v{VERSION} | Model: {self.model}")
        print(f"Playbooks: {len(self.loader.playbooks)} loaded")
        print(f"Database: {self.db.db_path}")
        print("Type 'quit' or 'exit' to end. Type '/help' for commands.\n")

        while True:
            try:
                user_input = input("You> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break

            if not user_input:
                continue

            # Handle chat commands
            if user_input.lower() in ("quit", "exit", "/quit", "/exit"):
                print("Session saved. Goodbye!")
                break

            if user_input.startswith("/"):
                self._handle_chat_command(user_input, session_id)
                continue

            # Get response
            system_prompt, playbooks_used = self._build_system_prompt(user_input)
            messages = self._build_messages(user_input, session_id)

            print("Thinking...", end="", flush=True)

            try:
                response = self.client.create_message(
                    model=self.model,
                    max_tokens=8192,
                    system=[{
                        "type": "text",
                        "text": system_prompt,
                        "cache_control": {"type": "ephemeral"},
                    }],
                    messages=messages,
                )
            except Exception as e:
                print(f"\rAPI Error: {e}")
                continue

            assistant_text = response["content"][0]["text"]

            # Persist
            self.db.add_message(session_id, "user", user_input, playbooks_used)
            self.db.add_message(session_id, "assistant", assistant_text, playbooks_used)

            # Display
            usage = response.get("usage", {})
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            cache_read = usage.get("cache_read_input_tokens", 0)
            print(f"\r{'':40}\r", end="")  # Clear "Thinking..."
            print(f"\nSonnet> {assistant_text}")
            print(f"\n  [{input_tokens} in / {output_tokens} out"
                  f" | cache: {cache_read} read"
                  f" | {len(playbooks_used)} playbooks]\n")

    def _handle_chat_command(self, cmd: str, session_id: str):
        """Handle slash commands in chat mode."""
        parts = cmd.split(maxsplit=1)
        command = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if command == "/help":
            print("""
Chat Commands:
  /help              Show this help
  /playbooks         List all loaded playbooks
  /relevant <topic>  Show which playbooks would load for a topic
  /history           Show conversation history
  /sessions          List all saved sessions
  /switch <name>     Switch to a different session
  /export [file]     Export current session to JSON
  /stats             Show session statistics
  /clear             Clear current session history
  /model             Show current model
  quit / exit        Save and exit
""")
        elif command == "/playbooks":
            print(self.loader.list_loaded())
        elif command == "/relevant":
            if not arg:
                print("Usage: /relevant <topic>")
                return
            full_pbs, summary_pbs = self.loader.get_relevant_playbooks(arg)
            print(f"Full context ({len(full_pbs)}):")
            for pb in full_pbs:
                print(f"  - {pb['filename']} ({pb['char_count']/1024:.1f} KB)")
            print(f"Summary context ({len(summary_pbs)}):")
            for pb in summary_pbs:
                print(f"  - {pb['filename']}")
        elif command == "/history":
            messages = self.db.get_messages(session_id, limit=10)
            for msg in messages:
                role = msg["role"].upper()
                content = msg["content"][:200]
                ts = msg["timestamp"][:19]
                print(f"  [{ts}] {role}: {content}...")
        elif command == "/sessions":
            sessions = self.db.list_sessions()
            if not sessions:
                print("  No sessions found.")
            for s in sessions:
                print(f"  {s['name']} (id:{s['id'][:8]}...) - {s['message_count']} msgs - {s['updated_at'][:19]}")
        elif command == "/switch":
            if not arg:
                print("Usage: /switch <session-name>")
                return
            session = self.db.get_session(arg)
            if session:
                self.current_session_id = session["id"]
                print(f"Switched to session '{arg}' ({session['message_count']} messages)")
            else:
                new_id = self.db.create_session(arg)
                self.current_session_id = new_id
                print(f"Created new session '{arg}'")
        elif command == "/export":
            export = self.db.export_session(session_id)
            if arg:
                with open(arg, "w") as f:
                    json.dump(export, f, indent=2)
                print(f"Session exported to {arg}")
            else:
                print(json.dumps(export, indent=2))
        elif command == "/stats":
            session = self.db.get_session_by_id(session_id)
            messages = self.db.get_messages(session_id, limit=1000)
            total_tokens = sum(m["token_estimate"] for m in messages)
            print(f"  Session: {session['name']} (id: {session['id'][:8]}...)")
            print(f"  Messages: {len(messages)}")
            print(f"  Token estimate: ~{total_tokens:,}")
            print(f"  Created: {session['created_at'][:19]}")
            print(f"  Updated: {session['updated_at'][:19]}")
            print(f"  Playbooks loaded: {len(self.loader.playbooks)}")
        elif command == "/clear":
            self.db.delete_session(session_id)
            new_id = self.db.create_session(session.get("name", "default") if (session := self.db.get_session_by_id(session_id)) else "default")
            self.current_session_id = new_id
            print("Session cleared. Fresh session started.")
        elif command == "/model":
            print(f"  Model: {self.model}")
        else:
            print(f"  Unknown command: {command}. Type /help for available commands.")


# =============================================================================
# CLI Entry Point
# =============================================================================

def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="sonnet-agent",
        description=f"{AGENT_NAME} v{VERSION} - Persistent Cross-Provider Expert",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single question
  python3 sonnet-agent.py --ask "How do I build a knowledge graph with Claude?"

  # Interactive chat (new session)
  python3 sonnet-agent.py --chat

  # Resume a named session
  python3 sonnet-agent.py --chat --context "my-kg-project"

  # Single question within a persistent session
  python3 sonnet-agent.py --ask "What about edge types?" --context "my-kg-project"

  # List all sessions
  python3 sonnet-agent.py --sessions

  # Export a session
  python3 sonnet-agent.py --export "my-kg-project" --output session.json

  # List loaded playbooks
  python3 sonnet-agent.py --playbooks

  # Show which playbooks are relevant to a topic
  python3 sonnet-agent.py --relevant "knowledge graph construction"

  # Use a different model
  python3 sonnet-agent.py --chat --model claude-sonnet-4-5-20250929

  # Custom playbook directory
  python3 sonnet-agent.py --chat --pb-dir /path/to/playbooks/

  # Delete a session
  python3 sonnet-agent.py --delete-session "old-session"

Environment:
  ANTHROPIC_API_KEY    Required. Your Anthropic API key.
  FORGE_AI_DB          Optional. Path to SQLite database (default: ~/.forge-ai/sonnet-agent.db)
  FORGE_AI_PB_DIR      Optional. Path to playbooks directory.
""",
    )

    # Mode selection (mutually exclusive)
    mode = parser.add_argument_group("Mode")
    mode.add_argument("--ask", type=str, metavar="QUESTION",
                      help="Ask a single question and get a response")
    mode.add_argument("--chat", action="store_true",
                      help="Start interactive chat mode")

    # Session management
    session = parser.add_argument_group("Session")
    session.add_argument("--context", type=str, metavar="NAME", default=None,
                         help="Named session for persistence (used with --ask or --chat)")
    session.add_argument("--sessions", action="store_true",
                         help="List all saved sessions")
    session.add_argument("--export", type=str, metavar="SESSION_NAME",
                         help="Export a session to JSON")
    session.add_argument("--delete-session", type=str, metavar="SESSION_NAME",
                         help="Delete a session and its history")

    # Playbook management
    pb = parser.add_argument_group("Playbooks")
    pb.add_argument("--playbooks", action="store_true",
                    help="List all loaded playbooks with stats")
    pb.add_argument("--relevant", type=str, metavar="TOPIC",
                    help="Show which playbooks are relevant to a topic")

    # Configuration
    config = parser.add_argument_group("Configuration")
    config.add_argument("--api-key", type=str, metavar="KEY",
                        help="Anthropic API key (overrides ANTHROPIC_API_KEY env)")
    config.add_argument("--model", type=str, default="claude-sonnet-4-5-20250929",
                        help="Model to use (default: claude-sonnet-4-5-20250929)")
    config.add_argument("--db-path", type=str,
                        default=os.environ.get("FORGE_AI_DB", DEFAULT_DB_PATH),
                        help="Path to SQLite database")
    config.add_argument("--pb-dir", type=str,
                        default=os.environ.get("FORGE_AI_PB_DIR", PLAYBOOKS_V2_DIR),
                        help="Path to playbooks directory")
    config.add_argument("--output", "-o", type=str, metavar="FILE",
                        help="Output file (for --export or --ask)")

    # Meta
    parser.add_argument("--version", action="version", version=f"{AGENT_NAME} v{VERSION}")

    return parser


def main():
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()

    # Handle info commands that don't need API key
    if args.sessions or args.playbooks or args.relevant or args.delete_session:
        # These may not need the API
        pass

    # --- Sessions list (no API needed) ---
    if args.sessions:
        db = ConversationDB(args.db_path)
        sessions = db.list_sessions()
        if not sessions:
            print("No sessions found.")
        else:
            print(f"{'Name':<25} {'ID':<12} {'Messages':>8} {'Last Updated':<20}")
            print("-" * 70)
            for s in sessions:
                print(f"{s['name']:<25} {s['id'][:10]:<12} {s['message_count']:>8} {s['updated_at'][:19]:<20}")
        db.close()
        return

    # --- Delete session (no API needed) ---
    if args.delete_session:
        db = ConversationDB(args.db_path)
        session = db.get_session(args.delete_session)
        if session:
            db.delete_session(session["id"])
            print(f"Deleted session '{args.delete_session}' ({session['message_count']} messages)")
        else:
            print(f"Session '{args.delete_session}' not found.")
        db.close()
        return

    # --- Playbook listing (needs loader but not API) ---
    if args.playbooks:
        loader = PlaybookLoader(args.pb_dir)
        count = loader.load_all()
        print(loader.list_loaded())
        return

    # --- Relevance check (needs loader but not API) ---
    if args.relevant:
        loader = PlaybookLoader(args.pb_dir)
        loader.load_all()
        full_pbs, summary_pbs = loader.get_relevant_playbooks(args.relevant)
        print(f"Topic: '{args.relevant}'\n")
        print(f"Full context ({len(full_pbs)}) - loaded in detail:")
        for pb in full_pbs:
            print(f"  [{pb['category']}] {pb['filename']} ({pb['char_count']/1024:.1f} KB)")
            print(f"    {pb['title']}")
        print(f"\nSummary context ({len(summary_pbs)}) - referenced:")
        for pb in summary_pbs:
            print(f"  [{pb['category']}] {pb['filename']}")
            print(f"    {pb['title']}")
        if not full_pbs and not summary_pbs:
            print("  No specific matches. Default playbooks would be used.")
        return

    # --- Export (needs DB but not API) ---
    if args.export:
        db = ConversationDB(args.db_path)
        session = db.get_session(args.export)
        if not session:
            print(f"Session '{args.export}' not found.")
            db.close()
            return
        export = db.export_session(session["id"])
        if args.output:
            with open(args.output, "w") as f:
                json.dump(export, f, indent=2)
            print(f"Exported to {args.output}")
        else:
            print(json.dumps(export, indent=2))
        db.close()
        return

    # --- Ask mode ---
    if args.ask:
        try:
            agent = SonnetAgent(
                api_key=args.api_key,
                db_path=args.db_path,
                pb_dir=args.pb_dir,
                model=args.model,
            )
        except ValueError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(1)

        result = agent.ask(args.ask, session_name=args.context)

        if args.output:
            with open(args.output, "w") as f:
                f.write(result)
            print(f"Response saved to {args.output}")
        else:
            print(result)

        agent.db.close()
        return

    # --- Chat mode ---
    if args.chat:
        try:
            agent = SonnetAgent(
                api_key=args.api_key,
                db_path=args.db_path,
                pb_dir=args.pb_dir,
                model=args.model,
            )
        except ValueError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(1)

        agent.chat(session_name=args.context or "default")
        agent.db.close()
        return

    # --- No mode specified: show help ---
    parser.print_help()


if __name__ == "__main__":
    main()

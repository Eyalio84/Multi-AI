#!/usr/bin/env python3
"""
Database Adapter — Unified Retrieval Layer

Auto-detects 3 KG SQLite schemas and normalizes to KGNode/KGEdge dataclasses.
Provides a uniform interface for querying any NLKE knowledge graph database.

Detected schemas:
  Schema 1 (standard):     claude-cookbook-kg.db — nodes(id, type, name, description)
                            edges(from_node, to_node, type, weight)
  Schema 2 (handbook_ext): handbooks-kg.db — nodes(id, type, name, description, source_handbook, category)
                            edges(source_id, target_id, relation_type, weight)
  Schema 3 (unified):      unified-complete.db — unified_nodes(node_id, node_type, name, description, intent_keywords)
                            unified_edges(source_node_id, target_node_id, edge_type, confidence)

Level 1 dependency — imports from config.py.

Created: February 8, 2026
"""

import os
import sqlite3
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple


# ============================================================================
# Normalized Data Models
# ============================================================================

@dataclass
class KGNode:
    """Normalized KG node across all schemas."""
    node_id: str
    name: str
    node_type: str
    description: str
    source_db: str = ""
    # Optional extended fields
    intent_keywords: str = ""
    category: str = ""
    source_handbook: str = ""
    domain: str = ""
    metadata: str = ""


@dataclass
class KGEdge:
    """Normalized KG edge across all schemas."""
    source_id: str
    target_id: str
    edge_type: str
    weight: float = 1.0
    source_db: str = ""


# ============================================================================
# Schema Detection
# ============================================================================

class SchemaType:
    """Known schema fingerprints."""
    STANDARD = "standard"         # claude-cookbook-kg: nodes(id, type, name, description)
    HANDBOOK_EXT = "handbook_ext" # handbooks-kg: nodes + source_handbook, category
    UNIFIED = "unified"           # unified-complete: unified_nodes(node_id, node_type, ...)
    UNKNOWN = "unknown"


def detect_schema(conn: sqlite3.Connection) -> str:
    """Auto-detect KG schema by inspecting table names and columns."""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {r[0] for r in cursor.fetchall()}

    # Schema 3: unified — uses unified_nodes table
    if "unified_nodes" in tables:
        return SchemaType.UNIFIED

    # Schema 1/2: both use 'nodes' table, differentiate by columns
    if "nodes" in tables:
        cursor.execute("PRAGMA table_info(nodes)")
        cols = {r[1] for r in cursor.fetchall()}
        if "source_handbook" in cols:
            return SchemaType.HANDBOOK_EXT
        return SchemaType.STANDARD

    return SchemaType.UNKNOWN


# ============================================================================
# Database Adapter
# ============================================================================

class KGAdapter:
    """Unified adapter for querying any NLKE KG database.

    Auto-detects schema and normalizes all results to KGNode/KGEdge.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.db_name = os.path.basename(db_path)
        self.schema: str = SchemaType.UNKNOWN
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self) -> bool:
        """Open connection and detect schema. Returns True if successful."""
        if not os.path.exists(self.db_path):
            return False
        try:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
            self.schema = detect_schema(self._conn)
            return self.schema != SchemaType.UNKNOWN
        except Exception:
            self._conn = None
            return False

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.close()

    # ------------------------------------------------------------------
    # Node queries
    # ------------------------------------------------------------------

    def get_all_nodes(self) -> List[KGNode]:
        """Retrieve all nodes from the database."""
        if not self._conn:
            return []

        cursor = self._conn.cursor()
        nodes = []

        if self.schema == SchemaType.STANDARD:
            cursor.execute("SELECT id, type, name, description, metadata FROM nodes")
            for r in cursor.fetchall():
                nodes.append(KGNode(
                    node_id=r["id"], name=r["name"] or "", node_type=r["type"] or "",
                    description=r["description"] or "", source_db=self.db_name,
                    metadata=r["metadata"] or "",
                ))

        elif self.schema == SchemaType.HANDBOOK_EXT:
            cursor.execute("SELECT id, type, name, description, source_handbook, category FROM nodes")
            for r in cursor.fetchall():
                nodes.append(KGNode(
                    node_id=r["id"], name=r["name"] or "", node_type=r["type"] or "",
                    description=r["description"] or "", source_db=self.db_name,
                    source_handbook=r["source_handbook"] or "",
                    category=r["category"] or "",
                ))

        elif self.schema == SchemaType.UNIFIED:
            cursor.execute("""
                SELECT node_id, node_type, name, description, intent_keywords, domain
                FROM unified_nodes
            """)
            for r in cursor.fetchall():
                nodes.append(KGNode(
                    node_id=r["node_id"], name=r["name"] or "",
                    node_type=r["node_type"] or "",
                    description=r["description"] or "", source_db=self.db_name,
                    intent_keywords=r["intent_keywords"] or "",
                    domain=r["domain"] or "",
                ))

        return nodes

    def search_nodes(self, keywords: List[str], limit: int = 20) -> List[KGNode]:
        """Search nodes by keyword LIKE matching on name + description."""
        if not self._conn or not keywords:
            return []

        cursor = self._conn.cursor()
        results = []
        seen_ids = set()

        for kw in keywords:
            pattern = f"%{kw}%"

            if self.schema == SchemaType.STANDARD:
                cursor.execute("""
                    SELECT id, type, name, description, metadata FROM nodes
                    WHERE LOWER(name) LIKE LOWER(?) OR LOWER(description) LIKE LOWER(?)
                    LIMIT ?
                """, (pattern, pattern, limit))
                for r in cursor.fetchall():
                    if r["id"] not in seen_ids:
                        seen_ids.add(r["id"])
                        results.append(KGNode(
                            node_id=r["id"], name=r["name"] or "",
                            node_type=r["type"] or "",
                            description=r["description"] or "",
                            source_db=self.db_name,
                            metadata=r["metadata"] or "",
                        ))

            elif self.schema == SchemaType.HANDBOOK_EXT:
                cursor.execute("""
                    SELECT id, type, name, description, source_handbook, category FROM nodes
                    WHERE LOWER(name) LIKE LOWER(?) OR LOWER(description) LIKE LOWER(?)
                    LIMIT ?
                """, (pattern, pattern, limit))
                for r in cursor.fetchall():
                    if r["id"] not in seen_ids:
                        seen_ids.add(r["id"])
                        results.append(KGNode(
                            node_id=r["id"], name=r["name"] or "",
                            node_type=r["type"] or "",
                            description=r["description"] or "",
                            source_db=self.db_name,
                            source_handbook=r["source_handbook"] or "",
                            category=r["category"] or "",
                        ))

            elif self.schema == SchemaType.UNIFIED:
                cursor.execute("""
                    SELECT node_id, node_type, name, description, intent_keywords, domain
                    FROM unified_nodes
                    WHERE LOWER(name) LIKE LOWER(?)
                       OR LOWER(description) LIKE LOWER(?)
                       OR LOWER(intent_keywords) LIKE LOWER(?)
                    LIMIT ?
                """, (pattern, pattern, pattern, limit))
                for r in cursor.fetchall():
                    if r["node_id"] not in seen_ids:
                        seen_ids.add(r["node_id"])
                        results.append(KGNode(
                            node_id=r["node_id"], name=r["name"] or "",
                            node_type=r["node_type"] or "",
                            description=r["description"] or "",
                            source_db=self.db_name,
                            intent_keywords=r["intent_keywords"] or "",
                            domain=r["domain"] or "",
                        ))

        return results[:limit]

    def get_node(self, node_id: str) -> Optional[KGNode]:
        """Get a single node by ID."""
        if not self._conn:
            return None

        cursor = self._conn.cursor()

        if self.schema == SchemaType.UNIFIED:
            cursor.execute("SELECT node_id, node_type, name, description, intent_keywords, domain FROM unified_nodes WHERE node_id = ?", (node_id,))
        else:
            cursor.execute("SELECT id, type, name, description FROM nodes WHERE id = ?", (node_id,))

        row = cursor.fetchone()
        if not row:
            return None

        if self.schema == SchemaType.UNIFIED:
            return KGNode(
                node_id=row["node_id"], name=row["name"] or "",
                node_type=row["node_type"] or "", description=row["description"] or "",
                source_db=self.db_name, intent_keywords=row["intent_keywords"] or "",
                domain=row["domain"] or "",
            )
        return KGNode(
            node_id=row["id"], name=row["name"] or "",
            node_type=row["type"] or "", description=row["description"] or "",
            source_db=self.db_name,
        )

    def node_count(self) -> int:
        """Count total nodes."""
        if not self._conn:
            return 0
        cursor = self._conn.cursor()
        table = "unified_nodes" if self.schema == SchemaType.UNIFIED else "nodes"
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        return cursor.fetchone()[0]

    # ------------------------------------------------------------------
    # Edge queries
    # ------------------------------------------------------------------

    def get_edges_for_node(self, node_id: str) -> List[KGEdge]:
        """Get all edges connected to a node (in either direction)."""
        if not self._conn:
            return []

        cursor = self._conn.cursor()
        edges = []

        if self.schema == SchemaType.STANDARD:
            cursor.execute("""
                SELECT from_node, to_node, type, weight FROM edges
                WHERE from_node = ? OR to_node = ?
            """, (node_id, node_id))
            for r in cursor.fetchall():
                edges.append(KGEdge(
                    source_id=r["from_node"], target_id=r["to_node"],
                    edge_type=r["type"] or "related_to",
                    weight=r["weight"] or 1.0, source_db=self.db_name,
                ))

        elif self.schema == SchemaType.HANDBOOK_EXT:
            cursor.execute("""
                SELECT source_id, target_id, relation_type, weight FROM edges
                WHERE source_id = ? OR target_id = ?
            """, (node_id, node_id))
            for r in cursor.fetchall():
                edges.append(KGEdge(
                    source_id=r["source_id"], target_id=r["target_id"],
                    edge_type=r["relation_type"] or "related_to",
                    weight=r["weight"] or 1.0, source_db=self.db_name,
                ))

        elif self.schema == SchemaType.UNIFIED:
            cursor.execute("""
                SELECT source_node_id, target_node_id, edge_type, confidence FROM unified_edges
                WHERE source_node_id = ? OR target_node_id = ?
            """, (node_id, node_id))
            for r in cursor.fetchall():
                edges.append(KGEdge(
                    source_id=r["source_node_id"], target_id=r["target_node_id"],
                    edge_type=r["edge_type"] or "related_to",
                    weight=r["confidence"] or 1.0, source_db=self.db_name,
                ))

        return edges

    def get_neighbors(self, node_id: str) -> List[str]:
        """Get IDs of all nodes connected to node_id."""
        edges = self.get_edges_for_node(node_id)
        neighbors = set()
        for e in edges:
            if e.source_id == node_id:
                neighbors.add(e.target_id)
            else:
                neighbors.add(e.source_id)
        return list(neighbors)

    def edge_count(self) -> int:
        """Count total edges."""
        if not self._conn:
            return 0
        cursor = self._conn.cursor()
        table = "unified_edges" if self.schema == SchemaType.UNIFIED else "edges"
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        return cursor.fetchone()[0]


# ============================================================================
# Self-test
# ============================================================================

if __name__ == "__main__":
    from config import KG_DATABASES

    print("db_adapter.py — Schema auto-detection test")
    print("=" * 60)

    total_nodes = 0
    total_edges = 0
    schemas_found = {}

    for name, path in KG_DATABASES.items():
        adapter = KGAdapter(path)
        if adapter.connect():
            nc = adapter.node_count()
            ec = adapter.edge_count()
            total_nodes += nc
            total_edges += ec
            schemas_found[adapter.schema] = schemas_found.get(adapter.schema, 0) + 1

            # Test search
            results = adapter.search_nodes(["prompt", "caching"], limit=3)
            result_names = [r.name for r in results]

            # Test edges for first result
            edge_count = 0
            if results:
                edges = adapter.get_edges_for_node(results[0].node_id)
                edge_count = len(edges)

            print(f"  {name:20s} schema={adapter.schema:12s} nodes={nc:5d} edges={ec:7d} search_hits={len(results)} first_edges={edge_count}")
            adapter.close()
        else:
            print(f"  {name:20s} NOT FOUND or unsupported")

    print(f"\nTotal: {total_nodes} nodes, {total_edges} edges")
    print(f"Schemas detected: {schemas_found}")
    assert total_nodes > 0, "Expected at least some nodes"
    print("\ndb_adapter.py OK")

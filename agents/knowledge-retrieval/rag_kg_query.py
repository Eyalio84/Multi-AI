#!/usr/bin/env python3
"""
RAG-KG Hybrid Query Agent

Graph-RAG system combining KG traversal (SQLite) with document
retrieval (text search) for context-enriched answers.

Layer: L1-L5 (Full 5-layer pattern via agent_base)

Usage:
    python3 rag_kg_query.py --example
    python3 rag_kg_query.py --workload query.json --summary

Created: February 6, 2026
"""

import sys
import os
import sqlite3
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.agent_base import (
    AgentInput, AgentOutput, BaseAnalyzer, run_standard_cli,
    KG_DATABASES, NLKE_ROOT, AILAB_HANDBOOKS,
)
from shared.retrieval import HybridFusion, tokenize_and_filter

from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any, Optional
from pathlib import Path


# ============================================================================
# L1: Data Models
# ============================================================================

@dataclass
class KGResult:
    source_db: str
    node_id: str
    node_name: str
    node_type: str
    description: str
    relevance: float
    connected_edges: int

@dataclass
class DocResult:
    source_file: str
    line_number: int
    text: str
    relevance: float
    context: str


# ============================================================================
# L2: Constants
# ============================================================================

HANDBOOK_DIR = AILAB_HANDBOOKS
DOC_DIRS = [
    NLKE_ROOT,
    HANDBOOK_DIR,
]


# ============================================================================
# L3: Analyzer
# ============================================================================

class RAGKGQueryAnalyzer(BaseAnalyzer):
    """Graph-RAG hybrid query engine with unified retrieval layer."""

    def __init__(self):
        super().__init__(
            agent_name="rag-kg-query",
            model="sonnet",
            version="2.0",
        )
        self.fusion = HybridFusion()
        self._fusion_indexed = False

    def get_example_input(self) -> Dict[str, Any]:
        return {
            "name": "RAG-KG Query Demo",
            "query": "How does prompt caching work with batch API for cost optimization?",
            "kg_limit": 10,
            "doc_limit": 5,
            "include_edges": True,
        }

    def _query_kg(self, db_path: str, keywords: List[str], limit: int) -> List[KGResult]:
        """Query a single KG database."""
        results = []
        if not os.path.exists(db_path):
            return results

        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Check if nodes table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='nodes'")
            if not cursor.fetchone():
                conn.close()
                return results

            db_name = os.path.basename(db_path)

            for keyword in keywords:
                pattern = f"%{keyword}%"
                cursor.execute("""
                    SELECT id, name, type, description FROM nodes
                    WHERE LOWER(name) LIKE LOWER(?) OR LOWER(description) LIKE LOWER(?)
                    LIMIT ?
                """, (pattern, pattern, limit))

                for row in cursor.fetchall():
                    # Count connected edges
                    cursor.execute("""
                        SELECT COUNT(*) FROM edges
                        WHERE from_node = ? OR to_node = ?
                    """, (row["id"], row["id"]))
                    edge_count = cursor.fetchone()[0]

                    # Relevance: more keyword matches = higher
                    desc = (row["description"] or "").lower()
                    name = (row["name"] or "").lower()
                    keyword_hits = sum(1 for kw in keywords if kw in name or kw in desc)
                    relevance = min(1.0, keyword_hits / max(1, len(keywords)) + 0.3)

                    results.append(KGResult(
                        source_db=db_name,
                        node_id=row["id"],
                        node_name=row["name"],
                        node_type=row["type"],
                        description=(row["description"] or "")[:300],
                        relevance=round(relevance, 2),
                        connected_edges=edge_count,
                    ))

            conn.close()
        except Exception:
            pass

        # Dedupe by node_id
        seen = set()
        unique = []
        for r in results:
            if r.node_id not in seen:
                seen.add(r.node_id)
                unique.append(r)
        return sorted(unique, key=lambda r: r.relevance, reverse=True)[:limit]

    def _search_docs(self, keywords: List[str], limit: int) -> List[DocResult]:
        """Search document corpus for keyword matches."""
        results = []

        for doc_dir in DOC_DIRS:
            if not os.path.exists(doc_dir):
                continue
            for md_path in Path(doc_dir).rglob("*.md"):
                try:
                    text = md_path.read_text(errors="replace")
                    lines = text.split("\n")
                    for i, line in enumerate(lines):
                        line_lower = line.lower()
                        hits = sum(1 for kw in keywords if kw in line_lower)
                        if hits >= 2 or (hits >= 1 and len(line) > 50):
                            context_start = max(0, i - 1)
                            context_end = min(len(lines), i + 2)
                            context = "\n".join(lines[context_start:context_end])
                            relevance = min(1.0, hits / max(1, len(keywords)) + 0.2)

                            results.append(DocResult(
                                source_file=str(md_path.relative_to(doc_dir) if doc_dir in str(md_path) else md_path.name),
                                line_number=i + 1,
                                text=line[:200],
                                relevance=round(relevance, 2),
                                context=context[:400],
                            ))
                except Exception:
                    pass

            # Also search .txt handbooks
            for txt_path in Path(doc_dir).rglob("*.txt"):
                try:
                    text = txt_path.read_text(errors="replace")
                    lines = text.split("\n")
                    for i, line in enumerate(lines):
                        line_lower = line.lower()
                        hits = sum(1 for kw in keywords if kw in line_lower)
                        if hits >= 2:
                            context_start = max(0, i - 1)
                            context_end = min(len(lines), i + 2)
                            context = "\n".join(lines[context_start:context_end])

                            results.append(DocResult(
                                source_file=txt_path.name,
                                line_number=i + 1,
                                text=line[:200],
                                relevance=round(min(1.0, hits / max(1, len(keywords))), 2),
                                context=context[:400],
                            ))
                except Exception:
                    pass

        results.sort(key=lambda r: r.relevance, reverse=True)
        return results[:limit]

    def analyze(self, agent_input: AgentInput) -> AgentOutput:
        w = agent_input.workload
        query = w.get("query", "")
        kg_limit = w.get("kg_limit", 10)
        doc_limit = w.get("doc_limit", 5)

        rules = [
            "rag_001_keyword_extraction",
            "rag_002_kg_traversal",
            "rag_003_document_retrieval",
            "rag_004_result_fusion",
            "rag_005_hybrid_fusion",
        ]

        # Lazy-index the fusion engine
        if not self._fusion_indexed:
            self.fusion.index()
            self._fusion_indexed = True

        # Extract keywords using unified stopwords
        keywords = tokenize_and_filter(query)

        # Hybrid fusion query (vector + BM25 + graph)
        fusion_results = self.fusion.query(query, k=kg_limit)
        dbs_queried = len(set(r.source_db for r in fusion_results))

        # Convert fusion results to KGResult format
        kg_results = []
        for r in fusion_results:
            kg_results.append(KGResult(
                source_db=r.source_db,
                node_id=r.node_id,
                node_name=r.name,
                node_type=r.node_type,
                description=r.description[:300],
                relevance=round(r.final_score, 2),
                connected_edges=0,  # Not tracked in fusion results
            ))

        # Document search (kept as-is, not part of KG fusion)
        doc_results = self._search_docs(keywords, doc_limit)

        recommendations = [{
            "technique": "rag_kg_hybrid_query",
            "applicable": True,
            "query": query,
            "keywords": keywords,
            "kg_results": [asdict(r) for r in kg_results],
            "doc_results": [asdict(r) for r in doc_results],
            "dbs_queried": dbs_queried,
            "total_kg_hits": len(kg_results),
            "total_doc_hits": len(doc_results),
            "rules_applied": rules,
            "fusion_method": "hybrid (vector + BM25 + graph)",
        }]

        anti_patterns = []
        if not kg_results and not doc_results:
            anti_patterns.append("No results found - try different query terms")

        meta_insight = (
            f"Query '{query[:50]}...' found {len(kg_results)} KG nodes "
            f"across {dbs_queried} databases and {len(doc_results)} document matches "
            f"using hybrid fusion (vector + BM25 + graph)."
        )

        return AgentOutput(
            recommendations=recommendations,
            rules_applied=rules,
            meta_insight=meta_insight,
            analysis_data={
                "query": query,
                "keywords": keywords,
                "kg_hits": len(kg_results),
                "doc_hits": len(doc_results),
                "dbs_queried": dbs_queried,
                "fusion_cache": self.fusion.cache.metrics.to_dict(),
            },
            anti_patterns=anti_patterns,
            agent_metadata=self.build_metadata(),
        )


if __name__ == "__main__":
    analyzer = RAGKGQueryAnalyzer()
    run_standard_cli(
        agent_name="RAG-KG Hybrid Query",
        description="Graph-RAG combining KG traversal with document retrieval",
        analyzer=analyzer,
    )

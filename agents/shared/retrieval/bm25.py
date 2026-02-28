#!/usr/bin/env python3
"""
BM25 Scoring Engine — Unified Retrieval Layer

Best-of-3 BM25 implementation merged from:
  - hybrid_query.py inverted index + BM25 scoring
  - enhanced_query.py BM25Index class
  - hybrid_retriever.py BM25 class

Features:
  - Inverted index with TF tracking per node
  - IDF with log-smoothing
  - Intent keyword 5x boosting
  - Score normalization to [0, 1]

Level 2 dependency — imports from stopwords.py, db_adapter.py.

Created: February 8, 2026
"""

import math
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Set

try:
    from .stopwords import tokenize_and_filter
    from .db_adapter import KGAdapter, KGNode
except ImportError:
    from stopwords import tokenize_and_filter
    from db_adapter import KGAdapter, KGNode


# ============================================================================
# BM25 Index
# ============================================================================

class BM25Index:
    """Inverted index BM25 scorer for KG nodes.

    Indexes node name + description text, computes IDF,
    and scores queries using Okapi BM25 with optional intent boosting.

    Adapted from hybrid_query.py (lines 206-233) and enhanced_query.py (118-179).
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75, boost_factor: float = 5.0):
        self.k1 = k1
        self.b = b
        self.boost_factor = boost_factor

        # Index structures
        self.inverted_index: Dict[str, List[Tuple[str, int]]] = defaultdict(list)  # term -> [(node_id, tf)]
        self.doc_freq: Dict[str, int] = defaultdict(int)  # term -> document frequency
        self.doc_lengths: Dict[str, int] = {}  # node_id -> total tokens
        self.total_docs: int = 0
        self.avg_dl: float = 0.0

        # Node data reference
        self.node_tokens: Dict[str, List[str]] = {}   # node_id -> token list
        self.intent_keywords: Dict[str, Set[str]] = {}  # node_id -> intent keyword set

        self._indexed = False

    def index_nodes(self, nodes: List[KGNode]) -> int:
        """Build inverted index from a list of KGNodes.

        Returns number of nodes indexed.
        """
        self.inverted_index.clear()
        self.doc_freq.clear()
        self.doc_lengths.clear()
        self.node_tokens.clear()
        self.intent_keywords.clear()

        for node in nodes:
            # Combine name + description for indexing
            text = f"{node.name} {node.description}"
            tokens = tokenize_and_filter(text, min_length=2)

            if not tokens:
                continue

            self.node_tokens[node.node_id] = tokens
            self.doc_lengths[node.node_id] = len(tokens)

            # Store intent keywords for boosting
            if node.intent_keywords:
                kw_tokens = tokenize_and_filter(node.intent_keywords, min_length=2)
                self.intent_keywords[node.node_id] = set(kw_tokens)

            # Build TF per term
            term_freq: Dict[str, int] = defaultdict(int)
            for token in tokens:
                term_freq[token] += 1

            # Update inverted index and doc freq
            for term, tf in term_freq.items():
                self.inverted_index[term].append((node.node_id, tf))
                self.doc_freq[term] += 1

        self.total_docs = len(self.doc_lengths)
        self.avg_dl = (sum(self.doc_lengths.values()) / self.total_docs) if self.total_docs > 0 else 1.0
        self._indexed = True

        return self.total_docs

    def index_from_adapter(self, adapter: KGAdapter) -> int:
        """Index all nodes from a database adapter.

        Returns number of nodes indexed.
        """
        nodes = adapter.get_all_nodes()
        return self.index_nodes(nodes)

    def score(self, query_tokens: List[str], node_id: str) -> float:
        """Calculate BM25 score for a single node against query tokens.

        From hybrid_query.py lines 206-233.
        """
        if node_id not in self.doc_lengths:
            return 0.0

        score = 0.0
        dl = self.doc_lengths[node_id]

        for term in query_tokens:
            if term not in self.inverted_index:
                continue

            # Find TF for this node
            tf = 0
            for nid, freq in self.inverted_index[term]:
                if nid == node_id:
                    tf = freq
                    break

            if tf == 0:
                continue

            # IDF: log((N - df + 0.5) / (df + 0.5) + 1)
            df = self.doc_freq.get(term, 1)
            idf = math.log((self.total_docs - df + 0.5) / (df + 0.5) + 1)

            # BM25 TF normalization
            tf_norm = (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * dl / self.avg_dl))

            # Intent keyword boost (5x from contextual_embeddings.py line 178)
            boost = 1.0
            if node_id in self.intent_keywords and term in self.intent_keywords[node_id]:
                boost = self.boost_factor

            score += idf * tf_norm * boost

        return score

    def search(self, query: str, k: int = 10) -> List[Tuple[str, float]]:
        """Search index and return top-k (node_id, normalized_score) pairs.

        Scores are normalized to [0, 1].
        """
        if not self._indexed or self.total_docs == 0:
            return []

        tokens = tokenize_and_filter(query, min_length=2)
        if not tokens:
            return []

        # Score all indexed nodes
        scores = []
        for node_id in self.doc_lengths:
            s = self.score(tokens, node_id)
            if s > 0:
                scores.append((node_id, s))

        if not scores:
            return []

        # Normalize to [0, 1]
        max_score = max(s for _, s in scores)
        if max_score > 0:
            scores = [(nid, s / max_score) for nid, s in scores]

        scores.sort(key=lambda x: -x[1])
        return scores[:k]

    @property
    def vocabulary_size(self) -> int:
        return len(self.inverted_index)


# ============================================================================
# Self-test
# ============================================================================

if __name__ == "__main__":
    from config import KG_DATABASES
    from db_adapter import KGAdapter

    print("bm25.py — BM25 Index self-test")
    print("=" * 60)

    bm25 = BM25Index(k1=1.5, b=0.75)

    # Test with claude-cookbook KG
    db_path = KG_DATABASES["claude_cookbook"]
    adapter = KGAdapter(db_path)
    if adapter.connect():
        count = bm25.index_from_adapter(adapter)
        print(f"Indexed {count} nodes from claude-cookbook-kg.db")
        print(f"  Vocabulary: {bm25.vocabulary_size} terms")
        print(f"  Avg doc length: {bm25.avg_dl:.1f} tokens")

        # Test search
        results = bm25.search("prompt caching cost optimization", k=5)
        print(f"\nSearch 'prompt caching cost optimization':")
        for nid, score in results:
            node = adapter.get_node(nid)
            name = node.name if node else nid
            print(f"  {score:.3f}  {name}")

        results2 = bm25.search("batch API processing", k=5)
        print(f"\nSearch 'batch API processing':")
        for nid, score in results2:
            node = adapter.get_node(nid)
            name = node.name if node else nid
            print(f"  {score:.3f}  {name}")

        adapter.close()
    else:
        print("  claude-cookbook-kg.db not found, skipping")

    # Test with unified KG (has intent_keywords)
    unified_path = KG_DATABASES.get("unified_77")
    if unified_path:
        adapter2 = KGAdapter(unified_path)
        if adapter2.connect():
            bm25_u = BM25Index()
            count2 = bm25_u.index_from_adapter(adapter2)
            results3 = bm25_u.search("prompt caching", k=3)
            print(f"\nUnified KG: indexed {count2} nodes, search returned {len(results3)} results")
            intent_count = sum(1 for v in bm25_u.intent_keywords.values() if v)
            print(f"  Nodes with intent keywords: {intent_count}")
            adapter2.close()

    print("\nbm25.py OK")

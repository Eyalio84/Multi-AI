#!/usr/bin/env python3
"""
Graph Proximity Scorer — Unified Retrieval Layer

Graph-based scoring using neighbor boosting and BFS path finding.
Adapted from:
  - hybrid_query.py graph neighbor boosting (lines 305-314)
  - intent_query.py BFS path finding (lines 487-515)
  - contextual_embeddings.py bidirectional neighbor index (lines 511-528)

Level 2 dependency — imports from config.py, db_adapter.py.

Created: February 8, 2026
"""

from collections import defaultdict, deque
from typing import Dict, List, Set, Optional, Tuple

try:
    from .config import EDGE_WEIGHTS, RetrievalConfig
    from .db_adapter import KGAdapter, KGEdge
except ImportError:
    from config import EDGE_WEIGHTS, RetrievalConfig
    from db_adapter import KGAdapter, KGEdge


# ============================================================================
# Graph Scorer
# ============================================================================

class GraphScorer:
    """Graph proximity scoring for KG retrieval.

    Provides:
        - Neighbor boosting: nodes connected to top results get boosted
        - BFS path finding: find shortest path between two nodes
        - Bidirectional neighbor index for fast lookups

    Adapted from hybrid_query.py lines 305-314 and intent_query.py lines 487-515.
    """

    def __init__(self, config: Optional[RetrievalConfig] = None):
        self.config = config or RetrievalConfig()
        # Bidirectional neighbor index: node_id -> set of (neighbor_id, edge_type, weight)
        self.neighbors: Dict[str, Set[Tuple[str, str, float]]] = defaultdict(set)
        # Simple neighbor ID sets for fast lookup
        self.neighbor_ids: Dict[str, Set[str]] = defaultdict(set)
        self._indexed = False

    def build_index(self, adapter: KGAdapter) -> int:
        """Build bidirectional neighbor index from a KG database.

        Returns number of edges indexed.
        """
        self.neighbors.clear()
        self.neighbor_ids.clear()

        nodes = adapter.get_all_nodes()
        edge_count = 0

        for node in nodes:
            edges = adapter.get_edges_for_node(node.node_id)
            for edge in edges:
                weight = EDGE_WEIGHTS.get(edge.edge_type, 0.5) * edge.weight

                # Bidirectional
                self.neighbors[edge.source_id].add((edge.target_id, edge.edge_type, weight))
                self.neighbors[edge.target_id].add((edge.source_id, edge.edge_type, weight))

                self.neighbor_ids[edge.source_id].add(edge.target_id)
                self.neighbor_ids[edge.target_id].add(edge.source_id)

                edge_count += 1

        self._indexed = True
        return edge_count

    def build_index_fast(self, adapter: KGAdapter) -> int:
        """Build neighbor index using only node IDs that appear in search results.

        Faster than full build — only indexes edges for specific nodes.
        For use when indexing the full graph would be too slow (600K+ edges).
        """
        self.neighbors.clear()
        self.neighbor_ids.clear()

        # For large graphs, just build the simple neighbor_ids map
        # by querying edges table directly
        if not adapter._conn:
            return 0

        cursor = adapter._conn.cursor()
        edge_count = 0

        if adapter.schema == "unified":
            cursor.execute("SELECT source_node_id, target_node_id, edge_type, confidence FROM unified_edges")
            for row in cursor.fetchall():
                src, tgt = row[0], row[1]
                self.neighbor_ids[src].add(tgt)
                self.neighbor_ids[tgt].add(src)
                edge_count += 1
        elif adapter.schema == "standard":
            cursor.execute("SELECT from_node, to_node, type, weight FROM edges")
            for row in cursor.fetchall():
                src, tgt = row[0], row[1]
                self.neighbor_ids[src].add(tgt)
                self.neighbor_ids[tgt].add(src)
                edge_count += 1
        elif adapter.schema == "handbook_ext":
            cursor.execute("SELECT source_id, target_id, relation_type, weight FROM edges")
            for row in cursor.fetchall():
                src, tgt = row[0], row[1]
                self.neighbor_ids[src].add(tgt)
                self.neighbor_ids[tgt].add(src)
                edge_count += 1

        self._indexed = True
        return edge_count

    def neighbor_boost(self, node_id: str, top_result_ids: Set[str],
                       gamma: float = 0.15, max_hits: int = 3) -> float:
        """Calculate neighbor proximity boost for a node.

        bonus = gamma * min(hits, max_hits) / max_hits

        A node gets boosted if its neighbors appear in the top results.
        From hybrid_query.py lines 305-314.

        Args:
            node_id: Node to calculate boost for
            top_result_ids: Set of node IDs in top results
            gamma: Graph weight from fusion formula
            max_hits: Cap for neighbor hits

        Returns:
            Boost value in [0, gamma]
        """
        if node_id not in self.neighbor_ids:
            return 0.0

        hits = len(top_result_ids & self.neighbor_ids[node_id])
        if hits == 0:
            return 0.0

        return gamma * min(hits, max_hits) / max_hits

    def score_results(self, candidate_ids: List[str], gamma: float = 0.15) -> Dict[str, float]:
        """Score all candidates with neighbor boosting.

        The top 1/3 of candidates (by position) form the "top set".
        Other candidates get boosted if connected to top set members.

        Args:
            candidate_ids: Ordered list of candidate node IDs (best first)
            gamma: Graph weight for boost calculation

        Returns:
            Dict of node_id -> graph boost score
        """
        if not candidate_ids or not self._indexed:
            return {}

        # Top 1/3 form the reference set
        top_count = max(1, len(candidate_ids) // 3)
        top_set = set(candidate_ids[:top_count])

        scores = {}
        for nid in candidate_ids:
            scores[nid] = self.neighbor_boost(nid, top_set, gamma)

        return scores

    def bfs_path(self, start_id: str, end_id: str, max_depth: int = 4) -> Optional[List[str]]:
        """Find shortest path between two nodes via BFS.

        From intent_query.py lines 487-515.

        Args:
            start_id: Starting node ID
            end_id: Target node ID
            max_depth: Maximum BFS depth

        Returns:
            List of node IDs in path, or None if no path found
        """
        if start_id == end_id:
            return [start_id]

        if start_id not in self.neighbor_ids or end_id not in self.neighbor_ids:
            return None

        visited = {start_id}
        queue = deque([(start_id, [start_id])])

        while queue:
            current, path = queue.popleft()

            if len(path) > max_depth:
                break

            for neighbor in self.neighbor_ids.get(current, set()):
                if neighbor == end_id:
                    return path + [neighbor]

                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return None

    def get_neighbors(self, node_id: str) -> Set[str]:
        """Get direct neighbor IDs for a node."""
        return self.neighbor_ids.get(node_id, set())

    @property
    def indexed_nodes(self) -> int:
        return len(self.neighbor_ids)


# ============================================================================
# Self-test
# ============================================================================

if __name__ == "__main__":
    from config import KG_DATABASES
    from db_adapter import KGAdapter

    print("graph_scorer.py — Graph Scorer self-test")
    print("=" * 60)

    scorer = GraphScorer()

    # Test with claude-cookbook (small, 562 edges)
    db_path = KG_DATABASES["claude_cookbook"]
    adapter = KGAdapter(db_path)
    if adapter.connect():
        edge_count = scorer.build_index(adapter)
        print(f"Indexed {edge_count} edges from claude-cookbook-kg.db")
        print(f"  Nodes with neighbors: {scorer.indexed_nodes}")

        # Test neighbor lookup
        nodes = adapter.search_nodes(["prompt"], limit=3)
        if nodes:
            test_node = nodes[0]
            nbrs = scorer.get_neighbors(test_node.node_id)
            print(f"\n  Node '{test_node.name}' has {len(nbrs)} neighbors")

            # Test BFS
            if len(nodes) >= 2:
                path = scorer.bfs_path(nodes[0].node_id, nodes[1].node_id)
                if path:
                    print(f"  Path from '{nodes[0].name}' to '{nodes[1].name}': {len(path)} hops")
                else:
                    print(f"  No path found between '{nodes[0].name}' and '{nodes[1].name}'")

            # Test neighbor boosting
            all_nodes = adapter.get_all_nodes()
            candidate_ids = [n.node_id for n in all_nodes[:20]]
            scores = scorer.score_results(candidate_ids, gamma=0.15)
            boosted = sum(1 for v in scores.values() if v > 0)
            print(f"\n  Boosted {boosted}/{len(candidate_ids)} candidates")

        adapter.close()

    # Test with unified (large, 677K edges) — use fast index
    unified_path = KG_DATABASES.get("unified_77")
    if unified_path:
        adapter2 = KGAdapter(unified_path)
        if adapter2.connect():
            import time
            t0 = time.time()
            edge_count2 = scorer.build_index_fast(adapter2)
            t1 = time.time()
            print(f"\nUnified KG: indexed {edge_count2} edges in {t1-t0:.2f}s (fast mode)")
            print(f"  Nodes with neighbors: {scorer.indexed_nodes}")
            adapter2.close()

    print("\ngraph_scorer.py OK")

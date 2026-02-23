"""KG-OS Query Engine — 12 ported methods from Flags Toolkit for intent-driven KG retrieval.

Sits between raw KG storage (kg_service, embedding_service) and the agentic loop.
Provides: intent classification, composition planning, impact analysis, dimension filtering,
Jaccard similarity, BFS traversal, edge-type boosting, and the 4-weight scoring formula.
"""
import re
import json
import sqlite3
import math
import logging
from typing import Any
from collections import defaultdict

logger = logging.getLogger(__name__)

# ── 14 Intent Categories ────────────────────────────────────────────
INTENT_PATTERNS = {
    "find_tool": [
        r"\b(find|search|look\s?for|discover|locate|get)\b.*\b(tool|command|function|method|utility)\b",
        r"\bhow\s+(do|can|to)\b.*\b(i|we)\b",
    ],
    "check_capability": [
        r"\bcan\s+\w+\s+(handle|support|do|process|work|manage|read|write|edit)\b",
        r"\bcan\s+(it|this|the)\b", r"\bdoes\s+(it|this)\b.*\bsupport\b",
        r"\bis\s+(it|this)\b.*\b(able|capable|possible)\b",
    ],
    "compose_workflow": [
        r"\b(workflow|pipeline|chain|sequence|steps|combine|compose|orchestrat)\b",
        r"\bhow\s+to\s+.*\band\s+.*\bthen\b",
    ],
    "compare": [
        r"\b(compare|versus|vs|difference|better|worse|alternative)\b",
        r"\bwhich\s+(is|one|should)\b",
    ],
    "debug": [
        r"\b(debug|error|fail|crash|broken|fix|issue|problem|trouble|wrong)\b",
        r"\bnot\s+work(ing)?\b", r"\bdoesn'?t\s+work\b",
    ],
    "optimize": [
        r"\b(optimiz|improv|faster|speed|performance|efficien|reduc|cost|cheap|save)\b",
    ],
    "learn": [
        r"\b(learn|understand|explain|what\s+is|how\s+does|tutorial|guide|intro)\b",
        r"\btell\s+me\s+about\b",
    ],
    "explore": [
        r"\b(explor|browse|list|show|overview|summary|all|everything)\b",
    ],
    "impact": [
        r"\b(impact|affect|depend\w*|downstream|upstream|consequence|ripple|breaking)\b",
        r"\bwhat\s+(depends|relies)\b",
    ],
    "trace": [
        r"\b(trace|path|connect|relation|link|between|from.*to)\b",
    ],
    "recommend": [
        r"\b(recommend|suggest|best|should\s+i|advise|guidance)\b",
    ],
    "create": [
        r"\b(create|build|make|generate|new|add|implement|develop|write)\b",
    ],
    "configure": [
        r"\b(config|setup|install|deploy|setting|environment|initialize)\b",
    ],
    "security": [
        r"\b(secur\w*|auth\w*|permission|access\s+control|encrypt\w*|credential|token|api\s*key)\b",
    ],
}


class KGOSQueryEngine:
    """12 query methods from Flags Toolkit, adapted for any KG via kg_service profiles."""

    def __init__(self):
        self._intent_cache: dict[str, str] = {}

    # ══════════════════════════════════════════════════════════════════
    # PUBLIC: Master search — orchestrates all strategies
    # ══════════════════════════════════════════════════════════════════

    def intent_search(
        self,
        db_id: str,
        query: str,
        alpha: float = 0.35,
        beta: float = 0.40,
        gamma: float = 0.15,
        delta: float = 0.10,
        limit: int = 10,
        methods: list[str] | None = None,
    ) -> dict:
        """Master KG-OS search combining embedding, text, graph, and intent strategies.

        The 4-weight formula: score = alpha*emb + beta*text + gamma*graph + delta*intent
        """
        from services.embedding_service import embedding_service

        active_methods = methods or ["hybrid", "intent"]

        # Embedding + text scores (via existing hybrid search)
        emb_scores: dict[str, float] = {}
        text_scores: dict[str, float] = {}
        graph_scores: dict[str, float] = {}
        intent_scores: dict[str, float] = {}

        if "hybrid" in active_methods or "embedding" in active_methods:
            emb_scores = self._get_embedding_scores(db_id, query, limit * 3)

        if "hybrid" in active_methods or "text" in active_methods:
            text_scores = self._get_text_scores(db_id, query)

        if "hybrid" in active_methods or "graph" in active_methods:
            seed_ids = set(
                sorted(text_scores, key=text_scores.get, reverse=True)[:10]
            ) | set(
                sorted(emb_scores, key=emb_scores.get, reverse=True)[:10]
            )
            graph_scores = self._get_graph_boost_scores(db_id, seed_ids)

        if "intent" in active_methods and delta > 0:
            intent = self.classify_intent(query)
            intent_results = self._intent_score_nodes(db_id, query, intent)
            intent_scores = intent_results

        # Combine with 4-weight formula
        all_ids = set(emb_scores) | set(text_scores) | set(graph_scores) | set(intent_scores)
        final: dict[str, float] = {}
        for nid in all_ids:
            score = (
                alpha * emb_scores.get(nid, 0.0)
                + beta * text_scores.get(nid, 0.0)
                + gamma * graph_scores.get(nid, 0.0)
                + delta * intent_scores.get(nid, 0.0)
            )
            if score > 0:
                final[nid] = score

        sorted_ids = sorted(final, key=final.get, reverse=True)[:limit]

        # Fetch node details
        from services.kg_service import kg_service
        results = []
        for nid in sorted_ids:
            node = kg_service.get_node(db_id, nid)
            if node:
                method_parts = []
                if nid in emb_scores:
                    method_parts.append("embedding")
                if nid in text_scores:
                    method_parts.append("text")
                if nid in graph_scores:
                    method_parts.append("graph")
                if nid in intent_scores:
                    method_parts.append("intent")
                results.append({
                    "node": node,
                    "score": round(final[nid], 4),
                    "method": "+".join(method_parts),
                    "scores": {
                        "embedding": round(emb_scores.get(nid, 0.0), 4),
                        "text": round(text_scores.get(nid, 0.0), 4),
                        "graph": round(graph_scores.get(nid, 0.0), 4),
                        "intent": round(intent_scores.get(nid, 0.0), 4),
                    },
                })

        return {
            "results": results,
            "query": query,
            "intent": self.classify_intent(query),
            "weights": {"alpha": alpha, "beta": beta, "gamma": gamma, "delta": delta},
            "total": len(results),
        }

    # ══════════════════════════════════════════════════════════════════
    # PUBLIC: want_to — goal-based tool/node discovery
    # ══════════════════════════════════════════════════════════════════

    def want_to(self, db_id: str, goal: str, k: int = 10) -> dict:
        """Find nodes that help achieve a goal. Keyword match + FTS + edge-type boosting."""
        from services.kg_service import kg_service

        # Extract goal keywords (verb + object patterns)
        keywords = self._extract_goal_keywords(goal)

        # Text matching
        text_hits = self._keyword_match_nodes(db_id, goal)

        # Boost nodes connected via goal-relevant edge types
        goal_edge_types = [
            "enables", "supports", "implements", "provides", "solves",
            "feeds_into", "used_for", "helps_with", "applies_to",
        ]
        if text_hits:
            seed_ids = set(list(text_hits.keys())[:10])
            edge_boost = self._edge_type_boost(db_id, seed_ids, goal_edge_types)
            for nid, score in edge_boost.items():
                text_hits[nid] = text_hits.get(nid, 0) + score * 0.5
        # Also boost via keyword-matched neighbors
        for kw in keywords[:3]:
            kw_hits = self._keyword_match_nodes(db_id, kw)
            for nid, score in kw_hits.items():
                text_hits[nid] = text_hits.get(nid, 0) + score * 0.3

        sorted_ids = sorted(text_hits, key=text_hits.get, reverse=True)[:k]

        results = []
        for nid in sorted_ids:
            node = kg_service.get_node(db_id, nid)
            if node:
                results.append({
                    "node": node,
                    "score": round(text_hits[nid], 4),
                    "relevance": "direct" if nid in (set(list(text_hits.keys())[:5])) else "related",
                })

        return {"goal": goal, "keywords": keywords, "results": results, "total": len(results)}

    # ══════════════════════════════════════════════════════════════════
    # PUBLIC: can_it — capability check with limitations/workarounds
    # ══════════════════════════════════════════════════════════════════

    def can_it(self, db_id: str, capability: str) -> dict:
        """Check if the KG has nodes supporting a capability, including limitations and workarounds."""
        from services.kg_service import kg_service

        matches = self._keyword_match_nodes(db_id, capability)
        if not matches:
            return {"capability": capability, "supported": False, "matches": [], "limitations": [], "workarounds": []}

        top_ids = list(matches.keys())[:5]
        limitations = []
        workarounds = []

        for nid in top_ids:
            try:
                neighbors = kg_service.get_neighbors(db_id, nid, depth=1, limit=30)
                for edge in neighbors.get("edges", []):
                    etype = edge.get("type", "").lower()
                    target_id = edge.get("target", "")
                    target_node = next(
                        (n for n in neighbors["nodes"] if str(n["id"]) == str(target_id)), None
                    )
                    if any(w in etype for w in ["limit", "restrict", "constraint", "cannot", "block"]):
                        limitations.append({
                            "edge_type": edge["type"],
                            "node": target_node or {"id": target_id, "name": target_id, "type": "unknown"},
                        })
                    if any(w in etype for w in ["workaround", "alternative", "fallback", "instead"]):
                        workarounds.append({
                            "edge_type": edge["type"],
                            "node": target_node or {"id": target_id, "name": target_id, "type": "unknown"},
                        })
            except Exception:
                pass

        results = []
        for nid in top_ids:
            node = kg_service.get_node(db_id, nid)
            if node:
                results.append({"node": node, "score": round(matches[nid], 4)})

        return {
            "capability": capability,
            "supported": len(results) > 0,
            "matches": results,
            "limitations": limitations,
            "workarounds": workarounds,
        }

    # ══════════════════════════════════════════════════════════════════
    # PUBLIC: compose_for — multi-node workflow composition
    # ══════════════════════════════════════════════════════════════════

    def compose_for(self, db_id: str, goal: str, max_steps: int = 5) -> dict:
        """Decompose a goal into sub-goals and find nodes for each, validating via edge connections."""
        from services.kg_service import kg_service

        # Simple sub-goal extraction (split on "and", "then", commas)
        sub_goals = re.split(r'\b(?:and|then|,)\b', goal)
        sub_goals = [s.strip() for s in sub_goals if s.strip()]
        if len(sub_goals) == 1:
            # Try to decompose further from the single goal
            sub_goals = [goal]

        steps = []
        previous_node_ids = set()

        for i, sg in enumerate(sub_goals[:max_steps]):
            matches = self._keyword_match_nodes(db_id, sg)

            # Boost nodes connected to previous step's nodes
            if previous_node_ids:
                compose_edges = ["feeds_into", "requires", "followed_by", "depends_on", "enables"]
                boost = self._edge_type_boost(db_id, previous_node_ids, compose_edges)
                for nid, score in boost.items():
                    matches[nid] = matches.get(nid, 0) + score * 0.6

            if matches:
                best_id = max(matches, key=matches.get)
                node = kg_service.get_node(db_id, best_id)
                if node:
                    steps.append({
                        "step": i + 1,
                        "sub_goal": sg,
                        "node": node,
                        "score": round(matches[best_id], 4),
                        "connected_to_previous": best_id in (
                            self._edge_type_boost(db_id, previous_node_ids, []) if previous_node_ids else {}
                        ),
                    })
                    previous_node_ids = {best_id}
            else:
                steps.append({
                    "step": i + 1,
                    "sub_goal": sg,
                    "node": None,
                    "score": 0,
                    "connected_to_previous": False,
                })

        return {
            "goal": goal,
            "sub_goals": sub_goals,
            "steps": steps,
            "complete": all(s["node"] is not None for s in steps),
            "total_steps": len(steps),
        }

    # ══════════════════════════════════════════════════════════════════
    # PUBLIC: similar_to — Jaccard similarity + type matching
    # ══════════════════════════════════════════════════════════════════

    def similar_to(self, db_id: str, node_id: str, k: int = 10) -> dict:
        """Find similar nodes using Jaccard neighbor similarity + type matching + name overlap."""
        from services.kg_service import kg_service

        target_node = kg_service.get_node(db_id, node_id)
        if not target_node:
            return {"node_id": node_id, "error": "Node not found", "results": []}

        # Get target's neighbors
        target_neighbors = self._get_neighbor_ids(db_id, node_id)
        target_type = target_node.get("type", "")
        target_name_tokens = set(re.findall(r'\w+', target_node.get("name", "").lower()))

        # Get all nodes and score them
        p = self._get_profile(db_id)
        conn = self._get_conn(db_id)
        rows = conn.execute(
            f"SELECT {p['node_id']}, {p['node_name']}, {p['node_type']} FROM {p['node_table']} LIMIT 500"
        ).fetchall()

        scores = {}
        for r in rows:
            cid = str(r[0])
            if cid == str(node_id):
                continue
            cname = str(r[1])
            ctype = str(r[2])

            # Jaccard similarity of neighbor sets
            candidate_neighbors = self._get_neighbor_ids(db_id, cid)
            intersection = target_neighbors & candidate_neighbors
            union = target_neighbors | candidate_neighbors
            jaccard = len(intersection) / max(len(union), 1)

            # Type match bonus
            type_match = 1.0 if ctype == target_type else 0.0

            # Name overlap
            cname_tokens = set(re.findall(r'\w+', cname.lower()))
            name_intersection = target_name_tokens & cname_tokens
            name_union = target_name_tokens | cname_tokens
            name_overlap = len(name_intersection) / max(len(name_union), 1)

            # Weighted combination: 0.70*jaccard + 0.20*type + 0.10*name
            score = 0.70 * jaccard + 0.20 * type_match + 0.10 * name_overlap
            if score > 0.01:
                scores[cid] = score

        sorted_ids = sorted(scores, key=scores.get, reverse=True)[:k]
        results = []
        for nid in sorted_ids:
            node = kg_service.get_node(db_id, nid)
            if node:
                results.append({"node": node, "similarity": round(scores[nid], 4)})

        return {"node_id": node_id, "target": target_node, "results": results, "total": len(results)}

    # ══════════════════════════════════════════════════════════════════
    # PUBLIC: impact_analysis — BFS forward/backward with risk scoring
    # ══════════════════════════════════════════════════════════════════

    def impact_analysis(
        self, db_id: str, node_id: str, direction: str = "forward", max_depth: int = 3
    ) -> dict:
        """BFS impact analysis — which nodes are affected if this node changes?"""
        from services.kg_service import kg_service

        source_node = kg_service.get_node(db_id, node_id)
        if not source_node:
            return {"node_id": node_id, "error": "Node not found", "layers": []}

        p = self._get_profile(db_id)
        conn = self._get_conn(db_id)

        visited = {str(node_id)}
        current_layer = {str(node_id)}
        layers = []

        for depth in range(1, max_depth + 1):
            next_layer = set()
            layer_nodes = []

            for nid in current_layer:
                if direction == "forward":
                    rows = conn.execute(
                        f"SELECT {p['edge_target']}, {p['edge_type']} FROM {p['edge_table']} WHERE {p['edge_source']} = ?",
                        (nid,),
                    ).fetchall()
                elif direction == "backward":
                    rows = conn.execute(
                        f"SELECT {p['edge_source']}, {p['edge_type']} FROM {p['edge_table']} WHERE {p['edge_target']} = ?",
                        (nid,),
                    ).fetchall()
                else:  # both
                    rows_fwd = conn.execute(
                        f"SELECT {p['edge_target']}, {p['edge_type']} FROM {p['edge_table']} WHERE {p['edge_source']} = ?",
                        (nid,),
                    ).fetchall()
                    rows_bwd = conn.execute(
                        f"SELECT {p['edge_source']}, {p['edge_type']} FROM {p['edge_table']} WHERE {p['edge_target']} = ?",
                        (nid,),
                    ).fetchall()
                    rows = list(rows_fwd) + list(rows_bwd)

                for r in rows:
                    tid = str(r[0])
                    if tid not in visited:
                        visited.add(tid)
                        next_layer.add(tid)
                        node = kg_service.get_node(db_id, tid)
                        if node:
                            # Risk scoring: deeper = lower risk, more connections = higher risk
                            risk = round(1.0 / depth * min(len(rows), 5) / 5, 2)
                            layer_nodes.append({
                                "node": node,
                                "edge_type": str(r[1]),
                                "risk": risk,
                                "via": nid,
                            })

            if layer_nodes:
                layers.append({"depth": depth, "count": len(layer_nodes), "nodes": layer_nodes})
            current_layer = next_layer
            if not next_layer:
                break

        total_impacted = sum(layer["count"] for layer in layers)
        return {
            "source": source_node,
            "direction": direction,
            "max_depth": max_depth,
            "layers": layers,
            "total_impacted": total_impacted,
        }

    # ══════════════════════════════════════════════════════════════════
    # PUBLIC: dimension_filter — filter nodes by semantic dimension values
    # ══════════════════════════════════════════════════════════════════

    def dimension_filter(self, db_id: str, filters: dict[str, dict], limit: int = 20) -> dict:
        """Filter nodes by semantic dimension thresholds stored in properties JSON.

        filters format: {"dimension_name": {"min": 0.5, "max": 1.0}}
        """
        from services.kg_service import kg_service

        p = self._get_profile(db_id)
        conn = self._get_conn(db_id)

        # Check if properties column exists
        props_col = p.get("node_props", "properties")

        # Build SQL conditions for json_extract
        conditions = []
        params = []
        for dim_name, bounds in filters.items():
            if "min" in bounds:
                conditions.append(
                    f"CAST(json_extract({props_col}, '$.{dim_name}') AS REAL) >= ?"
                )
                params.append(bounds["min"])
            if "max" in bounds:
                conditions.append(
                    f"CAST(json_extract({props_col}, '$.{dim_name}') AS REAL) <= ?"
                )
                params.append(bounds["max"])

        if not conditions:
            return {"filters": filters, "results": [], "total": 0}

        where_clause = " AND ".join(conditions)
        try:
            rows = conn.execute(
                f"SELECT {p['node_id']} FROM {p['node_table']} WHERE {where_clause} LIMIT ?",
                params + [limit],
            ).fetchall()
        except sqlite3.OperationalError:
            # json_extract not supported or column doesn't exist — fallback to Python filtering
            return self._dimension_filter_python(db_id, filters, limit)

        results = []
        for r in rows:
            node = kg_service.get_node(db_id, str(r[0]))
            if node:
                # Extract dimension values for the matched node
                dim_values = {}
                props = node.get("properties", {})
                for dim_name in filters:
                    if dim_name in props:
                        dim_values[dim_name] = props[dim_name]
                results.append({"node": node, "dimensions": dim_values})

        return {"filters": filters, "results": results, "total": len(results)}

    def _dimension_filter_python(self, db_id: str, filters: dict, limit: int) -> dict:
        """Fallback: filter in Python when json_extract isn't available."""
        from services.kg_service import kg_service

        p = self._get_profile(db_id)
        conn = self._get_conn(db_id)
        props_col = p.get("node_props", "properties")

        rows = conn.execute(
            f"SELECT {p['node_id']}, {props_col} FROM {p['node_table']}"
        ).fetchall()

        results = []
        for r in rows:
            nid = str(r[0])
            props_raw = r[1]
            if isinstance(props_raw, str):
                try:
                    props = json.loads(props_raw)
                except (json.JSONDecodeError, TypeError):
                    continue
            elif isinstance(props_raw, dict):
                props = props_raw
            else:
                continue

            match = True
            dim_values = {}
            for dim_name, bounds in filters.items():
                val = props.get(dim_name)
                if val is None:
                    match = False
                    break
                try:
                    val = float(val)
                except (ValueError, TypeError):
                    match = False
                    break
                if "min" in bounds and val < bounds["min"]:
                    match = False
                    break
                if "max" in bounds and val > bounds["max"]:
                    match = False
                    break
                dim_values[dim_name] = val

            if match:
                node = kg_service.get_node(db_id, nid)
                if node:
                    results.append({"node": node, "dimensions": dim_values})
                    if len(results) >= limit:
                        break

        return {"filters": filters, "results": results, "total": len(results)}

    # ══════════════════════════════════════════════════════════════════
    # PUBLIC: classify_intent — 14 intent categories via keyword patterns
    # ══════════════════════════════════════════════════════════════════

    def classify_intent(self, query: str) -> str:
        """Classify a query into one of 14 intent categories."""
        if query in self._intent_cache:
            return self._intent_cache[query]

        q = query.lower().strip()
        best_intent = "explore"  # default
        best_score = 0

        for intent, patterns in INTENT_PATTERNS.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, q, re.IGNORECASE):
                    score += 1
            if score > best_score:
                best_score = score
                best_intent = intent

        self._intent_cache[query] = best_intent
        return best_intent

    # ══════════════════════════════════════════════════════════════════
    # PUBLIC: trace_path — BFS shortest path between two nodes
    # ══════════════════════════════════════════════════════════════════

    def trace_path(self, db_id: str, node_a: str, node_b: str, max_depth: int = 5) -> dict:
        """Find shortest path between two nodes via BFS with edge annotations."""
        from services.kg_service import kg_service

        p = self._get_profile(db_id)
        conn = self._get_conn(db_id)

        node_a_data = kg_service.get_node(db_id, node_a)
        node_b_data = kg_service.get_node(db_id, node_b)
        if not node_a_data or not node_b_data:
            return {"error": "One or both nodes not found", "path": []}

        # BFS
        queue = [(str(node_a), [str(node_a)], [])]  # (current, path_nodes, path_edges)
        visited = {str(node_a)}

        while queue:
            current, path_nodes, path_edges = queue.pop(0)

            if len(path_nodes) > max_depth + 1:
                break

            # Get all neighbors (both directions)
            rows_fwd = conn.execute(
                f"SELECT {p['edge_target']}, {p['edge_type']} FROM {p['edge_table']} WHERE {p['edge_source']} = ?",
                (current,),
            ).fetchall()
            rows_bwd = conn.execute(
                f"SELECT {p['edge_source']}, {p['edge_type']} FROM {p['edge_table']} WHERE {p['edge_target']} = ?",
                (current,),
            ).fetchall()

            for r in rows_fwd:
                neighbor_id = str(r[0])
                edge_type = str(r[1])
                if neighbor_id == str(node_b):
                    # Found path!
                    final_path = path_nodes + [neighbor_id]
                    final_edges = path_edges + [{"from": current, "to": neighbor_id, "type": edge_type, "direction": "forward"}]
                    # Resolve node names
                    path_details = []
                    for pid in final_path:
                        pnode = kg_service.get_node(db_id, pid)
                        path_details.append(pnode or {"id": pid, "name": pid, "type": "unknown"})
                    return {"path": path_details, "edges": final_edges, "length": len(final_edges)}

                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((
                        neighbor_id,
                        path_nodes + [neighbor_id],
                        path_edges + [{"from": current, "to": neighbor_id, "type": edge_type, "direction": "forward"}],
                    ))

            for r in rows_bwd:
                neighbor_id = str(r[0])
                edge_type = str(r[1])
                if neighbor_id == str(node_b):
                    final_path = path_nodes + [neighbor_id]
                    final_edges = path_edges + [{"from": neighbor_id, "to": current, "type": edge_type, "direction": "backward"}]
                    path_details = []
                    for pid in final_path:
                        pnode = kg_service.get_node(db_id, pid)
                        path_details.append(pnode or {"id": pid, "name": pid, "type": "unknown"})
                    return {"path": path_details, "edges": final_edges, "length": len(final_edges)}

                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((
                        neighbor_id,
                        path_nodes + [neighbor_id],
                        path_edges + [{"from": neighbor_id, "to": current, "type": edge_type, "direction": "backward"}],
                    ))

        return {"path": [], "edges": [], "length": -1, "message": "No path found within depth limit"}

    # ══════════════════════════════════════════════════════════════════
    # PUBLIC: explore_smart — BFS with importance ranking per level
    # ══════════════════════════════════════════════════════════════════

    def explore_smart(self, db_id: str, start_node: str, depth: int = 2) -> dict:
        """BFS exploration with importance ranking (hub detection) per level."""
        from services.kg_service import kg_service

        source = kg_service.get_node(db_id, start_node)
        if not source:
            return {"start_node": start_node, "error": "Node not found", "levels": []}

        p = self._get_profile(db_id)
        conn = self._get_conn(db_id)

        visited = {str(start_node)}
        current_layer = {str(start_node)}
        levels = []

        for d in range(1, depth + 1):
            next_layer = set()
            level_nodes = []

            for nid in current_layer:
                # Both directions
                rows = conn.execute(
                    f"""SELECT {p['edge_target']} FROM {p['edge_table']} WHERE {p['edge_source']} = ?
                    UNION SELECT {p['edge_source']} FROM {p['edge_table']} WHERE {p['edge_target']} = ?""",
                    (nid, nid),
                ).fetchall()

                for r in rows:
                    tid = str(r[0])
                    if tid not in visited:
                        visited.add(tid)
                        next_layer.add(tid)

            # Rank by degree (hub detection)
            for tid in next_layer:
                degree = conn.execute(
                    f"""SELECT COUNT(*) FROM {p['edge_table']}
                    WHERE {p['edge_source']} = ? OR {p['edge_target']} = ?""",
                    (tid, tid),
                ).fetchone()[0]
                node = kg_service.get_node(db_id, tid)
                if node:
                    level_nodes.append({
                        "node": node,
                        "degree": degree,
                        "is_hub": degree > 5,
                    })

            level_nodes.sort(key=lambda x: x["degree"], reverse=True)
            if level_nodes:
                levels.append({"depth": d, "count": len(level_nodes), "nodes": level_nodes})
            current_layer = next_layer
            if not next_layer:
                break

        return {"start_node": source, "levels": levels, "total_explored": len(visited) - 1}

    # ══════════════════════════════════════════════════════════════════
    # PRIVATE: Score decomposition helpers
    # ══════════════════════════════════════════════════════════════════

    def _get_embedding_scores(self, db_id: str, query: str, limit: int = 50) -> dict[str, float]:
        """Normalized embedding cosine similarity scores."""
        from services.embedding_service import embedding_service
        raw = embedding_service._embedding_search(db_id, query, limit)
        if not raw:
            return {}
        max_v = max(raw.values()) if raw else 1
        return {k: v / max_v for k, v in raw.items()}

    def _get_text_scores(self, db_id: str, query: str) -> dict[str, float]:
        """Normalized BM25 + FTS text scores."""
        from services.embedding_service import embedding_service
        bm25_idx = embedding_service._build_bm25_index(db_id)
        bm25_scores = embedding_service._bm25_score(bm25_idx, query)
        fts_scores = embedding_service._fts_search(db_id, query, 50)

        all_ids = set(bm25_scores) | set(fts_scores)
        if not all_ids:
            return {}
        max_bm25 = max(bm25_scores.values()) if bm25_scores else 1
        max_fts = max(fts_scores.values()) if fts_scores else 1
        combined = {}
        for nid in all_ids:
            s1 = bm25_scores.get(nid, 0) / max_bm25 if max_bm25 else 0
            s2 = fts_scores.get(nid, 0) / max_fts if max_fts else 0
            combined[nid] = max(s1, s2)
        return combined

    def _get_graph_boost_scores(self, db_id: str, seed_ids: set[str]) -> dict[str, float]:
        """Graph neighbor boost scores from seed nodes."""
        from services.embedding_service import embedding_service
        return embedding_service._graph_boost(db_id, seed_ids)

    def _intent_score_nodes(self, db_id: str, query: str, intent: str) -> dict[str, float]:
        """Score nodes based on intent-specific edge types and keyword patterns."""
        # Map intents to relevant edge types
        intent_edge_map = {
            "find_tool": ["implements", "provides", "used_for", "enables"],
            "check_capability": ["supports", "has_capability", "enables", "has_limitation"],
            "compose_workflow": ["feeds_into", "requires", "followed_by", "depends_on"],
            "compare": ["similar_to", "alternative_to", "complements"],
            "debug": ["has_limitation", "has_workaround", "causes", "fixes"],
            "optimize": ["optimizes", "improves", "reduces", "enables"],
            "learn": ["explains", "teaches", "prerequisite_for", "builds_on"],
            "explore": ["relates_to", "contains", "part_of"],
            "impact": ["depends_on", "required_by", "feeds_into", "breaks"],
            "trace": ["connects_to", "feeds_into", "relates_to"],
            "recommend": ["recommended_for", "best_for", "suitable_for"],
            "create": ["creates", "generates", "produces", "implements"],
            "configure": ["configures", "sets_up", "requires", "depends_on"],
            "security": ["authenticates", "authorizes", "encrypts", "protects"],
        }

        # Get text matches as seeds
        text_hits = self._keyword_match_nodes(db_id, query)
        if not text_hits:
            return {}

        seed_ids = set(list(text_hits.keys())[:10])
        relevant_edges = intent_edge_map.get(intent, ["relates_to"])
        edge_boost = self._edge_type_boost(db_id, seed_ids, relevant_edges)

        # Combine: text + edge boost
        scores = {}
        for nid, score in text_hits.items():
            scores[nid] = score
        for nid, score in edge_boost.items():
            scores[nid] = scores.get(nid, 0) + score * 0.5

        # Normalize
        if scores:
            max_v = max(scores.values())
            scores = {k: v / max_v for k, v in scores.items()}

        return scores

    # ══════════════════════════════════════════════════════════════════
    # PRIVATE: Base-layer helpers
    # ══════════════════════════════════════════════════════════════════

    def _keyword_match_nodes(self, db_id: str, query: str) -> dict[str, float]:
        """SQL LIKE matching on node name, type, and properties."""
        p = self._get_profile(db_id)
        conn = self._get_conn(db_id)
        tokens = re.findall(r'\w+', query.lower())
        if not tokens:
            return {}

        scores: dict[str, float] = {}
        for token in tokens:
            like_pattern = f"%{token}%"
            try:
                rows = conn.execute(
                    f"SELECT {p['node_id']}, {p['node_name']}, {p['node_type']} FROM {p['node_table']} "
                    f"WHERE LOWER({p['node_name']}) LIKE ? OR LOWER({p['node_type']}) LIKE ? LIMIT 100",
                    (like_pattern, like_pattern),
                ).fetchall()
                for r in rows:
                    nid = str(r[0])
                    name = str(r[1]).lower()
                    ntype = str(r[2]).lower()
                    # Score: exact > partial, name > type
                    score = 0
                    if token in name.split('_') or token in name.split(' ') or token in name.split('-'):
                        score += 1.0  # exact word match in name
                    elif token in name:
                        score += 0.6  # partial match in name
                    if token in ntype:
                        score += 0.3  # match in type
                    scores[nid] = scores.get(nid, 0) + score
            except sqlite3.OperationalError:
                pass

        # Normalize
        if scores:
            max_v = max(scores.values())
            if max_v > 0:
                scores = {k: v / max_v for k, v in scores.items()}

        return scores

    def _edge_type_boost(self, db_id: str, seed_ids: set[str], boost_types: list[str]) -> dict[str, float]:
        """Boost nodes connected via specific edge types to seed nodes."""
        if not seed_ids:
            return {}

        p = self._get_profile(db_id)
        conn = self._get_conn(db_id)
        boost: dict[str, float] = {}
        placeholders = ",".join("?" for _ in seed_ids)

        try:
            if boost_types:
                type_placeholders = ",".join("?" for _ in boost_types)
                # Forward edges
                rows = conn.execute(
                    f"SELECT {p['edge_target']}, {p['edge_type']} FROM {p['edge_table']} "
                    f"WHERE {p['edge_source']} IN ({placeholders}) AND LOWER({p['edge_type']}) IN ({type_placeholders})",
                    list(seed_ids) + [t.lower() for t in boost_types],
                ).fetchall()
                for r in rows:
                    nid = str(r[0])
                    boost[nid] = boost.get(nid, 0) + 1.0

                # Backward edges
                rows = conn.execute(
                    f"SELECT {p['edge_source']}, {p['edge_type']} FROM {p['edge_table']} "
                    f"WHERE {p['edge_target']} IN ({placeholders}) AND LOWER({p['edge_type']}) IN ({type_placeholders})",
                    list(seed_ids) + [t.lower() for t in boost_types],
                ).fetchall()
                for r in rows:
                    nid = str(r[0])
                    boost[nid] = boost.get(nid, 0) + 0.7
            else:
                # All edge types
                rows = conn.execute(
                    f"SELECT {p['edge_target']} FROM {p['edge_table']} WHERE {p['edge_source']} IN ({placeholders})",
                    list(seed_ids),
                ).fetchall()
                for r in rows:
                    nid = str(r[0])
                    boost[nid] = boost.get(nid, 0) + 0.5
                rows = conn.execute(
                    f"SELECT {p['edge_source']} FROM {p['edge_table']} WHERE {p['edge_target']} IN ({placeholders})",
                    list(seed_ids),
                ).fetchall()
                for r in rows:
                    nid = str(r[0])
                    boost[nid] = boost.get(nid, 0) + 0.3
        except sqlite3.OperationalError:
            pass

        # Normalize
        if boost:
            max_b = max(boost.values())
            if max_b > 0:
                boost = {k: v / max_b for k, v in boost.items()}

        return boost

    def _get_neighbor_ids(self, db_id: str, node_id: str) -> set[str]:
        """Get the set of neighbor IDs for a node (both directions)."""
        p = self._get_profile(db_id)
        conn = self._get_conn(db_id)
        neighbors = set()
        try:
            rows = conn.execute(
                f"SELECT {p['edge_target']} FROM {p['edge_table']} WHERE {p['edge_source']} = ?",
                (str(node_id),),
            ).fetchall()
            for r in rows:
                neighbors.add(str(r[0]))
            rows = conn.execute(
                f"SELECT {p['edge_source']} FROM {p['edge_table']} WHERE {p['edge_target']} = ?",
                (str(node_id),),
            ).fetchall()
            for r in rows:
                neighbors.add(str(r[0]))
        except sqlite3.OperationalError:
            pass
        return neighbors

    def _extract_goal_keywords(self, goal: str) -> list[str]:
        """Extract goal-relevant keywords (verbs + objects)."""
        stop_words = {
            "i", "want", "to", "a", "the", "an", "is", "are", "was", "were",
            "be", "been", "being", "have", "has", "had", "do", "does", "did",
            "will", "would", "could", "should", "may", "might", "can",
            "this", "that", "these", "those", "my", "your", "our", "their",
            "it", "its", "me", "we", "you", "he", "she", "they", "them",
            "how", "what", "which", "who", "when", "where", "why",
            "and", "or", "but", "if", "then", "so", "for", "with", "from",
            "in", "on", "at", "by", "of", "about", "into", "through",
        }
        tokens = re.findall(r'\w+', goal.lower())
        return [t for t in tokens if t not in stop_words and len(t) > 2]

    def _get_profile(self, db_id: str) -> dict:
        """Get the KG schema profile for a database."""
        from services.kg_service import kg_service
        return kg_service._detect_profile(db_id)

    def _get_conn(self, db_id: str):
        """Get the SQLite connection for a database."""
        from services.kg_service import kg_service
        return kg_service._get_conn(db_id)


# ── Standard Dimensions Catalog ──────────────────────────────────────

STANDARD_DIMENSIONS = {
    "performance_cost": [
        "latency_sensitivity", "throughput_requirement", "pricing_tier",
        "token_efficiency", "batch_suitability", "cache_effectiveness",
        "rate_limit_sensitivity", "compute_intensity",
    ],
    "complexity_effort": [
        "implementation_complexity", "configuration_depth", "learning_curve",
        "error_handling_need", "debugging_difficulty", "maintenance_burden",
    ],
    "interaction_patterns": [
        "streaming_support", "batching_capability", "async_compatibility",
        "real_time_requirement", "multi_turn_depth", "context_dependency",
        "state_management",
    ],
    "data_characteristics": [
        "data_volume_sensitivity", "format_flexibility", "schema_strictness",
        "data_sensitivity_level", "multimodal_support", "structured_vs_unstructured",
    ],
    "api_capabilities": [
        "tool_use_support", "system_prompt_control", "temperature_sensitivity",
        "max_context_utilization", "function_calling_depth", "grounding_support",
        "safety_filter_level", "output_format_control",
    ],
    "problem_domains": [
        "code_generation_strength", "analytical_reasoning", "creative_capability",
        "instruction_following", "multilingual_support", "summarization_quality",
        "extraction_accuracy",
    ],
    "architectural_patterns": [
        "rag_suitability", "agent_compatibility", "fine_tuning_benefit",
        "pipeline_composability", "orchestration_complexity",
    ],
    "nlke_meta": [
        "knowledge_density", "relationship_richness", "emergence_potential",
    ],
    "cli_tool_characteristics": [
        "file_system_dependency", "git_integration_level", "shell_command_execution",
        "sandbox_sensitivity", "permission_requirement_level", "idempotency_guarantee",
    ],
}


# Singleton
kgos_query_engine = KGOSQueryEngine()

"""Analytics service — NetworkX-powered graph algorithms, comparison, diff, merge."""
import json
from typing import Any

from services.kg_service import kg_service

try:
    import networkx as nx
    _HAS_NX = True
except ImportError:
    _HAS_NX = False


class AnalyticsService:
    """Graph analytics using NetworkX loaded from SQLite KG databases."""

    _graph_cache: dict[str, Any] = {}  # db_id -> nx.DiGraph

    def _build_graph(self, db_id: str) -> Any:
        if not _HAS_NX:
            raise ImportError("networkx not installed — required for analytics")
        if db_id in self._graph_cache:
            return self._graph_cache[db_id]

        conn = kg_service._get_conn(db_id)
        p = kg_service._detect_profile(db_id)

        G = nx.DiGraph()

        # Load nodes
        rows = conn.execute(f"SELECT * FROM {p['node_table']}").fetchall()
        for r in rows:
            nd = kg_service._node_row_to_dict(r, p)
            G.add_node(nd["id"], name=nd["name"], type=nd["type"], **nd["properties"])

        # Load edges
        try:
            rows = conn.execute(f"SELECT * FROM {p['edge_table']}").fetchall()
            for r in rows:
                ed = kg_service._edge_row_to_dict(r, p)
                G.add_edge(ed["source"], ed["target"], type=ed["type"], id=ed["id"])
        except Exception:
            pass

        self._graph_cache[db_id] = G
        return G

    def invalidate_cache(self, db_id: str):
        self._graph_cache.pop(db_id, None)

    # ── Summary ─────────────────────────────────────────────────────
    def summary(self, db_id: str) -> dict:
        G = self._build_graph(db_id)
        Gu = G.to_undirected()
        return {
            "node_count": G.number_of_nodes(),
            "edge_count": G.number_of_edges(),
            "density": round(nx.density(G), 6),
            "components": nx.number_weakly_connected_components(G),
            "avg_degree": round(sum(d for _, d in G.degree()) / max(G.number_of_nodes(), 1), 2),
            "clustering": round(nx.average_clustering(Gu), 4) if G.number_of_nodes() > 0 else 0,
            "isolates": sum(1 for n in nx.isolates(G)),
        }

    # ── Centrality ──────────────────────────────────────────────────
    def centrality(self, db_id: str, metric: str = "degree", top_k: int = 20) -> dict:
        G = self._build_graph(db_id)

        if metric == "degree":
            scores = dict(G.degree())
            max_val = max(scores.values()) if scores else 1
            scores = {k: v / max_val for k, v in scores.items()}
        elif metric == "betweenness":
            if G.number_of_nodes() > 1000:
                scores = nx.betweenness_centrality(G, k=min(100, G.number_of_nodes()))
            else:
                scores = nx.betweenness_centrality(G)
        elif metric == "pagerank":
            try:
                scores = nx.pagerank(G, max_iter=100)
            except nx.PowerIterationFailedConvergence:
                scores = nx.pagerank(G, max_iter=200, tol=1e-4)
        else:
            scores = dict(G.degree())
            max_val = max(scores.values()) if scores else 1
            scores = {k: v / max_val for k, v in scores.items()}

        sorted_nodes = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        nodes = []
        for nid, score in sorted_nodes:
            data = G.nodes.get(nid, {})
            nodes.append({
                "id": nid,
                "name": data.get("name", nid),
                "type": data.get("type", "unknown"),
                "score": round(score, 6),
            })
        return {"metric": metric, "nodes": nodes}

    # ── Communities ──────────────────────────────────────────────────
    def communities(self, db_id: str) -> dict:
        G = self._build_graph(db_id)
        Gu = G.to_undirected()

        try:
            comms = list(nx.community.greedy_modularity_communities(Gu))
        except Exception:
            comms = list(nx.weakly_connected_components(G))

        result = []
        for i, comm in enumerate(sorted(comms, key=len, reverse=True)[:20]):
            members = []
            for nid in list(comm)[:50]:
                data = G.nodes.get(nid, {})
                members.append({
                    "id": nid,
                    "name": data.get("name", nid),
                    "type": data.get("type", "unknown"),
                })
            result.append({"id": i, "size": len(comm), "members": members})

        return {"communities": result, "total": len(comms)}

    # ── Shortest path ───────────────────────────────────────────────
    def shortest_path(self, db_id: str, source: str, target: str) -> dict:
        G = self._build_graph(db_id)
        try:
            path = nx.shortest_path(G, source, target)
            path_nodes = []
            for nid in path:
                data = G.nodes.get(nid, {})
                path_nodes.append({
                    "id": nid,
                    "name": data.get("name", nid),
                    "type": data.get("type", "unknown"),
                })
            return {"found": True, "length": len(path) - 1, "path": path_nodes}
        except (nx.NetworkXNoPath, nx.NodeNotFound) as e:
            return {"found": False, "error": str(e)}

    # ── Compare ─────────────────────────────────────────────────────
    def compare(self, db_id_a: str, db_id_b: str) -> dict:
        Ga = self._build_graph(db_id_a)
        Gb = self._build_graph(db_id_b)

        names_a = {Ga.nodes[n].get("name", n) for n in Ga.nodes()}
        names_b = {Gb.nodes[n].get("name", n) for n in Gb.nodes()}

        shared = names_a & names_b
        union = names_a | names_b
        jaccard = len(shared) / max(len(union), 1)

        types_a = {}
        for n in Ga.nodes():
            t = Ga.nodes[n].get("type", "unknown")
            types_a[t] = types_a.get(t, 0) + 1
        types_b = {}
        for n in Gb.nodes():
            t = Gb.nodes[n].get("type", "unknown")
            types_b[t] = types_b.get(t, 0) + 1

        return {
            "db_a": db_id_a,
            "db_b": db_id_b,
            "shared_nodes": len(shared),
            "unique_a": len(names_a - names_b),
            "unique_b": len(names_b - names_a),
            "jaccard_similarity": round(jaccard, 4),
            "structural_comparison": {
                "nodes_a": Ga.number_of_nodes(),
                "nodes_b": Gb.number_of_nodes(),
                "edges_a": Ga.number_of_edges(),
                "edges_b": Gb.number_of_edges(),
                "types_a": types_a,
                "types_b": types_b,
            },
        }

    # ── Diff ────────────────────────────────────────────────────────
    def diff(self, db_id_a: str, db_id_b: str) -> dict:
        Ga = self._build_graph(db_id_a)
        Gb = self._build_graph(db_id_b)

        names_a = {Ga.nodes[n].get("name", n): n for n in Ga.nodes()}
        names_b = {Gb.nodes[n].get("name", n): n for n in Gb.nodes()}

        only_a = [{"name": name, "type": Ga.nodes[nid].get("type", "unknown")}
                  for name, nid in names_a.items() if name not in names_b]
        only_b = [{"name": name, "type": Gb.nodes[nid].get("type", "unknown")}
                  for name, nid in names_b.items() if name not in names_a]

        return {
            "only_in_a": only_a[:100],
            "only_in_b": only_b[:100],
            "only_in_a_count": len(only_a),
            "only_in_b_count": len(only_b),
        }

    # ── Merge ───────────────────────────────────────────────────────
    def merge(self, source_db: str, target_db: str, strategy: str = "union") -> dict:
        source_nodes = kg_service.get_nodes(source_db, limit=100000)["nodes"]
        source_edges = kg_service.get_edges(source_db, limit=100000)["edges"]

        if strategy == "intersection":
            target_nodes = kg_service.get_nodes(target_db, limit=100000)["nodes"]
            target_names = {n["name"].lower() for n in target_nodes}
            source_nodes = [n for n in source_nodes if n["name"].lower() in target_names]
            valid_ids = {n["id"] for n in source_nodes}
            source_edges = [e for e in source_edges if e["source"] in valid_ids and e["target"] in valid_ids]

        nodes_added = 0
        edges_added = 0
        id_map = {}  # old source id -> new target id

        for n in source_nodes:
            try:
                new_node = kg_service.create_node(target_db, n["name"], n["type"], n.get("properties"))
                id_map[n["id"]] = new_node["id"]
                nodes_added += 1
            except Exception:
                pass

        for e in source_edges:
            src = id_map.get(e["source"], e["source"])
            tgt = id_map.get(e["target"], e["target"])
            try:
                kg_service.create_edge(target_db, src, tgt, e["type"], e.get("properties"))
                edges_added += 1
            except Exception:
                pass

        # Invalidate caches
        self.invalidate_cache(target_db)

        return {
            "strategy": strategy,
            "source": source_db,
            "target": target_db,
            "nodes_merged": nodes_added,
            "edges_merged": edges_added,
        }


# Singleton
analytics_service = AnalyticsService()

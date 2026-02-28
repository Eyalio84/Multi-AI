"""Embedding service — multi-strategy search: FTS5, sqlite-vec, Gemini API, Model2Vec.

KG-OS Retrieval Upgrade: Intent-adaptive weights, BM25 stemming, 5x keyword boost,
edge-type graph boost, PageRank authority, 4-weight formula, query caching, community diversity.
"""
import sqlite3
import json
import struct
import math
import re
import time
import hashlib
import logging
from pathlib import Path
from typing import Any

from services.kg_service import kg_service

logger = logging.getLogger(__name__)

# Optional imports with graceful fallback
_HAS_SQLITE_VEC = False
_HAS_NUMPY = False
_HAS_MODEL2VEC = False
_HAS_NETWORKX = False

try:
    import sqlite_vec
    _HAS_SQLITE_VEC = True
except ImportError:
    pass

try:
    import numpy as np
    _HAS_NUMPY = True
except ImportError:
    pass

try:
    from model2vec import StaticModel
    _HAS_MODEL2VEC = True
except ImportError:
    pass

try:
    import networkx as nx
    _HAS_NETWORKX = True
except ImportError:
    pass


def _serialize_f32(vec: list[float]) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec)


def _deserialize_f32(data: bytes) -> list[float]:
    n = len(data) // 4
    return list(struct.unpack(f"{n}f", data))


# ── Intent-Adaptive Weight Profiles ────────────────────────────────
# Source: agents/shared/retrieval/weight_profiles.py + docs/rag-graph/REPORT-WEIGHTS-GRAPHRAG-EMBEDDINGS.md
# Extended with delta (intent edge score) for 4-weight formula.
INTENT_WEIGHT_PROFILES = {
    "exact_match":      {"alpha": 0.15, "beta": 0.65, "gamma": 0.10, "delta": 0.10},
    "capability_check": {"alpha": 0.30, "beta": 0.55, "gamma": 0.10, "delta": 0.05},
    "debugging":        {"alpha": 0.30, "beta": 0.45, "gamma": 0.20, "delta": 0.05},
    "workflow":         {"alpha": 0.30, "beta": 0.25, "gamma": 0.30, "delta": 0.15},
    "comparison":       {"alpha": 0.35, "beta": 0.30, "gamma": 0.25, "delta": 0.10},
    "goal_based":       {"alpha": 0.40, "beta": 0.25, "gamma": 0.15, "delta": 0.20},
    "exploratory":      {"alpha": 0.45, "beta": 0.20, "gamma": 0.25, "delta": 0.10},
    "semantic":         {"alpha": 0.55, "beta": 0.15, "gamma": 0.15, "delta": 0.15},
}
DEFAULT_PROFILE = {"alpha": 0.40, "beta": 0.45, "gamma": 0.15, "delta": 0.0}

# ── Intent Classification Patterns ────────────────────────────────
# Source: agents/shared/retrieval/intent_router.py + kgos_query_engine.py
_INTENT_PATTERNS = [
    ("exact_match", [
        r'^"[^"]+"$',                          # Quoted string
        r"^[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*$",  # PascalCase
        r"^[a-z]+[-_][a-z]+",                  # kebab/snake_case identifier
        r"^\w+\.\w+$",                         # file.ext
    ]),
    ("debugging", [
        r"\b(?:error|fail|debug|fix|broken|issue|crash|bug|exception|traceback)\b",
    ]),
    ("capability_check", [
        r"\bcan\s+(?:it|you|this)\b",
        r"\bdoes\s+\w+\s+support\b",
        r"\bis\s+\w+\s+(?:able|capable|compatible)\b",
    ]),
    ("workflow", [
        r"\b(?:pipeline|workflow|step.by.step|automat|chain|sequenc)\b",
        r"^how\s+(?:to|do\s+I)\b",
    ]),
    ("comparison", [
        r"\b(?:vs|versus|compar|differ|which\s+is\s+better|alternative)\b",
    ]),
    ("goal_based", [
        r"\b(?:I\s+want\s+to|how\s+do\s+I|reduc|improv|achiev|optim)\b",
        r"\b(?:increase|decrease|minimize|maximize)\b",
    ]),
    ("exploratory", [
        r"\b(?:explor|brows|list|show\s+me|what\s+are|overview)\b",
        r"^tell\s+me\s+about\b",
    ]),
]

# ── BM25 Intent Keyword Boost Sets ────────────────────────────────
# Source: docs/rag-graph/REPORT-WEIGHTS-GRAPHRAG-EMBEDDINGS.md
# Keywords are stemmed forms for matching against stemmed tokens.
INTENT_KEYWORDS = {
    "exact_match": set(),
    "debugging": {"error", "fail", "debug", "fix", "broken", "issu", "crash", "bug", "except", "traceback"},
    "goal_based": {"cost", "reduc", "improv", "optim", "fast", "cheap", "save", "effici", "increas", "decreas"},
    "workflow": {"step", "pipelin", "flow", "chain", "sequenc", "automat", "process", "how"},
    "capability_check": {"support", "compat", "handl", "enabl", "provid", "capabl"},
    "comparison": {"compar", "differ", "vs", "better", "altern", "versus"},
    "exploratory": {"explor", "brows", "list", "show", "discov", "overview"},
    "semantic": set(),
}

# ── BM25 Stemming Suffixes ────────────────────────────────────────
_STEM_SUFFIXES = [
    "ation", "tion", "sion", "ment", "ness", "able", "ible",
    "ful", "less", "ous", "ive", "ing", "ed", "er", "est",
    "ly", "al", "ity",
]

# ── Edge Type Weights for Graph Boost ─────────────────────────────
# Source: agents/shared/retrieval/graph_scorer.py + kgos_query_engine.py
EDGE_TYPE_WEIGHTS = {
    "implements": 1.0, "provides": 1.0, "enables": 0.9,
    "used_for": 0.9, "depends_on": 0.8, "requires": 0.8,
    "feeds_into": 0.8, "followed_by": 0.7, "part_of": 0.7,
    "relates_to": 0.5, "similar_to": 0.6, "alternative_to": 0.4,
    "has_limitation": 0.3, "has_workaround": 0.4, "complements": 0.6,
}

# ── Intent → Edge Type Mapping for Delta Scoring ──────────────────
# Source: kgos_query_engine.py lines 790-804
INTENT_EDGE_MAP = {
    "exact_match": [],
    "capability_check": ["supports", "has_capability", "enables", "has_limitation"],
    "debugging": ["has_limitation", "has_workaround", "causes", "fixes"],
    "workflow": ["feeds_into", "requires", "followed_by", "depends_on", "enables"],
    "comparison": ["similar_to", "alternative_to", "complements"],
    "goal_based": ["enables", "supports", "implements", "provides", "solves", "used_for"],
    "exploratory": ["relates_to", "contains", "part_of"],
    "semantic": ["relates_to", "similar_to", "part_of"],
}


class EmbeddingService:
    """Multi-strategy semantic search across knowledge graphs."""

    def __init__(self):
        self._model2vec_model = None
        self._bm25_indices: dict[str, dict] = {}
        self._pagerank_cache: dict[str, dict[str, float]] = {}
        self._community_cache: dict[str, list[set]] = {}
        self._query_cache: dict[str, tuple[dict, float]] = {}
        self._cache_ttl = 300  # 5 minutes

    # ── Stemming ──────────────────────────────────────────────────
    @staticmethod
    def _stem(word: str) -> str:
        """Lightweight suffix-stripping stemmer for BM25 parity with FTS5 Porter."""
        for suffix in _STEM_SUFFIXES:
            if word.endswith(suffix) and len(word) - len(suffix) >= 3:
                return word[:-len(suffix)]
        return word

    # ── Intent Classification ─────────────────────────────────────
    def _classify_search_intent(self, query: str) -> str:
        """Classify query into one of 8 retrieval intent profiles."""
        q = query.strip()
        q_lower = q.lower()

        # Pattern matching (strongest signal)
        for intent_name, patterns in _INTENT_PATTERNS:
            for pattern in patterns:
                target = q if intent_name == "exact_match" else q_lower
                if re.search(pattern, target):
                    return intent_name

        # Long queries → semantic (embedding-heavy)
        if len(q_lower.split()) > 10:
            return "semantic"

        return "goal_based"  # Default: most users ask goal-oriented questions

    # ── BM25 implementation (with stemming + 5x keyword boost) ────
    def _build_bm25_index(self, db_id: str) -> dict:
        if db_id in self._bm25_indices:
            return self._bm25_indices[db_id]
        conn = kg_service._get_conn(db_id)
        p = kg_service._detect_profile(db_id)
        rows = conn.execute(f"SELECT {p['node_id']}, {p['node_name']}, {p['node_type']} FROM {p['node_table']}").fetchall()

        docs = {}
        df: dict[str, int] = {}
        for r in rows:
            nid = str(r[0])
            text = f"{r[1]} {r[2]}".lower()
            tokens = [self._stem(t) for t in re.findall(r'\w+', text) if len(t) >= 2]
            tf: dict[str, int] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            docs[nid] = {"tf": tf, "length": len(tokens), "name": str(r[1]), "type": str(r[2])}
            for t in set(tokens):
                df[t] = df.get(t, 0) + 1

        avg_dl = sum(d["length"] for d in docs.values()) / max(len(docs), 1)
        idx = {"docs": docs, "df": df, "n": len(docs), "avg_dl": avg_dl}
        self._bm25_indices[db_id] = idx
        return idx

    def _bm25_score(self, idx: dict, query: str, k1: float = 1.5, b: float = 0.75,
                    intent_keywords: set | None = None) -> dict[str, float]:
        raw_tokens = [self._stem(t) for t in re.findall(r'\w+', query.lower()) if len(t) >= 2]

        # 5x boost for intent-relevant keywords
        if intent_keywords:
            tokens = []
            for t in raw_tokens:
                tokens.extend([t] * (5 if t in intent_keywords else 1))
        else:
            tokens = raw_tokens

        scores: dict[str, float] = {}
        n = idx["n"]
        avg_dl = idx["avg_dl"]

        for nid, doc in idx["docs"].items():
            score = 0.0
            for t in tokens:
                dft = idx["df"].get(t, 0)
                if dft == 0:
                    continue
                idf = math.log((n - dft + 0.5) / (dft + 0.5) + 1)
                tf = doc["tf"].get(t, 0)
                numerator = tf * (k1 + 1)
                denominator = tf + k1 * (1 - b + b * doc["length"] / max(avg_dl, 1))
                score += idf * numerator / denominator
            if score > 0:
                scores[nid] = score
        return scores

    # ── FTS5 search ─────────────────────────────────────────────────
    def _fts_search(self, db_id: str, query: str, limit: int = 50) -> dict[str, float]:
        p = kg_service._detect_profile(db_id)
        if not kg_service._has_fts(db_id):
            return {}
        conn = kg_service._get_conn(db_id)
        fts_table = f"{p['node_table']}_fts"
        fts_q = query.replace('"', '""')
        try:
            rows = conn.execute(
                f"SELECT rowid, rank FROM {fts_table} WHERE {fts_table} MATCH ? ORDER BY rank LIMIT ?",
                (f'"{fts_q}"', limit),
            ).fetchall()
            result = {}
            for r in rows:
                node_row = conn.execute(
                    f"SELECT {p['node_id']} FROM {p['node_table']} WHERE rowid = ?",
                    (r[0],),
                ).fetchone()
                if node_row:
                    result[str(node_row[0])] = abs(r[1])
            return result
        except sqlite3.OperationalError:
            return {}

    # ── Graph neighbor boost (type-aware + 2-hop + PageRank) ──────
    def _graph_boost(self, db_id: str, top_ids: set[str], intent: str | None = None) -> dict[str, float]:
        if not top_ids:
            return {}
        p = kg_service._detect_profile(db_id)
        conn = kg_service._get_conn(db_id)
        boost: dict[str, float] = {}
        placeholders = ",".join("?" for _ in top_ids)
        id_list = list(top_ids)

        # Check if edge table has a type column
        has_edge_type = p.get("edge_type") is not None

        try:
            # 1-hop outgoing
            if has_edge_type:
                rows = conn.execute(
                    f"SELECT {p['edge_target']}, {p['edge_type']} FROM {p['edge_table']} WHERE {p['edge_source']} IN ({placeholders})",
                    id_list,
                ).fetchall()
                for r in rows:
                    nid = str(r[0])
                    etype = str(r[1]).lower() if r[1] else "relates_to"
                    weight = EDGE_TYPE_WEIGHTS.get(etype, 0.5) * 1.0  # outgoing direction factor
                    boost[nid] = boost.get(nid, 0) + weight
            else:
                rows = conn.execute(
                    f"SELECT {p['edge_target']} FROM {p['edge_table']} WHERE {p['edge_source']} IN ({placeholders})",
                    id_list,
                ).fetchall()
                for r in rows:
                    nid = str(r[0])
                    boost[nid] = boost.get(nid, 0) + 0.5

            # 1-hop incoming
            if has_edge_type:
                rows = conn.execute(
                    f"SELECT {p['edge_source']}, {p['edge_type']} FROM {p['edge_table']} WHERE {p['edge_target']} IN ({placeholders})",
                    id_list,
                ).fetchall()
                for r in rows:
                    nid = str(r[0])
                    etype = str(r[1]).lower() if r[1] else "relates_to"
                    weight = EDGE_TYPE_WEIGHTS.get(etype, 0.5) * 0.7  # incoming direction factor
                    boost[nid] = boost.get(nid, 0) + weight
            else:
                rows = conn.execute(
                    f"SELECT {p['edge_source']} FROM {p['edge_table']} WHERE {p['edge_target']} IN ({placeholders})",
                    id_list,
                ).fetchall()
                for r in rows:
                    nid = str(r[0])
                    boost[nid] = boost.get(nid, 0) + 0.3

            # 2-hop for workflow/exploratory intents (decay 0.3x)
            if intent in ("workflow", "exploratory") and boost:
                hop1_ids = list(boost.keys())[:20]
                if hop1_ids:
                    ph2 = ",".join("?" for _ in hop1_ids)
                    rows2 = conn.execute(
                        f"SELECT {p['edge_target']} FROM {p['edge_table']} WHERE {p['edge_source']} IN ({ph2})",
                        hop1_ids,
                    ).fetchall()
                    for r in rows2:
                        nid = str(r[0])
                        if nid not in top_ids:
                            boost[nid] = boost.get(nid, 0) + 0.15  # 0.5 * 0.3 decay

        except sqlite3.OperationalError:
            pass

        # Blend with PageRank authority (30% PageRank, 70% proximity)
        pr = self._get_pagerank_scores(db_id)
        if pr:
            all_boosted = set(boost.keys()) | set(pr.keys())
            for nid in all_boosted:
                prox = boost.get(nid, 0)
                authority = pr.get(nid, 0)
                boost[nid] = prox * 0.7 + authority * 0.3

        # Normalize
        if boost:
            max_b = max(boost.values())
            if max_b > 0:
                boost = {k: v / max_b for k, v in boost.items()}
        return boost

    # ── PageRank authority scores (lazy-cached) ───────────────────
    def _get_pagerank_scores(self, db_id: str) -> dict[str, float]:
        if db_id in self._pagerank_cache:
            return self._pagerank_cache[db_id]
        if not _HAS_NETWORKX:
            return {}
        try:
            p = kg_service._detect_profile(db_id)
            conn = kg_service._get_conn(db_id)
            edge_count = conn.execute(f"SELECT COUNT(*) FROM {p['edge_table']}").fetchone()[0]
            if edge_count < 20:
                self._pagerank_cache[db_id] = {}
                return {}

            G = nx.DiGraph()
            rows = conn.execute(
                f"SELECT {p['edge_source']}, {p['edge_target']} FROM {p['edge_table']}"
            ).fetchall()
            for r in rows:
                G.add_edge(str(r[0]), str(r[1]))

            try:
                pr = nx.pagerank(G, alpha=0.85, max_iter=100)
            except nx.PowerIterationFailedConvergence:
                pr = nx.pagerank(G, alpha=0.85, max_iter=200, tol=1e-4)

            # Normalize to [0, 1]
            max_pr = max(pr.values()) if pr else 1
            pr = {k: v / max_pr for k, v in pr.items()}
            self._pagerank_cache[db_id] = pr
            return pr
        except Exception:
            self._pagerank_cache[db_id] = {}
            return {}

    # ── Intent edge scoring (delta component) ─────────────────────
    def _intent_edge_score(self, db_id: str, intent: str, seed_ids: set[str]) -> dict[str, float]:
        edge_types = INTENT_EDGE_MAP.get(intent, [])
        if not edge_types or not seed_ids:
            return {}
        p = kg_service._detect_profile(db_id)
        has_edge_type = p.get("edge_type") is not None
        if not has_edge_type:
            return {}

        conn = kg_service._get_conn(db_id)
        scores: dict[str, float] = {}
        placeholders = ",".join("?" for _ in seed_ids)
        type_placeholders = ",".join("?" for _ in edge_types)
        id_list = list(seed_ids)

        try:
            # Forward: seed → target via intent-relevant edge types (+1.0)
            rows = conn.execute(
                f"SELECT {p['edge_target']} FROM {p['edge_table']} "
                f"WHERE {p['edge_source']} IN ({placeholders}) AND LOWER({p['edge_type']}) IN ({type_placeholders})",
                id_list + edge_types,
            ).fetchall()
            for r in rows:
                nid = str(r[0])
                scores[nid] = scores.get(nid, 0) + 1.0

            # Backward: source → seed via intent-relevant edge types (+0.7)
            rows = conn.execute(
                f"SELECT {p['edge_source']} FROM {p['edge_table']} "
                f"WHERE {p['edge_target']} IN ({placeholders}) AND LOWER({p['edge_type']}) IN ({type_placeholders})",
                id_list + edge_types,
            ).fetchall()
            for r in rows:
                nid = str(r[0])
                scores[nid] = scores.get(nid, 0) + 0.7
        except sqlite3.OperationalError:
            pass

        # Normalize
        if scores:
            max_s = max(scores.values())
            if max_s > 0:
                scores = {k: v / max_s for k, v in scores.items()}
        return scores

    # ── Community diversity (lazy-cached) ─────────────────────────
    def _get_communities(self, db_id: str) -> list[set]:
        if db_id in self._community_cache:
            return self._community_cache[db_id]
        if not _HAS_NETWORKX:
            return []
        try:
            p = kg_service._detect_profile(db_id)
            conn = kg_service._get_conn(db_id)
            edge_count = conn.execute(f"SELECT COUNT(*) FROM {p['edge_table']}").fetchone()[0]
            if edge_count < 10:
                self._community_cache[db_id] = []
                return []

            G = nx.Graph()
            rows = conn.execute(
                f"SELECT {p['edge_source']}, {p['edge_target']} FROM {p['edge_table']}"
            ).fetchall()
            for r in rows:
                G.add_edge(str(r[0]), str(r[1]))

            try:
                comms = list(nx.community.greedy_modularity_communities(G))
            except Exception:
                comms = [set(c) for c in nx.weakly_connected_components(nx.DiGraph(G))]

            self._community_cache[db_id] = comms
            return comms
        except Exception:
            self._community_cache[db_id] = []
            return []

    def _diversify_results(self, db_id: str, results: list[dict]) -> list[dict]:
        """Rerank results for community diversity (MMR-style)."""
        if len(results) <= 3:
            return results
        comms = self._get_communities(db_id)
        if not comms or len(comms) < 2:
            return results

        # Map node_id → community index
        node_to_comm = {}
        for i, comm in enumerate(comms):
            for nid in comm:
                node_to_comm[nid] = i

        # Boost results from under-represented communities
        seen = set()
        for r in results:
            nid = str(r["node"].get("id", ""))
            comm = node_to_comm.get(nid, -1)
            if comm >= 0 and comm not in seen:
                r["score"] *= 1.05  # 5% novelty boost
            seen.add(comm)

        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    # ── Query cache ───────────────────────────────────────────────
    def _cache_key(self, db_id: str, query: str, mode: str, intent: str | None) -> str:
        return hashlib.md5(f"{db_id}:{query}:{mode}:{intent}".encode()).hexdigest()

    def invalidate_cache(self, db_id: str | None = None):
        """Invalidate query cache. Call after KG modifications."""
        if db_id:
            prefix = hashlib.md5(db_id.encode()).hexdigest()[:8]
            self._query_cache = {k: v for k, v in self._query_cache.items() if not k.startswith(prefix)}
            self._bm25_indices.pop(db_id, None)
            self._pagerank_cache.pop(db_id, None)
            self._community_cache.pop(db_id, None)
        else:
            self._query_cache.clear()
            self._bm25_indices.clear()
            self._pagerank_cache.clear()
            self._community_cache.clear()

    # ── Embedding search (numpy cosine similarity) ────────────────
    def _embedding_search(self, db_id: str, query: str, limit: int = 50) -> dict[str, float]:
        if not _HAS_NUMPY:
            return {}
        conn = kg_service._get_conn(db_id)
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        emb_table = None
        for t in ["embeddings", "node_embeddings", "vec_embeddings"]:
            if t in tables:
                emb_table = t
                break
        if not emb_table:
            return {}
        try:
            rows = conn.execute(f"SELECT node_id, embedding FROM {emb_table}").fetchall()
        except sqlite3.OperationalError:
            return {}
        if not rows:
            return {}

        ids = []
        vecs = []
        for r in rows:
            nid = str(r[0])
            emb_data = r[1]
            if isinstance(emb_data, bytes):
                vecs.append(_deserialize_f32(emb_data))
                ids.append(nid)
            elif isinstance(emb_data, str):
                try:
                    arr = json.loads(emb_data)
                    if isinstance(arr, list):
                        vecs.append(arr)
                        ids.append(nid)
                except (json.JSONDecodeError, TypeError):
                    pass
        if not vecs:
            return {}

        query_vec = self._get_query_embedding(query, len(vecs[0]))
        if query_vec is None:
            return {}

        mat = np.array(vecs, dtype=np.float32)
        qvec = np.array(query_vec, dtype=np.float32)
        mat_norms = np.linalg.norm(mat, axis=1)
        mat_norms[mat_norms == 0] = 1.0
        q_norm = np.linalg.norm(qvec)
        if q_norm == 0:
            return {}
        similarities = (mat @ qvec) / (mat_norms * q_norm)

        top_indices = np.argsort(similarities)[::-1][:limit]
        result = {}
        for idx in top_indices:
            score = float(similarities[idx])
            if score > 0:
                result[ids[idx]] = score
        return result

    def _load_model2vec(self):
        if self._model2vec_model is not None:
            return self._model2vec_model
        if not _HAS_MODEL2VEC:
            return None
        try:
            self._model2vec_model = StaticModel.from_pretrained("minishlab/potion-base-8M")
            return self._model2vec_model
        except Exception:
            return None

    def _get_query_embedding(self, query: str, expected_dims: int) -> list[float] | None:
        if expected_dims == 256:
            model = self._load_model2vec()
            if model is not None:
                vec = model.encode([query])[0]
                return vec.tolist()

        try:
            from config import GEMINI_API_KEY
            if GEMINI_API_KEY:
                from google import genai
                client = genai.Client(api_key=GEMINI_API_KEY)
                result = client.models.embed_content(
                    model="gemini-embedding-001",
                    contents=[query],
                )
                return result.embeddings[0].values
        except Exception:
            pass

        model = self._load_model2vec()
        if model is not None:
            vec = model.encode([query])[0]
            vec_list = vec.tolist()
            if len(vec_list) < expected_dims:
                vec_list.extend([0.0] * (expected_dims - len(vec_list)))
            elif len(vec_list) > expected_dims:
                vec_list = vec_list[:expected_dims]
            return vec_list

        return None

    # ── Hybrid search (4-weight intent-adaptive formula) ──────────
    def search(self, db_id: str, query: str, mode: str = "hybrid",
               limit: int = 20, alpha: float | None = None, beta: float | None = None,
               gamma: float | None = None, intent: str | None = None) -> dict:

        # Intent-adaptive weights when no explicit weights passed
        if alpha is None and beta is None and gamma is None:
            detected_intent = intent or self._classify_search_intent(query)
            profile = INTENT_WEIGHT_PROFILES.get(detected_intent, DEFAULT_PROFILE)
            alpha = profile["alpha"]
            beta = profile["beta"]
            gamma = profile["gamma"]
            delta = profile.get("delta", 0)
        else:
            alpha = alpha if alpha is not None else 0.40
            beta = beta if beta is not None else 0.45
            gamma = gamma if gamma is not None else 0.15
            delta = 0
            detected_intent = intent or self._classify_search_intent(query)

        # Check query cache
        cache_key = self._cache_key(db_id, query, mode, detected_intent)
        if cache_key in self._query_cache:
            cached, ts = self._query_cache[cache_key]
            if time.time() - ts < self._cache_ttl:
                return cached

        # Get intent keywords for BM25 5x boost
        kw = INTENT_KEYWORDS.get(detected_intent, set()) if detected_intent else set()

        bm25_scores = {}
        fts_scores = {}
        emb_scores = {}

        if mode in ("hybrid", "fts"):
            bm25_idx = self._build_bm25_index(db_id)
            bm25_scores = self._bm25_score(bm25_idx, query, intent_keywords=kw)
            fts_scores = self._fts_search(db_id, query, limit * 3)

        if mode in ("hybrid", "embedding"):
            emb_scores = self._embedding_search(db_id, query, limit * 3)

        # Combine BM25 + FTS into single text score
        text_scores: dict[str, float] = {}
        all_text_ids = set(bm25_scores) | set(fts_scores)
        if all_text_ids:
            max_bm25 = max(bm25_scores.values()) if bm25_scores else 1
            max_fts = max(fts_scores.values()) if fts_scores else 1
            for nid in all_text_ids:
                s1 = bm25_scores.get(nid, 0) / max_bm25 if max_bm25 else 0
                s2 = fts_scores.get(nid, 0) / max_fts if max_fts else 0
                text_scores[nid] = max(s1, s2)

        # Normalize embedding scores
        if emb_scores:
            max_emb = max(emb_scores.values()) if emb_scores else 1
            emb_scores = {k: v / max_emb for k, v in emb_scores.items()}

        # Graph boost from top text AND embedding results (type-aware + PageRank)
        top_text_ids = sorted(text_scores, key=text_scores.get, reverse=True)[:10]
        top_emb_ids = sorted(emb_scores, key=emb_scores.get, reverse=True)[:10] if emb_scores else []
        boost_seed_ids = set(top_text_ids) | set(top_emb_ids)
        graph_scores = self._graph_boost(db_id, boost_seed_ids, intent=detected_intent)

        # Intent edge scoring (delta component)
        intent_scores: dict[str, float] = {}
        if delta > 0 and detected_intent:
            intent_scores = self._intent_edge_score(db_id, detected_intent, boost_seed_ids)

        # Combine: score = alpha*embedding + beta*text + gamma*graph + delta*intent
        all_ids = set(text_scores) | set(emb_scores) | set(graph_scores) | set(intent_scores)
        final_scores: dict[str, float] = {}
        for nid in all_ids:
            score = (
                alpha * emb_scores.get(nid, 0) +
                beta * text_scores.get(nid, 0) +
                gamma * graph_scores.get(nid, 0) +
                delta * intent_scores.get(nid, 0)
            )
            if score > 0:
                final_scores[nid] = score

        # Sort and fetch node data
        sorted_ids = sorted(final_scores, key=final_scores.get, reverse=True)[:limit]
        results = []
        for nid in sorted_ids:
            node = kg_service.get_node(db_id, nid)
            if node:
                method_parts = []
                if nid in text_scores:
                    method_parts.append("text")
                if nid in emb_scores:
                    method_parts.append("embedding")
                if nid in graph_scores:
                    method_parts.append("graph")
                if nid in intent_scores:
                    method_parts.append("intent")
                results.append({
                    "node": node,
                    "score": final_scores[nid],
                    "method": "+".join(method_parts),
                })

        # Community-aware diversity reranking
        results = self._diversify_results(db_id, results)

        result = {
            "results": results,
            "query": query,
            "mode": mode,
            "total": len(results),
            "intent": detected_intent,
            "weights": {"alpha": alpha, "beta": beta, "gamma": gamma, "delta": delta},
        }

        # Cache result
        self._query_cache[cache_key] = (result, time.time())
        return result

    # ── Status ──────────────────────────────────────────────────────
    def get_status(self, db_id: str) -> dict:
        conn = kg_service._get_conn(db_id)
        p = kg_service._detect_profile(db_id)
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}

        has_emb = False
        count = 0
        dims = None
        total_nodes = conn.execute(f"SELECT COUNT(*) FROM {p['node_table']}").fetchone()[0]

        for t in ["embeddings", "node_embeddings", "vec_embeddings"]:
            if t in tables:
                try:
                    count = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                    if count > 0:
                        has_emb = True
                        row = conn.execute(f"SELECT * FROM {t} LIMIT 1").fetchone()
                        if row:
                            for val in dict(row).values():
                                if isinstance(val, bytes):
                                    dims = len(val) // 4
                                    break
                                elif isinstance(val, str):
                                    try:
                                        arr = json.loads(val)
                                        if isinstance(arr, list):
                                            dims = len(arr)
                                            break
                                    except (json.JSONDecodeError, TypeError):
                                        pass
                except sqlite3.OperationalError:
                    pass
                break

        strategies = ["fts"]
        if _HAS_SQLITE_VEC:
            strategies.append("sqlite_vec")
        if _HAS_NUMPY:
            strategies.append("numpy_cosine")
        if _HAS_MODEL2VEC:
            strategies.append("model2vec")
        strategies.append("gemini")

        return {
            "has_embeddings": has_emb,
            "count": count,
            "dimensions": dims,
            "coverage_pct": round(count / max(total_nodes, 1) * 100, 1),
            "strategies_available": strategies,
        }

    # ── Generate embeddings ─────────────────────────────────────────
    async def generate_embeddings(self, db_id: str, strategy: str = "gemini") -> dict:
        conn = kg_service._get_conn(db_id)
        p = kg_service._detect_profile(db_id)
        rows = conn.execute(
            f"SELECT {p['node_id']}, {p['node_name']}, {p['node_type']} FROM {p['node_table']}"
        ).fetchall()

        if strategy == "model2vec":
            return self._generate_model2vec(db_id, conn, rows, p)
        elif strategy == "gemini":
            return await self._generate_gemini(db_id, conn, rows, p)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    def _generate_model2vec(self, db_id: str, conn, rows, p) -> dict:
        model = self._load_model2vec()
        if model is None:
            raise ImportError("model2vec not available")

        texts = [f"{r[1]} {r[2]}" for r in rows]
        ids = [str(r[0]) for r in rows]
        embeddings = model.encode(texts)

        conn.execute("CREATE TABLE IF NOT EXISTS embeddings (node_id TEXT PRIMARY KEY, embedding BLOB)")
        for nid, emb in zip(ids, embeddings):
            blob = _serialize_f32(emb.tolist())
            conn.execute("INSERT OR REPLACE INTO embeddings (node_id, embedding) VALUES (?, ?)", (nid, blob))
        conn.commit()

        self.invalidate_cache(db_id)
        return {"strategy": "model2vec", "count": len(ids), "dimensions": embeddings.shape[1]}

    async def _generate_gemini(self, db_id: str, conn, rows, p) -> dict:
        from config import GEMINI_API_KEY
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not configured")

        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)

        texts = [f"{r[1]} {r[2]}" for r in rows]
        ids = [str(r[0]) for r in rows]

        conn.execute("CREATE TABLE IF NOT EXISTS embeddings (node_id TEXT PRIMARY KEY, embedding BLOB)")
        dims = None
        batch_size = 100
        total = 0

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_ids = ids[i:i + batch_size]
            result = client.models.embed_content(
                model="gemini-embedding-001",
                contents=batch_texts,
            )
            for nid, emb_obj in zip(batch_ids, result.embeddings):
                vec = emb_obj.values
                dims = len(vec)
                blob = _serialize_f32(vec)
                conn.execute("INSERT OR REPLACE INTO embeddings (node_id, embedding) VALUES (?, ?)", (nid, blob))
            total += len(batch_ids)

        conn.commit()
        self.invalidate_cache(db_id)
        return {"strategy": "gemini", "count": total, "dimensions": dims}

    # ── Projection (2D) ─────────────────────────────────────────────
    def get_projection(self, db_id: str, method: str = "pca", max_points: int = 500) -> dict:
        conn = kg_service._get_conn(db_id)
        p = kg_service._detect_profile(db_id)

        try:
            rows = conn.execute("SELECT node_id, embedding FROM embeddings LIMIT ?", (max_points,)).fetchall()
        except sqlite3.OperationalError:
            return {"points": [], "method": method}

        if not rows or not _HAS_NUMPY:
            return {"points": [], "method": method}

        ids = [str(r[0]) for r in rows]
        vecs = [_deserialize_f32(r[1]) for r in rows if isinstance(r[1], bytes)]
        if not vecs:
            return {"points": [], "method": method}

        mat = np.array(vecs)

        if method == "pca":
            centered = mat - mat.mean(axis=0)
            cov = np.cov(centered.T)
            eigenvalues, eigenvectors = np.linalg.eigh(cov)
            idx_sorted = np.argsort(eigenvalues)[::-1]
            top2 = eigenvectors[:, idx_sorted[:2]]
            projected = centered @ top2
        else:
            n = len(vecs)
            projected = np.random.randn(n, 2) * 10
            for _ in range(50):
                for i in range(n):
                    dists = np.sum((mat[i] - mat) ** 2, axis=1)
                    nearest = np.argsort(dists)[1:6]
                    for j in nearest:
                        diff = projected[j] - projected[i]
                        projected[i] += diff * 0.01
                        projected[j] -= diff * 0.01
            projected -= projected.mean(axis=0)

        points = []
        for i, nid in enumerate(ids[:len(projected)]):
            node = kg_service.get_node(db_id, nid)
            if node:
                points.append({
                    "id": nid,
                    "name": node["name"],
                    "type": node["type"],
                    "x": float(projected[i][0]),
                    "y": float(projected[i][1]),
                })

        return {"points": points, "method": method}

    # ── Quality metrics ─────────────────────────────────────────────
    def get_quality_metrics(self, db_id: str) -> dict:
        conn = kg_service._get_conn(db_id)
        p = kg_service._detect_profile(db_id)
        total_nodes = conn.execute(f"SELECT COUNT(*) FROM {p['node_table']}").fetchone()[0]

        try:
            emb_count = conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
        except sqlite3.OperationalError:
            return {"coverage": 0, "count": 0, "total_nodes": total_nodes}

        if not _HAS_NUMPY or emb_count == 0:
            return {"coverage": round(emb_count / max(total_nodes, 1) * 100, 1), "count": emb_count,
                    "total_nodes": total_nodes}

        rows = conn.execute("SELECT embedding FROM embeddings LIMIT 100").fetchall()
        vecs = [_deserialize_f32(r[0]) for r in rows if isinstance(r[0], bytes)]
        if len(vecs) < 2:
            return {"coverage": round(emb_count / max(total_nodes, 1) * 100, 1), "count": emb_count,
                    "total_nodes": total_nodes}

        mat = np.array(vecs)
        norms = np.linalg.norm(mat, axis=1, keepdims=True)
        norms[norms == 0] = 1
        normed = mat / norms
        sims = normed @ normed.T
        np.fill_diagonal(sims, 0)
        upper = sims[np.triu_indices_from(sims, k=1)]

        return {
            "coverage": round(emb_count / max(total_nodes, 1) * 100, 1),
            "count": emb_count,
            "total_nodes": total_nodes,
            "avg_cosine_similarity": round(float(np.mean(upper)), 4),
            "min_cosine_similarity": round(float(np.min(upper)), 4),
            "max_cosine_similarity": round(float(np.max(upper)), 4),
            "std_cosine_similarity": round(float(np.std(upper)), 4),
        }


# Singleton
embedding_service = EmbeddingService()

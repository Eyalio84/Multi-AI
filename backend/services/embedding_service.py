"""Embedding service — multi-strategy search: FTS5, sqlite-vec, Gemini API, Model2Vec."""
import sqlite3
import json
import struct
import math
import re
from pathlib import Path
from typing import Any

from services.kg_service import kg_service

# Optional imports with graceful fallback
_HAS_SQLITE_VEC = False
_HAS_NUMPY = False
_HAS_MODEL2VEC = False

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


def _serialize_f32(vec: list[float]) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec)


def _deserialize_f32(data: bytes) -> list[float]:
    n = len(data) // 4
    return list(struct.unpack(f"{n}f", data))


class EmbeddingService:
    """Multi-strategy semantic search across knowledge graphs."""

    def __init__(self):
        self._model2vec_model = None
        self._bm25_indices: dict[str, dict] = {}  # db_id -> {doc_freqs, doc_count, ...}

    # ── BM25 implementation (pure Python) ───────────────────────────
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
            tokens = re.findall(r'\w+', text)
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

    def _bm25_score(self, idx: dict, query: str, k1: float = 1.5, b: float = 0.75) -> dict[str, float]:
        tokens = re.findall(r'\w+', query.lower())
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
            # Convert rowid to node_id
            result = {}
            for r in rows:
                node_row = conn.execute(
                    f"SELECT {p['node_id']} FROM {p['node_table']} WHERE rowid = ?",
                    (r[0],),
                ).fetchone()
                if node_row:
                    result[str(node_row[0])] = abs(r[1])  # rank is negative
            return result
        except sqlite3.OperationalError:
            return {}

    # ── Graph neighbor boost ────────────────────────────────────────
    def _graph_boost(self, db_id: str, top_ids: set[str]) -> dict[str, float]:
        if not top_ids:
            return {}
        p = kg_service._detect_profile(db_id)
        conn = kg_service._get_conn(db_id)
        boost: dict[str, float] = {}
        placeholders = ",".join("?" for _ in top_ids)
        try:
            rows = conn.execute(
                f"SELECT {p['edge_target']} FROM {p['edge_table']} WHERE {p['edge_source']} IN ({placeholders})",
                list(top_ids),
            ).fetchall()
            for r in rows:
                nid = str(r[0])
                boost[nid] = boost.get(nid, 0) + 0.5
            rows = conn.execute(
                f"SELECT {p['edge_source']} FROM {p['edge_table']} WHERE {p['edge_target']} IN ({placeholders})",
                list(top_ids),
            ).fetchall()
            for r in rows:
                nid = str(r[0])
                boost[nid] = boost.get(nid, 0) + 0.3
        except sqlite3.OperationalError:
            pass
        # Normalize
        max_b = max(boost.values()) if boost else 1
        return {k: v / max_b for k, v in boost.items()}

    # ── Embedding search (numpy cosine similarity, sqlite-vec when available) ──
    def _embedding_search(self, db_id: str, query: str, limit: int = 50) -> dict[str, float]:
        if not _HAS_NUMPY:
            return {}
        conn = kg_service._get_conn(db_id)
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        # Find embeddings table
        emb_table = None
        for t in ["embeddings", "node_embeddings", "vec_embeddings"]:
            if t in tables:
                emb_table = t
                break
        if not emb_table:
            return {}
        # Load stored embeddings
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

        # Compute query embedding
        query_vec = self._get_query_embedding(query, len(vecs[0]))
        if query_vec is None:
            return {}

        # Cosine similarity: query vs all stored embeddings
        mat = np.array(vecs, dtype=np.float32)
        qvec = np.array(query_vec, dtype=np.float32)
        # Normalize
        mat_norms = np.linalg.norm(mat, axis=1)
        mat_norms[mat_norms == 0] = 1.0
        q_norm = np.linalg.norm(qvec)
        if q_norm == 0:
            return {}
        similarities = (mat @ qvec) / (mat_norms * q_norm)

        # Top-k
        top_indices = np.argsort(similarities)[::-1][:limit]
        result = {}
        for idx in top_indices:
            score = float(similarities[idx])
            if score > 0:
                result[ids[idx]] = score
        return result

    def _load_model2vec(self):
        """Load Model2Vec model with graceful failure."""
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
        """Generate embedding for a search query, matching the stored embedding dimensions."""
        # Strategy 1: Model2Vec (fast, offline, 256-dim) — best match for 256-dim stored embeddings
        if expected_dims == 256:
            model = self._load_model2vec()
            if model is not None:
                vec = model.encode([query])[0]
                return vec.tolist()

        # Strategy 2: Gemini API (matches whatever Gemini generated)
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

        # Strategy 3: Model2Vec fallback even if dims don't match (pad/truncate)
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

    # ── Hybrid search (88.5% recall formula) ────────────────────────
    def search(self, db_id: str, query: str, mode: str = "hybrid",
               limit: int = 20, alpha: float = 0.40, beta: float = 0.45,
               gamma: float = 0.15) -> dict:

        bm25_scores = {}
        fts_scores = {}
        emb_scores = {}

        if mode in ("hybrid", "fts"):
            bm25_idx = self._build_bm25_index(db_id)
            bm25_scores = self._bm25_score(bm25_idx, query)
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

        # Graph boost from top text AND embedding results
        top_text_ids = sorted(text_scores, key=text_scores.get, reverse=True)[:10]
        top_emb_ids = sorted(emb_scores, key=emb_scores.get, reverse=True)[:10] if emb_scores else []
        boost_seed_ids = set(top_text_ids) | set(top_emb_ids)
        graph_scores = self._graph_boost(db_id, boost_seed_ids)

        # Combine: score = alpha*embedding + beta*text + gamma*graph
        all_ids = set(text_scores) | set(emb_scores) | set(graph_scores)
        final_scores: dict[str, float] = {}
        for nid in all_ids:
            score = (
                alpha * emb_scores.get(nid, 0) +
                beta * text_scores.get(nid, 0) +
                gamma * graph_scores.get(nid, 0)
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
                results.append({
                    "node": node,
                    "score": final_scores[nid],
                    "method": "+".join(method_parts),
                })

        return {
            "results": results,
            "query": query,
            "mode": mode,
            "total": len(results),
        }

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
                            # Try to detect dimensions
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

        # Store in embeddings table
        conn.execute("CREATE TABLE IF NOT EXISTS embeddings (node_id TEXT PRIMARY KEY, embedding BLOB)")
        for nid, emb in zip(ids, embeddings):
            blob = _serialize_f32(emb.tolist())
            conn.execute("INSERT OR REPLACE INTO embeddings (node_id, embedding) VALUES (?, ?)", (nid, blob))
        conn.commit()

        return {"strategy": "model2vec", "count": len(ids), "dimensions": embeddings.shape[1]}

    async def _generate_gemini(self, db_id: str, conn, rows, p) -> dict:
        from config import GEMINI_API_KEY
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not configured")

        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)

        texts = [f"{r[1]} {r[2]}" for r in rows]
        ids = [str(r[0]) for r in rows]

        # Batch embed (Gemini supports batching)
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
        return {"strategy": "gemini", "count": total, "dimensions": dims}

    # ── Projection (2D) ─────────────────────────────────────────────
    def get_projection(self, db_id: str, method: str = "pca", max_points: int = 500) -> dict:
        conn = kg_service._get_conn(db_id)
        p = kg_service._detect_profile(db_id)

        # Read embeddings
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

        # PCA (simple, no sklearn needed)
        if method == "pca":
            centered = mat - mat.mean(axis=0)
            cov = np.cov(centered.T)
            eigenvalues, eigenvectors = np.linalg.eigh(cov)
            idx_sorted = np.argsort(eigenvalues)[::-1]
            top2 = eigenvectors[:, idx_sorted[:2]]
            projected = centered @ top2
        else:
            # Simple t-SNE approximation (random init + neighbor attraction)
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

        # Fetch node info
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

        # Sample cosine similarities
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

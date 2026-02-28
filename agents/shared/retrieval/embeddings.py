#!/usr/bin/env python3
"""
Embedding Manager — Unified Retrieval Layer

Multi-backend embedding system with auto-detection:
  - HashEmbedder: Zero-cost 256D vectors via character n-gram hashing (always available)
  - ContextualEmbedder: Loads pre-trained serialized embeddings when available
  - EmbeddingManager: Facade that auto-detects best available backend

No external dependencies beyond stdlib + numpy.

Level 2 dependency — imports from config.py, db_adapter.py.

Created: February 8, 2026
"""

import hashlib
import os
import json
from typing import Dict, List, Optional, Tuple

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    from .config import EmbeddingBackend, RetrievalConfig
    from .db_adapter import KGAdapter, KGNode
except ImportError:
    from config import EmbeddingBackend, RetrievalConfig
    from db_adapter import KGAdapter, KGNode


# ============================================================================
# Hash Embedder (Zero-dependency fallback)
# ============================================================================

class HashEmbedder:
    """Character n-gram hash embedding encoder.

    Generates deterministic embedding vectors by hashing character n-grams
    and accumulating into a fixed-dimension vector. Zero external dependencies.

    Quality is lower than trained embeddings but provides meaningful
    similarity signal for keyword-rich KG nodes.
    """

    def __init__(self, dim: int = 256, ngram_range: Tuple[int, int] = (2, 4)):
        self.dim = dim
        self.ngram_range = ngram_range
        self.node_embeddings: Dict[str, "np.ndarray"] = {}

    def encode_text(self, text: str) -> "np.ndarray":
        """Encode text to embedding vector via character n-gram hashing."""
        if not HAS_NUMPY:
            return None

        vec = np.zeros(self.dim, dtype=np.float32)
        text_lower = text.lower().strip()

        if not text_lower:
            return vec

        # Extract character n-grams and hash them
        for n in range(self.ngram_range[0], self.ngram_range[1] + 1):
            for i in range(len(text_lower) - n + 1):
                ngram = text_lower[i:i + n]
                h = int(hashlib.md5(ngram.encode()).hexdigest(), 16)
                idx = h % self.dim
                sign = 1.0 if (h >> 17) & 1 else -1.0  # Random sign
                vec[idx] += sign

        # L2 normalize
        norm = np.linalg.norm(vec)
        if norm > 1e-8:
            vec = vec / norm

        return vec

    def index_nodes(self, nodes: List[KGNode]) -> int:
        """Encode and cache embeddings for all nodes."""
        if not HAS_NUMPY:
            return 0

        count = 0
        for node in nodes:
            text = f"{node.name} {node.description}"
            if text.strip():
                self.node_embeddings[node.node_id] = self.encode_text(text)
                count += 1
        return count

    def find_nearest(self, query_embedding: "np.ndarray", k: int = 10) -> List[Tuple[str, float]]:
        """Find k nearest neighbors by cosine similarity."""
        if not HAS_NUMPY or not self.node_embeddings:
            return []

        similarities = []
        for node_id, node_emb in self.node_embeddings.items():
            sim = float(np.dot(query_embedding, node_emb))
            similarities.append((node_id, sim))

        similarities.sort(key=lambda x: -x[1])
        return similarities[:k]

    @property
    def quality(self) -> str:
        return "hash"


# ============================================================================
# Contextual Embedder (Pre-trained, when available)
# ============================================================================

class ContextualEmbedder:
    """Loads pre-trained embeddings from serialized files.

    Looks for numpy .npy or JSON embedding files alongside KG databases.
    Falls back to HashEmbedder if no pre-trained embeddings found.
    """

    def __init__(self, dim: int = 256):
        self.dim = dim
        self.node_embeddings: Dict[str, "np.ndarray"] = {}
        self._loaded = False

    def load_embeddings(self, embedding_path: str) -> int:
        """Load pre-trained embeddings from .npy or .json file.

        Returns number of embeddings loaded.
        """
        if not HAS_NUMPY:
            return 0

        if not os.path.exists(embedding_path):
            return 0

        try:
            if embedding_path.endswith(".npy"):
                data = np.load(embedding_path, allow_pickle=False)
                self._loaded = True
                return len(data)

            elif embedding_path.endswith(".json"):
                with open(embedding_path, "r") as f:
                    data = json.load(f)
                for node_id, vec in data.items():
                    self.node_embeddings[node_id] = np.array(vec, dtype=np.float32)
                self._loaded = True
                return len(self.node_embeddings)

        except Exception:
            pass

        return 0

    def find_nearest(self, query_embedding: "np.ndarray", k: int = 10) -> List[Tuple[str, float]]:
        """Find k nearest neighbors."""
        if not self.node_embeddings:
            return []

        similarities = []
        for node_id, node_emb in self.node_embeddings.items():
            sim = float(np.dot(query_embedding, node_emb))
            similarities.append((node_id, sim))

        similarities.sort(key=lambda x: -x[1])
        return similarities[:k]

    @property
    def quality(self) -> str:
        return "semantic" if self._loaded else "untrained"


# ============================================================================
# Embedding Manager (Facade)
# ============================================================================

class EmbeddingManager:
    """Unified embedding interface with auto-detection of best backend.

    Priority: FAISS > contextual (pre-trained) > hash (always available).

    Adapted from contextual_embeddings.py inference path.
    """

    def __init__(self, config: Optional[RetrievalConfig] = None):
        self.config = config or RetrievalConfig()
        self._hash = HashEmbedder(
            dim=self.config.embedding_dim,
            ngram_range=self.config.ngram_range,
        )
        self._contextual = ContextualEmbedder(dim=self.config.embedding_dim)
        self._backend: EmbeddingBackend = EmbeddingBackend.HASH
        self._indexed = False

    def index_nodes(self, nodes: List[KGNode], embedding_path: Optional[str] = None) -> int:
        """Index nodes with best available backend.

        Args:
            nodes: List of KGNode objects to index
            embedding_path: Optional path to pre-trained embeddings

        Returns:
            Number of nodes indexed
        """
        # Try contextual first
        if embedding_path:
            count = self._contextual.load_embeddings(embedding_path)
            if count > 0:
                self._backend = EmbeddingBackend.CONTEXTUAL
                self._indexed = True
                # Also build hash index as fallback for nodes not in pre-trained
                self._hash.index_nodes(nodes)
                return count

        # Fall back to hash embeddings
        count = self._hash.index_nodes(nodes)
        self._backend = EmbeddingBackend.HASH
        self._indexed = True
        return count

    def index_from_adapter(self, adapter: KGAdapter, embedding_path: Optional[str] = None) -> int:
        """Index all nodes from a database adapter."""
        nodes = adapter.get_all_nodes()
        return self.index_nodes(nodes, embedding_path)

    def encode_query(self, query: str) -> Optional["np.ndarray"]:
        """Encode a query string to embedding vector."""
        if not HAS_NUMPY:
            return None
        return self._hash.encode_text(query)

    def search(self, query: str, k: int = 10) -> List[Tuple[str, float]]:
        """Search for nearest nodes to query.

        Returns list of (node_id, similarity_score) normalized to [0, 1].
        """
        if not self._indexed or not HAS_NUMPY:
            return []

        query_emb = self.encode_query(query)
        if query_emb is None:
            return []

        # Use best available backend
        if self._backend == EmbeddingBackend.CONTEXTUAL and self._contextual.node_embeddings:
            results = self._contextual.find_nearest(query_emb, k)
        else:
            results = self._hash.find_nearest(query_emb, k)

        if not results:
            return []

        # Normalize scores to [0, 1]
        scores = [s for _, s in results]
        min_s, max_s = min(scores), max(scores)
        range_s = max_s - min_s if max_s > min_s else 1.0

        normalized = []
        for nid, s in results:
            norm_s = (s - min_s) / range_s if range_s > 0 else 0.5
            normalized.append((nid, norm_s))

        return normalized

    @property
    def quality(self) -> str:
        """Report embedding quality level for weight auto-adjustment."""
        if self._backend == EmbeddingBackend.FAISS:
            return "semantic"
        elif self._backend == EmbeddingBackend.CONTEXTUAL:
            return self._contextual.quality
        return "hash"

    @property
    def backend(self) -> EmbeddingBackend:
        return self._backend

    @property
    def node_count(self) -> int:
        if self._backend == EmbeddingBackend.CONTEXTUAL:
            return len(self._contextual.node_embeddings)
        return len(self._hash.node_embeddings)


# ============================================================================
# Self-test
# ============================================================================

if __name__ == "__main__":
    from config import KG_DATABASES
    from db_adapter import KGAdapter

    print("embeddings.py — Embedding Manager self-test")
    print("=" * 60)
    print(f"numpy available: {HAS_NUMPY}")

    if not HAS_NUMPY:
        print("SKIP: numpy not available")
        exit(0)

    # Test HashEmbedder
    hasher = HashEmbedder(dim=256)
    v1 = hasher.encode_text("prompt caching optimization")
    v2 = hasher.encode_text("prompt cache cost reduction")
    v3 = hasher.encode_text("batch API processing")
    sim_12 = float(np.dot(v1, v2))
    sim_13 = float(np.dot(v1, v3))
    print(f"\nHashEmbedder (dim=256):")
    print(f"  'prompt caching optimization' vs 'prompt cache cost reduction': {sim_12:.3f}")
    print(f"  'prompt caching optimization' vs 'batch API processing':       {sim_13:.3f}")
    assert sim_12 > sim_13, "Similar queries should have higher similarity"

    # Test EmbeddingManager with real KG
    manager = EmbeddingManager()
    db_path = KG_DATABASES["claude_cookbook"]
    adapter = KGAdapter(db_path)
    if adapter.connect():
        count = manager.index_from_adapter(adapter)
        print(f"\nEmbeddingManager: indexed {count} nodes from claude-cookbook-kg.db")
        print(f"  Backend: {manager.backend.value}")
        print(f"  Quality: {manager.quality}")

        results = manager.search("prompt caching cost optimization", k=5)
        print(f"\nSearch 'prompt caching cost optimization':")
        for nid, score in results:
            node = adapter.get_node(nid)
            name = node.name if node else nid
            print(f"  {score:.3f}  {name}")

        adapter.close()

    print("\nembeddings.py OK")

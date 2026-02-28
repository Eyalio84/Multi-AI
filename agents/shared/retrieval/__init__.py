"""
Unified Retrieval Layer — agents.shared.retrieval

3-path hybrid fusion retrieval for KGs:
    H(q,n) = alpha * V(q,n) + beta * B(q,n) + gamma * G(q,n)

2-path hybrid fusion for memory:
    score = alpha * V(q,chunk) + beta * B(q,chunk)

Usage:
    from agents.shared.retrieval import HybridFusion, RetrievalConfig

    fusion = HybridFusion()
    fusion.index()
    results = fusion.query("prompt caching cost optimization", k=10)

    from agents.shared.retrieval import MemoryFusion

    mf = MemoryFusion("/path/to/memory")
    mf.index()
    results = mf.query("what decision about node IDs?")

Created: February 8, 2026
"""

# Level 0: Foundation
from .config import RetrievalConfig, EmbeddingBackend, EDGE_WEIGHTS, KG_DATABASES, KG_SCHEMAS
from .stopwords import STOPWORDS, tokenize_and_filter
from .query_cache import QueryCache, CacheMetrics

# Level 1: Adapters & Profiles
from .db_adapter import KGAdapter, KGNode, KGEdge, SchemaType, detect_schema
from .weight_profiles import QueryIntent, WeightProfile, INTENT_WEIGHTS, get_weights

# Level 2: Scoring Engines
from .bm25 import BM25Index
from .embeddings import EmbeddingManager, HashEmbedder, HAS_NUMPY
from .graph_scorer import GraphScorer

# Level 3: Routing
from .intent_router import IntentRouter, GOAL_TO_TOOLS, TARGETED_EXPANSIONS

# Level 4: Fusion
from .hybrid_fusion import HybridFusion, RetrievalResult

# Level 5: Memory
from .memory_parser import MemoryChunk, MemoryResult, parse_markdown_sections, scan_memory_directory
from .memory_fusion import MemoryFusion

__version__ = "1.1.0"

__all__ = [
    # Core engine
    "HybridFusion",
    "RetrievalResult",
    "RetrievalConfig",
    # Scoring engines
    "BM25Index",
    "EmbeddingManager",
    "HashEmbedder",
    "GraphScorer",
    # Routing
    "IntentRouter",
    "QueryIntent",
    "WeightProfile",
    # Data models
    "KGAdapter",
    "KGNode",
    "KGEdge",
    # Utilities
    "QueryCache",
    "STOPWORDS",
    "tokenize_and_filter",
    "get_weights",
    # Memory
    "MemoryFusion",
    "MemoryChunk",
    "MemoryResult",
    "parse_markdown_sections",
    "scan_memory_directory",
    # Constants
    "EDGE_WEIGHTS",
    "KG_DATABASES",
    "GOAL_TO_TOOLS",
    "TARGETED_EXPANSIONS",
    "HAS_NUMPY",
]

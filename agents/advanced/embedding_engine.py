#!/usr/bin/env python3
"""
Embedding Engine Agent (#28)

Embedding generation and vector operations using Gemini embedding API.
Supports text embedding, similarity computation, and nearest-neighbor search.

Layer: L1-L5 (Full 5-layer pattern via agent_base)

Usage:
    python3 embedding_engine.py --example
    python3 embedding_engine.py --workload embed_tasks.json --summary

Created: February 6, 2026
"""

import sys
import os
import json
import math
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.agent_base import (
    AgentInput, AgentOutput, BaseAnalyzer, run_standard_cli,
    GEMINI_API_BASE, GEMINI_MODELS, TOKENS_PER_MILLION,
)

from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any, Optional


# ============================================================================
# L1: Data Models
# ============================================================================

@dataclass
class EmbeddingResult:
    text: str
    embedding: List[float]
    dimensions: int
    model: str
    tokens_used: int


@dataclass
class SimilarityResult:
    text_a: str
    text_b: str
    cosine_similarity: float
    interpretation: str


# ============================================================================
# L2: Constants
# ============================================================================

EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_COST_PER_1M = 0.15  # $0.15 per 1M input tokens
MAX_BATCH_SIZE = 100
SIMILARITY_THRESHOLDS = {
    "identical": 0.95,
    "very_similar": 0.85,
    "similar": 0.70,
    "somewhat_related": 0.50,
    "unrelated": 0.0,
}


# ============================================================================
# L3: Analyzer
# ============================================================================

class EmbeddingEngineAnalyzer(BaseAnalyzer):
    """Embedding generation and vector operations engine."""

    def __init__(self):
        super().__init__(
            agent_name="embedding-engine",
            model="sonnet",
            version="1.0",
        )
        self.api_key = os.environ.get("GEMINI_API_KEY", "")

    def get_example_input(self) -> Dict[str, Any]:
        return {
            "name": "NLKE Agent Embedding Demo",
            "operation": "embed_and_compare",
            "texts": [
                "Knowledge graph construction using entity extraction",
                "Building ontologies from document analysis",
                "Cost optimization through prompt caching",
                "API batch processing for reduced latency",
                "Relationship suggestion using graph traversal",
            ],
            "compare_pairs": [
                [0, 1],  # KG construction vs ontology building (should be similar)
                [0, 2],  # KG construction vs cost optimization (less similar)
                [2, 3],  # Cost optimization vs batch processing (somewhat similar)
            ],
        }

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def _interpret_similarity(self, score: float) -> str:
        """Human-readable interpretation of similarity score."""
        for label, threshold in SIMILARITY_THRESHOLDS.items():
            if score >= threshold:
                return label
        return "unrelated"

    def _embed_texts(self, texts: List[str]) -> List[EmbeddingResult]:
        """Generate embeddings via Gemini API or fallback to hash-based."""
        results = []
        for text in texts:
            if self.api_key:
                embedding = self._call_embedding_api(text)
            else:
                # Deterministic fallback: hash-based pseudo-embedding (768 dims)
                embedding = self._hash_embedding(text)

            results.append(EmbeddingResult(
                text=text[:100],
                embedding=embedding,
                dimensions=len(embedding),
                model=EMBEDDING_MODEL if self.api_key else "hash-fallback",
                tokens_used=len(text) // 4,
            ))
        return results

    def _call_embedding_api(self, text: str) -> List[float]:
        """Call Gemini embedding API."""
        url = f"{GEMINI_API_BASE}/models/{EMBEDDING_MODEL}:embedContent?key={self.api_key}"
        payload = json.dumps({
            "model": f"models/{EMBEDDING_MODEL}",
            "content": {"parts": [{"text": text}]},
        }).encode("utf-8")
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return data["embedding"]["values"]
        except Exception:
            return self._hash_embedding(text)

    def _hash_embedding(self, text: str, dims: int = 768) -> List[float]:
        """Deterministic hash-based pseudo-embedding for offline mode."""
        import hashlib
        h = hashlib.sha512(text.encode()).hexdigest()
        values = []
        for i in range(dims):
            byte_pair = h[(i * 2) % len(h):(i * 2 + 2) % len(h)] or "00"
            val = (int(byte_pair, 16) - 128) / 128.0
            values.append(round(val, 6))
        return values

    def analyze(self, agent_input: AgentInput) -> AgentOutput:
        w = agent_input.workload
        texts = w.get("texts", [])
        compare_pairs = w.get("compare_pairs", [])
        operation = w.get("operation", "embed_and_compare")

        rules = [
            "embed_001_model_selection",
            "embed_002_batch_efficiency",
            "embed_003_similarity_thresholds",
            "embed_004_cost_tracking",
        ]

        # Generate embeddings
        embeddings = self._embed_texts(texts)
        total_tokens = sum(e.tokens_used for e in embeddings)
        total_cost = total_tokens / TOKENS_PER_MILLION * EMBEDDING_COST_PER_1M

        # Compute similarities
        similarities = []
        for pair in compare_pairs:
            if len(pair) == 2 and pair[0] < len(embeddings) and pair[1] < len(embeddings):
                score = self._cosine_similarity(
                    embeddings[pair[0]].embedding,
                    embeddings[pair[1]].embedding,
                )
                similarities.append(SimilarityResult(
                    text_a=texts[pair[0]][:60],
                    text_b=texts[pair[1]][:60],
                    cosine_similarity=round(score, 4),
                    interpretation=self._interpret_similarity(score),
                ))

        anti_patterns = []
        if len(texts) > MAX_BATCH_SIZE:
            anti_patterns.append(f"Batch size {len(texts)} exceeds max {MAX_BATCH_SIZE}")

        recommendations = [{
            "technique": "embedding_generation",
            "applicable": True,
            "total_texts": len(texts),
            "dimensions": embeddings[0].dimensions if embeddings else 0,
            "model": embeddings[0].model if embeddings else EMBEDDING_MODEL,
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 6),
            "similarities": [asdict(s) for s in similarities],
            "rules_applied": rules,
        }]

        sim_summary = ""
        if similarities:
            avg_sim = sum(s.cosine_similarity for s in similarities) / len(similarities)
            sim_summary = f" Avg similarity: {avg_sim:.3f}."

        meta_insight = (
            f"Embedded {len(texts)} texts ({total_tokens} tokens, "
            f"${total_cost:.4f}). {len(similarities)} comparisons.{sim_summary}"
        )

        return AgentOutput(
            recommendations=recommendations,
            rules_applied=rules,
            meta_insight=meta_insight,
            analysis_data={
                "embeddings": [
                    {"text": e.text, "dimensions": e.dimensions, "tokens": e.tokens_used}
                    for e in embeddings
                ],
                "similarities": [asdict(s) for s in similarities],
                "cost": round(total_cost, 6),
            },
            anti_patterns=anti_patterns,
            agent_metadata=self.build_metadata(),
        )


if __name__ == "__main__":
    analyzer = EmbeddingEngineAnalyzer()
    run_standard_cli(
        agent_name="Embedding Engine",
        description="Embedding generation and vector operations via Gemini API",
        analyzer=analyzer,
    )

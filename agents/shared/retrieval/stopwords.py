#!/usr/bin/env python3
"""
Stopword List & Tokenizer — Unified Retrieval Layer

Merged stopwords from 3 sources:
  - rag_kg_query.py (18 words)
  - intent_engine_agent.py (16 words)
  - case study extended list (62 words)

Level 0 dependency — no internal imports.

Created: February 8, 2026
"""

import re
from typing import List


# Merged superset from all NLKE agents + extended list
STOPWORDS: frozenset = frozenset({
    # Common English
    "a", "an", "the", "and", "or", "but", "not", "no",
    "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did",
    "will", "would", "shall", "should", "may", "might", "can", "could",
    "i", "me", "my", "we", "our", "you", "your", "he", "she", "it", "they", "them",
    "this", "that", "these", "those",
    "in", "on", "at", "to", "for", "of", "with", "by", "from", "as",
    "about", "into", "through", "during", "before", "after",
    # From rag_kg_query.py
    "how", "what", "why", "when", "where", "which", "who",
    # From intent_engine_agent.py
    "want", "using", "each",
    # Extended
    "also", "just", "than", "very", "too", "so", "if", "then",
    "here", "there", "all", "any", "both", "other", "some",
    "such", "only", "own", "same", "more", "most", "between",
})


def tokenize_and_filter(text: str, min_length: int = 3) -> List[str]:
    """Extract meaningful keywords from text.

    Tokenizes on word boundaries, lowercases, removes stopwords,
    and filters by minimum length.

    Args:
        text: Input text to tokenize
        min_length: Minimum word length to keep (default 3)

    Returns:
        List of filtered keyword tokens (preserves order, no dedup)
    """
    words = re.findall(r'\w+', text.lower())
    return [w for w in words if w not in STOPWORDS and len(w) >= min_length]


# ============================================================================
# Self-test
# ============================================================================

if __name__ == "__main__":
    assert len(STOPWORDS) >= 62, f"Expected 62+ stopwords, got {len(STOPWORDS)}"

    # Test tokenizer
    query = "How does prompt caching work with batch API for cost optimization?"
    tokens = tokenize_and_filter(query)
    assert "how" not in tokens
    assert "does" not in tokens
    assert "prompt" in tokens
    assert "caching" in tokens
    assert "cost" in tokens
    assert "optimization" in tokens

    # Intent engine style query
    query2 = "I want to build a cost-optimized multi-model pipeline"
    tokens2 = tokenize_and_filter(query2)
    assert "want" not in tokens2
    assert "build" in tokens2
    assert "cost" in tokens2

    print(f"stopwords.py OK: {len(STOPWORDS)} stopwords")
    print(f"  Query 1: {query!r}")
    print(f"  Tokens:  {tokens}")
    print(f"  Query 2: {query2!r}")
    print(f"  Tokens:  {tokens2}")

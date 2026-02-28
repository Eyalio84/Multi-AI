#!/usr/bin/env python3
"""
Weight Profiles — Unified Retrieval Layer

Adaptive fusion weights per query intent and embedding quality.
Maps QueryIntent -> (alpha, beta, gamma) weight profiles.

Level 1 dependency — imports from config.py.

Created: February 8, 2026
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Optional


# ============================================================================
# Query Intent Classification
# ============================================================================

class QueryIntent(Enum):
    """Detected query intent types for weight adaptation."""
    GENERAL = "general"            # Default / unclear intent
    PRECISION = "precision"        # Exact answer needed ("what is X?")
    EXPLORATORY = "exploratory"    # Broad discovery ("tell me about X")
    NAVIGATIONAL = "navigational"  # Find specific item ("find the agent for X")
    CONCEPTUAL = "conceptual"      # Understanding concepts ("how does X relate to Y?")
    EXACT = "exact"                # Exact match lookup ("agent cost-advisor")
    MULTI_ENTITY = "multi_entity"  # Multiple entities ("compare X and Y")
    HYBRID = "hybrid"              # Mixed intent (fallback to balanced)


# ============================================================================
# Weight Profile
# ============================================================================

@dataclass(frozen=True)
class WeightProfile:
    """Fusion weights for a specific intent type."""
    alpha: float   # Vector/embedding weight
    beta: float    # BM25 keyword weight
    gamma: float   # Graph proximity weight

    def validate(self) -> bool:
        return abs(self.alpha + self.beta + self.gamma - 1.0) < 0.01


# ============================================================================
# Intent -> Weight Mapping
# ============================================================================

# Adapted from eco-system enhanced_query.py ADAPTIVE_WEIGHTS (5 profiles)
# Extended with 3 additional profiles for NLKE use cases
INTENT_WEIGHTS: Dict[QueryIntent, WeightProfile] = {
    QueryIntent.GENERAL:       WeightProfile(alpha=0.40, beta=0.45, gamma=0.15),
    QueryIntent.PRECISION:     WeightProfile(alpha=0.30, beta=0.60, gamma=0.10),
    QueryIntent.EXPLORATORY:   WeightProfile(alpha=0.50, beta=0.30, gamma=0.20),
    QueryIntent.NAVIGATIONAL:  WeightProfile(alpha=0.25, beta=0.65, gamma=0.10),
    QueryIntent.CONCEPTUAL:    WeightProfile(alpha=0.50, beta=0.25, gamma=0.25),
    QueryIntent.EXACT:         WeightProfile(alpha=0.15, beta=0.75, gamma=0.10),
    QueryIntent.MULTI_ENTITY:  WeightProfile(alpha=0.35, beta=0.40, gamma=0.25),
    QueryIntent.HYBRID:        WeightProfile(alpha=0.40, beta=0.40, gamma=0.20),
}


# ============================================================================
# Embedding Quality Overrides
# ============================================================================

# When embedding quality is known, override alpha/beta balance
# Lower quality embeddings -> more weight on BM25
EMBEDDING_QUALITY_OVERRIDES: Dict[str, WeightProfile] = {
    "semantic":  WeightProfile(alpha=0.40, beta=0.45, gamma=0.15),  # Good embeddings
    "hash":      WeightProfile(alpha=0.20, beta=0.65, gamma=0.15),  # Hash fallback
    "untrained": WeightProfile(alpha=0.30, beta=0.55, gamma=0.15),  # Untrained/random
}


def get_weights(
    intent: QueryIntent = QueryIntent.GENERAL,
    embedding_quality: Optional[str] = None,
) -> WeightProfile:
    """Get fusion weights for given intent and embedding quality.

    Args:
        intent: Detected query intent
        embedding_quality: One of "semantic", "hash", "untrained", or None

    Returns:
        WeightProfile with alpha, beta, gamma summing to 1.0
    """
    # Embedding quality override takes precedence for alpha/beta balance
    if embedding_quality and embedding_quality in EMBEDDING_QUALITY_OVERRIDES:
        base = EMBEDDING_QUALITY_OVERRIDES[embedding_quality]
        intent_profile = INTENT_WEIGHTS.get(intent, INTENT_WEIGHTS[QueryIntent.GENERAL])
        # Blend: use quality override for alpha/beta ratio, intent for gamma
        return WeightProfile(
            alpha=base.alpha,
            beta=base.beta,
            gamma=intent_profile.gamma,
        )

    return INTENT_WEIGHTS.get(intent, INTENT_WEIGHTS[QueryIntent.GENERAL])


# ============================================================================
# Self-test
# ============================================================================

if __name__ == "__main__":
    # Validate all profiles sum to 1.0
    for intent, profile in INTENT_WEIGHTS.items():
        assert profile.validate(), f"{intent.value}: weights don't sum to 1.0"

    for quality, profile in EMBEDDING_QUALITY_OVERRIDES.items():
        assert profile.validate(), f"{quality}: weights don't sum to 1.0"

    # Test weight retrieval
    w = get_weights(QueryIntent.PRECISION)
    assert w.beta > w.alpha, "Precision should favor BM25"

    w2 = get_weights(QueryIntent.EXPLORATORY)
    assert w2.alpha > w2.beta, "Exploratory should favor vectors"

    w3 = get_weights(QueryIntent.EXACT)
    assert w3.beta >= 0.70, "Exact should heavily favor BM25"

    # Test embedding quality override
    w4 = get_weights(QueryIntent.GENERAL, embedding_quality="hash")
    assert w4.alpha < 0.25, "Hash embeddings should reduce alpha"
    assert w4.beta > 0.60, "Hash embeddings should boost beta"

    print(f"weight_profiles.py OK: {len(INTENT_WEIGHTS)} intent profiles")
    print(f"  {len(EMBEDDING_QUALITY_OVERRIDES)} quality overrides")
    for intent, profile in INTENT_WEIGHTS.items():
        print(f"  {intent.value:15s}: a={profile.alpha:.2f} b={profile.beta:.2f} g={profile.gamma:.2f}")

#!/usr/bin/env python3
"""
Context Engineer Agent v1.1

Designs optimal context configurations for AI workloads across Claude AND Gemini.
Token budget optimization, hierarchical stacking, caching strategies,
Gemini 1M context window exploitation, and cross-provider context strategies.
"90% context at 10% cost."

Layer: L1-L5 (Full 5-layer pattern via agent_base)

Usage:
    python3 context_engineer.py --example
    python3 context_engineer.py --workload context.json --summary

Created: February 6, 2026
Updated: February 6, 2026 (v1.1 - Tier 2 Gemini context patterns)
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.agent_base import (
    AgentInput, AgentOutput, BaseAnalyzer, run_standard_cli,
    PRICING, GEMINI_MODELS, TOKENS_PER_MILLION,
)

from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any


# ============================================================================
# L1: Data Models
# ============================================================================

@dataclass
class ContextLayer:
    name: str
    layer: str  # global, project, local
    tokens: int
    priority: str  # critical, high, medium, low
    cacheable: bool
    utilization_pct: float  # how much is actually used per request


# ============================================================================
# L2: Constants
# ============================================================================

LAYER_LIMITS = {
    "global": {"max_tokens": 2000, "typical": 800},
    "project": {"max_tokens": 10000, "typical": 4000},
    "local": {"max_tokens": 5000, "typical": 2000},
}

PRIORITY_WEIGHTS = {
    "critical": 1.0,
    "high": 0.85,
    "medium": 0.60,
    "low": 0.30,
}

CACHE_HIT_RATE = 0.80
COMPRESSION_RATIO = 0.65  # typical reduction from optimization

# Gemini context capabilities
GEMINI_CONTEXT_LIMITS = {
    "gemini-2.5-flash-lite": 1_048_576,
    "gemini-2.5-flash": 1_048_576,
    "gemini-2.5-pro": 1_048_576,
    "gemini-3-flash": 200_000,
    "gemini-3-pro": 1_048_576,
}
CLAUDE_CONTEXT_LIMIT = 200_000

# Gemini implicit caching: content reused within short time is cached automatically
# Pricing: cached read is ~75% discount on input
GEMINI_CACHE_DISCOUNT = 0.75
GEMINI_CACHE_MIN_TOKENS = 32_768  # Minimum tokens for context caching

# Cross-provider context strategy thresholds
CONTEXT_OVERFLOW_THRESHOLD = 150_000  # Above this, consider Gemini
CHUNKING_AVOIDANCE_THRESHOLD = 200_000  # Gemini eliminates chunking need


# ============================================================================
# L3: Analyzer
# ============================================================================

class ContextEngineerAnalyzer(BaseAnalyzer):
    """Context optimization engine."""

    def __init__(self):
        super().__init__(
            agent_name="context-engineer",
            model="haiku",
            version="1.1",
        )

    def get_example_input(self) -> Dict[str, Any]:
        return {
            "name": "NLKE Agent Ecosystem Context Audit",
            "context_sources": [
                {"name": "CLAUDE.md", "layer": "global", "tokens": 1500, "priority": "critical", "cacheable": True, "utilization_pct": 90},
                {"name": "MEMORY.md", "layer": "global", "tokens": 1200, "priority": "high", "cacheable": True, "utilization_pct": 70},
                {"name": "Agent system prompt", "layer": "project", "tokens": 3000, "priority": "critical", "cacheable": True, "utilization_pct": 95},
                {"name": "Handbook context", "layer": "project", "tokens": 8000, "priority": "medium", "cacheable": True, "utilization_pct": 40},
                {"name": "Synthesis rules subset", "layer": "project", "tokens": 5000, "priority": "medium", "cacheable": False, "utilization_pct": 30},
                {"name": "Current file content", "layer": "local", "tokens": 4000, "priority": "high", "cacheable": False, "utilization_pct": 85},
                {"name": "KG query results", "layer": "local", "tokens": 2000, "priority": "medium", "cacheable": False, "utilization_pct": 60},
            ],
            "model": "sonnet",
            "requests_per_day": 50,
        }

    def analyze(self, agent_input: AgentInput) -> AgentOutput:
        w = agent_input.workload
        sources = w.get("context_sources", [])
        model = w.get("model", "sonnet")
        rpd = w.get("requests_per_day", 50)

        rules = [
            "context_001_hierarchical_stacking",
            "context_002_section_prioritization",
            "context_003_cache_strategy",
            "context_004_compression",
            "context_005_gemini_context_window",
            "context_006_cross_provider_strategy",
            "context_007_gemini_implicit_caching",
            "playbook_025_session_continuity",
        ]

        layers = []
        for src in sources:
            layers.append(ContextLayer(
                name=src["name"],
                layer=src.get("layer", "project"),
                tokens=src.get("tokens", 1000),
                priority=src.get("priority", "medium"),
                cacheable=src.get("cacheable", False),
                utilization_pct=src.get("utilization_pct", 50),
            ))

        # Current state
        total_tokens = sum(l.tokens for l in layers)
        effective_tokens = sum(l.tokens * l.utilization_pct / 100 for l in layers)
        waste_pct = (1 - effective_tokens / max(1, total_tokens)) * 100

        # Optimized state
        optimized_layers = []
        for l in layers:
            weight = PRIORITY_WEIGHTS.get(l.priority, 0.5)
            opt_tokens = int(l.tokens * max(weight, l.utilization_pct / 100))
            optimized_layers.append({
                "name": l.name,
                "original_tokens": l.tokens,
                "optimized_tokens": opt_tokens,
                "reduction_pct": round((1 - opt_tokens / max(1, l.tokens)) * 100, 1),
                "cacheable": l.cacheable,
                "priority": l.priority,
            })

        opt_total = sum(o["optimized_tokens"] for o in optimized_layers)
        reduction = (1 - opt_total / max(1, total_tokens)) * 100

        # Cost analysis
        model_input_price = PRICING.get(f"{model}_input", 3.00)
        current_monthly = (total_tokens / TOKENS_PER_MILLION * model_input_price * rpd * 20)
        optimized_monthly = (opt_total / TOKENS_PER_MILLION * model_input_price * rpd * 20)

        # Caching savings
        cacheable_tokens = sum(l.tokens for l in layers if l.cacheable)
        cache_savings = (cacheable_tokens * CACHE_HIT_RATE / TOKENS_PER_MILLION *
                        (model_input_price - PRICING["cache_read"]) * rpd * 20)

        final_monthly = optimized_monthly - cache_savings

        # Layer breakdown
        by_layer = {}
        for l in layers:
            by_layer.setdefault(l.layer, {"count": 0, "tokens": 0})
            by_layer[l.layer]["count"] += 1
            by_layer[l.layer]["tokens"] += l.tokens

        anti_patterns = []
        if waste_pct > 50:
            anti_patterns.append(f"Context waste is {waste_pct:.0f}% - major optimization needed")
        low_util = [l for l in layers if l.utilization_pct < 30 and l.tokens > 2000]
        for l in low_util:
            anti_patterns.append(f"Low utilization ({l.utilization_pct}%): {l.name} ({l.tokens} tokens)")

        # Gemini context analysis
        gemini_analysis = self._analyze_gemini_context(total_tokens, cacheable_tokens, model, rpd)

        if total_tokens > CONTEXT_OVERFLOW_THRESHOLD:
            anti_patterns.append(
                f"Context ({total_tokens:,} tokens) approaches Claude 200K limit — "
                f"consider Gemini for 1M context window"
            )

        recommendations = [
            {
                "technique": "context_optimization",
                "applicable": True,
                "current_tokens": total_tokens,
                "optimized_tokens": opt_total,
                "token_reduction_pct": f"{reduction:.0f}%",
                "current_monthly_usd": round(current_monthly, 2),
                "optimized_monthly_usd": round(final_monthly, 2),
                "cache_savings_monthly_usd": round(cache_savings, 2),
                "total_savings_monthly_usd": round(current_monthly - final_monthly, 2),
                "layer_breakdown": by_layer,
                "optimized_sources": optimized_layers,
                "rules_applied": rules,
            },
            gemini_analysis,
        ]

        savings_pct = (1 - final_monthly / max(0.01, current_monthly)) * 100

        gemini_note = ""
        if gemini_analysis["applicable"]:
            gemini_note = (
                f" Gemini alternative: ${gemini_analysis['gemini_monthly_usd']}/mo "
                f"with 1M context (no chunking needed)."
            )

        meta_insight = (
            f"Context: {total_tokens:,} tokens -> {opt_total:,} tokens ({reduction:.0f}% reduction). "
            f"Monthly: ${current_monthly:.2f} -> ${final_monthly:.2f} "
            f"({savings_pct:.0f}% savings including caching).{gemini_note}"
        )

        return AgentOutput(
            recommendations=recommendations,
            rules_applied=rules,
            meta_insight=meta_insight,
            analysis_data={
                "current": {"tokens": total_tokens, "monthly_usd": round(current_monthly, 2)},
                "optimized": {"tokens": opt_total, "monthly_usd": round(final_monthly, 2)},
                "cache_savings_monthly": round(cache_savings, 2),
                "waste_pct": round(waste_pct, 1),
                "by_layer": by_layer,
                "gemini_context": gemini_analysis,
                "context_fits_claude": total_tokens <= CLAUDE_CONTEXT_LIMIT,
                "context_fits_gemini_1m": total_tokens <= 1_048_576,
            },
            anti_patterns=anti_patterns,
            agent_metadata=self.build_metadata(),
        )

    def _analyze_gemini_context(self, total_tokens: int, cacheable_tokens: int,
                                 model: str, rpd: int) -> Dict:
        """Analyze cost/benefit of using Gemini for context handling."""
        # Find comparable Gemini model
        gemini_model = "gemini-2.5-flash"  # Default cheap option
        if model == "opus":
            gemini_model = "gemini-3-pro"
        elif model == "sonnet":
            gemini_model = "gemini-2.5-pro"

        gemini_pricing = GEMINI_MODELS.get(gemini_model, {"input": 0.15, "output": 0.60})
        gemini_monthly = (total_tokens / TOKENS_PER_MILLION * gemini_pricing["input"] * rpd * 20)

        # Gemini implicit caching savings (if content > 32K and reused)
        gemini_cache_savings = 0.0
        if cacheable_tokens >= GEMINI_CACHE_MIN_TOKENS:
            gemini_cache_savings = (
                cacheable_tokens * GEMINI_CACHE_DISCOUNT / TOKENS_PER_MILLION *
                gemini_pricing["input"] * rpd * 20
            )

        gemini_final = gemini_monthly - gemini_cache_savings

        # Context advantages
        advantages = []
        if total_tokens > CONTEXT_OVERFLOW_THRESHOLD:
            advantages.append("Eliminates need for context chunking")
        if total_tokens > CLAUDE_CONTEXT_LIMIT:
            advantages.append("Content exceeds Claude 200K limit — only Gemini can handle full context")
        if cacheable_tokens >= GEMINI_CACHE_MIN_TOKENS:
            advantages.append(f"Implicit caching on {cacheable_tokens:,} tokens (75% discount)")
        advantages.append(f"1M context window (5x Claude's 200K)")

        return {
            "technique": "gemini_context_strategy",
            "applicable": total_tokens > 50000 or total_tokens > CONTEXT_OVERFLOW_THRESHOLD,
            "gemini_model": gemini_model,
            "gemini_monthly_usd": round(gemini_final, 2),
            "gemini_cache_savings_usd": round(gemini_cache_savings, 2),
            "context_window": "1M tokens",
            "advantages": advantages,
            "requires_chunking": total_tokens > CLAUDE_CONTEXT_LIMIT,
            "rules_applied": ["context_005_gemini_context_window", "context_007_gemini_implicit_caching"],
        }


if __name__ == "__main__":
    analyzer = ContextEngineerAnalyzer()
    run_standard_cli(
        agent_name="Context Engineer",
        description="Optimal context configuration and token budget optimization",
        analyzer=analyzer,
    )

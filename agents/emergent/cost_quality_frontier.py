#!/usr/bin/env python3
"""
Cost-Quality Frontier Agent

Pareto optimization across cost, quality, speed, and model selection.
Maps the full cost-quality frontier and recommends optimal configurations.

Composes: Agent 1 + Agent 2 + Agent 3 + Agent 7
Layer: L1-L5 (Full 5-layer pattern via agent_base)

Usage:
    python3 cost_quality_frontier.py --example
    python3 cost_quality_frontier.py --workload config.json --summary

Created: February 6, 2026
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.agent_base import (
    AgentInput, AgentOutput, BaseAnalyzer, run_standard_cli,
    PRICING, TOKENS_PER_MILLION,
)

from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any


# ============================================================================
# L1: Data Models
# ============================================================================

@dataclass
class FrontierPoint:
    name: str
    model: str
    thinking_budget: int
    caching: bool
    batching: bool
    cost_per_request: float
    quality_score: float
    latency_ms: int
    pareto_optimal: bool


# ============================================================================
# L2: Constants
# ============================================================================

# Quality estimates by configuration (from empirical testing)
QUALITY_MODEL = {
    "haiku": {"base": 0.65, "per_1k_thinking": 0.03, "cap": 0.82},
    "sonnet": {"base": 0.78, "per_1k_thinking": 0.025, "cap": 0.93},
    "opus": {"base": 0.88, "per_1k_thinking": 0.015, "cap": 0.98},
}

LATENCY_MODEL = {
    "haiku": {"base_ms": 200, "per_1k_thinking_ms": 50, "cache_reduction": 0.5},
    "sonnet": {"base_ms": 800, "per_1k_thinking_ms": 150, "cache_reduction": 0.4},
    "opus": {"base_ms": 2000, "per_1k_thinking_ms": 300, "cache_reduction": 0.3},
}

CONFIGS = [
    {"name": "Cheapest", "model": "haiku", "thinking": 0, "cache": True, "batch": True},
    {"name": "Budget Haiku", "model": "haiku", "thinking": 1000, "cache": True, "batch": False},
    {"name": "Standard Haiku", "model": "haiku", "thinking": 3000, "cache": True, "batch": False},
    {"name": "Max Haiku", "model": "haiku", "thinking": 6000, "cache": True, "batch": False},
    {"name": "Budget Sonnet", "model": "sonnet", "thinking": 0, "cache": True, "batch": True},
    {"name": "Standard Sonnet", "model": "sonnet", "thinking": 4000, "cache": True, "batch": False},
    {"name": "Quality Sonnet", "model": "sonnet", "thinking": 8000, "cache": True, "batch": False},
    {"name": "Max Sonnet", "model": "sonnet", "thinking": 10000, "cache": False, "batch": False},
    {"name": "Budget Opus", "model": "opus", "thinking": 0, "cache": True, "batch": True},
    {"name": "Standard Opus", "model": "opus", "thinking": 4000, "cache": True, "batch": False},
    {"name": "Quality Opus", "model": "opus", "thinking": 8000, "cache": False, "batch": False},
    {"name": "Maximum Quality", "model": "opus", "thinking": 10000, "cache": False, "batch": False},
]


# ============================================================================
# L3: Analyzer
# ============================================================================

class CostQualityFrontierAnalyzer(BaseAnalyzer):
    """Pareto frontier mapping engine."""

    def __init__(self):
        super().__init__(
            agent_name="cost-quality-frontier",
            model="sonnet",
            version="1.0",
        )

    def get_example_input(self) -> Dict[str, Any]:
        return {
            "name": "Document Analysis Workload",
            "avg_input_tokens": 5000,
            "avg_output_tokens": 1000,
            "repeated_tokens": 3000,
            "requests_per_day": 100,
            "priority": "balanced",  # cost-first, balanced, quality-first
        }

    def analyze(self, agent_input: AgentInput) -> AgentOutput:
        w = agent_input.workload
        avg_input = w.get("avg_input_tokens", 5000)
        avg_output = w.get("avg_output_tokens", 1000)
        repeated = w.get("repeated_tokens", 0)
        rpd = w.get("requests_per_day", 100)
        priority = w.get("priority", "balanced")

        rules = [
            "frontier_001_configuration_mapping",
            "frontier_002_pareto_identification",
            "frontier_003_priority_recommendation",
        ]

        # Map all configurations
        points = []
        for cfg in CONFIGS:
            model = cfg["model"]
            thinking = cfg["thinking"]
            cache = cfg["cache"]
            batch = cfg["batch"]

            # Cost calculation
            total_input = avg_input + thinking
            model_input_price = PRICING.get(f"{model}_input", 3.0)
            model_output_price = PRICING.get(f"{model}_output", 15.0)

            input_cost = total_input / TOKENS_PER_MILLION * model_input_price
            output_cost = avg_output / TOKENS_PER_MILLION * model_output_price
            cost = input_cost + output_cost

            if cache and repeated > 0:
                cache_savings = (repeated / TOKENS_PER_MILLION) * (model_input_price - PRICING["cache_read"])
                cost -= cache_savings * 0.8  # ~80% cache hit rate

            if batch:
                cost *= 0.5

            # Quality estimation
            qm = QUALITY_MODEL[model]
            quality = min(qm["cap"], qm["base"] + (thinking / 1000) * qm["per_1k_thinking"])

            # Latency estimation
            lm = LATENCY_MODEL[model]
            latency = lm["base_ms"] + (thinking / 1000) * lm["per_1k_thinking_ms"]
            if cache:
                latency *= lm["cache_reduction"]
            if batch:
                latency = 3600000  # 1h for batch

            points.append(FrontierPoint(
                name=cfg["name"],
                model=model,
                thinking_budget=thinking,
                caching=cache,
                batching=batch,
                cost_per_request=round(cost, 5),
                quality_score=round(quality, 3),
                latency_ms=int(latency),
                pareto_optimal=False,
            ))

        # Find Pareto-optimal points (non-dominated in cost-quality space)
        for i, p in enumerate(points):
            dominated = False
            for j, q in enumerate(points):
                if i != j:
                    if q.cost_per_request <= p.cost_per_request and q.quality_score >= p.quality_score:
                        if q.cost_per_request < p.cost_per_request or q.quality_score > p.quality_score:
                            dominated = True
                            break
            p.pareto_optimal = not dominated

        pareto_points = [p for p in points if p.pareto_optimal]

        # Recommend based on priority
        if priority == "cost-first":
            recommended = min(pareto_points, key=lambda p: p.cost_per_request)
        elif priority == "quality-first":
            recommended = max(pareto_points, key=lambda p: p.quality_score)
        else:  # balanced
            recommended = min(
                pareto_points,
                key=lambda p: p.cost_per_request / max(0.01, p.quality_score),
            )

        # Monthly cost at given RPD
        monthly = rpd * 20

        recommendations = [{
            "technique": "frontier_analysis",
            "applicable": True,
            "total_configurations": len(points),
            "pareto_optimal_count": len(pareto_points),
            "recommended": {
                "name": recommended.name,
                "model": recommended.model,
                "thinking_budget": recommended.thinking_budget,
                "cost_per_request": recommended.cost_per_request,
                "monthly_cost": round(recommended.cost_per_request * monthly, 2),
                "quality_score": recommended.quality_score,
            },
            "pareto_frontier": [asdict(p) for p in pareto_points],
            "all_configurations": [asdict(p) for p in points],
            "rules_applied": rules,
        }]

        # Cost range
        cheapest = min(points, key=lambda p: p.cost_per_request)
        highest_q = max(points, key=lambda p: p.quality_score)

        meta_insight = (
            f"Frontier mapped: {len(pareto_points)} Pareto-optimal configs from "
            f"${cheapest.cost_per_request:.4f}/req (quality {cheapest.quality_score:.2f}) to "
            f"${highest_q.cost_per_request:.4f}/req (quality {highest_q.quality_score:.2f}). "
            f"Recommended ({priority}): {recommended.name} at "
            f"${recommended.cost_per_request:.4f}/req, quality {recommended.quality_score:.2f}."
        )

        return AgentOutput(
            recommendations=recommendations,
            rules_applied=rules,
            meta_insight=meta_insight,
            analysis_data={
                "frontier": [asdict(p) for p in pareto_points],
                "all_points": [asdict(p) for p in points],
                "recommended": asdict(recommended),
                "cost_range": {
                    "min": cheapest.cost_per_request,
                    "max": highest_q.cost_per_request,
                },
                "quality_range": {
                    "min": cheapest.quality_score,
                    "max": highest_q.quality_score,
                },
                "monthly_at_recommended": round(recommended.cost_per_request * monthly, 2),
            },
            anti_patterns=[],
            agent_metadata=self.build_metadata(),
        )


if __name__ == "__main__":
    analyzer = CostQualityFrontierAnalyzer()
    run_standard_cli(
        agent_name="Cost-Quality Frontier",
        description="Pareto optimization across cost, quality, speed, and model selection",
        analyzer=analyzer,
    )

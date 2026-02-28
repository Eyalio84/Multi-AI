#!/usr/bin/env python3
"""
Batch Optimizer Agent

Calculates optimal batch sizes, latency tradeoffs, compound savings with caching,
and polling strategies for Claude Batch API workloads.

Wraps: AI-LAB batch_optimizer.py
Layer: L1-L5 (Full 5-layer pattern via agent_base)

Usage:
    python3 batch_optimizer_agent.py --example
    python3 batch_optimizer_agent.py --workload batch_config.json
    python3 batch_optimizer_agent.py --workload batch_config.json --summary

Created: February 6, 2026
"""

import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.agent_base import (
    AgentInput, AgentOutput, BaseAnalyzer, run_standard_cli,
    PRICING, TOKENS_PER_MILLION,
)

from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional


# ============================================================================
# L1: Data Models
# ============================================================================

@dataclass
class BatchConfig:
    batch_size: int
    total_requests: int
    parallel_batches: int
    estimated_hours: float
    format: str = "jsonl"


@dataclass
class ThroughputMetrics:
    requests_per_hour: float
    completion_hours: float
    latency_acceptable: bool
    assessment: str


# ============================================================================
# L2: Constants
# ============================================================================

MIN_BATCH_SIZE = 1
MAX_BATCH_SIZE = 10000
MIN_HOURS = 1
MAX_HOURS = 24
BASE_THROUGHPUT = 30  # requests/hour conservative
BATCH_DISCOUNT = 0.50
CACHE_DISCOUNT = 0.90

POLLING_STRATEGIES = {
    "aggressive": {"interval_sec": 10, "timeout_sec": 3600},
    "moderate": {"interval_sec": 60, "timeout_sec": 7200},
    "conservative": {"interval_sec": 300, "timeout_sec": 86400},
}


# ============================================================================
# L3: Analyzer
# ============================================================================

class BatchOptimizerAnalyzer(BaseAnalyzer):
    """Batch API optimization engine."""

    def __init__(self):
        super().__init__(
            agent_name="batch-optimizer",
            model="haiku",
            version="1.0",
        )

    def get_example_input(self) -> Dict[str, Any]:
        return {
            "name": "Large-Scale Evaluation Pipeline",
            "total_requests": 10000,
            "deadline": "24_hours",
            "async_compatible": True,
            "latency_sensitive": False,
            "avg_input_tokens": 5000,
            "avg_output_tokens": 500,
            "current_cost_per_request": 0.04,
            "cached_tokens": 3000,
            "current_model": "sonnet",
        }

    def analyze(self, agent_input: AgentInput) -> AgentOutput:
        w = agent_input.workload
        recommendations = []
        rules = []
        anti_patterns = []

        total_requests = w.get("total_requests", 1000)
        deadline_hours = self._parse_deadline(w.get("deadline", "24_hours"))
        async_compatible = w.get("async_compatible", True)
        latency_sensitive = w.get("latency_sensitive", False)
        cost_per_request = w.get("current_cost_per_request", 0.05)
        cached_tokens = w.get("cached_tokens", 0)
        avg_input = w.get("avg_input_tokens", 1000)

        # Validate applicability
        valid, validation_issues = self._validate(w)
        rules.append("dep_001_batch_requires_async")
        rules.append("cons_003_batch_latency_tradeoff")

        if not valid:
            for issue in validation_issues:
                anti_patterns.append(issue)
            recommendations.append({
                "technique": "batch_api",
                "applicable": False,
                "reason": " | ".join(validation_issues),
                "estimated_savings": "0%",
                "monthly_savings_usd": 0.0,
                "implementation_complexity": "N/A",
                "rules_applied": rules,
            })
            return AgentOutput(
                recommendations=recommendations,
                rules_applied=rules,
                meta_insight="Batch API not applicable to this workload",
                analysis_data={"validation_issues": validation_issues},
                anti_patterns=anti_patterns,
                agent_metadata=self.build_metadata(),
            )

        # Optimize batch size
        batch_size = self._optimize_batch_size(total_requests, deadline_hours)
        parallel_batches = math.ceil(total_requests / batch_size)
        rules.append("comp_002_batch_size_throughput")

        # Throughput analysis
        throughput = self._calculate_throughput(total_requests, batch_size)

        # Cost analysis
        baseline_cost = total_requests * cost_per_request
        batch_cost = baseline_cost * BATCH_DISCOUNT
        batch_savings = baseline_cost - batch_cost
        rules.append("compat_002_batch_async_workloads")

        recommendations.append({
            "technique": "batch_api",
            "applicable": True,
            "reason": f"{total_requests:,} requests, {deadline_hours}h deadline, async-compatible",
            "estimated_savings": "50% base cost reduction",
            "monthly_savings_usd": round(batch_savings, 2),
            "implementation_complexity": "medium",
            "rules_applied": ["dep_001", "comp_002", "compat_002"],
            "batch_config": {
                "batch_size": batch_size,
                "parallel_batches": parallel_batches,
                "estimated_hours": throughput.completion_hours,
            },
        })

        # Compound analysis (batch + caching)
        compound_data = None
        if cached_tokens > 0 and avg_input > 0:
            cache_ratio = cached_tokens / avg_input
            compound_cost = batch_cost * (1 - cache_ratio * CACHE_DISCOUNT)
            compound_savings = baseline_cost - compound_cost
            compound_pct = min(95, (compound_savings / baseline_cost * 100) if baseline_cost > 0 else 0)
            rules.append("compat_003_batch_caching_synergy")

            compound_data = {
                "cache_ratio": round(cache_ratio, 2),
                "compound_cost": round(compound_cost, 2),
                "compound_savings": round(compound_savings, 2),
                "compound_pct": round(compound_pct, 1),
            }

            recommendations.append({
                "technique": "compound_optimization",
                "applicable": True,
                "reason": f"Batch + caching synergy (cache ratio: {cache_ratio:.0%})",
                "estimated_savings": f"{compound_pct:.0f}% combined savings",
                "monthly_savings_usd": round(compound_savings, 2),
                "implementation_complexity": "medium",
                "rules_applied": ["compat_003_batch_caching_synergy"],
            })

        # Polling strategy
        polling = self._recommend_polling(throughput.completion_hours)

        # Meta-insight
        if compound_data:
            meta_insight = (
                f"Compound optimization achieves {compound_data['compound_pct']:.0f}% savings "
                f"(${compound_data['compound_savings']:.2f}). Optimal batch size: {batch_size}, "
                f"completion in ~{throughput.completion_hours:.1f}h"
            )
        else:
            meta_insight = (
                f"Batch API saves 50% (${batch_savings:.2f}). "
                f"Optimal batch size: {batch_size}, "
                f"completion in ~{throughput.completion_hours:.1f}h"
            )

        return AgentOutput(
            recommendations=recommendations,
            rules_applied=list(dict.fromkeys(rules)),
            meta_insight=meta_insight,
            analysis_data={
                "batch_config": asdict(BatchConfig(
                    batch_size=batch_size,
                    total_requests=total_requests,
                    parallel_batches=parallel_batches,
                    estimated_hours=throughput.completion_hours,
                )),
                "throughput": asdict(throughput),
                "cost": {
                    "baseline": round(baseline_cost, 2),
                    "batch": round(batch_cost, 2),
                    "savings": round(batch_savings, 2),
                },
                "compound": compound_data,
                "polling_strategy": polling,
            },
            anti_patterns=anti_patterns,
            agent_metadata=self.build_metadata(),
        )

    def _parse_deadline(self, deadline_str: str) -> float:
        s = str(deadline_str).lower().strip()
        for suffix in ("_hours", "hours", "_hour", "hour"):
            if s.endswith(suffix):
                return float(s.replace(suffix, ""))
        for suffix in ("_days", "days", "_day", "day"):
            if s.endswith(suffix):
                return float(s.replace(suffix, "")) * 24
        try:
            return float(s)
        except ValueError:
            return 24.0

    def _validate(self, w: Dict) -> tuple:
        issues = []
        if not w.get("async_compatible", False):
            issues.append("anti_dep001: workload not async-compatible")
        if w.get("latency_sensitive", False):
            issues.append("anti_002: latency-sensitive workload")
        return len(issues) == 0, issues

    def _optimize_batch_size(self, total: int, deadline_hours: float) -> int:
        deadline_hours = max(MIN_HOURS, min(MAX_HOURS, deadline_hours))
        max_throughput = deadline_hours * BASE_THROUGHPUT
        size = math.ceil(total / max(1, max_throughput))
        return max(MIN_BATCH_SIZE, min(MAX_BATCH_SIZE, size))

    def _calculate_throughput(self, total: int, batch_size: int) -> ThroughputMetrics:
        hours = min(MAX_HOURS, max(MIN_HOURS, batch_size / BASE_THROUGHPUT))
        rph = total / max(1, hours)
        acceptable = MIN_HOURS <= hours <= MAX_HOURS
        return ThroughputMetrics(
            requests_per_hour=round(rph, 1),
            completion_hours=round(hours, 1),
            latency_acceptable=acceptable,
            assessment=f"{'Acceptable' if acceptable else 'Outside range'}: {hours:.1f}h",
        )

    def _recommend_polling(self, hours: float) -> Dict:
        if hours > 12:
            name = "conservative"
        elif hours > 4:
            name = "moderate"
        else:
            name = "aggressive"
        strat = POLLING_STRATEGIES[name]
        return {
            "strategy": name,
            "interval_sec": strat["interval_sec"],
            "timeout_sec": strat["timeout_sec"],
            "estimated_polls": strat["timeout_sec"] // strat["interval_sec"],
        }


# ============================================================================
# L5: CLI
# ============================================================================

if __name__ == "__main__":
    analyzer = BatchOptimizerAnalyzer()
    run_standard_cli(
        agent_name="Batch Optimizer",
        description="Optimize batch API configuration and calculate cost savings",
        analyzer=analyzer,
    )

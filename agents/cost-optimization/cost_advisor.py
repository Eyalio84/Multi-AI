#!/usr/bin/env python3
"""
Cost Optimization Advisor Agent v1.1

Analyzes Claude AND Gemini API workloads for cost optimization opportunities
through caching, batching, model tiering, cross-provider migration, and
compound optimization strategies.

Wraps: AI-LAB cost_analyzer.py + cache_roi_calculator.py
Layer: L1-L5 (Full 5-layer pattern via agent_base)

Usage:
    python3 cost_advisor.py --example
    python3 cost_advisor.py --workload workload.json
    python3 cost_advisor.py --workload workload.json --summary
    cat workload.json | python3 cost_advisor.py

Created: February 6, 2026
Updated: February 6, 2026 (v1.1 - Tier 2 Gemini pricing)
"""

import sys
import os

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.agent_base import (
    AgentInput, AgentOutput, BaseAnalyzer, run_standard_cli,
    PRICING, THRESHOLDS, TOKENS_PER_MILLION, GEMINI_MODELS,
)

from dataclasses import dataclass, asdict
from typing import Dict, List, Any
from enum import Enum


# ============================================================================
# L1: Data Models
# ============================================================================

class OptimizationTechnique(Enum):
    PROMPT_CACHING = "prompt_caching"
    BATCH_API = "batch_api"
    MODEL_TIERING = "model_tiering"
    COMPOUND = "compound_optimization"


@dataclass
class CostRecommendation:
    technique: str
    applicable: bool
    reason: str
    estimated_savings: str
    monthly_savings_usd: float
    implementation_complexity: str
    rules_applied: List[str]


# ============================================================================
# L2: Constants
# ============================================================================

MODEL_TIERS = {
    # Claude models
    "opus": {"input": 15.00, "output": 75.00, "capability": "highest", "provider": "claude"},
    "sonnet": {"input": 3.00, "output": 15.00, "capability": "high", "provider": "claude"},
    "haiku": {"input": 0.80, "output": 4.00, "capability": "good", "provider": "claude"},
    # Gemini models
    "gemini-2.5-flash-lite": {"input": 0.10, "output": 0.40, "capability": "basic", "provider": "gemini"},
    "gemini-2.5-flash": {"input": 0.15, "output": 0.60, "capability": "good", "provider": "gemini"},
    "gemini-2.5-pro": {"input": 1.25, "output": 5.00, "capability": "high", "provider": "gemini"},
    "gemini-3-flash": {"input": 0.50, "output": 3.00, "capability": "good", "provider": "gemini"},
    "gemini-3-pro": {"input": 2.00, "output": 12.00, "capability": "highest", "provider": "gemini"},
}

# Cross-provider migration map: Claude model -> best Gemini alternative
MIGRATION_MAP = {
    "opus": {"target": "gemini-3-pro", "savings_pct": 80, "quality_note": "Similar quality for most tasks, 1M context"},
    "sonnet": {"target": "gemini-2.5-pro", "savings_pct": 58, "quality_note": "Strong coding, 1M context"},
    "haiku": {"target": "gemini-2.5-flash", "savings_pct": 81, "quality_note": "Fast bulk processing, 1M context"},
}

ANTI_PATTERN_SEVERITY = {
    "cache_single_request": "critical",
    "batch_realtime": "critical",
    "thinking_unbounded": "high",
    "overcaching": "medium",
    "model_overuse": "medium",
    "ignoring_gemini_for_bulk": "medium",
}


# ============================================================================
# L3: Analyzer
# ============================================================================

class CostAdvisorAnalyzer(BaseAnalyzer):
    """Cost optimization analysis engine."""

    def __init__(self):
        super().__init__(
            agent_name="cost-advisor",
            model="haiku",
            version="1.1",
        )

    def get_example_input(self) -> Dict[str, Any]:
        return {
            "name": "Multi-Document Q&A System",
            "requests_per_day": 500,
            "avg_input_tokens": 8000,
            "avg_output_tokens": 1000,
            "repeated_content": {
                "system_prompt": 2000,
                "tool_definitions": 3000,
                "document_context": 2000,
            },
            "latency_sensitive": False,
            "async_compatible": True,
            "current_model": "sonnet",
            "task_complexity": "medium",
            "thinking_budget": 4000,
        }

    def analyze(self, agent_input: AgentInput) -> AgentOutput:
        workload = agent_input.workload
        recommendations = []
        all_rules = []
        anti_patterns = []

        # Analysis 1: Caching
        cache_rec = self._analyze_caching(workload)
        recommendations.append(asdict(cache_rec))
        all_rules.extend(cache_rec.rules_applied)

        # Analysis 2: Batch API
        batch_rec = self._analyze_batch(workload)
        recommendations.append(asdict(batch_rec))
        all_rules.extend(batch_rec.rules_applied)

        # Analysis 3: Model tiering
        tier_rec = self._analyze_model_tiering(workload)
        recommendations.append(asdict(tier_rec))
        all_rules.extend(tier_rec.rules_applied)

        # Analysis 4: Compound optimization
        compound_rec = self._analyze_compound(workload, cache_rec, batch_rec)
        if compound_rec.applicable:
            recommendations.append(asdict(compound_rec))
            all_rules.extend(compound_rec.rules_applied)

        # Analysis 5: Gemini migration
        gemini_rec = self._analyze_gemini_migration(workload)
        recommendations.append(asdict(gemini_rec))
        all_rules.extend(gemini_rec.rules_applied)

        # Anti-pattern detection
        anti_patterns = self._detect_anti_patterns(workload)

        # Meta-insight generation
        applicable = [r for r in recommendations if r["applicable"]]
        total_savings = sum(r["monthly_savings_usd"] for r in applicable)

        if compound_rec.applicable:
            meta_insight = (
                f"Compound optimization available: batch + caching can save "
                f"up to ${compound_rec.monthly_savings_usd:.2f}/month "
                f"({compound_rec.estimated_savings})"
            )
        elif len(applicable) > 1:
            techniques = [r["technique"] for r in applicable]
            meta_insight = (
                f"Multiple optimizations available ({', '.join(techniques)}). "
                f"Combined potential: ${total_savings:.2f}/month"
            )
        elif len(applicable) == 1:
            meta_insight = f"Primary opportunity: {applicable[0]['technique']} - {applicable[0]['estimated_savings']}"
        else:
            meta_insight = "Workload already well-optimized or too small for significant savings"

        return AgentOutput(
            recommendations=recommendations,
            rules_applied=list(dict.fromkeys(all_rules)),
            meta_insight=meta_insight,
            analysis_data={
                "workload_summary": {
                    "requests_per_day": workload.get("requests_per_day", 0),
                    "avg_input_tokens": workload.get("avg_input_tokens", 0),
                    "avg_output_tokens": workload.get("avg_output_tokens", 0),
                    "repeated_content_tokens": sum(
                        workload.get("repeated_content", {}).values()
                    ),
                    "current_model": workload.get("current_model", "sonnet"),
                },
                "total_potential_savings_usd": total_savings,
            },
            anti_patterns=[ap["pattern"] for ap in anti_patterns],
            agent_metadata=self.build_metadata(),
        )

    def _analyze_caching(self, workload: Dict) -> CostRecommendation:
        requests_per_day = workload.get("requests_per_day", 0)
        repeated_content = workload.get("repeated_content", {})
        repeated_tokens = sum(repeated_content.values()) if repeated_content else 0
        avg_input = workload.get("avg_input_tokens", 0)
        rules = ["dep_002_caching_requires_repeated_requests", "comp_001_cache_size_effectiveness"]

        applicable = (
            requests_per_day >= THRESHOLDS["min_requests_for_caching"]
            and repeated_tokens >= THRESHOLDS["min_cached_tokens_for_caching"]
        )

        if applicable and repeated_tokens > 0 and avg_input > 0:
            monthly_requests = requests_per_day * 20
            baseline = (avg_input * monthly_requests) / TOKENS_PER_MILLION * PRICING["sonnet_input"]
            cache_writes = 20 * (repeated_tokens / TOKENS_PER_MILLION) * PRICING["cache_write"]
            cache_reads = ((monthly_requests - 20) * repeated_tokens) / TOKENS_PER_MILLION * PRICING["cache_read"]
            non_cached = ((avg_input - repeated_tokens) * monthly_requests) / TOKENS_PER_MILLION * PRICING["sonnet_input"]
            with_cache = cache_writes + cache_reads + non_cached
            savings = max(0, baseline - with_cache)
            pct = (savings / baseline * 100) if baseline > 0 else 0

            return CostRecommendation(
                technique="prompt_caching",
                applicable=True,
                reason=f"{repeated_tokens:,} repeated tokens across {', '.join(repeated_content.keys())}",
                estimated_savings=f"{pct:.0f}% on input costs",
                monthly_savings_usd=round(savings, 2),
                implementation_complexity="low",
                rules_applied=rules,
            )

        return CostRecommendation(
            technique="prompt_caching",
            applicable=False,
            reason="Insufficient repeated content or request volume",
            estimated_savings="0%",
            monthly_savings_usd=0.0,
            implementation_complexity="N/A",
            rules_applied=rules,
        )

    def _analyze_batch(self, workload: Dict) -> CostRecommendation:
        requests_per_day = workload.get("requests_per_day", 0)
        latency_sensitive = workload.get("latency_sensitive", True)
        async_compatible = workload.get("async_compatible", False)
        avg_input = workload.get("avg_input_tokens", 0)
        avg_output = workload.get("avg_output_tokens", 0)
        rules = ["dep_001_batch_requires_async", "cons_003_batch_latency_tradeoff"]

        applicable = (
            async_compatible
            and not latency_sensitive
            and requests_per_day >= THRESHOLDS["min_requests_for_batch"]
        )

        if applicable:
            monthly_requests = requests_per_day * 20
            model = workload.get("current_model", "sonnet")
            tier = MODEL_TIERS.get(model, MODEL_TIERS["sonnet"])
            baseline = (
                (avg_input * monthly_requests) / TOKENS_PER_MILLION * tier["input"]
                + (avg_output * monthly_requests) / TOKENS_PER_MILLION * tier["output"]
            )
            savings = baseline * 0.5
            return CostRecommendation(
                technique="batch_api",
                applicable=True,
                reason=f"{requests_per_day} requests/day, async-compatible",
                estimated_savings="50% base cost reduction",
                monthly_savings_usd=round(savings, 2),
                implementation_complexity="medium",
                rules_applied=rules,
            )

        reasons = []
        if not async_compatible:
            reasons.append("not async-compatible")
        if latency_sensitive:
            reasons.append("latency-sensitive")
        if requests_per_day < THRESHOLDS["min_requests_for_batch"]:
            reasons.append(f"volume < {THRESHOLDS['min_requests_for_batch']}/day")

        return CostRecommendation(
            technique="batch_api",
            applicable=False,
            reason=" | ".join(reasons),
            estimated_savings="0%",
            monthly_savings_usd=0.0,
            implementation_complexity="N/A",
            rules_applied=rules,
        )

    def _analyze_model_tiering(self, workload: Dict) -> CostRecommendation:
        current_model = workload.get("current_model", "sonnet")
        complexity = workload.get("task_complexity", "medium")
        requests_per_day = workload.get("requests_per_day", 0)
        avg_input = workload.get("avg_input_tokens", 0)
        avg_output = workload.get("avg_output_tokens", 0)
        rules = ["model_selection_001_match_complexity"]

        # Check if downtiering is possible
        can_downtier = (
            current_model in ("opus", "sonnet")
            and complexity in ("low", "medium")
        )

        if can_downtier and requests_per_day > 0:
            current_tier = MODEL_TIERS[current_model]
            target = "haiku" if complexity == "low" else ("haiku" if current_model == "opus" else current_model)

            if target == current_model:
                return CostRecommendation(
                    technique="model_tiering",
                    applicable=False,
                    reason="Already using optimal model tier",
                    estimated_savings="0%",
                    monthly_savings_usd=0.0,
                    implementation_complexity="N/A",
                    rules_applied=rules,
                )

            target_tier = MODEL_TIERS[target]
            monthly = requests_per_day * 20
            current_cost = (
                (avg_input * monthly) / TOKENS_PER_MILLION * current_tier["input"]
                + (avg_output * monthly) / TOKENS_PER_MILLION * current_tier["output"]
            )
            target_cost = (
                (avg_input * monthly) / TOKENS_PER_MILLION * target_tier["input"]
                + (avg_output * monthly) / TOKENS_PER_MILLION * target_tier["output"]
            )
            savings = current_cost - target_cost
            pct = (savings / current_cost * 100) if current_cost > 0 else 0

            return CostRecommendation(
                technique="model_tiering",
                applicable=True,
                reason=f"Downtier {current_model} -> {target} for {complexity} complexity",
                estimated_savings=f"{pct:.0f}% by using {target}",
                monthly_savings_usd=round(savings, 2),
                implementation_complexity="low",
                rules_applied=rules,
            )

        return CostRecommendation(
            technique="model_tiering",
            applicable=False,
            reason=f"Model {current_model} appropriate for {complexity} complexity",
            estimated_savings="0%",
            monthly_savings_usd=0.0,
            implementation_complexity="N/A",
            rules_applied=rules,
        )

    def _analyze_compound(
        self, workload: Dict, cache_rec: CostRecommendation, batch_rec: CostRecommendation
    ) -> CostRecommendation:
        rules = ["compat_003_batch_caching_synergy", "dep_003_compound_requires_both"]

        if not (cache_rec.applicable and batch_rec.applicable):
            return CostRecommendation(
                technique="compound_optimization",
                applicable=False,
                reason="Requires both caching and batch to be applicable",
                estimated_savings="N/A",
                monthly_savings_usd=0.0,
                implementation_complexity="N/A",
                rules_applied=rules,
            )

        avg_input = workload.get("avg_input_tokens", 0)
        repeated = sum(workload.get("repeated_content", {}).values())
        avg_output = workload.get("avg_output_tokens", 0)
        requests_per_day = workload.get("requests_per_day", 0)
        model = workload.get("current_model", "sonnet")
        tier = MODEL_TIERS.get(model, MODEL_TIERS["sonnet"])

        monthly = requests_per_day * 20
        baseline = (
            (avg_input * monthly) / TOKENS_PER_MILLION * tier["input"]
            + (avg_output * monthly) / TOKENS_PER_MILLION * tier["output"]
        )

        batch_discounted = baseline * 0.5
        cache_portion = repeated / avg_input if avg_input > 0 else 0
        compound_cost = batch_discounted * (1 - cache_portion * 0.9)
        savings = baseline - compound_cost
        pct = min(95, (savings / baseline * 100) if baseline > 0 else 0)

        return CostRecommendation(
            technique="compound_optimization",
            applicable=True,
            reason="Both caching and batch applicable - synergistic optimization",
            estimated_savings=f"{pct:.0f}% combined (batch 50% + cache 90% on repeated)",
            monthly_savings_usd=round(savings, 2),
            implementation_complexity="medium",
            rules_applied=rules,
        )

    def _analyze_gemini_migration(self, workload: Dict) -> CostRecommendation:
        """Analyze cost savings from migrating eligible tasks to Gemini."""
        current_model = workload.get("current_model", "sonnet")
        complexity = workload.get("task_complexity", "medium")
        requests_per_day = workload.get("requests_per_day", 0)
        avg_input = workload.get("avg_input_tokens", 0)
        avg_output = workload.get("avg_output_tokens", 0)
        latency_sensitive = workload.get("latency_sensitive", True)
        rules = [
            "gemini_001_migration_analysis",
            "gemini_002_cost_comparison",
            "gemini_003_context_advantage",
        ]

        migration = MIGRATION_MAP.get(current_model)
        if not migration or requests_per_day == 0:
            return CostRecommendation(
                technique="gemini_migration",
                applicable=False,
                reason="No Gemini migration path available or no request volume",
                estimated_savings="0%",
                monthly_savings_usd=0.0,
                implementation_complexity="N/A",
                rules_applied=rules,
            )

        # Can migrate if: not latency-critical OR complexity is low/medium
        can_migrate = (not latency_sensitive) or complexity in ("low", "medium")

        if not can_migrate:
            return CostRecommendation(
                technique="gemini_migration",
                applicable=False,
                reason=f"Latency-sensitive + {complexity} complexity - keep on Claude",
                estimated_savings="0%",
                monthly_savings_usd=0.0,
                implementation_complexity="N/A",
                rules_applied=rules,
            )

        current_tier = MODEL_TIERS[current_model]
        target_model = migration["target"]
        target_tier = MODEL_TIERS[target_model]
        monthly = requests_per_day * 20

        current_cost = (
            (avg_input * monthly) / TOKENS_PER_MILLION * current_tier["input"]
            + (avg_output * monthly) / TOKENS_PER_MILLION * current_tier["output"]
        )
        gemini_cost = (
            (avg_input * monthly) / TOKENS_PER_MILLION * target_tier["input"]
            + (avg_output * monthly) / TOKENS_PER_MILLION * target_tier["output"]
        )
        savings = current_cost - gemini_cost
        pct = (savings / current_cost * 100) if current_cost > 0 else 0

        return CostRecommendation(
            technique="gemini_migration",
            applicable=True,
            reason=(
                f"Migrate {current_model} -> {target_model}: "
                f"{migration['quality_note']}. "
                f"Context: 200K -> 1M tokens."
            ),
            estimated_savings=f"{pct:.0f}% by using {target_model}",
            monthly_savings_usd=round(savings, 2),
            implementation_complexity="medium",
            rules_applied=rules,
        )

    def _detect_anti_patterns(self, workload: Dict) -> List[Dict]:
        anti_patterns = []
        rpd = workload.get("requests_per_day", 0)

        if rpd == 1:
            anti_patterns.append({
                "pattern": "cache_without_repetition",
                "severity": "critical",
                "message": "Single request/day makes caching ineffective",
            })

        if workload.get("latency_sensitive") and workload.get("async_compatible"):
            anti_patterns.append({
                "pattern": "batch_for_realtime",
                "severity": "critical",
                "message": "Batch API incompatible with latency-sensitive workloads",
            })

        thinking = workload.get("thinking_budget", 0)
        if thinking > 20000:
            anti_patterns.append({
                "pattern": "thinking_unbounded",
                "severity": "high",
                "message": f"Thinking budget {thinking} > 20K recommended max",
            })

        current = workload.get("current_model", "sonnet")
        complexity = workload.get("task_complexity", "medium")
        if current == "opus" and complexity in ("low", "medium"):
            anti_patterns.append({
                "pattern": "model_overuse",
                "severity": "medium",
                "message": f"Using {current} for {complexity} complexity tasks",
            })

        # Gemini-specific anti-patterns
        if rpd >= 100 and complexity in ("low", "medium") and current in ("sonnet", "opus"):
            anti_patterns.append({
                "pattern": "ignoring_gemini_for_bulk",
                "severity": "medium",
                "message": (
                    f"{rpd} requests/day of {complexity} complexity on {current} — "
                    f"consider Gemini 2.5 Flash for {MIGRATION_MAP.get(current, {}).get('savings_pct', 50)}% savings"
                ),
            })

        return anti_patterns


# ============================================================================
# L5: CLI
# ============================================================================

if __name__ == "__main__":
    analyzer = CostAdvisorAnalyzer()
    run_standard_cli(
        agent_name="Cost Optimization Advisor",
        description="Analyze workloads for caching, batching, and model tiering opportunities",
        analyzer=analyzer,
    )

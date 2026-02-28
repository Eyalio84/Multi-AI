#!/usr/bin/env python3
"""
Multi-Model Orchestrator Agent v1.1

Master orchestrator across Claude (Opus/Sonnet/Haiku) and Gemini
(3-Pro/2.5-Pro/2.5-Flash) models. Assigns roles, routes tasks,
estimates costs, plans execution order, and delegates Gemini tasks
via GeminiDelegatorAnalyzer.

Layer: L1-L5 (Full 5-layer pattern via agent_base)

Usage:
    python3 multi_model_orchestrator.py --example
    python3 multi_model_orchestrator.py --workload plan.json --summary

Created: February 6, 2026
Updated: February 6, 2026 (v1.1 - Tier 2 Gemini execution routing)
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.agent_base import (
    AgentInput, AgentOutput, BaseAnalyzer, run_standard_cli,
    PRICING, GEMINI_MODELS, GEMINI_CAPABILITIES, TOKENS_PER_MILLION,
)

from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any, Optional


# ============================================================================
# L1: Data Models
# ============================================================================

@dataclass
class TaskAssignment:
    name: str
    complexity: str  # trivial, simple, moderate, complex, strategic
    role: str  # architect, coder, documenter, enhancer, orchestrator
    provider: str  # claude or gemini
    model: str
    thinking_budget: int
    estimated_cost: float
    reasoning: str
    parallel_group: int  # tasks in same group run in parallel


# ============================================================================
# L2: Constants
# ============================================================================

ALL_MODELS = {
    # Claude models
    "opus": {"provider": "claude", "input": 15.00, "output": 75.00, "tier": "strategic", "context": 200000},
    "sonnet": {"provider": "claude", "input": 3.00, "output": 15.00, "tier": "balanced", "context": 200000},
    "haiku": {"provider": "claude", "input": 0.80, "output": 4.00, "tier": "fast", "context": 200000},
    # Gemini models
    "gemini-2.5-flash": {"provider": "gemini", "input": 0.15, "output": 0.60, "tier": "bulk", "context": 1048576},
    "gemini-2.5-pro": {"provider": "gemini", "input": 1.25, "output": 5.00, "tier": "balanced", "context": 1048576},
    "gemini-3-pro-preview": {"provider": "gemini", "input": 2.50, "output": 10.00, "tier": "premium", "context": 1048576},
    "gemini-3-flash-preview": {"provider": "gemini", "input": 0.50, "output": 2.00, "tier": "fast", "context": 1048576},
}

ROLE_TO_MODELS = {
    "architect": ["opus"],
    "coder": ["sonnet", "gemini-2.5-pro"],
    "documenter": ["haiku", "gemini-2.5-flash"],
    "enhancer": ["gemini-3-pro-preview"],
    "orchestrator": ["sonnet"],
    "bulk_processor": ["gemini-2.5-flash"],
    "large_context": ["gemini-2.5-pro", "gemini-3-pro-preview"],
    "search": ["gemini-3-pro-preview"],
    "code_execution": ["gemini-2.5-pro", "gemini-3-pro-preview"],
    "embeddings": ["gemini-embedding-001"],
}

COMPLEXITY_TO_ROLE = {
    "trivial": "documenter",
    "simple": "documenter",
    "moderate": "coder",
    "complex": "coder",
    "strategic": "architect",
}

THINKING_BY_COMPLEXITY = {
    "trivial": 0, "simple": 1000, "moderate": 4000,
    "complex": 6000, "strategic": 8000,
}

# Gemini capability requirements mapping
CAPABILITY_TO_ROLE = {
    "web_search": "search",
    "google_search_grounding": "search",
    "code_execution": "code_execution",
    "function_calling": "coder",
    "embeddings": "embeddings",
}


# ============================================================================
# L3: Analyzer
# ============================================================================

class MultiModelOrchestratorAnalyzer(BaseAnalyzer):
    """Multi-model task routing and cost optimization engine."""

    def __init__(self):
        super().__init__(
            agent_name="multi-model-orchestrator",
            model="opus",
            version="1.1",
        )
        self._delegator = None

    def _get_delegator(self):
        """Lazy-load GeminiDelegatorAnalyzer for execution mode."""
        if self._delegator is None:
            try:
                from multi_model.gemini_delegator import GeminiDelegatorAnalyzer
                self._delegator = GeminiDelegatorAnalyzer()
            except ImportError:
                try:
                    from gemini_delegator import GeminiDelegatorAnalyzer
                    self._delegator = GeminiDelegatorAnalyzer()
                except ImportError:
                    self._delegator = False  # Mark as unavailable
        return self._delegator if self._delegator is not False else None

    def get_example_input(self) -> Dict[str, Any]:
        return {
            "name": "Full KG Enhancement + Documentation Pipeline",
            "tasks": [
                {"name": "Scan all KG databases", "complexity": "simple"},
                {"name": "Analyze 8 handbooks (31K lines)", "complexity": "simple", "context_tokens": 300000},
                {"name": "Detect orphaned nodes", "complexity": "moderate"},
                {"name": "Suggest new relationships", "complexity": "complex"},
                {"name": "Generate gap-fill nodes", "complexity": "complex"},
                {"name": "Update all documentation", "complexity": "simple"},
                {"name": "Plan merge strategy", "complexity": "strategic"},
                {"name": "Validate merged KG", "complexity": "moderate"},
                {"name": "Generate case study doc", "complexity": "moderate"},
                {"name": "Bulk categorize 200 files", "complexity": "trivial", "batch_size": 200},
                {"name": "Search latest API docs", "complexity": "moderate", "requires_capability": "web_search"},
                {"name": "Run statistical analysis", "complexity": "complex", "requires_capability": "code_execution"},
            ],
            "budget_usd": 2.00,
            "priority": "balanced",  # cost-first, balanced, quality-first
            "execute_gemini": False,  # Set True to actually call Gemini API
        }

    def analyze(self, agent_input: AgentInput) -> AgentOutput:
        w = agent_input.workload
        tasks = w.get("tasks", [])
        budget = w.get("budget_usd", 5.00)
        priority = w.get("priority", "balanced")
        execute_gemini = w.get("execute_gemini", False)

        rules = [
            "orch_001_multi_model_routing",
            "orch_002_role_assignment",
            "orch_003_cost_optimization",
            "orch_004_parallel_planning",
            "orch_005_gemini_context_routing",
            "orch_006_capability_matching",
            "orch_007_gemini_execution",
        ]

        assignments = []
        parallel_group = 0
        prev_deps = False

        for task in tasks:
            name = task.get("name", "unnamed")
            complexity = task.get("complexity", "moderate")
            context_tokens = task.get("context_tokens", 5000)
            batch_size = task.get("batch_size", 1)
            depends_on = task.get("depends_on", [])
            requires_cap = task.get("requires_capability", None)

            # Determine role - capability requirements take priority
            if requires_cap and requires_cap in CAPABILITY_TO_ROLE:
                role = CAPABILITY_TO_ROLE[requires_cap]
            elif context_tokens > 200000:
                role = "large_context"
            elif batch_size > 50:
                role = "bulk_processor"
            else:
                role = COMPLEXITY_TO_ROLE.get(complexity, "coder")

            # Select model based on role and priority
            candidates = ROLE_TO_MODELS.get(role, ["sonnet"])
            if priority == "cost-first":
                model = min(candidates, key=lambda m: ALL_MODELS[m]["input"])
            elif priority == "quality-first":
                model = max(candidates, key=lambda m: ALL_MODELS[m]["input"])
            else:
                model = candidates[0]

            config = ALL_MODELS[model]
            thinking = THINKING_BY_COMPLEXITY.get(complexity, 4000)
            if config["provider"] == "gemini":
                thinking = 0  # Gemini uses its own thinking

            # Cost estimate
            avg_input = context_tokens + thinking
            avg_output = max(1000, context_tokens // 5)
            cost = (avg_input / TOKENS_PER_MILLION * config["input"] +
                    avg_output / TOKENS_PER_MILLION * config["output"])
            cost *= max(1, batch_size / 10)

            # Parallel grouping
            if depends_on:
                parallel_group += 1
                prev_deps = True
            elif not prev_deps:
                pass  # Same group
            else:
                prev_deps = False

            assignments.append(TaskAssignment(
                name=name,
                complexity=complexity,
                role=role,
                provider=config["provider"],
                model=model,
                thinking_budget=thinking,
                estimated_cost=round(cost, 4),
                reasoning=f"{complexity} -> {role} -> {model} ({config['provider']})",
                parallel_group=parallel_group,
            ))

        # Calculate costs
        total_cost = sum(a.estimated_cost for a in assignments)
        claude_cost = sum(a.estimated_cost for a in assignments if a.provider == "claude")
        gemini_cost = sum(a.estimated_cost for a in assignments if a.provider == "gemini")

        # All-opus baseline
        all_opus_cost = sum(
            ((5000 + 8000) / TOKENS_PER_MILLION * 15.00 +
             2000 / TOKENS_PER_MILLION * 75.00)
            for _ in assignments
        )
        savings = (1 - total_cost / max(0.001, all_opus_cost)) * 100

        # Provider distribution
        by_provider = {"claude": 0, "gemini": 0}
        by_model = {}
        for a in assignments:
            by_provider[a.provider] += 1
            by_model[a.model] = by_model.get(a.model, 0) + 1

        # Execute Gemini tasks if requested
        gemini_execution_results = []
        if execute_gemini:
            delegator = self._get_delegator()
            if delegator:
                gemini_tasks = [
                    {
                        "name": a.name,
                        "type": "analyze",
                        "prompt": f"Task: {a.name}",
                        "model": a.model,
                        "execute": True,
                    }
                    for a in assignments if a.provider == "gemini"
                ]
                if gemini_tasks:
                    gemini_execution_results = delegator.delegate_batch(
                        gemini_tasks, dry_run=False
                    )

        anti_patterns = []
        if total_cost > budget:
            anti_patterns.append(f"Budget exceeded: ${total_cost:.2f} > ${budget:.2f}")
        if by_provider["gemini"] == 0 and any(t.get("context_tokens", 0) > 200000 for t in tasks):
            anti_patterns.append("Large context tasks not routed to Gemini (1M context)")
        if by_provider["gemini"] == 0 and any(t.get("requires_capability") in ("web_search", "code_execution") for t in tasks):
            anti_patterns.append("Capability-requiring tasks not routed to Gemini")

        recommendations = [{
            "technique": "multi_model_orchestration",
            "applicable": True,
            "total_tasks": len(assignments),
            "provider_distribution": by_provider,
            "model_distribution": by_model,
            "total_cost_usd": round(total_cost, 4),
            "claude_cost_usd": round(claude_cost, 4),
            "gemini_cost_usd": round(gemini_cost, 4),
            "all_opus_baseline_usd": round(all_opus_cost, 4),
            "savings_vs_opus": f"{savings:.0f}%",
            "within_budget": total_cost <= budget,
            "assignments": [asdict(a) for a in assignments],
            "rules_applied": rules,
        }]

        # Parallel groups
        groups = {}
        for a in assignments:
            groups.setdefault(a.parallel_group, []).append(a.name)
        parallel_stages = len(groups)

        meta_insight = (
            f"Orchestrated {len(assignments)} tasks across {len(by_model)} models "
            f"({by_provider['claude']} Claude, {by_provider['gemini']} Gemini). "
            f"Cost: ${total_cost:.3f} (saves {savings:.0f}% vs all-Opus). "
            f"{parallel_stages} parallel stages."
        )

        analysis = {
            "assignments": [asdict(a) for a in assignments],
            "costs": {"total": round(total_cost, 4), "claude": round(claude_cost, 4), "gemini": round(gemini_cost, 4)},
            "savings_vs_opus_pct": round(savings, 1),
            "parallel_stages": parallel_stages,
            "parallel_groups": {str(k): v for k, v in groups.items()},
            "gemini_capabilities_used": list({
                t.get("requires_capability") for t in tasks
                if t.get("requires_capability")
            }),
        }
        if gemini_execution_results:
            from dataclasses import asdict as _asdict
            analysis["gemini_execution"] = [_asdict(r) for r in gemini_execution_results]

        return AgentOutput(
            recommendations=recommendations,
            rules_applied=rules,
            meta_insight=meta_insight,
            analysis_data=analysis,
            anti_patterns=anti_patterns,
            agent_metadata=self.build_metadata(),
        )


if __name__ == "__main__":
    analyzer = MultiModelOrchestratorAnalyzer()
    run_standard_cli(
        agent_name="Multi-Model Orchestrator",
        description="Master orchestrator across Claude and Gemini model families",
        analyzer=analyzer,
    )

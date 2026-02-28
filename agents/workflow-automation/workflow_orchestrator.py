#!/usr/bin/env python3
"""
Workflow Orchestrator Agent v1.1

Plans multi-phase workflows with playbook selection, tool chaining,
thinking budget allocation, cross-provider model selection (Claude + Gemini),
and parallel execution planning.

Wraps: AI-LAB workflow_analyzer.py, task_classifier.py, agent_pattern_analyzer.py
Layer: L1-L5 (Full 5-layer pattern via agent_base)

Usage:
    python3 workflow_orchestrator.py --example
    python3 workflow_orchestrator.py --workload workflow.json --summary

Created: February 6, 2026
Updated: February 6, 2026 (v1.1 - Tier 2 Gemini model selection)
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.agent_base import (
    AgentInput, AgentOutput, BaseAnalyzer, run_standard_cli,
    PRICING, GEMINI_MODELS, TOKENS_PER_MILLION,
)

from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any, Optional
from enum import Enum


# ============================================================================
# L1: Data Models
# ============================================================================

class StepComplexity(Enum):
    TRIVIAL = "trivial"
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


@dataclass
class WorkflowStep:
    name: str
    description: str
    complexity: str = "moderate"
    category: str = "general"
    model: str = "sonnet"
    provider: str = "claude"
    thinking_budget: int = 4000
    estimated_minutes: float = 5.0
    estimated_cost_usd: float = 0.01
    tools: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)
    parallelizable: bool = False


# ============================================================================
# L2: Constants
# ============================================================================

# Claude-only model selection (default)
MODEL_SELECTION = {
    "trivial": "haiku",
    "simple": "haiku",
    "moderate": "sonnet",
    "complex": "sonnet",
    "very_complex": "opus",
}

# Cross-provider model selection (cost-optimized)
MODEL_SELECTION_CROSS_PROVIDER = {
    "trivial": "gemini-2.5-flash-lite",
    "simple": "gemini-2.5-flash",
    "moderate": "sonnet",
    "complex": "gemini-2.5-pro",
    "very_complex": "opus",
    "large_context": "gemini-2.5-pro",
    "bulk": "gemini-2.5-flash",
    "search": "gemini-3-pro",
    "code_execution": "gemini-2.5-pro",
}

# Model pricing for cross-provider cost estimation
ALL_MODEL_PRICING = {
    "haiku": {"input": 0.80, "output": 4.00, "provider": "claude"},
    "sonnet": {"input": 3.00, "output": 15.00, "provider": "claude"},
    "opus": {"input": 15.00, "output": 75.00, "provider": "claude"},
    "gemini-2.5-flash-lite": {"input": 0.10, "output": 0.40, "provider": "gemini"},
    "gemini-2.5-flash": {"input": 0.15, "output": 0.60, "provider": "gemini"},
    "gemini-2.5-pro": {"input": 1.25, "output": 5.00, "provider": "gemini"},
    "gemini-3-flash": {"input": 0.50, "output": 3.00, "provider": "gemini"},
    "gemini-3-pro": {"input": 2.00, "output": 12.00, "provider": "gemini"},
}

THINKING_BUDGETS = {
    "trivial": 0,
    "simple": 1000,
    "moderate": 3000,
    "complex": 6000,
    "very_complex": 8000,
}

CATEGORY_TIME_MULTIPLIERS = {
    "planning": 1.3,
    "design": 1.4,
    "implementation": 1.0,
    "validation": 0.8,
    "review": 0.6,
    "general": 1.0,
}

WORKFLOW_TEMPLATES = {
    "dev_lifecycle": [
        {"name": "Requirements", "category": "planning", "complexity": "moderate"},
        {"name": "Design", "category": "design", "complexity": "complex"},
        {"name": "Implementation", "category": "implementation", "complexity": "complex"},
        {"name": "Testing", "category": "validation", "complexity": "moderate"},
        {"name": "Review", "category": "review", "complexity": "simple"},
    ],
    "research_analysis": [
        {"name": "Question Formulation", "category": "planning", "complexity": "moderate"},
        {"name": "Literature Review", "category": "general", "complexity": "complex"},
        {"name": "Analysis", "category": "implementation", "complexity": "complex"},
        {"name": "Synthesis", "category": "design", "complexity": "very_complex"},
        {"name": "Reporting", "category": "general", "complexity": "moderate"},
    ],
    "kg_pipeline": [
        {"name": "Extract", "category": "implementation", "complexity": "moderate"},
        {"name": "Validate", "category": "validation", "complexity": "simple"},
        {"name": "Enrich", "category": "design", "complexity": "complex"},
        {"name": "Merge", "category": "implementation", "complexity": "moderate"},
        {"name": "Verify", "category": "validation", "complexity": "simple"},
    ],
    "decision_making": [
        {"name": "Problem Definition", "category": "planning", "complexity": "moderate"},
        {"name": "Options Generation", "category": "design", "complexity": "complex"},
        {"name": "Analysis", "category": "implementation", "complexity": "complex"},
        {"name": "Decision", "category": "review", "complexity": "very_complex"},
        {"name": "Communication", "category": "general", "complexity": "simple"},
    ],
}


# ============================================================================
# L3: Analyzer
# ============================================================================

class WorkflowOrchestratorAnalyzer(BaseAnalyzer):
    """Workflow planning and optimization engine."""

    def __init__(self):
        super().__init__(
            agent_name="workflow-orchestrator",
            model="sonnet",
            version="1.1",
        )

    def get_example_input(self) -> Dict[str, Any]:
        return {
            "name": "KG Enhancement Pipeline",
            "template": "kg_pipeline",
            "goal": "Extract new nodes from handbooks, validate quality, enrich with relationships, merge into main KG, and verify integrity",
            "total_budget_usd": 1.00,
            "max_time_minutes": 60,
            "cross_provider": True,  # Enable Gemini model selection
            "available_tools": [
                "kg_health_monitor", "relationship_suggester", "kg_completer",
                "cost_advisor", "thinking_budget_optimizer", "gemini_delegator",
            ],
        }

    def analyze(self, agent_input: AgentInput) -> AgentOutput:
        w = agent_input.workload
        template_name = w.get("template", "dev_lifecycle")
        goal = w.get("goal", "")
        total_budget = w.get("total_budget_usd", 1.00)
        max_time = w.get("max_time_minutes", 60)
        available_tools = w.get("available_tools", [])
        cross_provider = w.get("cross_provider", False)

        rules = [
            "workflow_001_template_selection",
            "workflow_002_complexity_classification",
            "workflow_003_budget_allocation",
            "workflow_004_model_selection",
            "workflow_005_parallelization",
        ]
        if cross_provider:
            rules.append("workflow_006_cross_provider_routing")
            rules.append("workflow_007_gemini_context_advantage")

        # Select model mapping
        model_map = MODEL_SELECTION_CROSS_PROVIDER if cross_provider else MODEL_SELECTION

        # Get template steps
        template = WORKFLOW_TEMPLATES.get(template_name, WORKFLOW_TEMPLATES["dev_lifecycle"])

        # Build workflow steps with optimized parameters
        steps = []
        total_cost = 0
        total_time = 0

        for i, step_def in enumerate(template):
            complexity = step_def["complexity"]
            category = step_def["category"]

            model = model_map.get(complexity, model_map.get("moderate", "sonnet"))
            thinking = THINKING_BUDGETS.get(complexity, 3000)
            base_time = 5.0 * CATEGORY_TIME_MULTIPLIERS.get(category, 1.0)

            # Determine provider from model
            pricing_info = ALL_MODEL_PRICING.get(model, ALL_MODEL_PRICING.get("sonnet"))
            provider = pricing_info["provider"]

            # Gemini models don't use Claude thinking budgets
            if provider == "gemini":
                thinking = 0

            # Cost estimation using cross-provider pricing
            est_tokens = 2000 + thinking
            cost = (est_tokens / TOKENS_PER_MILLION * pricing_info["input"] +
                    max(500, est_tokens // 3) / TOKENS_PER_MILLION * pricing_info["output"])

            # Parallelization detection
            parallelizable = i > 0 and not any(
                dep in step_def.get("depends_on", [])
                for dep in [s["name"] for s in template[:i]]
            )

            # Assign tools
            step_tools = []
            for tool in available_tools:
                tool_lower = tool.lower()
                if category == "validation" and "health" in tool_lower:
                    step_tools.append(tool)
                elif category == "design" and ("suggest" in tool_lower or "complete" in tool_lower):
                    step_tools.append(tool)
                elif category == "implementation" and ("complete" in tool_lower or "extract" in tool_lower):
                    step_tools.append(tool)

            step = WorkflowStep(
                name=step_def["name"],
                description=f"{step_def['name']} phase for: {goal[:80]}",
                complexity=complexity,
                category=category,
                model=model,
                provider=provider,
                thinking_budget=thinking,
                estimated_minutes=round(base_time, 1),
                estimated_cost_usd=round(cost, 4),
                tools=step_tools,
                depends_on=[template[i - 1]["name"]] if i > 0 else [],
                parallelizable=parallelizable,
            )
            steps.append(step)
            total_cost += cost
            total_time += base_time

        # Budget check
        anti_patterns = []
        if total_cost > total_budget:
            anti_patterns.append(
                f"Budget exceeded: estimated ${total_cost:.2f} > limit ${total_budget:.2f}"
            )
        if total_time > max_time:
            anti_patterns.append(
                f"Time exceeded: estimated {total_time:.0f}min > limit {max_time}min"
            )

        # Parallel time estimation
        parallel_groups = self._find_parallel_groups(steps)
        parallel_time = sum(
            max(s.estimated_minutes for s in group)
            for group in parallel_groups
        )

        # Build recommendations
        recommendations = [{
            "technique": "workflow_plan",
            "applicable": True,
            "template": template_name,
            "total_steps": len(steps),
            "steps": [asdict(s) for s in steps],
            "total_cost_usd": round(total_cost, 4),
            "sequential_time_min": round(total_time, 1),
            "parallel_time_min": round(parallel_time, 1),
            "speedup": round(total_time / max(1, parallel_time), 1),
            "parallel_groups": len(parallel_groups),
            "rules_applied": rules,
        }]

        # Model and provider distribution
        model_dist = {}
        provider_dist = {"claude": 0, "gemini": 0}
        for s in steps:
            model_dist[s.model] = model_dist.get(s.model, 0) + 1
            provider_dist[s.provider] = provider_dist.get(s.provider, 0) + 1

        provider_note = ""
        if cross_provider and provider_dist["gemini"] > 0:
            provider_note = f" Cross-provider: {provider_dist['claude']} Claude, {provider_dist['gemini']} Gemini."

        meta_insight = (
            f"Workflow '{template_name}' with {len(steps)} steps: "
            f"${total_cost:.3f} total, {parallel_time:.0f}min parallel "
            f"({total_time / max(1, parallel_time):.1f}x speedup). "
            f"Models: {', '.join(f'{m}({c})' for m, c in model_dist.items())}."
            f"{provider_note}"
        )

        return AgentOutput(
            recommendations=recommendations,
            rules_applied=list(dict.fromkeys(rules)),
            meta_insight=meta_insight,
            analysis_data={
                "template": template_name,
                "steps": [asdict(s) for s in steps],
                "cost": {
                    "total": round(total_cost, 4),
                    "budget": total_budget,
                    "within_budget": total_cost <= total_budget,
                },
                "time": {
                    "sequential_min": round(total_time, 1),
                    "parallel_min": round(parallel_time, 1),
                    "max_allowed_min": max_time,
                },
                "model_distribution": model_dist,
                "provider_distribution": provider_dist,
                "cross_provider_enabled": cross_provider,
                "parallel_groups": [
                    [s.name for s in group] for group in parallel_groups
                ],
            },
            anti_patterns=anti_patterns,
            agent_metadata=self.build_metadata(),
        )

    def _find_parallel_groups(self, steps: List[WorkflowStep]) -> List[List[WorkflowStep]]:
        """Group steps that can run in parallel."""
        groups = []
        current_group = []

        for step in steps:
            if step.parallelizable and current_group:
                current_group.append(step)
            else:
                if current_group:
                    groups.append(current_group)
                current_group = [step]

        if current_group:
            groups.append(current_group)

        return groups


# ============================================================================
# L5: CLI
# ============================================================================

if __name__ == "__main__":
    analyzer = WorkflowOrchestratorAnalyzer()
    run_standard_cli(
        agent_name="Workflow Orchestrator",
        description="Plan multi-phase workflows with optimal tool chaining and model selection",
        analyzer=analyzer,
    )

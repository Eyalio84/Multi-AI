#!/usr/bin/env python3
"""
Thinking Budget Optimizer Agent

Allocates optimal extended thinking budgets per workflow step based on
task complexity indicators. Detects budget anti-patterns and estimates
quality/cost tradeoffs.

Wraps: AI-LAB thinking_budget_optimizer.py, thinking_roi_estimator.py,
       thinking_quality_validator.py
Layer: L1-L5 (Full 5-layer pattern via agent_base)

Usage:
    python3 thinking_budget_agent.py --example
    python3 thinking_budget_agent.py --workload task.json
    python3 thinking_budget_agent.py --workload task.json --summary

Created: February 6, 2026
"""

import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.agent_base import (
    AgentInput, AgentOutput, BaseAnalyzer, run_standard_cli,
)

from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any, Tuple
from enum import Enum


# ============================================================================
# L1: Data Models
# ============================================================================

class TaskType(Enum):
    REQUIREMENTS_ANALYSIS = "requirements_analysis"
    ARCHITECTURE_DESIGN = "architecture_design"
    API_DESIGN = "api_design"
    CODE_DEBUGGING = "code_debugging"
    RESEARCH_ANALYSIS = "research_analysis"
    SYSTEM_OPTIMIZATION = "system_optimization"
    DECISION_MAKING = "decision_making"
    CONTENT_CREATION = "content_creation"
    CODE_REVIEW = "code_review"
    PROBLEM_SOLVING = "problem_solving"


class ComplexityLevel(Enum):
    TRIVIAL = "trivial"
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


@dataclass
class ComplexityIndicators:
    decision_points: int = 0
    dependencies: int = 0
    stakeholders: int = 1
    novelty: str = "low"
    scope: str = "single_file"
    time_pressure: str = "normal"


# ============================================================================
# L2: Constants
# ============================================================================

BASE_BUDGETS = {
    "requirements_analysis": 4000,
    "architecture_design": 8000,
    "api_design": 6000,
    "code_debugging": 6000,
    "research_analysis": 7000,
    "system_optimization": 10000,
    "decision_making": 8000,
    "content_creation": 4000,
    "code_review": 5000,
    "problem_solving": 7000,
}

PREVENTION_FACTORS = {
    "trivial": 0.0,
    "simple": 0.0,
    "moderate": 0.4,
    "complex": 0.7,
    "very_complex": 0.85,
}

NOVELTY_MULTIPLIERS = {
    "low": 1.0,
    "moderate": 1.2,
    "high": 1.5,
    "very_high": 1.8,
}

BUDGET_PLATEAU = 8000  # Diminishing returns beyond this

PHASE_ALLOCATIONS = {
    "requirements_analysis": {
        "problem_analysis": 0.40,
        "requirement_clarification": 0.40,
        "edge_case_identification": 0.20,
    },
    "architecture_design": {
        "problem_analysis": 0.30,
        "solution_design": 0.45,
        "validation": 0.20,
        "edge_cases": 0.05,
    },
    "code_debugging": {
        "problem_analysis": 0.35,
        "root_cause_finding": 0.40,
        "solution_design": 0.25,
    },
    "system_optimization": {
        "baseline_analysis": 0.25,
        "optimization_strategy": 0.40,
        "tradeoff_analysis": 0.25,
        "validation": 0.10,
    },
    "default": {
        "problem_analysis": 0.30,
        "solution_design": 0.50,
        "validation": 0.20,
    },
}


# ============================================================================
# L3: Analyzer
# ============================================================================

class ThinkingBudgetAnalyzer(BaseAnalyzer):
    """Thinking budget optimization engine."""

    def __init__(self):
        super().__init__(
            agent_name="thinking-budget-optimizer",
            model="haiku",
            version="1.0",
        )

    def get_example_input(self) -> Dict[str, Any]:
        return {
            "name": "API Gateway Architecture Design",
            "task_type": "architecture_design",
            "decision_points": 8,
            "dependencies": 12,
            "stakeholders": 3,
            "novelty": "moderate",
            "scope": "multi_module",
            "time_pressure": "normal",
            "max_budget": 10000,
            "min_budget": 500,
            "workflow_steps": [
                {"name": "Requirements gathering", "type": "requirements_analysis"},
                {"name": "Architecture design", "type": "architecture_design"},
                {"name": "API design", "type": "api_design"},
                {"name": "Code review", "type": "code_review"},
            ],
        }

    def analyze(self, agent_input: AgentInput) -> AgentOutput:
        w = agent_input.workload
        task_type = w.get("task_type", "problem_solving")

        indicators = ComplexityIndicators(
            decision_points=w.get("decision_points", 0),
            dependencies=w.get("dependencies", 0),
            stakeholders=w.get("stakeholders", 1),
            novelty=w.get("novelty", "low"),
            scope=w.get("scope", "single_file"),
            time_pressure=w.get("time_pressure", "normal"),
        )

        max_budget = w.get("max_budget", 10000)
        min_budget = w.get("min_budget", 500)

        # Step 1: Calculate complexity score
        score, level = self._calculate_complexity(indicators)

        # Step 2: Calculate optimal budget
        budget = self._calculate_budget(score, task_type, indicators, max_budget, min_budget)

        # Step 3: Phase breakdown
        breakdown = self._breakdown_budget(budget, task_type)

        # Step 4: Expected outcomes
        outcomes = self._estimate_outcomes(score, level, budget, task_type)

        # Step 5: Anti-patterns
        anti_patterns = self._detect_anti_patterns(level, budget, max_budget, outcomes)

        # Step 6: Workflow step budgets (if provided)
        workflow_budgets = None
        steps = w.get("workflow_steps", [])
        if steps:
            workflow_budgets = self._allocate_workflow(steps, indicators)

        # Rules
        rules = [
            "extended_thinking_002_budget_required",
            "extended_thinking_004_complex_problems_use",
            "extended_thinking_018_budget_formula",
        ]
        if level in (ComplexityLevel.COMPLEX, ComplexityLevel.VERY_COMPLEX):
            rules.append("extended_thinking_013_prevention_factor")
            rules.append("extended_thinking_016_adaptive_workflows")

        # Confidence
        confidence = 0.90
        if level == ComplexityLevel.MODERATE:
            confidence = 0.75
        if anti_patterns:
            confidence *= 0.85

        # Build recommendations
        recommendations = [{
            "technique": "thinking_budget_allocation",
            "applicable": True,
            "recommended_budget": budget,
            "confidence": round(confidence, 2),
            "complexity_level": level.value,
            "complexity_score": round(score, 3),
            "phase_breakdown": breakdown,
            "expected_outcomes": outcomes,
            "rules_applied": rules,
        }]

        if workflow_budgets:
            recommendations.append({
                "technique": "workflow_step_budgets",
                "applicable": True,
                "step_budgets": workflow_budgets,
                "total_budget": sum(s["budget"] for s in workflow_budgets),
                "rules_applied": ["extended_thinking_016_adaptive_workflows"],
            })

        # Strategy comparison
        strategies = self._compare_strategies(budget)

        # Meta-insight
        if level in (ComplexityLevel.COMPLEX, ComplexityLevel.VERY_COMPLEX):
            prevented = outcomes.get("revisions_prevented", 0)
            roi = outcomes.get("roi_multiplier", 0)
            meta_insight = (
                f"{level.value.upper()} task: {budget:,} tokens prevents "
                f"~{prevented} revisions (ROI: {roi}x). "
                f"Thinking is a high-value investment here."
            )
        elif level == ComplexityLevel.MODERATE:
            meta_insight = (
                f"MODERATE task: {budget:,} tokens is a balanced allocation. "
                f"Consider reducing to {budget * 3 // 4:,} if latency matters."
            )
        else:
            meta_insight = (
                f"{level.value.upper()} task: minimal thinking needed ({budget:,} tokens). "
                f"Save budget for complex decisions."
            )

        return AgentOutput(
            recommendations=recommendations,
            rules_applied=list(dict.fromkeys(rules)),
            meta_insight=meta_insight,
            analysis_data={
                "complexity": {
                    "score": round(score, 3),
                    "level": level.value,
                    "indicators": asdict(indicators),
                },
                "budget": {
                    "recommended": budget,
                    "confidence": round(confidence, 2),
                    "breakdown": breakdown,
                },
                "outcomes": outcomes,
                "strategies": strategies,
                "workflow_budgets": workflow_budgets,
            },
            anti_patterns=anti_patterns,
            agent_metadata=self.build_metadata(),
        )

    def _calculate_complexity(self, ind: ComplexityIndicators) -> Tuple[float, ComplexityLevel]:
        decision_score = min(0.4, ind.decision_points / 40.0)
        dependency_score = min(0.3, ind.dependencies / 100.0)
        stakeholder_score = min(0.15, (ind.stakeholders - 1) / 40.0)

        novelty_scores = {"low": 0.0, "moderate": 0.05, "high": 0.10, "very_high": 0.15}
        novelty_score = novelty_scores.get(ind.novelty, 0.0)

        scope_scores = {"single_file": 0.0, "single_module": 0.03, "multi_module": 0.07, "system": 0.10}
        scope_score = scope_scores.get(ind.scope, 0.05)

        pressure = 1.0
        if ind.time_pressure == "high":
            pressure = 0.95
        elif ind.time_pressure == "critical":
            pressure = 0.90

        total = (decision_score + dependency_score + stakeholder_score + novelty_score + scope_score) * pressure
        total = min(1.0, max(0.0, total))

        if total < 0.1:
            level = ComplexityLevel.TRIVIAL
        elif total < 0.3:
            level = ComplexityLevel.SIMPLE
        elif total < 0.5:
            level = ComplexityLevel.MODERATE
        elif total < 0.7:
            level = ComplexityLevel.COMPLEX
        else:
            level = ComplexityLevel.VERY_COMPLEX

        return total, level

    def _calculate_budget(
        self, score: float, task_type: str, ind: ComplexityIndicators,
        max_budget: int, min_budget: int,
    ) -> int:
        base = BASE_BUDGETS.get(task_type, 6000)
        complexity_mult = score ** 0.8
        novelty_mult = NOVELTY_MULTIPLIERS.get(ind.novelty, 1.0)

        pressure_factor = 1.0
        if ind.time_pressure == "critical":
            pressure_factor = 0.7

        dep_factor = 1.0 + (min(30, ind.dependencies) / 300.0)

        optimal = int(base * complexity_mult * novelty_mult * dep_factor * pressure_factor)
        return max(min_budget, min(max_budget, optimal))

    def _breakdown_budget(self, budget: int, task_type: str) -> Dict[str, int]:
        allocs = PHASE_ALLOCATIONS.get(task_type, PHASE_ALLOCATIONS["default"])
        return {phase: int(budget * pct) for phase, pct in allocs.items()}

    def _estimate_outcomes(
        self, score: float, level: ComplexityLevel, budget: int, task_type: str,
    ) -> Dict:
        prevention = PREVENTION_FACTORS.get(level.value, 0.0)
        revisions_map = {
            "requirements_analysis": 1, "architecture_design": 3, "api_design": 2,
            "code_debugging": 2, "research_analysis": 2, "system_optimization": 4,
            "decision_making": 2, "content_creation": 1, "code_review": 1,
            "problem_solving": 2,
        }
        est_revisions = revisions_map.get(task_type, 2)
        depth_factor = min(1.0, budget / BUDGET_PLATEAU)
        prevented = round(est_revisions * prevention * depth_factor)
        time_saved = prevented * 0.75
        cost_delta = 0.045 * (budget / BUDGET_PLATEAU)
        roi = round(time_saved / cost_delta, 1) if cost_delta > 0 else 0

        return {
            "revisions_prevented": prevented,
            "revisions_remaining": max(0, est_revisions - prevented),
            "time_saved_hours": round(time_saved, 2),
            "cost_delta_usd": round(cost_delta, 4),
            "roi_multiplier": roi,
            "quality_improvement": round(max(0, 0.95 - (0.6 + 0.1 * est_revisions)), 3),
        }

    def _detect_anti_patterns(
        self, level: ComplexityLevel, budget: int, max_budget: int, outcomes: Dict,
    ) -> List[str]:
        patterns = []
        if level in (ComplexityLevel.TRIVIAL, ComplexityLevel.SIMPLE) and budget > 2000:
            patterns.append("anti_004a: budget >2K on simple task")
        if level == ComplexityLevel.MODERATE and budget > 4000:
            patterns.append("anti_004b: budget >4K on moderate task")
        if outcomes.get("roi_multiplier", 0) < 2 and level not in (ComplexityLevel.TRIVIAL, ComplexityLevel.SIMPLE):
            patterns.append("anti_004c: ROI <2x suggests misclassification")
        if budget >= max_budget and level != ComplexityLevel.VERY_COMPLEX:
            patterns.append("anti_004d: hitting max without VERY_COMPLEX")
        return patterns

    def _allocate_workflow(self, steps: List[Dict], ind: ComplexityIndicators) -> List[Dict]:
        """Allocate budgets per workflow step based on step type."""
        results = []
        for step in steps:
            step_type = step.get("type", "problem_solving")
            step_name = step.get("name", step_type)
            base = BASE_BUDGETS.get(step_type, 6000)
            # Scale by overall complexity indicators (simplified)
            score, level = self._calculate_complexity(ind)
            mult = score ** 0.8
            novelty_mult = NOVELTY_MULTIPLIERS.get(ind.novelty, 1.0)
            budget = int(base * mult * novelty_mult)
            budget = max(500, min(10000, budget))
            results.append({
                "step": step_name,
                "type": step_type,
                "budget": budget,
                "complexity_level": level.value,
            })
        return results

    def _compare_strategies(self, recommended: int) -> Dict:
        strategies = {}
        for name, mult in [("minimal", 0.5), ("conservative", 0.75),
                           ("recommended", 1.0), ("aggressive", 1.5)]:
            budget = int(recommended * mult)
            depth = min(1.0, budget / BUDGET_PLATEAU)
            prevented = round(3 * 0.7 * depth)
            time_saved = prevented * 0.75
            cost = 0.045 * (budget / BUDGET_PLATEAU)
            strategies[name] = {
                "budget": budget,
                "revisions_prevented": prevented,
                "time_saved_hours": round(time_saved, 2),
                "cost_usd": round(cost, 4),
                "roi": round(time_saved / cost, 1) if cost > 0 else 0,
            }
        return strategies


# ============================================================================
# L5: CLI
# ============================================================================

if __name__ == "__main__":
    analyzer = ThinkingBudgetAnalyzer()
    run_standard_cli(
        agent_name="Thinking Budget Optimizer",
        description="Allocate optimal thinking budgets per task complexity",
        analyzer=analyzer,
    )

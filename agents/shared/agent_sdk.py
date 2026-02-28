#!/usr/bin/env python3
"""
NLKE Agent SDK Orchestrator

Python SDK for programmatically composing and running agent pipelines.
Supports sequential chains, parallel execution, conditional routing,
and result aggregation across the 33-agent ecosystem.

Usage:
    from agents.shared.agent_sdk import Pipeline, AgentRunner

    pipeline = Pipeline("KG Enhancement")
    pipeline.add("kg-health-monitor", {"db_path": "kg.db"})
    pipeline.add("relationship-suggester", depends_on=["kg-health-monitor"])
    pipeline.add("kg-completer", depends_on=["relationship-suggester"])
    results = pipeline.run()

Created: February 6, 2026
"""

import os
import sys
import json
import importlib
import importlib.util
import time
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path

# Ensure agent imports work
NLKE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(NLKE_ROOT))


# ============================================================================
# Agent Registry - Maps agent names to Python module paths
# ============================================================================

AGENT_MODULES = {
    "cost-advisor": "cost-optimization.cost_advisor",
    "batch-optimizer": "cost-optimization.batch_optimizer_agent",
    "thinking-budget-optimizer": "cost-optimization.thinking_budget_agent",
    "kg-health-monitor": "kg-enhancement.kg_health_monitor",
    "relationship-suggester": "kg-enhancement.relationship_suggester_agent",
    "kg-completer": "kg-enhancement.kg_completer",
    "workflow-orchestrator": "workflow-automation.workflow_orchestrator",
    "generator-agent": "workflow-automation.generator_agent",
    "progressive-assembly": "workflow-automation.progressive_assembly",
    "compound-intelligence": "emergent.compound_intelligence",
    "self-healing-docs": "emergent.self_healing_docs",
    "cost-quality-frontier": "emergent.cost_quality_frontier",
    "multi-model-orchestrator": "multi-model.multi_model_orchestrator",
    "gemini-delegator": "multi-model.gemini_delegator",
    "context-engineer": "multi-model.context_engineer",
    "rule-engine-agent": "rule-engine.rule_engine_agent",
    "anti-pattern-validator": "rule-engine.anti_pattern_validator",
    "playbook-advisor": "rule-engine.playbook_advisor",
    "rag-kg-query": "knowledge-retrieval.rag_kg_query",
    "intent-engine": "knowledge-retrieval.intent_engine_agent",
    "refactoring-agent": "knowledge-retrieval.refactoring_agent",
    "mcp-tool-creator": "mcp-tool-creator.mcp_tool_creator",
    "embedding-engine": "advanced.embedding_engine",
    "citation-analyzer": "advanced.citation_analyzer",
    "gemini-compute": "cross-provider.gemini_compute",
    "web-research": "cross-provider.web_research",
    "visual-report": "reporting.visual_report",
    "agentic-tool-router": "routing.agentic_tool_router",
    # Phase 9: Code Generation Fleet
    "codegen-python": "codegen.codegen_python",
    "codegen-javascript": "codegen.codegen_javascript",
    "codegen-sql": "codegen.codegen_sql",
    "codegen-bash": "codegen.codegen_bash",
    "codegen-html-css": "codegen.codegen_html_css",
    "codegen-gemini": "codegen.codegen_gemini",
    "codegen-orchestrator": "codegen.codegen_orchestrator",
}


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class StepResult:
    agent_name: str
    success: bool
    output: Dict[str, Any]
    duration_ms: float
    error: Optional[str] = None


@dataclass
class PipelineResult:
    name: str
    total_steps: int
    succeeded: int
    failed: int
    total_duration_ms: float
    steps: List[StepResult] = field(default_factory=list)
    aggregated_recommendations: List[Dict] = field(default_factory=list)
    aggregated_rules: List[str] = field(default_factory=list)


# ============================================================================
# Agent Runner
# ============================================================================

class AgentRunner:
    """Run a single NLKE agent by name with given workload."""

    _cache: Dict[str, Any] = {}

    @classmethod
    def load_analyzer(cls, agent_name: str):
        """Dynamically load an agent's analyzer class."""
        if agent_name in cls._cache:
            return cls._cache[agent_name]

        module_path = AGENT_MODULES.get(agent_name)
        if not module_path:
            raise ValueError(f"Unknown agent: {agent_name}. Available: {list(AGENT_MODULES.keys())}")

        # Convert dot-separated path to importable module
        parts = module_path.split(".")
        category = parts[0]
        module_name = parts[1]

        # Import the module
        full_path = NLKE_ROOT / category.replace("-", "-") / f"{module_name}.py"
        if not full_path.exists():
            raise FileNotFoundError(f"Agent module not found: {full_path}")

        spec = importlib.util.spec_from_file_location(module_name, str(full_path))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        # Find the Analyzer class (convention: *Analyzer)
        analyzer = None
        for name in dir(mod):
            obj = getattr(mod, name)
            if isinstance(obj, type) and name.endswith("Analyzer") and name != "BaseAnalyzer":
                analyzer = obj()
                break

        if analyzer is None:
            raise RuntimeError(f"No Analyzer class found in {module_path}")

        cls._cache[agent_name] = analyzer
        return analyzer

    @classmethod
    def run(cls, agent_name: str, workload: Dict[str, Any] = None) -> StepResult:
        """Run an agent with the given workload, returning a StepResult."""
        start = time.time()
        try:
            analyzer = cls.load_analyzer(agent_name)
            if workload is None:
                workload = analyzer.get_example_input()

            from shared.agent_base import AgentInput
            agent_input = AgentInput(workload=workload)
            output = analyzer.analyze(agent_input)

            return StepResult(
                agent_name=agent_name,
                success=True,
                output=asdict(output),
                duration_ms=round((time.time() - start) * 1000, 1),
            )
        except Exception as e:
            return StepResult(
                agent_name=agent_name,
                success=False,
                output={},
                duration_ms=round((time.time() - start) * 1000, 1),
                error=str(e),
            )


# ============================================================================
# Pipeline
# ============================================================================

@dataclass
class PipelineStep:
    agent_name: str
    workload: Optional[Dict[str, Any]] = None
    depends_on: List[str] = field(default_factory=list)
    transform: Optional[Callable] = None  # Transform previous output into workload


class Pipeline:
    """Compose and execute agent pipelines."""

    def __init__(self, name: str):
        self.name = name
        self.steps: List[PipelineStep] = []

    def add(self, agent_name: str, workload: Dict[str, Any] = None,
            depends_on: List[str] = None, transform: Callable = None) -> "Pipeline":
        """Add a step to the pipeline."""
        self.steps.append(PipelineStep(
            agent_name=agent_name,
            workload=workload,
            depends_on=depends_on or [],
            transform=transform,
        ))
        return self

    def run(self) -> PipelineResult:
        """Execute the pipeline sequentially (respecting dependencies)."""
        results: Dict[str, StepResult] = {}
        all_steps: List[StepResult] = []

        start = time.time()

        for step in self.steps:
            # Check dependencies
            for dep in step.depends_on:
                if dep in results and not results[dep].success:
                    sr = StepResult(
                        agent_name=step.agent_name,
                        success=False,
                        output={},
                        duration_ms=0,
                        error=f"Dependency failed: {dep}",
                    )
                    results[step.agent_name] = sr
                    all_steps.append(sr)
                    continue

            # Transform workload from previous step output
            workload = step.workload
            if step.transform and step.depends_on:
                dep_name = step.depends_on[0]
                if dep_name in results and results[dep_name].success:
                    try:
                        workload = step.transform(results[dep_name].output)
                    except Exception as e:
                        sr = StepResult(
                            agent_name=step.agent_name,
                            success=False,
                            output={},
                            duration_ms=0,
                            error=f"Transform failed: {e}",
                        )
                        results[step.agent_name] = sr
                        all_steps.append(sr)
                        continue

            sr = AgentRunner.run(step.agent_name, workload)
            results[step.agent_name] = sr
            all_steps.append(sr)

        # Aggregate results
        all_recs = []
        all_rules = set()
        for sr in all_steps:
            if sr.success:
                for rec in sr.output.get("recommendations", []):
                    all_recs.append(rec)
                for rule in sr.output.get("rules_applied", []):
                    all_rules.add(rule)

        total_ms = round((time.time() - start) * 1000, 1)
        succeeded = sum(1 for s in all_steps if s.success)

        return PipelineResult(
            name=self.name,
            total_steps=len(all_steps),
            succeeded=succeeded,
            failed=len(all_steps) - succeeded,
            total_duration_ms=total_ms,
            steps=all_steps,
            aggregated_recommendations=all_recs,
            aggregated_rules=sorted(all_rules),
        )

    def describe(self) -> str:
        """Print pipeline description."""
        lines = [f"Pipeline: {self.name}", f"Steps: {len(self.steps)}"]
        for i, step in enumerate(self.steps):
            deps = f" (after: {', '.join(step.depends_on)})" if step.depends_on else ""
            lines.append(f"  {i + 1}. {step.agent_name}{deps}")
        return "\n".join(lines)


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    print("NLKE Agent SDK Orchestrator")
    print(f"Available agents: {len(AGENT_MODULES)}")
    print(f"Agent list: {', '.join(sorted(AGENT_MODULES.keys()))}")

    # Demo pipeline
    print("\n--- Demo Pipeline ---")
    p = Pipeline("Cost Analysis Pipeline")
    p.add("cost-advisor")
    p.add("context-engineer", depends_on=["cost-advisor"])
    print(p.describe())
    print("\nRunning pipeline...")
    result = p.run()
    print(json.dumps(asdict(result), indent=2, default=str)[:2000])

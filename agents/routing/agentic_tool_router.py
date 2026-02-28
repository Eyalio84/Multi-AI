#!/usr/bin/env python3
"""
Agentic Tool Router Agent (#33)

Intelligent routing engine that matches tasks to the best NLKE agent
or tool. Analyzes task intent, complexity, and requirements to select
optimal agent(s) from the 33-agent ecosystem.

Layer: L1-L5 (Full 5-layer pattern via agent_base)

Usage:
    python3 agentic_tool_router.py --example
    python3 agentic_tool_router.py --workload task.json --summary

Created: February 6, 2026
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.agent_base import (
    AgentInput, AgentOutput, BaseAnalyzer, run_standard_cli,
)

from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any, Optional


# ============================================================================
# L1: Data Models
# ============================================================================

@dataclass
class RouteDecision:
    task: str
    primary_agent: str
    primary_agent_id: int
    confidence: float
    reasoning: str
    fallback_agents: List[str] = field(default_factory=list)
    estimated_cost_usd: float = 0.01
    model_tier: str = "sonnet"


# ============================================================================
# L2: Constants
# ============================================================================

# Full NLKE agent registry with capabilities
AGENT_REGISTRY = {
    1: {"name": "haiku-doc-updater", "model": "haiku", "capabilities": ["documentation", "synthesis", "updating"], "category": "foundation"},
    2: {"name": "haiku-md-cat", "model": "haiku", "capabilities": ["categorization", "markdown", "taxonomy"], "category": "foundation"},
    3: {"name": "haiku-py-cat", "model": "haiku", "capabilities": ["categorization", "python", "taxonomy"], "category": "foundation"},
    4: {"name": "opus-expender", "model": "opus", "capabilities": ["expansion", "creative", "visionary", "speculative"], "category": "foundation"},
    5: {"name": "sonnet-code-analyzer", "model": "sonnet", "capabilities": ["code_analysis", "capability_discovery", "undocumented"], "category": "foundation"},
    6: {"name": "cost-advisor", "model": "haiku", "capabilities": ["cost_analysis", "optimization", "caching", "batching", "gemini_pricing"], "category": "cost-optimization"},
    7: {"name": "batch-optimizer", "model": "haiku", "capabilities": ["batch_api", "throughput", "latency"], "category": "cost-optimization"},
    8: {"name": "thinking-budget-optimizer", "model": "haiku", "capabilities": ["thinking_budget", "allocation", "quality"], "category": "cost-optimization"},
    9: {"name": "kg-health-monitor", "model": "haiku", "capabilities": ["knowledge_graph", "health", "monitoring", "validation"], "category": "kg-enhancement"},
    10: {"name": "relationship-suggester", "model": "sonnet", "capabilities": ["knowledge_graph", "relationships", "edges", "suggestions"], "category": "kg-enhancement"},
    11: {"name": "kg-completer", "model": "sonnet", "capabilities": ["knowledge_graph", "gaps", "completion", "auto_fill"], "category": "kg-enhancement"},
    12: {"name": "workflow-orchestrator", "model": "sonnet", "capabilities": ["workflow", "planning", "orchestration", "multi_step", "gemini_routing"], "category": "workflow-automation"},
    13: {"name": "generator-agent", "model": "sonnet", "capabilities": ["agent_generation", "factory", "creation"], "category": "workflow-automation"},
    14: {"name": "progressive-assembly", "model": "haiku", "capabilities": ["chunking", "validation", "assembly", "quality"], "category": "workflow-automation"},
    15: {"name": "compound-intelligence", "model": "opus", "capabilities": ["cascade", "multi_tier", "strategic", "orchestration"], "category": "emergent"},
    16: {"name": "self-healing-docs", "model": "haiku", "capabilities": ["documentation", "drift", "repair", "autonomous"], "category": "emergent"},
    17: {"name": "cost-quality-frontier", "model": "sonnet", "capabilities": ["pareto", "optimization", "cost", "quality", "tradeoff"], "category": "emergent"},
    18: {"name": "multi-model-orchestrator", "model": "opus", "capabilities": ["multi_model", "claude", "gemini", "orchestration", "routing"], "category": "multi-model"},
    19: {"name": "gemini-delegator", "model": "sonnet", "capabilities": ["gemini", "delegation", "api", "batch", "retry"], "category": "multi-model"},
    20: {"name": "context-engineer", "model": "haiku", "capabilities": ["context", "tokens", "optimization", "caching", "gemini_context"], "category": "multi-model"},
    21: {"name": "rule-engine-agent", "model": "sonnet", "capabilities": ["rules", "engine", "validation", "synthesis"], "category": "rule-engine"},
    22: {"name": "anti-pattern-validator", "model": "haiku", "capabilities": ["anti_patterns", "validation", "pre_flight"], "category": "rule-engine"},
    23: {"name": "playbook-advisor", "model": "haiku", "capabilities": ["playbooks", "matching", "recommendations"], "category": "rule-engine"},
    24: {"name": "rag-kg-query", "model": "sonnet", "capabilities": ["rag", "knowledge_graph", "query", "retrieval"], "category": "knowledge-retrieval"},
    25: {"name": "intent-engine", "model": "sonnet", "capabilities": ["intent", "natural_language", "framework", "routing"], "category": "knowledge-retrieval"},
    26: {"name": "refactoring-agent", "model": "sonnet", "capabilities": ["refactoring", "code", "analysis", "improvement"], "category": "knowledge-retrieval"},
    27: {"name": "mcp-tool-creator", "model": "sonnet", "capabilities": ["mcp", "tool_creation", "server", "generation"], "category": "mcp-tool-creator"},
    28: {"name": "embedding-engine", "model": "sonnet", "capabilities": ["embeddings", "vectors", "similarity", "search"], "category": "advanced"},
    29: {"name": "citation-analyzer", "model": "haiku", "capabilities": ["citations", "validation", "fabrication", "sources"], "category": "advanced"},
    30: {"name": "gemini-compute", "model": "sonnet", "capabilities": ["computation", "code_execution", "statistics", "analysis"], "category": "cross-provider"},
    31: {"name": "web-research", "model": "sonnet", "capabilities": ["web_search", "research", "grounding", "sources"], "category": "cross-provider"},
    32: {"name": "visual-report", "model": "haiku", "capabilities": ["visualization", "charts", "reports", "matplotlib"], "category": "reporting"},
    33: {"name": "agentic-tool-router", "model": "sonnet", "capabilities": ["routing", "agent_selection", "task_matching"], "category": "routing"},
    # Phase 9: Code Generation Fleet
    34: {"name": "codegen-python", "model": "sonnet", "capabilities": ["codegen", "python", "scripts", "cli", "fastapi", "tests"], "category": "codegen"},
    35: {"name": "codegen-javascript", "model": "sonnet", "capabilities": ["codegen", "javascript", "typescript", "react", "express", "node"], "category": "codegen"},
    36: {"name": "codegen-sql", "model": "haiku", "capabilities": ["codegen", "sql", "sqlite", "postgresql", "schema", "queries"], "category": "codegen"},
    37: {"name": "codegen-bash", "model": "haiku", "capabilities": ["codegen", "bash", "shell", "automation", "deploy", "cicd"], "category": "codegen"},
    38: {"name": "codegen-html-css", "model": "sonnet", "capabilities": ["codegen", "html", "css", "tailwind", "responsive", "landing_page"], "category": "codegen"},
    39: {"name": "codegen-gemini", "model": "sonnet", "capabilities": ["codegen", "gemini", "embeddings", "grounding", "code_execution"], "category": "codegen"},
    40: {"name": "codegen-orchestrator", "model": "opus", "capabilities": ["codegen", "orchestration", "language_detection", "routing"], "category": "codegen"},
}

# Intent keywords mapping to capabilities
INTENT_KEYWORDS = {
    "cost": ["cost_analysis", "optimization", "caching", "batching"],
    "save": ["cost_analysis", "optimization"],
    "price": ["cost_analysis", "gemini_pricing"],
    "knowledge graph": ["knowledge_graph", "health", "relationships"],
    "kg": ["knowledge_graph", "health", "relationships"],
    "relationship": ["relationships", "edges", "suggestions"],
    "complete": ["gaps", "completion", "auto_fill"],
    "workflow": ["workflow", "planning", "orchestration"],
    "plan": ["workflow", "planning", "orchestration"],
    "generate agent": ["agent_generation", "factory"],
    "create agent": ["agent_generation", "factory"],
    "document": ["documentation", "synthesis", "updating"],
    "quality": ["quality", "validation", "pareto"],
    "embed": ["embeddings", "vectors", "similarity"],
    "vector": ["embeddings", "vectors", "similarity"],
    "cite": ["citations", "validation", "sources"],
    "search": ["web_search", "research", "grounding"],
    "research": ["web_search", "research", "grounding"],
    "compute": ["computation", "code_execution", "statistics"],
    "statistics": ["computation", "code_execution", "statistics"],
    "chart": ["visualization", "charts", "reports"],
    "report": ["visualization", "charts", "reports"],
    "visualize": ["visualization", "charts", "reports"],
    "gemini": ["gemini", "delegation", "gemini_routing"],
    "refactor": ["refactoring", "code", "improvement"],
    "mcp": ["mcp", "tool_creation", "server"],
    "rule": ["rules", "engine", "validation"],
    "playbook": ["playbooks", "matching", "recommendations"],
    "context": ["context", "tokens", "optimization"],
    "categorize": ["categorization", "taxonomy"],
    "expand": ["expansion", "creative", "visionary"],
}


# ============================================================================
# L3: Analyzer
# ============================================================================

class AgenticToolRouterAnalyzer(BaseAnalyzer):
    """Intelligent task-to-agent routing engine."""

    def __init__(self):
        super().__init__(
            agent_name="agentic-tool-router",
            model="sonnet",
            version="1.0",
        )

    def get_example_input(self) -> Dict[str, Any]:
        return {
            "name": "Multi-Task Routing Demo",
            "tasks": [
                "Analyze the cost of running 500 API requests per day with caching",
                "Build a knowledge graph from the handbook documentation",
                "Generate a visual report showing agent cost distribution",
                "Search for latest Gemini API documentation updates",
                "Create a new agent for log analysis",
                "Check all knowledge graphs for orphaned nodes",
                "Compute statistical correlation between cost and quality",
            ],
        }

    def _score_agent(self, task_lower: str, agent_id: int, agent_info: Dict) -> float:
        """Score an agent's relevance to a task based on keyword matching."""
        score = 0.0
        capabilities = set(agent_info["capabilities"])

        for keyword, relevant_caps in INTENT_KEYWORDS.items():
            if keyword in task_lower:
                matching = capabilities.intersection(relevant_caps)
                score += len(matching) * 10.0

        # Bonus for exact capability word matches
        for cap in capabilities:
            if cap.replace("_", " ") in task_lower:
                score += 5.0

        return score

    def _route_task(self, task: str) -> RouteDecision:
        """Route a single task to the best agent."""
        task_lower = task.lower()

        # Score all agents
        scores = []
        for agent_id, info in AGENT_REGISTRY.items():
            score = self._score_agent(task_lower, agent_id, info)
            if score > 0:
                scores.append((agent_id, info, score))

        scores.sort(key=lambda x: x[2], reverse=True)

        if not scores:
            # Default to intent-engine for unmatched tasks
            return RouteDecision(
                task=task,
                primary_agent="intent-engine",
                primary_agent_id=25,
                confidence=0.3,
                reasoning="No strong keyword match - routing to intent engine for NL analysis",
                fallback_agents=["compound-intelligence"],
                model_tier="sonnet",
            )

        best = scores[0]
        confidence = min(1.0, best[2] / 30.0)  # Normalize to 0-1

        fallbacks = [s[1]["name"] for s in scores[1:3]]

        # Estimate cost based on model
        model = best[1]["model"]
        cost_map = {"haiku": 0.002, "sonnet": 0.01, "opus": 0.05}

        return RouteDecision(
            task=task,
            primary_agent=best[1]["name"],
            primary_agent_id=best[0],
            confidence=round(confidence, 2),
            reasoning=f"Matched {int(best[2])} capability points in {best[1]['category']}",
            fallback_agents=fallbacks,
            estimated_cost_usd=cost_map.get(model, 0.01),
            model_tier=model,
        )

    def analyze(self, agent_input: AgentInput) -> AgentOutput:
        w = agent_input.workload
        tasks = w.get("tasks", [])

        rules = [
            "route_001_intent_matching",
            "route_002_capability_scoring",
            "route_003_fallback_selection",
            "route_004_cost_estimation",
        ]

        decisions = [self._route_task(task) for task in tasks]

        total_cost = sum(d.estimated_cost_usd for d in decisions)
        avg_confidence = sum(d.confidence for d in decisions) / max(1, len(decisions))

        # Agent utilization
        agent_usage: Dict[str, int] = {}
        for d in decisions:
            agent_usage[d.primary_agent] = agent_usage.get(d.primary_agent, 0) + 1

        # Model tier distribution
        tier_dist: Dict[str, int] = {}
        for d in decisions:
            tier_dist[d.model_tier] = tier_dist.get(d.model_tier, 0) + 1

        anti_patterns = []
        low_conf = [d for d in decisions if d.confidence < 0.5]
        if low_conf:
            anti_patterns.append(
                f"{len(low_conf)} tasks routed with low confidence (<0.5)"
            )

        recommendations = [{
            "technique": "agentic_routing",
            "applicable": True,
            "total_tasks": len(decisions),
            "avg_confidence": round(avg_confidence, 2),
            "total_estimated_cost_usd": round(total_cost, 4),
            "agent_utilization": agent_usage,
            "tier_distribution": tier_dist,
            "routes": [asdict(d) for d in decisions],
            "rules_applied": rules,
        }]

        top_agents = sorted(agent_usage.items(), key=lambda x: x[1], reverse=True)[:3]
        meta_insight = (
            f"Routed {len(decisions)} tasks across {len(agent_usage)} agents. "
            f"Avg confidence: {avg_confidence:.2f}. Est. cost: ${total_cost:.3f}. "
            f"Top agents: {', '.join(f'{a}({c})' for a, c in top_agents)}."
        )

        return AgentOutput(
            recommendations=recommendations,
            rules_applied=rules,
            meta_insight=meta_insight,
            analysis_data={
                "routes": [asdict(d) for d in decisions],
                "agent_utilization": agent_usage,
                "tier_distribution": tier_dist,
                "total_agents_in_registry": len(AGENT_REGISTRY),
            },
            anti_patterns=anti_patterns,
            agent_metadata=self.build_metadata(),
        )


if __name__ == "__main__":
    analyzer = AgenticToolRouterAnalyzer()
    run_standard_cli(
        agent_name="Agentic Tool Router",
        description="Route tasks to the best NLKE agent or tool",
        analyzer=analyzer,
    )

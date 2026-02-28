#!/usr/bin/env python3
"""
Code Generation Orchestrator Agent (#40)

Routes code generation tasks to the appropriate domain-specific
codegen agent. Detects target language/platform from the task
description and delegates to the optimal generator.

Layer: L1-L5 (Full 5-layer pattern via agent_base)

Usage:
    python3 codegen_orchestrator.py --example
    python3 codegen_orchestrator.py --workload spec.json --output result.json

Created: February 6, 2026
"""

import sys
import os
import re

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
class CodegenRoute:
    task: str
    detected_language: str
    target_agent: str
    agent_number: int
    confidence: float
    reasoning: str
    keywords_matched: List[str] = field(default_factory=list)


# ============================================================================
# L2: Constants
# ============================================================================

CODEGEN_AGENTS = {
    "python": {
        "agent": "codegen-python", "number": 34, "model": "sonnet",
        "keywords": ["python", "py", "pip", "pytest", "fastapi", "flask",
                     "django", "pandas", "numpy", "dataclass", "def ",
                     "import ", "asyncio", "pydantic", "agent", "cli tool"],
    },
    "javascript": {
        "agent": "codegen-javascript", "number": 35, "model": "sonnet",
        "keywords": ["javascript", "js", "typescript", "ts", "node", "react",
                     "express", "next.js", "vue", "angular", "npm", "yarn",
                     "component", "jsx", "tsx", "frontend", "webpack", "vite"],
    },
    "sql": {
        "agent": "codegen-sql", "number": 36, "model": "haiku",
        "keywords": ["sql", "sqlite", "postgresql", "postgres", "mysql",
                     "database", "schema", "table", "query", "select",
                     "insert", "migration", "index", "view", "join"],
    },
    "bash": {
        "agent": "codegen-bash", "number": 37, "model": "haiku",
        "keywords": ["bash", "shell", "sh", "automation", "deploy",
                     "ci/cd", "pipeline", "cron", "systemd", "docker",
                     "kubectl", "ansible", "terraform", "makefile"],
    },
    "html_css": {
        "agent": "codegen-html-css", "number": 38, "model": "sonnet",
        "keywords": ["html", "css", "webpage", "website", "landing page",
                     "form", "tailwind", "bootstrap", "responsive", "layout",
                     "card", "dashboard", "table", "ui", "interface", "page"],
    },
    "gemini": {
        "agent": "codegen-gemini", "number": 39, "model": "sonnet",
        "keywords": ["gemini", "gemini api", "embedding", "grounding",
                     "google search", "code execution", "function calling",
                     "multimodal", "generative ai", "genai", "vertex"],
    },
}

ORCHESTRATOR_RULES = [
    "codegen_orch_001_language_detection",
    "codegen_orch_002_keyword_matching",
    "codegen_orch_003_disambiguation",
    "codegen_orch_004_confidence_threshold",
    "codegen_orch_005_multi_language_split",
]


# ============================================================================
# L3: Analyzer
# ============================================================================

class CodegenOrchestratorAnalyzer(BaseAnalyzer):
    """Routes codegen tasks to domain-specific agents."""

    def __init__(self):
        super().__init__(
            agent_name="codegen-orchestrator",
            model="opus",
            version="1.0",
        )

    def get_example_input(self) -> Dict[str, Any]:
        return {
            "tasks": [
                "Write a Python CLI tool that validates JSON files against a schema",
                "Create an Express.js REST API for user authentication with JWT",
                "Design a SQLite schema for a blog with posts, comments, and tags",
                "Write a deployment script that builds Docker images and pushes to registry",
                "Build a responsive landing page for a SaaS product with pricing",
                "Generate a Gemini API integration for semantic search over documents",
                "Create a React TypeScript component for drag-and-drop file upload",
                "Write a Python agent that analyzes code quality",
            ],
        }

    def _detect_language(self, task: str) -> CodegenRoute:
        task_lower = task.lower()
        scores: Dict[str, float] = {}
        matches: Dict[str, List[str]] = {}

        for lang, info in CODEGEN_AGENTS.items():
            score = 0.0
            matched = []
            for kw in info["keywords"]:
                if kw in task_lower:
                    score += len(kw.split()) * 10.0
                    matched.append(kw)
            scores[lang] = score
            matches[lang] = matched

        best_lang = max(scores, key=scores.get) if scores else "python"
        best_score = scores.get(best_lang, 0)

        if best_score == 0:
            return CodegenRoute(
                task=task, detected_language="python",
                target_agent="codegen-python", agent_number=34,
                confidence=0.3, reasoning="No keywords detected, default Python",
            )

        info = CODEGEN_AGENTS[best_lang]
        confidence = min(1.0, best_score / 40.0)

        return CodegenRoute(
            task=task, detected_language=best_lang,
            target_agent=info["agent"], agent_number=info["number"],
            confidence=round(confidence, 2),
            reasoning=f"Matched {len(matches[best_lang])} keywords: {', '.join(matches[best_lang][:5])}",
            keywords_matched=matches[best_lang],
        )

    def analyze(self, agent_input: AgentInput) -> AgentOutput:
        w = agent_input.workload
        tasks = w.get("tasks", [])

        routes = [self._detect_language(t) for t in tasks]

        lang_dist: Dict[str, int] = {}
        agent_dist: Dict[str, int] = {}
        for r in routes:
            lang_dist[r.detected_language] = lang_dist.get(r.detected_language, 0) + 1
            agent_dist[r.target_agent] = agent_dist.get(r.target_agent, 0) + 1

        avg_conf = sum(r.confidence for r in routes) / max(1, len(routes))

        anti_patterns = []
        low = [r for r in routes if r.confidence < 0.4]
        if low:
            anti_patterns.append(f"{len(low)} tasks with low confidence (<0.4)")

        recommendations = [{
            "technique": "codegen_orchestration",
            "impact": f"Routed {len(routes)} tasks across {len(agent_dist)} agents",
            "reasoning": f"Languages: {lang_dist}",
            "routes": [asdict(r) for r in routes],
            "language_distribution": lang_dist,
            "agent_distribution": agent_dist,
        }]

        meta_insight = (
            f"Orchestrated {len(routes)} codegen tasks across {len(agent_dist)} agents. "
            f"Languages: {', '.join(f'{k}({v})' for k, v in sorted(lang_dist.items(), key=lambda x: -x[1]))}. "
            f"Avg confidence: {avg_conf:.2f}."
        )

        return AgentOutput(
            recommendations=recommendations,
            rules_applied=ORCHESTRATOR_RULES[:3 + len(agent_dist)],
            meta_insight=meta_insight,
            analysis_data={
                "total_tasks": len(routes),
                "routes": [asdict(r) for r in routes],
                "language_distribution": lang_dist,
                "agent_distribution": agent_dist,
                "avg_confidence": round(avg_conf, 2),
            },
            anti_patterns=anti_patterns,
            agent_metadata=self.build_metadata(),
        )


if __name__ == "__main__":
    analyzer = CodegenOrchestratorAnalyzer()
    run_standard_cli(
        agent_name="CodeGen Orchestrator",
        description="Route code generation tasks to domain agents",
        analyzer=analyzer,
    )

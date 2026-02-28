#!/usr/bin/env python3
"""
Intent Engine Agent

Natural language intent -> actionable framework generation.
Queries handbooks KG and synthesis rules.

Layer: L1-L5 (Full 5-layer pattern via agent_base)

Usage:
    python3 intent_engine_agent.py --example
    python3 intent_engine_agent.py --workload intent.json --summary

Created: February 6, 2026
"""

import sys
import os
import sqlite3
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.agent_base import (
    AgentInput, AgentOutput, BaseAnalyzer, run_standard_cli,
    KG_DATABASES, SYNTHESIS_RULES_ROOT, SYNTHESIS_RULES_DIR, AILAB_HANDBOOKS,
)
from shared.retrieval import HybridFusion, tokenize_and_filter

sys.path.insert(0, SYNTHESIS_RULES_ROOT)
try:
    from engine.rule_engine import RuleEngine
    ENGINE_AVAILABLE = True
except ImportError:
    ENGINE_AVAILABLE = False

from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any, Optional
from pathlib import Path


# ============================================================================
# L1: Data Models
# ============================================================================

@dataclass
class Framework:
    intent: str
    tools: List[Dict[str, Any]]
    patterns: List[Dict[str, Any]]
    workflow_steps: List[str]
    applicable_rules: List[Dict[str, Any]]
    warnings: List[str]
    estimated_complexity: str
    confidence: float


# ============================================================================
# L2: Constants
# ============================================================================

INTENT_KEYWORDS = {
    "build": ["tool", "pattern", "workflow"],
    "analyze": ["technique", "capability", "optimization"],
    "optimize": ["optimization", "best_practice", "pattern"],
    "create": ["tool", "workflow", "agent_pattern"],
    "fix": ["anti_pattern", "best_practice"],
    "search": ["capability", "tool"],
    "query": ["tool", "capability"],
    "monitor": ["tool", "workflow"],
    "test": ["technique", "best_practice"],
    "deploy": ["workflow", "best_practice"],
}

COMPLEXITY_INDICATORS = {
    "simple": ["simple", "basic", "quick", "small", "single"],
    "moderate": ["moderate", "standard", "typical", "some"],
    "complex": ["complex", "advanced", "multi", "large", "scale", "enterprise", "production"],
}

HANDBOOKS_DB = os.path.join(AILAB_HANDBOOKS, "handbooks-kg.db")


# ============================================================================
# L3: Analyzer
# ============================================================================

class IntentEngineAnalyzer(BaseAnalyzer):
    """Intent-to-framework generation engine with unified retrieval layer."""

    def __init__(self):
        super().__init__(
            agent_name="intent-engine-agent",
            model="sonnet",
            version="2.0",
        )
        self.rule_engine = None
        if ENGINE_AVAILABLE:
            self.rule_engine = RuleEngine(rules_dir=Path(SYNTHESIS_RULES_DIR))
        self.fusion = HybridFusion()
        self._fusion_indexed = False

    def get_example_input(self) -> Dict[str, Any]:
        return {
            "name": "Intent Engine Demo",
            "intent": "I want to build a cost-optimized multi-model pipeline that processes 500 documents using the cheapest model for each step",
            "context": {
                "domain": "document_processing",
                "scale": "500 documents",
                "priority": "cost",
            },
        }

    def _extract_keywords(self, intent: str) -> List[str]:
        """Extract meaningful keywords from intent using unified stopwords."""
        return tokenize_and_filter(intent)

    def _classify_complexity(self, intent: str) -> str:
        """Classify intent complexity."""
        intent_lower = intent.lower()
        for level, indicators in COMPLEXITY_INDICATORS.items():
            if any(ind in intent_lower for ind in indicators):
                return level
        return "moderate"

    def _query_handbooks_kg(self, keywords: List[str], limit: int = 15) -> List[Dict[str, Any]]:
        """Query KGs using hybrid fusion (vector + BM25 + graph)."""
        # Lazy-index the fusion engine
        if not self._fusion_indexed:
            self.fusion.index()
            self._fusion_indexed = True

        # Use the intent text for fusion query (better than individual keywords)
        query = " ".join(keywords[:8])
        fusion_results = self.fusion.query(query, k=limit)

        results = []
        for r in fusion_results:
            results.append({
                "id": r.node_id,
                "type": r.node_type,
                "name": r.name,
                "description": r.description[:200],
                "source": r.source_db,
                "fusion_score": r.final_score,
            })

        return results

    def _get_applicable_rules(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """Find applicable synthesis rules."""
        if not self.rule_engine:
            return []
        if not self.rule_engine.loaded:
            self.rule_engine.load_rules()
        query = " ".join(keywords[:5])
        found = self.rule_engine.find_rules(query, min_confidence=0.5)
        return [{
            "rule_id": r.get("rule_id", ""),
            "title": r.get("title", ""),
            "category": r.get("rule_category", ""),
            "confidence": r.get("metadata", {}).get("confidence", 0),
        } for r in found[:10]]

    def _build_workflow(self, intent_type: str, complexity: str, kg_nodes: List[Dict]) -> List[str]:
        """Build workflow steps from intent analysis."""
        # Determine intent action
        action_words = {"build", "create", "make", "develop"}
        analyze_words = {"analyze", "check", "audit", "review", "inspect"}
        optimize_words = {"optimize", "improve", "reduce", "speed", "cost"}

        intent_lower = intent_type.lower()

        if any(w in intent_lower for w in optimize_words):
            return [
                "1. Analyze current state and baseline metrics",
                "2. Identify optimization opportunities",
                "3. Apply relevant synthesis rules",
                "4. Implement optimizations (prioritized by ROI)",
                "5. Validate improvements against baseline",
                "6. Generate optimization report",
            ]
        elif any(w in intent_lower for w in analyze_words):
            return [
                "1. Gather target data/code/system",
                "2. Run analysis tools",
                "3. Cross-reference with KG patterns",
                "4. Apply synthesis rules validation",
                "5. Generate findings report",
            ]
        else:  # build/create
            steps = [
                "1. Define requirements from intent",
                "2. Query KG for matching patterns and tools",
                "3. Select optimal model tier per step",
            ]
            if complexity == "complex":
                steps.extend([
                    "4. Design multi-phase architecture",
                    "5. Implement with progressive assembly",
                    "6. Validate each phase (evaluator-optimizer loop)",
                    "7. Integrate and test end-to-end",
                ])
            else:
                steps.extend([
                    "4. Implement using matched patterns",
                    "5. Validate output",
                ])
            return steps

    def analyze(self, agent_input: AgentInput) -> AgentOutput:
        w = agent_input.workload
        intent = w.get("intent", "")
        context = w.get("context", {})

        rules_applied = [
            "intent_001_keyword_extraction",
            "intent_002_kg_query",
            "intent_003_rule_matching",
            "intent_004_framework_assembly",
        ]

        keywords = self._extract_keywords(intent)
        complexity = self._classify_complexity(intent)

        # Query KG
        kg_nodes = self._query_handbooks_kg(keywords)
        tools = [n for n in kg_nodes if n.get("type") in ("tool", "capability")]
        patterns = [n for n in kg_nodes if n.get("type") in ("pattern", "technique", "agent_pattern")]

        # Get rules
        applicable_rules = self._get_applicable_rules(keywords)

        # Build workflow
        workflow = self._build_workflow(intent, complexity, kg_nodes)

        # Warnings
        warnings = []
        if complexity == "complex" and not patterns:
            warnings.append("Complex intent but no matching patterns found - may need manual design")
        if not tools:
            warnings.append("No matching tools found - check KG coverage")

        # Confidence
        confidence = min(1.0, (len(kg_nodes) * 0.1 + len(applicable_rules) * 0.05 + 0.3))

        framework = Framework(
            intent=intent,
            tools=tools,
            patterns=patterns,
            workflow_steps=workflow,
            applicable_rules=applicable_rules,
            warnings=warnings,
            estimated_complexity=complexity,
            confidence=round(confidence, 2),
        )

        recommendations = [{
            "technique": "intent_to_framework",
            "applicable": True,
            "framework": asdict(framework),
            "rules_applied": rules_applied,
        }]

        meta_insight = (
            f"Intent parsed ({complexity}): found {len(tools)} tools, "
            f"{len(patterns)} patterns, {len(applicable_rules)} rules. "
            f"{len(workflow)} workflow steps. Confidence: {confidence:.0%}."
        )

        return AgentOutput(
            recommendations=recommendations,
            rules_applied=rules_applied,
            meta_insight=meta_insight,
            analysis_data=asdict(framework),
            anti_patterns=warnings,
            agent_metadata=self.build_metadata(),
        )


if __name__ == "__main__":
    analyzer = IntentEngineAnalyzer()
    run_standard_cli(
        agent_name="Intent Engine",
        description="Natural language intent to actionable framework generation",
        analyzer=analyzer,
    )

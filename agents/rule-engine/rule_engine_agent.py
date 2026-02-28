#!/usr/bin/env python3
"""
Rule Engine Agent

Deep integration with the 647-rule synthesis rules engine.
Load, query, validate, and search rules across 30 playbooks.

Layer: L1-L5 (Full 5-layer pattern via agent_base)

Usage:
    python3 rule_engine_agent.py --example
    python3 rule_engine_agent.py --workload query.json --summary

Created: February 6, 2026
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.agent_base import (
    AgentInput, AgentOutput, BaseAnalyzer, run_standard_cli,
    SYNTHESIS_RULES_ROOT, SYNTHESIS_ENGINE_DIR, SYNTHESIS_RULES_DIR,
)

# Deep integration with synthesis rules engine
sys.path.insert(0, SYNTHESIS_RULES_ROOT)
try:
    from engine.rule_engine import RuleEngine, ValidationResult, RuleCategory
    ENGINE_AVAILABLE = True
except ImportError:
    ENGINE_AVAILABLE = False

from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any, Optional
from pathlib import Path
import json


# ============================================================================
# L1: Data Models
# ============================================================================

@dataclass
class RuleMatch:
    rule_id: str
    title: str
    category: str
    confidence: float
    description: str
    tags: List[str]


# ============================================================================
# L2: Constants
# ============================================================================

CATEGORY_DESCRIPTIONS = {
    "composition": "Architecture, caching, orchestration patterns",
    "constraint": "Iteration limits, TTL cascades, budgets",
    "anti-pattern": "Failure mode taxonomy",
    "anti_pattern": "Failure mode taxonomy",
    "dependency": "Cross-layer requirements",
    "compatibility": "Integration requirements",
    "interface": "Human-AI collaboration patterns",
}


# ============================================================================
# L3: Analyzer
# ============================================================================

class RuleEngineAgentAnalyzer(BaseAnalyzer):
    """Synthesis rules engine integration."""

    def __init__(self):
        super().__init__(
            agent_name="rule-engine-agent",
            model="sonnet",
            version="1.0",
        )
        self.engine = None
        if ENGINE_AVAILABLE:
            rules_path = Path(SYNTHESIS_RULES_DIR)
            self.engine = RuleEngine(rules_dir=rules_path)

    def _ensure_loaded(self):
        """Lazy-load rules on first use."""
        if self.engine and not self.engine.loaded:
            self.engine.load_rules()

    def get_example_input(self) -> Dict[str, Any]:
        return {
            "name": "Rule Engine Demo",
            "mode": "all",  # validate, search, stats, all
            "validate": {
                "features": ["batch_api", "prompt_caching"],
                "context": {"async_capable": True, "repeated_content": True},
            },
            "search": {
                "query": "caching optimization",
                "category": None,
                "min_confidence": 0.7,
                "limit": 10,
            },
        }

    def analyze(self, agent_input: AgentInput) -> AgentOutput:
        w = agent_input.workload
        mode = w.get("mode", "all")

        rules_applied = [
            "engine_001_rule_loading",
            "engine_002_validation",
            "engine_003_search",
            "engine_004_statistics",
        ]

        if not ENGINE_AVAILABLE:
            return AgentOutput(
                recommendations=[{"technique": "rule_engine", "applicable": False,
                                  "error": "Rule engine not available. Check path."}],
                rules_applied=rules_applied,
                meta_insight="Rule engine import failed. Verify synthesis-rules path.",
                anti_patterns=["Engine not loaded"],
                agent_metadata=self.build_metadata(),
            )

        self._ensure_loaded()

        results = {}
        all_matches = []

        # Validation mode
        if mode in ("validate", "all") and "validate" in w:
            v = w["validate"]
            features = v.get("features", [])
            context = v.get("context", {})

            vr = self.engine.validate_combination(features, context)
            results["validation"] = {
                "valid": vr.valid,
                "confidence": vr.confidence,
                "matched_rules": len(vr.matched_rules),
                "constraints": vr.constraints,
                "warnings": vr.warnings,
                "recommendations": vr.recommendations,
                "errors": vr.errors,
                "cost_impact": vr.cost_impact,
                "rule_details": vr.matched_rules[:10],
            }
            for mr in vr.matched_rules:
                all_matches.append(RuleMatch(
                    rule_id=mr.get("rule_id", "unknown"),
                    title=mr.get("title", ""),
                    category=mr.get("rule_category", ""),
                    confidence=mr.get("metadata", {}).get("confidence", 0),
                    description=mr.get("description", ""),
                    tags=mr.get("metadata", {}).get("tags", []),
                ))

        # Search mode
        if mode in ("search", "all") and "search" in w:
            s = w["search"]
            query = s.get("query", "")
            category = s.get("category")
            min_conf = s.get("min_confidence", 0.0)
            limit = s.get("limit", 10)

            found = self.engine.find_rules(query, category=category, min_confidence=min_conf)
            results["search"] = {
                "query": query,
                "total_found": len(found),
                "results": [{
                    "rule_id": r.get("rule_id", ""),
                    "title": r.get("title", ""),
                    "category": r.get("rule_category", ""),
                    "confidence": r.get("metadata", {}).get("confidence", 0),
                    "description": r.get("description", "")[:200],
                } for r in found[:limit]],
            }

        # Statistics mode
        if mode in ("stats", "all"):
            stats = self.engine.get_statistics()
            results["statistics"] = stats

        # Build output
        recommendations = [{
            "technique": "rule_engine_query",
            "applicable": True,
            "engine_loaded": True,
            "total_rules": len(self.engine.rules) if self.engine else 0,
            "results": results,
            "rules_applied": rules_applied,
        }]

        anti_patterns = []
        if "validation" in results and not results["validation"]["valid"]:
            anti_patterns.append(f"Validation FAILED: {results['validation'].get('errors', [])}")
        if "validation" in results:
            anti_patterns.extend(results["validation"].get("warnings", []))

        total_rules = len(self.engine.rules) if self.engine else 0
        search_count = results.get("search", {}).get("total_found", 0)
        valid_str = ""
        if "validation" in results:
            v = results["validation"]
            valid_str = f" Validation: {'PASS' if v['valid'] else 'FAIL'} (confidence {v['confidence']:.2f})."

        meta_insight = (
            f"Rule engine loaded {total_rules} rules.{valid_str}"
            + (f" Search found {search_count} matching rules." if search_count else "")
        )

        return AgentOutput(
            recommendations=recommendations,
            rules_applied=rules_applied,
            meta_insight=meta_insight,
            analysis_data=results,
            anti_patterns=anti_patterns,
            agent_metadata=self.build_metadata(),
        )


if __name__ == "__main__":
    analyzer = RuleEngineAgentAnalyzer()
    run_standard_cli(
        agent_name="Rule Engine Agent",
        description="Deep integration with 647-rule synthesis rules engine",
        analyzer=analyzer,
    )

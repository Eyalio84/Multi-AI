#!/usr/bin/env python3
"""
Anti-Pattern Validator Agent

Pre-flight checker that scans configurations against 97 known
anti-patterns from the synthesis rules engine.

Layer: L1-L5 (Full 5-layer pattern via agent_base)

Usage:
    python3 anti_pattern_validator.py --example
    python3 anti_pattern_validator.py --workload config.json --summary

Created: February 6, 2026
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.agent_base import (
    AgentInput, AgentOutput, BaseAnalyzer, run_standard_cli,
    SYNTHESIS_RULES_ROOT, SYNTHESIS_RULES_DIR,
)

sys.path.insert(0, SYNTHESIS_RULES_ROOT)
try:
    from engine.rule_engine import RuleEngine, RuleCategory
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
class Violation:
    rule_id: str
    title: str
    severity: str  # critical, high, medium, low
    description: str
    why_it_fails: str
    correct_approach: str
    recovery_steps: List[str]
    matched_features: List[str]


# ============================================================================
# L2: Constants
# ============================================================================

# Common feature patterns to check for
FEATURE_PATTERNS = {
    "batch_api": ["batch", "batch_api", "async_batch"],
    "prompt_caching": ["cache", "caching", "prompt_cache"],
    "extended_thinking": ["thinking", "extended_thinking", "thinking_budget"],
    "real_time": ["realtime", "real_time", "latency_sensitive", "streaming"],
    "tool_loops": ["loop", "iteration", "recursive", "retry"],
    "error_handling": ["error", "exception", "fallback", "retry"],
    "session_management": ["session", "state", "context_window"],
    "multi_model": ["multi_model", "cascade", "delegation"],
}

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


# ============================================================================
# L3: Analyzer
# ============================================================================

class AntiPatternValidatorAnalyzer(BaseAnalyzer):
    """Anti-pattern pre-flight validation engine."""

    def __init__(self):
        super().__init__(
            agent_name="anti-pattern-validator",
            model="haiku",
            version="1.0",
        )
        self.engine = None
        self.anti_patterns = []
        if ENGINE_AVAILABLE:
            self.engine = RuleEngine(rules_dir=Path(SYNTHESIS_RULES_DIR))

    def _load_anti_patterns(self):
        """Load all anti-pattern rules."""
        if not self.engine:
            return
        if not self.engine.loaded:
            self.engine.load_rules()
        cat_key = None
        for k in self.engine.rules_by_category:
            if "anti" in str(k).lower():
                cat_key = k
                break
        if cat_key:
            self.anti_patterns = self.engine.rules_by_category[cat_key]

    def get_example_input(self) -> Dict[str, Any]:
        return {
            "name": "Workflow Pre-flight Check",
            "features": [
                "batch_api", "real_time", "prompt_caching",
                "extended_thinking", "tool_loops",
            ],
            "context": {
                "async_capable": False,
                "latency_sensitive": True,
                "max_iterations": None,
                "error_handling": "none",
            },
            "workflow_description": "Real-time chat with batch processing and unlimited retries",
        }

    def analyze(self, agent_input: AgentInput) -> AgentOutput:
        w = agent_input.workload
        features = w.get("features", [])
        context = w.get("context", {})
        description = w.get("workflow_description", "")

        rules_applied = [
            "validate_001_anti_pattern_scan",
            "validate_002_severity_classification",
            "validate_003_recovery_strategy",
        ]

        self._load_anti_patterns()

        violations = []

        # Rule engine validation
        if self.engine:
            result = self.engine.validate_combination(features, context)
            if not result.valid:
                for mr in result.matched_rules:
                    meta = mr.get("metadata", {})
                    recovery = mr.get("recovery_strategy", {})
                    violations.append(Violation(
                        rule_id=mr.get("rule_id", "unknown"),
                        title=mr.get("title", "Unknown anti-pattern"),
                        severity=meta.get("severity", "medium"),
                        description=mr.get("description", ""),
                        why_it_fails=meta.get("why_it_fails", "See rule description"),
                        correct_approach=meta.get("correct_approach", "See rule documentation"),
                        recovery_steps=recovery.get("if_already_implemented", []),
                        matched_features=mr.get("predicate", {}).get("inputs", []),
                    ))

        # Heuristic checks (supplement rule engine)
        if "batch_api" in features and ("real_time" in features or context.get("latency_sensitive")):
            if not any(v.rule_id.startswith("anti_001") for v in violations):
                violations.append(Violation(
                    rule_id="heuristic_001_batch_realtime",
                    title="Batch API with real-time requirement",
                    severity="critical",
                    description="Batch API adds 1-24h latency, incompatible with real-time",
                    why_it_fails="Batch API is asynchronous by design",
                    correct_approach="Use synchronous API for real-time, batch for async only",
                    recovery_steps=["Remove batch_api from real-time path", "Add async/sync routing"],
                    matched_features=["batch_api", "real_time"],
                ))

        if "tool_loops" in features and not context.get("max_iterations"):
            if not any("loop" in v.rule_id or "iteration" in v.rule_id for v in violations):
                violations.append(Violation(
                    rule_id="heuristic_002_unbounded_loops",
                    title="Tool loops without max_iterations",
                    severity="critical",
                    description="Unbounded loops can run forever, consuming unlimited tokens",
                    why_it_fails="No termination condition leads to runaway costs",
                    correct_approach="Always set max_iterations (recommended: 3-10)",
                    recovery_steps=["Add max_iterations parameter", "Add cost circuit breaker"],
                    matched_features=["tool_loops"],
                ))

        if context.get("error_handling") in ("none", None, ""):
            violations.append(Violation(
                rule_id="heuristic_003_no_error_handling",
                title="No error handling strategy",
                severity="high",
                description="Tools without error handling fail silently",
                why_it_fails="Silent failures cascade and corrupt downstream results",
                correct_approach="Implement retry, fallback, or abort strategy",
                recovery_steps=["Add try/except blocks", "Define fallback behavior", "Add logging"],
                matched_features=["error_handling"],
            ))

        if "extended_thinking" in features and not context.get("thinking_budget"):
            violations.append(Violation(
                rule_id="heuristic_004_unconstrained_thinking",
                title="Extended thinking without budget",
                severity="high",
                description="Unconstrained thinking can consume excessive tokens (plateau at 8K)",
                why_it_fails="Diminishing returns above 8,000 thinking tokens",
                correct_approach="Set explicit thinking budget based on complexity",
                recovery_steps=["Set thinking_budget to 8000 max", "Use Thinking Budget Optimizer agent"],
                matched_features=["extended_thinking"],
            ))

        # Sort by severity
        violations.sort(key=lambda v: SEVERITY_ORDER.get(v.severity, 3))

        # Build output
        by_severity = {}
        for v in violations:
            by_severity.setdefault(v.severity, []).append(v)

        recommendations = [{
            "technique": "anti_pattern_validation",
            "applicable": True,
            "total_violations": len(violations),
            "by_severity": {k: len(v) for k, v in by_severity.items()},
            "violations": [asdict(v) for v in violations],
            "engine_rules_loaded": len(self.anti_patterns),
            "pass": len(violations) == 0,
            "rules_applied": rules_applied,
        }]

        anti_patterns_out = [
            f"{v.severity.upper()}: [{v.rule_id}] {v.title}"
            for v in violations if v.severity in ("critical", "high")
        ]

        critical = len(by_severity.get("critical", []))
        high = len(by_severity.get("high", []))

        if violations:
            meta_insight = (
                f"Pre-flight FAILED: {len(violations)} violations "
                f"({critical} critical, {high} high). "
                f"Top: {violations[0].title}."
            )
        else:
            meta_insight = "Pre-flight PASSED: No anti-patterns detected."

        return AgentOutput(
            recommendations=recommendations,
            rules_applied=rules_applied,
            meta_insight=meta_insight,
            analysis_data={
                "violations": [asdict(v) for v in violations],
                "by_severity": {k: len(v) for k, v in by_severity.items()},
                "features_checked": features,
                "pass": len(violations) == 0,
            },
            anti_patterns=anti_patterns_out,
            agent_metadata=self.build_metadata(),
        )


if __name__ == "__main__":
    analyzer = AntiPatternValidatorAnalyzer()
    run_standard_cli(
        agent_name="Anti-Pattern Validator",
        description="Pre-flight scan against 97 known anti-patterns",
        analyzer=analyzer,
    )

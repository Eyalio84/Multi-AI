#!/usr/bin/env python3
"""
NLKE Agent Base Module - AI-LAB 5-Layer Pattern

Shared base for all NLKE agents implementing the standardized 5-layer architecture:
  L1: Data Models (AgentInput, AgentOutput dataclasses)
  L2: Constants (paths, pricing, thresholds)
  L3: BaseAnalyzer (abstract analysis class)
  L4: AgentOrchestrator (composition and pipeline)
  L5: CLI Helper (create_standard_cli)

Every NLKE agent inherits from this module to ensure consistent structure,
output format, and interoperability.

Created: February 6, 2026
"""

import json
import argparse
import sys
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime


# ============================================================================
# L1: Data Models
# ============================================================================

@dataclass
class AgentInput:
    """Standardized input for all NLKE agents."""
    workload: Dict[str, Any]
    options: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "AgentInput":
        return cls(
            workload=data.get("workload", data),
            options=data.get("options", {}),
            context=data.get("context", {}),
        )

    @classmethod
    def from_file(cls, path: str) -> "AgentInput":
        with open(path, "r") as f:
            return cls.from_json(json.load(f))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AgentOutput:
    """Standardized output for all NLKE agents.

    Every agent MUST produce:
    - recommendations: actionable items
    - rules_applied: which synthesis rules were used
    - meta_insight: emergent observation from the analysis
    """
    recommendations: List[Dict[str, Any]]
    rules_applied: List[str]
    meta_insight: str
    analysis_data: Dict[str, Any] = field(default_factory=dict)
    anti_patterns: List[str] = field(default_factory=list)
    agent_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)

    def format_summary(self) -> str:
        """Human-readable summary."""
        lines = []
        lines.append("=" * 70)
        lines.append(f"AGENT: {self.agent_metadata.get('agent_name', 'Unknown')}")
        lines.append(f"MODEL: {self.agent_metadata.get('model', 'Unknown')}")
        lines.append("=" * 70)

        lines.append(f"\nMETA-INSIGHT: {self.meta_insight}")

        lines.append(f"\nRECOMMENDATIONS ({len(self.recommendations)}):")
        for i, rec in enumerate(self.recommendations, 1):
            technique = rec.get("technique", rec.get("action", "—"))
            savings = rec.get("estimated_savings", rec.get("impact", "—"))
            lines.append(f"  {i}. {technique}: {savings}")

        if self.anti_patterns:
            lines.append(f"\nANTI-PATTERNS ({len(self.anti_patterns)}):")
            for ap in self.anti_patterns:
                lines.append(f"  - {ap}")

        lines.append(f"\nRULES APPLIED ({len(self.rules_applied)}):")
        for rule in self.rules_applied:
            lines.append(f"  - {rule}")

        lines.append("=" * 70)
        return "\n".join(lines)

    def save(self, path: str) -> None:
        """Save output to JSON file."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)


# ============================================================================
# L2: Constants
# ============================================================================

NLKE_ROOT = "/storage/self/primary/Download/44nlke/NLKE"
AGENTS_DIR = os.path.join(NLKE_ROOT, "agents")
CONTEXT_PACKETS_DIR = os.path.join(NLKE_ROOT, "context-packets")

AILAB_ROOT = "/storage/emulated/0/Download/gemini-3-pro/AI-LAB"
AILAB_TOOLS = os.path.join(AILAB_ROOT, "tech-analysis", "tools")
AILAB_HANDBOOKS = os.path.join(AILAB_ROOT, "tech-analysis", "handbooks")

# Synthesis Rules ecosystem
SYNTHESIS_RULES_ROOT = "/storage/emulated/0/Download/synthesis-rules"
SYNTHESIS_ENGINE_DIR = os.path.join(SYNTHESIS_RULES_ROOT, "engine")
SYNTHESIS_RULES_DIR = os.path.join(SYNTHESIS_RULES_ROOT, "rules")
SYNTHESIS_PLAYBOOKS_DIR = os.path.join(SYNTHESIS_RULES_ROOT, "playbooks")
SYNTHESIS_CONSOLIDATED = os.path.join(SYNTHESIS_RULES_DIR, "consolidated", "consolidated_rules.json")

# Custom playbooks (v2)
CUSTOM_PLAYBOOKS_DIR = "/storage/emulated/0/Download/gemini-3-pro/playbooks/playbooks-v2"

# Gemini API
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
GEMINI_MODELS = {
    "gemini-2.5-flash-lite": {"input": 0.10, "output": 0.40, "context": 1048576, "tier": "ultra-fast"},
    "gemini-2.5-flash": {"input": 0.15, "output": 0.60, "context": 1048576, "tier": "fast"},
    "gemini-2.5-pro": {"input": 1.25, "output": 5.00, "context": 1048576, "tier": "balanced"},
    "gemini-3-flash": {"input": 0.50, "output": 3.00, "context": 200000, "tier": "fast"},
    "gemini-3-pro": {"input": 2.00, "output": 12.00, "context": 1048576, "tier": "premium"},
    "gemini-embedding-001": {"input": 0.15, "output": 0, "context": 8192, "tier": "embedding"},
}

# Gemini API capabilities (Phase 7 Arsenal Expansion)
GEMINI_CAPABILITIES = {
    "function_calling": True,
    "code_execution": True,
    "google_search_grounding": True,
    "url_context": True,
    "context_caching": True,
    "structured_output": True,
    "thinking_mode": True,
    "embeddings": True,
    "batch_api": True,
    "file_api": True,
}

# Claude API capabilities (Phase 7 Arsenal Expansion)
CLAUDE_CAPABILITIES = {
    "max_output_tokens": 128000,
    "max_context_window": 1000000,
    "cache_ttl_default_hours": 1,
    "structured_output": True,
    "citations": True,
    "embeddings_model": "voyage-3",
    "web_search_tool": True,
    "files_api": True,
    "context_compaction": True,
}

# Claude API Pricing (per 1M tokens) - February 2026
PRICING = {
    "haiku_input": 0.80,
    "haiku_output": 4.00,
    "sonnet_input": 3.00,
    "sonnet_output": 15.00,
    "opus_input": 15.00,
    "opus_output": 75.00,
    "cache_read": 0.30,
    "cache_write": 3.75,
    "batch_discount": 0.50,
}

TOKENS_PER_MILLION = 1_000_000

# KG database paths
KG_DATABASES = {
    "claude_cookbook": os.path.join(NLKE_ROOT, "claude-cookbook-kg", "claude-cookbook-kg.db"),
    "handbooks": os.path.join(NLKE_ROOT, "handbooks", "handbooks-kg.db"),
    "handbooks_intent": os.path.join(AILAB_HANDBOOKS, "handbooks-kg.db"),
    "synthesis_rules": os.path.join(SYNTHESIS_RULES_ROOT, "claude-cookbook-kg.db"),
}

# Standard thresholds
THRESHOLDS = {
    "min_cached_tokens_for_caching": 1000,
    "min_requests_for_caching": 2,
    "min_requests_for_batch": 10,
    "batch_volume_threshold": 100,
    "cache_lifetime_minutes": 5,
    "thinking_budget_plateau": 8000,
}


# ============================================================================
# L3: BaseAnalyzer (Abstract)
# ============================================================================

class BaseAnalyzer(ABC):
    """Abstract base for all NLKE agent analyzers.

    Subclasses MUST implement:
    - analyze(input) -> AgentOutput
    - get_example_input() -> dict (for --example mode)
    """

    def __init__(self, agent_name: str, model: str, version: str = "1.0"):
        self.agent_name = agent_name
        self.model = model
        self.version = version
        self.created = datetime.now().isoformat()

    @abstractmethod
    def analyze(self, agent_input: AgentInput) -> AgentOutput:
        """Run the main analysis. Must return AgentOutput."""
        pass

    @abstractmethod
    def get_example_input(self) -> Dict[str, Any]:
        """Return an example workload for --example mode."""
        pass

    def build_metadata(self) -> Dict[str, Any]:
        """Build standard agent metadata."""
        return {
            "agent_name": self.agent_name,
            "model": self.model,
            "version": self.version,
            "timestamp": datetime.now().isoformat(),
        }


# ============================================================================
# L4: AgentOrchestrator
# ============================================================================

class AgentOrchestrator:
    """Composes multiple analyzers into a pipeline.

    Usage:
        orchestrator = AgentOrchestrator("my-pipeline", "sonnet")
        orchestrator.add_stage("cost", CostAnalyzer())
        orchestrator.add_stage("batch", BatchAnalyzer())
        result = orchestrator.run(input_data)
    """

    def __init__(self, name: str, model: str):
        self.name = name
        self.model = model
        self.stages: List[tuple] = []  # (name, analyzer)

    def add_stage(self, name: str, analyzer: BaseAnalyzer) -> None:
        self.stages.append((name, analyzer))

    def run(self, agent_input: AgentInput) -> AgentOutput:
        """Run all stages and merge results."""
        all_recommendations = []
        all_rules = []
        all_anti_patterns = []
        all_analysis = {}
        meta_insights = []

        for stage_name, analyzer in self.stages:
            output = analyzer.analyze(agent_input)
            all_recommendations.extend(output.recommendations)
            all_rules.extend(output.rules_applied)
            all_anti_patterns.extend(output.anti_patterns)
            all_analysis[stage_name] = output.analysis_data
            if output.meta_insight:
                meta_insights.append(f"[{stage_name}] {output.meta_insight}")

        combined_insight = " | ".join(meta_insights) if meta_insights else "No insights generated"

        return AgentOutput(
            recommendations=all_recommendations,
            rules_applied=list(dict.fromkeys(all_rules)),  # dedupe preserving order
            meta_insight=combined_insight,
            analysis_data=all_analysis,
            anti_patterns=list(dict.fromkeys(all_anti_patterns)),
            agent_metadata={
                "agent_name": self.name,
                "model": self.model,
                "stages": [name for name, _ in self.stages],
                "timestamp": datetime.now().isoformat(),
            },
        )


# ============================================================================
# L5: CLI Helper
# ============================================================================

def create_standard_cli(
    agent_name: str,
    description: str,
    analyzer_class: type,
    **analyzer_kwargs,
) -> argparse.Namespace:
    """Create a standard CLI for any NLKE agent.

    Provides:
    - --workload <file.json>   Load workload from JSON file
    - --example                Run with built-in example
    - --output <file.json>     Save output to file
    - --summary                Print human-readable summary
    - --json                   Print JSON output (default)

    Returns:
        Parsed args namespace. Caller should use run_standard_cli() instead
        for the full pipeline.
    """
    parser = argparse.ArgumentParser(
        description=f"{agent_name} - {description}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--workload", type=str,
        help="Path to workload JSON file",
    )
    parser.add_argument(
        "--example", action="store_true",
        help="Run with built-in example workload",
    )
    parser.add_argument(
        "--output", type=str,
        help="Save output to JSON file",
    )
    parser.add_argument(
        "--summary", action="store_true",
        help="Print human-readable summary",
    )
    parser.add_argument(
        "--json", action="store_true", default=True,
        help="Print JSON output (default)",
    )

    return parser.parse_args()


def run_standard_cli(
    agent_name: str,
    description: str,
    analyzer: BaseAnalyzer,
) -> None:
    """Full CLI pipeline: parse args -> load input -> analyze -> output.

    This is the standard main() for any NLKE agent tool.
    """
    parser = argparse.ArgumentParser(
        description=f"{agent_name} - {description}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--workload", type=str, help="Path to workload JSON file")
    parser.add_argument("--example", action="store_true", help="Run with built-in example")
    parser.add_argument("--output", type=str, help="Save output to JSON file")
    parser.add_argument("--summary", action="store_true", help="Print human-readable summary")

    args = parser.parse_args()

    # Load input
    if args.example:
        workload = analyzer.get_example_input()
        print(f"Running {agent_name} with example workload...\n")
    elif args.workload:
        agent_input_data = AgentInput.from_file(args.workload)
        workload = agent_input_data.workload
    elif not sys.stdin.isatty():
        workload = json.load(sys.stdin)
    else:
        print(f"Usage: python3 {sys.argv[0]} --example")
        print(f"       python3 {sys.argv[0]} --workload <file.json>")
        print(f"       cat input.json | python3 {sys.argv[0]}")
        sys.exit(1)

    # Run analysis
    agent_input = AgentInput(workload=workload)
    result = analyzer.analyze(agent_input)

    # Output
    if args.output:
        result.save(args.output)
        print(f"Output saved to {args.output}")

    if args.summary:
        print(result.format_summary())
    else:
        print(result.to_json())

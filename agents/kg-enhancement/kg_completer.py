#!/usr/bin/env python3
"""
KG Completer Agent

Detects extraction gaps between source material and knowledge graphs,
then auto-generates node/edge JSON to fill the most impactful gaps.

Wraps: NLKE completeness-checker.py + node-candidate-detector.py
Layer: L1-L5 (Full 5-layer pattern via agent_base)

Usage:
    python3 kg_completer.py --example
    python3 kg_completer.py --workload config.json
    python3 kg_completer.py --workload config.json --summary

Created: February 6, 2026
"""

import sys
import os
import re
import sqlite3

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.agent_base import (
    AgentInput, AgentOutput, BaseAnalyzer, run_standard_cli,
    NLKE_ROOT, KG_DATABASES,
)

from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any, Optional, Set, Tuple
from pathlib import Path


# ============================================================================
# L1: Data Models
# ============================================================================

@dataclass
class GapCandidate:
    text: str
    line_number: int
    section: str
    pattern_type: str
    confidence: float
    suggested_type: str
    reasoning: str
    priority: str  # critical, high, medium, low


@dataclass
class GeneratedNode:
    id: str
    name: str
    type: str
    description: str
    source_line: int
    confidence: float


@dataclass
class GeneratedEdge:
    from_node: str
    to_node: str
    type: str
    weight: float
    description: str


# ============================================================================
# L2: Constants
# ============================================================================

DETECTION_PATTERNS = {
    "enables_action": {
        "keywords": ["allows", "enables", "provides", "use .* to", "facilitates"],
        "suggested_type": "feature",
        "base_confidence": 0.75,
    },
    "has_identity": {
        "keywords": [r"`[A-Z][a-zA-Z_]+`", r'"[A-Z][a-zA-Z ]+"', "called", "named"],
        "suggested_type": "command",
        "base_confidence": 0.80,
    },
    "reusable_concept": {
        "keywords": ["pattern", "approach", "strategy", "technique", "method"],
        "suggested_type": "pattern",
        "base_confidence": 0.70,
    },
    "concrete_implementation": {
        "keywords": [r"\{\{", r"!\{", r"@\{", "```"],
        "suggested_type": "tool",
        "base_confidence": 0.85,
    },
    "architectural_component": {
        "keywords": ["architecture", "system", "layer", "component", "module"],
        "suggested_type": "system",
        "base_confidence": 0.70,
    },
    "security_mechanism": {
        "keywords": ["protects", "secures", "prevents", "isolates", "guards"],
        "suggested_type": "security",
        "base_confidence": 0.80,
    },
}

VALID_NODE_TYPES = {
    "feature", "command", "tool", "workflow", "use_case",
    "pattern", "primitive", "system", "security",
}

LOW_DENSITY_THRESHOLD = 0.01  # <1% extraction rate = gap


# ============================================================================
# L3: Analyzer
# ============================================================================

class KGCompleterAnalyzer(BaseAnalyzer):
    """KG completeness and gap-filling engine."""

    def __init__(self):
        super().__init__(
            agent_name="kg-completer",
            model="sonnet",
            version="1.0",
        )

    def get_example_input(self) -> Dict[str, Any]:
        handbook_candidates = [
            os.path.join(NLKE_ROOT, "handbooks", f)
            for f in os.listdir(os.path.join(NLKE_ROOT, "handbooks"))
            if f.endswith(".md")
        ] if os.path.exists(os.path.join(NLKE_ROOT, "handbooks")) else []

        return {
            "name": "Handbook KG Completeness Analysis",
            "db_path": KG_DATABASES.get(
                "claude_cookbook",
                os.path.join(NLKE_ROOT, "claude-cookbook-kg", "claude-cookbook-kg.db"),
            ),
            "source_files": handbook_candidates[:2],
            "max_candidates": 30,
            "min_confidence": 0.65,
            "auto_generate": True,
        }

    def analyze(self, agent_input: AgentInput) -> AgentOutput:
        w = agent_input.workload
        db_path = w.get("db_path", "")
        source_files = w.get("source_files", [])
        max_candidates = w.get("max_candidates", 30)
        min_confidence = w.get("min_confidence", 0.65)
        auto_generate = w.get("auto_generate", True)

        rules = [
            "completeness_001_section_coverage",
            "completeness_002_density_threshold",
            "candidate_001_pattern_detection",
            "candidate_002_type_classification",
        ]

        # Load existing graph concepts
        existing_names: Set[str] = set()
        if db_path and os.path.exists(db_path):
            existing_names = self._load_existing_names(db_path)

        # Scan source files for gaps
        all_gaps: List[GapCandidate] = []
        section_stats = {}

        for src in source_files:
            if os.path.exists(src):
                gaps, stats = self._scan_for_gaps(src, existing_names, min_confidence)
                all_gaps.extend(gaps)
                section_stats[os.path.basename(src)] = stats

        # Sort by priority and confidence
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        all_gaps.sort(key=lambda g: (priority_order.get(g.priority, 3), -g.confidence))
        all_gaps = all_gaps[:max_candidates]

        # Auto-generate nodes and edges
        generated_nodes = []
        generated_edges = []
        if auto_generate and all_gaps:
            generated_nodes, generated_edges = self._generate_fill(all_gaps, existing_names)

        # Build recommendations
        recommendations = []

        # Gap summary recommendation
        by_priority = {}
        for g in all_gaps:
            by_priority.setdefault(g.priority, []).append(g)

        recommendations.append({
            "technique": "gap_analysis",
            "applicable": True,
            "total_gaps": len(all_gaps),
            "by_priority": {k: len(v) for k, v in by_priority.items()},
            "by_pattern": self._count_by_field(all_gaps, "pattern_type"),
            "by_type": self._count_by_field(all_gaps, "suggested_type"),
            "rules_applied": rules[:2],
        })

        if generated_nodes:
            recommendations.append({
                "technique": "auto_generation",
                "applicable": True,
                "nodes_generated": len(generated_nodes),
                "edges_generated": len(generated_edges),
                "node_json": [asdict(n) for n in generated_nodes[:10]],
                "edge_json": [asdict(e) for e in generated_edges[:10]],
                "rules_applied": rules[2:],
            })

        # Coverage analysis
        total_sections = sum(s.get("total_sections", 0) for s in section_stats.values())
        covered = sum(s.get("covered_sections", 0) for s in section_stats.values())
        coverage = covered / max(1, total_sections)

        # Meta-insight
        if all_gaps:
            critical_count = len(by_priority.get("critical", []))
            meta_insight = (
                f"Found {len(all_gaps)} extraction gaps across {len(source_files)} files "
                f"({critical_count} critical). Coverage: {coverage:.0%}. "
                f"Generated {len(generated_nodes)} nodes and {len(generated_edges)} edges to fill gaps."
            )
        else:
            meta_insight = f"No significant gaps found. Coverage: {coverage:.0%}."

        return AgentOutput(
            recommendations=recommendations,
            rules_applied=list(dict.fromkeys(rules)),
            meta_insight=meta_insight,
            analysis_data={
                "coverage": round(coverage, 3),
                "section_stats": section_stats,
                "gaps": [asdict(g) for g in all_gaps],
                "generated": {
                    "nodes": [asdict(n) for n in generated_nodes],
                    "edges": [asdict(e) for e in generated_edges],
                },
            },
            anti_patterns=[
                f"Low coverage section: {g.section}" for g in all_gaps if g.priority == "critical"
            ][:5],
            agent_metadata=self.build_metadata(),
        )

    def _load_existing_names(self, db_path: str) -> Set[str]:
        """Load existing node names from DB."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT LOWER(name) FROM nodes")
        names = {row[0] for row in cursor.fetchall()}
        conn.close()
        return names

    def _scan_for_gaps(
        self, filepath: str, existing: Set[str], min_conf: float
    ) -> Tuple[List[GapCandidate], Dict]:
        """Scan a source file for extraction gaps."""
        with open(filepath, "r", errors="replace") as f:
            lines = f.readlines()

        gaps = []
        current_section = "Introduction"
        sections_found = set()
        sections_with_concepts = set()

        for i, line in enumerate(lines, 1):
            # Track sections
            if line.startswith("#"):
                current_section = line.strip("#").strip()
                sections_found.add(current_section)

            # Check each pattern
            for pattern_name, config in DETECTION_PATTERNS.items():
                for keyword in config["keywords"]:
                    try:
                        if re.search(keyword, line, re.IGNORECASE):
                            # Extract candidate text
                            candidate_text = line.strip()
                            if len(candidate_text) < 10:
                                continue

                            # Check if already exists
                            text_lower = candidate_text.lower()
                            already_exists = any(
                                name in text_lower for name in existing
                                if len(name) > 3
                            )

                            if not already_exists:
                                conf = config["base_confidence"]
                                # Boost confidence for headings
                                if line.startswith("#"):
                                    conf += 0.10

                                if conf >= min_conf:
                                    priority = "critical" if conf > 0.85 else "high" if conf > 0.75 else "medium"
                                    gaps.append(GapCandidate(
                                        text=candidate_text[:200],
                                        line_number=i,
                                        section=current_section,
                                        pattern_type=pattern_name,
                                        confidence=round(conf, 2),
                                        suggested_type=config["suggested_type"],
                                        reasoning=f"Matched pattern '{pattern_name}' with keyword '{keyword}'",
                                        priority=priority,
                                    ))
                                    sections_with_concepts.add(current_section)
                            break
                    except re.error:
                        continue

        stats = {
            "total_sections": len(sections_found),
            "covered_sections": len(sections_with_concepts),
            "coverage_ratio": round(
                len(sections_with_concepts) / max(1, len(sections_found)), 3
            ),
            "total_lines": len(lines),
            "gaps_found": len(gaps),
        }

        return gaps, stats

    def _generate_fill(
        self, gaps: List[GapCandidate], existing: Set[str]
    ) -> Tuple[List[GeneratedNode], List[GeneratedEdge]]:
        """Auto-generate nodes and edges from gap candidates."""
        nodes = []
        edges = []
        generated_ids = set()

        for gap in gaps:
            # Generate node ID from text
            name = re.sub(r'[^a-zA-Z0-9\s]', '', gap.text[:60]).strip()
            name_parts = name.lower().split()[:4]
            node_id = "_".join(name_parts)

            if node_id in generated_ids or len(node_id) < 3:
                continue

            generated_ids.add(node_id)

            nodes.append(GeneratedNode(
                id=node_id,
                name=name[:80],
                type=gap.suggested_type,
                description=gap.text[:200],
                source_line=gap.line_number,
                confidence=gap.confidence,
            ))

            # Generate edges to existing nodes with similar names
            for existing_name in list(existing)[:50]:
                if any(word in existing_name for word in name_parts if len(word) > 3):
                    edges.append(GeneratedEdge(
                        from_node=node_id,
                        to_node=existing_name,
                        type="enhances",
                        weight=0.70,
                        description=f"Generated: {name[:40]} enhances {existing_name}",
                    ))

        return nodes, edges

    def _count_by_field(self, items: list, field: str) -> Dict[str, int]:
        counts = {}
        for item in items:
            val = getattr(item, field, "unknown")
            counts[val] = counts.get(val, 0) + 1
        return counts


# ============================================================================
# L5: CLI
# ============================================================================

if __name__ == "__main__":
    analyzer = KGCompleterAnalyzer()
    run_standard_cli(
        agent_name="KG Completer",
        description="Detect extraction gaps and auto-generate node/edge JSON to fill them",
        analyzer=analyzer,
    )

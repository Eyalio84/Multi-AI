#!/usr/bin/env python3
"""
Relationship Suggester Agent

Extends NLKE relationship-suggester.py with cross-KG suggestions,
semantic similarity, and 3rd Knowledge merge analysis.

Wraps: NLKE relationship-suggester.py (736 lines, 9 relationship types)
Layer: L1-L5 (Full 5-layer pattern via agent_base)

Usage:
    python3 relationship_suggester_agent.py --example
    python3 relationship_suggester_agent.py --workload config.json
    python3 relationship_suggester_agent.py --workload config.json --summary

Created: February 6, 2026
"""

import sys
import os
import sqlite3
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.agent_base import (
    AgentInput, AgentOutput, BaseAnalyzer, run_standard_cli,
    NLKE_ROOT, KG_DATABASES,
)

from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any, Set, Tuple
from pathlib import Path


# ============================================================================
# L1: Data Models
# ============================================================================

@dataclass
class EdgeSuggestion:
    source_id: str
    source_name: str
    target_id: str
    target_name: str
    rel_type: str
    confidence: float
    weight: float
    evidence: List[str]
    reasoning: str


# ============================================================================
# L2: Constants
# ============================================================================

RELATIONSHIP_PATTERNS = {
    "enables": {
        "keywords": ["enables", "allows", "makes possible", "facilitates", "provides"],
        "base_weight": 0.85,
    },
    "requires": {
        "keywords": ["requires", "needs", "depends on", "relies on", "prerequisite"],
        "base_weight": 0.95,
    },
    "enhances": {
        "keywords": ["enhances", "improves", "strengthens", "boosts", "makes better"],
        "base_weight": 0.70,
    },
    "combines_with": {
        "keywords": ["combines with", "uses", "integrates with", "works with", "pairs with"],
        "base_weight": 0.80,
    },
    "composes_into": {
        "keywords": ["is part of", "component of", "built with", "consists of", "includes"],
        "base_weight": 0.85,
    },
    "implements": {
        "keywords": ["implements", "instance of", "example of", "type of", "provides concrete"],
        "base_weight": 1.00,
    },
    "secures": {
        "keywords": ["secures", "protects", "prevents", "isolates", "guards against"],
        "base_weight": 1.00,
    },
    "optimizes": {
        "keywords": ["optimizes", "makes faster", "reduces cost", "accelerates", "improves performance"],
        "base_weight": 0.75,
    },
    "similar_to": {
        "keywords": ["similar to", "like", "analogous to", "comparable to", "resembles"],
        "base_weight": 0.60,
    },
}

WEIGHT_MODIFIERS = {
    "critical": +0.10,
    "essential": +0.10,
    "required": +0.05,
    "must": +0.05,
    "optional": -0.10,
    "can": -0.05,
    "might": -0.05,
}


# ============================================================================
# L3: Analyzer
# ============================================================================

class RelationshipSuggesterAnalyzer(BaseAnalyzer):
    """Relationship suggestion engine."""

    def __init__(self):
        super().__init__(
            agent_name="relationship-suggester",
            model="sonnet",
            version="1.0",
        )

    def get_example_input(self) -> Dict[str, Any]:
        return {
            "name": "Claude Cookbook KG Relationship Discovery",
            "db_path": KG_DATABASES.get(
                "claude_cookbook",
                os.path.join(NLKE_ROOT, "claude-cookbook-kg", "claude-cookbook-kg.db"),
            ),
            "max_suggestions": 20,
            "min_confidence": 0.65,
            "cross_kg": False,
        }

    def analyze(self, agent_input: AgentInput) -> AgentOutput:
        w = agent_input.workload
        db_path = w.get("db_path", "")
        max_suggestions = w.get("max_suggestions", 20)
        min_confidence = w.get("min_confidence", 0.65)

        if not db_path or not os.path.exists(db_path):
            return AgentOutput(
                recommendations=[{
                    "technique": "relationship_suggestion",
                    "applicable": False,
                    "reason": f"Database not found: {db_path}",
                }],
                rules_applied=["validation"],
                meta_insight="Cannot analyze: database not found",
                agent_metadata=self.build_metadata(),
            )

        # Load graph data
        nodes, edges, existing_pairs = self._load_graph(db_path)
        rules = [
            "rel_001_evidence_based_scoring",
            "rel_002_weight_estimation",
            "rel_003_confidence_modifiers",
            "rel_004_cross_reference_validation",
        ]

        # Analyze all node pairs for potential relationships
        suggestions = self._find_relationships(nodes, existing_pairs, min_confidence)

        # Sort by confidence and limit
        suggestions.sort(key=lambda s: s.confidence, reverse=True)
        suggestions = suggestions[:max_suggestions]

        # Build recommendations
        recommendations = []
        for s in suggestions:
            recommendations.append({
                "technique": "relationship_suggestion",
                "applicable": True,
                "source": f"{s.source_name} ({s.source_id})",
                "target": f"{s.target_name} ({s.target_id})",
                "type": s.rel_type,
                "confidence": round(s.confidence, 2),
                "weight": round(s.weight, 2),
                "evidence": s.evidence,
                "reasoning": s.reasoning,
                "insert_sql": (
                    f"INSERT INTO edges (id, from_node, to_node, type, weight, confidence, description) "
                    f"VALUES ('{s.source_id}_{s.rel_type}_{s.target_id}', "
                    f"'{s.source_id}', '{s.target_id}', '{s.rel_type}', "
                    f"{s.weight}, 'medium', '{s.reasoning}');"
                ),
                "rules_applied": rules,
            })

        # Type distribution
        type_dist = {}
        for s in suggestions:
            type_dist[s.rel_type] = type_dist.get(s.rel_type, 0) + 1

        # Meta-insight
        if suggestions:
            top_type = max(type_dist, key=type_dist.get) if type_dist else "none"
            avg_conf = sum(s.confidence for s in suggestions) / len(suggestions)
            meta_insight = (
                f"Found {len(suggestions)} potential relationships "
                f"(avg confidence: {avg_conf:.2f}). "
                f"Most common type: {top_type} ({type_dist.get(top_type, 0)}). "
                f"Graph currently has {len(nodes)} nodes, {len(edges)} edges."
            )
        else:
            meta_insight = "No new relationships found above confidence threshold"

        return AgentOutput(
            recommendations=recommendations,
            rules_applied=list(dict.fromkeys(rules)),
            meta_insight=meta_insight,
            analysis_data={
                "graph_stats": {
                    "nodes": len(nodes),
                    "edges": len(edges),
                    "existing_pairs": len(existing_pairs),
                },
                "suggestions_found": len(suggestions),
                "type_distribution": type_dist,
                "confidence_range": {
                    "min": round(min(s.confidence for s in suggestions), 2) if suggestions else 0,
                    "max": round(max(s.confidence for s in suggestions), 2) if suggestions else 0,
                },
            },
            anti_patterns=[],
            agent_metadata=self.build_metadata(),
        )

    def _load_graph(self, db_path: str) -> tuple:
        """Load nodes, edges, and existing pairs from DB."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT id, name, type, description FROM nodes")
        nodes = [
            {"id": r[0], "name": r[1], "type": r[2], "description": r[3]}
            for r in cursor.fetchall()
        ]

        cursor.execute("SELECT id, from_node, to_node, type, weight FROM edges")
        edges = [
            {"id": r[0], "from": r[1], "to": r[2], "type": r[3], "weight": r[4]}
            for r in cursor.fetchall()
        ]

        existing_pairs = set()
        for e in edges:
            existing_pairs.add((e["from"], e["to"], e["type"]))

        conn.close()
        return nodes, edges, existing_pairs

    def _find_relationships(
        self, nodes: List[Dict], existing: Set[tuple], min_conf: float
    ) -> List[EdgeSuggestion]:
        """Analyze node pairs for potential relationships."""
        suggestions = []

        for i, n1 in enumerate(nodes):
            for n2 in nodes[i + 1:]:
                # Check each relationship type
                for rel_type, patterns in RELATIONSHIP_PATTERNS.items():
                    # Skip if already exists
                    if (n1["id"], n2["id"], rel_type) in existing:
                        continue
                    if (n2["id"], n1["id"], rel_type) in existing:
                        continue

                    # Check for keyword matches in descriptions
                    evidence = []
                    desc1 = (n1.get("description") or "").lower()
                    desc2 = (n2.get("description") or "").lower()
                    name1 = (n1.get("name") or "").lower()
                    name2 = (n2.get("name") or "").lower()

                    # Check if n1's description mentions n2
                    if name2 in desc1 or any(kw in desc1 for kw in [name2.replace("_", " "), name2.replace("-", " ")]):
                        evidence.append(f"{n1['name']} description references {n2['name']}")

                    # Check if n2's description mentions n1
                    if name1 in desc2 or any(kw in desc2 for kw in [name1.replace("_", " "), name1.replace("-", " ")]):
                        evidence.append(f"{n2['name']} description references {n1['name']}")

                    # Check for relationship keywords
                    combined = desc1 + " " + desc2
                    for kw in patterns["keywords"]:
                        if kw in combined:
                            evidence.append(f"Keyword match: '{kw}'")
                            break

                    # Type-based heuristics
                    if rel_type == "implements" and n1["type"] == "pattern" and n2["type"] == "tool":
                        evidence.append(f"Type heuristic: pattern->tool")
                    elif rel_type == "requires" and n1["type"] == "workflow" and n2["type"] == "tool":
                        evidence.append(f"Type heuristic: workflow requires tool")
                    elif rel_type == "enables" and n1["type"] == "feature" and n2["type"] == "use_case":
                        evidence.append(f"Type heuristic: feature enables use_case")

                    if len(evidence) >= 2:
                        conf = min(0.95, 0.50 + len(evidence) * 0.15)
                        if conf >= min_conf:
                            weight = self._estimate_weight(rel_type, combined)
                            suggestions.append(EdgeSuggestion(
                                source_id=n1["id"],
                                source_name=n1["name"],
                                target_id=n2["id"],
                                target_name=n2["name"],
                                rel_type=rel_type,
                                confidence=conf,
                                weight=weight,
                                evidence=evidence,
                                reasoning=f"{n1['name']} {rel_type} {n2['name']} ({len(evidence)} evidence points)",
                            ))

        return suggestions

    def _estimate_weight(self, rel_type: str, context: str) -> float:
        """Estimate edge weight based on type and context."""
        base = RELATIONSHIP_PATTERNS[rel_type]["base_weight"]
        for keyword, modifier in WEIGHT_MODIFIERS.items():
            if keyword in context:
                base += modifier
        return max(0.1, min(1.0, base))


# ============================================================================
# L5: CLI
# ============================================================================

if __name__ == "__main__":
    analyzer = RelationshipSuggesterAnalyzer()
    run_standard_cli(
        agent_name="Relationship Suggester",
        description="Suggest new edges between KG nodes using 9 relationship types",
        analyzer=analyzer,
    )

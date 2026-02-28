#!/usr/bin/env python3
"""
KG Health Monitor Agent

Monitors all NLKE knowledge graph databases for structural integrity,
orphaned nodes, connectivity drops, schema issues, and quality metrics.

Wraps: NLKE kg-health-check.py, quality-validator.py, ecosystem_integrity_check.py
Layer: L1-L5 (Full 5-layer pattern via agent_base)

Usage:
    python3 kg_health_monitor.py --example
    python3 kg_health_monitor.py --workload config.json
    python3 kg_health_monitor.py --workload config.json --summary

Created: February 6, 2026
"""

import sys
import os
import sqlite3

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.agent_base import (
    AgentInput, AgentOutput, BaseAnalyzer, run_standard_cli,
    NLKE_ROOT, KG_DATABASES,
)

from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional
from pathlib import Path


# ============================================================================
# L1: Data Models
# ============================================================================

@dataclass
class KGMetrics:
    db_path: str
    db_name: str
    node_count: int
    edge_count: int
    orphaned_nodes: int
    node_types: Dict[str, int]
    edge_types: Dict[str, int]
    connectivity_ratio: float
    avg_weight: float
    issues: List[str]
    health_status: str  # HEALTHY, WARNING, CRITICAL


# ============================================================================
# L2: Constants
# ============================================================================

VALID_NODE_TYPES = {
    "feature", "command", "tool", "workflow", "use_case",
    "pattern", "primitive", "system", "security", "agent_base",
    "atomic_capability", "atomic_feature", "claude_api_feature",
    "claude_capability", "claude_integration", "claude_multimodal",
    "claude_pattern", "claude_sdk_feature", "claude_skill",
    "claude_technique", "claude_tool_integration", "executable_tool",
    "external_tool", "mcp_server", "meta", "nlke_reference",
    "official_example", "subagent", "agent", "mcp_tool",
}

VALID_EDGE_TYPES = {
    "enables", "requires", "enhances", "combines_with", "similar_to",
    "implements", "conflicts_with", "replaces", "composes_into",
    "secures", "optimizes", "supports", "demonstrates", "uses",
    "related_to", "serves_use_case", "uses_feature", "depends_on",
    "extends", "wraps", "validates", "delegates_to", "routes_to",
}

EXPECTED_WEIGHT_RANGES = {
    "requires": (0.9, 1.0),
    "implements": (0.9, 1.0),
    "secures": (0.9, 1.0),
    "enables": (0.8, 0.9),
    "composes_into": (0.8, 0.9),
    "combines_with": (0.7, 0.9),
    "enhances": (0.6, 0.8),
    "optimizes": (0.6, 0.8),
    "similar_to": (0.5, 0.7),
}

HEALTH_THRESHOLDS = {
    "orphan_ratio_warning": 0.05,
    "orphan_ratio_critical": 0.15,
    "min_connectivity": 0.80,
    "min_edge_node_ratio": 1.5,
}


# ============================================================================
# L3: Analyzer
# ============================================================================

class KGHealthAnalyzer(BaseAnalyzer):
    """KG health monitoring engine."""

    def __init__(self):
        super().__init__(
            agent_name="kg-health-monitor",
            model="haiku",
            version="1.0",
        )

    def get_example_input(self) -> Dict[str, Any]:
        return {
            "name": "Full NLKE KG Health Check",
            "scan_all": True,
            "nlke_root": NLKE_ROOT,
            "specific_dbs": [],
        }

    def analyze(self, agent_input: AgentInput) -> AgentOutput:
        w = agent_input.workload
        nlke_root = w.get("nlke_root", NLKE_ROOT)
        specific_dbs = w.get("specific_dbs", [])

        # Discover databases
        if specific_dbs:
            db_paths = specific_dbs
        else:
            db_paths = self._discover_databases(nlke_root)

        if not db_paths:
            return AgentOutput(
                recommendations=[{
                    "technique": "kg_health_check",
                    "applicable": False,
                    "reason": "No .db files found",
                }],
                rules_applied=["discovery_scan"],
                meta_insight="No knowledge graph databases found to monitor",
                agent_metadata=self.build_metadata(),
            )

        # Analyze each database
        all_metrics = []
        all_issues = []
        recommendations = []
        rules = ["structure_validation", "connectivity_check", "weight_validation", "orphan_detection"]

        for db_path in db_paths:
            metrics = self._analyze_database(db_path)
            if metrics:
                all_metrics.append(metrics)
                all_issues.extend(
                    [f"[{metrics.db_name}] {issue}" for issue in metrics.issues]
                )

        # Generate recommendations
        for m in all_metrics:
            status_emoji = {"HEALTHY": "OK", "WARNING": "WARN", "CRITICAL": "CRIT"}
            rec = {
                "technique": "kg_health_check",
                "applicable": True,
                "database": m.db_name,
                "health_status": m.health_status,
                "nodes": m.node_count,
                "edges": m.edge_count,
                "orphaned": m.orphaned_nodes,
                "connectivity": round(m.connectivity_ratio, 3),
                "issues_count": len(m.issues),
                "rules_applied": rules,
            }
            recommendations.append(rec)

        # Cross-KG comparison
        cross_kg = None
        if len(all_metrics) >= 2:
            cross_kg = self._cross_kg_analysis(all_metrics)
            rules.append("cross_kg_comparison")

        # Health summary
        healthy = sum(1 for m in all_metrics if m.health_status == "HEALTHY")
        warning = sum(1 for m in all_metrics if m.health_status == "WARNING")
        critical = sum(1 for m in all_metrics if m.health_status == "CRITICAL")
        total_nodes = sum(m.node_count for m in all_metrics)
        total_edges = sum(m.edge_count for m in all_metrics)
        total_orphans = sum(m.orphaned_nodes for m in all_metrics)

        if critical > 0:
            overall = "CRITICAL"
            meta_insight = (
                f"{critical} KG(s) in CRITICAL state. "
                f"Total: {total_nodes} nodes, {total_edges} edges, {total_orphans} orphans. "
                f"Immediate attention required."
            )
        elif warning > 0:
            meta_insight = (
                f"{warning} KG(s) with warnings, {healthy} healthy. "
                f"Total: {total_nodes} nodes, {total_edges} edges. "
                f"Minor issues to address."
            )
            overall = "WARNING"
        else:
            meta_insight = (
                f"All {healthy} KG(s) healthy. "
                f"Total: {total_nodes} nodes, {total_edges} edges, "
                f"{total_orphans} orphans ({total_orphans/max(1,total_nodes)*100:.1f}%)."
            )
            overall = "HEALTHY"

        return AgentOutput(
            recommendations=recommendations,
            rules_applied=list(dict.fromkeys(rules)),
            meta_insight=meta_insight,
            analysis_data={
                "overall_status": overall,
                "databases_scanned": len(all_metrics),
                "health_summary": {
                    "healthy": healthy,
                    "warning": warning,
                    "critical": critical,
                },
                "totals": {
                    "nodes": total_nodes,
                    "edges": total_edges,
                    "orphans": total_orphans,
                },
                "per_database": [asdict(m) for m in all_metrics],
                "cross_kg": cross_kg,
                "all_issues": all_issues,
            },
            anti_patterns=[i for i in all_issues if "CRITICAL" in i or "orphan" in i.lower()],
            agent_metadata=self.build_metadata(),
        )

    def _discover_databases(self, root: str) -> List[str]:
        """Find all .db files in NLKE root."""
        dbs = []
        for p in Path(root).rglob("*.db"):
            # Check if it's a KG database (has nodes/edges tables)
            try:
                conn = sqlite3.connect(str(p))
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='nodes'")
                if cursor.fetchone():
                    dbs.append(str(p))
                conn.close()
            except Exception:
                pass
        return dbs

    def _analyze_database(self, db_path: str) -> Optional[KGMetrics]:
        """Analyze a single KG database."""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            issues = []

            # Node count
            cursor.execute("SELECT COUNT(*) FROM nodes")
            node_count = cursor.fetchone()[0]

            # Edge count
            cursor.execute("SELECT COUNT(*) FROM edges")
            edge_count = cursor.fetchone()[0]

            # Node types
            cursor.execute("SELECT type, COUNT(*) FROM nodes GROUP BY type ORDER BY COUNT(*) DESC")
            node_types = dict(cursor.fetchall())

            # Check for unexpected node types
            for nt in node_types:
                if nt not in VALID_NODE_TYPES:
                    issues.append(f"WARNING: Unknown node type '{nt}'")

            # Edge types
            cursor.execute("SELECT type, COUNT(*) FROM edges GROUP BY type ORDER BY COUNT(*) DESC")
            edge_types = dict(cursor.fetchall())

            for et in edge_types:
                if et not in VALID_EDGE_TYPES:
                    issues.append(f"WARNING: Unknown edge type '{et}'")

            # Orphaned nodes
            cursor.execute("""
                SELECT COUNT(*) FROM nodes n
                WHERE NOT EXISTS (SELECT 1 FROM edges WHERE from_node = n.id)
                AND NOT EXISTS (SELECT 1 FROM edges WHERE to_node = n.id)
            """)
            orphaned = cursor.fetchone()[0]

            # Connectivity ratio
            connected = node_count - orphaned
            connectivity = connected / max(1, node_count)

            # Average weight
            cursor.execute("SELECT AVG(weight) FROM edges")
            avg_weight_result = cursor.fetchone()[0]
            avg_weight = avg_weight_result if avg_weight_result else 0.0

            # Weight distribution check
            for edge_type, (low, high) in EXPECTED_WEIGHT_RANGES.items():
                if edge_type in edge_types:
                    cursor.execute(
                        "SELECT AVG(weight) FROM edges WHERE type = ?", (edge_type,)
                    )
                    type_avg = cursor.fetchone()[0]
                    if type_avg and (type_avg < low - 0.1 or type_avg > high + 0.1):
                        issues.append(
                            f"WARNING: {edge_type} avg weight {type_avg:.2f} "
                            f"outside expected {low}-{high}"
                        )

            conn.close()

            # Determine health status
            orphan_ratio = orphaned / max(1, node_count)
            edge_node_ratio = edge_count / max(1, node_count)

            if orphan_ratio > HEALTH_THRESHOLDS["orphan_ratio_critical"]:
                health = "CRITICAL"
                issues.append(f"CRITICAL: {orphan_ratio:.0%} orphaned nodes")
            elif orphan_ratio > HEALTH_THRESHOLDS["orphan_ratio_warning"]:
                health = "WARNING"
                issues.append(f"WARNING: {orphan_ratio:.0%} orphaned nodes")
            elif connectivity < HEALTH_THRESHOLDS["min_connectivity"]:
                health = "WARNING"
                issues.append(f"WARNING: Low connectivity {connectivity:.0%}")
            elif edge_node_ratio < HEALTH_THRESHOLDS["min_edge_node_ratio"]:
                health = "WARNING"
                issues.append(f"WARNING: Low edge/node ratio {edge_node_ratio:.1f}")
            else:
                health = "HEALTHY"

            db_name = Path(db_path).stem

            return KGMetrics(
                db_path=db_path,
                db_name=db_name,
                node_count=node_count,
                edge_count=edge_count,
                orphaned_nodes=orphaned,
                node_types=node_types,
                edge_types=edge_types,
                connectivity_ratio=round(connectivity, 3),
                avg_weight=round(avg_weight, 3),
                issues=issues,
                health_status=health,
            )
        except Exception as e:
            return KGMetrics(
                db_path=db_path,
                db_name=Path(db_path).stem,
                node_count=0,
                edge_count=0,
                orphaned_nodes=0,
                node_types={},
                edge_types={},
                connectivity_ratio=0.0,
                avg_weight=0.0,
                issues=[f"ERROR: Failed to analyze: {e}"],
                health_status="CRITICAL",
            )

    def _cross_kg_analysis(self, metrics: List[KGMetrics]) -> Dict:
        """Compare metrics across KGs."""
        return {
            "databases_compared": len(metrics),
            "largest_kg": max(metrics, key=lambda m: m.node_count).db_name,
            "smallest_kg": min(metrics, key=lambda m: m.node_count).db_name,
            "most_connected": max(metrics, key=lambda m: m.connectivity_ratio).db_name,
            "least_connected": min(metrics, key=lambda m: m.connectivity_ratio).db_name,
            "total_unique_node_types": len(
                set().union(*[set(m.node_types.keys()) for m in metrics])
            ),
            "total_unique_edge_types": len(
                set().union(*[set(m.edge_types.keys()) for m in metrics])
            ),
        }


# ============================================================================
# L5: CLI
# ============================================================================

if __name__ == "__main__":
    analyzer = KGHealthAnalyzer()
    run_standard_cli(
        agent_name="KG Health Monitor",
        description="Monitor knowledge graph health across all NLKE databases",
        analyzer=analyzer,
    )

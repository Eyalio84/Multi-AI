#!/usr/bin/env python3
"""
Visual Report Agent (#32)

Generate matplotlib/pillow visual reports from NLKE agent data.
Creates charts, diagrams, and summary images from JSON agent output.

Layer: L1-L5 (Full 5-layer pattern via agent_base)

Usage:
    python3 visual_report.py --example
    python3 visual_report.py --workload report_data.json --output report.png

Created: February 6, 2026
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.agent_base import (
    AgentInput, AgentOutput, BaseAnalyzer, run_standard_cli,
)

from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any, Optional

# Lazy imports for visualization libraries
_HAS_MATPLOTLIB = None
_HAS_PILLOW = None


def _check_matplotlib():
    global _HAS_MATPLOTLIB
    if _HAS_MATPLOTLIB is None:
        try:
            import matplotlib
            matplotlib.use("Agg")  # Non-interactive backend
            _HAS_MATPLOTLIB = True
        except ImportError:
            _HAS_MATPLOTLIB = False
    return _HAS_MATPLOTLIB


def _check_pillow():
    global _HAS_PILLOW
    if _HAS_PILLOW is None:
        try:
            from PIL import Image
            _HAS_PILLOW = True
        except ImportError:
            _HAS_PILLOW = False
    return _HAS_PILLOW


# ============================================================================
# L1: Data Models
# ============================================================================

@dataclass
class ChartSpec:
    chart_type: str  # bar, pie, line, heatmap, table
    title: str
    data: Dict[str, Any]
    output_path: Optional[str] = None


@dataclass
class ReportResult:
    charts_generated: int
    charts_failed: int
    output_files: List[str]
    total_data_points: int


# ============================================================================
# L2: Constants
# ============================================================================

CHART_TYPES = ["bar", "pie", "line", "heatmap", "table", "scatter"]

DEFAULT_COLORS = [
    "#4285F4", "#EA4335", "#FBBC04", "#34A853",  # Google colors
    "#7B61FF", "#FF6B6B", "#4ECDC4", "#45B7D1",  # Accent colors
]

REPORT_DIR = os.path.join(
    os.environ.get("NLKE_ROOT", "/storage/self/primary/Download/44nlke/NLKE"),
    "reports",
)


# ============================================================================
# L3: Analyzer
# ============================================================================

class VisualReportAnalyzer(BaseAnalyzer):
    """Visual report generation engine."""

    def __init__(self):
        super().__init__(
            agent_name="visual-report",
            model="haiku",
            version="1.0",
        )

    def get_example_input(self) -> Dict[str, Any]:
        return {
            "name": "NLKE Agent Ecosystem Report",
            "charts": [
                {
                    "chart_type": "bar",
                    "title": "Agent Count by Phase",
                    "data": {
                        "labels": ["Foundation", "Cost Opt", "KG", "Workflow", "Emergent", "Multi-Model", "Rule Engine", "Knowledge", "MCP"],
                        "values": [5, 3, 3, 3, 3, 3, 3, 3, 1],
                    },
                },
                {
                    "chart_type": "pie",
                    "title": "Model Tier Distribution",
                    "data": {
                        "labels": ["Opus (Strategic)", "Sonnet (Analysis)", "Haiku (Routine)"],
                        "values": [2, 14, 11],
                    },
                },
                {
                    "chart_type": "bar",
                    "title": "Cost per Execution (USD)",
                    "data": {
                        "labels": ["Haiku Agent", "Sonnet Agent", "Opus Agent", "Gemini Flash", "Gemini Pro"],
                        "values": [0.002, 0.01, 0.05, 0.001, 0.015],
                    },
                },
                {
                    "chart_type": "table",
                    "title": "Phase Completion Status",
                    "data": {
                        "headers": ["Phase", "Status", "Deliverables"],
                        "rows": [
                            ["Phase 0-1", "COMPLETE", "5 agents + infrastructure"],
                            ["Phase 2-4", "COMPLETE", "12 agents + MCP creator"],
                            ["Phase 4.5", "COMPLETE", "9 agents + rule engine"],
                            ["Phase 5-7", "COMPLETE", "Arsenal + hardening"],
                            ["Phase 8-8.5", "COMPLETE", "Audit + FORGE-AI"],
                        ],
                    },
                },
            ],
            "output_dir": REPORT_DIR,
            "generate_files": False,
        }

    def _generate_bar_chart(self, spec: ChartSpec, output_path: str) -> bool:
        """Generate a bar chart."""
        if not _check_matplotlib():
            return False
        import matplotlib.pyplot as plt

        labels = spec.data.get("labels", [])
        values = spec.data.get("values", [])

        fig, ax = plt.subplots(figsize=(10, 6))
        colors = DEFAULT_COLORS[:len(labels)]
        bars = ax.bar(range(len(labels)), values, color=colors)
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=9)
        ax.set_title(spec.title, fontsize=14, fontweight="bold")
        ax.set_ylabel("Value")

        # Add value labels on bars
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                    f"{val}", ha="center", va="bottom", fontsize=9)

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()
        return True

    def _generate_pie_chart(self, spec: ChartSpec, output_path: str) -> bool:
        """Generate a pie chart."""
        if not _check_matplotlib():
            return False
        import matplotlib.pyplot as plt

        labels = spec.data.get("labels", [])
        values = spec.data.get("values", [])

        fig, ax = plt.subplots(figsize=(8, 8))
        colors = DEFAULT_COLORS[:len(labels)]
        wedges, texts, autotexts = ax.pie(
            values, labels=labels, colors=colors,
            autopct="%1.0f%%", startangle=90,
        )
        ax.set_title(spec.title, fontsize=14, fontweight="bold")

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()
        return True

    def _generate_line_chart(self, spec: ChartSpec, output_path: str) -> bool:
        """Generate a line chart."""
        if not _check_matplotlib():
            return False
        import matplotlib.pyplot as plt

        x = spec.data.get("x", list(range(len(spec.data.get("y", [])))))
        y = spec.data.get("y", [])

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(x, y, marker="o", color=DEFAULT_COLORS[0], linewidth=2)
        ax.set_title(spec.title, fontsize=14, fontweight="bold")
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()
        return True

    def _generate_chart(self, spec: ChartSpec, output_dir: str, index: int) -> Optional[str]:
        """Generate a single chart and return path."""
        safe_title = spec.title.lower().replace(" ", "_")[:30]
        output_path = os.path.join(output_dir, f"chart_{index}_{safe_title}.png")

        generators = {
            "bar": self._generate_bar_chart,
            "pie": self._generate_pie_chart,
            "line": self._generate_line_chart,
        }

        gen = generators.get(spec.chart_type)
        if gen and gen(spec, output_path):
            return output_path
        return None

    def analyze(self, agent_input: AgentInput) -> AgentOutput:
        w = agent_input.workload
        charts_data = w.get("charts", [])
        output_dir = w.get("output_dir", REPORT_DIR)
        generate_files = w.get("generate_files", False)

        rules = [
            "report_001_chart_selection",
            "report_002_data_validation",
            "report_003_output_formats",
            "report_004_accessibility",
        ]

        os.makedirs(output_dir, exist_ok=True)

        specs = []
        for cd in charts_data:
            specs.append(ChartSpec(
                chart_type=cd.get("chart_type", "bar"),
                title=cd.get("title", "Untitled"),
                data=cd.get("data", {}),
            ))

        generated = []
        failed = 0
        total_points = 0

        for i, spec in enumerate(specs):
            # Count data points
            values = spec.data.get("values", spec.data.get("y", []))
            rows = spec.data.get("rows", [])
            total_points += len(values) + len(rows)

            if generate_files:
                path = self._generate_chart(spec, output_dir, i)
                if path:
                    generated.append(path)
                else:
                    failed += 1
            else:
                generated.append(f"[dry run] {spec.chart_type}: {spec.title}")

        has_matplotlib = _check_matplotlib()
        has_pillow = _check_pillow()

        anti_patterns = []
        if not has_matplotlib and generate_files:
            anti_patterns.append("matplotlib not installed — charts cannot be generated")
        if failed > 0:
            anti_patterns.append(f"{failed} charts failed to generate")

        report = ReportResult(
            charts_generated=len(generated),
            charts_failed=failed,
            output_files=generated,
            total_data_points=total_points,
        )

        recommendations = [{
            "technique": "visual_report",
            "applicable": True,
            "report": asdict(report),
            "chart_specs": [
                {"type": s.chart_type, "title": s.title, "data_points": len(s.data.get("values", s.data.get("y", s.data.get("rows", []))))}
                for s in specs
            ],
            "libraries": {"matplotlib": has_matplotlib, "pillow": has_pillow},
            "rules_applied": rules,
        }]

        meta_insight = (
            f"Report: {len(specs)} charts specified, {len(generated)} generated, "
            f"{failed} failed. {total_points} total data points. "
            f"matplotlib={'available' if has_matplotlib else 'missing'}."
        )

        return AgentOutput(
            recommendations=recommendations,
            rules_applied=rules,
            meta_insight=meta_insight,
            analysis_data={
                "report": asdict(report),
                "output_dir": output_dir,
            },
            anti_patterns=anti_patterns,
            agent_metadata=self.build_metadata(),
        )


if __name__ == "__main__":
    analyzer = VisualReportAnalyzer()
    run_standard_cli(
        agent_name="Visual Report",
        description="Generate matplotlib/pillow visual reports from agent data",
        analyzer=analyzer,
    )

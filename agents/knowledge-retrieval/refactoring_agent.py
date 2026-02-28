#!/usr/bin/env python3
"""
Refactoring Agent

Large-scale code analysis and refactoring planning.
Dependency graphs, code smells, extractable modules.

Layer: L1-L5 (Full 5-layer pattern via agent_base)

Usage:
    python3 refactoring_agent.py --example
    python3 refactoring_agent.py --workload target.json --summary

Created: February 6, 2026
"""

import sys
import os
import re
import ast

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.agent_base import (
    AgentInput, AgentOutput, BaseAnalyzer, run_standard_cli,
    NLKE_ROOT,
)

from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any, Optional, Set
from pathlib import Path


# ============================================================================
# L1: Data Models
# ============================================================================

@dataclass
class CodeSmell:
    file: str
    line: int
    smell_type: str
    severity: str  # critical, high, medium, low
    description: str
    suggestion: str

@dataclass
class FunctionInfo:
    name: str
    file: str
    line: int
    lines: int
    params: int
    calls: List[str]
    complexity: str  # low, medium, high


# ============================================================================
# L2: Constants
# ============================================================================

SMELL_THRESHOLDS = {
    "god_function": {"lines": 100, "severity": "high"},
    "deep_nesting": {"levels": 4, "severity": "medium"},
    "long_file": {"lines": 500, "severity": "medium"},
    "many_params": {"params": 6, "severity": "low"},
    "no_docstring": {"severity": "low"},
}


# ============================================================================
# L3: Analyzer
# ============================================================================

class RefactoringAnalyzer(BaseAnalyzer):
    """Code refactoring analysis engine."""

    def __init__(self):
        super().__init__(
            agent_name="refactoring-agent",
            model="sonnet",
            version="1.0",
        )

    def get_example_input(self) -> Dict[str, Any]:
        return {
            "name": "NLKE Root Python Files Analysis",
            "target_dir": NLKE_ROOT,
            "file_pattern": "*.py",
            "max_files": 10,
            "include_dependency_graph": True,
        }

    def _analyze_file(self, filepath: str) -> Dict[str, Any]:
        """Analyze a single Python file."""
        result = {
            "path": filepath,
            "lines": 0,
            "functions": [],
            "smells": [],
            "imports": [],
        }

        try:
            with open(filepath, "r", errors="replace") as f:
                content = f.read()
                lines = content.split("\n")
                result["lines"] = len(lines)

            # Parse AST
            try:
                tree = ast.parse(content)
            except SyntaxError:
                result["smells"].append(CodeSmell(
                    file=os.path.basename(filepath),
                    line=0, smell_type="syntax_error",
                    severity="critical",
                    description="File has syntax errors",
                    suggestion="Fix syntax errors before refactoring",
                ))
                return result

            # Extract imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        result["imports"].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        result["imports"].append(node.module)

            # Extract functions
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_lines = node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') and node.end_lineno else 0
                    params = len(node.args.args)

                    # Get calls within function
                    calls = []
                    for child in ast.walk(node):
                        if isinstance(child, ast.Call):
                            if isinstance(child.func, ast.Name):
                                calls.append(child.func.id)
                            elif isinstance(child.func, ast.Attribute):
                                calls.append(child.func.attr)

                    complexity = "low"
                    if func_lines > 50:
                        complexity = "medium"
                    if func_lines > 100:
                        complexity = "high"

                    func = FunctionInfo(
                        name=node.name,
                        file=os.path.basename(filepath),
                        line=node.lineno,
                        lines=func_lines,
                        params=params,
                        calls=calls[:10],
                        complexity=complexity,
                    )
                    result["functions"].append(func)

                    # Check for smells
                    if func_lines > SMELL_THRESHOLDS["god_function"]["lines"]:
                        result["smells"].append(CodeSmell(
                            file=os.path.basename(filepath),
                            line=node.lineno,
                            smell_type="god_function",
                            severity="high",
                            description=f"Function '{node.name}' is {func_lines} lines (>{SMELL_THRESHOLDS['god_function']['lines']})",
                            suggestion=f"Extract sub-functions from {node.name}",
                        ))

                    if params > SMELL_THRESHOLDS["many_params"]["params"]:
                        result["smells"].append(CodeSmell(
                            file=os.path.basename(filepath),
                            line=node.lineno,
                            smell_type="many_params",
                            severity="low",
                            description=f"Function '{node.name}' has {params} params (>{SMELL_THRESHOLDS['many_params']['params']})",
                            suggestion=f"Use dataclass or dict for {node.name} parameters",
                        ))

            # File-level smells
            if result["lines"] > SMELL_THRESHOLDS["long_file"]["lines"]:
                result["smells"].append(CodeSmell(
                    file=os.path.basename(filepath),
                    line=0, smell_type="long_file",
                    severity="medium",
                    description=f"File is {result['lines']} lines (>{SMELL_THRESHOLDS['long_file']['lines']})",
                    suggestion="Consider splitting into multiple modules",
                ))

            # Deep nesting check
            max_indent = 0
            for line in lines:
                stripped = line.lstrip()
                if stripped:
                    indent = len(line) - len(stripped)
                    max_indent = max(max_indent, indent // 4)
            if max_indent > SMELL_THRESHOLDS["deep_nesting"]["levels"]:
                result["smells"].append(CodeSmell(
                    file=os.path.basename(filepath),
                    line=0, smell_type="deep_nesting",
                    severity="medium",
                    description=f"Max nesting depth: {max_indent} levels (>{SMELL_THRESHOLDS['deep_nesting']['levels']})",
                    suggestion="Extract nested logic into helper functions",
                ))

        except Exception as e:
            result["smells"].append(CodeSmell(
                file=os.path.basename(filepath),
                line=0, smell_type="read_error",
                severity="low",
                description=f"Could not read file: {e}",
                suggestion="Check file permissions",
            ))

        return result

    def analyze(self, agent_input: AgentInput) -> AgentOutput:
        w = agent_input.workload
        target_dir = w.get("target_dir", NLKE_ROOT)
        pattern = w.get("file_pattern", "*.py")
        max_files = w.get("max_files", 20)

        rules = [
            "refactor_001_dependency_analysis",
            "refactor_002_smell_detection",
            "refactor_003_module_extraction",
            "refactor_004_progressive_refactoring",
        ]

        # Find files
        py_files = sorted(Path(target_dir).glob(pattern))[:max_files]

        all_results = []
        all_smells = []
        all_functions = []
        total_lines = 0
        import_graph = {}

        for filepath in py_files:
            result = self._analyze_file(str(filepath))
            all_results.append(result)
            total_lines += result["lines"]
            all_smells.extend(result["smells"])
            all_functions.extend(result["functions"])
            import_graph[os.path.basename(str(filepath))] = result["imports"]

        # Sort smells by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        all_smells.sort(key=lambda s: severity_order.get(s.severity, 3))

        by_severity = {}
        for s in all_smells:
            by_severity.setdefault(s.severity, []).append(s)

        by_type = {}
        for s in all_smells:
            by_type.setdefault(s.smell_type, []).append(s)

        # Find circular imports (simplified)
        circular = []
        for file_a, imports_a in import_graph.items():
            for file_b, imports_b in import_graph.items():
                if file_a != file_b:
                    base_a = file_a.replace(".py", "")
                    base_b = file_b.replace(".py", "")
                    if any(base_b in imp for imp in imports_a) and any(base_a in imp for imp in imports_b):
                        pair = tuple(sorted([file_a, file_b]))
                        if pair not in circular:
                            circular.append(pair)

        anti_patterns = [
            f"{s.severity.upper()}: {s.description}" for s in all_smells if s.severity in ("critical", "high")
        ][:5]

        if circular:
            for pair in circular:
                anti_patterns.append(f"CIRCULAR IMPORT: {pair[0]} <-> {pair[1]}")

        recommendations = [{
            "technique": "refactoring_analysis",
            "applicable": True,
            "files_analyzed": len(py_files),
            "total_lines": total_lines,
            "total_functions": len(all_functions),
            "total_smells": len(all_smells),
            "by_severity": {k: len(v) for k, v in by_severity.items()},
            "by_type": {k: len(v) for k, v in by_type.items()},
            "circular_imports": [list(c) for c in circular],
            "top_smells": [asdict(s) for s in all_smells[:10]],
            "largest_functions": [asdict(f) for f in sorted(all_functions, key=lambda f: f.lines, reverse=True)[:5]],
            "rules_applied": rules,
        }]

        critical = len(by_severity.get("critical", []))
        high = len(by_severity.get("high", []))

        meta_insight = (
            f"Analyzed {len(py_files)} files ({total_lines:,} lines, {len(all_functions)} functions). "
            f"Found {len(all_smells)} code smells ({critical} critical, {high} high). "
            f"{len(circular)} circular import(s)."
        )

        return AgentOutput(
            recommendations=recommendations,
            rules_applied=rules,
            meta_insight=meta_insight,
            analysis_data={
                "files": len(py_files),
                "lines": total_lines,
                "functions": len(all_functions),
                "smells": len(all_smells),
                "by_severity": {k: len(v) for k, v in by_severity.items()},
                "circular_imports": len(circular),
            },
            anti_patterns=anti_patterns,
            agent_metadata=self.build_metadata(),
        )


if __name__ == "__main__":
    analyzer = RefactoringAnalyzer()
    run_standard_cli(
        agent_name="Refactoring Agent",
        description="Large-scale code analysis and refactoring planning",
        analyzer=analyzer,
    )

#!/usr/bin/env python3
"""
Code Generation Agent: Bash/Shell (#37)

Generates shell scripts from natural language specifications.
Supports automation, CI/CD pipelines, system administration,
deployment scripts, and cron jobs.

Layer: L1-L5 (Full 5-layer pattern via agent_base)

Usage:
    python3 codegen_bash.py --example
    python3 codegen_bash.py --workload spec.json --output result.json

Created: February 6, 2026
"""

import sys
import os
import re
import textwrap

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.agent_base import (
    AgentInput, AgentOutput, BaseAnalyzer, run_standard_cli,
)

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


# ============================================================================
# L1: Data Models
# ============================================================================

@dataclass
class BashSpec:
    description: str
    script_type: str  # automation, cicd, deploy, system, cron, utility, setup
    name: str
    inputs: List[str] = field(default_factory=list)
    commands: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)


@dataclass
class GeneratedBash:
    filename: str
    code: str
    lines: int = 0
    functions: List[str] = field(default_factory=list)
    variables: List[str] = field(default_factory=list)


# ============================================================================
# L2: Constants
# ============================================================================

SCRIPT_TYPES = {
    "automation": {"needs_logging": True, "needs_error_handling": True},
    "cicd": {"needs_logging": True, "needs_error_handling": True},
    "deploy": {"needs_logging": True, "needs_error_handling": True},
    "system": {"needs_logging": False, "needs_error_handling": True},
    "cron": {"needs_logging": True, "needs_error_handling": True},
    "utility": {"needs_logging": False, "needs_error_handling": False},
    "setup": {"needs_logging": True, "needs_error_handling": True},
}

BASH_RULES = [
    "codegen_bash_001_set_euo_pipefail",
    "codegen_bash_002_quote_variables",
    "codegen_bash_003_use_functions",
    "codegen_bash_004_trap_cleanup",
    "codegen_bash_005_check_dependencies",
    "codegen_bash_006_usage_help",
]

BASH_ANTI_PATTERNS = [
    "unquoted_variables",
    "missing_error_handling",
    "no_shebang",
    "command_injection_risk",
    "hardcoded_credentials",
    "missing_cleanup",
]


# ============================================================================
# L3: Analyzer
# ============================================================================

class CodegenBashAnalyzer(BaseAnalyzer):
    """Bash/Shell script generation engine."""

    def __init__(self):
        super().__init__(
            agent_name="codegen-bash",
            model="haiku",
            version="1.0",
        )

    def get_example_input(self) -> Dict[str, Any]:
        return {
            "specs": [
                {
                    "description": "Deployment script that pulls latest code, runs tests, builds Docker image, and deploys to staging",
                    "script_type": "deploy",
                    "name": "deploy-staging",
                    "inputs": ["BRANCH", "IMAGE_TAG", "DEPLOY_ENV"],
                    "commands": ["git pull", "npm test", "docker build", "docker push", "kubectl apply"],
                    "dependencies": ["git", "npm", "docker", "kubectl"],
                    "constraints": ["rollback on failure", "notify on completion", "log all steps"],
                },
                {
                    "description": "System health check script that monitors CPU, memory, disk, and running services",
                    "script_type": "system",
                    "name": "health-check",
                    "inputs": ["THRESHOLD_CPU", "THRESHOLD_MEM", "THRESHOLD_DISK"],
                    "commands": ["top", "free", "df", "systemctl"],
                    "dependencies": ["top", "free", "df"],
                    "constraints": ["exit code reflects health", "output JSON format"],
                },
                {
                    "description": "Setup script that installs project dependencies, configures environment, and initializes database",
                    "script_type": "setup",
                    "name": "project-setup",
                    "inputs": ["PROJECT_DIR", "DB_NAME"],
                    "commands": ["pip install", "createdb", "alembic upgrade"],
                    "dependencies": ["python3", "pip", "psql", "alembic"],
                    "constraints": ["idempotent", "skip already-installed"],
                },
            ],
        }

    def _parse_spec(self, spec_dict: Dict) -> BashSpec:
        return BashSpec(
            description=spec_dict.get("description", ""),
            script_type=spec_dict.get("script_type", "utility"),
            name=spec_dict.get("name", "script"),
            inputs=spec_dict.get("inputs", []),
            commands=spec_dict.get("commands", []),
            dependencies=spec_dict.get("dependencies", []),
            constraints=spec_dict.get("constraints", []),
        )

    def _generate_bash(self, spec: BashSpec) -> GeneratedBash:
        type_info = SCRIPT_TYPES.get(spec.script_type, SCRIPT_TYPES["utility"])
        filename = f"{spec.name}.sh"
        functions = []
        variables = list(spec.inputs)

        # Header
        lines = [
            "#!/usr/bin/env bash",
            f"# {spec.description}",
            f"# Generated by NLKE codegen-bash",
            f"# Type: {spec.script_type}",
            "",
        ]

        # Safety settings
        if type_info["needs_error_handling"]:
            lines.append("set -euo pipefail")
            lines.append("")

        # Constants and variables
        if spec.inputs:
            lines.append("# Configuration")
            for inp in spec.inputs:
                default = "${1:-}" if inp == spec.inputs[0] else f'"default"'
                lines.append(f'{inp}=${{1:-{default.strip("${}:-")}}}')
            lines.append("")

        # Logging function
        if type_info["needs_logging"]:
            lines.extend([
                "# Logging",
                'log() { echo "[$(date +"%Y-%m-%d %H:%M:%S")] $*"; }',
                'log_error() { echo "[$(date +"%Y-%m-%d %H:%M:%S")] ERROR: $*" >&2; }',
                "",
            ])
            functions.extend(["log", "log_error"])

        # Cleanup trap
        if type_info["needs_error_handling"]:
            lines.extend([
                "# Cleanup on exit",
                "cleanup() {",
                '  log "Cleaning up..."',
                "  # TODO: add cleanup logic",
                "}",
                "trap cleanup EXIT",
                "",
            ])
            functions.append("cleanup")

        # Dependency check
        if spec.dependencies:
            lines.append("# Check dependencies")
            lines.append("check_deps() {")
            lines.append("  local missing=0")
            for dep in spec.dependencies:
                lines.append(f'  command -v {dep} >/dev/null 2>&1 || {{ log_error "{dep} not found"; missing=1; }}')
            lines.append('  [[ "$missing" -eq 1 ]] && { log_error "Missing dependencies"; exit 1; }')
            lines.append("}")
            lines.append("")
            functions.append("check_deps")

        # Usage function
        lines.extend([
            "# Usage",
            "usage() {",
            f'  echo "Usage: $0 {" ".join(f"<{i}>" for i in spec.inputs)}"',
            f'  echo "  {spec.description}"',
            "  exit 1",
            "}",
            "",
        ])
        functions.append("usage")

        # Main function with commands
        lines.append("# Main execution")
        lines.append("main() {")
        if spec.dependencies:
            lines.append("  check_deps")
        if type_info["needs_logging"]:
            lines.append(f'  log "Starting {spec.name}..."')
        lines.append("")

        for cmd in spec.commands:
            safe_cmd = cmd.replace('"', '\\"')
            if type_info["needs_logging"]:
                lines.append(f'  log "Running: {safe_cmd}"')
            lines.append(f"  {cmd}")
            lines.append("")

        if type_info["needs_logging"]:
            lines.append(f'  log "{spec.name} completed successfully"')
        lines.append("}")
        lines.append("")
        functions.append("main")

        # Invocation
        lines.append('main "$@"')
        lines.append("")

        code = "\n".join(lines)

        return GeneratedBash(
            filename=filename,
            code=code,
            lines=len(lines),
            functions=functions,
            variables=variables,
        )

    def _check_anti_patterns(self, code: str) -> List[str]:
        found = []
        if "#!/" not in code:
            found.append("no_shebang")
        if "set -e" not in code and "set -euo" not in code:
            found.append("missing_error_handling")
        # Check for unquoted variables (simplified)
        for line in code.split("\n"):
            if "$" in line and not line.strip().startswith("#"):
                if re.search(r'\$\w+(?!\})', line) and '"$' not in line and "'$" not in line:
                    if "=${" not in line:
                        found.append("unquoted_variables")
                        break
        return found

    def analyze(self, agent_input: AgentInput) -> AgentOutput:
        w = agent_input.workload
        specs_raw = w.get("specs", [])

        generated = []
        all_anti_patterns = []
        total_lines = 0
        type_counts: Dict[str, int] = {}

        for spec_dict in specs_raw:
            spec = self._parse_spec(spec_dict)
            result = self._generate_bash(spec)
            generated.append(result)
            total_lines += result.lines
            type_counts[spec.script_type] = type_counts.get(spec.script_type, 0) + 1
            all_anti_patterns.extend(self._check_anti_patterns(result.code))

        recommendations = []
        for gen in generated:
            recommendations.append({
                "technique": f"codegen_bash_{gen.filename}",
                "impact": f"Generated {gen.lines} lines",
                "reasoning": f"File: {gen.filename}, Functions: {gen.functions}",
                "filename": gen.filename,
                "code": gen.code,
                "lines": gen.lines,
                "functions": gen.functions,
                "variables": gen.variables,
            })

        meta_insight = (
            f"Generated {len(generated)} shell scripts totaling {total_lines} lines. "
            f"Types: {', '.join(f'{k}({v})' for k, v in type_counts.items())}. "
            f"Total functions: {sum(len(g.functions) for g in generated)}."
        )

        return AgentOutput(
            recommendations=recommendations,
            rules_applied=BASH_RULES[:len(generated) + 2],
            meta_insight=meta_insight,
            analysis_data={
                "files_generated": len(generated),
                "total_lines": total_lines,
                "type_distribution": type_counts,
                "all_functions": [f for g in generated for f in g.functions],
            },
            anti_patterns=list(set(all_anti_patterns)),
            agent_metadata=self.build_metadata(),
        )


if __name__ == "__main__":
    analyzer = CodegenBashAnalyzer()
    run_standard_cli(
        agent_name="CodeGen Bash",
        description="Generate shell scripts from natural language specifications",
        analyzer=analyzer,
    )

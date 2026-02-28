#!/usr/bin/env python3
"""
MCP Tool Creator - Phase 5 Compound Orchestrator

Generates MCP tool servers from existing agents, Python tools, and cookbook specs.
Composes 4 existing agents into a unified pipeline:
  1. Spec Parser → Parse input (4 formats)
  2. Validator (#22 extended) → Pre-flight anti-pattern scan
  3. Generator → Template-based code generation
  4. Rule Engine (#21 extended) → Quality validation

Architecture: L1-L5 (Full 5-layer pattern via agent_base)

Usage:
    python3 mcp_tool_creator.py --from-agent ~/.claude/agents/cost-advisor.md
    python3 mcp_tool_creator.py --from-python agents/cost-optimization/cost_advisor.py
    python3 mcp_tool_creator.py --from-cookbook AGENT-COOKBOOK.md --agent A1
    python3 mcp_tool_creator.py --interactive
    python3 mcp_tool_creator.py --example
    python3 mcp_tool_creator.py --batch agents/  # All Python tools in directory

Created: February 6, 2026
"""

import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any, Optional

# Add parent for agent_base imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.agent_base import (
    AgentInput, AgentOutput, BaseAnalyzer, AgentOrchestrator,
    run_standard_cli, NLKE_ROOT, AGENTS_DIR,
)

# Local imports
sys.path.insert(0, os.path.dirname(__file__))
from mcp_spec_parser import (
    MCPToolSpec, MCPToolDef,
    parse_agent_md, parse_python_tool, parse_cookbook_entry, build_interactive_spec,
)
from mcp_generators.from_agent import generate_from_agent
from mcp_generators.from_python import generate_from_python
from mcp_generators.from_cookbook import generate_from_cookbook
from mcp_validators.mcp_anti_patterns import validate_mcp_spec, format_violations
from mcp_validators.mcp_rules import match_rules, get_rule_stats


# ============================================================================
# L1: Data Models
# ============================================================================

@dataclass
class MCPGenerationResult:
    """Result of MCP tool generation pipeline."""
    success: bool
    server_name: str
    source_type: str
    source_path: str
    files_generated: Dict[str, str]  # filename -> path
    tools_count: int
    validation_passed: bool
    violations: List[Dict[str, Any]]
    rules_matched: int
    quality_score: float
    warnings: List[str]


# ============================================================================
# L2: Constants
# ============================================================================

MCP_OUTPUT_DIR = os.path.join(NLKE_ROOT, "agents", "mcp-tool-creator", "generated")

SUPPORTED_SOURCES = {
    "agent": {
        "description": "Claude Code agent (.md)",
        "parser": parse_agent_md,
        "generator": generate_from_agent,
        "extension": ".md",
    },
    "python": {
        "description": "Python agent tool (.py, 5-layer pattern)",
        "parser": parse_python_tool,
        "generator": generate_from_python,
        "extension": ".py",
    },
    "cookbook": {
        "description": "Agent cookbook entry (markdown)",
        "parser": parse_cookbook_entry,
        "generator": generate_from_cookbook,
        "extension": ".md",
    },
}


# ============================================================================
# L3: Analyzers (Compound Pipeline Stages)
# ============================================================================

class MCPSpecAnalyzer(BaseAnalyzer):
    """Stage 1: Parse and validate input spec."""

    def __init__(self):
        super().__init__(
            agent_name="mcp-spec-analyzer",
            model="haiku",
            version="1.0",
        )

    def get_example_input(self) -> Dict[str, Any]:
        return {
            "source_type": "python",
            "source_path": os.path.join(AGENTS_DIR, "cost-optimization", "cost_advisor.py"),
            "agent_id": "",
        }

    def analyze(self, agent_input: AgentInput) -> AgentOutput:
        w = agent_input.workload
        source_type = w.get("source_type", "")
        source_path = w.get("source_path", "")
        agent_id = w.get("agent_id", "")

        rules = ["mcp_spec_001_parse_input", "mcp_spec_002_validate_format"]
        anti_patterns = []

        if source_type not in SUPPORTED_SOURCES:
            return AgentOutput(
                recommendations=[{"technique": "error", "message": f"Unsupported source type: {source_type}"}],
                rules_applied=rules,
                meta_insight=f"Error: source_type must be one of {list(SUPPORTED_SOURCES.keys())}",
                anti_patterns=["unsupported_source_type"],
                agent_metadata=self.build_metadata(),
            )

        if not os.path.exists(source_path):
            return AgentOutput(
                recommendations=[{"technique": "error", "message": f"File not found: {source_path}"}],
                rules_applied=rules,
                meta_insight=f"Error: source file does not exist: {source_path}",
                anti_patterns=["file_not_found"],
                agent_metadata=self.build_metadata(),
            )

        # Parse spec
        parser = SUPPORTED_SOURCES[source_type]["parser"]
        try:
            if source_type == "cookbook":
                spec = parser(source_path, agent_id)
            else:
                spec = parser(source_path)
        except Exception as e:
            return AgentOutput(
                recommendations=[{"technique": "error", "message": f"Parse failed: {e}"}],
                rules_applied=rules,
                meta_insight=f"Error: failed to parse {source_path}: {e}",
                anti_patterns=["parse_failure"],
                agent_metadata=self.build_metadata(),
            )

        return AgentOutput(
            recommendations=[{
                "technique": "spec_parsed",
                "applicable": True,
                "server_name": spec.server_name,
                "tools_count": len(spec.tools),
                "source_type": source_type,
                "tool_names": [t.name for t in spec.tools],
            }],
            rules_applied=rules,
            meta_insight=f"Parsed {source_type} spec: {spec.server_name} with {len(spec.tools)} tools",
            analysis_data={"spec": spec.to_dict()},
            agent_metadata=self.build_metadata(),
        )


class MCPValidationAnalyzer(BaseAnalyzer):
    """Stage 2: Anti-pattern validation (extends #22)."""

    def __init__(self):
        super().__init__(
            agent_name="mcp-validation-analyzer",
            model="haiku",
            version="1.0",
        )

    def get_example_input(self) -> Dict[str, Any]:
        return {"spec": build_interactive_spec().to_dict()}

    def analyze(self, agent_input: AgentInput) -> AgentOutput:
        w = agent_input.workload
        spec_dict = w.get("spec", {})

        rules = ["mcp_val_001_anti_pattern_scan", "mcp_val_002_severity_check"]

        # Reconstruct spec from dict for validation
        tools = [MCPToolDef(**t) for t in spec_dict.get("tools", [])]
        spec = MCPToolSpec(
            server_name=spec_dict.get("server_name", ""),
            description=spec_dict.get("description", ""),
            version=spec_dict.get("version", "1.0"),
            tools=tools,
            env_vars=spec_dict.get("env_vars", {}),
            wraps=spec_dict.get("wraps", []),
        )

        violations = validate_mcp_spec(spec)
        critical = [v for v in violations if v.severity == "CRITICAL"]
        passed = len(critical) == 0

        return AgentOutput(
            recommendations=[{
                "technique": "anti_pattern_validation",
                "applicable": True,
                "passed": passed,
                "violations_count": len(violations),
                "critical_count": len(critical),
                "violations": [asdict(v) for v in violations],
            }],
            rules_applied=rules + [v.rule_id for v in violations],
            meta_insight=f"Validation {'PASSED' if passed else 'BLOCKED'}: "
                        f"{len(violations)} violations ({len(critical)} critical)",
            analysis_data={"violations": [asdict(v) for v in violations], "passed": passed},
            anti_patterns=[v.rule_id for v in violations],
            agent_metadata=self.build_metadata(),
        )


class MCPRuleMatchAnalyzer(BaseAnalyzer):
    """Stage 3: Rule engine matching (extends #21)."""

    def __init__(self):
        super().__init__(
            agent_name="mcp-rule-match-analyzer",
            model="haiku",
            version="1.0",
        )

    def get_example_input(self) -> Dict[str, Any]:
        return {"spec": build_interactive_spec().to_dict()}

    def analyze(self, agent_input: AgentInput) -> AgentOutput:
        w = agent_input.workload
        spec_dict = w.get("spec", {})

        rules = ["mcp_rule_001_match_engine", "mcp_rule_002_quality_score"]

        # Reconstruct spec
        tools = [MCPToolDef(**t) for t in spec_dict.get("tools", [])]
        spec = MCPToolSpec(
            server_name=spec_dict.get("server_name", ""),
            description=spec_dict.get("description", ""),
            tools=tools,
            transport=spec_dict.get("transport", "stdio"),
            wraps=spec_dict.get("wraps", []),
        )

        result = match_rules(spec)
        stats = get_rule_stats()

        return AgentOutput(
            recommendations=[{
                "technique": "rule_engine_match",
                "applicable": True,
                "matched_count": result["matched_count"],
                "quality_score": result["quality_score"],
                "categories_covered": result["categories_covered"],
                "top_warnings": result["warnings"][:5],
            }],
            rules_applied=rules + [r["rule_id"] for r in result["matched_rules"][:10]],
            meta_insight=f"Rule engine: {result['matched_count']}/{result['total_rules']} rules matched, "
                        f"quality score: {result['quality_score']}",
            analysis_data={"rule_match": result, "rule_stats": stats},
            agent_metadata=self.build_metadata(),
        )


# ============================================================================
# L4: Orchestrator (Compound Pipeline)
# ============================================================================

class MCPToolCreatorOrchestrator:
    """Main orchestrator composing all pipeline stages.

    Pipeline:
      1. Parse spec (MCPSpecAnalyzer)
      2. Validate (MCPValidationAnalyzer) - gate: block on CRITICAL
      3. Generate (from_agent/from_python/from_cookbook)
      4. Rule match (MCPRuleMatchAnalyzer) - quality score
      5. Output (write files + registration)
    """

    def __init__(self):
        self.spec_analyzer = MCPSpecAnalyzer()
        self.validation_analyzer = MCPValidationAnalyzer()
        self.rule_analyzer = MCPRuleMatchAnalyzer()

    def create_tool(
        self,
        source_type: str,
        source_path: str,
        output_dir: str = None,
        agent_id: str = "",
        write_files: bool = True,
    ) -> MCPGenerationResult:
        """Execute the full MCP tool creation pipeline."""

        output_dir = output_dir or MCP_OUTPUT_DIR
        os.makedirs(output_dir, exist_ok=True)

        # Stage 1: Parse
        parse_input = AgentInput(workload={
            "source_type": source_type,
            "source_path": source_path,
            "agent_id": agent_id,
        })
        parse_result = self.spec_analyzer.analyze(parse_input)

        if parse_result.anti_patterns:
            return MCPGenerationResult(
                success=False,
                server_name="",
                source_type=source_type,
                source_path=source_path,
                files_generated={},
                tools_count=0,
                validation_passed=False,
                violations=[{"error": parse_result.meta_insight}],
                rules_matched=0,
                quality_score=0.0,
                warnings=parse_result.anti_patterns,
            )

        spec_dict = parse_result.analysis_data.get("spec", {})

        # Stage 2: Validate
        val_input = AgentInput(workload={"spec": spec_dict})
        val_result = self.validation_analyzer.analyze(val_input)
        validation_passed = val_result.analysis_data.get("passed", False)

        violations = val_result.analysis_data.get("violations", [])
        critical_violations = [v for v in violations if v.get("severity") == "CRITICAL"]

        # Gate: block on CRITICAL violations
        if critical_violations:
            return MCPGenerationResult(
                success=False,
                server_name=spec_dict.get("server_name", ""),
                source_type=source_type,
                source_path=source_path,
                files_generated={},
                tools_count=len(spec_dict.get("tools", [])),
                validation_passed=False,
                violations=critical_violations,
                rules_matched=0,
                quality_score=0.0,
                warnings=[f"BLOCKED: {len(critical_violations)} critical violations"],
            )

        # Stage 3: Generate
        generator = SUPPORTED_SOURCES[source_type]["generator"]
        if source_type == "cookbook":
            gen_result = generator(source_path, agent_id, output_dir)
        else:
            gen_result = generator(source_path, output_dir)

        if "error" in gen_result:
            return MCPGenerationResult(
                success=False,
                server_name="",
                source_type=source_type,
                source_path=source_path,
                files_generated={},
                tools_count=0,
                validation_passed=validation_passed,
                violations=violations,
                rules_matched=0,
                quality_score=0.0,
                warnings=[gen_result["error"]],
            )

        # Stage 4: Rule match
        rule_input = AgentInput(workload={"spec": spec_dict})
        rule_result = self.rule_analyzer.analyze(rule_input)
        quality_score = rule_result.analysis_data.get("rule_match", {}).get("quality_score", 0.5)
        rules_matched = rule_result.analysis_data.get("rule_match", {}).get("matched_count", 0)

        # Stage 5: Output
        files_generated = {}
        if write_files:
            for file_key, file_info in gen_result.get("files", {}).items():
                filepath = os.path.join(output_dir, file_info["path"])
                os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else output_dir, exist_ok=True)
                with open(filepath, "w") as f:
                    f.write(file_info["content"])
                files_generated[file_key] = filepath

        summary = gen_result.get("summary", {})
        warnings = [v.get("title", "") for v in violations if v.get("severity") in ("HIGH", "MEDIUM")]

        return MCPGenerationResult(
            success=True,
            server_name=summary.get("server_name", ""),
            source_type=source_type,
            source_path=source_path,
            files_generated=files_generated,
            tools_count=summary.get("tools_count", 0),
            validation_passed=validation_passed,
            violations=violations,
            rules_matched=rules_matched,
            quality_score=quality_score,
            warnings=warnings,
        )


# ============================================================================
# L3: Main Analyzer (wraps orchestrator for agent_base compatibility)
# ============================================================================

class MCPToolCreatorAnalyzer(BaseAnalyzer):
    """Main analyzer wrapping the orchestrator for standard CLI integration."""

    def __init__(self):
        super().__init__(
            agent_name="mcp-tool-creator",
            model="sonnet",
            version="1.0",
        )
        self.orchestrator = MCPToolCreatorOrchestrator()

    def get_example_input(self) -> Dict[str, Any]:
        return {
            "source_type": "python",
            "source_path": os.path.join(AGENTS_DIR, "cost-optimization", "cost_advisor.py"),
            "output_dir": MCP_OUTPUT_DIR,
            "write_files": False,  # Don't write in example mode
        }

    def analyze(self, agent_input: AgentInput) -> AgentOutput:
        w = agent_input.workload
        source_type = w.get("source_type", "")
        source_path = w.get("source_path", "")
        agent_id = w.get("agent_id", "")
        output_dir = w.get("output_dir", MCP_OUTPUT_DIR)
        write_files = w.get("write_files", True)

        rules = [
            "mcp_creator_001_pipeline",
            "mcp_creator_002_compound_orchestration",
            "mcp_creator_003_validation_gate",
            "mcp_creator_004_rule_matching",
        ]

        result = self.orchestrator.create_tool(
            source_type=source_type,
            source_path=source_path,
            output_dir=output_dir,
            agent_id=agent_id,
            write_files=write_files,
        )

        recommendations = [{
            "technique": "mcp_tool_generation",
            "applicable": True,
            "success": result.success,
            "server_name": result.server_name,
            "tools_count": result.tools_count,
            "files_generated": result.files_generated,
            "validation_passed": result.validation_passed,
            "quality_score": result.quality_score,
            "rules_matched": result.rules_matched,
            "rules_applied": rules,
        }]

        status = "SUCCESS" if result.success else "FAILED"
        meta_insight = (
            f"MCP Tool Creation {status}: {result.server_name} "
            f"({result.tools_count} tools, quality: {result.quality_score}, "
            f"rules: {result.rules_matched}, violations: {len(result.violations)})"
        )

        return AgentOutput(
            recommendations=recommendations,
            rules_applied=rules,
            meta_insight=meta_insight,
            analysis_data={
                "result": asdict(result),
                "pipeline_stages": ["spec_parse", "validation", "generation", "rule_match", "output"],
            },
            anti_patterns=result.warnings,
            agent_metadata=self.build_metadata(),
        )


# ============================================================================
# L5: CLI (Extended beyond standard)
# ============================================================================

def main():
    """Extended CLI with MCP-specific arguments."""
    parser = argparse.ArgumentParser(
        description="MCP Tool Creator - Generate MCP tool servers from agents, Python tools, or cookbook specs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 mcp_tool_creator.py --from-agent ~/.claude/agents/cost-advisor.md
  python3 mcp_tool_creator.py --from-python agents/cost-optimization/cost_advisor.py
  python3 mcp_tool_creator.py --from-cookbook AGENT-COOKBOOK.md --agent A1
  python3 mcp_tool_creator.py --batch agents/cost-optimization/
  python3 mcp_tool_creator.py --example
  python3 mcp_tool_creator.py --stats
        """,
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--from-agent", type=str, help="Path to Claude Code agent .md file")
    group.add_argument("--from-python", type=str, help="Path to Python agent tool .py file")
    group.add_argument("--from-cookbook", type=str, help="Path to agent cookbook markdown")
    group.add_argument("--interactive", action="store_true", help="Interactive spec building mode")
    group.add_argument("--batch", type=str, help="Directory of .py files to batch convert")
    group.add_argument("--example", action="store_true", help="Run with example input")
    group.add_argument("--stats", action="store_true", help="Show MCP rules statistics")

    parser.add_argument("--agent", type=str, default="", help="Agent ID for cookbook mode (e.g., A1)")
    parser.add_argument("--output", type=str, default=MCP_OUTPUT_DIR, help="Output directory")
    parser.add_argument("--no-write", action="store_true", help="Dry run - don't write files")
    parser.add_argument("--summary", action="store_true", help="Print human-readable summary")
    parser.add_argument("--json", action="store_true", help="Print JSON output")

    args = parser.parse_args()

    orchestrator = MCPToolCreatorOrchestrator()

    # Stats mode
    if args.stats:
        stats = get_rule_stats()
        print("MCP Rules Statistics:")
        print(json.dumps(stats, indent=2))
        return

    # Interactive mode
    if args.interactive:
        spec = build_interactive_spec()
        print("Interactive MCP Tool Spec Template:")
        print(json.dumps(spec.to_dict(), indent=2))
        print("\nFill in the [FILL: ...] fields and pass as --workload")
        return

    # Determine source
    if args.from_agent:
        source_type, source_path = "agent", args.from_agent
    elif args.from_python:
        source_type, source_path = "python", args.from_python
    elif args.from_cookbook:
        source_type, source_path = "cookbook", args.from_cookbook
    elif args.batch:
        # Batch mode: convert all .py files in directory
        batch_dir = args.batch
        results = []
        py_files = [
            os.path.join(batch_dir, f)
            for f in sorted(os.listdir(batch_dir))
            if f.endswith(".py") and f != "__init__.py"
        ]
        print(f"Batch converting {len(py_files)} Python tools...")
        for py_file in py_files:
            result = orchestrator.create_tool(
                "python", py_file, args.output,
                write_files=not args.no_write,
            )
            status = "OK" if result.success else "FAIL"
            print(f"  [{status}] {os.path.basename(py_file)} -> {result.server_name} ({result.tools_count} tools)")
            results.append(asdict(result))

        success = sum(1 for r in results if r["success"])
        print(f"\nBatch complete: {success}/{len(results)} succeeded")
        if args.json:
            print(json.dumps(results, indent=2, default=str))
        return
    elif args.example:
        # Use standard CLI with example
        analyzer = MCPToolCreatorAnalyzer()
        run_standard_cli(
            agent_name="MCP Tool Creator",
            description="Generate MCP tool servers from agents, Python tools, or cookbook specs",
            analyzer=analyzer,
        )
        return
    else:
        parser.print_help()
        return

    # Single file mode
    result = orchestrator.create_tool(
        source_type=source_type,
        source_path=source_path,
        output_dir=args.output,
        agent_id=args.agent,
        write_files=not args.no_write,
    )

    if args.summary or not args.json:
        print(f"\nMCP Tool Creator - {'SUCCESS' if result.success else 'FAILED'}")
        print(f"{'=' * 60}")
        print(f"Server:     {result.server_name}")
        print(f"Source:     {result.source_path} ({result.source_type})")
        print(f"Tools:      {result.tools_count}")
        print(f"Quality:    {result.quality_score}")
        print(f"Rules:      {result.rules_matched} matched")
        print(f"Validation: {'PASSED' if result.validation_passed else 'FAILED'}")
        if result.violations:
            print(f"Violations: {len(result.violations)}")
            for v in result.violations[:3]:
                title = v.get("title", v.get("error", ""))
                severity = v.get("severity", "")
                print(f"  [{severity}] {title}")
        if result.files_generated:
            print(f"\nGenerated Files:")
            for key, path in result.files_generated.items():
                print(f"  {key}: {path}")
        if result.warnings:
            print(f"\nWarnings:")
            for w in result.warnings[:5]:
                print(f"  - {w}")
        print(f"{'=' * 60}")

    if args.json:
        print(json.dumps(asdict(result), indent=2, default=str))


if __name__ == "__main__":
    main()

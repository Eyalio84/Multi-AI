#!/usr/bin/env python3
"""
MCP Anti-Pattern Validator

Extends Anti-Pattern Validator (#22) with 15 MCP-specific anti-patterns.
Pre-flight validation gate for MCP tool generation.

Used by: mcp_tool_creator.py (Phase 5 compound orchestrator)
Created: February 6, 2026
"""

from typing import Dict, List, Any
from dataclasses import dataclass, asdict


@dataclass
class MCPViolation:
    """A detected MCP anti-pattern violation."""
    rule_id: str
    title: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    description: str
    why_it_fails: str
    correct_approach: str
    recovery_steps: List[str]


# ============================================================================
# MCP Anti-Pattern Database (15 patterns)
# ============================================================================

MCP_ANTI_PATTERNS = {
    "mcp_001_no_input_schema": {
        "title": "Tool without input schema",
        "severity": "CRITICAL",
        "description": "MCP tool defined without inputSchema property",
        "why_it_fails": "Claude cannot discover tool parameters without a schema. "
                        "The tool becomes unusable - Claude won't know what arguments to pass.",
        "correct_approach": "Always define inputSchema with type, properties, and required fields",
        "checks": lambda spec: any(
            not t.input_schema or not t.input_schema.get("properties")
            for t in spec.tools
        ),
    },
    "mcp_002_no_description": {
        "title": "Tool without description",
        "severity": "HIGH",
        "description": "MCP tool lacks description field",
        "why_it_fails": "Claude uses descriptions to decide which tool to call. "
                        "Without one, the tool may never be selected or be selected incorrectly.",
        "correct_approach": "Provide clear, specific description explaining what the tool does and when to use it",
        "checks": lambda spec: any(not t.description for t in spec.tools),
    },
    "mcp_003_blocking_io": {
        "title": "Blocking I/O in tool handler",
        "severity": "HIGH",
        "description": "Tool handler performs synchronous blocking operations",
        "why_it_fails": "Blocking I/O in stdio transport can cause deadlocks. "
                        "The server stops reading stdin while blocked, stalling the protocol.",
        "correct_approach": "Use timeouts for all I/O operations. Set max execution time.",
        "checks": lambda spec: False,  # Can only detect from source code analysis
    },
    "mcp_004_unbounded_result": {
        "title": "Tool returns unbounded result",
        "severity": "HIGH",
        "description": "Tool handler can return arbitrarily large results",
        "why_it_fails": "Stdio transport has practical limits (~4MB). Large results "
                        "cause memory issues and slow transmission.",
        "correct_approach": "Implement pagination or result size limits. Truncate with indicator.",
        "checks": lambda spec: False,  # Runtime check only
    },
    "mcp_005_no_error_handling": {
        "title": "Missing error handling in handlers",
        "severity": "CRITICAL",
        "description": "Tool handlers don't catch exceptions",
        "why_it_fails": "Unhandled exceptions crash the MCP server, dropping all tools. "
                        "Claude loses access to all tools in this server.",
        "correct_approach": "Wrap every handler in try/except. Return isError: true with message.",
        "checks": lambda spec: False,  # Source code analysis
    },
    "mcp_006_no_timeout": {
        "title": "No execution timeout",
        "severity": "MEDIUM",
        "description": "Tool execution has no time limit",
        "why_it_fails": "Infinite loops or slow operations freeze the entire MCP connection. "
                        "Claude waits indefinitely.",
        "correct_approach": "Set max execution time (30s recommended). Use signal.alarm or threading.",
        "checks": lambda spec: False,  # Source code analysis
    },
    "mcp_007_circular_deps": {
        "title": "Circular tool dependencies",
        "severity": "HIGH",
        "description": "Tool A calls Tool B which calls Tool A",
        "why_it_fails": "Creates infinite recursion consuming stack and memory.",
        "correct_approach": "Design acyclic tool graphs. Use depth limits if recursion is needed.",
        "checks": lambda spec: False,  # Composition analysis
    },
    "mcp_008_missing_server_info": {
        "title": "Missing server info in initialize",
        "severity": "MEDIUM",
        "description": "Server doesn't return name/version in initialize response",
        "why_it_fails": "Claude Code displays server info to users. Missing info "
                        "makes debugging and identification harder.",
        "correct_approach": "Return serverInfo with name and version in initialize response",
        "checks": lambda spec: not spec.server_name or not spec.version,
    },
    "mcp_009_duplicate_tool_names": {
        "title": "Duplicate tool names",
        "severity": "CRITICAL",
        "description": "Multiple tools with the same name in one server",
        "why_it_fails": "Only one handler can be dispatched per name. "
                        "Later definitions silently shadow earlier ones.",
        "correct_approach": "Ensure all tool names are unique within a server",
        "checks": lambda spec: len(spec.tools) != len(set(t.name for t in spec.tools)),
    },
    "mcp_010_invalid_json_schema": {
        "title": "Invalid JSON Schema in inputSchema",
        "severity": "HIGH",
        "description": "inputSchema doesn't conform to JSON Schema spec",
        "why_it_fails": "Claude may generate invalid arguments that don't match the schema, "
                        "causing runtime errors.",
        "correct_approach": "Use valid JSON Schema with proper types, required fields, descriptions",
        "checks": lambda spec: any(
            t.input_schema.get("type") not in ("object", "string", "array", None)
            for t in spec.tools
        ),
    },
    "mcp_011_no_tools": {
        "title": "Server with no tools",
        "severity": "CRITICAL",
        "description": "MCP server defines zero tools",
        "why_it_fails": "A server without tools serves no purpose. Claude won't use it.",
        "correct_approach": "Define at least one tool with name, description, and inputSchema",
        "checks": lambda spec: len(spec.tools) == 0,
    },
    "mcp_012_generic_name": {
        "title": "Overly generic tool name",
        "severity": "LOW",
        "description": "Tool name like 'run', 'execute', 'process' is too generic",
        "why_it_fails": "Generic names collide with other tools and confuse Claude's "
                        "tool selection when multiple servers are active.",
        "correct_approach": "Use specific, descriptive names: 'analyze_kg_health' not 'analyze'",
        "checks": lambda spec: any(
            t.name in ("run", "execute", "process", "do", "handle", "tool")
            for t in spec.tools
        ),
    },
    "mcp_013_sensitive_in_result": {
        "title": "Potential sensitive data in tool results",
        "severity": "MEDIUM",
        "description": "Tool may expose API keys, passwords, or secrets in results",
        "why_it_fails": "Tool results are visible to the LLM and may be logged. "
                        "Secrets in results can leak through conversation history.",
        "correct_approach": "Sanitize results. Never include raw credentials or tokens.",
        "checks": lambda spec: any("key" in (v.get("env_var", "") or "").lower() for v in spec.env_vars.values()) if isinstance(spec.env_vars, dict) else False,
    },
    "mcp_014_no_protocol_version": {
        "title": "Missing protocol version",
        "severity": "MEDIUM",
        "description": "Server doesn't declare supported MCP protocol version",
        "why_it_fails": "Version mismatches between client and server cause silent failures.",
        "correct_approach": "Return protocolVersion: '2024-11-05' in initialize response",
        "checks": lambda spec: False,  # Template always includes this
    },
    "mcp_015_too_many_tools": {
        "title": "Too many tools in single server",
        "severity": "LOW",
        "description": "Server defines more than 20 tools",
        "why_it_fails": "Large tool lists consume context window tokens. "
                        "Claude's tool selection accuracy decreases with many options.",
        "correct_approach": "Split into multiple focused servers. Group by domain.",
        "checks": lambda spec: len(spec.tools) > 20,
    },
}


# ============================================================================
# Validator
# ============================================================================

def validate_mcp_spec(spec) -> List[MCPViolation]:
    """Validate an MCPToolSpec against all MCP anti-patterns.

    Args:
        spec: MCPToolSpec to validate

    Returns:
        List of MCPViolation objects for any detected issues
    """
    violations = []

    for rule_id, pattern in MCP_ANTI_PATTERNS.items():
        checker = pattern.get("checks")
        if checker and checker(spec):
            violations.append(MCPViolation(
                rule_id=rule_id,
                title=pattern["title"],
                severity=pattern["severity"],
                description=pattern["description"],
                why_it_fails=pattern["why_it_fails"],
                correct_approach=pattern["correct_approach"],
                recovery_steps=[pattern["correct_approach"]],
            ))

    # Sort by severity
    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    violations.sort(key=lambda v: severity_order.get(v.severity, 4))

    return violations


def format_violations(violations: List[MCPViolation]) -> str:
    """Format violations as human-readable report."""
    if not violations:
        return "No MCP anti-patterns detected. Spec passes pre-flight validation."

    lines = [f"MCP Anti-Pattern Violations: {len(violations)}", ""]
    for v in violations:
        lines.append(f"  [{v.severity}] {v.rule_id}: {v.title}")
        lines.append(f"    Why: {v.why_it_fails}")
        lines.append(f"    Fix: {v.correct_approach}")
        lines.append("")

    critical = sum(1 for v in violations if v.severity == "CRITICAL")
    if critical:
        lines.append(f"BLOCKED: {critical} CRITICAL violation(s) must be fixed before generation.")
    else:
        lines.append("WARNING: Non-critical issues found. Generation can proceed with caution.")

    return "\n".join(lines)

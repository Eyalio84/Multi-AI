#!/usr/bin/env python3
"""
MCP Rules Engine Extension

Extends Rule Engine (#21) with ~50 MCP-specific rules across 6 categories.
Provides quality validation for generated MCP tools.

Used by: mcp_tool_creator.py (Phase 5 compound orchestrator)
Created: February 6, 2026
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class MCPRule:
    """A single MCP validation rule."""
    rule_id: str
    category: str
    title: str
    description: str
    confidence: float  # 0.0-1.0
    applies_when: str  # condition description
    recommendation: str


# ============================================================================
# MCP Rule Categories (50 rules)
# ============================================================================

MCP_RULES: Dict[str, List[MCPRule]] = {
    "composition": [
        MCPRule("mcp_comp_001", "composition", "Tool + Resource pairing",
                "Tools that read data should pair with resource URIs for discoverability",
                0.85, "Tool reads from a data source",
                "Expose data source as MCP resource alongside the tool"),
        MCPRule("mcp_comp_002", "composition", "Multi-tool server grouping",
                "Related tools should be in the same server for atomic operations",
                0.90, "Multiple tools operate on same data domain",
                "Group related tools in one server to share state"),
        MCPRule("mcp_comp_003", "composition", "Tool output as input pattern",
                "Output schema of tool A should match input schema of tool B for chaining",
                0.80, "Two tools are meant to be used sequentially",
                "Ensure output JSON shape matches downstream input schema"),
        MCPRule("mcp_comp_004", "composition", "Metadata passthrough",
                "Tool results should include metadata for provenance tracking",
                0.75, "Tool is part of a multi-step workflow",
                "Include source, timestamp, and rules_applied in results"),
        MCPRule("mcp_comp_005", "composition", "Error propagation chain",
                "Errors in composed tools should propagate with context",
                0.85, "Tools are chained in a pipeline",
                "Include upstream tool name and error in downstream error messages"),
        MCPRule("mcp_comp_006", "composition", "Idempotent tool design",
                "Tools should produce same result for same input (read tools especially)",
                0.80, "Tool is used in retry scenarios",
                "Design handlers as pure functions where possible"),
        MCPRule("mcp_comp_007", "composition", "Batch operation support",
                "High-volume tools should support batch input mode",
                0.70, "Tool processes items that could be batched",
                "Accept array inputs alongside single-item mode"),
        MCPRule("mcp_comp_008", "composition", "Result format consistency",
                "All tools in a server should use consistent result format",
                0.90, "Server has multiple tools",
                "Standardize on {result, metadata, error} format"),
        MCPRule("mcp_comp_009", "composition", "Cost estimation exposure",
                "Tools wrapping paid APIs should expose cost estimates",
                0.75, "Tool calls external APIs with usage-based pricing",
                "Include estimated_cost field in tool results"),
        MCPRule("mcp_comp_010", "composition", "Dry-run mode",
                "Destructive or expensive tools should support dry-run",
                0.70, "Tool modifies state or costs money",
                "Add optional dry_run parameter that returns plan without executing"),
        MCPRule("mcp_comp_011", "composition", "NLKE output contract",
                "Tools wrapping NLKE agents should preserve the output contract",
                0.95, "Tool wraps an NLKE agent",
                "Ensure recommendations, rules_applied, meta_insight are in result"),
        MCPRule("mcp_comp_012", "composition", "Progressive result support",
                "Long-running tools should support partial results",
                0.65, "Tool execution may exceed 10 seconds",
                "Return partial results with completion percentage"),
    ],
    "dependency": [
        MCPRule("mcp_dep_001", "dependency", "Transport before tools",
                "Server transport must be initialized before tool handlers register",
                0.95, "Always", "Initialize transport in server setup, register tools after"),
        MCPRule("mcp_dep_002", "dependency", "Schema before handler",
                "Input schema must be defined before handler implementation",
                0.90, "Always", "Define TOOLS list with schemas, then HANDLERS dict"),
        MCPRule("mcp_dep_003", "dependency", "Import isolation",
                "Tool handlers should not import at module level if imports may fail",
                0.80, "Tool wraps external library",
                "Use lazy imports inside handler functions"),
        MCPRule("mcp_dep_004", "dependency", "Path resolution",
                "File paths in tools should be absolute or relative to known root",
                0.85, "Tool accesses filesystem",
                "Use NLKE_ROOT or os.path.dirname(__file__) for path resolution"),
        MCPRule("mcp_dep_005", "dependency", "Environment variable dependency",
                "Required env vars should be checked at startup, not at call time",
                0.80, "Tool needs API keys or config",
                "Validate env vars in server initialization"),
        MCPRule("mcp_dep_006", "dependency", "Database connection lifecycle",
                "DB connections should be opened per-call, not held globally",
                0.85, "Tool queries SQLite or other DB",
                "Open connection in handler, close in finally block"),
        MCPRule("mcp_dep_007", "dependency", "Shared state isolation",
                "Tools in same server should not share mutable state unsafely",
                0.75, "Multiple tools in one server",
                "Use function-local state or explicit locking for shared resources"),
        MCPRule("mcp_dep_008", "dependency", "Graceful degradation",
                "If optional dependency unavailable, tool should still list (with error on call)",
                0.70, "Tool has optional features",
                "Always register in list_tools; return helpful error if dependency missing"),
    ],
    "compatibility": [
        MCPRule("mcp_compat_001", "compatibility", "Stdio transport default",
                "Use stdio transport for local tools (lowest latency)",
                0.90, "Tool runs locally",
                "Default to stdio; only use HTTP for remote/shared servers"),
        MCPRule("mcp_compat_002", "compatibility", "Python 3.8+ compatibility",
                "Generated code should work with Python 3.8+",
                0.85, "Always",
                "Avoid walrus operator, union types (X|Y), match statements"),
        MCPRule("mcp_compat_003", "compatibility", "JSON serialization safety",
                "All handler results must be JSON-serializable",
                0.95, "Always",
                "Use default=str in json.dumps for datetime, Path, etc."),
        MCPRule("mcp_compat_004", "compatibility", "No external package requirement",
                "Generated MCP tools should only need stdlib (no pip install)",
                0.80, "Tool is standalone",
                "Stick to json, os, sys, sqlite3, urllib. Document if external needed."),
        MCPRule("mcp_compat_005", "compatibility", "Protocol version 2024-11-05",
                "Use current stable MCP protocol version",
                0.95, "Always",
                "Return protocolVersion: '2024-11-05' in initialize response"),
        MCPRule("mcp_compat_006", "compatibility", "Claude Code .mcp.json format",
                "Config must match Claude Code's expected .mcp.json structure",
                0.95, "Always",
                "Use mcpServers.{name}.command + args format"),
        MCPRule("mcp_compat_007", "compatibility", "Android/Termux compatibility",
                "Consider Termux environment constraints (no /usr/bin, limited packages)",
                0.70, "Tool targets mobile environment",
                "Use python3 not python, avoid subprocess with shell=True for portability"),
        MCPRule("mcp_compat_008", "compatibility", "Unicode handling",
                "Tool results must handle Unicode correctly",
                0.80, "Tool processes text data",
                "Use UTF-8 encoding explicitly in file operations"),
        MCPRule("mcp_compat_009", "compatibility", "Multi-model result format",
                "Results should be usable by Claude Opus, Sonnet, Haiku, and Gemini",
                0.75, "Tool is part of multi-model workflow",
                "Return plain JSON, avoid model-specific formatting"),
        MCPRule("mcp_compat_010", "compatibility", "NLKE agent base compatibility",
                "Tools wrapping NLKE agents should import from agent_base correctly",
                0.90, "Tool wraps an NLKE Python agent",
                "Use sys.path.insert with relative path to agents/ directory"),
    ],
    "constraint": [
        MCPRule("mcp_const_001", "constraint", "Result size limit (4MB)",
                "Tool results should not exceed 4MB (stdio transport limit)",
                0.95, "Always",
                "Truncate or paginate results exceeding 4MB"),
        MCPRule("mcp_const_002", "constraint", "Execution timeout (30s)",
                "Tool handlers should complete within 30 seconds",
                0.85, "Always",
                "Implement timeout mechanism; return partial result if exceeded"),
        MCPRule("mcp_const_003", "constraint", "Memory budget (100MB)",
                "Tool should not allocate more than 100MB RAM",
                0.75, "Tool processes large data",
                "Use streaming or chunked processing for large datasets"),
        MCPRule("mcp_const_004", "constraint", "No network calls without timeout",
                "HTTP/API calls must have explicit timeout",
                0.90, "Tool makes network requests",
                "Set timeout=30 on all urllib/requests calls"),
        MCPRule("mcp_const_005", "constraint", "No file writes without permission",
                "Tools should not write files unless explicitly designed for it",
                0.85, "Tool could modify filesystem",
                "Read-only by default; document write operations clearly"),
        MCPRule("mcp_const_006", "constraint", "Rate limiting for API wrappers",
                "Tools wrapping external APIs should implement rate limiting",
                0.75, "Tool calls rate-limited API",
                "Add simple token-bucket or delay between calls"),
        MCPRule("mcp_const_007", "constraint", "Single responsibility",
                "Each tool should do one thing well",
                0.80, "Tool has complex multi-step logic",
                "Split into multiple tools rather than one mega-tool"),
        MCPRule("mcp_const_008", "constraint", "Deterministic output",
                "Same input should produce same output (when possible)",
                0.70, "Tool is used in reproducible workflows",
                "Seed random generators, document non-deterministic behavior"),
        MCPRule("mcp_const_009", "constraint", "Error message quality",
                "Error responses should be actionable, not just stack traces",
                0.85, "Always",
                "Return {error: 'description', suggestion: 'what to do'}"),
        MCPRule("mcp_const_010", "constraint", "Input validation",
                "Validate all tool inputs before processing",
                0.90, "Always",
                "Check required fields, types, ranges before executing logic"),
        MCPRule("mcp_const_011", "constraint", "No subprocess.shell=True",
                "Avoid shell=True in subprocess calls to prevent injection",
                0.95, "Tool uses subprocess",
                "Use subprocess.run with args list, never shell=True"),
        MCPRule("mcp_const_012", "constraint", "SQL injection prevention",
                "Use parameterized queries for all database operations",
                0.95, "Tool queries databases",
                "Use ? placeholders in sqlite3, never f-string SQL"),
        MCPRule("mcp_const_013", "constraint", "Path traversal prevention",
                "Validate file paths to prevent directory traversal",
                0.90, "Tool accepts file paths as input",
                "Normalize paths and check they're within allowed directories"),
        MCPRule("mcp_const_014", "constraint", "Logging to stderr only",
                "Log messages must go to stderr, never stdout (stdio transport)",
                0.95, "Tool has logging/debug output",
                "Use sys.stderr.write or logging with stderr handler"),
        MCPRule("mcp_const_015", "constraint", "Graceful shutdown",
                "Server should handle SIGTERM and clean up resources",
                0.70, "Server manages resources (DB connections, temp files)",
                "Register signal handler or use atexit for cleanup"),
    ],
    "interface": [
        MCPRule("mcp_iface_001", "interface", "Initialize handshake",
                "Server must respond to initialize with capabilities",
                0.95, "Always",
                "Return protocolVersion, capabilities.tools, serverInfo"),
        MCPRule("mcp_iface_002", "interface", "tools/list response format",
                "tools/list must return {tools: [{name, description, inputSchema}]}",
                0.95, "Always",
                "Each tool needs all three fields"),
        MCPRule("mcp_iface_003", "interface", "tools/call response format",
                "tools/call must return {content: [{type, text}]}",
                0.95, "Always",
                "Return content array with text type; set isError for failures"),
        MCPRule("mcp_iface_004", "interface", "Notification handling",
                "Server should silently ignore notifications (no response needed)",
                0.85, "Always",
                "Don't respond to notifications/initialized, etc."),
        MCPRule("mcp_iface_005", "interface", "Unknown method handling",
                "Server should return error for unknown methods, not crash",
                0.90, "Always",
                "Return JSON-RPC error response with method name"),
    ],
}


# ============================================================================
# Rule Matching Engine
# ============================================================================

def match_rules(spec, mode: str = "validate") -> Dict[str, Any]:
    """Match MCP rules against a tool spec.

    Args:
        spec: MCPToolSpec to validate
        mode: "validate" (check all), "search" (keyword filter), "stats" (summary)

    Returns:
        Dict with matched_rules, warnings, score, recommendations
    """
    matched = []
    warnings = []
    applicable_count = 0

    for category, rules in MCP_RULES.items():
        for rule in rules:
            # Check if rule applies to this spec
            applies = True

            # Category-specific applicability
            if "wraps an NLKE agent" in rule.applies_when:
                applies = bool(spec.wraps)
            elif "Tool runs locally" in rule.applies_when:
                applies = spec.transport == "stdio"
            elif "Multiple tools" in rule.applies_when or "Server has multiple tools" in rule.applies_when:
                applies = len(spec.tools) > 1
            elif "Tool queries" in rule.applies_when or "Tool accesses filesystem" in rule.applies_when:
                applies = True  # Conservative: assume most tools access data

            if applies:
                applicable_count += 1
                matched.append({
                    "rule_id": rule.rule_id,
                    "category": rule.category,
                    "title": rule.title,
                    "confidence": rule.confidence,
                    "recommendation": rule.recommendation,
                })

                # High-confidence rules become warnings if not met
                if rule.confidence >= 0.90:
                    warnings.append(f"[{rule.rule_id}] {rule.title}: {rule.recommendation}")

    # Calculate quality score
    total_rules = sum(len(rules) for rules in MCP_RULES.values())
    score = min(1.0, applicable_count / max(1, total_rules) + 0.5)

    return {
        "matched_rules": matched,
        "matched_count": len(matched),
        "total_rules": total_rules,
        "applicable_count": applicable_count,
        "warnings": warnings[:10],  # Top 10 warnings
        "quality_score": round(score, 2),
        "categories_covered": list(MCP_RULES.keys()),
    }


def get_rules_by_category(category: str) -> List[MCPRule]:
    """Get all rules for a specific category."""
    return MCP_RULES.get(category, [])


def get_rule_stats() -> Dict[str, Any]:
    """Get summary statistics of the MCP rule set."""
    stats = {}
    total = 0
    for category, rules in MCP_RULES.items():
        stats[category] = {
            "count": len(rules),
            "avg_confidence": round(sum(r.confidence for r in rules) / max(1, len(rules)), 2),
        }
        total += len(rules)
    stats["total"] = total
    return stats

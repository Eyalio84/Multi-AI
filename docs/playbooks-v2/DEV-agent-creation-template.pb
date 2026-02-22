# DEV-agent-creation-template.pb
# Meta-Template for Creating Production-Ready Agents
#
# This template distills patterns from:
# - CodeAnalyzerAgent (1,090 lines)
# - CodeWriterAgent (1,372 lines)
# - CodeReviewerAgent (1,442 lines)
# - HAL MCP Server (889 lines) - MCP tool patterns
# - HAL Emotional State (338 lines) - Export/analytics patterns
# - agent_orchestrator.py (901 lines) - Batch/parallel, error recovery
# - cost_analyzer.py - Cost tracking, budget enforcement
# - parser_adapters.py (1,343 lines) - Validation patterns
#
# Author: Eyal Nof
# Created: 2026-01-17
# Updated: 2026-01-17 (Added 8 production patterns)
# Version: 3.0
# Total Lines: ~3,360

## OVERVIEW

This playbook provides a complete pattern for creating agents that follow
the Synthesis Rules ecosystem conventions. All agents share common patterns
for accessibility (--explain, --interactive), security (--safe-mode),
and output (JSON for CI/CD).

### Pattern Categories

| Category | Patterns | Lines |
|----------|----------|-------|
| **Base Patterns** | SafeMode, ExplainMode, InteractiveMode, Dataclasses, CLI | ~880 |
| **HAL Patterns** | MCP Tools, Checkpoint/Resume, Export/Analytics | ~750 |
| **Production Patterns** | Batch/Parallel, Caching, Cost, Config, Progress, Validation, Error Recovery, Plugins | ~1,730 |
| **Total** | **11 patterns** | **~3,360** |

## AGENT CHARACTERISTICS

| Characteristic | Requirement |
|----------------|-------------|
| Cost | $0.00 (local analysis only) |
| Dependencies | Python stdlib only |
| Output | JSON to stdout |
| Target Size | 1,000-1,500 lines |
| Test Coverage | 30+ unit tests |
| Documentation | Dual format (.md + .pb) |

## FILE STRUCTURE

```
tools/agents/
├── {agent_name}_agent.py           # Main agent (1,000-1,500 lines)
├── docs/
│   ├── {agent_name}_agent.doc.md   # User documentation (400+ lines)
│   └── {agent_name}_agent.doc.pb   # Technical reference (250+ lines)
└── tests/
    ├── test_{agent_name}_unit.py   # Unit tests (30+ tests)
    └── fixtures/
        ├── sample_clean_code.py    # Test fixtures
        └── sample_buggy_code.py
```

## TEMPLATE STRUCTURE

### 1. HEADER DOCSTRING PATTERN

```python
#!/usr/bin/env python3
"""
{Agent Name} Agent

{Brief description of what the agent does}:
- {Capability 1}
- {Capability 2}
- {Capability 3}

Agent Capabilities:
- {Detailed capability 1}
- {Detailed capability 2}
- {Detailed capability 3}

Accessibility Modes:
- --explain: Educational explanations with examples and remediation
- --interactive: Step-by-step guided workflow with user decisions

Security Features:
- --safe-mode: Restricts file access to current directory and subdirectories
- Path traversal protection (blocks ../ attempts)

Cost: $0.00 (analysis only, no API calls)
Speed: <{estimated_time}ms per {unit} processed

Usage:
    # Basic usage
    python3 {agent_name}_agent.py {command} --file ./example.py

    # With safe mode
    python3 {agent_name}_agent.py {command} --file ./example.py --safe-mode

    # With explain mode
    python3 {agent_name}_agent.py {command} --file ./example.py --explain

    # Interactive mode
    python3 {agent_name}_agent.py {command} --file ./example.py --interactive

Author: Eyal Nof
Created: {YYYY-MM-DD}
"""
```

### 2. IMPORTS PATTERN

```python
import json
import argparse
import sys
import ast
import re
import os
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict, field
from enum import Enum
from pathlib import Path
from collections import defaultdict
```

### 3. SAFE MODE CLASS

```python
# ============================================================================
# SAFE MODE - Path Validation
# ============================================================================

class SafeMode:
    """
    Restricts file operations to safe directories.

    Prevents path traversal attacks and unauthorized access.
    When enabled, all file paths must be within the allowed directories.
    """

    def __init__(self, enabled: bool = False, base_dir: str = None):
        self.enabled = enabled
        self.base_dir = Path(base_dir or os.getcwd()).resolve()

    def validate_path(self, file_path: str) -> Tuple[bool, str]:
        """
        Validate that a file path is safe to access.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.enabled:
            return True, ""

        try:
            resolved = Path(file_path).resolve()

            # Check for path traversal attempts
            if ".." in str(file_path):
                return False, f"Path traversal detected: {file_path}"

            # Check if path is within allowed directory
            try:
                resolved.relative_to(self.base_dir)
                return True, ""
            except ValueError:
                return False, f"Path outside allowed directory: {file_path} (allowed: {self.base_dir})"

        except Exception as e:
            return False, f"Invalid path: {e}"

    def check_or_raise(self, file_path: str) -> str:
        """Validate path and raise error if invalid. Returns resolved path."""
        is_valid, error = self.validate_path(file_path)
        if not is_valid:
            raise PermissionError(f"[SAFE MODE] {error}")
        return str(Path(file_path).resolve())
```

### 4. EXPLAIN MODE CLASS

```python
# ============================================================================
# EXPLAIN MODE - Educational Explanations
# ============================================================================

class ExplainMode:
    """
    Provides educational explanations for findings.

    Includes:
    - What the issue/finding is
    - Why it matters (or is dangerous for security)
    - Example (or exploit example for security)
    - How to fix it (remediation code)
    """

    # Domain-specific explanations (customize for your agent)
    EXPLANATIONS = {
        "example_issue": {
            "what": "Description of what this issue is",
            "why_problem": "Why this is a problem",
            "example": '''# Code example showing the issue
def problematic():
    pass''',
            "remediation": '''# Code example showing the fix
def fixed():
    pass''',
            "references": [
                "Link to documentation or OWASP, etc."
            ]
        },
    }

    def __init__(self, enabled: bool = False):
        self.enabled = enabled

    def get_explanation(self, issue_type: str) -> Optional[Dict[str, Any]]:
        """Get educational explanation for an issue type."""
        if not self.enabled:
            return None

        # Normalize issue type
        normalized = issue_type.lower().replace(" ", "_").replace("-", "_")
        return self.EXPLANATIONS.get(normalized)

    def format_explanation(self, issue_type: str) -> str:
        """Format a full educational explanation as text."""
        explanation = self.get_explanation(issue_type)
        if not explanation:
            return ""

        lines = [
            "",
            "=" * 60,
            f"EDUCATIONAL EXPLANATION: {issue_type.replace('_', ' ').title()}",
            "=" * 60,
            "",
            "WHAT IS THIS?",
            explanation.get("what", ""),
            "",
            "WHY IS IT A PROBLEM?",
            explanation.get("why_problem", ""),
            "",
            "EXAMPLE:",
            explanation.get("example", ""),
            "",
            "HOW TO FIX:",
            explanation.get("remediation", ""),
        ]

        refs = explanation.get("references", [])
        if refs:
            lines.extend(["", "REFERENCES:"])
            lines.extend([f"  - {ref}" for ref in refs])

        lines.append("=" * 60)
        return "\n".join(lines)
```

### 5. INTERACTIVE MODE CLASS

```python
# ============================================================================
# INTERACTIVE MODE - Step-by-Step Workflow
# ============================================================================

class InteractiveMode:
    """
    Provides interactive step-by-step workflow.

    Walks through each finding and asks for user decisions.
    Tracks decisions for final summary.
    """

    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self.decisions = []  # Track user decisions

    def prompt_user(self, prompt: str, options: List[str] = None) -> str:
        """Prompt user for input with optional choices."""
        if not self.enabled:
            return ""

        if options:
            print(f"\n{prompt}")
            for i, opt in enumerate(options, 1):
                print(f"  [{i}] {opt}")
            print(f"  [q] Quit")

            while True:
                try:
                    choice = input("\nYour choice: ").strip().lower()
                    if choice == 'q':
                        return 'quit'
                    idx = int(choice) - 1
                    if 0 <= idx < len(options):
                        return options[idx]
                except (ValueError, IndexError):
                    pass
                print("Invalid choice. Try again.")
        else:
            return input(f"\n{prompt}: ").strip()

    def review_item(self, item: Dict[str, Any], explain_mode: 'ExplainMode' = None) -> Dict[str, Any]:
        """
        Present an item for interactive review.

        Args:
            item: Dict with item details (title, description, etc.)
            explain_mode: Optional ExplainMode for educational content

        Returns:
            Dict with user's decision and any comments
        """
        if not self.enabled:
            return {}

        print("\n" + "=" * 60)
        print(f"ITEM: {item.get('title', 'Unknown')}")
        print("=" * 60)
        print(f"\n{item.get('description', '')}")

        if item.get('suggestion'):
            print(f"\nSUGGESTION: {item['suggestion']}")

        # Show educational content if explain mode is enabled
        if explain_mode and explain_mode.enabled:
            issue_type = item.get('title', '').lower().replace(' ', '_')
            explanation = explain_mode.format_explanation(issue_type)
            if explanation:
                print(explanation)

        action = self.prompt_user(
            "How would you like to handle this?",
            ["Acknowledge", "Will fix", "Won't fix (justified)", "Skip"]
        )

        if action == 'quit':
            return {"action": "quit", "comment": ""}

        comment = ""
        if action == "Won't fix (justified)":
            comment = self.prompt_user("Please explain")

        decision = {
            "item": item.get('title'),
            "action": action,
            "comment": comment
        }
        self.decisions.append(decision)
        return decision

    def summarize_decisions(self) -> Dict[str, Any]:
        """Summarize all decisions made during review."""
        if not self.decisions:
            return {"total": 0, "summary": {}}

        summary = {}
        for d in self.decisions:
            action = d.get('action', 'unknown')
            summary[action] = summary.get(action, 0) + 1

        return {
            "total": len(self.decisions),
            "summary": summary,
            "decisions": self.decisions
        }

    def print_welcome(self, review_type: str = "item"):
        """Print welcome message for interactive mode."""
        if not self.enabled:
            return

        print("\n" + "+" + "=" * 58 + "+")
        print("|" + f" INTERACTIVE {review_type.upper()} REVIEW ".center(58) + "|")
        print("+" + "=" * 58 + "+")
        print("|" + " You will review each item step-by-step.".ljust(58) + "|")
        print("|" + " Press 'q' at any prompt to quit early.".ljust(58) + "|")
        print("+" + "=" * 58 + "+")

    def print_summary(self):
        """Print final summary of the session."""
        if not self.enabled:
            return

        summary = self.summarize_decisions()
        print("\n" + "+" + "=" * 58 + "+")
        print("|" + " SESSION COMPLETE ".center(58) + "|")
        print("+" + "=" * 58 + "+")
        print("|" + f" Total items reviewed: {summary['total']}".ljust(58) + "|")
        for action, count in summary.get('summary', {}).items():
            print("|" + f"   - {action}: {count}".ljust(58) + "|")
        print("+" + "=" * 58 + "+")
```

### 6. RESULT DATA CLASSES

```python
# ============================================================================
# RESULT DATA CLASSES
# ============================================================================

@dataclass
class Finding:
    """Individual finding from the agent."""
    title: str
    description: str
    severity: str  # "critical", "high", "medium", "low", "info"
    category: str
    file_path: str = ""
    line_number: int = 0
    suggestion: str = ""
    code_snippet: str = ""


@dataclass
class AgentResult:
    """Result from agent operation."""
    file_path: str
    success: bool
    findings: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: __import__('datetime').datetime.now().isoformat())
```

### 7. MAIN AGENT CLASS

```python
# ============================================================================
# MAIN AGENT CLASS
# ============================================================================

class {AgentName}Agent:
    """
    {Description of what the agent does}.

    Features:
    - {Feature 1}
    - {Feature 2}
    - Safe mode path validation
    - Explain mode educational content
    - Interactive mode step-by-step workflow
    """

    def __init__(
        self,
        verbose: bool = False,
        safe_mode: SafeMode = None,
        explain_mode: ExplainMode = None,
        interactive_mode: InteractiveMode = None,
    ):
        self.verbose = verbose
        self.safe_mode = safe_mode or SafeMode(enabled=False)
        self.explain_mode = explain_mode or ExplainMode(enabled=False)
        self.interactive_mode = interactive_mode or InteractiveMode(enabled=False)

    def _read_file(self, file_path: str) -> str:
        """Read file with safe mode validation."""
        # Validate path in safe mode
        validated_path = self.safe_mode.check_or_raise(file_path)

        with open(validated_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _parse_python(self, content: str) -> Optional[ast.AST]:
        """Parse Python code safely."""
        try:
            return ast.parse(content)
        except SyntaxError as e:
            return None

    def process_file(self, file_path: str) -> AgentResult:
        """
        Main processing method.

        Args:
            file_path: Path to file to process

        Returns:
            AgentResult with findings and metrics
        """
        try:
            content = self._read_file(file_path)
        except PermissionError as e:
            return AgentResult(
                file_path=file_path,
                success=False,
                errors=[str(e)]
            )
        except FileNotFoundError:
            return AgentResult(
                file_path=file_path,
                success=False,
                errors=[f"File not found: {file_path}"]
            )

        # Parse if Python
        tree = self._parse_python(content)

        # TODO: Implement your analysis logic here
        findings = []
        metrics = {
            "lines": len(content.splitlines()),
            "characters": len(content),
        }

        return AgentResult(
            file_path=file_path,
            success=True,
            findings=findings,
            metrics=metrics
        )

    def batch_process(self, directory: str, extensions: List[str] = None) -> Dict[str, Any]:
        """
        Process all matching files in a directory.

        Args:
            directory: Directory path
            extensions: File extensions to include (default: [".py"])

        Returns:
            Dict with combined results
        """
        extensions = extensions or [".py"]

        # Validate directory in safe mode
        validated_dir = self.safe_mode.check_or_raise(directory)
        dir_path = Path(validated_dir)

        results = []
        for ext in extensions:
            for file_path in dir_path.rglob(f"*{ext}"):
                result = self.process_file(str(file_path))
                results.append(asdict(result))

        return {
            "directory": directory,
            "files_processed": len(results),
            "results": results
        }
```

### 8. CLI ENTRY POINT

```python
# ============================================================================
# CLI ENTRY POINT
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="{Agent description}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Basic usage
    python3 {agent_name}_agent.py process --file ./example.py

    # With safe mode
    python3 {agent_name}_agent.py process --file ./example.py --safe-mode

    # With explain mode
    python3 {agent_name}_agent.py process --file ./example.py --explain

    # Interactive mode
    python3 {agent_name}_agent.py process --file ./example.py --interactive

    # Batch processing
    python3 {agent_name}_agent.py batch --path ./src
        """
    )

    # Global arguments (apply to all commands)
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable verbose output")
    parser.add_argument("--safe-mode", action="store_true",
                        help="Restrict file access to current directory")
    parser.add_argument("--explain", action="store_true",
                        help="Enable educational explanations")
    parser.add_argument("--interactive", action="store_true",
                        help="Enable interactive step-by-step mode")

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Process command
    process_p = subparsers.add_parser("process", help="Process a single file")
    process_p.add_argument("--file", required=True, help="File to process")

    # Batch command
    batch_p = subparsers.add_parser("batch", help="Process all files in a directory")
    batch_p.add_argument("--path", required=True, help="Directory to process")
    batch_p.add_argument("--output", help="Output file for report")
    batch_p.add_argument("--extensions", nargs="+", default=[".py"],
                         help="File extensions to process (default: .py)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Initialize modes
    safe_mode = SafeMode(enabled=args.safe_mode)
    explain_mode = ExplainMode(enabled=args.explain)
    interactive_mode = InteractiveMode(enabled=args.interactive)

    # Create agent with all modes
    agent = {AgentName}Agent(
        verbose=args.verbose,
        safe_mode=safe_mode,
        explain_mode=explain_mode,
        interactive_mode=interactive_mode
    )

    if args.command == "process":
        # Show interactive welcome if enabled
        if interactive_mode.enabled:
            interactive_mode.print_welcome("FILE")

        result = agent.process_file(args.file)

        # Interactive review of findings
        if interactive_mode.enabled and result.findings:
            for finding in result.findings:
                decision = interactive_mode.review_item(finding, explain_mode)
                if decision.get('action') == 'quit':
                    break
            interactive_mode.print_summary()
            output = asdict(result)
            output['interactive_decisions'] = interactive_mode.summarize_decisions()
            print(json.dumps(output, indent=2))
        elif explain_mode.enabled:
            output = asdict(result)
            output['explanations'] = []
            for finding in result.findings:
                issue_type = finding.get('title', '').lower().replace(' ', '_')
                explanation = explain_mode.get_explanation(issue_type)
                if explanation:
                    output['explanations'].append({
                        'issue': finding.get('title'),
                        'explanation': explanation
                    })
            print(json.dumps(output, indent=2))
        else:
            print(json.dumps(asdict(result), indent=2))

    elif args.command == "batch":
        result = agent.batch_process(args.path, extensions=args.extensions)
        output = json.dumps(result, indent=2)

        if args.output:
            if safe_mode.enabled:
                try:
                    args.output = safe_mode.check_or_raise(args.output)
                except PermissionError as e:
                    print(f"Error: {e}", file=sys.stderr)
                    sys.exit(1)

            with open(args.output, 'w') as f:
                f.write(output)
            print(f"Report saved to {args.output}")
        else:
            print(output)


if __name__ == "__main__":
    main()
```

## DOCUMENTATION TEMPLATE

### User Documentation (.doc.md)

```markdown
# {Agent Name} Agent

> {Brief description}

## Quick Start

\```bash
# Basic usage
python3 {agent_name}_agent.py process --file ./example.py
\```

## Features

- **{Feature 1}**: {Description}
- **{Feature 2}**: {Description}

## Accessibility Modes

### --explain Mode
Educational explanations with examples and remediation.

### --interactive Mode
Step-by-step guided workflow with user decisions.

## Security

### --safe-mode
Restricts file access to current directory and subdirectories.

## Output Format

All output is JSON for CI/CD compatibility:

\```json
{
  "file_path": "./example.py",
  "success": true,
  "findings": [...],
  "metrics": {...}
}
\```

## Examples

### Basic Processing
\```bash
python3 {agent_name}_agent.py process --file ./main.py
\```

### Safe Mode
\```bash
python3 {agent_name}_agent.py process --file ./main.py --safe-mode
\```

### Interactive Review
\```bash
python3 {agent_name}_agent.py process --file ./main.py --interactive --explain
\```
```

## TEST TEMPLATE

```python
#!/usr/bin/env python3
"""
Unit tests for {Agent Name} Agent.

Tests:
- SafeMode path validation
- ExplainMode educational content
- InteractiveMode workflow
- Main agent functionality

Author: Eyal Nof
Created: {YYYY-MM-DD}
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path
from io import StringIO
from unittest.mock import patch

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from {agent_name}_agent import (
    SafeMode, ExplainMode, InteractiveMode,
    {AgentName}Agent, AgentResult, Finding
)


class TestSafeMode(unittest.TestCase):
    """Tests for SafeMode class."""

    def test_disabled_allows_all(self):
        """SafeMode disabled should allow any path."""
        safe = SafeMode(enabled=False)
        is_valid, error = safe.validate_path("/etc/passwd")
        self.assertTrue(is_valid)

    def test_enabled_blocks_traversal(self):
        """SafeMode should block path traversal attempts."""
        safe = SafeMode(enabled=True)
        is_valid, error = safe.validate_path("../../../etc/passwd")
        self.assertFalse(is_valid)
        self.assertIn("traversal", error.lower())

    def test_enabled_allows_valid_path(self):
        """SafeMode should allow paths within base directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            safe = SafeMode(enabled=True, base_dir=tmpdir)
            test_file = Path(tmpdir) / "test.py"
            test_file.touch()
            is_valid, error = safe.validate_path(str(test_file))
            self.assertTrue(is_valid)


class TestExplainMode(unittest.TestCase):
    """Tests for ExplainMode class."""

    def test_disabled_returns_none(self):
        """ExplainMode disabled should return None."""
        explain = ExplainMode(enabled=False)
        result = explain.get_explanation("example_issue")
        self.assertIsNone(result)

    def test_enabled_returns_explanation(self):
        """ExplainMode enabled should return explanation dict."""
        explain = ExplainMode(enabled=True)
        # Test with an issue type that exists in EXPLANATIONS
        result = explain.get_explanation("example_issue")
        if result:  # Only if explanation exists
            self.assertIn("what", result)


class TestInteractiveMode(unittest.TestCase):
    """Tests for InteractiveMode class."""

    def test_disabled_returns_empty(self):
        """InteractiveMode disabled should return empty results."""
        interactive = InteractiveMode(enabled=False)
        result = interactive.review_item({"title": "test"})
        self.assertEqual(result, {})

    def test_summarize_empty(self):
        """Summarize with no decisions should return empty summary."""
        interactive = InteractiveMode(enabled=True)
        summary = interactive.summarize_decisions()
        self.assertEqual(summary["total"], 0)


class Test{AgentName}Agent(unittest.TestCase):
    """Tests for main agent class."""

    def setUp(self):
        """Set up test fixtures."""
        self.tmpdir = tempfile.mkdtemp()
        self.agent = {AgentName}Agent()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_process_nonexistent_file(self):
        """Processing nonexistent file should return error."""
        result = self.agent.process_file("/nonexistent/file.py")
        self.assertFalse(result.success)
        self.assertTrue(any("not found" in e.lower() for e in result.errors))

    def test_process_valid_file(self):
        """Processing valid file should succeed."""
        test_file = Path(self.tmpdir) / "test.py"
        test_file.write_text("print('hello')")
        result = self.agent.process_file(str(test_file))
        self.assertTrue(result.success)


if __name__ == "__main__":
    unittest.main()
```

## CHECKLIST FOR NEW AGENTS

- [ ] Header docstring with all sections
- [ ] SafeMode class (copy from template)
- [ ] ExplainMode class with domain-specific explanations
- [ ] InteractiveMode class (copy from template)
- [ ] Result dataclasses
- [ ] Main agent class with process_file() and batch_process()
- [ ] CLI with --safe-mode, --explain, --interactive flags
- [ ] JSON output to stdout
- [ ] Unit tests (30+ tests)
- [ ] Documentation (.md + .pb dual format)
- [ ] Author credit: "Eyal Nof"
- [ ] Test with safe mode enabled
- [ ] Test with explain mode enabled
- [ ] Test with interactive mode enabled

## CUSTOMIZATION POINTS

When creating a new agent, customize:

1. **Header docstring**: Agent name, description, capabilities, usage examples
2. **ExplainMode.EXPLANATIONS**: Domain-specific educational content
3. **Result dataclasses**: Add domain-specific fields
4. **Agent class methods**: Implement your analysis logic
5. **CLI subcommands**: Add domain-specific commands
6. **Tests**: Add domain-specific test cases

## REFERENCES

- CodeAnalyzerAgent: tools/agents/code_analyzer_agent.py
- CodeWriterAgent: tools/agents/code_writer_agent.py
- CodeReviewerAgent: tools/agents/code_reviewer_agent.py
- Documentation: tools/agents/docs/
- Tests: tools/agents/tests/
- HAL MCP Server: ~/HAL/hal_mcp_server.py
- HAL Emotional State: ~/HAL/hal_emotional_state.py

---

# HAL PATTERNS (Advanced)

The following patterns are extracted from the HAL MCP Server implementation.
Use these when building agents that need:
- MCP tool exposure
- Multi-step workflows with checkpoints
- State tracking with export/analytics

## HAL PATTERN 1: MCP TOOL DEFINITION

When exposing agent capabilities as MCP tools for Claude Code integration.

### Tool Definition Structure

```python
# ============================================================================
# MCP TOOL DEFINITIONS
# ============================================================================

TOOL_DEFINITIONS = [
    {
        "name": "agent_process",
        "description": """Process a file with the agent.

Use this for:
- {Use case 1}
- {Use case 2}
- {Use case 3}

Returns: {What it returns}
Takes: {Time estimate} on {hardware}.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to file to process"
                },
                "options": {
                    "type": "object",
                    "description": "Processing options",
                    "properties": {
                        "verbose": {"type": "boolean", "default": False},
                        "safe_mode": {"type": "boolean", "default": False}
                    }
                }
            },
            "required": ["file_path"]
        }
    },
    {
        "name": "agent_batch",
        "description": """Batch process multiple files.

Use this for:
- Processing entire directories
- Bulk analysis

Returns directory-level aggregated results.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "Directory to process"
                },
                "extensions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "File extensions to include",
                    "default": [".py"]
                }
            },
            "required": ["directory"]
        }
    }
]
```

### MCP Server Boilerplate

```python
import asyncio
from typing import Dict, Any, Optional

# Try to import MCP SDK
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

# ============================================================================
# MCP SERVER SETUP
# ============================================================================

if MCP_AVAILABLE:
    server = Server("{agent_name}")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """Return list of available tools."""
        return [
            Tool(
                name=t["name"],
                description=t["description"],
                inputSchema=t["inputSchema"]
            )
            for t in TOOL_DEFINITIONS
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        """Handle tool calls."""
        try:
            if name == "agent_process":
                result = await handle_process(
                    arguments.get("file_path", ""),
                    arguments.get("options", {})
                )
            elif name == "agent_batch":
                result = await handle_batch(
                    arguments.get("directory", ""),
                    arguments.get("extensions", [".py"])
                )
            else:
                result = f"Unknown tool: {name}"

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Run the MCP server."""
    if not MCP_AVAILABLE:
        print("Error: MCP SDK not available. Install with: pip install mcp")
        return

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
```

### MCP Tool Handler Pattern

```python
async def handle_process(file_path: str, options: Dict[str, Any] = None) -> str:
    """
    Handle agent_process tool call.

    Pattern: Parse args -> Validate -> Execute -> Format output
    """
    options = options or {}

    # Initialize modes from options
    safe_mode = SafeMode(enabled=options.get("safe_mode", False))
    verbose = options.get("verbose", False)

    # Create agent instance
    agent = {AgentName}Agent(
        verbose=verbose,
        safe_mode=safe_mode
    )

    # Execute
    result = agent.process_file(file_path)

    # Format as markdown for MCP output
    if not result.success:
        return f"**Error:** {', '.join(result.errors)}"

    output = [f"**Processed:** `{file_path}`\n"]
    output.append(f"**Findings:** {len(result.findings)}")

    for finding in result.findings[:10]:  # Limit for readability
        output.append(f"\n- **{finding.get('title')}** ({finding.get('severity')})")
        output.append(f"  {finding.get('description', '')[:100]}")

    output.append(f"\n---\n_Metrics: {result.metrics}_")

    return "\n".join(output)
```

## HAL PATTERN 2: CHECKPOINT/RESUME

For long-running operations that need resumability.

### Checkpoint Storage

```python
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
import hashlib
import json

# Global checkpoint storage (in-memory, or use file/database)
_checkpoints: Dict[str, Dict[str, Any]] = {}


@dataclass
class Checkpoint:
    """Checkpoint state for resumable operations."""
    checkpoint_id: str
    created_at: str
    status: str  # "in_progress", "completed", "failed"
    current_step: int
    total_steps: int
    completed_steps: list = field(default_factory=list)
    accumulated_context: str = ""
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Checkpoint':
        return cls(**data)
```

### Checkpoint Manager

```python
class CheckpointManager:
    """
    Manages checkpoints for resumable multi-step operations.

    Pattern from HAL's hal_compose tool.
    """

    def __init__(self, storage: Dict[str, Any] = None):
        self.storage = storage if storage is not None else _checkpoints

    def create(self, steps: list, context: str = "") -> Checkpoint:
        """Create a new checkpoint."""
        checkpoint_id = hashlib.md5(
            f"{datetime.now().isoformat()}-{len(steps)}".encode()
        ).hexdigest()[:12]

        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            created_at=datetime.now().isoformat(),
            status="in_progress",
            current_step=0,
            total_steps=len(steps),
            completed_steps=[],
            accumulated_context=context
        )

        self.storage[checkpoint_id] = checkpoint.to_dict()
        return checkpoint

    def get(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """Retrieve a checkpoint."""
        data = self.storage.get(checkpoint_id)
        if data:
            return Checkpoint.from_dict(data)
        return None

    def update(self, checkpoint: Checkpoint) -> None:
        """Update a checkpoint."""
        self.storage[checkpoint.checkpoint_id] = checkpoint.to_dict()

    def complete_step(self, checkpoint: Checkpoint, step_result: Dict[str, Any]) -> None:
        """Mark a step as complete and update context."""
        checkpoint.completed_steps.append(step_result)
        checkpoint.current_step = len(checkpoint.completed_steps)
        checkpoint.accumulated_context += f"\n\nStep {checkpoint.current_step}: {step_result.get('summary', '')}"

        if checkpoint.current_step >= checkpoint.total_steps:
            checkpoint.status = "completed"

        self.update(checkpoint)

    def fail(self, checkpoint: Checkpoint, error: str) -> None:
        """Mark checkpoint as failed."""
        checkpoint.status = "failed"
        checkpoint.error = error
        self.update(checkpoint)
```

### Multi-Step Execution with Checkpoints

```python
async def execute_multi_step(
    steps: list,
    checkpoint_id: Optional[str] = None,
    checkpoint_manager: CheckpointManager = None
) -> Dict[str, Any]:
    """
    Execute multiple steps with checkpoint support.

    Pattern from HAL's hal_compose tool.

    Args:
        steps: List of step descriptions/queries
        checkpoint_id: Optional ID to resume from
        checkpoint_manager: Optional custom checkpoint manager

    Returns:
        Dict with results, checkpoint_id, and status
    """
    manager = checkpoint_manager or CheckpointManager()

    # Resume or create new
    if checkpoint_id:
        checkpoint = manager.get(checkpoint_id)
        if not checkpoint:
            return {"error": f"Checkpoint not found: {checkpoint_id}"}
        start_step = checkpoint.current_step
    else:
        checkpoint = manager.create(steps)
        start_step = 0

    results = []
    total_time = 0.0

    # Execute remaining steps
    for i, step in enumerate(steps[start_step:], start=start_step + 1):
        step_start = datetime.now()

        try:
            # Execute step (customize this for your agent)
            step_result = await execute_single_step(
                step=step,
                step_number=i,
                context=checkpoint.accumulated_context
            )

            step_time = (datetime.now() - step_start).total_seconds()
            total_time += step_time

            # Record result
            result_record = {
                "step": i,
                "query": step,
                "result": step_result,
                "time_seconds": round(step_time, 2),
                "summary": step_result.get("summary", "")[:200]
            }
            results.append(result_record)

            # Update checkpoint
            manager.complete_step(checkpoint, result_record)

        except Exception as e:
            manager.fail(checkpoint, str(e))
            return {
                "status": "failed",
                "checkpoint_id": checkpoint.checkpoint_id,
                "completed_steps": len(checkpoint.completed_steps),
                "total_steps": checkpoint.total_steps,
                "error": str(e),
                "results": results
            }

    return {
        "status": checkpoint.status,
        "checkpoint_id": checkpoint.checkpoint_id,
        "completed_steps": len(checkpoint.completed_steps),
        "total_steps": checkpoint.total_steps,
        "total_time_seconds": round(total_time, 2),
        "results": results
    }


async def execute_single_step(step: str, step_number: int, context: str) -> Dict[str, Any]:
    """
    Execute a single step. Customize for your agent.

    Args:
        step: Step description/query
        step_number: Current step number
        context: Accumulated context from previous steps

    Returns:
        Dict with step result and summary
    """
    # TODO: Implement your step execution logic
    # Example: call LLM, run analysis, etc.

    return {
        "output": f"Result for step {step_number}",
        "summary": f"Completed: {step[:50]}"
    }
```

## HAL PATTERN 3: EXPORT/ANALYTICS

For agents that track state over time and need export capabilities.

### State Tracker with History

```python
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional
from datetime import datetime
import json


@dataclass
class StateSnapshot:
    """
    Single state snapshot at a point in time.

    Customize the dimensions for your agent's domain.
    """
    # Core dimensions (customize these)
    dimension_a: float = 0.5  # e.g., confidence, engagement
    dimension_b: float = 0.5  # e.g., coverage, quality
    dimension_c: float = 0.5  # e.g., risk, complexity
    dimension_d: float = 0.5  # e.g., progress, health

    # Metadata
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    triggers: List[str] = field(default_factory=list)
    session_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'dimension_a': round(self.dimension_a, 3),
            'dimension_b': round(self.dimension_b, 3),
            'dimension_c': round(self.dimension_c, 3),
            'dimension_d': round(self.dimension_d, 3),
            'timestamp': self.timestamp,
            'triggers': self.triggers,
            'session_id': self.session_id,
        }

    def to_vector(self) -> List[float]:
        """Return as vector for analysis."""
        return [self.dimension_a, self.dimension_b, self.dimension_c, self.dimension_d]

    def dominant_dimension(self) -> str:
        """Return the highest dimension."""
        dims = {
            'dimension_a': self.dimension_a,
            'dimension_b': self.dimension_b,
            'dimension_c': self.dimension_c,
            'dimension_d': self.dimension_d,
        }
        return max(dims, key=dims.get)

    def intensity(self) -> float:
        """Overall intensity (deviation from neutral 0.5)."""
        return (
            abs(self.dimension_a - 0.5) +
            abs(self.dimension_b - 0.5) +
            abs(self.dimension_c - 0.5) +
            abs(self.dimension_d - 0.5)
        ) / 2.0
```

### State Tracker with Export

```python
class StateTracker:
    """
    Tracks state over time with history and export capabilities.

    Pattern from HAL's EmotionalStateTracker.
    """

    def __init__(self, session_id: str = None):
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_state = StateSnapshot(session_id=self.session_id)
        self.history: List[StateSnapshot] = []

    def update(self, **dimension_updates) -> StateSnapshot:
        """
        Update state with new dimension values.

        Args:
            **dimension_updates: e.g., dimension_a=0.8, dimension_b=0.3

        Returns:
            Updated StateSnapshot
        """
        # Save current to history
        self.history.append(StateSnapshot(
            dimension_a=self.current_state.dimension_a,
            dimension_b=self.current_state.dimension_b,
            dimension_c=self.current_state.dimension_c,
            dimension_d=self.current_state.dimension_d,
            timestamp=self.current_state.timestamp,
            triggers=self.current_state.triggers.copy(),
            session_id=self.session_id,
        ))

        # Update current state
        triggers = []
        for dim, value in dimension_updates.items():
            if hasattr(self.current_state, dim):
                setattr(self.current_state, dim, min(1.0, max(0.0, value)))
                triggers.append(f"{dim}={value:.2f}")

        self.current_state.triggers = triggers
        self.current_state.timestamp = datetime.now().isoformat()

        return self.current_state

    def get_trend(self, dimension: str, window: int = 5) -> str:
        """Get trend for a dimension over recent history."""
        if len(self.history) < 2:
            return "stable"

        recent = self.history[-window:]
        values = [getattr(s, dimension, 0.5) for s in recent]

        if len(values) < 2:
            return "stable"

        delta = values[-1] - values[0]
        if delta > 0.1:
            return "increasing"
        elif delta < -0.1:
            return "decreasing"
        return "stable"

    # =========================================================================
    # EXPORT METHODS
    # =========================================================================

    def export_history(self) -> List[Dict[str, Any]]:
        """Export full history as JSON-serializable list."""
        history_data = [state.to_dict() for state in self.history]
        history_data.append(self.current_state.to_dict())
        return history_data

    def export_to_file(self, filepath: str) -> str:
        """Export history to JSON file."""
        from pathlib import Path

        export_data = {
            'session_id': self.session_id,
            'exported_at': datetime.now().isoformat(),
            'total_updates': len(self.history),
            'summary': self.summary(),
            'history': self.export_history(),
            'statistics': self.compute_statistics(),
        }

        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w') as f:
            json.dump(export_data, f, indent=2)

        return str(path)

    def compute_statistics(self) -> Dict[str, Any]:
        """Compute aggregated statistics over session history."""
        if not self.history:
            return {'error': 'No history available'}

        all_states = self.history + [self.current_state]
        dimensions = ['dimension_a', 'dimension_b', 'dimension_c', 'dimension_d']

        stats = {}
        for dim in dimensions:
            values = [getattr(s, dim, 0.5) for s in all_states]
            n = len(values)
            mean = sum(values) / n
            variance = sum((v - mean) ** 2 for v in values) / n if n > 1 else 0

            stats[dim] = {
                'min': round(min(values), 3),
                'max': round(max(values), 3),
                'mean': round(mean, 3),
                'variance': round(variance, 4),
                'range': round(max(values) - min(values), 3),
            }

        # Overall intensity statistics
        intensities = [s.intensity() for s in all_states]
        stats['intensity'] = {
            'min': round(min(intensities), 3),
            'max': round(max(intensities), 3),
            'mean': round(sum(intensities) / len(intensities), 3),
        }

        # Dominant dimension frequency
        dominants = [s.dominant_dimension() for s in all_states]
        freq = {}
        for d in dominants:
            freq[d] = freq.get(d, 0) + 1
        stats['dominant_frequency'] = freq

        return stats

    def export_timeline(self) -> List[Dict[str, Any]]:
        """Export state as timeline for visualization."""
        timeline = []
        for state in self.history + [self.current_state]:
            timeline.append({
                'timestamp': state.timestamp,
                'vector': state.to_vector(),
                'dominant': state.dominant_dimension(),
                'intensity': round(state.intensity(), 3),
                'triggers': state.triggers,
            })
        return timeline

    def summary(self) -> Dict[str, Any]:
        """Get session summary."""
        return {
            'session_id': self.session_id,
            'current_state': self.current_state.to_dict(),
            'updates': len(self.history),
            'dominant_dimension': self.current_state.dominant_dimension(),
            'trends': {
                'dimension_a': self.get_trend('dimension_a'),
                'dimension_b': self.get_trend('dimension_b'),
                'dimension_c': self.get_trend('dimension_c'),
                'dimension_d': self.get_trend('dimension_d'),
            }
        }
```

### Export Tool Handler (MCP Pattern)

```python
async def handle_export_state(
    format: str = "summary",
    save_to_file: Optional[str] = None,
    tracker: StateTracker = None
) -> str:
    """
    Handle state export tool call.

    Pattern from HAL's hal_export_state tool.

    Args:
        format: "summary", "history", "timeline", "statistics", "full"
        save_to_file: Optional path to save JSON export
        tracker: StateTracker instance

    Returns:
        Formatted export string
    """
    if not tracker:
        return "Error: State tracker not available."

    output = ["**State Export**\n"]

    if format == "summary":
        summary = tracker.summary()
        output.append(f"Session: `{summary['session_id']}`")
        output.append(f"Updates: {summary['updates']}")
        output.append(f"Dominant: {summary['dominant_dimension']}")
        output.append("\n**Current State:**")
        state = summary['current_state']
        for dim in ['dimension_a', 'dimension_b', 'dimension_c', 'dimension_d']:
            output.append(f"- {dim}: {state[dim]:.3f}")
        output.append("\n**Trends:**")
        for dim, trend in summary['trends'].items():
            output.append(f"- {dim}: {trend}")

    elif format == "history":
        history = tracker.export_history()
        output.append(f"Total entries: {len(history)}\n")
        for i, entry in enumerate(history[-10:], 1):  # Last 10
            output.append(f"**Entry {i}:** {entry['timestamp'][-8:]}")
            output.append(f"  Vector: {entry['dimension_a']:.2f}, {entry['dimension_b']:.2f}, {entry['dimension_c']:.2f}, {entry['dimension_d']:.2f}")

    elif format == "timeline":
        timeline = tracker.export_timeline()
        output.append(f"Timeline entries: {len(timeline)}\n")
        output.append("```")
        for entry in timeline[-15:]:
            vector = entry['vector']
            output.append(
                f"{entry['timestamp'][-8:]} | "
                f"[{vector[0]:.2f},{vector[1]:.2f},{vector[2]:.2f},{vector[3]:.2f}] | "
                f"{entry['dominant']} ({entry['intensity']:.2f})"
            )
        output.append("```")

    elif format == "statistics":
        stats = tracker.compute_statistics()
        if 'error' in stats:
            output.append(f"Note: {stats['error']}")
        else:
            output.append("**Per-Dimension Statistics:**\n")
            for dim in ['dimension_a', 'dimension_b', 'dimension_c', 'dimension_d']:
                s = stats[dim]
                output.append(f"**{dim}:** range=[{s['min']:.3f}, {s['max']:.3f}], mean={s['mean']:.3f}")
            output.append(f"\n**Dominant Frequency:** {stats['dominant_frequency']}")

    elif format == "full":
        export_data = {
            'session_id': tracker.session_id,
            'summary': tracker.summary(),
            'statistics': tracker.compute_statistics(),
            'history': tracker.export_history(),
        }
        output.append("```json")
        output.append(json.dumps(export_data, indent=2)[:3000])
        output.append("```")

    # Save to file if requested
    if save_to_file:
        try:
            filepath = tracker.export_to_file(save_to_file)
            output.append(f"\n_Saved to: `{filepath}`_")
        except Exception as e:
            output.append(f"\n_Error saving file: {str(e)}_")

    return "\n".join(output)
```

## HAL PATTERN CHECKLIST

When implementing HAL patterns:

- [ ] MCP Tool Definitions with clear descriptions
- [ ] MCP Server boilerplate with error handling
- [ ] Tool handlers with markdown-formatted output
- [ ] Checkpoint dataclass with serialization
- [ ] CheckpointManager with create/get/update/fail
- [ ] Multi-step execution with resume capability
- [ ] StateSnapshot with to_dict, to_vector, dominant
- [ ] StateTracker with history list
- [ ] Export methods: history, file, statistics, timeline
- [ ] Summary method for quick overview
- [ ] MCP tool for state export

## HAL PATTERN REFERENCES

- hal_compose implementation: ~/HAL/hal_mcp_server.py (lines 603-716)
- hal_export_state implementation: ~/HAL/hal_mcp_server.py (lines 719-806)
- EmotionalStateTracker: ~/HAL/hal_emotional_state.py (lines 143-314)
- MCP tool definitions: ~/HAL/hal_mcp_server.py (lines 232-412)

---

# PRODUCTION PATTERNS (Advanced)

The following patterns are extracted from the Synthesis Rules production tools.
Use these for building production-ready agents with cost optimization, resilience,
and extensibility.

## PATTERN 4: BATCH/PARALLEL PROCESSING

For executing operations either sequentially (with context passing) or in parallel
(for independent operations).

### Workflow Types

```python
from enum import Enum
import asyncio
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass, field
from datetime import datetime


class WorkflowType(Enum):
    """Execution workflow patterns."""
    SEQUENTIAL = "sequential"    # Execute one after another, pass context
    PARALLEL = "parallel"        # Execute concurrently, aggregate results
    CONDITIONAL = "conditional"  # Execute based on conditions


@dataclass
class WorkItem:
    """Single item in a batch."""
    item_id: str
    data: Any
    status: str = "pending"  # pending, running, completed, failed
    result: Any = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


@dataclass
class BatchResult:
    """Result of batch execution."""
    workflow_type: str
    total_items: int
    completed: int
    failed: int
    total_time_seconds: float
    items: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.total_items == 0:
            return 0.0
        return self.completed / self.total_items
```

### Batch Executor

```python
class BatchExecutor:
    """
    Execute operations in batch with sequential or parallel mode.

    Pattern from agent_orchestrator.py.
    """

    def __init__(
        self,
        workflow_type: WorkflowType = WorkflowType.SEQUENTIAL,
        max_concurrent: int = 10,
        timeout_per_item: float = 30.0,
        on_progress: Callable[[int, int], None] = None
    ):
        self.workflow_type = workflow_type
        self.max_concurrent = max_concurrent
        self.timeout_per_item = timeout_per_item
        self.on_progress = on_progress

    async def execute_sequential(
        self,
        items: List[WorkItem],
        processor: Callable[[WorkItem, Any], Any],
        context: Any = None
    ) -> BatchResult:
        """
        Execute items sequentially, passing context between items.

        Use when: Items depend on each other's output.
        """
        start_time = datetime.now()
        results = []
        current_context = context

        for i, item in enumerate(items):
            item.status = "running"
            item.started_at = datetime.now().isoformat()

            try:
                # Pass accumulated context to processor
                item.result = await processor(item, current_context)
                item.status = "completed"

                # Update context for next item (if processor returns new context)
                if isinstance(item.result, dict) and "context" in item.result:
                    current_context = item.result["context"]

            except Exception as e:
                item.status = "failed"
                item.error = str(e)

            item.completed_at = datetime.now().isoformat()
            results.append(item)

            # Progress callback
            if self.on_progress:
                self.on_progress(i + 1, len(items))

        total_time = (datetime.now() - start_time).total_seconds()

        return BatchResult(
            workflow_type="sequential",
            total_items=len(items),
            completed=sum(1 for r in results if r.status == "completed"),
            failed=sum(1 for r in results if r.status == "failed"),
            total_time_seconds=total_time,
            items=[self._item_to_dict(r) for r in results],
            errors=[r.error for r in results if r.error]
        )

    async def execute_parallel(
        self,
        items: List[WorkItem],
        processor: Callable[[WorkItem], Any]
    ) -> BatchResult:
        """
        Execute items in parallel with concurrency limit.

        Use when: Items are independent of each other.
        """
        start_time = datetime.now()
        semaphore = asyncio.Semaphore(self.max_concurrent)
        completed_count = 0

        async def process_with_semaphore(item: WorkItem) -> WorkItem:
            nonlocal completed_count
            async with semaphore:
                item.status = "running"
                item.started_at = datetime.now().isoformat()

                try:
                    item.result = await asyncio.wait_for(
                        processor(item),
                        timeout=self.timeout_per_item
                    )
                    item.status = "completed"
                except asyncio.TimeoutError:
                    item.status = "failed"
                    item.error = f"Timeout after {self.timeout_per_item}s"
                except Exception as e:
                    item.status = "failed"
                    item.error = str(e)

                item.completed_at = datetime.now().isoformat()
                completed_count += 1

                if self.on_progress:
                    self.on_progress(completed_count, len(items))

                return item

        # Execute all items concurrently
        results = await asyncio.gather(
            *[process_with_semaphore(item) for item in items],
            return_exceptions=True
        )

        # Handle any gather exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                items[i].status = "failed"
                items[i].error = str(result)
                processed_results.append(items[i])
            else:
                processed_results.append(result)

        total_time = (datetime.now() - start_time).total_seconds()

        return BatchResult(
            workflow_type="parallel",
            total_items=len(items),
            completed=sum(1 for r in processed_results if r.status == "completed"),
            failed=sum(1 for r in processed_results if r.status == "failed"),
            total_time_seconds=total_time,
            items=[self._item_to_dict(r) for r in processed_results],
            errors=[r.error for r in processed_results if r.error]
        )

    def _item_to_dict(self, item: WorkItem) -> Dict[str, Any]:
        return {
            "item_id": item.item_id,
            "status": item.status,
            "result": item.result,
            "error": item.error,
            "started_at": item.started_at,
            "completed_at": item.completed_at
        }
```

### Usage Example

```python
# Define processor
async def analyze_file(item: WorkItem, context: Any = None) -> Dict[str, Any]:
    # Your analysis logic here
    return {"file": item.data, "issues": [], "context": {}}

# Create executor
executor = BatchExecutor(
    workflow_type=WorkflowType.PARALLEL,
    max_concurrent=5,
    on_progress=lambda done, total: print(f"Progress: {done}/{total}")
)

# Create work items
items = [WorkItem(item_id=f"file_{i}", data=f) for i, f in enumerate(file_list)]

# Execute
result = await executor.execute_parallel(items, analyze_file)
print(f"Completed: {result.completed}/{result.total_items}")
```

## PATTERN 5: THREE-LAYER CACHING

For 85-95% cost savings through intelligent caching.

### Cache Layer Configuration

```python
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import hashlib
import json


@dataclass
class CacheLayer:
    """Single cache layer configuration."""
    name: str                    # "system", "tools", "conversation"
    enabled: bool = True
    ttl_seconds: int = 300       # 5 minutes (per Claude API cache window)
    max_entries: int = 1000
    savings_percentage: float = 0.0  # Tracked savings

    # Layer-specific expected savings
    EXPECTED_SAVINGS = {
        "system": 0.18,       # 15-20% savings
        "tools": 0.375,       # 35-40% savings
        "conversation": 0.375 # 30-45% savings
    }

    def __post_init__(self):
        self.savings_percentage = self.EXPECTED_SAVINGS.get(self.name, 0.0)


@dataclass
class CacheEntry:
    """Individual cache entry."""
    key: str
    value: Any
    created_at: float
    ttl_seconds: int
    hits: int = 0
    layer: str = ""

    def is_expired(self) -> bool:
        import time
        return (time.time() - self.created_at) > self.ttl_seconds
```

### Three-Layer Cache Manager

```python
class ThreeLayerCache:
    """
    Three-layer caching strategy for 85-95% cost savings.

    Layers:
    - System: System prompts, model instructions (15-20% savings)
    - Tools: Tool definitions, schemas (35-40% savings)
    - Conversation: Context, history (30-45% savings)

    Pattern from PLAYBOOK-1 and agent_orchestrator.py.
    """

    def __init__(
        self,
        system_enabled: bool = True,
        tools_enabled: bool = True,
        conversation_enabled: bool = True,
        ttl_seconds: int = 300
    ):
        self.layers = {
            "system": CacheLayer("system", system_enabled, ttl_seconds),
            "tools": CacheLayer("tools", tools_enabled, ttl_seconds),
            "conversation": CacheLayer("conversation", conversation_enabled, ttl_seconds)
        }
        self.cache: Dict[str, Dict[str, CacheEntry]] = {
            "system": {},
            "tools": {},
            "conversation": {}
        }
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "estimated_savings_usd": 0.0
        }

    def _generate_key(self, content: Any) -> str:
        """Generate cache key from content."""
        if isinstance(content, str):
            content_str = content
        else:
            content_str = json.dumps(content, sort_keys=True, default=str)
        return hashlib.md5(content_str.encode()).hexdigest()

    def get(self, layer: str, content: Any) -> Optional[Any]:
        """
        Get cached value if exists and not expired.

        Returns None if not cached or expired.
        """
        if layer not in self.layers or not self.layers[layer].enabled:
            return None

        key = self._generate_key(content)
        entry = self.cache[layer].get(key)

        if entry and not entry.is_expired():
            entry.hits += 1
            self.stats["hits"] += 1
            return entry.value

        if entry:  # Expired
            del self.cache[layer][key]
            self.stats["evictions"] += 1

        self.stats["misses"] += 1
        return None

    def set(self, layer: str, content: Any, value: Any) -> bool:
        """
        Cache a value in the specified layer.

        Returns True if cached successfully.
        """
        if layer not in self.layers or not self.layers[layer].enabled:
            return False

        layer_config = self.layers[layer]
        key = self._generate_key(content)

        # Evict oldest if at capacity
        layer_cache = self.cache[layer]
        if len(layer_cache) >= layer_config.max_entries:
            oldest_key = min(layer_cache, key=lambda k: layer_cache[k].created_at)
            del layer_cache[oldest_key]
            self.stats["evictions"] += 1

        import time
        layer_cache[key] = CacheEntry(
            key=key,
            value=value,
            created_at=time.time(),
            ttl_seconds=layer_config.ttl_seconds,
            layer=layer
        )
        return True

    def get_or_compute(
        self,
        layer: str,
        content: Any,
        compute_fn: Callable[[], Any]
    ) -> Tuple[Any, bool]:
        """
        Get from cache or compute and cache.

        Returns: (value, was_cached)
        """
        cached = self.get(layer, content)
        if cached is not None:
            return cached, True

        value = compute_fn()
        self.set(layer, content, value)
        return value, False

    def estimate_savings(self, base_cost_usd: float) -> Dict[str, Any]:
        """
        Estimate cost savings from caching.

        Based on: savings = cache_hit_rate × layer_savings × base_cost
        """
        total_requests = self.stats["hits"] + self.stats["misses"]
        if total_requests == 0:
            return {"total_savings_usd": 0.0, "hit_rate": 0.0}

        hit_rate = self.stats["hits"] / total_requests

        # Calculate per-layer contribution
        layer_savings = {}
        total_savings = 0.0

        for layer_name, layer_config in self.layers.items():
            if layer_config.enabled:
                layer_contribution = hit_rate * layer_config.savings_percentage * base_cost_usd
                layer_savings[layer_name] = round(layer_contribution, 4)
                total_savings += layer_contribution

        return {
            "total_savings_usd": round(total_savings, 4),
            "hit_rate": round(hit_rate, 3),
            "layer_savings": layer_savings,
            "cache_stats": self.stats
        }

    def clear(self, layer: Optional[str] = None):
        """Clear cache for one layer or all layers."""
        if layer:
            self.cache[layer] = {}
        else:
            for layer_name in self.cache:
                self.cache[layer_name] = {}

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        total_entries = sum(len(c) for c in self.cache.values())
        return {
            "total_entries": total_entries,
            "entries_by_layer": {k: len(v) for k, v in self.cache.items()},
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "evictions": self.stats["evictions"],
            "hit_rate": self.stats["hits"] / max(1, self.stats["hits"] + self.stats["misses"])
        }
```

## PATTERN 6: COST TRACKING

For budget enforcement and spend reporting.

### Cost Tracker

```python
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum


class CostCategory(Enum):
    """Cost categories for tracking."""
    INPUT_TOKENS = "input_tokens"
    OUTPUT_TOKENS = "output_tokens"
    CACHE_READ = "cache_read"
    CACHE_WRITE = "cache_write"
    API_CALLS = "api_calls"


@dataclass
class CostEntry:
    """Single cost entry."""
    category: str
    amount_usd: float
    tokens: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CostBudget:
    """Budget configuration."""
    max_usd: float
    warn_at_percentage: float = 0.8  # Warn at 80%
    enforce: bool = True  # Raise error when exceeded


class CostTracker:
    """
    Track costs and enforce budgets.

    Pattern from cost_analyzer.py and agent_orchestrator.py.
    """

    # Claude API pricing (per 1M tokens)
    PRICING = {
        "input_standard": 3.00,
        "output_standard": 15.00,
        "cache_read": 0.30,     # 90% savings
        "cache_write": 3.75,    # 25% overhead
    }

    def __init__(self, budget: Optional[CostBudget] = None):
        self.budget = budget
        self.entries: List[CostEntry] = []
        self.total_spent_usd = 0.0
        self.warnings_issued = 0

    def record(
        self,
        category: CostCategory,
        tokens: int = 0,
        cost_usd: Optional[float] = None,
        metadata: Dict[str, Any] = None
    ) -> CostEntry:
        """
        Record a cost entry.

        If cost_usd not provided, calculates from tokens.
        """
        if cost_usd is None:
            cost_usd = self._calculate_cost(category, tokens)

        entry = CostEntry(
            category=category.value,
            amount_usd=cost_usd,
            tokens=tokens,
            metadata=metadata or {}
        )
        self.entries.append(entry)
        self.total_spent_usd += cost_usd

        # Check budget
        self._check_budget()

        return entry

    def _calculate_cost(self, category: CostCategory, tokens: int) -> float:
        """Calculate cost from tokens."""
        pricing_map = {
            CostCategory.INPUT_TOKENS: self.PRICING["input_standard"],
            CostCategory.OUTPUT_TOKENS: self.PRICING["output_standard"],
            CostCategory.CACHE_READ: self.PRICING["cache_read"],
            CostCategory.CACHE_WRITE: self.PRICING["cache_write"],
        }
        rate = pricing_map.get(category, self.PRICING["input_standard"])
        return (tokens / 1_000_000) * rate

    def _check_budget(self):
        """Check budget and warn/enforce limits."""
        if not self.budget:
            return

        spent_percentage = self.total_spent_usd / self.budget.max_usd

        # Warning threshold
        if spent_percentage >= self.budget.warn_at_percentage:
            if self.warnings_issued == 0:
                import logging
                logging.warning(
                    f"Cost warning: Spent ${self.total_spent_usd:.4f} "
                    f"({spent_percentage:.1%} of ${self.budget.max_usd} budget)"
                )
            self.warnings_issued += 1

        # Enforcement
        if self.budget.enforce and spent_percentage >= 1.0:
            raise RuntimeError(
                f"Budget exceeded: Spent ${self.total_spent_usd:.4f} "
                f"(limit: ${self.budget.max_usd})"
            )

    def get_summary(self) -> Dict[str, Any]:
        """Get cost summary for JSON output."""
        by_category = {}
        for entry in self.entries:
            cat = entry.category
            if cat not in by_category:
                by_category[cat] = {"count": 0, "tokens": 0, "cost_usd": 0.0}
            by_category[cat]["count"] += 1
            by_category[cat]["tokens"] += entry.tokens
            by_category[cat]["cost_usd"] += entry.amount_usd

        summary = {
            "total_cost_usd": round(self.total_spent_usd, 6),
            "total_entries": len(self.entries),
            "by_category": {k: {**v, "cost_usd": round(v["cost_usd"], 6)}
                           for k, v in by_category.items()},
        }

        if self.budget:
            summary["budget"] = {
                "max_usd": self.budget.max_usd,
                "spent_percentage": round(self.total_spent_usd / self.budget.max_usd * 100, 1),
                "remaining_usd": round(self.budget.max_usd - self.total_spent_usd, 6)
            }

        return summary

    def estimate_remaining_capacity(self, avg_tokens_per_operation: int) -> int:
        """Estimate how many more operations fit in budget."""
        if not self.budget:
            return -1  # Unlimited

        remaining = self.budget.max_usd - self.total_spent_usd
        cost_per_op = self._calculate_cost(CostCategory.INPUT_TOKENS, avg_tokens_per_operation)
        if cost_per_op <= 0:
            return -1

        return int(remaining / cost_per_op)
```

## PATTERN 7: CONFIGURATION LOADING

For flexible configuration from multiple sources.

### Configuration Loader

```python
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, Type, TypeVar
from pathlib import Path
import json
import os


T = TypeVar('T')


@dataclass
class ConfigSource:
    """Track where configuration values came from."""
    source: str  # "default", "file", "cli", "env"
    path: Optional[str] = None


class ConfigLoader:
    """
    Load configuration from multiple sources with precedence.

    Precedence (highest to lowest):
    1. CLI arguments
    2. Environment variables
    3. Config file
    4. Defaults

    Pattern from various tools in synthesis-rules.
    """

    def __init__(
        self,
        config_class: Type[T],
        env_prefix: str = "",
        config_file: Optional[str] = None
    ):
        """
        Initialize config loader.

        Args:
            config_class: Dataclass to load configuration into
            env_prefix: Prefix for environment variables (e.g., "MYAGENT_")
            config_file: Path to JSON config file
        """
        self.config_class = config_class
        self.env_prefix = env_prefix
        self.config_file = config_file
        self.sources: Dict[str, ConfigSource] = {}

    def load(self, cli_args: Optional[Dict[str, Any]] = None) -> T:
        """
        Load configuration from all sources.

        Returns:
            Instance of config_class with merged configuration
        """
        # Start with defaults from dataclass
        config_dict = self._get_defaults()
        for key in config_dict:
            self.sources[key] = ConfigSource("default")

        # Layer 1: Config file
        if self.config_file:
            file_config = self._load_from_file()
            for key, value in file_config.items():
                if value is not None:
                    config_dict[key] = value
                    self.sources[key] = ConfigSource("file", self.config_file)

        # Layer 2: Environment variables
        env_config = self._load_from_env()
        for key, value in env_config.items():
            if value is not None:
                config_dict[key] = value
                self.sources[key] = ConfigSource("env", f"{self.env_prefix}{key.upper()}")

        # Layer 3: CLI arguments (highest precedence)
        if cli_args:
            for key, value in cli_args.items():
                if value is not None:
                    config_dict[key] = value
                    self.sources[key] = ConfigSource("cli")

        return self.config_class(**config_dict)

    def _get_defaults(self) -> Dict[str, Any]:
        """Get default values from dataclass fields."""
        import dataclasses
        defaults = {}
        for f in dataclasses.fields(self.config_class):
            if f.default is not dataclasses.MISSING:
                defaults[f.name] = f.default
            elif f.default_factory is not dataclasses.MISSING:
                defaults[f.name] = f.default_factory()
            else:
                defaults[f.name] = None
        return defaults

    def _load_from_file(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        if not self.config_file:
            return {}

        path = Path(self.config_file)
        if not path.exists():
            return {}

        try:
            with open(path) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def _load_from_env(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        config = {}
        import dataclasses

        for f in dataclasses.fields(self.config_class):
            env_name = f"{self.env_prefix}{f.name.upper()}"
            env_value = os.environ.get(env_name)

            if env_value is not None:
                # Convert to appropriate type
                config[f.name] = self._convert_type(env_value, f.type)

        return config

    def _convert_type(self, value: str, target_type: Any) -> Any:
        """Convert string value to target type."""
        if target_type == bool or target_type == Optional[bool]:
            return value.lower() in ('true', '1', 'yes', 'on')
        elif target_type == int or target_type == Optional[int]:
            return int(value)
        elif target_type == float or target_type == Optional[float]:
            return float(value)
        elif target_type == list or 'List' in str(target_type):
            return value.split(',')
        return value

    def get_sources(self) -> Dict[str, Dict[str, Any]]:
        """Get source information for each config value."""
        return {k: asdict(v) for k, v in self.sources.items()}
```

### Usage Example

```python
@dataclass
class AgentConfig:
    verbose: bool = False
    safe_mode: bool = False
    max_iterations: int = 10
    timeout_seconds: int = 300
    output_format: str = "json"

# Load configuration
loader = ConfigLoader(
    config_class=AgentConfig,
    env_prefix="MYAGENT_",
    config_file="config.json"
)

# CLI args from argparse
cli_args = {"verbose": True, "max_iterations": 5}

config = loader.load(cli_args)
print(f"Config loaded: verbose={config.verbose}, max_iterations={config.max_iterations}")
print(f"Sources: {loader.get_sources()}")
```

## PATTERN 8: PROGRESS CALLBACKS

For real-time status updates during long operations.

### Progress Reporter

```python
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Any
from datetime import datetime
from enum import Enum


class ProgressStage(Enum):
    """Stages of operation progress."""
    INITIALIZING = "initializing"
    RUNNING = "running"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ProgressUpdate:
    """Single progress update."""
    current: int
    total: int
    stage: str
    message: str = ""
    percentage: float = 0.0
    elapsed_seconds: float = 0.0
    eta_seconds: Optional[float] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ProgressReporter:
    """
    Report progress with callbacks and ETA calculation.

    Pattern for long-running agent operations.
    """

    def __init__(
        self,
        total: int,
        on_update: Optional[Callable[[ProgressUpdate], None]] = None,
        on_complete: Optional[Callable[[ProgressUpdate], None]] = None,
        update_interval: int = 1  # Update every N items
    ):
        self.total = total
        self.current = 0
        self.stage = ProgressStage.INITIALIZING
        self.on_update = on_update
        self.on_complete = on_complete
        self.update_interval = update_interval
        self.start_time = datetime.now()
        self.history: List[ProgressUpdate] = []

    def start(self, message: str = "Starting operation"):
        """Signal start of operation."""
        self.stage = ProgressStage.RUNNING
        self.start_time = datetime.now()
        self._emit_update(message)

    def advance(self, count: int = 1, message: str = ""):
        """Advance progress by count."""
        self.current = min(self.current + count, self.total)

        if self.current % self.update_interval == 0 or self.current == self.total:
            self._emit_update(message)

    def set_progress(self, current: int, message: str = ""):
        """Set progress to specific value."""
        self.current = min(max(0, current), self.total)
        self._emit_update(message)

    def complete(self, message: str = "Operation completed"):
        """Signal completion."""
        self.current = self.total
        self.stage = ProgressStage.COMPLETED
        update = self._emit_update(message)

        if self.on_complete:
            self.on_complete(update)

    def fail(self, message: str = "Operation failed"):
        """Signal failure."""
        self.stage = ProgressStage.FAILED
        self._emit_update(message)

    def _emit_update(self, message: str = "") -> ProgressUpdate:
        """Emit progress update."""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        percentage = (self.current / self.total * 100) if self.total > 0 else 0

        # Calculate ETA
        eta = None
        if self.current > 0 and self.current < self.total:
            rate = self.current / elapsed
            remaining = self.total - self.current
            eta = remaining / rate if rate > 0 else None

        update = ProgressUpdate(
            current=self.current,
            total=self.total,
            stage=self.stage.value,
            message=message,
            percentage=round(percentage, 1),
            elapsed_seconds=round(elapsed, 2),
            eta_seconds=round(eta, 2) if eta else None
        )

        self.history.append(update)

        if self.on_update:
            self.on_update(update)

        return update

    def get_summary(self) -> dict:
        """Get progress summary."""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        return {
            "current": self.current,
            "total": self.total,
            "percentage": round(self.current / self.total * 100, 1) if self.total > 0 else 0,
            "stage": self.stage.value,
            "elapsed_seconds": round(elapsed, 2),
            "updates_emitted": len(self.history)
        }
```

### Usage Example

```python
# Define progress callback
def on_progress(update: ProgressUpdate):
    bar_width = 30
    filled = int(bar_width * update.current / update.total)
    bar = "█" * filled + "░" * (bar_width - filled)
    eta = f"ETA: {update.eta_seconds:.0f}s" if update.eta_seconds else ""
    print(f"\r[{bar}] {update.percentage:.1f}% {update.message} {eta}", end="")

# Create reporter
reporter = ProgressReporter(
    total=100,
    on_update=on_progress,
    update_interval=5
)

# Use in processing loop
reporter.start("Processing files")
for i, file in enumerate(files):
    process(file)
    reporter.advance(message=f"Processed {file}")

reporter.complete("All files processed")
```

## PATTERN 9: VALIDATION LAYER

For input validation with clear error messages.

### Validation Classes

```python
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable, Union
from enum import Enum
import re


class ValidationSeverity(Enum):
    """Severity of validation issue."""
    ERROR = "error"      # Must be fixed
    WARNING = "warning"  # Should be fixed
    INFO = "info"        # Informational


@dataclass
class ValidationIssue:
    """Single validation issue."""
    field: str
    message: str
    severity: str
    value: Any = None
    suggestion: str = ""


@dataclass
class ValidationResult:
    """Result of validation."""
    valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]


class InputValidator:
    """
    Validate inputs with schema-like rules.

    Pattern from parser_adapters.py and composition_validator.py.
    """

    def __init__(self):
        self.rules: Dict[str, List[Callable]] = {}

    def add_rule(
        self,
        field: str,
        validator: Callable[[Any], Union[bool, str]],
        message: str = "",
        severity: ValidationSeverity = ValidationSeverity.ERROR
    ):
        """
        Add validation rule for a field.

        Args:
            field: Field name to validate
            validator: Function returning True (valid) or error message
            message: Default error message
            severity: Issue severity
        """
        if field not in self.rules:
            self.rules[field] = []

        self.rules[field].append({
            "validator": validator,
            "message": message,
            "severity": severity
        })

    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Validate data against all rules.

        Returns:
            ValidationResult with issues
        """
        issues = []

        for field, rules in self.rules.items():
            value = data.get(field)

            for rule in rules:
                result = rule["validator"](value)

                if result is not True:
                    message = result if isinstance(result, str) else rule["message"]
                    issues.append(ValidationIssue(
                        field=field,
                        message=message,
                        severity=rule["severity"].value,
                        value=value
                    ))

        return ValidationResult(
            valid=not any(i.severity == "error" for i in issues),
            issues=issues
        )

    # Built-in validators

    @staticmethod
    def required(value: Any) -> Union[bool, str]:
        """Value must be present and not None/empty."""
        if value is None or value == "" or value == []:
            return "This field is required"
        return True

    @staticmethod
    def is_type(expected_type: type) -> Callable[[Any], Union[bool, str]]:
        """Value must be of specified type."""
        def validator(value: Any) -> Union[bool, str]:
            if value is None:
                return True  # Let required handle None
            if not isinstance(value, expected_type):
                return f"Expected {expected_type.__name__}, got {type(value).__name__}"
            return True
        return validator

    @staticmethod
    def min_value(minimum: float) -> Callable[[Any], Union[bool, str]]:
        """Numeric value must be >= minimum."""
        def validator(value: Any) -> Union[bool, str]:
            if value is None:
                return True
            if value < minimum:
                return f"Value must be >= {minimum}"
            return True
        return validator

    @staticmethod
    def max_value(maximum: float) -> Callable[[Any], Union[bool, str]]:
        """Numeric value must be <= maximum."""
        def validator(value: Any) -> Union[bool, str]:
            if value is None:
                return True
            if value > maximum:
                return f"Value must be <= {maximum}"
            return True
        return validator

    @staticmethod
    def in_list(allowed: List[Any]) -> Callable[[Any], Union[bool, str]]:
        """Value must be in allowed list."""
        def validator(value: Any) -> Union[bool, str]:
            if value is None:
                return True
            if value not in allowed:
                return f"Must be one of: {allowed}"
            return True
        return validator

    @staticmethod
    def matches_pattern(pattern: str) -> Callable[[Any], Union[bool, str]]:
        """String must match regex pattern."""
        compiled = re.compile(pattern)
        def validator(value: Any) -> Union[bool, str]:
            if value is None:
                return True
            if not isinstance(value, str):
                return "Must be a string"
            if not compiled.match(value):
                return f"Must match pattern: {pattern}"
            return True
        return validator

    @staticmethod
    def file_exists() -> Callable[[Any], Union[bool, str]]:
        """Path must exist as a file."""
        def validator(value: Any) -> Union[bool, str]:
            if value is None:
                return True
            from pathlib import Path
            if not Path(value).is_file():
                return f"File not found: {value}"
            return True
        return validator
```

### Usage Example

```python
# Create validator
validator = InputValidator()

# Add rules
validator.add_rule("file_path", InputValidator.required, "File path is required")
validator.add_rule("file_path", InputValidator.file_exists(), "File must exist")
validator.add_rule("max_iterations", InputValidator.is_type(int))
validator.add_rule("max_iterations", InputValidator.min_value(1), "Must be >= 1")
validator.add_rule("max_iterations", InputValidator.max_value(100), "Must be <= 100")
validator.add_rule("output_format", InputValidator.in_list(["json", "text", "csv"]))

# Validate input
result = validator.validate({
    "file_path": "./example.py",
    "max_iterations": 10,
    "output_format": "json"
})

if not result.valid:
    for issue in result.errors:
        print(f"Error in {issue.field}: {issue.message}")
```

## PATTERN 10: ERROR RECOVERY

For resilient operations with retry and fallback strategies.

### Error Recovery Classes

```python
from dataclasses import dataclass, field
from typing import Callable, TypeVar, Optional, List, Any
from enum import Enum
import time
import logging

T = TypeVar('T')


class RecoveryStrategy(Enum):
    """Error recovery strategies."""
    RETRY = "retry"          # Retry with backoff
    FALLBACK = "fallback"    # Use fallback function
    ABORT = "abort"          # Fail immediately
    SKIP = "skip"            # Skip and continue


@dataclass
class RetryConfig:
    """Configuration for retry strategy."""
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True  # Add randomness to prevent thundering herd

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for attempt number."""
        delay = self.initial_delay * (self.exponential_base ** attempt)
        delay = min(delay, self.max_delay)

        if self.jitter:
            import random
            delay *= (0.5 + random.random())

        return delay


@dataclass
class RecoveryResult:
    """Result of recovery attempt."""
    success: bool
    value: Any = None
    attempts: int = 0
    errors: List[str] = field(default_factory=list)
    strategy_used: str = ""
    total_time_seconds: float = 0.0


class ErrorRecovery:
    """
    Execute operations with automatic error recovery.

    Pattern from agent_orchestrator.py.
    """

    def __init__(
        self,
        strategy: RecoveryStrategy = RecoveryStrategy.RETRY,
        retry_config: Optional[RetryConfig] = None,
        fallback_fn: Optional[Callable[[], T]] = None,
        on_retry: Optional[Callable[[int, Exception], None]] = None,
        retryable_exceptions: tuple = (Exception,)
    ):
        self.strategy = strategy
        self.retry_config = retry_config or RetryConfig()
        self.fallback_fn = fallback_fn
        self.on_retry = on_retry
        self.retryable_exceptions = retryable_exceptions
        self.logger = logging.getLogger(__name__)

    def execute(self, operation: Callable[[], T]) -> RecoveryResult:
        """
        Execute operation with recovery.

        Args:
            operation: Function to execute

        Returns:
            RecoveryResult with success status and value
        """
        start_time = time.time()
        errors = []
        attempt = 0

        while True:
            attempt += 1

            try:
                value = operation()
                return RecoveryResult(
                    success=True,
                    value=value,
                    attempts=attempt,
                    errors=errors,
                    strategy_used=self.strategy.value,
                    total_time_seconds=time.time() - start_time
                )

            except self.retryable_exceptions as e:
                error_msg = f"Attempt {attempt}: {type(e).__name__}: {str(e)}"
                errors.append(error_msg)
                self.logger.warning(error_msg)

                # Handle based on strategy
                if self.strategy == RecoveryStrategy.ABORT:
                    return RecoveryResult(
                        success=False,
                        attempts=attempt,
                        errors=errors,
                        strategy_used="abort",
                        total_time_seconds=time.time() - start_time
                    )

                elif self.strategy == RecoveryStrategy.SKIP:
                    return RecoveryResult(
                        success=True,
                        value=None,
                        attempts=attempt,
                        errors=errors,
                        strategy_used="skip",
                        total_time_seconds=time.time() - start_time
                    )

                elif self.strategy == RecoveryStrategy.RETRY:
                    if attempt >= self.retry_config.max_attempts:
                        # Exhausted retries, try fallback
                        if self.fallback_fn:
                            try:
                                value = self.fallback_fn()
                                return RecoveryResult(
                                    success=True,
                                    value=value,
                                    attempts=attempt,
                                    errors=errors,
                                    strategy_used="fallback",
                                    total_time_seconds=time.time() - start_time
                                )
                            except Exception as fe:
                                errors.append(f"Fallback failed: {str(fe)}")

                        return RecoveryResult(
                            success=False,
                            attempts=attempt,
                            errors=errors,
                            strategy_used="retry_exhausted",
                            total_time_seconds=time.time() - start_time
                        )

                    # Retry with backoff
                    delay = self.retry_config.get_delay(attempt - 1)
                    self.logger.info(f"Retrying in {delay:.2f}s...")

                    if self.on_retry:
                        self.on_retry(attempt, e)

                    time.sleep(delay)

                elif self.strategy == RecoveryStrategy.FALLBACK:
                    if self.fallback_fn:
                        try:
                            value = self.fallback_fn()
                            return RecoveryResult(
                                success=True,
                                value=value,
                                attempts=attempt,
                                errors=errors,
                                strategy_used="fallback",
                                total_time_seconds=time.time() - start_time
                            )
                        except Exception as fe:
                            errors.append(f"Fallback failed: {str(fe)}")

                    return RecoveryResult(
                        success=False,
                        attempts=attempt,
                        errors=errors,
                        strategy_used="fallback_failed",
                        total_time_seconds=time.time() - start_time
                    )
```

### Usage Example

```python
# Configure recovery
recovery = ErrorRecovery(
    strategy=RecoveryStrategy.RETRY,
    retry_config=RetryConfig(max_attempts=3, initial_delay=1.0),
    fallback_fn=lambda: {"status": "fallback", "data": []},
    on_retry=lambda attempt, e: print(f"Retry {attempt}: {e}")
)

# Execute with recovery
def risky_operation():
    # ... operation that might fail
    return {"status": "success", "data": [1, 2, 3]}

result = recovery.execute(risky_operation)
if result.success:
    print(f"Success after {result.attempts} attempts")
    print(f"Strategy used: {result.strategy_used}")
else:
    print(f"Failed after {result.attempts} attempts")
    print(f"Errors: {result.errors}")
```

## PATTERN 11: PLUGIN ARCHITECTURE

For extensible agents with dynamic capabilities.

### Plugin System

```python
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable, Type
from pathlib import Path
from abc import ABC, abstractmethod
import importlib.util
import logging


@dataclass
class PluginMetadata:
    """Plugin metadata."""
    name: str
    version: str
    description: str
    author: str = ""
    dependencies: List[str] = field(default_factory=list)
    hooks: List[str] = field(default_factory=list)


class PluginInterface(ABC):
    """
    Base interface for all plugins.

    All plugins must inherit from this class.
    """

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        pass

    def on_load(self, context: Dict[str, Any]) -> None:
        """Called when plugin is loaded."""
        pass

    def on_unload(self) -> None:
        """Called when plugin is unloaded."""
        pass


class HookRegistry:
    """
    Registry for plugin hooks.

    Hooks allow plugins to intercept and modify agent behavior.
    """

    def __init__(self):
        self.hooks: Dict[str, List[Callable]] = {}

    def register(self, hook_name: str, handler: Callable):
        """Register a hook handler."""
        if hook_name not in self.hooks:
            self.hooks[hook_name] = []
        self.hooks[hook_name].append(handler)

    def unregister(self, hook_name: str, handler: Callable):
        """Unregister a hook handler."""
        if hook_name in self.hooks:
            self.hooks[hook_name] = [h for h in self.hooks[hook_name] if h != handler]

    def call(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """
        Call all handlers for a hook.

        Returns list of results from each handler.
        """
        results = []
        for handler in self.hooks.get(hook_name, []):
            try:
                result = handler(*args, **kwargs)
                results.append(result)
            except Exception as e:
                logging.error(f"Hook {hook_name} handler error: {e}")
        return results

    def call_until(self, hook_name: str, predicate: Callable[[Any], bool], *args, **kwargs) -> Optional[Any]:
        """
        Call handlers until one returns a value matching predicate.

        Useful for hooks that can "handle" a request.
        """
        for handler in self.hooks.get(hook_name, []):
            try:
                result = handler(*args, **kwargs)
                if predicate(result):
                    return result
            except Exception as e:
                logging.error(f"Hook {hook_name} handler error: {e}")
        return None


class PluginManager:
    """
    Manage plugin loading, lifecycle, and hooks.

    Pattern from HAL add-ons architecture.
    """

    # Standard hooks
    HOOKS = [
        "pre_process",      # Before processing starts
        "post_process",     # After processing completes
        "on_finding",       # When a finding is detected
        "on_error",         # When an error occurs
        "transform_input",  # Transform input before processing
        "transform_output", # Transform output before returning
    ]

    def __init__(self, plugin_dir: Optional[str] = None):
        self.plugin_dir = Path(plugin_dir) if plugin_dir else None
        self.plugins: Dict[str, PluginInterface] = {}
        self.hooks = HookRegistry()
        self.logger = logging.getLogger(__name__)

    def discover(self) -> List[str]:
        """
        Discover plugins in plugin directory.

        Returns list of plugin file paths.
        """
        if not self.plugin_dir or not self.plugin_dir.exists():
            return []

        plugins = []
        for path in self.plugin_dir.glob("*.py"):
            if not path.name.startswith("_"):
                plugins.append(str(path))

        return plugins

    def load(self, plugin_path: str, context: Dict[str, Any] = None) -> bool:
        """
        Load a plugin from file.

        Args:
            plugin_path: Path to plugin Python file
            context: Context to pass to plugin on_load

        Returns:
            True if loaded successfully
        """
        try:
            # Load module from file
            spec = importlib.util.spec_from_file_location("plugin", plugin_path)
            if spec is None or spec.loader is None:
                return False

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find plugin class
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and
                    issubclass(attr, PluginInterface) and
                    attr is not PluginInterface):
                    plugin_class = attr
                    break

            if not plugin_class:
                self.logger.warning(f"No PluginInterface found in {plugin_path}")
                return False

            # Instantiate and register
            plugin = plugin_class()
            plugin.on_load(context or {})

            self.plugins[plugin.metadata.name] = plugin

            # Register hooks
            for hook_name in plugin.metadata.hooks:
                if hasattr(plugin, f"handle_{hook_name}"):
                    handler = getattr(plugin, f"handle_{hook_name}")
                    self.hooks.register(hook_name, handler)

            self.logger.info(f"Loaded plugin: {plugin.metadata.name} v{plugin.metadata.version}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to load plugin {plugin_path}: {e}")
            return False

    def unload(self, plugin_name: str) -> bool:
        """Unload a plugin."""
        if plugin_name not in self.plugins:
            return False

        plugin = self.plugins[plugin_name]

        # Unregister hooks
        for hook_name in plugin.metadata.hooks:
            if hasattr(plugin, f"handle_{hook_name}"):
                handler = getattr(plugin, f"handle_{hook_name}")
                self.hooks.unregister(hook_name, handler)

        plugin.on_unload()
        del self.plugins[plugin_name]

        self.logger.info(f"Unloaded plugin: {plugin_name}")
        return True

    def load_all(self, context: Dict[str, Any] = None) -> int:
        """
        Load all discovered plugins.

        Returns number of plugins loaded.
        """
        count = 0
        for plugin_path in self.discover():
            if self.load(plugin_path, context):
                count += 1
        return count

    def get_plugin(self, name: str) -> Optional[PluginInterface]:
        """Get plugin by name."""
        return self.plugins.get(name)

    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all loaded plugins."""
        return [
            {
                "name": p.metadata.name,
                "version": p.metadata.version,
                "description": p.metadata.description,
                "hooks": p.metadata.hooks
            }
            for p in self.plugins.values()
        ]

    def call_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Call a hook on all plugins."""
        return self.hooks.call(hook_name, *args, **kwargs)
```

### Example Plugin

```python
class MyAnalyzerPlugin(PluginInterface):
    """Example plugin that adds custom analysis."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="custom_analyzer",
            version="1.0.0",
            description="Adds custom analysis capabilities",
            author="Eyal Nof",
            hooks=["on_finding", "transform_output"]
        )

    def on_load(self, context: Dict[str, Any]) -> None:
        print(f"Custom analyzer loaded with context: {context}")

    def handle_on_finding(self, finding: Dict[str, Any]) -> Dict[str, Any]:
        """Add custom metadata to findings."""
        finding["custom_score"] = self._calculate_score(finding)
        return finding

    def handle_transform_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Add plugin summary to output."""
        output["custom_analyzer_summary"] = {
            "processed": True,
            "enhancements_added": 1
        }
        return output

    def _calculate_score(self, finding: Dict[str, Any]) -> float:
        # Custom scoring logic
        return 0.85
```

### Usage Example

```python
# Create plugin manager
plugins = PluginManager(plugin_dir="./plugins")

# Load all plugins
loaded = plugins.load_all(context={"agent": "my_agent"})
print(f"Loaded {loaded} plugins")

# In your agent processing:
def process_file(file_path: str) -> Dict[str, Any]:
    # Transform input via plugins
    input_data = {"file_path": file_path}
    for result in plugins.call_hook("transform_input", input_data):
        if result:
            input_data = result

    # Process...
    findings = analyze(input_data)

    # Notify plugins of each finding
    for finding in findings:
        plugins.call_hook("on_finding", finding)

    # Transform output via plugins
    output = {"findings": findings}
    for result in plugins.call_hook("transform_output", output):
        if result:
            output = result

    return output
```

## PRODUCTION PATTERN CHECKLIST

When implementing production patterns:

- [ ] Batch/Parallel: WorkflowType enum, BatchExecutor with both modes
- [ ] Three-Layer Caching: CacheLayer, ThreeLayerCache with TTL and stats
- [ ] Cost Tracking: CostTracker with budget enforcement and summary
- [ ] Configuration: ConfigLoader with file/env/cli precedence
- [ ] Progress: ProgressReporter with callbacks and ETA
- [ ] Validation: InputValidator with built-in and custom validators
- [ ] Error Recovery: ErrorRecovery with retry/fallback/abort strategies
- [ ] Plugins: PluginManager with hooks and lifecycle management

## PRODUCTION PATTERN REFERENCES

- agent_orchestrator.py: Batch/parallel, error recovery, caching
- cost_analyzer.py: Cost tracking, budget enforcement
- parser_adapters.py: Validation patterns
- HAL add-ons: Plugin architecture

---

# END OF META-TEMPLATE

Author: Eyal Nof
Version: 3.0 (added 8 production patterns)
Total Patterns: 11 (3 base + 3 HAL + 8 production)
Updated: 2026-01-17

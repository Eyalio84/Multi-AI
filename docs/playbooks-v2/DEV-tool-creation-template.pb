# DEV-tool-creation-template.pb
# Tool Creation Meta-Template for Synthesis Rules Ecosystem
#
# Author: Eyal Nof
# Created: 2026-01-17 (Session 4)
# Purpose: Systematic conversion of Playbooks → Python Tools
#
# This template captures patterns from 49 production tools (November-December 2025)
# Total analyzed: 700,000+ lines of tool code

================================================================================
                          QUICK REFERENCE
================================================================================

Tool Creation Checklist:
[ ] 1. Identify source playbook rules
[ ] 2. Define data models (@dataclass, Enum)
[ ] 3. Implement core logic class
[ ] 4. Add CLI with argparse
[ ] 5. Support JSON output (default)
[ ] 6. Include rules_applied tracking
[ ] 7. Add anti-pattern detection
[ ] 8. Write tests

Estimated Lines by Tool Complexity:
- Simple (calculator): 300-500 lines
- Medium (analyzer): 600-900 lines
- Complex (orchestrator): 900-1400 lines

================================================================================
                          SECTION 1: FILE STRUCTURE
================================================================================

## 1.1 Standard Tool Layout

```
tools/
├── {tool_name}.py           # Main tool implementation
├── test_{tool_name}.py      # Unit tests (optional, same directory)
└── {tool_name}_config.json  # Configuration (optional)
```

## 1.2 File Header Template (COPY-PASTE READY)

```python
#!/usr/bin/env python3
"""
{tool_name}.py - {Tool Title}

{One-paragraph description of what the tool does and why it exists.}

SYNTHESIS RULES APPLIED:
- {rule_id_1}: {brief description}
- {rule_id_2}: {brief description}
- {rule_id_3}: {brief description}

KEY FORMULAS:
- {formula_name}: {formula} (source: {rule_id})

Usage Examples:
    # Basic usage
    python3 {tool_name}.py --input data.json

    # With options
    python3 {tool_name}.py --input data.json --output results.json --verbose

    # Pipe from stdin
    cat data.json | python3 {tool_name}.py --stdin

Created: {YYYY-MM-DD} (SET-{N} {Set Name})
Author: Eyal Nof
"""
```

================================================================================
                          SECTION 2: IMPORTS PATTERN
================================================================================

## 2.1 Standard Imports (All Tools)

```python
import json
import argparse
import sys
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
```

## 2.2 Common Optional Imports

```python
# Path handling (50% of tools)
from pathlib import Path

# Date/time operations (40% of tools)
from datetime import datetime, timedelta

# Math operations (30% of tools)
import math

# Logging (20% of tools - orchestration/complex tools)
import logging

# Async operations (10% of tools - orchestrators only)
import asyncio

# AST parsing (code analysis tools only)
import ast

# Regular expressions (parsing tools)
import re

# Hashing (session/cache tools)
import hashlib
```

## 2.3 NEVER Import (External Dependencies)

```python
# ❌ NO external dependencies - stdlib only
# ❌ import requests
# ❌ import numpy
# ❌ import pandas
# ❌ import anthropic
```

================================================================================
                          SECTION 3: DATA MODELS
================================================================================

## 3.1 Enum Pattern (Categories/Options)

```python
class {Category}Type(Enum):
    """Categorization for {what}."""
    OPTION_A = "option_a"
    OPTION_B = "option_b"
    OPTION_C = "option_c"
```

**Real Example:**

```python
class OptimizationTechnique(Enum):
    """Supported optimization techniques."""
    PROMPT_CACHING = "prompt_caching"
    BATCH_API = "batch_api"
    COMPOUND_OPTIMIZATION = "compound_optimization"


class ComplexityLevel(Enum):
    """Task complexity classification."""
    TRIVIAL = "trivial"
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"
```

## 3.2 Dataclass Pattern (Structured Data)

```python
@dataclass
class {ResultName}:
    """Description of what this represents."""
    field_a: str
    field_b: int
    field_c: float
    optional_field: Optional[str] = None
    list_field: List[str] = field(default_factory=list)
    dict_field: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return asdict(self)
```

**Real Example:**

```python
@dataclass
class Recommendation:
    """Cost optimization recommendation."""
    technique: str
    applicable: bool
    reason: str
    estimated_savings: str
    monthly_savings_usd: float
    implementation_complexity: str
    rules_applied: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AnalysisResult:
    """Complete analysis output."""
    recommendations: List[Dict[str, Any]]
    anti_patterns_detected: List[str]
    meta_insight: str
    analysis_metadata: Dict[str, Any]
    rules_applied: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
```

## 3.3 Validation Pattern (__post_init__)

```python
@dataclass
class ConfigWithValidation:
    """Configuration with validation."""
    max_iterations: int
    timeout_seconds: int
    budget: float

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.max_iterations < 1:
            raise ValueError(f"max_iterations must be >= 1, got {self.max_iterations}")
        if self.timeout_seconds < 30:
            raise ValueError(f"timeout_seconds must be >= 30, got {self.timeout_seconds}")
        if self.budget < 0:
            raise ValueError(f"budget must be >= 0, got {self.budget}")
```

================================================================================
                          SECTION 4: CONSTANTS PATTERN
================================================================================

## 4.1 Pricing/Configuration Constants

```python
# ============================================================================
# Constants and Configuration
# ============================================================================

# API Pricing (per 1M tokens) - as of {date}
PRICING = {
    "input_standard": 3.00,
    "output_standard": 15.00,
    "cache_read": 0.30,
    "cache_write": 3.75,
    "batch_discount": 0.50,
}

# Thresholds for optimization applicability
THRESHOLDS = {
    "min_cached_tokens": 1000,
    "min_requests_for_batch": 10,
    "cache_lifetime_minutes": 5,
}

# Anti-pattern severity levels
ANTI_PATTERN_SEVERITY = {
    "pattern_a": "critical",
    "pattern_b": "high",
    "pattern_c": "medium",
}
```

## 4.2 Base Values by Category

```python
# Base budgets/values by type (from empirical validation)
BASE_VALUES = {
    "type_a": 4000,
    "type_b": 6000,
    "type_c": 8000,
}

# Multipliers for adjustments
MULTIPLIERS = {
    "low": 1.0,
    "moderate": 1.2,
    "high": 1.5,
}
```

================================================================================
                          SECTION 5: CORE LOGIC CLASS
================================================================================

## 5.1 Single-Responsibility Class Pattern

```python
class {ToolName}:
    """
    {Tool description}.

    Implements synthesis rules:
    - {rule_1}
    - {rule_2}

    Formulas:
    - {formula_name}: {formula}
    """

    def __init__(self, verbose: bool = False):
        """Initialize {tool}.

        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose
        self.meta_insights = []

    def analyze_{primary_function}(
        self,
        input_data: Dict[str, Any]
    ) -> {ResultType}:
        """
        Primary analysis function.

        Rule: {rule_id}
        Formula: {formula}

        Args:
            input_data: Input configuration

        Returns:
            {ResultType} with analysis
        """
        # Implementation
        pass

    def detect_anti_patterns(
        self,
        data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Detect anti-patterns in input.

        Rules applied:
        - anti_001: Description
        - anti_002: Description

        Args:
            data: Data to analyze

        Returns:
            List of detected anti-patterns
        """
        anti_patterns = []

        # Check pattern 1
        if condition_1:
            anti_patterns.append({
                "pattern": "pattern_name",
                "severity": "critical",
                "message": "Description of issue",
                "rule": "anti_001",
                "recommendation": "How to fix"
            })

        return anti_patterns
```

## 5.2 Analysis Pipeline Pattern

```python
def run_full_analysis(self, config: Dict[str, Any]) -> AnalysisResult:
    """
    Complete analysis pipeline.

    Steps:
    1. Validate input
    2. Run primary analysis
    3. Detect anti-patterns
    4. Generate recommendations
    5. Compile results

    Args:
        config: Input configuration

    Returns:
        AnalysisResult with all findings
    """
    # Step 1: Validate
    validation = self.validate_input(config)
    if not validation["valid"]:
        return self._error_result(validation["errors"])

    # Step 2: Primary analysis
    primary_result = self.analyze_primary(config)

    # Step 3: Anti-patterns
    anti_patterns = self.detect_anti_patterns(config)

    # Step 4: Recommendations
    recommendations = self.generate_recommendations(
        primary_result,
        anti_patterns
    )

    # Step 5: Compile
    return AnalysisResult(
        recommendations=recommendations,
        anti_patterns_detected=[ap["pattern"] for ap in anti_patterns],
        meta_insight=self._generate_insight(recommendations),
        analysis_metadata={
            "input_summary": self._summarize_input(config),
            "anti_patterns": anti_patterns,
        },
        rules_applied=self._get_applied_rules()
    )
```

================================================================================
                          SECTION 6: CLI PATTERN
================================================================================

## 6.1 Basic CLI (Single Command)

```python
def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="{Tool Name} - {Brief description}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:

  # Basic usage
  python3 {tool_name}.py --input data.json

  # With options
  python3 {tool_name}.py --input data.json --output results.json --pretty

  # From stdin
  cat data.json | python3 {tool_name}.py --stdin

Input Format:
{
  "field_a": "value",
  "field_b": 123
}
        """
    )

    parser.add_argument(
        "--input", "-i",
        type=str,
        help="Path to input JSON file"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Path to output file (default: stdout)"
    )
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="Read JSON input from stdin"
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print summary-only format"
    )

    return parser.parse_args()
```

## 6.2 Advanced CLI (Subcommands)

```python
def main():
    """CLI interface for {tool}."""
    parser = argparse.ArgumentParser(
        description="{Tool Name}"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Command 1: analyze
    analyze_cmd = subparsers.add_parser(
        "analyze",
        help="Run primary analysis"
    )
    analyze_cmd.add_argument(
        "--input", "-i",
        required=True,
        help="Input file or data"
    )
    analyze_cmd.add_argument(
        "--type",
        choices=["type_a", "type_b", "type_c"],
        default="type_a",
        help="Analysis type"
    )

    # Command 2: compare
    compare_cmd = subparsers.add_parser(
        "compare",
        help="Compare options"
    )
    compare_cmd.add_argument(
        "--baseline",
        type=int,
        default=1000,
        help="Baseline value"
    )

    # Command 3: validate
    validate_cmd = subparsers.add_parser(
        "validate",
        help="Validate configuration"
    )
    validate_cmd.add_argument(
        "--strict",
        action="store_true",
        help="Strict validation mode"
    )

    args = parser.parse_args()

    if args.command == "analyze":
        # Handle analyze
        pass
    elif args.command == "compare":
        # Handle compare
        pass
    elif args.command == "validate":
        # Handle validate
        pass
    else:
        parser.print_help()
```

## 6.3 Main Function Pattern

```python
def main():
    """Main CLI entry point."""
    args = parse_arguments()

    # Load input
    input_data = None

    if args.stdin:
        try:
            input_data = json.load(sys.stdin)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON from stdin: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.input:
        try:
            with open(args.input, 'r') as f:
                input_data = json.load(f)
        except FileNotFoundError:
            print(f"Error: File not found: {args.input}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in {args.input}: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Error: Provide --input or --stdin", file=sys.stderr)
        sys.exit(1)

    # Initialize and run
    tool = ToolClass(verbose=args.verbose)
    result = tool.run_full_analysis(input_data)

    # Output
    if args.summary:
        print(format_summary(result))
    else:
        indent = 2 if args.pretty else None
        output = json.dumps(result.to_dict(), indent=indent, default=str)

        if args.output:
            with open(args.output, 'w') as f:
                f.write(output)
            print(f"Results written to {args.output}", file=sys.stderr)
        else:
            print(output)


if __name__ == "__main__":
    main()
```

================================================================================
                          SECTION 7: OUTPUT PATTERNS
================================================================================

## 7.1 Standard JSON Output Structure

```json
{
  "recommendations": [
    {
      "technique": "technique_name",
      "applicable": true,
      "reason": "Why this applies",
      "estimated_savings": "85%",
      "monthly_savings_usd": 150.00,
      "implementation_complexity": "low"
    }
  ],
  "anti_patterns_detected": [
    "pattern_a",
    "pattern_b"
  ],
  "meta_insight": "Summary insight about the analysis",
  "analysis_metadata": {
    "input_summary": {
      "field_a": "value",
      "field_b": 123
    },
    "anti_patterns": [
      {
        "pattern": "pattern_a",
        "severity": "critical",
        "message": "Description",
        "rule": "anti_001",
        "recommendation": "How to fix"
      }
    ]
  },
  "rules_applied": [
    "comp_001_description",
    "dep_002_description",
    "anti_001_description"
  ]
}
```

## 7.2 Summary Text Output Format

```python
def format_summary(result: AnalysisResult) -> str:
    """Format analysis result as human-readable summary."""
    lines = []

    lines.append("=" * 80)
    lines.append("{TOOL NAME} ANALYSIS SUMMARY")
    lines.append("=" * 80)
    lines.append("")

    # Input summary
    lines.append("INPUT PROFILE:")
    for key, value in result.analysis_metadata["input_summary"].items():
        lines.append(f"  {key}: {value}")
    lines.append("")

    # Recommendations
    lines.append("RECOMMENDATIONS:")
    for i, rec in enumerate(result.recommendations, 1):
        lines.append(f"  {i}. {rec['technique'].upper()}")
        lines.append(f"     Applicable: {rec['applicable']}")
        lines.append(f"     Savings: {rec['estimated_savings']}")
        lines.append("")

    # Insight
    lines.append("INSIGHT:")
    lines.append(f"  {result.meta_insight}")
    lines.append("")

    # Anti-patterns
    if result.anti_patterns_detected:
        lines.append("ANTI-PATTERNS DETECTED:")
        for pattern in result.anti_patterns_detected:
            lines.append(f"  - {pattern}")
        lines.append("")

    lines.append("=" * 80)
    return "\n".join(lines)
```

================================================================================
                          SECTION 8: RULES TRACKING
================================================================================

## 8.1 Rules Applied Pattern

```python
def _get_applied_rules(self, context: Dict[str, Any]) -> List[str]:
    """Get list of synthesis rules applied in this analysis."""
    rules = [
        "comp_001_base_rule",
        "dep_001_dependency_rule",
    ]

    # Conditional rules
    if context.get("feature_a_enabled"):
        rules.append("compat_001_feature_a_compatibility")

    if context.get("complexity") in ["complex", "very_complex"]:
        rules.append("constr_001_complexity_constraint")

    return rules
```

## 8.2 Docstring Rules Documentation

```python
def analyze_something(self, data: Dict[str, Any]) -> Result:
    """
    Analyze something.

    Rules applied:
    - comp_001: Component rule description
    - dep_002: Dependency rule description
    - anti_003: Anti-pattern prevention

    Formula: result = base × multiplier × factor
    Source: PLAYBOOK-{N}

    Args:
        data: Input data

    Returns:
        Result with analysis
    """
    pass
```

================================================================================
                          SECTION 9: ANTI-PATTERN DETECTION
================================================================================

## 9.1 Standard Anti-Pattern Check

```python
def detect_anti_patterns(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Detect anti-patterns in configuration/usage.

    Anti-patterns checked:
    - anti_001: Description
    - anti_002: Description
    - anti_003: Description

    Args:
        data: Data to analyze

    Returns:
        List of detected anti-patterns with details
    """
    anti_patterns = []

    # Anti-pattern 1: {Description}
    if condition_for_anti_pattern_1(data):
        anti_patterns.append({
            "pattern": "pattern_name_1",
            "severity": "critical",  # critical, high, medium, low
            "message": "What's wrong",
            "rule": "anti_001_rule_id",
            "recommendation": "How to fix it"
        })

    # Anti-pattern 2: {Description}
    value = data.get("some_value", 0)
    if value > THRESHOLD_MAX:
        anti_patterns.append({
            "pattern": "pattern_name_2",
            "severity": "high",
            "message": f"Value {value} exceeds recommended maximum ({THRESHOLD_MAX})",
            "rule": "anti_002_rule_id",
            "recommendation": f"Reduce value to <= {THRESHOLD_MAX}"
        })

    return anti_patterns
```

================================================================================
                          SECTION 10: FORMULA DOCUMENTATION
================================================================================

## 10.1 Formula in Docstring

```python
def calculate_savings(
    self,
    baseline: float,
    cache_hits: int,
    cache_ratio: float
) -> float:
    """
    Calculate cost savings.

    Formula: savings = baseline × cache_ratio × (1 - (1/cache_hits))
    Source: PLAYBOOK-1 (Cost Optimization)
    Rule: comp_002_cache_savings_formula

    Args:
        baseline: Baseline cost in USD
        cache_hits: Number of cache hits
        cache_ratio: Ratio of cached content (0.0-1.0)

    Returns:
        Estimated savings in USD
    """
    if cache_hits < 2:
        return 0.0

    savings = baseline * cache_ratio * (1 - (1 / cache_hits))
    return round(savings, 2)
```

## 10.2 Formula Tracking in Output

```python
@dataclass
class CalculationResult:
    """Result with formula tracking."""
    value: float
    formula: str
    inputs: Dict[str, Any]
    source_rule: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# Usage:
result = CalculationResult(
    value=150.00,
    formula="savings = baseline × cache_ratio × (1 - 1/hits)",
    inputs={"baseline": 200.0, "cache_ratio": 0.9, "hits": 10},
    source_rule="comp_002_cache_savings_formula"
)
```

================================================================================
                          SECTION 11: TOOL CATEGORIES
================================================================================

## 11.1 Tool Category Reference

The synthesis-rules ecosystem contains 49 tools across 9 categories:

### Cost & Optimization (7 tools)
- cost_analyzer.py - Analyze workloads for cost optimization
- batch_optimizer.py - Optimize batch API configuration
- cache_roi_calculator.py - Calculate caching ROI
- thinking_budget_optimizer.py - Optimize thinking budgets
- thinking_quality_validator.py - Validate thinking quality
- thinking_roi_estimator.py - Estimate thinking ROI
- workflow_analyzer.py - Analyze workflow efficiency

### Agent Orchestration (3 tools)
- agent_orchestrator.py - Multi-agent coordination
- agent_pattern_analyzer.py - Detect agent patterns
- agent_composer.py - Compose agent configurations

### Code Analysis & Generation (6 tools)
- code_review_generator.py - Generate code reviews
- documentation_generator.py - Generate documentation
- tdd_assistant.py - Test-driven development helper
- refactoring_analyzer.py - Suggest refactorings
- composition_validator.py - Validate compositions
- task_classifier.py - Classify task complexity

### Embedding & Semantic (6 tools)
- embedding_generator_cli.py - Generate embeddings
- similarity_search_cli.py - Semantic search
- dimension_inspector_cli.py - Inspect embedding dimensions
- dimension_discovery_assistant.py - Discover patterns
- graph_embedder.py - Graph-based embeddings
- tfidf_indexer.py - TF-IDF indexing

### Parsing & Data (7 tools)
- parser_adapters.py - Multi-format parsing (1343 lines)
- universal_parser.py - Universal parsing interface
- coder_blueprints_parser.py - Parse coder blueprints
- kg_ingestion_tool.py - Knowledge graph ingestion
- markov_predictor.py - Markov chain prediction
- simple_pattern_miner.py - Mine simple patterns
- wikipedia_football_parser.py - Domain-specific parser

### Documentation & Prompts (7 tools)
- readme_generator_swarm.py - Generate READMEs with swarm
- doc_tracker_agent.py - Track documentation changes
- documentation_auditor.py - Audit documentation coverage
- prompt_generator.py - Generate prompts
- ai_studio_prompt_generator.py - AI Studio prompts
- ai_studio_prompt_generator_llm.py - LLM-powered prompts
- ai_studio_prompt_interview.py - Interview-based prompts

### Visualization & UI (3 tools)
- ascii_graph_viz.py - ASCII graph visualization
- textual_viewer.py - TUI viewer
- session_replayer.py - Replay sessions

### Utilities (7 tools)
- tool_registry_builder.py - Build tool registries
- validate_file_naming.py - Validate file names
- migrate_scaffolder.py - Scaffold migrations
- kdtree_spatial_index.py - Spatial indexing
- perceptual_kg_reasoner.py - KG reasoning
- hybrid_predictor.py - Hybrid prediction
- generate_test_interactions.py - Generate test data

### Tests (3 tools)
- test_agent_pattern_analyzer.py
- test_parser_adapters.py
- test_sample.py

================================================================================
                          SECTION 12: PLAYBOOK → TOOL CONVERSION
================================================================================

## 12.1 Conversion Process

```
PLAYBOOK-{N}
    │
    ├── 1. Extract Rules
    │   └── List all rule IDs and formulas
    │
    ├── 2. Identify Core Functions
    │   └── What calculations/analyses are needed?
    │
    ├── 3. Define Data Models
    │   └── @dataclass for inputs/outputs
    │
    ├── 4. Implement Logic
    │   └── One method per rule/formula
    │
    ├── 5. Add CLI
    │   └── argparse with examples
    │
    ├── 6. Track Rules
    │   └── rules_applied in output
    │
    └── 7. Detect Anti-Patterns
        └── Check for rule violations
```

## 12.2 Example: PLAYBOOK-1 → cost_analyzer.py

**Source Playbook Rules:**
- dep_002: Caching requires repeated requests
- comp_001: Cache effectiveness scales with content size
- cons_001: Cache lifetime constraints (5 minute expiration)
- anti_001: Avoid caching for single requests

**Tool Structure:**

```python
# Data Models
@dataclass
class Recommendation:
    technique: str
    applicable: bool
    reason: str
    estimated_savings: str
    monthly_savings_usd: float
    rules_applied: List[str]

# Core Logic
class CostAnalyzer:
    def analyze_caching_opportunity(self, workload):
        """Implements dep_002, comp_001, cons_001, anti_001"""
        pass

    def analyze_batch_opportunity(self, workload):
        """Implements dep_001, cons_003, anti_002"""
        pass

    def detect_anti_patterns(self, workload):
        """Implements anti_001 through anti_008"""
        pass

# CLI
def main():
    parser = argparse.ArgumentParser(...)
    # ... standard CLI pattern
```

## 12.3 Conversion Checklist

For each playbook rule:

| Step | Action | Output |
|------|--------|--------|
| 1 | Extract rule ID | `comp_001_name` |
| 2 | Extract formula | `result = a × b` |
| 3 | Define inputs | `@dataclass Input` |
| 4 | Define outputs | `@dataclass Result` |
| 5 | Implement function | `def analyze_rule()` |
| 6 | Add to CLI | `--option` |
| 7 | Track in output | `rules_applied` |
| 8 | Add anti-pattern | `detect_anti_patterns()` |

================================================================================
                          SECTION 13: COMPLETE TEMPLATE
================================================================================

## 13.1 Full Tool Template (COPY-PASTE READY)

```python
#!/usr/bin/env python3
"""
{tool_name}.py - {Tool Title}

{Description of what the tool does.}

SYNTHESIS RULES APPLIED:
- {rule_1}: {description}
- {rule_2}: {description}

Usage Examples:
    python3 {tool_name}.py --input data.json
    python3 {tool_name}.py --input data.json --output results.json --pretty
    cat data.json | python3 {tool_name}.py --stdin

Created: {YYYY-MM-DD} (SET-{N} {Set Name})
Author: Eyal Nof
"""

import json
import argparse
import sys
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
from enum import Enum


# ============================================================================
# Data Models
# ============================================================================

class {Category}Type(Enum):
    """Categories for {what}."""
    TYPE_A = "type_a"
    TYPE_B = "type_b"


@dataclass
class {Input}Config:
    """Input configuration."""
    field_a: str
    field_b: int
    optional_field: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class {Output}Result:
    """Analysis result."""
    recommendations: List[Dict[str, Any]]
    anti_patterns_detected: List[str]
    meta_insight: str
    rules_applied: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ============================================================================
# Constants
# ============================================================================

THRESHOLDS = {
    "min_value": 100,
    "max_value": 10000,
}

ANTI_PATTERN_SEVERITY = {
    "pattern_a": "critical",
    "pattern_b": "high",
}


# ============================================================================
# Core Logic
# ============================================================================

class {ToolName}:
    """
    {Tool description}.

    Implements rules: {rule_1}, {rule_2}
    """

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def analyze(self, config: Dict[str, Any]) -> {Output}Result:
        """
        Run analysis.

        Rules: {rule_1}, {rule_2}

        Args:
            config: Input configuration

        Returns:
            {Output}Result with analysis
        """
        # Validate
        validation = self._validate(config)
        if not validation["valid"]:
            return self._error_result(validation["errors"])

        # Analyze
        recommendations = self._generate_recommendations(config)

        # Anti-patterns
        anti_patterns = self._detect_anti_patterns(config)

        # Compile
        return {Output}Result(
            recommendations=recommendations,
            anti_patterns_detected=[ap["pattern"] for ap in anti_patterns],
            meta_insight=self._generate_insight(recommendations),
            rules_applied=self._get_rules()
        )

    def _validate(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate input configuration."""
        errors = []
        # Add validation logic
        return {"valid": len(errors) == 0, "errors": errors}

    def _generate_recommendations(self, config: Dict[str, Any]) -> List[Dict]:
        """Generate recommendations."""
        recommendations = []
        # Add recommendation logic
        return recommendations

    def _detect_anti_patterns(self, config: Dict[str, Any]) -> List[Dict]:
        """Detect anti-patterns."""
        anti_patterns = []
        # Add anti-pattern detection
        return anti_patterns

    def _generate_insight(self, recommendations: List[Dict]) -> str:
        """Generate meta-insight."""
        return "Analysis complete"

    def _get_rules(self) -> List[str]:
        """Get applied rules."""
        return ["{rule_1}", "{rule_2}"]

    def _error_result(self, errors: List[str]) -> {Output}Result:
        """Create error result."""
        return {Output}Result(
            recommendations=[],
            anti_patterns_detected=[],
            meta_insight=f"Validation failed: {', '.join(errors)}",
            rules_applied=[]
        )


# ============================================================================
# CLI
# ============================================================================

def parse_arguments():
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="{Tool Name}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 {tool_name}.py --input data.json
  python3 {tool_name}.py --input data.json --pretty
  cat data.json | python3 {tool_name}.py --stdin
        """
    )

    parser.add_argument("--input", "-i", help="Input JSON file")
    parser.add_argument("--output", "-o", help="Output file")
    parser.add_argument("--stdin", action="store_true", help="Read from stdin")
    parser.add_argument("--pretty", action="store_true", help="Pretty print")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose")

    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_arguments()

    # Load input
    if args.stdin:
        try:
            data = json.load(sys.stdin)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.input:
        try:
            with open(args.input) as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Error: Provide --input or --stdin", file=sys.stderr)
        sys.exit(1)

    # Run analysis
    tool = {ToolName}(verbose=args.verbose)
    result = tool.analyze(data)

    # Output
    indent = 2 if args.pretty else None
    output = json.dumps(result.to_dict(), indent=indent, default=str)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
```

================================================================================
                          SECTION 14: TESTING PATTERN
================================================================================

## 14.1 Test File Structure

```python
#!/usr/bin/env python3
"""
test_{tool_name}.py - Unit tests for {tool_name}

Tests cover:
- Input validation
- Core analysis logic
- Anti-pattern detection
- Output format
- CLI interface

Author: Eyal Nof
"""

import unittest
import json
from {tool_name} import {ToolName}, {Input}Config, {Output}Result


class Test{ToolName}Validation(unittest.TestCase):
    """Test input validation."""

    def setUp(self):
        self.tool = {ToolName}()

    def test_valid_input(self):
        """Test with valid input."""
        config = {"field_a": "value", "field_b": 100}
        result = self.tool._validate(config)
        self.assertTrue(result["valid"])

    def test_invalid_input(self):
        """Test with invalid input."""
        config = {}
        result = self.tool._validate(config)
        self.assertFalse(result["valid"])


class Test{ToolName}Analysis(unittest.TestCase):
    """Test core analysis."""

    def setUp(self):
        self.tool = {ToolName}()

    def test_basic_analysis(self):
        """Test basic analysis."""
        config = {"field_a": "value", "field_b": 100}
        result = self.tool.analyze(config)
        self.assertIsInstance(result, {Output}Result)
        self.assertTrue(len(result.rules_applied) > 0)


class Test{ToolName}AntiPatterns(unittest.TestCase):
    """Test anti-pattern detection."""

    def setUp(self):
        self.tool = {ToolName}()

    def test_detects_pattern_a(self):
        """Test detection of pattern_a."""
        config = {"field_b": 99999}  # Trigger anti-pattern
        patterns = self.tool._detect_anti_patterns(config)
        self.assertTrue(any(p["pattern"] == "pattern_a" for p in patterns))


if __name__ == "__main__":
    unittest.main()
```

================================================================================
                          SECTION 15: VERSION HISTORY
================================================================================

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-17 | Initial template from 49 tool analysis |

================================================================================
                          END OF TEMPLATE
================================================================================

# DEV-tool-creation-template.pb
# Total: ~1,200 lines
# Patterns from: 49 production tools
# Categories: 9 tool types
# Author: Eyal Nof

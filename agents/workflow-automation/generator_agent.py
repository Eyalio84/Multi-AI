#!/usr/bin/env python3
"""
Generator Agent (Agent Factory)

Generates both Claude Code agent (.md) and Python tool (.py) definitions
from natural language specifications. The "agent that builds agents."

Wraps: NLKE GENERATOR-AGENT-SPEC.md + AI-LAB agent_composer.py
Layer: L1-L5 (Full 5-layer pattern via agent_base)

Usage:
    python3 generator_agent.py --example
    python3 generator_agent.py --workload spec.json
    python3 generator_agent.py --workload spec.json --summary

Created: February 6, 2026
"""

import sys
import os
import re
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.agent_base import (
    AgentInput, AgentOutput, BaseAnalyzer, run_standard_cli,
    NLKE_ROOT, AILAB_ROOT,
)

from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any, Optional
from pathlib import Path


# ============================================================================
# L1: Data Models
# ============================================================================

@dataclass
class AgentSpec:
    name: str
    description: str
    model: str
    tools_list: List[str]
    category: str
    wraps: List[str]
    input_format: str
    output_format: str
    key_rules: List[str]


@dataclass
class GeneratedAgent:
    md_content: str
    py_content: str
    md_path: str
    py_path: str
    validation_score: float
    validation_issues: List[str]


# ============================================================================
# L2: Constants
# ============================================================================

AGENT_CATEGORIES = {
    "cost-optimization": "Cost analysis and optimization tools",
    "kg-enhancement": "Knowledge graph analysis and enrichment",
    "workflow-automation": "Workflow planning and execution",
    "emergent": "Cross-cutting emergent capabilities",
}

MODEL_SELECTION_GUIDE = {
    "simple_analysis": "haiku",
    "complex_analysis": "sonnet",
    "strategic_planning": "opus",
    "data_processing": "haiku",
    "creative_generation": "sonnet",
    "multi_agent_coordination": "opus",
}

PY_TEMPLATE = '''#!/usr/bin/env python3
"""
{title}

{description}

Wraps: {wraps}
Layer: L1-L5 (Full 5-layer pattern via agent_base)

Usage:
    python3 {filename} --example
    python3 {filename} --workload input.json
    python3 {filename} --workload input.json --summary

Created: February 6, 2026
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.agent_base import (
    AgentInput, AgentOutput, BaseAnalyzer, run_standard_cli,
    NLKE_ROOT,
)

from dataclasses import dataclass, asdict
from typing import Dict, List, Any


# L3: Analyzer
class {class_name}(BaseAnalyzer):
    """{title} analysis engine."""

    def __init__(self):
        super().__init__(
            agent_name="{agent_name}",
            model="{model}",
            version="1.0",
        )

    def get_example_input(self) -> Dict[str, Any]:
        return {example_input}

    def analyze(self, agent_input: AgentInput) -> AgentOutput:
        w = agent_input.workload
        # TODO: Implement analysis logic
        return AgentOutput(
            recommendations=[{{"technique": "{agent_name}", "applicable": True}}],
            rules_applied={rules},
            meta_insight="Generated agent - implement analysis logic",
            agent_metadata=self.build_metadata(),
        )


# L5: CLI
if __name__ == "__main__":
    analyzer = {class_name}()
    run_standard_cli(
        agent_name="{title}",
        description="{description}",
        analyzer=analyzer,
    )
'''

MD_TEMPLATE = '''---
name: {name}
description: {description}. Triggers on /{trigger}.
tools: {tools}
model: {model}
---

# {title}

{detailed_description}

## What You Do
{what_you_do}

## Tools Available
1. **Python tool:** `python3 /storage/self/primary/Download/44nlke/NLKE/agents/{category}/{filename}.py`

## Execution Steps

### Step 1: Understand Input
Gather the required parameters from the user or from provided JSON.

### Step 2: Run Analysis
```bash
python3 /storage/self/primary/Download/44nlke/NLKE/agents/{category}/{filename}.py --example
```

### Step 3: Interpret and Report
Present findings in a clear, actionable format.

$ARGUMENTS
'''


# ============================================================================
# L3: Analyzer
# ============================================================================

class GeneratorAgentAnalyzer(BaseAnalyzer):
    """Agent generation engine."""

    def __init__(self):
        super().__init__(
            agent_name="generator-agent",
            model="sonnet",
            version="1.0",
        )

    def get_example_input(self) -> Dict[str, Any]:
        return {
            "name": "example-analyzer",
            "title": "Example Analyzer",
            "description": "Analyzes example data for patterns and insights",
            "model": "haiku",
            "category": "workflow-automation",
            "tools": ["Read", "Bash", "Glob", "Grep"],
            "wraps": ["some_existing_tool.py"],
            "key_rules": ["rule_001_example"],
            "complexity": "simple_analysis",
        }

    def analyze(self, agent_input: AgentInput) -> AgentOutput:
        w = agent_input.workload
        name = w.get("name", "unnamed-agent")
        title = w.get("title", name.replace("-", " ").title())
        description = w.get("description", "Auto-generated agent")
        model = w.get("model", MODEL_SELECTION_GUIDE.get(w.get("complexity", ""), "sonnet"))
        category = w.get("category", "workflow-automation")
        tools = w.get("tools", ["Read", "Bash", "Glob", "Grep"])
        wraps = w.get("wraps", [])
        key_rules = w.get("key_rules", [])

        rules = [
            "gen_001_5layer_pattern",
            "gen_002_frontmatter_validation",
            "gen_003_example_workload",
            "gen_004_output_format",
        ]

        # Generate Python tool
        class_name = "".join(word.capitalize() for word in name.replace("-", "_").split("_")) + "Analyzer"
        filename = name.replace("-", "_")

        py_content = PY_TEMPLATE.format(
            title=title,
            description=description,
            wraps=", ".join(wraps) if wraps else "standalone",
            filename=f"{filename}.py",
            class_name=class_name,
            agent_name=name,
            model=model,
            example_input='{"name": "Example workload"}',
            rules=json.dumps(key_rules),
        )

        # Generate Claude Code agent
        trigger = name.replace("-", "_")
        md_content = MD_TEMPLATE.format(
            name=name,
            description=description,
            trigger=trigger,
            tools=", ".join(tools),
            model=model,
            title=title,
            detailed_description=f"You are the NLKE {title}. {description}.",
            what_you_do=f"- {description}\n- Analyze inputs and generate actionable recommendations\n- Follow the 5-layer agent pattern",
            category=category,
            filename=filename,
        )

        # Validate
        validation_issues = []
        score = 1.0

        if not name:
            validation_issues.append("Missing agent name")
            score -= 0.25
        if not description:
            validation_issues.append("Missing description")
            score -= 0.15
        if model not in ("haiku", "sonnet", "opus"):
            validation_issues.append(f"Invalid model: {model}")
            score -= 0.20
        if not key_rules:
            validation_issues.append("No rules specified")
            score -= 0.10

        # Paths
        md_path = f"~/.claude/agents/{name}.md"
        py_path = f"NLKE/agents/{category}/{filename}.py"

        recommendations = [{
            "technique": "agent_generation",
            "applicable": True,
            "agent_name": name,
            "model": model,
            "category": category,
            "md_path": md_path,
            "py_path": py_path,
            "validation_score": round(score, 2),
            "validation_issues": validation_issues,
            "md_content_preview": md_content[:300] + "...",
            "py_content_preview": py_content[:300] + "...",
            "rules_applied": rules,
        }]

        quality = "Production-ready" if score >= 0.95 else "Needs minor fixes" if score >= 0.85 else "Needs work"
        meta_insight = (
            f"Generated {name} ({model}): {quality} (score: {score:.2f}). "
            f"MD: {md_path}, PY: {py_path}."
        )

        return AgentOutput(
            recommendations=recommendations,
            rules_applied=list(dict.fromkeys(rules)),
            meta_insight=meta_insight,
            analysis_data={
                "agent_spec": {
                    "name": name,
                    "title": title,
                    "model": model,
                    "category": category,
                },
                "generated_files": {
                    "md": {"path": md_path, "lines": md_content.count("\n")},
                    "py": {"path": py_path, "lines": py_content.count("\n")},
                },
                "validation": {
                    "score": round(score, 2),
                    "issues": validation_issues,
                    "quality": quality,
                },
                "full_md_content": md_content,
                "full_py_content": py_content,
            },
            anti_patterns=validation_issues,
            agent_metadata=self.build_metadata(),
        )


# ============================================================================
# L5: CLI
# ============================================================================

if __name__ == "__main__":
    analyzer = GeneratorAgentAnalyzer()
    run_standard_cli(
        agent_name="Generator Agent",
        description="Generate agent definitions (.md + .py) from natural language specs",
        analyzer=analyzer,
    )

#!/usr/bin/env python3
"""
MCP Spec Parser - L3 Analyzer

Parses 4 input formats into a unified MCPToolSpec:
  --from-agent: Parse Claude Code agent .md files (YAML frontmatter + instructions)
  --from-python: Parse standalone Python agent tools (5-layer pattern)
  --from-cookbook: Parse agent cookbook specification entries
  --interactive: Guided spec building (returns template for user to fill)

Created: February 6, 2026
"""

import os
import re
import json
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any, Optional


# ============================================================================
# L1: Data Models
# ============================================================================

@dataclass
class MCPToolDef:
    """Definition of a single MCP tool within a server."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler_name: str = ""
    wraps_function: str = ""


@dataclass
class MCPToolSpec:
    """Complete specification for an MCP tool server."""
    server_name: str
    description: str
    version: str = "1.0"
    transport: str = "stdio"
    tools: List[MCPToolDef] = field(default_factory=list)
    source_type: str = ""  # "agent", "python", "cookbook", "interactive"
    source_path: str = ""
    agent_name: str = ""
    model_tier: str = ""
    category: str = ""
    wraps: List[str] = field(default_factory=list)
    env_vars: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["tools"] = [asdict(t) for t in self.tools]
        return result


# ============================================================================
# Parsers
# ============================================================================

def parse_agent_md(path: str) -> MCPToolSpec:
    """Parse a Claude Code agent .md file into MCPToolSpec.

    Extracts:
    - YAML frontmatter (name, description, tools, model)
    - Tool instructions (bash commands = potential MCP tools)
    - Python tool references (wraps directives)
    """
    with open(path, "r") as f:
        content = f.read()

    # Extract YAML frontmatter
    fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    frontmatter = {}
    if fm_match:
        for line in fm_match.group(1).strip().split("\n"):
            if ":" in line:
                key, val = line.split(":", 1)
                frontmatter[key.strip()] = val.strip()

    name = frontmatter.get("name", os.path.basename(path).replace(".md", ""))
    description = frontmatter.get("description", "")
    model = frontmatter.get("model", "sonnet")

    # Extract Python tool references
    py_refs = re.findall(
        r"python3\s+(/storage/self/primary/Download/44nlke/NLKE/agents/[^\s]+\.py)",
        content,
    )

    # Extract what the agent does from "What You Do" section
    what_match = re.search(r"## What You Do\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
    capabilities = []
    if what_match:
        for line in what_match.group(1).strip().split("\n"):
            line = line.strip().lstrip("- ")
            if line:
                capabilities.append(line)

    # Build tools from capabilities
    tools = []
    safe_name = name.replace("-", "_")

    # Primary tool: the agent's main capability
    tools.append(MCPToolDef(
        name=safe_name,
        description=description.split(". Triggers")[0] if ". Triggers" in description else description,
        input_schema={
            "type": "object",
            "properties": {
                "workload": {
                    "type": "object",
                    "description": "Input workload for analysis",
                },
            },
            "required": ["workload"],
        },
        handler_name=f"handle_{safe_name}",
        wraps_function=py_refs[0] if py_refs else "",
    ))

    return MCPToolSpec(
        server_name=f"mcp-{name}",
        description=f"MCP server wrapping {name} agent",
        tools=tools,
        source_type="agent",
        source_path=path,
        agent_name=name,
        model_tier=model,
        category=_detect_category(path),
        wraps=py_refs,
    )


def parse_python_tool(path: str) -> MCPToolSpec:
    """Parse a standalone Python agent tool into MCPToolSpec.

    Extracts:
    - Module docstring (description)
    - Class name extending BaseAnalyzer
    - get_example_input() return value (becomes input schema)
    - analyze() signature (becomes tool handler)
    """
    with open(path, "r") as f:
        content = f.read()

    # Extract module docstring
    doc_match = re.match(r'^#!/usr/bin/env python3\n"""(.*?)"""', content, re.DOTALL)
    docstring = doc_match.group(1).strip() if doc_match else ""

    # Extract title from first line of docstring
    title = docstring.split("\n")[0] if docstring else os.path.basename(path).replace(".py", "")

    # Extract class name
    class_match = re.search(r"class (\w+)\(BaseAnalyzer\)", content)
    class_name = class_match.group(1) if class_match else "UnknownAnalyzer"

    # Extract agent_name from __init__
    name_match = re.search(r'agent_name="([^"]+)"', content)
    agent_name = name_match.group(1) if name_match else os.path.basename(path).replace(".py", "")

    # Extract model from __init__
    model_match = re.search(r'model="([^"]+)"', content)
    model = model_match.group(1) if model_match else "sonnet"

    # Extract example input to build schema
    example_match = re.search(
        r"def get_example_input\(self\)[^:]*:\s*\n\s*return\s*(\{.*?\n\s*\})",
        content, re.DOTALL,
    )
    example_input = {}
    if example_match:
        try:
            # Clean up Python dict to JSON-parseable
            raw = example_match.group(1)
            raw = re.sub(r"#.*$", "", raw, flags=re.MULTILINE)
            raw = raw.replace("True", "true").replace("False", "false").replace("None", "null")
            raw = re.sub(r"(\w+):", r'"\1":', raw)  # keys to strings
            raw = re.sub(r"'", '"', raw)
            example_input = json.loads(raw)
        except (json.JSONDecodeError, Exception):
            pass

    # Build input schema from example
    schema_props = {}
    for key, val in example_input.items():
        if isinstance(val, str):
            schema_props[key] = {"type": "string", "description": f"{key} parameter"}
        elif isinstance(val, (int, float)):
            schema_props[key] = {"type": "number", "description": f"{key} parameter"}
        elif isinstance(val, bool):
            schema_props[key] = {"type": "boolean", "description": f"{key} parameter"}
        elif isinstance(val, list):
            schema_props[key] = {"type": "array", "description": f"{key} parameter", "items": {"type": "object"}}
        elif isinstance(val, dict):
            schema_props[key] = {"type": "object", "description": f"{key} parameter"}

    safe_name = agent_name.replace("-", "_")

    tools = [MCPToolDef(
        name=safe_name,
        description=title,
        input_schema={
            "type": "object",
            "properties": schema_props if schema_props else {
                "workload": {"type": "object", "description": "Input workload"},
            },
            "required": list(schema_props.keys())[:3] if schema_props else ["workload"],
        },
        handler_name=f"handle_{safe_name}",
        wraps_function=path,
    )]

    return MCPToolSpec(
        server_name=f"mcp-{agent_name}",
        description=f"MCP server wrapping {title}",
        tools=tools,
        source_type="python",
        source_path=path,
        agent_name=agent_name,
        model_tier=model,
        category=_detect_category(path),
        wraps=[path],
    )


def parse_cookbook_entry(path: str, agent_id: str = "") -> MCPToolSpec:
    """Parse an agent cookbook entry into MCPToolSpec.

    Expects markdown with agent spec sections like:
    ### A1: Agent Name
    **Purpose:** ...
    **Wraps:** ...
    **Model:** ...
    """
    with open(path, "r") as f:
        content = f.read()

    # Find the specific agent section if agent_id provided
    if agent_id:
        pattern = rf"###\s*{re.escape(agent_id)}:\s*(.*?)(?=\n###|\Z)"
        match = re.search(pattern, content, re.DOTALL)
        section = match.group(0) if match else content
    else:
        section = content

    # Extract fields
    name_match = re.search(r"###\s*\w+:\s*(.+)", section)
    name = name_match.group(1).strip() if name_match else "unknown-tool"
    safe_name = re.sub(r"[^a-z0-9_]", "_", name.lower().replace(" ", "_"))

    purpose_match = re.search(r"\*\*Purpose:\*\*\s*(.+)", section)
    purpose = purpose_match.group(1).strip() if purpose_match else name

    model_match = re.search(r"\*\*Model:\*\*\s*(.+)", section)
    model = model_match.group(1).strip().lower() if model_match else "sonnet"

    wraps_match = re.search(r"\*\*Wraps:\*\*\s*(.+)", section)
    wraps_raw = wraps_match.group(1).strip() if wraps_match else ""
    wraps = [w.strip() for w in wraps_raw.split(",") if w.strip()]

    tools = [MCPToolDef(
        name=safe_name,
        description=purpose,
        input_schema={
            "type": "object",
            "properties": {
                "workload": {"type": "object", "description": "Input workload"},
            },
            "required": ["workload"],
        },
        handler_name=f"handle_{safe_name}",
    )]

    return MCPToolSpec(
        server_name=f"mcp-{safe_name}",
        description=f"MCP server for {name}",
        tools=tools,
        source_type="cookbook",
        source_path=path,
        agent_name=safe_name,
        model_tier=model,
        wraps=wraps,
    )


def build_interactive_spec() -> MCPToolSpec:
    """Return a template MCPToolSpec for interactive mode.

    The caller (CLI or Claude Code agent) fills in the details.
    """
    return MCPToolSpec(
        server_name="mcp-custom-tool",
        description="[FILL: What does this MCP tool do?]",
        tools=[MCPToolDef(
            name="custom_tool",
            description="[FILL: Tool description]",
            input_schema={
                "type": "object",
                "properties": {
                    "input": {"type": "string", "description": "[FILL: Input description]"},
                },
                "required": ["input"],
            },
            handler_name="handle_custom_tool",
        )],
        source_type="interactive",
    )


# ============================================================================
# Helpers
# ============================================================================

def _detect_category(path: str) -> str:
    """Detect agent category from file path."""
    categories = [
        "cost-optimization", "kg-enhancement", "workflow-automation",
        "emergent", "multi-model", "rule-engine", "knowledge-retrieval",
    ]
    for cat in categories:
        if cat in path:
            return cat
    return "general"

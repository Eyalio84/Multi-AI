#!/usr/bin/env python3
"""
MCP Generator: From Agent

Converts a Claude Code agent (.md) into an MCP tool server.
Parses YAML frontmatter + instructions, maps to MCPToolSpec,
then generates tool server code using templates.

Input: --from-agent ~/.claude/agents/cost-advisor.md
Output: mcp_tool_{name}.py + config + test + registration

Created: February 6, 2026
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from mcp_spec_parser import parse_agent_md, MCPToolSpec
from mcp_templates.tool_template import TOOL_TEMPLATE, PASSTHROUGH_HANDLER_TEMPLATE
from mcp_templates.server_template import (
    generate_mcp_config,
    generate_registration_snippet,
    TEST_TEMPLATE,
)


def generate_from_agent(agent_path: str, output_dir: str = None) -> dict:
    """Generate MCP tool server from a Claude Code agent .md file.

    Args:
        agent_path: Path to the .md agent file
        output_dir: Directory for output files (default: cwd)

    Returns:
        Dict with generated file paths and content
    """
    if not os.path.exists(agent_path):
        return {"error": f"Agent file not found: {agent_path}"}

    # Parse agent spec
    spec = parse_agent_md(agent_path)
    output_dir = output_dir or os.getcwd()

    # Generate handler code
    handlers = []
    handler_names = {}

    for tool in spec.tools:
        if tool.wraps_function and os.path.exists(tool.wraps_function):
            # Generate passthrough handler that imports the Python tool
            tool_dir = os.path.dirname(os.path.dirname(tool.wraps_function))
            module_parts = os.path.basename(tool.wraps_function).replace(".py", "")
            # Detect analyzer class name from the Python file
            analyzer_class = _detect_analyzer_class(tool.wraps_function)

            handler_code = PASSTHROUGH_HANDLER_TEMPLATE.format(
                handler_name=tool.handler_name.replace("handle_", ""),
                params_signature="**kwargs",
                description=tool.description,
                wraps_tool=tool.wraps_function,
                tool_dir=tool_dir,
                module_name=module_parts,
                analyzer_class=analyzer_class,
                input_mapping='"workload": kwargs' if not tool.input_schema.get("properties") else
                    ", ".join(f'"{k}": kwargs.get("{k}")' for k in tool.input_schema.get("properties", {}).keys()),
            )
        else:
            # Generate stub handler
            handler_code = f'''
def handle_{tool.handler_name.replace("handle_", "")}(**kwargs) -> dict:
    """{tool.description}"""
    return {{
        "status": "stub",
        "message": "Handler not yet implemented. Source: {agent_path}",
        "input_received": kwargs,
    }}
'''
        handlers.append(handler_code)
        handler_names[tool.name] = tool.handler_name

    # Build tools JSON for template
    tools_json = json.dumps([{
        "name": t.name,
        "description": t.description,
        "inputSchema": t.input_schema,
    } for t in spec.tools], indent=4)

    # Build handlers dict string
    handlers_dict = "{\n" + "\n".join(
        f'    "{name}": {handler},'
        for name, handler in handler_names.items()
    ) + "\n}"

    # Generate main tool file
    filename = f"mcp_tool_{spec.agent_name.replace('-', '_')}.py"
    tool_code = TOOL_TEMPLATE.format(
        tool_name=spec.server_name,
        description=spec.description,
        filename=filename,
        version=spec.version,
        tools_json=tools_json,
        handler_functions="\n".join(handlers),
        handlers_dict=handlers_dict,
    )

    # Generate config
    server_path = os.path.join(output_dir, filename)
    config = generate_mcp_config(spec.server_name, server_path)
    registration = generate_registration_snippet(
        spec.server_name, server_path, len(spec.tools), spec.description,
    )

    # Generate test
    test_code = TEST_TEMPLATE.format(
        tool_name=spec.server_name,
        server_path=server_path,
        tools_count=len(spec.tools),
    )

    return {
        "spec": spec.to_dict(),
        "files": {
            "tool": {"path": filename, "content": tool_code},
            "config": {"path": f"{spec.server_name}-config.json", "content": json.dumps(config, indent=2)},
            "test": {"path": f"test_{filename}", "content": test_code},
            "registration": {"path": f"{spec.server_name}-registration.txt", "content": registration},
        },
        "summary": {
            "server_name": spec.server_name,
            "tools_count": len(spec.tools),
            "source": agent_path,
            "source_type": "agent",
            "wraps": spec.wraps,
        },
    }


def _detect_analyzer_class(py_path: str) -> str:
    """Detect the BaseAnalyzer subclass name from a Python file."""
    try:
        with open(py_path, "r") as f:
            for line in f:
                if "(BaseAnalyzer)" in line and "class " in line:
                    return line.split("class ")[1].split("(")[0].strip()
    except Exception:
        pass
    return "UnknownAnalyzer"

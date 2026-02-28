#!/usr/bin/env python3
"""
MCP Generator: From Cookbook

Converts agent cookbook entries into MCP tool servers.
Reads markdown-formatted agent specifications (### A1: Agent Name format)
and generates tool server code.

Input: --from-cookbook AGENT-COOKBOOK.md --agent A1
Output: mcp_tool_{name}.py + config + test + registration

Created: February 6, 2026
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from mcp_spec_parser import parse_cookbook_entry, MCPToolSpec
from mcp_templates.tool_template import TOOL_TEMPLATE
from mcp_templates.server_template import (
    generate_mcp_config,
    generate_registration_snippet,
    TEST_TEMPLATE,
)


def generate_from_cookbook(cookbook_path: str, agent_id: str = "", output_dir: str = None) -> dict:
    """Generate MCP tool server from an agent cookbook entry.

    Args:
        cookbook_path: Path to the cookbook markdown file
        agent_id: Agent identifier (e.g., "A1", "A15") to extract
        output_dir: Directory for output files (default: cwd)

    Returns:
        Dict with generated file paths and content
    """
    if not os.path.exists(cookbook_path):
        return {"error": f"Cookbook file not found: {cookbook_path}"}

    # Parse cookbook entry
    spec = parse_cookbook_entry(cookbook_path, agent_id)
    output_dir = output_dir or os.getcwd()

    # Generate stub handlers (cookbook entries are specs, not implementations)
    handlers = []
    handler_names = {}

    for tool in spec.tools:
        handler_code = f'''
def handle_{tool.handler_name.replace("handle_", "")}(**kwargs) -> dict:
    """{tool.description}

    Generated from cookbook: {cookbook_path}
    Agent ID: {agent_id}
    NOTE: This is a stub handler. Implement the actual logic.
    """
    return {{
        "status": "stub",
        "message": "Implementation needed. Generated from cookbook spec.",
        "agent_id": "{agent_id}",
        "source": "{cookbook_path}",
        "input_received": kwargs,
        "recommendations": [],
        "rules_applied": ["mcp_gen_001_from_cookbook"],
        "meta_insight": "Stub handler - implement analysis logic from cookbook spec",
    }}
'''
        handlers.append(handler_code)
        handler_names[tool.name] = tool.handler_name

    # Build tools JSON
    tools_json = json.dumps([{
        "name": t.name,
        "description": t.description,
        "inputSchema": t.input_schema,
    } for t in spec.tools], indent=4)

    # Build handlers dict
    handlers_dict = "{\n" + "\n".join(
        f'    "{name}": {handler},'
        for name, handler in handler_names.items()
    ) + "\n}"

    # Generate files
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

    server_path = os.path.join(output_dir, filename)
    config = generate_mcp_config(spec.server_name, server_path)
    registration = generate_registration_snippet(
        spec.server_name, server_path, len(spec.tools), spec.description,
    )
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
            "source": cookbook_path,
            "source_type": "cookbook",
            "agent_id": agent_id,
            "note": "Stub handlers generated - implement logic from cookbook spec",
        },
    }

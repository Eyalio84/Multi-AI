#!/usr/bin/env python3
"""
MCP Generator: From Python

Converts a standalone Python agent tool (.py, 5-layer pattern) into an MCP tool server.
Reads the class structure, example input, and analysis method to generate
tool definitions with proper JSON schemas.

Input: --from-python agents/cost-optimization/cost_advisor.py
Output: mcp_tool_{name}.py + config + test + registration

Created: February 6, 2026
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from mcp_spec_parser import parse_python_tool, MCPToolSpec
from mcp_templates.tool_template import TOOL_TEMPLATE, PASSTHROUGH_HANDLER_TEMPLATE
from mcp_templates.server_template import (
    generate_mcp_config,
    generate_registration_snippet,
    TEST_TEMPLATE,
)


def generate_from_python(py_path: str, output_dir: str = None) -> dict:
    """Generate MCP tool server from a Python agent tool.

    Args:
        py_path: Path to the .py agent tool file
        output_dir: Directory for output files (default: cwd)

    Returns:
        Dict with generated file paths and content
    """
    if not os.path.exists(py_path):
        return {"error": f"Python file not found: {py_path}"}

    # Parse Python tool spec
    spec = parse_python_tool(py_path)
    output_dir = output_dir or os.getcwd()

    # Detect analyzer class for import
    analyzer_class = _detect_analyzer_class(py_path)
    module_name = os.path.basename(py_path).replace(".py", "")
    tool_dir = os.path.dirname(os.path.dirname(py_path))

    # Generate passthrough handler
    handlers = []
    handler_names = {}

    for tool in spec.tools:
        # Build input mapping from schema properties
        props = tool.input_schema.get("properties", {})
        if "workload" in props:
            input_mapping = '"workload": kwargs'
        else:
            input_mapping = ", ".join(
                f'"{k}": kwargs.get("{k}")' for k in props.keys()
            ) if props else '"workload": kwargs'

        handler_code = PASSTHROUGH_HANDLER_TEMPLATE.format(
            handler_name=tool.handler_name.replace("handle_", ""),
            params_signature="**kwargs",
            description=tool.description,
            wraps_tool=py_path,
            tool_dir=tool_dir,
            module_name=module_name,
            analyzer_class=analyzer_class,
            input_mapping=input_mapping,
        )
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
            "source": py_path,
            "source_type": "python",
            "analyzer_class": analyzer_class,
            "module_name": module_name,
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

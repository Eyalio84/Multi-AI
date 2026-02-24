"""MCP Server — exposes all workspace tools as individual MCP tools.

Run standalone:
    python3 backend/mcp_server.py

Each registered tool in ToolsService becomes a separate MCP tool with its
specific name (e.g. `react_component_generator`, `security_scanner`).
"""
import asyncio
import json
import sys
from pathlib import Path

# Ensure backend is importable
sys.path.insert(0, str(Path(__file__).parent))

from services.tools_service import tools_service


# ── Type mapping ──────────────────────────────────────────────────────

def _param_to_json_schema(param) -> dict:
    """Convert a ToolParam to JSON Schema property."""
    type_map = {
        "string": "string",
        "text": "string",
        "json": "string",
        "integer": "integer",
        "float": "number",
        "boolean": "boolean",
    }
    schema = {
        "type": type_map.get(param.type, "string"),
        "description": param.description or param.label,
    }
    if param.default is not None:
        schema["default"] = param.default
    return schema


def _tool_to_mcp_schema(tool) -> dict:
    """Convert a ToolDefinition to MCP tool schema."""
    properties = {}
    required = []
    for p in tool.params:
        properties[p.name] = _param_to_json_schema(p)
        if p.required:
            required.append(p.name)

    return {
        "name": tool.id,
        "description": tool.description,
        "inputSchema": {
            "type": "object",
            "properties": properties,
            "required": required,
        },
    }


# ── MCP Protocol Implementation ──────────────────────────────────────

class MCPServer:
    """Minimal MCP server using stdio JSON-RPC transport."""

    def __init__(self):
        self.tools_service = tools_service
        self._tool_schemas = self._build_schemas()

    def _build_schemas(self) -> list[dict]:
        schemas = []
        for tool in self.tools_service._tools.values():
            schemas.append(_tool_to_mcp_schema(tool))
        return schemas

    async def handle_request(self, request: dict) -> dict:
        """Handle a JSON-RPC request."""
        method = request.get("method", "")
        req_id = request.get("id")
        params = request.get("params", {})

        if method == "initialize":
            return self._result(req_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {
                    "name": "vox-workspace-tools",
                    "version": "1.0.0",
                },
            })

        elif method == "notifications/initialized":
            return None  # No response for notifications

        elif method == "tools/list":
            return self._result(req_id, {"tools": self._tool_schemas})

        elif method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            return await self._call_tool(req_id, tool_name, arguments)

        elif method == "ping":
            return self._result(req_id, {})

        else:
            return self._error(req_id, -32601, f"Method not found: {method}")

    async def _call_tool(self, req_id, tool_name: str, arguments: dict) -> dict:
        """Execute a tool and return MCP-formatted result."""
        # Parse JSON string params back to objects
        tool = self.tools_service._tools.get(tool_name)
        if not tool:
            return self._error(req_id, -32602, f"Unknown tool: {tool_name}")

        # Type-coerce string params for json-type fields
        coerced = {}
        for p in tool.params:
            if p.name in arguments:
                val = arguments[p.name]
                if p.type == "json" and isinstance(val, str):
                    try:
                        val = json.loads(val)
                    except json.JSONDecodeError:
                        pass
                elif p.type == "integer" and isinstance(val, str):
                    try:
                        val = int(val)
                    except ValueError:
                        pass
                elif p.type == "float" and isinstance(val, str):
                    try:
                        val = float(val)
                    except ValueError:
                        pass
                elif p.type == "boolean" and isinstance(val, str):
                    val = val.lower() in ("true", "1", "yes")
                coerced[p.name] = val
            elif p.required and p.default is not None:
                coerced[p.name] = p.default

        try:
            result = await self.tools_service.run_tool(tool_name, coerced)
            text = json.dumps(result, indent=2, default=str)
            return self._result(req_id, {
                "content": [{"type": "text", "text": text}],
                "isError": not result.get("success", True),
            })
        except Exception as e:
            return self._result(req_id, {
                "content": [{"type": "text", "text": f"Error: {e}"}],
                "isError": True,
            })

    def _result(self, req_id, result: dict) -> dict:
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    def _error(self, req_id, code: int, message: str) -> dict:
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}

    async def run_stdio(self):
        """Run the MCP server over stdio."""
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)

        transport, _ = await asyncio.get_event_loop().connect_write_pipe(
            asyncio.streams.FlowControlMixin, sys.stdout
        )
        writer = asyncio.StreamWriter(transport, protocol, reader, asyncio.get_event_loop())

        while True:
            line = await reader.readline()
            if not line:
                break

            line = line.decode("utf-8").strip()
            if not line:
                continue

            try:
                request = json.loads(line)
            except json.JSONDecodeError:
                continue

            response = await self.handle_request(request)
            if response is not None:
                out = json.dumps(response) + "\n"
                writer.write(out.encode("utf-8"))
                await writer.drain()


# ── CLI ───────────────────────────────────────────────────────────────

def print_tool_list():
    """Print all registered tools for inspection."""
    data = tools_service.list_tools()
    print(f"\nVOX Workspace MCP Server — {data['total']} tools\n")
    print(f"{'Category':<20} {'ID':<35} {'Params'}")
    print("─" * 70)
    for cat in sorted(data["tools"].keys()):
        for tool in data["tools"][cat]:
            print(f"{cat:<20} {tool['id']:<35} {tool['param_count']}p")
    print(f"\n Total: {data['total']} tools across {len(data['categories'])} categories")


if __name__ == "__main__":
    if "--list" in sys.argv:
        print_tool_list()
    elif "--json" in sys.argv:
        schemas = MCPServer()._tool_schemas
        print(json.dumps(schemas, indent=2))
    else:
        print(f"VOX Workspace MCP Server — {tools_service.list_tools()['total']} tools", file=sys.stderr)
        print("Listening on stdio...", file=sys.stderr)
        server = MCPServer()
        asyncio.run(server.run_stdio())

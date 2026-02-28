"""VOX Tool Functions — Phase 2 additions.

Existing (in vox_registry.py): list_tools, run_tool (tools category)
New here: get_tool_info, search_tools
"""
from services.vox_registry import vox_registry


@vox_registry.register(
    name="get_tool_info",
    category="tools",
    description="Get detailed information about a specific Python tool including parameters",
    parameters={
        "type": "object",
        "properties": {
            "tool_id": {"type": "string", "description": "Tool ID to get info for"},
        },
        "required": ["tool_id"],
    },
)
async def get_tool_info(args: dict) -> dict:
    from services.tools_service import ToolsService
    svc = ToolsService()
    tool = svc.get_tool(args["tool_id"])
    if not tool:
        return {"success": False, "error": f"Tool '{args['tool_id']}' not found"}
    return {"success": True, "tool": tool}


@vox_registry.register(
    name="search_tools",
    category="tools",
    description="Search available tools by name or description",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
        },
        "required": ["query"],
    },
)
async def search_tools(args: dict) -> dict:
    from services.tools_service import ToolsService
    svc = ToolsService()
    all_tools = svc.list_tools()
    q = args["query"].lower()
    matched = []
    for t in all_tools.get("tools", []):
        if q in t.get("name", "").lower() or q in t.get("description", "").lower():
            matched.append(t)
    return {"success": True, "tools": matched, "count": len(matched)}

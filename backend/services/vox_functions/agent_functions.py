"""VOX Agent Functions — Phase 2 additions.

Existing (in vox_registry.py): run_agent, list_agents
New here: get_agent_status, search_agents, get_agent_details
"""
from services.vox_registry import vox_registry


@vox_registry.register(
    name="get_agent_status",
    category="agents",
    description="Get the current status and recent sessions of the Claude Agent SDK",
    parameters={"type": "object", "properties": {}},
)
async def get_agent_status(args: dict) -> dict:
    from services.agent_sdk_service import agent_sdk_service
    sessions = agent_sdk_service.list_sessions()
    return {"success": True, "sessions": sessions[:10], "total": len(sessions)}


@vox_registry.register(
    name="search_agents",
    category="agents",
    description="Search NLKE agents by name or capability",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search term for agent name or description"},
        },
        "required": ["query"],
    },
)
async def search_agents(args: dict) -> dict:
    from services.agent_bridge import AgentBridge
    bridge = AgentBridge()
    all_agents = bridge.list_agents()
    q = args["query"].lower()
    matched = [
        a for a in all_agents
        if q in a.get("name", "").lower() or q in a.get("description", "").lower()
    ]
    return {"success": True, "agents": matched, "count": len(matched)}


@vox_registry.register(
    name="get_agent_details",
    category="agents",
    description="Get detailed information about a specific NLKE agent",
    parameters={
        "type": "object",
        "properties": {
            "agent_name": {"type": "string", "description": "Agent name"},
        },
        "required": ["agent_name"],
    },
)
async def get_agent_details(args: dict) -> dict:
    from services.agent_bridge import AgentBridge
    bridge = AgentBridge()
    all_agents = bridge.list_agents()
    for a in all_agents:
        if a.get("name", "").lower() == args["agent_name"].lower():
            return {"success": True, "agent": a}
    return {"success": False, "error": f"Agent '{args['agent_name']}' not found"}

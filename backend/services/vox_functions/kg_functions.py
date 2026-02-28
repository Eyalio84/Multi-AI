"""VOX KG Functions — Phase 2 additions to existing 6 KG functions.

Existing (in vox_registry.py): query_kg, list_kgs, search_kg, get_kg_analytics, cross_kg_search, ingest_to_kg
New here: explore_node, compare_kgs, get_communities, find_path
"""
from services.vox_registry import vox_registry


@vox_registry.register(
    name="explore_node",
    category="kg",
    description="Get details of a specific node in a knowledge graph including its connections",
    parameters={
        "type": "object",
        "properties": {
            "database_id": {"type": "string", "description": "KG database ID"},
            "node_id": {"type": "string", "description": "Node ID to explore"},
        },
        "required": ["database_id", "node_id"],
    },
    requires_kg=True,
)
async def explore_node(args: dict) -> dict:
    from services.kg_service import kg_service
    node = kg_service.get_node(args["database_id"], args["node_id"])
    if not node:
        return {"success": False, "error": "Node not found"}
    edges = kg_service.get_edges(args["database_id"], node_id=args["node_id"])
    return {"success": True, "node": node, "connections": edges.get("edges", [])[:20]}


@vox_registry.register(
    name="compare_kgs",
    category="kg",
    description="Compare two knowledge graphs structurally — shared nodes, Jaccard similarity, type distributions",
    parameters={
        "type": "object",
        "properties": {
            "database_a": {"type": "string", "description": "First KG database ID"},
            "database_b": {"type": "string", "description": "Second KG database ID"},
        },
        "required": ["database_a", "database_b"],
    },
    requires_kg=True,
)
async def compare_kgs(args: dict) -> dict:
    from services.analytics_service import analytics_service
    result = analytics_service.compare(args["database_a"], args["database_b"])
    return {"success": True, **result}


@vox_registry.register(
    name="get_communities",
    category="kg",
    description="Detect communities/clusters in a knowledge graph using modularity analysis",
    parameters={
        "type": "object",
        "properties": {
            "database_id": {"type": "string", "description": "KG database ID"},
        },
        "required": ["database_id"],
    },
    requires_kg=True,
)
async def get_communities(args: dict) -> dict:
    from services.analytics_service import analytics_service
    result = analytics_service.communities(args["database_id"])
    return {"success": True, **result}


@vox_registry.register(
    name="find_path",
    category="kg",
    description="Find the shortest path between two nodes in a knowledge graph",
    parameters={
        "type": "object",
        "properties": {
            "database_id": {"type": "string", "description": "KG database ID"},
            "source_node": {"type": "string", "description": "Source node ID"},
            "target_node": {"type": "string", "description": "Target node ID"},
        },
        "required": ["database_id", "source_node", "target_node"],
    },
    requires_kg=True,
)
async def find_path(args: dict) -> dict:
    from services.analytics_service import analytics_service
    result = analytics_service.shortest_path(
        args["database_id"], args["source_node"], args["target_node"]
    )
    return {"success": True, **result}

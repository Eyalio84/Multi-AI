"""VOX Playbook Functions — Phase 2 additions.

Existing (in vox_registry.py): search_playbooks
New here: read_playbook, list_playbooks, get_recommendations
"""
from services.vox_registry import vox_registry


@vox_registry.register(
    name="read_playbook",
    category="playbooks",
    description="Read the full content of a specific playbook by filename",
    parameters={
        "type": "object",
        "properties": {
            "filename": {"type": "string", "description": "Playbook filename (e.g. PLAYBOOK-1-COST-OPTIMIZATION.md)"},
        },
        "required": ["filename"],
    },
)
async def read_playbook(args: dict) -> dict:
    from services.playbook_index import PlaybookIndex
    idx = PlaybookIndex()
    pb = idx.get_playbook(args["filename"])
    if not pb:
        return {"success": False, "error": "Playbook not found"}
    return {"success": True, "playbook": pb}


@vox_registry.register(
    name="list_playbooks",
    category="playbooks",
    description="List all available playbooks with their titles and categories",
    parameters={"type": "object", "properties": {}},
)
async def list_playbooks(args: dict) -> dict:
    from services.playbook_index import PlaybookIndex
    idx = PlaybookIndex()
    all_pb = idx.list_all()
    return {"success": True, "playbooks": all_pb, "count": len(all_pb)}


@vox_registry.register(
    name="get_recommendations",
    category="playbooks",
    description="Get playbook recommendations for a specific goal or problem",
    parameters={
        "type": "object",
        "properties": {
            "goal": {"type": "string", "description": "What you want to achieve (e.g. 'reduce API costs')"},
        },
        "required": ["goal"],
    },
)
async def get_recommendations(args: dict) -> dict:
    from services.playbook_index import PlaybookIndex
    idx = PlaybookIndex()
    results = idx.search(args["goal"])
    return {"success": True, "recommendations": results[:5]}

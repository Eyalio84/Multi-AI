"""VOX Expert Functions — Phase 2 additions.

Existing (in vox_registry.py): chat_with_expert, list_experts
New here: create_expert, get_expert_details, duplicate_expert
"""
from services.vox_registry import vox_registry


@vox_registry.register(
    name="create_expert",
    category="experts",
    description="Create a new AI expert with a specific knowledge domain and KG backing",
    parameters={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Expert name"},
            "description": {"type": "string", "description": "Expert specialization description"},
            "database_id": {"type": "string", "description": "KG database to back the expert"},
        },
        "required": ["name", "description"],
    },
)
async def create_expert(args: dict) -> dict:
    from services.expert_service import ExpertService
    svc = ExpertService()
    result = svc.create_expert({
        "name": args["name"],
        "description": args["description"],
        "database_id": args.get("database_id"),
    })
    return {"success": True, "expert": result}


@vox_registry.register(
    name="get_expert_details",
    category="experts",
    description="Get detailed information about a specific AI expert",
    parameters={
        "type": "object",
        "properties": {
            "expert_id": {"type": "string", "description": "Expert ID"},
        },
        "required": ["expert_id"],
    },
)
async def get_expert_details(args: dict) -> dict:
    from services.expert_service import ExpertService
    svc = ExpertService()
    expert = svc.get_expert(args["expert_id"])
    if not expert:
        return {"success": False, "error": "Expert not found"}
    return {"success": True, "expert": expert}


@vox_registry.register(
    name="duplicate_expert",
    category="experts",
    description="Duplicate an existing AI expert with all its configuration",
    parameters={
        "type": "object",
        "properties": {
            "expert_id": {"type": "string", "description": "Expert ID to duplicate"},
        },
        "required": ["expert_id"],
    },
)
async def duplicate_expert(args: dict) -> dict:
    from services.expert_service import ExpertService
    svc = ExpertService()
    result = svc.duplicate_expert(args["expert_id"])
    if not result:
        return {"success": False, "error": "Expert not found"}
    return {"success": True, "expert": result}

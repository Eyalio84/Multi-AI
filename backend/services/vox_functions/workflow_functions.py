"""VOX Workflow Functions — Phase 2 additions.

Existing (in vox_registry.py): run_workflow
New here: list_workflows, get_workflow_status, create_workflow
"""
from services.vox_registry import vox_registry


@vox_registry.register(
    name="list_workflows",
    category="workflows",
    description="List all available workflow templates",
    parameters={"type": "object", "properties": {}},
)
async def list_workflows(args: dict) -> dict:
    from services.workflow_service import list_workflows
    workflows = list_workflows()
    return {"success": True, "workflows": workflows, "count": len(workflows)}


@vox_registry.register(
    name="get_workflow_status",
    category="workflows",
    description="Get the details and status of a specific workflow",
    parameters={
        "type": "object",
        "properties": {
            "workflow_id": {"type": "string", "description": "Workflow ID"},
        },
        "required": ["workflow_id"],
    },
)
async def get_workflow_status(args: dict) -> dict:
    from services.workflow_service import get_workflow
    wf = get_workflow(args["workflow_id"])
    if not wf:
        return {"success": False, "error": "Workflow not found"}
    return {"success": True, "workflow": wf}


@vox_registry.register(
    name="create_workflow",
    category="workflows",
    description="Create a new custom workflow with defined steps",
    parameters={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Workflow name"},
            "description": {"type": "string", "description": "What the workflow does"},
            "goal": {"type": "string", "description": "Workflow goal"},
            "steps": {
                "type": "array",
                "description": "List of workflow step objects",
                "items": {
                    "type": "object",
                    "properties": {
                        "tool": {"type": "string"},
                        "inputs": {"type": "object"},
                    },
                },
            },
        },
        "required": ["name", "goal"],
    },
)
async def create_workflow(args: dict) -> dict:
    from services.workflow_service import create_workflow
    wf = create_workflow(
        name=args["name"],
        description=args.get("description", ""),
        goal=args["goal"],
        steps=args.get("steps", []),
    )
    return {"success": True, "workflow": wf}

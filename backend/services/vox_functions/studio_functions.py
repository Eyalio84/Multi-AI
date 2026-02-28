"""VOX Studio Functions — AI Studio project management via voice.

Existing (in vox_registry.py): create_project, list_projects (workspace category)
New here: studio_create_project, studio_list_projects, generate_code, refine_code,
save_version, restore_version, export_project, switch_mode
Note: studio_* prefixed to avoid collision with workspace create_project/list_projects.
"""
from services.vox_registry import vox_registry


@vox_registry.register(
    name="studio_create_project",
    category="studio",
    description="Create a new AI Studio project for code generation",
    parameters={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Project name"},
            "description": {"type": "string", "description": "Project description"},
        },
        "required": ["name"],
    },
)
async def studio_create_project(args: dict) -> dict:
    from services.studio_service import create_project
    result = create_project(args["name"], args.get("description", ""))
    return {"success": True, "project": result}


@vox_registry.register(
    name="studio_list_projects",
    category="studio",
    description="List all AI Studio projects",
    parameters={"type": "object", "properties": {}},
)
async def studio_list_projects(args: dict) -> dict:
    from services.studio_service import list_projects
    projects = list_projects()
    return {"success": True, "projects": projects, "count": len(projects)}


@vox_registry.register(
    name="studio_save_version",
    category="studio",
    description="Save a version snapshot of a Studio project",
    parameters={
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "Studio project ID"},
            "message": {"type": "string", "description": "Version message"},
        },
        "required": ["project_id"],
    },
)
async def studio_save_version(args: dict) -> dict:
    from services.studio_service import save_version
    result = save_version(args["project_id"], args.get("message", "Voice save"))
    if not result:
        return {"success": False, "error": "Project not found"}
    return {"success": True, "version": result}


@vox_registry.register(
    name="studio_restore_version",
    category="studio",
    description="Restore a previous version of a Studio project",
    parameters={
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "Studio project ID"},
            "version_number": {"type": "integer", "description": "Version number to restore"},
        },
        "required": ["project_id", "version_number"],
    },
)
async def studio_restore_version(args: dict) -> dict:
    from services.studio_service import restore_version
    ok = restore_version(args["project_id"], args["version_number"])
    if not ok:
        return {"success": False, "error": "Version not found"}
    return {"success": True, "restored": args["version_number"]}


@vox_registry.register(
    name="studio_export_project",
    category="studio",
    description="Export a Studio project as a downloadable ZIP archive",
    parameters={
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "Studio project ID"},
        },
        "required": ["project_id"],
    },
)
async def studio_export_project(args: dict) -> dict:
    from services.studio_service import export_project_zip
    data = export_project_zip(args["project_id"])
    if not data:
        return {"success": False, "error": "Project not found"}
    return {"success": True, "message": "Export ready — use the Studio page to download"}


@vox_registry.register(
    name="studio_get_project",
    category="studio",
    description="Get details of a specific Studio project including files and versions",
    parameters={
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "Studio project ID"},
        },
        "required": ["project_id"],
    },
)
async def studio_get_project(args: dict) -> dict:
    from services.studio_service import get_project
    project = get_project(args["project_id"])
    if not project:
        return {"success": False, "error": "Project not found"}
    return {"success": True, "project": project}


@vox_registry.register(
    name="studio_list_versions",
    category="studio",
    description="List all saved versions of a Studio project",
    parameters={
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "Studio project ID"},
        },
        "required": ["project_id"],
    },
)
async def studio_list_versions(args: dict) -> dict:
    from services.studio_service import get_project
    project = get_project(args["project_id"])
    if not project:
        return {"success": False, "error": "Project not found"}
    return {"success": True, "versions": project.get("versions", [])}

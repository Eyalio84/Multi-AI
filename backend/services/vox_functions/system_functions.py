"""VOX System Functions — health, config, and system management via voice.

Existing (in vox_registry.py): check_thermal (system category)
New here: get_health, get_models, toggle_mode, get_config, get_system_info
"""
from services.vox_registry import vox_registry


@vox_registry.register(
    name="get_health",
    category="system",
    description="Check the health status of the backend server",
    parameters={"type": "object", "properties": {}},
)
async def get_health(args: dict) -> dict:
    import config
    return {
        "success": True,
        "status": "healthy",
        "mode": getattr(config, "CURRENT_MODE", "standalone"),
        "providers": {
            "gemini": bool(getattr(config, "GEMINI_API_KEY", None)),
            "claude": bool(getattr(config, "ANTHROPIC_API_KEY", None)),
            "openai": bool(getattr(config, "OPENAI_API_KEY", None)),
        },
    }


@vox_registry.register(
    name="get_models",
    category="system",
    description="List all available AI models by provider and category",
    parameters={
        "type": "object",
        "properties": {
            "provider": {"type": "string", "description": "Filter by provider (gemini, claude, openai)"},
            "category": {"type": "string", "description": "Filter by category (text, image, video, audio, etc.)"},
        },
    },
)
async def get_models(args: dict) -> dict:
    from config import MODEL_CATALOG
    models = []
    for mid, info in MODEL_CATALOG.items():
        if args.get("provider") and info.get("provider", "").lower() != args["provider"].lower():
            continue
        if args.get("category") and info.get("category", "") != args["category"]:
            continue
        models.append({
            "id": mid,
            "name": info.get("name", mid),
            "provider": info.get("provider", "unknown"),
            "category": info.get("category", "text"),
        })
    return {"success": True, "models": models, "count": len(models)}


@vox_registry.register(
    name="toggle_mode",
    category="system",
    description="Toggle between standalone and Claude Code mode",
    parameters={
        "type": "object",
        "properties": {
            "mode": {"type": "string", "description": "Mode to switch to (standalone or claude_code)"},
        },
        "required": ["mode"],
    },
)
async def toggle_mode(args: dict) -> dict:
    import config
    mode = args["mode"].lower()
    if mode not in ("standalone", "claude_code"):
        return {"success": False, "error": "Mode must be 'standalone' or 'claude_code'"}
    config.CURRENT_MODE = mode
    return {"success": True, "mode": mode}


@vox_registry.register(
    name="get_config",
    category="system",
    description="Get current workspace configuration (mode, active providers, paths)",
    parameters={"type": "object", "properties": {}},
)
async def get_config(args: dict) -> dict:
    import config
    return {
        "success": True,
        "mode": getattr(config, "CURRENT_MODE", "standalone"),
        "data_dir": str(getattr(config, "DATA_DIR", "")),
        "model_count": len(getattr(config, "MODEL_CATALOG", {})),
    }


@vox_registry.register(
    name="get_system_info",
    category="system",
    description="Get system information including platform, thermal status, and resource usage",
    parameters={"type": "object", "properties": {}},
)
async def get_system_info(args: dict) -> dict:
    import platform
    from services.vox_thermal import get_thermal_status
    thermal = get_thermal_status()
    return {
        "success": True,
        "platform": platform.platform(),
        "python": platform.python_version(),
        "thermal": thermal,
    }

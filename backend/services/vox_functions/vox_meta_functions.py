"""VOX Meta Functions — VOX self-management and awareness via voice.

Existing (in vox_registry.py): start_guided_tour, get_available_tours (tours category),
list_macros, create_macro, run_macro, delete_macro (macros category), check_thermal (system)
New here: get_vox_status, change_voice, get_vox_capabilities, get_awareness_context, list_voices
"""
from services.vox_registry import vox_registry


@vox_registry.register(
    name="get_vox_status",
    category="vox_meta",
    description="Get VOX system status — function count, categories, active sessions",
    parameters={"type": "object", "properties": {}},
)
async def get_vox_status(args: dict) -> dict:
    cats = {}
    for name, fn in vox_registry.get_all().items():
        cats.setdefault(fn.category, []).append(name)
    return {
        "success": True,
        "total_functions": vox_registry.count,
        "categories": {cat: len(fns) for cat, fns in sorted(cats.items())},
        "browser_functions": len(vox_registry.get_browser_functions()),
        "async_functions": len(vox_registry.get_async_functions()),
    }


@vox_registry.register(
    name="change_voice",
    category="vox_meta",
    description="Change the VOX voice to one of 16 available Gemini voices",
    parameters={
        "type": "object",
        "properties": {
            "voice": {"type": "string", "description": "Voice name (Puck, Charon, Kore, Fenrir, Aoede, Leda, Orus, Zephyr, Sage, Vale, Solaria, River, Ember, Breeze, Cove, Orbit)"},
        },
        "required": ["voice"],
    },
)
async def change_voice(args: dict) -> dict:
    from services.vox_service import GEMINI_VOICES
    voice = args["voice"]
    valid_names = [v["id"] for v in GEMINI_VOICES]
    if voice not in valid_names:
        return {"success": False, "error": f"Unknown voice. Available: {', '.join(valid_names)}"}
    return {"success": True, "voice": voice, "note": "Voice change takes effect on next connection"}


@vox_registry.register(
    name="get_vox_capabilities",
    category="vox_meta",
    description="List all VOX capabilities organized by category",
    parameters={"type": "object", "properties": {}},
)
async def get_vox_capabilities(args: dict) -> dict:
    cats = {}
    for name, fn in vox_registry.get_all().items():
        cats.setdefault(fn.category, []).append({
            "name": name,
            "description": fn.declaration.get("description", ""),
        })
    return {"success": True, "capabilities": cats}


@vox_registry.register(
    name="get_awareness_context",
    category="vox_meta",
    description="Get VOX's current workspace awareness context (page visits, recent errors)",
    parameters={"type": "object", "properties": {}},
)
async def get_awareness_context(args: dict) -> dict:
    from services.vox_awareness import VoxAwareness
    awareness = VoxAwareness()
    ctx = awareness.get_context()
    return {"success": True, "awareness": ctx}


@vox_registry.register(
    name="list_voices",
    category="vox_meta",
    description="List all available VOX voices with their styles",
    parameters={"type": "object", "properties": {}},
)
async def list_voices(args: dict) -> dict:
    from services.vox_service import GEMINI_VOICES
    return {"success": True, "voices": GEMINI_VOICES, "count": len(GEMINI_VOICES)}

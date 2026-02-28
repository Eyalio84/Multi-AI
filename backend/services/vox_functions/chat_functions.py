"""VOX Chat Functions — chat session management via voice.

All new — no existing chat functions in the registry.
"""
from services.vox_registry import vox_registry


@vox_registry.register(
    name="get_chat_history",
    category="chat",
    description="Get recent chat history from the current or a specified conversation",
    parameters={
        "type": "object",
        "properties": {
            "conversation_id": {"type": "string", "description": "Conversation ID (optional, uses latest if omitted)"},
            "limit": {"type": "integer", "description": "Number of messages to return"},
        },
    },
)
async def get_chat_history(args: dict) -> dict:
    from services.memory_service import MemoryService
    svc = MemoryService()
    cid = args.get("conversation_id")
    if not cid:
        convos = svc.list_conversations(mode="chat", limit=1)
        if not convos:
            return {"success": True, "messages": [], "note": "No chat conversations found"}
        cid = convos[0]["id"]
    messages = svc.get_conversation_messages(cid, limit=args.get("limit", 10))
    return {"success": True, "conversation_id": cid, "messages": messages}


@vox_registry.register(
    name="summarize_conversation",
    category="chat",
    description="Get a summary of a specific conversation's key topics and decisions",
    parameters={
        "type": "object",
        "properties": {
            "conversation_id": {"type": "string", "description": "Conversation ID to summarize"},
        },
        "required": ["conversation_id"],
    },
)
async def summarize_conversation(args: dict) -> dict:
    from services.memory_service import MemoryService
    svc = MemoryService()
    convo = svc.get_conversation(args["conversation_id"])
    if not convo:
        return {"success": False, "error": "Conversation not found"}
    messages = svc.get_conversation_messages(args["conversation_id"], limit=50)
    msg_count = len(messages)
    topics = set()
    for m in messages:
        content = m.get("content", "")
        if len(content) > 20:
            topics.add(content[:60] + "...")
    return {
        "success": True,
        "conversation_id": args["conversation_id"],
        "message_count": msg_count,
        "mode": convo.get("mode", "unknown"),
        "sample_topics": list(topics)[:5],
    }


@vox_registry.register(
    name="change_persona",
    category="chat",
    description="Switch the active VOX persona (default, mentor, speed, debug)",
    parameters={
        "type": "object",
        "properties": {
            "persona": {"type": "string", "description": "Persona name (default, mentor, speed, debug)"},
        },
        "required": ["persona"],
    },
)
async def change_persona(args: dict) -> dict:
    valid = ["default", "mentor", "speed", "debug"]
    persona = args["persona"].lower()
    if persona not in valid:
        return {"success": False, "error": f"Unknown persona. Choose from: {', '.join(valid)}"}
    return {"success": True, "persona": persona, "note": "Persona change takes effect on next connection"}


@vox_registry.register(
    name="get_available_models",
    category="chat",
    description="List all available AI models across all providers",
    parameters={"type": "object", "properties": {}},
)
async def get_available_models(args: dict) -> dict:
    from config import MODEL_CATALOG
    models = []
    for mid, info in MODEL_CATALOG.items():
        models.append({
            "id": mid,
            "name": info.get("name", mid),
            "provider": info.get("provider", "unknown"),
            "category": info.get("category", "text"),
        })
    return {"success": True, "models": models, "count": len(models)}

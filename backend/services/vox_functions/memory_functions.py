"""VOX Memory Functions — conversation memory search and recall via voice.

All new — no existing memory functions in the registry.
"""
from services.vox_registry import vox_registry


@vox_registry.register(
    name="search_memory",
    category="memory",
    description="Search past conversations using hybrid semantic retrieval",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query for past conversations"},
            "limit": {"type": "integer", "description": "Max results to return"},
        },
        "required": ["query"],
    },
)
async def search_memory(args: dict) -> dict:
    from services.memory_service import MemoryService
    svc = MemoryService()
    results = svc.recall(args["query"], limit=args.get("limit", 5))
    return {"success": True, "results": results, "count": len(results)}


@vox_registry.register(
    name="list_conversations",
    category="memory",
    description="List recent conversations from memory",
    parameters={
        "type": "object",
        "properties": {
            "mode": {"type": "string", "description": "Filter by mode (chat, coding, studio, vox)"},
            "limit": {"type": "integer", "description": "Max conversations to return"},
        },
    },
)
async def list_conversations(args: dict) -> dict:
    from services.memory_service import MemoryService
    svc = MemoryService()
    convos = svc.list_conversations(
        mode=args.get("mode"),
        limit=args.get("limit", 10),
    )
    return {"success": True, "conversations": convos, "count": len(convos)}


@vox_registry.register(
    name="get_conversation",
    category="memory",
    description="Get the full content of a specific conversation by ID",
    parameters={
        "type": "object",
        "properties": {
            "conversation_id": {"type": "string", "description": "Conversation ID"},
        },
        "required": ["conversation_id"],
    },
)
async def get_conversation(args: dict) -> dict:
    from services.memory_service import MemoryService
    svc = MemoryService()
    convo = svc.get_conversation(args["conversation_id"])
    if not convo:
        return {"success": False, "error": "Conversation not found"}
    messages = svc.get_conversation_messages(args["conversation_id"], limit=20)
    return {"success": True, "conversation": convo, "messages": messages}


@vox_registry.register(
    name="recall_context",
    category="memory",
    description="Recall relevant past context for the current conversation topic",
    parameters={
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "Topic to recall context about"},
        },
        "required": ["topic"],
    },
)
async def recall_context(args: dict) -> dict:
    from services.memory_service import MemoryService
    svc = MemoryService()
    results = svc.recall(args["topic"], limit=5, min_score=0.2)
    return {"success": True, "context": results}


@vox_registry.register(
    name="get_memory_stats",
    category="memory",
    description="Get statistics about stored conversation memory",
    parameters={"type": "object", "properties": {}},
)
async def get_memory_stats(args: dict) -> dict:
    from services.memory_service import MemoryService
    svc = MemoryService()
    stats = svc.get_stats()
    return {"success": True, "stats": stats}

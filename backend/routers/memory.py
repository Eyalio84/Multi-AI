"""Memory + conversation REST endpoints."""
import json
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/memory", tags=["memory"])


class SearchRequest(BaseModel):
    query: str
    limit: int = 5


# ── Conversations ────────────────────────────────────────────────────

@router.get("/conversations")
async def list_conversations(
    mode: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = Query(20, le=100),
):
    from services.memory_service import memory_service
    return memory_service.list_conversations(mode=mode, source=source, limit=limit)


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    from services.memory_service import memory_service
    result = memory_service.get_conversation(conversation_id)
    if not result:
        raise HTTPException(404, "Conversation not found")
    return result


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    limit: int = Query(50, le=200),
    offset: int = 0,
):
    from services.memory_service import memory_service
    return memory_service.get_conversation_messages(conversation_id, limit, offset)


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    from services.memory_service import memory_service
    if not memory_service.delete_conversation(conversation_id):
        raise HTTPException(404, "Conversation not found")
    return {"deleted": True}


# ── Memory search ────────────────────────────────────────────────────

@router.post("/search")
async def search_memory(req: SearchRequest):
    from services.memory_service import memory_service
    results = memory_service.recall(req.query, limit=req.limit)
    return {"results": results, "query": req.query}


# ── Stats ────────────────────────────────────────────────────────────

@router.get("/stats")
async def memory_stats():
    from services.memory_service import memory_service
    stats = memory_service.get_stats()
    # Add injection stats if available
    try:
        from services.skill_injector import skill_injector
        stats["injection_stats"] = skill_injector.get_injection_stats()
    except Exception:
        stats["injection_stats"] = {}
    return stats

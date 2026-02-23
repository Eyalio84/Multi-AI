"""Expert + KG-OS router — 15 endpoints for expert CRUD, chat, and KG-OS direct access."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/experts", tags=["Experts & KG-OS"])


# ── Pydantic Models ──────────────────────────────────────────────────

class ExpertCreate(BaseModel):
    name: str
    description: str = ""
    kg_db_id: str
    kg_db_ids: list[str] = []
    persona_name: str = "Expert"
    persona_instructions: str = ""
    persona_style: str = "professional"
    retrieval_methods: list[str] = ["hybrid", "intent"]
    retrieval_alpha: float = 0.35
    retrieval_beta: float = 0.40
    retrieval_gamma: float = 0.15
    retrieval_delta: float = 0.10
    retrieval_limit: int = 10
    dimension_filters: dict = {}
    playbook_skills: list[str] = []
    custom_goal_mappings: dict = {}
    icon: str = "brain"
    color: str = "#0ea5e9"
    is_public: bool = True


class ExpertUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    kg_db_id: Optional[str] = None
    kg_db_ids: Optional[list[str]] = None
    persona_name: Optional[str] = None
    persona_instructions: Optional[str] = None
    persona_style: Optional[str] = None
    retrieval_methods: Optional[list[str]] = None
    retrieval_alpha: Optional[float] = None
    retrieval_beta: Optional[float] = None
    retrieval_gamma: Optional[float] = None
    retrieval_delta: Optional[float] = None
    retrieval_limit: Optional[int] = None
    dimension_filters: Optional[dict] = None
    playbook_skills: Optional[list[str]] = None
    custom_goal_mappings: Optional[dict] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    is_public: Optional[bool] = None


class ExpertChatRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None
    history: list[dict] = []


class KGOSQueryRequest(BaseModel):
    query: str
    alpha: float = 0.35
    beta: float = 0.40
    gamma: float = 0.15
    delta: float = 0.10
    limit: int = 10
    methods: list[str] = ["hybrid", "intent"]


class KGOSComposeRequest(BaseModel):
    goal: str
    max_steps: int = 5


class KGOSImpactRequest(BaseModel):
    direction: str = "forward"
    max_depth: int = 3


class KGOSDimensionRequest(BaseModel):
    filters: dict
    limit: int = 20


# ══════════════════════════════════════════════════════════════════════
# KG-OS Direct Access Endpoints — MUST come before /{expert_id} dynamic routes
# (FastAPI matches in definition order; "kgos" would be captured as expert_id otherwise)
# ══════════════════════════════════════════════════════════════════════

@router.get("/kgos/dimensions")
async def kgos_dimensions():
    from services.kgos_query_engine import STANDARD_DIMENSIONS
    return STANDARD_DIMENSIONS


@router.post("/kgos/query/{db_id}")
async def kgos_query(db_id: str, req: KGOSQueryRequest):
    from services.kgos_query_engine import kgos_query_engine
    try:
        return kgos_query_engine.intent_search(
            db_id=db_id, query=req.query,
            alpha=req.alpha, beta=req.beta, gamma=req.gamma, delta=req.delta,
            limit=req.limit, methods=req.methods,
        )
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/kgos/impact/{db_id}/{node_id}")
async def kgos_impact(db_id: str, node_id: str, req: KGOSImpactRequest):
    from services.kgos_query_engine import kgos_query_engine
    try:
        return kgos_query_engine.impact_analysis(db_id, node_id, req.direction, req.max_depth)
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/kgos/compose/{db_id}")
async def kgos_compose(db_id: str, req: KGOSComposeRequest):
    from services.kgos_query_engine import kgos_query_engine
    try:
        return kgos_query_engine.compose_for(db_id, req.goal, req.max_steps)
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/kgos/similar/{db_id}/{node_id}")
async def kgos_similar(db_id: str, node_id: str, k: int = 10):
    from services.kgos_query_engine import kgos_query_engine
    try:
        return kgos_query_engine.similar_to(db_id, node_id, k)
    except Exception as e:
        raise HTTPException(400, str(e))


# ══════════════════════════════════════════════════════════════════════
# Expert CRUD Endpoints — dynamic /{expert_id} routes after static /kgos/* routes
# ══════════════════════════════════════════════════════════════════════

@router.get("")
async def list_experts():
    from services.expert_service import expert_service
    return expert_service.list_experts()


@router.post("")
async def create_expert(data: ExpertCreate):
    from services.expert_service import expert_service
    return expert_service.create_expert(data.model_dump())


@router.get("/{expert_id}")
async def get_expert(expert_id: str):
    from services.expert_service import expert_service
    expert = expert_service.get_expert(expert_id)
    if not expert:
        raise HTTPException(404, "Expert not found")
    return expert


@router.put("/{expert_id}")
async def update_expert(expert_id: str, data: ExpertUpdate):
    from services.expert_service import expert_service
    updated = data.model_dump(exclude_none=True)
    result = expert_service.update_expert(expert_id, updated)
    if not result:
        raise HTTPException(404, "Expert not found")
    return result


@router.delete("/{expert_id}")
async def delete_expert(expert_id: str):
    from services.expert_service import expert_service
    expert_service.delete_expert(expert_id)
    return {"status": "deleted", "id": expert_id}


@router.post("/{expert_id}/duplicate")
async def duplicate_expert(expert_id: str):
    from services.expert_service import expert_service
    result = expert_service.duplicate_expert(expert_id)
    if not result:
        raise HTTPException(404, "Expert not found")
    return result


# ── Expert Chat (SSE Streaming) ──────────────────────────────────────

@router.post("/{expert_id}/chat")
async def expert_chat(expert_id: str, req: ExpertChatRequest):
    from services.expert_service import expert_service

    expert = expert_service.get_expert(expert_id)
    if not expert:
        raise HTTPException(404, "Expert not found")

    async def stream():
        async for chunk in expert_service.execute(
            expert_id=expert_id,
            query=req.query,
            conversation_id=req.conversation_id,
            history=req.history,
        ):
            yield f"data: {chunk}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


# ── Expert Conversation Endpoints ────────────────────────────────────

@router.get("/{expert_id}/conversations")
async def list_conversations(expert_id: str):
    from services.expert_service import expert_service
    return expert_service.list_conversations(expert_id)


@router.get("/{expert_id}/conversations/{conversation_id}")
async def get_conversation(expert_id: str, conversation_id: str):
    from services.expert_service import expert_service
    conv = expert_service.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(404, "Conversation not found")
    return conv


@router.delete("/{expert_id}/conversations/{conversation_id}")
async def delete_conversation(expert_id: str, conversation_id: str):
    from services.expert_service import expert_service
    expert_service.delete_conversation(conversation_id)
    return {"status": "deleted", "id": conversation_id}

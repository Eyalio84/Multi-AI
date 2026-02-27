"""Games router — Phaser 3 RPG game projects, interview, generation, chat, LLM."""

import json
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter(prefix="/games", tags=["Games"])


# ── Request Models ────────────────────────────────────────────────────

class GameCreate(BaseModel):
    name: str
    description: str = ""

class GameUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    files: Optional[dict] = None
    settings: Optional[dict] = None

class InterviewAnswer(BaseModel):
    question_id: str
    answer: str | list[str]

class GenerateRequest(BaseModel):
    kg_context: str = ""

class RefineRequest(BaseModel):
    prompt: str
    files: dict = {}

class ChatRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None
    history: list[dict] = []

class LLMChatRequest(BaseModel):
    npc_name: str
    system_prompt: str
    message: str
    history: list[dict] = []

class LLMLoadRequest(BaseModel):
    model_type: str


# ── Static routes first (before /{id} patterns) ──────────────────────

@router.get("/interview/questions")
async def get_interview_questions():
    from services.game_service import game_service
    return game_service.get_interview_questions()


@router.get("/llm/status")
async def llm_status():
    from services.game_llm_service import game_llm_service
    return game_llm_service.get_status()


@router.post("/llm/load")
async def llm_load(req: LLMLoadRequest):
    from services.game_llm_service import game_llm_service
    result = game_llm_service.load_model(req.model_type)
    if "error" in result:
        raise HTTPException(400, result["error"])
    return result


@router.post("/llm/unload")
async def llm_unload():
    from services.game_llm_service import game_llm_service
    return game_llm_service.unload()


@router.post("/llm/chat")
async def llm_chat(req: LLMChatRequest):
    from services.game_llm_service import game_llm_service
    result = game_llm_service.chat(
        npc_name=req.npc_name,
        system_prompt=req.system_prompt,
        user_message=req.message,
        history=req.history,
    )
    if "error" in result:
        raise HTTPException(400, result["error"])
    return result


# ── CRUD ──────────────────────────────────────────────────────────────

@router.get("")
async def list_games():
    from services.game_service import game_service
    return game_service.list_projects()


@router.post("")
async def create_game(data: GameCreate):
    from services.game_service import game_service
    return game_service.create_project(data.name, data.description)


@router.get("/{game_id}")
async def get_game(game_id: str):
    from services.game_service import game_service
    project = game_service.get_project(game_id)
    if not project:
        raise HTTPException(404, "Game project not found")
    return project


@router.put("/{game_id}")
async def update_game(game_id: str, data: GameUpdate):
    from services.game_service import game_service
    updates = data.model_dump(exclude_none=True)
    result = game_service.update_project(game_id, updates)
    if not result:
        raise HTTPException(404, "Game project not found")
    return result


@router.delete("/{game_id}")
async def delete_game(game_id: str):
    from services.game_service import game_service
    game_service.delete_project(game_id)
    return {"status": "deleted"}


# ── Interview ─────────────────────────────────────────────────────────

@router.post("/{game_id}/interview")
async def submit_interview_answer(game_id: str, data: InterviewAnswer):
    from services.game_service import game_service
    result = game_service.submit_answer(game_id, data.question_id, data.answer)
    if not result:
        raise HTTPException(404, "Game project not found")
    return result


# ── GDD Synthesis ─────────────────────────────────────────────────────

@router.post("/{game_id}/synthesize")
async def synthesize_gdd(game_id: str):
    from services.game_service import game_service
    gdd = game_service.synthesize_gdd(game_id)
    if not gdd:
        raise HTTPException(404, "Game project not found")
    return gdd


# ── Generation (SSE) ─────────────────────────────────────────────────

@router.post("/{game_id}/generate")
async def generate_game(game_id: str, req: GenerateRequest):
    from services.game_service import game_service
    from services.game_generator import game_generator

    project = game_service.get_project(game_id)
    if not project:
        raise HTTPException(404, "Game project not found")

    gdd = project.get("game_design_doc")
    if not gdd or (isinstance(gdd, str) and not gdd.strip()):
        # Auto-synthesize if interview is complete
        interview_data = project.get("interview_data", {})
        if interview_data and len(interview_data) >= 4:
            gdd = game_service.synthesize_gdd(game_id)
        if not gdd:
            raise HTTPException(400, "No GDD found — complete the interview first")

    async def stream():
        files = {}
        async for chunk in game_generator.generate(gdd, kg_context=req.kg_context):
            # Capture final files
            try:
                data = json.loads(chunk)
                if data.get("type") == "files_complete":
                    files = data.get("files", {})
            except (json.JSONDecodeError, TypeError):
                pass
            yield f"data: {chunk}\n\n"

        # Save files to project
        if files:
            game_service.update_project(game_id, {
                "files": files,
                "status": "playable",
            })

    return StreamingResponse(stream(), media_type="text/event-stream")


# ── Refine (SSE) ─────────────────────────────────────────────────────

@router.post("/{game_id}/refine")
async def refine_game(game_id: str, req: RefineRequest):
    from services.game_service import game_service
    from services.game_generator import game_generator

    project = game_service.get_project(game_id)
    if not project:
        raise HTTPException(404, "Game project not found")

    files = req.files or project.get("files", {})

    async def stream():
        final_files = {}
        async for chunk in game_generator.refine(files, req.prompt):
            try:
                data = json.loads(chunk)
                if data.get("type") == "files_complete":
                    final_files = data.get("files", {})
            except (json.JSONDecodeError, TypeError):
                pass
            yield f"data: {chunk}\n\n"

        if final_files:
            game_service.update_project(game_id, {
                "files": final_files,
                "status": "playable",
            })

    return StreamingResponse(stream(), media_type="text/event-stream")


# ── Versions ──────────────────────────────────────────────────────────

@router.post("/{game_id}/save")
async def save_version(game_id: str):
    from services.game_service import game_service
    result = game_service.save_version(game_id)
    if not result:
        raise HTTPException(404, "Game project not found")
    return result


@router.get("/{game_id}/versions")
async def list_versions(game_id: str):
    from services.game_service import game_service
    return game_service.list_versions(game_id)


@router.post("/{game_id}/versions/{version_number}/restore")
async def restore_version(game_id: str, version_number: int):
    from services.game_service import game_service
    result = game_service.restore_version(game_id, version_number)
    if not result:
        raise HTTPException(404, "Version not found")
    return result


# ── Export ────────────────────────────────────────────────────────────

@router.get("/{game_id}/export")
async def export_game(game_id: str):
    import io
    import zipfile
    from services.game_service import game_service

    project = game_service.get_project(game_id)
    if not project:
        raise HTTPException(404, "Game project not found")

    files = project.get("files", {})
    if not files:
        raise HTTPException(400, "No files to export")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for path, content in files.items():
            zf.writestr(path, content)

    buf.seek(0)
    name = project.get("name", "game").replace(" ", "_").lower()
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{name}.zip"'},
    )


# ── Expert Chat (SSE) ────────────────────────────────────────────────

@router.post("/{game_id}/chat")
async def game_chat(game_id: str, req: ChatRequest):
    from services.game_service import game_service

    project = game_service.get_project(game_id)
    if not project:
        raise HTTPException(404, "Game project not found")

    expert_id = game_service.ensure_expert()
    if not expert_id:
        raise HTTPException(500, "Failed to create GameForge expert")

    from services.expert_service import expert_service

    # Enrich query with game context
    gdd = project.get("game_design_doc", {})
    context = f"[Game: {project.get('name', '')}] "
    if gdd:
        context += f"[Genre: {gdd.get('meta', {}).get('genre', '')}] "
    enriched_query = context + req.query

    async def stream():
        async for chunk in expert_service.execute(
            expert_id=expert_id,
            query=enriched_query,
            conversation_id=req.conversation_id,
            history=req.history,
        ):
            yield f"data: {chunk}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


# ── Pattern Extraction ────────────────────────────────────────────────

@router.post("/{game_id}/extract-patterns")
async def extract_patterns(game_id: str):
    from services.game_service import game_service
    patterns = game_service.extract_patterns(game_id)
    return {"patterns": patterns, "count": len(patterns)}

"""Claude Agent SDK endpoints for autonomous agent tasks."""
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional

from services import agent_sdk_service

router = APIRouter()


class AgentRunRequest(BaseModel):
    prompt: str
    allowed_tools: Optional[list[str]] = None
    model: Optional[str] = None
    cwd: Optional[str] = None
    max_turns: Optional[int] = None
    session_id: Optional[str] = None


@router.post("/agent/run")
async def run_agent(request: AgentRunRequest):
    """Run an autonomous Claude agent task. Returns SSE stream."""
    async def event_stream():
        async for event in agent_sdk_service.run_agent_task(
            prompt=request.prompt,
            allowed_tools=request.allowed_tools,
            model=request.model,
            cwd=request.cwd,
            max_turns=request.max_turns,
            session_id=request.session_id,
        ):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/agent/sessions")
async def list_sessions():
    """List recent agent sessions."""
    sessions = await agent_sdk_service.list_sessions()
    return sessions


@router.get("/agent/sessions/{session_id}")
async def get_session(session_id: str):
    """Get status of a specific agent session."""
    session = await agent_sdk_service.get_session_status(session_id)
    if session is None:
        return JSONResponse(status_code=404, content={"message": "Session not found"})
    return session

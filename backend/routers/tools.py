"""Tools Playground router — list, inspect, and execute 30 Python tools."""
import json
from fastapi import APIRouter
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Any

from services.tools_service import tools_service

router = APIRouter()


class RunToolRequest(BaseModel):
    params: dict[str, Any] = {}


@router.get("/tools")
async def list_tools():
    """List all tools grouped by category."""
    return tools_service.list_tools()


@router.get("/tools/{tool_id}")
async def get_tool(tool_id: str):
    """Get full tool definition with param schema."""
    detail = tools_service.get_tool(tool_id)
    if not detail:
        return JSONResponse(status_code=404, content={"error": f"Tool not found: {tool_id}"})
    return detail


@router.post("/tools/{tool_id}/run")
async def run_tool(tool_id: str, body: RunToolRequest):
    """Execute a tool and return JSON result."""
    result = await tools_service.run_tool(tool_id, body.params)
    if not result.get("success"):
        return JSONResponse(status_code=422, content=result)
    return result


@router.post("/tools/{tool_id}/run/stream")
async def run_tool_stream(tool_id: str, body: RunToolRequest):
    """Execute a tool with SSE streaming for progress updates."""
    async def event_stream():
        yield f"data: {json.dumps({'type': 'progress', 'message': 'Starting tool execution...'})}\n\n"
        result = await tools_service.run_tool(tool_id, body.params)
        if result.get("success"):
            yield f"data: {json.dumps({'type': 'result', 'data': result['result']})}\n\n"
        else:
            yield f"data: {json.dumps({'type': 'error', 'message': result.get('error', 'Unknown error')})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

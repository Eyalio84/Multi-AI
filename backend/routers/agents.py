"""NLKE agent execution and pipeline endpoints."""
import asyncio
import json
import sqlite3
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from services.agent_bridge import (
    AgentBridge,
    AGENT_CATALOG,
    CUSTOM_AGENTS_DB,
    _get_agents_conn,
)

router = APIRouter()
bridge = AgentBridge()


@router.get("/agents")
async def list_agents():
    """List all available NLKE agents with metadata."""
    try:
        agents = bridge.list_agents()
        return {"agents": agents}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/agents")
async def create_agent(request: Request):
    """Create a custom agent definition."""
    body = await request.json()
    name = body.get("name", "").strip()
    if not name:
        return JSONResponse(status_code=400, content={"error": "Agent name is required"})

    if name in AGENT_CATALOG:
        return JSONResponse(status_code=409, content={"error": f"'{name}' conflicts with a built-in agent name"})

    description = body.get("description", "")
    category = body.get("category", "CUSTOM")
    system_prompt = body.get("system_prompt", "")
    tools = body.get("tools", [])
    agent_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    conn = _get_agents_conn()
    try:
        conn.execute(
            "INSERT INTO custom_agents (id, name, description, category, system_prompt, tools, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (agent_id, name, description, category, system_prompt, json.dumps(tools), now),
        )
        conn.commit()
        return {
            "agent": {
                "id": agent_id,
                "name": name,
                "description": description,
                "category": category,
                "system_prompt": system_prompt,
                "tools": tools,
                "created_at": now,
                "type": "custom",
            }
        }
    except sqlite3.IntegrityError:
        return JSONResponse(status_code=409, content={"error": f"Agent '{name}' already exists"})
    finally:
        conn.close()


@router.get("/agents/{name}/example")
async def get_example(name: str):
    """Get example workload for an agent."""
    try:
        example = await asyncio.to_thread(bridge.get_example, name)
        return {"example": example}
    except Exception as e:
        return JSONResponse(status_code=404, content={"error": str(e)})


@router.post("/agents/{name}/run")
async def run_agent(name: str, request_body: dict):
    """Execute an NLKE agent with a workload."""
    try:
        workload = request_body.get("workload", {})
        result = await asyncio.to_thread(bridge.run_agent, name, workload)
        return {"result": result}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/agents/{name}/export/claude-code")
async def export_agent_claude_code(name: str):
    """Export an agent definition as Claude Code skill JSON."""
    info = AGENT_CATALOG.get(name)
    if info is not None:
        return {
            "name": name,
            "description": info["description"],
            "system_prompt": (
                f"You are the '{name}' agent in the {info['category']} category.\n"
                f"Your role: {info['description']}\n\n"
                "Analyze the user's workload and provide a thorough, actionable response. "
                "Structure your output with clear sections. Be specific and practical."
            ),
            "tools": [],
            "model": "claude-sonnet-4-6",
            "max_turns": 10,
        }

    custom = bridge._get_custom_agent(name)
    if custom is not None:
        return {
            "name": custom["name"],
            "description": custom.get("description", ""),
            "system_prompt": custom.get("system_prompt", ""),
            "tools": custom.get("tools", []),
            "model": "claude-sonnet-4-6",
            "max_turns": 10,
        }

    return JSONResponse(status_code=404, content={"error": f"Agent '{name}' not found"})


@router.post("/pipelines/run")
async def run_pipeline(request_body: dict):
    """Execute a multi-agent pipeline."""
    try:
        steps = request_body.get("steps", [])
        result = await asyncio.to_thread(bridge.run_pipeline, steps)
        return {"result": result}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

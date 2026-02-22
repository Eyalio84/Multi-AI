"""NLKE agent execution and pipeline endpoints."""
import asyncio
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from services.agent_bridge import AgentBridge

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


@router.post("/pipelines/run")
async def run_pipeline(request_body: dict):
    """Execute a multi-agent pipeline."""
    try:
        steps = request_body.get("steps", [])
        result = await asyncio.to_thread(bridge.run_pipeline, steps)
        return {"result": result}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

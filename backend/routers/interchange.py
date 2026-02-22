"""JSON import/export between standalone and claude-code modes, and API key configuration."""
import os
from datetime import datetime
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

import config

router = APIRouter()


# --- Mode ---

@router.get("/mode")
async def get_mode():
    """Return current operating mode."""
    return {"mode": config.MODE}


@router.post("/mode")
async def set_mode(request: Request):
    """Switch operating mode."""
    body = await request.json()
    new_mode = body.get("mode", "standalone")
    if new_mode not in ("standalone", "claude-code"):
        return JSONResponse(status_code=400, content={"error": "Invalid mode. Use 'standalone' or 'claude-code'."})

    config.MODE = new_mode
    if new_mode == "claude-code":
        config.ANTHROPIC_API_KEY = None
    else:
        config.ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    return {"mode": config.MODE, "claude_available": bool(config.ANTHROPIC_API_KEY)}


# --- API Key Configuration ---

@router.get("/config/keys/status")
async def get_keys_status():
    """Check which API keys are configured (never exposes actual keys)."""
    return {
        "gemini": bool(config.GEMINI_API_KEY),
        "anthropic": bool(config.ANTHROPIC_API_KEY),
        "mode": config.MODE,
    }


@router.post("/config/keys")
async def set_keys(request: Request):
    """Set API keys at runtime. Keys are stored in memory only (not written to disk)."""
    body = await request.json()
    gemini_key = body.get("gemini_key")
    anthropic_key = body.get("anthropic_key")

    if not gemini_key and not anthropic_key:
        return JSONResponse(status_code=400, content={"error": "Provide at least one key: gemini_key or anthropic_key."})

    config.update_api_keys(
        gemini_key=gemini_key if gemini_key else None,
        anthropic_key=anthropic_key if anthropic_key else None,
    )

    return {
        "updated": True,
        "gemini_configured": bool(config.GEMINI_API_KEY),
        "anthropic_configured": bool(config.ANTHROPIC_API_KEY),
    }


@router.post("/export")
async def export_workspace(request: Request):
    """Export workspace state as JSON interchange format."""
    body = await request.json()
    export_data = {
        "version": "1.0",
        "mode": config.MODE,
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "projects": body.get("projects", []),
            "files": body.get("files", {}),
            "workflows": body.get("workflows", []),
            "agentResults": body.get("agentResults", []),
            "chatHistory": body.get("chatHistory", []),
            "playbooks": body.get("playbooks", []),
            "personas": body.get("personas", []),
        },
    }
    return export_data


@router.post("/import")
async def import_workspace(request: Request):
    """Import workspace JSON from the other mode."""
    body = await request.json()
    if body.get("version") != "1.0":
        return JSONResponse(status_code=400, content={"error": "Unsupported export version. Expected 1.0."})

    data = body.get("data", {})
    return {
        "imported": True,
        "counts": {
            "projects": len(data.get("projects", [])),
            "files": sum(len(v) for v in data.get("files", {}).values()),
            "workflows": len(data.get("workflows", [])),
            "chatMessages": len(data.get("chatHistory", [])),
            "personas": len(data.get("personas", [])),
        },
        "data": data,
    }

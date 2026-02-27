"""JSON import/export between standalone and claude-code modes, and API key configuration."""
import json
import os
import re
from datetime import datetime
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

import config
from backend_types.backend_spec import BackendSpec

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


# --- Studio export with backend spec ---

EXTRACT_SPEC_SYSTEM_PROMPT = """\
Analyze the provided project files and extract a structured backend specification \
as JSON. Return ONLY valid JSON with keys: version, framework, language, database \
(with tables and columns), endpoints (method, path, summary, request_body, response, \
auth_required), models (name and fields), dependencies, environment_variables. \
Omit database if no persistence is needed. Infer the backend from frontend code if \
no backend files exist.
"""


@router.post("/studio/export-with-spec")
async def export_with_spec(request: Request):
    """Export project as JSON with structured backend specification included."""
    from services import gemini_service, studio_service

    body = await request.json()
    project_id = body.get("project_id")
    if not project_id:
        return JSONResponse(status_code=400, content={"error": "project_id is required"})

    project = studio_service.get_project(project_id)
    if not project:
        return JSONResponse(status_code=404, content={"message": "Project not found"})

    files = project.get("files") or {}
    if isinstance(files, str):
        files = json.loads(files)

    chat_history = project.get("chat_history") or []
    if isinstance(chat_history, str):
        chat_history = json.loads(chat_history)

    # Extract backend spec via AI
    backend_spec = None
    try:
        parts = ["Project files:\n"]
        for path, content in files.items():
            file_content = content["content"] if isinstance(content, dict) else content
            parts.append(f"### FILE: {path}\n{file_content}\n### END FILE\n")
        parts.append("\nExtract the backend specification as JSON.")

        raw_response = gemini_service.generate_content(
            prompt="\n".join(parts),
            model="gemini-2.5-flash",
            system_instruction=EXTRACT_SPEC_SYSTEM_PROMPT,
            response_mime_type="application/json",
        )

        spec_data = json.loads(raw_response)
        spec = BackendSpec(**spec_data)
        backend_spec = spec.model_dump()
    except json.JSONDecodeError:
        json_match = re.search(r'\{[\s\S]*\}', raw_response)
        if json_match:
            try:
                spec_data = json.loads(json_match.group())
                spec = BackendSpec(**spec_data)
                backend_spec = spec.model_dump()
            except Exception:
                backend_spec = None
    except Exception:
        backend_spec = None

    return {
        "version": "1.0",
        "project": {
            "id": project.get("id"),
            "name": project.get("name"),
            "description": project.get("description"),
        },
        "files": files,
        "chat_history": chat_history,
        "backend_spec": backend_spec,
    }

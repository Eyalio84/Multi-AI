"""Studio feature — AI-powered React app generation with live preview."""
import json
import re
import io
import zipfile
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, JSONResponse

from config import MODE, ANTHROPIC_API_KEY
from services import gemini_service, claude_service
from services import studio_service

router = APIRouter()

# ---------------------------------------------------------------------------
# System prompt for React app generation
# ---------------------------------------------------------------------------

GENERATE_SYSTEM_PROMPT = """\
You are a Full-Stack React app generator.

When generating an app:
1. First, briefly describe your plan (2-3 sentences).
2. Then generate each file wrapped in markers:

### FILE: /App.js
import React from 'react';
// ... complete file content
export default App;
### END FILE

### FILE: /components/Header.js
// ... content
### END FILE

Rules:
- Use functional React components with hooks
- Use inline styles (style={{...}}) - NOT CSS classes or Tailwind
- App.js is always the entry point
- All imports should use relative paths starting with ./
- Make the app visually polished with proper spacing, colors, shadows
- Include responsive design via inline style media queries or window.innerWidth checks
- Generate complete, runnable code - no TODOs or placeholders
- IMPORTANT: Do NOT wrap file contents in markdown code fences (```). Write raw code directly after the ### FILE marker line. No ```javascript or ``` delimiters.
- If you need npm packages beyond react/react-dom, list them as:
### DEPS: {"package-name": "^version"}
"""

REFINE_SYSTEM_PROMPT = """\
You are a Full-Stack React app refiner. The user has an existing React app and wants changes.

Existing files are provided below. When refining:
1. Briefly describe what you will change (1-2 sentences).
2. Only output the files that changed, using the same marker format:

### FILE: /path/to/file.js
// complete updated content
### END FILE

Rules:
- Use functional React components with hooks
- Use inline styles (style={{...}}) - NOT CSS classes or Tailwind
- Maintain consistency with existing code style
- Generate complete file contents, not diffs
- IMPORTANT: Do NOT wrap file contents in markdown code fences (```). Write raw code directly after the ### FILE marker line. No ```javascript or ``` delimiters.
- If you need new npm packages, list them as:
### DEPS: {"package-name": "^version"}
"""


# ---------------------------------------------------------------------------
# Helpers: parse streaming tokens for file markers
# ---------------------------------------------------------------------------

def _build_user_prompt(prompt: str, files: dict | None, mode: str) -> str:
    """Build the user prompt including existing files for refine mode."""
    parts = []
    if mode == "refine" and files:
        parts.append("Here are the current project files:\n")
        for path, content in files.items():
            parts.append(f"### FILE: {path}\n{content}\n### END FILE\n")
        parts.append("\n---\n")
    parts.append(f"User request: {prompt}")
    return "\n".join(parts)


def _parse_file_markers(text: str):
    """Extract file blocks and deps from accumulated text.

    Returns (plan_text, files_dict, deps_dict, remainder).
    - plan_text: text before the first ### FILE marker
    - files_dict: {path: content}
    - deps_dict: {package: version}
    - remainder: any trailing text after last ### END FILE that may be
      an incomplete new block (to carry forward in streaming)
    """
    files = {}
    deps = {}

    # Extract deps
    for m in re.finditer(r'### DEPS:\s*(\{[^}]+\})', text):
        try:
            deps.update(json.loads(m.group(1)))
        except json.JSONDecodeError:
            pass

    # Split on file markers
    file_pattern = re.compile(
        r'### FILE:\s*(/[^\n]+)\n(.*?)### END FILE',
        re.DOTALL,
    )

    plan_text = text
    first_file_pos = None
    for m in file_pattern.finditer(text):
        if first_file_pos is None:
            first_file_pos = m.start()
        path = m.group(1).strip()
        content = m.group(2).rstrip("\n")
        # Strip markdown code fences that AI models sometimes wrap content in
        content = re.sub(r'^```[\w]*\n?', '', content)
        content = re.sub(r'\n?```\s*$', '', content)
        files[path] = content

    if first_file_pos is not None:
        plan_text = text[:first_file_pos].strip()

    # Check for incomplete trailing block
    remainder = ""
    last_end = 0
    for m in file_pattern.finditer(text):
        last_end = m.end()
    if last_end > 0:
        trailing = text[last_end:]
        if "### FILE:" in trailing:
            remainder = trailing

    return plan_text, files, deps, remainder


# ---------------------------------------------------------------------------
# POST /studio/stream — Main AI streaming endpoint
# ---------------------------------------------------------------------------

@router.post("/studio/stream")
async def studio_stream(request: Request):
    """Stream AI-generated React app files via SSE."""
    body = await request.json()
    project_id = body.get("project_id")
    prompt = body.get("prompt", "")
    files = body.get("files")  # existing files dict for refine mode
    chat_history = body.get("chat_history", [])
    provider = body.get("provider", "gemini")
    model = body.get("model")
    mode = body.get("mode", "generate")  # "generate" or "refine"

    system_prompt = REFINE_SYSTEM_PROMPT if mode == "refine" else GENERATE_SYSTEM_PROMPT
    user_prompt = _build_user_prompt(prompt, files, mode)

    # Build messages list for the AI
    messages = []
    for msg in chat_history[-10:]:  # keep last 10 for context window
        author = msg.get("author", msg.get("role", "user"))
        text = msg.get("text", "")
        if not text and "parts" in msg:
            text = " ".join(p.get("text", "") for p in msg["parts"])
        if text:
            messages.append({
                "author": author,
                "parts": [{"text": text}],
            })
    # Append current user message
    messages.append({
        "author": "user",
        "parts": [{"text": user_prompt}],
    })

    async def generate():
        accumulated = ""
        emitted_files = set()
        emitted_deps = {}
        plan_emitted = False

        try:
            # Choose provider
            if provider == "claude" and MODE == "standalone" and ANTHROPIC_API_KEY:
                target_model = model or "claude-sonnet-4-6"
                stream = claude_service.stream_chat(
                    messages=messages,
                    model=target_model,
                    system=system_prompt,
                    max_tokens=16384,
                    temperature=0.7,
                )
            else:
                target_model = model or "gemini-2.5-flash"
                stream = gemini_service.stream_chat(
                    messages=messages,
                    model=target_model,
                    system_instruction=system_prompt,
                    temperature=0.7,
                )

            async for chunk in stream:
                if chunk.get("type") == "token":
                    token_text = chunk["content"]
                    accumulated += token_text

                    # Emit raw token for chat display
                    yield f"data: {json.dumps({'type': 'token', 'content': token_text})}\n\n"

                    # Parse accumulated text for completed file blocks
                    plan_text, parsed_files, parsed_deps, _ = _parse_file_markers(accumulated)

                    # Emit plan (text before first file marker)
                    if not plan_emitted and plan_text and parsed_files:
                        yield f"data: {json.dumps({'type': 'studio_plan', 'content': plan_text})}\n\n"
                        plan_emitted = True

                    # Emit newly completed files
                    for path, content in parsed_files.items():
                        if path not in emitted_files:
                            emitted_files.add(path)
                            yield f"data: {json.dumps({'type': 'studio_file', 'path': path, 'content': content})}\n\n"

                    # Emit new deps
                    for pkg, ver in parsed_deps.items():
                        if pkg not in emitted_deps:
                            emitted_deps[pkg] = ver
                            yield f"data: {json.dumps({'type': 'studio_deps', 'dependencies': {pkg: ver}})}\n\n"

                elif chunk.get("type") == "done":
                    # Final parse pass — catch any remaining blocks
                    plan_text, parsed_files, parsed_deps, _ = _parse_file_markers(accumulated)

                    if not plan_emitted and plan_text:
                        yield f"data: {json.dumps({'type': 'studio_plan', 'content': plan_text})}\n\n"

                    for path, content in parsed_files.items():
                        if path not in emitted_files:
                            emitted_files.add(path)
                            yield f"data: {json.dumps({'type': 'studio_file', 'path': path, 'content': content})}\n\n"

                    for pkg, ver in parsed_deps.items():
                        if pkg not in emitted_deps:
                            emitted_deps[pkg] = ver
                            yield f"data: {json.dumps({'type': 'studio_deps', 'dependencies': {pkg: ver}})}\n\n"

                    # Auto-save files to project if we have a project_id
                    if project_id and parsed_files:
                        try:
                            project = studio_service.get_project(project_id)
                            if project:
                                existing_files = project.get("files") or {}
                                if isinstance(existing_files, str):
                                    existing_files = json.loads(existing_files)
                                existing_files.update(parsed_files)
                                studio_service.update_project(project_id, {
                                    "files": existing_files,
                                })
                        except Exception:
                            pass  # Non-critical: don't break the stream

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ---------------------------------------------------------------------------
# Project CRUD
# ---------------------------------------------------------------------------

@router.post("/studio/projects")
async def create_project(request: Request):
    """Create a new Studio project."""
    body = await request.json()
    name = body.get("name", "Untitled Project")
    description = body.get("description", "")
    try:
        project = studio_service.create_project(name, description)
        return project
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


@router.get("/studio/projects")
async def list_projects():
    """List all Studio projects (summaries)."""
    try:
        projects = studio_service.list_projects()
        return projects
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


@router.get("/studio/projects/{project_id}")
async def get_project(project_id: str):
    """Load a full project with files, chat, and versions."""
    try:
        project = studio_service.get_project(project_id)
        if not project:
            return JSONResponse(status_code=404, content={"message": "Project not found"})
        # _row_to_dict already parses JSON columns — only parse if still a string
        for key in ("files", "chat_history", "settings"):
            val = project.get(key)
            if isinstance(val, str):
                try:
                    project[key] = json.loads(val)
                except (json.JSONDecodeError, TypeError):
                    project[key] = {} if key != "chat_history" else []
        project["versions"] = studio_service.list_versions(project_id)
        return project
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


@router.put("/studio/projects/{project_id}")
async def update_project(project_id: str, request: Request):
    """Update project fields."""
    body = await request.json()
    try:
        # Serialize dicts to JSON strings for storage
        data = {}
        for key in ("name", "description"):
            if key in body:
                data[key] = body[key]
        for key in ("files", "chat_history", "settings"):
            if key in body:
                data[key] = json.dumps(body[key]) if isinstance(body[key], (dict, list)) else body[key]
        studio_service.update_project(project_id, data)
        return {"status": "ok"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


@router.delete("/studio/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project and all its versions."""
    try:
        studio_service.delete_project(project_id)
        return {"status": "deleted"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


# ---------------------------------------------------------------------------
# Version management
# ---------------------------------------------------------------------------

@router.post("/studio/projects/{project_id}/save")
async def save_version(project_id: str, request: Request):
    """Save a version snapshot of the current project files."""
    body = await request.json()
    message = body.get("message", "Manual save")
    try:
        version = studio_service.save_version(project_id, message)
        return version
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


@router.get("/studio/projects/{project_id}/versions")
async def list_versions(project_id: str):
    """List all versions for a project."""
    try:
        versions = studio_service.list_versions(project_id)
        return versions
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


@router.get("/studio/projects/{project_id}/versions/{version_number}")
async def get_version(project_id: str, version_number: int):
    """Get a specific version snapshot."""
    try:
        version = studio_service.get_version(project_id, version_number)
        if not version:
            return JSONResponse(status_code=404, content={"message": "Version not found"})
        if isinstance(version.get("files"), str):
            try:
                version["files"] = json.loads(version["files"])
            except (json.JSONDecodeError, TypeError):
                version["files"] = {}
        return version
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


@router.post("/studio/projects/{project_id}/versions/{version_number}/restore")
async def restore_version(project_id: str, version_number: int):
    """Restore a project to a specific version."""
    try:
        studio_service.restore_version(project_id, version_number)
        return {"status": "restored", "version": version_number}
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


# ---------------------------------------------------------------------------
# Mock server stubs
# ---------------------------------------------------------------------------

@router.post("/studio/projects/{project_id}/mock/start")
async def start_mock(project_id: str):
    """Start mock server (stub)."""
    return {"running": False, "message": "Mock server not yet implemented"}


@router.post("/studio/projects/{project_id}/mock/stop")
async def stop_mock(project_id: str):
    """Stop mock server (stub)."""
    return {"running": False}


@router.get("/studio/projects/{project_id}/mock/status")
async def mock_status(project_id: str):
    """Get mock server status (stub)."""
    return {"running": False, "port": None, "pid": None}


@router.post("/studio/projects/{project_id}/mock/update")
async def update_mock(project_id: str):
    """Update mock server routes (stub)."""
    return {"running": False, "message": "Mock server not yet implemented"}


# ---------------------------------------------------------------------------
# OpenAPI spec & TypeScript types (stubs calling extractors)
# ---------------------------------------------------------------------------

@router.get("/studio/projects/{project_id}/api-spec")
async def get_api_spec(project_id: str):
    """Extract OpenAPI spec from project's Python/FastAPI files."""
    try:
        project = studio_service.get_project(project_id)
        if not project:
            return JSONResponse(status_code=404, content={"message": "Project not found"})

        files = json.loads(project.get("files") or "{}")

        # Look for Python files that might contain FastAPI routes
        from services.openapi_extractor import extract_openapi_from_code
        combined_spec = {
            "openapi": "3.0.0",
            "info": {"title": "Generated API", "version": "1.0.0"},
            "paths": {},
            "components": {"schemas": {}},
        }
        for path, content in files.items():
            if path.endswith(".py"):
                spec = extract_openapi_from_code(content)
                combined_spec["paths"].update(spec.get("paths", {}))
                combined_spec["components"]["schemas"].update(
                    spec.get("components", {}).get("schemas", {})
                )
        return combined_spec
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


@router.get("/studio/projects/{project_id}/types")
async def get_ts_types(project_id: str):
    """Generate TypeScript interfaces from project's API spec."""
    try:
        project = studio_service.get_project(project_id)
        if not project:
            return JSONResponse(status_code=404, content={"message": "Project not found"})

        files = json.loads(project.get("files") or "{}")

        from services.openapi_extractor import extract_openapi_from_code
        from services.type_generator import generate_typescript_types

        combined_spec = {
            "openapi": "3.0.0",
            "info": {"title": "Generated API", "version": "1.0.0"},
            "paths": {},
            "components": {"schemas": {}},
        }
        for path, content in files.items():
            if path.endswith(".py"):
                spec = extract_openapi_from_code(content)
                combined_spec["components"]["schemas"].update(
                    spec.get("components", {}).get("schemas", {})
                )

        ts_code = generate_typescript_types(combined_spec)
        return {"types": ts_code}
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


# ---------------------------------------------------------------------------
# Export as ZIP
# ---------------------------------------------------------------------------

@router.get("/studio/projects/{project_id}/export")
async def export_project(project_id: str, request: Request):
    """Export project files as a downloadable ZIP archive."""
    scope = request.query_params.get("scope", "all")  # "all", "frontend", "backend"
    try:
        zip_bytes = studio_service.export_project_zip(project_id, scope)
        if zip_bytes is None:
            return JSONResponse(status_code=404, content={"message": "Project not found"})

        project = studio_service.get_project(project_id)
        name = project.get("name", "project").replace(" ", "-").lower()

        return StreamingResponse(
            io.BytesIO(zip_bytes),
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{name}.zip"',
            },
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})

"""Coding assistant with tool use — dual model support."""
import json
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from config import MODE
from services import gemini_service, claude_service

router = APIRouter()

# Tool declarations for Gemini format
GEMINI_TOOL_DECLARATIONS = [
    {
        "name": "listFiles",
        "description": "List all files in the current project.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "createFile",
        "description": "Create a new file in the project.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path relative to project root"},
                "content": {"type": "string", "description": "File content"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "readFile",
        "description": "Read the content of a file.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "File path to read"}},
            "required": ["path"],
        },
    },
    {
        "name": "updateFile",
        "description": "Update an existing file's content.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to update"},
                "newContent": {"type": "string", "description": "New file content"},
            },
            "required": ["path", "newContent"],
        },
    },
    {
        "name": "deleteFile",
        "description": "Delete a file from the project.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "File path to delete"}},
            "required": ["path"],
        },
    },
    {
        "name": "searchNpm",
        "description": "Search the npm registry for packages.",
        "parameters": {
            "type": "object",
            "properties": {"packageName": {"type": "string", "description": "Package name to search for"}},
            "required": ["packageName"],
        },
    },
    {
        "name": "runPython",
        "description": "Execute Python code and return the result.",
        "parameters": {
            "type": "object",
            "properties": {"code": {"type": "string", "description": "Python code to execute"}},
            "required": ["code"],
        },
    },
]

# Tool declarations for Claude format
CLAUDE_TOOL_DEFINITIONS = [
    {
        "name": "listFiles",
        "description": "List all files in the current project.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "createFile",
        "description": "Create a new file in the project.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path relative to project root"},
                "content": {"type": "string", "description": "File content"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "readFile",
        "description": "Read the content of a file.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "File path to read"}},
            "required": ["path"],
        },
    },
    {
        "name": "updateFile",
        "description": "Update an existing file's content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to update"},
                "newContent": {"type": "string", "description": "New file content"},
            },
            "required": ["path", "newContent"],
        },
    },
    {
        "name": "deleteFile",
        "description": "Delete a file from the project.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "File path to delete"}},
            "required": ["path"],
        },
    },
    {
        "name": "searchNpm",
        "description": "Search the npm registry for packages.",
        "input_schema": {
            "type": "object",
            "properties": {"packageName": {"type": "string", "description": "Package name to search for"}},
            "required": ["packageName"],
        },
    },
    {
        "name": "runPython",
        "description": "Execute Python code and return the result.",
        "input_schema": {
            "type": "object",
            "properties": {"code": {"type": "string", "description": "Python code to execute"}},
            "required": ["code"],
        },
    },
]


def _build_coding_system_prompt(projects: list[dict], persona: dict | None, custom_styles: list[dict] | None) -> str:
    """Build system prompt with project context."""
    parts = ["You are an expert coding assistant. You have access to tools for file operations, npm search, and Python execution."]

    if projects:
        project_context = []
        for p in projects:
            ctx = f"Project: {p['name']}"
            if p.get("dependencySummary"):
                ctx += f"\nDependencies: {p['dependencySummary']}"
            project_context.append(ctx)
        parts.append("Active Projects:\n" + "\n".join(project_context))

    if persona:
        if persona.get("baseInstructions"):
            parts.append(persona["baseInstructions"])
        for style in persona.get("composedStyles", []):
            style_name = style.get("name", "")
            if custom_styles:
                matched = next((s for s in custom_styles if s["name"] == style_name), None)
                if matched:
                    parts.append(matched["instructions"])

    return "\n\n".join(parts)


@router.post("/coding/stream")
async def coding_stream(request: Request):
    """SSE streaming with tool use for coding assistant."""
    body = await request.json()
    messages = body.get("history", body.get("messages", []))
    projects = body.get("projects", [])
    persona = body.get("persona")
    custom_styles = body.get("customStyles", [])
    use_web_search = body.get("useWebSearch", False)
    provider = body.get("provider", "gemini")
    model = body.get("model")
    thinking_budget = body.get("thinkingBudget")

    system_prompt = _build_coding_system_prompt(projects, persona, custom_styles)

    async def generate():
        try:
            if provider == "claude" and MODE == "standalone":
                target_model = model or "claude-sonnet-4-6"
                gen = claude_service.stream_with_tools(
                    messages=messages,
                    tools=CLAUDE_TOOL_DEFINITIONS,
                    model=target_model,
                    system=system_prompt,
                )
            else:
                target_model = model or "gemini-2.5-flash"
                gen = gemini_service.stream_with_tools(
                    messages=messages,
                    tool_declarations=GEMINI_TOOL_DECLARATIONS,
                    model=target_model,
                    system_instruction=system_prompt,
                    use_web_search=use_web_search,
                )

            async for chunk in gen:
                yield f"data: {json.dumps(chunk)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

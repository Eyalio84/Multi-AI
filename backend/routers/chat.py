"""Chat streaming endpoint — dual-model support."""
import json
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from config import MODE
from services import gemini_service, claude_service

router = APIRouter()


def _build_system_prompt(persona: dict | None, custom_styles: list[dict] | None) -> str:
    """Compose system prompt from persona + styles."""
    parts = []
    if persona:
        if persona.get("baseInstructions"):
            parts.append(persona["baseInstructions"])
        for style in persona.get("composedStyles", []):
            style_name = style.get("name", "")
            weight = style.get("weight", 1)
            if custom_styles:
                matched = next((s for s in custom_styles if s["name"] == style_name), None)
                if matched:
                    parts.append(f"[Style: {style_name}, Weight: {weight}]\n{matched['instructions']}")
    return "\n\n".join(parts) if parts else None


@router.post("/chat/stream")
async def chat_stream(request: Request):
    """SSE streaming chat endpoint. Supports both Gemini and Claude."""
    body = await request.json()
    messages = body.get("messages", [])
    model = body.get("model")
    provider = body.get("provider", "gemini")
    persona = body.get("persona")
    custom_styles = body.get("customStyles", [])
    use_web_search = body.get("useWebSearch", False)
    thinking_budget = body.get("thinkingBudget")

    system_prompt = _build_system_prompt(persona, custom_styles)

    async def generate():
        try:
            if provider == "claude":
                if MODE != "standalone":
                    # Claude-code mode: return structured context for Claude Code
                    context = {
                        "type": "claude_code_context",
                        "messages": messages,
                        "system": system_prompt,
                        "model": model,
                        "instruction": "Feed this context into your Claude Code session for processing.",
                    }
                    yield f"data: {json.dumps({'type': 'claude_code_export', 'content': context})}\n\n"
                    yield f"data: {json.dumps({'type': 'done'})}\n\n"
                    return

                target_model = model or "claude-sonnet-4-6"
                if thinking_budget and thinking_budget > 0:
                    gen = claude_service.stream_with_thinking(
                        messages=messages,
                        model=target_model,
                        system=system_prompt,
                        thinking_budget=thinking_budget,
                    )
                else:
                    gen = claude_service.stream_chat(
                        messages=messages,
                        model=target_model,
                        system=system_prompt,
                    )
            else:
                target_model = model or "gemini-2.5-flash"
                gen = gemini_service.stream_chat(
                    messages=messages,
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

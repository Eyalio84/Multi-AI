"""Chat streaming endpoint — dual-model support via unified agentic loop."""
import json
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

router = APIRouter()


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
    conversation_id = body.get("conversationId")

    async def generate():
        from services.agentic_loop import agentic_loop
        try:
            async for chunk in agentic_loop.run(
                messages=messages,
                conversation_id=conversation_id,
                mode="chat",
                provider=provider,
                model=model,
                persona=persona,
                custom_styles=custom_styles,
                use_web_search=use_web_search,
                thinking_budget=thinking_budget or 0,
            ):
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

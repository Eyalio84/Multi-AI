"""OpenAI API service wrapper using the Responses API."""
import json
import base64
import logging
from typing import AsyncGenerator, Optional

from config import DEFAULT_OPENAI_MODEL

logger = logging.getLogger(__name__)

_client = None
_client_key = None


def _get_client():
    """Lazy singleton with key-change detection (same pattern as gemini_service)."""
    global _client, _client_key
    from config import OPENAI_API_KEY as key
    if not key:
        raise ValueError("OPENAI_API_KEY not configured")
    if _client is None or _client_key != key:
        from openai import OpenAI
        _client = OpenAI(api_key=key)
        _client_key = key
    return _client


def _convert_messages(messages: list[dict], system: Optional[str] = None) -> list[dict]:
    """Convert frontend message format to OpenAI Responses API input format."""
    result = []
    if system:
        result.append({"role": "developer", "content": system})

    for msg in messages:
        author = msg.get("author", "user")

        # Tool response messages
        if author == "tool":
            tr = msg.get("toolResponse", {})
            result.append({
                "role": "tool",
                "tool_call_id": tr.get("tool_use_id", ""),
                "content": json.dumps(tr.get("response", {}).get("content", "")),
            })
            continue

        role = "user" if author == "user" else "assistant"

        # Extract text from parts
        content = ""
        for part in msg.get("parts", []):
            if part.get("text"):
                content += part["text"]

        # Assistant message with tool call
        if author == "assistant" and msg.get("toolCall"):
            tc = msg["toolCall"]
            result.append({
                "role": role,
                "content": content or None,
                "tool_calls": [{
                    "id": tc.get("id", ""),
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": json.dumps(tc.get("args", {})),
                    },
                }],
            })
            continue

        if content:
            result.append({"role": role, "content": content})

    return result


def _is_reasoning_model(model: str) -> bool:
    """Check if this is an o-series reasoning model."""
    return model.startswith("o3") or model.startswith("o4")


async def stream_chat(
    messages: list[dict],
    model: str = None,
    system: Optional[str] = None,
    max_tokens: int = 8192,
    temperature: float = 1.0,
    reasoning_effort: Optional[str] = None,
) -> AsyncGenerator[dict, None]:
    """Stream a chat response using the OpenAI Responses API."""
    model = model or DEFAULT_OPENAI_MODEL
    try:
        client = _get_client()
    except ValueError as e:
        yield {"type": "error", "content": str(e)}
        yield {"type": "done"}
        return

    converted = _convert_messages(messages, system)

    kwargs = {
        "model": model,
        "input": converted,
        "stream": True,
    }

    if _is_reasoning_model(model):
        if reasoning_effort:
            kwargs["reasoning"] = {"effort": reasoning_effort}
    else:
        kwargs["temperature"] = temperature
        if max_tokens:
            kwargs["max_output_tokens"] = max_tokens

    try:
        stream = client.responses.create(**kwargs)
        for event in stream:
            if hasattr(event, "type"):
                if event.type == "response.output_text.delta":
                    yield {"type": "token", "content": event.delta}
                elif event.type == "response.completed":
                    break
    except Exception as e:
        logger.error(f"OpenAI stream_chat error: {e}")
        yield {"type": "error", "content": str(e)}

    yield {"type": "done"}


async def stream_with_tools(
    messages: list[dict],
    tools: list[dict],
    model: str = None,
    system: Optional[str] = None,
    max_tokens: int = 8192,
    temperature: float = 1.0,
) -> AsyncGenerator[dict, None]:
    """Stream with function calling support via the Responses API."""
    model = model or DEFAULT_OPENAI_MODEL
    try:
        client = _get_client()
    except ValueError as e:
        yield {"type": "error", "content": str(e)}
        yield {"type": "done"}
        return

    converted = _convert_messages(messages, system)

    # Convert tool declarations to OpenAI format
    openai_tools = []
    for t in tools:
        openai_tools.append({
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t.get("description", ""),
                "parameters": t.get("parameters", t.get("input_schema", {})),
            },
        })

    kwargs = {
        "model": model,
        "input": converted,
        "tools": openai_tools,
        "stream": True,
    }

    if not _is_reasoning_model(model):
        kwargs["temperature"] = temperature
        if max_tokens:
            kwargs["max_output_tokens"] = max_tokens

    try:
        stream = client.responses.create(**kwargs)
        for event in stream:
            if not hasattr(event, "type"):
                continue
            if event.type == "response.output_text.delta":
                yield {"type": "token", "content": event.delta}
            elif event.type == "response.function_call_arguments.delta":
                yield {"type": "tool_call_delta", "content": event.delta}
            elif event.type == "response.function_call_arguments.done":
                yield {
                    "type": "tool_call",
                    "name": event.name,
                    "args": json.loads(event.arguments) if event.arguments else {},
                    "id": getattr(event, "call_id", ""),
                }
            elif event.type == "response.completed":
                break
    except Exception as e:
        logger.error(f"OpenAI stream_with_tools error: {e}")
        yield {"type": "error", "content": str(e)}

    yield {"type": "done"}


async def generate_image(
    prompt: str,
    model: str = "gpt-image-1.5",
    size: str = "1024x1024",
    quality: str = "auto",
    n: int = 1,
) -> list[dict]:
    """Generate images using OpenAI image models."""
    client = _get_client()
    response = client.images.generate(
        model=model,
        prompt=prompt,
        size=size,
        quality=quality,
        n=n,
    )
    results = []
    for img in response.data:
        if img.b64_json:
            results.append({"imageUrl": f"data:image/png;base64,{img.b64_json}"})
        elif img.url:
            results.append({"imageUrl": img.url})
    return results


async def generate_tts(
    text: str,
    model: str = "gpt-4o-mini-tts",
    voice: str = "alloy",
    speed: float = 1.0,
) -> dict:
    """Text-to-speech using OpenAI TTS models."""
    client = _get_client()
    response = client.audio.speech.create(
        model=model,
        voice=voice,
        input=text,
        speed=speed,
        response_format="wav",
    )
    audio_data = response.content
    b64 = base64.b64encode(audio_data).decode()
    # Approximate duration: WAV 16-bit mono 24kHz, header = 44 bytes
    duration = max(0, (len(audio_data) - 44)) / (24000 * 2)
    return {"audioUrl": f"data:audio/wav;base64,{b64}", "duration": round(duration, 2)}

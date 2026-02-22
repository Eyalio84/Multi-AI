"""Gemini API service wrapper using google-genai SDK."""
import json
from typing import AsyncGenerator, Optional
from google import genai
from google.genai import types

from config import GEMINI_API_KEY, DEFAULT_GEMINI_MODEL

client = genai.Client(api_key=GEMINI_API_KEY)


def _convert_messages(messages: list[dict]) -> list[types.Content]:
    """Convert frontend message format to Gemini Content objects."""
    contents = []
    for msg in messages:
        role = "user" if msg.get("author") == "user" else "model"
        parts = []
        for part in msg.get("parts", []):
            if part.get("text"):
                parts.append(types.Part(text=part["text"]))
        if msg.get("toolResponse"):
            tr = msg["toolResponse"]
            parts.append(types.Part(
                function_response=types.FunctionResponse(
                    name=tr["name"],
                    response=tr["response"]["content"],
                )
            ))
        if parts:
            contents.append(types.Content(role=role, parts=parts))
    return contents


async def stream_chat(
    messages: list[dict],
    model: str = DEFAULT_GEMINI_MODEL,
    system_instruction: Optional[str] = None,
    use_web_search: bool = False,
    temperature: float = 1.0,
) -> AsyncGenerator[dict, None]:
    """Stream a chat response as SSE-compatible dicts."""
    contents = _convert_messages(messages)

    config = types.GenerateContentConfig(
        temperature=temperature,
    )
    if system_instruction:
        config.system_instruction = system_instruction

    tools = []
    if use_web_search:
        tools.append(types.Tool(google_search=types.GoogleSearch()))

    if tools:
        config.tools = tools

    response = client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=config,
    )

    for chunk in response:
        if chunk.text:
            yield {"type": "token", "content": chunk.text}
        if hasattr(chunk, "candidates") and chunk.candidates:
            candidate = chunk.candidates[0]
            if hasattr(candidate, "grounding_metadata") and candidate.grounding_metadata:
                gm = candidate.grounding_metadata
                if hasattr(gm, "grounding_chunks") and gm.grounding_chunks:
                    sources = []
                    for gc in gm.grounding_chunks:
                        if hasattr(gc, "web") and gc.web:
                            sources.append({"uri": gc.web.uri, "title": gc.web.title or gc.web.uri})
                    if sources:
                        yield {"type": "grounding", "sources": sources}

    yield {"type": "done"}


async def stream_with_tools(
    messages: list[dict],
    tool_declarations: list[dict],
    model: str = DEFAULT_GEMINI_MODEL,
    system_instruction: Optional[str] = None,
    use_web_search: bool = False,
    temperature: float = 1.0,
) -> AsyncGenerator[dict, None]:
    """Stream with function calling support."""
    contents = _convert_messages(messages)

    # Build function declarations
    functions = []
    for td in tool_declarations:
        functions.append(types.FunctionDeclaration(
            name=td["name"],
            description=td.get("description", ""),
            parameters=td.get("parameters"),
        ))

    tools = [types.Tool(function_declarations=functions)]
    if use_web_search:
        tools.append(types.Tool(google_search=types.GoogleSearch()))

    config = types.GenerateContentConfig(
        temperature=temperature,
        tools=tools,
    )
    if system_instruction:
        config.system_instruction = system_instruction

    response = client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=config,
    )

    for chunk in response:
        if hasattr(chunk, "candidates") and chunk.candidates:
            candidate = chunk.candidates[0]
            if hasattr(candidate, "content") and candidate.content:
                for part in candidate.content.parts:
                    if hasattr(part, "function_call") and part.function_call:
                        fc = part.function_call
                        yield {
                            "type": "tool_call",
                            "name": fc.name,
                            "args": dict(fc.args) if fc.args else {},
                        }
                    elif hasattr(part, "text") and part.text:
                        yield {"type": "token", "content": part.text}
            if hasattr(candidate, "grounding_metadata") and candidate.grounding_metadata:
                gm = candidate.grounding_metadata
                if hasattr(gm, "grounding_chunks") and gm.grounding_chunks:
                    sources = []
                    for gc in gm.grounding_chunks:
                        if hasattr(gc, "web") and gc.web:
                            sources.append({"uri": gc.web.uri, "title": gc.web.title or gc.web.uri})
                    if sources:
                        yield {"type": "grounding", "sources": sources}

    yield {"type": "done"}


def generate_content(
    prompt: str,
    model: str = DEFAULT_GEMINI_MODEL,
    system_instruction: Optional[str] = None,
    response_mime_type: Optional[str] = None,
) -> str:
    """Synchronous full response generation."""
    config = types.GenerateContentConfig()
    if system_instruction:
        config.system_instruction = system_instruction
    if response_mime_type:
        config.response_mime_type = response_mime_type

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=config,
    )
    return response.text


async def edit_image(prompt: str, image_bytes: bytes, mime_type: str, model: str = "gemini-2.5-flash-image") -> dict:
    """Edit an image using Gemini's image generation."""
    import base64
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part(text=prompt),
                types.Part(inline_data=types.Blob(mime_type=mime_type, data=image_bytes)),
            ],
        )
    ]
    config = types.GenerateContentConfig(
        response_modalities=["IMAGE", "TEXT"],
    )
    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=config,
    )

    result_parts = []
    for part in response.candidates[0].content.parts:
        if part.text:
            result_parts.append({"text": part.text})
        if hasattr(part, "inline_data") and part.inline_data:
            b64 = base64.b64encode(part.inline_data.data).decode()
            result_parts.append({"imageUrl": f"data:{part.inline_data.mime_type};base64,{b64}"})
    return result_parts


async def generate_video(prompt: str, image_bytes: Optional[bytes] = None, mime_type: Optional[str] = None) -> str:
    """Start video generation, returns operation name for polling."""
    request_body = {"prompt": prompt}
    if image_bytes and mime_type:
        import base64
        request_body["image"] = {
            "imageBytes": base64.b64encode(image_bytes).decode(),
            "mimeType": mime_type,
        }

    operation = client.models.generate_videos(
        model="veo-2.0-generate-001",
        prompt=prompt,
    )
    return operation.name


async def check_video_status(operation_name: str) -> dict:
    """Poll video generation status."""
    operation = client.operations.get(name=operation_name)
    if operation.done:
        if hasattr(operation, "error") and operation.error:
            return {"done": True, "error": str(operation.error)}
        video = operation.response.generated_videos[0]
        return {"done": True, "videoUrl": video.video.uri}
    return {"done": False}

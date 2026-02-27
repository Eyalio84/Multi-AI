"""Gemini API service wrapper using google-genai SDK."""
import json
from typing import AsyncGenerator, Optional
from google import genai
from google.genai import types

from config import GEMINI_API_KEY, DEFAULT_GEMINI_MODEL

_client = None
_client_key = None


def _get_client():
    global _client, _client_key
    from config import GEMINI_API_KEY as key
    if not key:
        raise ValueError("GEMINI_API_KEY not configured")
    if _client is None or _client_key != key:
        _client = genai.Client(api_key=key)
        _client_key = key
    return _client


# Keep backward-compatible `client` reference as a lazy proxy
class _ClientProxy:
    def __getattr__(self, name):
        return getattr(_get_client(), name)


client = _ClientProxy()


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


async def generate_image(
    prompt: str,
    model: str = "gemini-3-pro-image-preview",
    aspect_ratio: str = "1:1",
    num_images: int = 1,
) -> list[dict]:
    """Generate images from text using Nano Banana Pro / Gemini Flash Image / Imagen 4."""
    import base64

    # Imagen 4 uses a dedicated generate_images API
    if model.startswith("imagen"):
        response = client.models.generate_images(
            model=model,
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=num_images,
                aspect_ratio=aspect_ratio,
            ),
        )
        results = []
        for img in response.generated_images:
            b64 = base64.b64encode(img.image.image_bytes).decode()
            results.append({"imageUrl": f"data:image/png;base64,{b64}"})
        return results

    # Nano Banana / Gemini Flash Image use generate_content with IMAGE modality
    config = types.GenerateContentConfig(
        response_modalities=["IMAGE", "TEXT"],
    )
    response = client.models.generate_content(
        model=model,
        contents=f"{prompt}\n\nAspect ratio: {aspect_ratio}",
        config=config,
    )

    results = []
    for part in response.candidates[0].content.parts:
        if part.text:
            results.append({"text": part.text})
        if hasattr(part, "inline_data") and part.inline_data:
            b64 = base64.b64encode(part.inline_data.data).decode()
            results.append({"imageUrl": f"data:{part.inline_data.mime_type};base64,{b64}"})
    return results


async def generate_video(
    prompt: str,
    model: str = "veo-3.1-generate-preview",
    image_bytes: Optional[bytes] = None,
    mime_type: Optional[str] = None,
    aspect_ratio: str = "16:9",
    duration_seconds: int = 8,
) -> str:
    """Start video generation with Veo 3.1, returns operation name for polling."""
    import base64

    kwargs = {
        "model": model,
        "prompt": prompt,
    }

    # Pass reference image if provided
    if image_bytes and mime_type:
        from google.genai.types import Image, RawReferenceImage
        kwargs["image"] = RawReferenceImage(
            reference_image=Image(
                image_bytes=image_bytes,
                mime_type=mime_type,
            ),
            reference_type="REFERENCE_TYPE_STYLE",
        )

    config_kwargs = {}
    if aspect_ratio:
        config_kwargs["aspect_ratio"] = aspect_ratio
    if duration_seconds:
        config_kwargs["duration_seconds"] = duration_seconds
    if config_kwargs:
        kwargs["config"] = types.GenerateVideosConfig(**config_kwargs)

    operation = client.models.generate_videos(**kwargs)
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


async def generate_tts(
    text: str,
    model: str = "gemini-2.5-flash-preview-tts",
    voice: str = "Kore",
    speed: float = 1.0,
) -> dict:
    """Text-to-speech using Gemini TTS models."""
    import base64
    import struct

    config = types.GenerateContentConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice),
            ),
        ),
    )

    response = client.models.generate_content(
        model=model,
        contents=text,
        config=config,
    )

    audio_data = response.candidates[0].content.parts[0].inline_data.data
    mime = response.candidates[0].content.parts[0].inline_data.mime_type or "audio/wav"

    # Wrap raw PCM in WAV header if needed
    if "pcm" in mime.lower() or not audio_data[:4] == b"RIFF":
        sample_rate = 24000
        num_channels = 1
        bits_per_sample = 16
        data_size = len(audio_data)
        header = struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF", 36 + data_size, b"WAVE",
            b"fmt ", 16, 1, num_channels,
            sample_rate, sample_rate * num_channels * bits_per_sample // 8,
            num_channels * bits_per_sample // 8, bits_per_sample,
            b"data", data_size,
        )
        audio_data = header + audio_data
        mime = "audio/wav"

    b64 = base64.b64encode(audio_data).decode()
    duration = len(audio_data) / (24000 * 2)  # approximate for 16-bit mono 24kHz
    return {"audioUrl": f"data:{mime};base64,{b64}", "duration": round(duration, 2)}


async def generate_music(
    prompt: str,
    model: str = "lyria-realtime-exp",
    duration_seconds: int = 30,
) -> dict:
    """Generate music using Lyria."""
    import base64

    config = types.GenerateContentConfig(
        response_modalities=["AUDIO"],
    )

    response = client.models.generate_content(
        model=model,
        contents=f"{prompt}\n\nDuration: approximately {duration_seconds} seconds.",
        config=config,
    )

    audio_data = response.candidates[0].content.parts[0].inline_data.data
    mime = response.candidates[0].content.parts[0].inline_data.mime_type or "audio/wav"
    b64 = base64.b64encode(audio_data).decode()
    return {"audioUrl": f"data:{mime};base64,{b64}", "duration": duration_seconds}

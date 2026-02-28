"""VOX Media Functions — image, video, TTS, music generation via voice.

All new — no existing media functions in the registry.
"""
from services.vox_registry import vox_registry


@vox_registry.register(
    name="generate_image",
    category="media",
    description="Generate an image from a text prompt using Gemini or OpenAI",
    parameters={
        "type": "object",
        "properties": {
            "prompt": {"type": "string", "description": "Image description prompt"},
            "model": {"type": "string", "description": "Model to use (e.g. gemini-3-pro-image-preview, gpt-image-1)"},
        },
        "required": ["prompt"],
    },
    is_async=True,
)
async def generate_image(args: dict) -> dict:
    from services.gemini_service import generate_image as gem_gen
    result = await gem_gen(args["prompt"], model=args.get("model", "gemini-3-pro-image-preview"))
    return {"success": True, **result}


@vox_registry.register(
    name="generate_video",
    category="media",
    description="Generate a video from a text prompt using Veo",
    parameters={
        "type": "object",
        "properties": {
            "prompt": {"type": "string", "description": "Video description prompt"},
            "model": {"type": "string", "description": "Model (veo-3.1-generate-preview or veo-3.1-fast-generate-preview)"},
        },
        "required": ["prompt"],
    },
    is_async=True,
)
async def generate_video(args: dict) -> dict:
    from services.gemini_service import generate_video as gem_vid
    result = await gem_vid(args["prompt"], model=args.get("model", "veo-3.1-generate-preview"))
    return {"success": True, **result}


@vox_registry.register(
    name="text_to_speech",
    category="media",
    description="Convert text to speech audio using Gemini TTS",
    parameters={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Text to convert to speech"},
            "voice": {"type": "string", "description": "Voice name (e.g. Kore, Puck, Charon)"},
        },
        "required": ["text"],
    },
)
async def text_to_speech(args: dict) -> dict:
    from services.gemini_service import generate_tts
    result = await generate_tts(args["text"], voice=args.get("voice", "Kore"))
    return {"success": True, **result}


@vox_registry.register(
    name="generate_music",
    category="media",
    description="Generate music from a text description using Lyria",
    parameters={
        "type": "object",
        "properties": {
            "prompt": {"type": "string", "description": "Music description (genre, mood, tempo)"},
        },
        "required": ["prompt"],
    },
    is_async=True,
)
async def generate_music(args: dict) -> dict:
    from services.gemini_service import generate_music as gem_music
    result = await gem_music(args["prompt"])
    return {"success": True, **result}


@vox_registry.register(
    name="edit_image",
    category="media",
    description="Edit an existing image with a text prompt describing changes",
    parameters={
        "type": "object",
        "properties": {
            "prompt": {"type": "string", "description": "Edit instruction"},
            "image_url": {"type": "string", "description": "URL or base64 of the image to edit"},
        },
        "required": ["prompt", "image_url"],
    },
)
async def edit_image(args: dict) -> dict:
    return {
        "success": True,
        "message": "Image editing via voice requires the image to be loaded in the Studio. Navigate to the Media page to edit images.",
    }

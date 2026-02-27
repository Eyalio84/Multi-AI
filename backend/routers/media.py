"""Image editing/generation, video generation, TTS, and music endpoints."""
from fastapi import APIRouter, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

from services import gemini_service

router = APIRouter()


# --- Existing endpoints (backward-compatible) ---

@router.post("/image/edit")
async def edit_image(prompt: str = Form(...), file: UploadFile = File(...)):
    """Edit an image using Gemini's multimodal capabilities."""
    try:
        image_bytes = await file.read()
        result_parts = await gemini_service.edit_image(
            prompt=prompt,
            image_bytes=image_bytes,
            mime_type=file.content_type or "image/png",
        )
        return result_parts
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


@router.post("/video/generate")
async def generate_video_legacy(prompt: str = Form(...), file: UploadFile | None = File(None)):
    """Start video generation (legacy endpoint, kept for backward compat)."""
    try:
        image_bytes = None
        mime_type = None
        if file:
            image_bytes = await file.read()
            mime_type = file.content_type

        operation_name = await gemini_service.generate_video(
            prompt=prompt,
            image_bytes=image_bytes,
            mime_type=mime_type,
        )
        return {"operationName": operation_name}
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


@router.get("/video/status")
async def video_status(operationName: str = Query(...)):
    """Poll video generation status."""
    try:
        result = await gemini_service.check_video_status(operationName)
        return result
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


# --- New media generation endpoints ---

class ImageGenRequest(BaseModel):
    prompt: str
    model: str = "gemini-3-pro-image-preview"
    aspect_ratio: str = "1:1"
    num_images: int = 1


@router.post("/media/image/generate")
async def generate_image(request: ImageGenRequest):
    """Generate images from text using Nano Banana Pro / Imagen 4 / GPT Image."""
    try:
        if request.model.startswith("gpt-image"):
            from services import openai_service
            results = await openai_service.generate_image(
                prompt=request.prompt,
                model=request.model,
                n=request.num_images,
            )
        else:
            results = await gemini_service.generate_image(
                prompt=request.prompt,
                model=request.model,
                aspect_ratio=request.aspect_ratio,
                num_images=request.num_images,
            )
        return results
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


class VideoGenRequest(BaseModel):
    prompt: str
    model: str = "veo-3.1-generate-preview"
    aspect_ratio: str = "16:9"
    duration_seconds: int = 8


@router.post("/media/video/generate")
async def generate_video(request: VideoGenRequest):
    """Start video generation with Veo 3.1."""
    try:
        operation_name = await gemini_service.generate_video(
            prompt=request.prompt,
            model=request.model,
            aspect_ratio=request.aspect_ratio,
            duration_seconds=request.duration_seconds,
        )
        return {"operationName": operation_name}
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


class TTSRequest(BaseModel):
    text: str
    model: str = "gemini-2.5-flash-preview-tts"
    voice: str = "Kore"
    speed: float = 1.0


@router.post("/media/tts/generate")
async def generate_tts(request: TTSRequest):
    """Text-to-speech using Gemini or OpenAI TTS models."""
    try:
        if request.model.startswith("gpt-4o-mini-tts"):
            from services import openai_service
            result = await openai_service.generate_tts(
                text=request.text,
                model=request.model,
                voice=request.voice,
                speed=request.speed,
            )
        else:
            result = await gemini_service.generate_tts(
                text=request.text,
                model=request.model,
                voice=request.voice,
                speed=request.speed,
            )
        return result
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


class MusicGenRequest(BaseModel):
    prompt: str
    model: str = "lyria-realtime-exp"
    duration_seconds: int = 30


@router.post("/media/music/generate")
async def generate_music(request: MusicGenRequest):
    """Generate music using Lyria."""
    try:
        result = await gemini_service.generate_music(
            prompt=request.prompt,
            model=request.model,
            duration_seconds=request.duration_seconds,
        )
        return result
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})

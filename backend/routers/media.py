"""Image editing and video generation endpoints."""
from fastapi import APIRouter, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse

from services import gemini_service

router = APIRouter()


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
async def generate_video(prompt: str = Form(...), file: UploadFile | None = File(None)):
    """Start video generation with Veo 2.0."""
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

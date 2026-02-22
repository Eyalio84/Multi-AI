"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from routers import chat, coding, agents, playbooks, workflows, builder, media, interchange

app = FastAPI(
    title="Multi-AI Agentic Workspace",
    description="Professional agentic workflow orchestrator for Gemini + Claude",
    version="1.0.0",
)

# CORS for dev (Vite on :5173 → FastAPI on :8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(chat.router, prefix="/api")
app.include_router(coding.router, prefix="/api")
app.include_router(agents.router, prefix="/api")
app.include_router(playbooks.router, prefix="/api")
app.include_router(workflows.router, prefix="/api")
app.include_router(builder.router, prefix="/api")
app.include_router(media.router, prefix="/api")
app.include_router(interchange.router, prefix="/api")


@app.get("/api/health")
async def health():
    from config import MODE, GEMINI_API_KEY, ANTHROPIC_API_KEY
    return {
        "status": "ok",
        "mode": MODE,
        "gemini_configured": bool(GEMINI_API_KEY),
        "claude_configured": bool(ANTHROPIC_API_KEY),
    }


@app.get("/api/models")
async def list_models():
    from config import MODELS, MODE
    result = {"gemini": MODELS["gemini"]}
    if MODE == "standalone":
        result["claude"] = MODELS["claude"]
    return result

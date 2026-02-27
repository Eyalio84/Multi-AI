"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from routers import chat, coding, agents, playbooks, workflows, builder, media, interchange, kg, studio, memory, integrations, experts, tools, vox, games, agent

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
app.include_router(kg.router, prefix="/api")
app.include_router(studio.router, prefix="/api")
app.include_router(memory.router, prefix="/api")
app.include_router(integrations.router, prefix="/api")
app.include_router(experts.router, prefix="/api")
app.include_router(tools.router, prefix="/api")
app.include_router(vox.router)  # No prefix: WS at /ws/vox, REST at /api/vox/*
app.include_router(games.router, prefix="/api")
app.include_router(agent.router, prefix="/api")

# Serve Phaser runtime for game preview
_phaser_dir = Path(__file__).parent.parent / "docs" / "phaser"
if _phaser_dir.exists():
    app.mount("/docs/phaser", StaticFiles(directory=str(_phaser_dir)), name="phaser-static")


@app.get("/api/health")
async def health():
    from config import MODE, GEMINI_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY
    return {
        "status": "ok",
        "mode": MODE,
        "gemini_configured": bool(GEMINI_API_KEY),
        "claude_configured": bool(ANTHROPIC_API_KEY),
        "openai_configured": bool(OPENAI_API_KEY),
    }


@app.get("/api/models")
async def list_models():
    from config import MODELS, MODE, OPENAI_API_KEY
    result = {"gemini": MODELS["gemini"]}
    if MODE == "standalone":
        result["claude"] = MODELS["claude"]
    if OPENAI_API_KEY:
        result["openai"] = MODELS["openai"]
    return result

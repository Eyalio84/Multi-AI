"""Configuration for the Multi-AI Agentic Workspace."""
import os
from pathlib import Path

# --- Mode Detection ---
# "standalone" = both APIs, "claude-code" = Gemini only
MODE = os.getenv("WORKSPACE_MODE", "standalone")

# --- API Keys ---
# Keys are read from environment variables. No hardcoded defaults.
# Users can also set keys at runtime via POST /api/config/keys.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
ANTHROPIC_API_KEY = (
    os.getenv("ANTHROPIC_API_KEY", "")
    if MODE == "standalone"
    else None
)


def update_api_keys(gemini_key: str = None, anthropic_key: str = None):
    """Update API keys at runtime (called from /api/config/keys)."""
    global GEMINI_API_KEY, ANTHROPIC_API_KEY
    if gemini_key is not None:
        GEMINI_API_KEY = gemini_key
    if anthropic_key is not None:
        ANTHROPIC_API_KEY = anthropic_key

# --- Paths ---
PROJECT_ROOT = Path(__file__).parent.parent
AGENTS_DIR = PROJECT_ROOT / "agents"
PLAYBOOKS_DIR = PROJECT_ROOT / "docs" / "playbooks-v2"
KGS_DIR = Path(os.getenv("KGS_DIR", str(PROJECT_ROOT / "docs" / "KGS")))

# --- Model Catalog ---
MODELS = {
    "gemini": {
        "gemini-3-pro-preview": {
            "name": "Gemini 3 Pro",
            "context": 1000000,
            "cost_in": 2.0,
            "cost_out": 12.0,
            "use_case": "Flagship reasoning",
        },
        "gemini-2.5-flash": {
            "name": "Gemini 2.5 Flash",
            "context": 1000000,
            "cost_in": 0.15,
            "cost_out": 0.60,
            "use_case": "Fast coding/streaming",
        },
        "gemini-2.5-pro": {
            "name": "Gemini 2.5 Pro",
            "context": 1000000,
            "cost_in": 1.25,
            "cost_out": 5.0,
            "use_case": "Deep reasoning",
        },
        "gemini-2.5-flash-image": {
            "name": "Gemini 2.5 Flash Image",
            "context": 1000000,
            "cost_in": 0.15,
            "cost_out": 0.60,
            "use_case": "Image generation",
        },
        "gemini-embedding-001": {
            "name": "Gemini Embedding",
            "context": 8192,
            "cost_in": 0,
            "cost_out": 0,
            "use_case": "RAG/embeddings",
        },
        "veo-2.0-generate-001": {
            "name": "Veo 2.0",
            "context": 0,
            "cost_in": 0,
            "cost_out": 0,
            "use_case": "Video generation",
        },
    },
    "claude": {
        "claude-opus-4-6": {
            "name": "Claude Opus 4.6",
            "context": 200000,
            "cost_in": 5.0,
            "cost_out": 25.0,
            "use_case": "Most intelligent",
        },
        "claude-sonnet-4-6": {
            "name": "Claude Sonnet 4.6",
            "context": 200000,
            "cost_in": 3.0,
            "cost_out": 15.0,
            "use_case": "Fast + capable",
        },
        "claude-haiku-4-5-20251001": {
            "name": "Claude Haiku 4.5",
            "context": 200000,
            "cost_in": 1.0,
            "cost_out": 5.0,
            "use_case": "Cheapest, routing",
        },
    },
}

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_CLAUDE_MODEL = "claude-sonnet-4-6"

# --- Integration Credentials (all optional, configured via UI) ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID", "")
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
DISCORD_PUBLIC_KEY = os.getenv("DISCORD_PUBLIC_KEY", "")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET", "")
GMAIL_CLIENT_ID = os.getenv("GMAIL_CLIENT_ID", "")
GMAIL_CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET", "")
GMAIL_REFRESH_TOKEN = os.getenv("GMAIL_REFRESH_TOKEN", "")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")
SPOTIFY_REFRESH_TOKEN = os.getenv("SPOTIFY_REFRESH_TOKEN", "")
GOOGLE_CALENDAR_CREDENTIALS = os.getenv("GOOGLE_CALENDAR_CREDENTIALS", "")

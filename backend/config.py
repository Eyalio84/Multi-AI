"""Configuration for the Multi-AI Agentic Workspace."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from backend/ or project root — keys persist across restarts
load_dotenv(Path(__file__).parent / ".env")
load_dotenv(Path(__file__).parent.parent / ".env")

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
TOOLS_DIR = PROJECT_ROOT.parent / "tools"

# --- Model Catalog ---
MODELS = {
    "gemini": {
        # --- Text models ---
        "gemini-3-pro-preview": {
            "name": "Gemini 3 Pro",
            "category": "text",
            "context": 1000000,
            "cost_in": 2.0,
            "cost_out": 12.0,
            "use_case": "Flagship reasoning",
        },
        "gemini-3.1-pro-preview": {
            "name": "Gemini 3.1 Pro",
            "category": "text",
            "context": 1000000,
            "cost_in": 2.0,
            "cost_out": 12.0,
            "use_case": "Better thinking, token efficiency, agentic workflows",
        },
        "gemini-3.1-pro-preview-customtools": {
            "name": "Gemini 3.1 Pro Custom Tools",
            "category": "text",
            "context": 1000000,
            "cost_in": 2.0,
            "cost_out": 12.0,
            "use_case": "Prioritizes custom tools over bash",
        },
        "gemini-3-flash-preview": {
            "name": "Gemini 3 Flash",
            "category": "text",
            "context": 1000000,
            "cost_in": 0.10,
            "cost_out": 0.40,
            "use_case": "Fast next-gen flash",
        },
        "gemini-2.5-flash": {
            "name": "Gemini 2.5 Flash",
            "category": "text",
            "context": 1000000,
            "cost_in": 0.15,
            "cost_out": 0.60,
            "use_case": "Fast coding/streaming",
        },
        "gemini-2.5-pro": {
            "name": "Gemini 2.5 Pro",
            "category": "text",
            "context": 1000000,
            "cost_in": 1.25,
            "cost_out": 5.0,
            "use_case": "Deep reasoning",
        },
        "gemini-2.5-flash-lite": {
            "name": "Gemini 2.5 Flash Lite",
            "category": "text",
            "context": 1000000,
            "cost_in": 0.075,
            "cost_out": 0.30,
            "use_case": "Cheapest Gemini, bulk tasks",
        },
        # --- Image models ---
        "gemini-2.5-flash-image": {
            "name": "Gemini 2.5 Flash Image",
            "category": "image",
            "context": 1000000,
            "cost_in": 0.15,
            "cost_out": 0.60,
            "use_case": "Fast image generation/editing",
        },
        "gemini-3-pro-image-preview": {
            "name": "Nano Banana Pro",
            "category": "image",
            "context": 1000000,
            "cost_in": 2.0,
            "cost_out": 12.0,
            "use_case": "High-quality image generation",
        },
        "imagen-4.0-generate-preview-05-20": {
            "name": "Imagen 4",
            "category": "image",
            "context": 0,
            "cost_in": 0,
            "cost_out": 0.04,
            "use_case": "Dedicated image generation (non-chat)",
        },
        # --- Video models ---
        "veo-2.0-generate-001": {
            "name": "Veo 2.0",
            "category": "video",
            "context": 0,
            "cost_in": 0,
            "cost_out": 0,
            "use_case": "Video generation (legacy)",
        },
        "veo-3.1-generate-preview": {
            "name": "Veo 3.1",
            "category": "video",
            "context": 0,
            "cost_in": 0,
            "cost_out": 0,
            "use_case": "Video generation with audio",
        },
        "veo-3.1-fast-generate-preview": {
            "name": "Veo 3.1 Fast",
            "category": "video",
            "context": 0,
            "cost_in": 0,
            "cost_out": 0,
            "use_case": "Fast video generation",
        },
        # --- Audio/TTS models ---
        "gemini-2.5-flash-native-audio-preview": {
            "name": "Gemini Flash Audio",
            "category": "audio",
            "context": 1000000,
            "cost_in": 0.15,
            "cost_out": 0.60,
            "use_case": "Native audio understanding/generation",
        },
        "gemini-2.5-flash-preview-tts": {
            "name": "Gemini Flash TTS",
            "category": "audio",
            "context": 8192,
            "cost_in": 0.15,
            "cost_out": 0.60,
            "use_case": "Text-to-speech (24 voices)",
        },
        "gemini-2.5-pro-preview-tts": {
            "name": "Gemini Pro TTS",
            "category": "audio",
            "context": 8192,
            "cost_in": 1.25,
            "cost_out": 5.0,
            "use_case": "High-quality text-to-speech",
        },
        # --- Music models ---
        "lyria-realtime-exp": {
            "name": "Lyria",
            "category": "music",
            "context": 0,
            "cost_in": 0,
            "cost_out": 0,
            "use_case": "AI music generation",
        },
        # --- Embedding models ---
        "gemini-embedding-001": {
            "name": "Gemini Embedding",
            "category": "embedding",
            "context": 8192,
            "cost_in": 0,
            "cost_out": 0,
            "use_case": "RAG/embeddings",
        },
        # --- Agent/specialized models ---
        "gemini-2.5-computer-use-preview": {
            "name": "Gemini Computer Use",
            "category": "agent",
            "context": 1000000,
            "cost_in": 1.25,
            "cost_out": 5.0,
            "use_case": "Autonomous computer control",
        },
        "deep-research-pro-preview": {
            "name": "Deep Research",
            "category": "agent",
            "context": 1000000,
            "cost_in": 2.0,
            "cost_out": 12.0,
            "use_case": "Multi-step web research",
        },
    },
    "claude": {
        "claude-opus-4-6": {
            "name": "Claude Opus 4.6",
            "category": "text",
            "context": 200000,
            "cost_in": 5.0,
            "cost_out": 25.0,
            "use_case": "Most intelligent",
        },
        "claude-sonnet-4-6": {
            "name": "Claude Sonnet 4.6",
            "category": "text",
            "context": 200000,
            "cost_in": 3.0,
            "cost_out": 15.0,
            "use_case": "Fast + capable",
        },
        "claude-haiku-4-5-20251001": {
            "name": "Claude Haiku 4.5",
            "category": "text",
            "context": 200000,
            "cost_in": 1.0,
            "cost_out": 5.0,
            "use_case": "Cheapest, routing",
        },
    },
}

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_CLAUDE_MODEL = "claude-sonnet-4-6"

# --- VOX Voice Configuration ---
VOX_AUDIO_SAMPLE_RATE_IN = 16000   # PCM capture rate from mic
VOX_AUDIO_SAMPLE_RATE_OUT = 24000  # Playback rate for Gemini audio
VOX_DEFAULT_VOICE = "Puck"         # Gemini Live API voice
VOX_DEFAULT_MODEL = "gemini-2.5-flash-native-audio-preview-12-2025"  # Live API model (2.0 deprecated)

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

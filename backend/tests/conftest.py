"""Shared fixtures and configuration for the test suite.

This module provides:
- API key configuration for Gemini and Claude
- Reusable client instances
- Common test data (messages, tools, etc.)
- Base URL and app instance for endpoint tests
"""
import os
import sys
import unittest
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure the backend package is importable regardless of how tests are run.
# ---------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# ---------------------------------------------------------------------------
# API Keys — set via environment or fall back to the project defaults.
# ---------------------------------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Force standalone mode so both providers are available during tests.
os.environ["WORKSPACE_MODE"] = "standalone"
os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY
os.environ["ANTHROPIC_API_KEY"] = ANTHROPIC_API_KEY

# ---------------------------------------------------------------------------
# Lazy client helpers
# ---------------------------------------------------------------------------
_gemini_client = None
_anthropic_client = None


def get_gemini_client():
    """Return a cached google-genai Client."""
    global _gemini_client
    if _gemini_client is None:
        from google import genai
        _gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    return _gemini_client


def get_anthropic_client():
    """Return a cached Anthropic client."""
    global _anthropic_client
    if _anthropic_client is None:
        import anthropic
        _anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _anthropic_client


# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------
SIMPLE_USER_MESSAGE = [
    {
        "author": "user",
        "parts": [{"text": "Hello, respond with a single short greeting."}],
    }
]

GEMINI_TOOL_DECLARATIONS = [
    {
        "name": "get_weather",
        "description": "Get the current weather for a city.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "city": {
                    "type": "STRING",
                    "description": "City name, e.g. San Francisco",
                },
            },
            "required": ["city"],
        },
    }
]

CLAUDE_TOOL_DEFINITIONS = [
    {
        "name": "get_weather",
        "description": "Get the current weather for a city.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name, e.g. San Francisco",
                },
            },
            "required": ["city"],
        },
    }
]

# ---------------------------------------------------------------------------
# Timeout constant for live API calls (seconds)
# ---------------------------------------------------------------------------
API_TIMEOUT = 30

# ---------------------------------------------------------------------------
# FastAPI app instance (import after path and env setup)
# ---------------------------------------------------------------------------
def get_app():
    """Import and return the FastAPI app instance."""
    from main import app
    return app

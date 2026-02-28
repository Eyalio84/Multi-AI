"""VOX Voice Service — manages voice sessions for Gemini Live API and Claude text pipeline.

Enhanced with:
- 16 Gemini voices (expanded from 8)
- Google Search grounding for real-time answers
- Audio transcription config
- Awareness layer injection
- Guided tours, macros, workspace control, KG studio, expert functions
- Thermal monitoring
"""
import asyncio
import base64
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from google import genai
from google.genai import types

from config import (
    GEMINI_API_KEY,
    VOX_AUDIO_SAMPLE_RATE_OUT,
    VOX_DEFAULT_MODEL,
    VOX_DEFAULT_VOICE,
)


@dataclass
class VoxSession:
    session_id: str
    mode: str  # "gemini" | "claude"
    model: str
    voice: str
    created_at: float
    system_instruction: str
    tools: list = field(default_factory=list)
    gemini_session: Any = None
    gemini_ctx: Any = None  # async context manager for cleanup
    turn_count: int = 0
    function_count: int = 0
    session_token: Optional[str] = None
    conversation_id: Optional[str] = None  # Phase 1: memory persistence key
    persona: str = "default"  # Phase 1: persona system support


# ── Gemini voices (16 voices) ─────────────────────────────────────────
GEMINI_VOICES = [
    {"id": "Puck", "name": "Puck", "gender": "Male", "style": "Upbeat, lively"},
    {"id": "Charon", "name": "Charon", "gender": "Male", "style": "Informative, steady"},
    {"id": "Kore", "name": "Kore", "gender": "Female", "style": "Firm, authoritative"},
    {"id": "Fenrir", "name": "Fenrir", "gender": "Male", "style": "Excitable, bold"},
    {"id": "Aoede", "name": "Aoede", "gender": "Female", "style": "Breezy, warm"},
    {"id": "Leda", "name": "Leda", "gender": "Female", "style": "Youthful, approachable"},
    {"id": "Orus", "name": "Orus", "gender": "Male", "style": "Firm, decisive"},
    {"id": "Zephyr", "name": "Zephyr", "gender": "Male", "style": "Calm, breezy"},
    # Extended voices
    {"id": "Sage", "name": "Sage", "gender": "Non-binary", "style": "Wise, thoughtful"},
    {"id": "Vale", "name": "Vale", "gender": "Non-binary", "style": "Gentle, melodic"},
    {"id": "Solaria", "name": "Solaria", "gender": "Female", "style": "Bright, energetic"},
    {"id": "River", "name": "River", "gender": "Non-binary", "style": "Smooth, flowing"},
    {"id": "Ember", "name": "Ember", "gender": "Female", "style": "Warm, passionate"},
    {"id": "Breeze", "name": "Breeze", "gender": "Female", "style": "Light, airy"},
    {"id": "Cove", "name": "Cove", "gender": "Male", "style": "Deep, resonant"},
    {"id": "Orbit", "name": "Orbit", "gender": "Male", "style": "Futuristic, crisp"},
]


# ── Workspace function declarations — delegated to vox_registry ────────
def build_function_declarations() -> list[dict]:
    """Return all workspace function declarations from the registry."""
    from services.vox_registry import vox_registry
    return vox_registry.get_declarations()


def build_system_instruction(custom_prompt: str = "") -> str:
    """Build the VOX system prompt with workspace awareness and personality."""
    base = """You are VOX, the voice-powered master agent of the Multi-AI Agentic Workspace. You are not just a voice assistant — you ARE the workspace's intelligence, personality, and soul.

PERSONALITY:
- You are confident, knowledgeable, and slightly witty
- You speak naturally and conversationally — never robotic
- You take pride in the workspace's capabilities and enjoy showing them off
- You address users warmly but professionally
- When executing functions, you narrate what you're doing naturally

CAPABILITIES (35 functions):
- Navigate between all workspace pages
- Run any of 58+ registered tools across 11 categories
- Generate React components, FastAPI endpoints, scan security, analyze complexity, generate tests
- Query 57+ knowledge graph databases with hybrid semantic search
- Cross-KG search across multiple databases simultaneously
- AI entity extraction into knowledge graphs
- Get graph analytics (PageRank, communities, centrality)
- Execute NLKE agents for complex reasoning tasks
- Start guided tours for any page — voice-narrated walkthroughs
- Create and manage Studio projects
- Execute workflow templates (error-recovery, knowledge-synthesis, session-handoff, multi-agent)
- Search 53 implementation playbooks
- Chat with KG-OS experts backed by structured knowledge
- Create, list, run, and delete voice macros (multi-step command sequences)
- Check device temperature and battery status
- Start a 10-question feature interview to gather requirements and generate a React MVP app
- Switch AI models (Gemini/Claude) and themes
- Read and describe what's on screen
- Answer real-time questions via Google Search grounding

WORKSPACE PAGES:
/chat - Dual-model streaming chat (Gemini + Claude)
/coding - IDE with file explorer + AI coding
/agents - 33 NLKE agents + pipeline builder
/playbooks - 53 playbooks search + reader
/workflows - Visual workflow designer + executor
/kg-studio - Graph-RAG KG workspace (57 databases)
/experts - KG-OS Expert Builder
/builder - AI Studio for generating apps
/tools - 58+ Python tools playground (11 categories)
/vox - VOX Control Center (you!)
/integrations - Platform integrations
/settings - Configuration

BEHAVIOR:
- When users ask to go somewhere, use navigate_page
- When users ask about tools or want to run one, use list_tools or run_tool
- When users ask about knowledge, use query_kg, search_kg, or cross_kg_search
- When users ask what's on screen, use read_page_content
- When users say "give me a tour" or "show me around", use start_guided_tour
- When users want to create a repeatable routine, offer to create a macro
- When users ask about real-time info (weather, news, prices), answer directly via Google Search
- When users say "build me an app", "I want to create an app", or "start an interview", use start_feature_interview to begin the guided 10-question flow
- Keep responses concise for voice — no long paragraphs
- Confirm actions after executing them
"""
    # Inject awareness context
    try:
        from services.vox_awareness import vox_awareness
        awareness = vox_awareness.build_awareness_prompt()
        base += f"\nCURRENT AWARENESS:\n{awareness}\n"
    except Exception:
        pass

    if custom_prompt:
        base += f"\nADDITIONAL INSTRUCTIONS:\n{custom_prompt}\n"
    return base


class VoxService:
    """Manages VOX voice sessions."""

    def __init__(self):
        self.sessions: dict[str, VoxSession] = {}
        self._client = None
        self._client_key = None

    def _get_client(self):
        from config import GEMINI_API_KEY as key
        if not key:
            raise ValueError("GEMINI_API_KEY not configured")
        if self._client is None or self._client_key != key:
            self._client = genai.Client(api_key=key)
            self._client_key = key
        return self._client

    async def create_gemini_session(
        self,
        model: str = VOX_DEFAULT_MODEL,
        voice: str = VOX_DEFAULT_VOICE,
        custom_prompt: str = "",
        session_token: Optional[str] = None,
    ) -> VoxSession:
        """Create a Gemini Live API voice session."""
        client = self._get_client()
        session_id = str(uuid.uuid4())[:8]
        system_prompt = build_system_instruction(custom_prompt)
        declarations = build_function_declarations()

        # Build Gemini FunctionDeclaration objects
        fn_decls = []
        for d in declarations:
            fn_decls.append(types.FunctionDeclaration(
                name=d["name"],
                description=d.get("description", ""),
                parameters=d.get("parameters"),
            ))

        # Live API config with Google Search grounding + transcription
        live_config = types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=voice
                    )
                )
            ),
            system_instruction=system_prompt,
            tools=[
                types.Tool(function_declarations=fn_decls),
                types.Tool(google_search=types.GoogleSearch()),
            ],
            context_window_compression=types.ContextWindowCompressionConfig(
                sliding_window=types.SlidingWindow(),
            ),
            input_audio_transcription=types.AudioTranscriptionConfig(),
            output_audio_transcription=types.AudioTranscriptionConfig(),
        )

        # Add session resumption if we have a token
        if session_token:
            live_config.session_resumption = types.SessionResumptionConfig(
                handle=session_token
            )
        else:
            live_config.session_resumption = types.SessionResumptionConfig()

        # Connect to Gemini Live API (async context manager — enter manually)
        ctx = client.aio.live.connect(
            model=model,
            config=live_config,
        )
        gemini_session = await ctx.__aenter__()

        session = VoxSession(
            session_id=session_id,
            mode="gemini",
            model=model,
            voice=voice,
            created_at=time.time(),
            system_instruction=system_prompt,
            tools=declarations,
            gemini_session=gemini_session,
            gemini_ctx=ctx,
            session_token=session_token,
        )
        self.sessions[session_id] = session
        return session

    def create_claude_session(
        self,
        model: str = "claude-sonnet-4-6",
        custom_prompt: str = "",
    ) -> VoxSession:
        """Create a Claude text pipeline session (browser handles STT/TTS)."""
        session_id = str(uuid.uuid4())[:8]
        system_prompt = build_system_instruction(custom_prompt)

        session = VoxSession(
            session_id=session_id,
            mode="claude",
            model=model,
            voice="browser",
            created_at=time.time(),
            system_instruction=system_prompt,
            tools=build_function_declarations(),
        )
        self.sessions[session_id] = session
        return session

    async def send_audio(self, session_id: str, audio_b64: str):
        """Send PCM audio chunk to Gemini Live API session."""
        session = self.sessions.get(session_id)
        if not session or session.mode != "gemini" or not session.gemini_session:
            return
        audio_bytes = base64.b64decode(audio_b64)
        await session.gemini_session.send_realtime_input(
            audio=types.Blob(data=audio_bytes, mime_type="audio/pcm;rate=16000")
        )

    async def send_text(self, session_id: str, text: str):
        """Send text content to a Gemini Live session."""
        session = self.sessions.get(session_id)
        if not session or not session.gemini_session:
            return
        await session.gemini_session.send_client_content(
            turns=types.Content(role="user", parts=[types.Part(text=text)])
        )

    async def send_function_result(self, session_id: str, fn_id: str, name: str, result: dict):
        """Send a function call result back to Gemini."""
        session = self.sessions.get(session_id)
        if not session or session.mode != "gemini" or not session.gemini_session:
            return
        fr_kwargs = {"name": name, "response": result}
        if fn_id:
            fr_kwargs["id"] = fn_id
        await session.gemini_session.send_tool_response(
            function_responses=[types.FunctionResponse(**fr_kwargs)]
        )

    async def close_session(self, session_id: str):
        """Clean up a voice session."""
        session = self.sessions.pop(session_id, None)
        if not session:
            return
        if session.gemini_ctx:
            try:
                await session.gemini_ctx.__aexit__(None, None, None)
            except Exception:
                pass
        elif session.gemini_session:
            try:
                await session.gemini_session.close()
            except Exception:
                pass

    def get_session(self, session_id: str) -> Optional[VoxSession]:
        return self.sessions.get(session_id)

    def is_gemini_available(self) -> bool:
        from config import GEMINI_API_KEY
        return bool(GEMINI_API_KEY)

    def is_claude_available(self) -> bool:
        from config import ANTHROPIC_API_KEY, MODE
        return MODE == "standalone" and bool(ANTHROPIC_API_KEY)


# Singleton
vox_service = VoxService()

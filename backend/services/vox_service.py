"""VOX Voice Service — manages voice sessions for Gemini Live API and Claude text pipeline."""
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
    turn_count: int = 0
    function_count: int = 0
    session_token: Optional[str] = None


# ── Gemini voices ──────────────────────────────────────────────────────
GEMINI_VOICES = [
    {"id": "Puck", "name": "Puck", "gender": "Male", "style": "Upbeat, lively"},
    {"id": "Charon", "name": "Charon", "gender": "Male", "style": "Informative, steady"},
    {"id": "Kore", "name": "Kore", "gender": "Female", "style": "Firm, authoritative"},
    {"id": "Fenrir", "name": "Fenrir", "gender": "Male", "style": "Excitable, bold"},
    {"id": "Aoede", "name": "Aoede", "gender": "Female", "style": "Breezy, warm"},
    {"id": "Leda", "name": "Leda", "gender": "Female", "style": "Youthful, approachable"},
    {"id": "Orus", "name": "Orus", "gender": "Male", "style": "Firm, decisive"},
    {"id": "Zephyr", "name": "Zephyr", "gender": "Male", "style": "Calm, breezy"},
]


# ── Workspace function declarations for Gemini Live API ────────────────
def build_function_declarations() -> list[dict]:
    """Return workspace function declarations for Gemini Live API tools."""
    return [
        {
            "name": "navigate_page",
            "description": "Navigate the workspace to a specific page. Available pages: chat, coding, agents, playbooks, workflows, kg-studio, experts, builder, tools, vox, integrations, settings.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The page path, e.g. '/chat', '/tools', '/kg-studio'",
                    }
                },
                "required": ["path"],
            },
        },
        {
            "name": "get_current_page",
            "description": "Get the current page path the user is viewing.",
            "parameters": {"type": "object", "properties": {}},
        },
        {
            "name": "get_workspace_state",
            "description": "Get the current workspace state: active provider, model, page, theme, and project count.",
            "parameters": {"type": "object", "properties": {}},
        },
        {
            "name": "switch_model",
            "description": "Switch the active AI model. Providers: 'gemini' or 'claude'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "provider": {"type": "string", "description": "Either 'gemini' or 'claude'"},
                    "model": {"type": "string", "description": "Model ID, e.g. 'gemini-2.5-flash'"},
                },
                "required": ["provider", "model"],
            },
        },
        {
            "name": "switch_theme",
            "description": "Switch the workspace visual theme. Available: default, crt, scratch, solarized, sunset.",
            "parameters": {
                "type": "object",
                "properties": {
                    "theme_id": {"type": "string", "description": "Theme ID"},
                },
                "required": ["theme_id"],
            },
        },
        {
            "name": "run_tool",
            "description": "Execute one of the 58+ registered workspace tools by ID. Examples: cost_analyzer, task_classifier, code_review_generator, embedding_generator, react_component_generator, security_scanner, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tool_id": {"type": "string", "description": "Tool ID to execute"},
                    "params": {
                        "type": "object",
                        "description": "Tool parameters as key-value pairs",
                    },
                },
                "required": ["tool_id"],
            },
        },
        {
            "name": "list_tools",
            "description": "List all available workspace tools with their categories.",
            "parameters": {"type": "object", "properties": {}},
        },
        {
            "name": "query_kg",
            "description": "Search a knowledge graph database using hybrid semantic search.",
            "parameters": {
                "type": "object",
                "properties": {
                    "database_id": {"type": "string", "description": "KG database ID"},
                    "query": {"type": "string", "description": "Search query"},
                },
                "required": ["database_id", "query"],
            },
        },
        {
            "name": "list_kgs",
            "description": "List all available knowledge graph databases.",
            "parameters": {"type": "object", "properties": {}},
        },
        {
            "name": "run_agent",
            "description": "Execute an NLKE agent by name. Examples: cost_analyzer, kg_curator, adaptive_reasoning, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_name": {"type": "string", "description": "Agent name"},
                    "input": {"type": "string", "description": "Input text for the agent"},
                },
                "required": ["agent_name", "input"],
            },
        },
        {
            "name": "list_agents",
            "description": "List all available NLKE agents.",
            "parameters": {"type": "object", "properties": {}},
        },
        {
            "name": "read_page_content",
            "description": "Read the visible text content of the current workspace page.",
            "parameters": {"type": "object", "properties": {}},
        },
        # ── Direct developer tool shortcuts ───────────────────────────────
        {
            "name": "generate_react_component",
            "description": "Generate a React component with TypeScript, props interface, hooks, and state management. Specify the framework (react/vue/svelte) for cross-framework support.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Component name, e.g. 'UserCard'"},
                    "description": {"type": "string", "description": "What the component should do"},
                    "framework": {"type": "string", "description": "Target framework: react, vue, or svelte. Default: react"},
                    "features": {"type": "string", "description": "Comma-separated features: state, effects, context, memo, portal, ref"},
                },
                "required": ["name", "description"],
            },
        },
        {
            "name": "generate_fastapi_endpoint",
            "description": "Generate a FastAPI route with Pydantic models, validation, and error handling from a natural language description.",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {"type": "string", "description": "What the endpoint should do, e.g. 'Create a user with email and password'"},
                    "method": {"type": "string", "description": "HTTP method: GET, POST, PUT, DELETE. Default: POST"},
                    "path": {"type": "string", "description": "URL path, e.g. '/api/users'"},
                    "framework": {"type": "string", "description": "Target framework: fastapi, express, flask, django. Default: fastapi"},
                },
                "required": ["description"],
            },
        },
        {
            "name": "scan_code_security",
            "description": "Scan code for security vulnerabilities: SQL injection, XSS, hardcoded secrets, eval usage, path traversal, and more.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Source code to scan"},
                    "language": {"type": "string", "description": "Programming language: python, javascript, typescript, java, go. Default: python"},
                },
                "required": ["code"],
            },
        },
        {
            "name": "analyze_code_complexity",
            "description": "Analyze code complexity using cyclomatic and cognitive complexity metrics via AST parsing.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Source code to analyze"},
                    "language": {"type": "string", "description": "Programming language. Default: python"},
                },
                "required": ["code"],
            },
        },
        {
            "name": "generate_tests",
            "description": "Generate test cases from function signatures using AST analysis. Produces pytest-style tests with edge cases.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Source code containing functions to test"},
                    "framework": {"type": "string", "description": "Test framework: pytest, unittest, jest, mocha. Default: pytest"},
                    "style": {"type": "string", "description": "Test style: unit, integration, property. Default: unit"},
                },
                "required": ["code"],
            },
        },
    ]


def build_system_instruction(custom_prompt: str = "") -> str:
    """Build the VOX system prompt with workspace awareness and personality."""
    base = """You are VOX, the voice-powered master agent of the Multi-AI Agentic Workspace. You are not just a voice assistant — you ARE the workspace's intelligence, personality, and soul.

PERSONALITY:
- You are confident, knowledgeable, and slightly witty
- You speak naturally and conversationally — never robotic
- You take pride in the workspace's capabilities and enjoy showing them off
- You address users warmly but professionally
- When executing functions, you narrate what you're doing naturally

CAPABILITIES:
- You can navigate between all workspace pages (Chat, Coding, Agents, Playbooks, Workflows, KG Studio, Experts, Studio, Tools, VOX, Integrations, Settings)
- You can run any of the 58+ registered tools across 11 categories:
  * Code Quality (4): code review, refactoring, TDD, analysis
  * Cost Optimization (5): cost analysis, thinking budgets, Haiku delegation
  * Agent Intelligence (4): plan complexity, ROI, composition, workload
  * Knowledge Graph (5): embeddings, RAG, fusion, context, graph engineering
  * Generators (4): boilerplate, AST, scaffold, template
  * Reasoning (5): thinking budgets, ROI, reasoning engine, workflow
  * Dev Tools (10): docs, commit messages, changelogs, dead code, complexity, security scanner
  * Frontend (3): React/Vue/Svelte component generator, JSX→TSX converter, CSS→Tailwind
  * Backend (3): FastAPI/Express endpoint generator, Pydantic model generator, pytest generator
  * Full-Stack (3): API contract generator, Dockerfile generator, env template generator
  * Orchestration (1): agent orchestrator with DAG planning
- You can DIRECTLY generate React components, FastAPI endpoints, scan security, analyze complexity, and generate tests — just ask!
- You can query 57+ knowledge graph databases with hybrid semantic search
- You can execute NLKE agents for complex reasoning tasks
- You can switch AI models (Gemini/Claude) and themes on command
- You can read and describe what's currently on screen

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
- When users ask about knowledge, use query_kg or list_kgs
- When users ask what's on screen, use read_page_content
- Keep responses concise for voice — no long paragraphs
- Confirm actions after executing them
"""
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

        # Live API config
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
            tools=[types.Tool(function_declarations=fn_decls)],
            context_window_compression=types.ContextWindowCompressionConfig(
                sliding_window=types.SlidingWindow(),
            ),
        )

        # Add session resumption if we have a token
        if session_token:
            live_config.session_resumption = types.SessionResumptionConfig(
                handle=session_token
            )
        else:
            live_config.session_resumption = types.SessionResumptionConfig()

        # Connect to Gemini Live API
        gemini_session = await client.aio.live.connect(
            model=model,
            config=live_config,
        )

        session = VoxSession(
            session_id=session_id,
            mode="gemini",
            model=model,
            voice=voice,
            created_at=time.time(),
            system_instruction=system_prompt,
            tools=declarations,
            gemini_session=gemini_session,
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
        await session.gemini_session.send_tool_response(
            function_responses=[types.FunctionResponse(
                name=name,
                response=result,
            )]
        )

    async def close_session(self, session_id: str):
        """Clean up a voice session."""
        session = self.sessions.pop(session_id, None)
        if not session:
            return
        if session.gemini_session:
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

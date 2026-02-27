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


# ── Workspace function declarations for Gemini Live API ────────────────
def build_function_declarations() -> list[dict]:
    """Return all workspace function declarations (~34 functions)."""
    return [
        # ── Browser-side functions (6) ─────────────────────────────────
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
            "name": "read_page_content",
            "description": "Read the visible text content of the current workspace page.",
            "parameters": {"type": "object", "properties": {}},
        },
        # ── Core workspace tools (6) ───────────────────────────────────
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
        # ── Direct developer tool shortcuts (5) ───────────────────────
        {
            "name": "generate_react_component",
            "description": "Generate a React component with TypeScript, props interface, hooks, and state management.",
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
            "description": "Generate a FastAPI route with Pydantic models, validation, and error handling.",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {"type": "string", "description": "What the endpoint should do"},
                    "method": {"type": "string", "description": "HTTP method: GET, POST, PUT, DELETE. Default: POST"},
                    "path": {"type": "string", "description": "URL path, e.g. '/api/users'"},
                    "framework": {"type": "string", "description": "Target framework: fastapi, express, flask, django. Default: fastapi"},
                },
                "required": ["description"],
            },
        },
        {
            "name": "scan_code_security",
            "description": "Scan code for security vulnerabilities: SQL injection, XSS, hardcoded secrets, eval usage, path traversal.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Source code to scan"},
                    "language": {"type": "string", "description": "Programming language. Default: python"},
                },
                "required": ["code"],
            },
        },
        {
            "name": "analyze_code_complexity",
            "description": "Analyze code complexity using cyclomatic and cognitive complexity metrics.",
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
            "description": "Generate test cases from function signatures using AST analysis.",
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
        # ── Guided Tours (2) ──────────────────────────────────────────
        {
            "name": "start_guided_tour",
            "description": "Start an interactive voice-narrated guided tour of a workspace page. VOX highlights UI elements and explains each feature.",
            "parameters": {
                "type": "object",
                "properties": {
                    "page": {"type": "string", "description": "Page to tour. Options: chat, coding, agents, playbooks, workflows, kg-studio, experts, builder, tools, vox, settings. If empty, tours the current page."},
                },
            },
        },
        {
            "name": "get_available_tours",
            "description": "List all available guided tours with page names and step counts.",
            "parameters": {"type": "object", "properties": {}},
        },
        # ── Workspace Control — Jarvis Mode (5) ───────────────────────
        {
            "name": "create_project",
            "description": "Create a new AI Studio project with a name and description.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Project name"},
                    "description": {"type": "string", "description": "What the project does"},
                },
                "required": ["name"],
            },
        },
        {
            "name": "list_projects",
            "description": "List all Studio projects with their status and file counts.",
            "parameters": {"type": "object", "properties": {}},
        },
        {
            "name": "run_workflow",
            "description": "Execute a workflow template by name. Available: error-recovery, knowledge-synthesis, session-handoff, multi-agent-orchestration.",
            "parameters": {
                "type": "object",
                "properties": {
                    "workflow_name": {"type": "string", "description": "Workflow template name"},
                    "input": {"type": "string", "description": "Input text for the workflow"},
                },
                "required": ["workflow_name"],
            },
        },
        {
            "name": "search_playbooks",
            "description": "Search through 53 implementation playbooks by keyword.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                },
                "required": ["query"],
            },
        },
        {
            "name": "search_kg",
            "description": "Enhanced KG search with optional filters. Returns top results with scores.",
            "parameters": {
                "type": "object",
                "properties": {
                    "database_id": {"type": "string", "description": "KG database ID"},
                    "query": {"type": "string", "description": "Search query"},
                    "node_type": {"type": "string", "description": "Optional: filter by node type (e.g. 'tool', 'pattern', 'concept')"},
                    "limit": {"type": "integer", "description": "Max results. Default: 5"},
                },
                "required": ["database_id", "query"],
            },
        },
        # ── KG Studio Control (3) ─────────────────────────────────────
        {
            "name": "get_kg_analytics",
            "description": "Get graph analytics for a KG database: node/edge counts, top nodes by centrality, and community count.",
            "parameters": {
                "type": "object",
                "properties": {
                    "database_id": {"type": "string", "description": "KG database ID"},
                },
                "required": ["database_id"],
            },
        },
        {
            "name": "cross_kg_search",
            "description": "Search across multiple knowledge graph databases simultaneously.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "database_ids": {"type": "string", "description": "Comma-separated database IDs, or 'all' for all databases"},
                    "limit": {"type": "integer", "description": "Max results per database. Default: 3"},
                },
                "required": ["query"],
            },
        },
        {
            "name": "ingest_to_kg",
            "description": "Extract entities and relationships from text and add them to a knowledge graph using AI.",
            "parameters": {
                "type": "object",
                "properties": {
                    "database_id": {"type": "string", "description": "Target KG database ID"},
                    "text": {"type": "string", "description": "Text to extract knowledge from"},
                },
                "required": ["database_id", "text"],
            },
        },
        # ── Expert Control (2) ─────────────────────────────────────────
        {
            "name": "chat_with_expert",
            "description": "Send a message to a KG-OS expert and get a response with source citations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expert_id": {"type": "string", "description": "Expert ID"},
                    "message": {"type": "string", "description": "Message to send to the expert"},
                },
                "required": ["expert_id", "message"],
            },
        },
        {
            "name": "list_experts",
            "description": "List all available KG-OS experts with their specializations.",
            "parameters": {"type": "object", "properties": {}},
        },
        # ── Voice Macros (4) ───────────────────────────────────────────
        {
            "name": "create_macro",
            "description": "Create a voice macro — a multi-step command sequence triggered by a phrase. Steps can chain functions together with output piping.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Macro name"},
                    "trigger_phrase": {"type": "string", "description": "Voice trigger phrase, e.g. 'morning routine'"},
                    "steps": {"type": "string", "description": "JSON array of steps: [{\"function\":\"fn_name\",\"args\":{},\"pipe_from\":null}]"},
                    "error_policy": {"type": "string", "description": "What to do on error: abort, skip, or retry. Default: abort"},
                },
                "required": ["name", "trigger_phrase", "steps"],
            },
        },
        {
            "name": "list_macros",
            "description": "List all saved voice macros with their trigger phrases and step counts.",
            "parameters": {"type": "object", "properties": {}},
        },
        {
            "name": "run_macro",
            "description": "Execute a voice macro by name or trigger phrase.",
            "parameters": {
                "type": "object",
                "properties": {
                    "macro_id": {"type": "string", "description": "Macro ID or trigger phrase"},
                },
                "required": ["macro_id"],
            },
        },
        {
            "name": "delete_macro",
            "description": "Delete a saved voice macro.",
            "parameters": {
                "type": "object",
                "properties": {
                    "macro_id": {"type": "string", "description": "Macro ID to delete"},
                },
                "required": ["macro_id"],
            },
        },
        # ── Thermal Monitoring (1) ─────────────────────────────────────
        {
            "name": "check_thermal",
            "description": "Check the device temperature and battery status. Warns if the device is getting too hot.",
            "parameters": {"type": "object", "properties": {}},
        },
        # ── Feature Interview (1) ─────────────────────────────────────
        {
            "name": "start_feature_interview",
            "description": "Start a 10-question guided interview to gather requirements for building a React MVP app. VOX walks the user through domain selection, purpose, target users, features, data, auth, style, integrations, key flow, and constraints. After completing the interview, the answers are used to generate a working React app via the Studio builder.",
            "parameters": {
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Optional pre-selected domain: landing, knowledge, saas, game, dashboard, ecommerce, social, portfolio. If empty, VOX asks the user to choose.",
                    },
                },
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

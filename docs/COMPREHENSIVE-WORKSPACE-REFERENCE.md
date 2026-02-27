# Comprehensive Workspace Reference

**Purpose:** Complete technical handoff document for another Claude instance building a standalone multi-AI React builder application. This document contains exhaustive implementation details, verbatim code snippets, architecture diagrams, and protocol specifications extracted directly from the Multi-AI Agentic Workspace codebase.

**Source codebase:** `/storage/self/primary/Download/gemini-3-pro/multi-ai-agentic-workspace`

**Document version:** 2026-02-26

---

## Table of Contents

- Part 0: Executive Summary
- Part 1: VOX Voice Agent Deep Dive
- Part 2: AI Studio / React Builder Deep Dive
- Part 3: (Future) KG Studio
- Part 4: (Future) Expert Builder / KG-OS
- Part 5: (Future) Tools Playground
- Part 6: (Future) Chat / Coding Pages
- Part 7: (Future) Theme System
- Part 8: (Future) Agents, Playbooks, Workflows

---

# Part 0: Executive Summary

## What This Workspace Is

The Multi-AI Agentic Workspace is a professional agentic workflow orchestrator that combines Gemini and Claude intelligence into a single full-stack application. It is built with:

- **Backend:** Python FastAPI, running on `uvicorn`
- **Frontend:** React 19 + TypeScript + Vite
- **Database:** SQLite (multiple databases for different subsystems)
- **AI SDKs:** `google-genai` (Gemini), `anthropic` (Claude)
- **Streaming:** Server-Sent Events (SSE) for chat/studio, WebSocket for VOX voice

The workspace provides 13 route pages, 58+ Python tools, 33 NLKE agents, 53 playbooks, 57 Knowledge Graph databases, a full AI Studio for generating React applications, a KG-OS Expert Builder, and a VOX voice agent with 34 function declarations.

## High-Level Architecture

```
multi-ai-agentic-workspace/
|
+-- backend/                    # FastAPI (Python 3.11+)
|   +-- main.py                 # App entry point, CORS, router mounting
|   +-- config.py               # API keys, model catalog, paths, VOX config
|   +-- routers/                # 15 API routers (one per feature domain)
|   |   +-- chat.py             # SSE streaming chat
|   |   +-- coding.py           # Coding with tool use
|   |   +-- agents.py           # NLKE agent CRUD + execution
|   |   +-- playbooks.py        # Playbook search + retrieval
|   |   +-- workflows.py        # Workflow templates + execution
|   |   +-- builder.py          # Legacy web app plan + generate
|   |   +-- studio.py           # Studio: SSE streaming + project CRUD (18 endpoints)
|   |   +-- experts.py          # Expert Builder + KG-OS (15 endpoints)
|   |   +-- tools.py            # Tools playground (list, get, run, stream)
|   |   +-- vox.py              # VOX voice agent (WebSocket + REST, 34 functions)
|   |   +-- media.py            # Image edit + video generation
|   |   +-- interchange.py      # JSON import/export, mode toggle
|   |   +-- kg.py               # KG Studio (33 endpoints)
|   |   +-- games.py            # Game generation
|   |   +-- config_router.py    # Runtime API key updates
|   +-- services/               # Business logic (22 services)
|   +-- data/                   # Static data files (tours, etc.)
|   +-- tests/                  # API integration tests
|
+-- frontend/                   # React 19 + TypeScript + Vite
|   +-- src/
|   |   +-- App.tsx             # React Router + layout shell
|   |   +-- context/            # Global state (AppContext, StudioContext, VoxContext)
|   |   +-- pages/              # 13 route pages
|   |   +-- components/         # Reusable UI components
|   |   +-- hooks/              # useChat, useTheme, useToast, useVox
|   |   +-- services/           # API + localStorage + studioApiService
|   |   +-- themes/             # 5 theme definitions (CSS variable maps)
|   |   +-- types/              # TypeScript interfaces
|   +-- package.json
|   +-- vite.config.ts
```

## How to Run

```bash
# Backend (from project root)
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (from project root)
cd frontend
npm install
npm run dev
# Frontend runs on port 5173 by default, proxies /api to :8000
```

**Environment variables** (set in `.env` or export):
- `GEMINI_API_KEY` -- Required for Gemini features, VOX voice, and KG embeddings
- `ANTHROPIC_API_KEY` -- Required for Claude features (standalone mode only)
- `WORKSPACE_MODE` -- `"standalone"` (default, both APIs) or `"claude-code"` (Gemini only)

## Model Catalog

All models are defined in `backend/config.py` in the `MODELS` dictionary.

| Provider | Model ID | Display Name | Context Window | Cost In ($/1M tokens) | Cost Out ($/1M tokens) | Use Case |
|----------|----------|-------------|----------------|----------------------|------------------------|----------|
| Gemini | `gemini-3-pro-preview` | Gemini 3 Pro | 1,000,000 | $2.00 | $12.00 | Flagship reasoning |
| Gemini | `gemini-2.5-flash` | Gemini 2.5 Flash | 1,000,000 | $0.15 | $0.60 | Fast coding/streaming |
| Gemini | `gemini-2.5-pro` | Gemini 2.5 Pro | 1,000,000 | $1.25 | $5.00 | Deep reasoning |
| Gemini | `gemini-2.5-flash-image` | Gemini 2.5 Flash Image | 1,000,000 | $0.15 | $0.60 | Image generation |
| Gemini | `gemini-embedding-001` | Gemini Embedding | 8,192 | $0.00 | $0.00 | RAG/embeddings |
| Gemini | `veo-2.0-generate-001` | Veo 2.0 | N/A | N/A | N/A | Video generation |
| Claude | `claude-opus-4-6` | Claude Opus 4.6 | 200,000 | $5.00 | $25.00 | Most intelligent |
| Claude | `claude-sonnet-4-6` | Claude Sonnet 4.6 | 200,000 | $3.00 | $15.00 | Fast + capable |
| Claude | `claude-haiku-4-5-20251001` | Claude Haiku 4.5 | 200,000 | $1.00 | $5.00 | Cheapest, routing |

Default models:
- `DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"`
- `DEFAULT_CLAUDE_MODEL = "claude-sonnet-4-6"`

## Dual-Mode Architecture

The workspace supports two operational modes controlled by the `WORKSPACE_MODE` environment variable:

**Standalone Mode** (default, `WORKSPACE_MODE="standalone"`):
- Both `GEMINI_API_KEY` and `ANTHROPIC_API_KEY` are active
- Backend calls both Gemini and Claude APIs directly
- Full dual-model UI with provider selector on every chat/coding page
- VOX supports both Gemini voice and Claude text pipeline modes

**Claude Code Mode** (`WORKSPACE_MODE="claude-code"`):
- Only `GEMINI_API_KEY` is active; `ANTHROPIC_API_KEY` is set to `None`
- Claude tasks return structured JSON intended for Claude Code CLI sessions
- 33 NLKE agents invocable via CLI by Claude Code
- Toggle via Settings page UI or `POST /api/mode`

The mode is checked at import time in `config.py`:

```python
MODE = os.getenv("WORKSPACE_MODE", "standalone")
ANTHROPIC_API_KEY = (
    os.getenv("ANTHROPIC_API_KEY", "")
    if MODE == "standalone"
    else None
)
```

## Key Pages (13 Routes)

| Route | Page Component | Purpose |
|-------|---------------|---------|
| `/chat` | ChatPage | Dual-model streaming chat (Gemini + Claude) |
| `/coding` | CodingPage | IDE with file explorer + AI coding |
| `/agents` | AgentsPage | 33 NLKE agents + pipeline builder |
| `/playbooks` | PlaybooksPage | 53 playbooks search + reader |
| `/workflows` | WorkflowsPage | Visual workflow designer + executor |
| `/kg-studio` | KGStudioPage | Graph-RAG KG workspace (57 DBs, React Flow + d3-force) |
| `/builder` | StudioPage | AI Studio: chat -> generate -> preview, 3 modes, version history |
| `/experts` | ExpertsPage | KG-OS Expert Builder: AI experts backed by KGs |
| `/tools` | ToolsPage | 58+ Python tools playground (11 categories) |
| `/vox` | VoxPage | VOX voice control center: 16 voices, 34 functions, macros |
| `/games` | GamesPage | AI-generated game builder |
| `/integrations` | IntegrationsPage | Platform integrations management |
| `/settings` | SettingsPage | Mode toggle, themes, export/import |

---

# Part 1: VOX Voice Agent Deep Dive

VOX is the voice-powered master agent of the workspace. It provides bidirectional voice communication through two distinct pipelines: native audio streaming via the Gemini Live API, and a browser-based STT/TTS pipeline via Claude's text API. VOX can execute 34 workspace functions by voice, including page navigation, tool execution, knowledge graph queries, guided tours, voice macros, and thermal monitoring.

## 1.1 Architecture Overview

```
+================================================================+
|                     VOX ARCHITECTURE                            |
+================================================================+
|                                                                 |
|  FRONTEND (React)                BACKEND (FastAPI)              |
|  +-----------------------+       +---------------------------+  |
|  | useVox.ts hook        |<----->| /ws/vox WebSocket         |  |
|  |  - Audio capture      | WS    | (routers/vox.py)          |  |
|  |  - Audio playback     |       |  - Message routing        |  |
|  |  - Browser STT/TTS    |       |  - Function execution     |  |
|  |  - Browser functions   |       |  - Session management     |  |
|  |  - Auto-reconnect     |       |                           |  |
|  +-----------------------+       +---------------------------+  |
|  | VoxOverlay.tsx        |       |                           |  |
|  |  - Floating pill UI   |       | +------ Services ------+  |  |
|  +-----------------------+       | | vox_service.py       |  |  |
|  | VoxTourOverlay.tsx    |       | |  - VoxSession        |  |  |
|  |  - Tour spotlight     |       | |  - Gemini Live API   |  |  |
|  +-----------------------+       | |  - Claude sessions    |  |  |
|  | VoxPage.tsx           |       | +---------------------+  |  |
|  |  - Control center     |       | | vox_awareness.py     |  |  |
|  +-----------------------+       | |  - SQLite tracking   |  |  |
|                                  | +---------------------+  |  |
|  REST endpoints:                 | | vox_macros.py        |  |  |
|  GET  /api/vox/status            | |  - Macro CRUD        |  |  |
|  GET  /api/vox/voices            | |  - Pipe chaining     |  |  |
|  GET  /api/vox/functions         | +---------------------+  |  |
|  POST /api/vox/function/{name}   | | vox_thermal.py       |  |  |
|  POST /api/vox/awareness         | |  - Termux battery    |  |  |
|  GET  /api/vox/awareness         | +---------------------+  |  |
|  GET  /api/vox/tours             |                           |  |
|  GET  /api/vox/tours/{page}      | External:                |  |
|  GET  /api/vox/macros            |  - Gemini Live API       |  |
|  POST /api/vox/macros            |  - Anthropic Messages    |  |
|  DELETE /api/vox/macros/{id}     |  - termux-battery-status |  |
|  POST /api/vox/macros/{id}/run   |                           |  |
|  GET  /api/vox/thermal           |                           |  |
|  WS   /ws/vox                    |                           |  |
+================================================================+
```

## 1.2 Gemini Voice Flow

```
+------------------------------------------------------------------+
| GEMINI VOICE FLOW                                                 |
+------------------------------------------------------------------+
|                                                                    |
|  User speaks    Frontend              Backend           Gemini     |
|  into mic       (useVox.ts)           (vox.py)          Live API   |
|     |               |                    |                 |       |
|     +---> getUserMedia()                 |                 |       |
|     |    AudioContext(16kHz)             |                 |       |
|     |    ScriptProcessor                 |                 |       |
|     |               |                    |                 |       |
|     |    Float32 -> Int16 -> base64      |                 |       |
|     |               |                    |                 |       |
|     |    WS: {type:"audio",              |                 |       |
|     |         data: "<b64>"}             |                 |       |
|     |               +-------WS---------->|                 |       |
|     |               |                    |                 |       |
|     |               |     send_realtime_input(             |       |
|     |               |       audio=Blob(pcm,16kHz))         |       |
|     |               |                    +---------------->|       |
|     |               |                    |                 |       |
|     |               |                    |    response     |       |
|     |               |                    |<----------------+       |
|     |               |                    |                 |       |
|     |               |  BRANCH: response.data (audio)       |       |
|     |               |  WS: {type:"audio",                  |       |
|     |               |       data: "<b64 24kHz>"}           |       |
|     |               |<---WS--------------+                 |       |
|     |               |                    |                 |       |
|     |    base64 -> Int16 -> Float32      |                 |       |
|     |    AudioBuffer(24kHz)              |                 |       |
|     |    BufferSource.start(scheduled)   |                 |       |
|     |               |                    |                 |       |
|     |               |  BRANCH: response.tool_call          |       |
|     |               |  Function dispatched:                |       |
|     |               |    browser fn -> WS to client        |       |
|     |               |    server fn -> _execute_server_fn   |       |
|     |               |    async fn  -> background task      |       |
|     |               |  Result sent back via                |       |
|     |               |    send_tool_response()              |       |
|     |               |                    +---------------->|       |
|     |               |                    |                 |       |
|     |               |  BRANCH: response.server_content     |       |
|     |               |    text parts -> WS {type:"text"}    |       |
|     |               |    turn_complete -> WS               |       |
|     |               |                    |                 |       |
|     |               |  BRANCH: session_resumption_update   |       |
|     |               |    Store new session token           |       |
|     |               |                    |                 |       |
|     |               |  BRANCH: go_away                     |       |
|     |               |    WS: {type:"go_away",              |       |
|     |               |          session_token: "..."}       |       |
|     |               |<---WS--------------+                 |       |
|     |               |                    |                 |       |
|     |    Auto-reconnect with token       |                 |       |
|     |               |                    |                 |       |
+------------------------------------------------------------------+
```

## 1.3 Claude Voice Flow

```
+------------------------------------------------------------------+
| CLAUDE VOICE FLOW                                                 |
+------------------------------------------------------------------+
|                                                                    |
|  User speaks    Frontend              Backend           Claude     |
|  into mic       (useVox.ts)           (vox.py)          API       |
|     |               |                    |                 |       |
|     +---> SpeechRecognition              |                 |       |
|     |    (webkitSpeechRecognition)       |                 |       |
|     |    continuous=true                 |                 |       |
|     |    lang='en-US'                    |                 |       |
|     |               |                    |                 |       |
|     |    onresult -> final transcript    |                 |       |
|     |               |                    |                 |       |
|     |    WS: {type:"text",              |                 |       |
|     |         text: "user words"}        |                 |       |
|     |               +-------WS---------->|                 |       |
|     |               |                    |                 |       |
|     |               |     _claude_text_pipeline()          |       |
|     |               |     messages.create(                 |       |
|     |               |       model, system,                 |       |
|     |               |       messages, tools)               |       |
|     |               |                    +---------------->|       |
|     |               |                    |                 |       |
|     |               |                    |    response     |       |
|     |               |                    |<----------------+       |
|     |               |                    |                 |       |
|     |               |  Loop up to 5 rounds:                |       |
|     |               |    text blocks -> accumulate         |       |
|     |               |    tool_use blocks:                  |       |
|     |               |      browser fn -> WS to client      |       |
|     |               |      server fn -> execute + result   |       |
|     |               |    Feed tool_results back to Claude  |       |
|     |               |                    +---------------->|       |
|     |               |                    |<----------------+       |
|     |               |  Until: no more tool_use blocks      |       |
|     |               |                    |                 |       |
|     |               |  WS: {type:"text",                   |       |
|     |               |       text: "full response"}         |       |
|     |               |<---WS--------------+                 |       |
|     |               |                    |                 |       |
|     |    SpeechSynthesisUtterance        |                 |       |
|     |    rate=1.1, pitch=1.0             |                 |       |
|     |    speechSynthesis.speak()         |                 |       |
|     |               |                    |                 |       |
|     |               |  WS: {type:"turn_complete",          |       |
|     |               |       turn: N}                       |       |
|     |               |<---WS--------------+                 |       |
|     |               |                    |                 |       |
+------------------------------------------------------------------+
```

## 1.4 WebSocket Message Lifecycle

```
+------------------------------------------------------------------+
| WEBSOCKET MESSAGE PROTOCOL (/ws/vox)                              |
+------------------------------------------------------------------+
|                                                                    |
| CLIENT -> SERVER messages:                                         |
|                                                                    |
|   {type: "start",                                                  |
|    mode: "gemini"|"claude",                                        |
|    model: "model-id",                                              |
|    voice: "Puck",                                                  |
|    systemPrompt: "...",                                            |
|    session_token: "..." (optional, for reconnect)}                 |
|                                                                    |
|   {type: "audio",                                                  |
|    data: "<base64 PCM 16kHz>"}                                     |
|                                                                    |
|   {type: "text",                                                   |
|    text: "user message"}                                           |
|                                                                    |
|   {type: "browser_function_result",                                |
|    name: "navigate_page",                                          |
|    result: {success: true, navigated_to: "/chat"},                 |
|    fn_call_id: "..."}                                              |
|                                                                    |
|   {type: "end"}                                                    |
|                                                                    |
+------------------------------------------------------------------+
|                                                                    |
| SERVER -> CLIENT messages:                                         |
|                                                                    |
|   {type: "setup_complete",                                         |
|    sessionId: "abc123",                                            |
|    mode: "gemini"|"claude",                                        |
|    resumed: true|false}                                            |
|                                                                    |
|   {type: "audio",                                                  |
|    data: "<base64 PCM 24kHz>"}                                     |
|                                                                    |
|   {type: "text",                                                   |
|    text: "VOX response text"}                                      |
|                                                                    |
|   {type: "transcript",                                             |
|    role: "user"|"model",                                           |
|    text: "transcribed text"}                                       |
|                                                                    |
|   {type: "turn_complete",                                          |
|    turn: 5}                                                        |
|                                                                    |
|   {type: "function_call",                                          |
|    name: "run_tool",                                               |
|    args: {tool_id: "security_scanner"},                            |
|    server_handled: true|false,                                     |
|    fn_call_id: "..." (browser fns only),                           |
|    async: true (async fns only)}                                   |
|                                                                    |
|   {type: "function_result",                                        |
|    name: "run_tool",                                               |
|    result: {success: true, ...}}                                   |
|                                                                    |
|   {type: "start_tour",                                             |
|    page: "kg-studio",                                              |
|    tour: {name: "...", steps: [...]}}                              |
|                                                                    |
|   {type: "async_task_started",                                     |
|    task_id: "abc123",                                              |
|    function: "ingest_to_kg"}                                       |
|                                                                    |
|   {type: "async_task_complete",                                    |
|    task_id: "abc123",                                              |
|    function: "ingest_to_kg",                                       |
|    result: {...}}                                                  |
|                                                                    |
|   {type: "go_away",                                                |
|    session_token: "...",                                            |
|    message: "Session reconnecting..."}                             |
|                                                                    |
|   {type: "error",                                                  |
|    message: "Error description"}                                   |
|                                                                    |
+------------------------------------------------------------------+
```

## 1.5 Backend: VoxSession Dataclass

**File:** `backend/services/vox_service.py`

```python
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
```

Fields explained:
- `session_id` -- 8-character UUID prefix, e.g. `"a3b7c9d1"`
- `mode` -- `"gemini"` for Live API audio streaming, `"claude"` for text pipeline with browser STT/TTS
- `model` -- The model ID string, e.g. `"gemini-2.5-flash-native-audio-preview-12-2025"` or `"claude-sonnet-4-6"`
- `voice` -- Gemini voice name (e.g. `"Puck"`), or `"browser"` for Claude mode
- `created_at` -- `time.time()` epoch float
- `system_instruction` -- The full VOX system prompt (built by `build_system_instruction()`)
- `tools` -- The list of 34 function declaration dicts
- `gemini_session` -- The live Gemini session object (only for Gemini mode)
- `gemini_ctx` -- The async context manager wrapping the session (for cleanup via `__aexit__`)
- `turn_count` -- Incremented after each turn_complete
- `function_count` -- Incremented after each function execution
- `session_token` -- Gemini session resumption token (updated from `session_resumption_update` responses)

## 1.6 The 16 Gemini Voices

**File:** `backend/services/vox_service.py`

```python
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
```

Gender breakdown: 6 Male, 6 Female, 4 Non-binary. The default voice is `"Puck"` (configured in `config.py` as `VOX_DEFAULT_VOICE`). The voice selection is persisted client-side in `localStorage` under the key `voxVoice`.

## 1.7 The 34 Function Declarations

**File:** `backend/services/vox_service.py`, function `build_function_declarations()`

All 34 functions grouped by category:

### Browser-Side Functions (6) -- executed in frontend JavaScript

These are forwarded to the client via WebSocket with `server_handled: false`. The frontend's `executeBrowserFunction()` handles them locally and sends results back.

| # | Function Name | Description | Required Params |
|---|--------------|-------------|-----------------|
| 1 | `navigate_page` | Navigate workspace to a page | `path` (string) |
| 2 | `get_current_page` | Get current page path | (none) |
| 3 | `get_workspace_state` | Get active provider, model, page, theme, project count | (none) |
| 4 | `switch_model` | Switch AI model | `provider`, `model` |
| 5 | `switch_theme` | Switch visual theme | `theme_id` |
| 6 | `read_page_content` | Read visible text content of current page | (none) |

### Core Workspace Tools (6) -- executed on backend

| # | Function Name | Description | Required Params |
|---|--------------|-------------|-----------------|
| 7 | `run_tool` | Execute any of 58+ registered tools | `tool_id`; optional `params` |
| 8 | `list_tools` | List all available tools by category | (none) |
| 9 | `query_kg` | Hybrid semantic search on a KG | `database_id`, `query` |
| 10 | `list_kgs` | List all KG databases | (none) |
| 11 | `run_agent` | Execute an NLKE agent | `agent_name`, `input` |
| 12 | `list_agents` | List all NLKE agents | (none) |

### Direct Developer Tool Shortcuts (5) -- backend, via tools_service

| # | Function Name | Description | Required Params |
|---|--------------|-------------|-----------------|
| 13 | `generate_react_component` | Generate React component with TS | `name`, `description`; optional `framework`, `features` |
| 14 | `generate_fastapi_endpoint` | Generate FastAPI route | `description`; optional `method`, `path`, `framework` |
| 15 | `scan_code_security` | Scan code for vulnerabilities | `code`; optional `language` |
| 16 | `analyze_code_complexity` | Cyclomatic/cognitive complexity | `code`; optional `language` |
| 17 | `generate_tests` | Generate test cases from code | `code`; optional `framework`, `style` |

### Guided Tours (2) -- backend

| # | Function Name | Description | Required Params |
|---|--------------|-------------|-----------------|
| 18 | `start_guided_tour` | Start voice-narrated tour of a page | optional `page` |
| 19 | `get_available_tours` | List all tours with step counts | (none) |

### Workspace Control / Jarvis Mode (5) -- backend

| # | Function Name | Description | Required Params |
|---|--------------|-------------|-----------------|
| 20 | `create_project` | Create AI Studio project | `name`; optional `description` |
| 21 | `list_projects` | List Studio projects | (none) |
| 22 | `run_workflow` | Execute a workflow template | `workflow_name`; optional `input` |
| 23 | `search_playbooks` | Search 53 playbooks | `query` |
| 24 | `search_kg` | Enhanced KG search with filters | `database_id`, `query`; optional `node_type`, `limit` |

### KG Studio Control (3) -- backend

| # | Function Name | Description | Required Params |
|---|--------------|-------------|-----------------|
| 25 | `get_kg_analytics` | Graph analytics (PageRank, communities) | `database_id` |
| 26 | `cross_kg_search` | Search across multiple KGs | `query`; optional `database_ids`, `limit` |
| 27 | `ingest_to_kg` | AI entity extraction into a KG | `database_id`, `text` |

### Expert Control (2) -- backend

| # | Function Name | Description | Required Params |
|---|--------------|-------------|-----------------|
| 28 | `chat_with_expert` | Chat with a KG-OS expert | `expert_id`, `message` |
| 29 | `list_experts` | List all KG-OS experts | (none) |

### Voice Macros (4) -- backend

| # | Function Name | Description | Required Params |
|---|--------------|-------------|-----------------|
| 30 | `create_macro` | Create multi-step voice macro | `name`, `trigger_phrase`, `steps`; optional `error_policy` |
| 31 | `list_macros` | List saved macros | (none) |
| 32 | `run_macro` | Execute a macro by ID or trigger phrase | `macro_id` |
| 33 | `delete_macro` | Delete a macro | `macro_id` |

### Thermal Monitoring (1) -- backend

| # | Function Name | Description | Required Params |
|---|--------------|-------------|-----------------|
| 34 | `check_thermal` | Device temperature + battery status | (none) |

### Function Routing Classification

Functions are classified into three execution categories:

```python
# Browser-side functions (forwarded to client, NOT executed on server)
BROWSER_FUNCTIONS = {
    "navigate_page", "get_current_page", "get_workspace_state",
    "switch_model", "switch_theme", "read_page_content",
}

# Async functions (run in background, result sent later)
ASYNC_FUNCTIONS = {"ingest_to_kg", "run_workflow", "cross_kg_search", "run_agent"}

# All other functions: synchronous server-side execution
```

## 1.8 VOX System Prompt

**File:** `backend/services/vox_service.py`, function `build_system_instruction()`

The system prompt is built dynamically at session creation time. It has three sections:

1. **Base personality and capabilities** (static)
2. **Awareness context** (dynamic, injected from `vox_awareness.build_awareness_prompt()`)
3. **Custom prompt** (optional, user-provided at connect time)

Full base prompt:

```
You are VOX, the voice-powered master agent of the Multi-AI Agentic Workspace. You are not just a voice assistant -- you ARE the workspace's intelligence, personality, and soul.

PERSONALITY:
- You are confident, knowledgeable, and slightly witty
- You speak naturally and conversationally -- never robotic
- You take pride in the workspace's capabilities and enjoy showing them off
- You address users warmly but professionally
- When executing functions, you narrate what you're doing naturally

CAPABILITIES (34 functions):
- Navigate between all workspace pages
- Run any of 58+ registered tools across 11 categories
- Generate React components, FastAPI endpoints, scan security, analyze complexity, generate tests
- Query 57+ knowledge graph databases with hybrid semantic search
- Cross-KG search across multiple databases simultaneously
- AI entity extraction into knowledge graphs
- Get graph analytics (PageRank, communities, centrality)
- Execute NLKE agents for complex reasoning tasks
- Start guided tours for any page -- voice-narrated walkthroughs
- Create and manage Studio projects
- Execute workflow templates (error-recovery, knowledge-synthesis, session-handoff, multi-agent)
- Search 53 implementation playbooks
- Chat with KG-OS experts backed by structured knowledge
- Create, list, run, and delete voice macros (multi-step command sequences)
- Check device temperature and battery status
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
- Keep responses concise for voice -- no long paragraphs
- Confirm actions after executing them
```

The awareness context is appended dynamically:

```
CURRENT AWARENESS:
Current page: /kg-studio (on page for 45s)
Recent pages: /chat -> /tools -> /kg-studio
Recent errors (1 unresolved): [api_error] Connection timeout to Gemini...
Active project: My Dashboard App
Session duration: 12m 34s
Most visited: /chat(15), /kg-studio(8), /tools(5)
```

## 1.9 VoxService Class

**File:** `backend/services/vox_service.py`

The `VoxService` class is a singleton (`vox_service = VoxService()`) that manages all voice sessions.

### Constructor and Client Management

```python
class VoxService:
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
```

The client is lazily initialized and cached. If the API key changes at runtime (via the settings UI), the client is recreated.

### create_gemini_session()

```python
async def create_gemini_session(
    self,
    model: str = VOX_DEFAULT_MODEL,
    voice: str = VOX_DEFAULT_VOICE,
    custom_prompt: str = "",
    session_token: Optional[str] = None,
) -> VoxSession:
```

This method:
1. Gets the Gemini client
2. Generates an 8-char session ID
3. Builds the system prompt via `build_system_instruction(custom_prompt)`
4. Builds 34 `types.FunctionDeclaration` objects
5. Constructs the `LiveConnectConfig` (see section 1.10)
6. Optionally attaches a `SessionResumptionConfig` with the provided token
7. Calls `client.aio.live.connect(model, config)` and enters the async context manager
8. Creates a `VoxSession` and stores it in `self.sessions`

The Live API model ID is configured in `config.py`:

```python
VOX_DEFAULT_MODEL = "gemini-2.5-flash-native-audio-preview-12-2025"
```

### create_claude_session()

```python
def create_claude_session(
    self,
    model: str = "claude-sonnet-4-6",
    custom_prompt: str = "",
) -> VoxSession:
```

This is a synchronous method (no Gemini Live API involved). It creates a `VoxSession` with `mode="claude"` and `voice="browser"`. The session has no `gemini_session` or `gemini_ctx`. All audio processing happens client-side using the Web Speech API.

### send_audio()

```python
async def send_audio(self, session_id: str, audio_b64: str):
    session = self.sessions.get(session_id)
    if not session or session.mode != "gemini" or not session.gemini_session:
        return
    audio_bytes = base64.b64decode(audio_b64)
    await session.gemini_session.send_realtime_input(
        audio=types.Blob(data=audio_bytes, mime_type="audio/pcm;rate=16000")
    )
```

Accepts base64-encoded PCM audio at 16kHz, decodes it, and forwards it to the Gemini Live API session as a `types.Blob`.

### send_text()

```python
async def send_text(self, session_id: str, text: str):
    session = self.sessions.get(session_id)
    if not session or not session.gemini_session:
        return
    await session.gemini_session.send_client_content(
        turns=types.Content(role="user", parts=[types.Part(text=text)])
    )
```

Sends text input to the Gemini Live API session. Used for text-based interactions in Gemini mode (the text input box on VoxPage).

### send_function_result()

```python
async def send_function_result(self, session_id: str, fn_id: str, name: str, result: dict):
    session = self.sessions.get(session_id)
    if not session or session.mode != "gemini" or not session.gemini_session:
        return
    fr_kwargs = {"name": name, "response": result}
    if fn_id:
        fr_kwargs["id"] = fn_id
    await session.gemini_session.send_tool_response(
        function_responses=[types.FunctionResponse(**fr_kwargs)]
    )
```

Sends function execution results back to the Gemini Live API so it can formulate a follow-up response. The `fn_id` (function call ID) is extracted from the original `tool_call.function_calls[].id` to correlate the response.

### close_session()

```python
async def close_session(self, session_id: str):
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
```

Properly cleans up by exiting the async context manager (which closes the Live API WebSocket connection).

### Availability Checks

```python
def is_gemini_available(self) -> bool:
    from config import GEMINI_API_KEY
    return bool(GEMINI_API_KEY)

def is_claude_available(self) -> bool:
    from config import ANTHROPIC_API_KEY, MODE
    return MODE == "standalone" and bool(ANTHROPIC_API_KEY)
```

## 1.10 Gemini Live API Configuration

**File:** `backend/services/vox_service.py`, inside `create_gemini_session()`

```python
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

# Session resumption
if session_token:
    live_config.session_resumption = types.SessionResumptionConfig(
        handle=session_token
    )
else:
    live_config.session_resumption = types.SessionResumptionConfig()
```

Key configuration details:
- **response_modalities:** `["AUDIO"]` -- Gemini responds with audio (not text)
- **speech_config:** Sets the voice for audio responses
- **tools:** Two tool objects -- one with the 34 function declarations, one with Google Search grounding for real-time queries
- **context_window_compression:** Uses `SlidingWindow` to manage long conversations
- **input_audio_transcription:** Enables transcription of user audio input
- **output_audio_transcription:** Enables transcription of model audio output
- **session_resumption:** Enables seamless reconnection if the session drops

The connection is established with:

```python
ctx = client.aio.live.connect(model=model, config=live_config)
gemini_session = await ctx.__aenter__()
```

## 1.11 Backend Router: REST Endpoints

**File:** `backend/routers/vox.py`

### Pydantic Models

```python
class FunctionRunRequest(BaseModel):
    args: dict = {}

class AwarenessEvent(BaseModel):
    event_type: str  # "page_visit" | "error" | "context"
    page: Optional[str] = None
    error_type: Optional[str] = None
    message: Optional[str] = None
    key: Optional[str] = None
    value: Optional[str] = None
    metadata: Optional[dict] = None

class MacroCreateRequest(BaseModel):
    name: str
    trigger_phrase: str
    steps: list[dict]
    error_policy: str = "abort"
```

### All 14 REST Endpoints

| Method | Path | Handler | Returns |
|--------|------|---------|---------|
| GET | `/api/vox/voices` | `list_voices()` | `{voices: GEMINI_VOICES}` |
| GET | `/api/vox/status` | `vox_status()` | `{gemini_available, claude_available, active_sessions}` |
| GET | `/api/vox/functions` | `list_functions()` | `{functions: [...], count: 34}` |
| POST | `/api/vox/function/{fn_name}` | `run_function()` | `{name, result}` |
| POST | `/api/vox/awareness` | `log_awareness()` | `{success, visit_id/error_id}` |
| GET | `/api/vox/awareness` | `get_awareness()` | `{prompt, recent_pages, unresolved_errors, page_stats}` |
| GET | `/api/vox/tours` | `list_tours()` | `{tours: [...], count: 11}` |
| GET | `/api/vox/tours/{page}` | `get_tour()` | `{page, name, description, steps}` |
| GET | `/api/vox/macros` | `list_macros()` | `{macros: [...]}` |
| POST | `/api/vox/macros` | `create_macro()` | `{success, macro}` |
| DELETE | `/api/vox/macros/{macro_id}` | `delete_macro()` | `{success}` |
| POST | `/api/vox/macros/{macro_id}/run` | `run_macro_endpoint()` | `{success, results}` |
| GET | `/api/vox/thermal` | `get_thermal()` | `{temperature, status, health, percentage, plugged, warning, threshold, suggestion}` |
| WS | `/ws/vox` | `vox_websocket()` | Bidirectional WebSocket |

## 1.12 Backend Router: WebSocket Handler

**File:** `backend/routers/vox.py`, function `vox_websocket()`

The WebSocket handler is the core of VOX. It accepts a connection, then enters an infinite loop processing client messages.

```python
@router.websocket("/ws/vox")
async def vox_websocket(ws: WebSocket):
    await ws.accept()
    session_id = None

    try:
        while True:
            raw = await ws.receive_text()
            msg = json.loads(raw)
            msg_type = msg.get("type", "")

            if msg_type == "start":
                # Create Gemini or Claude session
                # Start _gemini_receive_loop as background task (Gemini mode)
                ...

            elif msg_type == "audio" and session_id:
                # Forward PCM audio to Gemini Live API
                await vox_service.send_audio(session_id, msg.get("data", ""))

            elif msg_type == "text" and session_id:
                # Gemini: send_text()
                # Claude: launch _claude_text_pipeline() as background task
                ...

            elif msg_type == "browser_function_result" and session_id:
                # Forward browser function result to Gemini
                await vox_service.send_function_result(...)

            elif msg_type == "end":
                await vox_service.close_session(session_id)
                break

    except WebSocketDisconnect:
        pass
    finally:
        if session_id:
            await vox_service.close_session(session_id)
```

### _gemini_receive_loop()

This is launched as an `asyncio.create_task()` when a Gemini session starts. It runs continuously, receiving responses from the Gemini Live API and dispatching them to the WebSocket:

```python
async def _gemini_receive_loop(ws: WebSocket, session: VoxSession):
    try:
        async for response in session.gemini_session.receive():
            # 1. Audio data -> forward as base64
            if response.data:
                audio_b64 = base64.b64encode(response.data).decode("utf-8")
                await ws.send_json({"type": "audio", "data": audio_b64})

            # 2. Server content (text parts + turn_complete)
            if response.server_content:
                sc = response.server_content
                if sc.model_turn and sc.model_turn.parts:
                    for part in sc.model_turn.parts:
                        if hasattr(part, "text") and part.text:
                            await ws.send_json({"type": "text", "text": part.text})
                if sc.turn_complete:
                    session.turn_count += 1
                    await ws.send_json({"type": "turn_complete", "turn": session.turn_count})

            # 3. Tool calls (function declarations)
            if response.tool_call:
                for fc in response.tool_call.function_calls:
                    fn_name = fc.name
                    fn_args = dict(fc.args) if fc.args else {}
                    fn_call_id = getattr(fc, 'id', None) or ""
                    session.function_count += 1

                    # Route: async -> background task
                    if fn_name in ASYNC_FUNCTIONS:
                        # Launch background task, send async_task_started
                        ...

                    # Route: server-side -> execute immediately
                    elif fn_name not in BROWSER_FUNCTIONS:
                        result = await _execute_server_function(fn_name, fn_args)
                        # Send function_call + function_result to client
                        # Handle special start_tour result
                        # Send result back to Gemini via send_function_result
                        ...

                    # Route: browser-side -> forward to client
                    else:
                        await ws.send_json({
                            "type": "function_call",
                            "name": fn_name,
                            "args": fn_args,
                            "fn_call_id": fn_call_id,
                            "server_handled": False,
                        })

            # 4. Session resumption updates
            if response.session_resumption_update:
                update = response.session_resumption_update
                if update.resumable and update.new_handle:
                    session.session_token = update.new_handle

            # 5. GoAway (session about to terminate)
            if response.go_away:
                await ws.send_json({
                    "type": "go_away",
                    "session_token": session.session_token,
                    "message": "Session reconnecting...",
                })

            # 6. Transcripts (input + output)
            if response.server_content:
                sc = response.server_content
                if hasattr(sc, 'input_transcription') and sc.input_transcription:
                    await ws.send_json({
                        "type": "transcript", "role": "user",
                        "text": sc.input_transcription.text
                    })
                if hasattr(sc, 'output_transcription') and sc.output_transcription:
                    await ws.send_json({
                        "type": "transcript", "role": "model",
                        "text": sc.output_transcription.text
                    })
    except Exception as e:
        await ws.send_json({"type": "error", "message": f"Gemini stream error: {str(e)}"})
```

### _claude_text_pipeline()

Launched as an `asyncio.create_task()` when a text message arrives in Claude mode:

```python
async def _claude_text_pipeline(ws: WebSocket, session: VoxSession, text: str):
    client = _get_client()
    claude_tools = _build_claude_tools()  # Convert VOX declarations to Anthropic format
    messages = [{"role": "user", "content": text}]
    full_response = ""

    # Multi-turn tool use loop (max 5 rounds)
    for _ in range(5):
        response = await asyncio.to_thread(
            client.messages.create,
            model=session.model,
            max_tokens=2048,
            system=session.system_instruction,
            messages=messages,
            tools=claude_tools,
        )

        # Collect text parts and tool_use blocks
        text_parts = []
        tool_uses = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_uses.append(block)

        if text_parts:
            full_response += " ".join(text_parts)

        # No tool calls -> done
        if not tool_uses:
            break

        # Serialize assistant message
        assistant_content = [...]
        messages.append({"role": "assistant", "content": assistant_content})

        # Execute each tool_use block
        tool_results = []
        for tu in tool_uses:
            if tu.name not in BROWSER_FUNCTIONS:
                result = await _execute_server_function(tu.name, tu.input or {})
                # Send function_call + function_result via WS
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tu.id,
                    "content": json.dumps(result),
                })
            else:
                # Browser-side: acknowledge
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tu.id,
                    "content": json.dumps({"success": True, "note": "Executed in browser"}),
                })

        messages.append({"role": "user", "content": tool_results})

    # Send final text for browser TTS
    if full_response:
        await ws.send_json({"type": "text", "text": full_response})
    await ws.send_json({"type": "turn_complete", "turn": session.turn_count})
```

The `_build_claude_tools()` function converts VOX function declarations to the Anthropic `tool_use` format:

```python
def _build_claude_tools() -> list[dict]:
    tools = []
    for fn in build_function_declarations():
        tools.append({
            "name": fn["name"],
            "description": fn.get("description", ""),
            "input_schema": fn.get("parameters", {"type": "object", "properties": {}}),
        })
    return tools
```

### _execute_server_function()

This is the central dispatcher for all 28 server-side functions. It is a single large `if/elif` chain:

```python
async def _execute_server_function(name: str, args: dict) -> dict:
    try:
        if name == "run_tool":
            from services.tools_service import tools_service
            result = await tools_service.run_tool(args.get("tool_id"), args.get("params", {}))
            return {"success": True, "result": _safe_serialize(result)}

        elif name == "list_tools":
            # ...
        elif name == "query_kg":
            # ...
        elif name == "list_kgs":
            # ...
        elif name == "run_agent":
            # ...
        elif name == "list_agents":
            # ...
        elif name == "generate_react_component":
            # Delegates to tools_service.run_tool("react_component_generator", params)
        elif name == "generate_fastapi_endpoint":
            # Delegates to tools_service.run_tool("fastapi_endpoint_generator", params)
        elif name == "scan_code_security":
            # Delegates to tools_service.run_tool("security_scanner", params)
        elif name == "analyze_code_complexity":
            # Delegates to tools_service.run_tool("complexity_scorer", params)
        elif name == "generate_tests":
            # Delegates to tools_service.run_tool("pytest_generator", params)
        elif name == "start_guided_tour":
            # Loads tours JSON, returns {action: "start_tour", tour: {...}}
        elif name == "get_available_tours":
            # ...
        elif name == "create_project":
            # Delegates to studio_service.create_project()
        elif name == "list_projects":
            # Delegates to studio_service.list_projects()
        elif name == "run_workflow":
            # Maps workflow names to template files
        elif name == "search_playbooks":
            # Delegates to playbook_index.search()
        elif name == "search_kg":
            # Enhanced search with optional node_type filter
        elif name == "get_kg_analytics":
            # Delegates to analytics_service.get_analytics()
        elif name == "cross_kg_search":
            # Iterates up to 10 databases
        elif name == "ingest_to_kg":
            # Delegates to ingestion_service.ingest_text() via asyncio.to_thread
        elif name == "chat_with_expert":
            # Delegates to expert_service.chat()
        elif name == "list_experts":
            # Delegates to expert_service.list_experts()
        elif name == "create_macro":
            # Delegates to vox_macro_service.create_macro()
        elif name == "list_macros":
            # Delegates to vox_macro_service.list_macros()
        elif name == "run_macro":
            # Delegates to vox_macro_service.execute_macro()
        elif name == "delete_macro":
            # Delegates to vox_macro_service.delete_macro()
        elif name == "check_thermal":
            # Delegates to thermal_monitor.check()
        else:
            return {"success": False, "error": f"Unknown server function: {name}"}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

All return values are JSON-serializable dicts. The `_safe_serialize()` helper ensures any non-serializable objects are converted to strings.

## 1.13 Awareness Layer

**File:** `backend/services/vox_awareness.py`

The awareness layer is a SQLite-backed service that tracks what the user is doing in the workspace, so VOX can provide contextually relevant responses.

### SQLite Schema

Database file: `backend/vox_awareness.db`

```sql
CREATE TABLE IF NOT EXISTS page_visits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    page TEXT NOT NULL,
    timestamp REAL NOT NULL,
    duration REAL DEFAULT 0,
    metadata TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS error_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    error_type TEXT NOT NULL,
    message TEXT NOT NULL,
    page TEXT DEFAULT '',
    timestamp REAL NOT NULL,
    resolved INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS session_context (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_page_visits_ts ON page_visits(timestamp);
CREATE INDEX IF NOT EXISTS idx_error_log_ts ON error_log(timestamp);
```

### VoxAwareness Class Methods

```python
class VoxAwareness:
    def __init__(self, db_path: str = str(DB_PATH)):
        # Initialize DB, set session start time

    def log_page_visit(self, page: str, metadata: Optional[dict] = None) -> int:
        # 1. Update duration of previous visit
        # 2. Insert new visit record
        # Returns visit ID

    def log_error(self, error_type: str, message: str, page: str = "") -> int:
        # Insert error record, return error ID

    def resolve_error(self, error_id: int):
        # Mark error as resolved (resolved=1)

    def set_context(self, key: str, value: Any):
        # INSERT OR REPLACE into session_context

    def get_context(self, key: str) -> Optional[str]:
        # Retrieve context value by key

    def get_recent_pages(self, limit: int = 5) -> list[dict]:
        # Return last N page visits

    def get_unresolved_errors(self, limit: int = 3) -> list[dict]:
        # Return recent unresolved errors

    def get_page_stats(self) -> dict[str, int]:
        # Page visit frequency (GROUP BY page)

    def build_awareness_prompt(self) -> str:
        # Generates context string injected into VOX system prompt
        # Includes: current page, recent history, errors, active project/KG,
        # session duration, most visited pages

    def cleanup_old_data(self, max_age_hours: int = 24):
        # Prune data older than max_age_hours
```

The `build_awareness_prompt()` method output example:

```
Current page: /kg-studio (on page for 45s)
Recent pages: /chat -> /tools -> /kg-studio
Recent errors (1 unresolved): [api_error] Connection timeout to Gemini API
Active project: Dashboard App
Active KG: claude-code-tools-kg
Session duration: 12m 34s
Most visited: /chat(15), /kg-studio(8), /tools(5)
```

### Frontend Awareness Reporting

The `useVox.ts` hook automatically reports page visits:

```typescript
// Awareness: report page visits
const prevPageRef = useRef(location.pathname);
useEffect(() => {
    if (location.pathname !== prevPageRef.current) {
        prevPageRef.current = location.pathname;
        fetch(`${API_BASE}/api/vox/awareness`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                event_type: 'page_visit',
                page: location.pathname,
                metadata: { timestamp: Date.now() },
            }),
        }).catch(() => { /* best effort */ });
    }
}, [location.pathname]);
```

Additionally, during the Gemini receive loop, the server logs function executions to awareness:

```python
# In _gemini_receive_loop, after receiving a tool_call:
from services.vox_awareness import vox_awareness
vox_awareness.set_context("last_function", fn_name)
```

## 1.14 Voice Macros

**File:** `backend/services/vox_macros.py`

Macros are user-definable multi-step command sequences with pipe chaining. They allow users to create reusable voice-triggered workflows.

### SQLite Schema

Database file: `backend/vox_macros.db`

```sql
CREATE TABLE IF NOT EXISTS macros (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    trigger_phrase TEXT NOT NULL,
    steps TEXT NOT NULL,          -- JSON array of step objects
    error_policy TEXT DEFAULT 'abort',
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_macros_trigger ON macros(trigger_phrase);
```

### Macro Step Format

Each step in the `steps` JSON array has this structure:

```json
{
    "function": "function_name",
    "args": {"key": "value"},
    "pipe_from": null
}
```

- `function` -- One of the 34 VOX function names
- `args` -- Arguments for the function
- `pipe_from` -- Integer index of a previous step whose output should be piped as input (or `null`)

### Error Policies

| Policy | Behavior |
|--------|----------|
| `abort` | Stop macro execution on first failure |
| `skip` | Skip failed step, continue to next |
| `retry` | (Reserved, not yet implemented beyond abort/skip logic) |

### Pipe Chaining Engine

The `execute_macro()` method implements a pipe chaining execution engine:

```python
async def execute_macro(self, macro_id: str, execute_fn: Callable) -> list[dict]:
    macro = self.get_macro(macro_id)
    if not macro:
        macro = self.find_by_trigger(macro_id)  # Fuzzy match by trigger phrase
    if not macro:
        return [{"step": 0, "success": False, "error": f"Macro not found: {macro_id}"}]

    results = []
    error_policy = macro.get("error_policy", "abort")

    for i, step in enumerate(macro["steps"]):
        fn_name = step.get("function", "")
        fn_args = dict(step.get("args", {}))

        # Pipe chaining: inject output from a previous step
        pipe_from = step.get("pipe_from")
        if pipe_from is not None and isinstance(pipe_from, int):
            if 0 <= pipe_from < len(results) and results[pipe_from].get("success"):
                prev_result = results[pipe_from].get("result", {})
                if isinstance(prev_result, dict):
                    # Auto-inject: databases -> database_id, tools -> tool_id
                    if "databases" in prev_result and "database_id" not in fn_args:
                        fn_args["database_id"] = prev_result["databases"][0].get("id", "")
                    elif "tools" in prev_result and "tool_id" not in fn_args:
                        fn_args["tool_id"] = prev_result["tools"][0].get("id", "")
                    elif "result" in prev_result:
                        fn_args["_piped_input"] = prev_result["result"]

        try:
            result = await execute_fn(fn_name, fn_args)
            success = result.get("success", False) if isinstance(result, dict) else True
            results.append({"step": i, "function": fn_name, "success": success, "result": result})

            if not success and error_policy == "abort":
                results.append({"step": i + 1, "function": "macro_aborted", "success": False,
                                "error": f"Step {i} ({fn_name}) failed, aborting macro"})
                break
        except Exception as e:
            results.append({"step": i, "function": fn_name, "success": False, "error": str(e)})
            if error_policy == "abort":
                break

    return results
```

The `find_by_trigger()` method supports fuzzy matching:
1. First tries exact match on `trigger_phrase`
2. Falls back to `LIKE %phrase%` on both `trigger_phrase` and `name`

### Example Macro

A "Morning Routine" macro that lists KGs, searches one, then navigates to the KG Studio:

```json
{
    "name": "Morning Routine",
    "trigger_phrase": "morning routine",
    "steps": [
        {"function": "list_kgs", "args": {}, "pipe_from": null},
        {"function": "search_kg", "args": {"query": "latest updates"}, "pipe_from": 0},
        {"function": "navigate_page", "args": {"path": "/kg-studio"}, "pipe_from": null}
    ],
    "error_policy": "skip"
}
```

Step 1 lists KGs. Step 2 has `pipe_from: 0`, so the first database ID from step 1's results is auto-injected as `database_id`.

## 1.15 Thermal Monitoring

**File:** `backend/services/vox_thermal.py`

Thermal monitoring reads the device battery temperature via the `termux-battery-status` command (Android/Termux specific).

```python
class ThermalMonitor:
    def __init__(self, threshold: float = 42.0):
        self.threshold = threshold
        self._last_reading: Optional[dict] = None

    async def get_temperature(self) -> dict:
        try:
            proc = await asyncio.create_subprocess_exec(
                "termux-battery-status",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5.0)
            data = json.loads(stdout.decode())
            reading = {
                "temperature": data.get("temperature", 0),
                "status": data.get("status", "unknown"),
                "health": data.get("health", "unknown"),
                "percentage": data.get("percentage", -1),
                "plugged": data.get("plugged", "unknown"),
            }
            self._last_reading = reading
            return reading
        except asyncio.TimeoutError:
            return self._fallback("timeout")
        except FileNotFoundError:
            return self._fallback("termux-api not installed")
        except json.JSONDecodeError:
            return self._fallback("invalid response")
        except Exception as e:
            return self._fallback(str(e))

    async def check(self) -> dict:
        info = await self.get_temperature()
        temp = info.get("temperature", 0)
        warning = temp >= self.threshold if temp > 0 else False
        suggestion = ""
        if warning:
            if temp >= 45:
                suggestion = "Device is very hot. Consider pausing the voice session to cool down."
            else:
                suggestion = "Device is warm. Monitor closely."
        return {**info, "warning": warning, "threshold": self.threshold, "suggestion": suggestion}
```

Temperature thresholds:
- **42.0 C** -- Warning threshold (configurable via constructor)
- **>= 45 C** -- "Very hot" with suggestion to pause session
- **42-45 C** -- "Warm" with monitor suggestion

The fallback method returns a safe dict with `status: "unavailable"` when `termux-battery-status` is not available.

## 1.16 Guided Tours

**File:** `backend/data/vox_tours.json`

11 guided tour definitions covering all major workspace pages:

| Page ID | Tour Name | Description | Step Count |
|---------|-----------|-------------|------------|
| `chat` | Chat Page Tour | Learn how to use the dual-model streaming chat | 3 |
| `coding` | Coding Page Tour | Explore the AI-powered IDE | 3 |
| `agents` | Agents Page Tour | Discover the 33 NLKE agents | 3 |
| `playbooks` | Playbooks Page Tour | Browse 53 implementation playbooks | 2 |
| `workflows` | Workflows Page Tour | Design and execute visual workflows | 2 |
| `kg-studio` | KG Studio Tour | Explore the Graph-RAG knowledge workspace | 4 |
| `experts` | Experts Page Tour | Build AI experts backed by knowledge graphs | 2 |
| `builder` | Studio Tour | Generate full-stack React apps with AI | 3 |
| `tools` | Tools Page Tour | Explore 58+ Python tools across 11 categories | 3 |
| `vox` | VOX Tour | Master the VOX voice control center | 3 |
| `settings` | Settings Tour | Configure your workspace | 2 |

Each tour step has the structure:

```json
{
    "target": "CSS selector(s), comma-separated fallbacks",
    "speech": "What VOX says for this step",
    "position": "top|bottom|left|right",
    "highlight": true
}
```

Example (KG Studio tour):

```json
{
    "target": "[class*='search'], input[placeholder*='search']",
    "speech": "Use hybrid semantic search combining embeddings, BM25 keywords, and graph structure. This achieves 88.5 percent recall -- much better than any single method alone.",
    "position": "bottom",
    "highlight": true
}
```

## 1.17 Frontend: useVox Hook

**File:** `frontend/src/hooks/useVox.ts`

This is the primary React hook for all VOX voice integration. It manages:
- WebSocket connection lifecycle
- Audio capture (microphone) and playback
- Browser Speech Recognition (Claude mode)
- Browser Speech Synthesis (Claude mode)
- Browser function execution
- Auto-reconnect with exponential backoff
- Awareness reporting (page visits)
- Event system for external listeners
- Transcript and function log management
- Guided tour state

### Constants

```typescript
const API_BASE = `${window.location.protocol}//${window.location.hostname}:8000`;
const WS_BASE = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.hostname}:8000`;

const MAX_RECONNECT_ATTEMPTS = 3;
const RECONNECT_BASE_DELAY = 500; // ms, doubles each attempt (500, 1000, 2000)
```

### Initial State

```typescript
const initialState: VoxState = {
    connected: false,
    mode: null,
    voice: 'Puck',
    speaking: false,
    listening: false,
    turnCount: 0,
    functionCount: 0,
    sessionId: null,
    transcript: [],
    functionLog: [],
    error: null,
    reconnecting: false,
};
```

Voice is persisted in `localStorage('voxVoice')` and restored on initialization.

### Audio Pipeline (Gemini Mode)

**Capture (16kHz):**

```typescript
const startMic = useCallback(() => {
    navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
        micStreamRef.current = stream;
        // Try 16kHz AudioContext, fallback to native rate
        let ctx: AudioContext;
        try {
            ctx = new AudioContext({ sampleRate: 16000 });
        } catch (_) {
            ctx = new AudioContext();
        }

        const source = ctx.createMediaStreamSource(stream);
        const processor = ctx.createScriptProcessor(4096, 1, 1);

        const nativeRate = ctx.sampleRate;
        const targetRate = 16000;

        processor.onaudioprocess = (e) => {
            if (!connected || ws not open) return;
            const raw = e.inputBuffer.getChannelData(0);
            const samples = nativeRate !== targetRate
                ? downsample(raw, nativeRate, targetRate)
                : raw;
            sendPCMChunk(samples);
        };

        source.connect(processor);
        processor.connect(ctx.destination);
    });
}, []);
```

The `downsample()` function performs simple linear downsampling:

```typescript
const downsample = (buffer: Float32Array, fromRate: number, toRate: number): Float32Array => {
    if (fromRate === toRate) return buffer;
    const ratio = fromRate / toRate;
    const newLength = Math.floor(buffer.length / ratio);
    const result = new Float32Array(newLength);
    for (let i = 0; i < newLength; i++) result[i] = buffer[Math.floor(i * ratio)];
    return result;
};
```

The `sendPCMChunk()` function converts Float32 to Int16 (PCM), then base64-encodes it:

```typescript
const sendPCMChunk = useCallback((samples: Float32Array) => {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    const int16 = new Int16Array(samples.length);
    for (let i = 0; i < samples.length; i++) {
        const s = Math.max(-1, Math.min(1, samples[i]));
        int16[i] = s < 0 ? s * 32768 : s * 32767;
    }
    const bytes = new Uint8Array(int16.buffer);
    let binary = '';
    for (let j = 0; j < bytes.length; j++) binary += String.fromCharCode(bytes[j]);
    ws.send(JSON.stringify({ type: 'audio', data: btoa(binary) }));
}, []);
```

**Playback (24kHz):**

```typescript
const playAudioChunk = useCallback((b64Data: string) => {
    ensurePlayContext();  // AudioContext at 24kHz
    const ctx = playCtxRef.current!;

    // Decode base64 -> Uint8 -> Int16 -> Float32
    const binary = atob(b64Data);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
    const int16 = new Int16Array(bytes.buffer);
    const float32 = new Float32Array(int16.length);
    for (let j = 0; j < int16.length; j++) float32[j] = int16[j] / 32768.0;

    // Schedule playback with gapless buffering
    const audioBuffer = ctx.createBuffer(1, float32.length, 24000);
    audioBuffer.getChannelData(0).set(float32);
    const sourceNode = ctx.createBufferSource();
    sourceNode.buffer = audioBuffer;
    sourceNode.connect(ctx.destination);

    const now = ctx.currentTime;
    if (nextPlayTimeRef.current < now) nextPlayTimeRef.current = now + 0.01;
    sourceNode.start(nextPlayTimeRef.current);
    nextPlayTimeRef.current += audioBuffer.duration;

    setState(prev => ({ ...prev, speaking: true }));
    sourceNode.onended = () => setState(prev => ({ ...prev, speaking: false }));
}, [ensurePlayContext]);
```

Key detail: `nextPlayTimeRef` maintains a running playback schedule so audio chunks are played back gaplessly. Each chunk is scheduled to start immediately after the previous one ends.

### Speech Recognition / Synthesis (Claude Mode)

```typescript
// STT: Web Speech API
const startSpeechRecognition = useCallback(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onresult = (event) => {
        const last = event.results[event.results.length - 1];
        if (last.isFinal) {
            const text = last[0].transcript.trim();
            if (text) {
                addTranscript('user', text);
                ws.send(JSON.stringify({ type: 'text', text }));
            }
        }
    };

    // Auto-restart on end if still connected in claude mode
    recognition.onend = () => {
        if (connected && mode === 'claude') {
            try { recognition.start(); } catch (_) {}
        }
    };

    recognition.start();
}, []);

// TTS: SpeechSynthesis API
const speakText = useCallback((text: string) => {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.1;
    utterance.pitch = 1.0;
    setState(prev => ({ ...prev, speaking: true }));
    utterance.onend = () => setState(prev => ({ ...prev, speaking: false }));
    window.speechSynthesis.speak(utterance);
}, []);
```

### Browser Function Execution

```typescript
const executeBrowserFunction = useCallback((name: string, args: any): any => {
    switch (name) {
        case 'navigate_page': {
            const path = args.path || args.page || '';
            const pagePaths: Record<string, string> = {
                chat: '/chat', coding: '/coding', agents: '/agents',
                playbooks: '/playbooks', workflows: '/workflows',
                'kg-studio': '/kg-studio', 'kg studio': '/kg-studio',
                experts: '/experts', builder: '/builder', studio: '/builder',
                tools: '/tools', vox: '/vox', integrations: '/integrations',
                settings: '/settings',
            };
            const resolved = pagePaths[path.toLowerCase().replace(/^\//, '')] || path;
            navigate(resolved);
            return { success: true, navigated_to: resolved };
        }
        case 'get_current_page':
            return { path: location.pathname };
        case 'get_workspace_state':
            return { page: location.pathname };
        case 'switch_model':
            return { success: true, note: 'Model switch handled by context' };
        case 'switch_theme':
            return { success: true, note: 'Theme switch handled by context' };
        case 'read_page_content': {
            const main = document.querySelector('main') || document.querySelector('.flex-1');
            const content = main?.textContent?.replace(/\s+/g, ' ').trim().slice(0, 2000) || '';
            return { success: true, page: location.pathname, content };
        }
        default:
            return { success: false, error: `Unknown browser function: ${name}` };
    }
}, [navigate, location.pathname]);
```

When the hook receives a `function_call` message with `server_handled: false`, it executes the function locally and sends the result back:

```typescript
case 'function_call': {
    if (!msg.server_handled) {
        const result = executeBrowserFunction(fnName, fnArgs);
        updateFunctionLog(fnName, result, result.success ? 'success' : 'error');
        ws.send(JSON.stringify({
            type: 'browser_function_result',
            name: fnName,
            result,
        }));
    }
    break;
}
```

### Auto-Reconnect Logic

The hook implements exponential backoff reconnection:

```typescript
const MAX_RECONNECT_ATTEMPTS = 3;
const RECONNECT_BASE_DELAY = 500; // ms

const attemptReconnect = useCallback(() => {
    if (reconnectAttemptsRef.current >= MAX_RECONNECT_ATTEMPTS) {
        addTranscript('system', 'Max reconnect attempts reached. Please reconnect manually.');
        setState(prev => ({ ...prev, reconnecting: false, connected: false }));
        return;
    }

    const attempt = reconnectAttemptsRef.current;
    const delay = RECONNECT_BASE_DELAY * Math.pow(2, attempt);
    // delay sequence: 500ms, 1000ms, 2000ms
    reconnectAttemptsRef.current = attempt + 1;

    setTimeout(() => {
        // Re-connect with saved config, passing session token for Gemini
        const ws = new WebSocket(`${WS_BASE}/ws/vox`);
        ws.onopen = () => {
            const initMsg = { type: 'start', mode, voice, model, systemPrompt };
            if (sessionTokenRef.current && mode === 'gemini') {
                initMsg.session_token = sessionTokenRef.current;
            }
            ws.send(JSON.stringify(initMsg));
        };
        ws.onclose = () => {
            if (reconnecting) attemptReconnect();
        };
    }, delay);
}, []);
```

Reconnection is triggered by:
1. The `go_away` WebSocket message from the server (Gemini session about to terminate)
2. WebSocket `onclose` event while the `reconnecting` state flag is true

The session token is saved from `go_away` messages and passed in the `start` message during reconnection, enabling Gemini Live API session resumption.

### Event System

The hook exposes a simple pub/sub event system:

```typescript
const emit = (event: string, data: any) => { /* notify all listeners */ };
const on = (event: string, fn: VoxEventCallback) => { /* register listener */ };
const off = (event: string, fn: VoxEventCallback) => { /* unregister listener */ };
```

Events emitted:
- `connected` -- `{sessionId, resumed}`
- `disconnected` -- `{}`
- `transcript` -- `VoxTranscriptEntry`
- `function_result` -- `{name, result}`
- `turn_complete` -- `{turn}`
- `error` -- `{message}`
- `async_task_started` -- `{task_id, function}`
- `async_task_complete` -- `{task_id, function, result}`

### Transcript / Function Log Management

Transcript is limited to the last 50 entries. Function log is limited to the last 30 entries:

```typescript
const addTranscript = useCallback((role, text) => {
    const entry = { role, text, timestamp: Date.now() };
    setState(prev => ({
        ...prev,
        transcript: [...prev.transcript.slice(-49), entry],
    }));
}, []);

const addFunctionLog = useCallback((name, args, serverHandled) => {
    const entry = { name, args, serverHandled, timestamp: Date.now(), status: 'pending' };
    setState(prev => ({
        ...prev,
        functionLog: [...prev.functionLog.slice(-29), entry],
        functionCount: prev.functionCount + 1,
    }));
}, []);
```

### Hook Return Value

```typescript
return {
    state,          // VoxState
    connect,        // (mode: VoxMode, config?: Partial<VoxConfig>) => void
    disconnect,     // () => void
    toggleMic,      // () => void
    sendText,       // (text: string) => void
    setVoice,       // (voice: string) => void
    on,             // (event: string, fn: VoxEventCallback) => void
    off,            // (event: string, fn: VoxEventCallback) => void
    activeTour,     // Tour | null
    clearTour,      // () => void
};
```

## 1.18 Frontend: TypeScript Interfaces

**File:** `frontend/src/types/vox.ts`

```typescript
export interface VoxState {
    connected: boolean;
    mode: 'gemini' | 'claude' | null;
    voice: string;
    speaking: boolean;
    listening: boolean;
    turnCount: number;
    functionCount: number;
    sessionId: string | null;
    transcript: VoxTranscriptEntry[];
    functionLog: VoxFunctionEntry[];
    error: string | null;
    reconnecting: boolean;
}

export interface VoxTranscriptEntry {
    role: 'user' | 'model' | 'system';
    text: string;
    timestamp: number;
}

export interface VoxFunctionEntry {
    name: string;
    args: Record<string, any>;
    result?: any;
    serverHandled: boolean;
    timestamp: number;
    status: 'pending' | 'success' | 'error';
}

export interface VoxConfig {
    voice: string;
    model: string;
    systemPrompt: string;
}

export interface VoxVoice {
    id: string;
    name: string;
    gender: string;
    style: string;
}

export type VoxMode = 'gemini' | 'claude';
```

## 1.19 Frontend: VoxOverlay Component

**File:** `frontend/src/components/VoxOverlay.tsx`

A floating pill component visible on every page. Positioned `fixed bottom-4 right-4 z-50`.

**Collapsed state:** A rounded pill button showing "VOX" with a microphone icon. If connected, shows a green pulse indicator. Width is compact (auto).

**Expanded state:** A 320px wide panel with:
- **Header:** VOX label, mode badge (Gemini/Claude), green dot, close button
- **Not connected:** Two connect buttons (Gemini Voice / Claude Voice), voice selector dropdown, description text
- **Connected:**
  - Scrollable transcript area (max-height 240px, min-height 120px)
  - Text input form with Send button
  - Stats bar: Turns count, Functions count, Speaking/Listening indicators
  - Mic toggle button, Disconnect button (red)
- **Error display:** Red text at bottom when `state.error` is set

The component uses `useVoxContext()` (a React context wrapper around `useVox`), not the hook directly.

The voice selector in VoxOverlay has a local copy of the 16 voices (abbreviated styles). It stores the voice selection in `localStorage` via `setVoice()`.

## 1.20 Frontend: VoxTourOverlay Component

**File:** `frontend/src/components/VoxTourOverlay.tsx`

The tour overlay renders three layers:
1. **Backdrop:** Full-screen semi-transparent overlay (`rgba(0,0,0,0.5)`)
2. **Spotlight cutout:** Positioned over the target element with a glowing border
3. **Tooltip:** Positioned relative to the target element (top/bottom/left/right)

### Interfaces

```typescript
export interface TourStep {
    target: string;       // CSS selector(s), comma-separated
    speech: string;       // What VOX says
    position: 'top' | 'bottom' | 'left' | 'right';
    highlight: boolean;
}

export interface Tour {
    name: string;
    description: string;
    steps: TourStep[];
}

interface VoxTourOverlayProps {
    tour: Tour | null;
    onComplete: () => void;
    onStepChange?: (step: number, speech: string) => void;
}
```

### Target Element Discovery

The component tries each comma-separated selector from `step.target` to find the target element:

```typescript
const selectors = step.target.split(',').map(s => s.trim());
let el: Element | null = null;
for (const sel of selectors) {
    try {
        el = document.querySelector(sel);
        if (el) break;
    } catch (_) { /* invalid selector */ }
}

if (el) {
    setTargetRect(el.getBoundingClientRect());
} else {
    // Fallback: center of screen
    setTargetRect(new DOMRect(
        window.innerWidth / 2 - 100,
        window.innerHeight / 2 - 50,
        200, 100
    ));
}
```

### Tooltip Positioning

The tooltip is positioned relative to the target element with 12px padding. It is clamped to the viewport to prevent overflow:

```typescript
// Clamp to viewport
if (typeof tooltipStyle.left === 'number') {
    tooltipStyle.left = Math.max(8, Math.min(tooltipStyle.left, window.innerWidth - 340));
}
if (typeof tooltipStyle.top === 'number') {
    tooltipStyle.top = Math.max(8, Math.min(tooltipStyle.top, window.innerHeight - 200));
}
```

### Navigation Controls

- **Prev** button (disabled on first step)
- **Step dots** (visual indicator of progress)
- **Next** button (becomes "Finish" on last step)
- Clicking the backdrop skips the tour

The component calls `onStepChange(stepIndex, speechText)` when the step changes, allowing the parent to trigger VOX to speak the step text.

## 1.21 Frontend: VoxPage Component

**File:** `frontend/src/pages/VoxPage.tsx`

The VoxPage is the full-page VOX control center with a mobile-first design (no sidebar). It uses a tab-based layout:

### Tabs

| Tab ID | Label | Content |
|--------|-------|---------|
| `transcript` | Chat | Scrollable transcript with chat-bubble UI, text input at bottom |
| `controls` | Controls | Mode selector (Gemini/Claude), voice grid (16 voices), model dropdown, system prompt textarea, connect/disconnect buttons, session stats |
| `log` | Log | Function call log with status indicators (OK/ERR/...) |
| `macros` | Macros | List of saved macros with Run/Delete buttons |

### Voice Grid (Controls Tab)

The 16 voices are displayed in a 2-column grid (`grid grid-cols-2 gap-1`). Each voice shows name and style. The selected voice is highlighted with the primary color. Voice selection is disabled while connected.

### Model Selector (Controls Tab)

For Gemini mode, available models:
- `gemini-2.0-flash-live-001`
- `gemini-2.5-flash-preview-native-audio-dialog`
- `gemini-2.5-flash`
- `gemini-2.5-pro`

For Claude mode, available models:
- `claude-sonnet-4-6`
- `claude-haiku-4-5-20251001`
- `claude-opus-4-6`

### Macros Tab

Fetches macros from `GET /api/vox/macros` on mount. Each macro displays:
- Name (bold)
- Trigger phrase and step count
- Run button (calls `POST /api/vox/macros/{id}/run`)
- Delete button (calls `DELETE /api/vox/macros/{id}`)

## 1.22 VOX Audio Configuration Summary

| Parameter | Value | Location |
|-----------|-------|----------|
| Mic capture sample rate | 16,000 Hz (16kHz) | `config.py: VOX_AUDIO_SAMPLE_RATE_IN` |
| Playback sample rate | 24,000 Hz (24kHz) | `config.py: VOX_AUDIO_SAMPLE_RATE_OUT` |
| Audio format (wire) | Base64-encoded PCM Int16 | `useVox.ts: sendPCMChunk()` |
| ScriptProcessor buffer size | 4,096 samples | `useVox.ts: createScriptProcessor(4096, 1, 1)` |
| Playback scheduling | Gapless via `nextPlayTimeRef` | `useVox.ts: playAudioChunk()` |
| MIME type (to Gemini) | `audio/pcm;rate=16000` | `vox_service.py: send_audio()` |
| Speech Recognition | Web Speech API, continuous, en-US | `useVox.ts: startSpeechRecognition()` |
| Speech Synthesis | SpeechSynthesisUtterance, rate=1.1, pitch=1.0 | `useVox.ts: speakText()` |

## 1.23 Complete File Reference

| File | Purpose | Lines |
|------|---------|-------|
| `backend/services/vox_service.py` | VoxSession dataclass, 16 voices, 34 function declarations, system prompt builder, VoxService class (session CRUD, audio/text/function methods) | ~665 |
| `backend/routers/vox.py` | 14 REST endpoints, WebSocket handler, Gemini receive loop, Claude text pipeline, function dispatcher (28 server-side handlers), Pydantic models | ~901 |
| `backend/services/vox_awareness.py` | SQLite awareness tracking (3 tables), context injection for system prompt | ~209 |
| `backend/services/vox_macros.py` | SQLite macro CRUD, pipe-chaining execution engine, trigger phrase matching | ~279 |
| `backend/services/vox_thermal.py` | Termux battery API integration, temperature thresholds, warning logic | ~82 |
| `backend/data/vox_tours.json` | 11 guided tour definitions with CSS selectors, speech text, positioning | ~249 |
| `frontend/src/hooks/useVox.ts` | React hook: WebSocket management, audio pipeline, STT/TTS, browser functions, auto-reconnect, awareness, events, transcript/log | ~647 |
| `frontend/src/types/vox.ts` | TypeScript interfaces: VoxState, VoxTranscriptEntry, VoxFunctionEntry, VoxConfig, VoxVoice, VoxMode | ~44 |
| `frontend/src/components/VoxOverlay.tsx` | Floating pill + expanded panel: voice selector, transcript, text input, stats, mic/disconnect controls | ~246 |
| `frontend/src/components/VoxTourOverlay.tsx` | Tour spotlight: backdrop, cutout highlight, positioned tooltip, prev/next navigation, step dots | ~237 |
| `frontend/src/pages/VoxPage.tsx` | Full-page VOX control center: 4 tabs (Chat, Controls, Log, Macros), voice grid, model selector | ~512 |
| `backend/config.py` | VOX config constants (sample rates, default voice, default model) | ~136 |

---

---

# Part 2: AI Studio / React Builder Deep Dive

The AI Studio is a full-stack React application generator with live in-browser preview. Users describe an application in natural language, and the system generates complete, runnable React code streamed in real time via SSE. Generated files are rendered instantly in a Sandpack iframe preview. Projects are persisted in SQLite with full version history, ZIP export, and three editing modes (chat, code, visual).

## 2.1 Architecture Overview

```
User types prompt
       |
       v
+------------------+     POST /api/studio/stream      +-------------------+
| StudioContext     | -------------------------------->| studio.py router  |
| (sendMessage)     |     SSE: token, studio_file,     |                   |
|                   | <---------- studio_plan, deps     | _build_user_prompt|
| Parses SSE events |                                  | -> AI provider    |
| Updates files map |                                  | _parse_file_markers|
| Updates Sandpack  |                                  | -> emit SSE events|
+------------------+                                  +-------------------+
       |                                                       |
       v                                                       v
+------------------+                                  +-------------------+
| StudioPreviewPanel|                                 | studio_service.py |
| (SandpackProvider) |                                | (SQLite CRUD)     |
| Live preview       |                                | Auto-save on done |
+------------------+                                  +-------------------+
```

### Data Flow: Generate (first message)

```
1. User types "Build a todo app with dark theme"
2. StudioContext.sendMessage() fires
3. Mode detected: files empty + no messages = "generate"
4. studioApi.streamStudio() POSTs to /api/studio/stream
5. Backend selects GENERATE_SYSTEM_PROMPT
6. Backend builds user prompt (just the raw request)
7. Backend streams tokens from Gemini or Claude
8. As tokens accumulate, _parse_file_markers() extracts completed files
9. SSE events emitted: token -> studio_plan -> studio_file (per file) -> studio_deps -> done
10. Frontend updates files state -> Sandpack re-renders live
11. On "done", backend auto-saves files to SQLite project
12. Frontend creates assistant message with collected files, plan, deps
```

### Data Flow: Refine (subsequent messages)

```
1. User types "Add a filter dropdown to the todo list"
2. StudioContext.sendMessage() fires
3. Mode detected: files exist = "refine"
4. studioApi.streamStudio() POSTs with existing files + chat history
5. Backend selects REFINE_SYSTEM_PROMPT
6. Backend builds user prompt: existing files as ### FILE blocks + user request
7. AI sees current code + request, outputs only changed files
8. Same SSE parsing pipeline applies
9. Frontend merges new files into existing files map
10. Sandpack updates only changed files
```

## 2.2 System Prompts (Verbatim)

### GENERATE_SYSTEM_PROMPT

```python
GENERATE_SYSTEM_PROMPT = """\
You are a Full-Stack React app generator.

When generating an app:
1. First, briefly describe your plan (2-3 sentences).
2. Then generate each file wrapped in markers:

### FILE: /App.js
import React from 'react';
// ... complete file content
export default App;
### END FILE

### FILE: /components/Header.js
// ... content
### END FILE

Rules:
- Use functional React components with hooks
- Use inline styles (style={{...}}) - NOT CSS classes or Tailwind
- App.js is always the entry point
- All imports should use relative paths starting with ./
- Make the app visually polished with proper spacing, colors, shadows
- Include responsive design via inline style media queries or window.innerWidth checks
- Generate complete, runnable code - no TODOs or placeholders
- IMPORTANT: Do NOT wrap file contents in markdown code fences (```). Write raw code directly after the ### FILE marker line. No ```javascript or ``` delimiters.
- If you need npm packages beyond react/react-dom, list them as:
### DEPS: {"package-name": "^version"}
"""
```

### REFINE_SYSTEM_PROMPT

```python
REFINE_SYSTEM_PROMPT = """\
You are a Full-Stack React app refiner. The user has an existing React app and wants changes.

Existing files are provided below. When refining:
1. Briefly describe what you will change (1-2 sentences).
2. Only output the files that changed, using the same marker format:

### FILE: /path/to/file.js
// complete updated content
### END FILE

Rules:
- Use functional React components with hooks
- Use inline styles (style={{...}}) - NOT CSS classes or Tailwind
- Maintain consistency with existing code style
- Generate complete file contents, not diffs
- IMPORTANT: Do NOT wrap file contents in markdown code fences (```). Write raw code directly after the ### FILE marker line. No ```javascript or ``` delimiters.
- If you need new npm packages, list them as:
### DEPS: {"package-name": "^version"}
"""
```

### Key Design Decisions in the Prompts

1. **Inline styles only** -- Sandpack does not support Tailwind out of the box, so the prompt enforces `style={{...}}` for all visual styling. This guarantees the preview renders correctly without a Tailwind build step.

2. **No markdown code fences** -- AI models frequently wrap code in triple-backtick fences. The prompt explicitly forbids this because `_parse_file_markers()` expects raw code after the `### FILE:` line. A secondary regex strip in the parser handles models that ignore this instruction.

3. **Complete files, not diffs** -- The refine prompt asks for full file contents (not unified diffs) because the system overwrites files by path. This is simpler and more reliable than applying diffs, especially with streaming.

4. **Plan before code** -- Both prompts ask the model to describe its plan first. The parser detects this as text before the first `### FILE:` marker and emits it as a `studio_plan` SSE event, which the frontend renders as a collapsible plan section.

## 2.3 File Marker Protocol

The AI output protocol uses three marker types to delineate file blocks and dependency declarations within a plain-text stream:

```
### FILE: /path/to/file.ext
<raw file content, no code fences>
### END FILE

### DEPS: {"package-name": "^version", "another": "^1.0.0"}
```

### _build_user_prompt()

This helper constructs the user message sent to the AI. In refine mode, it prepends all existing files using the same marker format so the model sees current code:

```python
def _build_user_prompt(prompt: str, files: dict | None, mode: str) -> str:
    """Build the user prompt including existing files for refine mode."""
    parts = []
    if mode == "refine" and files:
        parts.append("Here are the current project files:\n")
        for path, content in files.items():
            parts.append(f"### FILE: {path}\n{content}\n### END FILE\n")
        parts.append("\n---\n")
    parts.append(f"User request: {prompt}")
    return "\n".join(parts)
```

### _parse_file_markers()

The core parsing function that extracts structured data from accumulated streaming text. It is called on every incoming token to detect newly completed file blocks:

```python
def _parse_file_markers(text: str):
    """Extract file blocks and deps from accumulated text.

    Returns (plan_text, files_dict, deps_dict, remainder).
    - plan_text: text before the first ### FILE marker
    - files_dict: {path: content}
    - deps_dict: {package: version}
    - remainder: any trailing text after last ### END FILE that may be
      an incomplete new block (to carry forward in streaming)
    """
    files = {}
    deps = {}

    # Extract deps
    for m in re.finditer(r'### DEPS:\s*(\{[^}]+\})', text):
        try:
            deps.update(json.loads(m.group(1)))
        except json.JSONDecodeError:
            pass

    # Split on file markers
    file_pattern = re.compile(
        r'### FILE:\s*(/[^\n]+)\n(.*?)### END FILE',
        re.DOTALL,
    )

    plan_text = text
    first_file_pos = None
    for m in file_pattern.finditer(text):
        if first_file_pos is None:
            first_file_pos = m.start()
        path = m.group(1).strip()
        content = m.group(2).rstrip("\n")
        # Strip markdown code fences that AI models sometimes wrap content in
        content = re.sub(r'^```[\w]*\n?', '', content)
        content = re.sub(r'\n?```\s*$', '', content)
        files[path] = content

    if first_file_pos is not None:
        plan_text = text[:first_file_pos].strip()

    # Check for incomplete trailing block
    remainder = ""
    last_end = 0
    for m in file_pattern.finditer(text):
        last_end = m.end()
    if last_end > 0:
        trailing = text[last_end:]
        if "### FILE:" in trailing:
            remainder = trailing

    return plan_text, files, deps, remainder
```

### Regex Details

| Pattern | Purpose |
|---------|---------|
| `r'### DEPS:\s*(\{[^}]+\})'` | Matches `### DEPS:` followed by a JSON object (single line). Captures the JSON string for `json.loads()`. |
| `r'### FILE:\s*(/[^\n]+)\n(.*?)### END FILE'` (DOTALL) | Matches a file block. Group 1 = path (must start with `/`). Group 2 = content between markers (non-greedy, multiline). |
| `r'^```[\w]*\n?'` | Strips leading code fence from file content (e.g., ` ```javascript\n`). |
| `r'\n?```\s*$'` | Strips trailing code fence from file content. |

### Protocol Robustness

The parser handles several edge cases:
- **Models that add code fences**: The post-extraction regex strips them.
- **Incomplete blocks during streaming**: The `remainder` return value carries forward partial `### FILE:` blocks that have not yet received their `### END FILE` marker.
- **Multiple deps declarations**: Each `### DEPS:` line is parsed independently and merged.
- **No files in output**: If the model only outputs text (no file markers), `plan_text` contains the entire output and `files` is empty.

## 2.4 Backend Router: All 18 Endpoints

**File:** `backend/routers/studio.py`

### Main Streaming Endpoint

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/studio/stream` | SSE streaming AI generation/refinement |

**Request body:**

```json
{
  "project_id": "uuid-string | null",
  "prompt": "Build a todo app",
  "files": {"path": "content", ...},
  "chat_history": [{"role": "user", "content": "..."}, ...],
  "provider": "gemini | claude",
  "model": "gemini-2.5-flash | claude-sonnet-4-6 | ...",
  "mode": "generate | refine"
}
```

**SSE event types emitted:**

| Event type | Payload | When |
|------------|---------|------|
| `token` | `{type: "token", content: "..."}` | Every token from AI stream |
| `studio_plan` | `{type: "studio_plan", content: "..."}` | Text before first file marker detected |
| `studio_file` | `{type: "studio_file", path: "/App.js", content: "..."}` | Each completed file block |
| `studio_deps` | `{type: "studio_deps", dependencies: {...}}` | Each new dependency block |
| `done` | `{type: "done"}` | Stream complete |
| `error` | `{type: "error", content: "..."}` | Error occurred |

**The generate() inner function (verbatim):**

```python
async def generate():
    accumulated = ""
    emitted_files = set()
    emitted_deps = {}
    plan_emitted = False

    try:
        # Choose provider
        if provider == "claude" and MODE == "standalone" and ANTHROPIC_API_KEY:
            target_model = model or "claude-sonnet-4-6"
            stream = claude_service.stream_chat(
                messages=messages,
                model=target_model,
                system=system_prompt,
                max_tokens=16384,
                temperature=0.7,
            )
        else:
            target_model = model or "gemini-2.5-flash"
            stream = gemini_service.stream_chat(
                messages=messages,
                model=target_model,
                system_instruction=system_prompt,
                temperature=0.7,
            )

        async for chunk in stream:
            if chunk.get("type") == "token":
                token_text = chunk["content"]
                accumulated += token_text

                # Emit raw token for chat display
                yield f"data: {json.dumps({'type': 'token', 'content': token_text})}\n\n"

                # Parse accumulated text for completed file blocks
                plan_text, parsed_files, parsed_deps, _ = _parse_file_markers(accumulated)

                # Emit plan (text before first file marker)
                if not plan_emitted and plan_text and parsed_files:
                    yield f"data: {json.dumps({'type': 'studio_plan', 'content': plan_text})}\n\n"
                    plan_emitted = True

                # Emit newly completed files
                for path, content in parsed_files.items():
                    if path not in emitted_files:
                        emitted_files.add(path)
                        yield f"data: {json.dumps({'type': 'studio_file', 'path': path, 'content': content})}\n\n"

                # Emit new deps
                for pkg, ver in parsed_deps.items():
                    if pkg not in emitted_deps:
                        emitted_deps[pkg] = ver
                        yield f"data: {json.dumps({'type': 'studio_deps', 'dependencies': {pkg: ver}})}\n\n"

            elif chunk.get("type") == "done":
                # Final parse pass -- catch any remaining blocks
                plan_text, parsed_files, parsed_deps, _ = _parse_file_markers(accumulated)

                if not plan_emitted and plan_text:
                    yield f"data: {json.dumps({'type': 'studio_plan', 'content': plan_text})}\n\n"

                for path, content in parsed_files.items():
                    if path not in emitted_files:
                        emitted_files.add(path)
                        yield f"data: {json.dumps({'type': 'studio_file', 'path': path, 'content': content})}\n\n"

                for pkg, ver in parsed_deps.items():
                    if pkg not in emitted_deps:
                        emitted_deps[pkg] = ver
                        yield f"data: {json.dumps({'type': 'studio_deps', 'dependencies': {pkg: ver}})}\n\n"

                # Auto-save files to project if we have a project_id
                if project_id and parsed_files:
                    try:
                        project = studio_service.get_project(project_id)
                        if project:
                            existing_files = project.get("files") or {}
                            if isinstance(existing_files, str):
                                existing_files = json.loads(existing_files)
                            existing_files.update(parsed_files)
                            studio_service.update_project(project_id, {
                                "files": existing_files,
                            })
                    except Exception:
                        pass  # Non-critical: don't break the stream

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
```

**Key implementation details:**

- `accumulated` grows as tokens arrive; `_parse_file_markers()` is called on every token to detect newly completed file blocks.
- `emitted_files` and `emitted_deps` sets prevent duplicate emissions.
- The plan is emitted only once, when the first file is also detected (ensuring the plan text is fully accumulated).
- On the `done` event from the underlying AI stream, a final parse pass catches any remaining blocks.
- Auto-save to SQLite is non-critical -- wrapped in try/except to avoid breaking the stream.
- Chat history is trimmed to the last 10 messages to stay within context windows.
- Default model is `gemini-2.5-flash` for Gemini, `claude-sonnet-4-6` for Claude.
- Temperature is set to 0.7 for creative generation.
- Max tokens for Claude is 16384.

### Project CRUD Endpoints

| Method | Path | Handler | Request | Response |
|--------|------|---------|---------|----------|
| POST | `/api/studio/projects` | `create_project()` | `{name, description}` | Full project object |
| GET | `/api/studio/projects` | `list_projects()` | -- | Array of project summaries |
| GET | `/api/studio/projects/{id}` | `get_project()` | -- | Full project + parsed JSON columns + versions |
| PUT | `/api/studio/projects/{id}` | `update_project()` | `{name?, description?, files?, chat_history?, settings?}` | `{status: "ok"}` |
| DELETE | `/api/studio/projects/{id}` | `delete_project()` | -- | `{status: "deleted"}` |

**Notes on get_project():**

The router-level handler adds extra processing beyond the service call:
- Parses `files`, `chat_history`, and `settings` from JSON strings if the service returned them as strings (defensive, since `_row_to_dict` already handles this).
- Appends `versions` list by calling `studio_service.list_versions(project_id)`.

**Notes on update_project():**

The router serializes `files`, `chat_history`, and `settings` to JSON strings before passing to the service, if they are dicts/lists.

### Version Management Endpoints

| Method | Path | Handler | Request | Response |
|--------|------|---------|---------|----------|
| POST | `/api/studio/projects/{id}/save` | `save_version()` | `{message: "Manual save"}` | Version object |
| GET | `/api/studio/projects/{id}/versions` | `list_versions()` | -- | Array of version summaries |
| GET | `/api/studio/projects/{id}/versions/{ver}` | `get_version()` | -- | Version object with parsed files |
| POST | `/api/studio/projects/{id}/versions/{ver}/restore` | `restore_version()` | -- | `{status: "restored", version: N}` |

### Mock Server Stubs

These endpoints exist but are not yet implemented. They return placeholder responses:

| Method | Path | Handler | Response |
|--------|------|---------|----------|
| POST | `/api/studio/projects/{id}/mock/start` | `start_mock()` | `{running: false, message: "Mock server not yet implemented"}` |
| POST | `/api/studio/projects/{id}/mock/stop` | `stop_mock()` | `{running: false}` |
| GET | `/api/studio/projects/{id}/mock/status` | `mock_status()` | `{running: false, port: null, pid: null}` |
| POST | `/api/studio/projects/{id}/mock/update` | `update_mock()` | `{running: false, message: "Mock server not yet implemented"}` |

### OpenAPI Spec and TypeScript Types Endpoints

| Method | Path | Handler | Purpose |
|--------|------|---------|---------|
| GET | `/api/studio/projects/{id}/api-spec` | `get_api_spec()` | Extract OpenAPI spec from Python/FastAPI files in the project |
| GET | `/api/studio/projects/{id}/types` | `get_ts_types()` | Generate TypeScript interfaces from the OpenAPI spec |

Both endpoints scan the project's files for `.py` files, run them through `openapi_extractor.extract_openapi_from_code()`, and combine the results. The types endpoint additionally calls `type_generator.generate_typescript_types()`.

### Export Endpoint

| Method | Path | Handler | Query Params | Response |
|--------|------|---------|--------------|----------|
| GET | `/api/studio/projects/{id}/export` | `export_project()` | `scope=all\|frontend\|backend` | ZIP file download |

## 2.5 Backend Service: SQLite Schema and CRUD

**File:** `backend/services/studio_service.py`

**Database path:** `backend/studio_projects.db`

### SQLite Schema

```sql
CREATE TABLE IF NOT EXISTS studio_projects (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL DEFAULT 'Untitled Project',
    description     TEXT NOT NULL DEFAULT '',
    settings        TEXT NOT NULL DEFAULT '{}',
    files           TEXT NOT NULL DEFAULT '{}',
    chat_history    TEXT NOT NULL DEFAULT '[]',
    current_version INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS studio_versions (
    id              TEXT PRIMARY KEY,
    project_id      TEXT NOT NULL,
    version_number  INTEGER NOT NULL,
    files           TEXT NOT NULL DEFAULT '{}',
    message         TEXT NOT NULL DEFAULT '',
    timestamp       TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES studio_projects(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_versions_project
    ON studio_versions(project_id, version_number);
```

**Key design decisions:**
- `files`, `chat_history`, and `settings` are stored as JSON TEXT columns.
- `current_version` is an incrementing integer on the project row.
- Versions reference projects via foreign key with CASCADE delete.
- The index on `(project_id, version_number)` optimizes version lookups.
- WAL journal mode is enabled for concurrent read performance.
- Foreign keys are explicitly enabled (`PRAGMA foreign_keys=ON`).

### Database Helpers

```python
DB_PATH = Path(__file__).parent.parent / "studio_projects.db"

def _get_conn() -> sqlite3.Connection:
    """Return a connection with row_factory set to sqlite3.Row."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

_JSON_COLUMNS = {"settings", "files", "chat_history"}

def _row_to_dict(row: sqlite3.Row | None) -> dict | None:
    """Convert a sqlite3.Row to a plain dict, parsing JSON columns."""
    if row is None:
        return None
    d = dict(row)
    for col in _JSON_COLUMNS:
        if col in d and isinstance(d[col], str):
            try:
                d[col] = json.loads(d[col])
            except (json.JSONDecodeError, TypeError):
                pass
    return d
```

### Service Methods

**create_project(name, description) -> dict**

Generates a UUID, inserts a row with empty files/chat/settings, returns the full project dict.

**list_projects() -> list[dict]**

Returns summaries (id, name, description, current_version, created_at, updated_at) ordered by `updated_at DESC`. Includes a `file_count` computed by parsing the `files` JSON column.

**get_project(project_id) -> dict | None**

Returns the full project row with JSON columns auto-parsed by `_row_to_dict()`.

**update_project(project_id, data) -> bool**

Updates only whitelisted fields (`name`, `description`, `settings`, `files`, `chat_history`, `current_version`). Automatically JSON-serializes dict/list values. Always updates `updated_at`.

**delete_project(project_id) -> bool**

Explicitly deletes versions first (belt and suspenders with CASCADE), then deletes the project row.

**save_version(project_id, message) -> dict**

1. Reads current `files` and `current_version` from the project.
2. Increments version number.
3. Inserts a new `studio_versions` row with the current files snapshot.
4. Updates `current_version` on the project.
5. Returns the version metadata.

**list_versions(project_id) -> list[dict]**

Returns version summaries (without file content) ordered by `version_number DESC`.

**get_version(project_id, version_number) -> dict | None**

Returns a specific version snapshot including files.

**restore_version(project_id, version_number) -> dict**

This is a non-destructive restore:
1. Reads the target version's files.
2. Reads the current project state.
3. **Auto-saves the current state** as a new version with message `"Auto-save before restoring v{N}"`.
4. Copies the target version's files back to the project.
5. Bumps `current_version` by 2 (one for auto-save, one for restore).
6. Returns the updated project.

This ensures you can always undo a restore by looking at the auto-saved version.

**export_project_zip(project_id, scope) -> bytes | None**

```python
def export_project_zip(project_id: str, scope: str = "all") -> bytes | None:
    """Generate a ZIP archive of project files. Returns bytes or None."""
    # ...
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for path, file_data in files.items():
            content = file_data["content"] if isinstance(file_data, dict) else file_data
            clean_path = path.lstrip("/")

            # Scope filtering
            if scope == "frontend":
                frontend_prefixes = (
                    "src/", "public/", "App", "index", "package",
                    "components/", "hooks/", "utils/", "styles/",
                )
                if not any(clean_path.startswith(p) or clean_path == p for p in frontend_prefixes):
                    if not clean_path.endswith((".js", ".jsx", ".ts", ".tsx", ".json", ".html", ".css")):
                        continue
            elif scope == "backend":
                backend_prefixes = ("api/", "server/", "backend/", "routes/", "models/", "services/")
                if not any(clean_path.startswith(p) for p in backend_prefixes):
                    if not clean_path.endswith(".py"):
                        continue

            archive_path = f"{project_name}/{clean_path}"
            zf.writestr(archive_path, content)

        # Add a basic package.json if not present
        if "package.json" not in files and "/package.json" not in files:
            pkg = {
                "name": project_name,
                "version": "0.1.0",
                "private": True,
                "dependencies": {
                    "react": "^18.2.0",
                    "react-dom": "^18.2.0",
                },
            }
            zf.writestr(f"{project_name}/package.json", json.dumps(pkg, indent=2))

    return buf.getvalue()
```

Scope filtering:
- `"all"`: Include everything.
- `"frontend"`: Include files under `src/`, `public/`, `components/`, `hooks/`, `utils/`, `styles/`, files starting with `App`, `index`, `package`, and any root-level web file extensions.
- `"backend"`: Include files under `api/`, `server/`, `backend/`, `routes/`, `models/`, `services/`, and any `.py` files.

If no `package.json` exists in the project, a minimal one is auto-generated.

## 2.6 TypeScript Interfaces

**File:** `frontend/src/types/studio.ts`

```typescript
export type StudioMode = 'chat' | 'code' | 'visual';

export interface StudioFile {
  path: string;
  content: string;
  language?: string;
  isEntry?: boolean;
}

export interface StudioProject {
  id: string;
  name: string;
  description: string;
  settings: StudioProjectSettings;
  files: Record<string, StudioFile>;
  chatHistory: StudioMessage[];
  currentVersion: number;
  createdAt: string;
  updatedAt: string;
}

export interface StudioProjectSettings {
  techStack: 'react' | 'react-ts';
  cssFramework: 'tailwind' | 'css' | 'none';
  hasBackend: boolean;
  backendFramework?: 'fastapi' | 'express';
  dependencies: Record<string, string>;
}

export interface StudioVersion {
  id: string;
  projectId: string;
  versionNumber: number;
  files: Record<string, StudioFile>;
  message: string;
  timestamp: string;
}

export interface StudioMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  files?: StudioFileChange[];
  plan?: string;
  apiSpec?: StudioApiSpec | null;
  deps?: Record<string, string>;
}

export interface StudioFileChange {
  path: string;
  content: string;
  action: 'create' | 'update' | 'delete';
}

export interface StudioApiSpec {
  openapi: string;
  info: { title: string; version: string };
  paths: Record<string, any>;
  components?: { schemas?: Record<string, any> };
}

export interface StudioApiEndpoint {
  method: string;
  path: string;
  summary?: string;
  parameters?: any[];
  requestBody?: any;
  responses?: Record<string, any>;
}

export interface StudioMockServerStatus {
  running: boolean;
  port?: number;
  pid?: number;
  endpoints?: StudioApiEndpoint[];
}

export interface StudioSelection {
  componentName: string;
  elementTag: string;
  filePath: string;
  lineNumber?: number;
  props?: Record<string, any>;
  styles?: Record<string, string>;
  text?: string;
}

export interface StudioEditorTab {
  path: string;
  isDirty: boolean;
}

export interface StudioStreamEvent {
  type: 'token' | 'thinking' | 'studio_plan' | 'studio_file' | 'studio_deps' | 'studio_api_spec' | 'done' | 'error';
  content?: string;
  path?: string;
  file_content?: string;
  deps?: Record<string, string>;
  api_spec?: StudioApiSpec;
}

export interface StudioProjectSummary {
  id: string;
  name: string;
  description: string;
  updatedAt: string;
  fileCount: number;
  versionCount: number;
}
```

## 2.7 Three Editing Modes

The Studio supports three editing modes, each with a distinct panel layout:

### Chat Mode (default)

```
+----------------+-------------------+-------------+
| StudioChatPanel| StudioPreviewPanel| StudioFiles |
| (AI chat)      | (Sandpack iframe) | Panel       |
|                |                   | (file tree) |
+----------------+-------------------+-------------+
```

- User types prompts in the chat panel.
- AI generates/refines files.
- Preview updates live as files are emitted.
- File tree shows current project files.

### Code Mode

```
+-------------+-------------------+-------------------+
| StudioFiles | StudioCodeEditor  | StudioPreviewPanel|
| Panel       | (Monaco-like)     | (Sandpack iframe) |
| (file tree) | (tabbed editor)   |                   |
+-------------+-------------------+-------------------+
```

- File tree on the left for navigation.
- Tabbed code editor in the center (with dirty indicators).
- Live preview on the right.
- Direct code editing with immediate preview updates.

### Visual Mode

```
+----------------+-------------------+-------------+
| StudioChatPanel| StudioVisualMode  | StudioFiles |
| (AI chat)      | (visual editor)   | Panel       |
|                |                   | (file tree) |
+----------------+-------------------+-------------+
```

- Visual editor in the center for component inspection.
- Uses `StudioSelection` interface for element targeting.
- Includes `StudioElementInspector`, `StudioComponentTree`, and `StudioSelectionOverlay`.

### Mode Switching

Mode is stored in `StudioContext.mode` and switched via `StudioToolbar`. The `StudioPage` renders a different `StudioLayout` configuration for each mode:

```typescript
const renderByMode = () => {
    switch (mode) {
      case 'chat':
        return (
          <StudioLayout
            left={<StudioChatPanel />}
            center={<StudioPreviewPanel />}
            right={<StudioFilesPanel />}
          />
        );
      case 'code':
        return (
          <StudioLayout
            left={<StudioFilesPanel />}
            center={<StudioCodeEditor />}
            right={<StudioPreviewPanel />}
          />
        );
      case 'visual':
        return (
          <StudioLayout
            left={<StudioChatPanel />}
            center={<StudioVisualMode />}
            right={<StudioFilesPanel />}
          />
        );
    }
};
```

## 2.8 Sandpack Preview Panel

**File:** `frontend/src/components/studio/StudioPreviewPanel.tsx`

The preview panel wraps `@codesandbox/sandpack-react` to render generated React code in an iframe.

### Full Component (Verbatim)

```tsx
import React, { useMemo, useState } from 'react';
import {
  SandpackProvider,
  SandpackLayout,
  SandpackPreview,
  SandpackConsole,
} from '@codesandbox/sandpack-react';
import { useStudio } from '../../context/StudioContext';

const StudioPreviewPanel: React.FC = () => {
  const { files, mode } = useStudio();
  const [showConsole, setShowConsole] = useState(false);

  // Convert studio files to Sandpack file format
  const sandpackFiles = useMemo(() => {
    const result: Record<string, { code: string; active?: boolean }> = {};

    const fileEntries = Object.entries(files);
    if (fileEntries.length === 0) {
      // Default empty state
      result['/App.js'] = {
        code: `export default function App() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center',
                  height: '100vh', fontFamily: 'system-ui', color: '#888',
                  background: '#111827' }}>
      <div style={{ textAlign: 'center' }}>
        <h2 style={{ color: '#0ea5e9', marginBottom: 8 }}>Studio Preview</h2>
        <p>Describe your app in the chat to get started</p>
      </div>
    </div>
  );
}`,
        active: true,
      };
      return result;
    }

    for (const [path, file] of fileEntries) {
      const sandpackPath = path.startsWith('/') ? path : `/${path}`;
      result[sandpackPath] = { code: file.content };
    }

    // Ensure we have an entry point
    if (!result['/App.js'] && !result['/App.tsx'] && !result['/App.jsx']) {
      if (result['/src/App.tsx']) {
        // Already has src structure
      } else if (result['/src/App.js']) {
        // ok
      } else {
        result['/App.js'] = {
          code: `export default function App() {
  return <div>Preview loading...</div>;
}`,
        };
      }
    }

    return result;
  }, [files]);

  // Compute dependencies from files
  const customDeps = useMemo(() => {
    const deps: Record<string, string> = {};
    const pkgFile = files['package.json'] || files['/package.json'];
    if (pkgFile) {
      try {
        const pkg = JSON.parse(pkgFile.content);
        if (pkg.dependencies) {
          Object.assign(deps, pkg.dependencies);
        }
      } catch {}
    }
    return deps;
  }, [files]);

  // ... render JSX (see below)
};
```

### File Conversion Logic

Studio files are `Record<string, StudioFile>` where `StudioFile = {path, content, language}`. Sandpack expects `Record<string, {code: string; active?: boolean}>`. The conversion:

1. If no files exist, renders a placeholder App.js with a "describe your app" message.
2. Paths are normalized to start with `/` (Sandpack requirement).
3. Entry point detection: checks for `/App.js`, `/App.tsx`, `/App.jsx`, `/src/App.tsx`, `/src/App.js`. If none found, creates a fallback `/App.js`.
4. Dependencies are extracted from `package.json` if present in files.

### Dark Theme Configuration

The Sandpack theme is a custom dark theme matching the workspace aesthetic:

```typescript
theme={{
  colors: {
    surface1: '#111827',    // bg-gray-900
    surface2: '#1f2937',    // bg-gray-800
    surface3: '#374151',    // bg-gray-700
    clickable: '#6b7280',   // text-gray-500
    base: '#f1f5f9',        // text-slate-100
    disabled: '#374151',
    hover: '#0ea5e9',       // sky-500
    accent: '#0ea5e9',      // sky-500
    error: '#ef4444',       // red-500
    errorSurface: '#7f1d1d',// red-900
  },
  syntax: {
    plain: '#f1f5f9',
    comment: { color: '#6b7280', fontStyle: 'italic' },
    keyword: '#c084fc',     // purple-400
    tag: '#22c55e',         // green-500
    punctuation: '#6b7280',
    definition: '#38bdf8',  // sky-400
    property: '#fbbf24',    // amber-400
    static: '#f472b6',      // pink-400
    string: '#a5f3fc',      // cyan-200
  },
  font: {
    body: "system-ui, -apple-system, sans-serif",
    mono: "'Menlo', 'Monaco', 'Courier New', monospace",
    size: '13px',
    lineHeight: '1.5',
  },
}}
```

### CSS Height Hack

Sandpack components set their own max-height, which prevents them from filling the available space. The panel uses absolute positioning and `!important` CSS overrides to force full-height rendering:

```css
.studio-sandpack-wrapper,
.studio-sandpack-wrapper > .sp-wrapper,
.studio-sandpack-wrapper > div {
  height: 100% !important;
  display: flex !important;
  flex-direction: column !important;
}
.studio-sandpack-wrapper .sp-layout {
  flex: 1 !important;
  height: 100% !important;
  max-height: none !important;
  border: none !important;
  border-radius: 0 !important;
  display: flex !important;
  flex-direction: column !important;
}
.studio-sandpack-wrapper .sp-stack {
  flex: 1 !important;
  height: 100% !important;
  max-height: none !important;
}
.studio-sandpack-wrapper .sp-preview-container {
  flex: 1 !important;
  height: 100% !important;
  max-height: none !important;
}
.studio-sandpack-wrapper .sp-preview-iframe {
  height: 100% !important;
  min-height: 0 !important;
}
.studio-sandpack-wrapper .sp-preview-actions {
  z-index: 10;
}
```

This is injected as a `<style>` element inside the component. The wrapper uses `position: absolute; inset: 0;` on the parent to establish a full-size containing block.

### Recompile Settings

```typescript
options={{
  recompileMode: 'delayed',
  recompileDelay: 500,  // 500ms debounce
}}
```

Sandpack waits 500ms after the last file change before recompiling, preventing excessive recompiles during streaming when files are being emitted rapidly.

### Console Toggle

A small "Console" button in the header toggles `SandpackConsole` visibility, useful for debugging `console.log` output from generated code.

## 2.9 StudioContext: State Management

**File:** `frontend/src/context/StudioContext.tsx`

The `StudioContext` provides all Studio state and operations to child components via React Context.

### Context Interface (StudioContextType)

| Category | Fields/Methods | Type |
|----------|---------------|------|
| **Mode** | `mode`, `setMode` | `StudioMode`, setter |
| **Project** | `project`, `projectList`, `isLoading`, `isDirty` | State fields |
| **Files** | `files`, `setFiles`, `updateFile`, `addFile`, `deleteFile`, `renameFile` | File CRUD |
| **Chat** | `messages`, `streamingText`, `streamingPlan`, `isStreaming`, `sendMessage`, `clearChat` | Chat state + streaming |
| **Project Ops** | `createProject`, `loadProject`, `saveProject`, `deleteProject`, `loadProjectList`, `closeProject` | CRUD wrappers |
| **Versions** | `versions`, `loadVersions`, `restoreVersion` | Version management |
| **API/Mock** | `apiSpec`, `mockServerStatus`, `startMockServer`, `stopMockServer` | API panel state |
| **Editor** | `openTabs`, `activeTab`, `openFile`, `closeTab`, `setActiveTab` | Tab management |
| **Visual** | `selectedElement`, `setSelectedElement` | Visual mode selection |
| **Provider** | `provider`, `model`, `setProvider`, `setModel` | AI provider config |

### sendMessage() Implementation (Verbatim)

```typescript
const sendMessage = useCallback(async (prompt: string) => {
    if (isStreaming) return;

    const userMsg: StudioMessage = {
      id: generateUniqueId(),
      role: 'user',
      content: prompt,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMsg]);
    setIsStreaming(true);
    setStreamingText('');
    setStreamingPlan('');

    try {
      const isFirstMessage = Object.keys(files).length === 0 && messages.length === 0;
      const chatHistory = [...messages, userMsg].map(m => ({
        role: m.role,
        content: m.content,
      }));

      const stream = await studioApi.streamStudio(
        project?.id || null,
        prompt,
        files,
        chatHistory,
        provider,
        model,
        isFirstMessage ? 'generate' : 'refine',
      );

      const reader = stream.getReader();
      const decoder = new TextDecoder();
      let accText = '';
      let accPlan = '';
      const collectedFiles: StudioFileChange[] = [];
      let collectedDeps: Record<string, string> = {};
      let collectedApiSpec: StudioApiSpec | null = null;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n').filter(l => l.startsWith('data: '));

        for (const line of lines) {
          try {
            const data = JSON.parse(line.slice(6));

            switch (data.type) {
              case 'token':
                accText += data.content;
                setStreamingText(accText);
                break;

              case 'thinking':
                break; // Silently consume thinking tokens

              case 'studio_plan':
                accPlan = data.content || '';
                setStreamingPlan(accPlan);
                break;

              case 'studio_file': {
                const filePath = data.path;
                const fileContent = data.file_content || data.content || '';
                collectedFiles.push({ path: filePath, content: fileContent, action: 'create' });
                // Immediately update Sandpack files
                setFiles(prev => ({
                  ...prev,
                  [filePath]: { path: filePath, content: fileContent, language: guessLanguage(filePath) },
                }));
                break;
              }

              case 'studio_deps':
                collectedDeps = { ...collectedDeps, ...(data.deps || data.content || {}) };
                break;

              case 'studio_api_spec':
                collectedApiSpec = data.api_spec || data.content || null;
                if (collectedApiSpec) setApiSpec(collectedApiSpec);
                break;

              case 'error':
                accText += `\n\nError: ${data.content}`;
                setStreamingText(accText);
                break;

              case 'done':
                break;
            }
          } catch {
            // Skip malformed lines
          }
        }
      }

      // Add assistant message
      const assistantMsg: StudioMessage = {
        id: generateUniqueId(),
        role: 'assistant',
        content: accText,
        timestamp: new Date().toISOString(),
        files: collectedFiles.length > 0 ? collectedFiles : undefined,
        plan: accPlan || undefined,
        apiSpec: collectedApiSpec,
        deps: Object.keys(collectedDeps).length > 0 ? collectedDeps : undefined,
      };
      setMessages(prev => [...prev, assistantMsg]);
      setIsDirty(true);

    } catch (err: any) {
      const errorMsg: StudioMessage = {
        id: generateUniqueId(),
        role: 'system',
        content: `Error: ${err.message}`,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsStreaming(false);
      setStreamingText('');
      setStreamingPlan('');
    }
  }, [isStreaming, files, messages, project, provider, model]);
```

**Key implementation details:**

1. **Mode auto-detection**: `isFirstMessage` is determined by `files.length === 0 && messages.length === 0`. First message uses "generate" mode; subsequent messages use "refine" mode.

2. **Immediate file updates**: When a `studio_file` event arrives, `setFiles` is called immediately, which causes `StudioPreviewPanel` to re-render the Sandpack preview with the new file content. This gives real-time visual feedback.

3. **SSE parsing**: The ReadableStream is read chunk by chunk with `TextDecoder`. Lines starting with `data: ` are parsed as JSON. The `line.slice(6)` strips the `data: ` prefix.

4. **Error resilience**: Malformed SSE lines are silently skipped. Network errors are caught and displayed as system messages.

5. **Thinking tokens**: The `thinking` event type is consumed but not displayed (used by some models for chain-of-thought).

### guessLanguage() Utility

```typescript
function guessLanguage(path: string): string {
  const ext = path.split('.').pop()?.toLowerCase() || '';
  const map: Record<string, string> = {
    tsx: 'typescript', ts: 'typescript', jsx: 'javascript', js: 'javascript',
    css: 'css', html: 'html', json: 'json', md: 'markdown', py: 'python',
    sql: 'sql', yaml: 'yaml', yml: 'yaml', txt: 'text',
  };
  return map[ext] || 'text';
}
```

## 2.10 API Client: studioApiService

**File:** `frontend/src/services/studioApiService.ts`

### mapProject() Response Mapper

The backend returns snake_case keys and may store files as plain strings or objects. The mapper normalizes this:

```typescript
function mapProject(raw: any): StudioProject {
  const rawFiles = raw.files || {};
  const mappedFiles: Record<string, any> = {};
  for (const [path, value] of Object.entries(rawFiles)) {
    if (typeof value === 'string') {
      mappedFiles[path] = { path, content: value, language: guessLang(path) };
    } else if (value && typeof value === 'object') {
      const v = value as any;
      mappedFiles[path] = { path: v.path || path, content: v.content || '', language: v.language || guessLang(path) };
    }
  }

  return {
    id: raw.id,
    name: raw.name,
    description: raw.description || '',
    settings: raw.settings || {},
    files: mappedFiles,
    chatHistory: raw.chat_history || raw.chatHistory || [],
    currentVersion: raw.current_version ?? raw.currentVersion ?? 0,
    createdAt: raw.created_at || raw.createdAt || '',
    updatedAt: raw.updated_at || raw.updatedAt || '',
  };
}
```

**File format normalization**: The backend may return `files` as `{"/App.js": "code..."}` (string values) or `{"/App.js": {path, content, language}}` (object values). The mapper handles both, ensuring the frontend always gets `StudioFile` objects.

**Field name normalization**: Handles both `snake_case` (from backend) and `camelCase` (from cached frontend data) using fallback patterns like `raw.chat_history || raw.chatHistory || []`.

### streamStudio() Client

```typescript
export const streamStudio = async (
  projectId: string | null,
  prompt: string,
  files: Record<string, { path: string; content: string }>,
  chatHistory: any[],
  provider: 'gemini' | 'claude',
  model: string,
  mode: 'generate' | 'refine',
): Promise<ReadableStream<Uint8Array>> => {
  const response = await fetch(`${BASE}/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      project_id: projectId, prompt, files,
      chat_history: chatHistory, provider, model, mode
    }),
  });
  if (!response.ok || !response.body) {
    const err = await response.json().catch(() => ({ message: 'Studio stream failed' }));
    throw new Error(err.message || err.detail || 'Failed to get studio response');
  }
  return response.body;
};
```

Returns the raw `ReadableStream<Uint8Array>` from `response.body`. The caller (StudioContext.sendMessage) is responsible for reading and parsing SSE events.

### All Client Methods

| Function | Method | Path | Returns |
|----------|--------|------|---------|
| `streamStudio()` | POST | `/api/studio/stream` | `ReadableStream<Uint8Array>` |
| `createProject()` | POST | `/api/studio/projects` | `StudioProject` |
| `listProjects()` | GET | `/api/studio/projects` | `StudioProjectSummary[]` |
| `getProject()` | GET | `/api/studio/projects/{id}` | `StudioProject` |
| `updateProject()` | PUT | `/api/studio/projects/{id}` | `StudioProject` |
| `deleteProject()` | DELETE | `/api/studio/projects/{id}` | `void` |
| `saveVersion()` | POST | `/api/studio/projects/{id}/save` | `StudioVersion` |
| `listVersions()` | GET | `/api/studio/projects/{id}/versions` | `StudioVersion[]` |
| `getVersion()` | GET | `/api/studio/projects/{id}/versions/{ver}` | `StudioVersion` |
| `restoreVersion()` | POST | `/api/studio/projects/{id}/versions/{ver}/restore` | `StudioProject` |
| `startMockServer()` | POST | `/api/studio/projects/{id}/mock/start` | `StudioMockServerStatus` |
| `stopMockServer()` | POST | `/api/studio/projects/{id}/mock/stop` | `void` |
| `getMockServerStatus()` | GET | `/api/studio/projects/{id}/mock/status` | `StudioMockServerStatus` |
| `updateMockServer()` | POST | `/api/studio/projects/{id}/mock/update` | `StudioMockServerStatus` |
| `getApiSpec()` | GET | `/api/studio/projects/{id}/api-spec` | `StudioApiSpec \| null` |
| `getGeneratedTypes()` | GET | `/api/studio/projects/{id}/types` | `string` |
| `exportProject()` | GET | `/api/studio/projects/{id}/export?scope=` | `Blob` |

## 2.11 Frontend Component Inventory

**24 Studio components** in `frontend/src/components/studio/`:

| Component | File | Purpose | Approx Lines |
|-----------|------|---------|-------------|
| `StudioLayout` | StudioLayout.tsx | 3-panel resizable layout (left/center/right) | ~60 |
| `StudioToolbar` | StudioToolbar.tsx | Top bar: project name, mode tabs (Chat/Code/Visual), save, provider/model selectors | ~120 |
| `StudioChatPanel` | StudioChatPanel.tsx | Chat interface: message list, input area, streaming indicator | ~150 |
| `StudioMessageItem` | StudioMessageItem.tsx | Single chat message: markdown rendering, file change badges, plan collapsible | ~100 |
| `StudioFilesPanel` | StudioFilesPanel.tsx | File tree: list of project files, click to open in code editor, new file button | ~80 |
| `StudioCodeEditor` | StudioCodeEditor.tsx | Tabbed code editor: syntax-highlighted textarea, tab bar, file content editing | ~130 |
| `StudioEditorTabs` | StudioEditorTabs.tsx | Editor tab bar: active tab highlight, dirty indicator dots, close buttons | ~60 |
| `StudioPreviewPanel` | StudioPreviewPanel.tsx | Sandpack live preview: SandpackProvider + SandpackPreview + console toggle | ~207 |
| `StudioNewFileDialog` | StudioNewFileDialog.tsx | Modal dialog for creating new files: path input, language selector | ~70 |
| `StudioDiffView` | StudioDiffView.tsx | Side-by-side diff view for comparing file versions | ~90 |
| `StudioApiPanel` | StudioApiPanel.tsx | OpenAPI spec viewer: endpoint list, schema explorer | ~120 |
| `StudioEndpointCard` | StudioEndpointCard.tsx | Single API endpoint card: method badge, path, params, response | ~80 |
| `StudioApiTester` | StudioApiTester.tsx | Interactive API tester: send requests to mock server, view responses | ~100 |
| `StudioVisualMode` | StudioVisualMode.tsx | Visual editing canvas: component tree + element inspector + selection overlay | ~110 |
| `StudioElementInspector` | StudioElementInspector.tsx | Element property editor: styles, props, text content editing | ~90 |
| `StudioComponentTree` | StudioComponentTree.tsx | Hierarchical component tree view with expand/collapse | ~80 |
| `StudioSelectionOverlay` | StudioSelectionOverlay.tsx | Visual selection highlight overlay on the preview iframe | ~60 |
| `StudioQuickActions` | StudioQuickActions.tsx | Quick action buttons: common operations (add component, change style, etc.) | ~70 |
| `StudioVersionHistory` | StudioVersionHistory.tsx | Version list: version number, message, timestamp, restore button | ~90 |
| `StudioProjectSettings` | StudioProjectSettings.tsx | Project configuration: name, description, tech stack, CSS framework | ~100 |
| `StudioWelcome` | StudioWelcome.tsx | Welcome screen when no project is loaded: create new or load existing | ~80 |
| `StudioErrorBoundary` | StudioErrorBoundary.tsx | React error boundary: catches rendering errors, shows fallback UI | ~40 |
| `StudioExportDialog` | StudioExportDialog.tsx | Export options: scope selector (all/frontend/backend), download button | ~70 |
| `StudioMobileLayout` | StudioMobileLayout.tsx | Mobile-optimized layout: bottom tab bar, swipeable panels | ~120 |

### Page Component: StudioPage

**File:** `frontend/src/pages/StudioPage.tsx`

The page component wraps everything in `StudioErrorBoundary` and `StudioProvider`, then renders `StudioContent`:

```typescript
const StudioPage: React.FC = () => {
  const { activeProvider, activeModel } = useAppContext();
  return (
    <StudioErrorBoundary>
      <StudioProvider initialProvider={activeProvider} initialModel={activeModel}>
        <StudioContent />
      </StudioProvider>
    </StudioErrorBoundary>
  );
};
```

`StudioContent` handles:
1. Loading project list on mount.
2. Responsive detection (`window.innerWidth < 768` triggers mobile layout).
3. Rendering `StudioWelcome` when no project is loaded.
4. Rendering `StudioMobileLayout` on mobile.
5. Rendering mode-specific layouts on desktop.
6. Overlay panels (export, versions, settings, API) as modal dialogs.

### Overlay Panels

Four overlay types managed by `OverlayPanel` state:

```typescript
type OverlayPanel = null | 'export' | 'versions' | 'settings' | 'api';
```

These are triggered by buttons in the secondary action bar below the toolbar:
- **History** -- opens `StudioVersionHistory`
- **Settings** -- opens `StudioProjectSettings`
- **API** -- opens `StudioApiPanel` (only visible when `apiSpec` is non-null)
- **Export** -- opens `StudioExportDialog`

## 2.12 End-to-End Flow: Complete Generation Sequence

```
USER                          FRONTEND                         BACKEND                        AI MODEL
  |                              |                                |                               |
  |  Types: "Build todo app"     |                                |                               |
  |----------------------------->|                                |                               |
  |                              |  1. Create userMsg             |                               |
  |                              |  2. isFirstMessage=true        |                               |
  |                              |  3. mode="generate"            |                               |
  |                              |                                |                               |
  |                              |  POST /api/studio/stream       |                               |
  |                              |  {prompt, mode:"generate",     |                               |
  |                              |   provider, model}             |                               |
  |                              |------------------------------->|                               |
  |                              |                                |  4. Select GENERATE_SYSTEM_PROMPT
  |                              |                                |  5. Build messages array       |
  |                              |                                |  6. Call AI stream             |
  |                              |                                |------------------------------>|
  |                              |                                |                               |
  |                              |                                |  7. Tokens arrive             |
  |                              |                                |<------------------------------|
  |                              |                                |                               |
  |                              |  SSE: {type:"token",           |  8. _parse_file_markers()     |
  |                              |        content:"I'll build"}   |     on every token            |
  |                              |<-------------------------------|                               |
  |                              |                                |                               |
  |                              |  9. setStreamingText()         |                               |
  |  [Chat shows streaming text] |                                |                               |
  |                              |                                |                               |
  |                              |  SSE: {type:"studio_plan",     |  10. Plan detected            |
  |                              |        content:"I'll create..."}|    (text before first marker) |
  |                              |<-------------------------------|                               |
  |                              |  11. setStreamingPlan()        |                               |
  |                              |                                |                               |
  |                              |  SSE: {type:"studio_file",     |  12. ### END FILE detected    |
  |                              |        path:"/App.js",         |      for first file           |
  |                              |        content:"import..."}    |                               |
  |                              |<-------------------------------|                               |
  |                              |                                |                               |
  |                              |  13. setFiles({"/App.js":...}) |                               |
  |  [Sandpack preview updates!] |                                |                               |
  |                              |                                |                               |
  |                              |  ...more files emitted...      |                               |
  |                              |                                |                               |
  |                              |  SSE: {type:"done"}            |  14. Final parse pass         |
  |                              |<-------------------------------|  15. Auto-save to SQLite      |
  |                              |                                |                               |
  |                              |  16. Create assistantMsg       |                               |
  |                              |  17. setMessages(...)          |                               |
  |                              |  18. setIsDirty(true)          |                               |
  |                              |  19. setIsStreaming(false)     |                               |
  |                              |                                |                               |
  |  [Full app visible in        |                                |                               |
  |   preview, chat shows        |                                |                               |
  |   assistant response]        |                                |                               |
```

## 2.13 End-to-End Flow: Refine Sequence

```
USER                          FRONTEND                         BACKEND
  |                              |                                |
  |  Types: "Add dark mode"      |                                |
  |----------------------------->|                                |
  |                              |  1. isFirstMessage=false       |
  |                              |  2. mode="refine"              |
  |                              |  3. files={"/App.js":...}      |
  |                              |                                |
  |                              |  POST /api/studio/stream       |
  |                              |  {prompt, files, chat_history, |
  |                              |   mode:"refine"}               |
  |                              |------------------------------->|
  |                              |                                |
  |                              |                                |  4. Select REFINE_SYSTEM_PROMPT
  |                              |                                |  5. _build_user_prompt():
  |                              |                                |     "Here are the current files:
  |                              |                                |      ### FILE: /App.js
  |                              |                                |      ...existing code...
  |                              |                                |      ### END FILE
  |                              |                                |      ---
  |                              |                                |      User request: Add dark mode"
  |                              |                                |
  |                              |                                |  6. AI sees all current code
  |                              |                                |     + change request
  |                              |                                |  7. AI outputs ONLY changed files
  |                              |                                |
  |                              |  SSE: studio_file events       |
  |                              |  (only modified files)         |
  |                              |<-------------------------------|
  |                              |                                |
  |                              |  8. setFiles() MERGES new      |
  |                              |     files into existing map    |
  |                              |     (unchanged files kept)     |
  |                              |                                |
  |  [Preview updates with       |                                |
  |   dark mode applied]         |                                |
```

## 2.14 Key File Locations Summary

| File | Path | Purpose | Approx Lines |
|------|------|---------|-------------|
| Studio router | `backend/routers/studio.py` | 18 API endpoints, system prompts, file marker parsing, SSE streaming | 522 |
| Studio service | `backend/services/studio_service.py` | SQLite CRUD, version management, ZIP export | 385 |
| OpenAPI extractor | `backend/services/openapi_extractor.py` | AST + regex FastAPI code analysis | ~200 |
| Type generator | `backend/services/type_generator.py` | OpenAPI spec to TypeScript interfaces | ~150 |
| Studio types | `frontend/src/types/studio.ts` | 13 TypeScript interfaces | 113 |
| Studio context | `frontend/src/context/StudioContext.tsx` | All Studio state + sendMessage SSE parsing | 473 |
| Studio API service | `frontend/src/services/studioApiService.ts` | 17 fetch wrappers + response mappers | 207 |
| Studio page | `frontend/src/pages/StudioPage.tsx` | Page shell: provider, mode routing, overlays | 220 |
| Preview panel | `frontend/src/components/studio/StudioPreviewPanel.tsx` | Sandpack integration, dark theme, CSS hacks | 207 |
| 24 Studio components | `frontend/src/components/studio/*.tsx` | Layout, chat, editor, files, visual, API, versions, etc. | ~2400 total |

---

*End of Parts 0, 1, and 2. Parts 3-8 will cover KG Studio, Expert Builder, Tools Playground, Chat/Coding, Theme System, and Agents/Playbooks/Workflows.*
# Part 3: Core Architecture

This section documents the foundational layers of the workspace: the FastAPI application entry point, configuration system, model routing intelligence, both provider service wrappers (Gemini and Claude), the chat and coding routers, the React application shell with its router and navigation, the SSE streaming protocol, the theme system, and the frontend API service layer.

---

## 3.1 Application Entry Point (`backend/main.py`)

The entire backend starts from a single FastAPI application instance with CORS middleware, 16 router mounts, a conditional static file mount for Phaser game assets, and two root-level endpoints.

### Full Source (verbatim)

```python
"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from routers import chat, coding, agents, playbooks, workflows, builder, media, interchange, kg, studio, memory, integrations, experts, tools, vox, games

app = FastAPI(
    title="Multi-AI Agentic Workspace",
    description="Professional agentic workflow orchestrator for Gemini + Claude",
    version="1.0.0",
)

# CORS for dev (Vite on :5173 -> FastAPI on :8000)
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
```

### Router Mount Order (16 routers)

Mount order matters in FastAPI because overlapping path patterns are resolved first-come-first-served. The VOX router is the only one mounted **without** the `/api` prefix, because it needs to serve a WebSocket at the bare `/ws/vox` path alongside REST endpoints at `/api/vox/*`.

| # | Router | Prefix | Notes |
|---|--------|--------|-------|
| 1 | `chat` | `/api` | `POST /api/chat/stream` |
| 2 | `coding` | `/api` | `POST /api/coding/stream` |
| 3 | `agents` | `/api` | Agent CRUD + execution |
| 4 | `playbooks` | `/api` | Playbook search + retrieval |
| 5 | `workflows` | `/api` | Templates + SSE execution |
| 6 | `builder` | `/api` | Legacy web app plan/generate |
| 7 | `media` | `/api` | Image edit + video gen |
| 8 | `interchange` | `/api` | JSON import/export, mode toggle |
| 9 | `kg` | `/api` | KG Studio (33 endpoints) |
| 10 | `studio` | `/api` | AI Studio (18 endpoints) |
| 11 | `memory` | `/api` | Conversations + search |
| 12 | `integrations` | `/api` | Platform integrations |
| 13 | `experts` | `/api` | Expert Builder + KG-OS (15 endpoints) |
| 14 | `tools` | `/api` | Tools playground |
| 15 | `vox` | *(none)* | WS at `/ws/vox`, REST at `/api/vox/*` |
| 16 | `games` | `/api` | Phaser RPG game builder |

### Phaser Static File Mount

```python
_phaser_dir = Path(__file__).parent.parent / "docs" / "phaser"
if _phaser_dir.exists():
    app.mount("/docs/phaser", StaticFiles(directory=str(_phaser_dir)), name="phaser-static")
```

This conditionally serves the Phaser runtime JS and assets from `/docs/phaser/` as static files at the `/docs/phaser` URL path. The game preview iframe loads Phaser from this path. The `if` guard avoids a startup crash if the directory is missing.

### Root-Level Endpoints

**`GET /api/health`** -- Returns operating mode and which API keys are configured:

```python
@app.get("/api/health")
async def health():
    from config import MODE, GEMINI_API_KEY, ANTHROPIC_API_KEY
    return {
        "status": "ok",
        "mode": MODE,
        "gemini_configured": bool(GEMINI_API_KEY),
        "claude_configured": bool(ANTHROPIC_API_KEY),
    }
```

**`GET /api/models`** -- Returns the model catalog, filtered by mode. In `claude-code` mode, Claude models are omitted:

```python
@app.get("/api/models")
async def list_models():
    from config import MODELS, MODE
    result = {"gemini": MODELS["gemini"]}
    if MODE == "standalone":
        result["claude"] = MODELS["claude"]
    return result
```

Both endpoints use late imports (`from config import ...`) inside the function body rather than at module level. This is a deliberate pattern to pick up runtime key updates from `update_api_keys()` without stale module-level references.

---

## 3.2 Configuration (`backend/config.py`)

### Full Source (verbatim)

```python
"""Configuration for the Multi-AI Agentic Workspace."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from backend/ or project root -- keys persist across restarts
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

# --- VOX Voice Configuration ---
VOX_AUDIO_SAMPLE_RATE_IN = 16000   # PCM capture rate from mic
VOX_AUDIO_SAMPLE_RATE_OUT = 24000  # Playback rate for Gemini audio
VOX_DEFAULT_VOICE = "Puck"         # Gemini Live API voice
VOX_DEFAULT_MODEL = "gemini-2.5-flash-native-audio-preview-12-2025"  # Live API model

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
```

### Key Design Decisions

**Dual `.env` loading.** Both `backend/.env` and the project root `.env` are loaded, with the backend-level file taking priority. This supports both running `uvicorn` from inside `backend/` and from the project root.

**Mode-gated Claude key.** When `WORKSPACE_MODE=claude-code`, `ANTHROPIC_API_KEY` is forced to `None` at import time, making it structurally impossible for any downstream code to accidentally call the Claude API.

**Runtime key updates.** The `update_api_keys()` function mutates the module-level globals. The Gemini service's lazy client detects key changes (see section 3.4) and reinitializes the SDK client when the key changes.

### Model Catalog Summary

| Model ID | Provider | Context | Cost In/Out ($/1M tokens) | Use Case |
|----------|----------|---------|---------------------------|----------|
| `gemini-3-pro-preview` | Gemini | 1M | $2.00 / $12.00 | Flagship reasoning |
| `gemini-2.5-flash` | Gemini | 1M | $0.15 / $0.60 | Fast coding/streaming |
| `gemini-2.5-pro` | Gemini | 1M | $1.25 / $5.00 | Deep reasoning |
| `gemini-2.5-flash-image` | Gemini | 1M | $0.15 / $0.60 | Image generation |
| `gemini-embedding-001` | Gemini | 8K | Free | RAG/embeddings |
| `veo-2.0-generate-001` | Gemini | -- | -- | Video generation |
| `claude-opus-4-6` | Claude | 200K | $5.00 / $25.00 | Most intelligent |
| `claude-sonnet-4-6` | Claude | 200K | $3.00 / $15.00 | Fast + capable |
| `claude-haiku-4-5-20251001` | Claude | 200K | $1.00 / $5.00 | Cheapest, routing |

### Path Constants

| Constant | Resolved To | Purpose |
|----------|-------------|---------|
| `PROJECT_ROOT` | `backend/..` (workspace root) | Base for all relative paths |
| `AGENTS_DIR` | `<root>/agents` (symlink to NLKE) | 33 NLKE agent definitions |
| `PLAYBOOKS_DIR` | `<root>/docs/playbooks-v2` | 53 playbook markdown files |
| `KGS_DIR` | `<root>/docs/KGS` (or env override) | 57 SQLite KG databases |
| `TOOLS_DIR` | `<root>/../tools` | 58+ Python tool scripts |

---

## 3.3 Model Router (`backend/services/model_router.py`)

The model router implements intelligent provider and model selection based on 4 input parameters. It is a pure function with no state and no API calls -- just a decision tree.

### Full Source (verbatim)

```python
"""Intelligent model selection based on task type, complexity, and budget."""
from config import MODE, MODELS


def route(
    task_type: str = "general",
    complexity: str = "medium",
    budget_preference: str = "balanced",
    context_length: int = 0,
) -> dict:
    """
    Select optimal model based on task characteristics.

    Args:
        task_type: general, coding, reasoning, creative, bulk, embedding, image, video
        complexity: low, medium, high
        budget_preference: cheap, balanced, quality
        context_length: estimated input tokens

    Returns:
        {"provider": str, "model": str, "reason": str}
    """
    # Video/Image always Gemini
    if task_type == "video":
        return {"provider": "gemini", "model": "veo-2.0-generate-001", "reason": "Video generation is Gemini-only"}
    if task_type == "image":
        return {"provider": "gemini", "model": "gemini-2.5-flash-image", "reason": "Image generation via Gemini"}
    if task_type == "embedding":
        return {"provider": "gemini", "model": "gemini-embedding-001", "reason": "Embeddings via Gemini"}

    # Large context always Gemini (1M window)
    if context_length > 150000:
        return {"provider": "gemini", "model": "gemini-2.5-pro", "reason": "Large context requires Gemini's 1M window"}

    # Claude-code mode: always Gemini
    if MODE == "claude-code":
        if budget_preference == "cheap" or complexity == "low":
            return {"provider": "gemini", "model": "gemini-2.5-flash", "reason": "Fast & cheap (claude-code mode)"}
        return {"provider": "gemini", "model": "gemini-2.5-pro", "reason": "Best Gemini reasoning (claude-code mode)"}

    # Standalone mode: choose between providers
    if budget_preference == "cheap":
        if complexity == "low":
            return {"provider": "gemini", "model": "gemini-2.5-flash", "reason": "Cheapest option for simple tasks"}
        return {"provider": "claude", "model": "claude-haiku-4-5-20251001", "reason": "Budget Claude for medium tasks"}

    if task_type == "coding":
        if complexity == "high":
            return {"provider": "claude", "model": "claude-sonnet-4-6", "reason": "Claude excels at complex coding"}
        return {"provider": "gemini", "model": "gemini-2.5-flash", "reason": "Fast coding with Gemini Flash"}

    if task_type == "reasoning":
        if complexity == "high":
            return {"provider": "claude", "model": "claude-opus-4-6", "reason": "Claude Opus for deep reasoning"}
        return {"provider": "claude", "model": "claude-sonnet-4-6", "reason": "Claude Sonnet for reasoning"}

    if budget_preference == "quality":
        return {"provider": "claude", "model": "claude-opus-4-6", "reason": "Highest quality model"}

    # Default balanced
    if complexity == "high":
        return {"provider": "claude", "model": "claude-sonnet-4-6", "reason": "Balanced quality for complex tasks"}
    return {"provider": "gemini", "model": "gemini-2.5-flash", "reason": "Fast default for general tasks"}
```

### Decision Tree (Priority Order)

The rules are evaluated top-to-bottom. The first matching rule wins.

| Priority | Condition | Provider | Model | Reason |
|----------|-----------|----------|-------|--------|
| 1 | `task_type == "video"` | gemini | `veo-2.0-generate-001` | Video is Gemini-only |
| 2 | `task_type == "image"` | gemini | `gemini-2.5-flash-image` | Image gen via Gemini |
| 3 | `task_type == "embedding"` | gemini | `gemini-embedding-001` | Embeddings via Gemini |
| 4 | `context_length > 150000` | gemini | `gemini-2.5-pro` | Gemini's 1M context window |
| 5 | `MODE == "claude-code"` AND (`cheap` OR `low`) | gemini | `gemini-2.5-flash` | Fast & cheap in CC mode |
| 6 | `MODE == "claude-code"` (otherwise) | gemini | `gemini-2.5-pro` | Best Gemini reasoning in CC mode |
| 7 | `budget == "cheap"` AND `complexity == "low"` | gemini | `gemini-2.5-flash` | Cheapest for simple tasks |
| 8 | `budget == "cheap"` (otherwise) | claude | `claude-haiku-4-5-20251001` | Budget Claude for medium tasks |
| 9 | `task_type == "coding"` AND `complexity == "high"` | claude | `claude-sonnet-4-6` | Claude excels at complex coding |
| 10 | `task_type == "coding"` (otherwise) | gemini | `gemini-2.5-flash` | Fast coding with Flash |
| 11 | `task_type == "reasoning"` AND `complexity == "high"` | claude | `claude-opus-4-6` | Opus for deep reasoning |
| 12 | `task_type == "reasoning"` (otherwise) | claude | `claude-sonnet-4-6` | Sonnet for reasoning |
| 13 | `budget == "quality"` | claude | `claude-opus-4-6` | Highest quality model |
| 14 | `complexity == "high"` | claude | `claude-sonnet-4-6` | Balanced quality for complex tasks |
| 15 | *(default fallthrough)* | gemini | `gemini-2.5-flash` | Fast default for general tasks |

### Design Notes

- Rules 1--3 are **capability locks**: video, image, and embedding generation only exist in the Gemini SDK. These take absolute priority.
- Rule 4 is a **context window lock**: Claude tops out at 200K tokens, so anything above 150K is routed to Gemini's 1M window with headroom.
- Rules 5--6 are the **claude-code mode firewall**: when running under Claude Code, Claude API is unavailable, so all traffic goes to Gemini.
- Rules 7--15 are the **standalone mode optimizer**: they balance cost, capability, and task characteristics across both providers.

---

## 3.4 Gemini Service (`backend/services/gemini_service.py`)

### Lazy Client with Key Rotation

```python
_client = None
_client_key = None


def _get_client():
    global _client, _client_key
    from config import GEMINI_API_KEY as key
    if not key:
        raise ValueError("GEMINI_API_KEY not configured")
    if _client is None or _client_key != key:
        _client = genai.Client(api_key=key)
        _client_key = key
    return _client
```

The client is a module-level singleton, but it tracks the key it was initialized with (`_client_key`). If `update_api_keys()` changes the key at runtime, the next call to `_get_client()` detects the mismatch and creates a fresh SDK client. This is the **key rotation pattern**.

A backward-compatible `client` proxy is also exposed for legacy call sites:

```python
class _ClientProxy:
    def __getattr__(self, name):
        return getattr(_get_client(), name)

client = _ClientProxy()
```

Any attribute access on `client` (like `client.models.generate_content_stream(...)`) is transparently forwarded to the lazily-initialized real client.

### `_convert_messages()`

```python
def _convert_messages(messages: list[dict]) -> list[types.Content]:
    """Convert frontend message format to Gemini Content objects."""
    contents = []
    for msg in messages:
        role = "user" if msg.get("author") == "user" else "model"
        parts = []
        for part in msg.get("parts", []):
            if part.get("text"):
                parts.append(types.Part(text=part["text"]))
        if msg.get("toolResponse"):
            tr = msg["toolResponse"]
            parts.append(types.Part(
                function_response=types.FunctionResponse(
                    name=tr["name"],
                    response=tr["response"]["content"],
                )
            ))
        if parts:
            contents.append(types.Content(role=role, parts=parts))
    return contents
```

Conversion rules:
- `author == "user"` maps to Gemini role `"user"`, everything else maps to `"model"`.
- Text parts from the frontend `parts[]` array become `types.Part(text=...)`.
- If a message has a `toolResponse` field, it is appended as a `FunctionResponse` part. This enables the multi-turn function calling loop.

### `stream_chat()`

```python
async def stream_chat(
    messages: list[dict],
    model: str = DEFAULT_GEMINI_MODEL,
    system_instruction: Optional[str] = None,
    use_web_search: bool = False,
    temperature: float = 1.0,
) -> AsyncGenerator[dict, None]:
```

Yields SSE event dicts. Noteworthy behaviors:

1. **Web search grounding.** When `use_web_search=True`, a `GoogleSearch` tool is added to the request. The response may include `grounding_metadata` with web source URLs.

2. **Grounding metadata extraction.** After yielding text tokens, the code inspects each chunk's `candidates[0].grounding_metadata.grounding_chunks` for web results:

```python
if hasattr(gm, "grounding_chunks") and gm.grounding_chunks:
    sources = []
    for gc in gm.grounding_chunks:
        if hasattr(gc, "web") and gc.web:
            sources.append({"uri": gc.web.uri, "title": gc.web.title or gc.web.uri})
    if sources:
        yield {"type": "grounding", "sources": sources}
```

3. **Event types emitted:** `token`, `grounding`, `done`.

### `stream_with_tools()`

```python
async def stream_with_tools(
    messages: list[dict],
    tool_declarations: list[dict],
    model: str = DEFAULT_GEMINI_MODEL,
    system_instruction: Optional[str] = None,
    use_web_search: bool = False,
    temperature: float = 1.0,
) -> AsyncGenerator[dict, None]:
```

Accepts a list of tool declaration dicts (Gemini format with `parameters` key) and converts them to `types.FunctionDeclaration` objects:

```python
functions = []
for td in tool_declarations:
    functions.append(types.FunctionDeclaration(
        name=td["name"],
        description=td.get("description", ""),
        parameters=td.get("parameters"),
    ))
tools = [types.Tool(function_declarations=functions)]
```

When the model invokes a function, the code detects a `function_call` part and yields:

```python
yield {
    "type": "tool_call",
    "name": fc.name,
    "args": dict(fc.args) if fc.args else {},
}
```

**Event types emitted:** `token`, `tool_call`, `grounding`, `done`.

### `generate_content()` (synchronous)

```python
def generate_content(
    prompt: str,
    model: str = DEFAULT_GEMINI_MODEL,
    system_instruction: Optional[str] = None,
    response_mime_type: Optional[str] = None,
) -> str:
```

A blocking call used by non-streaming endpoints (builder plan, game synthesis, ingestion). Accepts an optional `response_mime_type` (e.g. `"application/json"`) for structured output.

### `edit_image()` (multimodal)

```python
async def edit_image(prompt: str, image_bytes: bytes, mime_type: str,
                     model: str = "gemini-2.5-flash-image") -> dict:
```

Sends a text prompt alongside an `inline_data` blob to Gemini with `response_modalities=["IMAGE", "TEXT"]`. Returns a list of parts, where image parts are base64-encoded data URIs:

```python
result_parts.append({"imageUrl": f"data:{part.inline_data.mime_type};base64,{b64}"})
```

### `generate_video()` / `check_video_status()` (async pipeline)

Video generation is a two-phase async operation:

1. **`generate_video(prompt, image_bytes?, mime_type?)`** -- Calls `client.models.generate_videos()` with the `veo-2.0-generate-001` model. Returns an `operation.name` string for polling.

2. **`check_video_status(operation_name)`** -- Polls `client.operations.get()`. Returns `{"done": False}` while processing, or `{"done": True, "videoUrl": uri}` on success, or `{"done": True, "error": str}` on failure.

The frontend polls every 10 seconds via `apiService.generateVideo()`.

---

## 3.5 Claude Service (`backend/services/claude_service.py`)

### Lazy Client Initialization

```python
_client = None


def _get_client():
    global _client
    if _client is None:
        if not ANTHROPIC_API_KEY:
            raise RuntimeError("Claude API not available in claude-code mode")
        import anthropic
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client
```

Unlike the Gemini service, there is no key rotation detection -- the Claude client is initialized once and cached. If `ANTHROPIC_API_KEY` is `None` (claude-code mode), `_get_client()` raises a `RuntimeError` immediately. The `anthropic` import is deferred inside the function body to avoid import-time failures when the SDK is not installed.

### `_convert_messages()`

```python
def _convert_messages(messages: list[dict]) -> list[dict]:
    """Convert frontend message format to Anthropic message format."""
    result = []
    for msg in messages:
        author = msg.get("author", "user")
        if author == "user":
            role = "user"
        elif author == "assistant":
            role = "assistant"
        elif author == "tool":
            tr = msg.get("toolResponse", {})
            result.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": tr.get("tool_use_id", ""),
                    "content": json.dumps(tr.get("response", {}).get("content", "")),
                }],
            })
            continue
        else:
            continue

        content = []
        for part in msg.get("parts", []):
            if part.get("text"):
                content.append({"type": "text", "text": part["text"]})

        # If assistant message had a tool call, add tool_use block
        if author == "assistant" and msg.get("toolCall"):
            tc = msg["toolCall"]
            content.append({
                "type": "tool_use",
                "id": tc.get("id", ""),
                "name": tc["name"],
                "input": tc.get("args", {}),
            })

        if content:
            result.append({"role": role, "content": content})
    return result
```

Key differences from the Gemini converter:
- **Tool results** (`author == "tool"`) are sent as `role: "user"` messages with a `tool_result` content block. The Anthropic API requires tool results to come from the user role.
- **Tool calls in history** (`author == "assistant"` with `toolCall`) are reconstructed as `tool_use` content blocks appended to the assistant message's content array.
- The output is plain dicts (not SDK objects), because the Anthropic SDK accepts raw dicts.

### `stream_chat()`

```python
async def stream_chat(
    messages: list[dict],
    model: str = DEFAULT_CLAUDE_MODEL,
    system: Optional[str] = None,
    max_tokens: int = 8192,
    temperature: float = 1.0,
) -> AsyncGenerator[dict, None]:
```

**Mode guard.** Every Claude streaming method starts with a mode check:

```python
if MODE != "standalone":
    yield {"type": "error", "content": "Claude API not available in claude-code mode. Use Export to Claude Code instead."}
    yield {"type": "done"}
    return
```

This is a defense-in-depth measure on top of the `ANTHROPIC_API_KEY = None` in config.py.

**Event processing.** The Anthropic SDK's `messages.stream()` context manager yields events:

```python
with client.messages.stream(**kwargs) as stream:
    for event in stream:
        if event.type == "content_block_delta":
            if hasattr(event.delta, "text"):
                yield {"type": "token", "content": event.delta.text}
        elif event.type == "message_stop":
            break
```

**Event types emitted:** `token`, `error`, `done`.

### `stream_with_tools()`

```python
async def stream_with_tools(
    messages: list[dict],
    tools: list[dict],
    model: str = DEFAULT_CLAUDE_MODEL,
    system: Optional[str] = None,
    max_tokens: int = 8192,
    temperature: float = 1.0,
) -> AsyncGenerator[dict, None]:
```

The `tools` parameter uses Claude's format with `input_schema` (not Gemini's `parameters`). Event processing handles three additional event types:

```python
if event.type == "content_block_start":
    if hasattr(event.content_block, "type"):
        if event.content_block.type == "tool_use":
            yield {
                "type": "tool_call_start",
                "id": event.content_block.id,
                "name": event.content_block.name,
            }
elif event.type == "content_block_delta":
    if hasattr(event.delta, "text"):
        yield {"type": "token", "content": event.delta.text}
    elif hasattr(event.delta, "partial_json"):
        yield {"type": "tool_call_delta", "content": event.delta.partial_json}
```

**Event types emitted:** `token`, `tool_call_start`, `tool_call_delta`, `error`, `done`.

The `tool_call_start` event carries the tool use `id` and `name`. The `tool_call_delta` events stream the JSON arguments incrementally as `partial_json` fragments. The frontend accumulates these fragments and parses the complete JSON when the content block stops.

### `stream_with_thinking()` (Extended Thinking)

```python
async def stream_with_thinking(
    messages: list[dict],
    model: str = DEFAULT_CLAUDE_MODEL,
    system: Optional[str] = None,
    thinking_budget: int = 10000,
    max_tokens: int = 16384,
) -> AsyncGenerator[dict, None]:
```

Enables Claude's extended thinking mode with a configurable token budget:

```python
kwargs = {
    "model": model,
    "max_tokens": max_tokens,
    "messages": converted,
    "thinking": {
        "type": "enabled",
        "budget_tokens": thinking_budget,
    },
    "temperature": 1.0,  # Required for extended thinking
}
```

**Important constraint:** Extended thinking requires `temperature=1.0`. The Anthropic API rejects other temperature values when thinking is enabled.

Event processing distinguishes thinking blocks from text blocks:

```python
if event.type == "content_block_start":
    if hasattr(event.content_block, "type"):
        if event.content_block.type == "thinking":
            yield {"type": "thinking_start"}
elif event.type == "content_block_delta":
    if hasattr(event.delta, "thinking"):
        yield {"type": "thinking", "content": event.delta.thinking}
    elif hasattr(event.delta, "text"):
        yield {"type": "token", "content": event.delta.text}
```

**Event types emitted:** `thinking_start`, `thinking`, `token`, `error`, `done`.

---

## 3.6 SSE Streaming Protocol

All streaming endpoints use Server-Sent Events (SSE) over `text/event-stream` responses. Each event is a JSON object prefixed with `data: ` and terminated by `\n\n`.

### Wire Format

```
data: {"type":"token","content":"Hello"}\n\n
data: {"type":"token","content":" world"}\n\n
data: {"type":"done"}\n\n
```

### Complete Event Type Catalog

| Event Type | Fields | Emitted By | Description |
|------------|--------|------------|-------------|
| `token` | `content: string` | All streaming endpoints | Incremental text token |
| `done` | *(none)* | All streaming endpoints | Stream termination signal |
| `error` | `content: string` | All streaming endpoints | Error message |
| `grounding` | `sources: [{uri, title}]` | Gemini `stream_chat`, `stream_with_tools` | Google Search web sources |
| `tool_call` | `name: string, args: object` | Gemini `stream_with_tools` | Complete function call (Gemini sends it atomically) |
| `tool_call_start` | `id: string, name: string` | Claude `stream_with_tools` | Start of a tool use block |
| `tool_call_delta` | `content: string` | Claude `stream_with_tools` | Partial JSON fragment of tool arguments |
| `thinking_start` | *(none)* | Claude `stream_with_thinking` | Start of thinking block |
| `thinking` | `content: string` | Claude `stream_with_thinking` | Incremental thinking text |
| `sources` | `sources: [{node_id, name, ...}]` | Expert chat, KG RAG chat | KG retrieval source citations |
| `step` | `id, title, status, ...` | Workflow execution | Workflow step progress |
| `file` | `path: string, content: string` | Studio, Games | Generated file content |
| `plan` | `plan: object` | Studio | Generation plan |
| `chat` | `content: string` | Studio, Games | Chat message from AI |
| `complete` | `project: object` | Studio, Games | Generation complete with final state |
| `progress` | `message: string` | Studio, Games, Tools | Progress update |
| `result` | `data: any` | Tools stream | Tool execution result |

### Frontend SSE Consumption Pattern

The frontend reads SSE streams using the `ReadableStream` API:

```typescript
const stream = await streamChat(messages, provider, model, ...);
const reader = stream.getReader();
const decoder = new TextDecoder();
let buffer = '';

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  buffer += decoder.decode(value, { stream: true });
  const lines = buffer.split('\n');
  buffer = lines.pop() || '';
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const event = JSON.parse(line.slice(6));
      // dispatch based on event.type
    }
  }
}
```

---

## 3.7 Chat Router (`backend/routers/chat.py`)

The chat router is intentionally thin -- it is a pure delegation layer to the unified agentic loop.

### Full Source (verbatim)

```python
"""Chat streaming endpoint -- dual-model support via unified agentic loop."""
import json
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

router = APIRouter()


@router.post("/chat/stream")
async def chat_stream(request: Request):
    """SSE streaming chat endpoint. Supports both Gemini and Claude."""
    body = await request.json()
    messages = body.get("messages", [])
    model = body.get("model")
    provider = body.get("provider", "gemini")
    persona = body.get("persona")
    custom_styles = body.get("customStyles", [])
    use_web_search = body.get("useWebSearch", False)
    thinking_budget = body.get("thinkingBudget")
    conversation_id = body.get("conversationId")

    async def generate():
        from services.agentic_loop import agentic_loop
        try:
            async for chunk in agentic_loop.run(
                messages=messages,
                conversation_id=conversation_id,
                mode="chat",
                provider=provider,
                model=model,
                persona=persona,
                custom_styles=custom_styles,
                use_web_search=use_web_search,
                thinking_budget=thinking_budget or 0,
            ):
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

### Request Body Schema

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `messages` | `Message[]` | `[]` | Conversation history |
| `model` | `string?` | `null` (uses default) | Model override |
| `provider` | `"gemini" \| "claude"` | `"gemini"` | Provider selection |
| `persona` | `Persona?` | `null` | System prompt persona |
| `customStyles` | `CustomAiStyle[]` | `[]` | Additional style instructions |
| `useWebSearch` | `boolean` | `false` | Enable Google Search grounding |
| `thinkingBudget` | `number?` | `null` | Claude extended thinking budget |
| `conversationId` | `string?` | `null` | Conversation ID for memory persistence |

### Delegation to Agentic Loop

The router does **no** model-specific logic. It passes `mode="chat"` to `agentic_loop.run()`, which handles:
- Provider-specific service dispatch (Gemini vs Claude)
- System prompt assembly (persona + custom styles)
- Extended thinking activation when `thinkingBudget > 0`
- Conversation memory persistence when `conversationId` is set
- Error handling and mode guards

---

## 3.8 Coding Router (`backend/routers/coding.py`)

The coding router provides the IDE page's AI assistant with 7 tool declarations in dual format (Gemini and Claude), a system prompt builder, and delegates execution to the agentic loop.

### 7 Tool Declarations (Dual Format)

Each tool is declared twice: once in Gemini format (with `parameters` key) and once in Claude format (with `input_schema` key). The tools are identical in semantics; only the schema key name differs.

| Tool | Parameters | Description |
|------|-----------|-------------|
| `listFiles` | *(none)* | List all files in the current project |
| `createFile` | `path: string`, `content: string` | Create a new file |
| `readFile` | `path: string` | Read file content |
| `updateFile` | `path: string`, `newContent: string` | Update existing file |
| `deleteFile` | `path: string` | Delete a file |
| `searchNpm` | `packageName: string` | Search the npm registry |
| `runPython` | `code: string` | Execute Python code and return result |

**Gemini format example:**

```python
GEMINI_TOOL_DECLARATIONS = [
    {
        "name": "createFile",
        "description": "Create a new file in the project.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path relative to project root"},
                "content": {"type": "string", "description": "File content"},
            },
            "required": ["path", "content"],
        },
    },
    # ... 6 more
]
```

**Claude format example:**

```python
CLAUDE_TOOL_DEFINITIONS = [
    {
        "name": "createFile",
        "description": "Create a new file in the project.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path relative to project root"},
                "content": {"type": "string", "description": "File content"},
            },
            "required": ["path", "content"],
        },
    },
    # ... 6 more
]
```

### System Prompt Builder

```python
def _build_coding_system_prompt(projects: list[dict], persona: dict | None,
                                 custom_styles: list[dict] | None) -> str:
    parts = ["You are an expert coding assistant. You have access to tools for "
             "file operations, npm search, and Python execution."]
    if projects:
        project_context = []
        for p in projects:
            ctx = f"Project: {p['name']}"
            if p.get("dependencySummary"):
                ctx += f"\nDependencies: {p['dependencySummary']}"
            project_context.append(ctx)
        parts.append("Active Projects:\n" + "\n".join(project_context))
    return "\n\n".join(parts)
```

The system prompt includes project names and dependency summaries from the active project list, giving the AI context about what it is working on.

### Endpoint

```python
@router.post("/coding/stream")
async def coding_stream(request: Request):
    body = await request.json()
    messages = body.get("history", body.get("messages", []))
    # ... extract all parameters ...

    async def generate():
        from services.agentic_loop import agentic_loop
        try:
            async for chunk in agentic_loop.run(
                messages=messages,
                conversation_id=conversation_id,
                mode="coding",
                provider=provider,
                model=model,
                system_prompt=system_prompt,
                persona=persona,
                custom_styles=custom_styles,
                tools=GEMINI_TOOL_DECLARATIONS,
                tools_claude=CLAUDE_TOOL_DEFINITIONS,
                use_web_search=use_web_search,
                thinking_budget=thinking_budget or 0,
            ):
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

Note: The `messages` field accepts both `history` (legacy field name) and `messages` as keys, with `history` taking priority.

The key difference from the chat router is the passage of `tools` and `tools_claude` parameters, plus the `mode="coding"` flag. The agentic loop uses the appropriate tool declarations based on the selected provider.

---

## 3.9 Frontend Application Shell (`frontend/src/App.tsx`)

### Full Source (verbatim)

```tsx
import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AppProvider, useAppContext } from './context/AppContext';
import { VoxProvider, useVoxContext } from './context/VoxContext';
import NavBar from './components/NavBar';
import ChatPage from './pages/ChatPage';
import CodingPage from './pages/CodingPage';
import AgentsPage from './pages/AgentsPage';
import PlaybooksPage from './pages/PlaybooksPage';
import WorkflowsPage from './pages/WorkflowsPage';
import KGStudioPage from './pages/KGStudioPage';
import StudioPage from './pages/StudioPage';
import IntegrationsPage from './pages/IntegrationsPage';
import SettingsPage from './pages/SettingsPage';
import ExpertsPage from './pages/ExpertsPage';
import ToolsPage from './pages/ToolsPage';
import VoxPage from './pages/VoxPage';
import GamesPage from './pages/GamesPage';
import VoxOverlay from './components/VoxOverlay';
import VoxTourOverlay from './components/VoxTourOverlay';
import ToastContainer from './components/ToastContainer';

/** Bridge component that connects VoxTourOverlay to VoxContext */
const VoxTourBridge: React.FC = () => {
  const { activeTour, clearTour } = useVoxContext();
  if (!activeTour) return null;
  return <VoxTourOverlay tour={activeTour} onComplete={clearTour} />;
};

const AppContent: React.FC = () => {
  const { globalError, setGlobalError } = useAppContext();

  return (
    <VoxProvider>
      <div className="flex flex-col h-screen font-sans overflow-hidden"
           style={{ background: 'var(--t-bg)', color: 'var(--t-text)',
                    fontFamily: 'var(--t-font)' }}>
        <NavBar />
        <div className="flex-1 overflow-hidden">
          <Routes>
            <Route path="/" element={<Navigate to="/chat" replace />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/coding" element={<CodingPage />} />
            <Route path="/agents" element={<AgentsPage />} />
            <Route path="/playbooks" element={<PlaybooksPage />} />
            <Route path="/workflows" element={<WorkflowsPage />} />
            <Route path="/kg-studio" element={<KGStudioPage />} />
            <Route path="/builder" element={<StudioPage />} />
            <Route path="/experts" element={<ExpertsPage />} />
            <Route path="/tools" element={<ToolsPage />} />
            <Route path="/vox" element={<VoxPage />} />
            <Route path="/games" element={<GamesPage />} />
            <Route path="/integrations" element={<IntegrationsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </div>

        {globalError && (
          <div className="fixed bottom-4 right-4 p-4 rounded-lg shadow-lg max-w-sm z-50"
               style={{ background: 'var(--t-error)', color: '#fff' }}>
            <div className="flex justify-between items-center">
              <p className="font-semibold text-sm">Error</p>
              <button onClick={() => setGlobalError(null)}
                      className="text-xl leading-none">&times;</button>
            </div>
            <p className="text-sm mt-1">{globalError}</p>
          </div>
        )}

        <VoxOverlay />
        <VoxTourBridge />
        <ToastContainer />
      </div>
    </VoxProvider>
  );
};

const App: React.FC = () => (
  <AppProvider>
    <AppContent />
  </AppProvider>
);

export default App;
```

### Context Provider Nesting

```
<AppProvider>           -- Global state: projects, models, personas, mode, theme
  <AppContent>
    <VoxProvider>       -- VOX voice agent state: connection, transcript, tours
      <NavBar />
      <Routes />
      <VoxOverlay />    -- Floating voice pill (always visible)
      <VoxTourBridge /> -- Guided tour spotlight overlay
      <ToastContainer />
    </VoxProvider>
  </AppContent>
</AppProvider>
```

`AppProvider` wraps the entire tree and provides workspace-wide state. `VoxProvider` is nested inside `AppContent` (which has access to `useAppContext()`) so that VOX can read workspace state.

### Route Table (14 routes)

| Path | Component | Page |
|------|-----------|------|
| `/` | `Navigate to="/chat"` | Redirect to chat |
| `/chat` | `ChatPage` | Dual-model streaming chat |
| `/coding` | `CodingPage` | IDE with file explorer + AI coding |
| `/agents` | `AgentsPage` | 33 NLKE agents + pipeline builder |
| `/playbooks` | `PlaybooksPage` | 53 playbooks search + reader |
| `/workflows` | `WorkflowsPage` | Visual workflow designer + executor |
| `/kg-studio` | `KGStudioPage` | Graph-RAG KG workspace |
| `/builder` | `StudioPage` | AI Studio: app generation |
| `/experts` | `ExpertsPage` | KG-OS Expert Builder |
| `/tools` | `ToolsPage` | 58+ Python tools playground |
| `/vox` | `VoxPage` | VOX voice control center |
| `/games` | `GamesPage` | Phaser RPG game builder |
| `/integrations` | `IntegrationsPage` | Platform integrations management |
| `/settings` | `SettingsPage` | Mode toggle, themes, export/import |

### VoxTourBridge

The `VoxTourBridge` component solves a layering problem. `VoxTourOverlay` needs access to `VoxContext` (for tour state), but it is rendered as a sibling of the routes at the app root level. The bridge reads `activeTour` and `clearTour` from context and conditionally renders the overlay:

```tsx
const VoxTourBridge: React.FC = () => {
  const { activeTour, clearTour } = useVoxContext();
  if (!activeTour) return null;
  return <VoxTourOverlay tour={activeTour} onComplete={clearTour} />;
};
```

### Global Error Overlay

A fixed-position error toast in the bottom-right corner, rendered when `globalError` is non-null. It uses theme-aware styling (`var(--t-error)` for background) and is dismissible via a close button.

---

## 3.10 NavBar (`frontend/src/components/NavBar.tsx`)

### Navigation Links (12 links + Settings)

```typescript
const links = [
  { to: '/chat',         label: 'Chat' },
  { to: '/coding',       label: 'Coding' },
  { to: '/agents',       label: 'Agents' },
  { to: '/playbooks',    label: 'Playbooks' },
  { to: '/workflows',    label: 'Workflows' },
  { to: '/kg-studio',    label: 'KG Studio' },
  { to: '/experts',      label: 'Experts' },
  { to: '/builder',      label: 'Studio' },
  { to: '/vox',          label: 'VOX' },
  { to: '/games',        label: 'Games' },
  { to: '/tools',        label: 'Tools' },
  { to: '/integrations', label: 'Integrations' },
];
```

Settings is rendered separately as an icon-only link (gear SVG) outside the main links array.

### Layout Structure

- **Desktop** (`md:` and up): Horizontal link bar with all 12 links + ThemeSwitcher + Settings icon + model badge.
- **Mobile** (`< md`): Collapsed hamburger menu. ThemeSwitcher is in the header next to the hamburger button. Links expand vertically when menu is open.

### Mode Indicator

```tsx
<span className="hidden sm:inline text-xs px-2 py-0.5 rounded"
      style={{ color: 'var(--t-muted)', background: 'var(--t-surface2)' }}>
  {workspaceMode === 'claude-code' ? 'CC' : 'SA'}
</span>
```

Displays `CC` for claude-code mode or `SA` for standalone mode, next to the "AI Workspace" branding.

### Model Badge

```tsx
<span className="px-2 py-0.5 rounded" style={{
  background: activeProvider === 'claude' ? '#9a3412' : 'var(--t-primary)',
  color: '#fff',
}}>
  {activeProvider === 'claude' ? 'Claude' : 'Gemini'}
</span>
<span className="truncate max-w-[120px]" style={{ color: 'var(--t-muted)' }}>
  {activeModel}
</span>
```

Shows the active provider name (color-coded: amber-brown for Claude, theme primary for Gemini) and the active model ID, truncated to 120px.

### Active Link Styling (Scratch Theme Special Case)

The Scratch theme uses a CSS class (`t-nav-active`) instead of an inline background, because its active state uses a hand-drawn underline effect rather than a solid background fill:

```tsx
className={({ isActive }) =>
  `px-3 py-1.5 rounded text-xs font-medium transition-colors ${
    isActive && isScratch ? 't-nav-active' : ''
  }`
}
style={({ isActive }) => ({
  background: isActive && !isScratch ? 'var(--t-primary)' : 'transparent',
  color: isActive ? (isScratch ? 'var(--t-text)' : '#fff') : 'var(--t-muted)',
})}
```

---

## 3.11 Theme System

### Architecture

The theme system has three layers:

1. **Theme definitions** (`frontend/src/themes/index.ts`) -- 5 preset themes as CSS variable maps.
2. **Theme hook** (`frontend/src/hooks/useTheme.ts`) -- Applies variables to `:root`, persists to localStorage.
3. **Component consumption** -- All components use `style={{ background: 'var(--t-surface)' }}` for visual properties and `className` for layout.

### 5 Themes

| ID | Name | Background | Primary | Font | Radius | Special |
|----|------|------------|---------|------|--------|---------|
| `default` | Default | `#111827` (slate dark) | `#0ea5e9` (sky blue) | system-ui | `0.5rem` | -- |
| `crt` | Deluxe-CRT | `#0a0a08` (near-black) | `#ffb000` (amber) | Courier New | `0.25rem` | Scanline overlay via `data-theme="crt"` |
| `scratch` | Scratch | `#fafaf8` (off-white) | `#1a1a1a` (black) | Patrick Hand (cursive) | `0px` | Hand-drawn borders via `data-theme="scratch"` |
| `solarized` | Solarized Zen | `#002b36` (dark teal) | `#2aa198` (teal) | system-ui | `0.375rem` | -- |
| `sunset` | Sunset Warm | `#1a1218` (warm charcoal) | `#ff6b6b` (coral) | system-ui | `0.5rem` | -- |

### CSS Variable Map (17 variables per theme)

```typescript
vars: {
  '--t-bg':        string,  // Page background
  '--t-surface':   string,  // Card / panel background
  '--t-surface2':  string,  // Secondary surface (nested panels)
  '--t-border':    string,  // Border color
  '--t-primary':   string,  // Primary accent (buttons, active links)
  '--t-primary-h': string,  // Primary hover state
  '--t-accent1':   string,  // Secondary accent
  '--t-accent2':   string,  // Tertiary accent
  '--t-text':      string,  // Primary text color
  '--t-text2':     string,  // Secondary text color
  '--t-muted':     string,  // Muted / disabled text
  '--t-success':   string,  // Success state
  '--t-warning':   string,  // Warning state
  '--t-error':     string,  // Error state
  '--t-font':      string,  // Primary font family
  '--t-font-mono': string,  // Monospace font family
  '--t-radius':    string,  // Default border radius
}
```

### `useTheme` Hook

```typescript
export function useTheme() {
  const [themeId, setThemeId] = useState<ThemeId>(loadSavedTheme);

  useEffect(() => {
    applyTheme(themeId);
  }, [themeId]);

  const switchTheme = useCallback((id: ThemeId) => {
    setThemeId(id);
  }, []);

  return { themeId, switchTheme, theme: getTheme(themeId) };
}
```

**`loadSavedTheme()`** reads from `localStorage.getItem('workspace_theme')` and validates against the 5 known theme IDs. Falls back to `'default'`.

**`applyTheme(id)`** does three things:
1. Sets all CSS custom properties on `document.documentElement.style`.
2. Sets `data-theme` attribute for CSS selector-based effects (CRT scanlines, Scratch borders).
3. Persists the choice to localStorage.

### Component CSS Pattern

All components follow a strict pattern: **visual properties in `style`**, **layout properties in `className`**:

```tsx
// Correct pattern
<div className="flex items-center p-4 rounded-lg"
     style={{ background: 'var(--t-surface)', color: 'var(--t-text)',
              borderColor: 'var(--t-border)' }}>

// Anti-pattern (never used)
<div className="bg-gray-800 text-white p-4">
```

This ensures every component respects the active theme without hard-coded Tailwind color classes.

---

## 3.12 Frontend API Service (`frontend/src/services/apiService.ts`)

The API service is a single file exporting all API wrapper functions. It provides no state, caching, or retry logic -- it is a pure fetch-and-return layer. The base URL is `/api` (handled by Vite's proxy in development).

### Function Categories

#### Streaming Functions (return `ReadableStream<Uint8Array>`)

| Function | Endpoint | Method |
|----------|----------|--------|
| `streamChat(messages, provider, model, ...)` | `POST /api/chat/stream` | SSE |
| `streamCoding(history, projects, ...)` | `POST /api/coding/stream` | SSE |
| `streamWorkflowExecution(steps, goal)` | `POST /api/workflows/execute` | SSE |
| `streamKGChat(dbId, query, history, ...)` | `POST /api/kg/databases/{id}/chat` | SSE |
| `streamExpertChat(expertId, query, ...)` | `POST /api/experts/{id}/chat` | SSE |
| `runToolStream(id, params)` | `POST /api/tools/{id}/run/stream` | SSE |
| `streamGenerateGame(gameId)` | `POST /api/games/{id}/generate` | SSE |
| `streamRefineGame(gameId, prompt, files)` | `POST /api/games/{id}/refine` | SSE |
| `streamGameChat(gameId, query, ...)` | `POST /api/games/{id}/chat` | SSE |

All streaming functions check `!response.ok || !response.body` and throw on failure. They return the raw `ReadableStream` for the caller to consume.

#### FormData Functions (file uploads)

| Function | Endpoint | Payload |
|----------|----------|---------|
| `editImage(prompt, file)` | `POST /api/image/edit` | `FormData: prompt + file` |
| `generateVideo(prompt, file, updateStatus)` | `POST /api/video/generate` | `FormData: prompt + file?` |

`generateVideo` is unique: it initiates generation, then **polls** `/api/video/status?operationName=...` every 10 seconds until `result.done == true`, calling `updateStatus()` callbacks for UI feedback.

#### JSON CRUD Functions (return parsed JSON)

| Category | Functions |
|----------|-----------|
| **Agents** | `listAgents()`, `runAgent(name, workload)`, `getAgentExample(name)`, `runPipeline(steps)` |
| **Playbooks** | `listPlaybooks()`, `searchPlaybooks(q, category?)`, `getPlaybook(filename)`, `listPlaybookCategories()` |
| **Workflows** | `listWorkflowTemplates()`, `planWorkflow(goal, template?)` |
| **Builder** | `generateWebAppPlan(idea, provider?, model?)`, `generateWebAppCode(plan, theme, provider?, model?)` |
| **Models** | `listModels()` |
| **Mode** | `getMode()`, `setMode(mode)` |
| **Interchange** | `exportWorkspace(data)`, `importWorkspace(data)` |
| **Health** | `healthCheck()` |
| **KG (30 functions)** | `listKGDatabases()`, `getKGStats(dbId)`, `listKGNodes(dbId, ...)`, `getKGNode(dbId, nodeId)`, `getKGNeighbors(dbId, nodeId, ...)`, `listKGEdges(dbId, ...)`, `getKGTypes(dbId)`, `searchKG(dbId, query, ...)`, `multiSearchKG(query, dbIds, ...)`, `getKGEmbeddingStatus(dbId)`, `createKGDatabase(name)`, `createKGNode(dbId, ...)`, `updateKGNode(dbId, nodeId, ...)`, `deleteKGNode(dbId, nodeId)`, `createKGEdge(dbId, ...)`, `updateKGEdge(dbId, edgeId, ...)`, `deleteKGEdge(dbId, edgeId)`, `bulkCreateKG(dbId, nodes, edges)`, `ingestKGText(dbId, text, ...)`, `getKGAnalyticsSummary(dbId)`, `getKGCentrality(dbId, ...)`, `getKGCommunities(dbId)`, `findKGPath(dbId, ...)`, `compareKGs(dbIdA, dbIdB)`, `diffKGs(dbIdA, dbIdB)`, `mergeKGs(sourceDb, targetDb, ...)`, `batchDeleteByType(dbId, nodeType)`, `batchRetype(dbId, oldType, newType)`, `getKGEmbeddingProjection(dbId, ...)`, `generateKGEmbeddings(dbId, ...)`, `getKGEmbeddingQuality(dbId)` |
| **Memory** | `listConversations(mode?, limit?)`, `getConversation(id)`, `getConversationMessages(id, limit?, offset?)`, `deleteConversation(id)`, `searchMemory(query, limit?)`, `getMemoryStats()` |
| **Integrations** | `listIntegrations()`, `configureIntegration(platform, config, userLabel?)`, `testIntegration(platform)`, `enableIntegration(platform)`, `disableIntegration(platform)`, `deleteIntegration(platform)`, `getIntegrationSetup(platform)` |
| **Experts** | `listExperts()`, `createExpert(data)`, `getExpert(id)`, `updateExpert(id, data)`, `deleteExpert(id)`, `duplicateExpert(id)`, `listExpertConversations(expertId)`, `getExpertConversation(expertId, cid)`, `deleteExpertConversation(expertId, cid)`, `kgosQuery(dbId, query, options?)`, `kgosImpact(dbId, nodeId, ...)`, `kgosCompose(dbId, goal, ...)`, `kgosSimilar(dbId, nodeId, k?)` |
| **Tools** | `listTools()`, `getToolDetail(id)`, `runTool(id, params)` |
| **VOX** | `getVoxStatus()`, `getVoxVoices()`, `getVoxFunctions()`, `runVoxFunction(fnName, args?)` |
| **Config** | `getKeysStatus()`, `setApiKeys(geminiKey?, anthropicKey?)` |
| **Games** | `listGames()`, `createGame(name, desc?)`, `getGame(id)`, `updateGame(id, data)`, `deleteGame(id)`, `getInterviewQuestions()`, `submitInterviewAnswer(gameId, qId, answer)`, `synthesizeGDD(gameId)`, `saveGameVersion(gameId)`, `listGameVersions(gameId)`, `restoreGameVersion(gameId, ver)`, `exportGame(gameId)`, `extractGamePatterns(gameId)`, `gameLLMStatus()`, `gameLLMLoad(modelType)`, `gameLLMUnload()`, `gameLLMChat(npcName, systemPrompt, message, history?)` |

### Error Handling Pattern

Most functions use a simple pattern:

```typescript
const res = await fetch(`${BASE}/endpoint`, options);
if (!res.ok) throw new Error((await res.json()).detail || 'Default error message');
return res.json();
```

Some simpler functions skip the error check and just return `res.json()` directly. The streaming functions check both `!response.ok` and `!response.body` before returning the stream.

### Total Function Count

The `apiService.ts` file exports approximately **95+ functions** covering all 16 backend routers. This makes it the single most comprehensive file in the frontend codebase.

---

## 3.13 Architecture Summary Diagram

```
                    Browser (React 19 + Vite)
                              |
              ┌───────────────┼───────────────┐
              |               |               |
         apiService.ts   useVox.ts       useChat.ts
         (95+ functions)  (WebSocket)    (SSE consumer)
              |               |               |
              └───────┬───────┘───────────────┘
                      | HTTP / WS
                      v
              FastAPI (uvicorn :8000)
              ┌───────────────────────┐
              │  CORSMiddleware       │
              │  allow_origins=["*"]  │
              └───────┬───────────────┘
                      |
        ┌─────────────┼─────────────────────────────────┐
        |             |                                  |
   16 Routers    /api/health              /docs/phaser/*
   (prefix /api)  /api/models              (StaticFiles)
        |
        v
   ┌─────────────────────────────────────────────────┐
   │  Router → agentic_loop.run() → Service Layer    │
   │                                                  │
   │  chat.py ──────→ gemini_service.stream_chat()   │
   │                   claude_service.stream_chat()   │
   │  coding.py ────→ gemini_service.stream_with_tools()  │
   │                   claude_service.stream_with_tools()  │
   │  experts.py ───→ expert_service → kgos_query_engine   │
   │  kg.py ────────→ kg_service, embedding_service        │
   │  studio.py ────→ studio_service + gemini_service      │
   │  vox.py ───────→ vox_service (Gemini Live API + Claude)│
   │  games.py ─────→ game_service + game_generator        │
   │  tools.py ─────→ tools_service (58+ tools)            │
   └─────────────────────────────────────────────────┘
                      |
        ┌─────────────┼─────────────────────┐
        |             |                      |
   Gemini SDK    Anthropic SDK        SQLite DBs
   (google-genai) (anthropic)       (KGs, Studio,
                                     Experts, Games,
                                     Memory, VOX)
```
# Part 4: Data Models

## 4.1 Backend Pydantic Models

### VOX Router Models (`backend/routers/vox.py`)

```python
class FunctionRunRequest(BaseModel):
    args: dict = {}

class AwarenessEvent(BaseModel):
    event_type: str          # "page_visit" | "error" | "context"
    page: Optional[str] = None
    error_type: Optional[str] = None
    message: Optional[str] = None
    key: Optional[str] = None
    value: Optional[str] = None
    metadata: Optional[dict] = None

class MacroCreateRequest(BaseModel):
    name: str
    trigger_phrase: str
    steps: list[dict]
    error_policy: str = "abort"
```

### Games Router Models (`backend/routers/games.py`)

```python
class GameCreate(BaseModel):
    name: str
    description: str = ""

class GameUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    files: Optional[dict] = None
    settings: Optional[dict] = None

class InterviewAnswer(BaseModel):
    question_id: str
    answer: str | list[str]

class GenerateRequest(BaseModel):
    kg_context: str = ""

class RefineRequest(BaseModel):
    prompt: str
    files: dict = {}

class ChatRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None
    history: list[dict] = []

class LLMChatRequest(BaseModel):
    npc_name: str
    system_prompt: str
    message: str
    history: list[dict] = []

class LLMLoadRequest(BaseModel):
    model_type: str
```

---

## 4.2 VoxSession Dataclass (`backend/services/vox_service.py`)

```python
@dataclass
class VoxSession:
    session_id: str                        # UUID[:8], e.g. "a1b2c3d4"
    mode: str                              # "gemini" | "claude"
    model: str                             # Model ID, e.g. "gemini-2.5-flash-native-audio-preview-12-2025"
    voice: str                             # Voice name, e.g. "Puck" (Gemini) or "browser" (Claude)
    created_at: float                      # time.time() epoch seconds
    system_instruction: str                # Full VOX system prompt with awareness injection
    tools: list = field(default_factory=list)  # Function declaration dicts
    gemini_session: Any = None             # Gemini Live API session handle
    gemini_ctx: Any = None                 # Async context manager for cleanup
    turn_count: int = 0                    # Number of completed turns
    function_count: int = 0                # Number of functions executed
    session_token: Optional[str] = None    # Session resumption token (Gemini)
```

---

## 4.3 GEMINI_VOICES Array (16 Voices)

| # | ID | Name | Gender | Style |
|---|-----|------|--------|-------|
| 1 | Puck | Puck | Male | Upbeat, lively |
| 2 | Charon | Charon | Male | Informative, steady |
| 3 | Kore | Kore | Female | Firm, authoritative |
| 4 | Fenrir | Fenrir | Male | Excitable, bold |
| 5 | Aoede | Aoede | Female | Breezy, warm |
| 6 | Leda | Leda | Female | Youthful, approachable |
| 7 | Orus | Orus | Male | Firm, decisive |
| 8 | Zephyr | Zephyr | Male | Calm, breezy |
| 9 | Sage | Sage | Non-binary | Wise, thoughtful |
| 10 | Vale | Vale | Non-binary | Gentle, melodic |
| 11 | Solaria | Solaria | Female | Bright, energetic |
| 12 | River | River | Non-binary | Smooth, flowing |
| 13 | Ember | Ember | Female | Warm, passionate |
| 14 | Breeze | Breeze | Female | Light, airy |
| 15 | Cove | Cove | Male | Deep, resonant |
| 16 | Orbit | Orbit | Male | Futuristic, crisp |

Gender breakdown: 6 Male, 6 Female, 4 Non-binary.

---

## 4.4 Model Catalog (`backend/config.py`)

### Gemini Models

| Model ID | Display Name | Context | Cost In ($/1M) | Cost Out ($/1M) | Use Case |
|----------|-------------|---------|-----------------|-----------------|----------|
| `gemini-3-pro-preview` | Gemini 3 Pro | 1,000,000 | $2.00 | $12.00 | Flagship reasoning |
| `gemini-2.5-flash` | Gemini 2.5 Flash | 1,000,000 | $0.15 | $0.60 | Fast coding/streaming |
| `gemini-2.5-pro` | Gemini 2.5 Pro | 1,000,000 | $1.25 | $5.00 | Deep reasoning |
| `gemini-2.5-flash-image` | Gemini 2.5 Flash Image | 1,000,000 | $0.15 | $0.60 | Image generation |
| `gemini-embedding-001` | Gemini Embedding | 8,192 | $0.00 | $0.00 | RAG/embeddings |
| `veo-2.0-generate-001` | Veo 2.0 | 0 | $0.00 | $0.00 | Video generation |

### Claude Models

| Model ID | Display Name | Context | Cost In ($/1M) | Cost Out ($/1M) | Use Case |
|----------|-------------|---------|-----------------|-----------------|----------|
| `claude-opus-4-6` | Claude Opus 4.6 | 200,000 | $5.00 | $25.00 | Most intelligent |
| `claude-sonnet-4-6` | Claude Sonnet 4.6 | 200,000 | $3.00 | $15.00 | Fast + capable |
| `claude-haiku-4-5-20251001` | Claude Haiku 4.5 | 200,000 | $1.00 | $5.00 | Cheapest, routing |

---

## 4.5 Configuration Constants (`backend/config.py`)

| Constant | Value | Purpose |
|----------|-------|---------|
| `MODE` | `"standalone"` (default) | `"standalone"` or `"claude-code"` |
| `DEFAULT_GEMINI_MODEL` | `"gemini-2.5-flash"` | Default for Gemini API calls |
| `DEFAULT_CLAUDE_MODEL` | `"claude-sonnet-4-6"` | Default for Claude API calls |
| `VOX_AUDIO_SAMPLE_RATE_IN` | `16000` | PCM capture rate from microphone (Hz) |
| `VOX_AUDIO_SAMPLE_RATE_OUT` | `24000` | Playback rate for Gemini audio (Hz) |
| `VOX_DEFAULT_VOICE` | `"Puck"` | Default Gemini Live API voice |
| `VOX_DEFAULT_MODEL` | `"gemini-2.5-flash-native-audio-preview-12-2025"` | Gemini Live API model |
| `PROJECT_ROOT` | `Path(__file__).parent.parent` | Workspace root directory |
| `AGENTS_DIR` | `PROJECT_ROOT / "agents"` | Symlinked NLKE agents directory |
| `PLAYBOOKS_DIR` | `PROJECT_ROOT / "docs" / "playbooks-v2"` | Playbook markdown files |
| `KGS_DIR` | env `KGS_DIR` or `PROJECT_ROOT / "docs" / "KGS"` | Knowledge graph databases |
| `TOOLS_DIR` | `PROJECT_ROOT.parent / "tools"` | Python tool scripts |

### Integration Credential Constants

| Constant | Env Var | Platform |
|----------|---------|----------|
| `TELEGRAM_BOT_TOKEN` | `TELEGRAM_BOT_TOKEN` | Telegram |
| `WHATSAPP_TOKEN` | `WHATSAPP_TOKEN` | WhatsApp |
| `WHATSAPP_PHONE_ID` | `WHATSAPP_PHONE_ID` | WhatsApp |
| `WHATSAPP_VERIFY_TOKEN` | `WHATSAPP_VERIFY_TOKEN` | WhatsApp |
| `DISCORD_PUBLIC_KEY` | `DISCORD_PUBLIC_KEY` | Discord |
| `DISCORD_BOT_TOKEN` | `DISCORD_BOT_TOKEN` | Discord |
| `SLACK_BOT_TOKEN` | `SLACK_BOT_TOKEN` | Slack |
| `SLACK_SIGNING_SECRET` | `SLACK_SIGNING_SECRET` | Slack |
| `GMAIL_CLIENT_ID` | `GMAIL_CLIENT_ID` | Gmail |
| `GMAIL_CLIENT_SECRET` | `GMAIL_CLIENT_SECRET` | Gmail |
| `GMAIL_REFRESH_TOKEN` | `GMAIL_REFRESH_TOKEN` | Gmail |
| `SPOTIFY_CLIENT_ID` | `SPOTIFY_CLIENT_ID` | Spotify |
| `SPOTIFY_CLIENT_SECRET` | `SPOTIFY_CLIENT_SECRET` | Spotify |
| `SPOTIFY_REFRESH_TOKEN` | `SPOTIFY_REFRESH_TOKEN` | Spotify |
| `GOOGLE_CALENDAR_CREDENTIALS` | `GOOGLE_CALENDAR_CREDENTIALS` | Google Calendar |

---

## 4.6 Frontend TypeScript Interfaces

### Core Types (`frontend/src/types/index.ts` barrel)

Re-exports all interfaces from: `ai.ts`, `chat.ts`, `project.ts`, `kg.ts`, `studio.ts`, `memory.ts`, `expert.ts`, `tools.ts`, `vox.ts`.

### AI Types (`frontend/src/types/ai.ts`)

```typescript
interface CustomAiStyle {
  id: string;
  name: string;
  instructions: string;
  isDefault?: boolean;
}

interface ComposedStyle {
  name: string;
  weight: number;
}

interface Persona {
  id: string;
  name: string;
  baseInstructions: string;
  composedStyles: ComposedStyle[];
}

interface Agent {
  id: string;
  name: string;
  personaId: string;
  projectId: string;
}

interface ModelConfig {
  provider: 'gemini' | 'claude';
  model: string;
  thinkingBudget?: number;
}

interface NlkeAgent {
  name: string;
  category: string;
  description: string;
}

interface PlaybookMeta {
  filename: string;
  title: string;
  category: string;
  difficulty: string;
  sections: string[];
  word_count: number;
  score?: number;
}
```

### Chat Types (`frontend/src/types/chat.ts`)

```typescript
enum MessageAuthor {
  USER = 'user',
  ASSISTANT = 'assistant',
  SYSTEM = 'system',
  TOOL = 'tool',
}

type ChatMode = 'chat' | 'coding' | 'image-edit' | 'video-gen';

interface MessagePart {
  text?: string;
  imageUrl?: string;
  videoUrl?: string;
  sourceImageUrl?: string;
}

interface ToolCall {
  id?: string;
  name: string;
  args: any;
}

interface ToolResponse {
  name: string;
  tool_use_id?: string;
  response: { content: any; originalCode?: string };
}

interface GroundingMetadata {
  web: { uri: string; title: string };
}

interface Message {
  id: string;
  author: MessageAuthor;
  parts: MessagePart[];
  provider?: 'gemini' | 'claude';
  toolCall?: ToolCall;
  toolResponse?: ToolResponse;
  groundingMetadata?: GroundingMetadata[];
  thinkingContent?: string;
  regenerationData?: any;
}
```

### Project Types (`frontend/src/types/project.ts`)

```typescript
interface Project {
  id: string;
  name: string;
  createdAt: number;
  dependencySummary?: string;
}

interface ProjectFile {
  id: string;
  projectId: string;
  path: string;
  content: string;
  type: string;
  createdAt: number;
}
```

### Knowledge Graph Types (`frontend/src/types/kg.ts`)

```typescript
interface KGDatabase {
  id: string;
  filename: string;
  path: string;
  size_bytes: number;
  size_mb: number;
}

interface KGDatabaseStats {
  db_id: string;
  profile: string;
  node_count: number;
  edge_count: number;
  node_types: KGTypeCount[];
  edge_types: KGTypeCount[];
  has_fts: boolean;
}

interface KGTypeCount { type: string; count: number; }

interface KGNode {
  id: string;
  name: string;
  type: string;
  properties: Record<string, any>;
}

interface KGEdge {
  id: string;
  source: string;
  target: string;
  type: string;
  properties: Record<string, any>;
}

interface KGNodePage { nodes: KGNode[]; total: number; limit: number; offset: number; }
interface KGEdgePage { edges: KGEdge[]; total: number; limit: number; offset: number; }
interface KGSubgraph { nodes: KGNode[]; edges: KGEdge[]; }

interface KGSearchResult { node: KGNode; score: number; method: string; }
interface KGSearchResponse { results: KGSearchResult[]; query: string; mode: string; total: number; }

interface KGAnalyticsSummary {
  node_count: number; edge_count: number; density: number;
  components: number; avg_degree: number; clustering: number; isolates: number;
}

interface KGCentralityNode { id: string; name: string; type: string; score: number; }
interface KGCommunity { id: number; size: number; members: { id: string; name: string; type: string }[]; }

interface KGCompareResult {
  db_a: string; db_b: string;
  shared_nodes: number; unique_a: number; unique_b: number;
  jaccard_similarity: number; structural_comparison: Record<string, any>;
}

interface KGEmbeddingStatus {
  has_embeddings: boolean; count: number; dimensions: number | null;
  coverage_pct: number; strategies_available: string[];
}

interface KGProjectionPoint { id: string; name: string; type: string; x: number; y: number; }

type KGTab = 'explore' | 'search' | 'edit' | 'ingest' | 'analytics' | 'chat' | 'compare' | 'merge' | 'embeddings' | 'batch';
```

### Studio Types (`frontend/src/types/studio.ts`)

```typescript
type StudioMode = 'chat' | 'code' | 'visual';

interface StudioFile { path: string; content: string; language?: string; isEntry?: boolean; }

interface StudioProject {
  id: string; name: string; description: string;
  settings: StudioProjectSettings;
  files: Record<string, StudioFile>;
  chatHistory: StudioMessage[];
  currentVersion: number;
  createdAt: string; updatedAt: string;
}

interface StudioProjectSettings {
  techStack: 'react' | 'react-ts';
  cssFramework: 'tailwind' | 'css' | 'none';
  hasBackend: boolean;
  backendFramework?: 'fastapi' | 'express';
  dependencies: Record<string, string>;
}

interface StudioVersion {
  id: string; projectId: string; versionNumber: number;
  files: Record<string, StudioFile>;
  message: string; timestamp: string;
}

interface StudioMessage {
  id: string; role: 'user' | 'assistant' | 'system';
  content: string; timestamp: string;
  files?: StudioFileChange[];
  plan?: string;
  apiSpec?: StudioApiSpec | null;
  deps?: Record<string, string>;
}

interface StudioFileChange { path: string; content: string; action: 'create' | 'update' | 'delete'; }

interface StudioApiSpec {
  openapi: string;
  info: { title: string; version: string };
  paths: Record<string, any>;
  components?: { schemas?: Record<string, any> };
}

interface StudioApiEndpoint {
  method: string; path: string; summary?: string;
  parameters?: any[]; requestBody?: any; responses?: Record<string, any>;
}

interface StudioMockServerStatus { running: boolean; port?: number; pid?: number; endpoints?: StudioApiEndpoint[]; }

interface StudioSelection {
  componentName: string; elementTag: string; filePath: string;
  lineNumber?: number; props?: Record<string, any>;
  styles?: Record<string, string>; text?: string;
}

interface StudioEditorTab { path: string; isDirty: boolean; }

interface StudioStreamEvent {
  type: 'token' | 'thinking' | 'studio_plan' | 'studio_file' | 'studio_deps' | 'studio_api_spec' | 'done' | 'error';
  content?: string; path?: string; file_content?: string;
  deps?: Record<string, string>; api_spec?: StudioApiSpec;
}

interface StudioProjectSummary {
  id: string; name: string; description: string;
  updatedAt: string; fileCount: number; versionCount: number;
}
```

### Memory & Integration Types (`frontend/src/types/memory.ts`)

```typescript
interface Conversation {
  id: string; mode: string; source: string;
  started_at: string; last_message_at: string;
  message_count: number; summary: string;
  messages?: ConversationMessage[];
}

interface ConversationMessage {
  id: string; conversation_id: string; author: string;
  content: string; provider?: string; model?: string;
  metadata?: Record<string, any>; created_at: string;
}

interface MemoryNode {
  id: string; name: string; type: string;
  score: number; properties?: Record<string, any>;
}

interface MemoryStats {
  memory_nodes: number; conversations: number; messages: number;
  node_types: { type: string; count: number }[];
  injection_stats?: { total_injections: number; by_category: Record<string, number> };
}

interface Integration {
  id: string | null; platform: string; enabled: boolean;
  config_keys: string[]; message_count: number; user_label: string;
  created_at?: string; updated_at?: string;
}

interface IntegrationSetup { platform: string; steps: string[]; required_fields: string[]; }
```

### Expert Types (`frontend/src/types/expert.ts`)

```typescript
interface Expert {
  id: string; name: string; description: string;
  kg_db_id: string; kg_db_ids: string[];
  persona_name: string; persona_instructions: string; persona_style: string;
  retrieval_methods: string[];
  retrieval_alpha: number;   // Embedding weight (default 0.35)
  retrieval_beta: number;    // BM25/text weight (default 0.40)
  retrieval_gamma: number;   // Graph boost weight (default 0.15)
  retrieval_delta: number;   // Intent bonus weight (default 0.10)
  retrieval_limit: number;   // Max results (default 10)
  dimension_filters: Record<string, { min?: number; max?: number }>;
  playbook_skills: string[];
  custom_goal_mappings: Record<string, string[]>;
  icon: string; color: string; is_public: boolean;
  created_at: string; updated_at: string;
}

interface ExpertConversation {
  id: string; expert_id: string; title: string;
  message_count: number; created_at: string; last_message_at: string;
  messages?: ExpertMessage[];
}

interface ExpertMessage {
  id: string; conversation_id: string;
  author: 'user' | 'assistant'; content: string;
  sources: ExpertSource[]; retrieval_meta: Record<string, any>;
  created_at: string;
}

interface ExpertSource {
  id: string; name: string; type: string;
  score: number; method: string; db_id?: string;
}

interface KGOSSearchResult {
  node: { id: string; name: string; type: string; properties: Record<string, any> };
  score: number; method: string;
  scores: { embedding: number; text: number; graph: number; intent: number };
}

interface KGOSSearchResponse {
  results: KGOSSearchResult[]; query: string; intent: string;
  weights: { alpha: number; beta: number; gamma: number; delta: number };
  total: number;
}
```

### Tool Types (`frontend/src/types/tools.ts`)

```typescript
interface ToolParam {
  name: string;
  type: 'string' | 'text' | 'json' | 'integer' | 'float' | 'boolean';
  label: string; required: boolean; default: any;
  description: string; multiline: boolean;
}

interface ToolDetail {
  id: string; name: string; category: string; description: string;
  is_async: boolean; output_format: string; params: ToolParam[];
}

interface ToolSummary { id: string; name: string; description: string; is_async: boolean; param_count: number; }
interface ToolsListResponse { categories: string[]; tools: Record<string, ToolSummary[]>; total: number; }
interface ToolRunResult { success: boolean; result?: any; error?: string; traceback?: string; }
```

### VOX Types (`frontend/src/types/vox.ts`)

```typescript
interface VoxState {
  connected: boolean; mode: 'gemini' | 'claude' | null;
  voice: string; speaking: boolean; listening: boolean;
  turnCount: number; functionCount: number;
  sessionId: string | null;
  transcript: VoxTranscriptEntry[];
  functionLog: VoxFunctionEntry[];
  error: string | null; reconnecting: boolean;
}

interface VoxTranscriptEntry { role: 'user' | 'model' | 'system'; text: string; timestamp: number; }

interface VoxFunctionEntry {
  name: string; args: Record<string, any>; result?: any;
  serverHandled: boolean; timestamp: number;
  status: 'pending' | 'success' | 'error';
}

interface VoxConfig { voice: string; model: string; systemPrompt: string; }
interface VoxVoice { id: string; name: string; gender: string; style: string; }
type VoxMode = 'gemini' | 'claude';
```

### Game Types (`frontend/src/types/game.ts`)

```typescript
interface GameProject {
  id: string; name: string; description: string;
  status: 'draft' | 'interviewing' | 'generating' | 'playable' | 'editing';
  interview_data: Record<string, any>;
  game_design_doc: GameDesignDoc | null;
  files: Record<string, string>;
  settings: Record<string, any>;
  expert_id: string; current_version: number;
  created_at: string; updated_at: string;
}

interface GameDesignDoc {
  meta: {
    name: string; genre: string; unique_feature: string;
    starting_scenario: string; description: string;
  };
  player: {
    description: string; movement_style: 'free' | 'grid' | 'click';
    abilities: string[]; hp_system: string; progression: string[];
    base_stats: { hp: number; mp: number; strength: number; defense: number; speed: number };
  };
  world: { map_size: string; tile_theme: string; interactive_objects: string[]; };
  npcs: GameNPC[];
  enemies: GameEnemy[];
  systems: { combat: string; inventory: string; audio: string; };
  local_llm: { model: string; enabled: boolean; npc_intelligence: string; };
}

interface GameNPC {
  name: string; role: string; intelligence: string;
  dialogue_lines: number; personality: string; system_prompt?: string;
}

interface GameEnemy {
  name: string; hp: number; damage: number; speed: number;
  xp: number; color: string; behavior: string; is_boss?: boolean;
}

interface InterviewQuestion {
  id: string; story: 'player' | 'world' | 'technical';
  question: string; type: 'select' | 'multiselect' | 'text';
  options?: { value: string; label: string }[];
  default?: string | string[];
  kg_context: string[]; maps_to: string;
}

interface GameVersion {
  id: string; project_id: string; version_number: number;
  files: string; message: string; timestamp: string;
}
```

### Theme Types (`frontend/src/themes/index.ts`)

```typescript
type ThemeId = 'default' | 'crt' | 'scratch' | 'solarized' | 'sunset';

interface ThemeDefinition {
  id: ThemeId; name: string; description: string;
  vars: Record<string, string>;
  dataTheme: string;
  swatches: string[];
}
```

---

## 4.7 SQLite Schemas

### VOX Awareness Database (`backend/vox_awareness.db`)

```sql
CREATE TABLE IF NOT EXISTS page_visits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    page TEXT NOT NULL,
    timestamp REAL NOT NULL,
    duration REAL DEFAULT 0,
    metadata TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS error_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    error_type TEXT NOT NULL,
    message TEXT NOT NULL,
    page TEXT DEFAULT '',
    timestamp REAL NOT NULL,
    resolved INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS session_context (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_page_visits_ts ON page_visits(timestamp);
CREATE INDEX IF NOT EXISTS idx_error_log_ts ON error_log(timestamp);
```

### VOX Macros Database (`backend/vox_macros.db`)

```sql
CREATE TABLE IF NOT EXISTS macros (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    trigger_phrase TEXT NOT NULL,
    steps TEXT NOT NULL,          -- JSON array of {function, args, pipe_from?}
    error_policy TEXT DEFAULT 'abort',  -- "abort" | "skip" | "retry"
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_macros_trigger ON macros(trigger_phrase);
```

### Studio Projects Database (`backend/studio_projects.db`)

```sql
CREATE TABLE IF NOT EXISTS studio_projects (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL DEFAULT 'Untitled Project',
    description     TEXT NOT NULL DEFAULT '',
    settings        TEXT NOT NULL DEFAULT '{}',    -- JSON: StudioProjectSettings
    files           TEXT NOT NULL DEFAULT '{}',    -- JSON: Record<path, StudioFile>
    chat_history    TEXT NOT NULL DEFAULT '[]',    -- JSON: StudioMessage[]
    current_version INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL,                 -- ISO 8601 UTC
    updated_at      TEXT NOT NULL                  -- ISO 8601 UTC
);

CREATE TABLE IF NOT EXISTS studio_versions (
    id              TEXT PRIMARY KEY,
    project_id      TEXT NOT NULL,
    version_number  INTEGER NOT NULL,
    files           TEXT NOT NULL DEFAULT '{}',    -- JSON snapshot of all files
    message         TEXT NOT NULL DEFAULT '',
    timestamp       TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES studio_projects(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_versions_project
    ON studio_versions(project_id, version_number);
```

### Experts Database (`backend/experts.db`)

```sql
CREATE TABLE IF NOT EXISTS experts (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    kg_db_id TEXT NOT NULL,                         -- Primary KG database ID
    kg_db_ids TEXT DEFAULT '[]',                    -- JSON: additional KG IDs
    persona_name TEXT DEFAULT 'Expert',
    persona_instructions TEXT DEFAULT '',
    persona_style TEXT DEFAULT 'professional',
    retrieval_methods TEXT DEFAULT '["hybrid","intent"]', -- JSON array
    retrieval_alpha REAL DEFAULT 0.35,              -- Embedding weight
    retrieval_beta REAL DEFAULT 0.40,               -- BM25/text weight
    retrieval_gamma REAL DEFAULT 0.15,              -- Graph boost weight
    retrieval_delta REAL DEFAULT 0.10,              -- Intent bonus weight
    retrieval_limit INTEGER DEFAULT 10,
    dimension_filters TEXT DEFAULT '{}',            -- JSON: {dim: {min, max}}
    playbook_skills TEXT DEFAULT '[]',              -- JSON array of skill IDs
    custom_goal_mappings TEXT DEFAULT '{}',         -- JSON: {goal: [tools]}
    icon TEXT DEFAULT 'brain',
    color TEXT DEFAULT '#0ea5e9',
    is_public BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS expert_conversations (
    id TEXT PRIMARY KEY,
    expert_id TEXT NOT NULL REFERENCES experts(id) ON DELETE CASCADE,
    title TEXT DEFAULT '',
    message_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_message_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS expert_messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES expert_conversations(id) ON DELETE CASCADE,
    author TEXT NOT NULL,                -- 'user' | 'assistant'
    content TEXT NOT NULL,
    sources TEXT DEFAULT '[]',           -- JSON: ExpertSource[]
    retrieval_meta TEXT DEFAULT '{}',    -- JSON: {intent, weights, total_results, db_id}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### KG Standard Schema (`backend/services/kg_service.py` -- STANDARD_CREATE_SQL)

Used for newly created databases:

```sql
CREATE TABLE IF NOT EXISTS nodes (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL DEFAULT 'entity',
    properties TEXT DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS edges (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL REFERENCES nodes(id),
    target TEXT NOT NULL REFERENCES nodes(id),
    type TEXT NOT NULL DEFAULT 'relates_to',
    properties TEXT DEFAULT '{}',
    weight REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(type);
CREATE INDEX IF NOT EXISTS idx_nodes_name ON nodes(name);
CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source);
CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target);
CREATE INDEX IF NOT EXISTS idx_edges_type ON edges(type);

-- Full-text search virtual table with auto-sync triggers
CREATE VIRTUAL TABLE IF NOT EXISTS nodes_fts USING fts5(
    name, type, properties, content=nodes, content_rowid=rowid
);
CREATE TRIGGER IF NOT EXISTS nodes_ai AFTER INSERT ON nodes BEGIN
    INSERT INTO nodes_fts(rowid, name, type, properties)
    VALUES (new.rowid, new.name, new.type, new.properties);
END;
CREATE TRIGGER IF NOT EXISTS nodes_ad AFTER DELETE ON nodes BEGIN
    INSERT INTO nodes_fts(nodes_fts, rowid, name, type, properties)
    VALUES ('delete', old.rowid, old.name, old.type, old.properties);
END;
CREATE TRIGGER IF NOT EXISTS nodes_au AFTER UPDATE ON nodes BEGIN
    INSERT INTO nodes_fts(nodes_fts, rowid, name, type, properties)
    VALUES ('delete', old.rowid, old.name, old.type, old.properties);
    INSERT INTO nodes_fts(rowid, name, type, properties)
    VALUES (new.rowid, new.name, new.type, new.properties);
END;
```

---

## 4.8 KG Schema Profiles (6 Profiles)

The KG service auto-detects which schema profile an existing SQLite database uses by probing table and column names:

| Profile | Node Table | Edge Table | Node ID Col | Node Name Col | Node Type Col | Edge Source Col | Edge Target Col | Edge Type Col |
|---------|-----------|-----------|------------|--------------|--------------|----------------|----------------|--------------|
| **unified** | `unified_nodes` | `unified_edges` | `node_id` | `name` | `node_type` | `source_node_id` | `target_node_id` | `edge_type` |
| **standard** | `nodes` | `edges` | `id` | `name` | `type` | `source` | `target` | `type` |
| **claude** | `nodes` | `edges` | `node_id` | `name` | `node_type` | `source_node_id` | `target_node_id` | `edge_type` |
| **hal** | `nodes` | `edges` | `id` | `name` | `type` | `source_id` | `target_id` | `edge_type` |
| **from_node** | `nodes` | `edges` | `id` | `name` | `type` | `from_node` | `to_node` | `type` |
| **entities** | `entities` | `relations` | `id` | `name` | `type` | `source_id` | `target_id` | `relation_type` |
| **heuristic** | *(auto-detected)* | *(auto-detected)* | *(probed)* | *(probed)* | *(probed)* | *(probed)* | *(probed)* | *(probed)* |

Heuristic fallback tries common column names: `id`/`node_id`/`entity_id` for ID, `name`/`node_name`/`title` for name, etc.

---

## 4.9 VOX Function Declarations Registry (34 Functions)

### Browser-Side Functions (6) -- executed in frontend JavaScript

| # | Function | Description | Required Params |
|---|----------|-------------|-----------------|
| 1 | `navigate_page` | Navigate workspace to a page | `path: string` |
| 2 | `get_current_page` | Get current page path | *(none)* |
| 3 | `get_workspace_state` | Get active provider, model, page, theme, project count | *(none)* |
| 4 | `switch_model` | Switch AI provider and model | `provider: string`, `model: string` |
| 5 | `switch_theme` | Switch visual theme | `theme_id: string` |
| 6 | `read_page_content` | Read visible text of current page | *(none)* |

### Core Workspace Tools (6) -- executed on backend

| # | Function | Description | Required Params |
|---|----------|-------------|-----------------|
| 7 | `run_tool` | Execute any of 58+ registered tools | `tool_id: string` |
| 8 | `list_tools` | List all tools with categories | *(none)* |
| 9 | `query_kg` | Hybrid semantic search on a KG | `database_id: string`, `query: string` |
| 10 | `list_kgs` | List all KG databases | *(none)* |
| 11 | `run_agent` | Execute an NLKE agent | `agent_name: string`, `input: string` |
| 12 | `list_agents` | List all NLKE agents | *(none)* |

### Direct Developer Tool Shortcuts (5) -- proxy to tools_service

| # | Function | Description | Required Params |
|---|----------|-------------|-----------------|
| 13 | `generate_react_component` | Generate React/Vue/Svelte component | `name: string`, `description: string` |
| 14 | `generate_fastapi_endpoint` | Generate FastAPI/Express/Flask endpoint | `description: string` |
| 15 | `scan_code_security` | Scan for SQL injection, XSS, secrets, eval, path traversal | `code: string` |
| 16 | `analyze_code_complexity` | Cyclomatic and cognitive complexity metrics | `code: string` |
| 17 | `generate_tests` | Generate test cases from function signatures | `code: string` |

### Guided Tours (2)

| # | Function | Description | Required Params |
|---|----------|-------------|-----------------|
| 18 | `start_guided_tour` | Start voice-narrated UI tour of a page | `page: string` (optional) |
| 19 | `get_available_tours` | List all available tours with step counts | *(none)* |

### Workspace Control / Jarvis Mode (5)

| # | Function | Description | Required Params |
|---|----------|-------------|-----------------|
| 20 | `create_project` | Create a new AI Studio project | `name: string` |
| 21 | `list_projects` | List all Studio projects | *(none)* |
| 22 | `run_workflow` | Execute a workflow template | `workflow_name: string` |
| 23 | `search_playbooks` | Search through 53 playbooks | `query: string` |
| 24 | `search_kg` | Enhanced KG search with filters | `database_id: string`, `query: string` |

### KG Studio Control (3)

| # | Function | Description | Required Params |
|---|----------|-------------|-----------------|
| 25 | `get_kg_analytics` | Graph analytics: centrality, communities | `database_id: string` |
| 26 | `cross_kg_search` | Search across multiple KGs simultaneously | `query: string` |
| 27 | `ingest_to_kg` | AI entity extraction into a KG | `database_id: string`, `text: string` |

### Expert Control (2)

| # | Function | Description | Required Params |
|---|----------|-------------|-----------------|
| 28 | `chat_with_expert` | Send message to KG-OS expert | `expert_id: string`, `message: string` |
| 29 | `list_experts` | List all KG-OS experts | *(none)* |

### Voice Macros (4)

| # | Function | Description | Required Params |
|---|----------|-------------|-----------------|
| 30 | `create_macro` | Create multi-step voice command sequence | `name: string`, `trigger_phrase: string`, `steps: string` (JSON) |
| 31 | `list_macros` | List all saved macros | *(none)* |
| 32 | `run_macro` | Execute a macro by ID or trigger phrase | `macro_id: string` |
| 33 | `delete_macro` | Delete a saved macro | `macro_id: string` |

### Thermal Monitoring (1)

| # | Function | Description | Required Params |
|---|----------|-------------|-----------------|
| 34 | `check_thermal` | Check device temperature and battery | *(none)* |

### Async-Eligible Functions

These functions run in background tasks (potentially slow): `ingest_to_kg`, `run_workflow`, `cross_kg_search`, `run_agent`.

---

# Part 5: Quick Reference Tables

## 5.1 Router Mounting Order (`backend/main.py`)

Routers are mounted in this exact order. All use `prefix="/api"` except VOX (no prefix for WebSocket).

| # | Router Module | Prefix | Tags/Domain |
|---|--------------|--------|-------------|
| 1 | `chat` | `/api` | Chat streaming |
| 2 | `coding` | `/api` | Coding with tool use |
| 3 | `agents` | `/api` | NLKE agent CRUD + execution |
| 4 | `playbooks` | `/api` | Playbook search + retrieval |
| 5 | `workflows` | `/api` | Workflow templates + execution |
| 6 | `builder` | `/api` | Legacy web app plan + generate |
| 7 | `media` | `/api` | Image edit + video gen |
| 8 | `interchange` | `/api` | JSON import/export, mode toggle |
| 9 | `kg` | `/api` | KG Studio (33 endpoints) |
| 10 | `studio` | `/api` | Studio projects (18 endpoints) |
| 11 | `memory` | `/api` | Conversation memory |
| 12 | `integrations` | `/api` | Platform integrations |
| 13 | `experts` | `/api` | Expert Builder + KG-OS |
| 14 | `tools` | `/api` | Tools playground |
| 15 | `vox` | *(none)* | VOX voice (WS at `/ws/vox`, REST at `/api/vox/*`) |
| 16 | `games` | `/api` | Phaser 3 RPG game projects |

Additionally: Phaser static files served at `/docs/phaser` if directory exists. Health (`/api/health`) and models (`/api/models`) are defined directly in `main.py`.

---

## 5.2 Complete API Endpoint Table

### Global Endpoints (main.py)

| Method | Path | Purpose | Response |
|--------|------|---------|----------|
| GET | `/api/health` | Health check + mode detection | `{status, mode, gemini_configured, claude_configured}` |
| GET | `/api/models` | Available model catalog | `{gemini: {...}, claude?: {...}}` |

### Chat Router

| Method | Path | Purpose | Request Body | Response |
|--------|------|---------|-------------|----------|
| POST | `/api/chat/stream` | SSE streaming chat | `{messages, provider, model, persona?, customStyles?, useWebSearch?, thinkingBudget?}` | SSE stream of tokens/thinking/grounding |

### Coding Router

| Method | Path | Purpose | Request Body | Response |
|--------|------|---------|-------------|----------|
| POST | `/api/coding/stream` | Coding with tool use | `{history, projects, persona, customStyles, useWebSearch, provider, model, thinkingBudget?}` | SSE stream with tool calls |

### Agents Router

| Method | Path | Purpose | Request Body | Response |
|--------|------|---------|-------------|----------|
| GET | `/api/agents` | List 33 NLKE agents | -- | `{agents: NlkeAgent[]}` |
| POST | `/api/agents/{name}/run` | Execute an agent | `{workload: any}` | `{result: any}` |
| GET | `/api/agents/{name}/example` | Get agent example input | -- | `{example: any}` |

### Pipelines Router

| Method | Path | Purpose | Request Body | Response |
|--------|------|---------|-------------|----------|
| POST | `/api/pipelines/run` | Run agent pipeline | `{steps: any[]}` | `{results: any}` |

### Playbooks Router

| Method | Path | Purpose | Request Body | Response |
|--------|------|---------|-------------|----------|
| GET | `/api/playbooks` | List all 53 playbooks | -- | `{playbooks: PlaybookMeta[]}` |
| GET | `/api/playbooks/search?q=&category?=` | Search playbooks | -- (query params) | `{results: PlaybookMeta[]}` |
| GET | `/api/playbooks/categories` | List playbook categories | -- | `{categories: string[]}` |
| GET | `/api/playbooks/{filename}` | Get playbook content | -- | `{filename, title, content, ...}` |

### Workflows Router

| Method | Path | Purpose | Request Body | Response |
|--------|------|---------|-------------|----------|
| GET | `/api/workflows/templates` | List 4 workflow templates | -- | `{templates: WorkflowTemplate[]}` |
| POST | `/api/workflows/plan` | Plan a workflow from goal | `{goal, template?}` | `{steps: WorkflowStep[]}` |
| POST | `/api/workflows/execute` | Execute workflow (SSE) | `{steps, goal}` | SSE stream |

### Builder Router (Legacy)

| Method | Path | Purpose | Request Body | Response |
|--------|------|---------|-------------|----------|
| POST | `/api/builder/plan` | Generate web app plan | `{idea, provider?, model?}` | `{plan: object}` |
| POST | `/api/builder/generate` | Generate full code | `{plan, theme, provider?, model?}` | `Record<string, string>` |

### Media Router

| Method | Path | Purpose | Request Body | Response |
|--------|------|---------|-------------|----------|
| POST | `/api/image/edit` | Edit image with AI | `FormData: {prompt, file}` | `any[]` |
| POST | `/api/video/generate` | Generate video with Veo | `FormData: {prompt, file?}` | `{operationName}` |
| GET | `/api/video/status?operationName=` | Poll video generation | -- (query param) | `{done, videoUrl?, error?}` |

### Interchange Router

| Method | Path | Purpose | Request Body | Response |
|--------|------|---------|-------------|----------|
| POST | `/api/export` | Export workspace JSON | `{data: any}` | `{exported: any}` |
| POST | `/api/import` | Import workspace JSON | `{data: any}` | `{imported: any}` |
| GET | `/api/mode` | Get current mode | -- | `{mode: string}` |
| POST | `/api/mode` | Set mode | `{mode: "standalone" | "claude-code"}` | `{mode: string}` |

### Config Router

| Method | Path | Purpose | Request Body | Response |
|--------|------|---------|-------------|----------|
| GET | `/api/config/keys/status` | Check API key status | -- | `{gemini: bool, anthropic: bool, mode: string}` |
| POST | `/api/config/keys` | Set API keys at runtime | `{gemini_key?, anthropic_key?}` | `{success: bool}` |

### KG Studio Router (33 endpoints)

| Method | Path | Purpose | Request Body | Response |
|--------|------|---------|-------------|----------|
| GET | `/api/kg/databases` | List all KG databases (57+) | -- | `[{id, filename, path, size_bytes, size_mb, is_kg}]` |
| POST | `/api/kg/databases` | Create new KG database | `{name}` | `{id, filename, path}` |
| GET | `/api/kg/databases/{id}/stats` | Get database statistics | -- | `KGDatabaseStats` |
| GET | `/api/kg/databases/{id}/nodes` | Paginated node list | `?node_type=&search=&limit=&offset=` | `KGNodePage` |
| GET | `/api/kg/databases/{id}/nodes/{nid}` | Get single node | -- | `KGNode` |
| GET | `/api/kg/databases/{id}/nodes/{nid}/neighbors` | Get node neighborhood | `?depth=&limit=` | `KGSubgraph` |
| POST | `/api/kg/databases/{id}/nodes` | Create node | `{name, type, properties?}` | `KGNode` |
| PUT | `/api/kg/databases/{id}/nodes/{nid}` | Update node | `{name?, type?, properties?}` | `KGNode` |
| DELETE | `/api/kg/databases/{id}/nodes/{nid}` | Delete node + edges | -- | `{deleted: bool}` |
| GET | `/api/kg/databases/{id}/edges` | Paginated edge list | `?edge_type=&limit=&offset=` | `KGEdgePage` |
| POST | `/api/kg/databases/{id}/edges` | Create edge | `{source, target, type, properties?}` | `KGEdge` |
| PUT | `/api/kg/databases/{id}/edges/{eid}` | Update edge | `{type?, properties?}` | `KGEdge` |
| DELETE | `/api/kg/databases/{id}/edges/{eid}` | Delete edge | -- | `{deleted: bool}` |
| GET | `/api/kg/databases/{id}/types` | List node + edge types | -- | `{node_types, edge_types}` |
| POST | `/api/kg/databases/{id}/bulk` | Bulk create nodes + edges | `{nodes: [], edges: []}` | `{nodes_created, edges_created}` |
| POST | `/api/kg/databases/{id}/search` | Hybrid semantic search | `{query, mode?, limit?, alpha?, beta?, gamma?}` | `KGSearchResponse` |
| POST | `/api/kg/search/multi` | Cross-KG search | `{query, db_ids: [], mode?, limit?}` | `{results: Record<dbId, KGSearchResult[]>}` |
| POST | `/api/kg/databases/{id}/chat` | RAG chat (SSE) | `{query, history?, mode?, limit?}` | SSE stream with source citations |
| POST | `/api/kg/databases/{id}/ingest` | AI entity extraction | `{text, method?, source?}` | `{nodes_created, edges_created}` |
| GET | `/api/kg/databases/{id}/analytics/summary` | Graph summary metrics | -- | `KGAnalyticsSummary` |
| GET | `/api/kg/databases/{id}/analytics/centrality` | Node centrality | `?metric=&top_k=` | `KGCentralityNode[]` |
| GET | `/api/kg/databases/{id}/analytics/communities` | Community detection | -- | `KGCommunity[]` |
| POST | `/api/kg/databases/{id}/analytics/path` | Find path between nodes | `{source_node, target_node}` | `{path: string[], edges: KGEdge[]}` |
| POST | `/api/kg/compare` | Compare two KGs structurally | `{db_id_a, db_id_b}` | `KGCompareResult` |
| POST | `/api/kg/diff` | Diff two KGs | `{db_id_a, db_id_b}` | Diff details |
| POST | `/api/kg/merge` | Merge KGs | `{source_db, target_db, strategy?}` | Merge results |
| POST | `/api/kg/databases/{id}/batch/delete-by-type` | Batch delete nodes by type | `{node_type}` | `{deleted_count: int}` |
| POST | `/api/kg/databases/{id}/batch/retype` | Batch retype nodes | `{old_type, new_type}` | `{updated_count: int}` |
| GET | `/api/kg/databases/{id}/embedding-status` | Embedding coverage stats | -- | `KGEmbeddingStatus` |
| GET | `/api/kg/databases/{id}/embeddings/projection` | 2D embedding projection | `?method=&max_points=` | `KGProjectionPoint[]` |
| POST | `/api/kg/databases/{id}/embeddings/generate` | Generate embeddings | `{strategy?}` | `{generated: int}` |
| GET | `/api/kg/databases/{id}/embeddings/quality` | Embedding quality metrics | -- | Quality scores |

### Studio Router (18 endpoints)

| Method | Path | Purpose | Request Body | Response |
|--------|------|---------|-------------|----------|
| POST | `/api/studio/stream` | AI streaming (generate/refine) | `{messages, mode, project, ...}` | SSE stream of StudioStreamEvent |
| POST | `/api/studio/projects` | Create project | `{name, description?}` | `StudioProject` |
| GET | `/api/studio/projects` | List projects | -- | `StudioProjectSummary[]` |
| GET | `/api/studio/projects/{id}` | Load full project | -- | `StudioProject` |
| PUT | `/api/studio/projects/{id}` | Update project | `{name?, files?, settings?, chat_history?}` | `{updated: bool}` |
| DELETE | `/api/studio/projects/{id}` | Delete project + versions | -- | `{deleted: bool}` |
| POST | `/api/studio/projects/{id}/save` | Save version snapshot | `{message?}` | `StudioVersion` |
| GET | `/api/studio/projects/{id}/versions` | List versions | -- | `StudioVersion[]` |
| POST | `/api/studio/projects/{id}/versions/{ver}/restore` | Restore version | -- | `StudioProject` |
| GET | `/api/studio/projects/{id}/export` | Download ZIP archive | `?scope=` | Binary ZIP |
| POST | `/api/studio/projects/{id}/mock/start` | Start mock server | -- | `StudioMockServerStatus` |
| GET | `/api/studio/projects/{id}/api-spec` | Get OpenAPI spec | -- | `StudioApiSpec` |
| GET | `/api/studio/projects/{id}/types` | Get TypeScript types | -- | TypeScript source |

### Memory Router

| Method | Path | Purpose | Request Body | Response |
|--------|------|---------|-------------|----------|
| GET | `/api/memory/conversations` | List conversations | `?mode=&limit=` | `Conversation[]` |
| GET | `/api/memory/conversations/{id}` | Get conversation | -- | `Conversation` |
| GET | `/api/memory/conversations/{id}/messages` | Get messages | `?limit=&offset=` | `ConversationMessage[]` |
| DELETE | `/api/memory/conversations/{id}` | Delete conversation | -- | `{deleted: bool}` |
| POST | `/api/memory/search` | Search memory | `{query, limit?}` | `MemoryNode[]` |
| GET | `/api/memory/stats` | Memory statistics | -- | `MemoryStats` |

### Integrations Router

| Method | Path | Purpose | Request Body | Response |
|--------|------|---------|-------------|----------|
| GET | `/api/integrations` | List all integrations | -- | `Integration[]` |
| POST | `/api/integrations/{platform}/configure` | Configure integration | `{config: Record<str,str>, user_label?}` | `{configured: bool}` |
| POST | `/api/integrations/{platform}/test` | Test integration | -- | `{success: bool, message?}` |
| POST | `/api/integrations/{platform}/enable` | Enable integration | -- | `{enabled: bool}` |
| POST | `/api/integrations/{platform}/disable` | Disable integration | -- | `{disabled: bool}` |
| DELETE | `/api/integrations/{platform}` | Delete integration | -- | `{deleted: bool}` |
| GET | `/api/integrations/{platform}/setup` | Get setup instructions | -- | `IntegrationSetup` |

### Experts Router (15 endpoints)

| Method | Path | Purpose | Request Body | Response |
|--------|------|---------|-------------|----------|
| GET | `/api/experts` | List all experts | -- | `Expert[]` |
| POST | `/api/experts` | Create expert | `Expert fields` | `Expert` |
| GET | `/api/experts/{id}` | Get expert | -- | `Expert` |
| PUT | `/api/experts/{id}` | Update expert | `Partial<Expert>` | `Expert` |
| DELETE | `/api/experts/{id}` | Delete expert + conversations | -- | `{deleted: bool}` |
| POST | `/api/experts/{id}/duplicate` | Duplicate expert | -- | `Expert` |
| POST | `/api/experts/{id}/chat` | Expert chat (SSE) | `{query, conversation_id?, history?}` | SSE stream: sources, content, done |
| GET | `/api/experts/{id}/conversations` | List conversations | -- | `ExpertConversation[]` |
| GET | `/api/experts/{id}/conversations/{cid}` | Get conversation + messages | -- | `ExpertConversation` with `messages` |
| DELETE | `/api/experts/{id}/conversations/{cid}` | Delete conversation | -- | `{deleted: bool}` |
| POST | `/api/experts/kgos/query/{db_id}` | Direct KG-OS query | `{query, alpha?, beta?, gamma?, delta?, limit?}` | `KGOSSearchResponse` |
| POST | `/api/experts/kgos/impact/{db_id}/{nid}` | Impact analysis | `{direction?, max_depth?}` | Impact graph |
| POST | `/api/experts/kgos/compose/{db_id}` | Composition planning | `{goal, max_steps?}` | Composed workflow |
| POST | `/api/experts/kgos/similar/{db_id}/{nid}` | Similar nodes | `?k=` | Similar node list |
| GET | `/api/experts/kgos/dimensions` | List 56 standard dimensions | -- | `{dimensions: [...]}` |

### Tools Router

| Method | Path | Purpose | Request Body | Response |
|--------|------|---------|-------------|----------|
| GET | `/api/tools` | List 58+ tools (11 categories) | -- | `ToolsListResponse` |
| GET | `/api/tools/{id}` | Get tool definition + params | -- | `ToolDetail` |
| POST | `/api/tools/{id}/run` | Execute a tool | `{params: Record<string,any>}` | `ToolRunResult` |
| POST | `/api/tools/{id}/run/stream` | Execute tool (SSE) | `{params: Record<string,any>}` | SSE stream |

### VOX Router

| Method | Path | Purpose | Request Body | Response |
|--------|------|---------|-------------|----------|
| GET | `/api/vox/status` | VOX availability + active sessions | -- | `{gemini_available, claude_available, active_sessions}` |
| GET | `/api/vox/voices` | List 16 voices | -- | `{voices: VoxVoice[]}` |
| GET | `/api/vox/functions` | List 34 function declarations | -- | `{functions: [...], count: 34}` |
| POST | `/api/vox/function/{fn_name}` | Execute workspace function | `{args: dict}` | `{name, result}` |
| POST | `/api/vox/awareness` | Log awareness event | `AwarenessEvent` | `{success, visit_id? / error_id?}` |
| GET | `/api/vox/awareness` | Get current awareness context | -- | `{prompt, recent_pages, unresolved_errors, page_stats}` |
| GET | `/api/vox/tours` | List 11 guided tours | -- | `{tours: [...], count}` |
| GET | `/api/vox/tours/{page}` | Get tour steps for page | -- | `{page, name, description, steps}` |
| GET | `/api/vox/macros` | List saved macros | -- | `{macros: [...]}` |
| POST | `/api/vox/macros` | Create macro | `MacroCreateRequest` | `{success, macro}` |
| DELETE | `/api/vox/macros/{macro_id}` | Delete macro | -- | `{success: bool}` |
| POST | `/api/vox/macros/{macro_id}/run` | Execute macro | -- | `{success, results}` |
| GET | `/api/vox/thermal` | Device temperature + battery | -- | Thermal data |
| WS | `/ws/vox` | Bidirectional voice WebSocket | *(see 5.3)* | *(see 5.3)* |

### Games Router

| Method | Path | Purpose | Request Body | Response |
|--------|------|---------|-------------|----------|
| GET | `/api/games` | List all game projects | -- | `GameProject[]` |
| POST | `/api/games` | Create game project | `{name, description?}` | `GameProject` |
| GET | `/api/games/{id}` | Get game project | -- | `GameProject` |
| PUT | `/api/games/{id}` | Update game project | `GameUpdate` | `GameProject` |
| DELETE | `/api/games/{id}` | Delete game project | -- | `{status: "deleted"}` |
| GET | `/api/games/interview/questions` | Get interview questions | -- | `InterviewQuestion[]` |
| POST | `/api/games/{id}/interview` | Submit interview answer | `{question_id, answer}` | Updated interview data |
| POST | `/api/games/{id}/synthesize` | Synthesize GDD from answers | -- | `GameDesignDoc` |
| POST | `/api/games/{id}/generate` | Generate game code (SSE) | `{kg_context?}` | SSE stream of files |
| POST | `/api/games/{id}/refine` | Refine game code (SSE) | `{prompt, files?}` | SSE stream of files |
| POST | `/api/games/{id}/save` | Save version snapshot | -- | `GameVersion` |
| GET | `/api/games/{id}/versions` | List versions | -- | `GameVersion[]` |
| POST | `/api/games/{id}/versions/{ver}/restore` | Restore version | -- | `GameProject` |
| GET | `/api/games/{id}/export` | Download ZIP archive | -- | Binary ZIP |
| POST | `/api/games/{id}/chat` | Game expert chat (SSE) | `{query, conversation_id?, history?}` | SSE stream |
| POST | `/api/games/{id}/extract-patterns` | Extract game patterns | -- | `{patterns, count}` |
| GET | `/api/games/llm/status` | Local LLM status | -- | LLM status |
| POST | `/api/games/llm/load` | Load local LLM model | `{model_type}` | Load result |
| POST | `/api/games/llm/unload` | Unload local LLM | -- | Unload result |
| POST | `/api/games/llm/chat` | Chat with NPC via local LLM | `{npc_name, system_prompt, message, history?}` | Chat response |

---

## 5.3 WebSocket Message Protocol (`/ws/vox`)

### Client-to-Server Messages

| Message Type | Fields | Purpose |
|-------------|--------|---------|
| `start` | `{type: "start", mode: "gemini"\|"claude", model?, voice?, systemPrompt?, session_token?}` | Initialize a voice session |
| `audio` | `{type: "audio", data: "<base64 PCM>"}` | Send raw PCM audio chunk (Gemini mode) |
| `text` | `{type: "text", text: "<message>"}` | Send text input (both modes) |
| `browser_function_result` | `{type: "browser_function_result", name: "<fn>", result: {...}, fn_call_id: "<id>"}` | Return browser-executed function result to Gemini |
| `end` | `{type: "end"}` | Terminate the session |

### Server-to-Client Messages

| Message Type | Fields | Purpose |
|-------------|--------|---------|
| `setup_complete` | `{type: "setup_complete", sessionId, mode, resumed?}` | Session ready |
| `audio` | `{type: "audio", data: "<base64 PCM>"}` | Gemini audio response chunk |
| `text` | `{type: "text", text: "<response text>"}` | Text response (both modes) |
| `turn_complete` | `{type: "turn_complete", turn: <number>}` | Model finished responding |
| `function_call` | `{type: "function_call", name, args, server_handled, fn_call_id?, async?}` | Function call (server or browser) |
| `function_result` | `{type: "function_result", name, result}` | Server-executed function result |
| `async_task_started` | `{type: "async_task_started", task_id, function}` | Background task initiated |
| `async_task_complete` | `{type: "async_task_complete", task_id, function, result}` | Background task finished |
| `start_tour` | `{type: "start_tour", page, tour}` | Trigger guided tour overlay |
| `transcript` | `{type: "transcript", role: "user"\|"model", text}` | Audio transcription |
| `go_away` | `{type: "go_away", session_token, message}` | Session about to terminate; reconnect with token |
| `error` | `{type: "error", message}` | Error message |

---

## 5.4 Model Routing Decision Table (`backend/services/model_router.py`)

The `route(task_type, complexity, budget_preference, context_length)` function evaluates rules in priority order:

| Priority | Condition | Provider | Model | Reason |
|----------|-----------|----------|-------|--------|
| 1 | `task_type == "video"` | gemini | `veo-2.0-generate-001` | Video generation is Gemini-only |
| 2 | `task_type == "image"` | gemini | `gemini-2.5-flash-image` | Image generation via Gemini |
| 3 | `task_type == "embedding"` | gemini | `gemini-embedding-001` | Embeddings via Gemini |
| 4 | `context_length > 150000` | gemini | `gemini-2.5-pro` | Large context requires Gemini's 1M window |
| 5 | `MODE == "claude-code"` + cheap/low | gemini | `gemini-2.5-flash` | Fast & cheap (claude-code mode) |
| 6 | `MODE == "claude-code"` + other | gemini | `gemini-2.5-pro` | Best Gemini reasoning (claude-code mode) |
| 7 | `budget == "cheap"` + `complexity == "low"` | gemini | `gemini-2.5-flash` | Cheapest option for simple tasks |
| 8 | `budget == "cheap"` + other | claude | `claude-haiku-4-5-20251001` | Budget Claude for medium tasks |
| 9 | `task_type == "coding"` + `complexity == "high"` | claude | `claude-sonnet-4-6` | Claude excels at complex coding |
| 10 | `task_type == "coding"` + other | gemini | `gemini-2.5-flash` | Fast coding with Gemini Flash |
| 11 | `task_type == "reasoning"` + `complexity == "high"` | claude | `claude-opus-4-6` | Claude Opus for deep reasoning |
| 12 | `task_type == "reasoning"` + other | claude | `claude-sonnet-4-6` | Claude Sonnet for reasoning |
| 13 | `budget == "quality"` | claude | `claude-opus-4-6` | Highest quality model |
| 14 | `complexity == "high"` (default) | claude | `claude-sonnet-4-6` | Balanced quality for complex tasks |
| 15 | Default fallback | gemini | `gemini-2.5-flash` | Fast default for general tasks |

---

## 5.5 Key Constants Reference Table

### Audio / Voice

| Constant | Value | Unit | Location |
|----------|-------|------|----------|
| PCM input sample rate | 16,000 | Hz | `config.py: VOX_AUDIO_SAMPLE_RATE_IN` |
| PCM output sample rate | 24,000 | Hz | `config.py: VOX_AUDIO_SAMPLE_RATE_OUT` |
| Default voice | `"Puck"` | -- | `config.py: VOX_DEFAULT_VOICE` |
| Default Live API model | `gemini-2.5-flash-native-audio-preview-12-2025` | -- | `config.py: VOX_DEFAULT_MODEL` |
| Claude tool_use rounds | 5 (max) | iterations | `routers/vox.py: _claude_text_pipeline` |
| Claude max tokens | 2,048 | tokens | `routers/vox.py: _claude_text_pipeline` |
| Total voices | 16 | -- | `vox_service.py: GEMINI_VOICES` |
| Total function declarations | 34 | -- | `vox_service.py: build_function_declarations` |

### Retrieval / Search

| Constant | Value | Context |
|----------|-------|---------|
| Default alpha (embedding weight) | 0.35 / 0.40 | Expert / KG search |
| Default beta (BM25/text weight) | 0.40 / 0.45 | Expert / KG search |
| Default gamma (graph boost weight) | 0.15 | Both |
| Default delta (intent bonus weight) | 0.10 | Expert KG-OS only |
| Expert retrieval limit | 10 | Default max results |
| KG search default limit | 20 | Per apiService |
| Cross-KG max databases | 10 | `vox.py: cross_kg_search` |
| Expert generation temperature | 0.7 | `expert_service.py` |
| Expert max output tokens | 4,096 | `expert_service.py` |
| Expert graph neighbor depth | 1 | Top 3 results expanded |
| Expert graph neighbor limit | 10 | Per result |

### Database / Storage

| Constant | Value | Purpose |
|----------|-------|---------|
| Session ID length | 8 chars | UUID[:8] |
| Macro ID length | 8 chars | UUID[:8] |
| Expert ID length | 8 chars | UUID[:8] |
| Conversation ID length | 12 chars | UUID[:12] |
| Message ID length | 12 chars | UUID[:12] |
| Node ID length | 16 chars | MD5[:16] of `type:name` |
| Edge ID length | 16 chars | MD5[:16] of `source:type:target` |
| SQLite journal mode | WAL | All databases |
| Awareness cleanup max age | 24 hours | `vox_awareness.py` |
| Schema profiles | 6 + heuristic | `kg_service.py: PROFILES` |
| KG databases supported | 57+ | Auto-discovered in `KGS_DIR` |

### Async Functions

| Function | Runs Async | Reason |
|----------|-----------|--------|
| `ingest_to_kg` | Yes | AI extraction is slow |
| `run_workflow` | Yes | Multi-step execution |
| `cross_kg_search` | Yes | Multiple DB queries |
| `run_agent` | Yes | Agent execution chain |

---

## 5.6 Theme Comparison Table

| Property | Default | Deluxe-CRT | Scratch | Solarized Zen | Sunset Warm |
|----------|---------|------------|---------|---------------|-------------|
| **ID** | `default` | `crt` | `scratch` | `solarized` | `sunset` |
| **Vibe** | Clean dark slate | Retro amber terminal | B&W pen doodle | Warm earth tones | Coral & rose gold |
| `--t-bg` | `#111827` | `#0a0a08` | `#fafaf8` | `#002b36` | `#1a1218` |
| `--t-surface` | `#1f2937` | `#1a1810` | `#f0efe8` | `#073642` | `#2a1f25` |
| `--t-surface2` | `#374151` | `#2a2818` | `#e8e8e0` | `#0a4050` | `#3a2f35` |
| `--t-border` | `#374151` | `#3a3520` | `#1a1a1a` | `#586e75` | `#4a3540` |
| `--t-primary` | `#0ea5e9` | `#ffb000` | `#1a1a1a` | `#2aa198` | `#ff6b6b` |
| `--t-primary-h` | `#38bdf8` | `#ffc840` | `#333333` | `#35c4ba` | `#ff8a8a` |
| `--t-accent1` | `#a78bfa` | `#ff8c00` | `#555555` | `#b58900` | `#ffa94d` |
| `--t-accent2` | `#f472b6` | `#66bb6a` | `#888888` | `#cb4b16` | `#e8a0bf` |
| `--t-text` | `#f1f5f9` | `#ffe4b0` | `#1a1a1a` | `#eee8d5` | `#ffeef0` |
| `--t-text2` | `#cbd5e1` | `#ccb880` | `#333333` | `#93a1a1` | `#d4b0b8` |
| `--t-muted` | `#6b7280` | `#7a7050` | `#888888` | `#657b83` | `#8a7080` |
| `--t-success` | `#22c55e` | `#66bb6a` | `#2d5a2d` | `#859900` | `#7bc67b` |
| `--t-warning` | `#f59e0b` | `#ffb000` | `#8a6d00` | `#b58900` | `#ffa94d` |
| `--t-error` | `#ef4444` | `#ff5533` | `#8a2d2d` | `#dc322f` | `#ff4757` |
| `--t-font` | system-ui, sans-serif | Courier New, monospace | Patrick Hand, cursive | system-ui, sans-serif | system-ui, sans-serif |
| `--t-font-mono` | Menlo, Monaco, monospace | Courier New, monospace | Courier New, monospace | Menlo, Monaco, monospace | Menlo, Monaco, monospace |
| `--t-radius` | `0.5rem` | `0.25rem` | `0px` | `0.375rem` | `0.5rem` |
| **Light/Dark** | Dark | Dark | **Light** | Dark | Dark |
| **Special FX** | None | Scanline overlay | Hand-drawn borders | None | None |

---

## 5.7 File Path Index

### Backend Core

| File | Purpose | ~Lines |
|------|---------|--------|
| `backend/main.py` | FastAPI app, CORS, router mounting, health/models endpoints | ~66 |
| `backend/config.py` | API keys, model catalog, VOX config, paths, integration credentials | ~136 |

### Backend Routers

| File | Purpose | ~Lines |
|------|---------|--------|
| `backend/routers/chat.py` | SSE streaming chat (dual-model) | ~150 |
| `backend/routers/coding.py` | Coding with tool use | ~200 |
| `backend/routers/agents.py` | NLKE agent CRUD + execution | ~80 |
| `backend/routers/playbooks.py` | Playbook search + retrieval | ~80 |
| `backend/routers/workflows.py` | Workflow templates + execution | ~120 |
| `backend/routers/builder.py` | Legacy web app plan + generate | ~100 |
| `backend/routers/studio.py` | Studio SSE streaming + project CRUD (18 endpoints) | ~300 |
| `backend/routers/experts.py` | Expert Builder + KG-OS (15 endpoints) | ~200 |
| `backend/routers/tools.py` | Tools playground (list, get, run, stream) | ~80 |
| `backend/routers/vox.py` | VOX voice agent (WebSocket + REST, 34 functions) | ~901 |
| `backend/routers/media.py` | Image edit + video gen | ~120 |
| `backend/routers/interchange.py` | JSON import/export, mode toggle | ~60 |
| `backend/routers/kg.py` | KG Studio (33 endpoints) | ~500 |
| `backend/routers/memory.py` | Conversation memory | ~100 |
| `backend/routers/integrations.py` | Platform integrations | ~150 |
| `backend/routers/games.py` | Phaser 3 RPG game projects | ~330 |

### Backend Services

| File | Purpose | ~Lines |
|------|---------|--------|
| `backend/services/gemini_service.py` | google-genai SDK wrapper (lazy init) | ~150 |
| `backend/services/claude_service.py` | anthropic SDK wrapper (streaming + tool_use) | ~150 |
| `backend/services/model_router.py` | Intelligent model selection (15 rules) | ~64 |
| `backend/services/agent_bridge.py` | NLKE agent system bridge | ~80 |
| `backend/services/playbook_index.py` | Playbook file parser + search | ~100 |
| `backend/services/studio_service.py` | Studio SQLite CRUD, versions, ZIP export | ~385 |
| `backend/services/openapi_extractor.py` | FastAPI code to OpenAPI spec | ~200 |
| `backend/services/type_generator.py` | OpenAPI to TypeScript interfaces | ~150 |
| `backend/services/mock_server_manager.py` | Node.js mock server lifecycle | ~100 |
| `backend/services/tools_service.py` | 58+ tool registry, dynamic import + execution | ~300 |
| `backend/services/vox_service.py` | VOX sessions (Gemini Live API + Claude, 34 functions) | ~665 |
| `backend/services/vox_awareness.py` | Workspace awareness (SQLite: pages, errors, context) | ~209 |
| `backend/services/vox_macros.py` | Voice macro CRUD + pipe-chaining execution | ~279 |
| `backend/services/vox_thermal.py` | Device thermal monitoring (Termux battery API) | ~60 |
| `backend/services/expert_service.py` | Expert CRUD + KG-OS execution pipeline | ~451 |
| `backend/services/kgos_query_engine.py` | KG-OS: 12 query methods, 14 intents, 56 dimensions | ~400 |
| `backend/services/kg_service.py` | KG core: 6 schema profiles, auto-detect, CRUD | ~745 |
| `backend/services/embedding_service.py` | Hybrid search (numpy cosine + BM25 + graph boost) | ~300 |
| `backend/services/analytics_service.py` | NetworkX graph algorithms | ~200 |
| `backend/services/ingestion_service.py` | AI entity extraction from text | ~150 |
| `backend/services/rag_chat_service.py` | RAG chat with streaming + source citations | ~200 |
| `backend/services/game_service.py` | Game project CRUD + interview + GDD synthesis | ~400 |
| `backend/services/game_generator.py` | Phaser 3 code generation + refinement | ~500 |
| `backend/services/game_llm_service.py` | Local LLM integration for NPC dialogue | ~200 |

### Backend Data

| File | Purpose | ~Lines |
|------|---------|--------|
| `backend/data/vox_tours.json` | 11 guided tour definitions (steps, selectors, narration) | ~500 |
| `backend/mcp_server.py` | MCP server: 58+ tools via JSON-RPC stdio | ~200 |

### Frontend Pages

| File | Purpose | ~Lines |
|------|---------|--------|
| `frontend/src/App.tsx` | Router + layout shell + NavBar | ~100 |
| `frontend/src/pages/ChatPage.tsx` | Dual-model streaming chat | ~300 |
| `frontend/src/pages/CodingPage.tsx` | IDE with file explorer + AI coding | ~400 |
| `frontend/src/pages/AgentsPage.tsx` | 33 NLKE agents + pipeline builder | ~300 |
| `frontend/src/pages/PlaybooksPage.tsx` | 53 playbooks search + reader | ~250 |
| `frontend/src/pages/WorkflowsPage.tsx` | Visual workflow designer + executor | ~350 |
| `frontend/src/pages/KGStudioPage.tsx` | Graph-RAG KG workspace (10 tabs, 57 DBs) | ~800 |
| `frontend/src/pages/StudioPage.tsx` | AI Studio: chat, code, visual modes | ~500 |
| `frontend/src/pages/ExpertsPage.tsx` | KG-OS Expert Builder | ~400 |
| `frontend/src/pages/ToolsPage.tsx` | 58+ tools playground | ~300 |
| `frontend/src/pages/VoxPage.tsx` | VOX voice control center | ~400 |
| `frontend/src/pages/GamesPage.tsx` | Phaser 3 RPG game builder | ~600 |
| `frontend/src/pages/IntegrationsPage.tsx` | Platform integrations management | ~200 |
| `frontend/src/pages/SettingsPage.tsx` | Mode toggle, themes, export/import | ~200 |

### Frontend Types

| File | Purpose | ~Lines |
|------|---------|--------|
| `frontend/src/types/index.ts` | Barrel re-export | ~10 |
| `frontend/src/types/ai.ts` | CustomAiStyle, Persona, Agent, ModelConfig, NlkeAgent, PlaybookMeta | ~48 |
| `frontend/src/types/chat.ts` | MessageAuthor, ChatMode, Message, ToolCall, ToolResponse, GroundingMetadata | ~47 |
| `frontend/src/types/project.ts` | Project, ProjectFile | ~16 |
| `frontend/src/types/kg.ts` | 16 KG interfaces (KGDatabase, KGNode, KGEdge, KGSearchResult, etc.) + KGTab type | ~123 |
| `frontend/src/types/studio.ts` | 13 Studio interfaces (StudioProject, StudioFile, StudioVersion, etc.) | ~113 |
| `frontend/src/types/memory.ts` | Conversation, ConversationMessage, MemoryNode, MemoryStats, Integration, IntegrationSetup | ~57 |
| `frontend/src/types/expert.ts` | Expert, ExpertConversation, ExpertMessage, ExpertSource, KGOSSearchResult, KGOSSearchResponse | ~71 |
| `frontend/src/types/tools.ts` | ToolParam, ToolDetail, ToolSummary, ToolsListResponse, ToolRunResult | ~41 |
| `frontend/src/types/vox.ts` | VoxState, VoxTranscriptEntry, VoxFunctionEntry, VoxConfig, VoxVoice, VoxMode | ~44 |
| `frontend/src/types/game.ts` | GameProject, GameDesignDoc, GameNPC, GameEnemy, InterviewQuestion, GameVersion | ~89 |

### Frontend Services

| File | Purpose | ~Lines |
|------|---------|--------|
| `frontend/src/services/apiService.ts` | Complete REST API client (120+ functions) | ~856 |
| `frontend/src/themes/index.ts` | 5 theme definitions + getTheme() | ~161 |
| `frontend/src/hooks/useChat.ts` | Chat streaming hook | ~150 |
| `frontend/src/hooks/useTheme.ts` | Theme apply + persist to localStorage | ~50 |
| `frontend/src/hooks/useToast.ts` | Toast notification hook | ~40 |
| `frontend/src/hooks/useVox.ts` | VOX WebSocket hook + state management | ~300 |

### SQLite Database Files

| File | Purpose | Created By |
|------|---------|-----------|
| `backend/vox_awareness.db` | Page visits, errors, session context | `vox_awareness.py` |
| `backend/vox_macros.db` | Voice macro definitions + steps | `vox_macros.py` |
| `backend/studio_projects.db` | Studio projects + version snapshots | `studio_service.py` |
| `backend/experts.db` | Experts + conversations + messages | `expert_service.py` |
| `docs/KGS/*.db` (57+) | Knowledge graph databases (various schemas) | `kg_service.py` |

---

## 5.8 Integration Credentials Table

| Platform | Required Fields | Env Vars | Config Constants |
|----------|----------------|----------|-----------------|
| **Telegram** | Bot Token | `TELEGRAM_BOT_TOKEN` | `TELEGRAM_BOT_TOKEN` |
| **WhatsApp** | Token, Phone ID, Verify Token | `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_ID`, `WHATSAPP_VERIFY_TOKEN` | Same |
| **Discord** | Public Key, Bot Token | `DISCORD_PUBLIC_KEY`, `DISCORD_BOT_TOKEN` | Same |
| **Slack** | Bot Token, Signing Secret | `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET` | Same |
| **Gmail** | Client ID, Client Secret, Refresh Token | `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN` | Same |
| **Spotify** | Client ID, Client Secret, Refresh Token | `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, `SPOTIFY_REFRESH_TOKEN` | Same |
| **Google Calendar** | Credentials JSON | `GOOGLE_CALENDAR_CREDENTIALS` | Same |

All credentials are optional. Configured via environment variables or at runtime through `POST /api/integrations/{platform}/configure`.

---

## 5.9 Expert Retrieval 4-Weight Scoring Formula

```
score = alpha * embedding_similarity
      + beta  * bm25_text_score
      + gamma * graph_boost
      + delta * intent_bonus
```

| Weight | Symbol | Default | Range | Purpose |
|--------|--------|---------|-------|---------|
| Embedding | alpha | 0.35 | 0.0-1.0 | Cosine similarity of numpy embeddings |
| BM25/Text | beta | 0.40 | 0.0-1.0 | Keyword/term frequency matching |
| Graph Boost | gamma | 0.15 | 0.0-1.0 | Connected node boosting |
| Intent Bonus | delta | 0.10 | 0.0-1.0 | Intent classification match bonus |

Weights are configurable per-expert via the Expert Builder UI.

---

## 5.10 SSE Stream Event Types

### Studio Stream Events (`/api/studio/stream`)

| Event Type | Fields | Purpose |
|-----------|--------|---------|
| `token` | `{type: "token", content: "<text>"}` | Incremental AI response text |
| `thinking` | `{type: "thinking", content: "<text>"}` | Model thinking/reasoning trace |
| `studio_plan` | `{type: "studio_plan", content: "<plan text>"}` | Generation plan |
| `studio_file` | `{type: "studio_file", path: "<path>", file_content: "<code>"}` | Generated file |
| `studio_deps` | `{type: "studio_deps", deps: Record<string,string>}` | npm dependencies |
| `studio_api_spec` | `{type: "studio_api_spec", api_spec: StudioApiSpec}` | OpenAPI spec |
| `done` | `{type: "done"}` | Stream complete |
| `error` | `{type: "error", content: "<message>"}` | Error occurred |

### Expert Chat Stream Events (`/api/experts/{id}/chat`)

| Event Type | Fields | Purpose |
|-----------|--------|---------|
| `conversation_id` | `{type: "conversation_id", id: "<cid>"}` | Conversation identifier |
| `sources` | `{type: "sources", nodes: ExpertSource[]}` | KG-OS retrieved source nodes |
| `content` | `{type: "content", text: "<chunk>"}` | Incremental response text |
| `done` | `{type: "done"}` | Stream complete |
| `error` | `{type: "error", content: "<message>"}` | Error occurred |

### Game Generation Stream Events (`/api/games/{id}/generate`)

| Event Type | Fields | Purpose |
|-----------|--------|---------|
| `token` | `{type: "token", content: "<text>"}` | Incremental text |
| `file` | `{type: "file", path: "<path>", content: "<code>"}` | Generated game file |
| `files_complete` | `{type: "files_complete", files: Record<string,string>}` | All files bundle |
| `done` | `{type: "done"}` | Stream complete |
| `error` | `{type: "error", content: "<message>"}` | Error occurred |

---

## 5.11 Frontend Route Map

| Route Path | Component | NavBar Label | Mobile-Optimized |
|-----------|-----------|-------------|-----------------|
| `/chat` | `ChatPage` | Chat | Yes |
| `/coding` | `CodingPage` | Coding | Yes |
| `/agents` | `AgentsPage` | Agents | Yes |
| `/playbooks` | `PlaybooksPage` | Playbooks | Yes |
| `/workflows` | `WorkflowsPage` | Workflows | Yes |
| `/kg-studio` | `KGStudioPage` | KG Studio | Yes (`w-full lg:w-64`) |
| `/builder` | `StudioPage` | Studio | Yes |
| `/experts` | `ExpertsPage` | Experts | Yes (dropdown picker) |
| `/tools` | `ToolsPage` | Tools | Yes |
| `/vox` | `VoxPage` | VOX | Yes (dropdown picker) |
| `/games` | `GamesPage` | Games | Yes (dropdown picker) |
| `/integrations` | `IntegrationsPage` | Integrations | Yes |
| `/settings` | `SettingsPage` | Settings | Yes |

---

## 5.12 Complete `apiService.ts` Function Inventory

Total exported functions: **120+**

### Chat & Coding (2)

| Function | HTTP | Endpoint |
|----------|------|----------|
| `streamChat()` | POST | `/api/chat/stream` |
| `streamCoding()` | POST | `/api/coding/stream` |

### Media (2)

| Function | HTTP | Endpoint |
|----------|------|----------|
| `editImage()` | POST | `/api/image/edit` |
| `generateVideo()` | POST | `/api/video/generate` + polling |

### Agents (3)

| Function | HTTP | Endpoint |
|----------|------|----------|
| `listAgents()` | GET | `/api/agents` |
| `runAgent()` | POST | `/api/agents/{name}/run` |
| `getAgentExample()` | GET | `/api/agents/{name}/example` |

### Pipelines (1)

| Function | HTTP | Endpoint |
|----------|------|----------|
| `runPipeline()` | POST | `/api/pipelines/run` |

### Playbooks (4)

| Function | HTTP | Endpoint |
|----------|------|----------|
| `listPlaybooks()` | GET | `/api/playbooks` |
| `searchPlaybooks()` | GET | `/api/playbooks/search` |
| `getPlaybook()` | GET | `/api/playbooks/{filename}` |
| `listPlaybookCategories()` | GET | `/api/playbooks/categories` |

### Workflows (3)

| Function | HTTP | Endpoint |
|----------|------|----------|
| `listWorkflowTemplates()` | GET | `/api/workflows/templates` |
| `planWorkflow()` | POST | `/api/workflows/plan` |
| `streamWorkflowExecution()` | POST | `/api/workflows/execute` |

### Builder (2)

| Function | HTTP | Endpoint |
|----------|------|----------|
| `generateWebAppPlan()` | POST | `/api/builder/plan` |
| `generateWebAppCode()` | POST | `/api/builder/generate` |

### Models & Mode (5)

| Function | HTTP | Endpoint |
|----------|------|----------|
| `listModels()` | GET | `/api/models` |
| `getMode()` | GET | `/api/mode` |
| `setMode()` | POST | `/api/mode` |
| `exportWorkspace()` | POST | `/api/export` |
| `importWorkspace()` | POST | `/api/import` |

### Health & Config (3)

| Function | HTTP | Endpoint |
|----------|------|----------|
| `healthCheck()` | GET | `/api/health` |
| `getKeysStatus()` | GET | `/api/config/keys/status` |
| `setApiKeys()` | POST | `/api/config/keys` |

### Knowledge Graph (24)

| Function | HTTP | Endpoint |
|----------|------|----------|
| `listKGDatabases()` | GET | `/api/kg/databases` |
| `createKGDatabase()` | POST | `/api/kg/databases` |
| `getKGStats()` | GET | `/api/kg/databases/{id}/stats` |
| `listKGNodes()` | GET | `/api/kg/databases/{id}/nodes` |
| `getKGNode()` | GET | `/api/kg/databases/{id}/nodes/{nid}` |
| `getKGNeighbors()` | GET | `/api/kg/databases/{id}/nodes/{nid}/neighbors` |
| `createKGNode()` | POST | `/api/kg/databases/{id}/nodes` |
| `updateKGNode()` | PUT | `/api/kg/databases/{id}/nodes/{nid}` |
| `deleteKGNode()` | DELETE | `/api/kg/databases/{id}/nodes/{nid}` |
| `listKGEdges()` | GET | `/api/kg/databases/{id}/edges` |
| `createKGEdge()` | POST | `/api/kg/databases/{id}/edges` |
| `updateKGEdge()` | PUT | `/api/kg/databases/{id}/edges/{eid}` |
| `deleteKGEdge()` | DELETE | `/api/kg/databases/{id}/edges/{eid}` |
| `getKGTypes()` | GET | `/api/kg/databases/{id}/types` |
| `bulkCreateKG()` | POST | `/api/kg/databases/{id}/bulk` |
| `searchKG()` | POST | `/api/kg/databases/{id}/search` |
| `multiSearchKG()` | POST | `/api/kg/search/multi` |
| `streamKGChat()` | POST | `/api/kg/databases/{id}/chat` |
| `ingestKGText()` | POST | `/api/kg/databases/{id}/ingest` |
| `getKGAnalyticsSummary()` | GET | `/api/kg/databases/{id}/analytics/summary` |
| `getKGCentrality()` | GET | `/api/kg/databases/{id}/analytics/centrality` |
| `getKGCommunities()` | GET | `/api/kg/databases/{id}/analytics/communities` |
| `findKGPath()` | POST | `/api/kg/databases/{id}/analytics/path` |
| `compareKGs()` | POST | `/api/kg/compare` |

### Knowledge Graph (continued)

| Function | HTTP | Endpoint |
|----------|------|----------|
| `diffKGs()` | POST | `/api/kg/diff` |
| `mergeKGs()` | POST | `/api/kg/merge` |
| `batchDeleteByType()` | POST | `/api/kg/databases/{id}/batch/delete-by-type` |
| `batchRetype()` | POST | `/api/kg/databases/{id}/batch/retype` |
| `getKGEmbeddingStatus()` | GET | `/api/kg/databases/{id}/embedding-status` |
| `getKGEmbeddingProjection()` | GET | `/api/kg/databases/{id}/embeddings/projection` |
| `generateKGEmbeddings()` | POST | `/api/kg/databases/{id}/embeddings/generate` |
| `getKGEmbeddingQuality()` | GET | `/api/kg/databases/{id}/embeddings/quality` |

### Memory (6)

| Function | HTTP | Endpoint |
|----------|------|----------|
| `listConversations()` | GET | `/api/memory/conversations` |
| `getConversation()` | GET | `/api/memory/conversations/{id}` |
| `getConversationMessages()` | GET | `/api/memory/conversations/{id}/messages` |
| `deleteConversation()` | DELETE | `/api/memory/conversations/{id}` |
| `searchMemory()` | POST | `/api/memory/search` |
| `getMemoryStats()` | GET | `/api/memory/stats` |

### Integrations (7)

| Function | HTTP | Endpoint |
|----------|------|----------|
| `listIntegrations()` | GET | `/api/integrations` |
| `configureIntegration()` | POST | `/api/integrations/{platform}/configure` |
| `testIntegration()` | POST | `/api/integrations/{platform}/test` |
| `enableIntegration()` | POST | `/api/integrations/{platform}/enable` |
| `disableIntegration()` | POST | `/api/integrations/{platform}/disable` |
| `deleteIntegration()` | DELETE | `/api/integrations/{platform}` |
| `getIntegrationSetup()` | GET | `/api/integrations/{platform}/setup` |

### Experts (13)

| Function | HTTP | Endpoint |
|----------|------|----------|
| `listExperts()` | GET | `/api/experts` |
| `createExpert()` | POST | `/api/experts` |
| `getExpert()` | GET | `/api/experts/{id}` |
| `updateExpert()` | PUT | `/api/experts/{id}` |
| `deleteExpert()` | DELETE | `/api/experts/{id}` |
| `duplicateExpert()` | POST | `/api/experts/{id}/duplicate` |
| `streamExpertChat()` | POST | `/api/experts/{id}/chat` |
| `listExpertConversations()` | GET | `/api/experts/{id}/conversations` |
| `getExpertConversation()` | GET | `/api/experts/{id}/conversations/{cid}` |
| `deleteExpertConversation()` | DELETE | `/api/experts/{id}/conversations/{cid}` |
| `kgosQuery()` | POST | `/api/experts/kgos/query/{db_id}` |
| `kgosImpact()` | POST | `/api/experts/kgos/impact/{db_id}/{nid}` |
| `kgosCompose()` | POST | `/api/experts/kgos/compose/{db_id}` |

### Experts (continued)

| Function | HTTP | Endpoint |
|----------|------|----------|
| `kgosSimilar()` | POST | `/api/experts/kgos/similar/{db_id}/{nid}` |

### Tools (4)

| Function | HTTP | Endpoint |
|----------|------|----------|
| `listTools()` | GET | `/api/tools` |
| `getToolDetail()` | GET | `/api/tools/{id}` |
| `runTool()` | POST | `/api/tools/{id}/run` |
| `runToolStream()` | POST | `/api/tools/{id}/run/stream` |

### VOX (4)

| Function | HTTP | Endpoint |
|----------|------|----------|
| `getVoxStatus()` | GET | `/api/vox/status` |
| `getVoxVoices()` | GET | `/api/vox/voices` |
| `getVoxFunctions()` | GET | `/api/vox/functions` |
| `runVoxFunction()` | POST | `/api/vox/function/{fn_name}` |

### Games (17)

| Function | HTTP | Endpoint |
|----------|------|----------|
| `listGames()` | GET | `/api/games` |
| `createGame()` | POST | `/api/games` |
| `getGame()` | GET | `/api/games/{id}` |
| `updateGame()` | PUT | `/api/games/{id}` |
| `deleteGame()` | DELETE | `/api/games/{id}` |
| `getInterviewQuestions()` | GET | `/api/games/interview/questions` |
| `submitInterviewAnswer()` | POST | `/api/games/{id}/interview` |
| `synthesizeGDD()` | POST | `/api/games/{id}/synthesize` |
| `streamGenerateGame()` | POST | `/api/games/{id}/generate` |
| `streamRefineGame()` | POST | `/api/games/{id}/refine` |
| `saveGameVersion()` | POST | `/api/games/{id}/save` |
| `listGameVersions()` | GET | `/api/games/{id}/versions` |
| `restoreGameVersion()` | POST | `/api/games/{id}/versions/{ver}/restore` |
| `exportGame()` | GET | `/api/games/{id}/export` |
| `streamGameChat()` | POST | `/api/games/{id}/chat` |
| `extractGamePatterns()` | POST | `/api/games/{id}/extract-patterns` |
| `gameLLMStatus()` | GET | `/api/games/llm/status` |

### Games (continued)

| Function | HTTP | Endpoint |
|----------|------|----------|
| `gameLLMLoad()` | POST | `/api/games/llm/load` |
| `gameLLMUnload()` | POST | `/api/games/llm/unload` |
| `gameLLMChat()` | POST | `/api/games/llm/chat` |

---

## 5.13 Browser-Side vs Server-Side VOX Function Routing

| Execution Side | Functions | Count |
|---------------|-----------|-------|
| **Browser (frontend JS)** | `navigate_page`, `get_current_page`, `get_workspace_state`, `switch_model`, `switch_theme`, `read_page_content` | 6 |
| **Server (Python, sync)** | `run_tool`, `list_tools`, `query_kg`, `list_kgs`, `list_agents`, `generate_react_component`, `generate_fastapi_endpoint`, `scan_code_security`, `analyze_code_complexity`, `generate_tests`, `start_guided_tour`, `get_available_tours`, `create_project`, `list_projects`, `search_playbooks`, `search_kg`, `get_kg_analytics`, `chat_with_expert`, `list_experts`, `create_macro`, `list_macros`, `delete_macro`, `check_thermal` | 23 |
| **Server (Python, async background)** | `run_agent`, `run_workflow`, `cross_kg_search`, `ingest_to_kg`, `run_macro` | 5 |
| **Total** | | **34** |

---

*End of Parts 4 and 5 -- Data Models and Quick Reference Tables*

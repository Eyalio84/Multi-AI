# Multi-AI Agentic Workspace — Technical Reference

## Part 0: Executive Summary

---

### What This Is

The Multi-AI Agentic Workspace is a professional agentic workflow orchestrator that combines Google Gemini and Anthropic Claude intelligence into a unified development environment. It provides dual-model streaming chat, 33 NLKE agents, 53 playbooks, 58+ Python tools across 11 categories, a full Graph-RAG Knowledge Graph workspace with 57 SQLite KGs and live hybrid search, an AI-powered Studio for generating full-stack React apps with live Sandpack preview, a KG-OS Expert Builder for creating AI experts backed by structured knowledge graphs, a VOX voice agent with 34 function declarations and 16 voices, and a standalone MCP server exposing all tools via JSON-RPC.

---

### Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | FastAPI (Python 3.11+) |
| **Frontend** | React 19 + TypeScript + Vite |
| **Database** | SQLite (KGs, awareness, macros, studio projects) |
| **Live Preview** | Sandpack (CodeSandbox runtime) |
| **Graph Viz** | d3-force + React Flow |
| **Graph Analytics** | NetworkX |
| **Embeddings** | numpy cosine similarity (self-supervised, no external models) |
| **AI Providers** | Google GenAI SDK (`google-genai`), Anthropic SDK (`anthropic`) |
| **Voice** | Gemini Live API (native audio), Web Speech API (Claude fallback) |
| **Styling** | Tailwind CSS + CSS custom properties (5 themes) |

---

### High-Level Architecture

```
+-----------------------------------------------------------+
|                      BROWSER (React 19)                    |
|                                                            |
|  +--------+ +--------+ +--------+ +--------+ +--------+   |
|  |  Chat  | | Coding | |  KG    | | Studio | |  VOX   |   |
|  |  Page  | |  Page  | | Studio | |  Page  | |  Page  |   |
|  +--------+ +--------+ +--------+ +--------+ +--------+   |
|  + Agents, Playbooks, Workflows, Experts, Tools, Games,   |
|    Integrations, Settings                                  |
|                                                            |
|  HTTP REST (fetch)          WebSocket (/ws/vox)            |
+-------------|---------------------|------------------------+
              |                     |
              v                     v
+-------------|---------------------|------------------------+
|                   BACKEND (FastAPI :8000)                   |
|                                                            |
|  +------------------+    +--------------------+            |
|  | 16 API Routers   |    | VOX Router         |            |
|  | /api/chat/stream  |    | /ws/vox (WebSocket)|            |
|  | /api/coding/stream|    | /api/vox/* (REST)  |            |
|  | /api/kg/*         |    +--------------------+            |
|  | /api/studio/*     |              |                      |
|  | /api/experts/*    |    +---------+---------+            |
|  | /api/tools/*      |    | VoxService        |            |
|  | /api/agents/*     |    | VoxAwareness (SQL) |            |
|  | /api/vox/*        |    | VoxMacros (SQL)    |            |
|  +------------------+    | VoxThermal         |            |
|           |               +---------+---------+            |
|  +--------+--------+               |                      |
|  | 22 Services      |               |                      |
|  | gemini_service   |               |                      |
|  | claude_service   |               |                      |
|  | kg_service       |               |                      |
|  | embedding_service|               |                      |
|  | tools_service    |               |                      |
|  | expert_service   |               |                      |
|  | studio_service   |               |                      |
|  +--------+--------+               |                      |
+-----------|------------------------|------------------------+
            |                        |
     +------+------+         +------+------+
     |             |         |             |
     v             v         v             v
+---------+  +---------+  +---------+  +---------+
| Google  |  |Anthropic|  | Gemini  |  | Claude  |
| GenAI   |  |   SDK   |  | Live API|  | tool_use|
| REST API|  | REST API|  |(audio)  |  | (text)  |
+---------+  +---------+  +---------+  +---------+
```

---

### How to Run

**Backend:**

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

The frontend runs on port 5173 (Vite default) and proxies API requests to the backend on port 8000. CORS is configured to allow all origins in development mode.

**Environment Variables:**

| Variable | Required | Purpose |
|----------|----------|---------|
| `GEMINI_API_KEY` | Yes | Google GenAI API access |
| `ANTHROPIC_API_KEY` | For Claude features | Anthropic API access |
| `WORKSPACE_MODE` | No (default: `standalone`) | `standalone` or `claude-code` |

---

### 13 Route Pages

| Route | Page Component | Purpose |
|-------|----------------|---------|
| `/chat` | ChatPage | Dual-model streaming chat (Gemini + Claude) |
| `/coding` | CodingPage | IDE with file explorer + AI coding |
| `/agents` | AgentsPage | 33 NLKE agents + pipeline builder |
| `/playbooks` | PlaybooksPage | 53 playbooks search + reader |
| `/workflows` | WorkflowsPage | Visual workflow designer + executor |
| `/kg-studio` | KGStudioPage | Graph-RAG KG workspace (57 DBs, React Flow + d3-force) |
| `/builder` | StudioPage | AI Studio: chat, generate, preview with Sandpack |
| `/experts` | ExpertsPage | KG-OS Expert Builder with 4-weight scoring |
| `/tools` | ToolsPage | 58+ Python tools playground (11 categories) |
| `/vox` | VoxPage | VOX voice control center (16 voices, 34 functions) |
| `/games` | GamesPage | AI-generated Phaser games |
| `/integrations` | IntegrationsPage | Platform integrations management |
| `/settings` | SettingsPage | Mode toggle, themes, export/import |

The default route `/` redirects to `/chat`.

---

### Model Catalog

Defined in `backend/config.py`:

| Provider | Model ID | Name | Context | Cost In ($/1M) | Cost Out ($/1M) | Use Case |
|----------|----------|------|---------|----------------|-----------------|----------|
| Gemini | `gemini-3-pro-preview` | Gemini 3 Pro | 1M | $2.00 | $12.00 | Flagship reasoning |
| Gemini | `gemini-2.5-flash` | Gemini 2.5 Flash | 1M | $0.15 | $0.60 | Fast coding/streaming |
| Gemini | `gemini-2.5-pro` | Gemini 2.5 Pro | 1M | $1.25 | $5.00 | Deep reasoning |
| Gemini | `gemini-2.5-flash-image` | Gemini 2.5 Flash Image | 1M | $0.15 | $0.60 | Image generation |
| Gemini | `gemini-embedding-001` | Gemini Embedding | 8K | $0.00 | $0.00 | RAG/embeddings |
| Gemini | `veo-2.0-generate-001` | Veo 2.0 | - | $0.00 | $0.00 | Video generation |
| Claude | `claude-opus-4-6` | Claude Opus 4.6 | 200K | $5.00 | $25.00 | Most intelligent |
| Claude | `claude-sonnet-4-6` | Claude Sonnet 4.6 | 200K | $3.00 | $15.00 | Fast + capable |
| Claude | `claude-haiku-4-5-20251001` | Claude Haiku 4.5 | 200K | $1.00 | $5.00 | Cheapest, routing |

Default models: `gemini-2.5-flash` (Gemini), `claude-sonnet-4-6` (Claude).

VOX voice model: `gemini-2.5-flash-native-audio-preview-12-2025` (Gemini Live API).

---

### Dual-Mode Architecture

The workspace supports two operational modes controlled by the `WORKSPACE_MODE` environment variable:

**Standalone Mode** (default, `WORKSPACE_MODE=standalone`):
- Both `GEMINI_API_KEY` and `ANTHROPIC_API_KEY` are active
- Backend calls both Google and Anthropic APIs directly
- Full dual-model UI with provider selector on every chat/coding page
- VOX supports both Gemini voice (native audio) and Claude voice (browser STT/TTS)

**Claude Code Mode** (`WORKSPACE_MODE=claude-code`):
- Only `GEMINI_API_KEY` is active; `ANTHROPIC_API_KEY` is set to `None`
- Claude tasks return structured JSON intended for consumption by Claude Code CLI sessions
- 33 NLKE agents remain invocable via CLI by Claude Code
- Mode is toggled via the Settings page UI or `POST /api/mode`

The mode detection logic from `backend/config.py`:

```python
MODE = os.getenv("WORKSPACE_MODE", "standalone")

ANTHROPIC_API_KEY = (
    os.getenv("ANTHROPIC_API_KEY", "")
    if MODE == "standalone"
    else None
)
```

---

### Router Mounting

All routers are mounted in `backend/main.py`. Most use the `/api` prefix. The VOX router is mounted without a prefix because it serves both REST endpoints at `/api/vox/*` and a WebSocket at `/ws/vox`:

```python
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

---

### Theme System

5 themes applied via CSS custom properties on `:root`, persisted in `localStorage` under key `workspace_theme`:

| Theme ID | Name | Background | Primary | Notes |
|----------|------|------------|---------|-------|
| `default` | Default | `#111827` | `#0ea5e9` | Dark blue-gray |
| `crt` | Deluxe-CRT | `#0a0a08` | `#ffb000` | Scanline overlay |
| `scratch` | Scratch | `#fafaf8` | `#1a1a1a` | Patrick Hand font, light |
| `solarized` | Solarized Zen | `#002b36` | `#2aa198` | Ethan Schoonover's palette |
| `sunset` | Sunset Warm | `#1a1218` | `#ff6b6b` | Warm reds |

All components use `style={{ background: 'var(--t-surface)', color: 'var(--t-text)' }}` for visual properties and `className` for layout (flex, padding, rounding).

---
---

## Part 1: VOX Voice Agent

---

### 1.1 Architecture Overview

VOX is the workspace's voice-powered master agent. It connects the browser's audio capture pipeline to either the Gemini Live API (native bidirectional audio streaming) or the Claude text API (with browser-side STT/TTS), and can execute 34 workspace functions by voice command.

```
+------------------------------------------------------------------+
|                    BROWSER (React 19)                             |
|                                                                   |
|  useVox Hook                                                      |
|  +-----------+  +-------------+  +----------------+              |
|  | Mic       |  | Audio       |  | Browser        |              |
|  | Capture   |  | Playback    |  | Functions (6)  |              |
|  | PCM 16kHz |  | PCM 24kHz   |  | navigate_page  |              |
|  | -> base64 |  | <- base64   |  | get_current_pg |              |
|  +-----------+  +-------------+  | get_ws_state   |              |
|       |              ^           | switch_model   |              |
|       |              |           | switch_theme   |              |
|       v              |           | read_page      |              |
|  +----+--------------+----+     +----------------+              |
|  |    WebSocket /ws/vox    |           ^                         |
|  |    bidirectional JSON   +-----------+                         |
|  +------------+------------+  browser_function_result            |
+---------------|--------------------|-----------|-----------------+
                |                    |           |
                v                    |           |
+---------------|--------------------|-----------|-----------------+
|               |     BACKEND (FastAPI :8000)    |                 |
|               v                                |                 |
|  +------------------------+                    |                 |
|  |     VOX Router         |                    |                 |
|  |  (vox.py)              |                    |                 |
|  +------+-----------------+                    |                 |
|         |                                      |                 |
|    +----+----+    +----------+    +------------+-------+         |
|    |         |    |          |    |                     |         |
|    v         v    v          v    v                     |         |
|  Gemini   Claude  Server Functions (28)                |         |
|  Receive  Text    +------------------+                 |         |
|  Loop     Pipeline| run_tool         |                 |         |
|    |       |      | list_tools       |                 |         |
|    |       |      | query_kg         |                 |         |
|    v       v      | list_kgs         |                 |         |
|  +----+ +----+   | run_agent        |                 |         |
|  |Gem | |Cla |   | list_agents      |                 |         |
|  |ini | |ude |   | generate_react.. |                 |         |
|  |Live| |API |   | generate_fast..  |                 |         |
|  |API | |    |   | scan_code_sec..  |                 |         |
|  +----+ +----+   | analyze_code_..  |                 |         |
|                   | generate_tests   |                 |         |
|                   | start_guided_..  |                 |         |
|                   | get_available..  |                 |         |
|                   | create_project   |                 |         |
|                   | list_projects    |                 |         |
|                   | run_workflow     |                 |         |
|                   | search_playbooks |                 |         |
|                   | search_kg        |                 |         |
|                   | get_kg_analytics |                 |         |
|                   | cross_kg_search  |                 |         |
|                   | ingest_to_kg     |                 |         |
|                   | chat_with_expert |                 |         |
|                   | list_experts     |                 |         |
|                   | create_macro     |                 |         |
|                   | list_macros      |                 |         |
|                   | run_macro        |                 |         |
|                   | delete_macro     |                 |         |
|                   | check_thermal    |                 |         |
|                   +------------------+                 |         |
|                          |                             |         |
|    +---------------------+-----------------------------+         |
|    |                     |                                       |
|    v                     v                                       |
|  +------------------+  +--------------------+                    |
|  | Awareness Layer  |  | Voice Macros       |                    |
|  | (SQLite)         |  | (SQLite)           |                    |
|  | page_visits      |  | macro CRUD         |                    |
|  | error_log        |  | pipe-chain execute |                    |
|  | session_context  |  +--------------------+                    |
|  +------------------+                                            |
|  +------------------+  +--------------------+                    |
|  | Thermal Monitor  |  | Guided Tours       |                    |
|  | (Termux battery) |  | (vox_tours.json)   |                    |
|  +------------------+  | 11 page tours      |                    |
|                        +--------------------+                    |
+------------------------------------------------------------------+
```

**Source files:**
- `backend/services/vox_service.py` -- VoxSession, VoxService, voices, function declarations, system prompt
- `backend/routers/vox.py` -- REST endpoints, WebSocket handler, receive loops, server function execution
- `backend/services/vox_awareness.py` -- SQLite awareness layer
- `backend/services/vox_macros.py` -- SQLite macro system with pipe chaining
- `backend/services/vox_thermal.py` -- Termux battery temperature monitor
- `backend/data/vox_tours.json` -- 11 guided tour definitions
- `frontend/src/hooks/useVox.ts` -- React hook for audio, WebSocket, browser functions
- `frontend/src/types/vox.ts` -- TypeScript interfaces
- `frontend/src/context/VoxContext.tsx` -- React context provider
- `frontend/src/pages/VoxPage.tsx` -- VOX control center UI
- `frontend/src/components/VoxOverlay.tsx` -- Floating voice pill
- `frontend/src/components/VoxTourOverlay.tsx` -- Tour spotlight component

---

### 1.2 VoxSession Dataclass

Defined in `backend/services/vox_service.py`:

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

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | `str` | 8-character UUID prefix, e.g. `"a1b2c3d4"` |
| `mode` | `str` | Either `"gemini"` (native audio) or `"claude"` (text pipeline) |
| `model` | `str` | Model ID, e.g. `"gemini-2.5-flash-native-audio-preview-12-2025"` or `"claude-sonnet-4-6"` |
| `voice` | `str` | Gemini voice name (e.g. `"Puck"`), or `"browser"` for Claude mode |
| `created_at` | `float` | Unix timestamp of session creation |
| `system_instruction` | `str` | Full system prompt including personality, capabilities, awareness context |
| `tools` | `list` | List of function declaration dicts (34 entries) |
| `gemini_session` | `Any` | Active Gemini Live API session object (Gemini mode only) |
| `gemini_ctx` | `Any` | Async context manager for cleanup of the Live API connection |
| `turn_count` | `int` | Number of completed conversation turns |
| `function_count` | `int` | Number of function calls executed |
| `session_token` | `Optional[str]` | Gemini session resumption token for auto-reconnect |

---

### 1.3 16 Gemini Voices

Defined in the `GEMINI_VOICES` list in `backend/services/vox_service.py`:

| # | ID | Gender | Style |
|---|-----|--------|-------|
| 1 | Puck | Male | Upbeat, lively |
| 2 | Charon | Male | Informative, steady |
| 3 | Kore | Female | Firm, authoritative |
| 4 | Fenrir | Male | Excitable, bold |
| 5 | Aoede | Female | Breezy, warm |
| 6 | Leda | Female | Youthful, approachable |
| 7 | Orus | Male | Firm, decisive |
| 8 | Zephyr | Male | Calm, breezy |
| 9 | Sage | Non-binary | Wise, thoughtful |
| 10 | Vale | Non-binary | Gentle, melodic |
| 11 | Solaria | Female | Bright, energetic |
| 12 | River | Non-binary | Smooth, flowing |
| 13 | Ember | Female | Warm, passionate |
| 14 | Breeze | Female | Light, airy |
| 15 | Cove | Male | Deep, resonant |
| 16 | Orbit | Male | Futuristic, crisp |

Voices 1-8 are the original Gemini Live API voices. Voices 9-16 are extended voices added in v2.3.0.

The default voice is `"Puck"`, configured in `backend/config.py`:

```python
VOX_DEFAULT_VOICE = "Puck"
```

The voice is selected before connecting and persisted in `localStorage` under key `voxVoice` on the frontend.

---

### 1.4 34 Function Declarations

All 34 functions are defined in `build_function_declarations()` in `backend/services/vox_service.py`. They are registered as Gemini `FunctionDeclaration` objects for the Live API, and converted to Anthropic `tool_use` format for Claude.

#### Browser-Side Functions (6)

These execute in the browser via the `useVox` hook. The server forwards them to the client with `server_handled: false`.

**1. navigate_page**
```python
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
}
```

**2. get_current_page**
```python
{
    "name": "get_current_page",
    "description": "Get the current page path the user is viewing.",
    "parameters": {"type": "object", "properties": {}},
}
```

**3. get_workspace_state**
```python
{
    "name": "get_workspace_state",
    "description": "Get the current workspace state: active provider, model, page, theme, and project count.",
    "parameters": {"type": "object", "properties": {}},
}
```

**4. switch_model**
```python
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
}
```

**5. switch_theme**
```python
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
}
```

**6. read_page_content**
```python
{
    "name": "read_page_content",
    "description": "Read the visible text content of the current workspace page.",
    "parameters": {"type": "object", "properties": {}},
}
```

#### Core Workspace Functions (6)

**7. run_tool**
```python
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
}
```

**8. list_tools**
```python
{
    "name": "list_tools",
    "description": "List all available workspace tools with their categories.",
    "parameters": {"type": "object", "properties": {}},
}
```

**9. query_kg**
```python
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
}
```

**10. list_kgs**
```python
{
    "name": "list_kgs",
    "description": "List all available knowledge graph databases.",
    "parameters": {"type": "object", "properties": {}},
}
```

**11. run_agent**
```python
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
}
```

**12. list_agents**
```python
{
    "name": "list_agents",
    "description": "List all available NLKE agents.",
    "parameters": {"type": "object", "properties": {}},
}
```

#### Developer Tool Shortcuts (5)

**13. generate_react_component**
```python
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
}
```

**14. generate_fastapi_endpoint**
```python
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
}
```

**15. scan_code_security**
```python
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
}
```

**16. analyze_code_complexity**
```python
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
}
```

**17. generate_tests**
```python
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
}
```

#### Guided Tours (2)

**18. start_guided_tour**
```python
{
    "name": "start_guided_tour",
    "description": "Start an interactive voice-narrated guided tour of a workspace page. VOX highlights UI elements and explains each feature.",
    "parameters": {
        "type": "object",
        "properties": {
            "page": {"type": "string", "description": "Page to tour. Options: chat, coding, agents, playbooks, workflows, kg-studio, experts, builder, tools, vox, settings. If empty, tours the current page."},
        },
    },
}
```

**19. get_available_tours**
```python
{
    "name": "get_available_tours",
    "description": "List all available guided tours with page names and step counts.",
    "parameters": {"type": "object", "properties": {}},
}
```

#### Workspace Control -- Jarvis Mode (5)

**20. create_project**
```python
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
}
```

**21. list_projects**
```python
{
    "name": "list_projects",
    "description": "List all Studio projects with their status and file counts.",
    "parameters": {"type": "object", "properties": {}},
}
```

**22. run_workflow**
```python
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
}
```

**23. search_playbooks**
```python
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
}
```

**24. search_kg**
```python
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
}
```

#### KG Studio Control (3)

**25. get_kg_analytics**
```python
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
}
```

**26. cross_kg_search**
```python
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
}
```

**27. ingest_to_kg**
```python
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
}
```

#### Expert Control (2)

**28. chat_with_expert**
```python
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
}
```

**29. list_experts**
```python
{
    "name": "list_experts",
    "description": "List all available KG-OS experts with their specializations.",
    "parameters": {"type": "object", "properties": {}},
}
```

#### Voice Macros (4)

**30. create_macro**
```python
{
    "name": "create_macro",
    "description": "Create a voice macro -- a multi-step command sequence triggered by a phrase. Steps can chain functions together with output piping.",
    "parameters": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Macro name"},
            "trigger_phrase": {"type": "string", "description": "Voice trigger phrase, e.g. 'morning routine'"},
            "steps": {"type": "string", "description": 'JSON array of steps: [{"function":"fn_name","args":{},"pipe_from":null}]'},
            "error_policy": {"type": "string", "description": "What to do on error: abort, skip, or retry. Default: abort"},
        },
        "required": ["name", "trigger_phrase", "steps"],
    },
}
```

**31. list_macros**
```python
{
    "name": "list_macros",
    "description": "List all saved voice macros with their trigger phrases and step counts.",
    "parameters": {"type": "object", "properties": {}},
}
```

**32. run_macro**
```python
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
}
```

**33. delete_macro**
```python
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
}
```

#### Thermal Monitoring (1)

**34. check_thermal**
```python
{
    "name": "check_thermal",
    "description": "Check the device temperature and battery status. Warns if the device is getting too hot.",
    "parameters": {"type": "object", "properties": {}},
}
```

#### Summary by Category

| Category | Count | Functions |
|----------|-------|-----------|
| Browser-side | 6 | navigate_page, get_current_page, get_workspace_state, switch_model, switch_theme, read_page_content |
| Core Workspace | 6 | run_tool, list_tools, query_kg, list_kgs, run_agent, list_agents |
| Developer Tools | 5 | generate_react_component, generate_fastapi_endpoint, scan_code_security, analyze_code_complexity, generate_tests |
| Guided Tours | 2 | start_guided_tour, get_available_tours |
| Workspace Control | 5 | create_project, list_projects, run_workflow, search_playbooks, search_kg |
| KG Studio Control | 3 | get_kg_analytics, cross_kg_search, ingest_to_kg |
| Expert Control | 2 | chat_with_expert, list_experts |
| Voice Macros | 4 | create_macro, list_macros, run_macro, delete_macro |
| Thermal | 1 | check_thermal |
| **Total** | **34** | |

---

### 1.5 System Prompt

The full VOX system prompt is built by `build_system_instruction()` in `backend/services/vox_service.py`. It consists of a static base prompt, a dynamic awareness context injection, and an optional custom prompt from the user.

**Static base prompt (verbatim):**

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

**Dynamic awareness injection:**

After the static base, `build_system_instruction()` injects the current awareness context:

```python
try:
    from services.vox_awareness import vox_awareness
    awareness = vox_awareness.build_awareness_prompt()
    base += f"\nCURRENT AWARENESS:\n{awareness}\n"
except Exception:
    pass
```

The awareness prompt includes current page, recent navigation history, unresolved errors, active project/KG context, session duration, and most-visited pages.

**Custom prompt:**

If the user provides additional instructions via the system prompt field on the VOX page, they are appended:

```python
if custom_prompt:
    base += f"\nADDITIONAL INSTRUCTIONS:\n{custom_prompt}\n"
```

--- END OF PART 0 AND PART 1A ---

Sections 1.6-1.18 continue in WORKSPACE-REFERENCE-PART-1B.md

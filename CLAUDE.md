# CLAUDE.md — Multi-AI Agentic Workspace v2.2.0

## What This Is

A professional agentic workflow orchestrator combining Gemini + Claude intelligence. Built as a FastAPI backend + React 19 frontend with dual-model streaming, 33 NLKE agents, 53 playbooks, **58+ Python tools (11 categories)**, visual workflow execution, a full Graph-RAG Knowledge Graph workspace (57 SQLite KGs, 6 schema profiles, live hybrid search with numpy cosine similarity, d3-force graph visualization, NetworkX analytics, RAG chat, edge browser with edit/delete, multi-KG cross-search), an **AI-powered Studio** for generating full-stack React apps with live Sandpack preview, 3 editing modes, SQLite project persistence, and version history, a **KG-OS Expert Builder** for creating AI experts backed by structured knowledge graphs with intent-driven retrieval, a 4-weight scoring formula, and 56 semantic dimensions, a **VOX voice agent** (Gemini Live API + Claude tool_use, 17 function declarations), and a standalone **MCP server** exposing all tools via JSON-RPC.

## Quick Start

```bash
# Backend
cd backend && pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (install on laptop, copy node_modules to phone)
cd frontend && npm install && npm run dev
```

## Architecture

```
multi-ai-agentic-workspace/
├── backend/                    # FastAPI (Python)
│   ├── main.py                 # App entry, CORS, router mounting
│   ├── config.py               # API keys, model catalog, paths
│   ├── routers/                # 15 API routers
│   │   ├── chat.py             # POST /api/chat/stream (SSE, dual-model)
│   │   ├── coding.py           # POST /api/coding/stream (tool use)
│   │   ├── agents.py           # NLKE agent CRUD + execution
│   │   ├── playbooks.py        # Playbook search + retrieval
│   │   ├── workflows.py        # Workflow templates + execution
│   │   ├── builder.py          # Legacy web app plan + generate
│   │   ├── studio.py           # Studio: SSE streaming + project CRUD (18 endpoints)
│   │   ├── experts.py          # Expert Builder + KG-OS (15 endpoints, KGOS routes before dynamic)
│   │   ├── tools.py            # Tools playground (list, get, run, stream)
│   │   ├── vox.py              # VOX voice agent (WebSocket + REST, 17 functions, Claude tool_use)
│   │   ├── media.py            # Image edit + video gen
│   │   ├── interchange.py      # JSON import/export, mode toggle
│   │   └── kg.py               # KG Studio (33 endpoints, CRUD, search, analytics, RAG)
│   ├── services/               # Business logic (19 services)
│   │   ├── gemini_service.py   # google-genai SDK wrapper (lazy init)
│   │   ├── claude_service.py   # anthropic SDK wrapper (streaming + tool_use)
│   │   ├── model_router.py     # Intelligent model selection
│   │   ├── agent_bridge.py     # NLKE agent system bridge
│   │   ├── playbook_index.py   # Playbook file parser + search
│   │   ├── studio_service.py   # Studio SQLite CRUD, versions, ZIP export
│   │   ├── openapi_extractor.py # FastAPI code → OpenAPI spec (AST + regex)
│   │   ├── type_generator.py   # OpenAPI → TypeScript interfaces
│   │   ├── mock_server_manager.py # Node.js mock server process lifecycle
│   │   ├── tools_service.py    # 58+ tool registry, dynamic import + execution
│   │   ├── vox_service.py      # VOX sessions (Gemini Live API + Claude text pipeline)
│   │   ├── expert_service.py   # Expert CRUD + KG-OS execution pipeline
│   │   ├── kgos_query_engine.py # KG-OS: 12 query methods, 14 intents, 56 dimensions
│   │   ├── kg_service.py       # KG core: 6 schema profiles, auto-detect, CRUD
│   │   ├── embedding_service.py # Hybrid search (numpy cosine + BM25 + graph boost)
│   │   ├── analytics_service.py # NetworkX graph algorithms
│   │   ├── ingestion_service.py # AI entity extraction from text
│   │   └── rag_chat_service.py  # RAG chat with streaming + source citations
│   ├── mcp_server.py           # MCP server: 58+ tools via JSON-RPC stdio
│   └── tests/                  # API integration tests
│
├── frontend/                   # React 19 + TypeScript + Vite
│   ├── src/
│   │   ├── App.tsx             # Router + layout shell
│   │   ├── context/AppContext   # Global state (projects, models, personas)
│   │   ├── context/StudioContext # Studio state (files, mode, streaming, versions)
│   │   ├── context/VoxContext   # VOX voice agent state
│   │   ├── pages/              # 11 route pages (inc. ExpertsPage, ToolsPage, VoxPage)
│   │   ├── components/         # Reusable UI components
│   │   ├── components/studio/  # 28 Studio components (panels, editors, overlays)
│   │   ├── components/experts/ # 6 Expert components (Card, List, Builder, Chat, Config, Analytics)
│   │   ├── components/VoxOverlay.tsx # Floating VOX pill + transcript
│   │   ├── themes/             # 5 theme definitions (CSS variable maps)
│   │   ├── hooks/              # useChat, useTheme, useToast, useVox
│   │   ├── services/           # API + localStorage + studioApiService
│   │   └── types/              # TypeScript interfaces (studio, tools, vox, expert)
│   └── package.json
│
├── agents -> NLKE/agents       # Symlink to 33 NLKE agents
├── playbooks -> playbooks-v2   # Symlink to 53 playbooks
└── docs/                       # API docs, system atlas, user guide
```

## Dual-Mode Architecture

### Standalone Mode (default)
- Both `GEMINI_API_KEY` and `ANTHROPIC_API_KEY` active
- Backend calls both APIs directly
- Full dual-model UI with provider selector

### Claude Code Mode
- Only `GEMINI_API_KEY` active
- Claude tasks return structured JSON for Claude Code sessions
- 33 NLKE agents invocable via CLI by Claude Code
- Toggle via Settings page or `POST /api/mode`

## Key API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | /api/chat/stream | SSE streaming chat (Gemini or Claude) |
| POST | /api/coding/stream | Coding with tool use |
| GET | /api/agents | List 33 NLKE agents |
| POST | /api/agents/{name}/run | Execute an agent |
| GET | /api/playbooks | List 53 playbooks |
| GET | /api/playbooks/search?q= | Search playbooks |
| GET | /api/workflows/templates | 4 workflow templates |
| POST | /api/workflows/execute | Execute workflow (SSE) |
| POST | /api/builder/plan | Legacy AI project planning |
| POST | /api/builder/generate | Legacy full code generation |
| POST | /api/studio/stream | Studio AI streaming (generate/refine) |
| POST | /api/studio/projects | Create Studio project |
| GET | /api/studio/projects | List Studio projects |
| GET | /api/studio/projects/{id} | Load project (files + chat + versions) |
| PUT | /api/studio/projects/{id} | Update project |
| DELETE | /api/studio/projects/{id} | Delete project |
| POST | /api/studio/projects/{id}/save | Save version snapshot |
| GET | /api/studio/projects/{id}/versions | List versions |
| POST | /api/studio/projects/{id}/versions/{ver}/restore | Restore version |
| GET | /api/studio/projects/{id}/export | Download ZIP archive |
| POST | /api/studio/projects/{id}/mock/start | Start mock server |
| GET | /api/studio/projects/{id}/api-spec | Get OpenAPI spec |
| GET | /api/studio/projects/{id}/types | Get generated TypeScript types |
| POST | /api/export | Export workspace JSON |
| POST | /api/import | Import workspace JSON |
| GET | /api/kg/databases | List 57 KG databases with stats |
| GET | /api/kg/databases/{id}/nodes | Paginated nodes (search, filter) |
| POST | /api/kg/databases/{id}/search | Hybrid semantic search (0.40*embedding + 0.45*BM25 + 0.15*graph) |
| POST | /api/kg/search/multi | Cross-KG search across multiple databases |
| POST | /api/kg/databases/{id}/chat | RAG chat with streaming + source citations |
| GET | /api/kg/databases/{id}/analytics/* | Graph metrics, centrality, communities, paths |
| POST | /api/kg/compare | Structural KG comparison |
| POST | /api/kg/merge | Merge KGs (union/intersection/complement) |
| POST | /api/kg/databases/{id}/ingest | AI entity extraction from text |
| GET | /api/experts | List all experts |
| POST | /api/experts | Create expert |
| GET | /api/experts/{id} | Get expert |
| PUT | /api/experts/{id} | Update expert |
| DELETE | /api/experts/{id} | Delete expert |
| POST | /api/experts/{id}/duplicate | Duplicate expert |
| POST | /api/experts/{id}/chat | SSE streaming expert chat (KG-OS retrieval) |
| GET | /api/experts/{id}/conversations | List conversations |
| GET | /api/experts/{id}/conversations/{cid} | Get conversation with messages |
| DELETE | /api/experts/{id}/conversations/{cid} | Delete conversation |
| POST | /api/experts/kgos/query/{db_id} | Direct KG-OS query (testing/debug) |
| POST | /api/experts/kgos/impact/{db_id}/{node_id} | Impact analysis |
| POST | /api/experts/kgos/compose/{db_id} | Composition planning |
| POST | /api/experts/kgos/similar/{db_id}/{node_id} | Similar nodes |
| GET | /api/experts/kgos/dimensions | List 56 standard dimensions |
| GET | /api/tools | List 58+ tools (11 categories) |
| GET | /api/tools/{id} | Get tool definition + params |
| POST | /api/tools/{id}/run | Execute a tool |
| GET | /api/vox/status | VOX availability + active sessions |
| GET | /api/vox/voices | List Gemini Live API voices |
| GET | /api/vox/functions | List 17 VOX function declarations |
| POST | /api/vox/function/{name} | Execute a workspace function |
| WS | /ws/vox | VOX bidirectional voice WebSocket |
| GET | /api/health | Health check + mode |
| GET | /api/models | Available model catalog |

## Model Catalog

| Provider | Model | Use Case |
|----------|-------|----------|
| Gemini | gemini-2.5-flash | Fast coding, default |
| Gemini | gemini-2.5-pro | Deep reasoning |
| Gemini | gemini-3-pro | Flagship |
| Claude | claude-haiku-4.5 | Budget routing |
| Claude | claude-sonnet-4.6 | Fast + capable |
| Claude | claude-opus-4.6 | Most intelligent |

## Frontend Pages

| Route | Page | Purpose |
|-------|------|---------|
| /chat | ChatPage | Dual-model streaming chat |
| /coding | CodingPage | IDE with file explorer + AI coding |
| /agents | AgentsPage | 33 NLKE agents + pipeline builder |
| /playbooks | PlaybooksPage | 53 playbooks search + reader |
| /workflows | WorkflowsPage | Visual workflow designer + executor |
| /kg-studio | KGStudioPage | Graph-RAG KG workspace (10 tabs, 57 DBs, React Flow + d3-force, edge browser, multi-KG search) |
| /builder | StudioPage | AI Studio: chat→generate→preview, 3 modes, version history |
| /experts | ExpertsPage | KG-OS Expert Builder: create AI experts backed by KGs, 4-weight scoring, source citations |
| /tools | ToolsPage | 58+ Python tools playground (11 categories, dynamic param form, output panel) |
| /vox | VoxPage | VOX voice control center: mode/voice/model selectors, transcript, function log |
| /integrations | IntegrationsPage | Platform integrations management |
| /settings | SettingsPage | Mode toggle, themes, export/import |

## Theme System

5 themes via CSS custom properties on `:root`. Persisted in localStorage (`workspace_theme`).

| Theme ID | Name | Key Vars |
|----------|------|----------|
| `default` | Default | `--t-bg: #111827`, `--t-primary: #0ea5e9` |
| `crt` | Deluxe-CRT | `--t-bg: #0a0a08`, `--t-primary: #ffb000`, scanline overlay |
| `scratch` | Scratch | `--t-bg: #fafaf8`, `--t-text: #1a1a1a`, Patrick Hand font |
| `solarized` | Solarized Zen | `--t-bg: #002b36`, `--t-primary: #2aa198` |
| `sunset` | Sunset Warm | `--t-bg: #1a1218`, `--t-primary: #ff6b6b` |

**Key files:** `src/themes/index.ts` (definitions), `src/hooks/useTheme.ts` (apply + persist), `src/components/ThemeSwitcher.tsx` (NavBar dropdown)

**CSS variable pattern:** All components use `style={{ background: 'var(--t-surface)', color: 'var(--t-text)' }}` instead of hardcoded Tailwind colors. Layout classes (flex, p-4, rounded) stay in className.

## Symlink Setup (run manually)

```bash
cd multi-ai-agentic-workspace
ln -sf /storage/emulated/0/Download/44nlke/NLKE/agents agents
ln -sf /path/to/playbooks/playbooks-v2 playbooks
```

## Testing

```bash
cd backend
python -m pytest tests/ -v
# or
python tests/run_all.py
```

## Security Notes

- API keys are in config.py with env var overrides
- CORS allows all origins (dev mode)
- No authentication (local/trusted environment)

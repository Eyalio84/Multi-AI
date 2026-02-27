# CLAUDE.md — Multi-AI Agentic Workspace v3.0.0

## What This Is

A professional agentic workflow orchestrator combining Gemini + Claude + OpenAI intelligence. Built as a FastAPI backend + React 19 frontend with tri-model streaming, 33 NLKE agents, 53 playbooks, **58+ Python tools (11 categories)**, visual workflow execution, a full Graph-RAG Knowledge Graph workspace (57 SQLite KGs, 6 schema profiles, live hybrid search with numpy cosine similarity, d3-force graph visualization, NetworkX analytics, RAG chat, edge browser with edit/delete, multi-KG cross-search), an **AI-powered Studio** for generating full-stack React apps with live Sandpack preview, 3 editing modes, SQLite project persistence, and version history, a **KG-OS Expert Builder** for creating AI experts backed by structured knowledge graphs with intent-driven retrieval, a 4-weight scoring formula, and 56 semantic dimensions, a **VOX voice agent** (Gemini Live API + Claude tool_use, **34 function declarations**, 16 voices, Google Search grounding, awareness layer, guided tours, voice macros, thermal monitoring, auto-reconnect), a **Games Studio** for AI-generated Phaser 3 RPG games with structured interview, GDD synthesis, live preview, local LLM NPC dialogue, and expert chat, a **43-model catalog** (20 Gemini + 3 Claude + 20 OpenAI across 8 categories: text, reasoning, image, video, audio, music, embedding, agent), **5 slash commands** (/image, /tts, /video, /agent, /help) in the Chat page, **Claude Agent SDK** integration for autonomous tasks, **media generation endpoints** (image, video, TTS, music), a unified **8-stage agentic loop** (intake, memory, skills, context, infer, tools, stream, persist), **persistent conversation memory** stored as a KG with hybrid retrieval, **skill injection** (intent classification + playbook/KG context enrichment), a **messaging gateway** with 7 platform adapters, and a standalone **MCP server** exposing all tools via JSON-RPC.

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
│   ├── main.py                 # App entry, CORS, router mounting, Phaser static files
│   ├── config.py               # API keys, 44-model catalog (3 providers), paths, VOX config
│   ├── routers/                # 17 API routers
│   │   ├── chat.py             # POST /api/chat/stream (SSE, tri-model, agentic loop)
│   │   ├── coding.py           # POST /api/coding/stream (tool use)
│   │   ├── agents.py           # NLKE agent CRUD + execution
│   │   ├── playbooks.py        # Playbook search + retrieval
│   │   ├── workflows.py        # Workflow templates + execution
│   │   ├── builder.py          # Legacy web app plan + generate
│   │   ├── studio.py           # Studio: SSE streaming + project CRUD (18 endpoints)
│   │   ├── experts.py          # Expert Builder + KG-OS (15 endpoints, KGOS routes before dynamic)
│   │   ├── tools.py            # Tools playground (list, get, run, stream)
│   │   ├── vox.py              # VOX voice agent (WebSocket + REST, 34 functions, Claude tool_use)
│   │   ├── media.py            # Image edit/gen, video gen, TTS, music (9 endpoints)
│   │   ├── memory.py           # Conversation memory: CRUD, search, stats (7 endpoints)
│   │   ├── integrations.py     # Platform integrations (webhooks, Spotify, Calendar)
│   │   ├── interchange.py      # JSON import/export, mode toggle
│   │   ├── kg.py               # KG Studio (33 endpoints, CRUD, search, analytics, RAG)
│   │   ├── games.py            # Games Studio (20 endpoints: CRUD, interview, GDD, generate, refine, chat, LLM, versions, export)
│   │   └── agent.py            # Claude Agent SDK (run, sessions, session status)
│   ├── data/                   # Static data
│   │   └── vox_tours.json      # 11 guided tour definitions
│   ├── services/               # Business logic (31 services)
│   │   ├── gemini_service.py   # google-genai SDK wrapper (lazy init, image/video/TTS/music gen)
│   │   ├── claude_service.py   # anthropic SDK wrapper (streaming + tool_use)
│   │   ├── openai_service.py   # openai SDK wrapper (Responses API, streaming, image gen, TTS)
│   │   ├── model_router.py     # Intelligent model selection (tri-provider)
│   │   ├── agentic_loop.py     # Unified 8-stage pipeline (intake→memory→skills→context→infer→tools→stream→persist)
│   │   ├── memory_service.py   # Persistent conversation memory (KG-backed, FTS5, hybrid retrieval)
│   │   ├── skill_injector.py   # Intent classification + playbook/KG context injection (10 categories)
│   │   ├── agent_bridge.py     # NLKE agent system bridge
│   │   ├── agent_sdk_service.py # Claude Agent SDK wrapper (autonomous file operations)
│   │   ├── playbook_index.py   # Playbook file parser + search
│   │   ├── studio_service.py   # Studio SQLite CRUD, versions, ZIP export
│   │   ├── openapi_extractor.py # FastAPI code → OpenAPI spec (AST + regex)
│   │   ├── type_generator.py   # OpenAPI → TypeScript interfaces
│   │   ├── mock_server_manager.py # Node.js mock server process lifecycle
│   │   ├── tools_service.py    # 58+ tool registry, dynamic import + execution
│   │   ├── vox_service.py      # VOX sessions (Gemini Live API + Claude, 34 functions, 16 voices)
│   │   ├── vox_awareness.py    # Workspace awareness (SQLite: page visits, errors, context)
│   │   ├── vox_macros.py       # Voice macro CRUD + pipe-chaining execution
│   │   ├── vox_thermal.py      # Device thermal monitoring (Termux battery API)
│   │   ├── expert_service.py   # Expert CRUD + KG-OS execution pipeline
│   │   ├── kgos_query_engine.py # KG-OS: 12 query methods, 14 intents, 56 dimensions
│   │   ├── kg_service.py       # KG core: 6 schema profiles, auto-detect, CRUD
│   │   ├── embedding_service.py # Hybrid search (numpy cosine + BM25 + graph boost)
│   │   ├── analytics_service.py # NetworkX graph algorithms
│   │   ├── ingestion_service.py # AI entity extraction from text
│   │   ├── rag_chat_service.py  # RAG chat with streaming + source citations
│   │   ├── game_service.py     # Game project CRUD, 18-question interview, GDD synthesis, versions
│   │   ├── game_generator.py   # GDD → Phaser 3 code (AI + templates, ### FILE: markers)
│   │   ├── game_llm_service.py # Local LLM NPC dialogue (llama-cpp: DeepSeek, Gemma, Qwen)
│   │   ├── messaging_gateway.py # Inbound message routing through agentic loop
│   │   ├── platform_adapters.py # 7 platform adapters (Telegram, WhatsApp, Discord, Slack, Gmail, Spotify, Calendar)
│   │   └── workflow_service.py  # Workflow persistence (SQLite CRUD)
│   ├── mcp_server.py           # MCP server: 58+ tools via JSON-RPC stdio
│   └── tests/                  # API integration tests
│
├── frontend/                   # React 19 + TypeScript + Vite
│   ├── src/
│   │   ├── App.tsx             # Router + layout shell (14 routes)
│   │   ├── context/AppContext.tsx  # Global state (projects, models, personas)
│   │   ├── context/StudioContext.tsx # Studio state (files, mode, streaming, versions)
│   │   ├── context/VoxContext.tsx # VOX voice agent state
│   │   ├── pages/              # 14 route pages
│   │   │   ├── ChatPage.tsx    # Tri-model streaming chat + 5 slash commands
│   │   │   ├── CodingPage.tsx  # IDE with file explorer + AI coding
│   │   │   ├── AgentsPage.tsx  # 33 NLKE agents + pipeline builder
│   │   │   ├── PlaybooksPage.tsx # 53 playbooks search + reader
│   │   │   ├── WorkflowsPage.tsx # Visual workflow designer + executor
│   │   │   ├── KGStudioPage.tsx # Graph-RAG KG workspace (10 tabs, 57 DBs)
│   │   │   ├── StudioPage.tsx  # AI Studio: chat→generate→preview
│   │   │   ├── BuilderPage.tsx # Legacy web app builder
│   │   │   ├── ExpertsPage.tsx # KG-OS Expert Builder
│   │   │   ├── ToolsPage.tsx   # 58+ Python tools playground
│   │   │   ├── VoxPage.tsx     # VOX voice control center
│   │   │   ├── GamesPage.tsx   # Games Studio: interview→generate→preview→refine
│   │   │   ├── IntegrationsPage.tsx # Platform integrations management
│   │   │   └── SettingsPage.tsx # Mode toggle, themes, export/import
│   │   ├── components/         # Reusable UI components
│   │   │   ├── NavBar.tsx      # Navigation with 13 links + theme switcher + settings
│   │   │   ├── ModelSelector.tsx # Grouped model dropdown (43 models by category, 3 provider filters)
│   │   │   ├── ThemeSwitcher.tsx # NavBar theme dropdown
│   │   │   ├── ToastContainer.tsx # Toast notifications
│   │   │   ├── VoxOverlay.tsx  # Floating VOX pill + transcript
│   │   │   ├── VoxTourOverlay.tsx # Guided tour spotlight + navigation
│   │   │   ├── chat/           # 8 chat components (AssistantMessage, ChatPanel, CodeBlock, ConversationSidebar, LoadingIndicator, MessageItem, ToolMessage, UserMessage)
│   │   │   ├── studio/         # 28 Studio components (panels, editors, overlays)
│   │   │   ├── experts/        # 6 Expert components (Card, List, Builder, Chat, Config, Analytics)
│   │   │   ├── games/          # 7 Games components (GameChat, GameCodeEditor, GameDesignView, GameInterview, GameList, GamePreview, GameVersions)
│   │   │   ├── agents/         # Agent pipeline components
│   │   │   ├── builders/       # Builder components
│   │   │   ├── kg/             # KG Studio components
│   │   │   ├── playbooks/      # Playbook components
│   │   │   └── workflows/      # Workflow components
│   │   ├── themes/             # 5 theme definitions (CSS variable maps)
│   │   ├── hooks/              # useChat (slash commands), useTheme, useToast, useVox
│   │   ├── services/           # apiService, storageService, studioApiService
│   │   └── types/              # 11 TypeScript type files (ai, chat, expert, game, index, kg, memory, project, studio, tools, vox)
│   └── package.json
│
├── agents -> NLKE/agents       # Symlink to 33 NLKE agents
├── playbooks -> playbooks-v2   # Symlink to 53 playbooks
└── docs/                       # API docs, system atlas, user guide, Phaser runtime
```

## Tri-Provider Architecture

### Standalone Mode (default)
- All three API keys active: `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`
- Backend calls all three APIs directly
- Full tri-model UI with provider selector (Gemini / Claude / OpenAI)

### Claude Code Mode
- Only `GEMINI_API_KEY` active
- Claude/OpenAI tasks return structured JSON for Claude Code sessions
- 33 NLKE agents invocable via CLI by Claude Code
- Toggle via Settings page or `POST /api/mode`

## Unified Agentic Loop (8 Stages)

All chat/coding/studio/RAG/messaging streams flow through a single `AgenticLoop` pipeline:

| Stage | Name | Purpose |
|-------|------|---------|
| 1 | **Intake** | Parse request, resolve model, create/resume conversation |
| 2 | **Memory** | Recall relevant past conversations via hybrid search |
| 3 | **Skills** | Intent classification + playbook/KG context injection |
| 4 | **Context** | Build system prompt with persona, memories, skills |
| 5 | **Infer** | Call Gemini or Claude with streaming |
| 6 | **Tools** | Handle tool calls (file ops, code execution) |
| 7 | **Stream** | Yield SSE events (tokens, thinking, tool calls, grounding) |
| 8 | **Persist** | Save assistant response + extracted entities to memory KG |

Modes: `chat`, `coding`, `studio`, `rag`, `messaging`

## Key API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | /api/chat/stream | SSE streaming chat (Gemini or Claude, agentic loop) |
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
| POST | /api/kg/databases/{id}/search | Hybrid semantic search (0.40*emb + 0.45*BM25 + 0.15*graph) |
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
| GET | /api/vox/voices | List 16 Gemini Live API voices |
| GET | /api/vox/functions | List 34 VOX function declarations |
| POST | /api/vox/function/{name} | Execute a workspace function |
| POST | /api/vox/awareness | Log page visit / error / context |
| GET | /api/vox/awareness | Get current awareness context |
| GET | /api/vox/tours | List 11 available guided tours |
| GET | /api/vox/tours/{page} | Get tour steps for a page |
| GET | /api/vox/macros | List saved voice macros |
| POST | /api/vox/macros | Create a voice macro |
| DELETE | /api/vox/macros/{id} | Delete a voice macro |
| POST | /api/vox/macros/{id}/run | Execute a voice macro |
| GET | /api/vox/thermal | Device temperature + battery status |
| WS | /ws/vox | VOX bidirectional voice WebSocket |
| POST | /api/media/image/generate | Generate images (Nano Banana Pro / Imagen 4) |
| POST | /api/media/video/generate | Generate video (Veo 3.1) |
| POST | /api/media/tts/generate | Text-to-speech (Gemini TTS, 24 voices) |
| POST | /api/media/music/generate | Generate music (Lyria) |
| POST | /api/image/edit | Edit image (legacy, multimodal) |
| POST | /api/video/generate | Start video gen (legacy) |
| GET | /api/video/status | Poll video status (legacy) |
| POST | /api/agent/run | Run autonomous Claude agent (SSE stream) |
| GET | /api/agent/sessions | List recent agent sessions |
| GET | /api/agent/sessions/{id} | Get agent session status |
| GET | /api/memory/conversations | List conversations (filter by mode/source) |
| GET | /api/memory/conversations/{id} | Get conversation |
| GET | /api/memory/conversations/{id}/messages | Get messages (paginated) |
| DELETE | /api/memory/conversations/{id} | Delete conversation |
| POST | /api/memory/search | Search memory (hybrid retrieval) |
| GET | /api/memory/stats | Memory + injection statistics |
| GET | /api/games | List game projects |
| POST | /api/games | Create game project |
| GET | /api/games/{id} | Get game project |
| PUT | /api/games/{id} | Update game project |
| DELETE | /api/games/{id} | Delete game project |
| GET | /api/games/interview/questions | Get 18 interview questions |
| POST | /api/games/{id}/interview | Submit interview answer |
| POST | /api/games/{id}/synthesize | Synthesize GDD from answers |
| POST | /api/games/{id}/generate | Generate Phaser 3 code (SSE) |
| POST | /api/games/{id}/refine | Refine game code (SSE) |
| POST | /api/games/{id}/chat | Expert game chat (SSE) |
| POST | /api/games/{id}/save | Save version snapshot |
| GET | /api/games/{id}/versions | List versions |
| POST | /api/games/{id}/versions/{ver}/restore | Restore version |
| GET | /api/games/{id}/export | Export game as ZIP |
| POST | /api/games/{id}/extract-patterns | Extract gameplay patterns |
| GET | /api/games/llm/status | Local LLM status |
| POST | /api/games/llm/load | Load local LLM model |
| POST | /api/games/llm/unload | Unload local LLM |
| POST | /api/games/llm/chat | Chat with NPC via local LLM |
| GET | /api/integrations/* | Platform integrations (Telegram, WhatsApp, Discord, Slack, Gmail, Spotify, Calendar) |
| GET | /api/health | Health check + mode |
| GET | /api/models | Available model catalog (43 models, 3 providers) |

## Model Catalog (44 Models, 3 Providers, 8 Categories)

### Gemini Text Models (7)

| Provider | Model ID | Name | Context | Use Case |
|----------|----------|------|---------|----------|
| Gemini | gemini-3-pro-preview | Gemini 3 Pro | 1M | Flagship reasoning |
| Gemini | gemini-3.1-pro-preview | Gemini 3.1 Pro | 1M | Better thinking, token efficiency, agentic |
| Gemini | gemini-3.1-pro-preview-customtools | Gemini 3.1 Pro Custom Tools | 1M | Prioritizes custom tools over bash |
| Gemini | gemini-3-flash-preview | Gemini 3 Flash | 1M | Fast next-gen flash |
| Gemini | gemini-2.5-flash | Gemini 2.5 Flash | 1M | Fast coding/streaming (default) |
| Gemini | gemini-2.5-pro | Gemini 2.5 Pro | 1M | Deep reasoning |
| Gemini | gemini-2.5-flash-lite | Gemini 2.5 Flash Lite | 1M | Cheapest Gemini, bulk tasks |

### Gemini Image Models (3)

| Provider | Model ID | Name | Use Case |
|----------|----------|------|----------|
| Gemini | gemini-2.5-flash-image | Gemini 2.5 Flash Image | Fast image generation/editing |
| Gemini | gemini-3-pro-image-preview | Nano Banana Pro | High-quality image generation |
| Gemini | imagen-4.0-generate-preview-05-20 | Imagen 4 | Dedicated image generation (non-chat) |

### Gemini Video Models (3)

| Provider | Model ID | Name | Use Case |
|----------|----------|------|----------|
| Gemini | veo-2.0-generate-001 | Veo 2.0 | Video generation (legacy) |
| Gemini | veo-3.1-generate-preview | Veo 3.1 | Video generation with audio |
| Gemini | veo-3.1-fast-generate-preview | Veo 3.1 Fast | Fast video generation |

### Gemini Audio/TTS Models (3)

| Provider | Model ID | Name | Use Case |
|----------|----------|------|----------|
| Gemini | gemini-2.5-flash-native-audio-preview | Gemini Flash Audio | Native audio understanding/generation |
| Gemini | gemini-2.5-flash-preview-tts | Gemini Flash TTS | Text-to-speech (24 voices) |
| Gemini | gemini-2.5-pro-preview-tts | Gemini Pro TTS | High-quality text-to-speech |

### Gemini Music, Embedding, Agent Models (4)

| Provider | Model ID | Name | Use Case |
|----------|----------|------|----------|
| Gemini | lyria-realtime-exp | Lyria | AI music generation |
| Gemini | gemini-embedding-001 | Gemini Embedding | RAG/embeddings |
| Gemini | gemini-2.5-computer-use-preview | Gemini Computer Use | Autonomous computer control |
| Gemini | deep-research-pro-preview | Deep Research | Multi-step web research |

### Claude Models (3)

| Provider | Model ID | Name | Context | Use Case |
|----------|----------|------|---------|----------|
| Claude | claude-opus-4-6 | Claude Opus 4.6 | 200K | Most intelligent |
| Claude | claude-sonnet-4-6 | Claude Sonnet 4.6 | 200K | Fast + capable (default) |
| Claude | claude-haiku-4-5-20251001 | Claude Haiku 4.5 | 200K | Cheapest, routing |

### OpenAI Text Models (8)

| Provider | Model ID | Name | Context | Use Case |
|----------|----------|------|---------|----------|
| OpenAI | gpt-5.2 | GPT-5.2 | 400K | Latest flagship |
| OpenAI | gpt-5.1 | GPT-5.1 | 1M | Agentic coding (1M context) |
| OpenAI | gpt-5 | GPT-5 | 128K | Original GPT-5 |
| OpenAI | gpt-5-mini | GPT-5 Mini | 128K | Balanced (default) |
| OpenAI | gpt-5-nano | GPT-5 Nano | 128K | Budget |
| OpenAI | gpt-4.1 | GPT-4.1 | 1M | Long-context |
| OpenAI | gpt-4.1-mini | GPT-4.1 Mini | 1M | Fast long-context |
| OpenAI | gpt-4.1-nano | GPT-4.1 Nano | 1M | Cheapest long-context |

### OpenAI Reasoning Models (3)

| Provider | Model ID | Name | Context | Use Case |
|----------|----------|------|---------|----------|
| OpenAI | o3 | o3 | 200K | Deep reasoning |
| OpenAI | o4-mini | o4-mini | 200K | Fast reasoning |
| OpenAI | o3-pro | o3-pro | 200K | Highest quality reasoning |

### OpenAI Image, Video, Audio, Embedding, Agent Models (10)

| Provider | Model ID | Name | Category | Use Case |
|----------|----------|------|----------|----------|
| OpenAI | gpt-image-1.5 | GPT Image 1.5 | image | Latest image generation |
| OpenAI | gpt-image-1 | GPT Image 1 | image | Image generation |
| OpenAI | sora-2 | Sora 2 | video | Video generation |
| OpenAI | sora-2-pro | Sora 2 Pro | video | High-quality video |
| OpenAI | gpt-4o-mini-tts | GPT-4o Mini TTS | audio | Text-to-speech |
| OpenAI | whisper-1 | Whisper | audio | Speech-to-text |
| OpenAI | text-embedding-3-large | Embedding 3 Large | embedding | High-quality embeddings |
| OpenAI | text-embedding-3-small | Embedding 3 Small | embedding | Budget embeddings |
| OpenAI | gpt-5.2-codex | Codex (GPT-5.2) | agent | Autonomous coding agent |

## Frontend Pages (14 Routes)

| Route | Page | Purpose |
|-------|------|---------|
| /chat | ChatPage | Tri-model streaming chat + 5 slash commands (/image, /tts, /video, /agent, /help) |
| /coding | CodingPage | IDE with file explorer + AI coding |
| /agents | AgentsPage | 33 NLKE agents + pipeline builder |
| /playbooks | PlaybooksPage | 53 playbooks search + reader |
| /workflows | WorkflowsPage | Visual workflow designer + executor |
| /kg-studio | KGStudioPage | Graph-RAG KG workspace (10 tabs, 57 DBs, React Flow + d3-force, edge browser, multi-KG search) |
| /builder | StudioPage | AI Studio: chat, generate, preview, 3 modes, version history |
| /experts | ExpertsPage | KG-OS Expert Builder: create AI experts backed by KGs, 4-weight scoring, source citations |
| /tools | ToolsPage | 58+ Python tools playground (11 categories, dynamic param form, output panel) |
| /vox | VoxPage | VOX voice control center: 16 voices, 34 functions, macros panel, transcript, function log |
| /games | GamesPage | Games Studio: 18-question interview, GDD synthesis, Phaser 3 generation, live preview, code editor, expert chat, local LLM NPC dialogue, versions |
| /integrations | IntegrationsPage | Platform integrations management (Telegram, WhatsApp, Discord, Slack, Gmail, Spotify, Calendar) |
| /settings | SettingsPage | Mode toggle, themes, export/import |

Note: BuilderPage exists as a legacy route but /builder renders StudioPage in the router.

## Chat Page Slash Commands

The Chat page supports 5 slash commands processed client-side via `useChat.ts`:

| Command | Example | Description |
|---------|---------|-------------|
| `/image <prompt>` | `/image a sunset over mountains` | Generate an image via Nano Banana Pro |
| `/tts <text>` | `/tts Hello, welcome to the workspace` | Text-to-speech via Gemini TTS |
| `/video <prompt>` | `/video a mountain lake at sunrise` | Start video generation via Veo 3.1 |
| `/agent <prompt>` | `/agent list all Python files in backend` | Run autonomous Claude agent task |
| `/help` | `/help` | Show available commands |

## Games Studio

AI-powered Phaser 3 RPG game generator with a structured interview-to-playable pipeline:

| Phase | Description |
|-------|-------------|
| **Interview** | 18 questions across 3 story arcs (Player, World, Systems) with select/multi-select/text inputs |
| **GDD Synthesis** | AI synthesizes interview answers into a structured Game Design Document |
| **Generation** | AI generates complete Phaser 3.90.0 code (ES6 classes, Arcade Physics, programmatic sprites) |
| **Preview** | Live in-browser Phaser preview with local phaser.min.js runtime |
| **Refine** | Chat-based refinement — describe changes, AI regenerates affected files |
| **Expert Chat** | GameForge expert backed by game-dev KG for design advice |
| **Local LLM** | On-device NPC dialogue via llama-cpp-python (DeepSeek R1, Gemma 3 1B, Gemma 2 2B, Qwen) |
| **Versions** | Save/restore version snapshots, export as ZIP |

Frontend components: GameInterview, GamePreview, GameCodeEditor, GameChat, GameDesignView, GameList, GameVersions (6 tabs: Interview, Preview, Code, Chat, GDD, Versions)

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

- API keys loaded from `.env` files via `python-dotenv` with env var overrides
- Runtime key updates via `POST /api/config/keys`
- CORS allows all origins (dev mode)
- No authentication (local/trusted environment)

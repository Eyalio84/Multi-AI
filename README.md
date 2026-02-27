# Multi-AI Agentic Workspace

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=white)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.4-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Models](https://img.shields.io/badge/AI_Models-23-blueviolet)]()
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A professional agentic workflow orchestrator combining **Gemini + Claude** intelligence. 23 AI models across 7 categories, dual-model streaming, an AI-powered app Studio, Knowledge Graph workspace, Expert Builder, voice agent, game studio, 58+ tools, and 5 visual themes -- all in one interface.

---

## Features

- **Dual-Model AI Chat** -- Stream responses from Gemini or Claude with a 23-model selector and slash commands (`/image`, `/tts`, `/video`, `/agent`)
- **AI Studio** -- Generate full-stack React apps from a prompt with live Sandpack preview, 3 editing modes, SQLite project persistence, version history, and ZIP export
- **KG-OS Expert Builder** -- Create AI experts backed by structured knowledge graphs with intent-driven retrieval, 4-weight scoring formula, and 56 semantic dimensions
- **KG Studio** -- Graph-RAG workspace: 57 SQLite KGs, 6 schema profiles, hybrid search (embedding + BM25 + graph boost), d3-force visualization, NetworkX analytics, RAG chat with source citations, and multi-KG cross-search
- **Games Studio** -- AI-powered Phaser 3 RPG game generation with interview-driven design, KG context injection, and live preview
- **VOX Voice Agent** -- Gemini Live API + Claude tool_use: 34 function declarations, 16 voices, Google Search grounding, workspace awareness, guided tours, voice macros, thermal monitoring, and auto-reconnect
- **Tools Playground** -- 58+ Python tools across 11 categories with dynamic parameter forms and streaming output
- **Media Generation** -- Image (Imagen 4, Nano Banana Pro), video (Veo 3.1), TTS (24 voices), and music (Lyria)
- **33 NLKE Agents** -- Autonomous agents for error recovery, KG curation, reasoning, cost optimization, and more
- **53 Playbooks** -- Searchable implementation recipes for cost optimization, prompt engineering, deployment, and beyond
- **Visual Workflows** -- DAG-based workflow designer with SSE execution and 4 built-in templates
- **MCP Server** -- Standalone JSON-RPC server exposing all 58+ tools for Claude Code integration
- **5 Themes** -- Default, Deluxe-CRT, Scratch, Solarized Zen, Sunset Warm
- **Mobile-First** -- Responsive design with collapsible sidebars and touch-friendly controls

## Screenshots

<!-- Add screenshots here -->
<!-- ![Chat](docs/screenshots/chat.png) -->
<!-- ![Studio](docs/screenshots/studio.png) -->
<!-- ![KG Studio](docs/screenshots/kg-studio.png) -->
<!-- ![Games](docs/screenshots/games.png) -->

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.11+, FastAPI 0.115+, Uvicorn |
| **Frontend** | React 19, TypeScript 5.4, Vite 5 |
| **Styling** | Tailwind CSS 3.4, CSS custom properties (5 themes) |
| **AI SDKs** | `google-genai` (Gemini), `anthropic` (Claude) |
| **Graph/Search** | SQLite + FTS5, NetworkX, numpy, model2vec, LightRAG |
| **Visualization** | React Flow, d3-force |
| **App Preview** | Sandpack (CodeSandbox runtime) |
| **Game Engine** | Phaser 3 |
| **Voice** | Gemini Live API (WebSocket, PCM audio) |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- API keys for [Google AI Studio](https://aistudio.google.com/) and/or [Anthropic Console](https://console.anthropic.com/)

### Backend

```bash
cd backend
pip install -r requirements.txt

# Set API keys (or configure at runtime via the Settings page)
export GEMINI_API_KEY="your-gemini-key"
export ANTHROPIC_API_KEY="your-anthropic-key"  # optional for Claude Code mode

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). The Vite dev server proxies `/api` requests to the backend on port 8000.

### Verify

- **Swagger UI**: http://localhost:8000/docs
- **Frontend**: http://localhost:5173
- **Health check**: http://localhost:8000/api/health

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     React 19 Frontend                       │
│  Chat | Studio | Experts | KG Studio | Games | VOX | ...   │
├─────────────────────────────────────────────────────────────┤
│                  Vite Dev Server (:5173)                     │
│                  Proxy /api -> :8000                         │
├─────────────────────────────────────────────────────────────┤
│                  FastAPI Backend (:8000)                     │
│  17 Routers | 28 Services | Model Router | Agent Bridge     │
├─────────────────────────────────────────────────────────────┤
│                     External APIs                           │
│  Gemini API (20 models) | Claude API (3 models)            │
│  33 NLKE Agents         | 53 Playbooks                     │
│  57 SQLite KGs          | 58+ Python Tools                 │
└─────────────────────────────────────────────────────────────┘
```

### Dual-Mode Operation

| Mode | Description |
|------|-------------|
| **Standalone** (default) | Both `GEMINI_API_KEY` and `ANTHROPIC_API_KEY` active. Full dual-model UI with all 23 models. |
| **Claude Code** | Only `GEMINI_API_KEY` active. Claude tasks return structured JSON for CLI sessions. |

Toggle via the Settings page or `POST /api/mode`.

---

## Pages

| Route | Page | Description |
|-------|------|-------------|
| `/chat` | Chat | Dual-model streaming chat with 23-model selector and slash commands |
| `/coding` | Coding | IDE with file explorer and AI-assisted coding via tool use |
| `/builder` | Studio | AI app generator with live Sandpack preview, version history, ZIP export |
| `/experts` | Experts | KG-OS Expert Builder -- AI experts backed by knowledge graphs |
| `/kg-studio` | KG Studio | Graph-RAG workspace: 57 KGs, hybrid search, d3 visualization, RAG chat |
| `/games` | Games | Phaser 3 RPG game studio with AI interview-driven generation |
| `/tools` | Tools | 58+ Python tools playground with dynamic parameter forms |
| `/vox` | VOX | Voice agent: 16 voices, 34 functions, macros, transcript |
| `/agents` | Agents | 33 NLKE agents with pipeline builder |
| `/playbooks` | Playbooks | 53 searchable implementation playbooks |
| `/workflows` | Workflows | Visual workflow designer with SSE execution |
| `/integrations` | Integrations | Platform integrations (Telegram, Discord, Slack, Gmail, Spotify) |
| `/settings` | Settings | Mode toggle, theme picker, API key config, export/import |

---

## Model Catalog

### Gemini (20 models)

| Model | Category | Context | Cost (in/out $/MTok) | Use Case |
|-------|----------|---------|----------------------|----------|
| Gemini 3.1 Pro | Text | 1M | $2.00 / $12.00 | Flagship -- better thinking, agentic workflows |
| Gemini 3 Pro | Text | 1M | $2.00 / $12.00 | Flagship reasoning |
| Gemini 2.5 Pro | Text | 1M | $1.25 / $5.00 | Deep reasoning |
| Gemini 2.5 Flash | Text | 1M | $0.15 / $0.60 | Fast coding/streaming (default) |
| Gemini 3 Flash | Text | 1M | $0.10 / $0.40 | Fast next-gen flash |
| Gemini 2.5 Flash Lite | Text | 1M | $0.075 / $0.30 | Cheapest, bulk tasks |
| Nano Banana Pro | Image | 1M | $2.00 / $12.00 | High-quality image generation |
| Gemini 2.5 Flash Image | Image | 1M | $0.15 / $0.60 | Fast image generation/editing |
| Imagen 4 | Image | -- | $0 / $0.04 | Dedicated image generation |
| Veo 3.1 | Video | -- | -- | Video generation with audio |
| Veo 3.1 Fast | Video | -- | -- | Fast video generation |
| Veo 2.0 | Video | -- | -- | Video generation (legacy) |
| Gemini Flash Audio | Audio | 1M | $0.15 / $0.60 | Native audio understanding/generation |
| Gemini Flash TTS | Audio | 8K | $0.15 / $0.60 | Text-to-speech (24 voices) |
| Gemini Pro TTS | Audio | 8K | $1.25 / $5.00 | High-quality TTS |
| Lyria | Music | -- | -- | AI music generation |
| Gemini Embedding | Embedding | 8K | Free | RAG/embeddings |
| Gemini Computer Use | Agent | 1M | $1.25 / $5.00 | Autonomous computer control |
| Deep Research | Agent | 1M | $2.00 / $12.00 | Multi-step web research |

### Claude (3 models)

| Model | Context | Cost (in/out $/MTok) | Use Case |
|-------|---------|----------------------|----------|
| Claude Opus 4.6 | 200K | $5.00 / $25.00 | Most intelligent |
| Claude Sonnet 4.6 | 200K | $3.00 / $15.00 | Fast + capable (default) |
| Claude Haiku 4.5 | 200K | $1.00 / $5.00 | Budget routing |

---

## API Overview

The backend exposes **100+ REST endpoints** and a **WebSocket** for voice streaming. Key groups:

| Prefix | Count | Purpose |
|--------|-------|---------|
| `/api/chat` | 1 | SSE streaming chat (dual-model) |
| `/api/coding` | 1 | Coding with tool use |
| `/api/studio` | 18 | App Studio: stream, project CRUD, versions, export, mock server |
| `/api/kg` | 33 | KG Studio: CRUD, hybrid search, analytics, RAG chat, merge |
| `/api/experts` | 15 | Expert Builder: CRUD, chat, KG-OS query engine |
| `/api/games` | 10+ | Games: interview, generate, refine, chat, project CRUD |
| `/api/vox` | 12+ | VOX: sessions, functions, macros, tours, thermal |
| `/api/tools` | 4 | Tools playground: list, get, run, stream |
| `/api/agents` | 4 | NLKE agent CRUD + execution |
| `/api/playbooks` | 3 | Playbook search + retrieval |
| `/api/workflows` | 3 | Workflow templates + execution |
| `/api/media` | 4 | Image, video, TTS, music generation |
| `/api/agent` | 2 | Claude Agent SDK (run, sessions) |
| `/ws/vox` | 1 | Bidirectional voice WebSocket |

Interactive API docs are available at `/docs` (FastAPI Swagger UI) when the backend is running.

---

## Project Structure

```
multi-ai-agentic-workspace/
├── backend/
│   ├── main.py                    # FastAPI entry, CORS, 17 router mounts
│   ├── config.py                  # API keys, 23-model catalog, paths
│   ├── routers/                   # 17 API routers
│   │   ├── chat.py                #   Dual-model SSE streaming
│   │   ├── coding.py              #   IDE tool use
│   │   ├── studio.py              #   AI Studio (18 endpoints)
│   │   ├── kg.py                  #   KG Studio (33 endpoints)
│   │   ├── experts.py             #   Expert Builder + KG-OS (15 endpoints)
│   │   ├── games.py               #   Games studio
│   │   ├── vox.py                 #   VOX voice agent (WebSocket + REST)
│   │   ├── tools.py               #   Tools playground
│   │   ├── agents.py              #   NLKE agents
│   │   ├── playbooks.py           #   Playbook search
│   │   ├── workflows.py           #   Workflow engine
│   │   ├── media.py               #   Image/video/TTS/music generation
│   │   ├── agent.py               #   Claude Agent SDK
│   │   └── ...                    #   builder, memory, integrations, interchange
│   ├── services/                  # 28 business logic services (~12,400 lines)
│   ├── data/                      # Static data (tour definitions, etc.)
│   ├── mcp_server.py              # Standalone MCP server (JSON-RPC stdio)
│   └── tests/                     # Integration tests
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx                # React Router shell
│   │   ├── pages/                 # 14 route pages
│   │   ├── components/            # UI components (Studio, Experts, VOX, KG, Games)
│   │   ├── context/               # AppContext, StudioContext, VoxContext
│   │   ├── themes/                # 5 CSS variable theme definitions
│   │   ├── hooks/                 # useChat, useTheme, useToast, useVox
│   │   ├── services/              # API client + localStorage
│   │   └── types/                 # TypeScript interfaces
│   └── package.json
│
├── agents/                        # 33 NLKE agents (symlink)
├── playbooks/                     # 53 playbooks (symlink)
└── docs/                          # Guides, context packets, assets
```

---

## Theme System

Five built-in themes applied via CSS custom properties on `:root`. Selection persists in `localStorage`. Switch via the NavBar palette icon or Settings page.

| Theme | Style | Special |
|-------|-------|---------|
| **Default** | Dark slate, sky-blue accents | -- |
| **Deluxe-CRT** | Amber phosphor, monospace | Scanlines, vignette, text glow |
| **Scratch** | B&W, hand-drawn doodle | Dashed borders, Patrick Hand font |
| **Solarized Zen** | Warm earth tones, teal/amber | Clean and minimal |
| **Sunset Warm** | Coral, amber, rose gold | Gradient accents |

All components use `style={{ background: 'var(--t-surface)' }}` for theming while keeping layout utilities (`flex`, `p-4`, `rounded`) in `className`.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | -- | Google AI API key (required) |
| `ANTHROPIC_API_KEY` | -- | Anthropic API key (optional, enables Claude models) |
| `WORKSPACE_MODE` | `standalone` | `"standalone"` or `"claude-code"` |
| `KGS_DIR` | `docs/KGS` | Path to KG SQLite databases |

Keys can also be set at runtime via `POST /api/config/keys` or the Settings page.

---

## Symlink Setup

The agents and playbooks directories are expected as symlinks:

```bash
cd multi-ai-agentic-workspace
ln -sf /path/to/NLKE/agents agents
ln -sf /path/to/playbooks/playbooks-v2 playbooks
```

---

## Testing

```bash
cd backend
python -m pytest tests/ -v
```

---

## Environment Notes

This project was developed on **Termux/Android (proot-distro)** and works on standard Linux, macOS, and WSL.

- Termux requires setting `ESBUILD_BINARY_PATH` for frontend builds
- `sqlite-vec` has no aarch64 wheel; vector search degrades gracefully to FTS5
- VOX thermal monitoring uses the Termux battery API (optional)

---

## License

MIT

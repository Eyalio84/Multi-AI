# Multi-AI Agentic Workspace v1.0.1

A professional agentic workflow orchestrator combining **Gemini** and **Claude** intelligence into a unified web interface. Build real software with 33 NLKE agents, 53 playbooks, visual workflows, a dual-model coding IDE, and a full Graph-RAG Knowledge Graph workspace.

## Features

- **Dual-Model Chat** — Stream responses from Gemini or Claude, switch mid-conversation
- **Coding IDE** — File explorer, code editor, AI-powered file operations via tool use
- **33 NLKE Agents** — Run specialized agents (cost-advisor, code-reviewer, workflow-orchestrator, etc.)
- **53 Playbooks** — Searchable library of implementation recipes with category filtering
- **Visual Workflows** — 4 templates, AI-planned custom workflows, SSE execution with progress
- **KG Studio** — Full Graph-RAG workspace: 57 SQLite KGs, 6 auto-detected schema profiles, d3-force + React Flow visualization, **live hybrid semantic search** (0.40\*embedding + 0.45\*BM25 + 0.15\*graph via numpy cosine similarity), CRUD, AI ingestion (Gemini + LightRAG), NetworkX analytics (PageRank, communities, centrality), RAG chat with source citations, KG compare/diff/merge, embedding dashboard with PCA projections (10 tabs)
- **Web App Builder** — 5-step wizard: idea → plan → theme → generate → export/IDE
- **Workspace Transfer** — JSON import/export between standalone and Claude Code modes
- **5 Themes** — Default, Deluxe-CRT, Scratch (B&W doodle), Solarized Zen, Sunset Warm — switchable via NavBar or Settings
- **Mobile-First** — Responsive design, collapsible sidebars, touch-friendly

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    React 19 Frontend                      │
│  Chat │ Coding │ Agents │ Playbooks │ Workflows │ ...    │
├──────────────────────────────────────────────────────────┤
│                    Vite Dev Server (:5173)                │
│                    Proxy /api → :8000                     │
├──────────────────────────────────────────────────────────┤
│                    FastAPI Backend (:8000)                │
│  9 Routers │ 10 Services │ Model Router │ Agent Bridge   │
├──────────────────────────────────────────────────────────┤
│              External APIs                                │
│  Gemini API (google-genai) │ Claude API (anthropic)      │
│  33 NLKE Agents (Python)   │ 53 Playbooks (.pb files)   │
└──────────────────────────────────────────────────────────┘
```

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend
```bash
cd frontend
npm install    # Run on laptop, copy node_modules to phone
npm run dev    # Vite on :5173
```

### Verify
- Backend: http://localhost:8000/docs (Swagger UI)
- Frontend: http://localhost:5173
- Health: http://localhost:8000/api/health

## Dual-Mode Operation

### Standalone Mode (default)
Both Gemini and Claude APIs active. Full dual-model UI.

### Claude Code Mode
Only Gemini API active. Claude requests generate structured JSON context for Claude Code sessions. Toggle in Settings or via `POST /api/mode`.

## Model Catalog

| Provider | Model | Best For | Cost (in/out per MTok) |
|----------|-------|----------|------------------------|
| Gemini | 2.5 Flash | Fast coding/streaming | $0.15/$0.60 |
| Gemini | 2.5 Pro | Deep reasoning | $1.25/$5 |
| Gemini | 3 Pro | Flagship reasoning | ~$2/$12 |
| Claude | Haiku 4.5 | Budget routing | $1/$5 |
| Claude | Sonnet 4.6 | Fast + capable | $3/$15 |
| Claude | Opus 4.6 | Most intelligent | $5/$25 |

## Project Structure

```
multi-ai-agentic-workspace/
├── backend/
│   ├── main.py                 # FastAPI entry + CORS
│   ├── config.py               # Keys, models, paths
│   ├── requirements.txt        # Python dependencies
│   ├── routers/
│   │   ├── chat.py             # Dual-model SSE streaming
│   │   ├── coding.py           # IDE tool use (7 tools)
│   │   ├── agents.py           # NLKE agent execution
│   │   ├── playbooks.py        # Playbook search/retrieval
│   │   ├── workflows.py        # Workflow engine
│   │   ├── builder.py          # Web app generator
│   │   ├── media.py            # Image/video
│   │   ├── interchange.py      # Export/import
│   │   └── kg.py               # KG Studio (33 endpoints)
│   ├── services/
│   │   ├── gemini_service.py   # google-genai wrapper (lazy init)
│   │   ├── claude_service.py   # anthropic wrapper
│   │   ├── model_router.py     # Smart model selection
│   │   ├── agent_bridge.py     # NLKE bridge
│   │   ├── playbook_index.py   # .pb file parser
│   │   ├── kg_service.py       # KG core: 6 schema profiles, CRUD
│   │   ├── embedding_service.py # Hybrid search (numpy cosine + BM25 + graph boost)
│   │   ├── analytics_service.py # NetworkX graph algorithms
│   │   ├── ingestion_service.py # AI entity extraction
│   │   └── rag_chat_service.py  # RAG chat + source citations
│   └── tests/                  # Integration tests
├── frontend/
│   ├── src/
│   │   ├── App.tsx             # React Router shell
│   │   ├── context/            # Global state
│   │   ├── pages/              # 8 route pages
│   │   ├── components/         # UI components
│   │   ├── themes/             # 5 theme definitions (CSS vars)
│   │   ├── hooks/              # useChat, useTheme
│   │   ├── services/           # API + storage
│   │   └── types/              # TypeScript interfaces
│   ├── package.json
│   └── vite.config.ts
├── docs/
│   ├── API-Endpoints.md        # Full API reference
│   ├── KG-Libraries-Guide.md   # KG library capabilities (NetworkX, Model2Vec, LightRAG, d3-force)
│   ├── RTX3060-Build-Guide.md  # Desktop build guide (dual-boot, CUDA, local LLMs)
│   ├── system-atlas.html       # Interactive architecture
│   └── user-guide.html         # Usage guide
├── agents -> NLKE/agents       # 33 agents (symlink)
├── playbooks -> playbooks-v2   # 53 playbooks (symlink)
├── CLAUDE.md                   # Claude Code instructions
└── README.md                   # This file
```

## Testing

```bash
cd backend
python -m pytest tests/ -v              # All tests
python tests/run_all.py                  # With summary
python -m pytest tests/test_api_endpoints.py -v  # API only
```

## Symlink Setup

```bash
cd multi-ai-agentic-workspace
ln -sf /path/to/NLKE/agents agents
ln -sf /path/to/playbooks/playbooks-v2 playbooks
```

## Theme System

5 built-in themes, switchable via NavBar palette icon or Settings page:

| Theme | Style | Special Effects |
|-------|-------|-----------------|
| Default | Dark slate, sky-blue accents | None |
| Deluxe-CRT | Amber phosphor, monospace | Subtle scanlines, vignette, text glow |
| Scratch | B&W, hand-drawn doodle | Dashed borders, box-shadows, Patrick Hand font |
| Solarized Zen | Warm earth tones, teal/amber | None, clean & minimal |
| Sunset Warm | Coral, amber, rose gold | Subtle gradient accents |

Themes use CSS custom properties (`--t-bg`, `--t-surface`, `--t-primary`, etc.) applied to `:root`. Selection persists in localStorage.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| WORKSPACE_MODE | standalone | "standalone" or "claude-code" |
| GEMINI_API_KEY | (hardcoded) | Google AI API key |
| ANTHROPIC_API_KEY | (hardcoded) | Anthropic API key |

## License

Private project. Not for public distribution.

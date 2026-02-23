# CLAUDE.md — Multi-AI Agentic Workspace

## What This Is

A professional agentic workflow orchestrator combining Gemini + Claude intelligence. Built as a FastAPI backend + React 19 frontend with dual-model streaming, 33 NLKE agents, 53 playbooks, visual workflow execution, and a full Graph-RAG Knowledge Graph workspace (57 SQLite KGs, 6 schema profiles, hybrid search, analytics, RAG chat).

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
│   ├── routers/                # 9 API routers
│   │   ├── chat.py             # POST /api/chat/stream (SSE, dual-model)
│   │   ├── coding.py           # POST /api/coding/stream (tool use)
│   │   ├── agents.py           # NLKE agent CRUD + execution
│   │   ├── playbooks.py        # Playbook search + retrieval
│   │   ├── workflows.py        # Workflow templates + execution
│   │   ├── builder.py          # Web app plan + generate
│   │   ├── media.py            # Image edit + video gen
│   │   ├── interchange.py      # JSON import/export, mode toggle
│   │   └── kg.py               # KG Studio (33 endpoints, CRUD, search, analytics, RAG)
│   ├── services/               # Business logic
│   │   ├── gemini_service.py   # google-genai SDK wrapper (lazy init)
│   │   ├── claude_service.py   # anthropic SDK wrapper
│   │   ├── model_router.py     # Intelligent model selection
│   │   ├── agent_bridge.py     # NLKE agent system bridge
│   │   ├── playbook_index.py   # Playbook file parser + search
│   │   ├── kg_service.py       # KG core: 6 schema profiles, auto-detect, CRUD
│   │   ├── embedding_service.py # Multi-strategy search (Gemini, BM25, hybrid)
│   │   ├── analytics_service.py # NetworkX graph algorithms
│   │   ├── ingestion_service.py # AI entity extraction from text
│   │   └── rag_chat_service.py  # RAG chat with streaming + source citations
│   └── tests/                  # API integration tests
│
├── frontend/                   # React 19 + TypeScript + Vite
│   ├── src/
│   │   ├── App.tsx             # Router + layout shell
│   │   ├── context/AppContext   # Global state (projects, models, personas)
│   │   ├── pages/              # 8 route pages
│   │   ├── components/         # Reusable UI components
│   │   ├── themes/             # 5 theme definitions (CSS variable maps)
│   │   ├── hooks/              # useChat (streaming), useTheme (CSS vars)
│   │   ├── services/           # API + localStorage services
│   │   └── types/              # TypeScript interfaces
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
| POST | /api/builder/plan | AI project planning |
| POST | /api/builder/generate | Full code generation |
| POST | /api/export | Export workspace JSON |
| POST | /api/import | Import workspace JSON |
| GET | /api/kg/databases | List 57 KG databases with stats |
| GET | /api/kg/databases/{id}/nodes | Paginated nodes (search, filter) |
| POST | /api/kg/databases/{id}/search | Hybrid semantic search (BM25+embedding+graph) |
| POST | /api/kg/databases/{id}/chat | RAG chat with streaming + source citations |
| GET | /api/kg/databases/{id}/analytics/* | Graph metrics, centrality, communities, paths |
| POST | /api/kg/compare | Structural KG comparison |
| POST | /api/kg/merge | Merge KGs (union/intersection/complement) |
| POST | /api/kg/databases/{id}/ingest | AI entity extraction from text |
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
| /kg-studio | KGStudioPage | Graph-RAG KG workspace (10 tabs, 57 DBs, React Flow) |
| /builder | BuilderPage | 5-step web app generator |
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

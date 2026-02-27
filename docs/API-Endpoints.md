# API Endpoints Reference — v2.5.0

Base URL: `http://localhost:8000/api`

---

## Table of Contents

- [System](#system)
- [Chat](#chat)
- [Coding](#coding)
- [Claude Agent SDK](#claude-agent-sdk)
- [Agents (NLKE)](#agents-nlke)
- [Playbooks](#playbooks)
- [Workflows](#workflows)
- [Studio](#studio)
- [Builder (Legacy)](#builder-legacy)
- [Media Generation](#media-generation)
- [Games Studio](#games-studio)
- [Memory & Conversations](#memory--conversations)
- [Knowledge Graph Studio](#knowledge-graph-studio)
- [Tools Playground](#tools-playground)
- [Expert Builder (KG-OS)](#expert-builder-kg-os)
- [VOX Voice Agent](#vox-voice-agent)
- [Integrations](#integrations)
- [Mode & Interchange](#mode--interchange)
- [MCP Server](#mcp-server)
- [Model Catalog](#model-catalog)
- [Notes](#notes)

---

## System

### GET /api/health
Health check with mode and API status.

**Response:**
```json
{
  "status": "ok",
  "mode": "standalone",
  "gemini_configured": true,
  "claude_configured": true
}
```

### GET /api/models
List available models per provider. In `claude-code` mode, only Gemini models are returned.

**Response:**
```json
{
  "gemini": {
    "gemini-2.5-flash": { "name": "Gemini 2.5 Flash", "category": "text", "context": 1000000, "cost_in": 0.15, "cost_out": 0.60, "use_case": "Fast coding/streaming" },
    "gemini-3-pro-preview": { "name": "Gemini 3 Pro", "category": "text", ... },
    ...
  },
  "claude": {
    "claude-opus-4-6": { "name": "Claude Opus 4.6", "category": "text", "context": 200000, "cost_in": 5.0, "cost_out": 25.0, "use_case": "Most intelligent" },
    ...
  }
}
```

---

## Chat

### POST /api/chat/stream
SSE streaming chat with dual-model support. Routes through the unified agentic loop.

**Request:**
```json
{
  "messages": [{ "author": "user", "parts": [{ "text": "Hello" }] }],
  "provider": "gemini",
  "model": "gemini-2.5-flash",
  "persona": { "id": "default", "name": "Default", "baseInstructions": "", "composedStyles": [] },
  "customStyles": [],
  "useWebSearch": false,
  "thinkingBudget": 0,
  "conversationId": "optional-uuid"
}
```

**SSE Response Events:**
```
data: {"type": "token", "content": "Hello!"}
data: {"type": "thinking_start"}
data: {"type": "thinking", "content": "Let me think..."}
data: {"type": "grounding", "sources": [{"uri": "...", "title": "..."}]}
data: {"type": "claude_code_export", "content": {...}}
data: {"type": "error", "content": "Error message"}
data: {"type": "done"}
```

**Chat Slash Commands** (handled client-side, dispatched to respective endpoints):

| Command | Description | Target Endpoint |
|---------|-------------|-----------------|
| `/image <prompt>` | Generate an image | POST /api/media/image/generate |
| `/tts <text>` | Text-to-speech | POST /api/media/tts/generate |
| `/video <prompt>` | Generate a video | POST /api/media/video/generate |
| `/agent <prompt>` | Run Claude agent | POST /api/agent/run |
| `/help` | Show available commands | Client-side |

---

## Coding

### POST /api/coding/stream
SSE streaming with tool use for coding assistant. Routes through the unified agentic loop.

**Request:**
```json
{
  "history": [...],
  "projects": [{ "id": "...", "name": "my-app", "dependencySummary": "react, axios" }],
  "persona": {...},
  "customStyles": [],
  "useWebSearch": false,
  "provider": "gemini",
  "model": "gemini-2.5-flash",
  "thinkingBudget": 0,
  "conversationId": "optional-uuid"
}
```

**Additional SSE Events:**
```
data: {"type": "tool_call", "name": "createFile", "args": {"path": "src/App.tsx", "content": "..."}}
data: {"type": "tool_call_start", "id": "tc_123", "name": "readFile"}
data: {"type": "tool_call_delta", "content": "{\"path\":\""}
```

**Available Tools:**

| Tool | Description | Parameters |
|------|-------------|------------|
| listFiles | List project files | - |
| createFile | Create a file | path, content |
| readFile | Read file content | path |
| updateFile | Update file | path, newContent |
| deleteFile | Delete a file | path |
| searchNpm | Search npm registry | packageName |
| runPython | Execute Python code | code |

---

## Claude Agent SDK

Autonomous agent execution powered by the Claude Agent SDK (`claude-agent-sdk`).

### POST /api/agent/run
Run an autonomous Claude agent task. Returns SSE stream of agent events.

**Request:**
```json
{
  "prompt": "List all Python files and count their lines",
  "allowed_tools": ["Bash", "Read"],
  "model": "claude-sonnet-4-6",
  "cwd": "/path/to/project",
  "max_turns": 10,
  "session_id": "optional-resume-id"
}
```

**SSE Response Events:**
```
data: {"type": "thinking", "content": "..."}
data: {"type": "tool_use", "tool": "Bash", "input": {"command": "find . -name '*.py'"}}
data: {"type": "tool_result", "output": "..."}
data: {"type": "text", "content": "I found 15 Python files..."}
data: {"type": "done", "session_id": "abc123"}
data: {"type": "error", "message": "..."}
```

### GET /api/agent/sessions
List recent agent sessions.

**Response:**
```json
[
  { "session_id": "abc123", "prompt": "...", "status": "completed", "turns": 5, "created_at": "..." }
]
```

### GET /api/agent/sessions/{session_id}
Get status of a specific agent session.

**Response:**
```json
{
  "session_id": "abc123",
  "prompt": "...",
  "status": "completed",
  "turns": 5,
  "events": [...]
}
```

---

## Agents (NLKE)

### GET /api/agents
List all available NLKE agents (33 built-in + custom).

**Response:**
```json
{
  "agents": [
    { "name": "cost-advisor", "category": "FOUNDATION", "description": "Optimize API costs...", "type": "builtin" },
    { "id": "uuid", "name": "my-agent", "category": "CUSTOM", "description": "...", "type": "custom" },
    ...
  ]
}
```

### POST /api/agents
Create a custom agent definition.

**Request:**
```json
{
  "name": "my-agent",
  "description": "Custom analysis agent",
  "category": "CUSTOM",
  "system_prompt": "You are a specialized agent for...",
  "tools": ["Bash", "Read"]
}
```

### GET /api/agents/{name}/example
Get example workload for an agent.

### POST /api/agents/{name}/run
Execute an NLKE agent with a workload.

**Request:**
```json
{
  "workload": {
    "goal": "Reduce API costs by 50%",
    "context": { "current_model": "claude-opus-4-6", "monthly_cost": 500 }
  }
}
```

### GET /api/agents/{name}/export/claude-code
Export an agent definition as Claude Code skill JSON.

**Response:**
```json
{
  "name": "cost-advisor",
  "description": "...",
  "system_prompt": "...",
  "tools": [],
  "model": "claude-sonnet-4-6",
  "max_turns": 10
}
```

### POST /api/pipelines/run
Execute a multi-agent pipeline.

**Request:**
```json
{
  "steps": [
    { "agent": "cost-advisor", "workload": {...} },
    { "agent": "prompt-engineer", "workload": {...} }
  ]
}
```

---

## Playbooks

### GET /api/playbooks
List all playbooks with metadata.

### GET /api/playbooks/search?q={query}&category={category}
Search playbooks by keyword and optional category.

### GET /api/playbooks/categories
List categories with counts.

### GET /api/playbooks/{filename}
Get full playbook content.

---

## Workflows

### GET /api/workflows/templates
List built-in workflow templates.

**Templates:**
- `dev_lifecycle` -- Plan -> Code -> Test -> Review -> Docs
- `research_analysis` -- Research -> Analyze -> Validate -> Synthesize
- `kg_pipeline` -- Extract -> Relate -> Validate -> Export
- `decision_making` -- Options -> Pros/Cons -> Risk -> Recommend

### GET /api/workflows
List all saved workflows alongside built-in templates.

**Response:**
```json
{
  "saved": [{ "id": "uuid", "name": "My Workflow", "description": "...", "step_count": 3 }],
  "templates": [{ "id": "dev_lifecycle", "name": "Development Lifecycle", "description": "...", "step_count": 5, "type": "template" }]
}
```

### POST /api/workflows
Save a new workflow definition.

**Request:**
```json
{
  "name": "My Workflow",
  "description": "Custom workflow",
  "goal": "Build an API",
  "steps": [{ "id": "plan", "name": "Plan", "prompt_template": "...", "depends_on": [] }]
}
```

### GET /api/workflows/{workflow_id}
Get a saved workflow by ID.

### PUT /api/workflows/{workflow_id}
Update a saved workflow.

### DELETE /api/workflows/{workflow_id}
Delete a saved workflow.

### POST /api/workflows/plan
Plan a workflow (from template or AI-generated).

**Request:**
```json
{
  "goal": "Build a REST API for user management",
  "template": "dev_lifecycle"
}
```

### POST /api/workflows/execute
Execute a workflow, streaming progress per step.

**SSE Events:**
```
data: {"type": "step_start", "step_id": "plan", "name": "Architecture Planning"}
data: {"type": "step_token", "step_id": "plan", "content": "..."}
data: {"type": "step_complete", "step_id": "plan"}
data: {"type": "step_error", "step_id": "code", "error": "..."}
data: {"type": "workflow_complete", "step_count": 5}
```

### GET /api/workflows/{workflow_id}/export/claude-code
Export a saved workflow as Claude Code compatible JSON.

---

## Studio

AI-powered React app generation with live Sandpack preview, 3 editing modes, SQLite persistence, and version history.

### POST /api/studio/stream
SSE streaming for AI-powered React app generation with live file extraction.

**Request:**
```json
{
  "project_id": "uuid-or-null",
  "prompt": "Build a todo app with categories",
  "files": {},
  "chat_history": [],
  "provider": "gemini",
  "model": "gemini-2.5-flash",
  "mode": "generate"
}
```

**SSE Response Events:**
```
data: {"type": "token", "content": "I'll create a todo app..."}
data: {"type": "studio_plan", "content": "Plan text before files"}
data: {"type": "studio_file", "path": "/App.js", "content": "import React..."}
data: {"type": "studio_deps", "dependencies": {"axios": "^1.6.0"}}
data: {"type": "error", "content": "Error message"}
data: {"type": "done"}
```

**Modes:** `generate` (new app from scratch), `refine` (modify existing files)

### POST /api/studio/projects
Create a new Studio project.

**Request:** `{ "name": "My App", "description": "A todo app" }`

**Response:**
```json
{
  "id": "uuid",
  "name": "My App",
  "description": "A todo app",
  "settings": {},
  "files": {},
  "chat_history": [],
  "current_version": 0,
  "created_at": "2026-02-27T...",
  "updated_at": "2026-02-27T..."
}
```

### GET /api/studio/projects
List all projects (summaries with file counts).

### GET /api/studio/projects/{id}
Load full project with files, chat history, settings, and versions.

### PUT /api/studio/projects/{id}
Update project fields (name, description, files, chat_history, settings).

### DELETE /api/studio/projects/{id}
Delete project and all versions (cascade).

### POST /api/studio/projects/{id}/save
Save a version snapshot of current project files.

**Request:** `{ "message": "Added dark mode" }`

**Response:**
```json
{
  "id": "version-uuid",
  "project_id": "project-uuid",
  "version_number": 3,
  "message": "Added dark mode",
  "timestamp": "2026-02-27T..."
}
```

### GET /api/studio/projects/{id}/versions
List all versions for a project (newest first).

### GET /api/studio/projects/{id}/versions/{ver}
Get a specific version snapshot with files.

### POST /api/studio/projects/{id}/versions/{ver}/restore
Restore project to a previous version (auto-saves current state first).

### GET /api/studio/projects/{id}/export?scope=all
Download project as ZIP archive.

**Query params:** `scope` = `all` | `frontend` | `backend`

### POST /api/studio/projects/{id}/mock/start
Start Node.js mock server for the project's API spec.

### POST /api/studio/projects/{id}/mock/stop
Stop mock server.

### GET /api/studio/projects/{id}/mock/status
Get mock server status (running, port, pid).

### POST /api/studio/projects/{id}/mock/update
Restart mock server with updated routes.

### POST /api/studio/projects/{id}/extract-backend-spec
Use AI to analyze project files and extract structured backend specification (Pydantic-validated `BackendSpec`).

**Request:**
```json
{
  "provider": "gemini",
  "model": "gemini-2.5-flash"
}
```

**Response:**
```json
{
  "version": "1.0",
  "framework": "fastapi",
  "language": "python",
  "database": { "type": "sqlite", "tables": [...] },
  "endpoints": [{ "method": "GET", "path": "/api/items", "summary": "..." }],
  "models": { "Item": { "name": "Item", "fields": {...} } },
  "dependencies": ["fastapi", "uvicorn"],
  "environment_variables": ["DATABASE_URL"]
}
```

### POST /api/studio/projects/{id}/build-backend
Generate backend implementation from specification. Returns SSE stream of files using the `### FILE:` marker format.

**Request:**
```json
{
  "spec": { ... },
  "prompt": "Add authentication middleware",
  "provider": "gemini",
  "model": "gemini-2.5-flash"
}
```

### GET /api/studio/projects/{id}/api-spec
Extract OpenAPI spec from project's Python/FastAPI files.

### GET /api/studio/projects/{id}/types
Generate TypeScript interfaces from project's API spec.

### POST /api/studio/export-with-spec
Export project as JSON with AI-extracted structured backend specification included.

**Request:** `{ "project_id": "uuid" }`

**Response:**
```json
{
  "version": "1.0",
  "project": { "id": "...", "name": "...", "description": "..." },
  "files": {...},
  "chat_history": [...],
  "backend_spec": { ... }
}
```

---

## Builder (Legacy)

### POST /api/builder/plan
Generate a project plan from an idea.

**Request:**
```json
{
  "idea": "A kanban task board with drag-and-drop",
  "provider": "gemini",
  "model": "gemini-2.5-flash"
}
```

**Response:**
```json
{
  "projectName": "kanban-board",
  "description": "...",
  "features": ["..."],
  "techStack": { "frontend": "React + TypeScript + Tailwind" },
  "fileStructure": ["src/App.tsx", ...]
}
```

### POST /api/builder/generate
Generate complete project code.

**Request:**
```json
{
  "plan": {...},
  "theme": { "palette": "Dark & Bold", "typography": "Monospace & Technical" }
}
```

**Response:** `{ "src/App.tsx": "...", "package.json": "...", ... }`

---

## Media Generation

### POST /api/image/edit
Edit an image using Gemini's multimodal capabilities (legacy).

**Form Fields:** `prompt` (string), `file` (image file)

### POST /api/video/generate
Start video generation (legacy endpoint, kept for backward compat).

**Form Fields:** `prompt` (string), `file` (optional image)

**Response:** `{ "operationName": "..." }`

### GET /api/video/status?operationName={name}
Poll video generation status.

**Response:** `{ "done": true, "videoUrl": "..." }` or `{ "done": false }`

### POST /api/media/image/generate
Generate images from text using Nano Banana Pro / Imagen 4.

**Request:**
```json
{
  "prompt": "A futuristic city at sunset",
  "model": "gemini-3-pro-image-preview",
  "aspect_ratio": "1:1",
  "num_images": 1
}
```

**Models:** `gemini-3-pro-image-preview` (Nano Banana Pro), `imagen-4.0-generate-preview-05-20` (Imagen 4)

### POST /api/media/video/generate
Start video generation with Veo 3.1.

**Request:**
```json
{
  "prompt": "A drone flying over mountains",
  "model": "veo-3.1-generate-preview",
  "aspect_ratio": "16:9",
  "duration_seconds": 8
}
```

**Response:** `{ "operationName": "..." }`

**Models:** `veo-3.1-generate-preview` (Veo 3.1), `veo-3.1-fast-generate-preview` (Veo 3.1 Fast), `veo-2.0-generate-001` (Veo 2.0 legacy)

### POST /api/media/tts/generate
Text-to-speech using Gemini TTS models.

**Request:**
```json
{
  "text": "Hello world",
  "model": "gemini-2.5-flash-preview-tts",
  "voice": "Kore",
  "speed": 1.0
}
```

**Models:** `gemini-2.5-flash-preview-tts` (Flash TTS, 24 voices), `gemini-2.5-pro-preview-tts` (Pro TTS)

### POST /api/media/music/generate
Generate music using Lyria.

**Request:**
```json
{
  "prompt": "Upbeat electronic dance track",
  "model": "lyria-realtime-exp",
  "duration_seconds": 30
}
```

---

## Games Studio

Phaser 3 RPG game projects with AI-driven interview, GDD synthesis, code generation, and in-game LLM chat.

### GET /api/games/interview/questions
Get the game design interview questions.

### GET /api/games
List all game projects.

### POST /api/games
Create a new game project.

**Request:** `{ "name": "My RPG", "description": "A fantasy RPG" }`

### GET /api/games/{game_id}
Get a game project with all data (GDD, files, interview data).

### PUT /api/games/{game_id}
Update a game project.

**Request:**
```json
{
  "name": "Updated Name",
  "description": "...",
  "status": "playable",
  "files": { "index.html": "...", "game.js": "..." },
  "settings": {}
}
```

### DELETE /api/games/{game_id}
Delete a game project.

### POST /api/games/{game_id}/interview
Submit an interview answer for a game project.

**Request:**
```json
{
  "question_id": "q1",
  "answer": "Fantasy RPG"
}
```

### POST /api/games/{game_id}/synthesize
Synthesize a Game Design Document (GDD) from completed interview answers.

### POST /api/games/{game_id}/generate
Generate game code from GDD. Returns SSE stream.

**Request:** `{ "kg_context": "" }`

**SSE Events:**
```
data: {"type": "token", "content": "..."}
data: {"type": "studio_file", "path": "game.js", "content": "..."}
data: {"type": "files_complete", "files": {...}}
data: {"type": "done"}
```

### POST /api/games/{game_id}/refine
Refine existing game code with AI. Returns SSE stream.

**Request:**
```json
{
  "prompt": "Add a health bar to the player",
  "files": {}
}
```

### POST /api/games/{game_id}/save
Save a version snapshot of the game project.

### GET /api/games/{game_id}/versions
List all versions for a game project.

### POST /api/games/{game_id}/versions/{version_number}/restore
Restore a game project to a previous version.

### GET /api/games/{game_id}/export
Export game as downloadable ZIP archive.

### POST /api/games/{game_id}/chat
Expert chat for game development (SSE streaming, uses GameForge expert backed by a game dev KG).

**Request:**
```json
{
  "query": "How should I implement enemy AI?",
  "conversation_id": "optional-uuid",
  "history": []
}
```

### POST /api/games/{game_id}/extract-patterns
Extract reusable game development patterns from project code.

### GET /api/games/llm/status
Get in-game LLM status (for NPC dialogue generation).

### POST /api/games/llm/load
Load an LLM model for in-game NPC dialogue.

**Request:** `{ "model_type": "small" }`

### POST /api/games/llm/unload
Unload the in-game LLM model.

### POST /api/games/llm/chat
Generate NPC dialogue using the loaded LLM.

**Request:**
```json
{
  "npc_name": "Old Sage",
  "system_prompt": "You are a wise old sage in a fantasy village...",
  "message": "Tell me about the ancient prophecy",
  "history": []
}
```

---

## Memory & Conversations

Conversation persistence and semantic memory search.

### GET /api/memory/conversations?mode=&source=&limit=20
List conversations with optional mode/source filter.

### GET /api/memory/conversations/{conversation_id}
Get a conversation with metadata.

### GET /api/memory/conversations/{conversation_id}/messages?limit=50&offset=0
Get paginated messages for a conversation.

### DELETE /api/memory/conversations/{conversation_id}
Delete a conversation.

### POST /api/memory/search
Search across conversation memory.

**Request:**
```json
{
  "query": "cost optimization discussion",
  "limit": 5
}
```

**Response:**
```json
{
  "results": [...],
  "query": "cost optimization discussion"
}
```

### GET /api/memory/stats
Get memory statistics including injection stats.

---

## Knowledge Graph Studio

### GET /api/kg/databases
List all KG databases with metadata, stats, and schema profile.

**Response:**
```json
[
  {
    "id": "claude-code-tools-kg",
    "filename": "claude-code-tools-kg.db",
    "size_mb": 0.45,
    "modified": "2025-11-20T...",
    "is_kg": true,
    "profile": "claude",
    "node_count": 511,
    "edge_count": 631
  }
]
```

### GET /api/kg/databases/{db_id}/stats
Database statistics: node/edge counts, type breakdowns.

### GET /api/kg/databases/{db_id}/nodes?node_type=&search=&limit=100&offset=0
Paginated node listing with optional type filter and text search.

### GET /api/kg/databases/{db_id}/nodes/{node_id}
Single node with all properties and connections.

### GET /api/kg/databases/{db_id}/nodes/{node_id}/neighbors?depth=1&limit=50
Subgraph around a node for graph visualization (max limit 200).

### GET /api/kg/databases/{db_id}/edges?edge_type=&limit=100&offset=0
Paginated edge listing with optional type filter.

### GET /api/kg/databases/{db_id}/types
Node and edge type lists with counts.

### POST /api/kg/databases/{db_id}/search
Semantic search with multiple modes.

**Request:**
```json
{
  "query": "cost optimization",
  "mode": "hybrid",
  "limit": 20,
  "alpha": 0.40,
  "beta": 0.45,
  "gamma": 0.15
}
```

**Modes:** `fts` (BM25/FTS5), `embedding` (numpy cosine similarity), `hybrid` (combined: alpha*embedding + beta*BM25 + gamma*graph)

**Embedding search strategy (auto-selected):**
1. Model2Vec (256-dim, offline, ~1ms/query) -- used when stored embeddings are 256-dim
2. Gemini API (3072-dim, requires API key) -- used for Gemini-generated embeddings
3. Model2Vec with pad/truncate -- fallback for dimension mismatches

### POST /api/kg/search/multi
Cross-KG search across multiple databases simultaneously.

**Request:**
```json
{
  "query": "cost optimization",
  "db_ids": ["claude-code-tools-kg", "gemini-3-pro-kg"],
  "mode": "hybrid",
  "limit": 10
}
```

### POST /api/kg/databases
Create a new KG database.

**Request:** `{ "name": "my-knowledge-graph" }`

### POST /api/kg/databases/{db_id}/nodes
Create a node.

**Request:** `{ "name": "Node Name", "type": "concept", "properties": {} }`

### PUT /api/kg/databases/{db_id}/nodes/{node_id}
Update a node (name, type, properties).

### DELETE /api/kg/databases/{db_id}/nodes/{node_id}
Delete a node and its connected edges.

### POST /api/kg/databases/{db_id}/edges
Create an edge.

**Request:** `{ "source": "...", "target": "...", "type": "relates_to", "properties": {} }`

### PUT /api/kg/databases/{db_id}/edges/{edge_id}
Update an edge (type, properties).

### DELETE /api/kg/databases/{db_id}/edges/{edge_id}
Delete an edge.

### POST /api/kg/databases/{db_id}/bulk
Batch insert nodes and edges.

**Request:** `{ "nodes": [...], "edges": [...] }`

### POST /api/kg/databases/{db_id}/ingest
AI entity extraction from text using Gemini.

**Request:**
```json
{
  "text": "React is a JavaScript library maintained by Meta...",
  "method": "ai",
  "source": "optional-source-label"
}
```

**Methods:** `ai` (Gemini entity extraction), `lightrag` (LightRAG pipeline), `manual` (store as document node)

### GET /api/kg/databases/{db_id}/analytics/summary
Graph metrics: density, components, clustering, avg degree, isolates.

### GET /api/kg/databases/{db_id}/analytics/centrality?metric=degree&top_k=20
Top-k nodes by centrality metric.

**Metrics:** `degree`, `betweenness`, `pagerank`

### GET /api/kg/databases/{db_id}/analytics/communities
Community detection via greedy modularity.

### POST /api/kg/databases/{db_id}/analytics/path
Shortest path between two nodes.

**Request:** `{ "source_node": "...", "target_node": "..." }`

### GET /api/kg/databases/{db_id}/analytics/pagerank?top_k=20
Top-k nodes by PageRank (convenience alias for centrality with metric=pagerank).

### POST /api/kg/compare
Structural comparison between two KGs.

**Request:** `{ "db_id_a": "claude-kg", "db_id_b": "gemini-kg" }`

### POST /api/kg/diff
Detailed diff: added/removed/modified nodes and edges.

**Request:** `{ "db_id_a": "...", "db_id_b": "..." }`

### POST /api/kg/merge
Merge source KG into target.

**Request:** `{ "source_db": "...", "target_db": "...", "strategy": "union" }`

**Strategies:** `union`, `intersection`

### POST /api/kg/databases/{db_id}/batch/delete-by-type
Batch delete all nodes of a given type.

**Request:** `{ "node_type": "deprecated" }`

### POST /api/kg/databases/{db_id}/batch/retype
Batch rename a node type.

**Request:** `{ "old_type": "concept", "new_type": "entity" }`

### POST /api/kg/databases/{db_id}/chat
RAG chat with SSE streaming and source citations. Routes through the unified agentic loop.

**Request:**
```json
{
  "query": "How does cost optimization work?",
  "history": [],
  "mode": "hybrid",
  "limit": 10
}
```

**SSE Events:**
```
data: {"type": "token", "content": "Cost optimization..."}
data: {"type": "sources", "nodes": [{"id": "...", "name": "...", "score": 0.95}]}
data: {"type": "done"}
```

### GET /api/kg/databases/{db_id}/embedding-status
Check embedding availability and search strategies for a KG.

**Response:**
```json
{
  "has_embeddings": true,
  "count": 228,
  "dimensions": 384,
  "coverage_pct": 98.3,
  "strategies_available": ["fts", "numpy_cosine", "model2vec", "gemini"]
}
```

### GET /api/kg/databases/{db_id}/embeddings/projection?method=pca&max_points=500
2D PCA/t-SNE projection data for embedding visualization.

### POST /api/kg/databases/{db_id}/embeddings/generate
Generate embeddings for all nodes in a KG.

**Request:** `{ "strategy": "gemini" }`

**Strategies:** `gemini`, `model2vec`

### GET /api/kg/databases/{db_id}/embeddings/quality
Embedding quality metrics: coverage, similarity distribution.

---

## Tools Playground

### GET /api/tools
List all registered tools grouped by category.

**Response:**
```json
{
  "categories": ["Code Quality", "Frontend", "Backend", ...],
  "tools": {
    "Code Quality": [{ "id": "code_review_generator", "name": "Code Review Generator", "category": "Code Quality", "description": "...", "param_count": 3 }],
    ...
  },
  "total": 58
}
```

### GET /api/tools/{tool_id}
Get full tool definition with parameters.

### POST /api/tools/{tool_id}/run
Execute a tool and return JSON result.

**Request:**
```json
{
  "params": {
    "code": "def hello(): pass",
    "language": "python"
  }
}
```

**Response:** `{ "success": true, "result": {...}, "tool_id": "...", "execution_time": 0.05 }`

### POST /api/tools/{tool_id}/run/stream
Execute a tool with SSE streaming for progress updates.

**SSE Events:**
```
data: {"type": "progress", "message": "Starting tool execution..."}
data: {"type": "result", "data": {...}}
data: {"type": "error", "message": "..."}
data: {"type": "done"}
```

**Categories (11):** Code Quality, Cost Optimization, Agent Intelligence, Knowledge Graph, Generators, Reasoning, Dev Tools, Frontend, Backend, Full-Stack, Orchestration

---

## Expert Builder (KG-OS)

### GET /api/experts
List all experts.

### POST /api/experts
Create an expert backed by a KG.

**Request:**
```json
{
  "name": "Security Expert",
  "description": "Cybersecurity advisor",
  "kg_db_id": "security-kg",
  "kg_db_ids": [],
  "persona_name": "Expert",
  "persona_instructions": "You are a security expert...",
  "persona_style": "professional",
  "retrieval_methods": ["hybrid", "intent"],
  "retrieval_alpha": 0.35,
  "retrieval_beta": 0.40,
  "retrieval_gamma": 0.15,
  "retrieval_delta": 0.10,
  "retrieval_limit": 10,
  "dimension_filters": {},
  "playbook_skills": [],
  "custom_goal_mappings": {},
  "icon": "brain",
  "color": "#0ea5e9",
  "is_public": true
}
```

### GET /api/experts/{id}
Get expert configuration.

### PUT /api/experts/{id}
Update expert (any field from create, all optional).

### DELETE /api/experts/{id}
Delete expert and conversations.

### POST /api/experts/{id}/duplicate
Duplicate an expert.

### POST /api/experts/{id}/chat
SSE streaming expert chat with KG-OS retrieval and source citations.

**Request:**
```json
{
  "query": "How do I secure API endpoints?",
  "conversation_id": "optional-uuid",
  "history": []
}
```

**SSE Events:**
```
data: {"type": "token", "content": "To secure API endpoints..."}
data: {"type": "sources", "nodes": [{"id": "...", "name": "...", "score": 0.95}]}
data: {"type": "done"}
```

### GET /api/experts/{id}/conversations
List conversations for an expert.

### GET /api/experts/{id}/conversations/{cid}
Get conversation with messages.

### DELETE /api/experts/{id}/conversations/{cid}
Delete a conversation.

### POST /api/experts/kgos/query/{db_id}
Direct KG-OS query (testing/debug).

**Request:**
```json
{
  "query": "cost optimization",
  "alpha": 0.35,
  "beta": 0.40,
  "gamma": 0.15,
  "delta": 0.10,
  "limit": 10,
  "methods": ["hybrid", "intent"]
}
```

### POST /api/experts/kgos/impact/{db_id}/{node_id}
Impact analysis for a node.

**Request:** `{ "direction": "forward", "max_depth": 3 }`

### POST /api/experts/kgos/compose/{db_id}
Composition planning.

**Request:** `{ "goal": "Build a secure API", "max_steps": 5 }`

### POST /api/experts/kgos/similar/{db_id}/{node_id}?k=10
Find similar nodes.

### GET /api/experts/kgos/dimensions
List 56 standard semantic dimensions.

---

## VOX Voice Agent

Bidirectional voice agent powered by Gemini Live API + Claude tool_use with ~35 function handlers, awareness layer, guided tours, voice macros, thermal monitoring, and feature interview.

### GET /api/vox/status
Check VOX availability (Gemini/Claude configured, active sessions).

**Response:**
```json
{
  "gemini_available": true,
  "claude_available": true,
  "active_sessions": 0
}
```

### GET /api/vox/voices
List available Gemini Live API voices (Puck, Charon, Kore, Fenrir, Aoede, Leda, Orus, Zephyr, and more -- 16 total).

### GET /api/vox/functions
List all ~35 workspace function declarations available to VOX.

**Response:** `{ "functions": [...], "count": 35 }`

### POST /api/vox/function/{fn_name}
Execute a workspace function server-side.

**Request:** `{ "args": { "tool_id": "security_scanner", "params": { "code": "..." } } }`

**~35 Functions (server + browser):**

| Function | Category | Server/Browser |
|----------|----------|----------------|
| navigate_page | Navigation | Browser |
| get_current_page | Navigation | Browser |
| get_workspace_state | Navigation | Browser |
| switch_model | Navigation | Browser |
| switch_theme | Navigation | Browser |
| read_page_content | Navigation | Browser |
| run_tool | Core Tools | Server |
| list_tools | Core Tools | Server |
| query_kg | KG Access | Server |
| list_kgs | KG Access | Server |
| search_kg | KG Access | Server |
| get_kg_analytics | KG Access | Server |
| cross_kg_search | KG Access | Server (async) |
| ingest_to_kg | KG Access | Server (async) |
| run_agent | Agents | Server (async) |
| list_agents | Agents | Server |
| generate_react_component | Dev Shortcuts | Server |
| generate_fastapi_endpoint | Dev Shortcuts | Server |
| scan_code_security | Dev Shortcuts | Server |
| analyze_code_complexity | Dev Shortcuts | Server |
| generate_tests | Dev Shortcuts | Server |
| start_guided_tour | Tours | Server |
| get_available_tours | Tours | Server |
| create_project | Workspace | Server |
| list_projects | Workspace | Server |
| run_workflow | Workspace | Server (async) |
| search_playbooks | Workspace | Server |
| chat_with_expert | Experts | Server |
| list_experts | Experts | Server |
| create_macro | Macros | Server |
| list_macros | Macros | Server |
| run_macro | Macros | Server |
| delete_macro | Macros | Server |
| check_thermal | Monitoring | Server |
| start_feature_interview | Interview | Server |

### POST /api/vox/awareness
Log page visit, error, or context events from the frontend.

**Request:**
```json
{
  "event_type": "page_visit",
  "page": "/tools",
  "metadata": {}
}
```

**Event types:** `page_visit`, `error`, `context`

### GET /api/vox/awareness
Get current awareness context.

**Response:**
```json
{
  "prompt": "User recently visited: /tools, /kg-studio...",
  "recent_pages": ["/tools", "/kg-studio"],
  "unresolved_errors": [],
  "page_stats": { "/tools": 5, "/chat": 12 }
}
```

### GET /api/vox/tours
List available guided tours.

**Response:**
```json
{
  "tours": [{ "page": "chat", "name": "Chat Tour", "description": "...", "step_count": 5 }],
  "count": 11
}
```

### GET /api/vox/tours/{page}
Get tour steps for a specific page.

### GET /api/vox/macros
List all saved voice macros.

### POST /api/vox/macros
Create a new voice macro.

**Request:**
```json
{
  "name": "Security Scan",
  "trigger_phrase": "scan my code",
  "steps": [
    { "function": "run_tool", "args": { "tool_id": "security_scanner" } }
  ],
  "error_policy": "abort"
}
```

### DELETE /api/vox/macros/{macro_id}
Delete a voice macro.

### POST /api/vox/macros/{macro_id}/run
Execute a voice macro by ID.

### GET /api/vox/thermal
Get device temperature and battery status (Termux battery API).

### GET /api/vox/interview
Return the 10-question feature interview definition for MVP building.

### POST /api/vox/interview/generate
Accept interview answers and stream a React MVP via the Studio generation pipeline.

**Request:**
```json
{
  "answers": { "1": "dashboard", "2": "Track expenses" },
  "provider": "gemini",
  "model": "gemini-2.5-flash",
  "project_id": "optional-studio-project-uuid"
}
```

**SSE Events:** Same as Studio stream (`token`, `studio_plan`, `studio_file`, `studio_dep`, `complete`)

### WebSocket /ws/vox
Bidirectional WebSocket for VOX voice sessions. Supports both Gemini (native audio) and Claude (text + tool_use) modes.

**Client -> Server Messages:**
```json
{"type": "start", "mode": "gemini", "voice": "Puck", "model": "gemini-2.5-flash-exp-native-audio-thinking-dialog", "systemPrompt": "", "session_token": "optional-resume-token"}
{"type": "audio", "data": "<base64-pcm-16khz>"}
{"type": "text", "text": "Navigate to the tools page"}
{"type": "browser_function_result", "name": "navigate_page", "result": {"success": true}, "fn_call_id": "..."}
{"type": "end"}
```

**Server -> Client Messages:**
```json
{"type": "setup_complete", "sessionId": "abc123", "mode": "gemini", "resumed": false}
{"type": "audio", "data": "<base64-pcm-24khz>"}
{"type": "text", "text": "I'll navigate you to the tools page."}
{"type": "function_call", "name": "navigate_page", "args": {"path": "/tools"}, "server_handled": false}
{"type": "function_call", "name": "list_tools", "args": {}, "server_handled": true}
{"type": "function_result", "name": "list_tools", "result": {"success": true, "tools": [...]}}
{"type": "async_task_started", "task_id": "abc", "function": "run_agent"}
{"type": "async_task_complete", "task_id": "abc", "function": "run_agent", "result": {...}}
{"type": "start_tour", "page": "chat", "tour": {...}}
{"type": "turn_complete", "turn": 1}
{"type": "transcript", "role": "user", "text": "Navigate to tools"}
{"type": "transcript", "role": "model", "text": "Navigating to tools page..."}
{"type": "go_away", "session_token": "...", "message": "Session reconnecting..."}
{"type": "error", "message": "..."}
```

---

## Integrations

Platform integration webhooks and management. Supports Telegram, WhatsApp, Discord, Slack, Gmail, Spotify, and Calendar.

### Webhook Endpoints

| Method | Path | Platform |
|--------|------|----------|
| POST | /api/integrations/telegram/webhook | Telegram Bot updates |
| GET | /api/integrations/whatsapp/webhook | WhatsApp verification challenge |
| POST | /api/integrations/whatsapp/webhook | WhatsApp inbound messages |
| POST | /api/integrations/discord/webhook | Discord interactions (auto-handles PING) |
| POST | /api/integrations/slack/webhook | Slack Events API (auto-handles URL verification) |
| POST | /api/integrations/gmail/webhook | Gmail Pub/Sub push notifications |

### Management Endpoints

### GET /api/integrations
List all integrations with status (configured keys listed, secrets hidden).

### POST /api/integrations/{platform}/configure
Save credentials for a platform.

**Request:**
```json
{
  "config": { "bot_token": "...", "chat_id": "..." },
  "user_label": "My Telegram Bot"
}
```

### POST /api/integrations/{platform}/test
Test connectivity for a configured platform.

### POST /api/integrations/{platform}/enable
Enable a configured integration.

### POST /api/integrations/{platform}/disable
Disable an integration.

### DELETE /api/integrations/{platform}
Remove an integration entirely.

### GET /api/integrations/{platform}/setup
Get setup instructions for a platform.

### Spotify Endpoints

### GET /api/integrations/spotify/now-playing
Get currently playing track.

### POST /api/integrations/spotify/search
Search Spotify.

**Request:** `{ "query": "bohemian rhapsody", "type": "track" }`

### POST /api/integrations/spotify/queue
Add track to queue.

**Request:** `{ "uri": "spotify:track:..." }`

### GET /api/integrations/spotify/playlists
List user playlists.

### Calendar Endpoints

### GET /api/integrations/calendar/events?max_results=10&time_min=
List upcoming calendar events.

### POST /api/integrations/calendar/events
Create a calendar event.

**Request:**
```json
{
  "summary": "Team Meeting",
  "start": "2026-03-01T10:00:00Z",
  "end": "2026-03-01T11:00:00Z",
  "description": "Weekly sync"
}
```

### PUT /api/integrations/calendar/events/{event_id}
Update a calendar event.

**Request:** `{ "summary": "Updated Title", "start": "...", "end": "..." }`

### DELETE /api/integrations/calendar/events/{event_id}
Delete a calendar event.

---

## Mode & Interchange

### GET /api/mode
Get current operating mode.

### POST /api/mode
Switch mode.

**Request:** `{ "mode": "standalone" | "claude-code" }`

### GET /api/config/keys/status
Check which API keys are configured (never exposes actual keys).

**Response:**
```json
{
  "gemini": true,
  "anthropic": true,
  "mode": "standalone"
}
```

### POST /api/config/keys
Set API keys at runtime (stored in memory only, not written to disk).

**Request:**
```json
{
  "gemini_key": "AIza...",
  "anthropic_key": "sk-ant-..."
}
```

### POST /api/export
Export workspace state as JSON.

### POST /api/import
Import workspace JSON.

**Format:**
```json
{
  "version": "1.0",
  "mode": "standalone",
  "timestamp": "2026-02-27T...",
  "data": {
    "projects": [...],
    "files": {...},
    "workflows": [...],
    "chatHistory": [...],
    "personas": [...]
  }
}
```

---

## MCP Server

Standalone MCP server exposing all 58+ workspace tools as individual MCP tools.

```bash
python3 backend/mcp_server.py           # Run on stdio (JSON-RPC)
python3 backend/mcp_server.py --list    # Print tool table
python3 backend/mcp_server.py --json    # Dump tool schemas as JSON
```

**Supported MCP Methods:** `initialize`, `tools/list`, `tools/call`, `ping`

---

## Model Catalog

23 models across 7 categories from 2 providers.

### Gemini Models (20)

| Model ID | Name | Category | Context | Cost In/Out ($/1M) |
|----------|------|----------|---------|---------------------|
| gemini-3-pro-preview | Gemini 3 Pro | text | 1M | $2.00 / $12.00 |
| gemini-3.1-pro-preview | Gemini 3.1 Pro | text | 1M | $2.00 / $12.00 |
| gemini-3.1-pro-preview-customtools | Gemini 3.1 Pro Custom Tools | text | 1M | $2.00 / $12.00 |
| gemini-3-flash-preview | Gemini 3 Flash | text | 1M | $0.10 / $0.40 |
| gemini-2.5-flash | Gemini 2.5 Flash | text | 1M | $0.15 / $0.60 |
| gemini-2.5-pro | Gemini 2.5 Pro | text | 1M | $1.25 / $5.00 |
| gemini-2.5-flash-lite | Gemini 2.5 Flash Lite | text | 1M | $0.075 / $0.30 |
| gemini-2.5-flash-image | Gemini 2.5 Flash Image | image | 1M | $0.15 / $0.60 |
| gemini-3-pro-image-preview | Nano Banana Pro | image | 1M | $2.00 / $12.00 |
| imagen-4.0-generate-preview-05-20 | Imagen 4 | image | - | free / $0.04 |
| veo-2.0-generate-001 | Veo 2.0 | video | - | free |
| veo-3.1-generate-preview | Veo 3.1 | video | - | free |
| veo-3.1-fast-generate-preview | Veo 3.1 Fast | video | - | free |
| gemini-2.5-flash-native-audio-preview | Gemini Flash Audio | audio | 1M | $0.15 / $0.60 |
| gemini-2.5-flash-preview-tts | Gemini Flash TTS | audio | 8K | $0.15 / $0.60 |
| gemini-2.5-pro-preview-tts | Gemini Pro TTS | audio | 8K | $1.25 / $5.00 |
| lyria-realtime-exp | Lyria | music | - | free |
| gemini-embedding-001 | Gemini Embedding | embedding | 8K | free |
| gemini-2.5-computer-use-preview | Gemini Computer Use | agent | 1M | $1.25 / $5.00 |
| deep-research-pro-preview | Deep Research | agent | 1M | $2.00 / $12.00 |

### Claude Models (3)

| Model ID | Name | Category | Context | Cost In/Out ($/1M) |
|----------|------|----------|---------|---------------------|
| claude-opus-4-6 | Claude Opus 4.6 | text | 200K | $5.00 / $25.00 |
| claude-sonnet-4-6 | Claude Sonnet 4.6 | text | 200K | $3.00 / $15.00 |
| claude-haiku-4.5 | Claude Haiku 4.5 | text | 200K | $0.25 / $1.25 |

---

## Notes

### Theme System
Theme switching is handled entirely client-side via CSS custom properties. No backend API is involved. The active theme ID is persisted in `localStorage` under the key `workspace_theme`. Five themes available: default, crt, scratch, solarized, sunset.

### Conversation Persistence
All chat, coding, KG RAG, and expert conversations are automatically persisted via the memory service. The `conversationId` field enables multi-turn continuity across page reloads.

### Agentic Loop
Chat, coding, and KG RAG endpoints all route through a unified agentic loop (`services/agentic_loop.py`) that handles provider abstraction, tool execution, and streaming normalization.

### Phaser Static Files
Game preview uses Phaser 3 runtime served from `/docs/phaser/` via FastAPI static file mount (not an API endpoint).

### Playbooks Directory
Playbooks are loaded from `docs/playbooks-v2/` (configured in `backend/config.py` as `PLAYBOOKS_DIR`).

### Async VOX Functions
Functions marked as async (`ingest_to_kg`, `run_workflow`, `cross_kg_search`, `run_agent`) execute with a 5-minute timeout and emit `async_task_started` / `async_task_complete` WebSocket events.

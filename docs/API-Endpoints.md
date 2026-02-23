# API Endpoints Reference

Base URL: `http://localhost:8000/api`

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
List available models per provider.

**Response:**
```json
{
  "gemini": {
    "gemini-2.5-flash": { "name": "Gemini 2.5 Flash", "context": 1000000, "cost_in": 0.15, "cost_out": 0.60 },
    ...
  },
  "claude": { ... }
}
```

---

## Chat

### POST /api/chat/stream
SSE streaming chat with dual-model support.

**Request:**
```json
{
  "messages": [{ "author": "user", "parts": [{ "text": "Hello" }] }],
  "provider": "gemini",
  "model": "gemini-2.5-flash",
  "persona": { "id": "default", "name": "Default", "baseInstructions": "", "composedStyles": [] },
  "customStyles": [],
  "useWebSearch": false,
  "thinkingBudget": 0
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

---

## Coding

### POST /api/coding/stream
SSE streaming with tool use for coding assistant.

**Request:**
```json
{
  "history": [...],
  "projects": [{ "id": "...", "name": "my-app" }],
  "persona": {...},
  "customStyles": [],
  "useWebSearch": false,
  "provider": "gemini",
  "model": "gemini-2.5-flash",
  "thinkingBudget": 0
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

## Agents

### GET /api/agents
List all 33 NLKE agents.

**Response:**
```json
{
  "agents": [
    { "name": "cost-advisor", "category": "FOUNDATION", "description": "Optimize API costs..." },
    ...
  ]
}
```

### GET /api/agents/{name}/example
Get example workload for an agent.

### POST /api/agents/{name}/run
Execute an agent with a workload.

**Request:**
```json
{
  "workload": {
    "goal": "Reduce API costs by 50%",
    "context": { "current_model": "claude-opus-4-6", "monthly_cost": 500 }
  }
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
List 4 built-in workflow templates.

**Templates:**
- `dev_lifecycle` — Plan → Code → Test → Review → Docs
- `research_analysis` — Research → Analyze → Validate → Synthesize
- `kg_pipeline` — Extract → Relate → Validate → Export
- `decision_making` — Options → Pros/Cons → Risk → Recommend

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
Execute a workflow with SSE streaming.

**SSE Events:**
```
data: {"type": "step_start", "step_id": "plan", "name": "Architecture Planning"}
data: {"type": "step_token", "step_id": "plan", "content": "..."}
data: {"type": "step_complete", "step_id": "plan"}
data: {"type": "step_error", "step_id": "code", "error": "..."}
data: {"type": "workflow_complete", "step_count": 5}
```

---

## Builder

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

## Media

### POST /api/image/edit
Edit an image with AI (multipart form).

**Form Fields:** `prompt` (string), `file` (image file)

### POST /api/video/generate
Start video generation with Veo 2.0.

**Form Fields:** `prompt` (string), `file` (optional image)

**Response:** `{ "operationName": "..." }`

### GET /api/video/status?operationName={name}
Poll video generation status.

**Response:** `{ "done": true, "videoUrl": "..." }` or `{ "done": false }`

---

## Mode & Interchange

### GET /api/mode
Get current operating mode.

### POST /api/mode
Switch mode.

**Request:** `{ "mode": "standalone" | "claude-code" }`

### POST /api/export
Export workspace state as JSON.

### POST /api/import
Import workspace JSON.

**Format:**
```json
{
  "version": "1.0",
  "mode": "standalone",
  "timestamp": "2026-02-22T...",
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

### GET /api/kg/databases/{db_id}/nodes?node_type=&search=&limit=50&offset=0
Paginated node listing with optional type filter and text search.

### GET /api/kg/databases/{db_id}/nodes/{node_id}
Single node with all properties and connections.

### GET /api/kg/databases/{db_id}/nodes/{node_id}/neighbors?depth=1&limit=50
Subgraph around a node for graph visualization.

### GET /api/kg/databases/{db_id}/edges?edge_type=&limit=50&offset=0
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
  "limit": 20
}
```
**Modes:** `fts` (BM25/FTS5), `embedding` (vector), `hybrid` (combined: 0.40*embedding + 0.45*BM25 + 0.15*graph)

### POST /api/kg/search/multi
Cross-KG search across multiple databases.

### POST /api/kg/databases
Create a new KG database.

**Request:** `{ "name": "my-knowledge-graph", "description": "..." }`

### POST /api/kg/databases/{db_id}/nodes
Create a node.

**Request:** `{ "name": "Node Name", "node_type": "concept", "properties": {} }`

### PUT /api/kg/databases/{db_id}/nodes/{node_id}
Update a node.

### DELETE /api/kg/databases/{db_id}/nodes/{node_id}
Delete a node and its connected edges.

### POST /api/kg/databases/{db_id}/edges
Create an edge.

**Request:** `{ "source_id": "...", "target_id": "...", "edge_type": "relates_to" }`

### PUT /api/kg/databases/{db_id}/edges/{edge_id}
Update an edge.

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
  "method": "ai"
}
```
**Methods:** `ai` (Gemini entity extraction), `lightrag` (LightRAG pipeline), `manual` (store as document node)

### GET /api/kg/databases/{db_id}/analytics/summary
Graph metrics: density, components, clustering, avg degree, isolates.

### GET /api/kg/databases/{db_id}/analytics/centrality?metric=degree&limit=20
Top-k nodes by centrality metric.

**Metrics:** `degree`, `betweenness`, `pagerank`

### GET /api/kg/databases/{db_id}/analytics/communities
Community detection via greedy modularity.

### POST /api/kg/databases/{db_id}/analytics/path
Shortest path between two nodes.

**Request:** `{ "source_id": "...", "target_id": "..." }`

### POST /api/kg/databases/{db_id}/chat
RAG chat with SSE streaming and source citations.

**Request:**
```json
{
  "query": "How does cost optimization work?",
  "mode": "hybrid",
  "model": "gemini-2.5-flash"
}
```

**SSE Events:**
```
data: {"type": "token", "content": "Cost optimization..."}
data: {"type": "sources", "nodes": [{"id": "...", "name": "...", "score": 0.95}]}
data: {"type": "done"}
```

### POST /api/kg/compare
Structural comparison between two KGs.

**Request:** `{ "db_a": "claude-kg", "db_b": "gemini-kg" }`

### POST /api/kg/diff
Detailed diff: added/removed/modified nodes and edges.

### POST /api/kg/merge
Merge source KG into target.

**Request:** `{ "source": "...", "target": "...", "strategy": "union" }`
**Strategies:** `union`, `intersection`, `complement`

### POST /api/kg/databases/{db_id}/batch/delete-by-type
Batch delete all nodes of a given type.

### POST /api/kg/databases/{db_id}/batch/retype
Batch rename a node type.

### GET /api/kg/databases/{db_id}/embedding-status
Check embedding availability for a KG.

### GET /api/kg/databases/{db_id}/embeddings/projection
2D t-SNE/PCA projection data for embedding visualization.

### POST /api/kg/databases/{db_id}/embeddings/generate
Generate embeddings for all nodes in a KG.

### GET /api/kg/databases/{db_id}/embeddings/quality
Embedding quality metrics: coverage, similarity distribution.

---

## Notes

### Theme System
Theme switching is handled entirely client-side via CSS custom properties. No backend API is involved. The active theme ID is persisted in `localStorage` under the key `workspace_theme`.

### Model Names
Gemini model names no longer use preview suffixes:
- `gemini-2.5-flash` (was `gemini-2.5-flash-preview-05-20`)
- `gemini-2.5-pro` (was `gemini-2.5-pro-preview-05-06`)
- `gemini-2.5-flash-image` (was `gemini-2.5-flash-preview-native-audio-dialog`)

### Playbooks Directory
Playbooks are loaded from `docs/playbooks-v2/` (configured in `backend/config.py` as `PLAYBOOKS_DIR`).

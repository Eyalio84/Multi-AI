# 03-INTEGRATION-OPPORTUNITY-MAP.md — Where the Technology ISN'T Applied

> **Purpose**: Per-page audit of where KG/RAG technology IS and ISN'T applied, with concrete integration proposals. This document directly addresses the reverse Dunning-Kruger blind spot: the builder doesn't realize how much of his own platform could benefit from technology he already built.

---

## 3.1 The Gap: 26% Active Utilization

The multi-AI agentic workspace contains **14 frontend pages** and **17 backend routers**. Of these:

| KG Integration Level | Frontend Pages | Backend Routers | Details |
|---------------------|----------------|-----------------|---------|
| **Full KG** | 3 (21%) | 5 (29%) | Direct KG/embedding/analytics calls |
| **Partial KG** (via agentic loop) | 2 (14%) | 5 (29%) | Implicit through unified pipeline |
| **No KG** | 9 (64%) | 7 (41%) | Zero KG service interaction |

**The math is stark**: The builder created a 4-weight hybrid retrieval system achieving 88.5% recall, 62 KG databases, 70 semantic dimensions, 12 query methods, 14 intent profiles, and a full KG-OS query engine. Then he deployed it on **3 of 14 pages** (21%).

Put differently: 79% of the platform's surface area has zero access to the technology that makes the other 21% extraordinary.

### Current Integration Architecture

```
                    ┌─────────────────────────────────────────────┐
                    │            14 FRONTEND PAGES                 │
                    ├──────────┬──────────┬───────────────────────┤
                    │ FULL KG  │ PARTIAL  │    NO KG (9 pages)    │
                    │ (3 pages)│ (2 pages)│                       │
                    ├──────────┼──────────┼───────────────────────┤
                    │KGStudio  │Coding    │Agents  │Tools  │Games │
                    │Experts   │Studio    │Playbook│Vox    │Integ │
                    │Chat*     │          │Workflow│Setting│Builder│
                    └────┬─────┴────┬─────┴──┬────┴───┬───┴──────┘
                         │          │        │        │
                    ┌────▼──────────▼────┐   │        │
                    │   AGENTIC LOOP    │   │     NO PATH
                    │ memory + skills   │   │    TO KG LAYER
                    ├───────────────────┤   │        │
                    │ embedding_service │◄──┘        │
                    │ kg_service        │            │
                    │ kgos_query_engine │            │
                    │ analytics_service │            │
                    │ memory_service    │            │
                    │ ingestion_service │            │
                    └───────────────────┘
```

*Chat achieves full KG through the agentic loop's Stage 2 (Memory) and Stage 3 (Skills).

---

## 3.2 Per-Page Analysis

### 3.2.1 ChatPage — Full KG (via agentic loop)

**Source**: `frontend/src/pages/ChatPage.tsx` (175 bytes — delegates to `ChatPanel`)
**Backend**: `backend/routers/chat.py` (41 lines) → `agentic_loop.run(mode="chat")`

**Current KG Usage**:
- **Stage 2 — Memory Recall**: `memory_service.recall()` searches conversation KG with hybrid retrieval (embedding + BM25 + intent + FTS5). Up to 5 memories injected per turn.
  - Source: `agentic_loop.py:72-89`
- **Stage 3 — Skill Injection**: `skill_injector.get_relevant_context()` classifies intent across 10 categories and injects playbook excerpts + KG memory nodes.
  - Source: `skill_injector.py:106-170`, triggered for `mode in ("chat", "coding", "messaging")`
- **Stage 8 — Persist**: Saves assistant response + extracted entities to memory KG via `memory_service.log_message()` with regex entity extraction.
  - Source: `agentic_loop.py:67-69`, `memory_service.py:258-316`

**Missed Opportunities**:

1. **Semantic Context Panel** (Medium Effort)
   - Display retrieved memories and skill injections as a visible sidebar panel
   - Show the user WHICH memories influenced the response
   - Frontend: Add `ContextPanel` component showing memory nodes + scores
   - Backend: Emit memory/skill metadata as SSE events (add `type: "memory_context"` event in agentic_loop)
   - **Why it matters**: The user can't see the KG working. Making it visible builds trust and enables manual correction.

2. **Intent-Driven Model Routing** (Low Effort)
   - Current: User manually selects provider (Gemini/Claude/OpenAI)
   - Proposed: `skill_injector.classify_intent()` output feeds `model_router` to auto-suggest optimal model
   - Example: "reduce API costs" → `cost_optimization` intent → suggest Gemini Flash (cheapest)
   - Backend: `agentic_loop.py` Stage 1, after intent classification, emit `type: "model_suggestion"` event
   - **Why it matters**: The intent classification already runs — its output is just discarded after skill injection.

3. **Cross-Session Topic Continuity** (Medium Effort)
   - Current: Memory recall searches all conversations equally
   - Proposed: Detect topic continuity across sessions. If the user asks about "embeddings" and 3 of the last 5 sessions were about embeddings, boost those memories.
   - Backend: `memory_service.recall()` add session-affinity scoring
   - **Why it matters**: Memory is flat — it doesn't understand that 5 scattered mentions of "embeddings" form a coherent learning trajectory.

**Priority**: Medium — ChatPage already works well; improvements are visibility and intelligence upgrades.

---

### 3.2.2 CodingPage — Partial KG (via agentic loop)

**Source**: `frontend/src/pages/CodingPage.tsx` (6.6 KB)
**Backend**: `backend/routers/coding.py` (201 lines) → `agentic_loop.run(mode="coding")`

**Current KG Usage**:
- Same as ChatPage: memory recall + skill injection + persist via agentic loop
- Left panel: File explorer (AppContext project/file management — no KG)
- Right panel: ChatPanel with code streaming

**Missed Opportunities**:

1. **Code Pattern KG** (High Effort)
   - Build a KG from the project's code structure: functions→files, imports→dependencies, classes→methods
   - Use `ingestion_service` to extract entities from code files (adapt `EXTRACTION_PROMPT` for code)
   - Backend: New `/api/coding/analyze` endpoint that builds a project-specific KG
   - Frontend: Display dependency graph using d3-force (already available in KGStudioPage)
   - **Why it matters**: The coding assistant doesn't understand project structure. A code KG would enable "which files are affected if I change this function?"

2. **Error-Driven KG Navigation** (Medium Effort)
   - When tool calls fail or errors appear, search the memory KG for similar past errors and their resolutions
   - Backend: In `agentic_loop.py` Stage 6 (Tools), on error, call `memory_service.recall(error_message)`
   - Frontend: Display "Similar past errors" panel when errors occur
   - **Why it matters**: The same errors recur. The memory KG contains past resolutions but nobody queries it during error handling.

3. **Playbook-Guided Refactoring** (Low Effort)
   - Current: Skill injection gives generic playbook excerpts
   - Proposed: For coding mode, detect refactoring patterns (rename, extract, inline) and inject specific playbook sections
   - Backend: Add `"refactoring"` to `INTENT_PATTERNS` in `skill_injector.py` with patterns like "refactor", "extract method", "rename"
   - **Why it matters**: 53 playbooks contain production-tested coding patterns. The coding assistant ignores them unless the user explicitly asks about them.

**Priority**: High — CodingPage is a primary workflow surface but has minimal KG intelligence beyond generic memory recall.

---

### 3.2.3 AgentsPage — No KG

**Source**: `frontend/src/pages/AgentsPage.tsx` (9.8 KB)
**Backend**: `backend/routers/agents.py` (137 lines) → `agent_bridge`

**Current KG Usage**: None. The 33 NLKE agents are loaded from the filesystem via `agent_bridge`. Agent execution is a standalone process — no KG query, no memory recall, no skill injection.

**Missed Opportunities**:

1. **Capability-Aware Agent Router** (High Impact, Medium Effort)
   - Use the capability KGs (claude-capabilities, openai-capabilities, gemini-capabilities) to match user goals to optimal agents
   - Backend: New endpoint `/api/agents/recommend?goal=<text>` that calls `kgos_query_engine.want_to()` on the capability KGs
   - Frontend: "Recommended Agents" section above the agent list, based on recent chat context
   - **Why it matters**: 33 agents is overwhelming. The KG-OS system can route "I want to optimize my prompts" → Playbook Synthesizer Agent + Adaptive Reasoning Agent, but nobody asks it.

2. **Agent Composition Graph** (Medium Effort)
   - Build a KG of agent relationships: which agents complement each other, which share tools, which produce outputs others consume
   - Use `kgos_query_engine.compose_for()` to generate multi-agent workflows
   - Frontend: Visual pipeline builder backed by KG composition suggestions
   - Backend: `/api/agents/compose?goal=<text>` calling `compose_for()` on an agent-capability KG
   - **Why it matters**: The multi-agent orchestrator exists (`agents/multi_agent_orchestrator.py`) but it requires manual DAG specification. KG-OS could auto-compose agent pipelines.

3. **Agent Execution Memory** (Low Effort)
   - After each agent execution, persist the result to the memory KG
   - Backend: In `agents.py` `/agents/{name}/run`, after execution, call `memory_service.log_message()` with mode="agent"
   - **Why it matters**: Agent results evaporate after execution. If the KG Curator Agent finds 5 inconsistencies, that knowledge should persist and influence future queries.

**Priority**: High — Agents are the platform's most powerful feature but the least KG-connected.

---

### 3.2.4 PlaybooksPage — No KG

**Source**: `frontend/src/pages/PlaybooksPage.tsx` (6.7 KB)
**Backend**: `backend/routers/playbooks.py` (36 lines) → `playbook_index`

**Current KG Usage**: None. Playbooks are searched via static file-based keyword matching (`playbook_index.search()`). No embeddings, no KG traversal, no intent classification.

**Missed Opportunities**:

1. **Playbook Semantic Search** (High Impact, Low Effort)
   - Replace `playbook_index.search()` with `embedding_service.search()` on a playbook KG
   - Each playbook becomes a node. Sections become sub-nodes. Cross-references become edges.
   - Query "how to handle rate limits" → traverses cost_optimization + production_deployment + multi_model_workflows (currently returns only exact keyword matches)
   - Backend: Build playbook KG (one-time) via `ingestion_service.ingest()`. New endpoint: `/api/playbooks/semantic-search`
   - **Why it matters**: 53 playbooks contain 56K+ lines of institutional knowledge. File-based search misses cross-playbook insights that the 4-weight hybrid formula would find.

2. **Prerequisite DAG Visualization** (Medium Effort)
   - Playbooks reference each other: "See Playbook 8" from Playbook 17, "Combine with Playbook 9" from Playbook 23
   - Extract cross-references into a directed acyclic graph
   - Frontend: Render prerequisite graph using d3-force (reuse KGCanvas component)
   - Backend: `/api/playbooks/graph` endpoint returning nodes (playbooks) and edges (cross-references)
   - **Why it matters**: The "Quick Start Paths" in CLAUDE.md were manually curated. The DAG reveals paths the builder didn't consciously document.

3. **Reading History KG** (Low Effort)
   - Track which playbooks the user reads, how long, and in what order
   - Build a user-learning KG: user→read→playbook, playbook→leads_to→next_playbook
   - Use `kgos_query_engine.roadmap()` to suggest next reading based on learning trajectory
   - Backend: `/api/playbooks/{filename}/read` (log event), `/api/playbooks/recommended` (KG-OS roadmap)
   - **Why it matters**: 53 playbooks is a curriculum. Without tracking, the user re-reads familiar content and misses gaps.

**Priority**: High — Playbooks are the platform's institutional memory but use the crudest search of any feature.

---

### 3.2.5 WorkflowsPage — No KG

**Source**: `frontend/src/pages/WorkflowsPage.tsx` (8.5 KB)
**Backend**: `backend/routers/workflows.py` (262 lines) → `workflow_service`

**Current KG Usage**: Minimal. One workflow template ("KG Pipeline") mentions entity extraction, but no KG services are actually called during workflow planning or execution. Workflows are planned by the LLM, not by KG traversal.

**Missed Opportunities**:

1. **Pattern KG for Workflow Steps** (Medium Effort)
   - Build a KG of workflow patterns: common step sequences, tool chains, branching conditions
   - When the user describes a goal, `kgos_query_engine.compose_for()` generates the workflow DAG from KG structure
   - Backend: Populate a workflow-patterns KG from executed workflows. New: `/api/workflows/suggest?goal=<text>`
   - **Why it matters**: The LLM generates workflow steps from scratch every time. A pattern KG would ground suggestions in proven sequences.

2. **Step-Level Recommendations** (Low Effort)
   - During workflow execution (SSE streaming), after each step completes, use `kgos_query_engine.recommend()` to suggest refinements or alternatives for the next step
   - Backend: In `workflows.py` step execution loop, add KG-OS recommendation call
   - **Why it matters**: Workflows are linear. KG-OS can detect when a step could branch or when a better tool exists.

3. **Execution Analytics KG** (Medium Effort)
   - Log every workflow execution as a KG: steps→outcomes, tools→success_rates, patterns→performance
   - Use `analytics_service.centrality()` to find which steps are bottlenecks
   - Backend: Post-execution, call `memory_service.log_message()` with mode="workflow" + entity extraction
   - **Why it matters**: 4 workflow templates exist. After 100 executions, the KG would reveal which steps consistently fail and which alternatives work better.

**Priority**: Medium — Workflows work but miss the compound learning that KG persistence enables.

---

### 3.2.6 KGStudioPage — Full KG (flagship)

**Source**: `frontend/src/pages/KGStudioPage.tsx` (17 KB)
**Backend**: `backend/routers/kg.py` (503 lines) → kg_service, embedding_service, analytics_service, ingestion_service, capability_kg_builder

**Current KG Usage**: Comprehensive. 10 tabs covering:

| Tab | Backend Services | Key Operations |
|-----|-----------------|----------------|
| Explore | kg_service, embedding_service | d3-force graph viz, node selection, neighbor expansion |
| Search | embedding_service | 4-weight hybrid search (α=0.40, β=0.45, γ=0.15, δ=0.10) |
| Edit | kg_service | Node/edge CRUD, edge browser with type filtering |
| Ingest | ingestion_service | AI entity extraction (Gemini Flash / LightRAG / Manual) |
| Analytics | analytics_service | Centrality, communities, paths (NetworkX) |
| RAG Chat | agentic_loop (mode="rag") | Streaming chat with source citations |
| Compare | analytics_service | Structural KG comparison (Jaccard) |
| Merge | analytics_service | Union/intersection/complement merge |
| Embeddings | embedding_service | Projection (PCA/TSNE), quality metrics |
| Batch | kg_service | Bulk operations |

**Missed Opportunities** (minor — this page is excellent):

1. **Query History + Suggestion Engine** (Low Effort)
   - Track queries per KG database, build a query KG: query→returned→nodes, query→intent→category
   - Suggest queries based on what other users/sessions have searched
   - Frontend: "Suggested queries" dropdown in Search tab
   - **Why it matters**: Users re-ask similar questions. Past queries are the best input for suggestions.

2. **ULTRA 50G Link Prediction** (High Impact, Medium Effort)
   - The `docs/ultra_50g/` directory contains a pre-trained KG reasoning foundation model that performs zero-shot link prediction across 50+ knowledge graphs
   - **Architecture**: Dual Neural Bellman-Ford Networks (relation model + entity model), 169K parameters
   - **Performance**: MRR 0.389 vs Supervised SOTA 0.371 on unseen graphs — better zero-shot than models trained on specific graphs
   - **Integration**: Add "Predict" tab to KG Studio that runs `(head, relation, ?)` queries through ULTRA 50G
   - **Backend**: New service `ultra_service.py` wrapping `UltraForKnowledgeGraphReasoning.from_pretrained("mgalkin/ultra_50g")`
   - **Frontend**: "Link Prediction" panel showing ranked entity candidates with confidence scores
   - **Why it matters**: The workspace has 62 KGs but treats them as static. ULTRA 50G would enable dynamic reasoning — predicting missing edges, discovering implicit relationships, suggesting new connections. This transforms KGs from storage into inference engines.

3. **Cross-KG Automated Bridging** (Medium Effort)
   - Current: Bridge edges between capability KGs are built manually via `capability_kg_builder.build_unified_kg()`
   - Proposed: Use ULTRA 50G to predict bridge edges automatically across any KG pair
   - Query: `(claude.tool_use, equivalent_capability, ?)` → ULTRA predicts Gemini/OpenAI equivalents
   - **Why it matters**: 62 KGs are islands. Automated bridging creates a knowledge fabric.

**Priority**: Low for minor improvements, High for ULTRA 50G integration.

---

### 3.2.7 StudioPage — Partial KG (via agentic loop)

**Source**: `frontend/src/pages/StudioPage.tsx` (7.6 KB)
**Backend**: `backend/routers/studio.py` (1,460 lines) → project CRUD, streaming via agentic loop

**Current KG Usage**:
- Chat/refinement streaming uses agentic loop → memory recall + skill injection
- Project CRUD, version management, mock server, ZIP export — no KG

**Missed Opportunities**:

1. **Architecture Pattern KG** (High Impact, Medium Effort)
   - Build a KG of React/frontend patterns from past Studio projects: components→patterns, layouts→grid_systems, state→management_approaches
   - When generating new apps, query the pattern KG for proven architectures
   - Backend: After project generation, extract patterns via `ingestion_service.ingest()`. New: `/api/studio/patterns?goal=<text>`
   - **Why it matters**: Every Studio project starts from scratch. A pattern KG would accelerate generation by reusing proven structures.

2. **Component Reuse Graph** (Medium Effort)
   - Index all generated components across all Studio projects into a KG
   - When generating a new project, `kgos_query_engine.similar_to()` finds reusable components from past projects
   - Frontend: "Similar Components" panel in the file explorer
   - **Why it matters**: The builder generates hundreds of components. Without indexing, identical button/modal/form components are regenerated from scratch.

3. **Version Evolution KG** (Low Effort)
   - Track version snapshots as KG nodes. Edges: version→changed→files, version→added→feature, version→fixed→bug
   - Use `analytics_service.shortest_path()` to show the evolution path from initial idea to current state
   - Backend: Extend `/api/studio/projects/{id}/save` to also create KG nodes/edges
   - **Why it matters**: Studio already has version history. Adding KG structure enables "what changed between v3 and v7?" queries.

**Priority**: Medium — Studio generates valuable patterns that are lost after each project.

---

### 3.2.8 ExpertsPage — Full KG (via KG-OS)

**Source**: `frontend/src/pages/ExpertsPage.tsx` (12.5 KB)
**Backend**: `backend/routers/experts.py` (232 lines) → `expert_service`, `kgos_query_engine`

**Current KG Usage**: Comprehensive. The KG-OS Expert Builder is the platform's most sophisticated KG consumer:

| Feature | Service | Detail |
|---------|---------|--------|
| 4-weight retrieval | embedding_service | α=0.35, β=0.40, γ=0.15, δ=0.10 (configurable per expert) |
| 14 intent profiles | kgos_query_engine | Automatic intent classification per query |
| 56 semantic dimensions | kgos_query_engine | Dimension filtering per expert config |
| Source citations | expert_service | Retrieved nodes shown as chat sources |
| KG-OS direct access | kgos_query_engine | 5 direct endpoints: query, impact, compose, similar, dimensions |

Source: `expert_service.py:15-89` (schema), `experts.py:30-85` (KGOS endpoints)

**Missed Opportunities** (minor — this is the model pattern):

1. **Expert Composition Suggestions** (Low Effort)
   - When creating an expert, suggest backing KGs based on the expert's description
   - Use `kgos_query_engine.recommend()` on the expert's persona instructions
   - Frontend: "Recommended KGs" in ExpertBuilder step 2
   - **Why it matters**: Users don't know which of the 62 KGs best matches their expert's domain.

2. **Cross-Expert Knowledge Sharing** (Medium Effort)
   - When Expert A retrieves relevant nodes, make them available to Expert B if they share a KG
   - Build an expert-collaboration KG: expert→shares→kg, expert→specializes_in→domain
   - **Why it matters**: Experts are isolated. A "Claude Tools" expert and a "Gemini Capabilities" expert could share insights about cross-provider patterns.

**Priority**: Low — ExpertsPage is already the gold standard. Other pages should replicate this pattern.

---

### 3.2.9 ToolsPage — No KG

**Source**: `frontend/src/pages/ToolsPage.tsx` (16.7 KB)
**Backend**: `backend/routers/tools.py` (53 lines) → `tools_service`

**Current KG Usage**: None. 58+ Python tools are loaded from a static registry (`tools_service.py`). Tool discovery is by category browsing only.

**Missed Opportunities**:

1. **Tool Capability Graph** (High Impact, Medium Effort)
   - Build a KG of tool relationships: tool→accepts→input_type, tool→produces→output_type, tool→complements→other_tool
   - Use `kgos_query_engine.want_to()` for goal-based tool discovery
   - Query: "I want to analyze a KG" → KG Analytics Tool + Embedding Quality Tool + Graph Comparison Tool
   - Backend: Build tool-capability KG (one-time), new: `/api/tools/recommend?goal=<text>`
   - **Why it matters**: 58 tools across 11 categories is overwhelming. The KG-OS system can route "I want to test my embeddings" to exactly the right tools, but nobody asks it.

2. **Tool Success History** (Low Effort)
   - Log each tool execution to the memory KG: tool→executed_with→params, tool→produced→result, tool→failed_with→error
   - Use `memory_service.recall()` to show "Past executions of this tool" in the tool detail view
   - Backend: In `tools.py` `/tools/{id}/run`, post-execution, log to memory
   - **Why it matters**: The same tools are run with similar parameters repeatedly. History enables "last time you ran this with these params, the result was..."

3. **Tool Chaining Recommendations** (Medium Effort)
   - Use `kgos_query_engine.compose_for()` to suggest multi-tool workflows
   - Frontend: "Suggested next tool" panel after tool execution completes
   - **Why it matters**: Tools are used in isolation. The KG can reveal that "Embedding Quality → Graph Analytics → RAG Evaluation" is a proven chain.

**Priority**: High — 58 tools need intelligent discovery. Static category browsing wastes the KG-OS infrastructure.

---

### 3.2.10 VoxPage — Partial KG (server-side functions)

**Source**: `frontend/src/pages/VoxPage.tsx` (22.5 KB)
**Backend**: `backend/routers/vox.py` (1,081 lines) → 34 function declarations, awareness layer, macros

**Current KG Usage**: Limited. 4 of 34 VOX functions access KGs:
- `query_kg`: Calls `embedding_service.hybrid_search()` (limit=5)
- `list_kgs`: Lists all databases via `kg_service`
- `ingest_to_kg`: Queues async ingestion
- `cross_kg_search`: Multi-database search

Source: `vox.py` function declarations (server-side execution)

**Missed Opportunities**:

1. **Voice Macro KG** (Medium Effort)
   - Voice macros already exist (`vox_macros.py`) but are stored as flat sequences
   - Build a macro KG: macro→contains→command, command→targets→tool, macro→similar_to→other_macro
   - Use `kgos_query_engine.similar_to()` to suggest existing macros when the user describes a task
   - **Why it matters**: Users create similar macros. KG similarity would prevent duplication and suggest optimizations.

2. **Context-Aware KG Routing** (Low Effort)
   - Current: `query_kg` function requires the user to specify which database
   - Proposed: Use `vox_awareness.py` (page context + error log) to auto-select the relevant KG
   - If user is on CodingPage → route to code-pattern KG. If on ExpertsPage → route to expert's backing KG
   - Backend: In `query_kg` function, check `vox_awareness` for current page context
   - **Why it matters**: "Hey VOX, search for authentication patterns" should auto-route to the right KG without the user knowing database IDs.

3. **Conversation Learning via Memory KG** (Low Effort)
   - VOX conversations (WebSocket transcript) are not persisted to the memory KG
   - Backend: After each VOX session, serialize transcript → `memory_service.log_message()` with mode="vox"
   - **Why it matters**: Voice interactions contain rich intent signals. "Show me cost optimization" in voice is identical to typing it — but voice data is discarded.

**Priority**: Medium — VOX already has the infrastructure; it just needs better KG integration.

---

### 3.2.11 GamesPage — Partial KG (via expert chat)

**Source**: `frontend/src/pages/GamesPage.tsx` (13.1 KB)
**Backend**: `backend/routers/games.py` (329 lines) → `game_service`, `game_generator`, `expert_service`

**Current KG Usage**: Limited. Expert chat (`/{id}/chat`) uses KG-OS retrieval for game design advice. The interview, GDD synthesis, code generation, and refinement pipelines have zero KG involvement.

**Missed Opportunities**:

1. **Game Design Pattern KG** (High Impact, Medium Effort)
   - Build a KG from the 18-question interview structure: genre→requires→mechanics, mechanic→compatible_with→theme, art_style→fits→genre
   - After each interview, persist answers as KG nodes
   - Use `kgos_query_engine.recommend()` when the user is stuck on a question
   - Backend: New game-patterns KG built from interview answer history
   - **Why it matters**: Each game project starts from a blank interview. Past answers contain domain knowledge that should accelerate new projects.

2. **Asset Reuse Graph** (Medium Effort)
   - Index generated game assets (sprites, scenes, UI elements) into a KG
   - When generating a new game, `kgos_query_engine.similar_to()` finds reusable assets from past projects
   - Frontend: "Similar Assets" panel in GameCodeEditor
   - **Why it matters**: Programmatic sprites are regenerated identically. An asset KG would deduplicate and accelerate.

3. **NPC Dialogue KG** (Medium Effort)
   - The local LLM NPC dialogue system (`game_llm_service.py`) generates contextual dialogue
   - Build a dialogue KG: npc→says→response, response→triggers→event, event→requires→condition
   - Use the KG to ensure dialogue consistency across NPCs
   - **Why it matters**: NPC dialogue is stateless. A dialogue KG would enable multi-turn NPC conversations with persistent world state.

**Priority**: Medium — Games are a secondary workflow but demonstrate the pattern gap clearly.

---

### 3.2.12 IntegrationsPage — No KG

**Source**: `frontend/src/pages/IntegrationsPage.tsx` (10.8 KB)
**Backend**: `backend/routers/integrations.py` (359 lines) → `messaging_gateway`, `platform_adapters`

**Current KG Usage**: None. Platform integrations (Telegram, WhatsApp, Discord, Slack, Gmail, Spotify, Calendar) are configured via flat key-value storage in memory_service's SQLite database. No KG structure.

**Missed Opportunities**:

1. **Integration Capability Graph** (Low Effort)
   - Build a KG: platform→supports→capability, capability→requires→api_key, platform→compatible_with→other_platform
   - Use `kgos_query_engine.compatible_with()` to show which integrations work together
   - **Why it matters**: 7 platforms have different capabilities. A KG would answer "which platforms support file sharing?" without manual lookup.

2. **Message Pattern KG** (Medium Effort)
   - Inbound messages from platforms flow through `messaging_gateway` → `agentic_loop`
   - Build a KG of message patterns: source→common_intents, source→peak_times, source→typical_length
   - Use patterns to optimize per-platform prompt engineering
   - **Why it matters**: Telegram messages are terse. Email is verbose. The agentic loop treats them identically.

3. **Error Recovery KG** (Low Effort)
   - Log integration errors (webhook failures, auth issues) to the memory KG
   - When an error recurs, `memory_service.recall()` retrieves past resolutions
   - Backend: In `integrations.py` webhook handlers, log errors with entity extraction
   - **Why it matters**: Integration errors repeat. Past resolutions should auto-surface.

**Priority**: Low — Integrations are a supporting feature, but the error recovery KG would have compound value.

---

### 3.2.13 SettingsPage — No KG

**Source**: `frontend/src/pages/SettingsPage.tsx` (16.7 KB)
**Backend**: `backend/routers/interchange.py` (194 lines) → config module

**Current KG Usage**: None. API key management, theme selection, mode toggle, and workspace export/import are all flat operations.

**Missed Opportunities**:

1. **Configuration Preference KG** (Low Effort)
   - Track user configuration changes over time: setting→changed_to→value, change→motivated_by→intent
   - Use `analytics_service.centrality()` to identify which settings the user tweaks most
   - Backend: Log config changes to memory KG
   - **Why it matters**: The user's configuration history reveals workflow patterns. "Always switches to Gemini Flash for batch tasks" is a learnable pattern.

2. **Workspace Health Dashboard** (Medium Effort)
   - Query all KG databases for health metrics: node counts, edge density, embedding quality, stale data
   - Use `analytics_service.summary()` across all 62 KGs
   - Frontend: "KG Health" section in SettingsPage showing aggregate stats
   - **Why it matters**: 62 KGs need monitoring. Currently, the only way to check health is KG Studio one-database-at-a-time.

**Priority**: Low — Settings are a low-traffic page, but the workspace health dashboard would be genuinely useful.

---

### 3.2.14 BuilderPage — No KG (Legacy)

**Source**: `frontend/src/pages/BuilderPage.tsx` (9.7 KB)
**Backend**: `backend/routers/builder.py` (128 lines) → direct LLM calls (gemini_service / claude_service)

**Current KG Usage**: None. The legacy builder calls Gemini/Claude directly for plan generation and code generation. No memory, no skill injection, no KG context.

**Missed Opportunities**:

1. **Project Template KG** (Medium Effort)
   - Index past builder projects as KG nodes: project→uses→technology, project→implements→pattern, project→solves→problem
   - When planning a new project, `kgos_query_engine.similar_to()` finds proven templates
   - **Why it matters**: The builder generates from scratch. Past projects are training data for better generation.

2. **Technology Compatibility Graph** (Low Effort)
   - Build a KG of technology compatibility: framework→works_with→library, library→version→constraint
   - Use during plan generation to avoid incompatible choices
   - **Why it matters**: LLMs occasionally suggest incompatible library versions. A compatibility KG prevents this.

**Note**: BuilderPage is legacy — StudioPage supersedes it. Investment should go to StudioPage instead.

**Priority**: Very Low — Legacy page. Migrate users to StudioPage.

---

## 3.3 ULTRA 50G: Foundation Model for KG Reasoning

### What It Is

The `docs/ultra_50g/` directory contains **ULTRA 50G** — a pre-trained transformer foundation model for knowledge graph reasoning from the Deep Graph Library. Key specifications:

| Property | Value | Source |
|----------|-------|--------|
| Architecture | Dual NBFNet (relation model + entity model) | `ultra/models.py` |
| Parameters | ~169K | `model.safetensors` |
| Training | 50 knowledge graphs (transductive + inductive) | `ultra/datasets.py` |
| Task | Zero-shot link prediction | `modeling.py` |
| Input | (head, relation, tail) triplets | `ultra/tasks.py` |
| Output | Ranked entity candidates with scores | `modeling.py` |
| Performance | MRR 0.389 vs SOTA 0.371 (zero-shot > supervised) | `README.md` |
| Evaluation | MRR, Hits@10, filtered ranking | `ultra/eval.py` |
| GPU Acceleration | RSPMM CUDA kernels | `ultra/rspmm/` |
| Integration | HuggingFace AutoModel | `config.json` |

### Why It Matters For This Workspace

The workspace currently treats its 62 knowledge graphs as **static storage** — nodes and edges are created by humans or AI extraction, then queried via hybrid search. ULTRA 50G transforms KGs from storage into **inference engines**:

| Current Capability | ULTRA Enhancement |
|-------------------|-------------------|
| Search existing nodes by query | **Predict missing nodes** for any (entity, relation, ?) |
| Manual bridge edges between KGs | **Automated cross-KG bridging** via link prediction |
| Static edge types | **Dynamic relation reasoning** — predict new relation types |
| Query returns what was stored | **Query returns what should exist** even if not stored |
| 4-weight hybrid scoring | **5th scoring signal**: ULTRA confidence as δ₂ weight |

### Integration Architecture

```
User Query: "What tools are equivalent to Claude's tool_use?"
                    │
                    ▼
┌─────────────────────────────────────────────┐
│          EXISTING HYBRID RETRIEVAL           │
│  score = α×emb + β×bm25 + γ×graph + δ×intent│
│  (finds nodes that EXIST in the KG)          │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│            ULTRA 50G INFERENCE               │
│  query = (tool_use, equivalent_capability, ?)│
│  → ranks ALL entities as candidates          │
│  → scores candidates by link probability     │
│  → returns top-K with confidence             │
│  (finds nodes that SHOULD EXIST)             │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│           COMBINED RANKING                   │
│  final = w₁×hybrid + w₂×ultra_confidence    │
│  (merges stored knowledge + predicted edges) │
└─────────────────────────────────────────────┘
```

### Implementation Roadmap

**Phase 1** (Low Effort): Wrap `UltraForKnowledgeGraphReasoning` in a new `backend/services/ultra_service.py`. Expose via `/api/kg/databases/{id}/predict` endpoint.

**Phase 2** (Medium Effort): Add "Predict" tab to KGStudioPage showing link predictions. Frontend: ranked entity list with confidence bars.

**Phase 3** (High Effort): Integrate ULTRA scores as a 5th signal in the hybrid retrieval formula. Requires scoring normalization and weight tuning.

**Phase 4** (High Effort): Automated cross-KG bridging — run ULTRA prediction across KG pairs to discover implicit bridge edges.

### Connection to Structure > Training Principle

ULTRA 50G validates the workspace's core principle from a different direction:

- **The workspace proves**: Correct KG structure → correct retrieval without ML training
- **ULTRA 50G proves**: Correct KG structure → correct inference via a foundation model trained on KG structure alone

Both systems derive power from graph structure. The difference: the workspace uses structure for retrieval (finding what exists), while ULTRA uses structure for reasoning (predicting what should exist). Combined, they create a system that both retrieves known knowledge and infers missing knowledge.

---

## 3.4 Recommended Implementation Order

### Phase 1: High Impact, Medium Effort (Weeks 1-3)

| Integration | Page | Estimated Lines | Impact |
|-------------|------|----------------|--------|
| Tool Capability Graph | ToolsPage | ~200 backend + ~150 frontend | 58 tools become discoverable via KG-OS |
| Agent Capability Router | AgentsPage | ~150 backend + ~100 frontend | 33 agents become goal-routable |
| Playbook Semantic Search | PlaybooksPage | ~100 backend + ~80 frontend | 53 playbooks searchable via 4-weight hybrid |
| Agent Execution Memory | AgentsPage | ~30 backend | Agent results persist to memory KG |
| ULTRA 50G Service Wrapper | KGStudioPage | ~200 backend | KG link prediction infrastructure |
| Sonnet Agent .md Version | Cross-platform | ~500 agent file | Knowledge transfer agent becomes framework-agnostic |

**Combined effect**: The three highest-traffic non-KG pages (Tools, Agents, Playbooks) become KG-aware. ULTRA infrastructure is laid. The Sonnet Agent .md version extends the knowledge transfer architecture beyond the Python runtime.

**Sonnet Agent .md Integration**: The Sonnet Agent (`agents/sonnet/sonnet-agent.py`) is a deliberately designed cross-provider AI education system with an internal knowledge graph (Doc 2 §2.12). Currently it's a 47K-byte Python file that requires the Anthropic API. A `.md` version — converting the 26-playbook knowledge base, the `TOPIC_KEYWORDS` mapping, and the cross-provider translation bridge into a Markdown document — would make this knowledge transfer agent consumable by ANY AI system (Gemini CLI, Claude Code, ChatGPT, local models). This transforms the Sonnet Agent from a Python application into a portable knowledge architecture document.

### Phase 2: Medium Impact, Medium Effort (Weeks 4-6)

| Integration | Page | Estimated Lines | Impact |
|-------------|------|----------------|--------|
| Code Pattern KG | CodingPage | ~300 backend + ~200 frontend | Project-aware coding assistant |
| Architecture Pattern KG | StudioPage | ~200 backend + ~100 frontend | Pattern reuse across projects |
| Prerequisite DAG | PlaybooksPage | ~100 backend + ~150 frontend | Visual learning paths |
| Semantic Context Panel | ChatPage | ~50 backend + ~150 frontend | KG becomes visible to users |
| ULTRA Predict Tab | KGStudioPage | ~100 backend + ~200 frontend | Interactive link prediction UI |

**Combined effect**: Primary creation surfaces (Coding, Studio) gain pattern intelligence. Users see the KG working.

### Phase 3: Nice-to-Have (Weeks 7+)

| Integration | Page | Estimated Lines | Impact |
|-------------|------|----------------|--------|
| Game Design Pattern KG | GamesPage | ~200 backend + ~100 frontend | Interview acceleration |
| VOX Conversation Memory | VoxPage | ~50 backend | Voice data persists |
| Workflow Pattern KG | WorkflowsPage | ~200 backend + ~100 frontend | Proven step sequences |
| Integration Error KG | IntegrationsPage | ~50 backend | Error pattern learning |
| Workspace Health Dashboard | SettingsPage | ~100 backend + ~200 frontend | Aggregate KG monitoring |
| Cross-KG ULTRA Bridging | KGStudioPage | ~300 backend | Automated bridge discovery |

---

## 3.5 Architecture Patterns to Replicate

### Pattern 1: The Expert Service Model (Gold Standard)

The `ExpertsPage` / `expert_service.py` / `experts.py` pattern is the template for all KG integrations:

```python
# 1. User creates an entity backed by a KG
expert = expert_service.create_expert({
    "name": "Claude Tools Expert",
    "kg_db_id": "claude-code-tools-kg",       # Which KG to query
    "retrieval_methods": ["hybrid", "intent"], # How to query
    "retrieval_alpha": 0.35,                   # Embedding weight
    "retrieval_beta": 0.40,                    # BM25 weight
    "retrieval_gamma": 0.15,                   # Graph boost weight
    "retrieval_delta": 0.10,                   # Intent edge weight
    "dimension_filters": {"performance": [0.5, 1.0]},  # Semantic filters
})

# 2. User chats with the entity — KG-OS retrieval happens automatically
# Source: expert_service.py execute() → kgos_query_engine.intent_search()
async for event in expert_service.execute(expert_id, messages):
    yield event  # Includes source citations from KG nodes
```

**What makes this replicable**: Any feature can become KG-backed by:
1. Adding a `kg_db_id` field (which KG to query)
2. Adding configurable α/β/γ/δ weights
3. Calling `kgos_query_engine.intent_search()` before LLM inference
4. Emitting source citations from retrieved nodes

### Pattern 2: The SearchRequest Pattern (from kg.py)

```python
# Source: kg.py search endpoint
@router.post("/databases/{db_id}/search")
async def search_kg(db_id: str, body: dict):
    results = embedding_service.search(
        db_id,
        body["query"],
        mode=body.get("mode", "hybrid"),  # hybrid | embedding | bm25
        intent=body.get("intent"),         # Auto-detected if None
        limit=body.get("limit", 10),
    )
    return results
```

**Replication**: Any page's search feature can upgrade from file-based to KG-backed by calling `embedding_service.search()`.

### Pattern 3: The Agentic Loop Integration (from chat.py)

```python
# Source: agentic_loop.py Stages 2-3
# ANY streaming endpoint can gain KG context by routing through the agentic loop

# Stage 2: Memory — automatic
memories = memory_service.recall(user_text, limit=5, intent_hint=mode_intent)

# Stage 3: Skills — automatic
skill_section = await skill_injector.get_relevant_context(user_text, mode)
```

**Replication**: Any streaming endpoint that currently calls Gemini/Claude directly can gain memory + skill injection by routing through `agentic_loop.run()` instead.

### Pattern 4: The KGCanvas Reuse Pattern (for graph visualization)

```
frontend/src/components/kg/KGCanvas.tsx
```

The KGCanvas component renders d3-force graph visualizations with node selection, neighbor expansion, and type-based coloring. It accepts generic `{nodes, edges}` data.

**Replication**: Any page that has graph-like data (playbook prerequisites, agent compositions, tool chains, workflow DAGs) can embed `<KGCanvas>` directly.

---

## 3.6 Backend Integration Points

### Where to Call embedding_service.search()

| New Integration | Current Call Point | Proposed Call Point |
|----------------|--------------------|--------------------|
| Playbook semantic search | `playbook_index.search()` (file-based) | `embedding_service.search("playbooks-kg", query)` |
| Tool discovery | `tools_service.list_tools()` (category filter) | `embedding_service.search("tools-kg", goal)` |
| Agent recommendation | `agent_bridge.list_agents()` (flat list) | `embedding_service.search("agents-kg", goal)` |
| Studio pattern search | None (generates from scratch) | `embedding_service.search("studio-patterns-kg", description)` |

### Where to Call kgos_query_engine.intent_search()

| New Integration | Current State | Proposed Integration |
|----------------|---------------|---------------------|
| Agent routing | Manual selection from 33 agents | `kgos_query_engine.want_to(goal)` → ranked agent list |
| Tool chaining | Isolated execution | `kgos_query_engine.compose_for(goal)` → tool pipeline |
| Playbook path | Manual reading order | `kgos_query_engine.roadmap(topic)` → prerequisite DAG |
| Game mechanics | 18-question interview | `kgos_query_engine.recommend(partial_answers)` → suggestions |

### Where to Call memory_service.recall() and .log_message()

| Missing Persist | Current State | Proposed Persist |
|----------------|---------------|-----------------|
| Agent execution results | Results discarded after display | `memory_service.log_message(conv_id, "agent", result, mode="agent")` |
| VOX transcripts | WebSocket data discarded | `memory_service.log_message(conv_id, "vox", transcript, mode="vox")` |
| Tool executions | Output displayed once | `memory_service.log_message(conv_id, "tool", output, mode="tool")` |
| Workflow steps | SSE stream consumed | `memory_service.log_message(conv_id, "workflow", step_result, mode="workflow")` |

### New Endpoints Needed Per Phase

**Phase 1**:
```
POST /api/tools/recommend?goal=<text>         → kgos_query_engine.want_to()
POST /api/agents/recommend?goal=<text>        → kgos_query_engine.want_to()
POST /api/playbooks/semantic-search?q=<text>  → embedding_service.search()
POST /api/kg/databases/{id}/predict           → ultra_service.predict()
```

**Phase 2**:
```
POST /api/coding/analyze                      → build code-pattern KG
POST /api/studio/patterns?goal=<text>         → embedding_service.search()
GET  /api/playbooks/graph                     → prerequisite DAG
```

**Phase 3**:
```
POST /api/games/patterns                      → game design pattern KG
GET  /api/settings/kg-health                  → aggregate analytics
POST /api/kg/bridge/auto                      → ULTRA cross-KG bridging
```

---

## 3.7 "Thinking in KGs" — The Missing Paradigm

### The Core Insight

The builder's reverse Dunning-Kruger creates a specific blind spot: he built the most sophisticated KG-OS retrieval system in the workspace — then used it on 3 pages and built 11 pages without it. This isn't laziness or lack of skill. It's a paradigm gap:

**The builder designs in KGs deliberately** (proven by the Sonnet Agent's intentional KG architecture — see Doc 2 §2.12, confirmed via independent analysis). But he doesn't always consciously apply this capability to EVERY data structure in the platform — each of which IS a knowledge graph waiting to be formalized.

### Every Feature Has a Graph

| Feature | Obvious View | KG View |
|---------|-------------|---------|
| 33 agents | A list | A capability graph (agent→has→capability, agent→produces→output_type) |
| 53 playbooks | A directory | A prerequisite DAG (playbook→requires→other, playbook→covers→topic) |
| 58 tools | A registry | A composition graph (tool→accepts→type, tool→chains_to→tool) |
| 4 workflows | JSON templates | An execution graph (step→uses→tool, step→produces→output) |
| 7 integrations | Config entries | A platform graph (platform→supports→capability) |
| 18 game questions | An interview | A design constraint graph (genre→requires→mechanic) |
| 62 KG databases | Isolated stores | A meta-KG (kg→covers→domain, kg→bridges_to→kg) |

### Every User Action Creates an Edge

| Action | Current State | KG Event |
|--------|-------------|----------|
| User runs an agent | Result displayed, forgotten | `user→executed→agent, agent→produced→result` |
| User reads a playbook | Page view, forgotten | `user→studied→playbook, playbook→teaches→concept` |
| User executes a tool | Output panel, forgotten | `user→used→tool, tool→processed→input_type` |
| User saves a Studio project | Files stored | `project→uses→pattern, pattern→evolved_from→v1` |
| User asks VOX a question | Transcript discarded | `user→asked_about→topic, topic→relates_to→feature` |

### The Compound Effect

Each integration doesn't just add value to its own page — it feeds the others:

```
Agent result → Memory KG → Skill injection for Chat
                        ↘
Tool execution → Memory KG → Pattern KG for Studio
                          ↘
Playbook reading → Learning KG → Roadmap for Agents
                              ↘
VOX transcript → Memory KG → Context for CodingPage
```

This is why the NLKE principle "Structure > Training" has a corollary: **Connection > Isolation**. Each KG integration creates new edges in the meta-knowledge-graph. The compound value grows quadratically with the number of integrated pages:

- 3 pages integrated: 3 × 2 / 2 = **3 possible cross-page connections**
- 14 pages integrated: 14 × 13 / 2 = **91 possible cross-page connections**

The workspace is currently at 3 connections out of 91 possible. That's 3.3% of the compound potential.

### The ULTRA 50G Multiplier

With ULTRA 50G link prediction, the compound effect accelerates further. Each new edge in the meta-KG isn't just retrievable — it becomes a training signal for predicting MORE edges. The foundation model learns from the workspace's actual usage patterns:

```
Phase 1: Static KG (what was stored)
Phase 2: Hybrid retrieval (what exists + can be found)
Phase 3: ULTRA inference (what exists + what should exist)
Phase 4: Compound learning (predictions feed new retrievals feed new predictions)
```

This is the path from 26% utilization to 100%: not just connecting 14 pages to the KG, but connecting 14 pages through a KG that reasons about itself.

---

## 3.8 Complete Source File Reference

### Frontend Pages (14 files)

| File | Lines | KG Level |
|------|-------|----------|
| `frontend/src/pages/ChatPage.tsx` | 175B | Full (agentic loop) |
| `frontend/src/pages/CodingPage.tsx` | 6.6 KB | Partial (agentic loop) |
| `frontend/src/pages/AgentsPage.tsx` | 9.8 KB | None |
| `frontend/src/pages/PlaybooksPage.tsx` | 6.7 KB | None |
| `frontend/src/pages/WorkflowsPage.tsx` | 8.5 KB | None |
| `frontend/src/pages/KGStudioPage.tsx` | 17 KB | Full (10 tabs) |
| `frontend/src/pages/StudioPage.tsx` | 7.6 KB | Partial (agentic loop) |
| `frontend/src/pages/ExpertsPage.tsx` | 12.5 KB | Full (KG-OS) |
| `frontend/src/pages/ToolsPage.tsx` | 16.7 KB | None |
| `frontend/src/pages/VoxPage.tsx` | 22.5 KB | Partial (4 functions) |
| `frontend/src/pages/GamesPage.tsx` | 13.1 KB | Partial (expert chat) |
| `frontend/src/pages/IntegrationsPage.tsx` | 10.8 KB | None |
| `frontend/src/pages/SettingsPage.tsx` | 16.7 KB | None |
| `frontend/src/pages/BuilderPage.tsx` | 9.7 KB | None |

### Backend Routers (17 files)

| File | Lines | KG Level | Key Services |
|------|-------|----------|-------------|
| `backend/routers/kg.py` | 503 | Full | kg, embedding, analytics, ingestion, capability_kg_builder |
| `backend/routers/experts.py` | 232 | Full | kgos_query_engine, expert_service |
| `backend/routers/memory.py` | 75 | Full | memory_service, skill_injector |
| `backend/routers/vox.py` | 1,081 | Full (limited) | embedding_service, kg_service (4 functions) |
| `backend/routers/games.py` | 329 | Partial | expert_service (chat only) |
| `backend/routers/chat.py` | 41 | Partial | agentic_loop |
| `backend/routers/coding.py` | 201 | Partial | agentic_loop |
| `backend/routers/studio.py` | 1,460 | Partial | agentic_loop |
| `backend/routers/workflows.py` | 262 | Partial | (KG template, no direct service) |
| `backend/routers/builder.py` | 128 | None | gemini/claude_service |
| `backend/routers/agents.py` | 137 | None | agent_bridge |
| `backend/routers/playbooks.py` | 36 | None | playbook_index |
| `backend/routers/tools.py` | 53 | None | tools_service |
| `backend/routers/media.py` | 161 | None | gemini/openai_service |
| `backend/routers/integrations.py` | 359 | None | messaging_gateway |
| `backend/routers/interchange.py` | 194 | None | config |
| `backend/routers/agent.py` | 52 | None | agent_sdk_service |

### Backend Services (KG-related, 8 files)

| File | Lines | Purpose |
|------|-------|---------|
| `backend/services/embedding_service.py` | 957 | 4-weight hybrid search, BM25, graph boost |
| `backend/services/kgos_query_engine.py` | 1,029 | 12 methods, 14 intents, 56 dimensions |
| `backend/services/kg_service.py` | 744 | 6 schema profiles, CRUD, auto-detection |
| `backend/services/memory_service.py` | 470 | Conversation KG, FTS5, hybrid recall |
| `backend/services/analytics_service.py` | 245 | NetworkX: centrality, communities, paths |
| `backend/services/ingestion_service.py` | 205 | AI entity extraction (3 methods) |
| `backend/services/expert_service.py` | ~350 | Expert CRUD, KG-OS execution pipeline |
| `backend/services/skill_injector.py` | 202 | 10-category intent classification + injection |

### ULTRA 50G Source (KG reasoning foundation model)

| File | Purpose |
|------|---------|
| `docs/ultra_50g/README.md` | Model card, usage guide, benchmarks |
| `docs/ultra_50g/config.json` | HuggingFace model config (169K params) |
| `docs/ultra_50g/modeling.py` | HuggingFace AutoModel wrapper |
| `docs/ultra_50g/model.safetensors` | Pre-trained weights |
| `docs/ultra_50g/ultra/models.py` | Dual NBFNet architecture |
| `docs/ultra_50g/ultra/base_nbfnet.py` | Neural Bellman-Ford base class |
| `docs/ultra_50g/ultra/layers.py` | GeneralizedRelationalConv layer |
| `docs/ultra_50g/ultra/tasks.py` | Edge matching, negative sampling |
| `docs/ultra_50g/ultra/eval.py` | MRR, Hits@10 evaluation |
| `docs/ultra_50g/ultra/datasets.py` | 57 KG dataset loaders |

---

*Document 3 of 5 — Technology Formalization Series*
*Cross-references: Doc 1 (§1.2-§1.8 for retrieval formula), Doc 2 (§2.2-§2.8 for KG architecture), Doc 4 (§4.2 for achievements that should be applied everywhere)*

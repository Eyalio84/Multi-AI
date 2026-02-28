# VOX Jarvis-Mode Implementation — Context Preservation Packet
# Generated: 2026-02-28_11-00
# Purpose: Complete architectural state snapshot for Phase 1-7 implementation

---

## Mission Summary

Upgrade VOX from a 34-function voice assistant to a Jarvis-mode intelligent voice system with 100+ functions, persistent singleton state, News Hub, persona system, self-aware changelog, scheduling, analytics, and comprehensive tests. 7 sequential phases, each accumulating compound insights from an insights document (`docs/feb28-2026-insights.txt`).

**Methodology**: After each phase, use extended thinking to analyze accumulated insights, evaluate which enhance the next phase, and integrate high-impact ones. This is the Compound Intelligence methodology from `docs/firmalize/05-EMERGENT.md` — don't force connections, let insights emerge from the implementation process.

---

## Plan File

**Location**: `/root/.claude/plans/purring-sprouting-pinwheel.md`
**Status**: APPROVED by user
**Content**: Full 7-phase VOX Jarvis-Mode plan with file-level detail

---

## Insights Document

**Location**: `/storage/self/primary/Download/gemini-3-pro/multi-ai-agentic-workspace/docs/feb28-2026-insights.txt`
**Protocol**: Log insights during each phase. At phase completion, analyze with extended thinking, evaluate which compound insights enhance the next phase.

---

## 7-Phase Implementation Order (SEQUENTIAL, NO PARALLEL)

| Phase | Focus | Key Deliverables | Est. Lines |
|-------|-------|-----------------|------------|
| 1 | Core Refactor | `voxCore.ts` singleton, `vox_registry.py`, overlay 3-state, `useVox.ts` thin wrapper | ~700 |
| 2 | Expanded Functions | 16 function modules in `vox_functions/`, 104 functions total | ~1,200 |
| 3 | Context + Memory + Multi-Model | Memory persistence, page-KG routing, model config | ~500 |
| 4 | Tours + Personas + Error Recovery | `vox_personas.py`, autonomous tours, cascade fallback | ~500 |
| 5 | News Hub | `news_service.py`, `news_parsers.py`, `scheduler_service.py`, `NewsPage.tsx`, `news.py` router | ~1,800 |
| 6 | Automation + Analytics + Config | `vox_analytics.py`, VoxPage 7 tabs, model config UI | ~600 |
| 7 | Changelog + Accessibility + Tests | `vox_changelog.md`, `vox_accessibility.py`, `vox_wake_word.py`, 7 test files | ~1,100 |

---

## Firmalize Engineering Principles (Apply Throughout)

From `docs/firmalize/05-EMERGENT.md`:

1. **Cascade Architecture** — VOX fallback: Gemini Live -> Claude text -> local TTS -> text-only
2. **Orthogonal Signal Fusion (Color Mixing)** — Each function covers DIFFERENT intent space
3. **Structure > Training** — News Hub uses structured retrieval (4-weight formula)
4. **Connection > Isolation** — VOX as cross-page KG connector = highest-leverage integration
5. **Constraint as Generator** — Mobile constraints inspire innovations
6. **Strategic Context Withholding (90%/10%)** — VOX provides targeted, not exhaustive responses

From `docs/firmalize/03-INTEGRATION-OPPORTUNITY-MAP.md` Section 3.2.10:
- Only 4/34 current functions access KGs
- VOX transcripts are DISCARDED — must feed `memory_service`
- Missing: Voice Macro KG, Context-Aware KG Routing, Conversation Memory persistence

---

## Working Directory

```
/storage/self/primary/Download/gemini-3-pro/multi-ai-agentic-workspace
```

## Git State

- **Branch**: main
- **Last commit**: `74d7d97` — Remove API key from tracking
- **Untracked**: `docs/feb28-2026-insights.txt`, `docs/Tiny RPG Character Asset Pack/`
- **Clean**: All other files committed
- **GitHub**: https://github.com/Eyalio84/Multi-AI
- **Token**: `docs/git-token.txt`
- **CRITICAL**: NEVER add `Co-Authored-By Claude` to commits — Eyal is sole author

---

## Current VOX Architecture (BEFORE Modifications)

### Backend Files (2,374 lines total)

| File | Lines | Purpose |
|------|-------|---------|
| `backend/services/vox_service.py` | 680 | VoxSession dataclass, 34 function declarations, 16 voices, system instruction builder |
| `backend/routers/vox.py` | 1,081 | REST + WebSocket, `_execute_server_function()` 288-line if/elif, Claude pipeline |
| `backend/services/vox_awareness.py` | 208 | SQLite (page_visits, error_log, session_context), `build_awareness_prompt()` |
| `backend/services/vox_macros.py` | 324 | SQLite macro CRUD, pipe-chaining, error policies |
| `backend/services/vox_thermal.py` | 81 | Termux battery API, 42C threshold |
| `backend/data/vox_tours.json` | 248 | 11 tour definitions with CSS selectors |

### Frontend Files (1,712 lines total)

| File | Lines | Purpose |
|------|-------|---------|
| `frontend/src/hooks/useVox.ts` | 676 | ALL state + WebSocket + audio pipeline + 6 browser functions |
| `frontend/src/components/VoxOverlay.tsx` | 245 | Fixed pill z-50, expanded panel |
| `frontend/src/pages/VoxPage.tsx` | 511 | 4 tabs: Transcript, Controls, Log, Macros |
| `frontend/src/components/VoxTourOverlay.tsx` | 236 | CSS spotlight z-10000-10002 |
| `frontend/src/context/VoxContext.tsx` | 44 | React Context provider wrapping useVox |
| `frontend/src/types/vox.ts` | 44 | VoxState, VoxTranscriptEntry, VoxFunctionEntry, VoxConfig, VoxVoice, VoxMode |

### Key Data Structures

**VoxSession** (`vox_service.py:30-43`):
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
    gemini_ctx: Any = None
    turn_count: int = 0
    function_count: int = 0
    session_token: Optional[str] = None
```

**VoxState** (`types/vox.ts`):
```typescript
interface VoxState {
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
```

### Key Code Locations

| What | File | Line(s) |
|------|------|---------|
| If/elif dispatch (TO REPLACE) | `backend/routers/vox.py` | 354-650 |
| BROWSER_FUNCTIONS set | `backend/routers/vox.py` | 657-660 |
| ASYNC_FUNCTIONS set | `backend/routers/vox.py` | 351 |
| WebSocket handler | `backend/routers/vox.py` | 665-1081 |
| `_gemini_receive_loop` | `backend/routers/vox.py` | ~760 |
| `_claude_text_pipeline` | `backend/routers/vox.py` | ~900 |
| `build_function_declarations()` | `backend/services/vox_service.py` | ~60-500 |
| `build_system_instruction()` | `backend/services/vox_service.py` | ~500-680 |
| useVox hook (TO GUT) | `frontend/src/hooks/useVox.ts` | 1-676 |
| Audio capture (16kHz) | `frontend/src/hooks/useVox.ts` | ~200-300 |
| Audio playback (24kHz) | `frontend/src/hooks/useVox.ts` | ~300-400 |
| Browser functions (6) | `frontend/src/hooks/useVox.ts` | ~400-500 |
| Auto-reconnect logic | `frontend/src/hooks/useVox.ts` | ~500-600 |
| VoxOverlay pill | `frontend/src/components/VoxOverlay.tsx` | 1-245 |
| VoxPage 4 tabs | `frontend/src/pages/VoxPage.tsx` | 1-511 |
| Tour spotlight | `frontend/src/components/VoxTourOverlay.tsx` | 1-236 |
| VoxProvider in App.tsx | `frontend/src/App.tsx` | ~line 60-75 |

### API Endpoints (Current)

```
GET  /api/vox/status           — Availability check
GET  /api/vox/voices           — 16 Gemini voices
GET  /api/vox/functions        — 34 function declarations
POST /api/vox/function/{name}  — Execute workspace function
POST /api/vox/awareness        — Log page visit/error/context
GET  /api/vox/awareness        — Get awareness context
GET  /api/vox/tours            — List 11 tours
GET  /api/vox/tours/{page}     — Get tour steps
GET  /api/vox/macros           — List macros
POST /api/vox/macros           — Create macro
DEL  /api/vox/macros/{id}      — Delete macro
POST /api/vox/macros/{id}/run  — Execute macro
GET  /api/vox/thermal          — Temperature + battery
WS   /ws/vox                   — Bidirectional voice WebSocket
```

---

## AI-LAB Reference (Pattern Source)

**Location**: `/storage/emulated/0/Download/gemini-3-pro/AI-LAB/`

### Key Patterns to Port

1. **Module-level singleton state** (`AI-LAB/frontend/src/composables/useVox.js`, 602 lines):
   - `const connected = ref(false)` at module scope (Vue refs, translate to plain JS variables)
   - `let ws = null` for non-reactive internals
   - Exported function API: `connect()`, `disconnect()`, `toggleListening()`, `sendText()`
   - State survives all router navigation because it's at module scope, not component scope

2. **19 browser functions** (vs our current 6):
   - navigate, click_element, scroll_to_element, highlight_element, toggle_dropdown
   - read_content, get_page_state, fill_form, capture_screenshot, etc.

3. **118 function declarations** (vs our 34):
   - Organized in 16 categories
   - Non-blocking execution for slow functions (asyncio.create_task)

4. **Session resumption** via `session_token`
5. **Context window compression** after 400 turns (we'll use 200 for mobile)
6. **VoxOverlay outside RouterView** (we already do this in App.tsx)

---

## Related Services (Untouched but Interacted With)

| Service | Lines | VOX Integration Point |
|---------|-------|-----------------------|
| `memory_service.py` | 470 | Phase 3: persist VOX transcripts |
| `embedding_service.py` | 956 | Phase 5: News Hub hybrid search uses 4-weight formula |
| `agentic_loop.py` | 491 | Phase 3: `deep_think` function routing |
| `kgos_query_engine.py` | 1,028 | Phase 2: KG query functions |
| `kg_service.py` | 744 | Phase 2: KG CRUD functions |
| `expert_service.py` | 450 | Phase 2: Expert functions |
| `tools_service.py` | 1,019 | Phase 2: Tool functions |
| `skill_injector.py` | 201 | Phase 3: Context enrichment |
| `config.py` | 436 | API keys, model catalog |

---

## Full Codebase Stats

| Layer | Files | Lines |
|-------|-------|-------|
| Backend services | 33 files | 14,285 |
| Backend routers | 17 files | 5,304 |
| Frontend pages | 14 files | 3,683 |
| Frontend hooks | 4 files | ~1,000 |
| Frontend types | 11 files | ~500 |
| Frontend services | 3 files | ~1,200 |
| KG databases | 62 DBs | (docs/KGS/) |

---

## Package Dependencies

### Installed
- fastapi 0.128.6, uvicorn 0.40.0
- google-genai 1.64.0, anthropic 0.83.0, openai 2.24.0
- httpx 0.28.1, aiohttp 3.11.16
- numpy 2.2.4
- beautifulsoup4 4.14.3

### NOT Installed (Needed for Phases 5-6)
- **apscheduler** — `pip install --break-system-packages apscheduler` (Phase 5: scheduler)
- **feedparser** — `pip install --break-system-packages feedparser` (Phase 5: RSS parsing)
- **networkx** — `pip install --break-system-packages networkx` (in requirements.txt but not installed; needed for analytics_service.py)

### Frontend Build
```bash
cd frontend
ESBUILD_BINARY_PATH=/data/data/com.termux/files/usr/tmp/esbuild-native/esbuild npm run build
```

---

## Frontend Architecture Notes

- **App.tsx** (80 lines): VoxProvider wraps BrowserRouter, VoxOverlay + VoxTourBridge are siblings of Routes (same level, not inside)
- **NavBar.tsx** (113 lines): 13 nav links + ThemeSwitcher + settings gear
- **CSS variable pattern**: All components use `style={{ background: 'var(--t-surface)' }}` for theming
- **5 themes**: default, crt, scratch, solarized, sunset
- **API base**: `${window.location.protocol}//${window.location.hostname}:8088` (port 8088 in useVox, 8000 elsewhere — CHECK for consistency)
- **WebSocket base**: `ws://${hostname}:8088/ws/vox`

---

## Phase 1 Quick Start

When beginning Phase 1, read these files in order:
1. This context packet (you're reading it)
2. The plan file: `/root/.claude/plans/purring-sprouting-pinwheel.md` (Phase 1 section)
3. `backend/services/vox_service.py` — understand VoxSession and function declarations
4. `backend/routers/vox.py` — understand the if/elif dispatch to replace (lines 354-650)
5. `frontend/src/hooks/useVox.ts` — understand state + audio to extract into voxCore.ts
6. `frontend/src/components/VoxOverlay.tsx` — understand current overlay to upgrade
7. `frontend/src/types/vox.ts` — understand current type definitions

Phase 1 creates:
- `frontend/src/services/voxCore.ts` (~300 lines) — module-level singleton
- `backend/services/vox_registry.py` (~200 lines) — decorator registry

Phase 1 modifies:
- `frontend/src/hooks/useVox.ts` — gut from 676 to ~150 lines (thin React wrapper)
- `frontend/src/components/VoxOverlay.tsx` — 3-state "V" button
- `backend/routers/vox.py` — replace if/elif with `vox_registry.execute()`
- `backend/services/vox_service.py` — use registry for declarations

---

## User Context

- **Eyal Nof** — Self-taught systems architect, 6000+ hours, ADHD lateral thinking
- Wants FACTS not confirmation. Reverse Dunning-Kruger.
- NEVER add Co-Authored-By Claude to commits
- Platform: Android/Termux PRoot (Linux 6.17.0-PRoot-Distro)
- `find` unreliable on this platform — use `ls` instead
- `/storage/self/primary/` = `/storage/emulated/0/` (same filesystem)

---

## Commit Strategy

After each phase:
- Stage only phase-relevant files by name (no `git add -A`)
- Commit message: `VOX Jarvis Phase N: <description>`
- Do NOT push unless user requests it

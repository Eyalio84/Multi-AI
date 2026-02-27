# Context Packet: SDK Integration + Full Model Catalog
**Date**: 2026-02-27
**Status**: Research complete, user approved steps 1-4 for plan mode
**Action**: Enter plan mode for steps 1-4 immediately after compact

---

## What Was Accomplished This Session

### Fixes Deployed (all compile clean, frontend running on 5178)
1. **Chat persistence fix** — `StudioContext.tsx:344` changed `chatHistory: messages` to `chat_history: messages` (backend expects snake_case)
2. **Thinking token display** — Added `streamingThinking` state to StudioContext, captures `type: 'thinking'` SSE events instead of discarding. Shows live thinking with spinning icon during streaming, collapsible "Thought process" section on completed messages
3. Files modified: `StudioContext.tsx`, `StudioChatPanel.tsx`, `StudioMessageItem.tsx`, `types/studio.ts`

### SDK Research Findings

**Current stack:**
- Gemini: `google-genai` SDK (`from google import genai`), API key based
- Claude: `anthropic` SDK, API key based

**Claude Agent SDK** (`claude-agent-sdk`):
- Claude Code as a Python/TypeScript library
- Built-in tools: Read, Write, Edit, Bash, Glob, Grep, WebSearch, WebFetch, AskUserQuestion
- Features: subagents, sessions, hooks (PreToolUse/PostToolUse/Stop), MCP, permissions
- Install: `pip install claude-agent-sdk`
- Auth: Uses `ANTHROPIC_API_KEY` (existing key works)
- API: `async for message in query(prompt="...", options=ClaudeAgentOptions(allowed_tools=[...])):`
- Can also auth via Vertex (`CLAUDE_CODE_USE_VERTEX=1`) or Bedrock (`CLAUDE_CODE_USE_BEDROCK=1`)

**Google Gen AI SDK** (`google-genai`):
- Already installed, already supports ALL media generation models
- No Vertex SDK needed — API key works for image gen, video gen, music gen
- Just need to call the right model IDs

**Vertex AI (NOT needed now):**
- Unifies billing for both Claude + Gemini under one Google Cloud account
- Claude on Vertex: `pip install anthropic[vertex]`, uses Google Cloud creds, NOT Anthropic API key
- More setup complexity (GCP project, gcloud auth, billing)
- 10% premium on regional endpoints
- Future/enterprise option

---

## Approved Plan: Steps 1-4 (Enter Plan Mode For These)

### Step 1: Install Claude Agent SDK + Full Model Catalog Update

**Install:**
```bash
pip install claude-agent-sdk
```

**Full Gemini Model Catalog (leave none behind):**

| Model ID | Category | Purpose |
|----------|----------|---------|
| `gemini-3.1-pro-preview` | Text | Flagship agentic, best thinking + tool use |
| `gemini-3.1-pro-preview-customtools` | Text | Prioritizes custom tools over bash |
| `gemini-3-pro-preview` | Text | State-of-the-art reasoning |
| `gemini-3-flash-preview` | Text | Frontier-class, fraction of cost |
| `gemini-2.5-pro` | Text | Deep reasoning + coding (stable) |
| `gemini-2.5-flash` | Text | Fast budget reasoning (stable) |
| `gemini-2.5-flash-lite` | Text | Fastest, cheapest multimodal |
| `gemini-3-pro-image-preview` | Image | Nano Banana Pro — studio-quality 4K gen+edit |
| `gemini-2.5-flash-image` | Image | Nano Banana — fast image gen+edit |
| `imagen-4.0-generate-preview-05-20` | Image | Imagen 4 — text-to-image 2K |
| `veo-3.1-generate-preview` | Video | Cinematic 4K video + sync audio |
| `veo-3.1-fast-generate-preview` | Video | Fast video generation |
| `gemini-2.5-flash-native-audio-preview` | Audio | Live API, bidirectional voice |
| `gemini-2.5-flash-preview-tts` | Audio | Text-to-speech, controllable |
| `gemini-2.5-pro-preview-tts` | Audio | High-fidelity TTS (podcasts) |
| `lyria-realtime-exp` | Music | Music generation, 48kHz stereo PCM |
| `gemini-embedding-001` | Embedding | High-dimensional vectors for search |
| `gemini-2.5-computer-use-preview` | Agent | Screen vision + UI automation |
| `deep-research-pro-preview` | Agent | Multi-step autonomous research |
| `gemini-robotics-er-1.5-preview` | Specialized | Embodied reasoning for robotics |

**Claude Models:**

| Model ID | Purpose |
|----------|---------|
| `claude-opus-4-6` | Most intelligent, agents + coding |
| `claude-sonnet-4-6` | Fast + capable |
| `claude-haiku-4-5-20251001` | Budget, fastest |

### Step 2: Build Backend Service for Claude Agent SDK

Create `services/agent_sdk_service.py`:
- Wrap `claude-agent-sdk`'s `query()` function
- Give Claude autonomous file system access (Read, Write, Edit, Bash, Glob, Grep)
- Handle sessions (resume context across interactions)
- Configure permissions (what tools Claude can use)
- Hook into existing workspace (awareness of project structure)

Create router endpoint:
- `POST /api/agent/run` — run an autonomous Claude agent task
- SSE streaming of agent messages back to frontend

### Step 3: Update gemini_service.py for Media Generation

Add methods to `gemini_service.py`:
- `generate_image(prompt, model, ...)` — Nano Banana Pro / Nano Banana / Imagen 4
- `edit_image(image, prompt, model, ...)` — image editing via Nano Banana
- `generate_video(prompt, model, ...)` — Veo 3.1 / Veo 3.1 Fast
- `generate_music(prompt, model, ...)` — Lyria
- `generate_tts(text, model, ...)` — Flash TTS / Pro TTS

Add router endpoints:
- `POST /api/media/image/generate`
- `POST /api/media/image/edit`
- `POST /api/media/video/generate`
- `POST /api/media/music/generate`
- `POST /api/media/tts/generate`

### Step 4: Verify End-to-End

- Test Claude Agent SDK: file read/write on local storage, bash execution
- Test Gemini image gen: call Nano Banana Pro with a prompt
- Test Gemini video gen: call Veo 3.1
- Test Gemini music gen: call Lyria
- Confirm all model IDs accessible via updated catalog
- TypeScript compiles clean, both servers running

---

## Future Steps (SEPARATE brainstorming sessions, NOT part of current plan)

### Step 5: Autonomous Model-Update Agent (separate brainstorm)
- Weekly scheduled check of Anthropic + Google model pages
- Fetch documentation for any new releases
- Auto-update model catalog in config.py
- Generate summary of what's new, save to local storage location
- UI notification/indicator when new models detected
- Could use Claude Agent SDK itself to build this agent

### Step 6: 3 Creative Studio Pages (separate brainstorm)
- **Image Studio**: Nano Banana Pro + Nano Banana + Imagen 4 — generation, editing, manipulation
- **Video Studio**: Veo 3.1 — cinematic video creation with sync audio
- **Sound Studio**: Lyria — music production, instrument control, BPM

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `backend/config.py` | Model catalog, API keys, paths |
| `backend/services/gemini_service.py` | Gemini SDK wrapper (google-genai) |
| `backend/services/claude_service.py` | Claude SDK wrapper (anthropic) |
| `backend/services/vox_service.py` | VOX voice agent (34 functions) |
| `frontend/src/context/StudioContext.tsx` | Studio state (just fixed chat persistence + thinking) |
| `frontend/src/components/studio/StudioPreviewPanel.tsx` | Sandpack preview (has shim system) |
| `frontend/src/components/studio/StudioChatPanel.tsx` | Chat panel (just added thinking display) |
| `frontend/src/components/studio/StudioMessageItem.tsx` | Message renderer (just added thinking collapsible) |
| `/storage/emulated/0/gemini-models.txt` | Full Gemini model list from official page |

## Ports
- Backend: 8088 (or 8000 default)
- Frontend: 5178

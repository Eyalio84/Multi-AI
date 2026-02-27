# Multi-AI Agentic Workspace -- Technical Reference (Part 1B)

## Part 1 (continued): VOX Voice Agent -- Sections 1.6 through 1.11

---

### 1.6 VoxService Class

The `VoxService` class in `backend/services/vox_service.py` manages all VOX voice sessions. It is instantiated as a singleton at module level:

```python
vox_service = VoxService()
```

**Full class implementation (verbatim):**

```python
class VoxService:
    """Manages VOX voice sessions."""

    def __init__(self):
        self.sessions: dict[str, VoxSession] = {}
        self._client = None
        self._client_key = None

    def _get_client(self):
        from config import GEMINI_API_KEY as key
        if not key:
            raise ValueError("GEMINI_API_KEY not configured")
        if self._client is None or self._client_key != key:
            self._client = genai.Client(api_key=key)
            self._client_key = key
        return self._client

    async def create_gemini_session(
        self,
        model: str = VOX_DEFAULT_MODEL,
        voice: str = VOX_DEFAULT_VOICE,
        custom_prompt: str = "",
        session_token: Optional[str] = None,
    ) -> VoxSession:
        """Create a Gemini Live API voice session."""
        client = self._get_client()
        session_id = str(uuid.uuid4())[:8]
        system_prompt = build_system_instruction(custom_prompt)
        declarations = build_function_declarations()

        # Build Gemini FunctionDeclaration objects
        fn_decls = []
        for d in declarations:
            fn_decls.append(types.FunctionDeclaration(
                name=d["name"],
                description=d.get("description", ""),
                parameters=d.get("parameters"),
            ))

        # Live API config with Google Search grounding + transcription
        live_config = types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=voice
                    )
                )
            ),
            system_instruction=system_prompt,
            tools=[
                types.Tool(function_declarations=fn_decls),
                types.Tool(google_search=types.GoogleSearch()),
            ],
            context_window_compression=types.ContextWindowCompressionConfig(
                sliding_window=types.SlidingWindow(),
            ),
            input_audio_transcription=types.AudioTranscriptionConfig(),
            output_audio_transcription=types.AudioTranscriptionConfig(),
        )

        # Add session resumption if we have a token
        if session_token:
            live_config.session_resumption = types.SessionResumptionConfig(
                handle=session_token
            )
        else:
            live_config.session_resumption = types.SessionResumptionConfig()

        # Connect to Gemini Live API (async context manager)
        ctx = client.aio.live.connect(
            model=model,
            config=live_config,
        )
        gemini_session = await ctx.__aenter__()

        session = VoxSession(
            session_id=session_id,
            mode="gemini",
            model=model,
            voice=voice,
            created_at=time.time(),
            system_instruction=system_prompt,
            tools=declarations,
            gemini_session=gemini_session,
            gemini_ctx=ctx,
            session_token=session_token,
        )
        self.sessions[session_id] = session
        return session

    def create_claude_session(
        self,
        model: str = "claude-sonnet-4-6",
        custom_prompt: str = "",
    ) -> VoxSession:
        """Create a Claude text pipeline session (browser handles STT/TTS)."""
        session_id = str(uuid.uuid4())[:8]
        system_prompt = build_system_instruction(custom_prompt)

        session = VoxSession(
            session_id=session_id,
            mode="claude",
            model=model,
            voice="browser",
            created_at=time.time(),
            system_instruction=system_prompt,
            tools=build_function_declarations(),
        )
        self.sessions[session_id] = session
        return session

    async def send_audio(self, session_id: str, audio_b64: str):
        """Send PCM audio chunk to Gemini Live API session."""
        session = self.sessions.get(session_id)
        if not session or session.mode != "gemini" or not session.gemini_session:
            return
        audio_bytes = base64.b64decode(audio_b64)
        await session.gemini_session.send_realtime_input(
            audio=types.Blob(data=audio_bytes, mime_type="audio/pcm;rate=16000")
        )

    async def send_text(self, session_id: str, text: str):
        """Send text content to a Gemini Live session."""
        session = self.sessions.get(session_id)
        if not session or not session.gemini_session:
            return
        await session.gemini_session.send_client_content(
            turns=types.Content(role="user", parts=[types.Part(text=text)])
        )

    async def send_function_result(
        self, session_id: str, fn_id: str, name: str, result: dict
    ):
        """Send a function call result back to Gemini."""
        session = self.sessions.get(session_id)
        if not session or session.mode != "gemini" or not session.gemini_session:
            return
        fr_kwargs = {"name": name, "response": result}
        if fn_id:
            fr_kwargs["id"] = fn_id
        await session.gemini_session.send_tool_response(
            function_responses=[types.FunctionResponse(**fr_kwargs)]
        )

    async def close_session(self, session_id: str):
        """Clean up a voice session."""
        session = self.sessions.pop(session_id, None)
        if not session:
            return
        if session.gemini_ctx:
            try:
                await session.gemini_ctx.__aexit__(None, None, None)
            except Exception:
                pass
        elif session.gemini_session:
            try:
                await session.gemini_session.close()
            except Exception:
                pass

    def get_session(self, session_id: str) -> Optional[VoxSession]:
        return self.sessions.get(session_id)

    def is_gemini_available(self) -> bool:
        from config import GEMINI_API_KEY
        return bool(GEMINI_API_KEY)

    def is_claude_available(self) -> bool:
        from config import ANTHROPIC_API_KEY, MODE
        return MODE == "standalone" and bool(ANTHROPIC_API_KEY)
```

**Key implementation details:**

1. **Lazy client initialization**: `_get_client()` creates the `genai.Client` only on first use and caches it. If the API key changes at runtime (via `POST /api/config/keys`), the client is re-created.

2. **LiveConnectConfig** includes:
   - `response_modalities=["AUDIO"]` -- Gemini responds with audio
   - `speech_config` -- Selects the voice by name
   - Two `Tool` entries: one for function declarations, one for `GoogleSearch` grounding
   - `context_window_compression` with `SlidingWindow` -- automatic context management for long sessions
   - `input_audio_transcription` and `output_audio_transcription` -- enables transcripts of both user speech and model speech
   - `session_resumption` -- enables session resume after disconnection using a token

3. **Async context manager**: The Gemini Live API connection is opened as an async context manager (`client.aio.live.connect()`). The context manager's `__aenter__` is called manually to get the session object. On cleanup, `__aexit__` is called in `close_session()`.

4. **Claude sessions** are lightweight: no persistent connection, no audio. The Claude text pipeline is invoked per-message in `_claude_text_pipeline()`.

---

### 1.7 VOX Router

The VOX router (`backend/routers/vox.py`) provides 14 REST endpoints and 1 WebSocket endpoint.

#### GET /api/vox/voices

Returns the list of 16 available Gemini Live API voices.

```python
@router.get("/api/vox/voices")
async def list_voices():
    """List available Gemini Live API voices."""
    return {"voices": GEMINI_VOICES}
```

**Response:**
```json
{
  "voices": [
    {"id": "Puck", "name": "Puck", "gender": "Male", "style": "Upbeat, lively"},
    {"id": "Charon", "name": "Charon", "gender": "Male", "style": "Informative, steady"},
    ...
  ]
}
```

#### GET /api/vox/status

Checks VOX availability based on configured API keys.

```python
@router.get("/api/vox/status")
async def vox_status():
    return {
        "gemini_available": vox_service.is_gemini_available(),
        "claude_available": vox_service.is_claude_available(),
        "active_sessions": len(vox_service.sessions),
    }
```

#### GET /api/vox/functions

Lists all 34 workspace function declarations.

```python
@router.get("/api/vox/functions")
async def list_functions():
    fns = build_function_declarations()
    return {"functions": fns, "count": len(fns)}
```

#### POST /api/vox/function/{fn_name}

Runs a workspace function server-side with provided arguments.

```python
class FunctionRunRequest(BaseModel):
    args: dict = {}

@router.post("/api/vox/function/{fn_name}")
async def run_function(fn_name: str, req: FunctionRunRequest):
    result = await _execute_server_function(fn_name, req.args)
    return {"name": fn_name, "result": result}
```

#### POST /api/vox/awareness

Receives page visit, error, or context events from the frontend.

```python
class AwarenessEvent(BaseModel):
    event_type: str  # "page_visit" | "error" | "context"
    page: Optional[str] = None
    error_type: Optional[str] = None
    message: Optional[str] = None
    key: Optional[str] = None
    value: Optional[str] = None
    metadata: Optional[dict] = None

@router.post("/api/vox/awareness")
async def log_awareness(event: AwarenessEvent):
    from services.vox_awareness import vox_awareness
    if event.event_type == "page_visit" and event.page:
        visit_id = vox_awareness.log_page_visit(event.page, event.metadata)
        return {"success": True, "visit_id": visit_id}
    elif event.event_type == "error" and event.error_type and event.message:
        error_id = vox_awareness.log_error(
            event.error_type, event.message, event.page or ""
        )
        return {"success": True, "error_id": error_id}
    elif event.event_type == "context" and event.key and event.value:
        vox_awareness.set_context(event.key, event.value)
        return {"success": True}
    return {"success": False, "error": "Invalid event type or missing fields"}
```

#### GET /api/vox/awareness

Returns current awareness context.

```python
@router.get("/api/vox/awareness")
async def get_awareness():
    from services.vox_awareness import vox_awareness
    return {
        "prompt": vox_awareness.build_awareness_prompt(),
        "recent_pages": vox_awareness.get_recent_pages(5),
        "unresolved_errors": vox_awareness.get_unresolved_errors(3),
        "page_stats": vox_awareness.get_page_stats(),
    }
```

#### GET /api/vox/tours

Lists available guided tours with step counts.

```python
@router.get("/api/vox/tours")
async def list_tours():
    tours = _load_tours()
    summary = []
    for page_id, tour in tours.items():
        summary.append({
            "page": page_id,
            "name": tour.get("name", ""),
            "description": tour.get("description", ""),
            "step_count": len(tour.get("steps", [])),
        })
    return {"tours": summary, "count": len(summary)}
```

#### GET /api/vox/tours/{page}

Returns tour steps for a specific page.

```python
@router.get("/api/vox/tours/{page}")
async def get_tour(page: str):
    tours = _load_tours()
    tour = tours.get(page)
    if not tour:
        return {"error": f"No tour found for page: {page}"}
    return {"page": page, **tour}
```

#### GET /api/vox/macros

Lists all saved voice macros.

#### POST /api/vox/macros

Creates a new voice macro from a `MacroCreateRequest` body.

#### DELETE /api/vox/macros/{macro_id}

Deletes a voice macro by ID.

#### POST /api/vox/macros/{macro_id}/run

Runs all steps of a macro sequentially with pipe chaining.

#### GET /api/vox/thermal

Returns device temperature and battery status from Termux.

#### WS /ws/vox

Bidirectional WebSocket for VOX voice sessions. See section 1.8 for the full protocol.

---

### 1.8 WebSocket Protocol

The VOX WebSocket at `/ws/vox` carries JSON messages in both directions.

#### Client to Server Messages

**1. start** -- Initialize a voice session

```json
{
  "type": "start",
  "mode": "gemini",
  "model": "gemini-2.5-flash-native-audio-preview-12-2025",
  "voice": "Puck",
  "systemPrompt": "",
  "session_token": null
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | `"start"` | Yes | Message type |
| `mode` | `"gemini"` or `"claude"` | Yes | Voice backend |
| `model` | string | No | Model ID; defaults from config |
| `voice` | string | No | Gemini voice name; defaults to `"Puck"` |
| `systemPrompt` | string | No | Additional system instructions |
| `session_token` | string | No | Gemini session resumption token |

**2. audio** -- Send PCM audio data (Gemini mode only)

```json
{
  "type": "audio",
  "data": "<base64-encoded PCM int16 at 16000Hz>"
}
```

**3. text** -- Send text message

```json
{
  "type": "text",
  "text": "What tools are available?"
}
```

**4. browser_function_result** -- Return result from browser-side function

```json
{
  "type": "browser_function_result",
  "name": "navigate_page",
  "result": {"success": true, "navigated_to": "/tools"},
  "fn_call_id": "fc_abc123"
}
```

**5. end** -- Close the session

```json
{
  "type": "end"
}
```

#### Server to Client Messages

**1. setup_complete**
```json
{"type": "setup_complete", "sessionId": "a1b2c3d4", "mode": "gemini", "resumed": false}
```

**2. audio** -- PCM audio at 24000Hz
```json
{"type": "audio", "data": "<base64>"}
```

**3. text** -- Text response
```json
{"type": "text", "text": "I found 58 tools..."}
```

**4. transcript** -- Speech transcription
```json
{"type": "transcript", "role": "user", "text": "what tools do you have"}
```

**5. turn_complete**
```json
{"type": "turn_complete", "turn": 3}
```

**6. function_call** -- Function invocation (server-handled or browser-side)
```json
{"type": "function_call", "name": "list_tools", "args": {}, "server_handled": true}
```
```json
{"type": "function_call", "name": "navigate_page", "args": {"path": "/tools"}, "fn_call_id": "fc_abc123", "server_handled": false}
```

**7. function_result**
```json
{"type": "function_result", "name": "list_tools", "result": {"success": true, "tools": [...], "count": 58}}
```

**8. start_tour**
```json
{"type": "start_tour", "page": "kg-studio", "tour": {"name": "KG Studio Tour", "steps": [...]}}
```

**9. async_task_started**
```json
{"type": "async_task_started", "task_id": "e5f6g7h8", "function": "ingest_to_kg"}
```

**10. async_task_complete**
```json
{"type": "async_task_complete", "task_id": "e5f6g7h8", "function": "ingest_to_kg", "result": {...}}
```

**11. go_away** -- Session about to terminate
```json
{"type": "go_away", "session_token": "token-string", "message": "Session reconnecting..."}
```

**12. error**
```json
{"type": "error", "message": "Session start failed: GEMINI_API_KEY not configured"}
```

---

### 1.9 Gemini Receive Loop

The `_gemini_receive_loop()` function is an async coroutine launched via `asyncio.create_task()` immediately after a Gemini session is created. It continuously reads from `session.gemini_session.receive()` and forwards responses to the WebSocket client.

**Processing order per response:**

1. **Audio data** (`response.data`): Base64-encode and send as `audio` message
2. **Server content** (`response.server_content`): Extract text parts and turn_complete
3. **Tool calls** (`response.tool_call`): Route each function call:
   - If in `ASYNC_FUNCTIONS` set: spawn background task, notify client with `async_task_started`
   - If NOT in `BROWSER_FUNCTIONS`: execute server-side, send result to client AND back to Gemini
   - If in `BROWSER_FUNCTIONS`: forward to client with `server_handled: false`
4. **Session resumption** (`response.session_resumption_update`): Store new token
5. **GoAway** (`response.go_away`): Notify client with stored session token
6. **Transcription**: Forward input/output as `transcript` messages

**ASYNC_FUNCTIONS** (background tasks):
```python
ASYNC_FUNCTIONS = {"ingest_to_kg", "run_workflow", "cross_kg_search", "run_agent"}
```

**BROWSER_FUNCTIONS** (forwarded to client):
```python
BROWSER_FUNCTIONS = {
    "navigate_page", "get_current_page", "get_workspace_state",
    "switch_model", "switch_theme", "read_page_content",
}
```

The full implementation is 150 lines. Key code paths include the async function handler which creates an inner `_run_async` coroutine and spawns it with `asyncio.create_task()`, and the special handling for `start_guided_tour` which sends an additional `start_tour` message to trigger the browser's tour overlay component.

---

### 1.10 Claude Text Pipeline

The `_claude_text_pipeline()` converts VOX function declarations to Anthropic `tool_use` format and runs a multi-turn loop (max 5 rounds) to handle chained tool calls.

**Tool format conversion** (`_build_claude_tools()`):

```python
def _build_claude_tools() -> list[dict]:
    tools = []
    for fn in build_function_declarations():
        tools.append({
            "name": fn["name"],
            "description": fn.get("description", ""),
            "input_schema": fn.get("parameters", {"type": "object", "properties": {}}),
        })
    return tools
```

**Pipeline flow:**

1. Get Anthropic client via `_get_client()`
2. Convert 34 function declarations to Anthropic format
3. Initialize messages with user text
4. Loop up to 5 times:
   a. Call `client.messages.create()` via `asyncio.to_thread()`
   b. Process response content blocks (text and tool_use)
   c. If no tool_use blocks, break
   d. Serialize assistant message for multi-turn
   e. Execute each tool call (server or browser)
   f. Append tool_results to messages
   g. Continue to next iteration
5. Send accumulated text response to client
6. Send `turn_complete`

**Key difference from Gemini:** For browser-side functions, Claude receives a placeholder `tool_result` (`{"success": true, "note": "Executed in browser"}`) since the synchronous API call cannot wait for browser execution.

---

### 1.11 Server Function Execution

The `_execute_server_function()` function is the central dispatcher for all 28 server-side functions. It routes by function name to the appropriate backend service.

**Function routing table:**

| Function | Service | Method Called |
|----------|---------|--------------|
| `run_tool` | `tools_service` | `run_tool(tool_id, params)` |
| `list_tools` | `tools_service` | `list_tools()` -- returns summary with id, name, category |
| `query_kg` | `EmbeddingService` | `hybrid_search(query, limit=5)` |
| `list_kgs` | `kg_service` | `list_databases()` -- returns summary with id, name, node count |
| `run_agent` | `agent_bridge` | `run_agent(name, {"text": input})` via `asyncio.to_thread` |
| `list_agents` | `agent_bridge` | `list_agents()` |
| `generate_react_component` | `tools_service` | `run_tool("react_component_generator", ...)` |
| `generate_fastapi_endpoint` | `tools_service` | `run_tool("fastapi_endpoint_generator", ...)` |
| `scan_code_security` | `tools_service` | `run_tool("security_scanner", ...)` |
| `analyze_code_complexity` | `tools_service` | `run_tool("complexity_scorer", ...)` |
| `generate_tests` | `tools_service` | `run_tool("pytest_generator", ...)` |
| `start_guided_tour` | `_load_tours()` | Returns tour data with `action: "start_tour"` |
| `get_available_tours` | `_load_tours()` | Lists all tours with step counts |
| `create_project` | `studio_service` | `create_project(name, description)` |
| `list_projects` | `studio_service` | `list_projects()` |
| `run_workflow` | template mapping | Maps name to JSON file |
| `search_playbooks` | `playbook_index` | `search(query)` -- returns top 5 |
| `search_kg` | `EmbeddingService` | `hybrid_search()` with optional `node_type` filter |
| `get_kg_analytics` | `analytics_service` | `get_analytics(db_id)` |
| `cross_kg_search` | `EmbeddingService` per DB | Iterates up to 10 DBs |
| `ingest_to_kg` | `ingestion_service` | `ingest_text(db_id, text)` via `asyncio.to_thread` |
| `chat_with_expert` | `expert_service` | `chat(expert_id, message)` |
| `list_experts` | `expert_service` | `list_experts()` |
| `create_macro` | `vox_macro_service` | `create_macro(name, trigger, steps, policy)` |
| `list_macros` | `vox_macro_service` | `list_macros()` |
| `run_macro` | `vox_macro_service` | `execute_macro(id, _execute_server_function)` |
| `delete_macro` | `vox_macro_service` | `delete_macro(id)` |
| `check_thermal` | `thermal_monitor` | `check()` |

**Safe serialization helper:**

```python
def _safe_serialize(obj):
    """Ensure object is JSON-serializable."""
    if isinstance(obj, dict):
        return {k: _safe_serialize(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_safe_serialize(v) for v in obj]
    elif isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    else:
        return str(obj)
```

All results are wrapped through `_safe_serialize()` before being sent over WebSocket or returned from REST endpoints. Unknown function names return `{"success": false, "error": "Unknown server function: {name}"}`. Exceptions are caught and returned as `{"success": false, "error": str(e)}`.

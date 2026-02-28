"""VOX voice router — WebSocket for bidirectional audio + REST helpers.

Enhanced with:
- Function execution via vox_registry (decorator-based, replacing if/elif)
- Awareness endpoints
- Guided tours endpoints
- Voice macro endpoints
- Thermal monitoring endpoint
- Feature interview endpoints (10-question MVP builder)
- Async task queue for long-running operations
"""
import asyncio
import base64
import json
import uuid
from pathlib import Path
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from services.vox_service import vox_service, VoxSession, GEMINI_VOICES, build_function_declarations
from services.vox_registry import vox_registry

router = APIRouter()

# ── Function execution via registry ───────────────────────────────────

BROWSER_FUNCTIONS = vox_registry.get_browser_functions()
ASYNC_FUNCTIONS = vox_registry.get_async_functions()

# ── Async task queue for long-running operations ──────────────────────
_async_tasks: dict[str, asyncio.Task] = {}

ASYNC_TASK_TIMEOUT = 300  # 5 minutes


async def _run_with_timeout(coro, timeout=ASYNC_TASK_TIMEOUT):
    """Run a coroutine with a timeout. Returns result or error dict."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        return {"success": False, "error": f"Task timed out after {timeout}s"}


async def _execute_server_function(name: str, args: dict) -> dict:
    """Delegate to vox_registry."""
    return await vox_registry.execute(name, args)


# ── REST endpoints ─────────────────────────────────────────────────────

@router.get("/api/vox/voices")
async def list_voices():
    """List available Gemini Live API voices."""
    return {"voices": GEMINI_VOICES}


@router.get("/api/vox/status")
async def vox_status():
    """Check VOX availability based on configured API keys."""
    return {
        "gemini_available": vox_service.is_gemini_available(),
        "claude_available": vox_service.is_claude_available(),
        "active_sessions": len(vox_service.sessions),
    }


@router.get("/api/vox/functions")
async def list_functions():
    """List all workspace function declarations available to VOX."""
    fns = build_function_declarations()
    return {"functions": fns, "count": len(fns)}


class FunctionRunRequest(BaseModel):
    args: dict = {}


@router.post("/api/vox/function/{fn_name}")
async def run_function(fn_name: str, req: FunctionRunRequest):
    """Execute a workspace function server-side (for tools, KG, agents)."""
    result = await vox_registry.execute(fn_name, req.args)
    return {"name": fn_name, "result": result}


# ── Awareness endpoints ───────────────────────────────────────────────

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
    """Receive page visit, error, or context events from the frontend."""
    from services.vox_awareness import vox_awareness

    if event.event_type == "page_visit" and event.page:
        visit_id = vox_awareness.log_page_visit(event.page, event.metadata)
        return {"success": True, "visit_id": visit_id}
    elif event.event_type == "error" and event.error_type and event.message:
        error_id = vox_awareness.log_error(event.error_type, event.message, event.page or "")
        return {"success": True, "error_id": error_id}
    elif event.event_type == "context" and event.key and event.value:
        vox_awareness.set_context(event.key, event.value)
        return {"success": True}
    return {"success": False, "error": "Invalid event type or missing fields"}


@router.get("/api/vox/awareness")
async def get_awareness():
    """Get current awareness context."""
    from services.vox_awareness import vox_awareness
    return {
        "prompt": vox_awareness.build_awareness_prompt(),
        "recent_pages": vox_awareness.get_recent_pages(5),
        "unresolved_errors": vox_awareness.get_unresolved_errors(3),
        "page_stats": vox_awareness.get_page_stats(),
    }


# ── Guided Tours endpoints ────────────────────────────────────────────

TOURS_PATH = Path(__file__).parent.parent / "data" / "vox_tours.json"


def _load_tours() -> dict:
    """Load tour definitions from JSON file."""
    try:
        with open(TOURS_PATH) as f:
            return json.load(f)
    except Exception:
        return {}


@router.get("/api/vox/tours")
async def list_tours():
    """List available guided tours."""
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


@router.get("/api/vox/tours/{page}")
async def get_tour(page: str):
    """Get tour steps for a specific page."""
    tours = _load_tours()
    tour = tours.get(page)
    if not tour:
        return {"error": f"No tour found for page: {page}"}
    return {"page": page, **tour}


# ── Voice Macro endpoints ─────────────────────────────────────────────

class MacroCreateRequest(BaseModel):
    name: str
    trigger_phrase: str
    steps: list[dict]
    error_policy: str = "abort"


@router.get("/api/vox/macros")
async def list_macros():
    """List all saved voice macros."""
    from services.vox_macros import vox_macro_service
    return {"macros": vox_macro_service.list_macros()}


@router.post("/api/vox/macros")
async def create_macro(req: MacroCreateRequest):
    """Create a new voice macro."""
    from services.vox_macros import vox_macro_service
    macro = vox_macro_service.create_macro(
        name=req.name,
        trigger_phrase=req.trigger_phrase,
        steps=req.steps,
        error_policy=req.error_policy,
    )
    return {"success": True, "macro": macro}


@router.delete("/api/vox/macros/{macro_id}")
async def delete_macro(macro_id: str):
    """Delete a voice macro."""
    from services.vox_macros import vox_macro_service
    deleted = vox_macro_service.delete_macro(macro_id)
    return {"success": deleted}


@router.post("/api/vox/macros/{macro_id}/run")
async def run_macro_endpoint(macro_id: str):
    """Execute a voice macro by ID."""
    from services.vox_macros import vox_macro_service
    results = await vox_macro_service.execute_macro(macro_id, vox_registry.execute)
    return {"success": True, "results": results}


# ── Thermal endpoint ──────────────────────────────────────────────────

@router.get("/api/vox/thermal")
async def get_thermal():
    """Get device temperature and battery status."""
    from services.vox_thermal import thermal_monitor
    return await thermal_monitor.check()


# ── Feature Interview endpoints ───────────────────────────────────────

INTERVIEW_PATH = Path(__file__).parent.parent / "data" / "vox_interview.json"


def _load_interview() -> dict:
    """Load the interview definition from JSON file."""
    try:
        with open(INTERVIEW_PATH) as f:
            return json.load(f)
    except Exception:
        return {}


@router.get("/api/vox/interview")
async def get_interview():
    """Return the 10-question feature interview definition."""
    interview = _load_interview()
    if not interview:
        return {"error": "Interview definition not found"}
    return interview


class InterviewGenerateRequest(BaseModel):
    answers: dict
    provider: str = "gemini"
    model: Optional[str] = None
    project_id: Optional[str] = None


@router.post("/api/vox/interview/generate")
async def interview_generate(req: InterviewGenerateRequest):
    """Accept interview answers, build a prompt from the template, and stream a React MVP via Studio."""
    from config import MODE, ANTHROPIC_API_KEY
    from services import gemini_service, claude_service

    interview = _load_interview()
    if not interview:
        return {"error": "Interview definition not found"}

    template = interview.get("prompt_template", "")
    questions = interview.get("questions", [])

    # Build answer lookup keyed by question key
    answer_map: dict[str, str] = {}
    for q in questions:
        key = q.get("key", f"q{q['id']}")
        raw = req.answers.get(str(q["id"]), req.answers.get(key, ""))

        # For single_choice questions, resolve the label from the option id
        if q["type"] == "single_choice" and raw and q.get("options"):
            matched = next((o for o in q["options"] if o["id"] == raw), None)
            if matched:
                raw = f"{matched['label']} — {matched.get('description', '')}"

        answer_map[key] = str(raw) if raw else "not specified"

    # Fill the prompt template
    prompt = template
    for key, value in answer_map.items():
        prompt = prompt.replace(f"{{{key}}}", value)

    # Import the Studio system prompt for consistent file marker format
    from routers.studio import GENERATE_SYSTEM_PROMPT, _parse_file_markers

    messages = [{"author": "user", "parts": [{"text": prompt}]}]

    async def stream():
        accumulated = ""
        emitted_files: set[str] = set()
        emitted_deps: dict[str, str] = {}
        plan_emitted = False

        # Choose provider
        if req.provider == "claude" and MODE == "standalone" and ANTHROPIC_API_KEY:
            target_model = req.model or "claude-sonnet-4-6"
            ai_stream = claude_service.stream_chat(
                messages=messages,
                model=target_model,
                system=GENERATE_SYSTEM_PROMPT,
                max_tokens=16384,
                temperature=0.7,
            )
        else:
            target_model = req.model or "gemini-2.5-flash"
            ai_stream = gemini_service.stream_chat(
                messages=messages,
                model=target_model,
                system_instruction=GENERATE_SYSTEM_PROMPT,
                temperature=0.7,
            )

        async for chunk in ai_stream:
            if chunk.get("type") == "token":
                token_text = chunk["content"]
                accumulated += token_text

                yield f"data: {json.dumps({'type': 'token', 'content': token_text})}\n\n"

                plan_text, parsed_files, parsed_deps, _ = _parse_file_markers(accumulated)

                if not plan_emitted and plan_text and parsed_files:
                    yield f"data: {json.dumps({'type': 'studio_plan', 'content': plan_text})}\n\n"
                    plan_emitted = True

                for path, content in parsed_files.items():
                    if path not in emitted_files:
                        emitted_files.add(path)
                        yield f"data: {json.dumps({'type': 'studio_file', 'path': path, 'content': content})}\n\n"

                for pkg, ver in parsed_deps.items():
                    if pkg not in emitted_deps:
                        emitted_deps[pkg] = ver
                        yield f"data: {json.dumps({'type': 'studio_dep', 'package': pkg, 'version': ver})}\n\n"

        # Final parse of any remaining file blocks
        _, final_files, final_deps, _ = _parse_file_markers(accumulated)
        for path, content in final_files.items():
            if path not in emitted_files:
                emitted_files.add(path)
                yield f"data: {json.dumps({'type': 'studio_file', 'path': path, 'content': content})}\n\n"

        all_files = {p: final_files.get(p, "") for p in emitted_files}
        all_deps = {**emitted_deps, **final_deps}

        # Save to Studio project if project_id provided
        if req.project_id:
            try:
                from services.studio_service import studio_service
                studio_service.update_project_files(req.project_id, all_files, all_deps)
            except Exception:
                pass

        yield f"data: {json.dumps({'type': 'complete', 'files': all_files, 'deps': all_deps})}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


# ── WebSocket endpoint ─────────────────────────────────────────────────

@router.websocket("/ws/vox")
async def vox_websocket(ws: WebSocket):
    """Bidirectional WebSocket for VOX voice sessions."""
    await ws.accept()
    session_id = None

    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await ws.send_json({"type": "error", "message": "Invalid JSON"})
                continue

            msg_type = msg.get("type", "")

            # ── Start session ──────────────────────────────────────────
            if msg_type == "start":
                mode = msg.get("mode", "gemini")
                model = msg.get("model", "")
                voice = msg.get("voice", "Puck")
                system_prompt = msg.get("systemPrompt", "")
                token = msg.get("session_token")

                # Log awareness
                try:
                    from services.vox_awareness import vox_awareness
                    vox_awareness.set_context("vox_mode", mode)
                    vox_awareness.set_context("vox_voice", voice)
                except Exception:
                    pass

                try:
                    if mode == "gemini":
                        if not model:
                            from config import VOX_DEFAULT_MODEL
                            model = VOX_DEFAULT_MODEL
                        session = await vox_service.create_gemini_session(
                            model=model,
                            voice=voice,
                            custom_prompt=system_prompt,
                            session_token=token,
                        )
                        session_id = session.session_id
                        await ws.send_json({
                            "type": "setup_complete",
                            "sessionId": session_id,
                            "mode": "gemini",
                            "resumed": bool(token),
                        })
                        # Start receive loop for Gemini responses
                        asyncio.create_task(
                            _gemini_receive_loop(ws, session)
                        )

                    elif mode == "claude":
                        if not model:
                            from config import DEFAULT_CLAUDE_MODEL
                            model = DEFAULT_CLAUDE_MODEL
                        session = vox_service.create_claude_session(
                            model=model,
                            custom_prompt=system_prompt,
                        )
                        session_id = session.session_id
                        await ws.send_json({
                            "type": "setup_complete",
                            "sessionId": session_id,
                            "mode": "claude",
                        })
                    else:
                        await ws.send_json({"type": "error", "message": f"Unknown mode: {mode}"})

                except Exception as e:
                    await ws.send_json({"type": "error", "message": f"Session start failed: {str(e)}"})

            # ── Send audio (Gemini mode) ───────────────────────────────
            elif msg_type == "audio" and session_id:
                audio_data = msg.get("data", "")
                if audio_data:
                    await vox_service.send_audio(session_id, audio_data)

            # ── Send text ──────────────────────────────────────────────
            elif msg_type == "text" and session_id:
                text = msg.get("text", msg.get("content", ""))
                session = vox_service.get_session(session_id)
                if not session or not text:
                    continue

                if session.mode == "gemini":
                    await vox_service.send_text(session_id, text)

                elif session.mode == "claude":
                    # Claude text pipeline: send to Claude, return text response
                    asyncio.create_task(
                        _claude_text_pipeline(ws, session, text)
                    )

            # ── Browser function result ────────────────────────────────
            elif msg_type == "browser_function_result" and session_id:
                fn_name = msg.get("name", "")
                fn_result = msg.get("result", {})
                fn_cid = msg.get("fn_call_id", "")
                session = vox_service.get_session(session_id)
                if session and session.mode == "gemini":
                    await vox_service.send_function_result(
                        session_id, fn_cid, fn_name, fn_result
                    )

            # ── End session ────────────────────────────────────────────
            elif msg_type == "end":
                if session_id:
                    await vox_service.close_session(session_id)
                    session_id = None
                break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await ws.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        if session_id:
            await vox_service.close_session(session_id)


async def _gemini_receive_loop(ws: WebSocket, session: VoxSession):
    """Async loop that receives from Gemini Live API and forwards to WebSocket."""
    try:
        async for response in session.gemini_session.receive():
            # Audio data
            if response.data:
                audio_b64 = base64.b64encode(response.data).decode("utf-8")
                await ws.send_json({"type": "audio", "data": audio_b64})

            # Server content (text, turn_complete)
            if response.server_content:
                sc = response.server_content
                if sc.model_turn and sc.model_turn.parts:
                    for part in sc.model_turn.parts:
                        if hasattr(part, "text") and part.text:
                            await ws.send_json({"type": "text", "text": part.text})
                if sc.turn_complete:
                    session.turn_count += 1
                    await ws.send_json({
                        "type": "turn_complete",
                        "turn": session.turn_count,
                    })

            # Tool calls (function declarations)
            if response.tool_call:
                for fc in response.tool_call.function_calls:
                    fn_name = fc.name
                    fn_args = dict(fc.args) if fc.args else {}
                    fn_call_id = getattr(fc, 'id', None) or ""
                    session.function_count += 1

                    # Log to awareness
                    try:
                        from services.vox_awareness import vox_awareness
                        vox_awareness.set_context("last_function", fn_name)
                    except Exception:
                        pass

                    # Check for async execution
                    if fn_name in ASYNC_FUNCTIONS:
                        # Run in background, notify when done
                        task_id = str(uuid.uuid4())[:8]
                        await ws.send_json({
                            "type": "async_task_started",
                            "task_id": task_id,
                            "function": fn_name,
                        })
                        await ws.send_json({
                            "type": "function_call",
                            "name": fn_name,
                            "args": fn_args,
                            "server_handled": True,
                            "async": True,
                        })

                        async def _run_async(ws_ref, sess, fname, fargs, tid, fcid):
                            result = await _run_with_timeout(vox_registry.execute(fname, fargs))
                            try:
                                await ws_ref.send_json({
                                    "type": "async_task_complete",
                                    "task_id": tid,
                                    "function": fname,
                                    "result": result,
                                })
                                await ws_ref.send_json({
                                    "type": "function_result",
                                    "name": fname,
                                    "result": result,
                                })
                            except Exception:
                                pass
                            # Send result back to Gemini
                            await vox_service.send_function_result(
                                sess.session_id, fcid, fname, result
                            )

                        asyncio.create_task(_run_async(ws, session, fn_name, fn_args, task_id, fn_call_id))
                        continue

                    # Server-side functions: execute and send result back
                    if fn_name not in BROWSER_FUNCTIONS:
                        result = await vox_registry.execute(fn_name, fn_args)
                        await ws.send_json({
                            "type": "function_call",
                            "name": fn_name,
                            "args": fn_args,
                            "server_handled": True,
                        })
                        await ws.send_json({
                            "type": "function_result",
                            "name": fn_name,
                            "result": result,
                        })

                        # Handle special results that need browser action
                        if fn_name == "start_guided_tour" and result.get("success") and result.get("action") == "start_tour":
                            await ws.send_json({
                                "type": "start_tour",
                                "page": result["page"],
                                "tour": result["tour"],
                            })

                        # Send result back to Gemini
                        await vox_service.send_function_result(
                            session.session_id, fn_call_id, fn_name, result
                        )
                    else:
                        # Browser-side: forward to client for execution
                        await ws.send_json({
                            "type": "function_call",
                            "name": fn_name,
                            "args": fn_args,
                            "fn_call_id": fn_call_id,
                            "server_handled": False,
                        })

            # Session resumption updates
            if response.session_resumption_update:
                update = response.session_resumption_update
                if update.resumable and update.new_handle:
                    session.session_token = update.new_handle

            # GoAway (session about to terminate)
            if response.go_away:
                token = session.session_token
                await ws.send_json({
                    "type": "go_away",
                    "session_token": token,
                    "message": "Session reconnecting...",
                })

            # Transcript
            if hasattr(response, 'server_content') and response.server_content:
                sc = response.server_content
                if hasattr(sc, 'input_transcription') and sc.input_transcription:
                    await ws.send_json({
                        "type": "transcript",
                        "role": "user",
                        "text": sc.input_transcription.text if hasattr(sc.input_transcription, 'text') else str(sc.input_transcription),
                    })
                if hasattr(sc, 'output_transcription') and sc.output_transcription:
                    await ws.send_json({
                        "type": "transcript",
                        "role": "model",
                        "text": sc.output_transcription.text if hasattr(sc.output_transcription, 'text') else str(sc.output_transcription),
                    })

    except Exception as e:
        try:
            await ws.send_json({"type": "error", "message": f"Gemini stream error: {str(e)}"})
        except Exception:
            pass


def _build_claude_tools() -> list[dict]:
    """Convert VOX function declarations to Anthropic tool_use format."""
    tools = []
    for fn in vox_registry.get_declarations():
        tools.append({
            "name": fn["name"],
            "description": fn.get("description", ""),
            "input_schema": fn.get("parameters", {"type": "object", "properties": {}}),
        })
    return tools


async def _claude_text_pipeline(ws: WebSocket, session: VoxSession, text: str):
    """Process text through Claude using native tool_use API."""
    try:
        from services.claude_service import _get_client
        from config import MODE

        if MODE != "standalone":
            await ws.send_json({"type": "error", "message": "Claude not available in claude-code mode"})
            return

        client = _get_client()
        claude_tools = _build_claude_tools()
        messages = [{"role": "user", "content": text}]

        full_response = ""

        # Multi-turn tool use loop (max 5 rounds to handle chained tool calls)
        for _ in range(5):
            response = await asyncio.to_thread(
                client.messages.create,
                model=session.model,
                max_tokens=2048,
                system=session.system_instruction,
                messages=messages,
                tools=claude_tools,
            )

            # Process content blocks
            text_parts = []
            tool_uses = []
            for block in response.content:
                if block.type == "text":
                    text_parts.append(block.text)
                elif block.type == "tool_use":
                    tool_uses.append(block)

            if text_parts:
                full_response += " ".join(text_parts)

            # No tool calls — we're done
            if not tool_uses:
                break

            # Serialize assistant message for multi-turn
            assistant_content = []
            for block in response.content:
                if block.type == "text":
                    assistant_content.append({"type": "text", "text": block.text})
                elif block.type == "tool_use":
                    assistant_content.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    })
            messages.append({"role": "assistant", "content": assistant_content})

            # Execute each tool call
            tool_results = []
            for tu in tool_uses:
                fn_name = tu.name
                fn_args = tu.input or {}
                session.function_count += 1

                if fn_name not in BROWSER_FUNCTIONS:
                    result = await vox_registry.execute(fn_name, fn_args)
                    await ws.send_json({
                        "type": "function_call",
                        "name": fn_name,
                        "args": fn_args,
                        "server_handled": True,
                    })
                    await ws.send_json({
                        "type": "function_result",
                        "name": fn_name,
                        "result": result,
                    })

                    # Handle special tour result
                    if fn_name == "start_guided_tour" and result.get("success") and result.get("action") == "start_tour":
                        await ws.send_json({
                            "type": "start_tour",
                            "page": result["page"],
                            "tour": result["tour"],
                        })

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tu.id,
                        "content": json.dumps(result, default=str),
                    })
                else:
                    # Browser-side functions — acknowledge but can't execute server-side
                    await ws.send_json({
                        "type": "function_call",
                        "name": fn_name,
                        "args": fn_args,
                        "server_handled": False,
                    })
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tu.id,
                        "content": json.dumps({"success": True, "note": "Executed in browser"}),
                    })

            # Feed tool results back to Claude for next turn
            messages.append({"role": "user", "content": tool_results})

        session.turn_count += 1

        # Send final text response for browser TTS
        if full_response:
            await ws.send_json({"type": "text", "text": full_response})
        await ws.send_json({
            "type": "turn_complete",
            "turn": session.turn_count,
        })

    except Exception as e:
        try:
            await ws.send_json({"type": "error", "message": f"Claude error: {str(e)}"})
        except Exception:
            pass

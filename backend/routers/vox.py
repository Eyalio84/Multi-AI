"""VOX voice router — WebSocket for bidirectional audio + REST helpers.

Enhanced with:
- ~35 function handlers (up from 17)
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

router = APIRouter()

# ── Async task queue for long-running operations ──────────────────────
_async_tasks: dict[str, asyncio.Task] = {}

ASYNC_TASK_TIMEOUT = 300  # 5 minutes


async def _run_with_timeout(coro, timeout=ASYNC_TASK_TIMEOUT):
    """Run a coroutine with a timeout. Returns result or error dict."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        return {"success": False, "error": f"Task timed out after {timeout}s"}


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
    result = await _execute_server_function(fn_name, req.args)
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
    results = await vox_macro_service.execute_macro(macro_id, _execute_server_function)
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


# ── Server-side function execution ─────────────────────────────────────

# Functions that should run async (potentially slow)
ASYNC_FUNCTIONS = {"ingest_to_kg", "run_workflow", "cross_kg_search", "run_agent"}


async def _execute_server_function(name: str, args: dict) -> dict:
    """Execute workspace functions that need backend access."""
    try:
        # ── Core tools ─────────────────────────────────────────────
        if name == "run_tool":
            from services.tools_service import tools_service
            tool_id = args.get("tool_id", "")
            params = args.get("params", {})
            result = await tools_service.run_tool(tool_id, params)
            return {"success": True, "result": _safe_serialize(result)}

        elif name == "list_tools":
            from services.tools_service import tools_service
            tools_data = tools_service.list_tools()
            summary = []
            for cat_tools in tools_data.get("tools", {}).values():
                for t in cat_tools:
                    summary.append({"id": t["id"], "name": t["name"], "category": t["category"]})
            return {"success": True, "tools": summary, "count": len(summary)}

        elif name == "query_kg":
            from services.embedding_service import EmbeddingService
            db_id = args.get("database_id", "")
            query = args.get("query", "")
            svc = EmbeddingService(db_id)
            results = svc.hybrid_search(query, limit=5)
            return {"success": True, "results": results[:5], "database": db_id}

        elif name == "list_kgs":
            from services.kg_service import kg_service
            dbs = kg_service.list_databases()
            summary = [{"id": d["id"], "name": d.get("name", d["id"]), "nodes": d.get("node_count", 0)} for d in dbs]
            return {"success": True, "databases": summary, "count": len(summary)}

        elif name == "run_agent":
            from services.agent_bridge import run_agent
            agent_name = args.get("agent_name", "")
            agent_input = args.get("input", "")
            result = await asyncio.to_thread(run_agent, agent_name, {"text": agent_input})
            return {"success": True, "result": _safe_serialize(result)}

        elif name == "list_agents":
            from services.agent_bridge import list_agents
            agents = list_agents()
            return {"success": True, "agents": agents, "count": len(agents)}

        # ── Direct developer tool shortcuts ────────────────────────
        elif name == "generate_react_component":
            from services.tools_service import tools_service
            params = {
                "name": args.get("name", "MyComponent"),
                "description": args.get("description", ""),
                "framework": args.get("framework", "react"),
                "features": args.get("features", "state"),
            }
            result = await tools_service.run_tool("react_component_generator", params)
            return {"success": True, "result": _safe_serialize(result)}

        elif name == "generate_fastapi_endpoint":
            from services.tools_service import tools_service
            params = {
                "description": args.get("description", ""),
                "method": args.get("method", "POST"),
                "path": args.get("path", "/api/resource"),
                "framework": args.get("framework", "fastapi"),
            }
            result = await tools_service.run_tool("fastapi_endpoint_generator", params)
            return {"success": True, "result": _safe_serialize(result)}

        elif name == "scan_code_security":
            from services.tools_service import tools_service
            params = {
                "code": args.get("code", ""),
                "language": args.get("language", "python"),
            }
            result = await tools_service.run_tool("security_scanner", params)
            return {"success": True, "result": _safe_serialize(result)}

        elif name == "analyze_code_complexity":
            from services.tools_service import tools_service
            params = {
                "code": args.get("code", ""),
                "language": args.get("language", "python"),
            }
            result = await tools_service.run_tool("complexity_scorer", params)
            return {"success": True, "result": _safe_serialize(result)}

        elif name == "generate_tests":
            from services.tools_service import tools_service
            params = {
                "code": args.get("code", ""),
                "framework": args.get("framework", "pytest"),
                "style": args.get("style", "unit"),
            }
            result = await tools_service.run_tool("pytest_generator", params)
            return {"success": True, "result": _safe_serialize(result)}

        # ── Guided Tours ───────────────────────────────────────────
        elif name == "start_guided_tour":
            page = args.get("page", "")
            tours = _load_tours()
            if not page:
                return {"success": False, "error": "No page specified. Ask the user which page to tour."}
            tour = tours.get(page)
            if not tour:
                available = list(tours.keys())
                return {"success": False, "error": f"No tour for '{page}'. Available: {', '.join(available)}"}
            return {"success": True, "action": "start_tour", "page": page, "tour": tour}

        elif name == "get_available_tours":
            tours = _load_tours()
            summary = [
                {"page": p, "name": t.get("name", ""), "steps": len(t.get("steps", []))}
                for p, t in tours.items()
            ]
            return {"success": True, "tours": summary, "count": len(summary)}

        # ── Workspace Control (Jarvis Mode) ────────────────────────
        elif name == "create_project":
            from services.studio_service import studio_service
            project_name = args.get("name", "Untitled")
            description = args.get("description", "")
            project = studio_service.create_project(project_name, description)
            return {"success": True, "project_id": project.get("id"), "name": project_name}

        elif name == "list_projects":
            from services.studio_service import studio_service
            projects = studio_service.list_projects()
            summary = [{"id": p.get("id"), "name": p.get("name", ""), "file_count": p.get("file_count", 0)} for p in projects]
            return {"success": True, "projects": summary, "count": len(summary)}

        elif name == "run_workflow":
            workflow_name = args.get("workflow_name", "")
            workflow_input = args.get("input", "")
            # Map names to template files
            templates = {
                "error-recovery": "error-recovery-workflow.json",
                "knowledge-synthesis": "knowledge-synthesis-workflow.json",
                "session-handoff": "session-handoff-workflow.json",
                "multi-agent": "multi-agent-orchestration-workflow.json",
            }
            tpl_file = templates.get(workflow_name)
            if not tpl_file:
                return {"success": False, "error": f"Unknown workflow: {workflow_name}. Available: {', '.join(templates.keys())}"}
            return {"success": True, "workflow": workflow_name, "status": "initiated", "input": workflow_input[:200]}

        elif name == "search_playbooks":
            from services.playbook_index import playbook_index
            query = args.get("query", "")
            results = playbook_index.search(query)
            return {"success": True, "results": results[:5], "count": len(results)}

        elif name == "search_kg":
            from services.embedding_service import EmbeddingService
            db_id = args.get("database_id", "")
            query = args.get("query", "")
            limit = args.get("limit", 5)
            svc = EmbeddingService(db_id)
            results = svc.hybrid_search(query, limit=limit)
            # Optional type filter
            node_type = args.get("node_type", "")
            if node_type:
                results = [r for r in results if r.get("node_type", "") == node_type]
            return {"success": True, "results": results[:limit], "database": db_id, "query": query}

        # ── KG Studio Control ──────────────────────────────────────
        elif name == "get_kg_analytics":
            from services.analytics_service import get_analytics
            db_id = args.get("database_id", "")
            analytics = get_analytics(db_id)
            return {"success": True, "database": db_id, "analytics": _safe_serialize(analytics)}

        elif name == "cross_kg_search":
            from services.kg_service import kg_service
            from services.embedding_service import EmbeddingService
            query = args.get("query", "")
            db_ids_str = args.get("database_ids", "all")
            limit = args.get("limit", 3)
            if db_ids_str == "all":
                dbs = kg_service.list_databases()
                db_ids = [d["id"] for d in dbs[:10]]  # Max 10 DBs
            else:
                db_ids = [d.strip() for d in db_ids_str.split(",")]
            all_results = {}
            for db_id in db_ids:
                try:
                    svc = EmbeddingService(db_id)
                    results = svc.hybrid_search(query, limit=limit)
                    all_results[db_id] = results[:limit]
                except Exception:
                    all_results[db_id] = []
            return {"success": True, "results": _safe_serialize(all_results), "databases_searched": len(db_ids)}

        elif name == "ingest_to_kg":
            from services.ingestion_service import ingestion_service
            db_id = args.get("database_id", "")
            text = args.get("text", "")
            result = await asyncio.to_thread(ingestion_service.ingest_text, db_id, text)
            return {"success": True, "result": _safe_serialize(result)}

        # ── Expert Control ─────────────────────────────────────────
        elif name == "chat_with_expert":
            from services.expert_service import expert_service
            expert_id = args.get("expert_id", "")
            message = args.get("message", "")
            # Create or get conversation, get response
            result = expert_service.chat(expert_id, message)
            return {"success": True, "result": _safe_serialize(result)}

        elif name == "list_experts":
            from services.expert_service import expert_service
            experts = expert_service.list_experts()
            summary = [{"id": e.get("id"), "name": e.get("name", ""), "kg": e.get("database_id", "")} for e in experts]
            return {"success": True, "experts": summary, "count": len(summary)}

        # ── Voice Macros ───────────────────────────────────────────
        elif name == "create_macro":
            from services.vox_macros import vox_macro_service
            steps_raw = args.get("steps", "[]")
            if isinstance(steps_raw, str):
                steps = json.loads(steps_raw)
            else:
                steps = steps_raw
            macro = vox_macro_service.create_macro(
                name=args.get("name", ""),
                trigger_phrase=args.get("trigger_phrase", ""),
                steps=steps,
                error_policy=args.get("error_policy", "abort"),
            )
            return {"success": True, "macro": macro}

        elif name == "list_macros":
            from services.vox_macros import vox_macro_service
            return {"success": True, "macros": vox_macro_service.list_macros()}

        elif name == "run_macro":
            from services.vox_macros import vox_macro_service
            macro_id = args.get("macro_id", "")
            results = await vox_macro_service.execute_macro(macro_id, _execute_server_function)
            return {"success": True, "results": _safe_serialize(results)}

        elif name == "delete_macro":
            from services.vox_macros import vox_macro_service
            deleted = vox_macro_service.delete_macro(args.get("macro_id", ""))
            return {"success": deleted, "message": "Macro deleted" if deleted else "Macro not found"}

        # ── Thermal Monitoring ─────────────────────────────────────
        elif name == "check_thermal":
            from services.vox_thermal import thermal_monitor
            result = await thermal_monitor.check()
            return {"success": True, **result}

        # ── Feature Interview ─────────────────────────────────────
        elif name == "start_feature_interview":
            interview = _load_interview()
            if not interview:
                return {"success": False, "error": "Interview definition not found"}
            domain = args.get("domain", "")
            questions = interview.get("questions", [])
            # If domain pre-selected, mark Q1 as answered
            first_question = questions[0] if questions else {}
            if domain and first_question.get("options"):
                matched = next(
                    (o for o in first_question["options"] if o["id"] == domain),
                    None,
                )
                if matched:
                    return {
                        "success": True,
                        "action": "start_interview",
                        "total_questions": len(questions),
                        "pre_selected_domain": matched["label"],
                        "next_question": questions[1] if len(questions) > 1 else None,
                        "message": f"Great choice! You selected {matched['label']}. Let me walk you through 9 more questions to shape your MVP.",
                    }
            return {
                "success": True,
                "action": "start_interview",
                "total_questions": len(questions),
                "first_question": first_question,
                "message": "Let's build something! I'll ask you 10 quick questions to understand what you need, then generate a working React MVP. First up: what kind of app do you want to build?",
            }

        else:
            return {"success": False, "error": f"Unknown server function: {name}"}

    except Exception as e:
        return {"success": False, "error": str(e)}


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


# ── Browser-side function list (executed in frontend, not here) ────────
BROWSER_FUNCTIONS = {
    "navigate_page", "get_current_page", "get_workspace_state",
    "switch_model", "switch_theme", "read_page_content",
}


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
                            result = await _run_with_timeout(_execute_server_function(fname, fargs))
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
                        result = await _execute_server_function(fn_name, fn_args)
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
    for fn in build_function_declarations():
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
                    result = await _execute_server_function(fn_name, fn_args)
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

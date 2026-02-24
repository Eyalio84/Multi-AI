"""VOX voice router — WebSocket for bidirectional audio + REST helpers."""
import asyncio
import base64
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from services.vox_service import vox_service, VoxSession, GEMINI_VOICES, build_function_declarations

router = APIRouter()


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
    return {"functions": build_function_declarations(), "count": len(build_function_declarations())}


class FunctionRunRequest(BaseModel):
    args: dict = {}


@router.post("/api/vox/function/{fn_name}")
async def run_function(fn_name: str, req: FunctionRunRequest):
    """Execute a workspace function server-side (for tools, KG, agents)."""
    result = await _execute_server_function(fn_name, req.args)
    return {"name": fn_name, "result": result}


# ── Server-side function execution ─────────────────────────────────────

async def _execute_server_function(name: str, args: dict) -> dict:
    """Execute workspace functions that need backend access."""
    try:
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

        # ── Direct developer tool shortcuts ───────────────────────────────
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
                session = vox_service.get_session(session_id)
                if session and session.mode == "gemini":
                    await vox_service.send_function_result(
                        session_id, "", fn_name, fn_result
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
                    session.function_count += 1

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
                        # Send result back to Gemini
                        await vox_service.send_function_result(
                            session.session_id, "", fn_name, result
                        )
                    else:
                        # Browser-side: forward to client for execution
                        await ws.send_json({
                            "type": "function_call",
                            "name": fn_name,
                            "args": fn_args,
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
    """Process text through Claude using native tool_use API (replaces regex pattern matching)."""
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

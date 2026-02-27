"""Claude Agent SDK service for autonomous file operations."""
import uuid
from typing import AsyncGenerator, Optional

from config import DEFAULT_CLAUDE_MODEL, PROJECT_ROOT

# Session store: {session_id: {status, prompt, result, ...}}
_sessions: dict[str, dict] = {}


async def run_agent_task(
    prompt: str,
    allowed_tools: Optional[list[str]] = None,
    model: Optional[str] = None,
    cwd: Optional[str] = None,
    max_turns: Optional[int] = None,
    session_id: Optional[str] = None,
) -> AsyncGenerator[dict, None]:
    """
    Run an autonomous Claude agent task with file system access.
    Yields SSE-compatible dicts: {type: text/tool_use/result/error}
    """
    try:
        from claude_agent_sdk import (
            query,
            ClaudeAgentOptions,
            AssistantMessage,
            ResultMessage,
            SystemMessage,
            TextBlock,
            ToolUseBlock,
            CLINotFoundError,
            CLIConnectionError,
            ProcessError,
        )
    except ImportError:
        yield {"type": "error", "content": "claude-agent-sdk not installed. Run: pip install claude-agent-sdk"}
        return

    if allowed_tools is None:
        allowed_tools = ["Read", "Glob", "Grep", "Edit", "Write", "Bash"]

    options_kwargs = {
        "allowed_tools": allowed_tools,
        "permission_mode": "acceptEdits",
        "cwd": cwd or str(PROJECT_ROOT),
    }
    if model:
        options_kwargs["model"] = model
    if max_turns:
        options_kwargs["max_turns"] = max_turns
    if session_id and session_id in _sessions:
        options_kwargs["resume"] = session_id

    task_id = session_id or str(uuid.uuid4())
    _sessions[task_id] = {"status": "running", "prompt": prompt, "result": None}

    try:
        options = ClaudeAgentOptions(**options_kwargs)
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, SystemMessage):
                if hasattr(message, "session_id") and message.session_id:
                    task_id = message.session_id
                    _sessions[task_id] = _sessions.get(task_id, {"prompt": prompt})
                    _sessions[task_id]["status"] = "running"
                yield {"type": "system", "session_id": task_id, "subtype": getattr(message, "subtype", "info")}

            elif isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        yield {"type": "text", "content": block.text}
                    elif isinstance(block, ToolUseBlock):
                        yield {
                            "type": "tool_use",
                            "name": getattr(block, "name", "unknown"),
                            "input": getattr(block, "input", {}),
                        }

            elif isinstance(message, ResultMessage):
                result_text = getattr(message, "result", "")
                _sessions[task_id]["status"] = "completed"
                _sessions[task_id]["result"] = result_text
                yield {"type": "result", "content": result_text, "session_id": task_id}

        if _sessions.get(task_id, {}).get("status") == "running":
            _sessions[task_id]["status"] = "completed"

    except CLINotFoundError:
        _sessions[task_id]["status"] = "error"
        yield {"type": "error", "content": "Claude Code CLI not found. Install with: npm install -g @anthropic-ai/claude-code"}
    except CLIConnectionError as e:
        _sessions[task_id]["status"] = "error"
        yield {"type": "error", "content": f"Connection error: {e}"}
    except ProcessError as e:
        _sessions[task_id]["status"] = "error"
        yield {"type": "error", "content": f"Process error: {e}"}
    except Exception as e:
        _sessions[task_id]["status"] = "error"
        yield {"type": "error", "content": str(e)}

    yield {"type": "done"}


async def list_sessions() -> list[dict]:
    """List recent agent sessions."""
    return [
        {"session_id": sid, **{k: v for k, v in data.items() if k != "result"}}
        for sid, data in _sessions.items()
    ]


async def get_session_status(session_id: str) -> Optional[dict]:
    """Get status of a specific session."""
    if session_id in _sessions:
        return {"session_id": session_id, **_sessions[session_id]}
    return None

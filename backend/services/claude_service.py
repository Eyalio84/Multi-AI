"""Anthropic Claude API service wrapper."""
import json
from typing import AsyncGenerator, Optional

from config import ANTHROPIC_API_KEY, DEFAULT_CLAUDE_MODEL, MODE

_client = None


def _get_client():
    global _client
    if _client is None:
        if not ANTHROPIC_API_KEY:
            raise RuntimeError("Claude API not available in claude-code mode")
        import anthropic
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


def _convert_messages(messages: list[dict]) -> list[dict]:
    """Convert frontend message format to Anthropic message format."""
    result = []
    for msg in messages:
        author = msg.get("author", "user")
        if author == "user":
            role = "user"
        elif author == "assistant":
            role = "assistant"
        elif author == "tool":
            # Tool results go as user messages with tool_result content
            tr = msg.get("toolResponse", {})
            result.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": tr.get("tool_use_id", ""),
                    "content": json.dumps(tr.get("response", {}).get("content", "")),
                }],
            })
            continue
        else:
            continue

        content = []
        for part in msg.get("parts", []):
            if part.get("text"):
                content.append({"type": "text", "text": part["text"]})

        # If assistant message had a tool call, add tool_use block
        if author == "assistant" and msg.get("toolCall"):
            tc = msg["toolCall"]
            content.append({
                "type": "tool_use",
                "id": tc.get("id", ""),
                "name": tc["name"],
                "input": tc.get("args", {}),
            })

        if content:
            result.append({"role": role, "content": content})
    return result


async def stream_chat(
    messages: list[dict],
    model: str = DEFAULT_CLAUDE_MODEL,
    system: Optional[str] = None,
    max_tokens: int = 8192,
    temperature: float = 1.0,
) -> AsyncGenerator[dict, None]:
    """Stream a chat response as SSE-compatible dicts."""
    if MODE != "standalone":
        yield {"type": "error", "content": "Claude API not available in claude-code mode. Use Export to Claude Code instead."}
        yield {"type": "done"}
        return

    client = _get_client()
    converted = _convert_messages(messages)

    kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": converted,
        "temperature": temperature,
    }
    if system:
        kwargs["system"] = system

    with client.messages.stream(**kwargs) as stream:
        for event in stream:
            if event.type == "content_block_delta":
                if hasattr(event.delta, "text"):
                    yield {"type": "token", "content": event.delta.text}
            elif event.type == "message_stop":
                break

    yield {"type": "done"}


async def stream_with_tools(
    messages: list[dict],
    tools: list[dict],
    model: str = DEFAULT_CLAUDE_MODEL,
    system: Optional[str] = None,
    max_tokens: int = 8192,
    temperature: float = 1.0,
) -> AsyncGenerator[dict, None]:
    """Stream with tool use support."""
    if MODE != "standalone":
        yield {"type": "error", "content": "Claude API not available in claude-code mode."}
        yield {"type": "done"}
        return

    client = _get_client()
    converted = _convert_messages(messages)

    kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": converted,
        "tools": tools,
        "temperature": temperature,
    }
    if system:
        kwargs["system"] = system

    with client.messages.stream(**kwargs) as stream:
        for event in stream:
            if event.type == "content_block_start":
                if hasattr(event.content_block, "type"):
                    if event.content_block.type == "tool_use":
                        yield {
                            "type": "tool_call_start",
                            "id": event.content_block.id,
                            "name": event.content_block.name,
                        }
            elif event.type == "content_block_delta":
                if hasattr(event.delta, "text"):
                    yield {"type": "token", "content": event.delta.text}
                elif hasattr(event.delta, "partial_json"):
                    yield {"type": "tool_call_delta", "content": event.delta.partial_json}
            elif event.type == "content_block_stop":
                pass
            elif event.type == "message_stop":
                break

    yield {"type": "done"}


async def stream_with_thinking(
    messages: list[dict],
    model: str = DEFAULT_CLAUDE_MODEL,
    system: Optional[str] = None,
    thinking_budget: int = 10000,
    max_tokens: int = 16384,
) -> AsyncGenerator[dict, None]:
    """Stream with extended thinking enabled."""
    if MODE != "standalone":
        yield {"type": "error", "content": "Claude API not available in claude-code mode."}
        yield {"type": "done"}
        return

    client = _get_client()
    converted = _convert_messages(messages)

    kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": converted,
        "thinking": {
            "type": "enabled",
            "budget_tokens": thinking_budget,
        },
        "temperature": 1.0,  # Required for extended thinking
    }
    if system:
        kwargs["system"] = system

    with client.messages.stream(**kwargs) as stream:
        for event in stream:
            if event.type == "content_block_start":
                if hasattr(event.content_block, "type"):
                    if event.content_block.type == "thinking":
                        yield {"type": "thinking_start"}
            elif event.type == "content_block_delta":
                if hasattr(event.delta, "thinking"):
                    yield {"type": "thinking", "content": event.delta.thinking}
                elif hasattr(event.delta, "text"):
                    yield {"type": "token", "content": event.delta.text}
            elif event.type == "message_stop":
                break

    yield {"type": "done"}

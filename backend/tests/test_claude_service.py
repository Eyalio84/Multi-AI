"""Integration tests for Claude (Anthropic) API service.

These tests make REAL API calls to Anthropic's Claude API.
They require a valid ANTHROPIC_API_KEY and network access.

Run:
    python -m pytest backend/tests/test_claude_service.py -v
    python -m unittest backend.tests.test_claude_service -v
"""
import asyncio
import unittest
import sys
from pathlib import Path

# Ensure imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests.conftest import (
    ANTHROPIC_API_KEY,
    SIMPLE_USER_MESSAGE,
    CLAUDE_TOOL_DEFINITIONS,
    API_TIMEOUT,
)


def _run_async(coro):
    """Run an async coroutine synchronously and return the result."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _collect_stream(async_gen):
    """Collect all chunks from an async generator into a list."""
    chunks = []
    async for chunk in async_gen:
        chunks.append(chunk)
    return chunks


class TestClaudeStreamChat(unittest.TestCase):
    """Test streaming chat via Claude Sonnet."""

    @unittest.skipUnless(ANTHROPIC_API_KEY, "ANTHROPIC_API_KEY not set")
    def test_claude_stream_chat(self):
        """Stream 'Hello' via Sonnet, verify tokens."""
        from services import claude_service

        async def _run():
            chunks = await _collect_stream(
                claude_service.stream_chat(
                    messages=SIMPLE_USER_MESSAGE,
                    model="claude-sonnet-4-6",
                    max_tokens=256,
                    temperature=0.5,
                )
            )
            return chunks

        chunks = _run_async(asyncio.wait_for(_run(), timeout=API_TIMEOUT))

        token_chunks = [c for c in chunks if c.get("type") == "token"]
        done_chunks = [c for c in chunks if c.get("type") == "done"]

        self.assertGreater(
            len(token_chunks), 0,
            "Expected at least one token chunk from Claude stream",
        )
        self.assertEqual(
            len(done_chunks), 1,
            "Expected exactly one 'done' chunk from Claude stream",
        )

        # Verify content strings
        for tc in token_chunks:
            self.assertIn("content", tc)
            self.assertIsInstance(tc["content"], str)

        full_text = "".join(tc["content"] for tc in token_chunks)
        self.assertGreater(len(full_text), 0, "Combined streamed text should not be empty")


class TestClaudeWithTools(unittest.TestCase):
    """Test streaming with tool definitions."""

    @unittest.skipUnless(ANTHROPIC_API_KEY, "ANTHROPIC_API_KEY not set")
    def test_claude_with_tools(self):
        """Stream with tool definitions, verify response contains tokens or tool call events."""
        from services import claude_service

        tool_trigger_message = [
            {
                "author": "user",
                "parts": [{"text": "What is the weather in San Francisco?"}],
            }
        ]

        async def _run():
            chunks = await _collect_stream(
                claude_service.stream_with_tools(
                    messages=tool_trigger_message,
                    tools=CLAUDE_TOOL_DEFINITIONS,
                    model="claude-sonnet-4-6",
                    max_tokens=512,
                    temperature=0.0,
                )
            )
            return chunks

        chunks = _run_async(asyncio.wait_for(_run(), timeout=API_TIMEOUT))

        token_chunks = [c for c in chunks if c.get("type") == "token"]
        tool_start_chunks = [c for c in chunks if c.get("type") == "tool_call_start"]
        tool_delta_chunks = [c for c in chunks if c.get("type") == "tool_call_delta"]
        done_chunks = [c for c in chunks if c.get("type") == "done"]

        has_content = len(token_chunks) > 0 or len(tool_start_chunks) > 0
        self.assertTrue(
            has_content,
            "Expected either token or tool_call_start chunks from Claude with tools",
        )
        self.assertEqual(len(done_chunks), 1, "Expected exactly one 'done' chunk")

        # If tool call started, verify structure
        if tool_start_chunks:
            ts = tool_start_chunks[0]
            self.assertIn("name", ts, "tool_call_start must have 'name'")
            self.assertEqual(ts["name"], "get_weather")
            self.assertIn("id", ts, "tool_call_start must have 'id'")
            self.assertIsInstance(ts["id"], str)


class TestClaudeWithThinking(unittest.TestCase):
    """Test streaming with extended thinking enabled."""

    @unittest.skipUnless(ANTHROPIC_API_KEY, "ANTHROPIC_API_KEY not set")
    def test_claude_with_thinking(self):
        """Stream with extended thinking, verify thinking blocks appear."""
        from services import claude_service

        thinking_message = [
            {
                "author": "user",
                "parts": [{"text": "What is 17 * 23? Think step by step."}],
            }
        ]

        async def _run():
            chunks = await _collect_stream(
                claude_service.stream_with_thinking(
                    messages=thinking_message,
                    model="claude-sonnet-4-6",
                    thinking_budget=4096,
                    max_tokens=8192,
                )
            )
            return chunks

        chunks = _run_async(asyncio.wait_for(_run(), timeout=API_TIMEOUT))

        thinking_start_chunks = [c for c in chunks if c.get("type") == "thinking_start"]
        thinking_chunks = [c for c in chunks if c.get("type") == "thinking"]
        token_chunks = [c for c in chunks if c.get("type") == "token"]
        done_chunks = [c for c in chunks if c.get("type") == "done"]

        # Should have thinking blocks
        self.assertGreater(
            len(thinking_start_chunks), 0,
            "Expected at least one 'thinking_start' chunk with extended thinking",
        )
        self.assertGreater(
            len(thinking_chunks), 0,
            "Expected at least one 'thinking' content chunk",
        )

        # Should also have regular text output
        self.assertGreater(
            len(token_chunks), 0,
            "Expected at least one 'token' chunk after thinking",
        )
        self.assertEqual(len(done_chunks), 1, "Expected exactly one 'done' chunk")

        # Thinking content should be strings
        for tc in thinking_chunks:
            self.assertIn("content", tc)
            self.assertIsInstance(tc["content"], str)

        # Verify the answer contains 391 (17 * 23 = 391)
        full_text = "".join(tc["content"] for tc in token_chunks)
        self.assertIn(
            "391", full_text,
            f"Expected answer to contain '391' (17*23), got: {full_text[:200]}",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

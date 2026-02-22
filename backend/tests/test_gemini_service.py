"""Integration tests for Gemini API service.

These tests make REAL API calls to Google's Gemini API.
They require a valid GEMINI_API_KEY and network access.

Run:
    python -m pytest backend/tests/test_gemini_service.py -v
    python -m unittest backend.tests.test_gemini_service -v
"""
import asyncio
import unittest
import sys
from pathlib import Path

# Ensure imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests.conftest import (
    GEMINI_API_KEY,
    SIMPLE_USER_MESSAGE,
    GEMINI_TOOL_DECLARATIONS,
    API_TIMEOUT,
)


def _run_async(coro):
    """Run an async generator / coroutine synchronously and return results."""
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


class TestGeminiStreamChat(unittest.TestCase):
    """Test streaming chat via Gemini Flash."""

    @unittest.skipUnless(GEMINI_API_KEY, "GEMINI_API_KEY not set")
    def test_gemini_stream_chat(self):
        """Stream a simple 'Hello' message via Gemini Flash, verify we get tokens back."""
        from services import gemini_service

        async def _run():
            chunks = await _collect_stream(
                gemini_service.stream_chat(
                    messages=SIMPLE_USER_MESSAGE,
                    model="gemini-2.5-flash",
                    temperature=0.5,
                )
            )
            return chunks

        chunks = _run_async(asyncio.wait_for(_run(), timeout=API_TIMEOUT))

        # Must have at least one token chunk and a done chunk
        token_chunks = [c for c in chunks if c.get("type") == "token"]
        done_chunks = [c for c in chunks if c.get("type") == "done"]

        self.assertGreater(
            len(token_chunks), 0,
            "Expected at least one token chunk from Gemini stream",
        )
        self.assertEqual(
            len(done_chunks), 1,
            "Expected exactly one 'done' chunk from Gemini stream",
        )

        # Token content should be non-empty strings
        for tc in token_chunks:
            self.assertIn("content", tc)
            self.assertIsInstance(tc["content"], str)

        # Verify combined text is non-trivial
        full_text = "".join(tc["content"] for tc in token_chunks)
        self.assertGreater(len(full_text), 0, "Combined streamed text should not be empty")


class TestGeminiGenerateContent(unittest.TestCase):
    """Test synchronous content generation via Gemini."""

    @unittest.skipUnless(GEMINI_API_KEY, "GEMINI_API_KEY not set")
    def test_gemini_generate_content(self):
        """Full sync response, verify non-empty text."""
        from services import gemini_service

        result = gemini_service.generate_content(
            prompt="Say hello in exactly one sentence.",
            model="gemini-2.5-flash",
        )

        self.assertIsInstance(result, str)
        self.assertGreater(len(result.strip()), 0, "Response text should not be empty")


class TestGeminiWithTools(unittest.TestCase):
    """Test streaming with function calling (tool declarations)."""

    @unittest.skipUnless(GEMINI_API_KEY, "GEMINI_API_KEY not set")
    def test_gemini_with_tools(self):
        """Send a message with tool declarations, verify response contains text or function call."""
        from services import gemini_service

        tool_trigger_message = [
            {
                "author": "user",
                "parts": [{"text": "What is the weather in San Francisco right now?"}],
            }
        ]

        async def _run():
            chunks = await _collect_stream(
                gemini_service.stream_with_tools(
                    messages=tool_trigger_message,
                    tool_declarations=GEMINI_TOOL_DECLARATIONS,
                    model="gemini-2.5-flash",
                    temperature=0.0,
                )
            )
            return chunks

        chunks = _run_async(asyncio.wait_for(_run(), timeout=API_TIMEOUT))

        # Should get either token chunks (text) or tool_call chunks (function call)
        token_chunks = [c for c in chunks if c.get("type") == "token"]
        tool_call_chunks = [c for c in chunks if c.get("type") == "tool_call"]
        done_chunks = [c for c in chunks if c.get("type") == "done"]

        has_content = len(token_chunks) > 0 or len(tool_call_chunks) > 0
        self.assertTrue(
            has_content,
            "Expected either token or tool_call chunks from Gemini with tools",
        )
        self.assertEqual(len(done_chunks), 1, "Expected exactly one 'done' chunk")

        # If tool call present, verify structure
        if tool_call_chunks:
            tc = tool_call_chunks[0]
            self.assertIn("name", tc, "Tool call chunk must have 'name'")
            self.assertEqual(tc["name"], "get_weather")
            self.assertIn("args", tc, "Tool call chunk must have 'args'")
            self.assertIsInstance(tc["args"], dict)


if __name__ == "__main__":
    unittest.main(verbosity=2)

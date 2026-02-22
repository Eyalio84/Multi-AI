"""Integration tests for FastAPI endpoints using httpx AsyncClient.

Tests the HTTP layer: status codes, response shapes, SSE streaming format.
API-calling endpoints (chat/stream) make REAL API calls and are marked as
integration tests.

Run:
    python -m pytest backend/tests/test_api_endpoints.py -v
    python -m unittest backend.tests.test_api_endpoints -v
"""
import asyncio
import json
import unittest
import sys
from pathlib import Path

# Ensure imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests.conftest import (
    GEMINI_API_KEY,
    ANTHROPIC_API_KEY,
    API_TIMEOUT,
    get_app,
)


def _run_async(coro):
    """Run an async coroutine synchronously."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class TestHealthEndpoint(unittest.TestCase):
    """GET /api/health"""

    def test_health_endpoint(self):
        """Health endpoint returns status ok with mode and key flags."""
        import httpx

        app = get_app()

        async def _run():
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
            ) as client:
                resp = await client.get("/api/health")
                return resp

        resp = _run_async(_run())

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("mode", data)
        self.assertIn("gemini_configured", data)
        self.assertIn("claude_configured", data)
        self.assertIsInstance(data["gemini_configured"], bool)
        self.assertIsInstance(data["claude_configured"], bool)


class TestModelsEndpoint(unittest.TestCase):
    """GET /api/models"""

    def test_models_endpoint(self):
        """Models endpoint returns gemini models (and claude in standalone)."""
        import httpx

        app = get_app()

        async def _run():
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
            ) as client:
                resp = await client.get("/api/models")
                return resp

        resp = _run_async(_run())

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("gemini", data)
        self.assertIsInstance(data["gemini"], dict)
        self.assertGreater(len(data["gemini"]), 0, "Should have at least one Gemini model")

        # In standalone mode, Claude models should also be present
        if data.get("claude"):
            self.assertIsInstance(data["claude"], dict)
            self.assertGreater(len(data["claude"]), 0)


class TestModeEndpoint(unittest.TestCase):
    """The health endpoint implicitly exposes the mode."""

    def test_mode_endpoint(self):
        """Health endpoint mode field should be 'standalone' in test env."""
        import httpx

        app = get_app()

        async def _run():
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
            ) as client:
                resp = await client.get("/api/health")
                return resp

        resp = _run_async(_run())
        data = resp.json()
        self.assertEqual(
            data["mode"], "standalone",
            "Test environment should run in standalone mode",
        )


class TestAgentsList(unittest.TestCase):
    """GET /api/agents"""

    def test_agents_list(self):
        """Agents endpoint returns a list of agent metadata."""
        import httpx

        app = get_app()

        async def _run():
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
            ) as client:
                resp = await client.get("/api/agents")
                return resp

        resp = _run_async(_run())

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("agents", data)
        agents = data["agents"]
        self.assertIsInstance(agents, list)
        self.assertGreater(len(agents), 0, "Should have at least one agent")

        # Verify agent structure
        first = agents[0]
        self.assertIn("name", first)
        self.assertIn("category", first)
        self.assertIn("description", first)


class TestPlaybooksList(unittest.TestCase):
    """GET /api/playbooks"""

    def test_playbooks_list(self):
        """Playbooks endpoint returns a list (may be empty if no .pb files)."""
        import httpx

        app = get_app()

        async def _run():
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
            ) as client:
                resp = await client.get("/api/playbooks")
                return resp

        resp = _run_async(_run())

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("playbooks", data)
        self.assertIsInstance(data["playbooks"], list)


class TestWorkflowTemplates(unittest.TestCase):
    """GET /api/workflows/templates"""

    def test_workflow_templates(self):
        """Workflow templates endpoint returns built-in templates."""
        import httpx

        app = get_app()

        async def _run():
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
            ) as client:
                resp = await client.get("/api/workflows/templates")
                return resp

        resp = _run_async(_run())

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("templates", data)
        templates = data["templates"]
        self.assertIsInstance(templates, list)
        self.assertGreater(len(templates), 0, "Should have at least one workflow template")

        # Verify template structure
        first = templates[0]
        self.assertIn("id", first)
        self.assertIn("name", first)
        self.assertIn("description", first)
        self.assertIn("step_count", first)
        self.assertIn("steps", first)
        self.assertIsInstance(first["steps"], list)
        self.assertGreater(first["step_count"], 0)


class TestChatStreamGemini(unittest.TestCase):
    """POST /api/chat/stream with provider=gemini -- INTEGRATION TEST."""

    @unittest.skipUnless(GEMINI_API_KEY, "GEMINI_API_KEY not set")
    def test_chat_stream_gemini(self):
        """POST to chat/stream with Gemini provider, verify SSE format."""
        import httpx

        app = get_app()

        payload = {
            "messages": [
                {
                    "author": "user",
                    "parts": [{"text": "Say hello in one word."}],
                }
            ],
            "provider": "gemini",
            "model": "gemini-2.5-flash",
        }

        async def _run():
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
            ) as client:
                resp = await client.post(
                    "/api/chat/stream",
                    json=payload,
                    timeout=API_TIMEOUT,
                )
                return resp

        resp = _run_async(asyncio.wait_for(_run(), timeout=API_TIMEOUT + 5))

        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/event-stream", resp.headers.get("content-type", ""))

        # Parse SSE lines
        body = resp.text
        events = []
        for line in body.split("\n"):
            line = line.strip()
            if line.startswith("data: "):
                try:
                    event = json.loads(line[6:])
                    events.append(event)
                except json.JSONDecodeError:
                    pass

        self.assertGreater(len(events), 0, "Should receive at least one SSE event")

        # Should contain token events and a done event
        types_seen = {e.get("type") for e in events}
        self.assertIn("done", types_seen, "SSE stream should end with a 'done' event")

        token_events = [e for e in events if e.get("type") == "token"]
        self.assertGreater(
            len(token_events), 0,
            "Should receive at least one 'token' SSE event from Gemini",
        )


class TestChatStreamClaude(unittest.TestCase):
    """POST /api/chat/stream with provider=claude -- INTEGRATION TEST."""

    @unittest.skipUnless(ANTHROPIC_API_KEY, "ANTHROPIC_API_KEY not set")
    def test_chat_stream_claude(self):
        """POST to chat/stream with Claude provider, verify SSE format."""
        import httpx

        app = get_app()

        payload = {
            "messages": [
                {
                    "author": "user",
                    "parts": [{"text": "Say hello in one word."}],
                }
            ],
            "provider": "claude",
            "model": "claude-sonnet-4-6",
        }

        async def _run():
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
            ) as client:
                resp = await client.post(
                    "/api/chat/stream",
                    json=payload,
                    timeout=API_TIMEOUT,
                )
                return resp

        resp = _run_async(asyncio.wait_for(_run(), timeout=API_TIMEOUT + 5))

        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/event-stream", resp.headers.get("content-type", ""))

        # Parse SSE lines
        body = resp.text
        events = []
        for line in body.split("\n"):
            line = line.strip()
            if line.startswith("data: "):
                try:
                    event = json.loads(line[6:])
                    events.append(event)
                except json.JSONDecodeError:
                    pass

        self.assertGreater(len(events), 0, "Should receive at least one SSE event")

        types_seen = {e.get("type") for e in events}
        self.assertIn("done", types_seen, "SSE stream should end with a 'done' event")

        token_events = [e for e in events if e.get("type") == "token"]
        self.assertGreater(
            len(token_events), 0,
            "Should receive at least one 'token' SSE event from Claude",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

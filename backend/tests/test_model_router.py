"""Unit tests for model routing logic.

These tests do NOT make API calls -- they test the deterministic routing
logic in services.model_router.route().

Run:
    python -m pytest backend/tests/test_model_router.py -v
    python -m unittest backend.tests.test_model_router -v
"""
import os
import unittest
import sys
from pathlib import Path
from unittest.mock import patch

# Ensure imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestRouteVideo(unittest.TestCase):
    """Video tasks should always route to Gemini Veo."""

    def test_route_video(self):
        """task_type='video' -> Gemini veo-2.0-generate-001."""
        from services.model_router import route

        result = route(task_type="video")

        self.assertEqual(result["provider"], "gemini")
        self.assertEqual(result["model"], "veo-2.0-generate-001")
        self.assertIn("Video", result["reason"])

    def test_route_video_ignores_budget(self):
        """Video routing ignores budget_preference."""
        from services.model_router import route

        for budget in ("cheap", "balanced", "quality"):
            result = route(task_type="video", budget_preference=budget)
            self.assertEqual(result["model"], "veo-2.0-generate-001")

    def test_route_video_ignores_complexity(self):
        """Video routing ignores complexity."""
        from services.model_router import route

        for complexity in ("low", "medium", "high"):
            result = route(task_type="video", complexity=complexity)
            self.assertEqual(result["model"], "veo-2.0-generate-001")


class TestRouteCodingComplex(unittest.TestCase):
    """Complex coding should route to Claude."""

    def test_route_coding_complex(self):
        """task_type='coding', complexity='high' -> Claude Sonnet."""
        from services.model_router import route

        result = route(task_type="coding", complexity="high")

        self.assertEqual(result["provider"], "claude")
        self.assertEqual(result["model"], "claude-sonnet-4-6")
        self.assertIn("Claude", result["reason"])

    def test_route_coding_simple_goes_gemini(self):
        """Simple coding goes to Gemini Flash for speed."""
        from services.model_router import route

        result = route(task_type="coding", complexity="medium")

        self.assertEqual(result["provider"], "gemini")
        self.assertIn("Flash", result["reason"])


class TestRouteLargeContext(unittest.TestCase):
    """Large context (>150K tokens) should route to Gemini."""

    def test_route_large_context(self):
        """context_length > 150000 -> Gemini Pro with 1M window."""
        from services.model_router import route

        result = route(context_length=200000)

        self.assertEqual(result["provider"], "gemini")
        self.assertEqual(result["model"], "gemini-2.5-pro")
        self.assertIn("1M", result["reason"])

    def test_route_exactly_at_boundary(self):
        """context_length == 150000 should NOT trigger large context routing."""
        from services.model_router import route

        result = route(context_length=150000)

        # 150000 is not > 150000, so it should NOT route as large context
        # It will follow normal routing (default balanced -> gemini flash)
        self.assertNotIn("1M", result.get("reason", ""))

    def test_route_well_over_boundary(self):
        """context_length = 500000 -> Gemini Pro."""
        from services.model_router import route

        result = route(context_length=500000, task_type="reasoning", complexity="high")
        self.assertEqual(result["provider"], "gemini")
        self.assertEqual(result["model"], "gemini-2.5-pro")


class TestRouteClaudeCodeMode(unittest.TestCase):
    """In claude-code mode, everything should route to Gemini."""

    def test_route_claude_code_mode(self):
        """MODE='claude-code' -> always Gemini, even for coding/reasoning."""
        import services.model_router as router_module
        import config as config_module

        original_mode = config_module.MODE
        try:
            # Patch MODE in both the config module and the router module
            config_module.MODE = "claude-code"
            # The router imports MODE from config, so we need to reload
            # or patch it at the source
            with patch.object(router_module, "MODE", "claude-code"):
                result = router_module.route(
                    task_type="coding", complexity="high", budget_preference="quality"
                )
                self.assertEqual(
                    result["provider"], "gemini",
                    "In claude-code mode, provider must always be gemini",
                )
                self.assertIn("claude-code", result["reason"])

                # Also test reasoning
                result2 = router_module.route(
                    task_type="reasoning", complexity="high"
                )
                self.assertEqual(result2["provider"], "gemini")

                # And cheap
                result3 = router_module.route(
                    task_type="general", budget_preference="cheap", complexity="low"
                )
                self.assertEqual(result3["provider"], "gemini")
                self.assertIn("Flash", result3["model"])
        finally:
            config_module.MODE = original_mode

    def test_route_claude_code_mode_cheap_gets_flash(self):
        """In claude-code mode, cheap preference gets Flash."""
        import services.model_router as router_module

        with patch.object(router_module, "MODE", "claude-code"):
            result = router_module.route(
                task_type="general", complexity="low", budget_preference="cheap"
            )
            self.assertEqual(result["provider"], "gemini")
            self.assertIn("flash", result["model"].lower())


class TestRouteEdgeCases(unittest.TestCase):
    """Additional routing edge cases."""

    def test_route_image(self):
        """Image tasks -> Gemini image model."""
        from services.model_router import route

        result = route(task_type="image")
        self.assertEqual(result["provider"], "gemini")
        self.assertIn("native-audio-dialog", result["model"])

    def test_route_embedding(self):
        """Embedding tasks -> Gemini embedding model."""
        from services.model_router import route

        result = route(task_type="embedding")
        self.assertEqual(result["provider"], "gemini")
        self.assertEqual(result["model"], "gemini-embedding-001")

    def test_route_quality_preference(self):
        """Quality budget preference -> Claude Opus."""
        from services.model_router import route

        result = route(budget_preference="quality")
        self.assertEqual(result["provider"], "claude")
        self.assertEqual(result["model"], "claude-opus-4-6")

    def test_route_reasoning_high(self):
        """High complexity reasoning -> Claude Opus."""
        from services.model_router import route

        result = route(task_type="reasoning", complexity="high")
        self.assertEqual(result["provider"], "claude")
        self.assertEqual(result["model"], "claude-opus-4-6")

    def test_route_cheap_low(self):
        """Cheap + low complexity -> Gemini Flash."""
        from services.model_router import route

        result = route(budget_preference="cheap", complexity="low")
        self.assertEqual(result["provider"], "gemini")
        self.assertIn("flash", result["model"].lower())

    def test_route_cheap_medium(self):
        """Cheap + medium complexity -> Claude Haiku."""
        from services.model_router import route

        result = route(budget_preference="cheap", complexity="medium")
        self.assertEqual(result["provider"], "claude")
        self.assertIn("haiku", result["model"].lower())

    def test_route_default(self):
        """Default (no args) -> Gemini Flash for general tasks."""
        from services.model_router import route

        result = route()
        self.assertEqual(result["provider"], "gemini")
        self.assertIn("flash", result["model"].lower())

    def test_route_returns_required_keys(self):
        """Every route result must have provider, model, reason."""
        from services.model_router import route

        for task in ("general", "coding", "reasoning", "creative", "video", "image", "embedding"):
            for comp in ("low", "medium", "high"):
                result = route(task_type=task, complexity=comp)
                self.assertIn("provider", result, f"Missing 'provider' for {task}/{comp}")
                self.assertIn("model", result, f"Missing 'model' for {task}/{comp}")
                self.assertIn("reason", result, f"Missing 'reason' for {task}/{comp}")


if __name__ == "__main__":
    unittest.main(verbosity=2)

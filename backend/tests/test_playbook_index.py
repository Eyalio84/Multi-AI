"""Unit tests for the PlaybookIndex service.

These tests exercise the playbook parsing, listing, search, and category
logic. They do NOT make API calls.

Run:
    python -m pytest backend/tests/test_playbook_index.py -v
    python -m unittest backend.tests.test_playbook_index -v
"""
import unittest
import sys
from pathlib import Path

# Ensure imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestPlaybookListAll(unittest.TestCase):
    """Test PlaybookIndex.list_all()."""

    def test_list_all(self):
        """list_all() returns a list of dicts without 'content' key."""
        from services.playbook_index import PlaybookIndex

        index = PlaybookIndex()
        results = index.list_all()

        self.assertIsInstance(results, list)

        # Each entry should be a dict with expected metadata keys
        for item in results:
            self.assertIsInstance(item, dict)
            self.assertIn("filename", item)
            self.assertIn("title", item)
            self.assertIn("category", item)
            self.assertIn("difficulty", item)
            self.assertIn("sections", item)
            self.assertIn("word_count", item)
            # Content should be excluded from list_all
            self.assertNotIn(
                "content", item,
                "list_all() should exclude the 'content' field",
            )

    def test_list_all_returns_consistent_results(self):
        """Calling list_all() twice returns the same data."""
        from services.playbook_index import PlaybookIndex

        index = PlaybookIndex()
        first = index.list_all()
        second = index.list_all()
        self.assertEqual(len(first), len(second))
        for a, b in zip(first, second):
            self.assertEqual(a["filename"], b["filename"])


class TestPlaybookSearch(unittest.TestCase):
    """Test PlaybookIndex.search()."""

    def test_search(self):
        """search() returns scored results as a list of dicts."""
        from services.playbook_index import PlaybookIndex

        index = PlaybookIndex()
        results = index.search("agent")

        self.assertIsInstance(results, list)

        # Every result should have a score
        for item in results:
            self.assertIsInstance(item, dict)
            self.assertIn("score", item)
            self.assertGreater(item["score"], 0, "Score must be positive for matches")
            self.assertIn("filename", item)
            self.assertIn("title", item)
            # Content should be excluded
            self.assertNotIn("content", item)

    def test_search_empty_query_returns_nothing(self):
        """Searching for a nonsense string returns empty list or no results."""
        from services.playbook_index import PlaybookIndex

        index = PlaybookIndex()
        results = index.search("xyzzy_nonexistent_term_42")
        self.assertIsInstance(results, list)
        # All scores should be 0, meaning no results returned
        self.assertEqual(len(results), 0, "Nonsense query should match nothing")

    def test_search_results_sorted_by_score(self):
        """Results should be sorted descending by score."""
        from services.playbook_index import PlaybookIndex

        index = PlaybookIndex()
        results = index.search("cost")

        if len(results) > 1:
            scores = [r["score"] for r in results]
            self.assertEqual(
                scores, sorted(scores, reverse=True),
                "Search results should be sorted by score descending",
            )

    def test_search_with_category_filter(self):
        """search() with category parameter filters correctly."""
        from services.playbook_index import PlaybookIndex

        index = PlaybookIndex()
        all_results = index.search("agent")
        filtered = index.search("agent", category="AGENT")

        # Filtered results should be a subset
        self.assertLessEqual(len(filtered), len(all_results))

        for item in filtered:
            self.assertEqual(
                item["category"], "AGENT",
                "Filtered results should all have the specified category",
            )


class TestPlaybookCategories(unittest.TestCase):
    """Test PlaybookIndex.list_categories()."""

    def test_categories(self):
        """list_categories() returns list of {name, count} dicts."""
        from services.playbook_index import PlaybookIndex

        index = PlaybookIndex()
        categories = index.list_categories()

        self.assertIsInstance(categories, list)

        for cat in categories:
            self.assertIsInstance(cat, dict)
            self.assertIn("name", cat)
            self.assertIn("count", cat)
            self.assertIsInstance(cat["name"], str)
            self.assertIsInstance(cat["count"], int)
            self.assertGreater(cat["count"], 0, "Each category should have at least one playbook")

    def test_categories_counts_match_list_all(self):
        """Sum of category counts should equal total playbooks."""
        from services.playbook_index import PlaybookIndex

        index = PlaybookIndex()
        all_pbs = index.list_all()
        categories = index.list_categories()

        total_from_categories = sum(c["count"] for c in categories)
        self.assertEqual(
            total_from_categories, len(all_pbs),
            "Sum of category counts should equal total playbook count",
        )


class TestPlaybookGetByFilename(unittest.TestCase):
    """Test PlaybookIndex.get_playbook()."""

    def test_get_existing_playbook(self):
        """get_playbook() returns full content for a known filename."""
        from services.playbook_index import PlaybookIndex

        index = PlaybookIndex()
        all_pbs = index.list_all()

        if all_pbs:
            filename = all_pbs[0]["filename"]
            result = index.get_playbook(filename)
            self.assertIsNotNone(result, f"Should find playbook: {filename}")
            self.assertIn("content", result, "get_playbook should include content")
            self.assertEqual(result["filename"], filename)

    def test_get_nonexistent_playbook(self):
        """get_playbook() returns None for unknown filename."""
        from services.playbook_index import PlaybookIndex

        index = PlaybookIndex()
        result = index.get_playbook("nonexistent_playbook_xyz.pb")
        self.assertIsNone(result, "Should return None for unknown filename")


if __name__ == "__main__":
    unittest.main(verbosity=2)

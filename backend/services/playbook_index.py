"""Parse and index playbook .pb files for search and retrieval."""
import re
from pathlib import Path
from typing import Optional

from config import PLAYBOOKS_DIR

# Category mapping from filename prefixes
CATEGORIES = {
    "FOUND": "FOUNDATION",
    "DEV": "DEV",
    "AGENT": "AGENT",
    "KNOW": "KNOWLEDGE",
    "REASON": "REASONING",
    "SPEC": "SPECIALIZED",
    "ORCH": "ORCHESTRATION",
}


class PlaybookIndex:
    """In-memory index of playbook files."""

    def __init__(self):
        self._playbooks: list[dict] = []
        self._loaded = False

    def _ensure_loaded(self):
        if self._loaded:
            return
        self._load_playbooks()
        self._loaded = True

    def _load_playbooks(self):
        """Scan playbooks directory and parse all .pb files."""
        pb_dir = Path(PLAYBOOKS_DIR)
        if not pb_dir.exists():
            return

        for pb_file in sorted(pb_dir.glob("*.pb")):
            try:
                content = pb_file.read_text(encoding="utf-8", errors="replace")
                meta = self._parse_metadata(content, pb_file.name)
                self._playbooks.append(meta)
            except Exception:
                continue

    def _parse_metadata(self, content: str, filename: str) -> dict:
        """Extract metadata from playbook content."""
        lines = content.split("\n")

        # Extract title (first heading or first line)
        title = filename.replace(".pb", "").replace("-", " ").title()
        for line in lines[:10]:
            if line.startswith("# "):
                title = line[2:].strip()
                break
            if line.startswith("PLAYBOOK:") or line.startswith("Title:"):
                title = line.split(":", 1)[1].strip()
                break

        # Detect category from filename
        category = "GENERAL"
        upper_name = filename.upper()
        for prefix, cat in CATEGORIES.items():
            if prefix in upper_name:
                category = cat
                break

        # Extract section headers
        sections = [line[2:].strip() for line in lines if line.startswith("## ")]

        # Extract difficulty if present
        difficulty = "intermediate"
        for line in lines[:20]:
            lower_line = line.lower()
            if "difficulty:" in lower_line or "level:" in lower_line:
                if "beginner" in lower_line:
                    difficulty = "beginner"
                elif "advanced" in lower_line:
                    difficulty = "advanced"
                elif "expert" in lower_line:
                    difficulty = "expert"
                break

        return {
            "filename": filename,
            "title": title,
            "category": category,
            "difficulty": difficulty,
            "sections": sections,
            "content": content,
            "word_count": len(content.split()),
        }

    def list_all(self) -> list[dict]:
        """Return all playbooks with metadata (no content)."""
        self._ensure_loaded()
        return [
            {k: v for k, v in pb.items() if k != "content"}
            for pb in self._playbooks
        ]

    def search(self, query: str, category: Optional[str] = None) -> list[dict]:
        """Search playbooks by keyword."""
        self._ensure_loaded()
        query_lower = query.lower()
        keywords = query_lower.split()

        results = []
        for pb in self._playbooks:
            if category and pb["category"] != category:
                continue

            # Score based on keyword matches
            score = 0
            searchable = f"{pb['title']} {pb['category']} {' '.join(pb['sections'])}".lower()
            content_lower = pb["content"].lower()

            for kw in keywords:
                if kw in pb["title"].lower():
                    score += 10
                if kw in searchable:
                    score += 5
                if kw in content_lower:
                    score += 1

            if score > 0:
                results.append({
                    **{k: v for k, v in pb.items() if k != "content"},
                    "score": score,
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    def get_playbook(self, filename: str) -> Optional[dict]:
        """Get full playbook content by filename."""
        self._ensure_loaded()
        for pb in self._playbooks:
            if pb["filename"] == filename:
                return pb
        return None

    def list_categories(self) -> list[dict]:
        """Return categories with counts."""
        self._ensure_loaded()
        counts: dict[str, int] = {}
        for pb in self._playbooks:
            cat = pb["category"]
            counts[cat] = counts.get(cat, 0) + 1
        return [{"name": k, "count": v} for k, v in sorted(counts.items())]


# Singleton
playbook_index = PlaybookIndex()

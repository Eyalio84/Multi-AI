"""Selective skill injection — classify intent and inject relevant playbook/KG context."""
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# 10 intent categories with keyword patterns
INTENT_PATTERNS = {
    "cost_optimization": {
        "phrases": ["reduce costs", "save money", "api costs", "cheaper", "cost optimization", "budget"],
        "keywords": ["cost", "expensive", "cheap", "budget", "pricing", "billing", "savings"],
        "playbook_keywords": ["cost", "optimization", "pricing", "batch"],
    },
    "coding_help": {
        "phrases": ["write code", "fix bug", "refactor", "implement", "unit test"],
        "keywords": ["code", "function", "class", "bug", "error", "implement", "refactor", "test", "debug", "compile"],
        "playbook_keywords": ["coding", "development", "programming"],
    },
    "knowledge_graph": {
        "phrases": ["knowledge graph", "kg studio", "graph database", "entity extraction"],
        "keywords": ["knowledge", "graph", "kg", "nodes", "edges", "entity", "relationship", "triple"],
        "playbook_keywords": ["knowledge", "graph", "entity", "extraction"],
    },
    "agent_workflow": {
        "phrases": ["build agent", "autonomous workflow", "multi-agent", "orchestrate"],
        "keywords": ["agent", "workflow", "pipeline", "automate", "orchestrate", "autonomous"],
        "playbook_keywords": ["agent", "workflow", "autonomous", "pipeline"],
    },
    "prompt_engineering": {
        "phrases": ["system prompt", "prompt engineering", "few-shot", "chain of thought"],
        "keywords": ["prompt", "instruction", "persona", "template", "few-shot", "chain"],
        "playbook_keywords": ["prompt", "engineering", "instruction"],
    },
    "deployment": {
        "phrases": ["deploy to production", "docker container", "ci/cd", "monitoring"],
        "keywords": ["deploy", "production", "docker", "server", "hosting", "ci", "cd", "monitor"],
        "playbook_keywords": ["deployment", "production", "docker", "monitoring"],
    },
    "embedding_search": {
        "phrases": ["semantic search", "vector search", "embedding model", "similarity search"],
        "keywords": ["embedding", "search", "semantic", "vector", "similarity", "cosine", "retrieval"],
        "playbook_keywords": ["embedding", "search", "semantic", "retrieval"],
    },
    "reasoning": {
        "phrases": ["extended thinking", "chain of thought", "step by step", "analyze this"],
        "keywords": ["think", "reason", "analyze", "evaluate", "compare", "thinking", "logic"],
        "playbook_keywords": ["reasoning", "thinking", "analysis"],
    },
    "security": {
        "phrases": ["security audit", "vulnerability scan", "access control"],
        "keywords": ["security", "vulnerability", "audit", "permission", "auth", "encrypt", "token"],
        "playbook_keywords": ["security", "audit", "permission"],
    },
    "performance": {
        "phrases": ["optimize performance", "reduce latency", "improve speed"],
        "keywords": ["performance", "optimize", "fast", "slow", "latency", "cache", "speed", "throughput"],
        "playbook_keywords": ["performance", "optimization", "cache"],
    },
}

# Mode boosts: certain intents are more relevant in certain modes
MODE_BOOSTS = {
    "coding": {"coding_help": 0.5},
    "chat": {},
    "messaging": {},
}


class SkillInjector:
    """Classify user intent and inject relevant playbook excerpts + KG context."""

    def __init__(self):
        self._injection_counts: dict[str, int] = {}
        self._total_injections = 0

    def classify_intent(self, text: str, mode: str = "chat") -> list[tuple[str, float]]:
        """Weighted keyword matching. Returns top intents above threshold."""
        text_lower = text.lower()
        scores: dict[str, float] = {}

        for intent, patterns in INTENT_PATTERNS.items():
            score = 0.0

            # Phrase matches (exact phrases worth more)
            for phrase in patterns["phrases"]:
                if phrase in text_lower:
                    score += 1.0

            # Keyword matches
            for keyword in patterns["keywords"]:
                if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
                    score += 0.3

            # Mode boost
            mode_boost = MODE_BOOSTS.get(mode, {}).get(intent, 0)
            score += mode_boost

            if score > 0:
                scores[intent] = score

        # Sort by score, return top 3 above threshold
        sorted_intents = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [(intent, score) for intent, score in sorted_intents[:3] if score >= 0.3]

    async def get_relevant_context(
        self,
        user_text: str,
        mode: str = "chat",
        max_tokens: int = 600,
    ) -> str:
        """
        Classify intent and inject relevant playbook excerpts + KG context.
        Returns formatted string for system prompt injection.
        Token budget: ~600 tokens (~2400 chars).
        """
        intents = self.classify_intent(user_text, mode)
        if not intents:
            return ""

        top_intent, top_score = intents[0]
        char_budget = max_tokens * 4
        sections = []

        # 1. Search playbooks
        try:
            from services.playbook_index import playbook_index
            pb_keywords = INTENT_PATTERNS[top_intent]["playbook_keywords"]
            query = " ".join(pb_keywords)
            results = playbook_index.search(query)

            if results:
                top_pb = results[0]
                # Get an excerpt: first 2 sections or first 800 chars
                content = playbook_index.get_playbook(top_pb["filename"])
                if content:
                    excerpt = self._extract_excerpt(content["content"], char_budget // 2)
                    if excerpt:
                        sections.append(f"[From playbook: {top_pb['title']}]\n{excerpt}")
        except Exception as e:
            logger.debug(f"Playbook search failed: {e}")

        # 2. Search KG for relevant tools/patterns (if applicable)
        if top_intent in ("knowledge_graph", "coding_help", "agent_workflow", "embedding_search"):
            try:
                from services.embedding_service import embedding_service
                kg_results = embedding_service.search(
                    "__workspace_memory__", user_text, mode="hybrid", limit=3
                )
                for r in kg_results.get("results", [])[:2]:
                    node = r["node"]
                    sections.append(f"[Memory: {node['type']}] {node['name']}")
            except Exception:
                pass

        if not sections:
            return ""

        # Track injections
        self._injection_counts[top_intent] = self._injection_counts.get(top_intent, 0) + 1
        self._total_injections += 1

        # Assemble within budget
        result = "[Relevant knowledge]\n"
        for section in sections:
            if len(result) + len(section) > char_budget:
                break
            result += section + "\n"

        return result.strip()

    def _extract_excerpt(self, content: str, max_chars: int) -> str:
        """Extract first meaningful section from playbook content."""
        lines = content.split("\n")
        excerpt_lines = []
        in_section = False
        char_count = 0

        for line in lines:
            # Skip title
            if line.startswith("# ") and not in_section:
                in_section = True
                continue

            if in_section:
                if char_count + len(line) > max_chars:
                    break
                excerpt_lines.append(line)
                char_count += len(line) + 1

        return "\n".join(excerpt_lines).strip()

    def get_injection_stats(self) -> dict:
        return {
            "total_injections": self._total_injections,
            "by_category": dict(self._injection_counts),
        }


# Singleton
skill_injector = SkillInjector()

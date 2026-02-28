#!/usr/bin/env python3
"""
Intent Router — Unified Retrieval Layer

Intent classification and query expansion for the retrieval pipeline.
Detects query intent type, expands queries with synonyms, and routes
to appropriate weight profiles.

Adapted from:
  - intent_query.py GOAL_TO_TOOLS (76 entries)
  - hybrid_query.py TARGETED_EXPANSIONS (14 groups)
  - unified_retriever.py detect_intent() regex + keyword detection

Level 3 dependency — imports from stopwords.py, weight_profiles.py.

Created: February 8, 2026
"""

import re
from typing import Dict, List, Set, Optional, Tuple

try:
    from .stopwords import tokenize_and_filter
    from .weight_profiles import QueryIntent, WeightProfile, get_weights
except ImportError:
    from stopwords import tokenize_and_filter
    from weight_profiles import QueryIntent, WeightProfile, get_weights


# ============================================================================
# GOAL_TO_TOOLS Mapping (from intent_query.py lines 32-76)
# ============================================================================

GOAL_TO_TOOLS: Dict[str, List[str]] = {
    # File Operations
    "read": ["Read"], "view": ["Read"], "examine": ["Read"], "check": ["Read"],
    "look": ["Read"], "inspect": ["Read"], "see": ["Read"], "open": ["Read"],
    "write": ["Write"], "create": ["Write"], "make": ["Write"],
    "save": ["Write"], "generate": ["Write"], "output": ["Write"],
    "edit": ["Edit"], "modify": ["Edit"], "fix": ["Edit"], "change": ["Edit"],
    "update": ["Edit"], "patch": ["Edit"], "replace": ["Edit"],
    # Search Operations
    "find": ["Glob", "Grep"], "search": ["Grep", "Glob", "WebSearch"],
    "locate": ["Glob", "Grep"], "discover": ["Glob", "Grep"],
    "match": ["Grep", "Glob"], "pattern": ["Grep", "Glob"],
    # Execution
    "run": ["Bash"], "execute": ["Bash"], "test": ["Bash"],
    "build": ["Bash"], "install": ["Bash"], "compile": ["Bash"],
    "deploy": ["Bash"], "start": ["Bash"], "command": ["Bash"],
    # Web Operations
    "fetch": ["WebFetch"], "download": ["WebFetch"], "get": ["WebFetch"],
    "url": ["WebFetch"], "http": ["WebFetch"], "webpage": ["WebFetch"],
    "google": ["WebSearch"], "lookup": ["WebSearch"],
    # Meta Operations
    "delegate": ["Task"], "agent": ["Task"], "parallel": ["Task"],
    "subagent": ["Task"], "spawn": ["Task"],
    "plan": ["TodoWrite"], "track": ["TodoWrite"], "todo": ["TodoWrite"],
    "organize": ["TodoWrite"], "checklist": ["TodoWrite"],
    "ask": ["AskUserQuestion"], "question": ["AskUserQuestion"],
    "clarify": ["AskUserQuestion"], "confirm": ["AskUserQuestion"],
    # Compound Goals
    "understand": ["Read", "Glob", "Grep"],
    "refactor": ["Grep", "Read", "Edit"],
    "debug": ["Read", "Bash", "Grep"],
    "explore": ["Glob", "Grep", "Read"],
    "implement": ["Read", "Write", "Edit"],
    "migrate": ["Grep", "Read", "Edit", "Bash"],
    "document": ["Read", "Write"],
}


# ============================================================================
# TARGETED_EXPANSIONS (from hybrid_query.py lines 41-65)
# ============================================================================

TARGETED_EXPANSIONS: Dict[str, List[str]] = {
    "read": ["view", "examine", "check", "contents", "file"],
    "edit": ["modify", "change", "update", "fix", "alter"],
    "write": ["create", "new", "generate"],
    "find": ["search", "locate", "discover", "glob", "grep"],
    "run": ["execute", "test", "bash", "shell", "command"],
    "test": ["verify", "validate", "check", "unittest"],
    "cannot": ["blocked", "limitation", "restriction", "unable"],
    "why": ["reason", "cause", "blocker", "diagnose"],
    "fail": ["error", "problem", "issue", "broken"],
    "refactor": ["rename", "restructure", "reorganize"],
    "debug": ["troubleshoot", "investigate", "diagnose"],
    "automate": ["script", "batch", "task"],
    "track": ["progress", "todo", "organize", "list"],
    "clarify": ["ask", "question", "confirm", "verify"],
    # Extended for NLKE
    "optimize": ["reduce", "improve", "cost", "efficient", "performance"],
    "cache": ["caching", "cached", "prompt_caching", "context_cache"],
    "batch": ["bulk", "parallel", "volume", "concurrent"],
    "model": ["haiku", "sonnet", "opus", "gemini", "claude"],
    "agent": ["workflow", "pipeline", "orchestrate", "routing"],
    "knowledge": ["graph", "kg", "nodes", "edges", "relationships"],
}


# ============================================================================
# INTENT_KEYWORDS for Classification
# ============================================================================

INTENT_KEYWORDS: Dict[str, List[str]] = {
    "cost_reduction": ["cost", "cheap", "save", "budget", "price", "reduce", "efficient", "economy"],
    "speed": ["fast", "quick", "performance", "latency", "slow", "speed", "throughput"],
    "scale": ["large", "big", "scale", "volume", "massive", "many", "batch", "bulk"],
    "safety": ["safe", "secure", "protect", "guard", "permission", "sandbox", "restrict"],
    "simplicity": ["simple", "easy", "basic", "straightforward", "beginner", "quick"],
    "quality": ["accurate", "reliable", "robust", "best", "optimal", "quality", "precise"],
    "automation": ["automate", "workflow", "pipeline", "schedule", "trigger", "agent"],
}


# ============================================================================
# Intent Detection Patterns (regex-based)
# ============================================================================

INTENT_PATTERNS: Dict[QueryIntent, List[str]] = {
    QueryIntent.PRECISION: [
        r"^what\s+is\b",
        r"^define\b",
        r"^explain\s+(?:the\s+)?(?:concept|meaning|definition)\b",
        r"\bexactly\b",
        r"\bspecifically\b",
    ],
    QueryIntent.EXPLORATORY: [
        r"^tell\s+me\s+about\b",
        r"^(?:what|how)\s+(?:can|could|might)\b",
        r"\bexplore\b",
        r"\boverview\b",
        r"\bpossibilities\b",
    ],
    QueryIntent.NAVIGATIONAL: [
        r"^find\s+(?:the|a)\b",
        r"^(?:where|which)\s+(?:is|are)\b",
        r"^locate\b",
        r"\bagent\s+(?:for|that)\b",
        r"\btool\s+(?:for|that)\b",
    ],
    QueryIntent.CONCEPTUAL: [
        r"\brelat(?:e|ion|ionship)\b",
        r"\bconnect(?:ion|ed)?\b",
        r"\bcompare\b",
        r"\bdifference\s+between\b",
        r"how\s+does\s+\w+\s+(?:relate|connect|interact)\b",
    ],
    QueryIntent.EXACT: [
        r"^[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*$",  # PascalCase names
        r"^[a-z]+[-_][a-z]+",                          # kebab-case/snake_case
        r"^\w+\.py$",                                   # Filenames
    ],
    QueryIntent.MULTI_ENTITY: [
        r"\band\b.*\band\b",
        r"\bcompare\s+\w+\s+(?:and|vs|versus|with)\b",
        r"\bboth\b",
        r"\bmultiple\b",
    ],
}


# ============================================================================
# Intent Router
# ============================================================================

class IntentRouter:
    """Detects query intent, expands queries, and routes to weight profiles.

    Combines regex pattern matching with keyword analysis for robust
    intent classification across diverse query styles.
    """

    def detect_intent(self, query: str) -> QueryIntent:
        """Classify query intent using regex patterns + keyword analysis.

        From unified_retriever.py detect_intent() (lines 159-182).

        Args:
            query: Raw query text

        Returns:
            Detected QueryIntent enum value
        """
        query_lower = query.lower().strip()

        # Phase 1: Regex pattern matching (strongest signal)
        for intent, patterns in INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower if intent != QueryIntent.EXACT else query):
                    return intent

        # Phase 2: Keyword analysis
        tokens = set(tokenize_and_filter(query))

        # Check for multi-entity indicators
        if len(tokens) > 6 or ("compare" in tokens and "and" in query_lower):
            return QueryIntent.MULTI_ENTITY

        # Check for conceptual queries
        conceptual_words = {"relate", "relationship", "connection", "between", "versus", "difference"}
        if tokens & conceptual_words:
            return QueryIntent.CONCEPTUAL

        # Check for navigational queries
        nav_words = {"find", "locate", "where", "which", "agent", "tool"}
        if tokens & nav_words:
            return QueryIntent.NAVIGATIONAL

        # Check for precision queries
        precision_words = {"what", "define", "exactly", "specifically", "meaning"}
        if tokens & precision_words:
            return QueryIntent.PRECISION

        # Default to general
        return QueryIntent.GENERAL

    def expand_query(self, query: str) -> str:
        """Expand query with synonyms from TARGETED_EXPANSIONS.

        From hybrid_query.py lines 41-65.

        Args:
            query: Original query text

        Returns:
            Expanded query string with additional terms
        """
        query_lower = query.lower()
        expansions = [query]

        for trigger, terms in TARGETED_EXPANSIONS.items():
            if trigger in query_lower:
                expansions.extend(terms)

        return " ".join(expansions)

    def get_tools_for_goal(self, query: str) -> List[str]:
        """Map query keywords to relevant Claude Code tools.

        From intent_query.py GOAL_TO_TOOLS (lines 32-76).

        Args:
            query: User query/goal

        Returns:
            List of tool names that could serve the goal
        """
        tokens = tokenize_and_filter(query)
        tools = []
        seen = set()

        for token in tokens:
            for tool in GOAL_TO_TOOLS.get(token, []):
                if tool not in seen:
                    tools.append(tool)
                    seen.add(tool)

        return tools

    def classify_domain(self, query: str) -> List[str]:
        """Classify query into domain categories using INTENT_KEYWORDS.

        Args:
            query: Query text

        Returns:
            List of matching domain labels
        """
        tokens = set(tokenize_and_filter(query))
        domains = []

        for domain, keywords in INTENT_KEYWORDS.items():
            if tokens & set(keywords):
                domains.append(domain)

        return domains if domains else ["general"]

    def route(self, query: str, embedding_quality: Optional[str] = None) -> Tuple[QueryIntent, WeightProfile]:
        """Full routing: detect intent and get appropriate weight profile.

        Args:
            query: Raw query text
            embedding_quality: Optional quality level for weight adjustment

        Returns:
            Tuple of (QueryIntent, WeightProfile)
        """
        intent = self.detect_intent(query)
        weights = get_weights(intent, embedding_quality)
        return intent, weights


# ============================================================================
# Self-test
# ============================================================================

if __name__ == "__main__":
    router = IntentRouter()

    print("intent_router.py — Intent Router self-test")
    print("=" * 60)

    # Test intent detection
    test_cases = [
        ("What is prompt caching?", QueryIntent.PRECISION),
        ("Tell me about batch API capabilities", QueryIntent.EXPLORATORY),
        ("Find the agent for cost optimization", QueryIntent.NAVIGATIONAL),
        ("How does caching relate to batch processing?", QueryIntent.CONCEPTUAL),
        ("cost-advisor", QueryIntent.EXACT),
        ("Compare haiku and sonnet for document processing and code generation", QueryIntent.MULTI_ENTITY),
        ("How do I optimize my API costs?", QueryIntent.GENERAL),
    ]

    print("\nIntent Detection:")
    for query, expected in test_cases:
        actual = router.detect_intent(query)
        status = "PASS" if actual == expected else f"FAIL (got {actual.value})"
        print(f"  [{status}] '{query}' -> {actual.value}")

    # Test query expansion
    print("\nQuery Expansion:")
    expanded = router.expand_query("read file and debug error")
    print(f"  'read file and debug error' -> {len(expanded.split())} terms")
    assert "view" in expanded and "troubleshoot" in expanded

    # Test tool mapping
    print("\nGoal -> Tools:")
    tools = router.get_tools_for_goal("I want to find and fix a bug in the code")
    print(f"  'find and fix a bug' -> {tools}")
    assert "Grep" in tools or "Glob" in tools
    assert "Edit" in tools

    # Test domain classification
    print("\nDomain Classification:")
    domains = router.classify_domain("reduce cost of large batch processing")
    print(f"  'reduce cost of large batch processing' -> {domains}")
    assert "cost_reduction" in domains
    assert "scale" in domains

    # Test full routing
    print("\nFull Routing:")
    for query, _ in test_cases:
        intent, weights = router.route(query, embedding_quality="hash")
        print(f"  '{query[:45]}...' -> {intent.value}: a={weights.alpha:.2f} b={weights.beta:.2f} g={weights.gamma:.2f}")

    print(f"\nGOAL_TO_TOOLS entries: {len(GOAL_TO_TOOLS)}")
    print(f"TARGETED_EXPANSIONS groups: {len(TARGETED_EXPANSIONS)}")
    print(f"INTENT_KEYWORDS domains: {len(INTENT_KEYWORDS)}")
    print("\nintent_router.py OK")

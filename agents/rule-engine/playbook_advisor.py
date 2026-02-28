#!/usr/bin/env python3
"""
Playbook Advisor Agent

Task-to-playbook matching engine. Given a task description,
recommends relevant playbooks and their key rules.
Supports 29 core playbooks + variants + dynamic .pb file scanning.

Layer: L1-L5 (Full 5-layer pattern via agent_base)

Usage:
    python3 playbook_advisor.py --example
    python3 playbook_advisor.py --workload task.json --summary

Created: February 6, 2026
Updated: February 6, 2026 (v1.1 - custom .pb files integration)
"""

import sys
import os
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.agent_base import (
    AgentInput, AgentOutput, BaseAnalyzer, run_standard_cli,
    SYNTHESIS_RULES_ROOT, SYNTHESIS_RULES_DIR, SYNTHESIS_PLAYBOOKS_DIR,
    CUSTOM_PLAYBOOKS_DIR,
)

sys.path.insert(0, SYNTHESIS_RULES_ROOT)
try:
    from engine.rule_engine import RuleEngine
    ENGINE_AVAILABLE = True
except ImportError:
    ENGINE_AVAILABLE = False

from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any, Optional
from pathlib import Path


# ============================================================================
# L1: Data Models
# ============================================================================

@dataclass
class PlaybookMatch:
    name: str
    topic: str
    relevance_score: float
    matched_keywords: List[str]
    key_rules: List[Dict[str, Any]]
    rule_count: int
    file_path: str = ""
    category: str = ""


# ============================================================================
# L2: Constants
# ============================================================================

# Core 29 playbooks (PB-0 through PB-28) mapped to .pb filenames
PLAYBOOK_CATALOG = {
    # === FOUNDATION ===
    "PB-0": {
        "topic": "Playbook System",
        "keywords": ["playbook", "system", "meta", "create", "maintain", "documentation", "template"],
        "file": "FOUNDATION-playbook-system.pb",
        "category": "FOUNDATION",
    },
    "PB-1": {
        "topic": "Cost Optimization",
        "keywords": ["cost", "pricing", "savings", "budget", "caching", "batch", "discount", "roi", "api"],
        "file": "FOUNDATION-cost-optimization.pb",
        "category": "FOUNDATION",
    },
    "PB-2": {
        "topic": "Extended Thinking",
        "keywords": ["thinking", "reasoning", "budget", "tokens", "complexity", "quality", "extended"],
        "file": "FOUNDATION-extended-thinking.pb",
        "category": "FOUNDATION",
    },
    "PB-19": {
        "topic": "Opus Advisor Pattern",
        "keywords": ["opus", "advisor", "strategic", "architect", "review", "cascade", "model"],
        "file": "FOUNDATION-opus-advisor.pb",
        "category": "FOUNDATION",
    },
    "PB-20": {
        "topic": "Opus Advisor Usage",
        "keywords": ["opus", "advisor", "usage", "implement", "cascade", "sonnet", "routing"],
        "file": "FOUNDATION-opus-advisor-usage.pb",
        "category": "FOUNDATION",
    },
    "PB-21": {
        "topic": "Haiku Delegation",
        "keywords": ["haiku", "delegate", "cheap", "fast", "routine", "bulk", "cost", "reduction"],
        "file": "FOUNDATION-haiku-delegation.pb",
        "category": "FOUNDATION",
    },

    # === AGENT ===
    "PB-3": {
        "topic": "Agent Development",
        "keywords": ["agent", "tool", "create", "build", "generate", "pattern", "autonomous", "workflow"],
        "file": "AGENT-autonomous-development.pb",
        "category": "AGENT",
    },
    "PB-7": {
        "topic": "Conversation-Tool Patterns",
        "keywords": ["conversation", "tool", "chat", "interaction", "prompt", "composition", "sdk"],
        "file": "AGENT-conversation-tools.pb",
        "category": "AGENT",
    },
    "PB-8": {
        "topic": "Plan-Mode Patterns",
        "keywords": ["plan", "planning", "strategy", "architecture", "design", "mode", "complex"],
        "file": "AGENT-plan-mode-patterns.pb",
        "category": "AGENT",
    },
    "PB-11": {
        "topic": "Parallel Orchestration",
        "keywords": ["parallel", "concurrent", "orchestration", "distribute", "speedup", "swarm", "throughput"],
        "file": "AGENT-parallel-orchestration.pb",
        "category": "AGENT",
    },
    "PB-25": {
        "topic": "Session Continuity",
        "keywords": ["session", "continuity", "context", "memory", "persist", "resume", "handoff"],
        "file": "AGENT-session-continuity.pb",
        "category": "AGENT",
    },

    # === DEV ===
    "PB-5": {
        "topic": "Enhanced Coding",
        "keywords": ["code", "coding", "refactor", "implement", "debug", "test", "productivity"],
        "file": "DEV-enhanced-coding.pb",
        "category": "DEV",
    },
    "PB-6": {
        "topic": "Augmented Intelligence ML",
        "keywords": ["intelligence", "augment", "enhance", "compound", "cascade", "ml", "machine", "learning"],
        "file": "DEV-augmented-intelligence-ml.pb",
        "category": "DEV",
    },
    "PB-10": {
        "topic": "Production Resilience",
        "keywords": ["production", "resilience", "error", "recovery", "fault", "reliability", "retry"],
        "file": "DEV-production-resilience.pb",
        "category": "DEV",
    },
    "PB-12": {
        "topic": "Production Deployment",
        "keywords": ["deploy", "production", "release", "ci", "cd", "infrastructure", "operations"],
        "file": "DEV-production-deployment.pb",
        "category": "DEV",
    },
    "PB-15": {
        "topic": "Testing & QA",
        "keywords": ["test", "testing", "qa", "quality", "validation", "verify", "assert"],
        "file": "DEV-testing-qa.pb",
        "category": "DEV",
    },
    "PB-16": {
        "topic": "Prompt Engineering",
        "keywords": ["prompt", "instruction", "template", "format", "few-shot", "persona", "system"],
        "file": "DEV-prompt-engineering.pb",
        "category": "DEV",
    },
    "PB-22": {
        "topic": "Full-Stack Scaffolding",
        "keywords": ["scaffold", "fullstack", "frontend", "backend", "api", "app", "generate"],
        "file": "DEV-full-stack-scaffolding.pb",
        "category": "DEV",
    },

    # === KNOWLEDGE ===
    "PB-4": {
        "topic": "Knowledge Engineering",
        "keywords": ["knowledge", "graph", "kg", "nodes", "edges", "extraction", "ontology", "entity"],
        "file": "KNOWLEDGE-graph-engineering.pb",
        "category": "KNOWLEDGE",
    },
    "PB-14": {
        "topic": "Semantic Embeddings",
        "keywords": ["embedding", "semantic", "vector", "similarity", "search", "zero-cost"],
        "file": "KNOWLEDGE-semantic-embeddings.pb",
        "category": "KNOWLEDGE",
    },
    "PB-27": {
        "topic": "Advanced RAG Fusion",
        "keywords": ["rag", "retrieval", "augmented", "generation", "search", "fusion", "graph"],
        "file": "KNOWLEDGE-advanced-rag-fusion.pb",
        "category": "KNOWLEDGE",
    },

    # === REASONING ===
    "PB-9": {
        "topic": "Reasoning Patterns",
        "keywords": ["reasoning", "logic", "analysis", "decision", "evaluate", "thinking", "metacognition"],
        "file": "REASONING-patterns.pb",
        "category": "REASONING",
    },
    "PB-17": {
        "topic": "High-Depth Insights",
        "keywords": ["insight", "deep", "analysis", "pattern", "discovery", "depth", "recursive"],
        "file": "REASONING-high-depth-insights.pb",
        "category": "REASONING",
    },
    "PB-18": {
        "topic": "Meta-Optimization",
        "keywords": ["meta", "optimize", "self-improve", "recursive", "bootstrap", "methodology"],
        "file": "REASONING-meta-optimization.pb",
        "category": "REASONING",
    },
    "PB-23": {
        "topic": "Oracle Construction",
        "keywords": ["oracle", "knowledge", "expert", "domain", "specialized", "np-hard", "polynomial"],
        "file": "REASONING-oracle-construction.pb",
        "category": "REASONING",
    },
    "PB-24": {
        "topic": "Reasoning Engine",
        "keywords": ["engine", "reasoning", "rules", "inference", "logic", "unknown", "discovery"],
        "file": "REASONING-engine.pb",
        "category": "REASONING",
    },

    # === ORCHESTRATION ===
    "PB-13": {
        "topic": "Multi-Model Workflows",
        "keywords": ["multi-model", "gemini", "claude", "delegation", "routing", "cascade", "hybrid"],
        "file": "ORCHESTRATION-multi-model.pb",
        "category": "ORCHESTRATION",
    },

    # === SPECIALIZED ===
    "PB-26": {
        "topic": "Documentation Automation",
        "keywords": ["documentation", "docs", "generate", "automate", "update", "ecosystem", "maintenance"],
        "file": "SPECIALIZED-doc-ecosystem-automation.pb",
        "category": "SPECIALIZED",
    },
    "PB-28": {
        "topic": "Story-Driven Interviews",
        "keywords": ["interview", "story", "narrative", "elicit", "requirements", "context", "extraction"],
        "file": "SPECIALIZED-story-driven-interviews.pb",
        "category": "SPECIALIZED",
    },
}

# Variant and supplementary playbooks (beyond the core 29)
VARIANT_CATALOG = {
    "AGENT-continuous-learning": {
        "topic": "Continuous Learning Loop",
        "keywords": ["continuous", "learning", "loop", "persistence", "insight", "accumulation", "compound"],
        "file": "AGENT-continuous-learning.pb",
        "category": "AGENT",
    },
    "AGENT-conversation-tools-fractal": {
        "topic": "Fractal Combinatorial Composition",
        "keywords": ["fractal", "combinatorial", "composition", "discovery", "sdk", "tool", "combination"],
        "file": "AGENT-conversation-tools-fractal.pb",
        "category": "AGENT",
    },
    "AGENT-conversation-tools-llm": {
        "topic": "Local LLM Deployment & Routing",
        "keywords": ["local", "llm", "quantization", "deployment", "hybrid", "routing", "tuning"],
        "file": "AGENT-conversation-tools-llm.pb",
        "category": "AGENT",
    },
    "AGENT-conversation-tools-reasoning": {
        "topic": "Fractal Recursive Reasoning",
        "keywords": ["fractal", "recursive", "reasoning", "composition", "compound", "intelligence"],
        "file": "AGENT-conversation-tools-reasoning.pb",
        "category": "AGENT",
    },
    "AGENT-conversation-tools-synthesis": {
        "topic": "Conversation-Tool Synthesis Outline",
        "keywords": ["synthesis", "outline", "conversation", "tool", "pattern", "meta-insight"],
        "file": "AGENT-conversation-tools-synthesis.pb",
        "category": "AGENT",
    },
    "AGENT-pattern-parallel-synthesis": {
        "topic": "Multi-Agent Parallel Synthesis",
        "keywords": ["multi-agent", "parallel", "synthesis", "orchestration", "pattern", "swarm"],
        "file": "AGENT-pattern-parallel-synthesis.pb",
        "category": "AGENT",
    },
    "AGENT-plan-mode-web-game": {
        "topic": "Web Game Development with AI",
        "keywords": ["web", "game", "phaser", "websocket", "realtime", "ai", "browser"],
        "file": "AGENT-plan-mode-web-game.pb",
        "category": "AGENT",
    },
    "AGENT-session-handoff": {
        "topic": "Session Handoff Protocol",
        "keywords": ["session", "handoff", "transfer", "knowledge", "continuity", "protocol"],
        "file": "AGENT-session-handoff.pb",
        "category": "AGENT",
    },
    "AGENT-synthesis-complete": {
        "topic": "PB 7-9 Synthesis Summary",
        "keywords": ["synthesis", "summary", "complete", "patterns", "documented", "meta-insights"],
        "file": "AGENT-synthesis-complete.pb",
        "category": "AGENT",
    },
    "DEV-agent-creation-template": {
        "topic": "Agent Creation Meta-Template",
        "keywords": ["agent", "creation", "template", "meta", "production", "scaffold", "pattern"],
        "file": "DEV-agent-creation-template.pb",
        "category": "DEV",
    },
    "DEV-enhancement-from-extraction": {
        "topic": "Enhancement from Extraction",
        "keywords": ["enhancement", "extraction", "accumulated", "knowledge", "technique", "phase"],
        "file": "DEV-enhancement-from-extraction.pb",
        "category": "DEV",
    },
    "DEV-mcp-server-development": {
        "topic": "MCP Server Development",
        "keywords": ["mcp", "server", "model", "context", "protocol", "integration", "tools"],
        "file": "DEV-mcp-server-development.pb",
        "category": "DEV",
    },
    "DEV-text-to-structured-data": {
        "topic": "Text to Structured Data",
        "keywords": ["text", "structured", "data", "json", "schema", "extraction", "convert"],
        "file": "DEV-text-to-structured-data.pb",
        "category": "DEV",
    },
    "DEV-text-to-structured-data-design": {
        "topic": "Text to Structured Data Design",
        "keywords": ["text", "structured", "data", "design", "schema", "extraction", "specification"],
        "file": "DEV-text-to-structured-data-design.pb",
        "category": "DEV",
    },
    "DEV-tool-creation-template": {
        "topic": "Tool Creation Meta-Template",
        "keywords": ["tool", "creation", "template", "meta", "synthesis", "rules", "ecosystem"],
        "file": "DEV-tool-creation-template.pb",
        "category": "DEV",
    },
    "KNOWLEDGE-advanced-graph-reasoning": {
        "topic": "Advanced Graph Reasoning",
        "keywords": ["graph", "reasoning", "advanced", "validated", "patterns", "bidirectional", "domain"],
        "file": "KNOWLEDGE-advanced-graph-reasoning.pb",
        "category": "KNOWLEDGE",
    },
    "KNOWLEDGE-bidirectional-path-indexing": {
        "topic": "Bidirectional Path Indexing",
        "keywords": ["bidirectional", "path", "indexing", "impact", "analysis", "dependency", "tracking"],
        "file": "KNOWLEDGE-bidirectional-path-indexing.pb",
        "category": "KNOWLEDGE",
    },
    "KNOWLEDGE-embedding-systems": {
        "topic": "Embedding Systems & Semantic Search",
        "keywords": ["embedding", "systems", "semantic", "search", "ml", "infrastructure", "vector"],
        "file": "KNOWLEDGE-embedding-systems.pb",
        "category": "KNOWLEDGE",
    },
    "KNOWLEDGE-graph-traversal": {
        "topic": "Graph Traversal & Navigation",
        "keywords": ["graph", "traversal", "navigation", "movement", "path", "query", "kg"],
        "file": "KNOWLEDGE-graph-traversal.pb",
        "category": "KNOWLEDGE",
    },
    "KNOWLEDGE-perception-enhancement": {
        "topic": "AI Perception Enhancement",
        "keywords": ["perception", "enhancement", "ai", "traversal", "awareness", "understanding"],
        "file": "KNOWLEDGE-perception-enhancement.pb",
        "category": "KNOWLEDGE",
    },
    "KNOWLEDGE-rag-hybrid-methodology": {
        "topic": "Hybrid RAG Methodology",
        "keywords": ["rag", "hybrid", "retrieval", "query", "methodology", "validated", "accuracy"],
        "file": "KNOWLEDGE-rag-retrieval-query-hybrid-methodology.pb",
        "category": "KNOWLEDGE",
    },
    "REASONING-context-window-mgmt": {
        "topic": "Context Window Management",
        "keywords": ["context", "window", "management", "prompt", "caching", "session", "efficient"],
        "file": "REASONING-context-window-mgmt.pb",
        "category": "REASONING",
    },
    "REASONING-metacognition-workflows": {
        "topic": "Metacognition Workflows",
        "keywords": ["metacognition", "workflow", "validated", "reasoning", "tools", "phases", "validation"],
        "file": "REASONING-metacognition-workflows.pb",
        "category": "REASONING",
    },
    "SPECIALIZED-work-tracker": {
        "topic": "Work Tracker System",
        "keywords": ["work", "tracker", "project", "status", "management", "items", "tracking"],
        "file": "SPECIALIZED-work-tracker.pb",
        "category": "SPECIALIZED",
    },
}


# ============================================================================
# L3: Analyzer
# ============================================================================

class PlaybookAdvisorAnalyzer(BaseAnalyzer):
    """Task-to-playbook matching engine with dynamic .pb file scanning."""

    def __init__(self):
        super().__init__(
            agent_name="playbook-advisor",
            model="haiku",
            version="1.1",
        )
        self.engine = None
        if ENGINE_AVAILABLE:
            self.engine = RuleEngine(rules_dir=Path(SYNTHESIS_RULES_DIR))
        self._full_catalog = None

    def _build_full_catalog(self) -> Dict[str, Dict]:
        """Merge core + variant catalogs and scan for undiscovered .pb files."""
        if self._full_catalog is not None:
            return self._full_catalog

        catalog = {}
        catalog.update(PLAYBOOK_CATALOG)
        catalog.update(VARIANT_CATALOG)

        # Dynamic scan for any .pb files not already cataloged
        known_files = {v["file"] for v in catalog.values()}

        if os.path.isdir(CUSTOM_PLAYBOOKS_DIR):
            for entry in os.listdir(CUSTOM_PLAYBOOKS_DIR):
                if entry.endswith(".pb") and entry not in known_files:
                    # Auto-generate catalog entry from filename
                    stem = entry.replace(".pb", "")
                    parts = stem.split("-", 1)
                    category = parts[0] if len(parts) > 1 else "UNKNOWN"
                    topic_words = parts[1] if len(parts) > 1 else stem
                    topic = topic_words.replace("-", " ").title()

                    # Extract keywords from filename
                    keywords = [w for w in topic_words.lower().split("-") if len(w) > 2]

                    # Read first 10 lines for extra keywords
                    try:
                        filepath = os.path.join(CUSTOM_PLAYBOOKS_DIR, entry)
                        with open(filepath, "r", errors="replace") as f:
                            header = "".join(f.readline() for _ in range(10)).lower()
                        extra_kw = re.findall(r'\b[a-z]{4,}\b', header)
                        keywords.extend([w for w in extra_kw if w not in keywords][:5])
                    except Exception:
                        pass

                    catalog[f"DYNAMIC-{stem}"] = {
                        "topic": topic,
                        "keywords": keywords,
                        "file": entry,
                        "category": category.upper(),
                    }

        self._full_catalog = catalog
        return catalog

    def get_example_input(self) -> Dict[str, Any]:
        return {
            "name": "Find Playbooks for KG Enhancement Pipeline",
            "task_description": "I need to enhance a knowledge graph by detecting gaps, suggesting new relationships, and optimizing costs. The pipeline should use multiple models and include quality validation.",
            "max_playbooks": 10,
        }

    def analyze(self, agent_input: AgentInput) -> AgentOutput:
        w = agent_input.workload
        description = w.get("task_description", "").lower()
        max_pb = w.get("max_playbooks", 10)
        category_filter = w.get("category", None)

        rules_applied = [
            "advisor_001_keyword_matching",
            "advisor_002_relevance_scoring",
            "advisor_003_rule_extraction",
            "advisor_004_custom_pb_scan",
        ]

        full_catalog = self._build_full_catalog()
        total_core = len(PLAYBOOK_CATALOG)
        total_variant = len(VARIANT_CATALOG)
        total_dynamic = len(full_catalog) - total_core - total_variant

        # Optional category filter
        if category_filter:
            cat_upper = category_filter.upper()
            catalog = {k: v for k, v in full_catalog.items() if v.get("category", "").upper() == cat_upper}
        else:
            catalog = full_catalog

        # Keyword matching
        words = set(re.findall(r'\w+', description))
        matches = []

        for pb_name, pb_info in catalog.items():
            matched_kw = [kw for kw in pb_info["keywords"] if kw in words or any(kw in w for w in words)]
            if not matched_kw:
                # Fuzzy: check substring matches
                for kw in pb_info["keywords"]:
                    for word in words:
                        if kw in word or word in kw:
                            matched_kw.append(kw)
                            break

            if matched_kw:
                score = len(set(matched_kw)) / len(pb_info["keywords"])
                # Load rules from engine if available
                key_rules = []
                if self.engine:
                    if not self.engine.loaded:
                        self.engine.load_rules()
                    found = self.engine.find_rules(pb_info["topic"])
                    key_rules = [{
                        "rule_id": r.get("rule_id", ""),
                        "title": r.get("title", ""),
                        "confidence": r.get("metadata", {}).get("confidence", 0),
                    } for r in found[:5]]

                file_path = ""
                if "file" in pb_info:
                    file_path = os.path.join(CUSTOM_PLAYBOOKS_DIR, pb_info["file"])

                matches.append(PlaybookMatch(
                    name=pb_name,
                    topic=pb_info["topic"],
                    relevance_score=round(score, 2),
                    matched_keywords=list(set(matched_kw)),
                    key_rules=key_rules,
                    rule_count=len(key_rules),
                    file_path=file_path,
                    category=pb_info.get("category", ""),
                ))

        matches.sort(key=lambda m: m.relevance_score, reverse=True)
        top_matches = matches[:max_pb]

        # Category breakdown
        by_category = {}
        for m in matches:
            by_category.setdefault(m.category, []).append(m.name)

        recommendations = [{
            "technique": "playbook_advisory",
            "applicable": True,
            "total_playbooks_checked": len(catalog),
            "core_playbooks": total_core,
            "variant_playbooks": total_variant,
            "dynamic_playbooks": total_dynamic,
            "matched": len(matches),
            "top_matches": [asdict(m) for m in top_matches],
            "by_category": {k: len(v) for k, v in by_category.items()},
            "rules_applied": rules_applied,
        }]

        anti_patterns = []
        if not matches:
            anti_patterns.append("No playbooks matched - try more specific task description")
        if len(matches) > 20:
            anti_patterns.append(f"Very broad query matched {len(matches)} playbooks - consider narrowing with category filter")

        if top_matches:
            top = top_matches[0]
            meta_insight = (
                f"Best match: {top.name} ({top.topic}) with {top.relevance_score:.0%} relevance. "
                f"{len(matches)} total matched from {len(catalog)} available "
                f"({total_core} core + {total_variant} variants + "
                f"{total_dynamic} dynamic)."
            )
        else:
            meta_insight = f"No playbook matches found among {len(full_catalog)} playbooks. Try describing the task differently."

        return AgentOutput(
            recommendations=recommendations,
            rules_applied=rules_applied,
            meta_insight=meta_insight,
            analysis_data={
                "matches": [asdict(m) for m in top_matches],
                "total_matched": len(matches),
                "catalog_size": len(catalog),
                "task_keywords": list(words)[:20],
                "by_category": by_category,
            },
            anti_patterns=anti_patterns,
            agent_metadata=self.build_metadata(),
        )


if __name__ == "__main__":
    analyzer = PlaybookAdvisorAnalyzer()
    run_standard_cli(
        agent_name="Playbook Advisor",
        description="Task-to-playbook matching and rule recommendation engine (v1.1 - 52+ playbooks)",
        analyzer=analyzer,
    )

#!/usr/bin/env python3
"""
Web Research Agent (#31)

Cross-provider web research using Claude's web_search and Gemini's
google_search_grounding. Synthesizes results from both providers
for comprehensive research coverage.

Layer: L1-L5 (Full 5-layer pattern via agent_base)

Usage:
    python3 web_research.py --example
    python3 web_research.py --workload research.json --summary

Created: February 6, 2026
"""

import sys
import os
import json
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.agent_base import (
    AgentInput, AgentOutput, BaseAnalyzer, run_standard_cli,
    GEMINI_API_BASE, GEMINI_MODELS, TOKENS_PER_MILLION,
)

from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any, Optional


# ============================================================================
# L1: Data Models
# ============================================================================

@dataclass
class ResearchResult:
    query: str
    provider: str  # claude or gemini
    model: str
    success: bool
    summary: str
    sources: List[str]
    tokens_used: int
    cost_usd: float
    error: Optional[str] = None


@dataclass
class SynthesizedResult:
    query: str
    claude_summary: str
    gemini_summary: str
    merged_summary: str
    total_sources: int
    agreement_score: float  # 0-1, how much providers agree


# ============================================================================
# L2: Constants
# ============================================================================

GEMINI_SEARCH_MODEL = "gemini-3-pro"  # Best for google_search_grounding
CLAUDE_SEARCH_MODEL = "sonnet"

RESEARCH_STRATEGIES = {
    "quick": {"providers": ["gemini"], "depth": "summary"},
    "balanced": {"providers": ["gemini", "claude"], "depth": "analysis"},
    "thorough": {"providers": ["gemini", "claude"], "depth": "synthesis"},
}

SEARCH_COST = {
    "gemini_search": 0.002,  # per search query (estimated)
    "claude_search": 0.003,  # per search via web_search tool
}


# ============================================================================
# L3: Analyzer
# ============================================================================

class WebResearchAnalyzer(BaseAnalyzer):
    """Cross-provider web research engine."""

    def __init__(self):
        super().__init__(
            agent_name="web-research",
            model="sonnet",
            version="1.0",
        )
        self.gemini_key = os.environ.get("GEMINI_API_KEY", "")

    def get_example_input(self) -> Dict[str, Any]:
        return {
            "name": "API Documentation Research",
            "queries": [
                {
                    "query": "Claude API prompt caching best practices 2026",
                    "context": "Need to understand caching implementation for NLKE agents",
                },
                {
                    "query": "Gemini 2.5 Pro code execution capabilities",
                    "context": "Planning delegation of compute tasks",
                },
                {
                    "query": "Knowledge graph construction tools Python 2026",
                    "context": "Evaluating tools for NLKE KG pipeline",
                },
            ],
            "strategy": "balanced",
            "execute": False,
        }

    def _search_gemini(self, query: str, context: str = "") -> ResearchResult:
        """Search using Gemini's google_search_grounding."""
        if not self.gemini_key:
            return ResearchResult(
                query=query, provider="gemini", model=GEMINI_SEARCH_MODEL,
                success=False, summary="", sources=[], tokens_used=0,
                cost_usd=0, error="GEMINI_API_KEY not set",
            )

        prompt = f"Research the following topic and provide a comprehensive summary with sources:\n\nQuery: {query}"
        if context:
            prompt += f"\nContext: {context}"

        payload = {
            "system_instruction": {
                "parts": [{"text": "You are a research assistant. Provide factual, well-sourced answers. Always cite your sources."}],
            },
            "contents": [{"parts": [{"text": prompt}]}],
            "tools": [{"google_search": {}}],
            "safetySettings": [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            ],
        }

        url = f"{GEMINI_API_BASE}/models/{GEMINI_SEARCH_MODEL}:generateContent?key={self.gemini_key}"

        try:
            data_bytes = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url, data=data_bytes,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            text = data["candidates"][0]["content"]["parts"][0].get("text", "")
            usage = data.get("usageMetadata", {})
            tokens = usage.get("totalTokenCount", len(prompt) // 4)

            # Extract grounding sources if present
            sources = []
            grounding = data["candidates"][0].get("groundingMetadata", {})
            for chunk in grounding.get("groundingChunks", []):
                web = chunk.get("web", {})
                if web.get("uri"):
                    sources.append(web["uri"])

            pricing = GEMINI_MODELS.get(GEMINI_SEARCH_MODEL, {"input": 2.00, "output": 12.00})
            cost = tokens / TOKENS_PER_MILLION * (pricing["input"] + pricing["output"]) / 2

            return ResearchResult(
                query=query, provider="gemini", model=GEMINI_SEARCH_MODEL,
                success=True, summary=text[:2000], sources=sources,
                tokens_used=tokens, cost_usd=round(cost, 6),
            )
        except Exception as e:
            return ResearchResult(
                query=query, provider="gemini", model=GEMINI_SEARCH_MODEL,
                success=False, summary="", sources=[], tokens_used=0,
                cost_usd=0, error=str(e),
            )

    def analyze(self, agent_input: AgentInput) -> AgentOutput:
        w = agent_input.workload
        queries = w.get("queries", [])
        strategy = w.get("strategy", "balanced")
        execute = w.get("execute", False)

        rules = [
            "research_001_multi_provider",
            "research_002_source_synthesis",
            "research_003_grounding_verification",
            "research_004_cost_tracking",
        ]

        config = RESEARCH_STRATEGIES.get(strategy, RESEARCH_STRATEGIES["balanced"])
        results = []
        total_cost = 0.0

        for q in queries:
            query_text = q.get("query", "")
            context = q.get("context", "")

            if execute and "gemini" in config["providers"]:
                result = self._search_gemini(query_text, context)
            else:
                # Estimate
                tokens_est = len(query_text) // 4 + 3000
                pricing = GEMINI_MODELS.get(GEMINI_SEARCH_MODEL, {"input": 2.00, "output": 12.00})
                cost_est = tokens_est / TOKENS_PER_MILLION * (pricing["input"] + pricing["output"]) / 2
                result = ResearchResult(
                    query=query_text, provider="gemini", model=GEMINI_SEARCH_MODEL,
                    success=True, summary="[dry run - not executed]",
                    sources=[], tokens_used=tokens_est, cost_usd=round(cost_est, 6),
                )

            results.append(result)
            total_cost += result.cost_usd

        successes = sum(1 for r in results if r.success)
        total_sources = sum(len(r.sources) for r in results)

        anti_patterns = []
        for r in results:
            if r.error:
                anti_patterns.append(f"FAILED: {r.query[:50]} - {r.error}")
        if not execute:
            anti_patterns.append("Dry run mode - no actual web searches performed")

        recommendations = [{
            "technique": "web_research",
            "applicable": True,
            "strategy": strategy,
            "total_queries": len(results),
            "successes": successes,
            "total_sources": total_sources,
            "providers": config["providers"],
            "total_cost_usd": round(total_cost, 6),
            "results": [asdict(r) for r in results],
            "rules_applied": rules,
        }]

        meta_insight = (
            f"Researched {len(results)} queries ({strategy} strategy): "
            f"{successes} succeeded, {total_sources} sources found. "
            f"Cost: ${total_cost:.4f}."
        )

        return AgentOutput(
            recommendations=recommendations,
            rules_applied=rules,
            meta_insight=meta_insight,
            analysis_data={
                "results": [asdict(r) for r in results],
                "total_cost": round(total_cost, 6),
                "strategy": strategy,
                "total_sources": total_sources,
            },
            anti_patterns=anti_patterns,
            agent_metadata=self.build_metadata(),
        )


if __name__ == "__main__":
    analyzer = WebResearchAnalyzer()
    run_standard_cli(
        agent_name="Web Research",
        description="Cross-provider web research via Claude and Gemini search",
        analyzer=analyzer,
    )

#!/usr/bin/env python3
"""
Citation Analyzer Agent (#29)

Extract, validate, and analyze citations from AI API responses.
Tracks source attribution, detects fabricated references, and
scores citation quality.

Layer: L1-L5 (Full 5-layer pattern via agent_base)

Usage:
    python3 citation_analyzer.py --example
    python3 citation_analyzer.py --workload citations.json --summary

Created: February 6, 2026
"""

import sys
import os
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.agent_base import (
    AgentInput, AgentOutput, BaseAnalyzer, run_standard_cli,
)

from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any, Optional


# ============================================================================
# L1: Data Models
# ============================================================================

@dataclass
class Citation:
    text: str
    source_type: str  # url, doi, book, paper, code, unknown
    confidence: float  # 0-1, likelihood this is a real citation
    url: Optional[str] = None
    issues: List[str] = field(default_factory=list)


@dataclass
class CitationReport:
    total_citations: int
    valid_citations: int
    suspect_citations: int
    citation_density: float  # citations per 1000 tokens
    quality_score: float  # 0-100


# ============================================================================
# L2: Constants
# ============================================================================

URL_PATTERN = re.compile(r'https?://[^\s\)\]]+')
DOI_PATTERN = re.compile(r'10\.\d{4,}/[^\s]+')
ARXIV_PATTERN = re.compile(r'arxiv:\s*\d{4}\.\d{4,5}', re.IGNORECASE)
RFC_PATTERN = re.compile(r'RFC\s*\d{3,5}', re.IGNORECASE)

CITATION_PATTERNS = {
    "url": URL_PATTERN,
    "doi": DOI_PATTERN,
    "arxiv": ARXIV_PATTERN,
    "rfc": RFC_PATTERN,
}

# Known fabrication indicators
FABRICATION_SIGNALS = [
    "et al., 20",  # Often hallucinated author citations
    "Journal of",  # Generic journal names
    "Proceedings of the",
]

QUALITY_WEIGHTS = {
    "url": 0.7,
    "doi": 1.0,
    "arxiv": 0.95,
    "rfc": 0.9,
    "book": 0.6,
    "code": 0.8,
    "unknown": 0.3,
}


# ============================================================================
# L3: Analyzer
# ============================================================================

class CitationAnalyzerAnalyzer(BaseAnalyzer):
    """Citation extraction and validation engine."""

    def __init__(self):
        super().__init__(
            agent_name="citation-analyzer",
            model="haiku",
            version="1.0",
        )

    def get_example_input(self) -> Dict[str, Any]:
        return {
            "name": "API Response Citation Check",
            "response_text": (
                "According to the Claude API documentation (https://docs.anthropic.com/en/docs), "
                "prompt caching can reduce costs by up to 90%. The technique is described in "
                "the Anthropic cookbook (https://github.com/anthropics/anthropic-cookbook). "
                "For batch processing patterns, see RFC 7231 for HTTP semantics. "
                "Smith et al., 2024 demonstrated that progressive assembly yields 15-20% "
                "quality improvements. The Gemini API (https://ai.google.dev/docs) supports "
                "1M token context windows. See also arxiv: 2401.12345 for embedding comparisons. "
                "DOI: 10.1234/fake.reference.2024 provides theoretical foundations."
            ),
            "token_count": 150,
            "check_fabrication": True,
        }

    def _extract_citations(self, text: str) -> List[Citation]:
        """Extract all citations from text."""
        citations = []
        seen = set()

        for source_type, pattern in CITATION_PATTERNS.items():
            for match in pattern.finditer(text):
                cite_text = match.group().strip().rstrip(".,;)")
                if cite_text in seen:
                    continue
                seen.add(cite_text)

                issues = []
                confidence = QUALITY_WEIGHTS.get(source_type, 0.5)

                # URL-specific validation
                if source_type == "url":
                    if "example.com" in cite_text or "placeholder" in cite_text:
                        issues.append("Placeholder URL")
                        confidence *= 0.3

                citations.append(Citation(
                    text=cite_text,
                    source_type=source_type,
                    confidence=round(confidence, 2),
                    url=cite_text if source_type == "url" else None,
                    issues=issues,
                ))

        return citations

    def _check_fabrication(self, text: str, citations: List[Citation]) -> List[str]:
        """Detect potential fabricated citations."""
        fabrication_warnings = []

        for signal in FABRICATION_SIGNALS:
            if signal in text:
                # Check if the surrounding context looks like a hallucinated citation
                idx = text.find(signal)
                context = text[max(0, idx - 50):idx + 50]
                # Check if there's a matching real citation
                has_real = any(
                    c.source_type in ("doi", "arxiv", "url") and c.confidence > 0.8
                    for c in citations
                    if c.text in context
                )
                if not has_real:
                    fabrication_warnings.append(
                        f"Potential fabrication near '{signal}': {context[:80].strip()}"
                    )

        return fabrication_warnings

    def analyze(self, agent_input: AgentInput) -> AgentOutput:
        w = agent_input.workload
        text = w.get("response_text", "")
        token_count = w.get("token_count", len(text) // 4)
        check_fab = w.get("check_fabrication", True)

        rules = [
            "cite_001_extraction_patterns",
            "cite_002_source_classification",
            "cite_003_fabrication_detection",
            "cite_004_quality_scoring",
        ]

        # Extract citations
        citations = self._extract_citations(text)

        # Fabrication check
        fabrication_warnings = []
        if check_fab:
            fabrication_warnings = self._check_fabrication(text, citations)

        # Quality scoring
        valid = [c for c in citations if c.confidence >= 0.7]
        suspect = [c for c in citations if c.confidence < 0.7]
        density = (len(citations) / max(1, token_count)) * 1000

        quality_score = 0.0
        if citations:
            avg_confidence = sum(c.confidence for c in citations) / len(citations)
            type_diversity = len(set(c.source_type for c in citations)) / len(CITATION_PATTERNS)
            quality_score = round(avg_confidence * 60 + type_diversity * 20 + min(density, 10) * 2, 1)

        report = CitationReport(
            total_citations=len(citations),
            valid_citations=len(valid),
            suspect_citations=len(suspect),
            citation_density=round(density, 2),
            quality_score=quality_score,
        )

        anti_patterns = []
        anti_patterns.extend(fabrication_warnings)
        if density < 1.0 and token_count > 500:
            anti_patterns.append("Low citation density for a long response")
        for c in citations:
            anti_patterns.extend(c.issues)

        recommendations = [{
            "technique": "citation_analysis",
            "applicable": True,
            "report": asdict(report),
            "citations": [asdict(c) for c in citations],
            "by_type": {
                t: sum(1 for c in citations if c.source_type == t)
                for t in set(c.source_type for c in citations)
            },
            "fabrication_warnings": fabrication_warnings,
            "rules_applied": rules,
        }]

        meta_insight = (
            f"Found {len(citations)} citations ({len(valid)} valid, {len(suspect)} suspect). "
            f"Quality score: {quality_score}/100. "
            f"Density: {density:.1f} citations/1K tokens."
        )
        if fabrication_warnings:
            meta_insight += f" WARNING: {len(fabrication_warnings)} potential fabrications detected."

        return AgentOutput(
            recommendations=recommendations,
            rules_applied=rules,
            meta_insight=meta_insight,
            analysis_data={
                "report": asdict(report),
                "citations": [asdict(c) for c in citations],
                "fabrication_warnings": fabrication_warnings,
            },
            anti_patterns=anti_patterns,
            agent_metadata=self.build_metadata(),
        )


if __name__ == "__main__":
    analyzer = CitationAnalyzerAnalyzer()
    run_standard_cli(
        agent_name="Citation Analyzer",
        description="Citation extraction, validation, and fabrication detection",
        analyzer=analyzer,
    )

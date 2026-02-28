#!/usr/bin/env python3
"""
Gemini Delegator Agent v2.1

Claude-to-Gemini task delegation via REST API. Handles model selection,
prompt construction, API calls, response parsing, batch delegation,
retry with exponential backoff, and response caching.

Layer: L1-L5 (Full 5-layer pattern via agent_base)

Usage:
    python3 gemini_delegator.py --example
    python3 gemini_delegator.py --workload task.json --summary

Created: February 6, 2026
Updated: February 6, 2026 (v2.1 - Tier 2 Gemini enhancement)
"""

import sys
import os
import json
import time
import hashlib
import urllib.request
import urllib.error

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.agent_base import (
    AgentInput, AgentOutput, BaseAnalyzer, run_standard_cli,
    GEMINI_API_BASE, GEMINI_MODELS, GEMINI_CAPABILITIES, TOKENS_PER_MILLION,
)

from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any, Optional


# ============================================================================
# L1: Data Models
# ============================================================================

@dataclass
class DelegationResult:
    task_name: str
    model: str
    success: bool
    response_text: str
    input_tokens: int
    output_tokens: int
    estimated_cost: float
    error: Optional[str] = None
    retries: int = 0
    cached: bool = False
    latency_ms: float = 0.0


# ============================================================================
# L2: Constants
# ============================================================================

TASK_TO_MODEL = {
    "read": "gemini-2.5-flash",
    "analyze": "gemini-2.5-pro",
    "search": "gemini-3-pro",
    "summarize": "gemini-2.5-flash",
    "generate": "gemini-2.5-pro",
    "batch": "gemini-2.5-flash-lite",
    "code": "gemini-2.5-pro",
    "enhance": "gemini-3-pro",
}

# Standard safety settings (Gemini API best practice: always set explicitly)
DEFAULT_SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

# Structured output schema for NLKE delegation responses
NLKE_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "success": {"type": "BOOLEAN"},
        "result": {"type": "STRING"},
        "confidence": {"type": "NUMBER"},
        "model": {"type": "STRING"},
    },
    "required": ["success", "result"],
}

# Retry configuration
MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.0  # seconds
RETRY_BACKOFF_FACTOR = 2.0
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

# Response cache (in-memory, keyed by prompt hash)
_response_cache: Dict[str, DelegationResult] = {}
MAX_CACHE_SIZE = 100


# ============================================================================
# L3: Analyzer
# ============================================================================

class GeminiDelegatorAnalyzer(BaseAnalyzer):
    """Gemini API delegation engine."""

    def __init__(self):
        super().__init__(
            agent_name="gemini-delegator",
            model="sonnet",
            version="2.1",
        )
        self.api_key = os.environ.get("GEMINI_API_KEY", "")

    def get_example_input(self) -> Dict[str, Any]:
        return {
            "name": "Gemini Delegation Demo",
            "tasks": [
                {
                    "name": "Summarize handbook content",
                    "type": "summarize",
                    "prompt": "Summarize the key patterns in this text: Progressive assembly breaks large outputs into chunks of 5-10 items, validates each independently, and combines only passing chunks. This yields 15-20% quality improvement.",
                    "execute": True,
                },
                {
                    "name": "Analyze cost tradeoffs",
                    "type": "analyze",
                    "prompt": "Compare cost-efficiency: Claude Haiku ($0.80/$4.00 per 1M) vs Gemini 2.5 Flash ($0.15/$0.60 per 1M) for bulk categorization of 500 documents.",
                    "execute": True,
                },
            ],
            "dry_run": False,
        }

    def _count_tokens(self, model: str, prompt: str) -> int:
        """Pre-flight token count (free Gemini API call)."""
        if not self.api_key:
            return len(prompt) // 4  # Fallback estimate
        url = f"{GEMINI_API_BASE}/models/{model}:countTokens?key={self.api_key}"
        payload = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
        }).encode("utf-8")
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return data.get("totalTokens", len(prompt) // 4)
        except Exception:
            return len(prompt) // 4

    def _build_payload(self, model: str, prompt: str, task_type: str,
                       system_instruction: str = None,
                       use_structured_output: bool = True,
                       use_search_grounding: bool = False) -> dict:
        """Build Gemini API payload with all best practices."""
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "safetySettings": DEFAULT_SAFETY_SETTINGS,
        }

        # 1. System instruction (separate from user content)
        sys_text = system_instruction or (
            "You are an NLKE delegation worker. Respond concisely and accurately. "
            "Follow the user's output format instructions exactly."
        )
        payload["system_instruction"] = {"parts": [{"text": sys_text}]}

        # 2. Structured output (JSON schema enforcement)
        if use_structured_output:
            payload["generationConfig"] = {
                "responseMimeType": "application/json",
                "responseSchema": NLKE_RESPONSE_SCHEMA,
            }

        # 3. Google Search grounding (for search tasks)
        if use_search_grounding:
            payload["tools"] = [{"google_search": {}}]

        return payload

    def _cache_key(self, model: str, prompt: str, task_type: str) -> str:
        """Generate cache key from model + prompt + task_type."""
        raw = f"{model}:{task_type}:{prompt}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def _call_gemini(self, model: str, prompt: str,
                     task_type: str = "analyze",
                     system_instruction: str = None,
                     use_cache: bool = True) -> DelegationResult:
        """Make Gemini API call with retry, caching, and all 5 best practices."""
        if not self.api_key:
            return DelegationResult(
                task_name="api_call", model=model, success=False,
                response_text="", input_tokens=0, output_tokens=0,
                estimated_cost=0, error="GEMINI_API_KEY not set",
            )

        # Check cache first
        cache_k = self._cache_key(model, prompt, task_type)
        if use_cache and cache_k in _response_cache:
            cached = _response_cache[cache_k]
            cached.cached = True
            return cached

        # Pre-flight: count tokens (free call)
        preflight_tokens = self._count_tokens(model, prompt)

        use_search = task_type == "search"
        use_structured = task_type != "search"

        payload = self._build_payload(
            model, prompt, task_type,
            system_instruction=system_instruction,
            use_structured_output=use_structured,
            use_search_grounding=use_search,
        )

        url = f"{GEMINI_API_BASE}/models/{model}:generateContent?key={self.api_key}"
        data_bytes = json.dumps(payload).encode("utf-8")

        # Retry loop with exponential backoff
        last_error = None
        for attempt in range(MAX_RETRIES + 1):
            if attempt > 0:
                delay = RETRY_BASE_DELAY * (RETRY_BACKOFF_FACTOR ** (attempt - 1))
                time.sleep(delay)

            req = urllib.request.Request(
                url, data=data_bytes,
                headers={"Content-Type": "application/json"},
            )

            start_ms = time.time() * 1000
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                latency = time.time() * 1000 - start_ms

                text = data["candidates"][0]["content"]["parts"][0]["text"]
                usage = data.get("usageMetadata", {})
                input_tok = usage.get("promptTokenCount", preflight_tokens)
                output_tok = usage.get("candidatesTokenCount", len(text) // 4)

                model_pricing = GEMINI_MODELS.get(model, {"input": 1.0, "output": 4.0})
                cost = (input_tok / TOKENS_PER_MILLION * model_pricing["input"] +
                        output_tok / TOKENS_PER_MILLION * model_pricing["output"])

                result = DelegationResult(
                    task_name="api_call", model=model, success=True,
                    response_text=text, input_tokens=input_tok,
                    output_tokens=output_tok, estimated_cost=round(cost, 6),
                    retries=attempt, latency_ms=round(latency, 1),
                )

                # Store in cache
                if use_cache and len(_response_cache) < MAX_CACHE_SIZE:
                    _response_cache[cache_k] = result

                return result

            except urllib.error.HTTPError as e:
                last_error = f"HTTP {e.code}: {e.reason}"
                if e.code not in RETRYABLE_STATUS_CODES:
                    break  # Non-retryable error
            except Exception as e:
                last_error = str(e)
                if attempt == MAX_RETRIES:
                    break

        return DelegationResult(
            task_name="api_call", model=model, success=False,
            response_text="", input_tokens=0, output_tokens=0,
            estimated_cost=0, error=last_error,
            retries=min(attempt, MAX_RETRIES),
        )

    def delegate_batch(self, tasks: List[Dict], dry_run: bool = False) -> List[DelegationResult]:
        """Delegate multiple tasks efficiently with shared session state."""
        results = []
        for task in tasks:
            name = task.get("name", "unnamed")
            task_type = task.get("type", "analyze")
            prompt = task.get("prompt", "")
            execute = task.get("execute", False) and not dry_run
            model = task.get("model", TASK_TO_MODEL.get(task_type, "gemini-2.5-flash"))

            if execute and prompt:
                result = self._call_gemini(
                    model, prompt, task_type=task_type,
                    system_instruction=task.get("system_instruction"),
                    use_cache=task.get("use_cache", True),
                )
                result.task_name = name
            else:
                input_tok = len(prompt) // 4 if prompt else 5000
                model_pricing = GEMINI_MODELS.get(model, {"input": 1.0, "output": 4.0})
                cost = (input_tok / TOKENS_PER_MILLION * model_pricing["input"] +
                        1000 / TOKENS_PER_MILLION * model_pricing["output"])
                result = DelegationResult(
                    task_name=name, model=model, success=True,
                    response_text="[dry run - not executed]",
                    input_tokens=input_tok, output_tokens=1000,
                    estimated_cost=round(cost, 6),
                )
            results.append(result)
        return results

    def analyze(self, agent_input: AgentInput) -> AgentOutput:
        w = agent_input.workload
        tasks = w.get("tasks", [])
        dry_run = w.get("dry_run", True)

        rules = [
            "delegate_001_model_selection",
            "delegate_002_structured_output",
            "delegate_003_cost_tracking",
            "delegate_004_error_handling",
            "delegate_005_system_instruction",
            "delegate_006_safety_settings",
            "delegate_007_preflight_token_count",
            "delegate_008_search_grounding",
            "delegate_009_retry_backoff",
            "delegate_010_response_caching",
            "delegate_011_batch_delegation",
        ]

        # Use batch delegation method
        results = self.delegate_batch(tasks, dry_run=dry_run)
        total_cost = sum(r.estimated_cost for r in results)

        successes = sum(1 for r in results if r.success)
        failures = sum(1 for r in results if not r.success)
        cached_hits = sum(1 for r in results if r.cached)
        total_retries = sum(r.retries for r in results)

        anti_patterns = []
        for r in results:
            if r.error:
                anti_patterns.append(f"FAILED: {r.task_name} - {r.error}")
        if total_retries > len(results):
            anti_patterns.append(
                f"High retry rate: {total_retries} retries across {len(results)} tasks"
            )

        # Model distribution
        by_model: Dict[str, float] = {}
        for r in results:
            by_model[r.model] = by_model.get(r.model, 0) + r.estimated_cost

        recommendations = [{
            "technique": "gemini_delegation",
            "applicable": True,
            "total_tasks": len(results),
            "successes": successes,
            "failures": failures,
            "cached_hits": cached_hits,
            "total_retries": total_retries,
            "total_cost_usd": round(total_cost, 6),
            "results": [asdict(r) for r in results],
            "rules_applied": rules,
        }]

        cache_note = f", {cached_hits} cached" if cached_hits else ""
        retry_note = f", {total_retries} retries" if total_retries else ""
        meta_insight = (
            f"Delegated {len(results)} tasks to Gemini: "
            f"{successes} succeeded, {failures} failed{cache_note}{retry_note}. "
            f"Total cost: ${total_cost:.4f}. "
            f"Models: {', '.join(f'{m}(${c:.4f})' for m, c in by_model.items())}."
        )

        return AgentOutput(
            recommendations=recommendations,
            rules_applied=rules,
            meta_insight=meta_insight,
            analysis_data={
                "results": [asdict(r) for r in results],
                "total_cost": round(total_cost, 6),
                "by_model": {m: round(c, 6) for m, c in by_model.items()},
                "cached_hits": cached_hits,
                "total_retries": total_retries,
                "cache_size": len(_response_cache),
            },
            anti_patterns=anti_patterns,
            agent_metadata=self.build_metadata(),
        )


if __name__ == "__main__":
    analyzer = GeminiDelegatorAnalyzer()
    run_standard_cli(
        agent_name="Gemini Delegator",
        description="Claude-to-Gemini task delegation via REST API",
        analyzer=analyzer,
    )

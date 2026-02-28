#!/usr/bin/env python3
"""
Gemini Compute Agent (#30)

Delegates computational tasks to Gemini's code_execution and
function_calling capabilities. Runs Python code in Gemini's sandbox
(NumPy, Pandas, SciPy available) and parses structured results.

Layer: L1-L5 (Full 5-layer pattern via agent_base)

Usage:
    python3 gemini_compute.py --example
    python3 gemini_compute.py --workload compute_tasks.json --summary

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
class ComputeResult:
    task_name: str
    model: str
    success: bool
    code_executed: str
    output: str
    execution_time_ms: float
    tokens_used: int
    cost_usd: float
    error: Optional[str] = None


# ============================================================================
# L2: Constants
# ============================================================================

COMPUTE_MODEL = "gemini-2.5-pro"  # Best for code execution
COMPUTE_FALLBACK = "gemini-3-pro"

# Available in Gemini sandbox
SANDBOX_LIBRARIES = [
    "numpy", "pandas", "scipy", "matplotlib", "sympy",
    "sklearn", "statistics", "math", "json", "csv",
]

TASK_TEMPLATES = {
    "statistics": "Calculate descriptive statistics (mean, median, std, quartiles) for: {data}",
    "correlation": "Calculate Pearson and Spearman correlation between: {data}",
    "regression": "Fit a linear regression to: {data}. Return coefficients, R², and predictions.",
    "clustering": "Perform k-means clustering (k={k}) on: {data}. Return cluster assignments.",
    "timeseries": "Analyze time series trends for: {data}. Return trend, seasonality, residuals.",
    "custom": "{prompt}",
}


# ============================================================================
# L3: Analyzer
# ============================================================================

class GeminiComputeAnalyzer(BaseAnalyzer):
    """Gemini code execution delegation engine."""

    def __init__(self):
        super().__init__(
            agent_name="gemini-compute",
            model="sonnet",
            version="1.0",
        )
        self.api_key = os.environ.get("GEMINI_API_KEY", "")

    def get_example_input(self) -> Dict[str, Any]:
        return {
            "name": "NLKE Agent Metrics Analysis",
            "tasks": [
                {
                    "name": "Agent cost statistics",
                    "type": "statistics",
                    "data": [0.001, 0.003, 0.01, 0.04, 0.15, 0.005, 0.002, 0.008, 0.05, 0.12],
                    "description": "Cost per execution for 10 agents (USD)",
                },
                {
                    "name": "Correlation: cost vs quality",
                    "type": "correlation",
                    "data": {
                        "cost": [0.001, 0.003, 0.01, 0.04, 0.15],
                        "quality": [60, 72, 85, 92, 98],
                    },
                    "description": "Does spending more improve quality?",
                },
                {
                    "name": "Custom analysis",
                    "type": "custom",
                    "prompt": "Given agent costs [0.001, 0.003, 0.01, 0.04, 0.15] and quality scores [60, 72, 85, 92, 98], find the cost-quality Pareto frontier. Return the optimal cost threshold.",
                },
            ],
            "execute": False,
        }

    def _build_code_execution_payload(self, prompt: str, model: str) -> dict:
        """Build Gemini API payload with code_execution tool."""
        return {
            "system_instruction": {
                "parts": [{"text": (
                    "You are a computation agent. Write and execute Python code to solve the task. "
                    "Use numpy, pandas, scipy as needed. Always print results clearly."
                )}],
            },
            "contents": [{"parts": [{"text": prompt}]}],
            "tools": [{"code_execution": {}}],
            "safetySettings": [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            ],
        }

    def _execute_compute(self, task_name: str, prompt: str) -> ComputeResult:
        """Execute a compute task via Gemini code_execution."""
        model = COMPUTE_MODEL
        if not self.api_key:
            return ComputeResult(
                task_name=task_name, model=model, success=False,
                code_executed="", output="", execution_time_ms=0,
                tokens_used=0, cost_usd=0,
                error="GEMINI_API_KEY not set",
            )

        payload = self._build_code_execution_payload(prompt, model)
        url = f"{GEMINI_API_BASE}/models/{model}:generateContent?key={self.api_key}"

        try:
            data_bytes = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url, data=data_bytes,
                headers={"Content-Type": "application/json"},
            )
            import time
            start = time.time()
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            elapsed = (time.time() - start) * 1000

            # Extract code and output from response
            parts = data["candidates"][0]["content"]["parts"]
            code = ""
            output = ""
            for part in parts:
                if "executableCode" in part:
                    code = part["executableCode"].get("code", "")
                elif "codeExecutionResult" in part:
                    output = part["codeExecutionResult"].get("output", "")
                elif "text" in part:
                    output += part["text"]

            usage = data.get("usageMetadata", {})
            tokens = usage.get("totalTokenCount", len(prompt) // 4)
            pricing = GEMINI_MODELS.get(model, {"input": 1.25, "output": 5.00})
            cost = tokens / TOKENS_PER_MILLION * (pricing["input"] + pricing["output"]) / 2

            return ComputeResult(
                task_name=task_name, model=model, success=True,
                code_executed=code, output=output,
                execution_time_ms=round(elapsed, 1),
                tokens_used=tokens, cost_usd=round(cost, 6),
            )
        except Exception as e:
            return ComputeResult(
                task_name=task_name, model=model, success=False,
                code_executed="", output="",
                execution_time_ms=0, tokens_used=0, cost_usd=0,
                error=str(e),
            )

    def _build_prompt(self, task: Dict) -> str:
        """Build compute prompt from task specification."""
        task_type = task.get("type", "custom")
        template = TASK_TEMPLATES.get(task_type, TASK_TEMPLATES["custom"])

        data = task.get("data", "")
        prompt = task.get("prompt", "")
        k = task.get("k", 3)

        return template.format(data=json.dumps(data), prompt=prompt, k=k)

    def analyze(self, agent_input: AgentInput) -> AgentOutput:
        w = agent_input.workload
        tasks = w.get("tasks", [])
        execute = w.get("execute", False)

        rules = [
            "compute_001_code_execution",
            "compute_002_sandbox_libraries",
            "compute_003_result_parsing",
            "compute_004_cost_tracking",
        ]

        results = []
        total_cost = 0.0

        for task in tasks:
            name = task.get("name", "unnamed")
            prompt = self._build_prompt(task)

            if execute:
                result = self._execute_compute(name, prompt)
            else:
                # Estimate only
                tokens_est = len(prompt) // 4 + 2000  # prompt + code execution overhead
                pricing = GEMINI_MODELS.get(COMPUTE_MODEL, {"input": 1.25, "output": 5.00})
                cost_est = tokens_est / TOKENS_PER_MILLION * (pricing["input"] + pricing["output"]) / 2
                result = ComputeResult(
                    task_name=name, model=COMPUTE_MODEL, success=True,
                    code_executed="[dry run]", output="[not executed]",
                    execution_time_ms=0, tokens_used=tokens_est,
                    cost_usd=round(cost_est, 6),
                )

            results.append(result)
            total_cost += result.cost_usd

        successes = sum(1 for r in results if r.success)
        failures = sum(1 for r in results if not r.success)

        anti_patterns = []
        for r in results:
            if r.error:
                anti_patterns.append(f"FAILED: {r.task_name} - {r.error}")

        recommendations = [{
            "technique": "gemini_compute",
            "applicable": True,
            "total_tasks": len(results),
            "successes": successes,
            "failures": failures,
            "total_cost_usd": round(total_cost, 6),
            "sandbox_libraries": SANDBOX_LIBRARIES,
            "results": [asdict(r) for r in results],
            "rules_applied": rules,
        }]

        meta_insight = (
            f"Computed {len(results)} tasks: {successes} succeeded, {failures} failed. "
            f"Total cost: ${total_cost:.4f}. "
            f"Available libraries: {', '.join(SANDBOX_LIBRARIES[:5])}+."
        )

        return AgentOutput(
            recommendations=recommendations,
            rules_applied=rules,
            meta_insight=meta_insight,
            analysis_data={
                "results": [asdict(r) for r in results],
                "total_cost": round(total_cost, 6),
            },
            anti_patterns=anti_patterns,
            agent_metadata=self.build_metadata(),
        )


if __name__ == "__main__":
    analyzer = GeminiComputeAnalyzer()
    run_standard_cli(
        agent_name="Gemini Compute",
        description="Delegate computational tasks to Gemini code_execution sandbox",
        analyzer=analyzer,
    )

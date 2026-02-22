# Playbook 13: Hybrid Multi-Model Workflows

**Version:** 1.0
**Created:** November 27, 2025
**Category:** Orchestration
**Prerequisites:** PB 1 (Cost), PB 3 (Agents), ORCHESTRATION.md

---

## Executive Summary

This playbook operationalizes multi-model orchestration, providing executable patterns for combining Claude and Gemini in single workflows. It bridges the gap between ORCHESTRATION.md (theory) and production implementations.

**Core Principle:** Different models excel at different tasks. Intelligent routing maximizes quality while minimizing cost.

---

## Table of Contents

1. [Core Orchestration Patterns](#1-core-orchestration-patterns)
2. [Routing Decision Logic](#2-routing-decision-logic)
3. [Cost-Optimized Workflows](#3-cost-optimized-workflows)
4. [Quality-Optimized Workflows](#4-quality-optimized-workflows)
5. [Domain-Specific Recipes](#5-domain-specific-recipes)
6. [Implementation Patterns](#6-implementation-patterns)

---

## 1. Core Orchestration Patterns

### 1.1 Sequential Pattern (Model A → Model B)

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│  Input  │ ──▶ │ Model A │ ──▶ │ Model B │ ──▶ Output
└─────────┘     └─────────┘     └─────────┘
                 (Process)       (Refine)
```

**Use When:**
- First pass is cheaper, refinement needs quality
- Large input needs summarization before analysis
- Output of first model becomes context for second

```python
async def sequential_workflow(input_data: str) -> dict:
    """
    Gemini processes large input → Claude refines.

    Cost: $0.95 vs $5.00 all-Claude
    Quality: 95% of all-Claude
    """
    # Step 1: Gemini handles large context
    summary = await gemini.process(
        input_data,
        prompt="Summarize key points, extract entities"
    )

    # Step 2: Claude refines and structures
    refined = await claude.process(
        summary,
        prompt="Structure these findings, identify patterns"
    )

    return {"summary": summary, "analysis": refined}
```

### 1.2 Parallel Pattern (Model A + Model B → Synthesis)

```
              ┌─────────┐
              │ Model A │──┐
┌─────────┐   └─────────┘  │   ┌───────────┐
│  Input  │───              ├──▶│ Synthesis │──▶ Output
└─────────┘   ┌─────────┐  │   └───────────┘
              │ Model B │──┘
              └─────────┘
```

**Use When:**
- Problem benefits from multiple perspectives
- Need cross-validation
- Time allows parallel execution

```python
import asyncio

async def parallel_workflow(problem: str) -> dict:
    """
    Get independent perspectives, synthesize best aspects.

    Quality: Higher than either model alone
    Cost: 2x single model
    """
    # Launch both in parallel
    claude_task = asyncio.create_task(
        claude.analyze(problem, prompt="Analyze from first principles")
    )
    gemini_task = asyncio.create_task(
        gemini.analyze(problem, prompt="Analyze with broad context")
    )

    claude_analysis, gemini_analysis = await asyncio.gather(
        claude_task, gemini_task
    )

    # Synthesize (use better reasoner)
    synthesis = await claude.process(
        f"""Two perspectives on the same problem:

PERSPECTIVE A (Claude):
{claude_analysis}

PERSPECTIVE B (Gemini):
{gemini_analysis}

Synthesize the best aspects of both. Note where they agree
and where they differ. Produce a unified analysis."""
    )

    return {
        "claude": claude_analysis,
        "gemini": gemini_analysis,
        "synthesis": synthesis
    }
```

### 1.3 Cascade Pattern (Fallback Chain)

```
┌─────────┐    success    ┌────────┐
│ Model A │──────────────▶│ Output │
└────┬────┘               └────────┘
     │ failure
     ▼
┌─────────┐    success    ┌────────┐
│ Model B │──────────────▶│ Output │
└────┬────┘               └────────┘
     │ failure
     ▼
┌─────────┐    success    ┌────────┐
│ Model C │──────────────▶│ Output │
└─────────┘               └────────┘
```

**Use When:**
- Need graceful degradation
- Primary model may hit quota
- Cost vs quality trade-off acceptable

```python
class CascadeOrchestrator:
    """
    Try primary model first, fall back on failure or quota.
    """

    def __init__(self):
        self.chain = [
            ("Claude Opus 4.5", claude_opus, 1.0),
            ("Gemini 3 Pro", gemini_pro, 0.9),
            ("Gemini Flash", gemini_flash, 0.75),
        ]

    async def execute(self, task: str) -> dict:
        for name, model, quality in self.chain:
            try:
                result = await model.process(task)
                return {
                    "result": result,
                    "provider": name,
                    "quality_score": quality,
                    "degraded": name != self.chain[0][0]
                }
            except (RateLimitError, QuotaExceededError) as e:
                continue
            except Exception as e:
                # Non-recoverable error
                raise

        raise AllModelsFailedError("All models in cascade failed")
```

### 1.4 Voting Pattern (Consensus for Critical Decisions)

```
              ┌─────────┐
              │ Model A │──▶ Vote A
┌─────────┐   └─────────┘            ┌────────────┐
│  Input  │───┌─────────┐      ───▶  │  Consensus │──▶ Final
└─────────┘   │ Model B │──▶ Vote B  └────────────┘
              └─────────┘
              ┌─────────┐
              │ Model C │──▶ Vote C
              └─────────┘
```

**Use When:**
- Decision is high-stakes
- Need high confidence
- Cost is secondary to correctness

```python
async def voting_workflow(question: str, options: list) -> dict:
    """
    Multiple models vote, resolve disagreements.
    """
    prompt = f"""Question: {question}
Options: {', '.join(options)}

Choose ONE option and explain briefly why."""

    # Get votes from 3 models
    votes = await asyncio.gather(
        claude_opus.process(prompt),
        gemini_pro.process(prompt),
        claude_sonnet.process(prompt)  # Cheaper third voter
    )

    # Extract choices
    choices = [extract_choice(v, options) for v in votes]

    if len(set(choices)) == 1:
        # Unanimous
        return {
            "decision": choices[0],
            "confidence": "unanimous",
            "votes": votes
        }
    else:
        # Disagreement - use strongest model to resolve
        resolution_prompt = f"""Question: {question}
Options: {', '.join(options)}

Three AI models gave different answers:
- Claude Opus: {choices[0]}
- Gemini Pro: {choices[1]}
- Claude Sonnet: {choices[2]}

Analyze the disagreement and provide the correct answer with reasoning."""

        resolution = await claude_opus.process(resolution_prompt)

        return {
            "decision": extract_choice(resolution, options),
            "confidence": "resolved_disagreement",
            "votes": votes,
            "resolution": resolution
        }
```

---

## 2. Routing Decision Logic

### 2.1 Capability-Based Router

```python
class CapabilityRouter:
    """
    Route based on task requirements and model capabilities.
    """

    CAPABILITIES = {
        "claude_opus": {
            "reasoning": 1.0,
            "coding": 0.95,
            "context_window": 200_000,
            "cost_per_1k": 15.0
        },
        "claude_sonnet": {
            "reasoning": 0.85,
            "coding": 0.9,
            "context_window": 200_000,
            "cost_per_1k": 3.0
        },
        "gemini_pro": {
            "reasoning": 0.85,
            "coding": 0.85,
            "context_window": 1_000_000,
            "cost_per_1k": 1.25
        },
        "gemini_flash": {
            "reasoning": 0.7,
            "coding": 0.75,
            "context_window": 1_000_000,
            "cost_per_1k": 0.075
        }
    }

    def route(self, task: dict) -> str:
        """
        Route task to optimal model.

        Args:
            task: {
                "type": "reasoning" | "coding" | "analysis",
                "context_size": int,
                "priority": "quality" | "cost" | "balanced"
            }
        """
        context_size = task.get("context_size", 0)
        task_type = task.get("type", "reasoning")
        priority = task.get("priority", "balanced")

        # Filter by context window
        candidates = {
            k: v for k, v in self.CAPABILITIES.items()
            if v["context_window"] >= context_size
        }

        if not candidates:
            raise NoSuitableModelError(f"No model supports {context_size} tokens")

        # Score candidates
        scored = []
        for name, caps in candidates.items():
            quality = caps.get(task_type, caps["reasoning"])
            cost = caps["cost_per_1k"]

            if priority == "quality":
                score = quality
            elif priority == "cost":
                score = 1 / cost  # Higher is better
            else:  # balanced
                score = quality / (cost ** 0.5)  # Quality-weighted cost efficiency

            scored.append((name, score))

        # Return best
        return max(scored, key=lambda x: x[1])[0]
```

### 2.2 Context Size Router

```python
def route_by_context(context_tokens: int, quality_required: float = 0.8) -> str:
    """
    Route based on context size.

    Size thresholds:
    - < 100K: Claude preferred (better quality)
    - 100K-200K: Either works, route by cost
    - 200K-1M: Gemini only
    """
    if context_tokens > 200_000:
        return "gemini"  # Only option

    if context_tokens > 100_000:
        if quality_required > 0.9:
            return "claude"  # Still fits, quality matters
        return "gemini"  # Cheaper for large context

    return "claude"  # Default to higher quality
```

### 2.3 Cost-Aware Router

```python
class CostAwareRouter:
    """
    Route to minimize cost while maintaining quality threshold.
    """

    def __init__(self, budget_per_day: float = 100.0):
        self.budget = budget_per_day
        self.spent_today = 0.0
        self.last_reset = datetime.now().date()

    def route(self, task: dict, min_quality: float = 0.7) -> str:
        """Route considering budget constraints."""
        # Reset daily budget
        if datetime.now().date() > self.last_reset:
            self.spent_today = 0.0
            self.last_reset = datetime.now().date()

        estimated_cost = self._estimate_cost(task)
        remaining_budget = self.budget - self.spent_today

        # If budget is tight, force cheaper option
        if remaining_budget < estimated_cost["claude_opus"] * 2:
            if min_quality <= 0.75:
                return "gemini_flash"
            return "gemini_pro"

        # Otherwise, route by quality
        if task.get("priority") == "quality":
            return "claude_opus"

        # Default: balanced
        return "claude_sonnet" if task.get("type") == "coding" else "gemini_pro"

    def _estimate_cost(self, task: dict) -> dict:
        tokens = task.get("context_size", 0) + task.get("expected_output", 1000)
        return {
            "claude_opus": tokens * 15 / 1_000_000,
            "claude_sonnet": tokens * 3 / 1_000_000,
            "gemini_pro": tokens * 1.25 / 1_000_000,
            "gemini_flash": tokens * 0.075 / 1_000_000
        }
```

---

## 3. Cost-Optimized Workflows

### 3.1 Gemini First-Pass → Claude Refinement

```python
async def cost_optimized_analysis(documents: list[str]) -> dict:
    """
    Process large document set cost-efficiently.

    Pattern:
    1. Gemini Flash: Initial pass ($0.50 for 100 docs)
    2. Claude Sonnet: Synthesize to findings ($0.30)
    3. Gemini Pro: Validate findings ($0.15)

    Total: $0.95 vs $5.00 all-Claude
    """
    # Step 1: Batch analysis with Gemini Flash
    analyses = await asyncio.gather(*[
        gemini_flash.process(doc, prompt="Extract key points, entities, themes")
        for doc in documents
    ])

    # Step 2: Claude synthesizes
    combined = "\n---\n".join(analyses)
    synthesis = await claude_sonnet.process(
        combined,
        prompt="""Synthesize these analyses into:
1. Top 10 key findings
2. Common themes
3. Notable patterns
4. Potential issues"""
    )

    # Step 3: Gemini validates
    validation = await gemini_pro.process(
        f"Original analyses:\n{combined}\n\nSynthesis:\n{synthesis}",
        prompt="Validate synthesis. Flag any missing items or errors."
    )

    return {
        "synthesis": synthesis,
        "validation": validation,
        "document_count": len(documents),
        "estimated_cost": "$0.95"
    }
```

### 3.2 Caching Across Models

```python
class CrossModelCache:
    """
    Cache results across models to avoid redundant computation.
    """

    def __init__(self):
        self.cache = {}

    def _make_key(self, prompt: str, semantic: bool = True) -> str:
        """Create cache key, optionally semantic."""
        if semantic:
            # Normalize for semantic similarity
            return hashlib.md5(prompt.lower().strip().encode()).hexdigest()
        return hashlib.md5(prompt.encode()).hexdigest()

    async def get_or_compute(
        self,
        prompt: str,
        model_func,
        model_name: str,
        ttl_seconds: int = 3600
    ) -> dict:
        """Get cached result or compute."""
        key = self._make_key(prompt)

        if key in self.cache:
            entry = self.cache[key]
            if datetime.now() - entry["time"] < timedelta(seconds=ttl_seconds):
                return {
                    "result": entry["result"],
                    "cached": True,
                    "original_model": entry["model"]
                }

        # Compute
        result = await model_func(prompt)
        self.cache[key] = {
            "result": result,
            "model": model_name,
            "time": datetime.now()
        }

        return {"result": result, "cached": False, "model": model_name}
```

---

## 4. Quality-Optimized Workflows

### 4.1 Claude Primary → Gemini Validation

```python
async def quality_optimized_reasoning(problem: str) -> dict:
    """
    Maximum quality reasoning with validation.
    """
    # Claude for primary reasoning
    primary = await claude_opus.process(
        problem,
        prompt="""Think step by step. Show your reasoning.
Be thorough and consider edge cases.""",
        extended_thinking=True
    )

    # Gemini validates
    validation = await gemini_pro.process(
        f"Problem: {problem}\n\nSolution: {primary}",
        prompt="""Validate this solution:
1. Is the reasoning sound?
2. Are there logical errors?
3. Were edge cases considered?
4. What's missing?"""
    )

    # If validation finds issues, iterate
    if "error" in validation.lower() or "missing" in validation.lower():
        refined = await claude_opus.process(
            f"Original: {primary}\n\nValidation feedback: {validation}",
            prompt="Address the validation feedback and improve your answer."
        )
        return {
            "result": refined,
            "iterations": 2,
            "validation": validation
        }

    return {
        "result": primary,
        "iterations": 1,
        "validation": validation
    }
```

### 4.2 Multi-Perspective Analysis

```python
async def multi_perspective_analysis(topic: str) -> dict:
    """
    Analyze from multiple perspectives using model strengths.
    """
    perspectives = await asyncio.gather(
        claude_opus.process(
            topic,
            prompt="Analyze from a first-principles, logical perspective."
        ),
        gemini_pro.process(
            topic,
            prompt="Analyze with broad context and historical patterns."
        ),
        claude_sonnet.process(
            topic,
            prompt="Play devil's advocate. What could go wrong?"
        )
    )

    synthesis = await claude_opus.process(
        f"""Three perspectives on: {topic}

LOGICAL (Claude Opus):
{perspectives[0]}

CONTEXTUAL (Gemini):
{perspectives[1]}

CRITICAL (Devil's Advocate):
{perspectives[2]}

Synthesize into a comprehensive analysis that incorporates all perspectives."""
    )

    return {
        "perspectives": {
            "logical": perspectives[0],
            "contextual": perspectives[1],
            "critical": perspectives[2]
        },
        "synthesis": synthesis
    }
```

---

## 5. Domain-Specific Recipes

### 5.1 Code Review (Claude writes, Gemini checks)

```python
async def code_review_workflow(code: str, requirements: str) -> dict:
    """
    Multi-model code review.

    Claude: Deep logic analysis (better at code)
    Gemini: Broad pattern detection, security (large context)
    """
    # Claude analyzes logic
    logic_review = await claude_opus.process(
        f"Requirements:\n{requirements}\n\nCode:\n{code}",
        prompt="""Review this code for:
1. Correctness relative to requirements
2. Edge cases and error handling
3. Performance considerations
4. Code quality and maintainability"""
    )

    # Gemini checks patterns and security
    security_review = await gemini_pro.process(
        code,
        prompt="""Security and pattern review:
1. Check for OWASP Top 10 vulnerabilities
2. Identify common anti-patterns
3. Check for potential injection points
4. Review error handling for information leakage"""
    )

    # Synthesize
    synthesis = await claude_sonnet.process(
        f"Logic Review:\n{logic_review}\n\nSecurity Review:\n{security_review}",
        prompt="Create unified code review summary with prioritized action items."
    )

    return {
        "logic": logic_review,
        "security": security_review,
        "summary": synthesis
    }
```

### 5.2 Document Analysis (Gemini reads, Claude summarizes)

```python
async def large_document_analysis(document: str) -> dict:
    """
    Analyze large documents (>100K tokens).

    Gemini: Read entire document (1M context)
    Claude: Deep summarization
    """
    token_count = len(document) // 4  # Rough estimate

    if token_count > 200_000:
        # Only Gemini can handle
        extraction = await gemini_pro.process(
            document,
            prompt="""Extract from this large document:
1. Executive summary (500 words)
2. Key findings (numbered list)
3. Critical quotes with page references
4. Data tables and figures summary
5. Recommendations"""
        )

        # Claude refines the extraction
        refined = await claude_opus.process(
            extraction,
            prompt="Refine this extraction into a polished analysis document."
        )

        return {
            "method": "gemini_extract_claude_refine",
            "extraction": extraction,
            "analysis": refined
        }

    else:
        # Claude can handle directly
        return {
            "method": "claude_direct",
            "analysis": await claude_opus.process(document, prompt="Analyze this document comprehensively.")
        }
```

---

## 6. Implementation Patterns

### 6.1 Unified Model Interface

```python
from abc import ABC, abstractmethod

class ModelInterface(ABC):
    """Unified interface for all models."""

    @abstractmethod
    async def process(self, input: str, prompt: str = None, **kwargs) -> str:
        pass

    @abstractmethod
    def estimate_tokens(self, text: str) -> int:
        pass

    @abstractmethod
    def get_capabilities(self) -> dict:
        pass


class ClaudeModel(ModelInterface):
    def __init__(self, model_id: str = "claude-opus-4"):
        self.model_id = model_id
        self.capabilities = {
            "reasoning": 1.0,
            "coding": 0.95,
            "context_window": 200_000
        }

    async def process(self, input: str, prompt: str = None, **kwargs) -> str:
        # Implementation
        pass


class GeminiModel(ModelInterface):
    def __init__(self, model_id: str = "gemini-2.5-pro"):
        self.model_id = model_id
        self.capabilities = {
            "reasoning": 0.85,
            "coding": 0.85,
            "context_window": 1_000_000
        }

    async def process(self, input: str, prompt: str = None, **kwargs) -> str:
        # Implementation
        pass
```

### 6.2 Workflow Definition DSL

```python
from dataclasses import dataclass
from typing import Callable, Optional

@dataclass
class WorkflowStep:
    name: str
    model: str
    prompt: str
    depends_on: Optional[list[str]] = None
    condition: Optional[Callable] = None

class MultiModelWorkflow:
    """Define and execute multi-model workflows."""

    def __init__(self, name: str):
        self.name = name
        self.steps = []
        self.results = {}

    def add_step(self, step: WorkflowStep):
        self.steps.append(step)
        return self

    async def execute(self, input_data: dict) -> dict:
        """Execute workflow with dependency resolution."""
        for step in self._topological_sort():
            # Check condition
            if step.condition and not step.condition(self.results):
                continue

            # Gather dependencies
            context = {
                "input": input_data,
                **{dep: self.results[dep] for dep in (step.depends_on or [])}
            }

            # Execute
            model = self._get_model(step.model)
            prompt = step.prompt.format(**context)

            self.results[step.name] = await model.process(
                context.get("input", ""),
                prompt=prompt
            )

        return self.results

    def _topological_sort(self) -> list[WorkflowStep]:
        # Implement topological sort based on depends_on
        pass

    def _get_model(self, model_name: str) -> ModelInterface:
        # Return appropriate model instance
        pass
```

---

## Related Playbooks

| Playbook | Relationship |
|----------|--------------|
| PB 1: Cost Optimization | Cost-aware routing |
| PB 2: Extended Thinking | Multi-model reasoning |
| PB 3: Agent Development | Multi-model agents |
| ORCHESTRATION.md | Theory reference |

---

## Key Insights

- **Parallel > Sequential** for quality
- **Sequential > Parallel** for cost
- **Cascade** for reliability
- **Voting** for critical decisions

---

**Playbook Version:** 1.0
**Last Updated:** November 27, 2025

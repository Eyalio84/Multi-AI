# Playbook 15: Testing & Quality Assurance for AI Systems

**Version:** 1.0
**Created:** November 27, 2025
**Category:** Quality Assurance
**Prerequisites:** PB 3 (Agents), PB 10 (MCP Servers)

---

## Executive Summary

This playbook provides systematic testing methodologies for AI-powered systems. It addresses the unique challenges of testing non-deterministic outputs, validating LLM behaviors, and ensuring quality across model updates.

**Core Principle:** AI systems require different testing strategies than traditional software. Property-based and semantic testing replace exact-match assertions.

---

## Table of Contents

1. [Testing Challenges in AI Systems](#1-testing-challenges-in-ai-systems)
2. [LLM Output Testing](#2-llm-output-testing)
3. [Agent Workflow Testing](#3-agent-workflow-testing)
4. [Knowledge Graph Testing](#4-knowledge-graph-testing)
5. [MCP Server Testing](#5-mcp-server-testing)
6. [Regression Testing](#6-regression-testing)
7. [Performance Testing](#7-performance-testing)
8. [CI/CD Integration](#8-cicd-integration)

---

## 1. Testing Challenges in AI Systems

### 1.1 Non-Determinism

```python
# Traditional software: deterministic
def add(a, b):
    return a + b  # Always the same for same inputs

assert add(2, 3) == 5  # Always passes

# LLM outputs: non-deterministic
async def summarize(text):
    return await llm.process(text, prompt="Summarize in 50 words")

# This might fail even with correct summaries!
assert summarize(doc) == "The document discusses..."  # DON'T DO THIS
```

### 1.2 The Testing Pyramid for AI

```
                    /\
                   /  \
                  / E2E \
                 /      \
                /--------\
               / Integration\
              /    Tests     \
             /----------------\
            /  Property-Based   \
           /      Semantic       \
          /        Tests          \
         /------------------------\
        /    Unit Tests (Logic)     \
       /                             \
      /-------------------------------\
     /   Schema & Contract Validation   \
    /-------------------------------------\
```

### 1.3 Testing Strategy Matrix

| Component | Test Type | What to Assert |
|-----------|-----------|----------------|
| LLM output | Semantic | Similarity > 0.85, contains key points |
| Agent workflow | Property | Steps executed, state valid |
| KG query | Recall | Expected nodes in top-k |
| MCP server | Contract | Schema valid, response time < SLA |
| Embeddings | Benchmark | Recall@5 >= 0.85 |

---

## 2. LLM Output Testing

### 2.1 Semantic Similarity Assertions

```python
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class SemanticAssertion:
    """Assert semantic equivalence instead of exact match."""

    def __init__(self, embedding_model):
        self.model = embedding_model

    def assert_similar(
        self,
        actual: str,
        expected: str,
        threshold: float = 0.85,
        message: str = None
    ):
        """Assert texts are semantically similar."""
        actual_emb = self.model.encode(actual)
        expected_emb = self.model.encode(expected)

        similarity = cosine_similarity(
            [actual_emb], [expected_emb]
        )[0][0]

        if similarity < threshold:
            raise AssertionError(
                f"Semantic similarity {similarity:.3f} below threshold {threshold}\n"
                f"Expected: {expected[:100]}...\n"
                f"Actual: {actual[:100]}...\n"
                f"{message or ''}"
            )

        return similarity

# Usage
semantic = SemanticAssertion(embedding_model)

def test_summarization():
    result = await llm.summarize(long_document)

    semantic.assert_similar(
        actual=result,
        expected="Key points: cost reduction strategies using caching",
        threshold=0.80
    )
```

### 2.2 Property-Based Testing

```python
from hypothesis import given, strategies as st

class LLMProperties:
    """Test invariant properties of LLM outputs."""

    @given(st.text(min_size=100, max_size=1000))
    def test_summary_shorter_than_input(self, input_text):
        """Summary should always be shorter than input."""
        summary = await llm.summarize(input_text)

        assert len(summary) < len(input_text), \
            f"Summary ({len(summary)}) not shorter than input ({len(input_text)})"

    @given(st.text(min_size=50))
    def test_output_is_valid_text(self, input_text):
        """Output should be valid, printable text."""
        output = await llm.process(input_text)

        assert output.isprintable(), "Output contains non-printable characters"
        assert len(output) > 0, "Output is empty"
        assert not output.startswith("Error"), "Output starts with error"

    @given(st.sampled_from(["positive", "negative", "neutral"]))
    def test_sentiment_classification_valid(self, expected_sentiment):
        """Classification should return valid sentiment."""
        text = generate_text_with_sentiment(expected_sentiment)
        result = await llm.classify_sentiment(text)

        assert result in ["positive", "negative", "neutral"], \
            f"Invalid sentiment: {result}"
```

### 2.3 Schema Validation for Structured Output

```python
from pydantic import BaseModel, ValidationError
from typing import List, Optional

class CodeReviewOutput(BaseModel):
    """Expected schema for code review output."""
    issues: List[dict]
    severity: str
    recommendations: List[str]
    overall_score: float

    class Config:
        extra = "forbid"  # No extra fields allowed


def test_code_review_schema():
    """Test LLM returns valid schema."""
    result = await llm.review_code(
        code="def foo(): pass",
        prompt="Return JSON with: issues, severity, recommendations, overall_score"
    )

    # Parse JSON
    try:
        data = json.loads(result)
    except json.JSONDecodeError as e:
        pytest.fail(f"Invalid JSON: {e}")

    # Validate schema
    try:
        validated = CodeReviewOutput(**data)
    except ValidationError as e:
        pytest.fail(f"Schema validation failed: {e}")

    # Additional assertions
    assert 0 <= validated.overall_score <= 1.0
    assert validated.severity in ["low", "medium", "high", "critical"]
```

### 2.4 Golden Dataset Testing

```python
class GoldenDatasetTest:
    """Test against curated examples with known correct outputs."""

    def __init__(self, golden_path: str):
        with open(golden_path) as f:
            self.golden = json.load(f)

    async def run_tests(self, llm_func, threshold: float = 0.8) -> dict:
        """Run all golden tests."""
        results = {
            "passed": 0,
            "failed": 0,
            "failures": []
        }

        for example in self.golden:
            actual = await llm_func(example["input"])

            # Check semantic similarity
            similarity = compute_similarity(actual, example["expected"])

            if similarity >= threshold:
                results["passed"] += 1
            else:
                results["failed"] += 1
                results["failures"].append({
                    "input": example["input"][:100],
                    "expected": example["expected"][:100],
                    "actual": actual[:100],
                    "similarity": similarity
                })

        return results


# Golden dataset format
GOLDEN_DATASET = [
    {
        "input": "Explain what context caching is in 2 sentences.",
        "expected": "Context caching stores prompt tokens for reuse. It reduces API costs by up to 90%.",
        "tags": ["caching", "cost"]
    },
    {
        "input": "What's the benefit of batch API?",
        "expected": "Batch API provides 50% cost reduction for non-time-critical requests.",
        "tags": ["batch", "cost"]
    }
]
```

---

## 3. Agent Workflow Testing

### 3.1 Mock Infrastructure

```python
class MockLLM:
    """Mock LLM for deterministic testing."""

    def __init__(self, responses: dict = None):
        self.responses = responses or {}
        self.call_log = []

    async def process(self, prompt: str, **kwargs) -> str:
        """Return predefined response or default."""
        self.call_log.append({
            "prompt": prompt,
            "kwargs": kwargs,
            "timestamp": datetime.now()
        })

        # Match response by keyword
        for keyword, response in self.responses.items():
            if keyword.lower() in prompt.lower():
                return response

        return "Mock response: No specific response configured"

    def assert_called_with(self, keyword: str):
        """Assert LLM was called with prompt containing keyword."""
        for call in self.call_log:
            if keyword.lower() in call["prompt"].lower():
                return True
        raise AssertionError(f"No call with keyword '{keyword}'")

    def assert_call_count(self, expected: int):
        """Assert number of LLM calls."""
        actual = len(self.call_log)
        if actual != expected:
            raise AssertionError(f"Expected {expected} calls, got {actual}")


class MockKG:
    """Mock Knowledge Graph for testing."""

    def __init__(self, nodes: list = None, edges: list = None):
        self.nodes = nodes or []
        self.edges = edges or []
        self.query_log = []

    def query(self, query: str, k: int = 5) -> list:
        self.query_log.append(query)
        # Return first k nodes
        return self.nodes[:k]
```

### 3.2 Agent Test Fixtures

```python
import pytest

@pytest.fixture
def mock_llm():
    return MockLLM(responses={
        "analyze": "Analysis complete: Found 3 issues",
        "summarize": "Summary: Key points identified",
        "validate": "Validation passed"
    })

@pytest.fixture
def mock_kg():
    return MockKG(nodes=[
        {"name": "pattern_caching", "type": "pattern"},
        {"name": "use_case_reduce_costs", "type": "use_case"}
    ])

@pytest.fixture
def test_agent(mock_llm, mock_kg):
    """Create agent with mocked dependencies."""
    return AnalysisAgent(llm=mock_llm, kg=mock_kg)


class TestAnalysisAgent:
    async def test_analyze_executes_all_steps(self, test_agent, mock_llm):
        """Test that analysis goes through all expected steps."""
        result = await test_agent.analyze("test input")

        # Verify steps executed
        mock_llm.assert_called_with("analyze")
        assert result["status"] == "complete"

    async def test_handles_empty_input(self, test_agent):
        """Test graceful handling of empty input."""
        result = await test_agent.analyze("")

        assert result["status"] == "error"
        assert "empty" in result["message"].lower()

    async def test_retry_on_failure(self, mock_kg):
        """Test retry logic when LLM fails."""
        failing_llm = MockLLM(responses={})
        failing_llm.process = AsyncMock(side_effect=[
            Exception("Rate limit"),
            "Success after retry"
        ])

        agent = AnalysisAgent(llm=failing_llm, kg=mock_kg)
        result = await agent.analyze("test")

        assert failing_llm.call_count == 2  # Retried once
```

### 3.3 Multi-Step Workflow Testing

```python
class WorkflowTestHarness:
    """Test multi-step agent workflows."""

    def __init__(self, workflow_def: dict):
        self.workflow = workflow_def
        self.step_results = {}
        self.errors = []

    async def execute_with_checkpoints(self, input_data: dict) -> dict:
        """Execute workflow with checkpoints for testing."""
        for step in self.workflow["steps"]:
            try:
                result = await self._execute_step(step, input_data)
                self.step_results[step["id"]] = {
                    "success": True,
                    "result": result
                }
            except Exception as e:
                self.step_results[step["id"]] = {
                    "success": False,
                    "error": str(e)
                }
                self.errors.append(step["id"])

                if not self.workflow.get("continue_on_error"):
                    break

        return {
            "completed": len(self.errors) == 0,
            "steps": self.step_results,
            "errors": self.errors
        }

    def assert_step_completed(self, step_id: str):
        """Assert specific step completed successfully."""
        if step_id not in self.step_results:
            raise AssertionError(f"Step {step_id} was not executed")

        if not self.step_results[step_id]["success"]:
            raise AssertionError(
                f"Step {step_id} failed: {self.step_results[step_id]['error']}"
            )

    def assert_all_steps_completed(self):
        """Assert all steps completed successfully."""
        for step_id, result in self.step_results.items():
            if not result["success"]:
                raise AssertionError(f"Step {step_id} failed")


# Usage
async def test_error_recovery_workflow():
    harness = WorkflowTestHarness(ERROR_RECOVERY_WORKFLOW)

    result = await harness.execute_with_checkpoints({
        "error_message": "Rate limit exceeded",
        "failed_tool": "claude_api"
    })

    harness.assert_step_completed("classify_error")
    harness.assert_step_completed("find_alternatives")
    assert result["completed"]
```

---

## 4. Knowledge Graph Testing

### 4.1 Query Recall Benchmarks

```python
class KGRecallBenchmark:
    """Benchmark KG query recall."""

    GOLDEN_QUERIES = [
        {
            "query": "How to reduce API costs?",
            "expected": ["pattern_context_caching", "use_case_reduce_costs"],
            "min_recall": 1.0  # Must find both
        },
        {
            "query": "multimodal processing",
            "expected": ["pattern_multimodal_input"],
            "min_recall": 0.8
        },
        {
            "query": "error handling best practices",
            "expected": ["pattern_error_handling", "use_case_robust_systems"],
            "min_recall": 0.5
        }
    ]

    def __init__(self, kg_query_func):
        self.query = kg_query_func

    def run_benchmark(self, k: int = 5) -> dict:
        """Run full benchmark suite."""
        results = {
            "total": len(self.GOLDEN_QUERIES),
            "passed": 0,
            "failed": 0,
            "details": []
        }

        for test in self.GOLDEN_QUERIES:
            found = self.query(test["query"], k=k)
            found_names = [r["name"] for r in found]

            matches = [e for e in test["expected"] if e in found_names]
            recall = len(matches) / len(test["expected"])

            passed = recall >= test["min_recall"]
            if passed:
                results["passed"] += 1
            else:
                results["failed"] += 1

            results["details"].append({
                "query": test["query"],
                "expected": test["expected"],
                "found": found_names,
                "recall": recall,
                "passed": passed
            })

        return results


def test_kg_recall_threshold():
    """Test KG maintains minimum recall threshold."""
    benchmark = KGRecallBenchmark(kg.query)
    results = benchmark.run_benchmark()

    assert results["passed"] / results["total"] >= 0.8, \
        f"Recall benchmark failed: {results}"
```

### 4.2 Schema Consistency Tests

```python
def test_kg_schema_consistency():
    """Test KG schema is consistent."""
    conn = sqlite3.connect(KG_PATH)
    cursor = conn.cursor()

    # Test 1: All edges reference valid nodes
    cursor.execute("""
        SELECT COUNT(*) FROM edges e
        WHERE NOT EXISTS (SELECT 1 FROM nodes n WHERE n.node_id = e.source_id)
           OR NOT EXISTS (SELECT 1 FROM nodes n WHERE n.node_id = e.target_id)
    """)
    orphan_edges = cursor.fetchone()[0]
    assert orphan_edges == 0, f"Found {orphan_edges} orphan edges"

    # Test 2: No duplicate nodes
    cursor.execute("""
        SELECT node_id, COUNT(*) as cnt FROM nodes
        GROUP BY node_id HAVING cnt > 1
    """)
    duplicates = cursor.fetchall()
    assert len(duplicates) == 0, f"Found duplicate nodes: {duplicates}"

    # Test 3: All nodes have required fields
    cursor.execute("""
        SELECT COUNT(*) FROM nodes
        WHERE name IS NULL OR node_type IS NULL
    """)
    invalid_nodes = cursor.fetchone()[0]
    assert invalid_nodes == 0, f"Found {invalid_nodes} nodes with missing fields"

    conn.close()
```

### 4.3 Embedding Drift Detection

```python
class EmbeddingDriftDetector:
    """Detect if embeddings have drifted from expected behavior."""

    def __init__(self, reference_path: str):
        with open(reference_path, 'rb') as f:
            self.reference = pickle.load(f)

    def check_drift(self, current_embeddings: dict, threshold: float = 0.1) -> dict:
        """
        Check if current embeddings have drifted from reference.

        Drift indicates potential quality degradation.
        """
        drifted_nodes = []

        for node_id, ref_emb in self.reference.items():
            if node_id not in current_embeddings:
                continue

            curr_emb = current_embeddings[node_id]
            similarity = cosine_similarity([ref_emb], [curr_emb])[0][0]
            drift = 1 - similarity

            if drift > threshold:
                drifted_nodes.append({
                    "node_id": node_id,
                    "drift": drift
                })

        return {
            "total_checked": len(self.reference),
            "drifted_count": len(drifted_nodes),
            "drifted_nodes": drifted_nodes,
            "max_drift": max(d["drift"] for d in drifted_nodes) if drifted_nodes else 0
        }


def test_embedding_stability():
    """Test embeddings haven't drifted significantly."""
    detector = EmbeddingDriftDetector("reference_embeddings.pkl")
    current = load_current_embeddings()

    result = detector.check_drift(current, threshold=0.15)

    assert result["drifted_count"] / result["total_checked"] < 0.05, \
        f"Too many drifted embeddings: {result['drifted_count']}"
```

---

## 5. MCP Server Testing

### 5.1 Tool Contract Testing

```python
class MCPToolContractTest:
    """Test MCP tool contracts."""

    def __init__(self, server_module):
        self.server = server_module
        self.handler = server_module.handler

    async def test_tool_schema(self, tool_name: str):
        """Test tool accepts valid input and returns expected schema."""
        tool_def = next(
            t for t in self.server.TOOL_DEFINITIONS
            if t["name"] == tool_name
        )

        # Generate valid input from schema
        valid_input = self._generate_from_schema(tool_def["inputSchema"])

        # Call tool
        result = await self.handler.handle(tool_name, valid_input)

        # Validate result
        assert "error" not in result or result.get("error") is None
        return result

    async def test_tool_error_handling(self, tool_name: str, invalid_input: dict):
        """Test tool handles invalid input gracefully."""
        result = await self.handler.handle(tool_name, invalid_input)

        # Should return error, not crash
        assert isinstance(result, dict)
        # Error should be descriptive
        if "error" in result:
            assert len(result["error"]) > 0


# Integration test suite
class TestMCPIntentServer:
    @pytest.fixture
    def server(self):
        from nlke_mcp.servers import nlke_intent_server
        return nlke_intent_server

    async def test_want_to_returns_tools(self, server):
        result = await server.handler.handle(
            "want_to",
            {"goal": "read a file"}
        )
        assert "tools" in result
        assert len(result["tools"]) > 0

    async def test_can_it_returns_capability(self, server):
        result = await server.handler.handle(
            "can_it",
            {"capability": "edit binary files"}
        )
        assert "can" in result
        assert isinstance(result["can"], bool)
```

### 5.2 Load Testing

```python
import asyncio
import time

async def load_test_mcp_server(
    handler,
    tool_name: str,
    params: dict,
    concurrent: int = 10,
    duration_seconds: int = 30
) -> dict:
    """Load test an MCP server."""
    results = {
        "total_requests": 0,
        "successful": 0,
        "failed": 0,
        "latencies": [],
        "errors": []
    }

    start_time = time.time()

    async def make_request():
        nonlocal results
        while time.time() - start_time < duration_seconds:
            req_start = time.time()
            try:
                await handler.handle(tool_name, params)
                results["successful"] += 1
                results["latencies"].append(time.time() - req_start)
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(str(e))
            results["total_requests"] += 1

    # Run concurrent workers
    await asyncio.gather(*[make_request() for _ in range(concurrent)])

    # Calculate statistics
    if results["latencies"]:
        results["avg_latency"] = np.mean(results["latencies"])
        results["p95_latency"] = np.percentile(results["latencies"], 95)
        results["p99_latency"] = np.percentile(results["latencies"], 99)

    results["requests_per_second"] = results["total_requests"] / duration_seconds

    return results


async def test_server_handles_load():
    """Test server maintains SLA under load."""
    results = await load_test_mcp_server(
        handler=intent_handler,
        tool_name="want_to",
        params={"goal": "read files"},
        concurrent=10,
        duration_seconds=10
    )

    assert results["p95_latency"] < 2.0, f"P95 latency too high: {results['p95_latency']}"
    assert results["failed"] / results["total_requests"] < 0.01, "Error rate too high"
```

---

## 6. Regression Testing

### 6.1 Model Upgrade Safety

```python
class ModelUpgradeValidator:
    """Validate model upgrades don't degrade quality."""

    def __init__(self, golden_examples: list):
        self.examples = golden_examples

    async def compare_models(
        self,
        old_model,
        new_model,
        quality_func
    ) -> dict:
        """Compare old vs new model on golden examples."""
        results = {
            "improved": 0,
            "degraded": 0,
            "unchanged": 0,
            "details": []
        }

        for example in self.examples:
            old_output = await old_model.process(example["input"])
            new_output = await new_model.process(example["input"])

            old_quality = quality_func(old_output, example["expected"])
            new_quality = quality_func(new_output, example["expected"])

            diff = new_quality - old_quality

            if diff > 0.05:
                results["improved"] += 1
            elif diff < -0.05:
                results["degraded"] += 1
            else:
                results["unchanged"] += 1

            results["details"].append({
                "input": example["input"][:50],
                "old_quality": old_quality,
                "new_quality": new_quality,
                "change": diff
            })

        return results


async def test_model_upgrade_safety():
    """Test new model doesn't degrade quality."""
    validator = ModelUpgradeValidator(GOLDEN_EXAMPLES)

    results = await validator.compare_models(
        old_model=claude_4_0,
        new_model=claude_4_5,
        quality_func=semantic_similarity
    )

    # Allow some degradation but flag significant drops
    degraded_pct = results["degraded"] / len(GOLDEN_EXAMPLES)
    assert degraded_pct < 0.1, f"Too much degradation: {degraded_pct:.1%}"
```

### 6.2 Prompt Change Impact

```python
class PromptRegressionTest:
    """Test prompt changes don't break behavior."""

    def __init__(self, test_cases: list):
        self.test_cases = test_cases

    async def test_prompt_change(
        self,
        old_prompt: str,
        new_prompt: str,
        llm
    ) -> dict:
        """Compare outputs with old vs new prompt."""
        results = []

        for case in self.test_cases:
            old_result = await llm.process(case["input"], prompt=old_prompt)
            new_result = await llm.process(case["input"], prompt=new_prompt)

            # Check key properties maintained
            properties_maintained = self._check_properties(
                old_result, new_result, case.get("required_properties", [])
            )

            results.append({
                "input": case["input"][:50],
                "properties_maintained": properties_maintained,
                "old_output": old_result[:100],
                "new_output": new_result[:100]
            })

        maintained_count = sum(1 for r in results if r["properties_maintained"])

        return {
            "total": len(results),
            "maintained": maintained_count,
            "broken": len(results) - maintained_count,
            "details": results
        }

    def _check_properties(self, old: str, new: str, properties: list) -> bool:
        """Check if required properties are maintained."""
        for prop in properties:
            if prop == "length_similar":
                if abs(len(old) - len(new)) > len(old) * 0.5:
                    return False
            elif prop == "contains_keywords":
                # Check both contain similar keywords
                old_words = set(old.lower().split())
                new_words = set(new.lower().split())
                overlap = len(old_words & new_words) / len(old_words | new_words)
                if overlap < 0.3:
                    return False
        return True
```

---

## 7. Performance Testing

### 7.1 Latency Benchmarks

```python
class LatencyBenchmark:
    """Benchmark query latency."""

    def __init__(self):
        self.measurements = []

    async def measure(self, func, *args, iterations: int = 100, **kwargs):
        """Measure function latency over multiple iterations."""
        for _ in range(iterations):
            start = time.perf_counter()
            await func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            self.measurements.append(elapsed)

        return {
            "iterations": iterations,
            "mean": np.mean(self.measurements),
            "median": np.median(self.measurements),
            "std": np.std(self.measurements),
            "p50": np.percentile(self.measurements, 50),
            "p95": np.percentile(self.measurements, 95),
            "p99": np.percentile(self.measurements, 99),
            "min": min(self.measurements),
            "max": max(self.measurements)
        }


async def test_query_latency_sla():
    """Test query latency meets SLA."""
    benchmark = LatencyBenchmark()

    results = await benchmark.measure(
        kg.query,
        "reduce API costs",
        k=5,
        iterations=100
    )

    assert results["p95"] < 0.5, f"P95 latency {results['p95']:.3f}s exceeds 500ms SLA"
    assert results["p99"] < 1.0, f"P99 latency {results['p99']:.3f}s exceeds 1s SLA"
```

### 7.2 Cost Tracking Tests

```python
def test_cost_within_budget():
    """Test operation costs stay within budget."""
    tracker = CostTracker()

    # Simulate operations
    operations = [
        {"model": "claude-opus", "input_tokens": 1000, "output_tokens": 500},
        {"model": "gemini-flash", "input_tokens": 10000, "output_tokens": 2000},
    ]

    total_cost = 0
    for op in operations:
        cost = tracker.calculate_cost(
            model=op["model"],
            input_tokens=op["input_tokens"],
            output_tokens=op["output_tokens"]
        )
        total_cost += cost

    assert total_cost < 1.0, f"Total cost ${total_cost:.2f} exceeds $1.00 budget"
```

---

## 8. CI/CD Integration

### 8.1 GitHub Actions Workflow

```yaml
name: AI System Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements-test.txt

      - name: Run unit tests
        run: pytest tests/unit/ -v --tb=short

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v3

      - name: Run integration tests
        run: pytest tests/integration/ -v --tb=short

  kg-benchmark:
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - name: Run KG recall benchmark
        run: python tests/benchmarks/kg_recall.py

      - name: Check recall threshold
        run: |
          RECALL=$(cat recall_results.json | jq '.recall_at_5')
          if (( $(echo "$RECALL < 0.85" | bc -l) )); then
            echo "Recall $RECALL below 0.85 threshold"
            exit 1
          fi

  load-test:
    runs-on: ubuntu-latest
    needs: integration-tests
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - name: Run load test
        run: python tests/load/mcp_server_load.py --duration 60 --concurrent 10

      - name: Check SLA
        run: python tests/load/check_sla.py results.json
```

### 8.2 Test Configuration

```python
# conftest.py
import pytest

def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: marks integration tests")
    config.addinivalue_line("markers", "benchmark: marks benchmark tests")

@pytest.fixture(scope="session")
def kg_connection():
    """Shared KG connection for all tests."""
    conn = sqlite3.connect(KG_PATH)
    yield conn
    conn.close()

@pytest.fixture(scope="session")
def embeddings():
    """Shared embeddings for all tests."""
    with open(EMBEDDING_PATH, 'rb') as f:
        return pickle.load(f)
```

---

## Related Playbooks

| Playbook | Relationship |
|----------|--------------|
| PB 3: Agent Development | Agent testing patterns |
| PB 10: MCP Server Development | Server testing |
| PB 12: Production Deployment | Production validation |
| PB 14: Embedding Systems | Embedding benchmarks |

---

## Key Insights

- **Property > Exact Match** for LLM outputs
- **Semantic Similarity** replaces string equality
- **Golden Datasets** provide regression safety
- **CI/CD Integration** catches issues early

---

**Playbook Version:** 1.0
**Last Updated:** November 27, 2025

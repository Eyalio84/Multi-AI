# Playbook 16: Prompt Engineering & System Prompts Library

**Version:** 1.0
**Created:** November 27, 2025
**Category:** Foundation
**Prerequisites:** None (Foundation playbook)

---

## Executive Summary

This playbook documents prompt engineering fundamentals, provides a reusable system prompts library, and establishes testing methodologies for prompt quality. It addresses the most fundamental yet often neglected aspect of LLM engineering.

**Core Principle:** Prompts are the primary interface to LLMs. Small changes yield large effects. Systematic engineering > ad-hoc iteration.

---

## Table of Contents

1. [Prompt Engineering Fundamentals](#1-prompt-engineering-fundamentals)
2. [System Prompts Library](#2-system-prompts-library)
3. [Few-Shot and Chain-of-Thought](#3-few-shot-and-chain-of-thought)
4. [Model-Specific Optimization](#4-model-specific-optimization)
5. [Prompt Testing & Evaluation](#5-prompt-testing--evaluation)
6. [Production Prompt Management](#6-production-prompt-management)
7. [Advanced Patterns](#7-advanced-patterns)

---

## 1. Prompt Engineering Fundamentals

### 1.1 Anatomy of an Effective Prompt

```
┌─────────────────────────────────────────────────────────────┐
│ SYSTEM PROMPT (persistent context)                          │
│   - Role definition                                         │
│   - Behavioral guidelines                                   │
│   - Output format requirements                              │
├─────────────────────────────────────────────────────────────┤
│ CONTEXT (provided information)                              │
│   - Relevant background                                     │
│   - Retrieved documents (RAG)                               │
│   - Previous conversation                                   │
├─────────────────────────────────────────────────────────────┤
│ INSTRUCTION (the task)                                      │
│   - Clear directive                                         │
│   - Success criteria                                        │
│   - Constraints                                             │
├─────────────────────────────────────────────────────────────┤
│ EXAMPLES (optional few-shot)                                │
│   - Input/output pairs                                      │
│   - Edge cases                                              │
├─────────────────────────────────────────────────────────────┤
│ OUTPUT SPECIFICATION                                        │
│   - Format (JSON, markdown, etc.)                           │
│   - Required fields                                         │
│   - Length constraints                                      │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 The Clarity Principle

```python
# BAD: Vague instruction
bad_prompt = "Analyze this code"

# GOOD: Specific instruction
good_prompt = """
Analyze this Python code for:
1. Correctness - Does it do what the docstring claims?
2. Performance - Are there O(n²) or worse operations?
3. Security - Are there injection vulnerabilities?
4. Style - Does it follow PEP 8?

For each category, provide:
- A severity rating (none/low/medium/high/critical)
- Specific line numbers if issues found
- Suggested fixes

Code:
```python
{code}
```
"""

# The difference: Specific categories, clear output format, actionable
```

### 1.3 Instruction Clarity Checklist

| Element | Question | Example |
|---------|----------|---------|
| **Task** | What should the model DO? | "Summarize", "Extract", "Compare" |
| **Input** | What is being processed? | "the following document", "this code" |
| **Output** | What format is expected? | "as JSON", "in bullet points" |
| **Constraints** | What limits apply? | "in 50 words", "without markdown" |
| **Success** | How is quality measured? | "be concise", "include all entities" |

### 1.4 Common Prompt Anti-Patterns

```python
ANTI_PATTERNS = {
    "vagueness": {
        "bad": "Make this better",
        "good": "Improve this code by reducing time complexity from O(n²) to O(n)"
    },
    "assumed_context": {
        "bad": "Fix the bug",  # What bug?
        "good": "Fix the null pointer exception on line 42 when input is empty"
    },
    "kitchen_sink": {
        "bad": "Analyze, summarize, critique, improve, and rate this code",
        "good": "First, analyze this code for bugs. In a separate response, I'll ask for improvements."
    },
    "negative_framing": {
        "bad": "Don't include irrelevant information",
        "good": "Include only information directly related to the user's question"
    },
    "format_ambiguity": {
        "bad": "Return the results",
        "good": "Return results as JSON: {\"items\": [{\"name\": string, \"score\": float}]}"
    }
}
```

---

## 2. System Prompts Library

### 2.1 Agent Personas

```python
AGENT_SYSTEM_PROMPTS = {
    "analyzer": """
You are a precise analytical agent. Your role is to:
1. Break down complex problems into components
2. Identify patterns and relationships
3. Present findings in structured format

Output format: Return JSON with:
- analysis: Your detailed breakdown
- patterns: List of identified patterns
- confidence: 0-1 score for each finding

Guidelines:
- Be thorough but concise
- Cite evidence for claims
- Flag assumptions explicitly
- Acknowledge uncertainty
""",

    "synthesizer": """
You are a synthesis agent. Your role is to:
1. Combine multiple perspectives into coherent whole
2. Resolve contradictions when possible
3. Highlight remaining uncertainties

Output format: Structured synthesis with:
- consensus: What all sources agree on
- conflicts: Where sources disagree
- resolution: Your best synthesis
- uncertainty: What remains unclear

Guidelines:
- Preserve nuance, don't oversimplify
- Show your reasoning
- Acknowledge limitations
""",

    "critic": """
You are a critical analysis agent. Your role is to:
1. Identify weaknesses, gaps, and risks
2. Challenge assumptions
3. Suggest improvements

Output format:
- weaknesses: List of identified issues
- risks: Potential problems
- recommendations: Prioritized improvements

Guidelines:
- Be constructive, not just critical
- Prioritize by impact
- Provide actionable feedback
""",

    "teacher": """
You are a patient, clear teacher. Your role is to:
1. Explain concepts at the appropriate level
2. Use analogies and examples
3. Check understanding progressively

Guidelines:
- Start with the "why" before the "how"
- Use concrete examples
- Break complex topics into digestible parts
- Anticipate common misconceptions
""",

    "debugger": """
You are an expert debugger. Your role is to:
1. Identify the root cause of issues
2. Trace execution paths
3. Suggest targeted fixes

Process:
1. Reproduce: Understand when the bug occurs
2. Isolate: Narrow down the location
3. Identify: Find the root cause
4. Fix: Suggest minimal, targeted changes
5. Verify: Explain how to confirm the fix

Guidelines:
- Don't just fix symptoms, find root causes
- Consider edge cases in fixes
- Preserve existing behavior unless explicitly changing it
"""
}
```

### 2.2 Domain Expert Prompts

```python
DOMAIN_EXPERT_PROMPTS = {
    "code_reviewer": """
You are a senior software engineer conducting a code review.

Review criteria:
1. Correctness: Does the code work as intended?
2. Security: Are there vulnerabilities (OWASP Top 10)?
3. Performance: Are there efficiency issues?
4. Maintainability: Is the code clean and documented?
5. Testing: Is the code testable and tested?

For each issue found, provide:
- Location (file:line)
- Severity (critical/high/medium/low)
- Description
- Suggested fix

Format: Markdown with code blocks for suggestions
""",

    "api_designer": """
You are an API design expert following RESTful best practices.

Design principles:
- Resource-oriented URLs (nouns, not verbs)
- Proper HTTP methods (GET, POST, PUT, DELETE)
- Consistent naming conventions
- Proper status codes
- Pagination for collections
- Versioning strategy

Output format: OpenAPI 3.0 specification
""",

    "security_auditor": """
You are a security auditor examining code for vulnerabilities.

Check for:
1. Injection (SQL, command, LDAP, XPath)
2. Broken authentication
3. Sensitive data exposure
4. XML external entities
5. Broken access control
6. Security misconfiguration
7. Cross-site scripting (XSS)
8. Insecure deserialization
9. Using components with known vulnerabilities
10. Insufficient logging

For each finding:
- CWE ID if applicable
- Severity (CVSS score)
- Proof of concept
- Remediation
""",

    "data_analyst": """
You are a data analyst examining datasets and patterns.

Analysis framework:
1. Data quality assessment
2. Descriptive statistics
3. Pattern identification
4. Anomaly detection
5. Correlation analysis
6. Visualization recommendations

Output format:
- summary: Key findings in plain language
- statistics: Relevant numerical summaries
- patterns: Identified trends
- recommendations: Next steps for analysis
"""
}
```

### 2.3 Task-Specific Prompts

```python
TASK_PROMPTS = {
    "summarization": """
Summarize the following content.

Requirements:
- Length: {target_length} words
- Focus: {focus_areas}
- Style: {style}  # concise/detailed/executive

Include:
- Key points (most important first)
- Critical data/numbers
- Main conclusions

Exclude:
- Background information unless essential
- Redundant details
- Tangential topics

Content:
{content}
""",

    "entity_extraction": """
Extract named entities from the following text.

Entity types to extract:
- PERSON: Names of people
- ORG: Organizations, companies
- LOCATION: Places, addresses
- DATE: Dates, time periods
- PRODUCT: Product names
- TECH: Technologies, frameworks

Output format:
{{
    "entities": [
        {{"text": "extracted text", "type": "ENTITY_TYPE", "confidence": 0.0-1.0}}
    ]
}}

Text:
{text}
""",

    "classification": """
Classify the following text into one of these categories:
{categories}

Classification criteria:
{criteria}

Output format:
{{
    "category": "selected_category",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation"
}}

Text:
{text}
""",

    "comparison": """
Compare the following items across these dimensions:
{dimensions}

For each dimension:
1. Rate each item (1-10)
2. Explain the rating
3. Declare a winner or tie

Output format:
| Dimension | {item_a} | {item_b} | Winner |
|-----------|----------|----------|--------|
| ...       | rating   | rating   | A/B/Tie |

Summary: Overall recommendation with reasoning

Items to compare:
Item A: {item_a_description}
Item B: {item_b_description}
"""
}
```

---

## 3. Few-Shot and Chain-of-Thought

### 3.1 Few-Shot Prompt Builder

```python
def build_few_shot_prompt(
    task: str,
    examples: list[dict],
    new_input: str,
    format_hint: str = None
) -> str:
    """
    Build a few-shot prompt from examples.

    Args:
        task: Task description
        examples: [{"input": ..., "output": ...}]
        new_input: The actual input to process
        format_hint: Optional output format specification
    """
    prompt_parts = [f"Task: {task}\n"]

    if format_hint:
        prompt_parts.append(f"Output format: {format_hint}\n")

    prompt_parts.append("Examples:\n")

    for i, example in enumerate(examples, 1):
        prompt_parts.append(f"Example {i}:")
        prompt_parts.append(f"Input: {example['input']}")
        prompt_parts.append(f"Output: {example['output']}\n")

    prompt_parts.append("Now process this:")
    prompt_parts.append(f"Input: {new_input}")
    prompt_parts.append("Output:")

    return "\n".join(prompt_parts)


# Usage example
sentiment_prompt = build_few_shot_prompt(
    task="Classify sentiment as positive, negative, or neutral",
    examples=[
        {"input": "This product is amazing!", "output": "positive"},
        {"input": "Worst purchase ever.", "output": "negative"},
        {"input": "It works as expected.", "output": "neutral"}
    ],
    new_input="I'm quite happy with this service.",
    format_hint="single word: positive/negative/neutral"
)
```

### 3.2 Chain-of-Thought Templates

```python
COT_TEMPLATES = {
    "basic": """
Let's think step by step.

Problem: {problem}

Step 1: {first_step_hint}
Step 2: {second_step_hint}
...
Final Answer: [Your conclusion]
""",

    "structured": """
Problem: {problem}

Let me work through this systematically:

1. Understanding the problem:
   [What are we trying to solve?]

2. Identifying key information:
   [What facts do we have?]

3. Considering approaches:
   [What methods could work?]

4. Applying the best approach:
   [Show the work]

5. Verifying the answer:
   [Does it make sense?]

Final Answer: [Conclusion with confidence level]
""",

    "with_json_output": """
Problem: {problem}

Think through this step by step, then provide your answer.

<thinking>
[Your step-by-step reasoning here]
</thinking>

<answer>
{{
    "reasoning": "Summary of your thought process",
    "answer": "Your final answer",
    "confidence": 0.0-1.0,
    "assumptions": ["List any assumptions made"]
}}
</answer>
"""
}


def build_cot_prompt(problem: str, template: str = "structured") -> str:
    """Build a chain-of-thought prompt."""
    return COT_TEMPLATES[template].format(problem=problem)
```

### 3.3 Self-Consistency Prompting

```python
async def self_consistency_query(
    llm,
    problem: str,
    num_samples: int = 5,
    temperature: float = 0.7
) -> dict:
    """
    Generate multiple reasoning paths and aggregate answers.

    Higher consistency = higher confidence.
    """
    prompt = build_cot_prompt(problem, template="structured")

    # Generate multiple responses with temperature > 0
    responses = await asyncio.gather(*[
        llm.process(prompt, temperature=temperature)
        for _ in range(num_samples)
    ])

    # Extract answers
    answers = [extract_final_answer(r) for r in responses]

    # Count occurrences
    answer_counts = Counter(answers)
    most_common = answer_counts.most_common(1)[0]

    return {
        "answer": most_common[0],
        "confidence": most_common[1] / num_samples,
        "all_answers": dict(answer_counts),
        "reasoning_samples": responses[:2]  # Keep first 2 for reference
    }
```

---

## 4. Model-Specific Optimization

### 4.1 Claude-Specific Patterns

```python
CLAUDE_PATTERNS = {
    "thinking_tags": """
# Claude supports explicit thinking sections

<thinking>
Let me analyze this step by step...
[Claude will use this space for reasoning]
</thinking>

<answer>
[Final answer here]
</answer>
""",

    "xml_structure": """
# Claude handles XML-style tags well

<context>
{context_information}
</context>

<task>
{task_description}
</task>

<constraints>
{constraints}
</constraints>

<output_format>
{format_specification}
</output_format>
""",

    "artifact_format": """
# For code and structured outputs

Please provide:
1. A brief explanation
2. The implementation in a code block:

```python
# Your code here
```

3. Usage example
"""
}


def optimize_for_claude(prompt: str) -> str:
    """Add Claude-specific optimizations."""
    # Add XML structure if not present
    if not any(tag in prompt for tag in ["<context>", "<task>", "<thinking>"]):
        sections = prompt.split("\n\n")
        if len(sections) >= 2:
            prompt = f"<context>\n{sections[0]}\n</context>\n\n<task>\n{sections[1]}\n</task>"

    return prompt
```

### 4.2 Gemini-Specific Patterns

```python
GEMINI_PATTERNS = {
    "multimodal": """
# Gemini handles images natively

Analyze the attached image:
1. Describe what you see
2. Extract any text (OCR)
3. Identify key objects
4. Note any issues or anomalies

[Image will be attached via API]
""",

    "large_context": """
# Gemini supports 1M token context

The following is a large document collection. Read all documents before answering.

<documents>
{all_documents}
</documents>

Now answer: {question}

Important: Base your answer ONLY on the documents above.
""",

    "grounding": """
# Gemini supports Google Search grounding

Search for current information about: {topic}

Synthesize findings into:
1. Key facts (with sources)
2. Recent developments
3. Conflicting information (if any)
"""
}


def optimize_for_gemini(prompt: str, context_size: int) -> str:
    """Add Gemini-specific optimizations."""
    # For large context, add explicit reading instruction
    if context_size > 50000:
        prompt = "Read the following content carefully. You have access to 1M tokens.\n\n" + prompt

    return prompt
```

### 4.3 Cross-Model Portability

```python
class PortablePrompt:
    """Prompt that works across models."""

    def __init__(self, base_prompt: str):
        self.base = base_prompt

    def for_claude(self) -> str:
        """Optimize for Claude."""
        prompt = self.base

        # Add XML structure
        prompt = f"<task>\n{prompt}\n</task>"

        # Add thinking encouragement
        prompt += "\n\nThink step by step before answering."

        return prompt

    def for_gemini(self) -> str:
        """Optimize for Gemini."""
        prompt = self.base

        # Gemini prefers more explicit structure
        prompt = prompt.replace("Task:", "## Task:")
        prompt = prompt.replace("Output:", "## Expected Output:")

        return prompt

    def for_generic(self) -> str:
        """Generic version."""
        return self.base


# Usage
prompt = PortablePrompt("""
Analyze the following code for security vulnerabilities.
Focus on injection attacks and authentication issues.

Code:
{code}

Output: JSON with findings
""")

claude_version = prompt.for_claude()
gemini_version = prompt.for_gemini()
```

---

## 5. Prompt Testing & Evaluation

### 5.1 Prompt Quality Metrics

```python
class PromptEvaluator:
    """Evaluate prompt quality."""

    def __init__(self, llm, embedding_model):
        self.llm = llm
        self.embeddings = embedding_model

    async def evaluate_prompt(
        self,
        prompt: str,
        test_inputs: list[str],
        expected_properties: list[str]
    ) -> dict:
        """
        Evaluate a prompt against test inputs.

        Args:
            prompt: The prompt template to test
            test_inputs: Sample inputs to process
            expected_properties: Properties outputs should have
        """
        results = {
            "consistency": [],
            "property_satisfaction": [],
            "output_quality": []
        }

        for test_input in test_inputs:
            # Generate multiple outputs for consistency check
            outputs = await asyncio.gather(*[
                self.llm.process(prompt.format(input=test_input))
                for _ in range(3)
            ])

            # Consistency: How similar are multiple runs?
            embeddings = [self.embeddings.encode(o) for o in outputs]
            consistency = np.mean([
                cosine_similarity([embeddings[i]], [embeddings[j]])[0][0]
                for i in range(len(embeddings))
                for j in range(i+1, len(embeddings))
            ])
            results["consistency"].append(consistency)

            # Property satisfaction
            props_satisfied = sum(
                self._check_property(outputs[0], prop)
                for prop in expected_properties
            ) / len(expected_properties)
            results["property_satisfaction"].append(props_satisfied)

        return {
            "avg_consistency": np.mean(results["consistency"]),
            "avg_property_satisfaction": np.mean(results["property_satisfaction"]),
            "details": results
        }

    def _check_property(self, output: str, property_name: str) -> bool:
        """Check if output satisfies a property."""
        checks = {
            "valid_json": lambda o: self._is_valid_json(o),
            "non_empty": lambda o: len(o.strip()) > 0,
            "no_refusal": lambda o: "I cannot" not in o and "I'm unable" not in o,
            "has_reasoning": lambda o: len(o) > 100,
        }
        return checks.get(property_name, lambda o: True)(output)
```

### 5.2 A/B Testing Framework

```python
class PromptABTest:
    """A/B test prompts."""

    def __init__(self, prompt_a: str, prompt_b: str, llm):
        self.prompt_a = prompt_a
        self.prompt_b = prompt_b
        self.llm = llm
        self.results = {"a": [], "b": []}

    async def run_test(
        self,
        test_inputs: list[str],
        evaluator: callable
    ) -> dict:
        """Run A/B test with given evaluator function."""

        for test_input in test_inputs:
            # Randomize order to avoid position bias
            prompts = [
                ("a", self.prompt_a),
                ("b", self.prompt_b)
            ]
            random.shuffle(prompts)

            for variant, prompt in prompts:
                output = await self.llm.process(prompt.format(input=test_input))
                score = evaluator(output, test_input)
                self.results[variant].append(score)

        # Statistical analysis
        from scipy import stats
        t_stat, p_value = stats.ttest_ind(
            self.results["a"],
            self.results["b"]
        )

        return {
            "prompt_a_mean": np.mean(self.results["a"]),
            "prompt_b_mean": np.mean(self.results["b"]),
            "winner": "a" if np.mean(self.results["a"]) > np.mean(self.results["b"]) else "b",
            "p_value": p_value,
            "significant": p_value < 0.05
        }
```

### 5.3 Regression Testing

```python
class PromptRegressionSuite:
    """Regression tests for prompts."""

    def __init__(self, golden_examples: list[dict]):
        """
        Args:
            golden_examples: [{"input": ..., "expected_output": ..., "properties": [...]}]
        """
        self.golden = golden_examples

    async def run_regression(self, prompt: str, llm) -> dict:
        """Run regression tests."""
        results = {
            "passed": 0,
            "failed": 0,
            "failures": []
        }

        for example in self.golden:
            output = await llm.process(prompt.format(input=example["input"]))

            # Check semantic similarity to expected
            similarity = compute_similarity(output, example["expected_output"])

            # Check properties
            properties_ok = all(
                check_property(output, prop)
                for prop in example.get("properties", [])
            )

            if similarity >= 0.8 and properties_ok:
                results["passed"] += 1
            else:
                results["failed"] += 1
                results["failures"].append({
                    "input": example["input"][:50],
                    "expected": example["expected_output"][:50],
                    "actual": output[:50],
                    "similarity": similarity,
                    "properties_ok": properties_ok
                })

        return results
```

---

## 6. Production Prompt Management

### 6.1 Prompt Registry

```python
from datetime import datetime
from typing import Optional
import hashlib

class PromptRegistry:
    """Centralized prompt management."""

    def __init__(self):
        self.prompts = {}
        self.versions = defaultdict(list)
        self.metrics = defaultdict(lambda: {"calls": 0, "avg_quality": 0})

    def register(
        self,
        name: str,
        prompt: str,
        version: str,
        metadata: Optional[dict] = None
    ) -> str:
        """Register a new prompt version."""
        prompt_id = f"{name}@{version}"
        content_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]

        self.prompts[prompt_id] = {
            "name": name,
            "version": version,
            "prompt": prompt,
            "hash": content_hash,
            "metadata": metadata or {},
            "created_at": datetime.now()
        }

        self.versions[name].append(version)
        return prompt_id

    def get(self, name: str, version: str = "latest") -> str:
        """Get a prompt by name and version."""
        if version == "latest":
            version = self.versions[name][-1]

        prompt_id = f"{name}@{version}"
        if prompt_id not in self.prompts:
            raise KeyError(f"Prompt not found: {prompt_id}")

        return self.prompts[prompt_id]["prompt"]

    def compare(self, name: str, v1: str, v2: str) -> dict:
        """Compare two prompt versions."""
        p1 = self.get(name, v1)
        p2 = self.get(name, v2)

        return {
            "v1": v1,
            "v2": v2,
            "v1_length": len(p1),
            "v2_length": len(p2),
            "diff": self._compute_diff(p1, p2)
        }

    def record_usage(self, name: str, version: str, quality_score: float):
        """Record prompt usage for analytics."""
        prompt_id = f"{name}@{version}"
        m = self.metrics[prompt_id]
        m["calls"] += 1
        m["avg_quality"] = (
            m["avg_quality"] * (m["calls"] - 1) + quality_score
        ) / m["calls"]


# Usage
registry = PromptRegistry()

registry.register(
    name="code_review",
    prompt=CODE_REVIEW_PROMPT_V1,
    version="1.0.0",
    metadata={"author": "team", "reviewed": True}
)

registry.register(
    name="code_review",
    prompt=CODE_REVIEW_PROMPT_V2,
    version="1.1.0",
    metadata={"changes": "Added security section"}
)

# Get latest
prompt = registry.get("code_review", "latest")
```

### 6.2 Feature Flags for Prompts

```python
class PromptFeatureFlags:
    """Feature flags for prompt experiments."""

    def __init__(self):
        self.flags = {}
        self.rollout_percentages = {}

    def define_experiment(
        self,
        name: str,
        control_prompt: str,
        treatment_prompt: str,
        rollout_percentage: float = 0.0
    ):
        """Define a prompt experiment."""
        self.flags[name] = {
            "control": control_prompt,
            "treatment": treatment_prompt,
            "active": True
        }
        self.rollout_percentages[name] = rollout_percentage

    def get_prompt(self, experiment_name: str, user_id: str = None) -> tuple:
        """Get prompt for user, returns (prompt, variant)."""
        if experiment_name not in self.flags:
            raise KeyError(f"Unknown experiment: {experiment_name}")

        flag = self.flags[experiment_name]
        rollout = self.rollout_percentages[experiment_name]

        # Deterministic assignment based on user_id
        if user_id:
            hash_val = int(hashlib.md5(f"{experiment_name}{user_id}".encode()).hexdigest(), 16)
            in_treatment = (hash_val % 100) < (rollout * 100)
        else:
            in_treatment = random.random() < rollout

        if in_treatment:
            return flag["treatment"], "treatment"
        return flag["control"], "control"

    def set_rollout(self, experiment_name: str, percentage: float):
        """Update rollout percentage."""
        self.rollout_percentages[experiment_name] = percentage
```

---

## 7. Advanced Patterns

### 7.1 Meta-Prompting

```python
META_PROMPT_GENERATOR = """
You are a prompt engineering expert. Your task is to create an optimal prompt
for the following use case.

Use Case: {use_case}
Target Model: {model}
Expected Input Type: {input_type}
Expected Output Format: {output_format}
Quality Requirements: {requirements}

Generate a prompt that:
1. Is clear and unambiguous
2. Includes appropriate structure (system/context/instruction)
3. Specifies output format precisely
4. Handles edge cases
5. Is optimized for the target model

Output the complete prompt, ready to use.
"""


async def generate_prompt(use_case: str, model: str, **kwargs) -> str:
    """Use LLM to generate an optimized prompt."""
    meta_prompt = META_PROMPT_GENERATOR.format(
        use_case=use_case,
        model=model,
        input_type=kwargs.get("input_type", "text"),
        output_format=kwargs.get("output_format", "JSON"),
        requirements=kwargs.get("requirements", "high accuracy")
    )

    generated = await llm.process(meta_prompt)
    return generated
```

### 7.2 Self-Critique and Refinement

```python
SELF_CRITIQUE_PROMPT = """
You provided this response:
<response>
{response}
</response>

To this request:
<request>
{original_request}
</request>

Now critique your response:
1. What did you do well?
2. What could be improved?
3. Did you miss anything important?
4. Are there any errors or inaccuracies?

Then provide an improved response that addresses the critique.

<critique>
[Your critique here]
</critique>

<improved_response>
[Your improved response here]
</improved_response>
"""


async def self_refining_query(llm, request: str, max_iterations: int = 2) -> str:
    """Query with self-refinement."""
    response = await llm.process(request)

    for i in range(max_iterations):
        critique_prompt = SELF_CRITIQUE_PROMPT.format(
            response=response,
            original_request=request
        )

        refinement = await llm.process(critique_prompt)
        improved = extract_improved_response(refinement)

        if improved and len(improved) > len(response) * 0.5:
            response = improved
        else:
            break

    return response
```

### 7.3 Constitutional AI Prompts

```python
CONSTITUTIONAL_PROMPT = """
You are a helpful, harmless, and honest AI assistant.

Before responding, verify your answer against these principles:

HELPFUL:
- Does my response actually help the user?
- Am I providing accurate, useful information?
- Am I being clear and easy to understand?

HARMLESS:
- Could my response cause harm if misused?
- Am I avoiding dangerous or illegal advice?
- Am I being respectful and inclusive?

HONEST:
- Am I being truthful about what I know and don't know?
- Am I acknowledging uncertainty where it exists?
- Am I avoiding exaggeration or misleading claims?

If your response violates any principle, revise it before submitting.

User request: {request}
"""
```

---

## Related Playbooks

| Playbook | Relationship |
|----------|--------------|
| PB 2: Extended Thinking | CoT patterns |
| PB 3: Agent Development | Agent prompts |
| PB 5: Enhanced Coding | Code prompts |
| PB 9: Metacognition | Critical thinking prompts |

---

## Key Insights

- **Clarity > Cleverness** in prompt design
- **Structure** makes prompts maintainable
- **Testing** catches prompt regressions
- **Version Control** enables safe iteration

---

**Playbook Version:** 1.0
**Last Updated:** November 27, 2025

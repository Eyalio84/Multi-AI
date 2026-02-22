# Playbook 5: Enhanced Coding with Claude
## Advanced Code Generation, Refactoring, Testing & Optimization

**Version:** 1.0
**Last Updated:** November 8, 2025
**Audience:** Software Engineers, DevOps Engineers, Technical Leads
**Prerequisites:** Programming fundamentals, familiarity with software development lifecycle

---

## Table of Contents

1. [Introduction](#introduction)
2. [Pattern Library](#pattern-library)
3. [Context-Aware Code Generation](#context-aware-code-generation)
4. [Codebase Analysis & Understanding](#codebase-analysis--understanding)
5. [Intelligent Refactoring](#intelligent-refactoring)
6. [Test Generation & Validation](#test-generation--validation)
7. [Documentation Generation](#documentation-generation)
8. [Error Handling & Debugging](#error-handling--debugging)
9. [Performance Optimization](#performance-optimization)
10. [Code Review Automation](#code-review-automation)
11. [Migration & Modernization](#migration--modernization)
12. [Production Patterns](#production-patterns)
13. [Cost Optimization](#cost-optimization)
14. [Troubleshooting](#troubleshooting)
15. [Real-World Use Cases](#real-world-use-cases)

---

## Introduction

### What is Enhanced Coding with Claude?

Enhanced Coding goes beyond basic code generation to provide intelligent, context-aware assistance across the entire software development lifecycle. Claude excels at:

- **Context-Aware Generation**: Understanding project structure, coding patterns, and conventions
- **Intelligent Refactoring**: Improving code quality while preserving functionality
- **Comprehensive Testing**: Generating unit, integration, and end-to-end tests
- **Living Documentation**: Creating and maintaining up-to-date documentation
- **Bug Detection**: Identifying and fixing errors proactively
- **Performance Tuning**: Optimizing code for speed and resource efficiency

### Why Claude for Enhanced Coding?

1. **Large Context Window**: 200K tokens = ~50,000 lines of code analyzable at once
2. **Extended Thinking**: Deep reasoning for complex refactoring and architecture decisions
3. **Multi-Language Support**: Python, JavaScript, TypeScript, Go, Rust, Java, C++, and more
4. **Tool Integration**: Direct interaction with IDEs, test runners, linters, and build systems
5. **Consistency**: Maintains coding style and patterns across entire codebase

### Playbook Goals

By the end of this playbook, you will:

- Generate production-ready code with proper error handling and documentation
- Analyze and understand complex codebases quickly
- Refactor code systematically with confidence
- Generate comprehensive test suites automatically
- Maintain living documentation that stays synchronized with code
- Debug and optimize code efficiently
- Automate code review workflows
- Migrate legacy code to modern frameworks

---

## Pattern Library

### Official Examples Used in This Playbook

| Example | Category | Purpose | Location |
|---------|----------|---------|----------|
| Extended Thinking - Basic | Extended Thinking | Complex architecture decisions | Week 1-2 Examples |
| Streaming Extended Thinking | Extended Thinking | Real-time code generation feedback | Week 1-2 Examples |
| Tool Use with Extended Thinking | Extended Thinking | IDE/build system integration | Week 1-2 Examples |
| Prompt Caching - Large Context | Prompt Caching | Cache codebase context | Week 1-2 Examples |
| Prompt Caching - Tool Definitions | Prompt Caching | Cache coding standards/patterns | Week 1-2 Examples |
| Batch API - Code Review | Batch Processing | Parallel file analysis | Week 1-2 Examples |

### Pattern Combinations for Enhanced Coding

```
Pattern: Codebase Analysis → Refactoring
- Prompt Caching for codebase structure
- Extended Thinking for refactoring strategy
- Tool Use for applying changes via IDE

Pattern: Test Generation → Validation
- Prompt Caching for test frameworks/patterns
- Extended Thinking for edge case identification
- Tool Use for running test suite

Pattern: Documentation → Synchronization
- Prompt Caching for documentation style guide
- Streaming for real-time doc generation
- Tool Use for updating doc files
```

---

## Context-Aware Code Generation

### Basic Code Generation with Context

**Goal**: Generate code that fits naturally into existing codebase

```python
import anthropic
import os

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def generate_function(
    codebase_context: str,
    function_spec: str,
    language: str = "python"
):
    """
    Generate a function that matches existing code style and patterns.

    Args:
        codebase_context: Existing code samples showing style/patterns
        function_spec: Description of function to generate
        language: Programming language

    Returns:
        Generated function code
    """
    prompt = f"""Given this existing codebase context showing our coding style:

```{language}
{codebase_context}
```

Generate a {language} function that:
{function_spec}

Requirements:
1. Match the existing code style (naming, formatting, patterns)
2. Include proper type hints/annotations
3. Add comprehensive docstring
4. Include error handling
5. Add inline comments for complex logic
6. Follow DRY principle (don't repeat existing code)

Return only the function code, properly formatted.
"""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text


# Example usage
existing_code = '''
def process_document(doc_path: str) -> Dict[str, Any]:
    """
    Process a document and extract metadata.

    Args:
        doc_path: Path to document file

    Returns:
        Dictionary containing extracted metadata

    Raises:
        FileNotFoundError: If document doesn't exist
        ValueError: If document format is invalid
    """
    if not os.path.exists(doc_path):
        raise FileNotFoundError(f"Document not found: {doc_path}")

    try:
        with open(doc_path, 'r') as f:
            content = f.read()

        metadata = extract_metadata(content)
        return metadata

    except Exception as e:
        raise ValueError(f"Failed to process document: {e}")
'''

spec = """
Create a function that validates a document before processing.
It should:
- Check if file exists
- Validate file extension (.txt, .md, .pdf)
- Check file size (max 10MB)
- Return validation result with error messages if any
"""

new_function = generate_function(existing_code, spec, "python")
print(new_function)
```

### Advanced: Multi-File Code Generation with Extended Thinking

**Goal**: Generate complex features spanning multiple files with architectural reasoning

```python
def generate_feature(
    codebase_structure: Dict,
    existing_files: Dict[str, str],
    feature_spec: str
):
    """
    Generate a complete feature with multiple files using extended thinking.

    Args:
        codebase_structure: Project structure (directories, key files)
        existing_files: Content of relevant existing files
        feature_spec: Detailed feature requirements

    Returns:
        Dictionary mapping file paths to generated code
    """
    # Prepare context
    structure_text = json.dumps(codebase_structure, indent=2)
    files_text = "\n\n".join([
        f"File: {path}\n```\n{content}\n```"
        for path, content in existing_files.items()
    ])

    prompt = f"""Project Structure:
{structure_text}

Existing Files:
{files_text}

Feature to Implement:
{feature_spec}

Using extended thinking, analyze:
1. Which files need to be created/modified
2. How this feature integrates with existing architecture
3. What patterns to follow from existing code
4. Potential edge cases and error scenarios
5. Testing strategy

Then generate:
- All new files needed
- Modifications to existing files
- Explanation of design decisions

Return as JSON:
{{
  "reasoning": "your architectural thinking",
  "files_to_create": {{"path": "code", ...}},
  "files_to_modify": {{"path": "changes", ...}},
  "tests_to_create": {{"path": "test code", ...}},
  "documentation": "feature documentation"
}}
"""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=16000,
        thinking={
            "type": "enabled",
            "budget_tokens": 8000
        },
        messages=[{"role": "user", "content": prompt}]
    )

    # Extract thinking and answer
    thinking_content = ""
    answer_content = ""

    for block in response.content:
        if block.type == "thinking":
            thinking_content = block.thinking
        elif block.type == "text":
            answer_content = block.text

    # Parse JSON response
    import json
    if "```json" in answer_content:
        answer_content = answer_content.split("```json")[1].split("```")[0]

    result = json.loads(answer_content.strip())
    result["architectural_reasoning"] = thinking_content

    return result
```

---

## Codebase Analysis & Understanding

### Rapid Codebase Understanding

**Goal**: Quickly understand unfamiliar codebase structure and patterns

```python
def analyze_codebase(
    file_paths: List[str],
    focus_areas: List[str] = None
):
    """
    Analyze codebase and generate comprehensive understanding report.

    Args:
        file_paths: List of file paths to analyze
        focus_areas: Optional specific areas to focus on
                    (e.g., ['architecture', 'data_flow', 'patterns'])

    Returns:
        Analysis report with key insights
    """
    if focus_areas is None:
        focus_areas = [
            'architecture',
            'key_components',
            'data_flow',
            'design_patterns',
            'dependencies',
            'potential_issues'
        ]

    # Read files
    files_content = {}
    for path in file_paths:
        with open(path, 'r') as f:
            files_content[path] = f.read()

    # Prepare context
    code_blocks = "\n\n".join([
        f"File: {path}\n```\n{content[:2000]}...\n```"  # First 2000 chars
        for path, content in files_content.items()
    ])

    prompt = f"""Analyze this codebase focusing on: {', '.join(focus_areas)}

Code Files:
{code_blocks}

Provide:
1. **Architecture Overview**: High-level structure and organization
2. **Key Components**: Main classes, functions, modules and their purposes
3. **Data Flow**: How data moves through the system
4. **Design Patterns**: Patterns used (MVC, Factory, Observer, etc.)
5. **Dependencies**: External libraries and internal dependencies
6. **Code Quality**: Strengths and potential improvements
7. **Entry Points**: Where to start reading the code
8. **Recommendations**: Suggestions for navigation and understanding

Format as structured markdown.
"""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=8192,
        thinking={
            "type": "enabled",
            "budget_tokens": 4000
        },
        messages=[{"role": "user", "content": prompt}]
    )

    # Extract answer
    answer_content = ""
    for block in response.content:
        if block.type == "text":
            answer_content = block.text

    return answer_content


# Example usage
codebase_files = [
    "src/main.py",
    "src/database.py",
    "src/api_routes.py",
    "src/models.py"
]

analysis = analyze_codebase(
    codebase_files,
    focus_areas=['architecture', 'data_flow', 'potential_issues']
)

print(analysis)
```

### Dependency Analysis with Prompt Caching

**Goal**: Cache codebase structure for fast dependency queries

```python
def setup_codebase_cache(codebase_files: Dict[str, str]) -> str:
    """
    Create cached representation of codebase structure.

    Args:
        codebase_files: Dictionary of file_path -> content

    Returns:
        Formatted codebase context for caching
    """
    context_parts = ["# Codebase Structure\n"]

    for path, content in codebase_files.items():
        context_parts.append(f"\n## File: {path}\n")
        context_parts.append(f"```\n{content}\n```\n")

    return "\n".join(context_parts)


def query_dependencies(
    codebase_context: str,
    query: str,
    conversation_history: List = None
):
    """
    Query codebase dependencies using cached context.

    Args:
        codebase_context: Cached codebase structure
        query: Dependency question
        conversation_history: Previous conversation for follow-ups

    Returns:
        Answer about dependencies
    """
    if conversation_history is None:
        conversation_history = []

    conversation_history.append({
        "role": "user",
        "content": query
    })

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2048,
        system=[{
            "type": "text",
            "text": codebase_context,
            "cache_control": {"type": "ephemeral"}
        }],
        messages=conversation_history
    )

    answer = response.content[0].text
    conversation_history.append({
        "role": "assistant",
        "content": answer
    })

    return answer, conversation_history


# Usage Example
codebase_files = {
    "main.py": open("src/main.py").read(),
    "utils.py": open("src/utils.py").read(),
    "api.py": open("src/api.py").read()
}

# Cache codebase (first request creates cache)
codebase_ctx = setup_codebase_cache(codebase_files)

# Query 1: ~$0.02 (cache creation)
answer1, history = query_dependencies(
    codebase_ctx,
    "What modules does main.py depend on?"
)

# Query 2: ~$0.002 (cache hit, 90% savings)
answer2, history = query_dependencies(
    codebase_ctx,
    "Which functions in utils.py are used by api.py?",
    history
)

# Query 3: ~$0.002 (cache hit)
answer3, history = query_dependencies(
    codebase_ctx,
    "What would break if I removed the process_data function from utils.py?",
    history
)
```

---

## Intelligent Refactoring

### Safe Refactoring with Verification

**Goal**: Refactor code while ensuring functionality is preserved

```python
def refactor_code(
    original_code: str,
    refactoring_goal: str,
    language: str = "python"
):
    """
    Refactor code with safety verification.

    Args:
        original_code: Code to refactor
        refactoring_goal: What to improve (readability, performance, etc.)
        language: Programming language

    Returns:
        Refactored code with explanation and verification tests
    """
    prompt = f"""Refactor this {language} code to {refactoring_goal}.

Original Code:
```{language}
{original_code}
```

Provide:
1. **Refactored Code**: Improved version
2. **Changes Made**: List of specific changes
3. **Rationale**: Why each change improves the code
4. **Verification Tests**: Tests to ensure functionality is preserved
5. **Potential Risks**: Any edge cases to watch for

Requirements:
- Preserve all functionality
- Maintain or improve performance
- Follow language best practices
- Add comments explaining complex changes
"""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=8192,
        thinking={
            "type": "enabled",
            "budget_tokens": 3000
        },
        messages=[{"role": "user", "content": prompt}]
    )

    # Extract answer
    answer_content = ""
    for block in response.content:
        if block.type == "text":
            answer_content = block.text

    return answer_content


# Example usage
old_code = '''
def process_items(items):
    results = []
    for item in items:
        if item is not None:
            if item > 0:
                results.append(item * 2)
    return results
'''

refactored = refactor_code(
    old_code,
    "improve readability and add type hints",
    "python"
)

print(refactored)
```

### Batch Refactoring Across Multiple Files

**Goal**: Refactor entire codebase systematically with 50% cost savings

```python
def batch_refactor_files(
    files_to_refactor: Dict[str, str],
    refactoring_rules: List[str],
    coding_standards: str
):
    """
    Refactor multiple files in batch with consistent rules.

    Args:
        files_to_refactor: Dictionary of file_path -> current_code
        refactoring_rules: List of refactoring goals
        coding_standards: Project coding standards document

    Returns:
        Batch results with refactored code for each file
    """
    # Create batch requests
    batch_requests = []

    for file_path, code_content in files_to_refactor.items():
        rules_text = "\n".join([f"- {rule}" for rule in refactoring_rules])

        batch_requests.append({
            "custom_id": f"refactor-{file_path}",
            "params": {
                "model": "claude-sonnet-4-5-20250929",
                "max_tokens": 8192,
                "system": [{
                    "type": "text",
                    "text": f"Coding Standards:\n{coding_standards}",
                    "cache_control": {"type": "ephemeral"}
                }],
                "messages": [{
                    "role": "user",
                    "content": f"""Refactor this code following these rules:
{rules_text}

File: {file_path}
```
{code_content}
```

Return refactored code with explanation of changes.
"""
                }]
            }
        })

    # Submit batch
    message_batch = client.messages.batches.create(requests=batch_requests)

    # Poll for completion
    import time
    while True:
        batch_status = client.messages.batches.retrieve(message_batch.id)
        if batch_status.processing_status == "ended":
            break
        time.sleep(10)

    # Retrieve results
    refactored_files = {}
    for result in client.messages.batches.results(message_batch.id):
        if result.result.type == "succeeded":
            file_path = result.custom_id.replace("refactor-", "")
            refactored_content = result.result.message.content[0].text

            refactored_files[file_path] = refactored_content

    return refactored_files


# Example usage
files = {
    "utils/helpers.py": open("utils/helpers.py").read(),
    "utils/validators.py": open("utils/validators.py").read(),
    "utils/formatters.py": open("utils/formatters.py").read()
}

rules = [
    "Add type hints to all functions",
    "Improve variable naming for clarity",
    "Add docstrings following Google style",
    "Extract magic numbers into named constants",
    "Simplify complex conditionals"
]

standards = open("docs/CODING_STANDARDS.md").read()

# Cost: ~50% savings vs individual API calls
refactored = batch_refactor_files(files, rules, standards)
```

---

## Test Generation & Validation

### Comprehensive Test Suite Generation

**Goal**: Generate unit, integration, and edge-case tests automatically

```python
def generate_test_suite(
    code_to_test: str,
    test_framework: str = "pytest",
    coverage_target: int = 90
):
    """
    Generate comprehensive test suite for given code.

    Args:
        code_to_test: Source code to generate tests for
        test_framework: Testing framework (pytest, unittest, jest, etc.)
        coverage_target: Target code coverage percentage

    Returns:
        Complete test suite code
    """
    prompt = f"""Generate a comprehensive {test_framework} test suite for this code:

```python
{code_to_test}
```

Requirements:
1. **Unit Tests**: Test each function/method individually
2. **Edge Cases**: Test boundary conditions, empty inputs, None values
3. **Error Cases**: Test exception handling and invalid inputs
4. **Integration Tests**: Test functions working together
5. **Coverage**: Aim for {coverage_target}% code coverage
6. **Test Data**: Include diverse test cases with fixtures
7. **Assertions**: Use descriptive assertion messages

Structure:
- Group related tests in classes
- Use descriptive test names (test_feature_scenario_expectedResult)
- Add docstrings explaining what each test validates
- Include setup/teardown if needed
- Add parametrized tests for multiple inputs

Return complete, runnable test file.
"""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=8192,
        thinking={
            "type": "enabled",
            "budget_tokens": 4000
        },
        messages=[{"role": "user", "content": prompt}]
    )

    # Extract test code
    answer_content = ""
    for block in response.content:
        if block.type == "text":
            answer_content = block.text

    return answer_content


# Example usage
code = '''
def calculate_discount(price: float, discount_percent: float) -> float:
    """Calculate discounted price."""
    if price < 0:
        raise ValueError("Price cannot be negative")
    if discount_percent < 0 or discount_percent > 100:
        raise ValueError("Discount must be between 0 and 100")

    discount_amount = price * (discount_percent / 100)
    return price - discount_amount
'''

test_suite = generate_test_suite(code, "pytest", coverage_target=95)
print(test_suite)
```

### Test-Driven Development (TDD) Assistant

**Goal**: Generate tests first, then implementation

```python
def tdd_workflow(
    function_spec: str,
    examples: List[Dict],
    language: str = "python"
):
    """
    Follow TDD workflow: Generate tests first, then implementation.

    Args:
        function_spec: Description of function to build
        examples: List of input/output examples
        language: Programming language

    Returns:
        Dictionary with tests and implementation
    """
    # Step 1: Generate tests based on specification
    examples_text = "\n".join([
        f"- Input: {ex['input']} → Output: {ex['output']}"
        for ex in examples
    ])

    test_prompt = f"""Following TDD, write tests FIRST for a function that:
{function_spec}

Examples:
{examples_text}

Generate comprehensive {language} tests that would validate:
1. Basic functionality with provided examples
2. Edge cases (empty input, None, large values)
3. Error cases (invalid input types)
4. Boundary conditions

Return test code that will initially FAIL (Red phase of TDD).
"""

    test_response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4096,
        messages=[{"role": "user", "content": test_prompt}]
    )

    tests = test_response.content[0].text

    # Step 2: Generate implementation to pass tests
    impl_prompt = f"""Now write the IMPLEMENTATION to pass these tests:

Tests:
{tests}

Requirements:
- Make all tests pass
- Follow best practices
- Include proper error handling
- Add type hints and docstring
"""

    impl_response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4096,
        messages=[{"role": "user", "content": impl_prompt}]
    )

    implementation = impl_response.content[0].text

    return {
        "tests": tests,
        "implementation": implementation,
        "workflow": "TDD: Red → Green → Refactor"
    }


# Example usage
spec = "Create a function that validates email addresses"
examples = [
    {"input": "user@example.com", "output": True},
    {"input": "invalid-email", "output": False},
    {"input": "user@domain.co.uk", "output": True}
]

tdd_result = tdd_workflow(spec, examples)
print("Tests (Red phase):")
print(tdd_result["tests"])
print("\nImplementation (Green phase):")
print(tdd_result["implementation"])
```

---

## Documentation Generation

### Living Documentation from Code

**Goal**: Generate and maintain documentation that stays synchronized with code

```python
def generate_documentation(
    code_files: Dict[str, str],
    doc_type: str = "api",
    format: str = "markdown"
):
    """
    Generate comprehensive documentation from code.

    Args:
        code_files: Dictionary of file_path -> code_content
        doc_type: Type of documentation (api, user_guide, architecture)
        format: Output format (markdown, rst, html)

    Returns:
        Generated documentation
    """
    code_context = "\n\n".join([
        f"File: {path}\n```\n{content}\n```"
        for path, content in code_files.items()
    ])

    prompts = {
        "api": """Generate API documentation including:
- Overview and purpose
- Installation instructions
- API reference for all public functions/classes
- Parameter descriptions with types
- Return value descriptions
- Usage examples for each function
- Error handling guide
""",
        "user_guide": """Generate user guide including:
- Getting started tutorial
- Common use cases with examples
- Configuration options
- Troubleshooting guide
- FAQ section
- Best practices
""",
        "architecture": """Generate architecture documentation including:
- System overview diagram (described in text)
- Component descriptions
- Data flow diagrams (described in text)
- Design decisions and rationale
- Extension points
- Performance considerations
"""
    }

    prompt = f"""{prompts.get(doc_type, prompts['api'])}

Code:
{code_context}

Format the documentation as {format}.
Make it comprehensive but readable.
Include code examples where helpful.
"""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=16000,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text


# Example usage
files = {
    "api/routes.py": open("api/routes.py").read(),
    "api/models.py": open("api/models.py").read()
}

api_docs = generate_documentation(files, doc_type="api", format="markdown")
with open("docs/API.md", "w") as f:
    f.write(api_docs)
```

### Inline Documentation Improvement

**Goal**: Add/improve inline comments and docstrings

```python
def improve_inline_docs(
    code: str,
    language: str = "python",
    doc_style: str = "google"
):
    """
    Add comprehensive inline documentation to code.

    Args:
        code: Source code to document
        language: Programming language
        doc_style: Docstring style (google, numpy, sphinx)

    Returns:
        Code with improved documentation
    """
    prompt = f"""Add comprehensive inline documentation to this code:

```{language}
{code}
```

Requirements:
1. Add {doc_style}-style docstrings to all functions/classes
2. Add inline comments explaining complex logic
3. Document parameters, return values, exceptions
4. Add module-level docstring if missing
5. Include usage examples in docstrings
6. Explain WHY not just WHAT (especially for non-obvious code)

Maintain all existing functionality.
Return the fully documented code.
"""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text
```

---

## Error Handling & Debugging

### Intelligent Error Detection

**Goal**: Proactively identify potential bugs and error scenarios

```python
def analyze_for_errors(
    code: str,
    language: str = "python",
    context: str = ""
):
    """
    Analyze code for potential errors and bugs.

    Args:
        code: Code to analyze
        language: Programming language
        context: Additional context about how code is used

    Returns:
        Detailed error analysis report
    """
    prompt = f"""Analyze this {language} code for potential errors and bugs:

```{language}
{code}
```

Context: {context}

Identify:
1. **Syntax Errors**: Any language syntax issues
2. **Logic Errors**: Incorrect logic or algorithms
3. **Runtime Errors**: Potential exceptions or crashes
4. **Edge Cases**: Unhandled edge cases
5. **Resource Leaks**: Memory/file/connection leaks
6. **Security Issues**: SQL injection, XSS, path traversal, etc.
7. **Performance Issues**: Inefficient algorithms or operations
8. **Type Errors**: Type mismatches or casting issues

For each issue:
- Severity: Critical/High/Medium/Low
- Location: Line number or code section
- Explanation: What the problem is
- Fix: Suggested correction
- Example: How the error could manifest

Format as structured report.
"""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=8192,
        thinking={
            "type": "enabled",
            "budget_tokens": 4000
        },
        messages=[{"role": "user", "content": prompt}]
    )

    # Extract answer
    answer_content = ""
    for block in response.content:
        if block.type == "text":
            answer_content = block.text

    return answer_content


# Example usage
buggy_code = '''
def divide_numbers(a, b):
    return a / b

def process_list(items):
    total = 0
    for i in range(len(items)):
        total += items[i + 1]
    return total

def read_file(filename):
    f = open(filename, 'r')
    data = f.read()
    return data
'''

error_report = analyze_for_errors(
    buggy_code,
    context="Used in production API for financial calculations"
)

print(error_report)
```

### Automated Debugging Assistant

**Goal**: Debug errors using extended thinking

```python
def debug_error(
    code: str,
    error_message: str,
    stack_trace: str = "",
    context: str = ""
):
    """
    Debug an error using extended thinking to analyze root cause.

    Args:
        code: Code that produced the error
        error_message: Error message text
        stack_trace: Full stack trace if available
        context: Additional context (inputs, environment)

    Returns:
        Debug analysis with root cause and fix
    """
    prompt = f"""Debug this error using systematic reasoning:

Code:
```
{code}
```

Error Message:
{error_message}

Stack Trace:
{stack_trace}

Context:
{context}

Analyze:
1. **Root Cause**: What is the underlying problem?
2. **Why It Happened**: What conditions led to this error?
3. **Reproduce Steps**: How to reliably reproduce the error
4. **Fix**: Corrected code that resolves the issue
5. **Prevention**: How to prevent similar errors in future
6. **Testing**: Tests to verify the fix works

Think through the debugging process step by step.
"""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=8192,
        thinking={
            "type": "enabled",
            "budget_tokens": 5000
        },
        messages=[{"role": "user", "content": prompt}]
    )

    # Extract thinking and answer
    thinking_content = ""
    answer_content = ""

    for block in response.content:
        if block.type == "thinking":
            thinking_content = block.thinking
        elif block.type == "text":
            answer_content = block.text

    return {
        "reasoning": thinking_content,
        "solution": answer_content
    }
```

---

## Performance Optimization

### Code Performance Analysis

**Goal**: Identify performance bottlenecks and optimization opportunities

```python
def optimize_performance(
    code: str,
    performance_goals: str,
    language: str = "python"
):
    """
    Analyze code and suggest performance optimizations.

    Args:
        code: Code to optimize
        performance_goals: Target (e.g., "reduce time complexity", "minimize memory")
        language: Programming language

    Returns:
        Optimized code with performance analysis
    """
    prompt = f"""Optimize this {language} code for: {performance_goals}

Original Code:
```{language}
{code}
```

Provide:
1. **Performance Analysis**:
   - Time complexity (Big O)
   - Space complexity
   - Bottlenecks identified

2. **Optimized Code**:
   - Improved implementation
   - Complexity after optimization

3. **Optimization Techniques Used**:
   - List each optimization
   - Explain why it helps

4. **Benchmarks**:
   - Expected performance improvement
   - Trade-offs made

5. **Alternative Approaches**:
   - Other optimization strategies considered
   - Why chosen approach is best
"""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=8192,
        thinking={
            "type": "enabled",
            "budget_tokens": 4000
        },
        messages=[{"role": "user", "content": prompt}]
    )

    # Extract answer
    answer_content = ""
    for block in response.content:
        if block.type == "text":
            answer_content = block.text

    return answer_content


# Example usage
slow_code = '''
def find_duplicates(items):
    duplicates = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if items[i] == items[j] and items[i] not in duplicates:
                duplicates.append(items[i])
    return duplicates
'''

optimized = optimize_performance(
    slow_code,
    performance_goals="reduce time complexity from O(n²) to O(n)",
    language="python"
)

print(optimized)
```

---

## Code Review Automation

### Automated Code Review

**Goal**: Perform comprehensive code review automatically

```python
def automated_code_review(
    code_diff: str,
    coding_standards: str,
    review_checklist: List[str]
):
    """
    Perform automated code review against standards and checklist.

    Args:
        code_diff: Git diff or changed code
        coding_standards: Project coding standards document
        review_checklist: List of review criteria

    Returns:
        Code review report with feedback
    """
    checklist_text = "\n".join([f"- {item}" for item in review_checklist])

    prompt = f"""Perform a code review on this change:

Code Diff:
```
{code_diff}
```

Coding Standards:
{coding_standards}

Review Checklist:
{checklist_text}

Provide structured review:

1. **Summary**: Overall assessment (Approve/Request Changes/Comment)

2. **Strengths**: What's done well

3. **Issues Found**:
   - Severity (Critical/Major/Minor)
   - Location (line/function)
   - Description
   - Suggested fix

4. **Suggestions**:
   - Performance improvements
   - Readability enhancements
   - Best practice recommendations

5. **Security Review**:
   - Potential vulnerabilities
   - Security best practices

6. **Test Coverage**:
   - Are tests included?
   - Test quality assessment

Format as GitHub-style review comments.
"""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=8192,
        thinking={
            "type": "enabled",
            "budget_tokens": 3000
        },
        messages=[{"role": "user", "content": prompt}]
    )

    # Extract answer
    answer_content = ""
    for block in response.content:
        if block.type == "text":
            answer_content = block.text

    return answer_content


# Example usage
diff = '''
+ def process_user_data(user_input):
+     query = f"SELECT * FROM users WHERE name = '{user_input}'"
+     result = db.execute(query)
+     return result
'''

standards = open("CODING_STANDARDS.md").read()
checklist = [
    "No hardcoded credentials",
    "SQL injection prevention",
    "Input validation",
    "Error handling",
    "Type hints present",
    "Docstring included"
]

review = automated_code_review(diff, standards, checklist)
print(review)
```

---

## Migration & Modernization

### Legacy Code Migration

**Goal**: Migrate legacy code to modern frameworks/languages

```python
def migrate_code(
    legacy_code: str,
    source_language: str,
    target_language: str,
    target_framework: str = None
):
    """
    Migrate code from legacy to modern language/framework.

    Args:
        legacy_code: Original code to migrate
        source_language: Current language
        target_language: Target language
        target_framework: Optional target framework

    Returns:
        Migrated code with migration notes
    """
    framework_text = f" using {target_framework} framework" if target_framework else ""

    prompt = f"""Migrate this {source_language} code to {target_language}{framework_text}:

Legacy Code:
```{source_language}
{legacy_code}
```

Provide:
1. **Migrated Code**: Complete {target_language} version
2. **Migration Notes**:
   - Key changes made
   - Language/framework differences handled
   - Modern patterns adopted
3. **Functionality Mapping**: How each part translates
4. **Potential Issues**: Things to watch for
5. **Testing Strategy**: How to verify migration
6. **Dependencies**: Libraries needed in {target_language}

Ensure:
- All functionality preserved
- Modern best practices followed
- Idiomatic {target_language} code
- Proper error handling
"""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=16000,
        thinking={
            "type": "enabled",
            "budget_tokens": 6000
        },
        messages=[{"role": "user", "content": prompt}]
    )

    # Extract answer
    answer_content = ""
    for block in response.content:
        if block.type == "text":
            answer_content = block.text

    return answer_content


# Example: Python 2 to Python 3
legacy = '''
import urllib2

def fetch_data(url):
    response = urllib2.urlopen(url)
    data = response.read()
    print "Fetched %d bytes" % len(data)
    return data
'''

migrated = migrate_code(
    legacy,
    source_language="Python 2",
    target_language="Python 3",
    target_framework="requests library"
)

print(migrated)
```

---

## Production Patterns

### Complete Production Pipeline

```python
class CodeEnhancementPipeline:
    """
    Production pipeline combining all enhanced coding patterns.
    Uses: Caching + Thinking + Batch + Tool Use
    """

    def __init__(self, anthropic_api_key: str, coding_standards: str):
        self.client = anthropic.Anthropic(api_key=anthropic_api_key)
        self.coding_standards = coding_standards

    def process_codebase(
        self,
        files: Dict[str, str],
        tasks: List[str]
    ):
        """
        Process entire codebase with multiple enhancement tasks.

        Args:
            files: Dictionary of file_path -> code_content
            tasks: List of tasks (analyze, refactor, test, document, review)

        Returns:
            Comprehensive results for all tasks
        """
        results = {}

        # Cache codebase structure
        codebase_context = self._create_codebase_context(files)

        for task in tasks:
            if task == "analyze":
                results["analysis"] = self._analyze_cached(codebase_context)
            elif task == "refactor":
                results["refactored"] = self._refactor_batch(files)
            elif task == "test":
                results["tests"] = self._generate_tests_batch(files)
            elif task == "document":
                results["docs"] = self._generate_docs(files)
            elif task == "review":
                results["review"] = self._review_cached(codebase_context, files)

        return results

    def _create_codebase_context(self, files: Dict[str, str]) -> str:
        """Create cached codebase context."""
        context_parts = [f"# Codebase Context\n\n## Coding Standards\n{self.coding_standards}\n"]

        for path, content in files.items():
            context_parts.append(f"\n## File: {path}\n```\n{content[:1000]}...\n```")

        return "\n".join(context_parts)

    def _analyze_cached(self, codebase_context: str) -> str:
        """Analyze codebase using cached context."""
        response = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=8192,
            system=[{
                "type": "text",
                "text": codebase_context,
                "cache_control": {"type": "ephemeral"}
            }],
            thinking={
                "type": "enabled",
                "budget_tokens": 4000
            },
            messages=[{
                "role": "user",
                "content": "Analyze this codebase: architecture, patterns, quality, issues."
            }]
        )

        answer = ""
        for block in response.content:
            if block.type == "text":
                answer = block.text

        return answer

    def _refactor_batch(self, files: Dict[str, str]) -> Dict[str, str]:
        """Refactor files in batch (50% cost savings)."""
        batch_requests = []

        for path, content in files.items():
            batch_requests.append({
                "custom_id": f"refactor-{path}",
                "params": {
                    "model": "claude-sonnet-4-5-20250929",
                    "max_tokens": 8192,
                    "system": [{
                        "type": "text",
                        "text": f"Coding Standards:\n{self.coding_standards}",
                        "cache_control": {"type": "ephemeral"}
                    }],
                    "messages": [{
                        "role": "user",
                        "content": f"Refactor this code following standards:\n\n```\n{content}\n```"
                    }]
                }
            })

        # Submit and retrieve batch
        message_batch = self.client.messages.batches.create(requests=batch_requests)

        # Poll for completion
        import time
        while True:
            batch_status = self.client.messages.batches.retrieve(message_batch.id)
            if batch_status.processing_status == "ended":
                break
            time.sleep(10)

        # Collect results
        refactored = {}
        for result in self.client.messages.batches.results(message_batch.id):
            if result.result.type == "succeeded":
                path = result.custom_id.replace("refactor-", "")
                refactored[path] = result.result.message.content[0].text

        return refactored

    def _generate_tests_batch(self, files: Dict[str, str]) -> Dict[str, str]:
        """Generate tests for files in batch."""
        # Similar to refactor_batch but for test generation
        batch_requests = []

        for path, content in files.items():
            batch_requests.append({
                "custom_id": f"test-{path}",
                "params": {
                    "model": "claude-sonnet-4-5-20250929",
                    "max_tokens": 8192,
                    "messages": [{
                        "role": "user",
                        "content": f"Generate comprehensive pytest tests:\n\n```\n{content}\n```"
                    }]
                }
            })

        message_batch = self.client.messages.batches.create(requests=batch_requests)

        import time
        while True:
            batch_status = self.client.messages.batches.retrieve(message_batch.id)
            if batch_status.processing_status == "ended":
                break
            time.sleep(10)

        tests = {}
        for result in self.client.messages.batches.results(message_batch.id):
            if result.result.type == "succeeded":
                path = result.custom_id.replace("test-", "")
                tests[f"test_{path}"] = result.result.message.content[0].text

        return tests

    def _generate_docs(self, files: Dict[str, str]) -> str:
        """Generate documentation from code."""
        code_context = "\n\n".join([
            f"File: {path}\n```\n{content}\n```"
            for path, content in files.items()
        ])

        response = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=16000,
            messages=[{
                "role": "user",
                "content": f"Generate API documentation:\n\n{code_context}"
            }]
        )

        return response.content[0].text

    def _review_cached(self, codebase_context: str, files: Dict[str, str]) -> Dict[str, str]:
        """Review files using cached context."""
        reviews = {}

        for path, content in files.items():
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=4096,
                system=[{
                    "type": "text",
                    "text": codebase_context,
                    "cache_control": {"type": "ephemeral"}
                }],
                messages=[{
                    "role": "user",
                    "content": f"Review this file for issues:\n\n```\n{content}\n```"
                }]
            )

            reviews[path] = response.content[0].text

        return reviews


# Usage Example
pipeline = CodeEnhancementPipeline(
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
    coding_standards=open("CODING_STANDARDS.md").read()
)

files = {
    "api/routes.py": open("api/routes.py").read(),
    "api/models.py": open("api/models.py").read(),
    "utils/helpers.py": open("utils/helpers.py").read()
}

results = pipeline.process_codebase(
    files=files,
    tasks=["analyze", "refactor", "test", "document", "review"]
)

# Results contain all enhancements
print(f"Analysis: {results['analysis'][:200]}...")
print(f"Refactored {len(results['refactored'])} files")
print(f"Generated {len(results['tests'])} test files")
print(f"Documentation: {len(results['docs'])} chars")
print(f"Reviews: {len(results['review'])} files reviewed")
```

---

## Cost Optimization

### Cost Breakdown for Enhanced Coding

**Typical Costs** (Claude Sonnet 4.5):

| Task | Input Tokens | Output Tokens | Cost per File |
|------|--------------|---------------|---------------|
| Code Analysis | 2,000 | 1,000 | $0.021 |
| Refactoring | 1,500 | 2,000 | $0.035 |
| Test Generation | 1,000 | 3,000 | $0.048 |
| Documentation | 2,000 | 4,000 | $0.066 |
| Code Review | 1,500 | 1,500 | $0.027 |
| **Total per File** | | | **$0.197** |

### Optimization Strategies

**1. Prompt Caching for Standards (85-90% savings)**
```python
# Cache coding standards across all operations
system=[{
    "type": "text",
    "text": coding_standards_text,  # Reused for all files
    "cache_control": {"type": "ephemeral"}
}]

# Cost reduction:
# - First file: $0.197
# - Subsequent files: ~$0.020 (90% savings)
```

**2. Batch Processing (50% savings)**
```python
# Process 50 files in batch
batch_requests = [create_request(file) for file in files]
batch = client.messages.batches.create(requests=batch_requests)

# Cost reduction:
# - Standard API: $9.85 for 50 files
# - Batch API: $4.93 for 50 files (50% savings)
```

**3. Combined: Caching + Batch (92-95% savings)**
```python
# Batch with cached standards
# - Standard: $9.85 for 50 files
# - Optimized: ~$0.50 for 50 files (95% savings!)
```

### Real-World Cost Example

**Scenario**: Enhance 100-file codebase (analyze, refactor, test, document, review)

| Strategy | Cost | Time | Notes |
|----------|------|------|-------|
| Standard API (no optimization) | $19.70 | ~45 min | Individual requests |
| Prompt Caching only | $2.00 | ~45 min | 90% savings |
| Batch Processing only | $9.85 | 24 hours | 50% savings |
| **Caching + Batch** | **$1.00** | **24 hours** | **95% savings** |

---

## Troubleshooting

### Common Issues

**Issue: Generated code doesn't match project style**
- **Solution**: Include style guide in cached system prompt
- **Example**: Cache coding standards + sample files

**Issue: Tests don't cover edge cases**
- **Solution**: Use extended thinking + explicit edge case prompts
- **Budget**: 3000-5000 thinking tokens for comprehensive coverage

**Issue: Documentation is too generic**
- **Solution**: Provide project context + user personas in prompt

**Issue: Refactoring breaks functionality**
- **Solution**: Request verification tests with refactoring
- **Pattern**: Refactor → Generate tests → Validate

**Issue: Performance optimizations don't help**
- **Solution**: Include profiling data in prompt
- **Context**: "Function takes 2.5s, most time in database query"

---

## Real-World Use Cases

### Use Case 1: Microservice Scaffolding

```python
# Generate complete microservice from specification
spec = {
    "service_name": "user-auth-service",
    "endpoints": ["/login", "/register", "/refresh"],
    "database": "PostgreSQL",
    "framework": "FastAPI",
    "auth": "JWT"
}

service_code = generate_feature(
    codebase_structure={},
    existing_files={},
    feature_spec=json.dumps(spec)
)

# Result: Complete service with routes, models, tests, docs
```

### Use Case 2: Legacy System Modernization

```python
# Migrate PHP 5 to Python FastAPI
legacy_php = open("legacy/api.php").read()

modern_python = migrate_code(
    legacy_php,
    source_language="PHP 5",
    target_language="Python 3",
    target_framework="FastAPI"
)
```

### Use Case 3: Test Coverage Sprint

```python
# Generate tests for untested codebase
untested_files = glob.glob("src/**/*.py")

for file_path in untested_files:
    code = open(file_path).read()
    tests = generate_test_suite(code, coverage_target=90)

    test_path = file_path.replace("src/", "tests/test_")
    with open(test_path, "w") as f:
        f.write(tests)

# Result: 90%+ test coverage in hours
```

---

## Summary

### Key Takeaways

1. **Context is King**: Cache codebase structure for consistency
2. **Think Before Acting**: Use extended thinking for complex tasks
3. **Batch for Scale**: Process multiple files with 50% savings
4. **Test Everything**: Generate comprehensive test suites automatically
5. **Document as You Go**: Keep documentation synchronized with code

### Cost-Optimized Workflow

```
Cache Standards → Analyze Codebase → Batch Refactor/Test/Document →
Review Changes → Deploy
```

**Expected Costs** (100 files):
- Without optimization: $19.70
- With optimization: $1.00 (95% savings)

### Next Steps

1. Set up coding standards document for caching
2. Implement ProductionCodePipeline for your codebase
3. Start with analysis to understand current state
4. Apply refactoring in batches with verification tests
5. Generate documentation and review changes
6. Deploy enhanced codebase with confidence

---

## Additional Resources

**Related Playbooks**:
- Playbook 1: Cost Optimization (caching, batch)
- Playbook 2: Extended Thinking (complex reasoning)
- Playbook 3: Agent Development (coding agents)
- Playbook 4: Knowledge Engineering (codebase as KG)

**Tools**:
- Claude Code CLI for IDE integration
- pytest for Python testing
- Jest for JavaScript testing
- Sphinx/MkDocs for documentation

**Official Examples**:
- All Week 1-2 examples in `/claude-cookbook-kg/`
- Extended thinking examples for complex refactoring
- Batch API examples for parallel processing

---

**Playbook Version**: 1.0
**Last Updated**: November 8, 2025
**Maintained By**: NLKE Project
**Feedback**: Submit issues or suggestions to project repository

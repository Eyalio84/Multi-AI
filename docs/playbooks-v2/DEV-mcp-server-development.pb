# Playbook 10: MCP Server Development
## Building Model Context Protocol Servers for Claude Code Integration

**Version:** 1.0
**Last Updated:** November 27, 2025
**Audience:** Developers building MCP servers, Claude Code integrators, tool builders
**Prerequisites:** Python 3.8+, understanding of JSON-RPC, basic async programming
**Related Playbooks:** Playbook 3 (Agent Development), Playbook 8 (Continuous Learning Loop)

---

## Table of Contents

1. [Overview](#overview)
2. [MCP Architecture](#mcp-architecture)
3. [Our 4 Servers as Case Studies](#our-4-servers-as-case-studies)
4. [Building Your First Server](#building-your-first-server)
5. [Tool Design Patterns](#tool-design-patterns)
6. [Testing and Validation](#testing-and-validation)
7. [Integration with Claude Code](#integration-with-claude-code)
8. [Cost Optimization](#cost-optimization)
9. [Troubleshooting](#troubleshooting)
10. [Real-World Examples](#real-world-examples)

---

## Overview

### What is MCP?

**Model Context Protocol (MCP)** is a standardized interface for connecting AI models to external tools and data sources. It defines:

- **Tools**: Functions the model can call
- **Resources**: Data the model can read
- **Prompts**: Pre-built prompt templates

### Why Build MCP Servers?

| Without MCP | With MCP |
|-------------|----------|
| Model has no persistent state | Tools can access databases, files |
| Limited to conversation context | Access to external knowledge |
| Can't execute actions | Can run code, query APIs |
| Generic capabilities | Domain-specific expertise |

### Our Implementation

We built **4 MCP servers with 63 tools**:

| Server | Tools | Purpose | Cost |
|--------|-------|---------|------|
| nlke-intent | 14 | Structure-based KG queries | $0 (local) |
| nlke-ml | 5 | Embedding-based semantic search | $0 (local) |
| nlke-unified | 9 | Cross-domain unified queries | $0 (local) |
| nlke-metacog | 35 | Critical thinking & persistence | $0 (local) |

**Total: 63 tools, $0 API cost per query**

---

## MCP Architecture

### The Protocol Stack

```
┌─────────────────────────────────────────────────────────────┐
│                     CLAUDE CODE                              │
│              (MCP Client / Host)                             │
└─────────────────────────────────────────────────────────────┘
                              │
                    JSON-RPC over stdio
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     MCP SERVER                               │
│                                                              │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│   │   Tools     │  │  Resources  │  │   Prompts   │        │
│   │ (callable)  │  │ (readable)  │  │ (templates) │        │
│   └─────────────┘  └─────────────┘  └─────────────┘        │
│                              │                              │
│                      Your Implementation                    │
│                    (databases, APIs, logic)                 │
└─────────────────────────────────────────────────────────────┘
```

### Communication Flow

```
1. Claude Code discovers server tools via list_tools()
2. Claude decides to call a tool based on user query
3. Claude sends tool call via JSON-RPC
4. Server executes tool, returns result
5. Claude incorporates result into response
```

### The MCP SDK

```python
# Two approaches to building servers:

# Approach 1: Low-level Server class
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("my-server")

@server.list_tools()
async def list_tools():
    return [Tool(name="my_tool", description="...", inputSchema={...})]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "my_tool":
        return [TextContent(type="text", text="result")]

# Approach 2: FastMCP (higher-level)
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-server")

@mcp.tool()
async def my_tool(param: str) -> str:
    """Tool description here"""
    return "result"
```

---

## Our 4 Servers as Case Studies

### Server 1: nlke-intent (Structure-Based)

**Philosophy:** "Structure > Training" - Use KG edges, not embeddings.

**14 Tools:**
```
Phase 1 (4): want_to, can_it, trace, why_not
Phase 2 (10): similar_to, compose_for, alternatives, optimize_for,
              learn, recommend, compatible_with, debug_tool,
              explore_smart, roadmap
```

**Architecture:**
```python
# nlke_intent_server.py structure

TOOL_DEFINITIONS = [
    {
        "name": "want_to",
        "description": """Goal-based tool discovery...""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "goal": {"type": "string", "description": "..."},
                "k": {"type": "integer", "default": 10}
            },
            "required": ["goal"]
        }
    },
    # ... 13 more tools
]

class NLKEIntentServer:
    def __init__(self):
        self.intent_query = IntentDrivenQuery()  # KG adapter

    async def handle_tool_call(self, name: str, args: dict):
        if name == "want_to":
            return self.intent_query.want_to(args["goal"], args.get("k", 10))
        # ... route other tools
```

**Key Pattern:** Each tool maps to a KG traversal method.

### Server 2: nlke-ml (Embedding-Based)

**Philosophy:** "When structure isn't enough, use statistics."

**5 Tools:**
```
hybrid_search, semantic_similarity, cluster_by_topic,
suggest_related, evaluate_query
```

**Architecture:**
```python
# nlke_ml_server.py structure

class NLKEMLServer:
    def __init__(self):
        self.kg_query = BestKGQuery()  # Hybrid search (88.5% recall)

    async def hybrid_search(self, query: str, k: int, scope: str):
        # Uses: embedding (α=0.40) + BM25 (β=0.45) + graph boost (γ=0.15)
        return self.kg_query.query(query, k=k)
```

**Key Pattern:** Wraps trained embeddings in simple API.

### Server 3: nlke-unified (Cross-Domain)

**Philosophy:** "One interface, two KGs, cross-domain insights."

**9 Tools:**
```
unified_query, want_to, can_it, tools_for_pattern,
patterns_for_tool, kg_stats, identify_unsights,
cannot_do, get_anti_patterns
```

**Architecture:**
```python
# nlke_unified_server.py structure

class UnifiedKGQuery:
    # Domain detection keywords
    CLAUDE_SIGNALS = ['tool', 'edit', 'read', 'write', ...]
    GEMINI_SIGNALS = ['gemini', 'api', 'pricing', 'context', ...]
    CROSS_SIGNALS = ['pattern', 'both', 'cross', 'bridge', ...]

    def detect_domain(self, query: str) -> str:
        """Auto-route to claude, gemini, or cross partition"""
        query_lower = query.lower()

        claude_score = sum(1 for s in self.CLAUDE_SIGNALS if s in query_lower)
        gemini_score = sum(1 for s in self.GEMINI_SIGNALS if s in query_lower)

        if any(s in query_lower for s in self.CROSS_SIGNALS):
            return 'cross'
        return 'claude' if claude_score >= gemini_score else 'gemini'
```

**Key Pattern:** Domain auto-detection routes queries optimally.

### Server 4: nlke-metacog (Critical Thinking)

**Philosophy:** "Tools for awareness, not sentience."

**35 Tools across 7 Phases:**
```
Phase 1 (7): validate_fact, check_combinability, detect_mud, synthesize,
             log_synthesis, get_synthesis_chain, metacog_status
Phase 2 (3): assess_texture, texture_compatibility, smooth_to_rough_bridge
Phase 3 (4): identify_lighting, change_lighting, shadow_detection, lighting_compatibility
Phase 4 (4): determine_composition, composition_compatibility, recompose, identify_gaps
Phase 5 (4): assess_contrast, contrast_compatibility, nuance_check, reveal_hidden_contrast
Phase 6 (4): assess_method, method_compatibility, method_sensitivity, reveal_method_assumptions
Phase 7 (9): persist_validated_fact, retrieve_relevant_facts, log_insight,
             analyze_recursion_depth, log_evolution_event, get_evolution_history,
             add_causal_relation, check_retrain_needed
```

**Architecture:**
```python
# nlke_metacognition_server.py structure (3600+ lines of logic)

from nlke_mcp.tools.metacognition import MetaCognition

class MetaCognitionServer:
    def __init__(self):
        self.metacog = MetaCognition()  # Core logic

    async def validate_fact(self, statement: str, evidence: str = None, domain: str = None):
        return self.metacog.validate_fact(statement, evidence, domain)

    async def detect_mud(self, inputs: List[str], proposed_output: str):
        # 6-layer mud detection
        return self.metacog.detect_mud(inputs, proposed_output)
```

**Key Pattern:** Heavy logic lives in separate module (`metacognition.py`), server is thin wrapper.

---

## Building Your First Server

### Step 1: Define Your Tools

Start by defining what your server will do:

```python
# my_server_tools.py

TOOL_DEFINITIONS = [
    {
        "name": "my_first_tool",
        "description": """What this tool does.

When to use:
- Scenario 1
- Scenario 2

Returns: Description of return value""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "required_param": {
                    "type": "string",
                    "description": "What this parameter does"
                },
                "optional_param": {
                    "type": "integer",
                    "default": 10,
                    "description": "Optional with default"
                }
            },
            "required": ["required_param"]
        }
    }
]
```

### Step 2: Implement Tool Logic

```python
# my_server_logic.py

class MyServerLogic:
    def __init__(self):
        # Initialize any resources (databases, APIs, etc.)
        self.db = sqlite3.connect("my_data.db")

    def my_first_tool(self, required_param: str, optional_param: int = 10):
        """Implementation of my_first_tool"""
        # Your logic here
        result = self.query_database(required_param, optional_param)
        return {"status": "success", "data": result}

    def close(self):
        """Cleanup resources"""
        self.db.close()
```

### Step 3: Create the Server

```python
# my_mcp_server.py
#!/usr/bin/env python3
"""
My MCP Server
=============

Description of what this server provides.

Tools:
- my_first_tool: Does X
- my_second_tool: Does Y
"""

import sys
import asyncio
import json
from pathlib import Path

# MCP SDK imports
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("Warning: MCP SDK not installed. Install with: pip install mcp")

# Import your logic
from my_server_logic import MyServerLogic
from my_server_tools import TOOL_DEFINITIONS


def create_server():
    """Create and configure the MCP server"""

    server = Server("my-server")
    logic = MyServerLogic()

    @server.list_tools()
    async def list_tools():
        """Return available tools"""
        return [
            Tool(
                name=t["name"],
                description=t["description"],
                inputSchema=t["inputSchema"]
            )
            for t in TOOL_DEFINITIONS
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        """Handle tool calls"""
        try:
            if name == "my_first_tool":
                result = logic.my_first_tool(
                    required_param=arguments["required_param"],
                    optional_param=arguments.get("optional_param", 10)
                )
            else:
                result = {"error": f"Unknown tool: {name}"}

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        except Exception as e:
            return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

    return server


async def main():
    """Run the server"""
    if not MCP_AVAILABLE:
        print("MCP SDK required. Install with: pip install mcp")
        sys.exit(1)

    server = create_server()

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
```

### Step 4: Register with Claude Code

Add to your Claude Code configuration:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "python3",
      "args": ["/path/to/my_mcp_server.py"]
    }
  }
}
```

---

## Tool Design Patterns

### Pattern 1: Query Tools

**Purpose:** Retrieve information from a data source.

```python
{
    "name": "search_documents",
    "description": """Search documents by keyword or semantic similarity.

Use this when:
- User asks about a specific topic
- Need to find relevant information

Returns: List of matching documents with relevance scores""",
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "k": {"type": "integer", "default": 5, "description": "Number of results"},
            "filter_type": {"type": "string", "enum": ["all", "recent", "popular"]}
        },
        "required": ["query"]
    }
}
```

**Implementation:**
```python
def search_documents(self, query: str, k: int = 5, filter_type: str = "all"):
    results = self.index.search(query, k=k)
    if filter_type == "recent":
        results = [r for r in results if r.date > recent_threshold]
    return {"results": results, "query": query, "count": len(results)}
```

### Pattern 2: Action Tools

**Purpose:** Perform an action with side effects.

```python
{
    "name": "persist_fact",
    "description": """Store a validated fact for future retrieval.

Use this when:
- A fact has been validated with confidence > 0.8
- Knowledge should persist across sessions

Side effects: Writes to persistent storage
Returns: Fact ID and persistence status""",
    "inputSchema": {
        "type": "object",
        "properties": {
            "fact": {"type": "string", "description": "The fact to persist"},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "domain": {"type": "string"}
        },
        "required": ["fact", "confidence"]
    }
}
```

**Implementation:**
```python
def persist_fact(self, fact: str, confidence: float, domain: str = None):
    if confidence < 0.8:
        return {"persisted": False, "reason": "Confidence below threshold"}

    fact_id = self.db.insert_fact(fact, confidence, domain)
    return {"persisted": True, "fact_id": fact_id}
```

### Pattern 3: Analysis Tools

**Purpose:** Analyze input and return structured assessment.

```python
{
    "name": "assess_texture",
    "description": """Assess the factual quality (texture) of a statement.

Texture types:
- smooth: Well-established, high consensus
- rough: Contested, nuanced
- grainy: Statistical, probabilistic

Returns: Texture type, confidence, indicators""",
    "inputSchema": {
        "type": "object",
        "properties": {
            "statement": {"type": "string", "description": "Statement to assess"}
        },
        "required": ["statement"]
    }
}
```

### Pattern 4: Compatibility Check Tools

**Purpose:** Check if two items can be combined.

```python
{
    "name": "check_combinability",
    "description": """Check if two facts can be meaningfully combined.

Returns:
- combinable: Boolean
- risks: Array of potential issues
- recommendation: Suggested action""",
    "inputSchema": {
        "type": "object",
        "properties": {
            "fact_a": {"type": "string"},
            "fact_b": {"type": "string"},
            "proposed_synthesis": {"type": "string", "description": "Optional: expected result"}
        },
        "required": ["fact_a", "fact_b"]
    }
}
```

### Pattern 5: Transformation Tools

**Purpose:** Transform input into different form.

```python
{
    "name": "reframe_perspective",
    "description": """Reframe a statement from a different perspective.

Perspectives: technical, business, user, security, ethical
Returns: Reframed statement with confidence""",
    "inputSchema": {
        "type": "object",
        "properties": {
            "statement": {"type": "string"},
            "new_perspective": {
                "type": "string",
                "enum": ["technical", "business", "user", "security", "ethical"]
            }
        },
        "required": ["statement", "new_perspective"]
    }
}
```

### Pattern 6: Meta/Status Tools

**Purpose:** Provide information about the system itself.

```python
{
    "name": "metacog_status",
    "description": """Get current meta-cognitive status.

Shows:
- Validations performed
- Syntheses completed
- Mud detected
- Average confidence

Useful for monitoring reasoning quality""",
    "inputSchema": {
        "type": "object",
        "properties": {
            "window": {
                "type": "string",
                "enum": ["session", "recent", "all"],
                "default": "session"
            }
        }
    }
}
```

---

## Testing and Validation

### Unit Testing Tools

```python
# test_my_server.py

import pytest
from my_server_logic import MyServerLogic

class TestMyServerLogic:

    def setup_method(self):
        self.logic = MyServerLogic()

    def teardown_method(self):
        self.logic.close()

    def test_my_first_tool_basic(self):
        """Test basic functionality"""
        result = self.logic.my_first_tool("test input")
        assert result["status"] == "success"
        assert "data" in result

    def test_my_first_tool_with_optional(self):
        """Test with optional parameter"""
        result = self.logic.my_first_tool("test", optional_param=5)
        assert result["status"] == "success"

    def test_my_first_tool_invalid_input(self):
        """Test error handling"""
        with pytest.raises(ValueError):
            self.logic.my_first_tool("")  # Empty input should fail


# Run with: pytest test_my_server.py -v
```

### Integration Testing

```python
# test_integration.py

import asyncio
import json
from my_mcp_server import create_server

async def test_server_integration():
    """Test full server flow"""
    server = create_server()

    # Test list_tools
    tools = await server.list_tools()
    assert len(tools) > 0
    assert any(t.name == "my_first_tool" for t in tools)

    # Test call_tool
    result = await server.call_tool("my_first_tool", {"required_param": "test"})
    assert len(result) == 1
    data = json.loads(result[0].text)
    assert data["status"] == "success"


if __name__ == "__main__":
    asyncio.run(test_server_integration())
```

### Our Test Suite Example

```python
# From nlke_metacognition_server.py (64 tests)

def run_tests():
    """Run comprehensive test suite"""

    tests_passed = 0
    tests_failed = 0

    # Phase 1: Base validation tests
    test_cases = [
        # Test validate_fact
        ("validate_fact_true", lambda: metacog.validate_fact(
            "Water boils at 100°C at sea level"
        )['is_fact'] == True),

        ("validate_fact_opinion", lambda: metacog.validate_fact(
            "I think Python is the best"
        )['is_fact'] == False),

        # Test detect_mud
        ("detect_mud_valid", lambda: metacog.detect_mud(
            ["Water boils at 100°C", "Steam is hot"],
            "Boiling water produces hot steam"
        )['is_mud'] == False),

        ("detect_mud_invalid", lambda: metacog.detect_mud(
            ["I think X is good", "X is popular"],
            "X is good because it's popular"
        )['is_mud'] == True),

        # ... 60 more tests
    ]

    for name, test_fn in test_cases:
        try:
            if test_fn():
                tests_passed += 1
                print(f"  ✓ {name}")
            else:
                tests_failed += 1
                print(f"  ✗ {name}")
        except Exception as e:
            tests_failed += 1
            print(f"  ✗ {name}: {e}")

    print(f"\n{tests_passed}/{tests_passed + tests_failed} tests passed")
    return tests_failed == 0
```

### Running Tests

```bash
# Run as MCP server
python3 nlke_metacognition_server.py

# Run tests
python3 nlke_metacognition_server.py --test

# Expected output:
# Running NLKE Meta-Cognition tests...
# Phase 1: Base validation
#   ✓ validate_fact_true
#   ✓ validate_fact_opinion
#   ...
# 64/64 tests passed
```

---

## Integration with Claude Code

### Configuration File

Location: `~/.config/claude-code/config.json` (or similar)

```json
{
  "mcpServers": {
    "nlke-intent": {
      "command": "python3",
      "args": ["/path/to/nlke_mcp/servers/nlke_intent_server.py"],
      "description": "Intent-driven KG queries (14 tools)"
    },
    "nlke-ml": {
      "command": "python3",
      "args": ["/path/to/nlke_mcp/servers/nlke_ml_server.py"],
      "description": "ML-based semantic search (5 tools)"
    },
    "nlke-unified": {
      "command": "python3",
      "args": ["/path/to/nlke_mcp/servers/nlke_unified_server.py"],
      "description": "Cross-domain unified queries (9 tools)"
    },
    "nlke-metacog": {
      "command": "python3",
      "args": ["/path/to/nlke_mcp/servers/nlke_metacognition_server.py"],
      "description": "Meta-cognition tools (35 tools)"
    }
  }
}
```

### Tool Naming Conventions

MCP tools appear in Claude Code with prefix `mcp__<server>__<tool>`:

```
mcp__nlke-intent__want_to
mcp__nlke-intent__can_it
mcp__nlke-ml__hybrid_search
mcp__nlke-metacog__validate_fact
```

### Tool Discovery by Claude

Claude Code automatically:
1. Lists available tools at startup
2. Reads tool descriptions
3. Matches user queries to appropriate tools
4. Calls tools with appropriate parameters

**Good descriptions help Claude choose correctly:**

```python
# Bad description (too vague)
"description": "Searches things"

# Good description (specific and actionable)
"description": """Hybrid semantic search with 88.5% recall.

Combines:
- Embedding similarity (α=0.40)
- BM25 keyword matching (β=0.45)
- Graph neighbor boosting (γ=0.15)

Use this when:
- Simple keyword search fails
- Need semantic understanding
- Looking for conceptually related content

Examples:
- hybrid_search("reduce API costs") → finds cost optimization patterns
- hybrid_search("error handling best practices")
"""
```

---

## Cost Optimization

### Local vs API-Based Tools

| Approach | Cost | Latency | Use Case |
|----------|------|---------|----------|
| Local database | $0 | ~10ms | KG queries, cached data |
| Local embeddings | $0 | ~50ms | Semantic search |
| Local model | $0 | ~500ms | Text generation |
| API call (Claude) | ~$0.003/1k tokens | ~1s | Complex reasoning |
| API call (Gemini) | ~$0.0001/1k tokens | ~500ms | Large context |

### Our Cost Structure

```
nlke-intent: 14 tools × $0 = $0/query (KG traversal)
nlke-ml: 5 tools × $0 = $0/query (local embeddings)
nlke-unified: 9 tools × $0 = $0/query (unified KG)
nlke-metacog: 35 tools × $0 = $0/query (rule-based)

Total: 63 tools, $0 per query
```

### When to Use External APIs

```python
# Decision framework

def should_use_api(task_type: str) -> str:
    """Decide: local vs API"""

    # Use local for:
    # - KG queries (structure is enough)
    # - Cached lookups (already computed)
    # - Rule-based validation (deterministic)
    # - Simple transformations (regex, etc.)

    # Use API for:
    # - Novel text generation
    # - Complex multi-step reasoning
    # - Large context understanding (>100k tokens)
    # - Tasks requiring latest knowledge

    if task_type in ["kg_query", "lookup", "validation", "transform"]:
        return "local"
    elif task_type in ["generate", "reason", "summarize_large"]:
        return "api"
    else:
        return "local"  # Default to free
```

### Caching Strategies

```python
class CachedMCPServer:
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 3600  # 1 hour

    def get_cached(self, key: str):
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.cache_ttl:
                return value
        return None

    def set_cached(self, key: str, value: any):
        self.cache[key] = (value, time.time())

    def query_with_cache(self, query: str, k: int = 5):
        cache_key = f"query:{query}:{k}"

        cached = self.get_cached(cache_key)
        if cached:
            return cached

        result = self.expensive_query(query, k)
        self.set_cached(cache_key, result)
        return result
```

---

## Troubleshooting

### Issue: Server Not Starting

**Symptoms:** Server fails to launch, no tools available

**Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| MCP SDK not installed | `pip install mcp` |
| Python path issues | Check shebang: `#!/usr/bin/env python3` |
| Import errors | Verify all dependencies available |
| Permission denied | `chmod +x server.py` |

**Debug:**
```bash
# Test server directly
python3 /path/to/server.py

# Check for import errors
python3 -c "from mcp.server import Server; print('OK')"

# Verify database access
python3 -c "import sqlite3; sqlite3.connect('/path/to/db.db'); print('OK')"
```

### Issue: Tools Not Appearing

**Symptoms:** Server runs but tools not visible in Claude Code

**Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| Config path wrong | Check `~/.config/claude-code/config.json` |
| Server name mismatch | Match config key to server name |
| list_tools() error | Check server logs for exceptions |

**Debug:**
```python
# Test list_tools directly
import asyncio
from my_server import create_server

async def test():
    server = create_server()
    tools = await server.list_tools()
    for t in tools:
        print(f"- {t.name}: {t.description[:50]}...")

asyncio.run(test())
```

### Issue: Tool Call Failing

**Symptoms:** Tool appears but returns errors when called

**Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| Parameter mismatch | Check inputSchema matches handler |
| Missing required param | Add to "required" array |
| Type coercion | Use `arguments.get("param", default)` |
| Exception not caught | Wrap in try/except |

**Debug:**
```python
# Add logging to call_tool
@server.call_tool()
async def call_tool(name: str, arguments: dict):
    print(f"DEBUG: call_tool({name}, {arguments})")
    try:
        result = handle_tool(name, arguments)
        print(f"DEBUG: result = {result}")
        return [TextContent(type="text", text=json.dumps(result))]
    except Exception as e:
        print(f"DEBUG: error = {e}")
        import traceback
        traceback.print_exc()
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]
```

### Issue: Slow Response Times

**Symptoms:** Tools work but take too long

**Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| Database not indexed | Add indexes on query columns |
| Loading embeddings each call | Load once at startup |
| No caching | Implement result caching |
| Network latency | Use local resources |

**Profile:**
```python
import time

def timed_query(self, query: str):
    start = time.time()
    result = self.actual_query(query)
    elapsed = time.time() - start
    print(f"Query took {elapsed:.3f}s")
    return result
```

---

## Real-World Examples

### Example 1: Building a Documentation Server

**Goal:** Expose internal documentation via MCP.

```python
# doc_server.py

TOOL_DEFINITIONS = [
    {
        "name": "search_docs",
        "description": "Search internal documentation",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "section": {"type": "string", "enum": ["api", "guides", "faq"]}
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_doc",
        "description": "Get a specific document by ID",
        "inputSchema": {
            "type": "object",
            "properties": {
                "doc_id": {"type": "string"}
            },
            "required": ["doc_id"]
        }
    }
]

class DocServer:
    def __init__(self):
        self.docs = self.load_docs()
        self.index = self.build_index()

    def search_docs(self, query: str, section: str = None):
        results = self.index.search(query)
        if section:
            results = [r for r in results if r.section == section]
        return results

    def get_doc(self, doc_id: str):
        return self.docs.get(doc_id)
```

### Example 2: Building a Metrics Server

**Goal:** Expose application metrics to Claude for analysis.

```python
# metrics_server.py

TOOL_DEFINITIONS = [
    {
        "name": "get_metrics",
        "description": "Get application metrics for a time range",
        "inputSchema": {
            "type": "object",
            "properties": {
                "metric_name": {"type": "string"},
                "start_time": {"type": "string", "format": "date-time"},
                "end_time": {"type": "string", "format": "date-time"},
                "aggregation": {"type": "string", "enum": ["avg", "sum", "max", "min"]}
            },
            "required": ["metric_name"]
        }
    },
    {
        "name": "detect_anomalies",
        "description": "Detect anomalies in metric data",
        "inputSchema": {
            "type": "object",
            "properties": {
                "metric_name": {"type": "string"},
                "sensitivity": {"type": "number", "minimum": 0, "maximum": 1}
            },
            "required": ["metric_name"]
        }
    }
]
```

### Example 3: Building a Code Analysis Server

**Goal:** Expose codebase analysis tools.

```python
# code_analysis_server.py

TOOL_DEFINITIONS = [
    {
        "name": "find_function",
        "description": "Find function definitions by name",
        "inputSchema": {
            "type": "object",
            "properties": {
                "function_name": {"type": "string"},
                "language": {"type": "string", "enum": ["python", "javascript", "go"]}
            },
            "required": ["function_name"]
        }
    },
    {
        "name": "analyze_complexity",
        "description": "Analyze code complexity",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"}
            },
            "required": ["file_path"]
        }
    },
    {
        "name": "find_dependencies",
        "description": "Find all imports/dependencies of a file",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "depth": {"type": "integer", "default": 1}
            },
            "required": ["file_path"]
        }
    }
]
```

---

## Summary

### Building MCP Servers Checklist

1. **Define tools** with clear descriptions and input schemas
2. **Implement logic** in separate module for testability
3. **Create server** using MCP SDK patterns
4. **Test thoroughly** with unit and integration tests
5. **Register** with Claude Code configuration
6. **Optimize** for cost and latency

### Key Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Separation of concerns** | Logic separate from server wrapper |
| **Clear descriptions** | Help Claude choose right tool |
| **Typed parameters** | Use inputSchema for validation |
| **Error handling** | Always wrap in try/except |
| **Local first** | Minimize API calls |
| **Testability** | Unit tests for each tool |

### Our 4-Server Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CLAUDE CODE                              │
└─────────────────────────────────────────────────────────────┘
              │           │           │           │
              ▼           ▼           ▼           ▼
         ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
         │ Intent │  │   ML   │  │Unified │  │Metacog │
         │   14   │  │    5   │  │    9   │  │   35   │
         │ tools  │  │ tools  │  │ tools  │  │ tools  │
         └────────┘  └────────┘  └────────┘  └────────┘
              │           │           │           │
              ▼           ▼           ▼           ▼
         ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
         │ClaudeKG│  │GeminiKG│  │UnifiedKG│ │ SQLite │
         │  511n  │  │  278n  │  │ Bridge │  │  DB    │
         └────────┘  └────────┘  └────────┘  └────────┘

Total: 63 tools, $0 per query, local processing
```

---

## Additional Resources

**See Also (Playbooks):**
- **[Playbook 3: Agent Development](PLAYBOOK-3-AGENT-DEVELOPMENT.md)** - Autonomous workflows
- **[Playbook 8: Continuous Learning Loop](PLAYBOOK-8-CONTINUOUS-LEARNING-LOOP.md)** - Fact persistence
- **[Playbook 9: Metacognition Workflows](PLAYBOOK-9-METACOGNITION-WORKFLOWS.md)** - 35 metacog tools
- **[Playbook 11: Session Handoff Protocol](PLAYBOOK-11-SESSION-HANDOFF-PROTOCOL.md)** - Knowledge transfer

**MCP Documentation:**
- `nlke_mcp/MCP-SERVER-MANUAL.md` (complete reference)
- `nlke_mcp/servers/*.py` (our implementations)
- `nlke_mcp/tools/metacognition.py` (3600+ lines of logic)

**Official Resources:**
- MCP SDK: `pip install mcp`
- MCP Specification: https://modelcontextprotocol.io

---

**Playbook Version:** 1.0
**Last Updated:** November 27, 2025
**Created By:** Eyal + Claude Opus 4.5
**Methodology:** NLKE v3.0 - Build WITH AI, Document AS you build

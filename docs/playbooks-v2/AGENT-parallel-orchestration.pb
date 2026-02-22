# PLAYBOOK-11: Parallel Agent Orchestration

> **Synthesis Origin**: Claude Code Task Tool + Agent SDK + Swarm Patterns
> **Color Mix**: Blue (Subagents) + Yellow (Parallelism) = Green (Scalable Workflows)

## Overview

This playbook covers **orchestrating multiple Claude agents** for parallel task execution. Master subagent spawning, model selection, context isolation, and swarm coordination.

**Key Insight**: Large codebases exceed single context windows. Parallel agents with isolated contexts can explore, analyze, and modify different parts simultaneously, achieving 10x throughput.

### Strategic Value

| Approach | Speed | Cost | Context |
|----------|-------|------|---------|
| Single agent | 1x | Baseline | 200K shared |
| Sequential subagents | 1.5x | Similar | 200K each |
| Parallel subagents (10) | 10x | Higher | 200K × 10 |
| Hybrid (Haiku workers) | 8x | 60% lower | Mixed |

---

## Part 1: Subagent Architecture

### 1.1 The Task Tool Model

```
┌─────────────────────────────────────────────────────────────┐
│                   SUBAGENT ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              COORDINATOR (Main Agent)                │    │
│  │                                                      │    │
│  │  • Receives user request                            │    │
│  │  • Decomposes into subtasks                         │    │
│  │  • Spawns subagents via Task tool                   │    │
│  │  • Aggregates results                               │    │
│  │  • Responds to user                                 │    │
│  └──────────────────────┬───────────────────────────────┘    │
│                         │                                    │
│           ┌─────────────┼─────────────┐                     │
│           │             │             │                      │
│           ▼             ▼             ▼                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │  Subagent   │ │  Subagent   │ │  Subagent   │           │
│  │   (Haiku)   │ │  (Sonnet)   │ │  (Haiku)    │           │
│  │             │ │             │ │             │            │
│  │ Own context │ │ Own context │ │ Own context │            │
│  │ Own tools   │ │ Own tools   │ │ Own tools   │            │
│  │ Isolated    │ │ Isolated    │ │ Isolated    │            │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘           │
│         │               │               │                    │
│         ▼               ▼               ▼                    │
│      Result 1        Result 2        Result 3                │
│         │               │               │                    │
│         └───────────────┴───────────────┘                   │
│                         │                                    │
│                         ▼                                    │
│                   Aggregated Result                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Available Subagent Types

| Type | Purpose | Tools | Best For |
|------|---------|-------|----------|
| `Explore` | Codebase exploration | Glob, Grep, Read | Finding files, understanding structure |
| `Plan` | Design implementation | All tools | Architecture planning |
| `general-purpose` | Multi-step tasks | All tools | Complex autonomous work |
| `claude-code-guide` | Documentation lookup | Web tools | CLI/SDK questions |

### 1.3 Task Tool Parameters

```python
# Task tool parameters
{
    "subagent_type": "Explore",        # Required: Agent type
    "description": "Find auth files",   # Required: Short description (3-5 words)
    "prompt": "Find authentication...", # Required: Detailed task
    "model": "haiku",                   # Optional: haiku/sonnet/opus
    "run_in_background": True,          # Optional: Don't block
    "resume": "agent_id_123"            # Optional: Continue previous agent
}
```

### 1.4 Model Selection Guide

```
┌─────────────────────────────────────────────────────────────┐
│                    MODEL SELECTION MATRIX                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  HAIKU ($0.25/$1.25 per M tokens)                           │
│  ─────────────────────────────────                          │
│  Use for:                                                    │
│  • File discovery (Glob patterns)                           │
│  • Code search (Grep operations)                            │
│  • Simple file reads                                         │
│  • Format conversions                                        │
│  • Parallel workers in swarms                               │
│                                                              │
│  SONNET ($3/$15 per M tokens)                               │
│  ─────────────────────────────                               │
│  Use for:                                                    │
│  • Code analysis and review                                  │
│  • Implementation planning                                   │
│  • Debugging assistance                                      │
│  • Documentation generation                                  │
│  • Default choice for most tasks                            │
│                                                              │
│  OPUS ($15/$75 per M tokens)                                │
│  ────────────────────────────                                │
│  Use for:                                                    │
│  • Architecture decisions                                    │
│  • Complex refactoring                                       │
│  • Security analysis                                         │
│  • Multi-file coordination                                   │
│  • Final synthesis/aggregation                              │
│                                                              │
│  COST COMPARISON (1M tokens):                               │
│  Haiku:  $1.50                                              │
│  Sonnet: $18.00                                             │
│  Opus:   $90.00                                             │
│                                                              │
│  Opus is 60x more expensive than Haiku!                     │
│  Use strategically.                                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Part 2: Parallel Execution Patterns

### 2.1 Fan-Out Pattern

Spawn multiple agents for independent tasks:

```
User: "Review all API endpoints for security issues"

Coordinator thinks:
- This can be parallelized by module
- API has 5 modules: auth, users, products, orders, payments
- Each module can be reviewed independently

Coordinator spawns 5 Haiku agents in parallel:
- Agent 1: Review auth module (src/api/auth/)
- Agent 2: Review users module (src/api/users/)
- Agent 3: Review products module (src/api/products/)
- Agent 4: Review orders module (src/api/orders/)
- Agent 5: Review payments module (src/api/payments/)

Each agent returns findings.

Coordinator (Sonnet) aggregates into final report.
```

### 2.2 Scatter-Gather Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                   SCATTER-GATHER PATTERN                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│                      ┌──────────┐                           │
│                      │   User   │                           │
│                      │  Query   │                           │
│                      └────┬─────┘                           │
│                           │                                  │
│                           ▼                                  │
│                   ┌──────────────┐                          │
│                   │ Coordinator  │                          │
│                   │   (Opus)     │                          │
│                   └──────┬───────┘                          │
│                          │                                   │
│         ┌────────────────┼────────────────┐                 │
│         │ SCATTER        │                │                 │
│         ▼                ▼                ▼                  │
│   ┌───────────┐   ┌───────────┐   ┌───────────┐            │
│   │  Worker 1 │   │  Worker 2 │   │  Worker 3 │            │
│   │  (Haiku)  │   │  (Haiku)  │   │  (Haiku)  │            │
│   │           │   │           │   │           │             │
│   │ Explore   │   │ Explore   │   │ Explore   │            │
│   │ src/api/  │   │ src/core/ │   │ src/util/ │            │
│   └─────┬─────┘   └─────┬─────┘   └─────┬─────┘            │
│         │               │               │                    │
│         │ GATHER        │               │                    │
│         └───────────────┼───────────────┘                   │
│                         │                                    │
│                         ▼                                    │
│                 ┌──────────────┐                            │
│                 │   Synthesis  │                            │
│                 │   (Sonnet)   │                            │
│                 └──────┬───────┘                            │
│                        │                                     │
│                        ▼                                     │
│                   ┌─────────┐                               │
│                   │ Result  │                               │
│                   └─────────┘                               │
│                                                              │
│  Benefits:                                                   │
│  • 3x faster than sequential                                │
│  • 60% cost reduction (Haiku workers)                       │
│  • 3x context capacity (separate windows)                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 Pipeline Pattern

Sequential agents with handoff:

```
┌─────────────────────────────────────────────────────────────┐
│                     PIPELINE PATTERN                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │  Stage 1:   │    │  Stage 2:   │    │  Stage 3:   │     │
│  │  Explore    │───►│  Analyze    │───►│  Implement  │     │
│  │  (Haiku)    │    │  (Sonnet)   │    │  (Opus)     │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│                                                              │
│  Example: Adding a new API endpoint                         │
│                                                              │
│  Stage 1 (Haiku): Find similar endpoints, patterns          │
│  Output: File list, code patterns                           │
│                                                              │
│  Stage 2 (Sonnet): Design endpoint based on patterns        │
│  Output: Implementation plan, interface design              │
│                                                              │
│  Stage 3 (Opus): Write code, tests, documentation           │
│  Output: Complete implementation                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 2.4 Background Agent Pattern

Non-blocking execution with TaskOutput:

```python
# Conceptual flow for background agents

# 1. Spawn background agents (don't wait)
spawn_agent(
    type="Explore",
    prompt="Find all test files",
    run_in_background=True,
    id="agent_tests"
)

spawn_agent(
    type="Explore",
    prompt="Find all config files",
    run_in_background=True,
    id="agent_config"
)

# 2. Continue other work while agents run
do_other_work()

# 3. Retrieve results when needed
test_files = get_output("agent_tests", block=True)
config_files = get_output("agent_config", block=True)

# 4. Use results
process_findings(test_files, config_files)
```

---

## Part 3: Swarm Orchestration

### 3.1 Swarm Concepts

```
┌─────────────────────────────────────────────────────────────┐
│                      SWARM CONCEPTS                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  SWARM = Multiple agents working toward shared goal          │
│                                                              │
│  Components:                                                 │
│  ───────────                                                 │
│  • Queen (Coordinator) - Plans and assigns tasks            │
│  • Workers (Subagents) - Execute individual tasks           │
│  • Shared Context - Common knowledge across swarm           │
│  • Result Buffer - Aggregated findings                      │
│                                                              │
│  Concurrency Limits:                                         │
│  ──────────────────                                          │
│  • Maximum 10 parallel subagents                            │
│  • Each has own 200K context window                         │
│  • Total potential context: 2M tokens (10 × 200K)           │
│                                                              │
│  Communication:                                              │
│  ──────────────                                              │
│  • Agents cannot communicate directly                       │
│  • All coordination through coordinator                     │
│  • Results passed back to coordinator                       │
│  • Coordinator synthesizes and distributes                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Swarm Task Decomposition

```python
# Task decomposition for swarm execution

def decompose_for_swarm(task: str, codebase_size: int) -> list:
    """
    Decompose a task for parallel execution.

    Rules:
    1. Independent subtasks only (no dependencies)
    2. Each subtask < 200K context
    3. Maximum 10 subtasks (concurrency limit)
    4. Prefer Haiku for workers (cost)
    """

    subtasks = []

    # Strategy 1: By directory
    if "entire codebase" in task:
        directories = get_top_directories()
        for dir in directories[:10]:  # Max 10
            subtasks.append({
                "scope": dir,
                "prompt": f"In {dir}: {task}",
                "model": "haiku"
            })

    # Strategy 2: By file type
    elif "all files of type" in task:
        file_groups = group_files_by_type()
        for file_type, files in file_groups.items():
            subtasks.append({
                "scope": file_type,
                "files": files,
                "model": "haiku"
            })

    # Strategy 3: By concern
    elif "review" in task or "analyze" in task:
        concerns = ["security", "performance", "maintainability"]
        for concern in concerns:
            subtasks.append({
                "focus": concern,
                "prompt": f"Focus on {concern}: {task}",
                "model": "sonnet"  # Analysis needs Sonnet
            })

    return subtasks
```

### 3.3 Swarm Coordination Example

```
User: "Find all security vulnerabilities in the codebase"

Coordinator (Opus) creates swarm plan:

PHASE 1 - Discovery (Parallel, Haiku)
├── Agent 1: Find all SQL queries (potential injection)
├── Agent 2: Find all user input handling
├── Agent 3: Find all authentication code
├── Agent 4: Find all file operations
├── Agent 5: Find all external API calls
└── Agent 6: Find all crypto/hashing code

PHASE 2 - Analysis (Parallel, Sonnet)
├── Agent 7: Analyze SQL findings for injection
├── Agent 8: Analyze input handling for XSS
├── Agent 9: Analyze auth for bypass risks
└── Agent 10: Analyze crypto for weak algorithms

PHASE 3 - Synthesis (Sequential, Opus)
└── Aggregate all findings into prioritized report

Estimated time: 3 minutes (vs 20 minutes sequential)
Estimated cost: $2.50 (60% savings from Haiku workers)
```

---

## Part 4: Context Isolation

### 4.1 Context Boundaries

```
┌─────────────────────────────────────────────────────────────┐
│                   CONTEXT ISOLATION                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Each subagent has COMPLETELY ISOLATED context:             │
│                                                              │
│  ┌─────────────────┐      ┌─────────────────┐              │
│  │   Coordinator   │      │   Subagent 1    │              │
│  │                 │      │                 │               │
│  │ • Full convo    │      │ • Only prompt   │              │
│  │ • All files     │      │ • No history    │              │
│  │ • User context  │      │ • Fresh start   │              │
│  │                 │      │                 │               │
│  │ [200K tokens]   │      │ [200K tokens]   │              │
│  └─────────────────┘      └─────────────────┘              │
│                                                              │
│  IMPLICATIONS:                                               │
│  ─────────────                                               │
│                                                              │
│  1. Subagents don't know conversation history               │
│     → Include all necessary context in prompt               │
│                                                              │
│  2. Subagents can't see each other's work                   │
│     → Coordinator must aggregate and redistribute           │
│                                                              │
│  3. Subagents start fresh each time                         │
│     → No state between spawns (unless resumed)              │
│                                                              │
│  4. Each has full 200K for their task                       │
│     → Can read large files without affecting main context   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Prompt Engineering for Subagents

```markdown
# Good subagent prompt (self-contained)

You are exploring a Python codebase to find authentication-related files.

CONTEXT:
- This is a FastAPI application
- Authentication should be in src/auth/ or similar
- Look for: JWT, OAuth, session, login, password patterns

TASK:
Find all files related to authentication. For each file:
1. File path
2. Primary purpose
3. Key functions/classes

OUTPUT FORMAT:
Return a JSON list:
[{"path": "...", "purpose": "...", "key_items": [...]}]

DO:
- Use Glob to find Python files
- Use Grep to search for auth patterns
- Read promising files to confirm

DON'T:
- Modify any files
- Make assumptions about other modules
- Return more than 20 files
```

```markdown
# Bad subagent prompt (assumes context)

Find the auth files we discussed earlier and add the OAuth feature.

# Problems:
# - "we discussed" - subagent has no history
# - "the auth files" - not specified
# - "add OAuth" - too vague without specs
```

### 4.3 Agent Resume Pattern

Continue previous agent's work:

```python
# First spawn - exploration
agent_id = spawn_agent(
    type="Explore",
    prompt="Find all API endpoints in src/api/",
    model="haiku"
)
# Returns: agent_id = "abc123", result = {...}

# Later - continue with same context
spawn_agent(
    resume="abc123",  # Resume previous agent
    prompt="Now categorize those endpoints by HTTP method"
)
# Agent has full context from previous exploration
```

---

## Part 5: Cost Optimization

### 5.1 Haiku-First Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                  HAIKU-FIRST STRATEGY                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  PRINCIPLE: Start cheap, escalate only when needed          │
│                                                              │
│  Step 1: Try Haiku first                                    │
│  ─────────────────────────                                   │
│  Cost: $0.25/$1.25 per M tokens                             │
│  Good for: Discovery, simple analysis, formatting           │
│                                                              │
│  Step 2: Escalate to Sonnet if needed                       │
│  ────────────────────────────────────                        │
│  Cost: $3/$15 per M tokens (12x Haiku)                      │
│  Trigger: Haiku response is low quality/incomplete          │
│                                                              │
│  Step 3: Use Opus for critical synthesis                    │
│  ─────────────────────────────────────                       │
│  Cost: $15/$75 per M tokens (60x Haiku)                     │
│  Trigger: Final aggregation, architecture decisions         │
│                                                              │
│  EXAMPLE COST BREAKDOWN:                                     │
│  ────────────────────────                                    │
│  Task: Review 10 modules for security                       │
│                                                              │
│  All Opus:     10 × $90 = $900                              │
│  All Sonnet:   10 × $18 = $180                              │
│  Haiku + Opus: (10 × $1.50) + (1 × $90) = $105             │
│                                                              │
│  Savings: 88% vs All Opus, 42% vs All Sonnet               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Task Routing Rules

```python
# Task routing for cost optimization

def select_model(task: dict) -> str:
    """
    Select optimal model for a task.

    Cost: Haiku ($1.50/M) < Sonnet ($18/M) < Opus ($90/M)
    """

    task_type = task.get("type", "")
    complexity = task.get("complexity", "medium")
    requires_accuracy = task.get("requires_accuracy", False)

    # Always Haiku for:
    if task_type in ["glob", "grep", "find", "list"]:
        return "haiku"

    if task_type == "read" and not requires_accuracy:
        return "haiku"

    # Always Sonnet for:
    if task_type in ["analyze", "review", "explain"]:
        return "sonnet"

    if complexity == "medium":
        return "sonnet"

    # Only Opus for:
    if complexity == "high":
        return "opus"

    if task_type in ["architecture", "security_audit", "refactor_plan"]:
        return "opus"

    if requires_accuracy and task_type == "write":
        return "opus"

    # Default
    return "sonnet"
```

### 5.3 Batch Parallel Execution

```
┌─────────────────────────────────────────────────────────────┐
│                BATCH PARALLEL EXECUTION                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Instead of: 10 sequential Opus calls ($900)                │
│                                                              │
│  Do: 10 parallel Haiku calls + 1 Opus synthesis ($105)      │
│                                                              │
│  Timeline:                                                   │
│  ─────────                                                   │
│                                                              │
│  Sequential (Opus only):                                     │
│  [Task 1]→[Task 2]→[Task 3]→...→[Task 10]                  │
│  Time: 10 minutes | Cost: $900                              │
│                                                              │
│  Parallel (Haiku workers):                                   │
│  [Task 1]┐                                                  │
│  [Task 2]├→[Synthesis (Opus)]                               │
│  [Task 3]┤                                                   │
│  ...     │                                                   │
│  [Task10]┘                                                  │
│  Time: 1.5 minutes | Cost: $105                             │
│                                                              │
│  Speedup: 6.7x                                              │
│  Cost savings: 88%                                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Part 6: Error Handling

### 6.1 Subagent Failure Modes

| Failure | Cause | Recovery |
|---------|-------|----------|
| Timeout | Task too complex | Split into smaller tasks |
| Context overflow | Too many files | Limit scope |
| No results | Bad prompt | Refine prompt, retry |
| Partial results | Interrupted | Resume agent |
| Wrong results | Misunderstood task | Clarify prompt |

### 6.2 Fault-Tolerant Swarm

```python
# Fault-tolerant swarm execution

class FaultTolerantSwarm:
    """Swarm with automatic retry and fallback."""

    def __init__(self, max_retries: int = 2):
        self.max_retries = max_retries
        self.results = {}
        self.failures = {}

    async def execute(self, tasks: list) -> dict:
        """Execute tasks with fault tolerance."""

        # Phase 1: Try all tasks in parallel
        pending = tasks.copy()
        attempt = 0

        while pending and attempt < self.max_retries:
            attempt += 1

            # Spawn agents for pending tasks
            agents = []
            for task in pending:
                agent = spawn_agent(
                    type=task["type"],
                    prompt=task["prompt"],
                    model=self._select_model(task, attempt),
                    run_in_background=True
                )
                agents.append((task["id"], agent))

            # Gather results
            for task_id, agent in agents:
                try:
                    result = await get_output(agent, timeout=60)
                    self.results[task_id] = result
                    pending = [t for t in pending if t["id"] != task_id]
                except Exception as e:
                    self.failures[task_id] = str(e)

            # Escalate model for retries
            # Haiku failed? Try Sonnet. Sonnet failed? Try Opus.

        return {
            "results": self.results,
            "failures": self.failures,
            "success_rate": len(self.results) / len(tasks)
        }

    def _select_model(self, task: dict, attempt: int) -> str:
        """Escalate model on retry."""
        models = ["haiku", "sonnet", "opus"]
        base_index = models.index(task.get("model", "haiku"))
        escalated_index = min(base_index + attempt - 1, 2)
        return models[escalated_index]
```

### 6.3 Graceful Degradation

```
┌─────────────────────────────────────────────────────────────┐
│                  GRACEFUL DEGRADATION                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  If parallel execution fails, degrade gracefully:           │
│                                                              │
│  Level 1: Full Swarm (10 parallel agents)                   │
│           ↓ (>50% failures)                                 │
│  Level 2: Reduced Swarm (5 parallel agents)                 │
│           ↓ (still failing)                                 │
│  Level 3: Sequential Execution (1 agent at a time)          │
│           ↓ (still failing)                                 │
│  Level 4: Manual Fallback (report partial results)          │
│                                                              │
│  At each level:                                              │
│  • Log degradation reason                                   │
│  • Notify user of reduced capability                        │
│  • Return best-effort results                               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Part 7: Decision Framework

### When to Use Parallel Agents

```
┌─────────────────────────────────────────────────────────────┐
│              PARALLELIZATION DECISION TREE                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│                Can task be decomposed?                       │
│                        │                                     │
│              ┌─────────┴─────────┐                          │
│              │                   │                           │
│              ▼                   ▼                           │
│             YES                  NO                          │
│              │                   │                           │
│              │                   └──► Single agent           │
│              │                                               │
│              ▼                                               │
│        Are subtasks independent?                            │
│              │                                               │
│     ┌────────┴────────┐                                     │
│     │                 │                                      │
│     ▼                 ▼                                      │
│    YES                NO                                     │
│     │                 │                                      │
│     │                 └──► Pipeline (sequential)            │
│     │                                                        │
│     ▼                                                        │
│ Worth the overhead?                                          │
│ (task > 30 seconds)                                          │
│     │                                                        │
│ ┌───┴───┐                                                   │
│ │       │                                                    │
│ ▼       ▼                                                    │
│YES      NO                                                   │
│ │       │                                                    │
│ │       └──► Single agent (overhead not worth it)           │
│ │                                                            │
│ └──► PARALLEL AGENTS                                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Agent Type Selection

| Scenario | Agent Type | Model | Why |
|----------|------------|-------|-----|
| Find files | Explore | Haiku | Simple, cheap |
| Understand code | Explore | Sonnet | Needs comprehension |
| Design feature | Plan | Opus | Architecture decisions |
| Write code | general-purpose | Opus | Quality critical |
| Run tests | general-purpose | Sonnet | Moderate complexity |
| Answer CLI question | claude-code-guide | Sonnet | Doc lookup |

---

## Checklist

### Planning
- [ ] Task can be decomposed into independent subtasks
- [ ] Each subtask fits in 200K context
- [ ] Subtasks are truly independent (no cross-dependencies)
- [ ] Worth the overhead (total time > 30 seconds)

### Model Selection
- [ ] Using Haiku for simple discovery tasks
- [ ] Using Sonnet for analysis tasks
- [ ] Using Opus only for synthesis/critical decisions
- [ ] Cost estimate acceptable

### Prompt Engineering
- [ ] Subagent prompts are self-contained
- [ ] Context is explicitly provided
- [ ] Output format is specified
- [ ] Scope is clearly limited

### Execution
- [ ] Maximum 10 parallel agents
- [ ] Timeout configured for each task
- [ ] Background execution where appropriate
- [ ] Results aggregation planned

### Error Handling
- [ ] Retry strategy defined
- [ ] Model escalation on failure
- [ ] Graceful degradation path
- [ ] Partial results acceptable

---

## Troubleshooting

### Subagent Returns Empty Results

**Symptom**: Agent returns "no results found"

**Causes**:
1. Prompt too vague → Add specific patterns/paths
2. Scope too narrow → Expand search area
3. Wrong agent type → Use Explore for discovery

### Swarm Takes Too Long

**Symptom**: Parallel execution slower than expected

**Causes**:
1. Tasks not truly parallel → Check dependencies
2. Single bottleneck task → Split large tasks
3. Too many agents (>10) → Batch into waves

### Context Overflow in Subagent

**Symptom**: Agent fails with context error

**Causes**:
1. Too many files to read → Limit scope
2. Files too large → Read specific sections
3. Too much history → Fresh agent (no resume)

### Results Don't Aggregate Well

**Symptom**: Synthesis produces poor output

**Causes**:
1. Inconsistent output formats → Standardize prompts
2. Overlapping scopes → Define boundaries
3. Missing context in synthesis → Include more detail

---

## Resources

### Claude Code Documentation
- [Task Tool Reference](https://docs.anthropic.com/en/docs/claude-code)
- [Agent SDK Guide](https://docs.anthropic.com/en/docs/agents)

### Patterns
- [Scatter-Gather Pattern](https://www.enterpriseintegrationpatterns.com/patterns/messaging/BroadcastAggregate.html)
- [Pipeline Pattern](https://www.enterpriseintegrationpatterns.com/patterns/messaging/PipesAndFilters.html)

### This Project
- `tools/agent_orchestrator.py` - Orchestration implementation
- `tools/agent_pattern_analyzer.py` - Pattern analysis

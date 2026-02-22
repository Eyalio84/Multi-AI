# Pattern #27: Multi-Agent Parallel Synthesis

**Pattern ID:** NLKE-ORCHESTRATION-027
**Version:** 1.0
**Created:** November 27, 2025
**Classification:** Generative Pattern
**Complexity:** Expert

---

## Pattern Description

Multi-Agent Parallel Synthesis is a workflow orchestration pattern that compresses multi-session work into single-session parallel execution while preserving context and enabling cross-pollination between facets.

**Core Principle:** When a complex task has N independent facets, launch N specialized agents in parallel rather than handling them sequentially across multiple sessions.

---

## The Problem It Solves

### Traditional Sequential Approach

```
Session 1: Topic A research + documentation
    ↓ (handoff with ~20% context loss)
Session 2: Topic B research + documentation
    ↓ (handoff with ~20% context loss)
Session 3: Topic C research + documentation
    ↓ (cumulative context loss: ~50%)
Session N: Synthesis (working with degraded context)

Problems:
- Time: Days to weeks
- Cost: N × full session tokens
- Context: Cumulative degradation
- Coherence: Each session has different perspective
- Cross-pollination: None
```

### Multi-Agent Parallel Solution

```
Single Session:
                    ORCHESTRATOR (Opus)
                         │
        ┌────────────────┼────────────────┐
        │                │                │
    Agent A          Agent B          Agent N
   (Sonnet)         (Sonnet)         (Sonnet)
        │                │                │
        └────────────────┼────────────────┘
                         │
                 SYNTHESIS (Opus)
                         │
                   Coherent Output

Benefits:
- Time: Hours (single session)
- Cost: Orchestrator + N × Sonnet (cheaper than N × Opus sessions)
- Context: 100% preserved (shared orchestrator)
- Coherence: Same context, same perspective
- Cross-pollination: Full (synthesis phase)
```

---

## When To Apply

### Ideal Conditions

| Condition | Why It Matters |
|-----------|----------------|
| Task has 3+ distinct facets | Justifies orchestration overhead |
| Facets are independent | Enables true parallel execution |
| Context preservation critical | Sequential would cause unacceptable loss |
| Synthesis adds value | Combining outputs creates emergent insight |
| Time pressure exists | Need results faster than sequential allows |

### Example Triggers

- "Create comprehensive documentation for 5 system components"
- "Analyze codebase from security, performance, and maintainability perspectives"
- "Generate implementation plans for multiple features"
- "Research and synthesize information across multiple domains"

### Anti-Triggers (Don't Use When)

- Task is simple/singular
- Facets have strict sequential dependencies
- Output from Agent A required as input for Agent B
- Cost is severely constrained (parallel uses more tokens than careful sequential)

---

## Implementation Steps

### Step 1: Decompose Task

```python
def decompose_task(complex_task: str) -> List[Facet]:
    """
    Break task into independent facets suitable for parallel processing.

    Criteria for valid facet:
    1. Can be analyzed independently
    2. Substantial enough to warrant dedicated agent
    3. Complementary to other facets (not duplicative)
    4. Has clear deliverable format
    """
    facets = identify_facets(complex_task)
    validate_independence(facets)
    return facets
```

### Step 2: Engineer Agent Prompts

Each agent needs:
1. **Shared context** - Project identity, methodology, goals
2. **Facet-specific context** - Current state, gaps, opportunities
3. **Clear directive** - What to produce, in what format
4. **Output structure** - Standardized for synthesis

```markdown
## Agent Prompt Template

You are a Claude agent analyzing [FACET] in a Claude + Human collaboration
project (codenamed "gemini-3-pro"). This project builds Claude-enhancing
tools using NLKE methodology.

**Current state of [FACET]:**
- Exists: [inventory]
- Gaps: [what's missing]
- Opportunities: [potential additions]

**Task:** [Specific directive]

For each suggestion:
1. Name and category
2. Problem it solves
3. Why needed NOW (gap analysis)
4. Synergy with existing system
5. Implementation complexity

**Output:** Structured markdown document
```

### Step 3: Launch Parallel Agents

In Claude Code, use multiple Task tool calls in a single message:

```
All Task tool invocations in one response = parallel execution
```

Configuration per agent:
- `model: "sonnet"` - Cost-effective for parallel work
- `subagent_type: "general-purpose"` - Full capability access
- `prompt: [facet-specific prompt with shared context]`

### Step 4: Collect and Analyze Results

Once all agents complete:
1. Gather all outputs
2. Identify cross-cutting themes
3. Map dependencies between facets
4. Detect synergies and conflicts
5. Log emergent insights

### Step 5: Synthesize

Create coherence document explaining:
- Why the N outputs form a system
- Dependency/implementation order
- Combined impact assessment
- Unified roadmap

---

## Cost Analysis

### Token Economics

| Approach | Tokens Used | Effective Cost |
|----------|-------------|----------------|
| 5 Sequential Opus Sessions | 5 × 100K = 500K | 5 × full context |
| 1 Orchestrated Session | 1 × 100K + 5 × 30K = 250K | 50% reduction |

### Time Economics

| Approach | Time Required |
|----------|---------------|
| 5 Sequential Sessions | 5 days (1/day) to 5 hours (1/hour) |
| 1 Orchestrated Session | 30-60 minutes |

### Context Economics

| Approach | Context Preserved |
|----------|-------------------|
| Sequential with Handoffs | ~50% (cumulative loss) |
| Parallel with Orchestrator | ~100% (shared context) |

---

## Validation Criteria

### Success Checklist

- [ ] All N agents completed without error
- [ ] Each agent produced structured output matching format
- [ ] Cross-cutting themes identified and documented
- [ ] Synthesis document explains coherence (not just concatenation)
- [ ] Emergent insights logged (target: 2+ per facet)
- [ ] Total time < N × sequential session time
- [ ] Pattern documented for reuse (this document)

### Quality Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Completion Rate | 100% | All agents finish |
| Output Consistency | High | Same format across agents |
| Cross-Reference | Present | Agents reference related facets |
| Synthesis Value | Significant | New insights in synthesis |
| Replicability | Demonstrated | Pattern can be reused |

---

## Real-World Validation

### Case Study: 25 Strategic Suggestions (November 27, 2025)

**Task:** Generate strategic suggestions for 5 ecosystem topics

**Execution:**
1. Decomposed into 5 facets: Templates, Playbooks, Tools, Agents, Workflows
2. Engineered 5 specialized prompts with shared project context
3. Launched 5 Sonnet agents in parallel via Task tool
4. Collected results and identified cross-cutting themes
5. Synthesized coherence document explaining connections

**Results:**
- 6 documents created (2,745 lines total)
- 25 suggestions with consistent structure
- 10 emergent insights logged (#212-221)
- Compression: 11 sessions → 1 session
- Context preservation: 100%

**Key Learning:** The synthesis phase revealed that all 25 suggestions converged on "operationalization" - a theme that wouldn't have emerged from sequential sessions.

---

## Anti-Patterns To Avoid

### 1. Sequential Fallback
**Problem:** Defaulting to "let me do A first, then B..."
**Solution:** Force parallel by putting all Task calls in one message

### 2. Minimal Agent Context
**Problem:** Each agent only gets facet-specific info
**Solution:** All agents get full project context + facet specifics

### 3. Concatenation Instead of Synthesis
**Problem:** Just joining agent outputs together
**Solution:** Create coherence narrative explaining connections

### 4. Skipping Insight Logging
**Problem:** Completing task without capturing learnings
**Solution:** Log insights at multiple phases (per-agent, cross-cutting, meta)

### 5. Not Crystallizing the Pattern
**Problem:** Using pattern without documenting it
**Solution:** This document exists because we used the pattern

---

## Integration Points

### Related Playbooks
- **Playbook 3** (Agent Development) - Agent architecture foundations
- **Playbook 7** (Fractal Agent) - Combination discovery patterns
- **Playbook 11** (Session Handoff) - When parallel isn't possible

### Related Templates
- **Template #26** (Multi-Agent Parallel Synthesis) - Structural blueprint
- **Session Handoff Template** - Fallback for sequential needs
- **Multi-Tool Workflow Template** - Tool-level composition

### Related Workflows
- **Workflow #5** (Multi-Agent Orchestration) - Execution patterns
- **Cross-Session Transfer** - Context preservation

### MCP Tool Integration
- `log_insight()` - Capture emergent patterns
- `log_evolution_event()` - Track pattern usage
- `persist_validated_fact()` - Store validated outputs

---

## Evolution Notes

### How This Pattern Emerged

1. **Problem observed:** Multi-session work causing context loss and incoherence
2. **Hypothesis:** Parallel agents with shared context could compress work
3. **Experiment:** 25 Strategic Suggestions task
4. **Validation:** 11:1 compression, 100% context preservation
5. **Crystallization:** This pattern document + Template #26

### Future Enhancements

- Automatic facet decomposition based on task analysis
- Dynamic agent count based on task complexity
- Cross-agent communication during execution
- Automated coherence scoring for synthesis

---

## Quick Reference

```yaml
Pattern: Multi-Agent Parallel Synthesis
When: Complex task with 3+ independent facets
Why: Compress time, preserve context, enable cross-pollination
How:
  1. Decompose task into facets
  2. Engineer agent prompts with shared context
  3. Launch N agents in parallel (single message)
  4. Collect results and identify themes
  5. Synthesize coherence document
Validation:
  - All agents complete
  - Cross-cutting themes identified
  - Synthesis explains coherence
  - Insights logged
  - Pattern documented
```

---

**Pattern Version:** 1.0
**Validated:** November 27, 2025
**Created By:** Eyal + Claude Opus 4.5
**Methodology:** NLKE v3.0 - Build WITH AI, Document AS you build

---

*"The best way to handle complex multi-faceted tasks is not to serialize them, but to parallelize them while maintaining shared context."*

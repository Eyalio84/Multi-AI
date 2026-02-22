# Playbook 8: Continuous Learning Loop
## Building Compound Intelligence Through Fact Persistence and Insight Accumulation

**Version:** 1.0
**Last Updated:** November 27, 2025
**Audience:** AI practitioners, knowledge workers, developers using Claude for extended projects
**Prerequisites:** Basic understanding of knowledge graphs, Claude API, MCP tools
**Related Playbooks:** Playbook 4 (Knowledge Engineering), Playbook 6 (Augmented Intelligence ML)

---

## Table of Contents

1. [Overview](#overview)
2. [The 5-Step Recursion Loop](#the-5-step-recursion-loop)
3. [Core Tools Reference](#core-tools-reference)
4. [Quality Gates](#quality-gates)
5. [Workflow Patterns](#workflow-patterns)
6. [Measuring Compound Growth](#measuring-compound-growth)
7. [Integration Patterns](#integration-patterns)
8. [Troubleshooting](#troubleshooting)
9. [Real-World Examples](#real-world-examples)
10. [Future: Local Model Integration](#future-local-model-integration)

---

## Overview

### What is Continuous Learning?

**Continuous Learning** in this context means building a system where:
- Knowledge **persists** across sessions
- Insights **compound** over time
- Quality is **validated** before persistence
- Growth is **measurable**

This is fundamentally different from how LLMs typically work (session-bounded, no persistent memory).

### The Problem with Session-Bounded AI

```
Session 1: Discover insight A
Session 2: Discover insight A again (no memory)
Session 3: Discover insight A again (no memory)
...
Result: Linear effort, no compound growth
```

### The Solution: Validated Persistence

```
Session 1: Discover insight A → validate → persist
Session 2: Retrieve A → build insight B (depends on A) → persist
Session 3: Retrieve A,B → build insight C (depends on A,B) → persist
...
Result: Exponential potential, compound growth
```

### Why "Validated" Matters

Not all AI outputs should be persisted:
- Opinions masquerading as facts
- Low-confidence statements
- Contradictory information
- Context-dependent statements presented as universal

**This playbook teaches you to persist ONLY validated knowledge.**

---

## The 5-Step Recursion Loop

### The Core Pattern

```
┌─────────────────────────────────────────────────────────┐
│                    RECURSION LOOP                       │
│                                                         │
│    ┌──────────┐     ┌──────────┐     ┌──────────┐      │
│    │ GENERATE │────▶│ EVALUATE │────▶│ PERSIST  │      │
│    └──────────┘     └──────────┘     └──────────┘      │
│         ▲                                  │           │
│         │                                  ▼           │
│    ┌──────────┐                      ┌──────────┐      │
│    │ BUILD ON │◀────────────────────│ RETRIEVE │      │
│    └──────────┘                      └──────────┘      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Step 1: GENERATE

Claude produces an insight, fact, or synthesis during normal work.

**Example:**
```
Working on: Code review for authentication module
Generated: "Session tokens should be rotated after privilege escalation"
```

### Step 2: EVALUATE

The generated statement is validated using metacognition tools.

**Tool:** `validate_fact(statement, evidence, domain)`

**Checks:**
- Is this actually a fact (not an opinion)?
- What's the confidence level?
- Is there supporting evidence?
- What domain does this belong to?

**Example:**
```python
result = validate_fact(
    statement="Session tokens should be rotated after privilege escalation",
    evidence="OWASP Session Management Cheat Sheet",
    domain="security"
)
# Returns: {is_fact: true, confidence: 0.92, issues: []}
```

### Step 3: PERSIST

If validation passes (confidence > 0.8), persist the fact.

**Tool:** `persist_validated_fact(fact, confidence, evidence, domain, builds_on)`

**Example:**
```python
result = persist_validated_fact(
    fact="Session tokens should be rotated after privilege escalation",
    confidence=0.92,
    evidence="OWASP Session Management Cheat Sheet",
    domain="security"
)
# Returns: {persisted: true, fact_id: 42, depth: 1}
```

### Step 4: RETRIEVE

In future sessions, retrieve relevant accumulated facts.

**Tool:** `retrieve_relevant_facts(query, k, min_confidence, domain)`

**Example:**
```python
facts = retrieve_relevant_facts(
    query="authentication security best practices",
    k=5,
    min_confidence=0.8,
    domain="security"
)
# Returns: [{fact: "Session tokens should be...", confidence: 0.92, ...}, ...]
```

### Step 5: BUILD ON

Use retrieved facts to generate deeper insights.

**The Key:** New insights can reference existing fact IDs via `builds_on` parameter.

**Example:**
```python
# New session discovers:
# "Given session rotation (fact_id: 42), we should also invalidate old tokens"

result = persist_validated_fact(
    fact="Old session tokens must be invalidated immediately upon rotation",
    confidence=0.95,
    evidence="Derived from fact_id:42 + OWASP guidelines",
    domain="security",
    builds_on=[42]  # Links to parent fact
)
# Returns: {persisted: true, fact_id: 43, depth: 2}
```

**Result:** Fact 43 has depth=2 because it builds on fact 42 (depth=1).

---

## Core Tools Reference

### Persistence Tools (Phase 7A)

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `persist_validated_fact` | Store validated fact | fact, confidence, evidence, domain, builds_on |
| `retrieve_relevant_facts` | Query accumulated facts | query, k, min_confidence, domain |

### Insight Tracking Tools (Phase 7B)

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `log_insight` | Record emergent insight | insight, builds_on, tags, auto_document |
| `analyze_recursion_depth` | Trace derivation chain | item_id, item_type |

### Evolution Tracking Tools (Phase 7C)

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `log_evolution_event` | Track system changes | component, change_type, description, metrics_before/after |
| `get_evolution_history` | Review change history | component, change_type, limit |

### Causal Relations (Phase 7D)

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `add_causal_relation` | Encode causality | cause_node, effect_node, relation_type, strength |
| `check_retrain_needed` | Check if embeddings need update | (no params) |

### Tool Usage Pattern

```python
# Session workflow
async def continuous_learning_session(topic: str):
    # 1. Retrieve existing knowledge
    existing = await retrieve_relevant_facts(query=topic, k=10)

    # 2. Work with Claude (generates new insights)
    # ... normal work happens here ...

    # 3. For each new insight:
    for insight in new_insights:
        # Validate first
        validation = await validate_fact(
            statement=insight.text,
            evidence=insight.source,
            domain=insight.domain
        )

        # Only persist if high confidence
        if validation['is_fact'] and validation['confidence'] > 0.8:
            await persist_validated_fact(
                fact=insight.text,
                confidence=validation['confidence'],
                evidence=insight.source,
                domain=insight.domain,
                builds_on=insight.parent_ids  # if any
            )

    # 4. Log session-level insights
    await log_insight(
        insight=f"Session on {topic} produced {len(new_insights)} validated facts",
        tags=[topic, "session_summary"]
    )
```

---

## Quality Gates

### The 0.8 Confidence Threshold

**Why 0.8?**
- Below 0.8: Too uncertain to treat as persistent fact
- Above 0.95: Rare, indicates well-established knowledge
- 0.8-0.95: The productive zone for new validated knowledge

**What affects confidence:**
- Explicit evidence increases confidence
- Opinion markers ("I think", "probably") decrease confidence
- Domain specificity increases confidence
- Verifiable claims score higher than abstract statements

### The 6-Layer Mud Detection

Before persisting, facts can be checked against 6 dimensions:

| Layer | What It Checks | Example Failure |
|-------|---------------|-----------------|
| **Base** | Is input actually a fact? | "I believe X is true" → Not a fact |
| **Texture** | Fact quality (smooth/rough/grainy) | Mixing statistics with absolutes |
| **Lighting** | Perspective/framing | Hidden assumptions or bias |
| **Composition** | Structural form | Missing premises in arguments |
| **Contrast** | Nuance preservation | False dichotomies |
| **Method** | Reasoning validity | Induction claimed as deduction |

**Usage:**
```python
# Full validation before persistence
result = detect_mud(
    inputs=["Statement A", "Statement B"],
    proposed_output="Combined conclusion"
)

if result['is_mud']:
    print(f"Invalid synthesis: {result['mud_sources']}")
else:
    # Safe to persist the synthesis
    persist_validated_fact(...)
```

### When to Skip Validation

Not every statement needs full validation:

| Scenario | Skip Validation? | Reason |
|----------|-----------------|--------|
| Documenting your own actions | Yes | Observation, not fact claim |
| Recording user preferences | Yes | Subjective, not truth claim |
| Noting a hypothesis for testing | Yes | Explicitly provisional |
| Claiming something is true | **No** | Needs validation |
| Building on previous facts | **No** | Chain quality matters |
| Synthesizing from multiple sources | **No** | Combination can introduce error |

---

## Workflow Patterns

### Pattern 1: Session Start

**Goal:** Prime context with relevant accumulated knowledge

```python
async def session_start(topic: str):
    # Retrieve relevant facts from previous sessions
    facts = await retrieve_relevant_facts(
        query=topic,
        k=10,
        min_confidence=0.8
    )

    # Format for context
    context = "Accumulated knowledge on this topic:\n"
    for fact in facts:
        context += f"- [{fact['confidence']:.0%}] {fact['fact']}\n"
        if fact.get('builds_on'):
            context += f"  (builds on fact IDs: {fact['builds_on']})\n"

    return context

# Example output:
# Accumulated knowledge on this topic:
# - [95%] Session tokens should be rotated after privilege escalation
# - [92%] Old tokens must be invalidated immediately (builds on: [42])
# - [88%] Token rotation should be logged for audit purposes
```

### Pattern 2: During Work (Continuous Capture)

**Goal:** Capture insights as they emerge, validate inline

```python
async def capture_insight(
    statement: str,
    context: str,
    parent_facts: List[int] = None
):
    # Quick validation
    validation = await validate_fact(
        statement=statement,
        evidence=context
    )

    if not validation['is_fact']:
        return {"status": "not_fact", "issues": validation['issues']}

    if validation['confidence'] < 0.8:
        return {"status": "low_confidence", "confidence": validation['confidence']}

    # Persist
    result = await persist_validated_fact(
        fact=statement,
        confidence=validation['confidence'],
        evidence=context,
        builds_on=parent_facts
    )

    return {
        "status": "persisted",
        "fact_id": result['fact_id'],
        "depth": result['depth']
    }
```

### Pattern 3: Session End (Summary + Handoff)

**Goal:** Capture session-level insights, prepare for next session

```python
async def session_end(
    session_topic: str,
    facts_created: List[int],
    key_learnings: List[str]
):
    # Log session summary
    summary_insight = f"""
    Session on '{session_topic}':
    - Created {len(facts_created)} new facts
    - Key learnings: {', '.join(key_learnings)}
    """

    await log_insight(
        insight=summary_insight,
        tags=[session_topic, "session_summary"],
        auto_document=True  # Appends to EMERGENT-INSIGHTS.md
    )

    # Check recursion growth
    if facts_created:
        for fact_id in facts_created:
            depth = await analyze_recursion_depth(item_id=fact_id, item_type="fact")
            if depth['depth'] > 3:
                print(f"Deep chain detected: Fact {fact_id} at depth {depth['depth']}")

    # Log evolution if significant changes
    if len(facts_created) > 5:
        await log_evolution_event(
            component="knowledge_base",
            change_type="addition",
            description=f"Added {len(facts_created)} facts on {session_topic}",
            metrics_before={"facts": get_fact_count() - len(facts_created)},
            metrics_after={"facts": get_fact_count()}
        )
```

### Pattern 4: Synthesis Workflow

**Goal:** Combine multiple facts into higher-order insight

```python
async def synthesize_facts(fact_ids: List[int], proposed_synthesis: str):
    # Retrieve the facts
    facts = [await get_fact_by_id(fid) for fid in fact_ids]

    # Check combinability
    for i, fact_a in enumerate(facts):
        for fact_b in facts[i+1:]:
            combinability = await check_combinability(
                fact_a=fact_a['fact'],
                fact_b=fact_b['fact'],
                proposed_synthesis=proposed_synthesis
            )
            if not combinability['combinable']:
                return {"error": f"Cannot combine: {combinability['risks']}"}

    # Detect potential mud
    mud_check = await detect_mud(
        inputs=[f['fact'] for f in facts],
        proposed_output=proposed_synthesis
    )

    if mud_check['is_mud']:
        return {"error": f"Synthesis produces mud: {mud_check['mud_sources']}"}

    # Perform synthesis
    synthesis_result = await synthesize(
        fact_a=facts[0]['fact'],
        fact_b=facts[1]['fact'] if len(facts) > 1 else facts[0]['fact'],
        synthesis_type="composition",  # or deduction, induction, analogy
        validation_ids=[f['fact_id'] for f in facts]
    )

    # Persist the synthesis
    if synthesis_result['confidence'] > 0.8 and not synthesis_result['is_mud']:
        await persist_validated_fact(
            fact=synthesis_result['synthesized_fact'],
            confidence=synthesis_result['confidence'],
            evidence=f"Synthesized from facts: {fact_ids}",
            builds_on=fact_ids
        )

    return synthesis_result
```

---

## Measuring Compound Growth

### Key Metrics

| Metric | What It Measures | Good Range |
|--------|-----------------|------------|
| **Facts per session** | Productivity | 3-10 validated facts |
| **Average confidence** | Quality | 0.85-0.95 |
| **Max recursion depth** | Compound growth | 3+ indicates building |
| **Facts retrieved vs created** | Learning vs discovering | Mix of both |

### Measuring Recursion Depth

```python
async def measure_compound_growth():
    # Get all facts
    all_facts = await retrieve_relevant_facts(query="*", k=1000, min_confidence=0.0)

    depths = []
    for fact in all_facts:
        if fact.get('fact_id'):
            depth_info = await analyze_recursion_depth(
                item_id=fact['fact_id'],
                item_type="fact"
            )
            depths.append(depth_info['depth'])

    return {
        "total_facts": len(all_facts),
        "max_depth": max(depths) if depths else 0,
        "avg_depth": sum(depths) / len(depths) if depths else 0,
        "depth_distribution": {d: depths.count(d) for d in set(depths)}
    }

# Example output:
# {
#   "total_facts": 187,
#   "max_depth": 5,
#   "avg_depth": 2.3,
#   "depth_distribution": {1: 50, 2: 80, 3: 40, 4: 12, 5: 5}
# }
```

### Interpretation

```
Depth 1: Root facts (no dependencies)
        → Foundation of knowledge base
        → Should be high-confidence, well-evidenced

Depth 2: First-order syntheses
        → Built on single root facts
        → The "obvious" derivations

Depth 3+: Higher-order insights
        → Built on multiple layers
        → These are where compound growth shows
        → Emergence of non-obvious connections

Depth 5+: Deep chains
        → Rare and valuable
        → Represents significant accumulated reasoning
        → Monitor for error propagation
```

### Growth Visualization

```
Session 1: ●●●●● (5 depth-1 facts)
Session 2: ●●●●● ○○○ (3 depth-2 facts building on session 1)
Session 3: ●●●●● ○○○ □□ (2 depth-3 facts)
Session 4: ●●●●● ○○○ □□ ◇ (1 depth-4 fact!)

● = depth 1  ○ = depth 2  □ = depth 3  ◇ = depth 4

Total: 11 facts, max depth 4
This shows healthy compound growth.
```

---

## Integration Patterns

### Integration with Knowledge Graph

```python
# Persist fact AND add to KG
async def persist_fact_to_kg(fact: str, confidence: float, domain: str, kg_node_type: str):
    # 1. Persist to metacognition system
    fact_result = await persist_validated_fact(
        fact=fact,
        confidence=confidence,
        domain=domain
    )

    # 2. Add corresponding node to KG
    await add_kg_node(
        node_id=f"fact_{fact_result['fact_id']}",
        node_type=kg_node_type,
        name=fact[:50],  # Truncate for node name
        properties={
            "full_text": fact,
            "confidence": confidence,
            "domain": domain,
            "metacog_fact_id": fact_result['fact_id']
        }
    )

    # 3. If builds_on, create KG edges
    if fact_result.get('builds_on'):
        for parent_id in fact_result['builds_on']:
            await add_kg_edge(
                source=f"fact_{parent_id}",
                target=f"fact_{fact_result['fact_id']}",
                edge_type="enables"
            )

    return fact_result
```

### Integration with Session Handoff

```python
# Generate handoff document with accumulated facts
async def generate_handoff(session_topic: str, next_tasks: List[str]):
    # Get session facts
    session_facts = await retrieve_relevant_facts(
        query=session_topic,
        k=20,
        min_confidence=0.8
    )

    # Get high-depth facts (compound insights)
    deep_facts = [f for f in session_facts if f.get('depth', 1) >= 3]

    # Build handoff
    handoff = f"""
# Session Handoff: {session_topic}

## Accumulated Knowledge ({len(session_facts)} facts)

### Deep Insights (depth 3+)
{format_facts(deep_facts)}

### Foundation Facts
{format_facts([f for f in session_facts if f.get('depth', 1) == 1])}

## Next Session Tasks
{format_tasks(next_tasks)}

## Suggested Starting Point
Retrieve facts with: `retrieve_relevant_facts(query="{next_tasks[0]}", k=10)`
"""

    return handoff
```

### Integration with Insight Logging

```python
# Auto-document insights to markdown
async def capture_emergent_insight(
    insight: str,
    context: str,
    parent_insights: List[int] = None
):
    # Log the insight
    result = await log_insight(
        insight=insight,
        builds_on=parent_insights,
        tags=extract_tags(insight),
        auto_document=True,  # Appends to EMERGENT-INSIGHTS.md
        document_source=context
    )

    # Also persist as fact if factual
    validation = await validate_fact(statement=insight)
    if validation['is_fact'] and validation['confidence'] > 0.8:
        await persist_validated_fact(
            fact=insight,
            confidence=validation['confidence'],
            evidence=context,
            builds_on=parent_insights
        )

    return result
```

---

## Troubleshooting

### Issue: Facts Not Being Retrieved

**Symptoms:** `retrieve_relevant_facts` returns empty or irrelevant results

**Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| Query too specific | Broaden query terms |
| Domain mismatch | Check domain parameter matches persisted facts |
| Confidence threshold too high | Lower min_confidence (try 0.7) |
| No facts persisted yet | Check persist_validated_fact was called |

**Debug:**
```python
# Check what's in the fact store
all_facts = await retrieve_relevant_facts(query="*", k=100, min_confidence=0.0)
print(f"Total facts: {len(all_facts)}")
for f in all_facts[:5]:
    print(f"- {f['fact'][:50]}... (conf: {f['confidence']}, domain: {f.get('domain')})")
```

### Issue: Validation Always Failing

**Symptoms:** validate_fact returns is_fact=False for reasonable statements

**Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| Opinion markers in statement | Remove "I think", "probably", etc. |
| Statement too vague | Make more specific and verifiable |
| Missing evidence | Provide evidence parameter |
| Statement is actually opinion | That's correct behavior! |

**Debug:**
```python
result = await validate_fact(statement="Your statement", evidence="Supporting source")
print(f"Is fact: {result['is_fact']}")
print(f"Confidence: {result['confidence']}")
print(f"Issues: {result['issues']}")  # This tells you what's wrong
```

### Issue: Mud Detection Blocking Everything

**Symptoms:** detect_mud returns is_mud=True for reasonable syntheses

**Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| Mixing incompatible textures | Use texture bridging first |
| Conflicting perspectives | Acknowledge perspectives explicitly |
| Method mismatch | Ensure reasoning methods are compatible |
| False dichotomy | Use spectrum instead of binary |

**Debug:**
```python
# Check each layer individually
texture_a = await assess_texture(fact_a)
texture_b = await assess_texture(fact_b)
compatibility = await texture_compatibility(fact_a, fact_b)
print(f"Texture A: {texture_a['texture']}")
print(f"Texture B: {texture_b['texture']}")
print(f"Compatible: {compatibility['compatible']}")
print(f"Needs bridging: {compatibility['bridging_needed']}")
```

### Issue: Low Recursion Depth

**Symptoms:** All facts at depth 1, no compound growth

**Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| Not using builds_on | Reference parent fact IDs |
| Isolated facts | Look for connections between facts |
| Not retrieving before persisting | Always retrieve relevant facts first |

**Fix Pattern:**
```python
# Before persisting, check for related facts
related = await retrieve_relevant_facts(query=new_fact_text, k=5)

# If related facts exist, build on them
if related:
    parent_ids = [f['fact_id'] for f in related if f['confidence'] > 0.8]
    await persist_validated_fact(
        fact=new_fact_text,
        confidence=confidence,
        builds_on=parent_ids  # This increases depth
    )
```

---

## Real-World Examples

### Example 1: Building Security Knowledge Base

**Session 1:**
```python
# Root facts (depth 1)
await persist_validated_fact(
    fact="SQL injection occurs when user input is concatenated into queries",
    confidence=0.95,
    evidence="OWASP Top 10",
    domain="security"
)  # fact_id: 1

await persist_validated_fact(
    fact="Parameterized queries prevent SQL injection",
    confidence=0.98,
    evidence="OWASP Prevention Cheat Sheet",
    domain="security"
)  # fact_id: 2
```

**Session 2:**
```python
# Retrieve and build (depth 2)
related = await retrieve_relevant_facts(query="SQL injection prevention")

await persist_validated_fact(
    fact="ORMs that use parameterized queries by default are safer than raw SQL",
    confidence=0.90,
    evidence="Synthesis of facts 1,2 + ORM documentation",
    domain="security",
    builds_on=[1, 2]
)  # fact_id: 3, depth: 2
```

**Session 3:**
```python
# Higher-order synthesis (depth 3)
await persist_validated_fact(
    fact="Modern frameworks with built-in ORM should be preferred for security-critical applications",
    confidence=0.85,
    evidence="Synthesis of fact 3 + framework security audits",
    domain="security",
    builds_on=[3]
)  # fact_id: 4, depth: 3
```

**Result:** 4 facts, max depth 3, clear derivation chain.

### Example 2: Our System (187+ Insights in 48 Hours)

**How we achieved 187+ insights in 48 hours:**

1. **Started with foundations:**
   - IA paradigm documentation
   - NLKE methodology
   - KG structure decisions

2. **Each session built on previous:**
   - Session 1: Basic KG → Insight about embeddings
   - Session 2: Embedding insight → Hybrid search approach
   - Session 3: Hybrid search → 88.5% recall achievement
   - Session 4: Achievement → Methodology documentation

3. **Logged everything:**
   - Used log_insight() for all discoveries
   - Tracked builds_on relationships
   - Measured recursion depth

4. **Key insight example:**
   ```
   Insight #153: The 5-step recursion loop
   - builds_on: Insights about persistence, validation, retrieval
   - depth: 4
   - This insight ABOUT the system was discovered BY the system
   ```

### Example 3: Cost Tracking Across Sessions

**Session 1:**
```python
await persist_validated_fact(
    fact="Prompt caching saves 90% on tokens with cache_control: ephemeral",
    confidence=0.95,
    evidence="Anthropic documentation + our tests",
    domain="api_cost"
)  # fact_id: 101
```

**Session 2:**
```python
await persist_validated_fact(
    fact="Batch API saves 50% on async workloads",
    confidence=0.95,
    evidence="Anthropic documentation",
    domain="api_cost"
)  # fact_id: 102
```

**Session 3:**
```python
# Compound insight
await persist_validated_fact(
    fact="Combining prompt caching + batch API achieves 95% cost savings",
    confidence=0.92,
    evidence="Calculated: 1 - (0.1 * 0.5) = 0.95, validated in playbooks",
    domain="api_cost",
    builds_on=[101, 102]
)  # fact_id: 103, depth: 2
```

---

## Future: Local Model Integration

### Why Local Model Changes Everything

| API-Based | Local Model |
|-----------|-------------|
| Session-bounded | Persistent state |
| Pay per query | Unlimited queries |
| No fine-tuning | Domain adaptation |
| External dependency | Offline operation |

### The Vision: True Continuous Learning

```
Day 1: Local model validates facts → persists to KG
Day 2: Retrieves accumulated facts → richer context
Day 3: Fine-tune on validated syntheses (LoRA)
Day 4: Model is BETTER at this domain
...repeat...
```

### Prerequisites (When RTX 3060 Arrives)

1. **Ollama + Mistral 7B** for local inference
2. **MCP bridge** to connect local model to tools
3. **Fine-tuning pipeline** (Axolotl/Unsloth)
4. **Validation corpus** from accumulated facts

### Placeholder Architecture

```python
# Future: continuous_learning.py (placeholder)

class ContinuousLearner:
    def __init__(self, local_model, metacog_tools, fact_store):
        self.model = local_model
        self.tools = metacog_tools
        self.facts = fact_store

    async def run_loop(self):
        while True:
            # 1. Check for new inputs
            inputs = await self.get_pending_inputs()

            # 2. Process with local model
            for input in inputs:
                result = await self.model.process(input)

                # 3. Validate with metacognition
                if await self.validate(result):
                    # 4. Persist
                    await self.persist(result)

            # 5. Sleep and repeat
            await asyncio.sleep(60)

    async def maybe_fine_tune(self):
        # Check if enough new facts accumulated
        if await self.tools.check_retrain_needed():
            # Collect high-confidence facts
            training_data = await self.collect_training_data()
            # Fine-tune local model
            await self.fine_tune(training_data)
```

---

## Summary

### Key Takeaways

1. **The 5-Step Loop**: Generate → Evaluate → Persist → Retrieve → Build
2. **Quality Gates**: 0.8 confidence threshold, 6-layer mud detection
3. **Compound Growth**: Measure via recursion depth (depth 3+ is good)
4. **Integration**: Connect to KG, handoffs, insight logging
5. **Future**: Local model enables true continuous learning

### Quick Start Checklist

- [ ] Understand the 5-step recursion loop
- [ ] Use `validate_fact()` before persisting
- [ ] Use `builds_on` parameter to track derivations
- [ ] Start sessions with `retrieve_relevant_facts()`
- [ ] End sessions with `log_insight()` summary
- [ ] Monitor recursion depth for compound growth

### The Bottom Line

**Without continuous learning:**
- Every session starts from zero
- No compound growth
- Linear effort, linear results

**With continuous learning:**
- Sessions build on each other
- Knowledge compounds over time
- Exponential potential, measured growth

---

## Additional Resources

**See Also (Playbooks):**
- **[Playbook 4: Knowledge Engineering](PLAYBOOK-4-KNOWLEDGE-ENGINEERING.md)** - Entity extraction, KG construction
- **[Playbook 6: Augmented Intelligence ML](PLAYBOOK-6-AUGMENTED-INTELLIGENCE-ML.md)** - SRAIS methodology
- **[Playbook 9: Metacognition Workflows](PLAYBOOK-9-METACOGNITION-WORKFLOWS.md)** - Validated reasoning
- **[Playbook 11: Session Handoff Protocol](PLAYBOOK-11-SESSION-HANDOFF-PROTOCOL.md)** - Knowledge transfer

**Core Documentation:**
- `docs/RECURSIVE-INTELLIGENCE-EXPLAINED.md`
- `docs/MCP-AS-CONTINUAL-LEARNING-BRIDGE.md`
- `nlke_mcp/tools/metacognition.py` (implementation)

**MCP Tools Reference:**
- `nlke_mcp/servers/nlke_metacognition_server.py`
- 35 tools across 7 phases

---

**Playbook Version:** 1.0
**Last Updated:** November 27, 2025
**Created By:** Eyal + Claude Opus 4.5
**Methodology:** NLKE v3.0 - Build WITH AI, Document AS you build

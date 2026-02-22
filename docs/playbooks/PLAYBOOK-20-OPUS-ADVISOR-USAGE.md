# PLAYBOOK-18: Opus 4.5 Advisor - Usage Guide

**Purpose**: Practical guide for Sonnet to effectively use the Opus Advisor pattern
**Prerequisite**: PLAYBOOK-17 (Opus Advisor Pattern)
**Created**: November 27, 2025

---

## The Core Principle

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   "Eat the cake and keep it whole"                         │
│                                                             │
│   Sonnet handles 90% of work (volume, iteration, speed)    │
│   Opus handles 10% of work (strategy, review, validation)  │
│                                                             │
│   Result: 95%+ quality with 3-4x weekly limit extension    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Start for Sonnet

### Step 1: Recognize When to Call Opus

**ALWAYS call Opus for:**
- Architecture decisions (>5 files affected)
- Security-sensitive code
- After 3+ failed debug attempts
- User explicitly requests "ask Opus" or "get Opus opinion"

**CONSIDER calling Opus for:**
- Complex refactoring
- Multi-phase planning
- Performance-critical paths
- Uncertain synthesis (confidence <80%)

**DON'T call Opus for:**
- File reads/writes
- Simple edits
- Standard patterns
- Documentation
- Routine bug fixes

### Step 2: Use the Right Slash Command

```bash
/opus-review    # "Review my plan/code/approach"
/opus-plan      # "Create a strategic plan for..."
/opus-debug     # "Help debug this after my attempts failed"
/opus-architecture  # "Which approach should we use?"
/opus-validate  # "Validate this reasoning chain"
```

### Step 3: Or Call Directly via Task Tool

```python
Task(
    subagent_type="general-purpose",
    model="opus",
    prompt="""
    OPUS ADVISOR REQUEST: [Type]

    ## Context
    [Relevant background]

    ## Specific Request
    [What you need from Opus]

    ## Constraints
    [Any limitations]
    """
)
```

---

## Workflow: The Sonnet-Opus Dance

### Phase 1: Sonnet Explores
```
User Request
    │
    ▼
Sonnet: Read files, explore codebase
Sonnet: Understand requirements
Sonnet: Identify complexity level
    │
    ▼
Decision: Is this complex enough for Opus?
    │
    ├─ No  → Sonnet proceeds alone
    │
    └─ Yes → Continue to Phase 2
```

### Phase 2: Sonnet Prepares
```
Sonnet: Draft initial plan
Sonnet: Use meta-cognition tools
    │
    ├─ validate_fact() on key claims
    ├─ detect_mud() on synthesis
    └─ want_to() for existing patterns
    │
    ▼
Sonnet: Format Opus request using template
```

### Phase 3: Opus Reviews
```
Sonnet → Task(model="opus", prompt=request)
    │
    ▼
Opus: Extended thinking analysis
Opus: Returns structured feedback
    │
    ▼
Sonnet: Receives enhanced plan/validation
```

### Phase 4: Sonnet Implements
```
Sonnet: Incorporate Opus feedback
Sonnet: Execute enhanced plan
Sonnet: Iterate without further Opus calls
    │
    ▼
(Only call Opus again if major blocker)
```

### Phase 5: Sonnet Persists
```
Sonnet: Complete implementation
Sonnet: Log valuable insights
    │
    ├─ log_insight() for methodology
    ├─ persist_validated_fact() for facts
    └─ log_evolution_event() if system changed
```

---

## Template Selection Guide

| You Need To... | Use Template | Slash Command |
|---------------|--------------|---------------|
| Verify a plan before implementing | Review | `/opus-review` |
| Create a plan for complex task | Plan | `/opus-plan` |
| Fix a bug that won't go away | Debug | `/opus-debug` |
| Choose between approaches | Architecture | `/opus-architecture` |
| Check if reasoning is sound | Validate | `/opus-validate` |

---

## Prompt Crafting Tips

### DO:
- Provide full context (Opus doesn't have conversation history)
- Include what you've already tried
- State your confidence level
- List specific questions
- Mention constraints

### DON'T:
- Send vague requests ("review this")
- Omit relevant code/logs
- Skip your own analysis
- Ask multiple unrelated questions
- Forget to mention user requirements

### Example - Good Request:
```markdown
OPUS ADVISOR REQUEST: Architecture Decision

## Context
Building authentication for a FastAPI backend.
Currently have 12 endpoints, expect 50+ at scale.
User wants minimal dependencies.

## Options I've Identified
1. JWT tokens - stateless, scalable
2. Session cookies - simpler, established
3. OAuth2 with refresh - industry standard

## My Lean
JWT seems right for scalability, but user mentioned
"minimal dependencies" which might favor sessions.

## Questions
1. Which approach for this specific context?
2. Security considerations I might be missing?
3. Implementation gotchas?
```

### Example - Bad Request:
```markdown
Which auth should I use?
```

---

## Handling Opus Responses

### If APPROVE:
```
Sonnet: "Opus validated the approach. Proceeding with implementation."
[Execute plan as-is]
```

### If REVISE:
```
Sonnet: "Opus suggested improvements. Key changes:
- [Change 1]
- [Change 2]
Incorporating these into the plan."
[Modify and proceed]
```

### If REJECT:
```
Sonnet: "Opus identified fundamental issues:
- [Issue 1]
- [Issue 2]
Let me rethink the approach."
[Draft new plan, optionally re-validate with Opus]
```

---

## Integration with Meta-Cognition

### Pre-Opus Checklist
Before calling Opus, Sonnet should:

1. **Self-validate** with meta-cognition tools
   ```python
   # Am I making valid claims?
   validate_fact("key claim about the system")

   # Is my synthesis sound?
   detect_mud(["fact A", "fact B"], "my conclusion")

   # Does a pattern already exist?
   want_to("what I'm trying to achieve")
   ```

2. **Check if Opus is really needed**
   - Is confidence >80%? Maybe proceed without Opus
   - Is there a KG pattern? Use it instead
   - Is it routine work? Don't waste Opus call

### Post-Opus Persistence
After receiving Opus feedback:

```python
# Novel methodology insight
log_insight(
    insight="Opus revealed that...",
    tags=["opus-feedback", "architecture"],
    builds_on=[previous_insight_ids]
)

# Verified fact worth keeping
persist_validated_fact(
    fact="Opus confirmed that JWT is optimal for...",
    confidence=0.95,
    domain="architecture"
)

# System change worth tracking
log_evolution_event(
    component="auth_system",
    change_type="addition",
    description="Added JWT auth per Opus recommendation"
)
```

---

## Cost-Benefit Tracking

### Per-Session Metrics
Track these to validate the pattern:

| Metric | Target | Your Session |
|--------|--------|--------------|
| Opus calls made | < 3 | ___ |
| Issues Opus caught | Record them | ___ |
| Plans revised after Opus | < 20% | ___ |
| Insight depth achieved | > 5 | ___ |

### Weekly Metrics
| Metric | Without Pattern | With Pattern |
|--------|-----------------|--------------|
| Days to limit | 3-4 | 7+ |
| Quality degradation | N/A | < 5% |
| Major issues caught | Variable | > 80% |

---

## Common Scenarios

### Scenario 1: New Feature Request
```
User: "Add dark mode to the app"

Sonnet:
1. Explore codebase (find styling patterns)
2. Draft plan (5 steps identified)
3. Check complexity → Medium, multiple files
4. Call /opus-review with plan
5. Opus: "Consider CSS variables for theming"
6. Implement enhanced plan
7. Done - 1 Opus call total
```

### Scenario 2: Persistent Bug
```
User: "The API keeps timing out"

Sonnet:
1. Read logs, check code
2. Try fix #1 (increase timeout) → Still fails
3. Try fix #2 (connection pooling) → Still fails
4. Try fix #3 (async refactor) → Still fails
5. Call /opus-debug with all attempts
6. Opus: "Race condition in middleware"
7. Fix the actual issue
8. Done - 1 Opus call after 3 attempts
```

### Scenario 3: Architecture Choice
```
User: "Should we use Redis or PostgreSQL for caching?"

Sonnet:
1. Understand requirements
2. List pros/cons for each
3. Call /opus-architecture
4. Opus: "PostgreSQL UNLOGGED tables given your constraint"
5. Present recommendation to user
6. Done - 1 Opus call for critical decision
```

---

## Anti-Patterns to Avoid

### 1. Over-calling Opus
**Bad**: Calling Opus for every small decision
**Good**: Batch questions, call once for strategic review

### 2. Under-preparing requests
**Bad**: "Should I do X?"
**Good**: Full context + options + your analysis + specific questions

### 3. Ignoring Opus feedback
**Bad**: Getting REVISE but proceeding with original plan
**Good**: Actually incorporate the feedback

### 4. Not persisting insights
**Bad**: Getting great Opus insight, then forgetting it
**Good**: log_insight() immediately after valuable feedback

### 5. Skipping self-validation
**Bad**: Calling Opus before trying meta-cognition tools
**Good**: validate_fact() and detect_mud() first

---

## Troubleshooting

### "Opus response seems generic"
- Add more specific context
- Include actual code/logs
- Ask pointed questions

### "Not sure which template to use"
- Review → checking something you made
- Plan → creating something new
- Debug → fixing something broken
- Architecture → choosing between options
- Validate → verifying reasoning

### "Opus call seems wasteful for this"
- Trust that feeling - proceed without Opus
- Use meta-cognition tools instead
- Only escalate if truly stuck

---

## Summary: The 5 Rules

1. **Self-validate first** - Use meta-cognition before Opus
2. **Prepare thoroughly** - Context, options, questions
3. **Call sparingly** - Target <3 Opus calls per session
4. **Integrate fully** - Actually use the feedback
5. **Persist always** - Log insights after every Opus call

---

*PLAYBOOK-18: Opus 4.5 Advisor Usage Guide*
*Companion to PLAYBOOK-17 (Pattern) and Template*
*Part of NLKE Model Cascading System*

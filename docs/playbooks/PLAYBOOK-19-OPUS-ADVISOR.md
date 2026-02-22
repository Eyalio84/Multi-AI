# PLAYBOOK-17: Opus 4.5 Advisor Pattern

**Purpose**: Maximize reasoning quality while minimizing Opus 4.5 usage through strategic model cascading.

**Problem Solved**: Weekly Opus limits reached too quickly when using Opus for all tasks.

**Solution**: Sonnet handles volume work, Opus provides strategic review at key decision points.

---

## The Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                    SONNET (Main Model)                       │
│                                                              │
│   Explore ──► Plan ──► Draft ──► Implement ──► Iterate      │
│                  │                    │                      │
│                  ▼                    ▼                      │
│            ┌─────────────────────────────────────┐          │
│            │       OPUS 4.5 ADVISOR              │          │
│            │  (Task tool with model="opus")      │          │
│            │                                     │          │
│            │  • Strategic review                 │          │
│            │  • Architecture decisions           │          │
│            │  • Complex reasoning validation     │          │
│            │  • Enhanced extended thinking       │          │
│            └─────────────────────────────────────┘          │
│                  │                    │                      │
│                  ▼                    ▼                      │
│           Enhanced Plan ──────► Refined Implementation      │
└─────────────────────────────────────────────────────────────┘
```

---

## When to Call Opus Advisor

### HIGH VALUE (Always worth it)
- **Architecture decisions** - System design, pattern selection
- **Complex planning** - Multi-phase projects, dependency ordering
- **Risk assessment** - Security review, edge case analysis
- **Synthesis validation** - When combining multiple complex concepts

### MEDIUM VALUE (Consider)
- **Debugging complex issues** - After Sonnet attempts fail
- **Performance optimization** - Algorithm selection, bottleneck analysis
- **Code review** - Critical paths, security-sensitive code

### LOW VALUE (Sonnet sufficient)
- **Routine implementation** - CRUD, standard patterns
- **File operations** - Search, read, edit
- **Documentation** - READMEs, comments
- **Simple fixes** - Typos, formatting, minor bugs

---

## Implementation

### Method 1: Direct Task Call

```python
# Sonnet calls Opus for plan review
Task(
    subagent_type="general-purpose",
    model="opus",
    prompt="""
    OPUS ADVISOR REQUEST: Plan Review

    ## Context
    [Describe the project/problem]

    ## Current Plan
    [The plan Sonnet drafted]

    ## Questions for Opus
    1. Are there architectural concerns I'm missing?
    2. What edge cases should I handle?
    3. Is this the optimal approach, or is there a better pattern?

    ## Constraints
    - [Time/resource constraints]
    - [Technical constraints]

    Please provide:
    1. Critical issues (must fix)
    2. Recommendations (should consider)
    3. Enhanced plan (if significantly different)
    """
)
```

### Method 2: Slash Commands (Recommended)

Use the pre-built slash commands:

```
/opus-review [plan/code/approach]
/opus-plan [complex problem]
/opus-debug [issue after Sonnet attempts failed]
/opus-architecture [system design question]
```

### Method 3: Explicit User Request

User can always request:
```
"Ask Opus to review this plan before implementing"
"Get Opus's opinion on this architecture"
"Have Opus validate my reasoning chain"
```

---

## Prompt Templates for Opus Advisor

### Template 1: Plan Review

```markdown
# OPUS ADVISOR: Plan Review

## Project Context
{brief_description}

## Sonnet's Proposed Plan
{numbered_steps}

## Specific Questions
1. {question_1}
2. {question_2}

## Request
Analyze this plan using extended thinking. Identify:
- Critical gaps or risks
- Optimization opportunities
- Better alternative approaches (if any)

Provide a clear APPROVE / REVISE / REJECT recommendation with reasoning.
```

### Template 2: Architecture Decision

```markdown
# OPUS ADVISOR: Architecture Decision

## Problem
{what_we_need_to_build}

## Options Identified by Sonnet
1. {option_1}: {pros/cons}
2. {option_2}: {pros/cons}
3. {option_3}: {pros/cons}

## Constraints
- {constraint_1}
- {constraint_2}

## Request
Use extended thinking to analyze trade-offs. Recommend the optimal approach with:
- Clear recommendation
- Reasoning chain
- Implementation considerations
- Potential pitfalls to avoid
```

### Template 3: Complex Debugging

```markdown
# OPUS ADVISOR: Debug Assistance

## Problem
{description_of_issue}

## What Sonnet Tried
1. {attempt_1} - Result: {result}
2. {attempt_2} - Result: {result}

## Relevant Code/Logs
```
{code_or_logs}
```

## Request
Apply deep reasoning to identify root cause. Consider:
- Non-obvious failure modes
- System interactions
- Race conditions / timing issues
- Environmental factors
```

### Template 4: Reasoning Validation

```markdown
# OPUS ADVISOR: Reasoning Validation

## Sonnet's Reasoning Chain
Fact A: {fact_a}
Fact B: {fact_b}
Synthesis: {conclusion}

## Confidence Level
Sonnet's confidence: {X}%

## Request
Validate this reasoning chain:
1. Are the input facts accurate?
2. Is the synthesis logically valid?
3. What assumptions are being made?
4. What's the actual confidence level?

Use our meta-cognition framework (texture, lighting, composition, contrast, method).
```

---

## Cost-Benefit Analysis

### Without Pattern (Pure Opus)
- All tasks use Opus
- Weekly limit hit in ~3-4 days
- 100% of reasoning is Opus-quality

### With Pattern (Sonnet + Opus Advisor)
- 90% tasks use Sonnet (fast, cheap)
- 10% strategic calls to Opus (enhanced)
- Weekly limit extends to full week+
- 95%+ of outcomes match pure Opus quality

### Why 95%+ Quality is Maintained
1. **Sonnet is highly capable** for most tasks
2. **Opus reviews catch critical issues** before they compound
3. **Our NLKE system provides structure** that reduces need for raw reasoning
4. **Meta-cognition tools validate** reasoning quality programmatically

---

## Integration with NLKE System

### Before Calling Opus, Sonnet Should:

1. **Use meta-cognition tools** to validate own reasoning
   ```python
   validate_fact(statement)
   detect_mud(inputs, proposed_output)
   assess_method(reasoning)
   ```

2. **Check the KG** for existing patterns
   ```python
   want_to(goal)
   compose_for(complex_task)
   ```

3. **Only escalate to Opus when**:
   - Meta-cognition flags uncertainty
   - No clear pattern in KG
   - High-stakes decision point
   - User explicitly requests

### After Opus Response:

1. **Persist valuable insights**
   ```python
   persist_validated_fact(opus_insight, confidence=0.95)
   log_insight(opus_recommendation)
   ```

2. **Update KG if new pattern discovered**

3. **Document for future reference**

---

## Example Workflow

### Scenario: Implement New Feature

```
1. USER: "Add authentication to the API"

2. SONNET:
   - Explores codebase (Task: Explore)
   - Drafts implementation plan
   - Uses meta-cognition to validate plan
   - Confidence: 75% (complex feature)

3. SONNET → OPUS ADVISOR:
   Task(model="opus", prompt="""
   Review this authentication implementation plan:
   [plan details]

   Concerns:
   - Security implications
   - Session management approach
   - Integration with existing middleware
   """)

4. OPUS RETURNS:
   - "Plan is solid, but add rate limiting"
   - "Consider JWT over sessions for scalability"
   - "Add CSRF protection to forms"

5. SONNET:
   - Incorporates Opus feedback
   - Implements enhanced plan
   - Iterates without further Opus calls

6. RESULT:
   - Opus-quality architecture (1 call)
   - Sonnet-speed implementation (many calls)
   - Weekly limit preserved
```

---

## Metrics & Monitoring

Track to validate pattern effectiveness:

| Metric | Target |
|--------|--------|
| Opus calls per session | < 3 |
| Issues caught by Opus review | > 80% of critical |
| Plan revision rate after Opus | < 20% |
| Weekly limit utilization | Full week coverage |

---

## Related Playbooks

- **PLAYBOOK-2**: Extended Thinking (Opus uses this internally)
- **PLAYBOOK-3**: Agent Development (Task tool patterns)
- **PLAYBOOK-8**: Continuous Learning (persist Opus insights)

---

## Slash Commands Reference

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `/opus-review` | Review plan/code/approach | Before major implementation |
| `/opus-plan` | Generate strategic plan | Complex multi-step tasks |
| `/opus-debug` | Deep debugging | After Sonnet attempts fail |
| `/opus-architecture` | Architecture decision | System design choices |
| `/opus-validate` | Validate reasoning chain | Uncertain synthesis |

---

*PLAYBOOK-17: Opus 4.5 Advisor Pattern*
*Created: November 27, 2025*
*Part of NLKE Model Cascading Strategy*

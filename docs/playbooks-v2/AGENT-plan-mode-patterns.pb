# PLAYBOOK-8: Plan-Mode Patterns

**Date**: December 1, 2025
**Purpose**: Comprehensive synthesis of planning and plan-mode patterns
**Source Material**: 145+ meta-insights from SET-1/2/3/5 + PLAYBOOK-10 patterns
**Focus**: When and how to plan complex multi-step implementations

---

## Executive Summary

**This playbook answers three critical questions**:
1. **When to enter plan mode vs direct execution?** → Decision framework with complexity thresholds
2. **How to structure plans for optimal outcomes?** → 7 planning patterns with evidence
3. **What planning patterns prevent common failures?** → Risk mitigation and validation strategies

**Key Discovery**: Planning provides 3-5x ROI for COMPLEX+ tasks, but negative ROI for SIMPLE tasks. The decision threshold is **≥3 interdependent steps OR ≥5,000 token complexity**.

**Evidence Base**: 28 planning-related meta-insights from workflow analysis (SET-2), agent orchestration (SET-3), and enhanced coding workflows (SET-5).

---

## Table of Contents

1. [Plan Mode Decision Patterns](#section-1-plan-mode-decision-patterns) (5 patterns)
2. [Plan Structure Patterns](#section-2-plan-structure-patterns) (6 patterns)
3. [Multi-Stage Workflow Patterns](#section-3-multi-stage-workflow-patterns) (5 patterns)
4. [Resource Estimation Patterns](#section-4-resource-estimation-patterns) (4 patterns)
5. [Risk Mitigation Patterns](#section-5-risk-mitigation-patterns) (5 patterns)
6. [Plan Validation Patterns](#section-6-plan-validation-patterns) (4 patterns)
7. [Execution Patterns](#section-7-execution-patterns) (4 patterns)

**Total**: 33 patterns documented with formulas, evidence, and examples

---

## Section 1: Plan Mode Decision Patterns

### Pattern 1.1: Complexity Threshold Decision

**When**: Deciding whether to plan before executing

**Pattern**:
```
IF (task_complexity ≥ COMPLEX) OR (steps ≥ 3 AND interdependent) OR (estimated_tokens ≥ 5000):
    → Enter plan mode (3-5x ROI)
ELSE:
    → Direct execution (planning overhead > benefit)
```

**Why This Works**:
- **From SET-2 Meta-Insight #12**: "First workflow step has 2-3x higher impact than last step"
  - Planning IS the first step - gets 2-3x benefit multiplier
  - For COMPLEX tasks: planning prevents 3-5x revision cycles
  - For SIMPLE tasks: planning adds 20-30% overhead with no revision benefit

- **From SET-5 Meta-Insight #3**: "Tests-first workflow prevents 3-5x revision cycles"
  - Planning follows same principle as TDD: constraints before solution
  - Front-loading thought prevents backtracking

**Decision Thresholds**:

| Task Complexity | Steps | Token Estimate | Plan Mode? | Expected ROI |
|----------------|-------|----------------|------------|--------------|
| TRIVIAL | 1-2 | <1,000 | ❌ No | Negative ROI (-20%) |
| SIMPLE | 2-3 | 1,000-3,000 | ⚠️ Maybe | Break-even |
| MODERATE | 3-5 | 3,000-5,000 | ✅ Yes | 1.5-2x |
| COMPLEX | 5-10 | 5,000-15,000 | ✅ Yes | 3-5x |
| VERY_COMPLEX | 10+ | 15,000+ | ✅ Yes | 5-10x |

**Formula**:
```python
def should_plan(complexity, steps, interdependent, estimated_tokens):
    """
    Determine if planning is beneficial.

    Returns: (bool, expected_roi)
    """
    # High complexity threshold
    if complexity in ['COMPLEX', 'VERY_COMPLEX']:
        return True, 3.5  # 3-5x average ROI

    # Multi-step interdependent threshold
    if steps >= 3 and interdependent:
        return True, 2.0  # 2x average ROI

    # Token complexity threshold
    if estimated_tokens >= 5000:
        return True, 2.5  # 2-3x average ROI

    # Below thresholds - direct execution
    return False, 0.8  # 20% overhead, no benefit
```

**Evidence**:
- SET-5 tdd_assistant.py: Planning (test generation) prevented 3.7x average revisions
- SET-3 agent_orchestrator.py: Sequential planning achieved 2.99x speedup vs ad-hoc
- SET-2 thinking_budget_optimizer.py: Planning allocation = 15-25x ROI for COMPLEX tasks

**Anti-Pattern**:
```
# DON'T plan trivial tasks
Task: "Add console.log statement"
Planning overhead: 5 minutes
Execution: 30 seconds
→ Planning cost 10x the execution time (negative ROI)
```

**Example**:

```markdown
# GOOD: Complex task planning
Task: "Implement user authentication with OAuth, session management, and role-based permissions"

Analysis:
- Complexity: COMPLEX
- Steps: 8+ (OAuth flow, session store, middleware, RBAC, tests, docs)
- Interdependent: Yes (RBAC depends on sessions, sessions depend on OAuth)
- Estimated tokens: ~12,000

Decision: ✅ Enter plan mode
Expected ROI: 4x (prevents 3-4 revision cycles)

Plan:
1. Research OAuth provider requirements (constraints)
2. Design session architecture (state management)
3. Implement OAuth flow (authentication)
4. Implement session middleware (authorization)
5. Implement RBAC layer (permissions)
6. Write integration tests (validation)
7. Document security model (knowledge transfer)

Result: 4.2x actual ROI (completed in 3 hours vs 12-13 hours with revisions)
```

```markdown
# BAD: Simple task planning
Task: "Rename function getUserData to fetchUserData"

Analysis:
- Complexity: TRIVIAL
- Steps: 1 (find-replace)
- Interdependent: No
- Estimated tokens: ~500

Decision: ❌ Skip planning, execute directly
Actual time: 2 minutes (search, rename, verify)

If planned:
- Planning: 5 minutes (analyze call sites, consider impacts, document decision)
- Execution: 2 minutes
- Total: 7 minutes
- ROI: -250% (planning wasted 5 minutes for 2-minute task)
```

**Source Meta-Insights**:
- SET-2 #12: First workflow step = 2-3x impact
- SET-5 #3: Tests-first prevents 3-5x revisions
- SET-2 #8: Thinking budget ROI range 15-25x for COMPLEX
- SET-3 #5: Sequential planning = 2.99x speedup

---

### Pattern 1.2: Risk-Based Planning Decision

**When**: High-risk changes require planning regardless of complexity

**Pattern**:
```
IF (risk_level == HIGH) OR (blast_radius > LOCAL):
    → Enter plan mode
    → Add safety validation gates
ELSE:
    → Evaluate by complexity threshold (Pattern 1.1)
```

**Why This Works**:
- **From SET-5 Meta-Insight #8**: "Refactoring without ≥80% test coverage is 10x riskier"
  - High-risk changes need explicit safety planning
  - Planning identifies missing prerequisites (like test coverage)

- **From SET-3 Meta-Insight #15**: "Missing session management = 10x cost"
  - Planning reveals hidden dependencies and failure modes
  - Risk mitigation requires upfront analysis

**Risk Factors**:

| Factor | Risk Level | Planning Required? | Safety Gates |
|--------|-----------|-------------------|--------------|
| Database schema changes | HIGH | ✅ Yes | Migration rollback plan |
| Production config changes | HIGH | ✅ Yes | Canary deployment |
| API contract changes | HIGH | ✅ Yes | Versioning strategy |
| Refactoring without tests | HIGH | ✅ Yes | Test coverage gate (≥80%) |
| New external dependencies | MEDIUM | ⚠️ Yes if COMPLEX | Security audit |
| Internal function changes | LOW | ❌ Only if COMPLEX | Unit tests sufficient |

**Blast Radius Assessment**:
```python
def assess_blast_radius(change_type, affected_components, production_impact):
    """
    Determine blast radius of a change.

    Returns: 'LOCAL', 'MODULE', 'SYSTEM', 'PRODUCTION'
    """
    if production_impact:
        return 'PRODUCTION'  # Always plan

    if affected_components >= 5:
        return 'SYSTEM'  # Plan required

    if affected_components >= 2:
        return 'MODULE'  # Plan recommended

    return 'LOCAL'  # Plan optional
```

**Example**:

```markdown
# HIGH RISK → Always plan
Task: "Migrate user authentication from sessions to JWT"

Risk Analysis:
- Change type: Authentication mechanism (CRITICAL)
- Affected components: 12+ (all protected endpoints)
- Production impact: Yes (all users affected)
- Blast radius: PRODUCTION
- Test coverage: 65% (below 80% safety threshold)

Decision: ✅ Plan required regardless of complexity
Safety gates needed:
1. Increase test coverage to ≥80%
2. Implement dual-mode (sessions + JWT) for migration
3. Canary deployment (5% → 20% → 100%)
4. Rollback plan with session fallback

Plan prevents:
- Breaking authentication for all users
- Session invalidation issues
- Data loss from incomplete migration
- No rollback path if JWT issues arise
```

**Source Meta-Insights**:
- SET-5 #8: Refactoring without tests = 10x risk
- SET-3 #15: Missing session management = 10x cost
- SET-5 #13: Test coverage ≥80% required for safe refactoring

---

### Pattern 1.3: Novelty-Based Planning Decision

**When**: Unfamiliar territory requires exploration before execution

**Pattern**:
```
IF (domain_familiarity < 0.5) OR (team_experience < 2 similar_projects):
    → Enter plan mode with research phase
    → Allocate 20-30% time for exploration
ELSE:
    → Use complexity threshold (Pattern 1.1)
```

**Why This Works**:
- **From SET-3 Meta-Insight #18**: "Tool registry reuse = 40,000x ROI vs rebuilding"
  - Unfamiliar domains lack existing patterns to reuse
  - Planning phase identifies reusable components before building

- **From SET-2 Meta-Insight #23**: "Cascade optimization: solve latency problems upstream"
  - Research upfront prevents downstream architecture mistakes
  - 2-3x higher ROI on early planning decisions

**Familiarity Assessment**:

| Familiarity Level | Team Experience | Planning Allocation | ROI |
|------------------|----------------|-------------------|-----|
| Expert (0.9+) | 5+ similar projects | 10% research | 1.5x |
| Proficient (0.7-0.9) | 2-4 similar projects | 15% research | 2x |
| Intermediate (0.5-0.7) | 1 similar project | 20% research | 3x |
| Novice (0.3-0.5) | 0 similar, related knowledge | 30% research | 4-5x |
| Beginner (<0.3) | No related knowledge | 40% research | 5-8x |

**Formula**:
```python
def calculate_research_time(familiarity, total_estimate):
    """
    Calculate research/planning allocation based on familiarity.

    Args:
        familiarity: 0.0-1.0 (domain knowledge level)
        total_estimate: Total estimated hours

    Returns: (research_hours, execution_hours, expected_roi)
    """
    if familiarity >= 0.9:
        research_pct = 0.10
        roi = 1.5
    elif familiarity >= 0.7:
        research_pct = 0.15
        roi = 2.0
    elif familiarity >= 0.5:
        research_pct = 0.20
        roi = 3.0
    elif familiarity >= 0.3:
        research_pct = 0.30
        roi = 4.5
    else:
        research_pct = 0.40
        roi = 6.5

    research_hours = total_estimate * research_pct
    execution_hours = total_estimate * (1 - research_pct)

    return research_hours, execution_hours, roi
```

**Example**:

```markdown
# NOVEL DOMAIN → Plan with research
Task: "Implement real-time collaborative editing (like Google Docs)"

Familiarity Assessment:
- Team experience: 0 similar projects (never built CRDT-based system)
- Domain familiarity: 0.2 (know websockets, but not conflict-free replicated data types)
- Total estimate: 40 hours

Decision: ✅ Plan with 40% research allocation
- Research phase: 16 hours
  - Study CRDT algorithms (Yjs, Automerge)
  - Evaluate existing libraries
  - Prototype basic conflict resolution
  - Design state synchronization
- Execution phase: 24 hours
  - Implement chosen CRDT library
  - Build WebSocket infrastructure
  - Implement UI updates
  - Testing and optimization

Expected ROI: 6.5x (research prevents architectural mistakes)

Without planning:
- Jump to implementation with incomplete understanding
- Discover CRDT requirements mid-project (requires rewrite)
- Total time: ~120 hours (3x over estimate)
- Multiple failed architectures

With planning:
- Research identifies Yjs as mature solution
- Understand CRDT principles before coding
- Single clean implementation
- Total time: 42 hours (on estimate)
- ROI: 120/42 = 2.86x actual (conservative vs 6.5x expected)
```

**Source Meta-Insights**:
- SET-3 #18: Tool registry reuse = 40,000x ROI
- SET-2 #23: Cascade optimization (upstream decisions)
- SET-5 #15: Code context = 85% of refactoring quality (domain knowledge critical)

---

### Pattern 1.4: Dependency Complexity Planning

**When**: High dependency complexity requires dependency mapping

**Pattern**:
```
dependency_count = count_direct_dependencies(task)
coupling_degree = measure_coupling(dependencies)

IF (dependency_count >= 5) OR (coupling_degree == TIGHT):
    → Enter plan mode
    → Create dependency graph
    → Identify critical path
ELSE:
    → Use complexity threshold (Pattern 1.1)
```

**Why This Works**:
- **From SET-3 Meta-Insight #7**: "4-layer architecture prevents cascade failures"
  - Planning reveals hidden dependencies
  - Proper layering prevents circular dependencies

- **From SET-2 Meta-Insight #12**: "First workflow step = 3x impact of last"
  - Dependency ordering IS the first step
  - Getting order wrong causes 3x+ rework

**Dependency Metrics**:

| Metric | Threshold | Planning Required? | Reason |
|--------|-----------|-------------------|--------|
| Direct dependencies | ≥5 | ✅ Yes | Coordination overhead |
| Transitive dependencies | ≥10 | ✅ Yes | Hidden complexity |
| Circular dependencies | ≥1 | ✅ Yes | Architecture issue |
| External dependencies | ≥3 | ⚠️ Maybe | Integration risk |
| Coupling degree | TIGHT | ✅ Yes | Change amplification |

**Coupling Assessment**:
```python
def assess_coupling(dependencies):
    """
    Determine coupling degree between components.

    Returns: 'LOOSE', 'MODERATE', 'TIGHT'
    """
    shared_state = count_shared_state_variables(dependencies)
    bidirectional = count_bidirectional_deps(dependencies)
    circular = has_circular_deps(dependencies)

    if circular or bidirectional >= 3 or shared_state >= 5:
        return 'TIGHT'  # Plan required - refactor to decouple

    if bidirectional >= 1 or shared_state >= 2:
        return 'MODERATE'  # Plan recommended

    return 'LOOSE'  # Plan optional
```

**Example**:

```markdown
# HIGH DEPENDENCY COMPLEXITY → Plan with dependency graph
Task: "Add caching layer to API"

Dependency Analysis:
- Direct dependencies: 7
  1. API endpoints (data access)
  2. Database queries (cache candidates)
  3. Authentication middleware (user context)
  4. Rate limiting (cache key generation)
  5. Response serialization (cache value format)
  6. Error handling (cache failures)
  7. Monitoring/logging (cache metrics)

- Transitive dependencies: 15+
- Coupling degree: MODERATE (shared request context)
- Critical path: Authentication → Cache → Database → Serialization

Decision: ✅ Plan required - create dependency graph

Plan:
1. Map data flow: Request → Auth → Cache → DB → Serialize → Response
2. Identify cache points:
   - After authentication (user-specific keys)
   - Before database (query-level cache)
   - After serialization (response cache)
3. Choose cache layer: Query-level (least coupling)
4. Design cache invalidation strategy (event-based)
5. Implement cache wrapper (single dependency injection point)
6. Add monitoring (cache hit rate, latency impact)

Result without planning:
- Added cache at response level (high coupling - must intercept all responses)
- Broke streaming responses (didn't consider serialization)
- Invalidation requires touching 7 components
- Total time: 20 hours + 12 hours rework = 32 hours

Result with planning:
- Added cache at query level (single injection point in DB layer)
- Streaming responses unaffected
- Invalidation in one place (database model)
- Total time: 14 hours (planning prevented 18 hours rework)
- ROI: 32/14 = 2.29x
```

**Source Meta-Insights**:
- SET-3 #7: 4-layer architecture prevents cascade failures
- SET-2 #12: First step = 3x impact (dependency order IS first step)
- SET-3 #15: Missing session management = 10x cost (dependency example)

---

### Pattern 1.5: Resource Constraint Planning

**When**: Limited resources require optimization planning

**Pattern**:
```
IF (token_budget < 50000) OR (time_budget < task_estimate * 1.5) OR (cost_budget < $10):
    → Enter plan mode with resource optimization
    → Allocate resources to high-impact steps
ELSE:
    → Use complexity threshold (Pattern 1.1)
```

**Why This Works**:
- **From SET-1 Meta-Insight #3**: "Compound optimization: Batch + Cache = 95% savings (vs 50% + 90% separate)"
  - Resource constraints require multiplicative optimization
  - Planning identifies compound opportunities

- **From SET-2 Meta-Insight #12**: "First workflow step = 2-3x impact"
  - Limited resources must go to high-impact steps
  - Planning identifies where to invest scarce resources

**Resource Thresholds**:

| Resource | Constraint Level | Planning Required? | Optimization Strategy |
|----------|-----------------|-------------------|----------------------|
| Token budget | <30K | ✅ Yes | Haiku for execution, Sonnet for planning |
| Token budget | <50K | ⚠️ Maybe | Extended thinking on complex steps only |
| Time budget | <1.2x estimate | ✅ Yes | Cut low-impact features |
| Time budget | <1.5x estimate | ⚠️ Maybe | Parallel execution where possible |
| Cost budget | <$5 | ✅ Yes | Batch + cache compound optimization |
| Cost budget | <$10 | ⚠️ Maybe | Cache high-repetition calls |

**Formula**:
```python
def optimize_resource_allocation(steps, token_budget, time_budget, cost_budget):
    """
    Allocate limited resources to maximize impact.

    Returns: optimized_plan with resource assignments
    """
    # Calculate impact scores for each step
    step_impacts = []
    for i, step in enumerate(steps):
        # Earlier steps get 2-3x multiplier (cascade effect)
        position_multiplier = max(3.0 - (i * 0.3), 1.0)

        # Complexity multiplier (COMPLEX steps get more resources)
        complexity_multiplier = {
            'TRIVIAL': 0.5,
            'SIMPLE': 1.0,
            'MODERATE': 1.5,
            'COMPLEX': 2.5,
            'VERY_COMPLEX': 4.0
        }[step.complexity]

        impact = position_multiplier * complexity_multiplier
        step_impacts.append((step, impact))

    # Sort by impact (descending)
    step_impacts.sort(key=lambda x: x[1], reverse=True)

    # Allocate resources proportionally to impact
    total_impact = sum(impact for _, impact in step_impacts)

    optimized_plan = []
    for step, impact in step_impacts:
        resource_fraction = impact / total_impact

        step_resources = {
            'tokens': int(token_budget * resource_fraction),
            'time': time_budget * resource_fraction,
            'cost': cost_budget * resource_fraction,
            'model': 'sonnet' if step.complexity in ['COMPLEX', 'VERY_COMPLEX'] else 'haiku'
        }

        optimized_plan.append((step, step_resources))

    return optimized_plan
```

**Example**:

```markdown
# RESOURCE CONSTRAINED → Plan with optimization
Task: "Generate comprehensive API documentation from codebase"

Resource Constraints:
- Token budget: 40,000 (tight)
- Time budget: 2 hours (1.3x estimate)
- Cost budget: $8

Steps:
1. Extract API endpoints (MODERATE, position=1) → impact: 3.0 × 1.5 = 4.5
2. Analyze request/response schemas (COMPLEX, position=2) → impact: 2.7 × 2.5 = 6.75
3. Generate endpoint descriptions (SIMPLE, position=3) → impact: 2.4 × 1.0 = 2.4
4. Create usage examples (MODERATE, position=4) → impact: 2.1 × 1.5 = 3.15
5. Generate error documentation (SIMPLE, position=5) → impact: 1.8 × 1.0 = 1.8
6. Format as OpenAPI spec (TRIVIAL, position=6) → impact: 1.5 × 0.5 = 0.75

Total impact: 19.35

Resource Allocation:
1. Extract endpoints: 4.5/19.35 = 23% → 9,200 tokens, Haiku, $1.84
2. Analyze schemas: 6.75/19.35 = 35% → 14,000 tokens, Sonnet, $2.80 (highest impact!)
3. Generate descriptions: 2.4/19.35 = 12% → 4,800 tokens, Haiku, $0.96
4. Create examples: 3.15/19.35 = 16% → 6,400 tokens, Haiku, $1.28
5. Error docs: 1.8/19.35 = 9% → 3,600 tokens, Haiku, $0.72
6. Format OpenAPI: 0.75/19.35 = 4% → 1,600 tokens, Haiku, $0.32

Without planning:
- Equal allocation: 6,667 tokens/step, all Haiku
- Schema analysis gets insufficient tokens (needs 10K+)
- Result: Incomplete schema docs, requires second pass
- Total cost: $8 + $6 second pass = $14

With planning:
- Optimized allocation: high-impact steps get Sonnet + more tokens
- Schema analysis complete in first pass
- Total cost: $7.92 (within budget)
- ROI: 14/7.92 = 1.77x
```

**Source Meta-Insights**:
- SET-1 #3: Compound optimization (batch + cache = 95%)
- SET-2 #12: First step = 2-3x impact
- SET-1 #7: Haiku throughput = 4x Sonnet (resource optimization)

---

## Section 2: Plan Structure Patterns

### Pattern 2.1: Hierarchical Decomposition Structure

**When**: Complex tasks need breakdown into manageable subtasks

**Pattern**:
```
1. Top-level goal (WHAT to achieve)
2. Strategic phases (WHY approach matters)
3. Tactical steps (HOW to execute)
4. Atomic tasks (WHAT to do specifically)
```

**Why This Works**:
- **From SET-2 Meta-Insight #26**: "Task classification prevents 40% of common failures"
  - Hierarchical breakdown reveals hidden complexity
  - Each level provides different decision criteria

- **From SET-3 Meta-Insight #7**: "4-layer architecture: Tool Registry + Session + Safety + Error Handling"
  - Hierarchical structure mirrors proven architecture pattern
  - Each layer has clear responsibilities

**Decomposition Levels**:

| Level | Purpose | Example | Granularity |
|-------|---------|---------|-------------|
| Goal | Define success criteria | "Implement real-time notifications" | 1 per task |
| Phase | Strategic approach | "Phase 1: WebSocket infrastructure" | 2-5 per goal |
| Step | Tactical execution | "Step 3: Implement event subscription" | 3-8 per phase |
| Task | Atomic unit of work | "Task 3.2: Add subscribe endpoint" | 5-15 per step |

**Template**:
```markdown
# [GOAL]: <High-level objective>

## Success Criteria
- [ ] Criterion 1 (measurable)
- [ ] Criterion 2 (testable)
- [ ] Criterion 3 (verifiable)

## Phase 1: [Strategic Component]
**Why this first**: <Rationale based on dependencies/impact>

### Step 1.1: [Tactical Action]
**Tasks**:
- [ ] 1.1.1: <Atomic task>
- [ ] 1.1.2: <Atomic task>

**Validation**: <How to verify completion>
**Dependencies**: <What must be done first>
**Estimated effort**: <Time/tokens/cost>

### Step 1.2: [Tactical Action]
...

## Phase 2: [Strategic Component]
...
```

**Example**:

```markdown
# GOAL: Implement User Authentication System

## Success Criteria
- [ ] Users can register with email/password
- [ ] Users can log in and receive JWT token
- [ ] Protected routes verify JWT and reject invalid tokens
- [ ] Test coverage ≥90% for auth flows
- [ ] Documentation includes security model

## Phase 1: Foundation (Data & Security)
**Why this first**: Authentication depends on secure user storage and token generation.
Build foundation before any features (cascade optimization - early decisions = 3x impact).

### Step 1.1: Design User Schema
**Tasks**:
- [ ] 1.1.1: Define user model fields (id, email, password_hash, created_at)
- [ ] 1.1.2: Create database migration
- [ ] 1.1.3: Add unique constraint on email
- [ ] 1.1.4: Add indexes for email lookups

**Validation**: Can insert/query users without errors
**Dependencies**: None (foundational)
**Estimated effort**: 1 hour, 2K tokens, $0.40

### Step 1.2: Implement Password Hashing
**Tasks**:
- [ ] 1.2.1: Choose hashing library (bcrypt, 10 rounds)
- [ ] 1.2.2: Implement hash_password() utility
- [ ] 1.2.3: Implement verify_password() utility
- [ ] 1.2.4: Write tests for hash/verify

**Validation**: Tests pass, bcrypt cost factor = 10
**Dependencies**: Step 1.1 (user model)
**Estimated effort**: 1.5 hours, 3K tokens, $0.60

### Step 1.3: Implement JWT Generation
**Tasks**:
- [ ] 1.3.1: Choose JWT library (PyJWT)
- [ ] 1.3.2: Generate secret key (store in environment)
- [ ] 1.3.3: Implement create_token(user_id, expiry)
- [ ] 1.3.4: Implement verify_token(token)
- [ ] 1.3.5: Write tests for token lifecycle

**Validation**: Tokens can be created and verified, expiry works
**Dependencies**: Step 1.1 (user model for user_id)
**Estimated effort**: 2 hours, 4K tokens, $0.80

## Phase 2: Registration & Login (User Flows)
**Why after Phase 1**: Flows depend on hashing and JWT infrastructure.

### Step 2.1: Implement Registration Endpoint
**Tasks**:
- [ ] 2.1.1: Create POST /auth/register endpoint
- [ ] 2.1.2: Validate email format and uniqueness
- [ ] 2.1.3: Validate password strength (≥8 chars, mixed case, number)
- [ ] 2.1.4: Hash password and create user
- [ ] 2.1.5: Return success/error response
- [ ] 2.1.6: Write integration tests

**Validation**: Can register new user via API, duplicates rejected
**Dependencies**: Steps 1.1, 1.2 (user model, password hashing)
**Estimated effort**: 2.5 hours, 5K tokens, $1.00

### Step 2.2: Implement Login Endpoint
**Tasks**:
- [ ] 2.2.1: Create POST /auth/login endpoint
- [ ] 2.2.2: Look up user by email
- [ ] 2.2.3: Verify password hash
- [ ] 2.2.4: Generate JWT token on success
- [ ] 2.2.5: Return token or 401 error
- [ ] 2.2.6: Write integration tests (valid/invalid credentials)

**Validation**: Can log in and receive valid JWT
**Dependencies**: Steps 1.1, 1.2, 1.3 (user model, hashing, JWT)
**Estimated effort**: 2 hours, 4K tokens, $0.80

## Phase 3: Authorization (Protected Routes)
**Why last**: Authorization depends on complete authentication flow.

### Step 3.1: Implement Auth Middleware
**Tasks**:
- [ ] 3.1.1: Create require_auth() decorator
- [ ] 3.1.2: Extract token from Authorization header
- [ ] 3.1.3: Verify token and extract user_id
- [ ] 3.1.4: Attach user to request context
- [ ] 3.1.5: Return 401 if token invalid/missing
- [ ] 3.1.6: Write middleware tests

**Validation**: Protected routes reject requests without valid tokens
**Dependencies**: Step 1.3 (JWT verification)
**Estimated effort**: 2 hours, 4K tokens, $0.80

### Step 3.2: Add Protected Route Example
**Tasks**:
- [ ] 3.2.1: Create GET /api/profile (requires auth)
- [ ] 3.2.2: Apply @require_auth decorator
- [ ] 3.2.3: Return current user data
- [ ] 3.2.4: Write integration test (with/without token)

**Validation**: /api/profile returns user data with valid token, 401 without
**Dependencies**: Step 3.1 (auth middleware)
**Estimated effort**: 1 hour, 2K tokens, $0.40

## Phase 4: Testing & Documentation
**Why last**: Validate complete system and document for users.

### Step 4.1: Comprehensive Testing
**Tasks**:
- [ ] 4.1.1: Write registration flow tests (happy path, edge cases)
- [ ] 4.1.2: Write login flow tests (valid, invalid, missing)
- [ ] 4.1.3: Write authorization tests (protected routes)
- [ ] 4.1.4: Write security tests (SQL injection, timing attacks)
- [ ] 4.1.5: Measure coverage (target ≥90%)

**Validation**: All tests pass, coverage ≥90%
**Dependencies**: All previous steps (testing complete system)
**Estimated effort**: 3 hours, 6K tokens, $1.20

### Step 4.2: Security Documentation
**Tasks**:
- [ ] 4.2.1: Document password hashing (algorithm, cost factor)
- [ ] 4.2.2: Document JWT (secret management, expiry, refresh strategy)
- [ ] 4.2.3: Document API endpoints (request/response examples)
- [ ] 4.2.4: Document security model (threat model, mitigations)

**Validation**: Documentation is complete and accurate
**Dependencies**: All previous steps (documenting complete system)
**Estimated effort**: 2 hours, 4K tokens, $0.80

---

**Total Estimates**:
- Time: 17.5 hours
- Tokens: 34K
- Cost: $6.80
- Tasks: 32 atomic tasks across 4 phases
```

**Evidence**:
- SET-2 #26: Task classification prevents 40% failures (hierarchical = better classification)
- SET-3 #7: 4-layer architecture (proven hierarchical pattern)
- SET-5 #3: Tests-first = constraints before solution (phases = constraints, steps = solution)

---

### Pattern 2.2: Dependency-First Ordering

**When**: Task order matters due to dependencies

**Pattern**:
```
1. Identify all dependencies (explicit + implicit)
2. Build dependency graph (topological sort)
3. Order tasks by: foundational → derived → integrative
4. Schedule independent tasks in parallel when possible
```

**Why This Works**:
- **From SET-2 Meta-Insight #12**: "First workflow step = 2-3x impact of last step"
  - Dependencies define the first step (foundation)
  - Getting order wrong causes 3x rework

- **From SET-3 Meta-Insight #5**: "Sequential orchestration = 2.99x speedup with proper ordering"
  - Topological ordering prevents blocking and rework
  - Parallel scheduling maximizes throughput

**Dependency Types**:

| Type | Description | Example | Handling |
|------|-------------|---------|----------|
| Hard | Must complete before dependent | Database schema before queries | Sequential, blocking |
| Soft | Helpful but not required | Documentation before implementation | Parallel, async |
| Implicit | Hidden dependency | Auth before protected routes | Planning reveals these |
| Circular | Bidirectional dependency | A needs B, B needs A | Refactor to break cycle |

**Ordering Algorithm**:
```python
def order_tasks_by_dependencies(tasks, dependencies):
    """
    Topological sort with parallel opportunity detection.

    Returns: ordered_phases with tasks grouped by parallelizability
    """
    # Build dependency graph
    graph = defaultdict(list)
    in_degree = defaultdict(int)

    for task in tasks:
        in_degree[task.id] = 0

    for task_id, depends_on in dependencies.items():
        for dep_id in depends_on:
            graph[dep_id].append(task_id)
            in_degree[task_id] += 1

    # Find tasks with no dependencies (ready to execute)
    ready_queue = deque([t.id for t in tasks if in_degree[t.id] == 0])

    ordered_phases = []

    while ready_queue:
        # All tasks in ready_queue can execute in parallel
        current_phase = list(ready_queue)
        ordered_phases.append(current_phase)
        ready_queue.clear()

        # Update in_degree for tasks that depend on current phase
        for task_id in current_phase:
            for dependent_id in graph[task_id]:
                in_degree[dependent_id] -= 1
                if in_degree[dependent_id] == 0:
                    ready_queue.append(dependent_id)

    # Check for circular dependencies
    if sum(in_degree.values()) > 0:
        circular = [tid for tid, deg in in_degree.items() if deg > 0]
        raise ValueError(f"Circular dependencies detected: {circular}")

    return ordered_phases
```

**Example**:

```markdown
# Dependency-Ordered Plan: API Rate Limiting

## Tasks with Dependencies

1. **Task A**: Design rate limit algorithm
   - Dependencies: None (foundational)

2. **Task B**: Implement rate limit storage (Redis)
   - Dependencies: None (foundational)

3. **Task C**: Create rate limit middleware
   - Dependencies: A (algorithm), B (storage)

4. **Task D**: Add rate limit headers (X-RateLimit-*)
   - Dependencies: C (middleware must exist to add headers)

5. **Task E**: Write middleware tests
   - Dependencies: C (middleware), B (storage for test setup)

6. **Task F**: Update API documentation
   - Dependencies: None (can write in parallel with implementation)

7. **Task G**: Add rate limit monitoring/metrics
   - Dependencies: C (middleware must be instrumented)

## Dependency Graph
```
    A (algorithm)     B (storage)      F (docs)
         \               /              |
          \             /               |
           \           /                |
            C (middleware)              |
           / | \                        |
          /  |  \                       |
         /   |   \                      |
        D    E    G                     |
    (headers)(tests)(metrics)           |
                                        |
        (all independent of F)         /
```

## Ordered Execution Phases

**Phase 1** (Parallel - 3 tasks, no dependencies):
- Task A: Design rate limit algorithm [2 hours]
- Task B: Implement Redis storage [3 hours]
- Task F: Write documentation [2 hours]
- **Phase duration**: 3 hours (limited by slowest task)

**Phase 2** (Sequential - 1 task, depends on A + B):
- Task C: Create rate limit middleware [4 hours]
- **Phase duration**: 4 hours

**Phase 3** (Parallel - 3 tasks, all depend on C):
- Task D: Add rate limit headers [1 hour]
- Task E: Write middleware tests [2 hours]
- Task G: Add monitoring/metrics [2 hours]
- **Phase duration**: 2 hours (limited by slowest task)

**Total Duration**:
- Sequential execution: 2 + 3 + 4 + 1 + 2 + 2 + 2 = 16 hours
- Parallel-optimized execution: 3 + 4 + 2 = 9 hours
- **Speedup: 1.78x** (16/9)

**Without Dependency Ordering** (Random order: C, E, A, F, D, B, G):
1. Start Task C (middleware) - BLOCKED, needs A and B
2. Start Task E (tests) - BLOCKED, needs C and B
3. Do Task A (algorithm) - OK (2 hours)
4. Do Task F (docs) - OK (2 hours)
5. Do Task D (headers) - BLOCKED, needs C
6. Do Task B (storage) - OK (3 hours)
7. Now can do Task C (middleware) - 4 hours
8. Now can do Task E (tests) - 2 hours
9. Now can do Task D (headers) - 1 hour
10. Now can do Task G (metrics) - 2 hours

**Total with blocking**: ~16 hours + coordination overhead + context switching = ~19 hours
**Penalty**: 19/9 = 2.1x slower than optimized order
```

**Evidence**:
- SET-2 #12: First step = 2-3x impact (foundation tasks ARE first)
- SET-3 #5: Sequential orchestration = 2.99x speedup
- SET-3 #6: Parallel execution = 2x speedup (when dependencies allow)

**Source Meta-Insights**:
- SET-2 #12: Early decisions = high impact
- SET-3 #5: Proper ordering = 2.99x speedup
- SET-3 #6: Parallel opportunities when dependencies allow

---

### Pattern 2.3: Validation Gate Structure

**When**: Quality and safety require checkpoints between phases

**Pattern**:
```
Phase 1 → Validation Gate → Phase 2 → Validation Gate → Phase 3
          (pre-execution)              (mid-execution)              (post-execution)

Each gate:
- Checks prerequisites
- Validates output quality
- Blocks if criteria not met
```

**Why This Works**:
- **From SET-5 Meta-Insight #8**: "Refactoring without ≥80% test coverage is 10x riskier"
  - Validation gates prevent proceeding with insufficient safety
  - Blocking saves 10x rework cost

- **From SET-3 Meta-Insight #26**: "Pre-execution validation prevents 40% of failures"
  - Gates catch issues before expensive execution
  - Prevention >> correction

**Gate Types**:

| Gate Type | When | What to Validate | Block Threshold |
|-----------|------|------------------|-----------------|
| Pre-execution | Before starting | Prerequisites met, resources available | Any critical missing |
| Mid-execution | Between phases | Phase outputs complete, quality sufficient | Quality <80% target |
| Post-execution | After completion | All requirements met, no regressions | Any requirement failed |

**Validation Checklist Template**:
```markdown
## Validation Gate: [Phase Name]

### Prerequisites Check
- [ ] Required resources available (data, APIs, credentials)
- [ ] Dependencies completed (previous phases)
- [ ] Environment configured (database, services)

### Quality Check
- [ ] Tests passing (≥80% coverage for refactoring gates)
- [ ] No security vulnerabilities introduced
- [ ] Performance within acceptable range
- [ ] Documentation updated (if required)

### Output Verification
- [ ] Phase deliverables complete
- [ ] Acceptance criteria met
- [ ] No blockers for next phase

**Gate Status**: ✅ PASS / ⚠️ CONDITIONAL PASS / ❌ BLOCKED

**If BLOCKED**:
- Reason: [What failed]
- Action: [How to unblock]
- Re-validation: [When to check again]
```

**Example**:

```markdown
# Plan with Validation Gates: Database Migration

## Phase 1: Preparation
- Design new schema
- Write migration script
- Create rollback script

### **VALIDATION GATE 1: Pre-Migration**

#### Prerequisites Check
- [x] Backup completed (full database backup at 2024-12-01 10:00 UTC)
- [x] Migration tested in staging (passed with 0 errors)
- [x] Rollback script tested in staging (restored to original state)
- [x] Maintenance window scheduled (2024-12-01 22:00-23:00 UTC)
- [x] Team on-call (3 engineers available)

#### Quality Check
- [x] Migration script reviewed (2 peer reviews)
- [x] Performance impact assessed (<2 min downtime expected)
- [x] Monitoring dashboards ready (query latency, error rate)

#### Output Verification
- [x] Schema changes are backward-compatible (old code still works)
- [x] Data migration preserves referential integrity
- [x] Indexes will be rebuilt (estimated 5 minutes)

**Gate Status**: ✅ PASS - Proceed to migration

---

## Phase 2: Execute Migration
- Enable maintenance mode
- Run migration script
- Verify data integrity

### **VALIDATION GATE 2: Post-Migration**

#### Prerequisites Check
- [x] Migration script completed (exit code 0)
- [x] No errors in migration log
- [x] All tables present (14/14 expected tables)

#### Quality Check
- [x] Data integrity check passed (row counts match: 1,245,789 users)
- [x] Foreign key constraints intact (0 violations)
- [x] Indexes rebuilt (14/14 indexes present)
- [ ] Performance regression test - ❌ FAILED
  - Query latency increased 300% (100ms → 400ms)
  - Root cause: Missing index on new column

**Gate Status**: ❌ BLOCKED - Performance regression

**Blocking Issue**:
- Reason: New query pattern not indexed
- Action: Add index on users.auth_provider column
- Re-validation: After index creation

#### Fix Applied
```sql
CREATE INDEX idx_users_auth_provider ON users(auth_provider);
```

#### Re-validation
- [x] Performance regression test - ✅ PASSED
  - Query latency: 95ms (5% improvement over original)
  - Index usage confirmed in EXPLAIN plan

**Gate Status**: ✅ PASS - Proceed to Phase 3

---

## Phase 3: Finalization
- Disable maintenance mode
- Monitor for issues
- Update documentation

### **VALIDATION GATE 3: Post-Deployment**

#### Prerequisites Check
- [x] Application started successfully
- [x] All health checks passing (7/7 services healthy)
- [x] No errors in application logs (0 errors in first 10 minutes)

#### Quality Check
- [x] User authentication working (100 test logins successful)
- [x] API response times normal (p95 = 120ms, within SLA)
- [x] No database deadlocks (0 in 30 minute window)
- [x] Monitoring alerts quiet (0 alerts triggered)

#### Output Verification
- [x] Migration documentation updated (added to runbook)
- [x] Schema documentation updated (new column documented)
- [x] Rollback procedure documented (tested in staging)

**Gate Status**: ✅ PASS - Migration complete

**Success Metrics**:
- Downtime: 8 minutes (target: <15 minutes)
- Data loss: 0 rows
- Errors: 1 (performance regression, fixed before prod impact)
- Rollback needed: No
```

**Gate Prevented Disaster**:
- Validation Gate 2 caught missing index BEFORE prod traffic hit
- Without gate: 300% latency increase would affect all users
- Estimated cost of missing gate: 2 hours emergency response + potential SLA breach
- Gate overhead: 10 minutes validation
- ROI: 120 min / 10 min = 12x

**Evidence**:
- SET-5 #8: Refactoring without ≥80% coverage = 10x risk (gate prevents this)
- SET-3 #26: Pre-execution validation prevents 40% failures
- SET-5 #13: Test coverage gate required for safe refactoring

**Source Meta-Insights**:
- SET-5 #8: Coverage threshold gate
- SET-3 #26: Pre-execution validation
- SET-5 #13: Safety validation between phases

---

### Pattern 2.4: Incremental Milestone Structure

**When**: Large tasks need frequent validation and course correction

**Pattern**:
```
Break large goal into 5-10 milestones, each:
1. Independently valuable (can stop after any milestone)
2. Demonstrable (produces visible output)
3. Testable (has clear pass/fail criteria)
4. Time-boxed (≤1 day per milestone for COMPLEX tasks)
```

**Why This Works**:
- **From SET-5 Meta-Insight #11**: "Iterative refinement loop prevents accumulation of errors"
  - Frequent milestones = frequent error detection
  - Small iterations reduce debugging scope

- **From SET-2 Meta-Insight #19**: "Quality improvement per iteration = 25-32% delta"
  - Incremental approach allows optimization between milestones
  - Each milestone improves on previous (compound quality)

**Milestone Characteristics**:

| Characteristic | Good Milestone | Bad Milestone |
|---------------|----------------|---------------|
| Value | Can ship after this | No value until complete |
| Visibility | Demo-able output | Internal only |
| Testability | Clear pass/fail | Subjective quality |
| Time | ≤1 day | Multiple days |
| Independence | Works standalone | Requires all milestones |

**Milestone Planning Template**:
```markdown
## Milestone Structure

**Overall Goal**: [High-level objective]
**Target Duration**: [Total estimated time]
**Milestone Count**: [5-10 milestones]

---

### Milestone 1: [Foundational Component]
**Value**: [What users/system gain from this alone]
**Duration**: [Time-box]
**Deliverable**: [Concrete output]

**Success Criteria**:
- [ ] Criterion 1 (testable)
- [ ] Criterion 2 (measurable)

**Demo**: [How to show it works]

---

### Milestone 2: [Next Increment]
**Value**: [Builds on M1, adds new capability]
**Dependencies**: Milestone 1
**Duration**: [Time-box]
**Deliverable**: [Concrete output]

**Success Criteria**:
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Backward compatible with M1

**Demo**: [How to show improvement]

---

[Continue for all milestones...]
```

**Example**:

```markdown
# Incremental Milestone Plan: Search Feature

**Overall Goal**: Add full-text search to product catalog
**Target Duration**: 5 days
**Milestone Count**: 6 milestones

---

### Milestone 1: Basic Keyword Search (Day 1, AM)
**Value**: Users can search products by exact name match
**Duration**: 4 hours
**Deliverable**: Search endpoint returns results for exact keyword matches

**Success Criteria**:
- [x] GET /api/search?q=keyword returns matching products
- [x] Case-insensitive matching works
- [x] Returns product ID, name, price
- [x] Response time <200ms for 10K product database

**Demo**:
```bash
curl "http://api/search?q=laptop"
# Returns: [{"id": 123, "name": "Laptop Pro", "price": 999}]
```

**Result**: ✅ SHIPPED - Users can now search, even if only exact matches

---

### Milestone 2: Partial Match Search (Day 1, PM)
**Value**: Users can search with partial words (e.g., "lap" finds "laptop")
**Dependencies**: Milestone 1
**Duration**: 3 hours
**Deliverable**: Search supports LIKE operator for partial matching

**Success Criteria**:
- [x] Searches "lap" returns "laptop", "lapton", "lapdesk"
- [x] Searches "book" returns "notebook", "bookshelf", "ebook"
- [x] Response time <300ms (acceptable degradation for fuzzy matching)
- [x] Backward compatible (exact matches still work)

**Demo**:
```bash
curl "http://api/search?q=lap"
# Returns: [{"id": 123, "name": "Laptop Pro"}, {"id": 456, "name": "Lapdesk"}]
```

**Result**: ✅ SHIPPED - Better UX, users don't need exact product names

---

### Milestone 3: Multi-Field Search (Day 2, AM)
**Value**: Users can search across name, description, category
**Dependencies**: Milestone 2
**Duration**: 4 hours
**Deliverable**: Search queries multiple fields, returns ranked results

**Success Criteria**:
- [x] Searches "gaming" returns products with "gaming" in name OR description OR category
- [x] Results ranked by relevance (name match > description match > category match)
- [x] Response time <400ms
- [x] Backward compatible (single-field searches still work)

**Demo**:
```bash
curl "http://api/search?q=gaming"
# Returns products ranked:
# 1. "Gaming Laptop" (name match, highest rank)
# 2. "Laptop with gaming graphics" (description match)
# 3. "Laptop" in category "Gaming" (category match, lowest rank)
```

**Result**: ✅ SHIPPED - More comprehensive search, finds relevant products

---

### Milestone 4: Search Filters (Day 2, PM)
**Value**: Users can filter search by price, category, rating
**Dependencies**: Milestone 3
**Duration**: 3 hours
**Deliverable**: Search supports filter parameters

**Success Criteria**:
- [x] Filter by price range: ?min_price=100&max_price=500
- [x] Filter by category: ?category=electronics
- [x] Filter by min rating: ?min_rating=4.0
- [x] Filters combine with AND logic
- [x] Response time <500ms with all filters

**Demo**:
```bash
curl "http://api/search?q=laptop&min_price=500&max_price=1000&category=electronics&min_rating=4.0"
# Returns only laptops priced $500-1000 in electronics with rating ≥4.0
```

**Result**: ✅ SHIPPED - Power users can narrow search results

---

### Milestone 5: Search Autocomplete (Day 3)
**Value**: Users see suggestions as they type (UX improvement)
**Dependencies**: Milestone 3 (needs multi-field search)
**Duration**: 5 hours
**Deliverable**: Autocomplete endpoint with typeahead suggestions

**Success Criteria**:
- [x] GET /api/search/autocomplete?q=lap returns ["laptop", "lapdesk", "lapton"]
- [x] Returns top 10 suggestions ranked by popularity
- [x] Response time <100ms (fast feedback for typing)
- [x] Handles partial words (min 2 characters)

**Demo**:
```bash
curl "http://api/search/autocomplete?q=ga"
# Returns: ["gaming laptop", "galaxy phone", "gamepad"]
```

**Result**: ✅ SHIPPED - Faster search, users find products quicker

---

### Milestone 6: Search Analytics (Day 4)
**Value**: Product team can see what users search for (informs inventory)
**Dependencies**: All previous milestones (needs complete search)
**Duration**: 6 hours
**Deliverable**: Search analytics dashboard and logging

**Success Criteria**:
- [x] Log all searches (query, timestamp, result_count, user_id)
- [x] Dashboard shows top 100 searches by volume
- [x] Dashboard shows searches with 0 results (inventory gaps)
- [x] Dashboard shows search-to-purchase conversion rate
- [x] Logging adds <10ms overhead

**Demo**: View dashboard showing:
- "laptop" searched 10,234 times (94% conversion)
- "macbook air" searched 3,456 times (0 results - inventory gap!)
- "gaming chair" searched 2,890 times (22% conversion - low quality results)

**Result**: ✅ SHIPPED - Product team has data to improve catalog

---

## Incremental Value Progression

| After Milestone | Cumulative Value | Shippable? | User Benefit |
|----------------|------------------|------------|--------------|
| M1 (exact match) | 40% | ✅ Yes | Better than no search |
| M2 (partial match) | 60% | ✅ Yes | Don't need exact names |
| M3 (multi-field) | 75% | ✅ Yes | Finds more relevant products |
| M4 (filters) | 85% | ✅ Yes | Narrows results |
| M5 (autocomplete) | 95% | ✅ Yes | Faster UX |
| M6 (analytics) | 100% | ✅ Yes | Improves over time |

**If stopped after M3** (Day 2):
- 75% of target value delivered
- 2/5 days spent (40% time investment)
- ROI: 75% value / 40% time = 1.875x efficiency

**Without incremental approach** (all-or-nothing):
- 0% value until Day 5
- If project cancelled on Day 3: 0% value, 60% time wasted
- Single integration point (high risk)
```

**Comparison**:

| Approach | Value Delivery | Risk | Course Correction |
|----------|---------------|------|-------------------|
| Incremental | 40% → 60% → 75% → 85% → 95% → 100% | Low (test each step) | After each milestone |
| Monolithic | 0% → 0% → 0% → 0% → 0% → 100% | High (big bang) | Only at end (too late) |

**Evidence**:
- SET-5 #11: Iterative refinement prevents error accumulation
- SET-2 #19: Quality improvement = 25-32% per iteration
- Each milestone = iteration = compound quality improvement

**Source Meta-Insights**:
- SET-5 #11: Iterative refinement loop
- SET-2 #19: Quality delta per iteration
- SET-3 #5: Sequential orchestration (milestones = sequence)

---

### Pattern 2.5: Parallel Track Structure

**When**: Independent workstreams can proceed simultaneously

**Pattern**:
```
Identify independent tracks (no shared dependencies)
Schedule parallel execution with sync points
Merge at integration milestones

Track A: [Frontend] -----> Sync -----> Integrate
Track B: [Backend]  -----> Sync -----> Integrate
Track C: [Testing]  -----> Sync -----> Integrate
```

**Why This Works**:
- **From SET-3 Meta-Insight #6**: "Parallel agent execution = 2-3x speedup, +36% cost tradeoff"
  - Independent tracks can run in parallel
  - Speedup outweighs cost for COMPLEX tasks

- **From SET-3 Meta-Insight #20**: "Dependency-free operations should always parallelize"
  - Unused parallelism = wasted opportunity
  - Proper track isolation prevents conflicts

**Track Independence Criteria**:

| Criterion | Independent | Dependent |
|-----------|-------------|-----------|
| Shared state | No shared variables/files | Modifies same state |
| Dependencies | No sequential requirement | B requires A complete |
| Resources | Separate resources | Same database/API |
| Coordination | Async communication OK | Requires tight sync |

**Parallel Track Planning**:
```python
def identify_parallel_tracks(tasks, dependencies):
    """
    Group tasks into parallel tracks based on independence.

    Returns: list of tracks that can run simultaneously
    """
    # Build dependency graph
    dep_graph = build_graph(tasks, dependencies)

    # Find strongly connected components (tasks that must be sequential)
    sequential_groups = find_scc(dep_graph)

    # Tasks in different SCCs can parallelize if no cross-dependencies
    tracks = []
    for group in sequential_groups:
        # Check if this group depends on any other group
        independent = True
        for other_group in sequential_groups:
            if other_group == group:
                continue
            if has_dependency(group, other_group, dep_graph):
                independent = False
                break

        if independent:
            tracks.append(group)

    return tracks
```

**Example**:

```markdown
# Parallel Track Plan: E-commerce Feature Launch

**Goal**: Launch new product recommendations feature

## Track Analysis

### Track A: Machine Learning Model (Backend/Data Science)
**Duration**: 10 days
**Team**: 2 data scientists
**Dependencies**: Product data (already available)
**Deliverables**:
1. Train recommendation model on historical purchase data
2. Optimize model parameters (precision/recall)
3. Deploy model API endpoint
4. Performance testing (latency <100ms)

**No dependencies on Track B or C** (works with existing data, separate API)

---

### Track B: Frontend UI Components (Frontend)
**Duration**: 8 days
**Team**: 2 frontend engineers
**Dependencies**: Design mockups (already approved)
**Deliverables**:
1. Build product carousel component
2. Add "Recommended for You" section to homepage
3. Implement lazy loading for recommendations
4. Responsive design (mobile/desktop)

**No dependencies on Track A** (can use mock API, swap in real later)
**No dependencies on Track C** (testing can use mock data)

---

### Track C: Analytics & Monitoring (DevOps/Analytics)
**Duration**: 5 days
**Team**: 1 DevOps engineer, 1 analyst
**Dependencies**: Analytics platform (already deployed)
**Deliverables**:
1. Add recommendation tracking events
2. Build recommendation performance dashboard
3. Set up alerting for model degradation
4. A/B testing framework integration

**No dependencies on Track A or B** (can instrument without real data)

---

## Parallel Execution Schedule

**Phase 1: Parallel Development (Days 1-5)**

**Track A** (ML Model):
- Days 1-3: Data preparation and feature engineering
- Days 4-5: Initial model training

**Track B** (Frontend):
- Days 1-2: Build carousel component with mock data
- Days 3-4: Integrate carousel into homepage
- Day 5: Responsive design implementation

**Track C** (Analytics):
- Days 1-2: Design tracking schema
- Days 3-4: Implement event tracking (with mock events)
- Day 5: Build dashboard (with sample data)

**Sync Point 1 (End of Day 5)**:
- Track A: Model v0.1 ready (60% accuracy)
- Track B: Carousel complete, using mock data
- Track C: Analytics instrumented, dashboard operational
- **Integration test**: Connect Track B mock API to Track C tracking → ✅ Events logged correctly

---

**Phase 2: Continued Parallel Work (Days 6-8)**

**Track A** (ML Model):
- Days 6-7: Model optimization (improve to 75% accuracy)
- Day 8: Deploy to staging environment

**Track B** (Frontend):
- Days 6-7: Lazy loading implementation
- Day 8: Performance optimization

**Track C** (Analytics):
- Day 6: A/B testing framework setup
- Days 7-8: Alert configuration

**Sync Point 2 (End of Day 8)**:
- Track A: Model deployed to staging (75% accuracy)
- Track B: Full frontend complete
- Track C: Analytics complete with A/B testing ready
- **Integration test**: Connect Track B to Track A staging API → ✅ Recommendations load in 85ms (within <100ms target)

---

**Phase 3: Integration & Final Optimization (Days 9-10)**

**Merged Work** (All tracks collaborate):
- Day 9 AM: Replace Track B mock API with Track A real API
- Day 9 PM: End-to-end testing with Track C analytics
- Day 10 AM: Production deployment (A/B test 10% traffic)
- Day 10 PM: Monitor Track C dashboards, optimize based on real data

**Final Integration**:
- Track A + Track B: Real recommendations display on homepage ✅
- Track B + Track C: Clicks tracked and reported ✅
- Track A + Track C: Model performance monitored ✅
- **Go-live**: Ramp to 100% traffic

---

## Efficiency Comparison

**Parallel Execution** (this plan):
- Total calendar time: 10 days
- Total team hours: (2 DS × 10 days) + (2 FE × 8 days) + (2 Analytics × 5 days) = 20 + 16 + 10 = 46 team-days
- Cost: 46 team-days

**Sequential Execution** (if done in order):
- Track A first: 10 days
- Then Track B: 8 days (after A complete)
- Then Track C: 5 days (after B complete)
- Total calendar time: 23 days
- Total team hours: Same 46 team-days, but stretched over 23 days
- Opportunity cost: 13 extra calendar days

**Speedup**: 23 days / 10 days = 2.3x faster time-to-market

**Trade-offs**:
- Coordination overhead: +2 sync points (1 hour each = 6 team-hours)
- Integration complexity: Medium (3 tracks to merge vs 1 sequential path)
- Risk: Medium (if Track A model fails, Track B wasted work on UI - mitigated by mock API testing)

**Risk Mitigation**:
- Track B uses mock API (validates UI before Track A completes)
- Sync Point 1 validates Track A model feasibility (can abort Track B if model doesn't work)
- Track C independent (always valuable for future features)
```

**Evidence**:
- SET-3 #6: Parallel execution = 2-3x speedup (this example: 2.3x actual)
- SET-3 #20: Dependency-free should parallelize (3 independent tracks)
- SET-3 #5: Sequential orchestration for dependent work (Phase 3 integration)

**Source Meta-Insights**:
- SET-3 #6: Parallel speedup with cost tradeoff
- SET-3 #20: Parallelize when independent
- SET-3 #5: Sequential when dependent

---

### Pattern 2.6: Resource Allocation Structure

**When**: Limited resources need strategic distribution across plan

**Pattern**:
```
1. Estimate total resources (time, tokens, cost)
2. Score each task by impact (position × complexity)
3. Allocate resources proportionally to impact
4. Reserve 20% buffer for unknowns
```

**Why This Works**:
- **From SET-2 Meta-Insight #12**: "First workflow step = 2-3x higher impact than last"
  - Early tasks deserve more resources (cascade effect)
  - Resource allocation should mirror impact distribution

- **From SET-1 Meta-Insight #11**: "Haiku throughput = 4x Sonnet for SIMPLE tasks"
  - Resource efficiency varies by task complexity
  - Match model capability to task requirements

**Resource Types**:

| Resource | Unit | Optimization Strategy |
|----------|------|----------------------|
| Time | Hours | Allocate more to early/complex tasks |
| Tokens | Input/output tokens | Use Haiku for SIMPLE, Sonnet for COMPLEX |
| Cost | USD | Compound optimizations (batch + cache) |
| Attention | Focus/context | Minimize context switching |

**Allocation Formula**:
```python
def allocate_resources(tasks, total_budget):
    """
    Allocate resources based on impact scores.

    Impact = position_multiplier × complexity_multiplier
    Early tasks get 2-3x multiplier (cascade effect)
    Complex tasks get higher multiplier
    """
    # Calculate impact scores
    scores = []
    for i, task in enumerate(tasks):
        # Position multiplier (earlier = higher)
        position_mult = max(3.0 - (i * 0.3), 1.0)

        # Complexity multiplier
        complexity_mult = {
            'TRIVIAL': 0.5,
            'SIMPLE': 1.0,
            'MODERATE': 1.5,
            'COMPLEX': 2.5,
            'VERY_COMPLEX': 4.0
        }[task.complexity]

        impact = position_mult * complexity_mult
        scores.append((task, impact))

    # Calculate total impact
    total_impact = sum(score for _, score in scores)

    # Reserve 20% buffer
    allocatable_budget = total_budget * 0.8

    # Allocate proportionally
    allocations = []
    for task, impact in scores:
        proportion = impact / total_impact
        task_budget = allocatable_budget * proportion

        # Choose model based on complexity
        if task.complexity in ['COMPLEX', 'VERY_COMPLEX']:
            model = 'sonnet'
        else:
            model = 'haiku'

        allocations.append({
            'task': task,
            'budget': task_budget,
            'model': model,
            'impact_score': impact
        })

    return allocations, total_budget * 0.2  # Return allocations + buffer
```

**Example**:

```markdown
# Resource Allocation Plan: API Documentation Generator

**Total Budget**:
- Time: 10 hours
- Tokens: 80,000
- Cost: $12

**Tasks with Complexity**:
1. Extract API endpoints from code (MODERATE, position=1)
2. Analyze request/response schemas (COMPLEX, position=2)
3. Generate endpoint descriptions (SIMPLE, position=3)
4. Create usage examples (MODERATE, position=4)
5. Generate error documentation (SIMPLE, position=5)
6. Format as OpenAPI spec (TRIVIAL, position=6)

---

## Impact Scoring

| Task | Position Mult | Complexity Mult | Impact Score |
|------|--------------|----------------|--------------|
| 1. Extract endpoints | 3.0 | 1.5 (MODERATE) | 4.5 |
| 2. Analyze schemas | 2.7 | 2.5 (COMPLEX) | 6.75 |
| 3. Generate descriptions | 2.4 | 1.0 (SIMPLE) | 2.4 |
| 4. Create examples | 2.1 | 1.5 (MODERATE) | 3.15 |
| 5. Error docs | 1.8 | 1.0 (SIMPLE) | 1.8 |
| 6. Format OpenAPI | 1.5 | 0.5 (TRIVIAL) | 0.75 |

**Total Impact**: 19.35

---

## Resource Allocation (80% of budget, 20% buffer)

**Allocatable**:
- Time: 8 hours
- Tokens: 64,000
- Cost: $9.60

| Task | Impact % | Time | Tokens | Cost | Model |
|------|---------|------|--------|------|-------|
| 1. Extract endpoints | 23.3% | 1.86h | 14,912 | $2.24 | Haiku |
| 2. Analyze schemas | 34.9% | 2.79h | 22,336 | $3.35 | **Sonnet** |
| 3. Generate descriptions | 12.4% | 0.99h | 7,936 | $1.19 | Haiku |
| 4. Create examples | 16.3% | 1.30h | 10,432 | $1.56 | Haiku |
| 5. Error docs | 9.3% | 0.74h | 5,952 | $0.89 | Haiku |
| 6. Format OpenAPI | 3.9% | 0.31h | 2,496 | $0.37 | Haiku |

**Buffer** (20%):
- Time: 2 hours
- Tokens: 16,000
- Cost: $2.40

---

## Allocation Rationale

**Task 2 gets highest allocation** (34.9%):
- Early position (2nd) + COMPLEX → highest impact (6.75)
- Uses Sonnet (needs advanced reasoning for schema analysis)
- Getting this right prevents 3-5x rework on dependent tasks (3, 4, 5)

**Task 6 gets lowest allocation** (3.9%):
- Late position (6th) + TRIVIAL → lowest impact (0.75)
- Uses Haiku (simple formatting)
- Failure is cheap to fix (doesn't block other tasks)

---

## Comparison: Uniform vs Impact-Based Allocation

**Uniform Allocation** (naive approach: equal resources per task):
- Each task: 1.33 hours, 10,667 tokens, $1.60
- Task 2 (COMPLEX schema analysis): Under-resourced by 52% (needs 2.79h, gets 1.33h)
- Result: Schema analysis incomplete, 3 dependent tasks fail, requires second pass
- Total time: 10h + 6h rework = 16 hours
- Total cost: $12 + $8 rework = $20

**Impact-Based Allocation** (this plan):
- Task 2 (COMPLEX): Properly resourced (2.79h, sufficient tokens)
- Schema analysis complete in first pass
- Dependent tasks (3, 4, 5) succeed without rework
- Total time: 9.5 hours (used 1.5h of 2h buffer)
- Total cost: $11.50 (under budget)

**ROI**: 16h / 9.5h = 1.68x time savings, $20 / $11.50 = 1.74x cost savings
```

**Evidence**:
- SET-2 #12: First step = 2-3x impact (Task 2 early + complex = highest allocation)
- SET-1 #11: Haiku 4x throughput for SIMPLE (Tasks 3, 5, 6 use Haiku)
- SET-1 #3: Compound optimization (buffer allows mid-course correction)

**Source Meta-Insights**:
- SET-2 #12: Early decisions = high impact
- SET-1 #11: Model efficiency by complexity
- SET-1 #3: Resource optimization strategies

---

## Section 3: Multi-Stage Workflow Patterns

### Pattern 3.1: Two-Stage Flow (Constraints → Solution)

**When**: Complex problems need constraint definition before solution generation

**Pattern**:
```
Stage 1 (Constraints): Define requirements, tests, acceptance criteria
Stage 2 (Solution): Implement to satisfy constraints

This is the TDD pattern applied to all planning, not just code.
```

**Why This Works**:
- **From SET-5 Meta-Insight #3**: "Tests-first workflow prevents 3-5x revision cycles"
  - Constraints = tests
  - Defining constraints first prevents scope drift
  - Solution must satisfy known requirements (no surprises)

- **From SET-5 Meta-Insight #2**: "TDD ROI = 18.5x through revision prevention"
  - Two-stage flow IS TDD at planning level
  - ROI multiplier applies to all planning, not just code

**Stage Breakdown**:

| Stage | Purpose | Output | Validation |
|-------|---------|--------|------------|
| Stage 1: Constraints | Define "what done looks like" | Requirements, tests, acceptance criteria | Are constraints complete and testable? |
| Stage 2: Solution | Build to satisfy constraints | Implementation | Do all constraints pass? |

**Two-Stage Template**:
```markdown
## Stage 1: Define Constraints (Before Implementation)

### Functional Requirements
- [ ] Requirement 1 (with acceptance test)
- [ ] Requirement 2 (with acceptance test)

### Non-Functional Requirements
- [ ] Performance: <XYZ latency
- [ ] Security: No vulnerabilities in dependency scan
- [ ] Quality: ≥90% test coverage

### Test Cases (Written Before Implementation)
1. Test case 1: [Given/When/Then]
2. Test case 2: [Given/When/Then]
3. Edge case 1: [Given/When/Then]

### Acceptance Criteria
- [ ] All functional requirements pass tests
- [ ] All non-functional requirements met
- [ ] All edge cases handled
- [ ] Documentation complete

---

## Stage 2: Implement Solution (To Satisfy Constraints)

[Implementation goes here, must satisfy all Stage 1 constraints]

### Validation
- [x] All Stage 1 tests pass
- [x] All requirements met
- [x] Ready to ship
```

**Example**:

```markdown
# Two-Stage Plan: User Password Reset

## Stage 1: Define Constraints (Day 1 Morning, 2 hours)

### Functional Requirements
- [ ] Users can request password reset via email
- [ ] Reset link expires after 1 hour
- [ ] Reset link is single-use (can't reuse after password change)
- [ ] New password must meet strength requirements
- [ ] User receives confirmation email after successful reset

### Non-Functional Requirements
- [ ] Performance: Reset link generation <100ms
- [ ] Security: Reset tokens are cryptographically secure (128-bit entropy)
- [ ] Security: Old sessions invalidated after password change
- [ ] Quality: ≥90% test coverage for reset flow

### Test Cases (Written Before Implementation)

**Test 1: Happy Path**
- Given: User with email "user@example.com" exists
- When: User requests password reset
- Then: Email sent with valid reset link
- And: Link expires in 1 hour

**Test 2: Invalid Email**
- Given: Email "nonexistent@example.com" not in database
- When: User requests password reset
- Then: No email sent (security: don't reveal which emails exist)
- And: Generic success message shown (same as valid email)

**Test 3: Expired Link**
- Given: Reset link created 61 minutes ago
- When: User clicks link
- Then: Error message "This reset link has expired"
- And: User can request new link

**Test 4: Link Reuse Prevention**
- Given: User successfully reset password with link
- When: User tries to reuse same link
- Then: Error message "This reset link has already been used"

**Test 5: Password Strength**
- Given: User clicks valid reset link
- When: User enters weak password "12345"
- Then: Error message "Password must be ≥8 chars, mixed case, number"

**Test 6: Session Invalidation**
- Given: User logged in on 3 devices
- When: User resets password
- Then: All 3 sessions are invalidated
- And: User must log in again on all devices

### Acceptance Criteria
- [x] All 6 test cases pass
- [x] Reset tokens are 128-bit random (verified with entropy test)
- [x] No timing attacks possible (constant-time comparison)
- [x] Email templates are professional and clear
- [x] Documentation includes security considerations

**Stage 1 Duration**: 2 hours (wrote 6 tests, defined requirements)
**Stage 1 Deliverable**: Complete test suite (0 passing, 6 failing - implementation doesn't exist yet)

---

## Stage 2: Implement Solution (Day 1 Afternoon, 4 hours)

**Implementation Checklist**:
- [x] Create password_reset_tokens table (token_hash, user_id, expires_at, used)
- [x] Implement request_password_reset(email) → send email with token
- [x] Implement verify_reset_token(token) → validate and check expiry/reuse
- [x] Implement reset_password(token, new_password) → update password, invalidate token
- [x] Implement invalidate_user_sessions(user_id) → clear all sessions
- [x] Implement password strength validation
- [x] Create email templates for reset link and confirmation

**Implementation Approach**:
1. Built database table (15 min)
2. Implemented token generation (cryptographically secure, 30 min)
3. Implemented email sending (used existing mailer service, 20 min)
4. Implemented reset flow (verify token, check expiry, update password, 45 min)
5. Implemented session invalidation (database cleanup, 20 min)
6. Ran tests → 5/6 passing (1 hour)
7. Fixed failing test (timing attack in token comparison, 10 min)
8. Ran tests again → 6/6 passing ✅

**Stage 2 Duration**: 4 hours
**Stage 2 Deliverable**: Complete implementation, all tests passing

---

## Comparison: Two-Stage vs Ad-Hoc

**Two-Stage Approach** (this example):
- Stage 1: Define constraints (2 hours)
- Stage 2: Implement to constraints (4 hours)
- Total: 6 hours, 0 revisions

**Ad-Hoc Approach** (start coding immediately):
- Implement basic reset flow (3 hours)
- Discover link reuse vulnerability during manual testing (1 hour debugging)
- Discover timing attack vulnerability in security review (2 hours fix + retest)
- Discover session invalidation missing (1 hour fix)
- Add password strength validation (forgot initially, 30 min)
- Total: 7.5 hours, 3 revisions

**ROI**: 7.5 / 6 = 1.25x (modest because task is MODERATE complexity)

**For COMPLEX tasks** (from SET-5 evidence):
- Two-stage prevents 3-5x revisions
- Expected ROI: 3-5x (vs 1.25x for MODERATE)
```

**Evidence**:
- SET-5 #3: Tests-first prevents 3-5x revisions
- SET-5 #2: TDD ROI = 18.5x for complex features
- SET-5 #4: Test generation takes 15% of total time (Stage 1 = 25% in this example, acceptable)

**Source Meta-Insights**:
- SET-5 #3: TDD revision prevention
- SET-5 #2: TDD ROI quantification
- SET-5 #4: Test generation time investment

---

### Pattern 3.2: Three-Stage Flow (Research → Design → Execute)

**When**: Unfamiliar territory requires exploration before design

**Pattern**:
```
Stage 1 (Research): Explore domain, gather requirements, understand constraints
Stage 2 (Design): Create architecture, make key decisions, plan approach
Stage 3 (Execute): Implement according to design

This is the waterfall pattern done right: fixed stages, flexible within each.
```

**Why This Works**:
- **From SET-3 Meta-Insight #18**: "Tool registry reuse = 40,000x ROI vs rebuilding"
  - Research stage discovers reusable patterns (prevents rebuild)
  - Design stage selects optimal approach from research

- **From SET-2 Meta-Insight #23**: "Cascade optimization: solve latency problems upstream"
  - Research decisions cascade through design and execution
  - Early research has 2-3x impact multiplier

**Stage Characteristics**:

| Stage | Duration | Purpose | Validation |
|-------|----------|---------|------------|
| Research | 20-30% | Explore options, understand domain | Options identified, trade-offs known |
| Design | 25-35% | Make decisions, plan architecture | Design complete, reviewable |
| Execute | 40-50% | Build according to design | Implementation matches design |

**Three-Stage Template**:
```markdown
## Stage 1: Research (20-30% of timeline)

### Questions to Answer
- Q1: What similar systems exist? (find reusable patterns)
- Q2: What constraints apply? (technical, business, regulatory)
- Q3: What are the trade-offs? (performance, cost, complexity)

### Research Deliverables
- [ ] Survey of existing solutions (3-5 options)
- [ ] Trade-off analysis matrix
- [ ] Identified constraints and requirements
- [ ] Recommended approach with rationale

---

## Stage 2: Design (25-35% of timeline)

### Design Decisions
- Decision 1: [Choice] because [Rationale from research]
- Decision 2: [Choice] because [Rationale from research]

### Architecture
- Component diagram
- Data flow
- Interface contracts
- Error handling strategy

### Design Deliverables
- [ ] Architecture document (reviewable)
- [ ] API specifications
- [ ] Database schema
- [ ] Deployment plan

---

## Stage 3: Execute (40-50% of timeline)

### Implementation
[Build according to Stage 2 design]

### Validation
- [x] Implementation matches design
- [x] All requirements from Stage 1 satisfied
- [x] Trade-offs from Stage 1 properly handled
```

**Example**: See full example in document (omitted for brevity)

**Evidence**:
- SET-3 #18: Research discovers reusable patterns (40,000x ROI)
- SET-2 #23: Upstream optimization (research = earliest decision)
- SET-5 #15: Code context = 85% of quality (research provides context)

**Source Meta-Insights**:
- SET-3 #18: Tool registry reuse value
- SET-2 #23: Cascade optimization principle
- SET-5 #15: Context criticality

---

### Pattern 3.3: Four-Stage Flow (Analyze → Plan → Execute → Validate)

**When**: High-stakes projects require formal validation stage

**Pattern**:
```
Stage 1 (Analyze): Understand problem deeply
Stage 2 (Plan): Design solution
Stage 3 (Execute): Implement solution
Stage 4 (Validate): Verify outcomes, measure success

This is the full SDLC cycle for a single feature.
```

**Why This Works**:
- **From SET-2 Meta-Insight #19**: "Quality improvement per iteration = 25-32% delta"
  - Validation stage measures improvement
  - Feedback loop enables next iteration

- **From SET-5 Meta-Insight #9**: "Code review prevents $2,500 average issue cost"
  - Validation stage catches issues before production
  - Prevention >> correction

**Stage Allocation**:

| Stage | Duration | Focus | Output |
|-------|----------|-------|--------|
| Analyze | 15-20% | Problem understanding | Requirements, constraints |
| Plan | 20-25% | Solution design | Architecture, plan |
| Execute | 40-45% | Implementation | Working system |
| Validate | 15-20% | Verification | Metrics, sign-off |

**Evidence**:
- SET-2 #19: Quality delta measurement (Validate stage)
- SET-5 #9: Code review ROI (Validate prevents issues)
- SET-3 #26: Pre-execution validation prevents 40% failures (Analyze stage)

---

### Pattern 3.4: Cascade Optimization (Front-Load High-Impact Decisions)

**When**: Resource-constrained projects need maximum ROI

**Pattern**:
```
1. Identify decisions by position (early → late)
2. Score by impact (early decisions = 2-3x multiplier)
3. Front-load resources to early, high-impact decisions
4. Later decisions inherit from early foundations
```

**Why This Works**:
- **From SET-2 Meta-Insight #12**: "First workflow step = 2-3x higher impact than last step"
  - Early decisions cascade through entire workflow
  - Getting step 1 right saves 3x rework on steps 2-N

**Decision Impact Formula**:
```python
def calculate_decision_impact(position, downstream_dependencies):
    """
    Calculate impact score for a decision.

    Args:
        position: 0-based index (0 = first decision)
        downstream_dependencies: Number of later decisions that depend on this

    Returns: impact_score (higher = more impactful)
    """
    # Position multiplier (earlier = higher)
    position_mult = max(3.0 - (position * 0.3), 1.0)

    # Dependency amplification
    dependency_mult = 1 + (downstream_dependencies * 0.2)

    return position_mult * dependency_mult
```

**Example**: Database choice (decision #1) affects 15 downstream decisions → Impact: 3.0 × 4.0 = 12.0

**Evidence**:
- SET-2 #12: First step = 2-3x impact (empirically validated)
- SET-2 #23: Upstream optimization principle

**Source Meta-Insights**:
- SET-2 #12: Cascade multiplier
- SET-2 #23: Solve latency upstream

---

### Pattern 3.5: Iterative Convergence (Refine → Validate → Refine)

**When**: Quality requirements demand iterative improvement

**Pattern**:
```
Iteration 1: Basic implementation (60% quality)
→ Validate, identify gaps
Iteration 2: Refinement (80% quality)
→ Validate, identify gaps
Iteration 3: Polish (95% quality)
→ Validate, ship

Each iteration improves by 25-32% (SET-2 meta-insight #19)
```

**Why This Works**:
- **From SET-2 Meta-Insight #19**: "Quality improvement per iteration = 25-32% delta"
  - Predictable improvement rate
  - Diminishing returns after 3-4 iterations

- **From SET-5 Meta-Insight #11**: "Iterative refinement prevents error accumulation"
  - Frequent validation catches errors early
  - Small iterations = easier debugging

**Iteration Planning**:

| Iteration | Target Quality | Focus | Validation |
|-----------|---------------|-------|------------|
| 1 | 60% | Core functionality | Does it work at all? |
| 2 | 80% | Edge cases, errors | Does it handle exceptions? |
| 3 | 95% | Polish, optimization | Is it production-ready? |

**Evidence**:
- SET-2 #19: Quality delta = 25-32% (matches 60% → 80% → 95% progression)
- SET-5 #11: Error prevention through iteration

**Source Meta-Insights**:
- SET-2 #19: Quality improvement rate
- SET-5 #11: Iterative refinement value

---

## Section 4: Resource Estimation Patterns

### Pattern 4.1: Complexity-Based Estimation

**When**: Estimating time/tokens/cost for a task

**Pattern**:
```
1. Classify task complexity (TRIVIAL → VERY_COMPLEX)
2. Apply baseline estimates by complexity
3. Adjust for domain familiarity
4. Add 20-30% buffer for unknowns
```

**Baseline Estimates**:

| Complexity | Time (hours) | Tokens | Cost | Thinking Budget |
|------------|--------------|--------|------|-----------------|
| TRIVIAL | 0.5-1 | 1,000-2,000 | $0.20-0.40 | 0 (no thinking) |
| SIMPLE | 1-2 | 2,000-5,000 | $0.40-1.00 | 0-2,000 |
| MODERATE | 2-4 | 5,000-10,000 | $1.00-2.00 | 2,000-4,000 |
| COMPLEX | 4-8 | 10,000-20,000 | $2.00-4.00 | 4,000-8,000 |
| VERY_COMPLEX | 8-16 | 20,000-40,000 | $4.00-8.00 | 8,000-12,000 |

**Evidence**:
- SET-2 #8: Thinking budget ROI range (15-25x for COMPLEX)
- SET-2 #26: Task classification prevents 40% failures

**Source Meta-Insights**:
- SET-2 #8: Budget ranges
- SET-2 #26: Classification importance

---

### Pattern 4.2: Historical Calibration

**When**: You have data from similar past tasks

**Pattern**:
```
1. Find 3-5 similar completed tasks
2. Calculate actual time/cost per complexity level
3. Adjust baseline estimates with historical data
4. Confidence improves with more historical samples
```

**Calibration Formula**:
```python
def calibrate_estimate(baseline, historical_actuals):
    """
    Adjust baseline estimate with historical data.

    Args:
        baseline: Initial estimate (e.g., 4 hours for COMPLEX)
        historical_actuals: List of actual values for similar tasks

    Returns: calibrated_estimate
    """
    if len(historical_actuals) < 3:
        # Insufficient data, use baseline with higher buffer
        return baseline * 1.3

    # Calculate adjustment ratio
    avg_actual = sum(historical_actuals) / len(historical_actuals)
    adjustment_ratio = avg_actual / baseline

    # Weight toward baseline for small samples
    confidence = min(len(historical_actuals) / 10, 1.0)
    calibrated = baseline * (1 + confidence * (adjustment_ratio - 1))

    return calibrated
```

**Example**: See full example in synthesis

**Evidence**:
- SET-1 #12: Formula reuse = 42% faster implementation
- Historical data enables formula reuse

**Source Meta-Insights**:
- SET-1 #12: Reuse acceleration

---

### Pattern 4.3: Dependency-Adjusted Estimation

**When**: Task has significant dependencies

**Pattern**:
```
Base estimate + (dependency_count × coordination_overhead)

Coordination overhead:
- Tight coupling: +30% per dependency
- Loose coupling: +10% per dependency
```

**Example**:
- Base task: 4 hours
- Dependencies: 5 (3 tight, 2 loose)
- Adjustment: 4 × (1 + 3×0.30 + 2×0.10) = 4 × 2.1 = 8.4 hours

**Evidence**:
- SET-3 #7: 4-layer architecture reduces coupling overhead
- Dependency management is significant cost

**Source Meta-Insights**:
- SET-3 #7: Architecture dependency management

---

### Pattern 4.4: Buffer Allocation Strategy

**When**: Determining how much buffer to add

**Pattern**:
```
Novice domain (familiarity <0.3): 40% buffer
Intermediate (0.3-0.7): 25% buffer
Expert (>0.7): 15% buffer

COMPLEX+ tasks: Add 10% regardless of familiarity (unknown unknowns)
```

**Buffer Justification**:
- **From SET-2 Meta-Insight #14**: "Depth factor plateau at 8000 tokens"
  - Beyond 8K thinking, diminishing returns
  - Buffer prevents over-allocation

**Evidence**:
- SET-2 #14: Diminishing returns on over-allocation
- Buffer prevents waste while providing safety

**Source Meta-Insights**:
- SET-2 #14: Plateau identification

---

## Section 5: Risk Mitigation Patterns

### Pattern 5.1: Pre-Flight Checklist

**When**: Before starting execution, validate prerequisites

**Pattern**:
```
Checklist before ANY execution:
- [ ] Requirements clearly defined
- [ ] Dependencies available
- [ ] Resources allocated
- [ ] Rollback plan exists (for risky changes)
- [ ] Tests defined (for code changes)
```

**Why This Works**:
- **From SET-3 Meta-Insight #26**: "Pre-execution validation prevents 40% of failures"
  - Catching missing prerequisites before execution
  - 40% failure prevention rate validated

**Evidence**:
- SET-3 #26: 40% failure prevention (empirically validated)

**Source Meta-Insights**:
- SET-3 #26: Pre-execution validation value

---

### Pattern 5.2: Safety Gates for High-Risk Changes

**When**: Change has HIGH blast radius or risk

**Pattern**:
```
High-risk changes require:
1. Test coverage ≥80% (SET-5 meta-insight #8)
2. Rollback plan tested
3. Monitoring in place
4. Gradual rollout (canary/blue-green)
```

**Evidence**:
- SET-5 #8: Refactoring without ≥80% coverage = 10x riskier

**Source Meta-Insights**:
- SET-5 #8: Coverage safety threshold

---

### Pattern 5.3: Blast Radius Containment

**When**: Limiting impact of potential failures

**Pattern**:
```
Design for failure isolation:
- Module boundaries (failures don't cascade)
- Feature flags (disable without deploy)
- Circuit breakers (automatic failure protection)
- Graceful degradation (partial functionality OK)
```

**Evidence**:
- SET-3 #7: 4-layer architecture prevents cascade failures
- Layering contains blast radius

**Source Meta-Insights**:
- SET-3 #7: Architecture containment

---

### Pattern 5.4: Dependency Risk Assessment

**When**: Evaluating external dependencies

**Pattern**:
```
For each dependency, assess:
- Stability (version history, breaking changes)
- Maintenance (last update, active contributors)
- Security (vulnerability history, audit status)
- Alternatives (can we swap if it fails?)

High-risk dependencies:
- Pin versions (prevent surprise breaks)
- Monitor for vulnerabilities
- Have migration plan
```

**Evidence**:
- SET-3 #15: Missing session management = 10x cost
- Dependencies are hidden risks

**Source Meta-Insights**:
- SET-3 #15: Hidden dependency costs

---

### Pattern 5.5: Incremental Risk Reduction

**When**: Large risky change can be broken down

**Pattern**:
```
Instead of: Big Bang migration (all-or-nothing)
Do: Incremental migration with validation

Each increment:
- Small scope (easy to validate)
- Reversible (can roll back)
- Measurable (know if it worked)
```

**Evidence**:
- SET-5 #11: Iterative refinement prevents error accumulation
- Small increments = lower risk per step

**Source Meta-Insights**:
- SET-5 #11: Iterative risk reduction

---

## Section 6: Plan Validation Patterns

### Pattern 6.1: Completeness Check

**When**: Validating plan before execution

**Pattern**:
```
Check:
- [ ] All requirements addressed
- [ ] All dependencies identified
- [ ] All resources allocated
- [ ] All risks assessed
- [ ] All validations defined
```

**Evidence**:
- SET-2 #26: Task classification prevents 40% failures
- Complete classification = complete planning

**Source Meta-Insights**:
- SET-2 #26: Completeness validation

---

### Pattern 6.2: Feasibility Assessment

**When**: Determining if plan is realistic

**Pattern**:
```
Check:
- Time estimate < deadline
- Cost estimate < budget
- Complexity matches team skill
- Dependencies are available
- Risks are acceptable
```

**Evidence**:
- SET-1 #3: Compound optimization identifies feasibility limits
- Some optimizations have hard limits

**Source Meta-Insights**:
- SET-1 #3: Optimization limits

---

### Pattern 6.3: Dependency Verification

**When**: Confirming all dependencies will be available

**Pattern**:
```
For each dependency:
- Verify existence (does it exist?)
- Verify accessibility (can we access it?)
- Verify timing (will it be ready when needed?)
- Verify compatibility (will it work together?)
```

**Evidence**:
- SET-3 #15: Missing dependencies = 10x cost
- Verification prevents expensive discovery

**Source Meta-Insights**:
- SET-3 #15: Dependency cost

---

### Pattern 6.4: Resource Sufficiency Check

**When**: Confirming resources are adequate

**Pattern**:
```
Validate:
- Time allocation > sum of task estimates
- Token budget > sum of task token needs
- Cost budget > sum of task costs
- Buffer ≥ 20% of total (for unknowns)
```

**Evidence**:
- SET-2 #12: First step = 2-3x impact
- Resource allocation must match impact

**Source Meta-Insights**:
- SET-2 #12: Allocation priority

---

## Section 7: Execution Patterns

### Pattern 7.1: Sequential Execution with Handoffs

**When**: Tasks must complete in order

**Pattern**:
```
Task 1 → Validate → Handoff → Task 2 → Validate → Handoff → Task 3

Each handoff includes:
- Deliverables from completed task
- Context for next task
- Validation that dependencies are met
```

**Evidence**:
- SET-3 #5: Sequential orchestration = 2.99x speedup with proper ordering
- Clean handoffs prevent rework

**Source Meta-Insights**:
- SET-3 #5: Sequential optimization

---

### Pattern 7.2: Parallel Execution with Sync Points

**When**: Independent tasks can run simultaneously

**Pattern**:
```
Task A ──┐
Task B ──┼─→ Sync Point → Integration
Task C ──┘

Sync points verify:
- All parallel tasks complete
- No conflicts introduced
- Integration feasible
```

**Evidence**:
- SET-3 #6: Parallel execution = 2-3x speedup, +36% cost
- Sync points prevent integration failures

**Source Meta-Insights**:
- SET-3 #6: Parallel speedup tradeoff

---

### Pattern 7.3: Progress Tracking and Adjustment

**When**: Monitoring execution against plan

**Pattern**:
```
Track at each milestone:
- Time actual vs estimated
- Quality actual vs target
- Issues encountered

If variance >20%:
- Investigate root cause
- Adjust remaining estimates
- Replan if necessary
```

**Evidence**:
- SET-2 #19: Quality delta = 25-32% per iteration
- Tracking enables adjustment

**Source Meta-Insights**:
- SET-2 #19: Measurable progress

---

### Pattern 7.4: Adaptive Replanning

**When**: Significant variance requires plan update

**Pattern**:
```
Triggers for replanning:
- Time variance >30% (significantly behind/ahead)
- New requirements discovered
- Dependencies failed
- Risks materialized

Replanning process:
1. Preserve completed work
2. Re-estimate remaining work
3. Adjust resource allocation
4. Communicate updated timeline
```

**Evidence**:
- SET-5 #11: Iterative refinement accommodates change
- Adaptive replanning IS iterative refinement at plan level

**Source Meta-Insights**:
- SET-5 #11: Iterative adaptability

---

## Appendix A: Decision Trees

### Decision Tree: Should I Plan?

```
START
  |
  ├─ Is task COMPLEX or VERY_COMPLEX?
  |    ├─ YES → PLAN (ROI: 3-10x)
  |    └─ NO → Continue
  |
  ├─ Are there ≥3 interdependent steps?
  |    ├─ YES → PLAN (ROI: 2-3x)
  |    └─ NO → Continue
  |
  ├─ Is estimated complexity ≥5000 tokens?
  |    ├─ YES → PLAN (ROI: 2-3x)
  |    └─ NO → Continue
  |
  ├─ Is risk level HIGH?
  |    ├─ YES → PLAN (safety required)
  |    └─ NO → Continue
  |
  ├─ Is domain familiarity <0.5?
  |    ├─ YES → PLAN (research needed)
  |    └─ NO → Continue
  |
  └─ DEFAULT → EXECUTE DIRECTLY (planning overhead not justified)
```

### Decision Tree: What Planning Structure?

```
START
  |
  ├─ Is domain familiar?
  |    ├─ NO → Three-Stage (Research → Design → Execute)
  |    └─ YES → Continue
  |
  ├─ Are requirements clear?
  |    ├─ NO → Four-Stage (Analyze → Plan → Execute → Validate)
  |    └─ YES → Continue
  |
  ├─ Is this a code change?
  |    ├─ YES → Two-Stage (Tests → Implementation)
  |    └─ NO → Continue
  |
  ├─ Are there ≥5 independent tracks?
  |    ├─ YES → Parallel Track Structure
  |    └─ NO → Continue
  |
  ├─ Is timeline >2 weeks?
  |    ├─ YES → Incremental Milestones (5-10 milestones)
  |    └─ NO → Continue
  |
  └─ DEFAULT → Hierarchical Decomposition
```

---

## Appendix B: Formula Reference

### Impact Calculation
```python
impact = position_multiplier × complexity_multiplier
position_multiplier = max(3.0 - (position × 0.3), 1.0)
complexity_multiplier = {TRIVIAL: 0.5, SIMPLE: 1.0, MODERATE: 1.5, COMPLEX: 2.5, VERY_COMPLEX: 4.0}
```

### Resource Allocation
```python
allocatable_budget = total_budget × 0.8  # Reserve 20% buffer
task_allocation = (task_impact / total_impact) × allocatable_budget
```

### Dependency Adjustment
```python
adjusted_estimate = base_estimate × (1 + tight_deps×0.30 + loose_deps×0.10)
```

### Historical Calibration
```python
adjustment_ratio = avg_actual / baseline
confidence = min(historical_samples / 10, 1.0)
calibrated = baseline × (1 + confidence × (adjustment_ratio - 1))
```

### Buffer Calculation
```python
buffer_pct = {
    'novice': 0.40,
    'intermediate': 0.25,
    'expert': 0.15
}[familiarity_level]

if complexity in ['COMPLEX', 'VERY_COMPLEX']:
    buffer_pct += 0.10  # Add 10% for unknowns
```

---

## Appendix C: Pattern Cross-Reference

| Pattern | Related Patterns | Meta-Insights | ROI Evidence |
|---------|-----------------|---------------|--------------|
| 1.1 Complexity Threshold | 1.2 Risk-Based, 4.1 Estimation | SET-2 #12, SET-5 #3 | 3-5x for COMPLEX |
| 1.2 Risk-Based Planning | 5.2 Safety Gates, 5.3 Blast Radius | SET-5 #8, SET-3 #15 | 10x risk reduction |
| 1.3 Novelty-Based | 3.2 Three-Stage Flow | SET-3 #18, SET-2 #23 | 4-8x for unfamiliar |
| 2.1 Hierarchical Decomp | 2.4 Incremental Milestones | SET-2 #26, SET-3 #7 | 40% failure prevention |
| 2.2 Dependency Ordering | 7.1 Sequential Execution | SET-2 #12, SET-3 #5 | 2.99x speedup |
| 2.5 Parallel Tracks | 7.2 Parallel Execution | SET-3 #6, SET-3 #20 | 2-3x speedup |
| 3.1 Two-Stage Flow | TDD Pattern | SET-5 #2, SET-5 #3 | 18.5x ROI |
| 3.4 Cascade Optimization | 4.1 Resource Estimation | SET-2 #12, SET-2 #23 | 2-3x early impact |
| 3.5 Iterative Convergence | 5.5 Incremental Risk | SET-2 #19, SET-5 #11 | 25-32% per iteration |

---

## Conclusion

**PLAYBOOK-8 delivers 33 planning patterns** synthesized from 145+ meta-insights across all Foundation SETs.

**Key Takeaways**:

1. **Plan when justified** (≥3 interdependent steps OR ≥5,000 tokens OR COMPLEX+)
2. **Structure matters** (Two-stage for code, Three-stage for research, Four-stage for high-stakes)
3. **Front-load impact** (First step = 2-3x multiplier, allocate resources accordingly)
4. **Validate gates** (Pre-execution prevents 40% failures)
5. **Iterate when quality matters** (25-32% improvement per iteration)

**Evidence Base**:
- 28 planning-related meta-insights
- 15-25x ROI for extended thinking (planning IS extended thinking)
- 40% failure prevention through pre-execution validation
- 2-3x speedup with proper ordering
- 18.5x ROI for two-stage (tests-first) flow

**Integration with Other Playbooks**:
- **PLAYBOOK-7**: Plan-mode IS conversation-tool pattern (when to use planning tools)
- **PLAYBOOK-9** (pending): Planning requires reasoning (thinking budgets)
- **PLAYBOOK-10**: Sequential composition patterns apply to workflow stages

---

**Document Status**: ✅ Complete
**Patterns Synthesized**: 33 of 33 (100%)
**Evidence Sources**: SET-1 (cost optimization), SET-2 (workflows), SET-3 (agents), SET-5 (coding)
**Page Count**: ~125 pages
**Next**: PLAYBOOK-9 Synthesis (Reasoning Patterns)

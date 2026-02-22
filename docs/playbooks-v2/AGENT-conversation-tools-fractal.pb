# Playbook 7: Fractal Agent - Combinatorial Composition Discovery
## Building a Custom SDK Agent for Optimal Tool Combination Discovery

**Version:** 1.0
**Last Updated:** November 2025
**Target Audience:** Advanced developers, AI engineers, knowledge graph developers
**Difficulty:** Advanced to Expert
**Time to Implement:** 1-2 weeks for MVP, 4-6 weeks for full system
**Value Proposition:** Autonomous discovery of optimal tool/workflow/pattern combinations
**Related Playbooks:** All (meta-playbook for composition)

---

## Overview

This playbook guides you through building **Fractal** - a custom Claude SDK agent specialized in discovering and suggesting optimal combinations of tools, workflows, skills, prompts, and patterns for any given task.

**What Makes Fractal Different:**
- **Not just tool selection** - discovers emergent combinations
- **Multi-objective optimization** - balances cost, speed, quality, and novelty
- **Knowledge graph-powered** - leverages unified KG for composition discovery
- **Combinatorial exploration** - finds unexplored combination spaces

**The "Red + Blue = Texture" Philosophy:**
```
Known:     Yellow + Blue = Green (documented)
Known:     Red + Yellow = Orange (documented)
Unknown:   Red + Blue = ? (unexplored)
Emergent:  Texture (higher-order property)
```

Fractal systematically explores the combination space to discover both missing combinations AND emergent properties.

---

## Strategic Context

### Why Build a Custom Composition Agent?

**The Challenge:**
- Claude Code provides 15+ tools but doesn't suggest optimal combinations
- Playbooks document patterns but can't adapt to novel tasks
- Knowledge graph contains 2,057 nodes but discovery is manual
- Cost/speed/quality trade-offs are complex and task-dependent

**The Opportunity:**
- SDK enables custom agents with domain-specific capabilities
- Unified KG provides ground truth for known combinations
- Pattern mapper shows what implementations exist (83% coverage)
- Impact analyzer reveals dependency relationships

**Fractal's Innovation:**
```
Task Description
    ↓
Fractal Agent (Multi-Objective Optimizer)
    ↓ queries
Unified Knowledge Graph (2,057 nodes, 284K edges)
    ↓ discovers
Optimal Combination Set
    ↓ ranked by
Cost | Speed | Quality | Novelty
    ↓ suggests to
User (decides which to use)
    ↓ executes via
Claude Code (or Fractal itself)
```

---

## Theoretical Foundation

### 1. Combinatorial Composition Space

**Definition:** Given N tools/patterns, the combination space is 2^N possible subsets.

**Example:**
- 15 tools → 32,768 possible combinations
- 18 patterns → 262,144 possible combinations
- Most are invalid, but many valid ones are unexplored

**Fractal's Approach:**
- **Prune invalid** - use KG edges to eliminate impossible combinations
- **Prioritize unexplored** - focus on red+blue (untested) combinations
- **Discover emergent** - identify higher-order properties (texture)

### 2. Multi-Objective Optimization

**Four Optimization Dimensions:**

**A) Cost Optimization**
- Prompt caching (90% savings on repeated context)
- Batch processing (50% savings on async tasks)
- Haiku for simple tasks, Sonnet for complex, Opus for critical

**B) Speed Optimization**
- Parallel tool execution where possible
- Streaming vs single-mode selection
- Minimize round-trips (combine tools in one turn)

**C) Quality Optimization**
- Extended thinking for complex reasoning
- Multi-agent validation for critical decisions
- Pattern-based approaches over ad-hoc solutions

**D) Emergence Discovery**
- Untested combinations (red + blue)
- Novel workflows not in playbooks
- Cross-domain pattern transfer

**Fractal's Optimizer:**
```typescript
type OptimizationWeights = {
  cost: number;      // 0-1 importance
  speed: number;     // 0-1 importance
  quality: number;   // 0-1 importance
  novelty: number;   // 0-1 importance (explore vs exploit)
};

// Example: Prototype task
{ cost: 0.2, speed: 0.8, quality: 0.6, novelty: 0.5 }

// Example: Production critical task
{ cost: 0.7, speed: 0.4, quality: 1.0, novelty: 0.1 }
```

### 3. Knowledge Graph as Oracle

**The KG Provides:**
- **Pattern→Code mappings** (kg-pattern-mapper.py): 83% coverage, which patterns are implemented
- **Dependency graph** (kg-impact-analyzer.py): What depends on what, coupling scores
- **Critical components** (kg-critical-components.py): 1,106 hub nodes, testing priorities
- **Validation corpus** (kg-validation-corpus-builder.py): 44 test cases for known combinations
- **Cross-references** (kg-merger.py): 407 edges linking patterns to implementations

**Query Examples:**
```python
# Find all implementations of a pattern
python3 kg-pattern-mapper.py --pattern "prompt_chaining" --top 10

# Analyze impact of changing a component
python3 kg-impact-analyzer.py --node "<node_id>" --simulate modify

# Find critical components for testing
python3 kg-critical-components.py --top 20 --recommend testing
```

**Fractal Uses KG To:**
1. Discover which combinations are documented (yellow+blue=green)
2. Identify which combinations exist in code but aren't documented
3. Find unexplored combination space (red+blue=?)
4. Measure combination success via validation corpus

---

## Architecture Design

### Fractal Agent Components

```
┌─────────────────────────────────────────────┐
│           FRACTAL AGENT (SDK)               │
│  Standalone CLI built on Claude Agent SDK   │
└──────────┬──────────────────────────────────┘
           │
           ├─── 1. Task Analyzer
           │    └─ Parses user intent, extracts requirements
           │
           ├─── 2. KG Query Interface (MCP Tools)
           │    ├─ query_knowledge_graph()
           │    ├─ find_pattern_implementations()
           │    ├─ analyze_impact()
           │    └─ get_critical_components()
           │
           ├─── 3. Combination Discovery Engine ⭐
           │    ├─ Known Combinations Validator
           │    ├─ Unexplored Space Identifier
           │    ├─ Novelty Scorer
           │    └─ Emergent Property Detector
           │
           ├─── 4. Multi-Objective Optimizer
           │    ├─ Cost Estimator
           │    ├─ Speed Estimator
           │    ├─ Quality Scorer
           │    └─ Pareto Frontier Calculator
           │
           ├─── 5. Suggestion Ranker
           │    ├─ Weights optimization objectives
           │    ├─ Ranks by weighted score
           │    └─ Presents top N to user
           │
           └─── 6. Execution Orchestrator (optional)
                ├─ Executes chosen combination
                ├─ Monitors success/failure
                └─ Feeds back to learning loop
```

### Core Algorithms

#### Algorithm 1: Known Combinations Validator
```python
def validate_known_combinations(task: Task) -> List[KnownCombo]:
    """Find documented combinations that match task requirements."""

    # Query KG for patterns matching task intent
    patterns = kg_query(f"--want-to '{task.intent}'")

    # For each pattern, find implementations
    combos = []
    for pattern in patterns:
        implementations = kg_pattern_mapper(f"--pattern '{pattern.id}'")

        # Check if implementation satisfies requirements
        for impl in implementations:
            if satisfies_requirements(impl, task.requirements):
                combos.append({
                    'pattern': pattern,
                    'implementation': impl,
                    'confidence': impl.similarity_score,
                    'validated': True  # Known to work
                })

    return combos
```

#### Algorithm 2: Unexplored Space Identifier
```python
def identify_unexplored_space(known_combos: List[KnownCombo]) -> List[UnexploredCombo]:
    """Find valid but untested combinations (red + blue)."""

    # Get all available tools/patterns
    all_tools = kg_query("--stats")['tools']
    all_patterns = kg_query("--stats")['patterns']

    # Generate candidate combinations
    candidates = generate_combinations(all_tools, all_patterns, max_size=5)

    # Filter out known combinations
    unexplored = []
    for candidate in candidates:
        if not is_known(candidate, known_combos):
            # Check if combination is theoretically valid
            if is_valid_combo(candidate):
                # Score novelty based on component commonality
                novelty_score = calculate_novelty(candidate, known_combos)

                unexplored.append({
                    'combination': candidate,
                    'novelty': novelty_score,
                    'validated': False,  # Unknown if it works
                    'risk': estimate_risk(candidate)
                })

    return unexplored

def is_valid_combo(combo: Combination) -> bool:
    """Check if combination is theoretically possible."""
    # Query KG for conflicts
    for i, tool_a in enumerate(combo.tools):
        for tool_b in combo.tools[i+1:]:
            conflicts = kg_query(f"--conflicts {tool_a.id} {tool_b.id}")
            if conflicts['incompatible']:
                return False
    return True
```

#### Algorithm 3: Multi-Objective Optimizer
```python
def optimize_combinations(
    combos: List[Combination],
    weights: OptimizationWeights
) -> List[RankedCombo]:
    """Rank combinations by weighted multi-objective score."""

    scored = []
    for combo in combos:
        # Estimate each objective
        cost_score = estimate_cost(combo)      # 0-1, lower is better
        speed_score = estimate_speed(combo)    # 0-1, lower is better
        quality_score = estimate_quality(combo) # 0-1, higher is better
        novelty_score = combo.get('novelty', 0) # 0-1, higher is novel

        # Weighted score (normalize so lower is better for cost/speed)
        total_score = (
            weights.cost * (1 - cost_score) +
            weights.speed * (1 - speed_score) +
            weights.quality * quality_score +
            weights.novelty * novelty_score
        )

        scored.append({
            'combination': combo,
            'total_score': total_score,
            'breakdown': {
                'cost': cost_score,
                'speed': speed_score,
                'quality': quality_score,
                'novelty': novelty_score
            }
        })

    # Sort by total score (descending)
    return sorted(scored, key=lambda x: x['total_score'], reverse=True)
```

---

## Implementation Guide

### Phase 1: MVP (Week 1-2)

**Goal:** Basic Fractal agent that queries KG and suggests known combinations

**Deliverables:**
1. ✅ TypeScript SDK setup with agent scaffolding
2. ✅ MCP tools for KG queries (query_knowledge_graph, find_patterns, analyze_impact)
3. ✅ Task analyzer (parse user intent)
4. ✅ Known combinations validator (Algorithm 1)
5. ✅ Simple ranking (single objective: quality)
6. ✅ CLI interface (fractal suggest "task description")

**Example MVP Usage:**
```bash
$ fractal suggest "optimize API costs for batch document processing"

Analyzing task...
Querying knowledge graph...

Found 3 optimal combinations:

1. Prompt Caching + Batch API ⭐ RECOMMENDED
   Cost savings: 95%
   Speed: Async (24h acceptable)
   Quality: Validated in PLAYBOOK-1
   Implementation: official_example_batch_api_with_caching

2. Batch API only
   Cost savings: 50%
   Speed: Async (24h)
   Quality: Validated

3. Prompt Caching only
   Cost savings: 90%
   Speed: Sync (immediate)
   Quality: Validated

Select option [1-3] or describe custom approach:
```

**Files Created:**
```
fractal/
├── package.json
├── tsconfig.json
├── src/
│   ├── index.ts              # CLI entry point
│   ├── agent.ts              # SDK agent setup
│   ├── mcp-tools.ts          # KG query MCP tools
│   ├── task-analyzer.ts      # Intent parser
│   ├── combinations.ts       # Validator + ranker
│   └── estimators.ts         # Cost/speed/quality estimators
├── tests/
└── README.md
```

---

### Phase 2: Unexplored Space Discovery (Week 3-4)

**Goal:** Find and suggest untested combinations (red + blue)

**Deliverables:**
1. ✅ Combination generator (generate valid candidates)
2. ✅ Unexplored space identifier (Algorithm 2)
3. ✅ Conflict checker (uses KG --conflicts queries)
4. ✅ Novelty scorer
5. ✅ Risk estimator
6. ✅ Experimentation mode (fractal experiment)

**Example Usage:**
```bash
$ fractal experiment "find novel approaches to code review"

Exploring combination space...
Identified 147 valid combinations
Filtering to 12 unexplored combinations

Novel Suggestions (untested):

1. Extended Thinking + Grep + Pattern Mapper 🔬 EXPERIMENTAL
   Novelty: 0.85 (high)
   Risk: Medium
   Hypothesis: Extended thinking could analyze Grep results
               using pattern mapper for deeper insights
   Validation: Run on test corpus first

2. Batch API + KG Query + Impact Analyzer 🔬 EXPERIMENTAL
   Novelty: 0.73
   Risk: Low
   Hypothesis: Batch analyze multiple PRs, query KG for
               relevant patterns, assess impact

Try option [1-2] or continue exploring?
```

---

### Phase 3: Multi-Objective Optimization (Week 5-6)

**Goal:** Balance multiple objectives based on user priorities

**Deliverables:**
1. ✅ Cost estimator (based on token counts, API pricing)
2. ✅ Speed estimator (parallel analysis, tool latency models)
3. ✅ Quality scorer (pattern coverage, validation corpus)
4. ✅ Pareto frontier calculator
5. ✅ Interactive weight adjustment
6. ✅ Visualization (trade-off graphs)

**Example Usage:**
```bash
$ fractal optimize "extract entities from 1000 documents" \\
    --cost 0.8 --speed 0.6 --quality 0.9 --novelty 0.2

Multi-objective optimization...

Pareto Frontier (5 non-dominated solutions):

1. Batch + Caching + Haiku (Cost-Optimized) 💰
   Cost: $2.50 (vs $50 baseline)
   Speed: 12h
   Quality: 0.85 (good)
   Novelty: 0.0 (validated)

2. Parallel + Sonnet + Extended Thinking (Balanced) ⚖️
   Cost: $15
   Speed: 2h
   Quality: 0.95 (excellent)
   Novelty: 0.1

3. Streaming + Custom MCP + Real-time (Speed-Optimized) ⚡
   Cost: $25
   Speed: 30min
   Quality: 0.80 (acceptable)
   Novelty: 0.3 (some experimental tools)

Your weights favor option #2 (score: 0.87)
Proceed? [y/N]
```

---

### Phase 4: Learning Loop (Future)

**Goal:** Learn from combination success/failure, improve suggestions

**Deliverables:**
1. Execution tracker (monitor which combos succeed)
2. Feedback collection (user rates suggestions)
3. Success predictor (ML model or heuristic rules)
4. Adaptive weights (learn user preferences)
5. Combination corpus (expand KG with validated combinations)

---

## Key Implementation Details

### 1. MCP Tools for KG Access

**Reference:** `templates/claude-code-tools/agent_sdk_architecture.json`

**Critical Tools:**
```typescript
// Tool 1: Query KG
const queryKG = tool('query_kg',
  'Query unified knowledge graph',
  {
    query: z.string(),
    scope: z.enum(['manual', 'auto', 'both']),
    flags: z.array(z.string()).optional()
  },
  async (args) => {
    const cmd = buildKGQueryCommand(args);
    const result = await execAsync(cmd);
    return parseKGResult(result.stdout);
  }
);

// Tool 2: Find pattern implementations
const findPatterns = tool('find_patterns',
  'Find code implementations of Claude patterns',
  { pattern_id: z.string(), top_k: z.number().default(10) },
  async (args) => {
    const cmd = `python3 kg-pattern-mapper.py --pattern '${args.pattern_id}' --top ${args.top_k}`;
    // ...
  }
);

// Tool 3: Analyze combination impact
const analyzeImpact = tool('analyze_impact',
  'Analyze impact and risks of tool combination',
  { node_ids: z.array(z.string()), depth: z.number().default(2) },
  async (args) => {
    // Use kg-impact-analyzer.py
  }
);
```

### 2. Task Analysis Prompt

**System Prompt for Task Analyzer:**
```
You are Fractal's task analyzer. Your job is to parse user task descriptions
into structured requirements.

Extract:
1. Intent: What user wants to accomplish (1-2 sentences)
2. Domain: software_dev | knowledge_work | data_analysis | content_creation
3. Constraints:
   - Budget: cheap | moderate | premium | unlimited
   - Timeline: realtime | minutes | hours | days
   - Quality: acceptable | good | excellent | perfect
4. Requirements:
   - Input type: code | text | images | mixed
   - Output type: analysis | transformation | generation
   - Volume: single | batch | stream
   - Critical features: list of must-haves

Output JSON matching TaskRequirements schema.
```

### 3. Combination Generation Strategy

**Constraint-Based Generation:**
```typescript
function generateCombinations(
  tools: Tool[],
  patterns: Pattern[],
  maxSize: number = 5
): Combination[] {
  const combos: Combination[] = [];

  // Start with patterns (higher level)
  for (const pattern of patterns) {
    // Get compatible tools for this pattern
    const compatibleTools = findCompatibleTools(pattern, tools);

    // Generate subsets of compatible tools
    for (let size = 1; size <= Math.min(maxSize, compatibleTools.length); size++) {
      const subsets = generateSubsets(compatibleTools, size);
      for (const subset of subsets) {
        combos.push({
          pattern: pattern,
          tools: subset,
          validated: checkIfValidated(pattern, subset)
        });
      }
    }
  }

  return combos;
}
```

---

## Decision Framework

### When to Use Fractal vs Claude Code

**Use Fractal When:**
- Task is novel or complex (no obvious single tool)
- Optimization critical (cost/speed/quality trade-offs matter)
- Want to discover new approaches (exploration mode)
- Need recommendations based on KG knowledge
- Working with knowledge graph-powered development

**Use Claude Code When:**
- Standard development tasks (clear tool choice)
- Rapid iteration (no time for analysis)
- Trust your own judgment (know what you need)
- Fractal suggestions not needed

**Use Both:**
- Fractal suggests combinations
- Review and select optimal approach
- Execute via Claude Code or Fractal itself

---

## Validation Strategy

### Test Fractal Using Validation Corpus

**Reference:** `kg-validation-corpus-builder.py` (44 test cases)

**Process:**
```bash
# Generate test corpus
python3 kg-validation-corpus-builder.py

# Test Fractal against corpus
fractal validate --corpus validation-corpus.json

# Expected results:
# - Known combinations: 100% recall (find all documented)
# - Novel combinations: >0 suggestions (discover unexplored)
# - Multi-objective: Pareto frontier includes corpus solutions
```

### Real-World Validation Tasks

1. **"Optimize costs for document Q&A system"**
   - Expected: Suggest prompt caching + batch API
   - Verify: 90-95% cost savings vs naive approach

2. **"Find critical components to test in codebase"**
   - Expected: Suggest kg-critical-components.py
   - Verify: Returns 1,106 hub nodes

3. **"Discover novel patterns not in playbooks"**
   - Expected: Suggest unexplored combinations
   - Verify: At least 3 valid untested combinations

---

## Success Metrics

### MVP Success Criteria

- [ ] Fractal agent initializes without errors
- [ ] Queries unified KG successfully (2,057 nodes accessible)
- [ ] Suggests ≥3 combinations for given task
- [ ] At least 1 suggestion matches validation corpus
- [ ] CLI responds in <5 seconds for simple queries
- [ ] User can select and execute suggested combination

### Phase 2 Success Criteria

- [ ] Identifies ≥10 unexplored valid combinations
- [ ] Novelty scores correlate with actual uniqueness
- [ ] Conflict checker prevents invalid combinations
- [ ] Experimentation mode finds combinations not in playbooks

### Phase 3 Success Criteria

- [ ] Multi-objective optimizer produces Pareto frontier
- [ ] Cost estimates within 20% of actual (validated on corpus)
- [ ] Speed estimates predict within 2x of actual
- [ ] Quality scores align with user satisfaction (survey)

---

## See Also (Playbooks)

- **[Playbook 1: Cost Optimization](PLAYBOOK-1-COST-OPTIMIZATION.md)** - Fractal suggests these patterns
- **[Playbook 4: Knowledge Engineering](PLAYBOOK-4-KNOWLEDGE-ENGINEERING.md)** - Methodologies Fractal uses
- **[Playbook 6: Augmented Intelligence ML](PLAYBOOK-6-AUGMENTED-INTELLIGENCE-ML.md)** - Fractal is an SRAIS
- **[Playbook 8: Continuous Learning Loop](PLAYBOOK-8-CONTINUOUS-LEARNING-LOOP.md)** - Persistent discoveries
- **[Playbook 9: Metacognition Workflows](PLAYBOOK-9-METACOGNITION-WORKFLOWS.md)** - Validated compositions

---

## Next Steps

1. **Implement MVP** (Week 1-2)
   - Follow SDK templates in `templates/claude-code-tools/`
   - Build MCP tools for KG access
   - Create basic combination validator

2. **Test Against Corpus** (Week 2)
   - Use `validation-corpus.json`
   - Verify recall on known combinations
   - Measure suggestion quality

3. **Add Unexplored Discovery** (Week 3-4)
   - Implement combination generator
   - Build novelty scorer
   - Test experimentation mode

4. **Iterate Based on Feedback** (Ongoing)
   - Collect user ratings of suggestions
   - Improve cost/speed/quality estimators
   - Expand combination corpus

---

**Status:** ✅ PLAYBOOK COMPLETE - Ready for implementation
**Next:** Create `fractal_sdk_agent.md` MVP plan with week-by-week roadmap

---

*Created: November 16, 2025*
*Version: 1.0.0*
*Purpose: Guide implementation of Fractal combinatorial composition discovery agent*

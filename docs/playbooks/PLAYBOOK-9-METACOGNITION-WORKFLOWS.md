# Playbook 9: Metacognition Workflows
## Validated Reasoning Through 35 Tools Across 7 Phases

**Version:** 1.0
**Last Updated:** November 27, 2025
**Audience:** AI practitioners, knowledge workers, developers seeking validated reasoning
**Prerequisites:** Basic understanding of Claude, Playbook 8 (Continuous Learning Loop)
**Related Playbooks:** Playbook 4 (Knowledge Engineering), Playbook 8 (Continuous Learning Loop)

---

## Table of Contents

1. [Overview](#overview)
2. [The 6 Dimensions of Analysis](#the-6-dimensions-of-analysis)
3. [Phase-by-Phase Tool Guide](#phase-by-phase-tool-guide)
4. [Decision Framework](#decision-framework)
5. [Workflow Patterns](#workflow-patterns)
6. [Quality Gates and Thresholds](#quality-gates-and-thresholds)
7. [Cost Optimization](#cost-optimization)
8. [Integration with Other Systems](#integration-with-other-systems)
9. [Troubleshooting](#troubleshooting)
10. [Real-World Examples](#real-world-examples)

---

## Overview

### What is Metacognition?

**Metacognition** = "Thinking about thinking"

In the context of this system, metacognition means:
- **Validating inputs** before using them
- **Detecting invalid combinations** ("mud")
- **Tracking reasoning chains** for auditability
- **Ensuring quality** through multi-dimensional analysis

### The Problem: Unvalidated AI Reasoning

```
Input: "I think Python is the best"
       + "Python is widely used"
       ↓
Output: "Python is the best because it's widely used"  ← INVALID!
```

The first input is opinion, not fact. The synthesis smuggles opinion as fact.

### The Solution: 35 Tools Across 7 Phases

```
Input: "I think Python is the best"
       ↓
validate_fact() → is_fact: FALSE, confidence: 0.35
       ↓
BLOCKED: Cannot use opinion as fact input

Input: "Python is widely used"
       ↓
validate_fact() → is_fact: TRUE, confidence: 0.95
       ↓
APPROVED: Can be used in synthesis
```

### The Color Mixing Principle

```
Fact A (Blue) + Fact B (Yellow) = Fact C (Green)    ✓ Valid synthesis
Fact A (Blue) + Opinion (??) = Brown Mud            ✗ Invalid - "mud"
```

**The tools don't make Claude conscious - they provide structure for explicit reasoning.**

---

## The 6 Dimensions of Analysis

### Overview

| Dimension | What It Assesses | Tool Phase | Key Question |
|-----------|-----------------|------------|--------------|
| **Texture** | Factual quality | Phase 2 | "How established is this fact?" |
| **Lighting** | Perspective/framing | Phase 3 | "What viewpoint is this from?" |
| **Composition** | Structural form | Phase 4 | "How is this argument structured?" |
| **Contrast** | Difference awareness | Phase 5 | "What distinctions are being made?" |
| **Method** | Reasoning approach | Phase 6 | "How was this conclusion reached?" |
| **Recursion** | Build depth | Phase 7 | "How many layers deep is this?" |

### Dimension 1: Texture

**What texture measures:** The "factual quality" of a statement.

| Texture Type | Description | Example | Confidence Impact |
|--------------|-------------|---------|-------------------|
| **Smooth** | Well-established, high consensus | "Water boils at 100°C at sea level" | High (0.9+) |
| **Rough** | Contested, nuanced, debatable | "Remote work improves productivity" | Medium (0.6-0.8) |
| **Grainy** | Statistical, probabilistic | "70% of users prefer dark mode" | Depends on source |

**When textures matter:**
- Mixing smooth + rough without acknowledgment = oversimplification
- Mixing smooth + grainy without context = misrepresenting precision

**Tool:** `assess_texture(statement)`

```python
result = assess_texture("Water boils at 100°C at sea level")
# Returns: {texture: "smooth", confidence: 0.95, indicators: ["established_fact"]}

result = assess_texture("Most developers prefer Python")
# Returns: {texture: "rough", confidence: 0.7, indicators: ["contested_claim"]}
```

### Dimension 2: Lighting

**What lighting measures:** The perspective or framing of a statement.

| Lighting Type | Description | Example Marker |
|---------------|-------------|----------------|
| **Highlight** | Emphasizes certain aspects | "The key point is..." |
| **Shadow** | De-emphasizes or omits | "Despite X, ..." |
| **Ambient** | Neutral, contextual | "Generally speaking..." |
| **Directional** | Specific viewpoint | "From a business perspective..." |

**What lighting reveals:**
- Every framing choice illuminates some aspects while shadowing others
- Hidden assumptions live in the shadows
- Directional lighting may exclude important perspectives

**Tool:** `identify_lighting(statement)`

```python
result = identify_lighting("The most important factor is performance")
# Returns: {
#   lighting_type: "highlight",
#   perspective: "technical",
#   hidden_aspects: ["cost", "maintainability", "user experience"]
# }
```

### Dimension 3: Composition

**What composition measures:** The structural arrangement of an argument.

| Composition Type | Structure | Example |
|------------------|-----------|---------|
| **Premise-Conclusion** | A, B → C | "Given X and Y, therefore Z" |
| **Chronological** | Time sequence | "First... then... finally..." |
| **Cause-Effect** | Causal chain | "Because X happened, Y resulted" |
| **Compare-Contrast** | Side-by-side | "X is like Y, but differs in Z" |
| **Hierarchical** | Ranked importance | "Most importantly... secondarily..." |
| **Parallel** | Equal-weight items | "X, Y, and Z are all important" |

**Why composition matters:**
- Missing premises make invalid arguments look valid
- Wrong structural form can misrepresent relationships
- Hierarchical claims need justification for ordering

**Tool:** `determine_composition(statement)`

```python
result = determine_composition("Because it rained, the ground is wet")
# Returns: {
#   composition_type: "cause_effect",
#   structural_roles: ["cause", "effect"],
#   missing_elements: ["mechanism"]  # How rain makes ground wet
# }
```

### Dimension 4: Contrast

**What contrast measures:** How differences are expressed.

| Contrast Type | Description | Risk |
|---------------|-------------|------|
| **Binary** | Either/or dichotomy | False dichotomies |
| **Spectrum** | Gradations along continuum | Over-nuancing |
| **Absence** | Contrast through what's missing | Hidden comparisons |
| **Implicit** | Hidden or unstated | Unstated assumptions |

**The false dichotomy problem:**
```
"You're either with us or against us"  ← Binary (usually invalid)
"Support ranges from strong to weak"   ← Spectrum (usually valid)
```

**Tool:** `assess_contrast(statement)`

```python
result = assess_contrast("You're either with us or against us")
# Returns: {
#   contrast_type: "binary",
#   contrast_validity: "false_dichotomy",
#   contrast_strength: 0.9
# }
```

### Dimension 5: Method

**What method measures:** How a conclusion was reached.

| Method | Description | Certainty | Example |
|--------|-------------|-----------|---------|
| **Deduction** | Logical necessity | 1.0 | "All A are B, X is A, therefore X is B" |
| **Induction** | Generalization | 0.8 | "All observed swans are white, so all swans are white" |
| **Analogy** | Domain transfer | 0.7 | "This worked for project A, so it will work for B" |
| **Abduction** | Best explanation | 0.6 | "The best explanation for X is Y" |

**The Boat/Ball Principle:**

Same inputs + different method = different outcome.

```
Material: Iron
Shape: Boat → Floats
Shape: Ball → Sinks

Facts: A, B
Method: Deduction → Certainty: 1.0
Method: Induction → Certainty: 0.8
```

**Tool:** `assess_method(statement)`

```python
result = assess_method("All observed cases show X, therefore X is universal")
# Returns: {
#   reasoning_method: "induction",
#   method_certainty: 0.8,
#   assumptions: ["Sample is representative", "No counterexamples exist"]
# }
```

### Dimension 6: Recursion

**What recursion measures:** How many layers of derivation deep.

```
Depth 1: Root facts (no dependencies)
Depth 2: Built on 1 layer
Depth 3: Built on 2+ layers
Depth 4+: Deep chains (valuable but monitor for error propagation)
```

**Tool:** `analyze_recursion_depth(item_id, item_type)`

```python
result = analyze_recursion_depth(item_id=42, item_type="fact")
# Returns: {
#   depth: 3,
#   chain: [fact_42, fact_30, fact_15],
#   root_items: [fact_15]
# }
```

---

## Phase-by-Phase Tool Guide

### Phase 1: Base Validation (7 tools)

**Purpose:** Validate inputs before any synthesis.

| Tool | Purpose | Key Parameters | Returns |
|------|---------|----------------|---------|
| `validate_fact` | Check if statement is fact | statement, evidence, domain | is_fact, confidence, issues |
| `check_combinability` | Can two facts combine? | fact_a, fact_b, proposed_synthesis | combinable, risks, recommendation |
| `detect_mud` | Is synthesis invalid? | inputs[], proposed_output | is_mud, mud_sources, clean_alternative |
| `synthesize` | Combine validated facts | fact_a, fact_b, synthesis_type | synthesized_fact, confidence, is_mud |
| `log_synthesis` | Record synthesis for tracking | fact_a, fact_b, result, confidence | synthesis_id, logged |
| `get_synthesis_chain` | Trace derivation history | fact_or_id, depth | chain, root_facts |
| `metacog_status` | Check reasoning metrics | window | validations_count, mud_detected_count |

**Core Workflow:**
```python
# 1. Validate inputs
val_a = await validate_fact("Statement A", evidence="Source")
val_b = await validate_fact("Statement B", evidence="Source")

if not val_a['is_fact'] or not val_b['is_fact']:
    # Cannot proceed - inputs aren't facts
    return

# 2. Check if they can combine
combo = await check_combinability(
    fact_a="Statement A",
    fact_b="Statement B",
    proposed_synthesis="Combined conclusion"
)

if not combo['combinable']:
    # Cannot combine - see combo['risks']
    return

# 3. Detect mud before synthesizing
mud = await detect_mud(
    inputs=["Statement A", "Statement B"],
    proposed_output="Combined conclusion"
)

if mud['is_mud']:
    # Invalid synthesis - see mud['mud_sources']
    return

# 4. Safe to synthesize
result = await synthesize(
    fact_a="Statement A",
    fact_b="Statement B",
    synthesis_type="deduction"
)
```

### Phase 2: Texture Analysis (3 tools)

**Purpose:** Assess and bridge factual quality differences.

| Tool | Purpose | Key Parameters | Returns |
|------|---------|----------------|---------|
| `assess_texture` | Determine fact texture | statement | texture, confidence, indicators |
| `texture_compatibility` | Can textures combine? | fact_a, fact_b | compatible, bridging_needed |
| `smooth_to_rough_bridge` | Create bridging statement | smooth_fact, context | bridged_fact, bridged_confidence |

**When to use:**
- Before combining facts from different sources
- When mixing research findings with practical observations
- When applying universal principles to specific contexts

**Example:**
```python
# Smooth fact meets rough context
smooth = "Code should be tested"  # Universal principle
context = "Legacy system with no test infrastructure"

# Direct combination would be mud - need bridging
bridge = await smooth_to_rough_bridge(
    smooth_fact=smooth,
    context=context
)
# Returns: {
#   bridged_fact: "While code testing is best practice,
#                 legacy systems may require incremental adoption",
#   bridged_confidence: 0.7
# }
```

### Phase 3: Lighting Analysis (4 tools)

**Purpose:** Understand and adjust perspective/framing.

| Tool | Purpose | Key Parameters | Returns |
|------|---------|----------------|---------|
| `identify_lighting` | Detect statement perspective | statement | lighting_type, perspective, hidden_aspects |
| `change_lighting` | Reframe from new perspective | statement, new_perspective | reframed, reframed_confidence |
| `shadow_detection` | What's hidden/de-emphasized? | statement | shadows, shadow_depth |
| `lighting_compatibility` | Can perspectives combine? | fact_a, fact_b | compatible, conflicts |

**Perspectives available for `change_lighting`:**
- technical, business, user, security
- ethical, legal, scientific, practical
- neutral, balanced

**Example:**
```python
# Detect what's hidden
shadows = await shadow_detection(
    "Our product is the best solution"
)
# Returns: {
#   shadow_depth: "deep",
#   shadows: {
#     hidden_contrasts: ["'best' hides criteria used"],
#     implied_opposites: ["Alternatives are NOT best"],
#     unstated_alternatives: ["Other options exist"]
#   }
# }

# Reframe for balance
reframed = await change_lighting(
    statement="Our product is the best solution",
    new_perspective="balanced"
)
# Returns: {
#   reframed: "Our product addresses specific needs well,
#             though other solutions may excel in different areas"
# }
```

### Phase 4: Composition Analysis (4 tools)

**Purpose:** Analyze and transform structural form.

| Tool | Purpose | Key Parameters | Returns |
|------|---------|----------------|---------|
| `determine_composition` | Detect structural type | statement | composition_type, structural_roles, missing_elements |
| `composition_compatibility` | Can structures combine? | fact_a, fact_b | compatible, structure_conflict |
| `recompose` | Transform structure type | statement, target_composition | recomposed, recomposed_confidence |
| `identify_gaps` | Find missing structural elements | statement | gaps, completeness_score, suggestions |

**Example:**
```python
# Find structural gaps
gaps = await identify_gaps("Therefore, we should use Python")
# Returns: {
#   composition_type: "premise_conclusion",
#   gaps: {missing_roles: ["premise"]},  # Missing: WHY?
#   gap_severity: "critical",
#   suggestions: ["Add supporting premises (given that, because, since)"]
# }

# Recompose for completeness
recomposed = await recompose(
    statement="Python is readable",
    target_composition="premise_conclusion"
)
# Returns: {
#   recomposed: "Given that Python is readable,
#               it follows that readability benefits exist"
# }
```

### Phase 5: Contrast Analysis (4 tools)

**Purpose:** Detect and preserve nuance.

| Tool | Purpose | Key Parameters | Returns |
|------|---------|----------------|---------|
| `assess_contrast` | Detect contrast type | statement | contrast_type, contrast_validity, contrast_strength |
| `contrast_compatibility` | Can contrasts combine? | fact_a, fact_b | compatible, nuance_lost |
| `nuance_check` | Is binary actually spectrum? | statement | is_false_dichotomy, should_be_spectrum |
| `reveal_hidden_contrast` | Expose implicit comparisons | statement | hidden_contrasts, implied_opposites |

**Example:**
```python
# Check for false dichotomy
nuance = await nuance_check("Testing is always necessary")
# Returns: {
#   is_false_dichotomy: true,
#   should_be_spectrum: true,
#   alternative_framing: "Testing is often necessary,
#                        with varying levels based on context"
# }

# Reveal hidden contrasts
hidden = await reveal_hidden_contrast("Our approach is innovative")
# Returns: {
#   hidden_contrasts: ["'innovative' implies others are NOT"],
#   implied_opposites: ["Traditional approaches are outdated"],
#   unstated_alternatives: ["Other innovative approaches exist"]
# }
```

### Phase 6: Method Analysis (4 tools)

**Purpose:** Assess reasoning approach validity.

| Tool | Purpose | Key Parameters | Returns |
|------|---------|----------------|---------|
| `assess_method` | Detect reasoning method | statement | reasoning_method, method_certainty, assumptions |
| `method_compatibility` | Can methods combine? | fact_a, fact_b | compatible, certainty_mismatch |
| `method_sensitivity` | Would different method change result? | statement | sensitivity, alternative_methods |
| `reveal_method_assumptions` | Expose hidden assumptions | statement | implicit_assumptions, validity_risks |

**Example:**
```python
# Assess method and assumptions
method = await assess_method(
    "Since this worked for project A, it will work for project B"
)
# Returns: {
#   reasoning_method: "analogy",
#   method_certainty: 0.7,
#   assumptions: ["Projects are sufficiently similar",
#                "Key factors transfer"]
# }

# Check sensitivity
sensitivity = await method_sensitivity(
    "Based on the pattern, the next number is 8"
)
# Returns: {
#   sensitivity: "high",
#   current_method: "induction",
#   would_conclusion_change: {
#     deduction: true,  # Different method = different conclusion
#     analogy: true
#   }
# }
```

### Phase 7: Persistence & Evolution (9 tools)

**Purpose:** Store validated knowledge, track growth.

See **Playbook 8: Continuous Learning Loop** for detailed coverage.

| Sub-Phase | Tools | Purpose |
|-----------|-------|---------|
| 7A: Persistence | `persist_validated_fact`, `retrieve_relevant_facts` | Store/retrieve facts |
| 7B: Insights | `log_insight`, `analyze_recursion_depth` | Track insights, measure depth |
| 7C: Evolution | `log_evolution_event`, `get_evolution_history` | Track system changes |
| 7D: Causality | `add_causal_relation`, `check_retrain_needed` | Encode causality, signal retraining |

---

## Decision Framework

### When to Use Each Dimension

```
START: Have a statement to evaluate
  │
  ├─► Is it claiming to be a fact?
  │     └─► validate_fact() [Phase 1]
  │
  ├─► Combining with another statement?
  │     └─► check_combinability() + detect_mud() [Phase 1]
  │
  ├─► Mixing research with observation?
  │     └─► texture analysis [Phase 2]
  │
  ├─► Concerned about bias or framing?
  │     └─► lighting analysis [Phase 3]
  │
  ├─► Argument structure seems weak?
  │     └─► composition analysis [Phase 4]
  │
  ├─► Seems oversimplified?
  │     └─► contrast analysis [Phase 5]
  │
  ├─► Uncertain about reasoning validity?
  │     └─► method analysis [Phase 6]
  │
  └─► Want to persist for future?
        └─► persistence [Phase 7]
```

### Quick Decision Table

| Situation | Use This | Skip These |
|-----------|----------|------------|
| Simple fact check | Phase 1 only | 2-6 |
| Combining two sources | Phase 1 + 2 | 3-5 |
| Detecting bias | Phase 1 + 3 | 2, 4-5 |
| Argument validation | Phase 1 + 4 | 2-3, 5 |
| Avoiding oversimplification | Phase 1 + 5 | 2-4 |
| Full validation before persist | Phase 1-6 | None |
| Quick persist (known good) | Phase 7 only | 1-6 |

### Dimension Interaction Matrix

| Dimension A | + Dimension B | Common Use Case |
|-------------|---------------|-----------------|
| Texture | Lighting | Academic claim with business framing |
| Texture | Composition | Statistical data in argument form |
| Lighting | Contrast | Biased comparison |
| Composition | Method | Logical argument validation |
| Contrast | Method | Deduction from dichotomy |
| All 6 | - | High-stakes synthesis |

---

## Workflow Patterns

### Pattern 1: Quick Validation

**Use when:** Simple fact check needed, low stakes

```python
async def quick_validate(statement: str) -> dict:
    result = await validate_fact(statement)
    return {
        "valid": result['is_fact'] and result['confidence'] > 0.8,
        "confidence": result['confidence'],
        "issues": result['issues']
    }

# Usage
valid = await quick_validate("Python uses indentation for blocks")
# Returns: {valid: true, confidence: 0.98, issues: []}
```

**Tools used:** 1 (validate_fact)
**Phases covered:** 1

### Pattern 2: Standard Synthesis

**Use when:** Combining two facts, moderate stakes

```python
async def standard_synthesis(fact_a: str, fact_b: str, synthesis: str) -> dict:
    # 1. Validate both inputs
    val_a = await validate_fact(fact_a)
    val_b = await validate_fact(fact_b)

    if not (val_a['is_fact'] and val_b['is_fact']):
        return {"error": "Invalid inputs"}

    # 2. Check combinability
    combo = await check_combinability(fact_a, fact_b, synthesis)
    if not combo['combinable']:
        return {"error": f"Cannot combine: {combo['risks']}"}

    # 3. Detect mud
    mud = await detect_mud([fact_a, fact_b], synthesis)
    if mud['is_mud']:
        return {"error": f"Mud detected: {mud['mud_sources']}"}

    # 4. Synthesize
    result = await synthesize(fact_a, fact_b, synthesis_type="composition")
    return result

# Usage
result = await standard_synthesis(
    fact_a="Python is readable",
    fact_b="Readable code is maintainable",
    synthesis="Python code is maintainable"
)
```

**Tools used:** 5 (validate_fact ×2, check_combinability, detect_mud, synthesize)
**Phases covered:** 1

### Pattern 3: Full Dimensional Analysis

**Use when:** High-stakes synthesis, need maximum validation

```python
async def full_analysis(fact_a: str, fact_b: str, synthesis: str) -> dict:
    report = {"fact_a": fact_a, "fact_b": fact_b, "synthesis": synthesis}

    # Phase 1: Base validation
    report['validation_a'] = await validate_fact(fact_a)
    report['validation_b'] = await validate_fact(fact_b)

    if not (report['validation_a']['is_fact'] and report['validation_b']['is_fact']):
        report['status'] = 'invalid_inputs'
        return report

    # Phase 2: Texture
    report['texture_a'] = await assess_texture(fact_a)
    report['texture_b'] = await assess_texture(fact_b)
    report['texture_compat'] = await texture_compatibility(fact_a, fact_b)

    # Phase 3: Lighting
    report['lighting_a'] = await identify_lighting(fact_a)
    report['lighting_b'] = await identify_lighting(fact_b)

    # Phase 4: Composition
    report['composition_a'] = await determine_composition(fact_a)
    report['composition_b'] = await determine_composition(fact_b)
    report['composition_compat'] = await composition_compatibility(fact_a, fact_b)

    # Phase 5: Contrast
    report['contrast_a'] = await assess_contrast(fact_a)
    report['contrast_b'] = await assess_contrast(fact_b)
    report['contrast_compat'] = await contrast_compatibility(fact_a, fact_b)

    # Phase 6: Method
    report['method_a'] = await assess_method(fact_a)
    report['method_b'] = await assess_method(fact_b)
    report['method_compat'] = await method_compatibility(fact_a, fact_b)

    # Final mud check (uses all dimensions internally)
    report['mud_check'] = await detect_mud([fact_a, fact_b], synthesis)

    # Status
    report['status'] = 'valid' if not report['mud_check']['is_mud'] else 'mud_detected'
    return report
```

**Tools used:** 17+
**Phases covered:** 1-6

### Pattern 4: Incremental Building

**Use when:** Building knowledge over multiple steps

```python
async def incremental_build(statements: List[str]) -> dict:
    validated = []
    rejected = []

    for stmt in statements:
        # Validate each statement
        val = await validate_fact(stmt)

        if val['is_fact'] and val['confidence'] > 0.8:
            # Check compatibility with existing validated facts
            compatible = True
            for existing in validated:
                combo = await check_combinability(existing, stmt, "")
                if not combo['combinable']:
                    compatible = False
                    break

            if compatible:
                validated.append(stmt)
            else:
                rejected.append({"stmt": stmt, "reason": "incompatible"})
        else:
            rejected.append({"stmt": stmt, "reason": val['issues']})

    return {"validated": validated, "rejected": rejected}
```

### Pattern 5: Perspective Exploration

**Use when:** Need to understand multiple viewpoints

```python
async def explore_perspectives(statement: str) -> dict:
    perspectives = ['technical', 'business', 'user', 'security', 'ethical']
    explorations = {}

    # Original lighting
    original = await identify_lighting(statement)
    explorations['original'] = original

    # Hidden aspects
    shadows = await shadow_detection(statement)
    explorations['hidden'] = shadows

    # Alternative framings
    for perspective in perspectives:
        if perspective != original.get('perspective'):
            reframed = await change_lighting(statement, perspective)
            explorations[perspective] = reframed

    return explorations
```

---

## Quality Gates and Thresholds

### Confidence Thresholds

| Threshold | When to Use | Effect |
|-----------|-------------|--------|
| 0.95+ | Well-established facts only | Very restrictive |
| 0.80 | Standard validation (recommended) | Balanced |
| 0.70 | Exploratory synthesis | Permissive |
| 0.60 | Hypothesis generation | Very permissive |

### Quality Gate Rules

**Gate 1: Input Validation**
```
IF validate_fact().is_fact == FALSE:
    BLOCK: Cannot proceed
    ACTION: Reformulate statement or acknowledge as opinion
```

**Gate 2: Combinability**
```
IF check_combinability().combinable == FALSE:
    BLOCK: Cannot combine these facts
    ACTION: See risks[], find compatible alternative
```

**Gate 3: Mud Detection**
```
IF detect_mud().is_mud == TRUE:
    BLOCK: Synthesis would be invalid
    ACTION: See mud_sources[], use clean_alternative if available
```

**Gate 4: Texture Compatibility**
```
IF texture_compatibility().bridging_needed == TRUE:
    WARNING: Need bridging statement
    ACTION: Use smooth_to_rough_bridge() before combining
```

**Gate 5: Method Certainty**
```
IF method_compatibility().certainty_mismatch == TRUE:
    WARNING: Certainty levels incompatible
    ACTION: Acknowledge lower certainty in synthesis
```

### The 6-Layer Mud Detection

`detect_mud()` internally checks all 6 layers:

```
Layer 1: Base → Is each input a fact?
Layer 2: Texture → Are textures compatible?
Layer 3: Lighting → Do perspectives conflict?
Layer 4: Composition → Are structures compatible?
Layer 5: Contrast → Is nuance preserved?
Layer 6: Method → Are certainty levels compatible?

ANY layer fails → is_mud = TRUE
```

---

## Cost Optimization

### When to Skip Validation

| Scenario | Skip? | Reason |
|----------|-------|--------|
| Documenting observations | Yes | Not truth claims |
| Recording preferences | Yes | Subjective |
| Noting hypotheses | Yes | Explicitly provisional |
| **Claiming truth** | **No** | Core use case |
| **Building on facts** | **No** | Chain quality matters |
| **Synthesizing** | **No** | Combinations can introduce error |

### Tiered Validation Strategy

```
Tier 1: Quick (1 tool)
  → validate_fact() only
  → Use for: Low-stakes, high-volume

Tier 2: Standard (3-5 tools)
  → validate_fact() + check_combinability() + detect_mud()
  → Use for: Normal operations

Tier 3: Full (15+ tools)
  → All 6 dimensions
  → Use for: High-stakes decisions

Tier 4: Persist (Tier 2 + Phase 7)
  → Standard validation + persistence
  → Use for: Building knowledge base
```

### Tool Call Budget

| Validation Level | Tool Calls | When |
|-----------------|------------|------|
| Minimal | 1 | Trust source, just checking |
| Light | 3 | Normal fact checking |
| Standard | 5-7 | Synthesis validation |
| Deep | 10-15 | Multi-dimensional analysis |
| Full | 17+ | Complete audit |

### Caching Validated Facts

```python
# Don't re-validate known facts
async def smart_validate(statement: str, fact_cache: dict) -> dict:
    # Check cache first
    if statement in fact_cache:
        return fact_cache[statement]

    # Validate
    result = await validate_fact(statement)

    # Cache if valid
    if result['is_fact'] and result['confidence'] > 0.9:
        fact_cache[statement] = result

    return result
```

---

## Integration with Other Systems

### Integration with Knowledge Graph

```python
async def validate_and_add_to_kg(statement: str, node_type: str):
    # 1. Full validation
    val = await validate_fact(statement)
    if not val['is_fact'] or val['confidence'] < 0.8:
        return {"error": "Validation failed"}

    # 2. Texture check for node categorization
    texture = await assess_texture(statement)

    # 3. Add to KG with metadata
    node_id = await add_kg_node(
        node_type=node_type,
        name=statement[:50],
        properties={
            "full_text": statement,
            "confidence": val['confidence'],
            "texture": texture['texture'],
            "validated": True
        }
    )

    return {"node_id": node_id, "validation": val}
```

### Integration with Continuous Learning (Playbook 8)

```python
async def validated_persist(statement: str, domain: str):
    # 1. Full validation
    val = await validate_fact(statement, domain=domain)

    if not val['is_fact']:
        return {"error": f"Not a fact: {val['issues']}"}

    if val['confidence'] < 0.8:
        return {"error": f"Low confidence: {val['confidence']}"}

    # 2. Check for related existing facts
    related = await retrieve_relevant_facts(query=statement, k=5)

    # 3. Determine builds_on
    builds_on = []
    for fact in related:
        combo = await check_combinability(fact['fact'], statement, "")
        if combo['combinable']:
            builds_on.append(fact['fact_id'])

    # 4. Persist with lineage
    result = await persist_validated_fact(
        fact=statement,
        confidence=val['confidence'],
        domain=domain,
        builds_on=builds_on
    )

    return result
```

### Integration with Session Handoff

```python
async def validated_handoff(session_topic: str):
    # Get all facts from session
    facts = await retrieve_relevant_facts(query=session_topic, k=50)

    # Group by validation status
    handoff = {
        "high_confidence": [f for f in facts if f['confidence'] >= 0.9],
        "medium_confidence": [f for f in facts if 0.8 <= f['confidence'] < 0.9],
        "needs_review": [f for f in facts if f['confidence'] < 0.8]
    }

    # Include dimension analysis for key facts
    for fact in handoff['high_confidence'][:5]:
        fact['texture'] = await assess_texture(fact['fact'])
        fact['method'] = await assess_method(fact['fact'])

    return handoff
```

---

## Troubleshooting

### Issue: Everything Fails Validation

**Symptoms:** `validate_fact()` returns `is_fact: false` for reasonable statements

**Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| Opinion markers present | Remove "I think", "probably", "seems like" |
| Too vague | Make specific and verifiable |
| Missing evidence | Provide `evidence` parameter |
| Actually an opinion | Correct behavior - reframe as observation |

**Debug:**
```python
result = await validate_fact(
    statement="Statement here",
    evidence="Supporting source"
)
print(f"Issues: {result['issues']}")  # Shows what's wrong
```

### Issue: Mud Detection Too Aggressive

**Symptoms:** `detect_mud()` blocks reasonable syntheses

**Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| Texture mismatch | Use `smooth_to_rough_bridge()` first |
| Perspective conflict | Acknowledge perspectives explicitly |
| Method incompatibility | Match certainty levels |
| False dichotomy | Use spectrum framing |

**Debug:**
```python
# Check each dimension separately
texture_a = await assess_texture(fact_a)
texture_b = await assess_texture(fact_b)
compat = await texture_compatibility(fact_a, fact_b)
print(f"Bridging needed: {compat['bridging_needed']}")
```

### Issue: Low Recursion Depth

**Symptoms:** All facts at depth 1, no compound growth

**Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| Not using `builds_on` | Always check for related facts first |
| Isolated domains | Look for cross-domain connections |
| Not retrieving first | Start sessions with `retrieve_relevant_facts()` |

**Fix:**
```python
# Before persisting, always check for related facts
related = await retrieve_relevant_facts(query=new_fact, k=5)
builds_on = [f['fact_id'] for f in related if f['confidence'] > 0.8]
await persist_validated_fact(fact=new_fact, builds_on=builds_on)
```

### Issue: Conflicting Dimension Results

**Symptoms:** One dimension says compatible, another says not

**Resolution:** Dimensions measure different things - conflicts are informative.

```python
# Example: Texture compatible but method incompatible
texture_compat = await texture_compatibility(a, b)  # compatible: true
method_compat = await method_compatibility(a, b)    # compatible: false

# Resolution: The facts have similar quality (texture)
# but use different reasoning approaches (method).
# Action: Acknowledge different certainty levels in synthesis.
```

---

## Real-World Examples

### Example 1: Code Review Insight Validation

**Scenario:** During code review, you notice a pattern and want to persist it.

```python
# Raw observation
observation = "Functions longer than 50 lines are harder to test"

# Step 1: Validate
val = await validate_fact(observation)
# Returns: {is_fact: false, confidence: 0.6, issues: ["Generalization without evidence"]}

# Problem: Too general. Refine:
refined = "In this codebase, functions over 50 lines have 40% lower test coverage"

val = await validate_fact(refined, evidence="Coverage report analysis")
# Returns: {is_fact: true, confidence: 0.88}

# Step 2: Check texture (is this project-specific or universal?)
texture = await assess_texture(refined)
# Returns: {texture: "grainy", indicators: ["contains_number", "specific_measurement"]}

# Step 3: Persist with appropriate framing
await persist_validated_fact(
    fact=refined,
    confidence=0.88,
    domain="code_quality",
    evidence="Coverage report analysis of 500 functions"
)
```

### Example 2: Business Decision Analysis

**Scenario:** Evaluating a claim for a business decision.

```python
claim = "Switching to microservices will improve our deployment speed"

# Step 1: Validate
val = await validate_fact(claim)
# Returns: {is_fact: false, issues: ["Prediction, not established fact"]}

# This is a hypothesis, not a fact. Let's analyze it:

# Step 2: Check method
method = await assess_method(claim)
# Returns: {
#   reasoning_method: "abduction",
#   method_certainty: 0.6,
#   assumptions: ["Team has microservices expertise",
#                "Current monolith is the bottleneck"]
# }

# Step 3: Reveal assumptions
assumptions = await reveal_method_assumptions(claim)
# Returns detailed list of hidden assumptions

# Step 4: Reframe as conditional
reframed = "If the team gains microservices expertise and the monolith is the deployment bottleneck, switching to microservices may improve deployment speed"

# This is more honest - acknowledges assumptions
```

### Example 3: Research Synthesis

**Scenario:** Combining findings from two different sources.

```python
finding_a = "Study A: Remote workers report 20% higher job satisfaction"
finding_b = "Study B: Remote workers show 15% lower collaboration scores"

# Step 1: Validate both
val_a = await validate_fact(finding_a, evidence="Study A citation")
val_b = await validate_fact(finding_b, evidence="Study B citation")
# Both valid

# Step 2: Check texture
texture_a = await assess_texture(finding_a)
texture_b = await assess_texture(finding_b)
# Both grainy (statistical findings)

compat = await texture_compatibility(finding_a, finding_b)
# compatible: true (both grainy)

# Step 3: Check contrast
contrast_compat = await contrast_compatibility(finding_a, finding_b)
# Returns: nuance_lost: false (they measure different things)

# Step 4: Proposed synthesis
synthesis = "Remote work improves satisfaction but may reduce collaboration"

mud = await detect_mud([finding_a, finding_b], synthesis)
# is_mud: false - valid synthesis

# Step 5: Persist
await persist_validated_fact(
    fact=synthesis,
    confidence=0.85,
    evidence="Synthesis of Study A and Study B",
    domain="workplace_research"
)
```

### Example 4: Debugging False Dichotomy

**Scenario:** Statement seems oversimplified.

```python
claim = "You either support automated testing or you don't care about quality"

# Step 1: Validate
val = await validate_fact(claim)
# Returns: {is_fact: false, issues: ["False dichotomy"]}

# Step 2: Nuance check
nuance = await nuance_check(claim)
# Returns: {
#   is_false_dichotomy: true,
#   should_be_spectrum: true,
#   alternative_framing: "Testing is one of many quality practices,
#                        with varying levels of automation appropriate
#                        for different contexts"
# }

# Step 3: Reveal hidden contrast
hidden = await reveal_hidden_contrast(claim)
# Returns: {
#   hidden_contrasts: ["Excludes other quality practices"],
#   implied_opposites: ["Manual testing = not caring"],
#   unstated_alternatives: ["Code review", "pair programming", "static analysis"]
# }

# Result: Original claim is invalid. Use nuanced alternative.
```

---

## Summary

### The 7 Phases at a Glance

| Phase | Tools | Purpose | When to Use |
|-------|-------|---------|-------------|
| 1 | 7 | Base validation | Always |
| 2 | 3 | Texture analysis | Mixing sources |
| 3 | 4 | Lighting analysis | Checking bias |
| 4 | 4 | Composition analysis | Argument validity |
| 5 | 4 | Contrast analysis | Avoiding oversimplification |
| 6 | 4 | Method analysis | Reasoning validity |
| 7 | 9 | Persistence | Building knowledge |

### Key Takeaways

1. **Tools provide structure, not consciousness**
   - Calling validate_fact() forces explicit validation
   - The scaffolding enables quality reasoning

2. **6 dimensions catch different issues**
   - Texture: fact quality
   - Lighting: perspective bias
   - Composition: structural validity
   - Contrast: nuance preservation
   - Method: reasoning soundness
   - Recursion: derivation depth

3. **Use appropriate validation level**
   - Quick (1 tool) for low stakes
   - Standard (5 tools) for normal work
   - Full (15+ tools) for high stakes

4. **Integration compounds value**
   - Connect to KG for persistence
   - Use with Playbook 8 for learning
   - Build handoffs for continuity

5. **Mud detection is your friend**
   - Invalid synthesis caught early
   - Clean alternatives suggested
   - Quality maintained over time

### Quick Reference Card

```
VALIDATE INPUT:
  validate_fact(statement, evidence, domain)
  → is_fact, confidence, issues

COMBINE FACTS:
  check_combinability(a, b, synthesis) → combinable, risks
  detect_mud([inputs], output) → is_mud, mud_sources

ANALYZE DIMENSIONS:
  assess_texture() → smooth/rough/grainy
  identify_lighting() → highlight/shadow/ambient/directional
  determine_composition() → premise_conclusion/cause_effect/etc.
  assess_contrast() → binary/spectrum/absence/implicit
  assess_method() → deduction/induction/analogy/abduction

PERSIST KNOWLEDGE:
  persist_validated_fact(fact, confidence, domain, builds_on)
  retrieve_relevant_facts(query, k, min_confidence)
  analyze_recursion_depth(item_id) → depth, chain
```

---

## Additional Resources

**See Also (Playbooks):**
- **[Playbook 4: Knowledge Engineering](PLAYBOOK-4-KNOWLEDGE-ENGINEERING.md)** - Entity extraction, KG construction
- **[Playbook 8: Continuous Learning Loop](PLAYBOOK-8-CONTINUOUS-LEARNING-LOOP.md)** - Fact persistence, compound growth
- **[Playbook 6: Augmented Intelligence ML](PLAYBOOK-6-AUGMENTED-INTELLIGENCE-ML.md)** - SRAIS methodology
- **[Playbook 2: Extended Thinking](PLAYBOOK-2-EXTENDED-THINKING.md)** - Reasoning quality

**Core Documentation:**
- `nlke_mcp/tools/metacognition.py` (3600+ lines implementation)
- `nlke_mcp/MCP-SERVER-MANUAL.md` (complete tool reference)
- `docs/SCIENTIFIC-ANALYSIS-TIME-COMPRESSION.md` (methodology)

**MCP Tools Reference:**
- `nlke_mcp/servers/nlke_metacognition_server.py`
- 35 tools across 7 phases
- 64 tests passing

---

**Playbook Version:** 1.0
**Last Updated:** November 27, 2025
**Created By:** Eyal + Claude Opus 4.5
**Methodology:** NLKE v3.0 - Build WITH AI, Document AS you build

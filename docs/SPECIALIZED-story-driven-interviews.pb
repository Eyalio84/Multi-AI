# Playbook 28: Story-Driven Architectural Interviews

**Version:** 1.0
**Date:** December 12, 2025
**Focus:** Meta-pattern for creating domain-specific interview tools that extract 10x richer context through narrative scaffolding
**Prerequisites:** PB-0 (Playbook System), PB-22 (Full-Stack Scaffolding)
**Difficulty:** Intermediate
**Time Investment:** 2-4 hours to learn pattern, 30 min to create new interview

---

## Table of Contents

1. [The Interview Engineering Problem](#1-the-interview-engineering-problem)
2. [Story-Driven Prompting Methodology](#2-story-driven-prompting-methodology)
3. [Question Taxonomy](#3-question-taxonomy)
4. [Section Design Patterns](#4-section-design-patterns)
5. [The Interview Factory Pattern](#5-the-interview-factory-pattern)
6. [Domain Templates](#6-domain-templates)
7. [Implementation Patterns](#7-implementation-patterns)
8. [Synthesis and Output Generation](#8-synthesis-and-output-generation)
9. [Anti-Patterns to Avoid](#9-anti-patterns-to-avoid)
10. [Quick Reference](#10-quick-reference)

---

## 1. The Interview Engineering Problem

### Why Shallow Prompts Produce Shallow Output

```
Shallow Prompt:
User: "Build me a todo app"
AI: [Generic CRUD scaffold with default styling]

Result:
- No understanding of WHO uses it
- No understanding of WHY they need it
- No design direction
- Generic, forgettable output
```

The AI has no context to make opinionated decisions, so it defaults to generic patterns.

### The 10x Context Extraction Principle

```
Enhanced Interview:
Q1: "What problem does this solve?"
A1: "I forget tasks and miss deadlines constantly"

Q2: "Who experiences this most?"
A2: "Busy professionals juggling multiple projects"

Q3: "What's frustrating about current solutions?"
A3: "Too many features, cognitive overload, guilt-inducing"

Q4: "Describe the mood in 3 words"
A4: "Calm, minimal, forgiving"

Result:
- Persona: Overwhelmed professional
- Core need: Reduce cognitive load, not add features
- Design direction: Calm, minimal, no guilt mechanics
- Opinionated output: Zen-like task app, not another Todoist clone
```

**The principle:** Structured interviews extract 10x more usable context at ~2x the interaction cost. The ROI strongly favors interviews for any non-trivial generation task.

### Interview Engineering as a Meta-Skill

Interview engineering is the discipline of designing question sets that:
1. **Extract implicit requirements** (what users don't know to say)
2. **Force prioritization** (what matters MOST)
3. **Anchor abstracts to concretes** (reference examples)
4. **Define boundaries through negation** (what NOT to do)
5. **Establish success criteria** (how to measure done)

This playbook teaches you to CREATE interview tools, not just use them.

---

## 2. Story-Driven Prompting Methodology

### Narrative Scaffolding vs Feature Lists

```
Feature List Approach:
"What features do you want?"
→ "Login, dashboard, notifications, settings, export..."
→ Flat list, no priorities, no context

Story-Driven Approach:
"Tell me about someone using this. What's their day like?"
→ "Sarah is a product manager. She starts her day overwhelmed..."
→ Rich persona, emotional context, implicit priorities
```

**Key insight:** Stories naturally encode priorities, emotions, and context that feature lists miss.

### The Story Arc Structure

Every good interview follows a story arc:

```
ACT 1: THE PROBLEM (Why does this need to exist?)
├── Who has this problem?
├── What's their current pain?
├── What have they tried?
└── Why did those solutions fail?

ACT 2: THE SOLUTION (What does success look like?)
├── What does the ideal outcome enable?
├── What's the ONE thing it must do well?
├── What would cause failure?
└── How do we measure success?

ACT 3: THE EXPERIENCE (How should it feel?)
├── What emotions should it evoke?
├── What does it look/feel like?
├── What's the key interaction?
└── What references capture the vision?
```

### Progressive Disclosure Pattern

Questions should flow from broad to specific:

```
Level 1: Open exploration (discover unknown unknowns)
         "What problem are you trying to solve?"

Level 2: Guided exploration (explore known territory)
         "Who experiences this problem most acutely?"

Level 3: Constrained choices (force decisions)
         "Desktop-first or mobile-first?"

Level 4: Specific details (nail down implementation)
         "What's your primary brand color?"
```

This prevents premature specificity while ensuring all decisions get made.

---

## 3. Question Taxonomy

### Type 1: Open Exploratory Questions

**Purpose:** Discover unknown unknowns, let the interviewee lead

**Patterns:**
- "Describe..."
- "Tell me about..."
- "What..."
- "How..."

**Examples:**
- "What problem does this application solve?"
- "Describe a typical user of this system"
- "How do people currently handle this?"

**When to use:** Start of sections, complex topics, when you don't know what you don't know

**Characteristics:**
- No predefined answer format
- Encourages elaboration
- May need follow-up probing

---

### Type 2: Constrained Choice Questions

**Purpose:** Force decisions, reduce ambiguity, make trade-offs explicit

**Patterns:**
- "X or Y?"
- "Choose from: A, B, C"
- "On a scale of 1-5..."
- "Rank these in order..."

**Examples:**
- "Desktop-first, mobile-first, or equal priority?"
- "Minimal/clean or feature-rich/dense?"
- "REST, GraphQL, or gRPC?"

**When to use:** Binary decisions, spectrum positions, architecture choices

**Characteristics:**
- Limited answer space
- Forces commitment
- Reveals priorities through trade-offs

---

### Type 3: Reference Anchoring Questions

**Purpose:** Ground abstract concepts in concrete examples

**Patterns:**
- "Name examples of..."
- "What's similar to..."
- "Show me something that..."
- "What existing X captures this?"

**Examples:**
- "Name 2-3 apps you love the feel of"
- "What API do you consider well-designed?"
- "What game captures the feeling you want?"

**When to use:** Aesthetic decisions, complex concepts, when words fail

**Characteristics:**
- Concrete touchstones
- Shared reference points
- Reduces miscommunication dramatically

---

### Type 4: Negative Space Questions

**Purpose:** Define boundaries through exclusion, surface fears and risks

**Patterns:**
- "What would make you..."
- "What should we avoid..."
- "What would cause failure..."
- "What's a dealbreaker..."

**Examples:**
- "What would make users abandon this app?"
- "What should we definitely NOT do?"
- "What's the worst possible outcome?"

**When to use:** Identifying anti-requirements, risk discovery, priority validation

**Characteristics:**
- Reveals hidden requirements
- Surfaces fears and concerns
- Often more revealing than positive questions

---

### Type 5: Success Criteria Questions

**Purpose:** Anchor to measurable outcomes, define "done"

**Patterns:**
- "How will you know..."
- "What metrics indicate..."
- "What does success look like..."
- "When would you consider this complete..."

**Examples:**
- "How will you know this succeeded?"
- "What metrics would indicate this is working?"
- "What would make you consider this a win?"

**When to use:** End of problem sections, validation points, scope definition

**Characteristics:**
- Measurable criteria
- Prevents scope creep
- Aligns expectations

---

### The Golden Ratio

For a 10-question section, aim for:

```
Open Exploratory:     3 questions (30%)
Constrained Choice:   3 questions (30%)
Reference Anchoring:  2 questions (20%)
Negative Space:       1 question  (10%)
Success Criteria:     1 question  (10%)
```

This ratio balances discovery with decision-making.

---

## 4. Section Design Patterns

### Pattern 1: Problem/Solution Split

**Structure:**
- Section 1: Problem Space (Why? Who? What's wrong?)
- Section 2: Solution Space (How? What? How does it feel?)

**Best for:** Product development, app scaffolding, feature design

**Example:**
```
Section 1: The Problem Story
├── What problem does this solve?
├── Who has this problem?
├── Current solutions and their failures
├── What does success enable?
└── How to measure success?

Section 2: The Experience Story
├── How should it feel?
├── What does it look like?
├── Key interactions
├── References and inspirations
└── Constraints and requirements
```

---

### Pattern 2: Consumer/Contract Split

**Structure:**
- Section 1: Consumer Story (Who uses this? What do they need?)
- Section 2: Contract Story (What promises do we make? How do we keep them?)

**Best for:** API design, service interfaces, integration patterns

**Example:**
```
Section 1: Consumer Story
├── Who consumes this?
├── What are they trying to accomplish?
├── What frustrates them about similar APIs?
├── Volume and latency expectations
└── Success metrics

Section 2: Contract Story
├── Versioning strategy
├── Error handling philosophy
├── Authentication approach
├── Rate limiting
└── Documentation format
```

---

### Pattern 3: Player/Mechanics Split

**Structure:**
- Section 1: Player Story (Who plays? Why? What emotions?)
- Section 2: Mechanics Story (What actions? What feedback? What progression?)

**Best for:** Game development, interactive experiences, gamification

**Example:**
```
Section 1: Player Story
├── What kind of experience?
├── Who is the ideal player?
├── What emotions should they feel?
├── Session length and frequency
└── What makes them quit?

Section 2: Mechanics Story
├── Core mechanic (one verb)
├── Inputs and feedback
├── Progression system
├── Win/fail states
└── Satisfying moments
```

---

### Pattern 4: Data/Model Split

**Structure:**
- Section 1: Data Story (What data? Where from? What biases?)
- Section 2: Model Story (What predictions? What constraints? How to validate?)

**Best for:** ML pipelines, data products, analytics systems

**Example:**
```
Section 1: Data Story
├── What prediction/output?
├── Available data sources
├── Collection methods
├── Potential biases
└── Ground truth definition

Section 2: Model Story
├── Interpretability requirements
├── Latency budget
├── Training frequency
├── Deployment target
└── Monitoring strategy
```

---

### Pattern 5: Abstract-to-Concrete Gradient

Within any section, questions should flow:

```
ABSTRACT (emotions, goals, personas)
    ↓
"What mood should this evoke?"
"Who is the ideal user?"
    ↓
SEMI-CONCRETE (references, comparisons)
    ↓
"What apps capture this feeling?"
"What's similar to what you want?"
    ↓
CONCRETE (specific choices, constraints)
    ↓
"What's the primary color?"
"Desktop or mobile first?"
```

This prevents premature specificity while ensuring details get captured.

---

## 5. The Interview Factory Pattern

### Step 1: Domain Analysis

**Input:** Target domain (e.g., "Database Schema Design")
**Output:** Key decision dimensions

**Process:**
```
1. List ALL decisions that must be made to complete this task
   - What entities exist?
   - What relationships?
   - What constraints?
   - What indexes?
   - What access patterns?
   - ...

2. Group decisions into logical clusters
   - Data Model decisions
   - Performance decisions
   - Access Pattern decisions
   - Constraint decisions

3. Identify the "story" each cluster tells
   - "What data are we storing and why?"
   - "How will this data be accessed?"
```

---

### Step 2: Section Identification

**Pattern:** Each section should tell a coherent part of the story

**Formula:**
```
Number of sections = 2-4 (more causes fatigue)
Questions per section = 8-12 (10 is ideal)
Total questions = 16-40 (20 is sweet spot)
```

**Section Naming Convention:**
```
[Domain] + "Story"

Examples:
- "The Problem Story"
- "The Consumer Story"
- "The Data Story"
- "The Player Story"
- "The Experience Story"
```

---

### Step 3: Question Generation

**For each section, apply the golden ratio:**

```python
def generate_section_questions(topic: str, count: int = 10) -> list:
    questions = []

    # 30% Open Exploratory (start broad)
    questions.extend([
        f"What is the core purpose of {topic}?",
        f"Who interacts with {topic} and why?",
        f"What problems does {topic} solve?",
    ][:int(count * 0.3)])

    # 20% Reference Anchoring
    questions.extend([
        f"Name 2-3 examples of good {topic} you've seen",
        f"What existing {topic} comes closest to what you want?",
    ][:int(count * 0.2)])

    # 30% Constrained Choice
    questions.extend([
        f"[Specific binary choice about {topic}]",
        f"[Specific spectrum choice about {topic}]",
        f"[Specific option choice about {topic}]",
    ][:int(count * 0.3)])

    # 10% Negative Space
    questions.append(f"What would make {topic} fail?")

    # 10% Success Criteria
    questions.append(f"How will you measure if {topic} is successful?")

    return questions
```

---

### Step 4: Synthesis Template Creation

**For each section, define:**

```yaml
section_synthesis:
  name: "Problem Space"

  output_artifact: "Product Requirements Document"

  question_mapping:
    Q1_answer: "problem_statement"
    Q2_answer: "target_persona"
    Q3_answer: "competitive_landscape"
    Q4_answer: "pain_points"
    Q5_answer: "value_proposition"
    Q6_answer: "core_feature"
    Q7_answer: "anti_requirements"
    Q8_answer: "data_model_hints"
    Q9_answer: "technical_constraints"
    Q10_answer: "success_metrics"

  defaults:
    Q1_skip: "General productivity improvement"
    Q2_skip: "General users"
    # ... defaults for each question

  validation:
    Q1_min_length: 20
    Q6_required: true
    Q10_must_be_measurable: true
```

---

### Factory Pattern Summary

```
┌─────────────────────────────────────────────────────────────┐
│                    INTERVIEW FACTORY                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  INPUT: Domain Description                                  │
│         "I need an interview for API design"                │
│                                                             │
│  STEP 1: Domain Analysis                                    │
│          → List all decisions                               │
│          → Group into clusters                              │
│          → Identify stories                                 │
│                                                             │
│  STEP 2: Section Identification                             │
│          → 2-4 sections                                     │
│          → Name each story                                  │
│          → Order logically                                  │
│                                                             │
│  STEP 3: Question Generation                                │
│          → Apply golden ratio                               │
│          → 10 questions per section                         │
│          → Progressive disclosure                           │
│                                                             │
│  STEP 4: Synthesis Template                                 │
│          → Map answers to outputs                           │
│          → Define defaults                                  │
│          → Set validation rules                             │
│                                                             │
│  OUTPUT: Complete Interview Tool                            │
│          Ready to use for domain-specific context extraction│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Domain Templates

### Template A: Web Application Interview

**Section 1: Problem Space (10 Questions)**

| # | Question | Type |
|---|----------|------|
| 1 | What problem does this application solve? | Open |
| 2 | Who experiences this problem most acutely? | Open |
| 3 | How do they currently solve this problem? | Open |
| 4 | What's frustrating about current solutions? | Open |
| 5 | What would a perfect solution enable them to do? | Open |
| 6 | What is the ONE thing this app must do well? | Constrained |
| 7 | What would make users abandon this app? | Negative |
| 8 | What data does this app need to work with? | Open |
| 9 | Are there hard constraints? (budget, timeline, tech) | Constrained |
| 10 | How will you know this succeeded? | Success |

**Section 2: UI/UX Appearance (10 Questions)**

| # | Question | Type |
|---|----------|------|
| 1 | Describe the mood in 3 words | Open |
| 2 | Name 2-3 apps/sites you love the feel of | Reference |
| 3 | What colors come to mind? Any to avoid? | Open |
| 4 | Desktop-first, mobile-first, or equal? | Constrained |
| 5 | Minimal/clean or feature-rich/dense? | Constrained |
| 6 | Any accessibility requirements? | Constrained |
| 7 | Dark mode, light mode, or both? | Constrained |
| 8 | What's the most important action users take? | Reference |
| 9 | How much customization should users have? | Constrained |
| 10 | Any branding elements to incorporate? | Open |

---

### Template B: API Design Interview

**Section 1: Consumer Story (10 Questions)**

| # | Question | Type |
|---|----------|------|
| 1 | Who will consume this API? | Open |
| 2 | What are they trying to accomplish? | Open |
| 3 | Name 2-3 APIs you consider well-designed | Reference |
| 4 | What frustrates you about APIs you've used? | Negative |
| 5 | REST, GraphQL, or gRPC? | Constrained |
| 6 | What authentication method? | Constrained |
| 7 | Expected request volume? | Constrained |
| 8 | Latency requirements? | Constrained |
| 9 | What data entities are central? | Open |
| 10 | How will you measure API success? | Success |

**Section 2: Contract Story (10 Questions)**

| # | Question | Type |
|---|----------|------|
| 1 | Describe the ideal developer experience in 3 words | Open |
| 2 | Versioning strategy? | Constrained |
| 3 | Error response philosophy? | Constrained |
| 4 | What operations must be idempotent? | Open |
| 5 | Rate limiting approach? | Constrained |
| 6 | What would cause a breaking change? | Negative |
| 7 | Pagination style? | Constrained |
| 8 | What's the most important endpoint? | Reference |
| 9 | Webhook support needed? | Constrained |
| 10 | Documentation format? | Constrained |

---

### Template C: Game Development Interview

**Section 1: Player Story (10 Questions)**

| # | Question | Type |
|---|----------|------|
| 1 | What kind of experience is this? | Open |
| 2 | Who is your ideal player? Describe them. | Open |
| 3 | Name 2-3 games that inspire this project | Reference |
| 4 | What emotions should players feel? | Open |
| 5 | Single player, multiplayer, or both? | Constrained |
| 6 | Session length? | Constrained |
| 7 | What would make a player quit permanently? | Negative |
| 8 | Progression system type? | Constrained |
| 9 | What's the core loop? (one sentence) | Open |
| 10 | How will you know the game is "fun"? | Success |

**Section 2: Mechanics Story (10 Questions)**

| # | Question | Type |
|---|----------|------|
| 1 | Describe the core mechanic in one action verb | Open |
| 2 | What inputs does the player have? | Open |
| 3 | What feedback do they receive? | Open |
| 4 | Turn-based or real-time? | Constrained |
| 5 | Difficulty scaling? | Constrained |
| 6 | What resources does the player manage? | Open |
| 7 | What's the fail state? | Open |
| 8 | What's the win state? | Open |
| 9 | Any randomness? | Constrained |
| 10 | What's the most satisfying moment? | Reference |

---

### Template D: ML Pipeline Interview

**Section 1: Data Story (10 Questions)**

| # | Question | Type |
|---|----------|------|
| 1 | What prediction/output are you making? | Open |
| 2 | What data do you have access to? | Open |
| 3 | How is this data collected? | Open |
| 4 | What biases might exist in this data? | Negative |
| 5 | Structured, unstructured, or mixed? | Constrained |
| 6 | Data volume? | Constrained |
| 7 | Real-time inference or batch? | Constrained |
| 8 | What's the cost of a wrong prediction? | Open |
| 9 | How is ground truth determined? | Open |
| 10 | What accuracy would be "good enough"? | Success |

**Section 2: Model Story (10 Questions)**

| # | Question | Type |
|---|----------|------|
| 1 | Interpretability requirement? | Constrained |
| 2 | Latency budget for inference? | Constrained |
| 3 | Training frequency? | Constrained |
| 4 | Deployment target? | Constrained |
| 5 | What would cause model failure in production? | Negative |
| 6 | Any regulatory constraints? | Open |
| 7 | Human-in-the-loop requirements? | Constrained |
| 8 | A/B testing approach? | Constrained |
| 9 | Model versioning strategy? | Open |
| 10 | How will you monitor model drift? | Success |

---

### Template E: Database Schema Interview

**Section 1: Data Model Story (10 Questions)**

| # | Question | Type |
|---|----------|------|
| 1 | What is this database storing? | Open |
| 2 | What are the main entities/objects? | Open |
| 3 | How do these entities relate to each other? | Open |
| 4 | What's an example of well-designed schema you've used? | Reference |
| 5 | Relational, document, graph, or key-value? | Constrained |
| 6 | What data should NEVER be stored? | Negative |
| 7 | What's the most frequently accessed data? | Open |
| 8 | Expected total data size in 1 year? | Constrained |
| 9 | Any compliance requirements? (GDPR, HIPAA) | Open |
| 10 | How will you know the schema is "right"? | Success |

**Section 2: Access Pattern Story (10 Questions)**

| # | Question | Type |
|---|----------|------|
| 1 | What are the 3 most common queries? | Open |
| 2 | Read-heavy, write-heavy, or balanced? | Constrained |
| 3 | Any real-time requirements? | Constrained |
| 4 | What queries would be unacceptably slow? | Negative |
| 5 | Full-text search needed? | Constrained |
| 6 | Geographic/spatial queries needed? | Constrained |
| 7 | Time-series data patterns? | Constrained |
| 8 | Multi-tenancy requirements? | Constrained |
| 9 | Backup and recovery requirements? | Open |
| 10 | What latency is acceptable for reads? | Success |

---

## 7. Implementation Patterns

### Pattern A: Interactive CLI Interview

```python
class InteractiveCLIInterview:
    """Command-line interview flow."""

    def __init__(self, interview_template: dict):
        self.template = interview_template
        self.answers = {}

    def run(self) -> dict:
        """Execute the interview."""
        print(f"\n{'='*60}")
        print(f"  {self.template['title']}")
        print(f"{'='*60}\n")

        for section in self.template['sections']:
            self._run_section(section)

        return self._synthesize()

    def _run_section(self, section: dict):
        """Run a single section."""
        print(f"\n--- {section['name']} ---\n")

        for i, question in enumerate(section['questions'], 1):
            answer = self._ask_question(i, question)
            self.answers[question['id']] = answer

    def _ask_question(self, num: int, question: dict) -> str:
        """Ask a single question with validation."""
        print(f"Q{num}: {question['text']}")

        if question.get('hint'):
            print(f"    (Hint: {question['hint']})")

        if question.get('options'):
            for opt in question['options']:
                print(f"    - {opt}")

        while True:
            answer = input("\n>>> ").strip()

            if not answer and question.get('default'):
                answer = question['default']
                print(f"    [Using default: {answer}]")

            if self._validate_answer(answer, question):
                return answer

            print("    Please provide a more complete answer.")

    def _validate_answer(self, answer: str, question: dict) -> bool:
        """Validate answer meets requirements."""
        if question.get('required') and not answer:
            return False
        if question.get('min_length') and len(answer) < question['min_length']:
            return False
        return True

    def _synthesize(self) -> dict:
        """Synthesize answers into output artifacts."""
        return {
            'raw_answers': self.answers,
            'prd': self._generate_prd(),
            'design_brief': self._generate_design_brief(),
        }
```

---

### Pattern B: Slash Command Integration

```markdown
# /interview Command

## Usage
/interview <domain>

## Available Domains
- webapp    → Web Application Interview (Problem + UI/UX)
- api       → API Design Interview (Consumer + Contract)
- game      → Game Development Interview (Player + Mechanics)
- ml        → ML Pipeline Interview (Data + Model)
- database  → Database Schema Interview (Model + Access)
- custom    → Start Interview Factory to create new

## Example
/interview webapp

## Output
After completing the interview:
1. Synthesized PRD (Product Requirements Document)
2. Design Brief
3. Technical Recommendations
4. Ready-to-use context for scaffolding
```

---

### Pattern C: Claude Code Integration

```python
# Integration with Claude Code AskUserQuestion tool

def run_interview_with_claude_code(interview_template: dict):
    """Run interview using Claude Code's question tool."""

    answers = {}

    for section in interview_template['sections']:
        # Present section intro
        print(f"\n## {section['name']}\n")

        for question in section['questions']:
            # Use AskUserQuestion for constrained choices
            if question['type'] == 'constrained':
                response = ask_user_question(
                    questions=[{
                        "question": question['text'],
                        "header": question['short_label'],
                        "options": [
                            {"label": opt, "description": desc}
                            for opt, desc in question['options'].items()
                        ],
                        "multiSelect": question.get('multi', False)
                    }]
                )
                answers[question['id']] = response

            # Use direct output for open questions
            else:
                print(f"**{question['text']}**")
                if question.get('hint'):
                    print(f"*{question['hint']}*")
                # Wait for user response in conversation

    return synthesize(answers, interview_template)
```

---

### Pattern D: Export Formats

```python
def export_interview_results(answers: dict, format: str) -> str:
    """Export interview results in various formats."""

    if format == 'json':
        return json.dumps(answers, indent=2)

    elif format == 'markdown':
        md = "# Interview Results\n\n"
        for section, section_answers in answers.items():
            md += f"## {section}\n\n"
            for q, a in section_answers.items():
                md += f"**{q}:** {a}\n\n"
        return md

    elif format == 'yaml':
        return yaml.dump(answers, default_flow_style=False)

    elif format == 'context':
        # Optimized for LLM context injection
        return f"""
<interview_context>
{json.dumps(answers, indent=2)}
</interview_context>
"""
```

---

## 8. Synthesis and Output Generation

### The Synthesis Pipeline

```
Raw Answers → Structured Data → Artifacts → Generation Context
```

### PRD Template

```markdown
# Product Requirements Document

## Problem Statement
${answers.problem_description}

## Target User
${answers.persona_description}

### User Pain Points
${answers.current_frustrations}

## Solution Overview

### Core Value Proposition
${answers.perfect_solution_enables}

### Primary Feature (Must Have)
${answers.one_thing_must_do_well}

### Anti-Requirements (Will Not Do)
${answers.what_would_cause_abandonment}

## Success Criteria
${answers.how_to_measure_success}

## Constraints
${answers.hard_constraints}

## Data Requirements
${answers.data_needs}
```

### Design Brief Template

```markdown
# Design Brief

## Visual Direction

### Mood
${answers.mood_words}

### Reference Points
${answers.reference_apps}

### Color Direction
- Preferred: ${answers.preferred_colors}
- Avoid: ${answers.avoid_colors}

## Interaction Design

### Platform Strategy
${answers.platform_priority}

### Information Density
${answers.density_preference}

### Primary Action
${answers.most_important_action}

## Technical Requirements

### Accessibility
${answers.accessibility_requirements}

### Theming
${answers.theme_preference}

### Personalization Scope
${answers.customization_level}

### Brand Integration
${answers.brand_elements}
```

### Context Injection for Generation

```python
def create_generation_context(prd: str, design_brief: str) -> str:
    """Create optimized context for code generation."""

    return f"""
You are generating code for an application with these requirements:

<product_requirements>
{prd}
</product_requirements>

<design_brief>
{design_brief}
</design_brief>

Based on these requirements:
1. The target user is {extract_persona(prd)}
2. The core feature is {extract_core_feature(prd)}
3. The visual style should be {extract_mood(design_brief)}
4. The platform priority is {extract_platform(design_brief)}

Generate code that directly addresses these specific requirements.
Do NOT generate generic boilerplate - every decision should reflect the interview answers.
"""
```

---

## 9. Anti-Patterns to Avoid

### Anti-Pattern 1: Question Overload

```markdown
❌ BAD: 50 questions across 5 sections
   → Interview fatigue, declining answer quality
   → Users start skipping or giving minimal answers

✓ GOOD: 20 questions across 2 sections (10 each)
   → Sustainable engagement
   → Thoughtful answers throughout
```

**Rule:** Maximum 40 questions total, ideally 20.

---

### Anti-Pattern 2: All Open-Ended

```markdown
❌ BAD: Every question is "Describe..." or "Tell me about..."
   → No forced decisions
   → Vague, uncommitted answers
   → Hard to synthesize into actionable spec

✓ GOOD: Mix of open (30%) + constrained (30%) + others
   → Discovery balanced with decisions
   → Clear, actionable outputs
```

---

### Anti-Pattern 3: No Synthesis Step

```markdown
❌ BAD: Collect answers → Immediately generate code
   → No validation of understanding
   → Errors compound into output
   → No chance to correct misinterpretations

✓ GOOD: Collect answers → Synthesize → Validate → Generate
   → "Here's what I understood..." checkpoint
   → User can correct before generation
   → Higher quality output
```

---

### Anti-Pattern 4: Skipping Negative Space

```markdown
❌ BAD: Only ask what they want
   → Miss critical anti-requirements
   → Generate features that cause failure
   → Scope creep because boundaries unclear

✓ GOOD: Include "What would make this fail?" questions
   → Clear boundaries
   → Explicit anti-requirements
   → Focused scope
```

---

### Anti-Pattern 5: Generic Questions

```markdown
❌ BAD: "What features do you want?"
   → Feature list, no priorities
   → No context for decisions
   → Generic output

✓ GOOD: "What is the ONE thing this must do well?"
   → Forces prioritization
   → Reveals true requirements
   → Opinionated output
```

---

## 10. Quick Reference

### Question Type Cheat Sheet

| Type | Pattern | Example | When |
|------|---------|---------|------|
| Open | "What/How/Describe..." | "What problem does this solve?" | Discovery |
| Constrained | "X or Y?" | "Desktop or mobile first?" | Decisions |
| Reference | "Name examples of..." | "Apps you love the feel of?" | Anchoring |
| Negative | "What would cause..." | "What would make users quit?" | Boundaries |
| Success | "How will you know..." | "How to measure success?" | Criteria |

### Golden Ratio

```
Open:        30%  (3/10 questions)
Constrained: 30%  (3/10 questions)
Reference:   20%  (2/10 questions)
Negative:    10%  (1/10 questions)
Success:     10%  (1/10 questions)
```

### Section Design Formula

```
Sections:           2-4 (prefer 2)
Questions/section:  8-12 (prefer 10)
Total questions:    16-40 (prefer 20)
```

### Interview Flow

```
1. DISCOVER  → Open questions (what problem? who?)
2. ANCHOR    → Reference questions (examples?)
3. DECIDE    → Constrained questions (this or that?)
4. BOUND     → Negative questions (what NOT to do?)
5. MEASURE   → Success questions (how to know done?)
6. VALIDATE  → Synthesis checkpoint (is this right?)
7. GENERATE  → Use context for output
```

### Factory Checklist

```
□ List all decisions for domain
□ Group into 2-4 sections
□ Name each section as a "story"
□ Generate 10 questions per section using golden ratio
□ Create synthesis template mapping answers to outputs
□ Define defaults for skipped questions
□ Set validation rules
□ Test with 3 different scenarios
```

---

**Document Version:** 1.0
**Emergent From:** Full-Stack Scaffolder enhancement session
**Key Insight:** Structured interviews extract 10x more context at 2x interaction cost - the ROI strongly favors interview engineering for any non-trivial generation task.

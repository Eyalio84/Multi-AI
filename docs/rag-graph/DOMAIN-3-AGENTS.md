# Domain Report 3: Agents

**Author:** Eyal Nof | **Date:** February 8, 2026 | **Scope:** The 40-agent architecture, SDK, dual format, rules, skills, and plugin system

---

## 1. Agent Census

| Metric | Count |
|--------|-------|
| Total agents | 40 |
| .md agents (Claude Code) | 40 at `~/.claude/agents/` |
| .py agents (standalone) | 36 at `agents/<category>/` |
| .md-only (no .py) | 5 (doc-updater, md-cat, py-cat, opus-expender, sonnet-code-analyzer) |
| SDK-registered | 35 in `agent_sdk.py` |
| Categories | 14 |
| Model tiers | Opus (4), Sonnet (20), Haiku (16) |

---

## 2. The 5-Layer Pattern (agent_base.py, 403 lines)

Every `.py` agent follows the same structural template:

```
L1: Data Models     — AgentInput, AgentOutput dataclasses + category-specific types
L2: Constants       — Pricing dicts, path strings, threshold values, enums
L3: BaseAnalyzer    — Abstract analysis class with analyze() method
L4: Orchestrator    — AgentOrchestrator for multi-stage pipelines (optional)
L5: CLI             — run_standard_cli() with --example, --workload, --output, --summary
```

### 2.1 L1: Core Data Models

**AgentInput (line 35):**
```python
@dataclass
class AgentInput:
    workload: Dict[str, Any]                      # Primary input data
    context: Optional[Dict[str, Any]] = None      # Additional context
    options: Optional[Dict[str, Any]] = None      # Runtime options
```

**AgentOutput (line 43):**
```python
@dataclass
class AgentOutput:
    recommendations: List[Dict[str, Any]]         # REQUIRED: actionable items
    rules_applied: List[str]                       # REQUIRED: synthesis rule IDs
    meta_insight: str                              # REQUIRED: emergent observation
    anti_patterns: List[Dict[str, Any]] = field(default_factory=list)  # Optional
    agent_metadata: Dict[str, Any] = field(default_factory=dict)       # Optional
    analysis_data: Dict[str, Any] = field(default_factory=dict)        # Optional
```

**SynthesisRule (line 55):**
```python
@dataclass
class SynthesisRule:
    rule_id: str         # "PLAYBOOK-X_rule_YYY" format
    description: str
    category: str        # e.g., "cost-optimization", "kg-operations"
    severity: str        # "critical", "high", "medium", "low"
```

**Recommendation (line 63):**
```python
@dataclass
class Recommendation:
    technique: str       # Name of the optimization technique
    impact: str          # "high", "medium", "low"
    reasoning: str       # Why this recommendation
    implementation: str  # How to implement
    savings: Optional[float] = None  # Estimated savings %
```

**AntiPattern (line 73):**
```python
@dataclass
class AntiPattern:
    pattern_id: str
    title: str
    severity: str
    description: str
    why_it_fails: str
    correct_approach: str
    recovery_steps: List[str]
```

### 2.2 L2: Shared Constants (lines 85-200)

**MODEL_PRICING (line 87):** 8 models with input/output pricing per million tokens:

| Model | Input $/M | Output $/M | Provider |
|-------|-----------|------------|----------|
| claude-opus-4 | 15.00 | 75.00 | Anthropic |
| claude-sonnet-4-5 | 3.00 | 15.00 | Anthropic |
| claude-haiku-3-5 | 0.80 | 4.00 | Anthropic |
| gemini-3-pro | 1.25 | 5.00 | Google |
| gemini-2.5-pro | 1.25 | 10.00 | Google |
| gemini-2.5-flash | 0.075 | 0.30 | Google |
| gemini-flash-lite | 0.0375 | 0.15 | Google |
| cache_read | 0.30 | — | Anthropic |

**Path constants:**
```python
NLKE_ROOT = Path(__file__).parent.parent.parent  # NLKE/ directory
AGENTS_DIR = NLKE_ROOT / "agents"
KG_DIR = NLKE_ROOT / "knowledge-graphs"
DOC_DIRS = [NLKE_ROOT / "docs", NLKE_ROOT / "Eyal-s--agents" / "docs"]
```

**KG_DATABASES (line 130):** 4 registered KG databases with paths.

**THINKING_THRESHOLDS (line 140):**

| Tier | Max Tokens | Use Case |
|------|-----------|----------|
| minimal | 1,000 | Simple lookups |
| standard | 4,000 | Most analyses |
| deep | 8,000 | Complex reasoning |
| max | 16,000 | Architecture decisions |

### 2.3 L3: BaseAnalyzer (lines 205-280)

```python
class BaseAnalyzer(ABC):
    def __init__(self, agent_name: str, model: str, version: str = "1.0"):
        self.agent_name = agent_name
        self.model = model
        self.version = version

    @abstractmethod
    def get_example_input(self) -> Dict[str, Any]:
        """Return example workload for --example mode."""
        pass

    @abstractmethod
    def analyze(self, agent_input: AgentInput) -> AgentOutput:
        """Core analysis method. Must return valid AgentOutput."""
        pass

    def build_metadata(self) -> Dict[str, Any]:
        """Standard metadata for every agent output."""
        return {
            "agent_name": self.agent_name,
            "model": self.model,
            "version": self.version,
            "timestamp": datetime.now().isoformat()
        }
```

### 2.4 L4: AgentOrchestrator (lines 282-300)

**Multi-stage pipeline within a single agent:**

```python
class AgentOrchestrator:
    def __init__(self, stages: List[Tuple[str, BaseAnalyzer]]):
        self.stages = stages  # [(name, analyzer), ...]

    def run(self, agent_input: AgentInput) -> AgentOutput:
        # Sequential stage execution
        # Accumulates: recommendations, rules, anti_patterns, analysis_data
        # Meta-insights concatenated with " | " separator, prefixed [stage_name]
        # Rules de-duplicated via list(dict.fromkeys())
```

**Only used by:** MCP Tool Creator (3 internal sub-analyzers: MCPSpecAnalyzer -> MCPValidationAnalyzer -> MCPRuleMatchAnalyzer).

### 2.5 L5: CLI (lines 302-403)

**`run_standard_cli(agent_name, description, analyzer)` (line 354):**

Input resolution priority:
1. `--example` → calls `analyzer.get_example_input()`
2. `--workload <file>` → reads JSON from file
3. `stdin` (piped JSON) → reads from pipe
4. None → prints usage and exits

Output modes:
- `--output <file>` → saves JSON to file
- `--summary` → prints human-readable summary
- Default → prints full JSON to stdout

**CLI arguments:**

| Flag | Type | Description |
|------|------|-------------|
| `--workload` | str | JSON input file path |
| `--example` | flag | Use built-in example data |
| `--output` | str | Output file path |
| `--summary` | flag | Human-readable output |
| `--json` | flag | JSON output (default=True) |

---

## 3. Agent SDK (agent_sdk.py, 307 lines)

### 3.1 AGENT_MODULES Registry (lines 40-77)

35 agents registered as name -> module path:

| # | Agent Name | Module Path | Category |
|---|-----------|-------------|----------|
| 1 | cost-advisor | cost-optimization.cost_advisor | cost-opt |
| 2 | batch-optimizer | cost-optimization.batch_optimizer_agent | cost-opt |
| 3 | thinking-budget-optimizer | cost-optimization.thinking_budget_agent | cost-opt |
| 4 | kg-health-monitor | kg-enhancement.kg_health_monitor | kg |
| 5 | relationship-suggester | kg-enhancement.relationship_suggester_agent | kg |
| 6 | kg-completer | kg-enhancement.kg_completer | kg |
| 7 | workflow-orchestrator | workflow-automation.workflow_orchestrator | workflow |
| 8 | generator-agent | workflow-automation.generator_agent | workflow |
| 9 | progressive-assembly | workflow-automation.progressive_assembly | workflow |
| 10 | compound-intelligence | emergent.compound_intelligence | emergent |
| 11 | self-healing-docs | emergent.self_healing_docs | emergent |
| 12 | cost-quality-frontier | emergent.cost_quality_frontier | emergent |
| 13 | multi-model-orchestrator | multi-model.multi_model_orchestrator | multi-model |
| 14 | gemini-delegator | multi-model.gemini_delegator | multi-model |
| 15 | context-engineer | multi-model.context_engineer | multi-model |
| 16 | rule-engine-agent | rule-engine.rule_engine_agent | rule-engine |
| 17 | anti-pattern-validator | rule-engine.anti_pattern_validator | rule-engine |
| 18 | playbook-advisor | rule-engine.playbook_advisor | rule-engine |
| 19 | rag-kg-query | knowledge-retrieval.rag_kg_query | knowledge |
| 20 | intent-engine | knowledge-retrieval.intent_engine_agent | knowledge |
| 21 | refactoring-agent | knowledge-retrieval.refactoring_agent | knowledge |
| 22 | mcp-tool-creator | mcp-tool-creator.mcp_tool_creator | mcp |
| 23 | embedding-engine | advanced.embedding_engine | advanced |
| 24 | citation-analyzer | advanced.citation_analyzer | advanced |
| 25 | gemini-compute | cross-provider.gemini_compute | cross-provider |
| 26 | web-research | cross-provider.web_research | cross-provider |
| 27 | visual-report | reporting.visual_report | reporting |
| 28 | agentic-tool-router | routing.agentic_tool_router | routing |
| 29 | codegen-python | codegen.codegen_python | codegen |
| 30 | codegen-javascript | codegen.codegen_javascript | codegen |
| 31 | codegen-sql | codegen.codegen_sql | codegen |
| 32 | codegen-bash | codegen.codegen_bash | codegen |
| 33 | codegen-html-css | codegen.codegen_html_css | codegen |
| 34 | codegen-gemini | codegen.codegen_gemini | codegen |
| 35 | codegen-orchestrator | codegen.codegen_orchestrator | codegen |

**5 .md-only agents** (not in SDK): doc-updater, md-cat, py-cat, opus-expender, sonnet-code-analyzer.

### 3.2 AgentRunner — Dynamic Loading (lines 109-178)

```python
class AgentRunner:
    _cache: Dict[str, Any] = {}  # Class-level module cache
```

**Loading algorithm (`load_analyzer`, lines 115-150):**
1. Check class-level `_cache` dict
2. Look up module path from `AGENT_MODULES`
3. Split into `category` and `module_name`
4. Construct absolute path: `NLKE_ROOT / agents / category / module_name.py`
5. `importlib.util.spec_from_file_location()` + `module_from_spec()` + `exec_module()`
6. Find Analyzer: iterate `dir(mod)`, find type ending in `"Analyzer"` that is not `"BaseAnalyzer"`
7. Instantiate with `obj()` and cache

**Run method (lines 153-178):**
- Wraps load + execute in try/except
- Measures wall-clock time with `time.time()`
- Returns `StepResult(agent_name, success, output, duration_ms, error)`

### 3.3 Pipeline — Dependency Resolution (lines 185-287)

**PipelineStep data model:**
```python
@dataclass
class PipelineStep:
    agent_name: str
    workload: Optional[Dict] = None
    depends_on: List[str] = field(default_factory=list)
    transform: Optional[Callable] = None  # Transform predecessor output to workload
```

**Pipeline.run() algorithm (lines 211-278):**
```
1. Iterate through steps sequentially
2. For each step:
   a. Check depends_on: if any dependency failed -> skip with error
   b. If transform + depends_on: workload = transform(results[dep].output)
   c. Run: AgentRunner.run(step.agent_name, workload)
   d. Store result
3. Aggregate:
   - Collect recommendations from all successful steps
   - Collect rules via set union (sorted)
   - Sum durations
4. Return PipelineResult
```

**Three composition patterns:**

| Pattern | How | Example |
|---------|-----|---------|
| Sequential chain | `depends_on + transform` | Cost advisor output feeds compound intelligence |
| Parallel fan-out | Shared workload, no depends_on | Multiple codegen agents on same spec |
| Escalation cascade | Tier routing within compound-intelligence | Haiku -> Sonnet -> Opus |

---

## 4. Dual Format System (.md + .py)

### 4.1 .md Agent Structure

All 40 `.md` files at `~/.claude/agents/` follow:

```yaml
---
name: <kebab-case>              # Agent identifier
description: <one-liner>        # Triggers on /<command>
tools: Read, Write, Bash, ...   # Claude Code tools needed
model: <haiku|sonnet|opus>      # Model tier
---
```

**Body sections:**
1. **Title** — `# Agent Name`
2. **System prompt** — "You are the NLKE [Agent Name]..."
3. **What You Do** — Capabilities list
4. **Tools Available** — Python CLI commands with full absolute paths
5. **Execution Steps** — Numbered workflow
6. **Output Format / Key Rules** — Domain-specific guidance
7. **`$ARGUMENTS`** — Runtime arguments placeholder

### 4.2 .py Agent Structure

Every `.py` file follows the exact same skeleton:

```python
"""
Module docstring with description, layer reference, usage examples
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from shared.agent_base import *

# ── L1: Data Models ──────────────────
@dataclass
class CategorySpecificType: ...

# ── L2: Constants ─────────────────────
CATEGORY_CONSTANTS = { ... }

# ── L3: Analyzer ──────────────────────
class XxxAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__(agent_name="xxx", model="haiku|sonnet|opus", version="1.0")

    def get_example_input(self) -> Dict[str, Any]:
        return { ... }

    def analyze(self, agent_input: AgentInput) -> AgentOutput:
        workload = agent_input.workload
        # ... category-specific analysis ...
        return AgentOutput(
            recommendations=[...],
            rules_applied=[...],
            meta_insight="...",
            agent_metadata=self.build_metadata()
        )

# ── L5: CLI ───────────────────────────
if __name__ == "__main__":
    analyzer = XxxAnalyzer()
    run_standard_cli("xxx", "Description", analyzer)
```

### 4.3 How .md and .py Relate

The `.md` file acts as the Claude Code "persona" that instructs Claude how to USE the `.py` tool:

```
.md file                          .py file
┌─────────────────────┐          ┌─────────────────────┐
│ Strategic guidance  │          │ Deterministic logic  │
│ When to use         │──uses──>│ Calculations         │
│ How to interpret    │          │ Database queries     │
│ Claude Code tools   │          │ Code generation      │
│ Model tier          │          │ JSON output          │
└─────────────────────┘          └─────────────────────┘
```

Example relationships:
- **compound-intelligence.md** (72 lines, Opus): References 4 Python tools, describes cascade strategy
- **cost-advisor.md** (83 lines, Haiku): References 3 tools, includes Gemini comparison table
- **rag-kg-query.md** (41 lines, Sonnet): References 1 tool, lists knowledge sources

---

## 5. Category-Specific Agent Analysis

### 5.1 Cost Optimization (3 agents, Haiku tier)

**cost_advisor.py (531 lines):**
- 5 sequential sub-analyses: caching, batch, model tiering, compound, Gemini migration
- Custom types: `OptimizationTechnique(Enum)`, `CostRecommendation`
- Gemini `MIGRATION_MAP`: opus->gemini-3-pro (80%), sonnet->gemini-2.5-pro (58%), haiku->gemini-2.5-flash (81%)
- 5 anti-pattern checks: single RPD caching, batch+latency, thinking >20K, opus for low complexity, ignoring Gemini
- 10 rule IDs applied

**batch_optimizer_agent.py:** Batch API eligibility analysis, 50% discount calculation.

**thinking_budget_agent.py:** Extended thinking optimization, diminishing returns analysis.

### 5.2 KG Enhancement (3 agents, mixed tiers)

**kg_health_monitor.py (390 lines, Haiku):**
- 30 `VALID_NODE_TYPES`, 23 `VALID_EDGE_TYPES`
- Health thresholds: orphan_ratio_warning=0.05, orphan_ratio_critical=0.15, min_connectivity=0.80
- Orphan detection SQL: anti-join pattern
- Cross-KG comparative analysis

**relationship_suggester_agent.py (Sonnet):** Suggests new edges based on node proximity.

**kg_completer.py (Sonnet):** Gap detection in KG coverage.

### 5.3 Workflow Automation (3 agents, mixed tiers)

**workflow_orchestrator.py (374 lines, Sonnet):**
- 5 complexity levels: TRIVIAL -> SIMPLE -> MODERATE -> COMPLEX -> VERY_COMPLEX
- Cross-provider model selection: Claude + Gemini routing
- `THINKING_BUDGETS`: trivial=0, simple=1000, moderate=3000, complex=6000, very_complex=8000
- `CATEGORY_TIME_MULTIPLIERS`: planning=1.3, design=1.4, implementation=1.0, validation=0.8, review=0.6
- 4 `WORKFLOW_TEMPLATES`: dev_lifecycle, research_analysis, kg_pipeline, decision_making
- Parallelization detection: groups consecutive parallelizable steps

### 5.4 Emergent (3 agents, mixed tiers)

**compound_intelligence.py (216 lines, Opus):**
- 3-tier cascade: Haiku (Worker) / Sonnet (Coordinator) / Opus (Strategic)
- `COMPLEXITY_TO_TIER`: trivial/simple->1, moderate/complex->2, very_complex->3
- `DEFAULT_DISTRIBUTION`: {1: 0.90, 2: 0.10, 3: 0.00}
- Cascade cost: per-task `(avg_input + thinking + avg_output) / 1M * price`
- Savings comparison: vs all-opus, vs all-sonnet

**cost_quality_frontier.py (254 lines, Sonnet):**
- 12-point Pareto optimization across 3 dimensions (cost, quality, latency)
- Quality model: haiku 0.65-0.82, sonnet 0.78-0.93, opus 0.88-0.98
- Latency model: haiku 200ms base, sonnet 800ms, opus 2000ms
- O(n^2) Pareto dominance check
- 3 recommendation modes: cost-first, quality-first, balanced

**self_healing_docs.py (Haiku):** Documentation drift detection.

### 5.5 Multi-Model (3 agents, mixed tiers)

**context_engineer.py (306 lines, Haiku):**
- 3-tier context hierarchy: global (2K), project (10K), local (5K)
- Priority weights: critical=1.0, high=0.85, medium=0.60, low=0.30
- Optimization: `opt_tokens = tokens * max(priority_weight, utilization_pct/100)`
- Cross-provider Gemini analysis with implicit caching (75% discount on 32K+)
- `CONTEXT_OVERFLOW_THRESHOLD` = 150,000 tokens
- Example input models NLKE's own context: CLAUDE.md (1500 tokens), MEMORY.md (1200 tokens)

**multi_model_orchestrator.py (Opus):** Cross-provider task routing.

**gemini_delegator.py (Sonnet):** Gemini-specific delegation.

### 5.6 Rule Engine (3 agents, mixed tiers)

**anti_pattern_validator.py (265 lines, Haiku):**
- 4 built-in heuristic checks:
  1. `heuristic_001_batch_realtime`: batch_api + real_time conflict
  2. `heuristic_002_unbounded_loops`: tool_loops without max_iterations
  3. `heuristic_003_no_error_handling`: missing error handling
  4. `heuristic_004_unconstrained_thinking`: thinking without budget
- `FEATURE_PATTERNS`: 8 categories with keyword lists
- Results sorted by severity

**rule_engine_agent.py (Sonnet):** Full synthesis rule evaluation.

**playbook_advisor.py (Haiku):** Playbook selection guidance.

### 5.7 Knowledge Retrieval (3 agents, mixed tiers)

**rag_kg_query.py (296 lines, Sonnet):**
- Keyword extraction: regex `\w+`, 20 stopwords, min length 3
- KG query: `WHERE LOWER(name) LIKE ? OR LOWER(description) LIKE ?`
- Relevance: `min(1.0, keyword_hits / total_keywords + 0.3)`
- Document search: recursive .md/.txt scan, line-level keyword match
- Document threshold: hits >= 2 OR (hits >= 1 AND line_length > 50)
- 4 registered KGs + auto-discovered .db files

**intent_engine_agent.py (Sonnet):** Intent classification for query routing.

**refactoring_agent.py (Sonnet):** Code refactoring suggestions.

### 5.8 Code Generation (7 agents, mixed tiers)

**codegen_python.py (603 lines, Sonnet):**
- 8 code types: script, class, function, cli, api, test, agent, pipeline
- Template-based generation via 8 generator methods
- `_gen_agent()` generates full NLKE 5-layer agent scaffold
- `_check_anti_patterns(code)` scans for: bare except, import *, mutable defaults, os.path usage

**codegen_orchestrator.py (Opus):** Routes to appropriate language-specific generator.

**codegen_javascript.py, codegen_sql.py, codegen_bash.py, codegen_html_css.py, codegen_gemini.py** (Sonnet/Haiku).

### 5.9 MCP Tool Creator (1 agent, Sonnet)

**mcp_tool_creator.py (638 lines):**
- Most complex agent — compound orchestrator with 3 internal sub-analyzers
- L4 Orchestrator: `MCPToolCreatorOrchestrator` with 5-stage pipeline:
  1. Parse (MCPSpecAnalyzer) -> 2. Validate (MCPValidationAnalyzer, gates on CRITICAL) -> 3. Generate -> 4. Rule Match (MCPRuleMatchAnalyzer) -> 5. Output
- Extended CLI: `--from-agent`, `--from-python`, `--from-cookbook`, `--interactive`, `--batch`, `--stats`, `--no-write`
- Supports batch conversion of entire directories

### 5.10 Other Categories

**Routing:** `agentic_tool_router.py` (295 lines, Sonnet) — Complete 40-agent registry with scoring. Score = `matching_capabilities * 10.0 + exact_match * 5.0`. Confidence = `min(1.0, score / 30.0)`.

**Reporting:** `visual_report.py` (335 lines, Haiku) — Matplotlib bar/pie/line charts with non-interactive Agg backend.

**Advanced:** `embedding_engine.py` (Sonnet), `citation_analyzer.py` (Haiku).

**Cross-Provider:** `gemini_compute.py` (Sonnet), `web_research.py` (Sonnet).

---

## 6. Output Contract Enforcement

### 6.1 Contract Definition

Every agent MUST produce:
- `recommendations` — List of actionable items with technique, impact, reasoning
- `rules_applied` — Rule IDs in `PLAYBOOK-X_rule_YYY` format
- `meta_insight` — Single most important emergent observation

### 6.2 Enforcement Chain

```
Agent completes
    |
    v
[SubagentStop hook fires]  (plugin.json)
    |
    v
[validate_agent_output.py]
    |
    +---> Check: "recommendations" key exists and is non-empty list
    +---> Check: "rules_applied" key exists and is non-empty list
    +---> Check: "meta_insight" key exists and is non-empty string
    |
    v
Pass: agent output accepted
Fail: error reported to user
```

### 6.3 Rule ID Naming Convention

All rule IDs follow `{domain}_{number}_{description}`:

| Domain | Example | Agent |
|--------|---------|-------|
| dep | `dep_002_caching_requires_repeated_requests` | cost-advisor |
| comp | `comp_001_cache_size_effectiveness` | cost-advisor |
| cons | `cons_003_batch_latency_tradeoff` | cost-advisor |
| model_selection | `model_selection_001_match_complexity` | cost-advisor |
| gemini | `gemini_001_migration_analysis` | cost-advisor |
| cascade | `cascade_001_tier_routing` | compound-intelligence |
| context | `context_001_hierarchical_stacking` | context-engineer |
| validate | `validate_001_anti_pattern_scan` | anti-pattern-validator |
| heuristic | `heuristic_001_batch_realtime` | anti-pattern-validator |
| rag | `rag_001_keyword_extraction` | rag-kg-query |
| codegen | `codegen_001_type_hints_required` | codegen-python |
| report | `report_001_chart_selection` | visual-report |
| route | `route_001_intent_matching` | agentic-tool-router |
| mcp | `mcp_creator_001_pipeline` | mcp-tool-creator |
| workflow | `workflow_001_template_selection` | workflow-orchestrator |

---

## 7. Plugin System (.claude/plugin.json)

```json
{
  "name": "nlke",
  "version": "11.0",
  "description": "NLKE Agent Ecosystem - 40 specialized AI agents...",
  "author": "Eyal",
  "hooks": {
    "SubagentStop": [{
      "type": "command",
      "command": "python3 scripts/hooks/validate_agent_output.py"
    }]
  },
  "skills": ["skills/kg-build.md", "skills/cost-analyze.md", "skills/generate-agent.md"],
  "metadata": {
    "total_agents": 40,
    "total_python_tools": 51,
    "total_commands": 8,
    "model_tiers": {"opus": 4, "sonnet": 20, "haiku": 16},
    "categories": 14,
    "phase": "10.0"
  }
}
```

---

## 8. Rules Layer (6 files at .claude/rules/)

| File | Paths Scope | Preserves |
|------|------------|-----------|
| `output-contract.md` | All agents | Output contract (recommendations, rules_applied, meta_insight) + 5-layer pattern |
| `agent-conventions.md` | All agents | 8 rules: dual format, shared base, CLI, model tiers, YAML frontmatter, naming |
| `cost-optimization.md` | `**/cost-*`, `**/batch-*`, `**/thinking-*` | Claude+Gemini pricing, thresholds (thinking plateau=8K, cache min=1K, batch min=10) |
| `gemini-api.md` | `**/gemini-*`, `**/multi-model*` | 5 best practices: system_instruction, response_mime_type, safety_settings, countTokens, caching |
| `kg-operations.md` | `**/*kg*`, `**/kg-*`, `**/knowledge*` | 6 KG databases with counts, 30 valid node types, mandatory health check before/after |
| `mcp-development.md` | `**/mcp-*`, `**/mcp_*` | 15 anti-patterns, 50 rules, constraints (30s timeout, 4MB limit, JSON-serializable) |

**Path-conditional loading:** Claude Code loads rules based on the working directory. Universal rules always apply; domain rules apply only when editing matching paths.

---

## 9. Skills Layer (3 files at .claude/skills/)

### 9.1 kg-build.md (43 lines)

6-step pipeline: Entity Extraction -> Build SQLite KG -> Health Check (kg_health_monitor.py) -> Relationship Suggestion (relationship_suggester.py) -> Gap Detection (kg_completer.py) -> Validation Report

### 9.2 cost-analyze.md (38 lines)

5-step pipeline: Gather Workload -> Run Cost Advisor -> Thinking Budget Analysis -> Cross-Provider Comparison -> Implementation Roadmap

### 9.3 generate-agent.md (45 lines)

5-step pipeline: Gather Spec -> Generate .md -> Generate .py (5-layer) -> Test (`--example`) -> Register in MEMORY.md

**Self-referential:** Step 5 updates MEMORY.md after creating a new agent, ensuring persistent memory reflects the new state.

---

## 10. Model Tier Distribution

### 10.1 By Tier

**Opus (4):** Strategic, compound, cross-provider orchestration
- opus-expender, compound-intelligence, multi-model-orchestrator, codegen-orchestrator

**Sonnet (20):** Analysis, generation, reasoning
- code-analyzer, relationship-suggester, kg-completer, workflow-orchestrator, generator-agent, cost-quality-frontier, gemini-delegator, rule-engine, rag-kg-query, intent-engine, refactoring-agent, mcp-tool-creator, embedding-engine, gemini-compute, web-research, agentic-tool-router, codegen-python, codegen-javascript, codegen-html-css, codegen-gemini

**Haiku (16):** Monitoring, validation, quick lookups
- doc-updater, md-cat, py-cat, cost-advisor, batch-optimizer, thinking-budget, kg-health, progressive-assembly, self-healing-docs, context-engineer, anti-pattern-validator, playbook-advisor, citation-analyzer, visual-report, codegen-sql, codegen-bash

### 10.2 Cost Implications

| Tier | Agents | Input $/M | Output $/M | Typical Use |
|------|--------|-----------|------------|-------------|
| Opus | 4 | 15.00 | 75.00 | Architecture, strategy, orchestration |
| Sonnet | 20 | 3.00 | 15.00 | Analysis, generation, reasoning |
| Haiku | 16 | 0.80 | 4.00 | Monitoring, validation, lookups |

**Compound Intelligence default:** 90% Haiku + 10% Sonnet + 0% Opus = massive savings vs all-Opus.

---

## 11. Architecture Visualization (ARCHITECTURE.mmd)

171-line Mermaid diagram defining complete topology:

```
Tier groupings:
  Opus (4): opus-expender, compound-intelligence, multi-model-orchestrator, codegen-orchestrator
  Sonnet (20): organized into 8 subgroups
  Haiku (16): organized into 4 subgroups

Data flow connections:
  Escalation: Haiku Cost -> Sonnet Emergent -> Opus Compound Intelligence
  Routing: codegen-orchestrator -> language-specific generators
  External: gemini-delegator -> Gemini API; rule-engine -> Synthesis Rules
  KG: kg-health + rag-kg-query -> KG databases
  AI-LAB: Output Contract -> AI-LAB (22 GGUF models)
```

---

## 12. Cross-Agent Data Flow Patterns

### 12.1 Agent Invocation Chain

```
User invokes /<agent-name> in Claude Code
    |
    v
Claude Code loads ~/.claude/agents/<name>.md
    |  (YAML frontmatter: model, tools, description)
    |  (Body: system prompt, capabilities, workflow)
    |
    v
Claude Code becomes the agent
    |  (Uses declared tools: Read, Write, Bash, Glob, Grep, Task)
    |
    v
Agent's .md instructs Claude to run .py tool:
    python3 /absolute/path/to/agents/<category>/<name>.py --example
    |
    v
.py tool executes deterministic analysis:
    L3 Analyzer.analyze(AgentInput) -> AgentOutput
    |
    v
Claude reads JSON output, interprets via .md guidance
    |
    v
SubagentStop hook: validate_agent_output.py checks output contract
    |
    v
Response to user with recommendations + rules + meta_insight
```

### 12.2 Pipeline SDK Chain

```
Pipeline("cost-optimization")
    .add("cost-advisor", workload={...})
    .add("compound-intelligence", depends_on=["cost-advisor"],
         transform=lambda out: {"subtasks": out["recommendations"]})
    .add("cost-quality-frontier", workload={...})
    .run()
    |
    v
PipelineResult(
    name="cost-optimization",
    total_steps=3, succeeded=3, failed=0,
    aggregated_recommendations=[...all merged...],
    aggregated_rules=[...all unique...]
)
```

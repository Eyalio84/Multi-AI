# NLKE Agents — Project Instructions

## What This Is

The `agents/` directory contains all 40 NLKE agent Python implementations organized by category.
Each agent is a standalone CLI tool that follows the 5-layer architecture pattern.

## Rules

### Output Contract (Mandatory)
Every agent MUST produce `AgentOutput` with:
- `recommendations` — List of actionable items with `technique`, `impact`, `reasoning`
- `rules_applied` — Which synthesis rules were used (PLAYBOOK-X_rule_YYY format)
- `meta_insight` — Single most important emergent observation

### 5-Layer Pattern (Mandatory)
All agents inherit from `shared/agent_base.py`:
- **L1:** `AgentInput`, `AgentOutput` dataclasses
- **L2:** Constants (paths, pricing, thresholds)
- **L3:** `BaseAnalyzer` subclass with `analyze()` and `get_example_input()`
- **L4:** `AgentOrchestrator` for multi-stage composition
- **L5:** `run_standard_cli()` for CLI interface

### CLI Interface (Mandatory)
Every agent must work with:
```bash
python3 agents/<category>/<agent>.py --example          # Built-in example data
python3 agents/<category>/<agent>.py --workload f.json  # Custom input
python3 agents/<category>/<agent>.py --output out.json  # Save to file
python3 agents/<category>/<agent>.py --summary          # Human-readable
```

### Naming Conventions
- Directory names: `kebab-case` (e.g., `cost-optimization/`)
- Python files: `snake_case` (e.g., `cost_advisor.py`)
- Analyzer classes: `PascalCase` ending in `Analyzer` (e.g., `CostAnalyzer`)
- Agent registry keys: `kebab-case` matching the agent name (e.g., `cost-advisor`)

### Model Tier Assignment
- **Haiku** ($0.00025/call): Routine tasks, monitoring, validation, simple categorization
- **Sonnet** ($0.003/call): Complex analysis, code generation, multi-step reasoning
- **Opus** ($0.015/call): Strategic orchestration, compound intelligence, cross-agent routing

### Imports
```python
# All agents import from shared base
from agents.shared.agent_base import (
    AgentInput, AgentOutput, BaseAnalyzer,
    AgentOrchestrator, run_standard_cli,
    NLKE_ROOT, PRICING, THRESHOLDS,
)
```

### Path Resolution
All file paths must be absolute. Use `Path(__file__).resolve().parent` for relative references.
Never hardcode paths relative to CWD.

### Gemini Fallback
Any agent calling Gemini APIs must gracefully handle missing `GEMINI_API_KEY`:
```python
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    return fallback_result()  # Local analysis without Gemini
```

## Pipeline SDK

The SDK at `shared/agent_sdk.py` registers 35 agents for pipeline composition:
```python
from agents.shared.agent_sdk import Pipeline, AgentRunner

# Single agent
result = AgentRunner.run("cost-advisor", workload={...})

# Pipeline
pipeline = Pipeline("Name")
pipeline.add("agent-1", workload={...})
pipeline.add("agent-2", depends_on=["agent-1"])
result = pipeline.run()
```

## Testing

```bash
# Test any single agent
python3 agents/cost-optimization/cost_advisor.py --example

# Test all agents (from NLKE root)
for f in agents/*/[!_]*.py; do python3 "$f" --example > /dev/null 2>&1 && echo "PASS: $f" || echo "FAIL: $f"; done
```

## Key Paths

| Resource | Path |
|----------|------|
| Shared base | `agents/shared/agent_base.py` |
| Agent SDK | `agents/shared/agent_sdk.py` |
| NLKE root | `/storage/self/primary/Download/44nlke/NLKE/` |
| AI-LAB root | `/storage/emulated/0/Download/gemini-3-pro/AI-LAB/` |
| Synthesis rules | `/storage/emulated/0/Download/synthesis-rules/` |
| KG databases | See `agent_base.py` `KG_DATABASES` dict |

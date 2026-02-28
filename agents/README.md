# NLKE Agents Directory

**40 agents** across **14 categories** — the Python implementation layer of the NLKE ecosystem.

## Quick Start

```bash
# Run any agent with built-in example data
python3 agents/cost-optimization/cost_advisor.py --example

# Run with custom workload
python3 agents/kg-enhancement/kg_health_monitor.py --workload input.json

# Save output to file
python3 agents/codegen/codegen_python.py --example --output result.json

# Human-readable summary
python3 agents/emergent/compound_intelligence.py --example --summary

# Run via SDK pipeline
python3 agents/shared/agent_sdk.py
```

## Directory Structure

```
agents/
├── shared/                    # Shared infrastructure (2 files)
│   ├── agent_base.py          # L1-L5 base classes, constants, CLI helper
│   └── agent_sdk.py           # Pipeline SDK, 35-agent registry, AgentRunner
│
├── cost-optimization/         # API cost analysis (3 agents)
│   ├── cost_advisor.py        # Haiku — API cost analysis + Gemini pricing
│   ├── batch_optimizer_agent.py # Haiku — Batch API configuration
│   └── thinking_budget_agent.py # Haiku — Thinking budget allocation
│
├── kg-enhancement/            # Knowledge graph tools (3 agents)
│   ├── kg_health_monitor.py   # Haiku — Multi-KG health monitoring
│   ├── relationship_suggester_agent.py # Sonnet — 9-type edge suggestion
│   └── kg_completer.py        # Sonnet — Gap detection + auto-fill
│
├── workflow-automation/       # Orchestration (3 agents)
│   ├── workflow_orchestrator.py # Sonnet — Cross-provider workflow planning
│   ├── generator_agent.py     # Sonnet — Agent factory (creates new agents)
│   └── progressive_assembly.py # Haiku — Chunk-validate-combine
│
├── emergent/                  # Emergent intelligence (3 agents)
│   ├── compound_intelligence.py # Opus — 3-tier cascade (haiku→sonnet→opus)
│   ├── self_healing_docs.py   # Haiku — Doc drift detection and repair
│   └── cost_quality_frontier.py # Sonnet — Pareto optimization curves
│
├── multi-model/               # Cross-provider orchestration (3 agents)
│   ├── multi_model_orchestrator.py # Opus — Capability matching + Gemini exec
│   ├── gemini_delegator.py    # Sonnet — Batch delegation, retry, caching
│   └── context_engineer.py    # Sonnet — Gemini 1M context strategy
│
├── rule-engine/               # Rule validation (3 agents)
│   ├── rule_engine_agent.py   # Sonnet — 647-rule engine integration
│   ├── anti_pattern_validator.py # Haiku — Pre-flight anti-pattern scan
│   └── playbook_advisor.py    # Haiku — Task-to-playbook matching
│
├── knowledge-retrieval/       # RAG and query (3 agents)
│   ├── rag_kg_query.py        # Sonnet — Graph-RAG hybrid query
│   ├── intent_engine_agent.py # Sonnet — NL intent to framework mapping
│   └── refactoring_agent.py   # Sonnet — Code analysis + refactoring
│
├── mcp-tool-creator/          # MCP server generation (1 agent + 10 support files)
│   ├── mcp_tool_creator.py    # Sonnet — Compound MCP tool server generator
│   ├── mcp_spec_parser.py     # Spec parsing
│   ├── mcp_generators/        # Code generation modules
│   │   ├── from_agent.py
│   │   ├── from_cookbook.py
│   │   └── from_python.py
│   ├── mcp_templates/         # Server/tool templates
│   │   ├── server_template.py
│   │   └── tool_template.py
│   ├── mcp_validators/        # Validation rules
│   │   ├── mcp_anti_patterns.py
│   │   └── mcp_rules.py
│   └── generated/             # Generated MCP tools + tests
│       ├── mcp_tool_cost_advisor.py
│       ├── mcp_tool_batch_optimizer.py
│       ├── mcp_tool_thinking_budget_optimizer.py
│       └── test_mcp_tool_*.py
│
├── advanced/                  # Specialized tools (2 agents)
│   ├── embedding_engine.py    # Sonnet — Gemini embedding + cosine similarity
│   └── citation_analyzer.py   # Haiku — Citation extraction + fabrication detection
│
├── cross-provider/            # Gemini integration (2 agents)
│   ├── gemini_compute.py      # Sonnet — Gemini code_execution sandbox
│   └── web_research.py        # Sonnet — Gemini google_search_grounding
│
├── reporting/                 # Output generation (1 agent)
│   └── visual_report.py       # Haiku — matplotlib/pillow chart generation
│
├── routing/                   # Agent routing (1 agent)
│   └── agentic_tool_router.py # Sonnet — 40-agent registry, intent routing
│
└── codegen/                   # Code generation fleet (7 agents)
    ├── codegen_python.py      # Sonnet — Python scripts/classes/CLI/API/tests
    ├── codegen_javascript.py  # Sonnet — JS/TS/React/Express/Node
    ├── codegen_sql.py         # Haiku — SQLite/PostgreSQL schema/queries
    ├── codegen_bash.py        # Haiku — Shell automation/CI-CD/deploy
    ├── codegen_html_css.py    # Sonnet — HTML/CSS/Tailwind/responsive
    ├── codegen_gemini.py      # Sonnet — Gemini API integrations
    └── codegen_orchestrator.py # Opus — Routes tasks to domain agents
```

## Model Tiers

| Tier | Count | Cost/Call | Agents |
|------|-------|-----------|--------|
| **Opus** | 4 | $0.015 | compound-intelligence, multi-model-orchestrator, codegen-orchestrator, opus-expender |
| **Sonnet** | 20 | $0.003 | code-analyzer, relationship-suggester, kg-completer, workflow-orchestrator, generator-agent, cost-quality-frontier, gemini-delegator, context-engineer, rule-engine, rag-kg-query, intent-engine, refactoring-agent, mcp-tool-creator, embedding-engine, gemini-compute, web-research, agentic-tool-router, codegen-python, codegen-javascript, codegen-html-css, codegen-gemini |
| **Haiku** | 16 | $0.00025 | doc-updater, md-cat, py-cat, cost-advisor, batch-optimizer, thinking-budget, kg-health, progressive-assembly, self-healing-docs, anti-pattern-validator, playbook-advisor, citation-analyzer, visual-report, codegen-sql, codegen-bash |

## 5-Layer Architecture

Every agent follows the same pattern:

```
L1: Data Models     → AgentInput, AgentOutput (dataclasses)
L2: Constants       → Paths, pricing tables, thresholds
L3: BaseAnalyzer    → Abstract class with analyze() + get_example_input()
L4: Orchestrator    → AgentOrchestrator for multi-stage composition
L5: CLI             → run_standard_cli() with --example, --workload, --output, --summary
```

## Output Contract

Every agent MUST produce:

```python
AgentOutput(
    recommendations=[...],  # List of actionable items
    rules_applied=[...],    # Synthesis rules used (PLAYBOOK-X_rule_YYY)
    meta_insight="...",     # Key emergent observation
)
```

## Pipeline SDK

Compose multi-agent pipelines programmatically:

```python
from agents.shared.agent_sdk import Pipeline

pipeline = Pipeline("My Workflow")
pipeline.add("cost-advisor", workload={"api_calls": [...]})
pipeline.add("batch-optimizer", depends_on=["cost-advisor"])
pipeline.add("visual-report", depends_on=["batch-optimizer"])
result = pipeline.run()

print(f"Succeeded: {result.succeeded}/{result.total_steps}")
print(f"Recommendations: {len(result.aggregated_recommendations)}")
```

## File Stats

- **68 Python files** (51 `.py` + 17 `__init__.py`)
- **14 directories** (categories)
- **35 agents** registered in SDK pipeline registry
- **~12,000 lines** of Python across all agents

## Related Resources

- Agent definitions (`.md`): `~/.claude/agents/`
- NOF workflows: `Eyal-s--agents/workflows/*.nof.md`
- Web dashboard: `Eyal-s--agents/site/server.py`
- SDK source: `agents/shared/agent_sdk.py`
- Base classes: `agents/shared/agent_base.py`

"""Registry-based service that wraps 30 Python tools for the Tools Playground."""
import sys
import asyncio
import importlib
import dataclasses
import traceback
from dataclasses import dataclass, field, asdict
from typing import Any, Optional
from pathlib import Path

from config import TOOLS_DIR


@dataclass
class ToolParam:
    name: str
    type: str           # string | text | json | integer | float | boolean
    label: str
    required: bool
    default: Any
    description: str
    multiline: bool = False


@dataclass
class ToolDefinition:
    id: str
    name: str
    category: str
    description: str
    params: list
    module_path: str     # dotted path under tools/ e.g. "reasoning.task_classifier"
    entry_point: str     # "ClassName.method" or "function_name"
    constructor_params: list = field(default_factory=list)
    is_async: bool = False
    output_format: str = "json"


class ToolsService:
    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}
        self._path_added = False
        self._register_all()

    def _ensure_path(self):
        if self._path_added:
            return
        tools_root = str(TOOLS_DIR)
        if tools_root not in sys.path:
            sys.path.insert(0, tools_root)
        # Also add each subdirectory for relative imports within tools
        for sub in TOOLS_DIR.iterdir():
            if sub.is_dir() and not sub.name.startswith(("__", ".")):
                sub_str = str(sub)
                if sub_str not in sys.path:
                    sys.path.insert(0, sub_str)
        self._path_added = True

    def _reg(self, tool: ToolDefinition):
        self._tools[tool.id] = tool

    def _register_all(self):
        # === Code Quality (4) ===
        self._reg(ToolDefinition(
            id="code_review_generator",
            name="Code Review Generator",
            category="Code Quality",
            description="Analyze code for style, security, performance, and maintainability issues",
            module_path="dev.enhanced_coding",
            entry_point="CodeReviewGenerator.generate_review",
            constructor_params=[],
            params=[
                ToolParam("code", "text", "Code to Review", True, None, "Paste the code to analyze", True),
                ToolParam("language", "string", "Language", False, "python", "Programming language"),
                ToolParam("depth", "string", "Review Depth", False, "comprehensive", "quick | focused | comprehensive"),
            ],
        ))
        self._reg(ToolDefinition(
            id="refactoring_analyzer",
            name="Refactoring Analyzer",
            category="Code Quality",
            description="Detect code smells and suggest refactoring opportunities with ROI estimates",
            module_path="dev.refactoring_analyzer",
            entry_point="RefactoringAnalyzer.analyze_code_smells",
            constructor_params=["code", "language"],
            params=[
                ToolParam("code", "text", "Code to Analyze", True, None, "Paste code to analyze for smells", True),
                ToolParam("language", "string", "Language", False, "python", "Programming language"),
            ],
        ))
        self._reg(ToolDefinition(
            id="tdd_assistant",
            name="TDD Assistant",
            category="Code Quality",
            description="Validate TDD workflow execution and generate test recommendations",
            module_path="dev.tdd_assistant",
            entry_point="validate_tdd_workflow",
            params=[
                ToolParam("execution", "json", "Execution Data", True, None,
                          '{"function_spec": {"name": "add", "description": "Add two numbers", "inputs": ["a: int", "b: int"], "outputs": "int"}, "tests_written": 3, "tests_passing": 2, "cycle": "red"}',
                          True),
            ],
        ))
        self._reg(ToolDefinition(
            id="code_analyzer",
            name="Code Analyzer Agent",
            category="Code Quality",
            description="Multi-dimensional code analysis: complexity, patterns, security, dependencies",
            module_path="agents.code_analyzer_agent",
            entry_point="CodeAnalyzerAgent.analyze_file",
            constructor_params=[],
            params=[
                ToolParam("file_path", "string", "File Path", True, None, "Path to Python file to analyze"),
            ],
        ))

        # === Cost Optimization (5) ===
        self._reg(ToolDefinition(
            id="cost_analyzer",
            name="Cost Analyzer",
            category="Cost Optimization",
            description="Analyze API workload for caching, batching, and compound optimization opportunities",
            module_path="foundation.cost_optimization",
            entry_point="analyze_cost_opportunities",
            params=[
                ToolParam("workload", "json", "Workload Config", True, None,
                          '{"requests_per_day": 1000, "avg_input_tokens": 2000, "avg_output_tokens": 500, "has_repeated_prefixes": true, "batch_eligible_pct": 0.3}',
                          True),
            ],
        ))
        self._reg(ToolDefinition(
            id="thinking_budget_optimizer",
            name="Thinking Budget Optimizer",
            category="Cost Optimization",
            description="Calculate optimal thinking token budgets for complex tasks",
            module_path="foundation.extended_thinking",
            entry_point="ThinkingBudgetOptimizer.optimize",
            constructor_params=[],
            params=[
                ToolParam("task_description", "text", "Task Description", True, None, "Describe the task to optimize thinking for", True),
                ToolParam("task_type", "string", "Task Type", False, "PROBLEM_SOLVING",
                          "REQUIREMENTS_ANALYSIS | ARCHITECTURE_DESIGN | API_DESIGN | CODE_DEBUGGING | RESEARCH_ANALYSIS | CODE_REVIEW | PROBLEM_SOLVING"),
            ],
        ))
        self._reg(ToolDefinition(
            id="haiku_delegation",
            name="Haiku Delegation Analyzer",
            category="Cost Optimization",
            description="Determine which tasks can be delegated to cheaper Haiku model",
            module_path="foundation.haiku_delegation",
            entry_point="classify_task_complexity",
            params=[
                ToolParam("task_description", "text", "Task Description", True, None, "Describe the task to classify", True),
            ],
        ))
        self._reg(ToolDefinition(
            id="task_classifier",
            name="Task Classifier",
            category="Cost Optimization",
            description="Classify task complexity (TRIVIAL to VERY_COMPLEX) with detailed indicators",
            module_path="reasoning.task_classifier",
            entry_point="TaskClassifier.classify",
            constructor_params=[],
            params=[
                ToolParam("task_description", "text", "Task Description", True, None, "Describe the task to classify", True),
            ],
        ))
        self._reg(ToolDefinition(
            id="error_classifier",
            name="Error Classifier",
            category="Cost Optimization",
            description="Classify API errors and recommend retry strategies with backoff calculations",
            module_path="dev.production_resilience",
            entry_point="classify_error",
            params=[
                ToolParam("status_code", "integer", "Status Code", True, 429, "HTTP status code"),
                ToolParam("error_message", "string", "Error Message", False, "", "Error message text"),
            ],
        ))

        # === Agent Intelligence (4) ===
        self._reg(ToolDefinition(
            id="plan_complexity",
            name="Plan Complexity Analyzer",
            category="Agent Intelligence",
            description="Classify task complexity and estimate blast radius for agent planning",
            module_path="agent.plan_mode_patterns",
            entry_point="classify_complexity",
            params=[
                ToolParam("task_description", "text", "Task Description", True, None, "Describe the task to analyze", True),
                ToolParam("codebase_size", "string", "Codebase Size", False, "medium", "small | medium | large"),
            ],
        ))
        self._reg(ToolDefinition(
            id="plan_roi_estimator",
            name="Plan ROI Estimator",
            category="Agent Intelligence",
            description="Estimate return on investment for planning vs. direct execution",
            module_path="agent.plan_mode_patterns",
            entry_point="estimate_roi",
            params=[
                ToolParam("task_description", "text", "Task Description", True, None, "Describe the task", True),
                ToolParam("estimated_files", "integer", "Estimated Files Changed", False, 5, "Number of files expected to change"),
            ],
        ))
        self._reg(ToolDefinition(
            id="composition_analyzer",
            name="Tool Composition Analyzer",
            category="Agent Intelligence",
            description="Analyze tool composition patterns and detect anti-patterns",
            module_path="agent.conversation_tools",
            entry_point="analyze_composition",
            params=[
                ToolParam("tools", "json", "Tool Chain", True, None,
                          '["prompt_caching", "batch_api", "extended_thinking"]',
                          True),
                ToolParam("goal", "string", "Goal", False, "", "What the composition aims to achieve"),
            ],
        ))
        self._reg(ToolDefinition(
            id="workload_analyzer",
            name="Workload Analyzer",
            category="Agent Intelligence",
            description="Analyze a workload to determine optimal tool combinations",
            module_path="agent.conversation_tools",
            entry_point="analyze_workload",
            params=[
                ToolParam("workload", "json", "Workload", True, None,
                          '{"task": "code review", "volume": "high", "latency_sensitive": false}',
                          True),
            ],
        ))

        # === Knowledge Graph (5) ===
        self._reg(ToolDefinition(
            id="embedding_generator",
            name="Embedding Generator",
            category="Knowledge Graph",
            description="Generate semantic embeddings for items using heuristic (free) or hybrid approach",
            module_path="knowledge.embedding_systems",
            entry_point="generate_heuristic_embedding",
            params=[
                ToolParam("item", "json", "Item Data", True, None,
                          '{"name": "context caching", "description": "Cache repeated prefixes to reduce costs", "type": "pattern", "category": "optimization"}',
                          True),
            ],
        ))
        self._reg(ToolDefinition(
            id="rag_analyzer",
            name="RAG Query Analyzer",
            category="Knowledge Graph",
            description="Analyze a RAG query and recommend retrieval method, fusion strategy, and context optimization",
            module_path="knowledge.advanced_rag_fusion",
            entry_point="analyze_rag_query",
            params=[
                ToolParam("query", "text", "Query", True, None, "The search query to analyze", True),
                ToolParam("corpus_size", "integer", "Corpus Size", False, 1000, "Number of documents in corpus"),
                ToolParam("avg_doc_length", "integer", "Avg Doc Length", False, 500, "Average document length in tokens"),
            ],
        ))
        self._reg(ToolDefinition(
            id="fusion_recommender",
            name="Fusion Strategy Recommender",
            category="Knowledge Graph",
            description="Recommend optimal fusion method for combining retrieval sources",
            module_path="knowledge.advanced_rag_fusion",
            entry_point="recommend_fusion",
            params=[
                ToolParam("sources", "json", "Sources", True, None,
                          '["semantic_search", "bm25_keyword", "graph_neighbors"]', True),
                ToolParam("query_type", "string", "Query Type", False, "factual", "factual | exploratory | navigational"),
            ],
        ))
        self._reg(ToolDefinition(
            id="context_optimizer",
            name="Context Window Optimizer",
            category="Knowledge Graph",
            description="Optimize context window allocation and recommend compression strategies",
            module_path="knowledge.advanced_rag_fusion",
            entry_point="optimize_context",
            params=[
                ToolParam("context_size", "integer", "Context Size (tokens)", True, 50000, "Current context size in tokens"),
                ToolParam("model_limit", "integer", "Model Limit (tokens)", False, 200000, "Model context window limit"),
                ToolParam("num_sources", "integer", "Number of Sources", False, 10, "Number of retrieval sources"),
            ],
        ))
        self._reg(ToolDefinition(
            id="graph_engineer",
            name="Graph Engineer",
            category="Knowledge Graph",
            description="Parse documentation into KG nodes and edges with complexity/cost estimates",
            module_path="knowledge.graph_engineering",
            entry_point="DocumentationParser.parse_documentation_matrix",
            constructor_params=["documentation_text"],
            params=[
                ToolParam("documentation_text", "text", "Documentation Text", True, None,
                          "Paste documentation to parse into knowledge graph nodes and edges", True),
            ],
        ))

        # === Generators (4) ===
        self._reg(ToolDefinition(
            id="boilerplate_generator",
            name="Boilerplate Generator",
            category="Generators",
            description="Generate design patterns (singleton, factory, builder, retry, cache, etc.)",
            module_path="generators.boilerplate_generator",
            entry_point="BoilerplateGenerator.generate_pattern",
            constructor_params=[],
            params=[
                ToolParam("pattern_name", "string", "Pattern", True, "singleton",
                          "singleton | factory | builder | adapter | decorator | facade | observer | strategy | retry | cache | logging | timer | validate | circuit_breaker"),
                ToolParam("class_name", "string", "Class Name", False, "MyClass", "Name for the generated class"),
            ],
        ))
        self._reg(ToolDefinition(
            id="ast_generator",
            name="AST Code Generator",
            category="Generators",
            description="Programmatically generate syntactically-correct Python code via AST",
            module_path="generators.ast_generator",
            entry_point="ASTGenerator.generate_function",
            constructor_params=[],
            params=[
                ToolParam("name", "string", "Function Name", True, "process_data", "Name of the function"),
                ToolParam("params", "json", "Parameters", False, '["data: list", "verbose: bool = False"]', "List of param strings", True),
                ToolParam("returns", "string", "Return Type", False, "dict", "Return type annotation"),
                ToolParam("body_description", "string", "Body Description", False, "Process and return data", "What the function should do"),
            ],
        ))
        self._reg(ToolDefinition(
            id="scaffold_generator",
            name="Project Scaffold Generator",
            category="Generators",
            description="Preview Python project scaffold structure (API, CLI, library, agent, MCP server)",
            module_path="generators.scaffold_generator",
            entry_point="ScaffoldGenerator.preview_project",
            constructor_params=[],
            params=[
                ToolParam("project_type", "string", "Project Type", True, "api", "api | cli | library | fullstack | script | agent | mcp_server"),
                ToolParam("name", "string", "Project Name", True, "my-project", "Name of the project"),
                ToolParam("features", "json", "Features", False, '["auth", "database"]', "List of features to include", True),
            ],
        ))
        self._reg(ToolDefinition(
            id="template_generator",
            name="Template Validator",
            category="Generators",
            description="Validate Jinja2-style templates and inspect variables/blocks",
            module_path="generators.template_generator",
            entry_point="TemplateGenerator.validate",
            constructor_params=[],
            params=[
                ToolParam("template", "text", "Template", True, None,
                          "Hello {{ name }}! {% if premium %}Premium member{% endif %}", True),
            ],
        ))

        # === Reasoning & Workflows (5) ===
        self._reg(ToolDefinition(
            id="thinking_budget_calculator",
            name="Thinking Budget Calculator",
            category="Reasoning",
            description="Calculate optimal thinking token budget based on complexity, novelty, and stakes",
            module_path="reasoning.patterns",
            entry_point="calculate_budget",
            params=[
                ToolParam("task_description", "text", "Task Description", True, None, "Describe the task", True),
                ToolParam("novelty", "float", "Novelty (0-1)", False, 0.5, "How novel is this task? 0=routine, 1=unprecedented"),
                ToolParam("stakes", "string", "Stakes", False, "medium", "low | medium | high"),
            ],
        ))
        self._reg(ToolDefinition(
            id="thinking_roi",
            name="Thinking ROI Estimator",
            category="Reasoning",
            description="Estimate ROI of extended thinking for a given task",
            module_path="reasoning.patterns",
            entry_point="estimate_roi",
            params=[
                ToolParam("task_description", "text", "Task Description", True, None, "Describe the task", True),
                ToolParam("thinking_tokens", "integer", "Thinking Tokens", False, 10000, "Number of thinking tokens to allocate"),
            ],
        ))
        self._reg(ToolDefinition(
            id="reasoning_engine",
            name="Reasoning Engine",
            category="Reasoning",
            description="Analyze goals for reasoning patterns (tangential, adversarial, causal, combinatorial)",
            module_path="reasoning.engine",
            entry_point="analyze_goal",
            params=[
                ToolParam("goal", "text", "Goal", True, None, "Describe the goal or problem to analyze reasoning patterns for", True),
            ],
        ))
        self._reg(ToolDefinition(
            id="token_budget_calculator",
            name="Token Budget Calculator",
            category="Reasoning",
            description="Calculate token budget allocation across system, context, conversation layers",
            module_path="reasoning.context_window_mgmt",
            entry_point="calculate_budget",
            params=[
                ToolParam("task_type", "string", "Task Type", False, "feature", "bug_fix | feature | refactor | architecture"),
                ToolParam("total_budget", "integer", "Total Budget", False, 200000, "Total token budget"),
                ToolParam("project_files", "integer", "Project Files", False, 20, "Number of relevant project files"),
            ],
        ))
        self._reg(ToolDefinition(
            id="workflow_analyzer",
            name="Workflow Analyzer",
            category="Reasoning",
            description="Analyze multi-step workflows for complexity, parallelism opportunities, and ROI",
            module_path="reasoning.metacognition_workflows",
            entry_point="_run_workflow_analyzer",
            params=[
                ToolParam("steps", "json", "Workflow Steps", True, None,
                          '[{"name": "analyze", "complexity": "moderate", "category": "analysis"}, {"name": "implement", "complexity": "complex", "category": "implementation", "dependencies": ["analyze"]}]',
                          True),
                ToolParam("total_budget", "integer", "Total Budget", False, 30000, "Total thinking token budget"),
            ],
        ))

        # === Phase 1: Adapted Tools (14) ===

        self._reg(ToolDefinition(
            id="agent_pattern_analyzer",
            name="Agent Pattern Analyzer",
            category="Agent Intelligence",
            description="Analyze agent architecture patterns, communication styles, and anti-patterns",
            module_path="agent.agent_pattern_analyzer",
            entry_point="AgentPatternAnalyzer.analyze",
            constructor_params=[],
            params=[
                ToolParam("description", "text", "System Description", True, None, "Describe the agent system to analyze", True),
            ],
        ))
        self._reg(ToolDefinition(
            id="agent_orchestrator",
            name="Agent Orchestrator Planner",
            category="Orchestration",
            description="Decompose goals into orchestrated agent tasks with dependency ordering",
            module_path="orchestration.agent_orchestrator_tool",
            entry_point="AgentOrchestratorTool.plan",
            constructor_params=[],
            params=[
                ToolParam("goal", "text", "Goal", True, None, "Goal to decompose into agent tasks", True),
                ToolParam("max_agents", "integer", "Max Agents", False, 6, "Maximum number of agents"),
            ],
        ))
        self._reg(ToolDefinition(
            id="composition_validator",
            name="Composition Validator",
            category="Agent Intelligence",
            description="Validate tool/agent compositions for compatibility, conflicts, and synergies",
            module_path="agent.composition_validator",
            entry_point="CompositionValidator.validate",
            constructor_params=[],
            params=[
                ToolParam("tools", "json", "Tools List", True, None, '["rag", "embeddings", "batch_api"]', True),
                ToolParam("goal", "string", "Goal", False, "", "What the composition aims to achieve"),
            ],
        ))
        self._reg(ToolDefinition(
            id="universal_parser",
            name="Universal Parser",
            category="Knowledge Graph",
            description="Parse any text format (markdown, JSON, CSV, code, YAML) into structured data",
            module_path="knowledge.universal_parser",
            entry_point="UniversalParser.parse",
            constructor_params=[],
            params=[
                ToolParam("text", "text", "Text to Parse", True, None, "Paste text in any format", True),
                ToolParam("format_hint", "string", "Format Hint", False, "auto", "auto | markdown | json | csv | code | yaml"),
            ],
        ))
        self._reg(ToolDefinition(
            id="documentation_generator",
            name="Documentation Generator",
            category="Dev Tools",
            description="Generate API docs, README, or function docs from Python source code via AST",
            module_path="dev.documentation_generator",
            entry_point="DocumentationGenerator.generate",
            constructor_params=[],
            params=[
                ToolParam("code", "text", "Source Code", True, None, "Python code to document", True),
                ToolParam("doc_type", "string", "Doc Type", False, "api", "api | readme | function | module"),
                ToolParam("language", "string", "Language", False, "python", "Programming language"),
            ],
        ))
        self._reg(ToolDefinition(
            id="thinking_quality_validator",
            name="Thinking Quality Validator",
            category="Reasoning",
            description="Validate reasoning quality: detect fallacies, check structure, score arguments",
            module_path="reasoning.thinking_quality_validator",
            entry_point="ThinkingQualityValidator.validate",
            constructor_params=[],
            params=[
                ToolParam("reasoning", "text", "Reasoning Text", True, None, "Reasoning chain to validate", True),
                ToolParam("claim", "string", "Claim", False, "", "The claim being supported"),
            ],
        ))
        self._reg(ToolDefinition(
            id="batch_optimizer",
            name="Batch Optimizer",
            category="Cost Optimization",
            description="Optimize batch processing workloads for cost savings and throughput",
            module_path="foundation.batch_optimizer",
            entry_point="BatchOptimizer.optimize",
            constructor_params=[],
            params=[
                ToolParam("total_requests", "integer", "Total Requests", True, 1000, "Number of requests"),
                ToolParam("avg_input_tokens", "integer", "Avg Input Tokens", False, 1000, "Average input tokens per request"),
                ToolParam("avg_output_tokens", "integer", "Avg Output Tokens", False, 500, "Average output tokens per request"),
                ToolParam("model", "string", "Model", False, "gemini-2.5-flash", "Model to optimize for"),
            ],
        ))
        self._reg(ToolDefinition(
            id="cache_roi_calculator",
            name="Cache ROI Calculator",
            category="Cost Optimization",
            description="Calculate ROI for prompt caching with break-even analysis across 6 models",
            module_path="foundation.cache_roi_calculator",
            entry_point="CacheROICalculator.calculate",
            constructor_params=[],
            params=[
                ToolParam("prefix_tokens", "integer", "Prefix Tokens", True, 5000, "Number of cacheable prefix tokens"),
                ToolParam("requests_per_day", "integer", "Requests/Day", False, 100, "Daily request volume"),
                ToolParam("model", "string", "Model", False, "gemini-2.5-flash", "Target model"),
            ],
        ))
        self._reg(ToolDefinition(
            id="tool_registry_builder",
            name="Tool Registry Builder",
            category="Agent Intelligence",
            description="Generate tool definitions from Python code in OpenAI, Anthropic, Gemini, or MCP format",
            module_path="agent.tool_registry_builder",
            entry_point="ToolRegistryBuilder.build",
            constructor_params=[],
            params=[
                ToolParam("code", "text", "Python Code", True, None, "Code to extract tool definitions from", True),
                ToolParam("output_format", "string", "Output Format", False, "openai", "openai | anthropic | gemini | mcp"),
            ],
        ))
        self._reg(ToolDefinition(
            id="tfidf_indexer",
            name="TF-IDF Search",
            category="Knowledge Graph",
            description="Build and query a TF-IDF index from documents for keyword-based retrieval",
            module_path="knowledge.tfidf_indexer",
            entry_point="TFIDFIndexer.search",
            constructor_params=[],
            params=[
                ToolParam("documents", "json", "Documents", True, None,
                          '[{"id": "doc1", "text": "Python is great"}, {"id": "doc2", "text": "JavaScript is popular"}]', True),
                ToolParam("query", "string", "Search Query", True, "Python programming", "Query to search for"),
                ToolParam("top_k", "integer", "Top K", False, 5, "Number of results"),
            ],
        ))
        self._reg(ToolDefinition(
            id="prompt_generator",
            name="Prompt Generator",
            category="Knowledge Graph",
            description="Generate structured prompts from 7 templates (system, few-shot, chain-of-thought, etc.)",
            module_path="knowledge.prompt_generator",
            entry_point="PromptGenerator.generate",
            constructor_params=[],
            params=[
                ToolParam("prompt_type", "string", "Prompt Type", False, "system",
                          "system | few_shot | chain_of_thought | extraction | classification | summarization | comparison"),
                ToolParam("variables", "json", "Variables", False, '{"role": "expert coder", "task": "review code", "constraints": ["be concise"], "output_format": "JSON"}',
                          "Template variable values as JSON", True),
            ],
        ))
        self._reg(ToolDefinition(
            id="documentation_auditor",
            name="Documentation Auditor",
            category="Dev Tools",
            description="Audit documentation quality: structure, completeness, links, and code coverage",
            module_path="dev.documentation_auditor",
            entry_point="DocumentationAuditor.audit",
            constructor_params=[],
            params=[
                ToolParam("documentation", "text", "Documentation", True, None, "Documentation text to audit", True),
                ToolParam("code", "text", "Source Code", False, "", "Optional code to check coverage against", True),
            ],
        ))
        self._reg(ToolDefinition(
            id="thinking_roi_deep",
            name="Thinking ROI Deep",
            category="Reasoning",
            description="Deep ROI estimation for extended thinking across 8 task profiles with optimal budget",
            module_path="reasoning.thinking_roi_deep",
            entry_point="ThinkingROIDeep.estimate",
            constructor_params=[],
            params=[
                ToolParam("task_type", "string", "Task Type", False, "general",
                          "code_review | architecture | debugging | math | creative | research | planning | general"),
                ToolParam("thinking_tokens", "integer", "Thinking Tokens", False, 10000, "Token budget to evaluate"),
                ToolParam("model", "string", "Model", False, "claude-sonnet-4-6", "Model to estimate for"),
                ToolParam("error_cost_usd", "float", "Error Cost (USD)", False, 100.0, "Cost of an error in dollars"),
            ],
        ))
        self._reg(ToolDefinition(
            id="parser_adapters",
            name="Format Converter",
            category="Knowledge Graph",
            description="Convert between JSON, CSV, Markdown tables, and YAML with auto-detection",
            module_path="knowledge.parser_adapters",
            entry_point="parse_any",
            params=[
                ToolParam("text", "text", "Input Text", True, None, "Text to convert", True),
                ToolParam("from_format", "string", "From Format", False, "auto", "auto | json | csv | markdown_table | yaml"),
                ToolParam("to_format", "string", "To Format", False, "json", "json | csv | markdown_table | yaml"),
            ],
        ))

        # === Phase 2: NEW Developer Tools (14) ===

        # -- Frontend (3) --
        self._reg(ToolDefinition(
            id="react_component_generator",
            name="Component Generator",
            category="Frontend",
            description="Generate React TSX, Vue SFC, or Svelte components with props, state, and hooks",
            module_path="frontend.react_component_generator",
            entry_point="ReactComponentGenerator.generate",
            constructor_params=[],
            params=[
                ToolParam("name", "string", "Component Name", True, "MyComponent", "PascalCase component name"),
                ToolParam("props", "string", "Props", False, "", "Comma-separated props (name:type)"),
                ToolParam("features", "string", "Features", False, "state", "state,effects,form,list,modal,fetch"),
                ToolParam("framework", "string", "Framework", False, "react", "react | vue | svelte"),
            ],
        ))
        self._reg(ToolDefinition(
            id="jsx_to_tsx_converter",
            name="JSX to TSX Converter",
            category="Frontend",
            description="Convert JSX to TypeScript TSX with inferred prop types and interfaces",
            module_path="frontend.jsx_to_tsx_converter",
            entry_point="JsxToTsxConverter.convert",
            constructor_params=[],
            params=[
                ToolParam("jsx_code", "text", "JSX Code", True, None, "JSX code to convert to TypeScript", True),
                ToolParam("component_name", "string", "Component Name", False, "", "Override component name detection"),
            ],
        ))
        self._reg(ToolDefinition(
            id="css_to_tailwind",
            name="CSS to Tailwind",
            category="Frontend",
            description="Convert CSS property-value pairs to Tailwind utility classes",
            module_path="frontend.css_to_tailwind",
            entry_point="CssToTailwindConverter.convert",
            constructor_params=[],
            params=[
                ToolParam("css", "text", "CSS Code", True, None, "CSS to convert to Tailwind classes", True),
            ],
        ))

        # -- Backend (3) --
        self._reg(ToolDefinition(
            id="fastapi_endpoint_generator",
            name="API Endpoint Generator",
            category="Backend",
            description="Generate FastAPI, Express, Flask, or Django endpoints from descriptions",
            module_path="backend.fastapi_endpoint_generator",
            entry_point="FastAPIEndpointGenerator.generate",
            constructor_params=[],
            params=[
                ToolParam("description", "text", "Endpoint Description", True, None, "Describe what the endpoint does", True),
                ToolParam("method", "string", "HTTP Method", False, "GET", "GET | POST | PUT | DELETE"),
                ToolParam("path", "string", "Path", False, "/api/resource", "API path"),
                ToolParam("framework", "string", "Framework", False, "fastapi", "fastapi | express | flask | django"),
                ToolParam("auth", "boolean", "Require Auth", False, False, "Add authentication middleware"),
            ],
        ))
        self._reg(ToolDefinition(
            id="pydantic_model_generator",
            name="Data Model Generator",
            category="Backend",
            description="Infer Pydantic, TypeScript, Zod, or dataclass models from JSON samples",
            module_path="backend.pydantic_model_generator",
            entry_point="PydanticModelGenerator.generate",
            constructor_params=[],
            params=[
                ToolParam("json_sample", "text", "JSON Sample", True, None,
                          '{"name": "John", "age": 30, "email": "john@example.com", "active": true}', True),
                ToolParam("model_name", "string", "Model Name", False, "MyModel", "Name for generated model"),
                ToolParam("output_format", "string", "Output Format", False, "pydantic", "pydantic | typescript | zod | dataclass"),
            ],
        ))
        self._reg(ToolDefinition(
            id="pytest_generator",
            name="Test Generator",
            category="Backend",
            description="Generate pytest, jest, or vitest tests from function signatures via AST",
            module_path="backend.pytest_generator",
            entry_point="PytestGenerator.generate",
            constructor_params=[],
            params=[
                ToolParam("code", "text", "Source Code", True, None, "Code to generate tests for", True),
                ToolParam("test_framework", "string", "Test Framework", False, "pytest", "pytest | jest | vitest"),
                ToolParam("language", "string", "Language", False, "python", "python | javascript | typescript"),
            ],
        ))

        # -- Full-Stack (3) --
        self._reg(ToolDefinition(
            id="api_contract_generator",
            name="API Contract Generator",
            category="Full-Stack",
            description="Generate OpenAPI specs from natural language descriptions",
            module_path="fullstack.api_contract_generator",
            entry_point="APIContractGenerator.generate",
            constructor_params=[],
            params=[
                ToolParam("description", "text", "API Description", True, None, "Describe the API (CRUD operations, resources)", True),
                ToolParam("base_path", "string", "Base Path", False, "/api", "API base path"),
                ToolParam("title", "string", "API Title", False, "API", "OpenAPI spec title"),
            ],
        ))
        self._reg(ToolDefinition(
            id="dockerfile_generator",
            name="Dockerfile Generator",
            category="Full-Stack",
            description="Generate Dockerfile + docker-compose for Python, Node, React, Go, or Rust stacks",
            module_path="fullstack.dockerfile_generator",
            entry_point="DockerfileGenerator.generate",
            constructor_params=[],
            params=[
                ToolParam("stack", "string", "Stack", False, "python", "python | node | react | go | rust"),
                ToolParam("app_name", "string", "App Name", False, "app", "Application name"),
                ToolParam("services", "string", "Services", False, "", "Comma-separated: postgres,redis,mongo"),
                ToolParam("port", "integer", "Port Override", False, 0, "Override default port (0 = use default)"),
            ],
        ))
        self._reg(ToolDefinition(
            id="env_template_generator",
            name="Env Template Generator",
            category="Full-Stack",
            description="Scan code for env var references and generate .env.example templates",
            module_path="fullstack.env_template_generator",
            entry_point="EnvTemplateGenerator.generate",
            constructor_params=[],
            params=[
                ToolParam("code", "text", "Source Code", True, None, "Code to scan for environment variables", True),
                ToolParam("project_name", "string", "Project Name", False, "project", "Project name for template header"),
            ],
        ))

        # -- Dev Tools additions (5) --
        self._reg(ToolDefinition(
            id="commit_message_generator",
            name="Commit Message Generator",
            category="Dev Tools",
            description="Generate conventional commit messages from change descriptions",
            module_path="dev.commit_message_generator",
            entry_point="CommitMessageGenerator.generate",
            constructor_params=[],
            params=[
                ToolParam("description", "text", "Change Description", True, None, "Describe what changed", True),
                ToolParam("files_changed", "string", "Files Changed", False, "", "Comma-separated file paths"),
                ToolParam("breaking", "boolean", "Breaking Change", False, False, "Is this a breaking change?"),
            ],
        ))
        self._reg(ToolDefinition(
            id="changelog_generator",
            name="Changelog Generator",
            category="Dev Tools",
            description="Generate Keep-a-Changelog formatted changelogs from commit messages",
            module_path="dev.changelog_generator",
            entry_point="ChangelogGenerator.generate",
            constructor_params=[],
            params=[
                ToolParam("commits", "text", "Commits", True, None, "Newline-separated conventional commit messages", True),
                ToolParam("version", "string", "Version", False, "Unreleased", "Version number"),
            ],
        ))
        self._reg(ToolDefinition(
            id="dead_code_detector",
            name="Dead Code Detector",
            category="Dev Tools",
            description="Find unused functions, imports, and variables via AST analysis",
            module_path="dev.dead_code_detector",
            entry_point="DeadCodeDetector.detect",
            constructor_params=[],
            params=[
                ToolParam("code", "text", "Source Code", True, None, "Code to scan for dead code", True),
                ToolParam("language", "string", "Language", False, "python", "python | javascript"),
            ],
        ))
        self._reg(ToolDefinition(
            id="complexity_scorer",
            name="Complexity Scorer",
            category="Dev Tools",
            description="Score cyclomatic + cognitive complexity of Python functions via AST",
            module_path="dev.complexity_scorer",
            entry_point="ComplexityScorer.score",
            constructor_params=[],
            params=[
                ToolParam("code", "text", "Source Code", True, None, "Python code to analyze", True),
                ToolParam("language", "string", "Language", False, "python", "python (more coming)"),
            ],
        ))
        self._reg(ToolDefinition(
            id="security_scanner",
            name="Security Scanner",
            category="Dev Tools",
            description="Scan for SQL injection, XSS, hardcoded secrets, eval, and OWASP patterns",
            module_path="dev.security_scanner",
            entry_point="SecurityScanner.scan",
            constructor_params=[],
            params=[
                ToolParam("code", "text", "Source Code", True, None, "Code to scan for vulnerabilities", True),
                ToolParam("language", "string", "Language", False, "auto", "auto | python | javascript"),
            ],
        ))

        # === Dev Tools (3 — original) ===
        self._reg(ToolDefinition(
            id="production_resilience",
            name="Circuit Breaker Analyzer",
            category="Dev Tools",
            description="Analyze circuit breaker state and recommend recovery strategies",
            module_path="dev.production_resilience",
            entry_point="analyze_circuit_breaker",
            params=[
                ToolParam("recent_errors", "integer", "Recent Errors", True, 5, "Number of errors in observation window"),
                ToolParam("total_requests", "integer", "Total Requests", True, 100, "Total requests in observation window"),
                ToolParam("current_state", "string", "Current State", False, "closed", "closed | open | half_open"),
            ],
        ))
        self._reg(ToolDefinition(
            id="backoff_calculator",
            name="Backoff Calculator",
            category="Dev Tools",
            description="Calculate exponential backoff timing with jitter for retry strategies",
            module_path="dev.production_resilience",
            entry_point="calculate_backoff",
            params=[
                ToolParam("attempt", "integer", "Attempt Number", True, 1, "Current retry attempt (1-based)"),
                ToolParam("base_delay", "float", "Base Delay (sec)", False, 1.0, "Base delay in seconds"),
                ToolParam("max_delay", "float", "Max Delay (sec)", False, 60.0, "Maximum delay cap in seconds"),
            ],
        ))
        self._reg(ToolDefinition(
            id="ml_task_analyzer",
            name="ML Task Analyzer",
            category="Dev Tools",
            description="Analyze ML tasks and recommend approaches, models, and estimate development time",
            module_path="dev.augmented_intelligence_ml",
            entry_point="analyze_ml_task",
            params=[
                ToolParam("task_description", "text", "Task Description", True, None, "Describe the ML task", True),
                ToolParam("data_size", "string", "Data Size", False, "medium", "small | medium | large | very_large"),
                ToolParam("accuracy_requirement", "string", "Accuracy Need", False, "high", "low | medium | high | critical"),
            ],
        ))

    # --- Public API ---

    def list_tools(self) -> dict:
        """Return tools grouped by category."""
        categories: dict[str, list] = {}
        for tool in self._tools.values():
            cat = tool.category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append({
                "id": tool.id,
                "name": tool.name,
                "description": tool.description,
                "is_async": tool.is_async,
                "param_count": len(tool.params),
            })
        return {
            "categories": sorted(categories.keys()),
            "tools": categories,
            "total": len(self._tools),
        }

    def get_tool(self, tool_id: str) -> Optional[dict]:
        """Return full tool definition with param schemas."""
        tool = self._tools.get(tool_id)
        if not tool:
            return None
        return {
            "id": tool.id,
            "name": tool.name,
            "category": tool.category,
            "description": tool.description,
            "is_async": tool.is_async,
            "output_format": tool.output_format,
            "params": [
                {
                    "name": p.name,
                    "type": p.type,
                    "label": p.label,
                    "required": p.required,
                    "default": p.default,
                    "description": p.description,
                    "multiline": p.multiline,
                }
                for p in tool.params
            ],
        }

    async def run_tool(self, tool_id: str, params: dict) -> dict:
        """Import, resolve, execute, and serialize a tool."""
        tool = self._tools.get(tool_id)
        if not tool:
            return {"success": False, "error": f"Unknown tool: {tool_id}"}

        try:
            self._ensure_path()
            result = await asyncio.to_thread(self._execute_sync, tool, params)
            serialized = self._serialize(result)
            return {"success": True, "result": serialized}
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
            }

    # --- Private helpers ---

    def _import_module(self, module_path: str):
        """Import a tool module by dotted path."""
        parts = module_path.split(".")
        if len(parts) == 2:
            subdir, module_name = parts
            module_file = TOOLS_DIR / subdir / f"{module_name}.py"
        else:
            module_file = TOOLS_DIR / f"{module_path.replace('.', '/')}.py"

        spec = importlib.util.spec_from_file_location(module_path, str(module_file))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def _execute_sync(self, tool: ToolDefinition, params: dict):
        """Synchronously import and execute a tool."""
        # Special-case handlers for tools needing dataclass conversion
        if tool.id == "workflow_analyzer":
            return self._run_workflow_analyzer(params)

        mod = self._import_module(tool.module_path)

        entry = tool.entry_point
        if "." in entry:
            # ClassName.method pattern
            class_name, method_name = entry.split(".", 1)
            cls = getattr(mod, class_name)

            # Split params between constructor and method
            ctor_kwargs = {}
            method_kwargs = {}
            for key, val in params.items():
                if key in tool.constructor_params:
                    ctor_kwargs[key] = val
                else:
                    method_kwargs[key] = val

            instance = cls(**ctor_kwargs)
            method = getattr(instance, method_name)
            return method(**method_kwargs)
        else:
            # Plain function
            func = getattr(mod, entry)
            return func(**params)

    def _run_workflow_analyzer(self, params: dict):
        """Special handler: convert step dicts to WorkflowStep dataclasses."""
        mod = self._import_module("reasoning.metacognition_workflows")
        WorkflowStep = getattr(mod, "WorkflowStep")
        WorkflowAnalyzer = getattr(mod, "WorkflowAnalyzer")

        steps_raw = params.get("steps", [])
        steps = []
        for s in steps_raw:
            steps.append(WorkflowStep(
                name=s.get("name", "unnamed"),
                complexity=s.get("complexity", "moderate"),
                category=s.get("category", "implementation"),
                dependencies=s.get("dependencies", []),
                latency_critical=s.get("latency_critical", False),
                estimated_time_hours=s.get("estimated_time_hours", 1.0),
            ))

        analyzer = WorkflowAnalyzer()
        return analyzer.analyze_workflow(
            workflow=steps,
            total_budget=params.get("total_budget", 30000),
        )

    def _serialize(self, obj: Any) -> Any:
        """Recursively serialize dataclasses, enums, and other objects to JSON-safe types."""
        if obj is None:
            return None
        if isinstance(obj, (str, int, float, bool)):
            return obj
        if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
            return {k: self._serialize(v) for k, v in dataclasses.asdict(obj).items()}
        if isinstance(obj, dict):
            return {str(k): self._serialize(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [self._serialize(item) for item in obj]
        if hasattr(obj, 'value'):  # Enum
            return obj.value
        if hasattr(obj, '__dict__'):
            return {k: self._serialize(v) for k, v in vars(obj).items() if not k.startswith('_')}
        return str(obj)


tools_service = ToolsService()

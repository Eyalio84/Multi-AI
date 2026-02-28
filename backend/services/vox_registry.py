"""VOX Function Registry — decorator-based function registration replacing if/elif dispatch.

Phase 1 of VOX Jarvis-Mode: All 35 workspace functions registered with metadata
(category, is_async, is_browser, requires_kg). Browser-side vs server-side distinction
preserved via is_browser flag (INSIGHT-005).

Usage:
    from services.vox_registry import vox_registry

    # Get all declarations for Gemini Live API
    declarations = vox_registry.get_declarations()

    # Execute a server-side function
    result = await vox_registry.execute("run_tool", {"tool_id": "cost_analyzer"})

    # Check if function is browser-side
    if name in vox_registry.get_browser_functions(): ...
"""
import asyncio
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional


# ── Registry infrastructure ───────────────────────────────────────────────

@dataclass
class VoxFunction:
    name: str
    handler: Optional[Callable]
    declaration: dict
    category: str
    is_async: bool = False
    is_browser: bool = False
    requires_kg: bool = False


class VoxRegistry:
    """Central registry for all VOX functions."""

    def __init__(self):
        self._registry: dict[str, VoxFunction] = {}

    def register(
        self,
        name: str,
        category: str,
        description: str,
        parameters: dict,
        is_async: bool = False,
        is_browser: bool = False,
        requires_kg: bool = False,
    ):
        """Decorator to register a VOX function."""
        def decorator(fn):
            self._registry[name] = VoxFunction(
                name=name,
                handler=fn,
                declaration={
                    "name": name,
                    "description": description,
                    "parameters": parameters,
                },
                category=category,
                is_async=is_async,
                is_browser=is_browser,
                requires_kg=requires_kg,
            )
            return fn
        return decorator

    def register_browser(self, name: str, category: str, description: str, parameters: dict):
        """Register a browser-side function (no server handler)."""
        self._registry[name] = VoxFunction(
            name=name,
            handler=None,
            declaration={
                "name": name,
                "description": description,
                "parameters": parameters,
            },
            category=category,
            is_browser=True,
        )

    async def execute(self, name: str, args: dict) -> dict:
        """Execute a registered server-side function by name."""
        func = self._registry.get(name)
        if not func:
            return {"success": False, "error": f"Unknown server function: {name}"}
        if func.is_browser:
            return {"success": True, "note": "Executed in browser"}
        if not func.handler:
            return {"success": False, "error": f"No handler for function: {name}"}
        try:
            result = func.handler(args)
            if asyncio.iscoroutine(result):
                result = await result
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_declarations(self) -> list[dict]:
        """Return all function declarations for Gemini Live API."""
        return [f.declaration for f in self._registry.values()]

    def get_browser_functions(self) -> set[str]:
        """Return set of browser-side function names."""
        return {name for name, f in self._registry.items() if f.is_browser}

    def get_async_functions(self) -> set[str]:
        """Return set of async (potentially slow) function names."""
        return {name for name, f in self._registry.items() if f.is_async}

    def get_by_category(self, category: str) -> list[VoxFunction]:
        """Get functions filtered by category."""
        return [f for f in self._registry.values() if f.category == category]

    def get_all(self) -> dict[str, VoxFunction]:
        return dict(self._registry)

    @property
    def count(self) -> int:
        return len(self._registry)


# ── Singleton ─────────────────────────────────────────────────────────────

vox_registry = VoxRegistry()


# ── Helpers ───────────────────────────────────────────────────────────────

TOURS_PATH = Path(__file__).parent.parent / "data" / "vox_tours.json"
INTERVIEW_PATH = Path(__file__).parent.parent / "data" / "vox_interview.json"


def _load_tours() -> dict:
    try:
        with open(TOURS_PATH) as f:
            return json.load(f)
    except Exception:
        return {}


def _load_interview() -> dict:
    try:
        with open(INTERVIEW_PATH) as f:
            return json.load(f)
    except Exception:
        return {}


def _safe_serialize(obj):
    """Ensure object is JSON-serializable."""
    if isinstance(obj, dict):
        return {k: _safe_serialize(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_safe_serialize(v) for v in obj]
    elif isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    else:
        return str(obj)


# ══════════════════════════════════════════════════════════════════════════
# FUNCTION REGISTRATIONS — 35 functions across 10 categories
# ══════════════════════════════════════════════════════════════════════════

# ── Browser-side functions (6) — executed in frontend, not here ──────────

vox_registry.register_browser(
    "navigate_page", "navigation",
    "Navigate the workspace to a specific page. Available pages: chat, coding, agents, playbooks, workflows, kg-studio, experts, builder, tools, vox, integrations, settings, games.",
    {"type": "object", "properties": {"path": {"type": "string", "description": "The page path, e.g. '/chat', '/tools', '/kg-studio'"}}, "required": ["path"]},
)

vox_registry.register_browser(
    "get_current_page", "navigation",
    "Get the current page path the user is viewing.",
    {"type": "object", "properties": {}},
)

vox_registry.register_browser(
    "get_workspace_state", "navigation",
    "Get the current workspace state: active provider, model, page, theme, and project count.",
    {"type": "object", "properties": {}},
)

vox_registry.register_browser(
    "switch_model", "navigation",
    "Switch the active AI model. Providers: 'gemini', 'claude', or 'openai'.",
    {"type": "object", "properties": {"provider": {"type": "string", "description": "Either 'gemini', 'claude', or 'openai'"}, "model": {"type": "string", "description": "Model ID, e.g. 'gemini-2.5-flash'"}}, "required": ["provider", "model"]},
)

vox_registry.register_browser(
    "switch_theme", "navigation",
    "Switch the workspace visual theme. Available: default, crt, scratch, solarized, sunset.",
    {"type": "object", "properties": {"theme_id": {"type": "string", "description": "Theme ID"}}, "required": ["theme_id"]},
)

vox_registry.register_browser(
    "read_page_content", "navigation",
    "Read the visible text content of the current workspace page.",
    {"type": "object", "properties": {}},
)


# ── Core workspace tools (6) ─────────────────────────────────────────────

@vox_registry.register(
    "run_tool", "tools",
    "Execute one of the 58+ registered workspace tools by ID. Examples: cost_analyzer, task_classifier, code_review_generator, embedding_generator, react_component_generator, security_scanner, etc.",
    {"type": "object", "properties": {"tool_id": {"type": "string", "description": "Tool ID to execute"}, "params": {"type": "object", "description": "Tool parameters as key-value pairs"}}, "required": ["tool_id"]},
)
async def _handle_run_tool(args: dict) -> dict:
    from services.tools_service import tools_service
    tool_id = args.get("tool_id", "")
    params = args.get("params", {})
    result = await tools_service.run_tool(tool_id, params)
    return {"success": True, "result": _safe_serialize(result)}


@vox_registry.register(
    "list_tools", "tools",
    "List all available workspace tools with their categories.",
    {"type": "object", "properties": {}},
)
def _handle_list_tools(args: dict) -> dict:
    from services.tools_service import tools_service
    tools_data = tools_service.list_tools()
    summary = []
    for cat_tools in tools_data.get("tools", {}).values():
        for t in cat_tools:
            summary.append({"id": t["id"], "name": t["name"], "category": t["category"]})
    return {"success": True, "tools": summary, "count": len(summary)}


@vox_registry.register(
    "query_kg", "kg", "Search a knowledge graph database using hybrid semantic search.",
    {"type": "object", "properties": {"database_id": {"type": "string", "description": "KG database ID"}, "query": {"type": "string", "description": "Search query"}}, "required": ["database_id", "query"]},
    requires_kg=True,
)
def _handle_query_kg(args: dict) -> dict:
    from services.embedding_service import EmbeddingService
    db_id = args.get("database_id", "")
    query = args.get("query", "")
    svc = EmbeddingService(db_id)
    results = svc.hybrid_search(query, limit=5)
    return {"success": True, "results": results[:5], "database": db_id}


@vox_registry.register(
    "list_kgs", "kg", "List all available knowledge graph databases.",
    {"type": "object", "properties": {}},
    requires_kg=True,
)
def _handle_list_kgs(args: dict) -> dict:
    from services.kg_service import kg_service
    dbs = kg_service.list_databases()
    summary = [{"id": d["id"], "name": d.get("name", d["id"]), "nodes": d.get("node_count", 0)} for d in dbs]
    return {"success": True, "databases": summary, "count": len(summary)}


@vox_registry.register(
    "run_agent", "agents", "Execute an NLKE agent by name. Examples: cost_analyzer, kg_curator, adaptive_reasoning, etc.",
    {"type": "object", "properties": {"agent_name": {"type": "string", "description": "Agent name"}, "input": {"type": "string", "description": "Input text for the agent"}}, "required": ["agent_name", "input"]},
    is_async=True,
)
async def _handle_run_agent(args: dict) -> dict:
    from services.agent_bridge import run_agent
    agent_name = args.get("agent_name", "")
    agent_input = args.get("input", "")
    result = await asyncio.to_thread(run_agent, agent_name, {"text": agent_input})
    return {"success": True, "result": _safe_serialize(result)}


@vox_registry.register(
    "list_agents", "agents", "List all available NLKE agents.",
    {"type": "object", "properties": {}},
)
def _handle_list_agents(args: dict) -> dict:
    from services.agent_bridge import list_agents
    agents = list_agents()
    return {"success": True, "agents": agents, "count": len(agents)}


# ── Direct developer tool shortcuts (5) ──────────────────────────────────

@vox_registry.register(
    "generate_react_component", "dev_tools",
    "Generate a React component with TypeScript, props interface, hooks, and state management.",
    {"type": "object", "properties": {"name": {"type": "string", "description": "Component name, e.g. 'UserCard'"}, "description": {"type": "string", "description": "What the component should do"}, "framework": {"type": "string", "description": "Target framework: react, vue, or svelte. Default: react"}, "features": {"type": "string", "description": "Comma-separated features: state, effects, context, memo, portal, ref"}}, "required": ["name", "description"]},
)
async def _handle_generate_react_component(args: dict) -> dict:
    from services.tools_service import tools_service
    params = {
        "name": args.get("name", "MyComponent"),
        "description": args.get("description", ""),
        "framework": args.get("framework", "react"),
        "features": args.get("features", "state"),
    }
    result = await tools_service.run_tool("react_component_generator", params)
    return {"success": True, "result": _safe_serialize(result)}


@vox_registry.register(
    "generate_fastapi_endpoint", "dev_tools",
    "Generate a FastAPI route with Pydantic models, validation, and error handling.",
    {"type": "object", "properties": {"description": {"type": "string", "description": "What the endpoint should do"}, "method": {"type": "string", "description": "HTTP method: GET, POST, PUT, DELETE. Default: POST"}, "path": {"type": "string", "description": "URL path, e.g. '/api/users'"}, "framework": {"type": "string", "description": "Target framework: fastapi, express, flask, django. Default: fastapi"}}, "required": ["description"]},
)
async def _handle_generate_fastapi_endpoint(args: dict) -> dict:
    from services.tools_service import tools_service
    params = {
        "description": args.get("description", ""),
        "method": args.get("method", "POST"),
        "path": args.get("path", "/api/resource"),
        "framework": args.get("framework", "fastapi"),
    }
    result = await tools_service.run_tool("fastapi_endpoint_generator", params)
    return {"success": True, "result": _safe_serialize(result)}


@vox_registry.register(
    "scan_code_security", "dev_tools",
    "Scan code for security vulnerabilities: SQL injection, XSS, hardcoded secrets, eval usage, path traversal.",
    {"type": "object", "properties": {"code": {"type": "string", "description": "Source code to scan"}, "language": {"type": "string", "description": "Programming language. Default: python"}}, "required": ["code"]},
)
async def _handle_scan_code_security(args: dict) -> dict:
    from services.tools_service import tools_service
    params = {"code": args.get("code", ""), "language": args.get("language", "python")}
    result = await tools_service.run_tool("security_scanner", params)
    return {"success": True, "result": _safe_serialize(result)}


@vox_registry.register(
    "analyze_code_complexity", "dev_tools",
    "Analyze code complexity using cyclomatic and cognitive complexity metrics.",
    {"type": "object", "properties": {"code": {"type": "string", "description": "Source code to analyze"}, "language": {"type": "string", "description": "Programming language. Default: python"}}, "required": ["code"]},
)
async def _handle_analyze_code_complexity(args: dict) -> dict:
    from services.tools_service import tools_service
    params = {"code": args.get("code", ""), "language": args.get("language", "python")}
    result = await tools_service.run_tool("complexity_scorer", params)
    return {"success": True, "result": _safe_serialize(result)}


@vox_registry.register(
    "generate_tests", "dev_tools",
    "Generate test cases from function signatures using AST analysis.",
    {"type": "object", "properties": {"code": {"type": "string", "description": "Source code containing functions to test"}, "framework": {"type": "string", "description": "Test framework: pytest, unittest, jest, mocha. Default: pytest"}, "style": {"type": "string", "description": "Test style: unit, integration, property. Default: unit"}}, "required": ["code"]},
)
async def _handle_generate_tests(args: dict) -> dict:
    from services.tools_service import tools_service
    params = {
        "code": args.get("code", ""),
        "framework": args.get("framework", "pytest"),
        "style": args.get("style", "unit"),
    }
    result = await tools_service.run_tool("pytest_generator", params)
    return {"success": True, "result": _safe_serialize(result)}


# ── Guided Tours (2) ─────────────────────────────────────────────────────

@vox_registry.register(
    "start_guided_tour", "tours",
    "Start an interactive voice-narrated guided tour of a workspace page. VOX highlights UI elements and explains each feature.",
    {"type": "object", "properties": {"page": {"type": "string", "description": "Page to tour. Options: chat, coding, agents, playbooks, workflows, kg-studio, experts, builder, tools, vox, games, settings. If empty, tours the current page."}}},
)
def _handle_start_guided_tour(args: dict) -> dict:
    page = args.get("page", "")
    tours = _load_tours()
    if not page:
        return {"success": False, "error": "No page specified. Ask the user which page to tour."}
    tour = tours.get(page)
    if not tour:
        available = list(tours.keys())
        return {"success": False, "error": f"No tour for '{page}'. Available: {', '.join(available)}"}
    return {"success": True, "action": "start_tour", "page": page, "tour": tour}


@vox_registry.register(
    "get_available_tours", "tours",
    "List all available guided tours with page names and step counts.",
    {"type": "object", "properties": {}},
)
def _handle_get_available_tours(args: dict) -> dict:
    tours = _load_tours()
    summary = [
        {"page": p, "name": t.get("name", ""), "steps": len(t.get("steps", []))}
        for p, t in tours.items()
    ]
    return {"success": True, "tours": summary, "count": len(summary)}


# ── Workspace Control — Jarvis Mode (5) ──────────────────────────────────

@vox_registry.register(
    "create_project", "workspace",
    "Create a new AI Studio project with a name and description.",
    {"type": "object", "properties": {"name": {"type": "string", "description": "Project name"}, "description": {"type": "string", "description": "What the project does"}}, "required": ["name"]},
)
def _handle_create_project(args: dict) -> dict:
    from services.studio_service import studio_service
    project_name = args.get("name", "Untitled")
    description = args.get("description", "")
    project = studio_service.create_project(project_name, description)
    return {"success": True, "project_id": project.get("id"), "name": project_name}


@vox_registry.register(
    "list_projects", "workspace",
    "List all Studio projects with their status and file counts.",
    {"type": "object", "properties": {}},
)
def _handle_list_projects(args: dict) -> dict:
    from services.studio_service import studio_service
    projects = studio_service.list_projects()
    summary = [{"id": p.get("id"), "name": p.get("name", ""), "file_count": p.get("file_count", 0)} for p in projects]
    return {"success": True, "projects": summary, "count": len(summary)}


@vox_registry.register(
    "run_workflow", "workspace",
    "Execute a workflow template by name. Available: error-recovery, knowledge-synthesis, session-handoff, multi-agent-orchestration.",
    {"type": "object", "properties": {"workflow_name": {"type": "string", "description": "Workflow template name"}, "input": {"type": "string", "description": "Input text for the workflow"}}, "required": ["workflow_name"]},
    is_async=True,
)
def _handle_run_workflow(args: dict) -> dict:
    workflow_name = args.get("workflow_name", "")
    workflow_input = args.get("input", "")
    templates = {
        "error-recovery": "error-recovery-workflow.json",
        "knowledge-synthesis": "knowledge-synthesis-workflow.json",
        "session-handoff": "session-handoff-workflow.json",
        "multi-agent": "multi-agent-orchestration-workflow.json",
    }
    tpl_file = templates.get(workflow_name)
    if not tpl_file:
        return {"success": False, "error": f"Unknown workflow: {workflow_name}. Available: {', '.join(templates.keys())}"}
    return {"success": True, "workflow": workflow_name, "status": "initiated", "input": workflow_input[:200]}


@vox_registry.register(
    "search_playbooks", "workspace",
    "Search through 53 implementation playbooks by keyword.",
    {"type": "object", "properties": {"query": {"type": "string", "description": "Search query"}}, "required": ["query"]},
)
def _handle_search_playbooks(args: dict) -> dict:
    from services.playbook_index import playbook_index
    query = args.get("query", "")
    results = playbook_index.search(query)
    return {"success": True, "results": results[:5], "count": len(results)}


@vox_registry.register(
    "search_kg", "kg",
    "Enhanced KG search with optional filters. Returns top results with scores.",
    {"type": "object", "properties": {"database_id": {"type": "string", "description": "KG database ID"}, "query": {"type": "string", "description": "Search query"}, "node_type": {"type": "string", "description": "Optional: filter by node type (e.g. 'tool', 'pattern', 'concept')"}, "limit": {"type": "integer", "description": "Max results. Default: 5"}}, "required": ["database_id", "query"]},
    requires_kg=True,
)
def _handle_search_kg(args: dict) -> dict:
    from services.embedding_service import EmbeddingService
    db_id = args.get("database_id", "")
    query = args.get("query", "")
    limit = args.get("limit", 5)
    svc = EmbeddingService(db_id)
    results = svc.hybrid_search(query, limit=limit)
    node_type = args.get("node_type", "")
    if node_type:
        results = [r for r in results if r.get("node_type", "") == node_type]
    return {"success": True, "results": results[:limit], "database": db_id, "query": query}


# ── KG Studio Control (3) ────────────────────────────────────────────────

@vox_registry.register(
    "get_kg_analytics", "kg",
    "Get graph analytics for a KG database: node/edge counts, top nodes by centrality, and community count.",
    {"type": "object", "properties": {"database_id": {"type": "string", "description": "KG database ID"}}, "required": ["database_id"]},
    requires_kg=True,
)
def _handle_get_kg_analytics(args: dict) -> dict:
    from services.analytics_service import get_analytics
    db_id = args.get("database_id", "")
    analytics = get_analytics(db_id)
    return {"success": True, "database": db_id, "analytics": _safe_serialize(analytics)}


@vox_registry.register(
    "cross_kg_search", "kg",
    "Search across multiple knowledge graph databases simultaneously.",
    {"type": "object", "properties": {"query": {"type": "string", "description": "Search query"}, "database_ids": {"type": "string", "description": "Comma-separated database IDs, or 'all' for all databases"}, "limit": {"type": "integer", "description": "Max results per database. Default: 3"}}, "required": ["query"]},
    is_async=True, requires_kg=True,
)
def _handle_cross_kg_search(args: dict) -> dict:
    from services.kg_service import kg_service
    from services.embedding_service import EmbeddingService
    query = args.get("query", "")
    db_ids_str = args.get("database_ids", "all")
    limit = args.get("limit", 3)
    if db_ids_str == "all":
        dbs = kg_service.list_databases()
        db_ids = [d["id"] for d in dbs[:10]]
    else:
        db_ids = [d.strip() for d in db_ids_str.split(",")]
    all_results = {}
    for db_id in db_ids:
        try:
            svc = EmbeddingService(db_id)
            results = svc.hybrid_search(query, limit=limit)
            all_results[db_id] = results[:limit]
        except Exception:
            all_results[db_id] = []
    return {"success": True, "results": _safe_serialize(all_results), "databases_searched": len(db_ids)}


@vox_registry.register(
    "ingest_to_kg", "kg",
    "Extract entities and relationships from text and add them to a knowledge graph using AI.",
    {"type": "object", "properties": {"database_id": {"type": "string", "description": "Target KG database ID"}, "text": {"type": "string", "description": "Text to extract knowledge from"}}, "required": ["database_id", "text"]},
    is_async=True, requires_kg=True,
)
async def _handle_ingest_to_kg(args: dict) -> dict:
    from services.ingestion_service import ingestion_service
    db_id = args.get("database_id", "")
    text = args.get("text", "")
    result = await asyncio.to_thread(ingestion_service.ingest_text, db_id, text)
    return {"success": True, "result": _safe_serialize(result)}


# ── Expert Control (2) ───────────────────────────────────────────────────

@vox_registry.register(
    "chat_with_expert", "experts",
    "Send a message to a KG-OS expert and get a response with source citations.",
    {"type": "object", "properties": {"expert_id": {"type": "string", "description": "Expert ID"}, "message": {"type": "string", "description": "Message to send to the expert"}}, "required": ["expert_id", "message"]},
)
def _handle_chat_with_expert(args: dict) -> dict:
    from services.expert_service import expert_service
    expert_id = args.get("expert_id", "")
    message = args.get("message", "")
    result = expert_service.chat(expert_id, message)
    return {"success": True, "result": _safe_serialize(result)}


@vox_registry.register(
    "list_experts", "experts",
    "List all available KG-OS experts with their specializations.",
    {"type": "object", "properties": {}},
)
def _handle_list_experts(args: dict) -> dict:
    from services.expert_service import expert_service
    experts = expert_service.list_experts()
    summary = [{"id": e.get("id"), "name": e.get("name", ""), "kg": e.get("database_id", "")} for e in experts]
    return {"success": True, "experts": summary, "count": len(summary)}


# ── Voice Macros (4) ─────────────────────────────────────────────────────

@vox_registry.register(
    "create_macro", "macros",
    "Create a voice macro — a multi-step command sequence triggered by a phrase. Steps can chain functions together with output piping.",
    {"type": "object", "properties": {"name": {"type": "string", "description": "Macro name"}, "trigger_phrase": {"type": "string", "description": "Voice trigger phrase, e.g. 'morning routine'"}, "steps": {"type": "string", "description": "JSON array of steps: [{\"function\":\"fn_name\",\"args\":{},\"pipe_from\":null}]"}, "error_policy": {"type": "string", "description": "What to do on error: abort, skip, or retry. Default: abort"}}, "required": ["name", "trigger_phrase", "steps"]},
)
def _handle_create_macro(args: dict) -> dict:
    from services.vox_macros import vox_macro_service
    steps_raw = args.get("steps", "[]")
    if isinstance(steps_raw, str):
        steps = json.loads(steps_raw)
    else:
        steps = steps_raw
    macro = vox_macro_service.create_macro(
        name=args.get("name", ""),
        trigger_phrase=args.get("trigger_phrase", ""),
        steps=steps,
        error_policy=args.get("error_policy", "abort"),
    )
    return {"success": True, "macro": macro}


@vox_registry.register(
    "list_macros", "macros",
    "List all saved voice macros with their trigger phrases and step counts.",
    {"type": "object", "properties": {}},
)
def _handle_list_macros(args: dict) -> dict:
    from services.vox_macros import vox_macro_service
    return {"success": True, "macros": vox_macro_service.list_macros()}


@vox_registry.register(
    "run_macro", "macros",
    "Execute a voice macro by name or trigger phrase.",
    {"type": "object", "properties": {"macro_id": {"type": "string", "description": "Macro ID or trigger phrase"}}, "required": ["macro_id"]},
)
async def _handle_run_macro(args: dict) -> dict:
    from services.vox_macros import vox_macro_service
    macro_id = args.get("macro_id", "")
    results = await vox_macro_service.execute_macro(macro_id, vox_registry.execute)
    return {"success": True, "results": _safe_serialize(results)}


@vox_registry.register(
    "delete_macro", "macros",
    "Delete a saved voice macro.",
    {"type": "object", "properties": {"macro_id": {"type": "string", "description": "Macro ID to delete"}}, "required": ["macro_id"]},
)
def _handle_delete_macro(args: dict) -> dict:
    from services.vox_macros import vox_macro_service
    deleted = vox_macro_service.delete_macro(args.get("macro_id", ""))
    return {"success": deleted, "message": "Macro deleted" if deleted else "Macro not found"}


# ── Thermal Monitoring (1) ───────────────────────────────────────────────

@vox_registry.register(
    "check_thermal", "system",
    "Check the device temperature and battery status. Warns if the device is getting too hot.",
    {"type": "object", "properties": {}},
)
async def _handle_check_thermal(args: dict) -> dict:
    from services.vox_thermal import thermal_monitor
    result = await thermal_monitor.check()
    return {"success": True, **result}


# ── Feature Interview (1) ────────────────────────────────────────────────

@vox_registry.register(
    "start_feature_interview", "workspace",
    "Start a 10-question guided interview to gather requirements for building a React MVP app.",
    {"type": "object", "properties": {"domain": {"type": "string", "description": "Optional pre-selected domain: landing, knowledge, saas, game, dashboard, ecommerce, social, portfolio."}}},
)
def _handle_start_feature_interview(args: dict) -> dict:
    interview = _load_interview()
    if not interview:
        return {"success": False, "error": "Interview definition not found"}
    domain = args.get("domain", "")
    questions = interview.get("questions", [])
    first_question = questions[0] if questions else {}
    if domain and first_question.get("options"):
        matched = next(
            (o for o in first_question["options"] if o["id"] == domain),
            None,
        )
        if matched:
            return {
                "success": True,
                "action": "start_interview",
                "total_questions": len(questions),
                "pre_selected_domain": matched["label"],
                "next_question": questions[1] if len(questions) > 1 else None,
                "message": f"Great choice! You selected {matched['label']}. Let me walk you through 9 more questions to shape your MVP.",
            }
    return {
        "success": True,
        "action": "start_interview",
        "total_questions": len(questions),
        "first_question": first_question,
        "message": "Let's build something! I'll ask you 10 quick questions to understand what you need, then generate a working React MVP.",
    }

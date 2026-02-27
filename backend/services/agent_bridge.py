"""Bridge to NLKE agent system — imports AgentRunner and Pipeline from agent SDK.

Falls back to an AI-powered executor (Gemini) when the SDK symlink is unavailable.
"""
import sys
import json
import sqlite3
from pathlib import Path
from typing import Optional

from config import AGENTS_DIR

# Agent catalog — maps name to module info
AGENT_CATALOG = {
    "cost-advisor": {"category": "FOUNDATION", "description": "Optimize API costs with model selection and caching strategies"},
    "context-optimizer": {"category": "FOUNDATION", "description": "Optimize context window usage and prompt compression"},
    "rate-limit-handler": {"category": "FOUNDATION", "description": "Handle API rate limits with retry strategies"},
    "error-recovery": {"category": "FOUNDATION", "description": "Classify errors and find recovery strategies"},
    "prompt-engineer": {"category": "DEV", "description": "Generate and optimize system prompts"},
    "code-reviewer": {"category": "DEV", "description": "Review code for quality, security, and best practices"},
    "test-generator": {"category": "DEV", "description": "Generate test cases from code analysis"},
    "refactor-advisor": {"category": "DEV", "description": "Suggest refactoring improvements"},
    "doc-generator": {"category": "DEV", "description": "Generate documentation from code"},
    "dependency-analyzer": {"category": "DEV", "description": "Analyze project dependencies and suggest updates"},
    "security-auditor": {"category": "DEV", "description": "Security vulnerability scanning and recommendations"},
    "performance-profiler": {"category": "DEV", "description": "Profile code performance and suggest optimizations"},
    "workflow-orchestrator": {"category": "AGENT", "description": "Plan and execute multi-step workflows"},
    "task-decomposer": {"category": "AGENT", "description": "Break complex tasks into subtasks"},
    "multi-model-router": {"category": "AGENT", "description": "Route tasks to optimal AI models"},
    "pipeline-builder": {"category": "AGENT", "description": "Build agent execution pipelines"},
    "kg-builder": {"category": "KNOWLEDGE", "description": "Build knowledge graphs from documents"},
    "entity-extractor": {"category": "KNOWLEDGE", "description": "Extract entities and relationships from text"},
    "embedding-trainer": {"category": "KNOWLEDGE", "description": "Train and evaluate embedding models"},
    "semantic-searcher": {"category": "KNOWLEDGE", "description": "Semantic search across knowledge bases"},
    "fact-validator": {"category": "REASONING", "description": "Validate facts using multi-source verification"},
    "synthesis-engine": {"category": "REASONING", "description": "Synthesize insights from multiple sources"},
    "metacognition-advisor": {"category": "REASONING", "description": "Meta-cognitive analysis of reasoning quality"},
    "insight-logger": {"category": "REASONING", "description": "Log and track emerging insights"},
    "playbook-advisor": {"category": "SPECIALIZED", "description": "Recommend playbooks for goals"},
    "session-handoff": {"category": "SPECIALIZED", "description": "Transfer context between sessions"},
    "learning-path": {"category": "SPECIALIZED", "description": "Generate personalized learning paths"},
    "pattern-detector": {"category": "SPECIALIZED", "description": "Detect patterns across data"},
    "deployment-planner": {"category": "ORCHESTRATION", "description": "Plan production deployments"},
    "monitor-agent": {"category": "ORCHESTRATION", "description": "Monitor system health and performance"},
    "scaling-advisor": {"category": "ORCHESTRATION", "description": "Advise on scaling strategies"},
    "backup-recovery": {"category": "ORCHESTRATION", "description": "Plan backup and disaster recovery"},
    "compliance-checker": {"category": "ORCHESTRATION", "description": "Check compliance with standards"},
}


CUSTOM_AGENTS_DB = Path(__file__).parent.parent / "data" / "agents.db"


def _get_agents_conn() -> sqlite3.Connection:
    """Return a connection to the custom agents database."""
    CUSTOM_AGENTS_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(CUSTOM_AGENTS_DB))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _init_agents_db():
    """Create the custom_agents table if it does not exist."""
    conn = _get_agents_conn()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS custom_agents (
                id            TEXT PRIMARY KEY,
                name          TEXT NOT NULL UNIQUE,
                description   TEXT NOT NULL DEFAULT '',
                category      TEXT NOT NULL DEFAULT 'CUSTOM',
                system_prompt TEXT NOT NULL DEFAULT '',
                tools         TEXT NOT NULL DEFAULT '[]',
                created_at    TEXT NOT NULL
            )
        """)
        conn.commit()
    finally:
        conn.close()


_init_agents_db()


def _load_custom_agents() -> list[dict]:
    """Load all custom agents from SQLite."""
    conn = _get_agents_conn()
    try:
        rows = conn.execute("SELECT * FROM custom_agents ORDER BY created_at DESC").fetchall()
        results = []
        for row in rows:
            d = dict(row)
            if isinstance(d.get("tools"), str):
                try:
                    d["tools"] = json.loads(d["tools"])
                except (json.JSONDecodeError, TypeError):
                    d["tools"] = []
            results.append(d)
        return results
    finally:
        conn.close()


class AgentBridge:
    """Bridge between the web API and NLKE agent system."""

    def __init__(self):
        self._sdk_loaded = False
        self._runner = None
        self._pipeline_cls = None

    def _ensure_sdk(self):
        """Lazy-load the agent SDK."""
        if self._sdk_loaded:
            return
        agents_path = str(AGENTS_DIR)
        if agents_path not in sys.path:
            sys.path.insert(0, agents_path)
        try:
            from shared.agent_sdk import AgentRunner, Pipeline
            self._runner = AgentRunner
            self._pipeline_cls = Pipeline
            self._sdk_loaded = True
        except ImportError:
            # SDK not available — agents will use AI-powered fallback
            self._sdk_loaded = True

    def _run_with_ai(self, name: str, workload: dict) -> dict:
        """AI-powered agent executor using Gemini when the SDK is unavailable."""
        from services import gemini_service

        # Look up agent metadata from catalog or custom agents
        info = AGENT_CATALOG.get(name)
        if info is None:
            custom = self._get_custom_agent(name)
            if custom is None:
                return {"error": f"Unknown agent: {name}", "agent": name}
            system_prompt = custom.get("system_prompt", "")
            description = custom.get("description", "")
            category = custom.get("category", "CUSTOM")
        else:
            description = info["description"]
            category = info["category"]
            system_prompt = ""

        if not system_prompt:
            system_prompt = (
                f"You are the '{name}' agent in the {category} category.\n"
                f"Your role: {description}\n\n"
                "Analyze the user's workload and provide a thorough, actionable response. "
                "Structure your output with clear sections. Be specific and practical."
            )

        workload_text = json.dumps(workload, indent=2) if isinstance(workload, dict) else str(workload)

        try:
            result_text = gemini_service.generate_content(
                prompt=workload_text,
                system_instruction=system_prompt,
            )
            return {
                "agent": name,
                "status": "completed",
                "output": result_text,
                "executor": "ai_fallback",
            }
        except Exception as e:
            return {"agent": name, "status": "error", "error": str(e)}

    def _get_custom_agent(self, name: str) -> dict | None:
        """Look up a custom agent by name."""
        conn = _get_agents_conn()
        try:
            row = conn.execute("SELECT * FROM custom_agents WHERE name = ?", (name,)).fetchone()
            if row is None:
                return None
            d = dict(row)
            if isinstance(d.get("tools"), str):
                try:
                    d["tools"] = json.loads(d["tools"])
                except (json.JSONDecodeError, TypeError):
                    d["tools"] = []
            return d
        finally:
            conn.close()

    def list_agents(self) -> list[dict]:
        """Return all agents (catalog + custom) with metadata."""
        agents = []
        for name, info in AGENT_CATALOG.items():
            agents.append({
                "name": name,
                "category": info["category"],
                "description": info["description"],
                "type": "builtin",
            })

        for custom in _load_custom_agents():
            agents.append({
                "name": custom["name"],
                "category": custom.get("category", "CUSTOM"),
                "description": custom.get("description", ""),
                "type": "custom",
                "system_prompt": custom.get("system_prompt", ""),
                "tools": custom.get("tools", []),
            })

        return agents

    def get_example(self, name: str) -> dict:
        """Get example workload for an agent."""
        if name not in AGENT_CATALOG:
            custom = self._get_custom_agent(name)
            if custom is None:
                raise ValueError(f"Unknown agent: {name}")
            return {
                "goal": f"Example goal for {name}",
                "context": {"description": custom.get("description", "")},
            }

        self._ensure_sdk()
        if self._runner:
            try:
                from shared.agent_analyzer import get_example_input
                return get_example_input(name)
            except Exception:
                pass

        return {
            "goal": f"Example goal for {name}",
            "context": {"project": "my-project", "language": "python"},
        }

    def run_agent(self, name: str, workload: dict) -> dict:
        """Execute an agent with a workload."""
        is_known = name in AGENT_CATALOG or self._get_custom_agent(name) is not None
        if not is_known:
            raise ValueError(f"Unknown agent: {name}")

        self._ensure_sdk()
        if self._runner:
            try:
                result = self._runner.run(name, workload)
                return result.to_dict() if hasattr(result, "to_dict") else {"output": str(result)}
            except Exception as e:
                return {"error": str(e), "agent": name}

        # AI-powered fallback when SDK is unavailable
        return self._run_with_ai(name, workload)

    def run_pipeline(self, steps: list[dict]) -> dict:
        """Execute a multi-agent pipeline."""
        self._ensure_sdk()
        if self._pipeline_cls:
            try:
                pipeline = self._pipeline_cls(steps)
                result = pipeline.run()
                return result.to_dict() if hasattr(result, "to_dict") else {"output": str(result)}
            except Exception as e:
                return {"error": str(e)}

        # Fallback: run agents sequentially
        results = []
        for step in steps:
            agent_name = step.get("agent", step.get("name", ""))
            workload = step.get("workload", {})
            result = self.run_agent(agent_name, workload)
            results.append({"step": agent_name, "result": result})
        return {"pipeline_results": results}

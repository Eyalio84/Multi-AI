"""Bridge to NLKE agent system — imports AgentRunner and Pipeline from agent SDK."""
import sys
import json
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
            # SDK not available — agents will work in metadata-only mode
            self._sdk_loaded = True

    def list_agents(self) -> list[dict]:
        """Return all agent names with metadata."""
        agents = []
        for name, info in AGENT_CATALOG.items():
            agents.append({
                "name": name,
                "category": info["category"],
                "description": info["description"],
            })
        return agents

    def get_example(self, name: str) -> dict:
        """Get example workload for an agent."""
        if name not in AGENT_CATALOG:
            raise ValueError(f"Unknown agent: {name}")

        self._ensure_sdk()
        if self._runner:
            try:
                from shared.agent_analyzer import get_example_input
                return get_example_input(name)
            except Exception:
                pass

        # Fallback example
        return {
            "goal": f"Example goal for {name}",
            "context": {"project": "my-project", "language": "python"},
        }

    def run_agent(self, name: str, workload: dict) -> dict:
        """Execute an agent with a workload."""
        if name not in AGENT_CATALOG:
            raise ValueError(f"Unknown agent: {name}")

        self._ensure_sdk()
        if self._runner:
            try:
                result = self._runner.run(name, workload)
                return result.to_dict() if hasattr(result, "to_dict") else {"output": str(result)}
            except Exception as e:
                return {"error": str(e), "agent": name}

        return {
            "agent": name,
            "status": "sdk_not_available",
            "message": f"Agent SDK not loaded. Ensure agents symlink exists at {AGENTS_DIR}",
            "workload_received": workload,
        }

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

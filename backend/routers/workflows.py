"""Workflow execution engine — plan, template, and execute multi-step workflows."""
import json
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, JSONResponse

from services import gemini_service
from services.model_router import route as route_model

router = APIRouter()

# Built-in workflow templates
WORKFLOW_TEMPLATES = {
    "dev_lifecycle": {
        "name": "Development Lifecycle",
        "description": "Full software development workflow: plan → code → test → review → deploy",
        "steps": [
            {"id": "plan", "name": "Architecture Planning", "model_hint": "reasoning", "prompt_template": "Create a detailed architecture plan for: {goal}"},
            {"id": "code", "name": "Code Generation", "model_hint": "coding", "prompt_template": "Implement the following plan:\n{prev_output}", "depends_on": ["plan"]},
            {"id": "test", "name": "Test Generation", "model_hint": "coding", "prompt_template": "Write comprehensive tests for:\n{prev_output}", "depends_on": ["code"]},
            {"id": "review", "name": "Code Review", "model_hint": "reasoning", "prompt_template": "Review this code for quality, security, and best practices:\n{prev_output}", "depends_on": ["code"]},
            {"id": "docs", "name": "Documentation", "model_hint": "general", "prompt_template": "Generate documentation for:\n{prev_output}", "depends_on": ["code"]},
        ],
    },
    "research_analysis": {
        "name": "Research & Analysis",
        "description": "Research a topic with multi-model cross-validation",
        "steps": [
            {"id": "research", "name": "Initial Research", "model_hint": "reasoning", "prompt_template": "Research comprehensively: {goal}"},
            {"id": "analyze", "name": "Deep Analysis", "model_hint": "reasoning", "prompt_template": "Analyze the key findings:\n{prev_output}", "depends_on": ["research"]},
            {"id": "validate", "name": "Cross-Validate", "model_hint": "reasoning", "prompt_template": "Cross-validate and fact-check:\n{prev_output}", "depends_on": ["analyze"]},
            {"id": "synthesize", "name": "Synthesize Report", "model_hint": "general", "prompt_template": "Synthesize into a final report:\n{prev_output}", "depends_on": ["validate"]},
        ],
    },
    "kg_pipeline": {
        "name": "Knowledge Graph Pipeline",
        "description": "Extract entities, build relationships, and generate a knowledge graph",
        "steps": [
            {"id": "extract", "name": "Entity Extraction", "model_hint": "reasoning", "prompt_template": "Extract all entities and their types from: {goal}"},
            {"id": "relate", "name": "Relationship Mapping", "model_hint": "reasoning", "prompt_template": "Map relationships between entities:\n{prev_output}", "depends_on": ["extract"]},
            {"id": "validate", "name": "Validate Graph", "model_hint": "reasoning", "prompt_template": "Validate the knowledge graph for consistency:\n{prev_output}", "depends_on": ["relate"]},
            {"id": "export", "name": "Export Graph", "model_hint": "coding", "prompt_template": "Generate JSON export of the knowledge graph:\n{prev_output}", "depends_on": ["validate"]},
        ],
    },
    "decision_making": {
        "name": "Decision Framework",
        "description": "Structured decision making with pros/cons and risk analysis",
        "steps": [
            {"id": "options", "name": "Generate Options", "model_hint": "reasoning", "prompt_template": "Generate all viable options for: {goal}"},
            {"id": "proscons", "name": "Pros & Cons Analysis", "model_hint": "reasoning", "prompt_template": "Analyze pros and cons of each option:\n{prev_output}", "depends_on": ["options"]},
            {"id": "risk", "name": "Risk Assessment", "model_hint": "reasoning", "prompt_template": "Assess risks for each option:\n{prev_output}", "depends_on": ["proscons"]},
            {"id": "recommend", "name": "Recommendation", "model_hint": "reasoning", "prompt_template": "Provide a final recommendation with justification:\n{prev_output}", "depends_on": ["risk"]},
        ],
    },
}


@router.get("/workflows/templates")
async def list_templates():
    """Return available workflow templates."""
    templates = []
    for key, tmpl in WORKFLOW_TEMPLATES.items():
        templates.append({
            "id": key,
            "name": tmpl["name"],
            "description": tmpl["description"],
            "step_count": len(tmpl["steps"]),
            "steps": [{"id": s["id"], "name": s["name"]} for s in tmpl["steps"]],
        })
    return {"templates": templates}


@router.post("/workflows/plan")
async def plan_workflow(request: Request):
    """Use AI to plan a custom workflow for a goal."""
    body = await request.json()
    goal = body.get("goal", "")
    template_id = body.get("template")

    if template_id and template_id in WORKFLOW_TEMPLATES:
        template = WORKFLOW_TEMPLATES[template_id]
        steps = []
        for step in template["steps"]:
            model_info = route_model(task_type=step["model_hint"], complexity="medium")
            steps.append({
                **step,
                "provider": model_info["provider"],
                "model": model_info["model"],
                "reason": model_info["reason"],
            })
        return {"goal": goal, "template": template_id, "steps": steps}

    # AI-generated plan
    prompt = f"""Create a workflow plan for this goal: {goal}

Return a JSON array of steps, each with:
- id: short identifier
- name: step name
- prompt_template: what to ask the AI (use {{goal}} and {{prev_output}} placeholders)
- depends_on: array of step IDs this depends on (empty for first step)
- model_hint: "coding", "reasoning", or "general"

Return ONLY valid JSON."""

    try:
        result = gemini_service.generate_content(
            prompt=prompt,
            response_mime_type="application/json",
        )
        steps = json.loads(result)
        for step in steps:
            model_info = route_model(task_type=step.get("model_hint", "general"), complexity="medium")
            step["provider"] = model_info["provider"]
            step["model"] = model_info["model"]
        return {"goal": goal, "steps": steps}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/workflows/execute")
async def execute_workflow(request: Request):
    """Execute a workflow, streaming progress per step."""
    body = await request.json()
    steps = body.get("steps", [])
    goal = body.get("goal", "")

    async def generate():
        step_outputs = {}

        for step in steps:
            step_id = step.get("id", "unknown")
            step_name = step.get("name", step_id)
            yield f"data: {json.dumps({'type': 'step_start', 'step_id': step_id, 'name': step_name})}\n\n"

            # Check dependencies
            depends = step.get("depends_on", [])
            prev_output = ""
            for dep_id in depends:
                if dep_id in step_outputs:
                    prev_output += step_outputs[dep_id] + "\n"

            # Build prompt
            prompt_template = step.get("prompt_template", "Execute: {goal}")
            prompt = prompt_template.replace("{goal}", goal).replace("{prev_output}", prev_output)

            # Execute step
            provider = step.get("provider", "gemini")
            model = step.get("model", "gemini-2.5-flash")

            accumulated = ""
            try:
                messages = [{"author": "user", "parts": [{"text": prompt}]}]
                if provider == "claude":
                    from services import claude_service
                    gen = claude_service.stream_chat(messages=messages, model=model)
                else:
                    gen = gemini_service.stream_chat(messages=messages, model=model)

                async for chunk in gen:
                    if chunk["type"] == "token":
                        accumulated += chunk["content"]
                        yield f"data: {json.dumps({'type': 'step_token', 'step_id': step_id, 'content': chunk['content']})}\n\n"
                    elif chunk["type"] == "done":
                        break

                step_outputs[step_id] = accumulated
                yield f"data: {json.dumps({'type': 'step_complete', 'step_id': step_id})}\n\n"

            except Exception as e:
                yield f"data: {json.dumps({'type': 'step_error', 'step_id': step_id, 'error': str(e)})}\n\n"

        yield f"data: {json.dumps({'type': 'workflow_complete', 'step_count': len(steps)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

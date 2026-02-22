"""Web app builder — plan and generate full projects."""
import json
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from config import MODE
from services import gemini_service, claude_service

router = APIRouter()


@router.post("/builder/plan")
async def generate_plan(request: Request):
    """Generate a structured project plan from an idea."""
    body = await request.json()
    idea = body.get("idea", "")
    provider = body.get("provider", "gemini")
    model = body.get("model")

    prompt = f"""You are an expert web application architect. Based on this idea, create a detailed project plan.

Idea: {idea}

Return a JSON object with:
{{
  "projectName": "kebab-case-name",
  "description": "Brief description",
  "features": ["feature1", "feature2", ...],
  "techStack": {{
    "frontend": "React + TypeScript + Tailwind",
    "backend": "optional",
    "database": "optional"
  }},
  "fileStructure": [
    "src/App.tsx",
    "src/components/Header.tsx",
    ...
  ],
  "pages": ["Home", "About", ...]
}}

Return ONLY valid JSON."""

    try:
        if provider == "claude" and MODE == "standalone":
            target_model = model or "claude-sonnet-4-6"
            # Use Claude for planning
            import anthropic
            client = anthropic.Anthropic(api_key=__import__("config").ANTHROPIC_API_KEY)
            response = client.messages.create(
                model=target_model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text
        else:
            target_model = model or "gemini-2.5-flash"
            text = gemini_service.generate_content(
                prompt=prompt,
                model=target_model,
                response_mime_type="application/json",
            )

        plan = json.loads(text)
        return plan
    except json.JSONDecodeError:
        # Try to extract JSON from response
        import re
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            return json.loads(json_match.group())
        return JSONResponse(status_code=500, content={"message": "Failed to parse plan as JSON"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


@router.post("/builder/generate")
async def generate_code(request: Request):
    """Generate full project code from a plan."""
    body = await request.json()
    plan = body.get("plan", {})
    theme = body.get("theme", {})
    provider = body.get("provider", "gemini")
    model = body.get("model")

    prompt = f"""You are an expert React developer. Generate a complete React + Vite + TypeScript + Tailwind CSS project.

Project Plan:
{json.dumps(plan, indent=2)}

Theme:
- Palette: {theme.get('palette', 'Modern & Minimal')}
- Typography: {theme.get('typography', 'Sans-serif & Friendly')}

Generate ALL files as a JSON object where keys are file paths and values are file contents.
Include: index.html, package.json, vite.config.ts, tsconfig.json, tailwind.config.js, src/App.tsx, src/main.tsx, and all component files.

Return ONLY a valid JSON object mapping file paths to their string contents."""

    try:
        if provider == "claude" and MODE == "standalone":
            target_model = model or "claude-sonnet-4-6"
            import anthropic
            client = anthropic.Anthropic(api_key=__import__("config").ANTHROPIC_API_KEY)
            response = client.messages.create(
                model=target_model,
                max_tokens=16384,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text
        else:
            target_model = model or "gemini-2.5-flash"
            text = gemini_service.generate_content(
                prompt=prompt,
                model=target_model,
                response_mime_type="application/json",
            )

        files = json.loads(text)
        return files
    except json.JSONDecodeError:
        import re
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            return json.loads(json_match.group())
        return JSONResponse(status_code=500, content={"message": "Failed to parse generated code as JSON"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})

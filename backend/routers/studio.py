"""Studio feature — AI-powered React app generation with live preview."""
import json
import re
import io
import zipfile
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, JSONResponse

from config import MODE, ANTHROPIC_API_KEY, OPENAI_API_KEY
from services import gemini_service, claude_service
from services import studio_service
from backend_types.backend_spec import BackendSpec

router = APIRouter()

# ---------------------------------------------------------------------------
# System prompt for React app generation
# ---------------------------------------------------------------------------

GENERATE_SYSTEM_PROMPT = """\
You are a Full-Stack React app generator.

When generating an app:
1. First, briefly describe your plan (2-3 sentences).
2. Then generate each file wrapped in markers:

### FILE: /App.js
import React from 'react';
// ... complete file content
export default App;
### END FILE

### FILE: /components/Header.js
// ... content
### END FILE

Rules:
- Use functional React components with hooks
- Use inline styles (style={{...}}) - NOT CSS classes or Tailwind
- App.js is always the entry point
- All imports should use relative paths starting with ./
- Make the app visually polished with proper spacing, colors, shadows
- Include responsive design via inline style media queries or window.innerWidth checks
- Generate complete, runnable code - no TODOs or placeholders
- IMPORTANT: Do NOT wrap file contents in markdown code fences (```). Write raw code directly after the ### FILE marker line. No ```javascript or ``` delimiters.
- If you need npm packages beyond react/react-dom, list them as:
### DEPS: {"package-name": "^version"}
"""

# ---------------------------------------------------------------------------
# Aesthetic prompt injection — visual config → system prompt sections
# ---------------------------------------------------------------------------

AESTHETIC_PROMPTS = {
    "typography": {
        "editorial": "Use sophisticated editorial typography: serif headings (Georgia, Playfair Display), generous line-height (1.7+), letter-spacing on caps, clear visual hierarchy with 3-4 size levels.",
        "playful": "Use fun, expressive typography: rounded sans-serif (Nunito, Quicksand), bouncy sizes, emoji-friendly, large headings with personality, friendly feel.",
        "minimal": "Use minimal typography: one clean sans-serif (Inter, System UI), tight spacing, small body text (14px), restrained sizing — let whitespace do the work.",
        "bold": "Use bold, high-impact typography: heavy weights (800-900), large display headings (48px+), strong contrast between heading and body, uppercase accents.",
    },
    "theme": {
        "light": "Use a clean light theme: white/near-white backgrounds, dark text, subtle shadows, light borders. Ensure AAA contrast ratios.",
        "dark": "Use a dark theme: dark backgrounds (#0f172a or #111827), light text, glowing accents, subtle borders with transparency. Ensure readability.",
        "colorful": "Use a vibrant, colorful palette: bold primary + complementary accent, colorful gradients, saturated UI elements. NOT pastel — vivid and energetic.",
    },
    "motion": {
        "subtle": "Add subtle micro-interactions: fade-in on mount (300ms), gentle hover scale (1.02), smooth transitions on state changes. Use CSS transitions, not heavy libraries.",
        "rich": "Add rich animations: staggered entrance animations, parallax-like scroll effects, animated gradients, spring physics on interactions. Use CSS keyframes and transitions.",
    },
    "background": {
        "gradient": "Use gradient backgrounds: linear or radial gradients for hero sections, subtle gradient overlays on cards, gradient text for headings.",
        "pattern": "Use subtle background patterns: dot grids, diagonal lines, or geometric shapes using CSS/SVG. Keep them low-opacity to not overwhelm content.",
        "glass": "Use glassmorphism: frosted glass cards with backdrop-filter blur, semi-transparent backgrounds (rgba with 0.1-0.3 alpha), subtle borders.",
    },
    "stateManagement": {
        "zustand": "Use zustand for state management. Create a store with `create()` and use hooks directly in components. Keep state minimal and actions co-located.",
        "redux": "Use Redux Toolkit for state management. Create slices with `createSlice()`, configure store with `configureStore()`. Use `useSelector` and `useDispatch` hooks.",
    },
    "stylingParadigm": {
        "tailwind": "Use Tailwind CSS utility classes for all styling. Use className with Tailwind utilities. Add tailwindcss as a dependency.",
        "css-modules": "Use CSS Modules for scoped styling. Create .module.css files alongside components. Import as `styles` and use `styles.className`.",
        "styled": "Use styled-components for CSS-in-JS styling. Create styled elements with tagged template literals. Add styled-components as a dependency.",
    },
}

ANTI_SLOP_PROMPT = """\
CRITICAL DESIGN DIRECTIVE — Anti-Slop:
- Do NOT use generic Bootstrap/Material UI aesthetics
- Do NOT use bland placeholder colors (#007bff, #6c757d)
- Do NOT use default button styles or generic card layouts
- Create a DISTINCTIVE visual identity: custom color palette, unique spacing rhythm, memorable visual details
- Every design choice should feel intentional, not default
"""

SELF_REFLECTION_PROMPT = """\
After generating the code, mentally evaluate your output against this rubric:
1. Visual Distinctiveness (1-5): Does this look like a custom-designed app or a generic template?
2. Code Quality (1-5): Clean component structure, no unnecessary complexity?
3. Completeness (1-5): All features working, no placeholder TODOs?
4. Responsiveness (1-5): Looks good on mobile and desktop?
If any score is below 3, revise that aspect before outputting.
"""


def _build_aesthetic_system_prompt(base_prompt: str, visual_config: dict | None, provider: str = "gemini") -> str:
    """Inject aesthetic prompt sections based on visual config. Provider-dialect-aware."""
    if not visual_config:
        return base_prompt

    sections = []

    for dimension, value in visual_config.items():
        if dimension in ("antiSlop", "selfReflection"):
            continue
        if value and dimension in AESTHETIC_PROMPTS and value in AESTHETIC_PROMPTS[dimension]:
            sections.append(AESTHETIC_PROMPTS[dimension][value])

    if visual_config.get("antiSlop"):
        sections.append(ANTI_SLOP_PROMPT)

    if visual_config.get("selfReflection"):
        sections.append(SELF_REFLECTION_PROMPT)

    if not sections:
        return base_prompt

    # Format injections based on provider dialect
    if provider == "claude":
        # Claude prefers XML tags
        injection = "\n".join(
            f"<aesthetic_directive>\n{s}\n</aesthetic_directive>" for s in sections
        )
    elif provider == "openai":
        # OpenAI prefers markdown headers
        injection = "\n".join(
            f"### Design Directive\n{s}" for s in sections
        )
    else:
        # Gemini: plain text
        injection = "\n\n".join(sections)

    return f"{base_prompt}\n\n--- Design Configuration ---\n{injection}"


REFINE_SYSTEM_PROMPT = """\
You are a Full-Stack React app refiner. The user has an existing React app and wants changes.

Existing files are provided below. When refining:
1. Briefly describe what you will change (1-2 sentences).
2. Only output the files that changed, using the same marker format:

### FILE: /path/to/file.js
// complete updated content
### END FILE

Rules:
- Use functional React components with hooks
- Use inline styles (style={{...}}) - NOT CSS classes or Tailwind
- Maintain consistency with existing code style
- Generate complete file contents, not diffs
- IMPORTANT: Do NOT wrap file contents in markdown code fences (```). Write raw code directly after the ### FILE marker line. No ```javascript or ``` delimiters.
- If you need new npm packages, list them as:
### DEPS: {"package-name": "^version"}
"""


# ---------------------------------------------------------------------------
# Helpers: parse streaming tokens for file markers
# ---------------------------------------------------------------------------

def _build_user_prompt(prompt: str, files: dict | None, mode: str) -> str:
    """Build the user prompt including existing files for refine mode."""
    parts = []
    if mode == "refine" and files:
        parts.append("Here are the current project files:\n")
        for path, content in files.items():
            parts.append(f"### FILE: {path}\n{content}\n### END FILE\n")
        parts.append("\n---\n")
    parts.append(f"User request: {prompt}")
    return "\n".join(parts)


def _parse_file_markers(text: str):
    """Extract file blocks and deps from accumulated text.

    Returns (plan_text, files_dict, deps_dict, remainder).
    - plan_text: text before the first ### FILE marker
    - files_dict: {path: content}
    - deps_dict: {package: version}
    - remainder: any trailing text after last ### END FILE that may be
      an incomplete new block (to carry forward in streaming)
    """
    files = {}
    deps = {}

    # Extract deps
    for m in re.finditer(r'### DEPS:\s*(\{[^}]+\})', text):
        try:
            deps.update(json.loads(m.group(1)))
        except json.JSONDecodeError:
            pass

    # Split on file markers
    file_pattern = re.compile(
        r'### FILE:\s*(/[^\n]+)\n(.*?)### END FILE',
        re.DOTALL,
    )

    plan_text = text
    first_file_pos = None
    for m in file_pattern.finditer(text):
        if first_file_pos is None:
            first_file_pos = m.start()
        path = m.group(1).strip()
        content = m.group(2).rstrip("\n")
        # Strip markdown code fences that AI models sometimes wrap content in
        content = re.sub(r'^```[\w]*\n?', '', content)
        content = re.sub(r'\n?```\s*$', '', content)
        files[path] = content

    if first_file_pos is not None:
        plan_text = text[:first_file_pos].strip()

    # Check for incomplete trailing block
    remainder = ""
    last_end = 0
    for m in file_pattern.finditer(text):
        last_end = m.end()
    if last_end > 0:
        trailing = text[last_end:]
        if "### FILE:" in trailing:
            remainder = trailing

    return plan_text, files, deps, remainder


# ---------------------------------------------------------------------------
# POST /studio/stream — Main AI streaming endpoint
# ---------------------------------------------------------------------------

@router.post("/studio/stream")
async def studio_stream(request: Request):
    """Stream AI-generated React app files via SSE."""
    body = await request.json()
    project_id = body.get("project_id")
    prompt = body.get("prompt", "")
    files = body.get("files")  # existing files dict for refine mode
    chat_history = body.get("chat_history", [])
    provider = body.get("provider", "gemini")
    model = body.get("model")
    mode = body.get("mode", "generate")  # "generate" or "refine"
    visual_config = body.get("visual_config")  # aesthetic prompt injection config

    base_prompt = REFINE_SYSTEM_PROMPT if mode == "refine" else GENERATE_SYSTEM_PROMPT
    system_prompt = _build_aesthetic_system_prompt(base_prompt, visual_config, provider)
    user_prompt = _build_user_prompt(prompt, files, mode)

    # Build messages list for the AI
    messages = []
    for msg in chat_history[-10:]:  # keep last 10 for context window
        author = msg.get("author", msg.get("role", "user"))
        text = msg.get("text", "")
        if not text and "parts" in msg:
            text = " ".join(p.get("text", "") for p in msg["parts"])
        if text:
            messages.append({
                "author": author,
                "parts": [{"text": text}],
            })
    # Append current user message
    messages.append({
        "author": "user",
        "parts": [{"text": user_prompt}],
    })

    async def generate():
        accumulated = ""
        emitted_files = set()
        emitted_deps = {}
        plan_emitted = False

        try:
            # Choose provider
            if provider == "claude" and MODE == "standalone" and ANTHROPIC_API_KEY:
                target_model = model or "claude-sonnet-4-6"
                stream = claude_service.stream_chat(
                    messages=messages,
                    model=target_model,
                    system=system_prompt,
                    max_tokens=16384,
                    temperature=0.7,
                )
            elif provider == "openai" and MODE == "standalone" and OPENAI_API_KEY:
                from services import openai_service
                target_model = model or "gpt-5-mini"
                stream = openai_service.stream_chat(
                    messages=messages,
                    model=target_model,
                    system=system_prompt,
                    max_tokens=16384,
                    temperature=0.7,
                )
            else:
                target_model = model or "gemini-2.5-flash"
                stream = gemini_service.stream_chat(
                    messages=messages,
                    model=target_model,
                    system_instruction=system_prompt,
                    temperature=0.7,
                )

            async for chunk in stream:
                if chunk.get("type") == "token":
                    token_text = chunk["content"]
                    accumulated += token_text

                    # Emit raw token for chat display
                    yield f"data: {json.dumps({'type': 'token', 'content': token_text})}\n\n"

                    # Parse accumulated text for completed file blocks
                    plan_text, parsed_files, parsed_deps, _ = _parse_file_markers(accumulated)

                    # Emit plan (text before first file marker)
                    if not plan_emitted and plan_text and parsed_files:
                        yield f"data: {json.dumps({'type': 'studio_plan', 'content': plan_text})}\n\n"
                        plan_emitted = True

                    # Emit newly completed files
                    for path, content in parsed_files.items():
                        if path not in emitted_files:
                            emitted_files.add(path)
                            yield f"data: {json.dumps({'type': 'studio_file', 'path': path, 'content': content})}\n\n"

                    # Emit new deps
                    for pkg, ver in parsed_deps.items():
                        if pkg not in emitted_deps:
                            emitted_deps[pkg] = ver
                            yield f"data: {json.dumps({'type': 'studio_deps', 'dependencies': {pkg: ver}})}\n\n"

                elif chunk.get("type") == "done":
                    # Final parse pass — catch any remaining blocks
                    plan_text, parsed_files, parsed_deps, _ = _parse_file_markers(accumulated)

                    if not plan_emitted and plan_text:
                        yield f"data: {json.dumps({'type': 'studio_plan', 'content': plan_text})}\n\n"

                    for path, content in parsed_files.items():
                        if path not in emitted_files:
                            emitted_files.add(path)
                            yield f"data: {json.dumps({'type': 'studio_file', 'path': path, 'content': content})}\n\n"

                    for pkg, ver in parsed_deps.items():
                        if pkg not in emitted_deps:
                            emitted_deps[pkg] = ver
                            yield f"data: {json.dumps({'type': 'studio_deps', 'dependencies': {pkg: ver}})}\n\n"

                    # Auto-save files to project if we have a project_id
                    if project_id and parsed_files:
                        try:
                            project = studio_service.get_project(project_id)
                            if project:
                                existing_files = project.get("files") or {}
                                if isinstance(existing_files, str):
                                    existing_files = json.loads(existing_files)
                                existing_files.update(parsed_files)
                                studio_service.update_project(project_id, {
                                    "files": existing_files,
                                })
                        except Exception:
                            pass  # Non-critical: don't break the stream

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ---------------------------------------------------------------------------
# Multi-Model Orchestration Pipeline
# ---------------------------------------------------------------------------

# Model pricing estimates (per 1M tokens input) for cost tracking
_MODEL_COST_PER_1M = {
    "gemini-2.5-flash": 0.15, "gemini-3-pro-preview": 1.25, "gemini-3.1-pro-preview": 1.25,
    "gemini-3-flash-preview": 0.15, "gemini-2.5-pro": 1.25,
    "claude-sonnet-4-6": 3.0, "claude-opus-4-6": 15.0, "claude-haiku-4-5-20251001": 0.8,
    "gpt-5-mini": 0.40, "gpt-5": 2.0, "gpt-5.1": 2.0, "gpt-5.2": 2.0, "o3": 2.0, "o4-mini": 1.1,
}


async def _get_provider_stream(provider: str, model: str, messages: list, system: str):
    """Route to the correct provider's streaming function."""
    if provider == "claude" and ANTHROPIC_API_KEY:
        return claude_service.stream_chat(
            messages=messages, model=model or "claude-sonnet-4-6",
            system=system, max_tokens=16384, temperature=0.7,
        )
    elif provider == "openai" and OPENAI_API_KEY:
        from services import openai_service
        return openai_service.stream_chat(
            messages=messages, model=model or "gpt-5-mini",
            system=system, max_tokens=16384, temperature=0.7,
        )
    else:
        return gemini_service.stream_chat(
            messages=messages, model=model or "gemini-2.5-flash",
            system_instruction=system, temperature=0.7,
        )


async def _collect_full_response(provider: str, model: str, messages: list, system: str) -> str:
    """Collect full non-streaming response from a provider (for internal pipeline stages)."""
    stream = await _get_provider_stream(provider, model, messages, system)
    accumulated = ""
    async for chunk in stream:
        if chunk.get("type") == "token":
            accumulated += chunk["content"]
        elif chunk.get("type") == "done":
            break
    return accumulated


def _normalize_model_output(text: str) -> str:
    """Strip provider-specific wrappers between pipeline stages."""
    # Claude artifact XML tags
    text = re.sub(r'<artifact[^>]*>', '', text)
    text = text.replace('</artifact>', '')
    # Remove markdown code fences wrapping entire output
    text = re.sub(r'^```[\w]*\n', '', text)
    text = re.sub(r'\n```\s*$', '', text)
    return text.strip()


def _estimate_cost(model: str, tokens: int) -> float:
    """Estimate USD cost for tokens used."""
    rate = _MODEL_COST_PER_1M.get(model, 1.0)
    return round((tokens / 1_000_000) * rate, 6)


def _extract_image_needs(code: str, limit: int = 5) -> list[dict]:
    """Scan generated code for placeholder images that could be replaced with AI-generated ones."""
    needs = []
    seen = set()

    # Match via.placeholder.com URLs (including query string)
    for m in re.finditer(r'(https?://via\.placeholder\.com/\d+[x\d]*(?:\?[^\s\'")]*)?)', code):
        url = m.group(1)
        if url not in seen and len(needs) < limit:
            seen.add(url)
            # Try to extract text hint from ?text= param
            text_match = re.search(r'[?&]text=([^&\s\'"]+)', url)
            hint = text_match.group(1).replace('+', ' ') if text_match else "website image"
            needs.append({"placeholder": url, "prompt": hint, "type": "placeholder"})

    # Match alt texts containing common asset keywords
    for m in re.finditer(r'alt=["\']([^"\']*(?:logo|hero|banner|icon|avatar|brand)[^"\']*)["\']', code, re.IGNORECASE):
        alt = m.group(1).strip()
        if alt and alt not in seen and len(needs) < limit:
            seen.add(alt)
            # Find the corresponding src to use as placeholder reference
            # Look backwards from the alt for an src attribute
            pos = m.start()
            src_match = re.search(r'src=["\']([^"\']+)["\']', code[max(0, pos - 200):pos + 200])
            placeholder = src_match.group(1) if src_match else f"ALT:{alt}"
            needs.append({"placeholder": placeholder, "prompt": alt, "type": "alt_text"})

    return needs


async def _generate_images_for_code(image_needs: list[dict], image_stage: dict | None):
    """Generate images for extracted needs. Yields studio_image SSE events."""
    if not image_needs:
        return

    provider = (image_stage or {}).get("provider", "gemini")

    for need in image_needs:
        try:
            prompt = f"Professional website asset: {need['prompt']}. Clean, modern, high quality, suitable for a web application."

            if provider == "gemini":
                img_data = gemini_service.generate_image(
                    prompt=prompt,
                    model="imagen-4.0-generate-preview-05-20",
                )
                if img_data and img_data.get("image_url"):
                    yield f"data: {json.dumps({'type': 'studio_image', 'imageUrl': img_data['image_url'], 'originalPlaceholder': need['placeholder'], 'prompt': need['prompt']})}\n\n"
            elif provider == "openai" and OPENAI_API_KEY:
                from services import openai_service
                img_list = await openai_service.generate_image(prompt=prompt)
                if img_list and len(img_list) > 0:
                    img_url = img_list[0].get("url") or img_list[0].get("b64_json", "")
                    if img_url:
                        yield f"data: {json.dumps({'type': 'studio_image', 'imageUrl': img_url, 'originalPlaceholder': need['placeholder'], 'prompt': need['prompt']})}\n\n"
        except Exception as e:
            # Image generation failure is non-critical
            yield f"data: {json.dumps({'type': 'orchestration_ping', 'message': f'Image generation skipped: {str(e)[:80]}'})}\n\n"


@router.post("/studio/orchestrate")
async def studio_orchestrate(request: Request):
    """Multi-model orchestration pipeline with 5 strategies."""
    body = await request.json()
    project_id = body.get("project_id")
    prompt = body.get("prompt", "")
    files = body.get("files")
    chat_history = body.get("chat_history", [])
    mode = body.get("mode", "generate")
    pipeline_config = body.get("pipeline_config", {})

    strategy = pipeline_config.get("strategy", "single")
    stages = pipeline_config.get("stages", [])
    visual_config = pipeline_config.get("visual_config")

    base_system = REFINE_SYSTEM_PROMPT if mode == "refine" else GENERATE_SYSTEM_PROMPT
    user_prompt = _build_user_prompt(prompt, files, mode)

    # Build messages list
    messages = []
    for msg in chat_history[-10:]:
        author = msg.get("author", msg.get("role", "user"))
        text = msg.get("text", msg.get("content", ""))
        if text:
            messages.append({"author": author, "parts": [{"text": text}]})
    messages.append({"author": "user", "parts": [{"text": user_prompt}]})

    async def orchestrate():
        import time
        import asyncio

        total_tokens = 0
        total_cost = 0.0

        try:
            if strategy == "advisor_builder" and len(stages) >= 2:
                # ── Advisor + Builder ─────────────────────────────
                advisor = stages[0]
                builder = stages[1]

                # Stage 1: Advisor enriches the spec
                yield f"data: {json.dumps({'type': 'orchestration_stage', 'stage': 1, 'role': 'advisor', 'provider': advisor['provider'], 'model': advisor['model'], 'status': 'started'})}\n\n"

                advisor_system = (
                    "You are an expert application architect and UX advisor. "
                    "Analyze the user's request and produce an enriched specification that includes: "
                    "1. Component architecture (what components, their responsibilities) "
                    "2. Data model (state shape, props flow) "
                    "3. UX recommendations (layout, interactions, edge cases) "
                    "4. Technical requirements (APIs, libraries) "
                    "Be specific and actionable. Your output will be used as input for a code generator."
                )
                advisor_system = _build_aesthetic_system_prompt(advisor_system, visual_config, advisor["provider"])

                start = time.time()
                advisor_response = await _collect_full_response(
                    advisor["provider"], advisor["model"], messages, advisor_system,
                )
                duration = int((time.time() - start) * 1000)
                est_tokens = len(advisor_response.split()) * 2
                total_tokens += est_tokens

                yield f"data: {json.dumps({'type': 'advisor_suggestion', 'content': advisor_response})}\n\n"
                yield f"data: {json.dumps({'type': 'orchestration_stage', 'stage': 1, 'role': 'advisor', 'provider': advisor['provider'], 'model': advisor['model'], 'status': 'completed', 'tokens_used': est_tokens, 'duration_ms': duration})}\n\n"

                # Stage 2: Builder generates code using advisor's enriched spec
                yield f"data: {json.dumps({'type': 'orchestration_stage', 'stage': 2, 'role': 'builder', 'provider': builder['provider'], 'model': builder['model'], 'status': 'started'})}\n\n"

                builder_system = _build_aesthetic_system_prompt(base_system, visual_config, builder["provider"])
                enriched_messages = messages.copy()
                enriched_messages.insert(-1, {
                    "author": "model",
                    "parts": [{"text": f"Architecture advisor notes:\n{advisor_response}"}],
                })

                # Stream the builder output
                async for event in _run_single_stage(builder, enriched_messages, builder_system, project_id, files):
                    yield event

                yield f"data: {json.dumps({'type': 'orchestration_stage', 'stage': 2, 'role': 'builder', 'provider': builder['provider'], 'model': builder['model'], 'status': 'completed'})}\n\n"

            elif strategy == "builder_critic" and len(stages) >= 2:
                # ── Builder + Critic ──────────────────────────────
                builder = stages[0]
                critic = stages[1]

                # Stage 1: Builder generates
                yield f"data: {json.dumps({'type': 'orchestration_stage', 'stage': 1, 'role': 'builder', 'provider': builder['provider'], 'model': builder['model'], 'status': 'started'})}\n\n"

                builder_system = _build_aesthetic_system_prompt(base_system, visual_config, builder["provider"])
                start = time.time()
                builder_response = await _collect_full_response(
                    builder["provider"], builder["model"], messages, builder_system,
                )
                duration = int((time.time() - start) * 1000)
                builder_response = _normalize_model_output(builder_response)

                yield f"data: {json.dumps({'type': 'orchestration_stage', 'stage': 1, 'role': 'builder', 'provider': builder['provider'], 'model': builder['model'], 'status': 'completed', 'duration_ms': duration})}\n\n"

                # Keep-alive ping during critic stage
                yield f"data: {json.dumps({'type': 'orchestration_ping', 'message': 'Stage 2: Critic reviewing...'})}\n\n"

                # Stage 2: Critic reviews
                yield f"data: {json.dumps({'type': 'orchestration_stage', 'stage': 2, 'role': 'critic', 'provider': critic['provider'], 'model': critic['model'], 'status': 'started'})}\n\n"

                critic_system = (
                    "You are an expert code reviewer. Review the generated React app code and provide: "
                    "1. A list of specific improvements (bugs, UX issues, code quality) "
                    "2. Rate overall quality 1-5 "
                    "3. If quality >= 4, say 'APPROVED' at the end "
                    "Be concise and actionable."
                )
                critic_messages = [
                    {"author": "user", "parts": [{"text": f"Review this generated app:\n\n{builder_response}"}]},
                ]
                start = time.time()
                critic_response = await _collect_full_response(
                    critic["provider"], critic["model"], critic_messages, critic_system,
                )
                duration = int((time.time() - start) * 1000)

                yield f"data: {json.dumps({'type': 'critic_feedback', 'content': critic_response})}\n\n"
                yield f"data: {json.dumps({'type': 'orchestration_stage', 'stage': 2, 'role': 'critic', 'provider': critic['provider'], 'model': critic['model'], 'status': 'completed', 'duration_ms': duration})}\n\n"

                # Stage 3: Builder refines based on critic feedback (if not approved)
                if "APPROVED" not in critic_response.upper():
                    yield f"data: {json.dumps({'type': 'orchestration_ping', 'message': 'Stage 3: Refining based on feedback...'})}\n\n"
                    yield f"data: {json.dumps({'type': 'orchestration_stage', 'stage': 3, 'role': 'builder', 'provider': builder['provider'], 'model': builder['model'], 'status': 'started'})}\n\n"

                    refine_messages = messages.copy()
                    refine_messages.append({
                        "author": "model",
                        "parts": [{"text": builder_response}],
                    })
                    refine_messages.append({
                        "author": "user",
                        "parts": [{"text": f"Code review feedback — please fix these issues:\n{critic_response}"}],
                    })

                    async for event in _run_single_stage(builder, refine_messages, builder_system, project_id, files):
                        yield event

                    yield f"data: {json.dumps({'type': 'orchestration_stage', 'stage': 3, 'role': 'builder', 'provider': builder['provider'], 'model': builder['model'], 'status': 'completed'})}\n\n"
                else:
                    # Critic approved — stream builder's original output
                    async for event in _stream_accumulated_text(builder_response, project_id, files):
                        yield event

            elif strategy == "ping_pong" and len(stages) >= 2:
                # ── Ping Pong (3 iterations) ──────────────────────
                model_a = stages[0]
                model_b = stages[1]
                current_code = ""
                max_iterations = 3

                for iteration in range(max_iterations):
                    current_model = model_a if iteration % 2 == 0 else model_b
                    stage_num = iteration + 1

                    yield f"data: {json.dumps({'type': 'orchestration_stage', 'stage': stage_num, 'role': 'builder', 'provider': current_model['provider'], 'model': current_model['model'], 'status': 'started'})}\n\n"
                    ping_msg = f"Iteration {stage_num}/{max_iterations}: {current_model['provider']} refining..."
                    yield f"data: {json.dumps({'type': 'orchestration_ping', 'message': ping_msg})}\n\n"

                    iter_system = _build_aesthetic_system_prompt(base_system, visual_config, current_model["provider"])
                    # In later iterations, inject "accept prior decisions" directive
                    if iteration > 0:
                        iter_system += (
                            "\n\nIMPORTANT: Accept the prior architectural decisions (component structure, naming, patterns). "
                            "Focus ONLY on improving quality, fixing bugs, and enhancing the design. "
                            "Do NOT restructure or rewrite from scratch."
                        )

                    iter_messages = messages.copy()
                    if current_code:
                        iter_messages.append({
                            "author": "model",
                            "parts": [{"text": current_code}],
                        })
                        iter_messages.append({
                            "author": "user",
                            "parts": [{"text": "Improve this code. Fix any issues and enhance the quality. Keep the same architecture."}],
                        })

                    start = time.time()
                    response = await _collect_full_response(
                        current_model["provider"], current_model["model"], iter_messages, iter_system,
                    )
                    duration = int((time.time() - start) * 1000)
                    current_code = _normalize_model_output(response)

                    yield f"data: {json.dumps({'type': 'orchestration_stage', 'stage': stage_num, 'role': 'builder', 'provider': current_model['provider'], 'model': current_model['model'], 'status': 'completed', 'duration_ms': duration})}\n\n"

                # Stream final result
                async for event in _stream_accumulated_text(current_code, project_id, files):
                    yield event

            elif strategy == "chain" and len(stages) >= 2:
                # ── Chain (sequential stages) ─────────────────────
                accumulated_context = ""
                for i, stage in enumerate(stages):
                    stage_num = i + 1
                    yield f"data: {json.dumps({'type': 'orchestration_stage', 'stage': stage_num, 'role': stage['role'], 'provider': stage['provider'], 'model': stage['model'], 'status': 'started'})}\n\n"
                    chain_ping = f"Stage {stage_num}/{len(stages)}: {stage['role']} ({stage['provider']})..."
                    yield f"data: {json.dumps({'type': 'orchestration_ping', 'message': chain_ping})}\n\n"

                    if stage["role"] == "advisor":
                        advisor_system = (
                            "You are an expert architect. Produce an enriched spec with component architecture, "
                            "data model, and UX recommendations."
                        )
                        advisor_system = _build_aesthetic_system_prompt(advisor_system, visual_config, stage["provider"])
                        start = time.time()
                        accumulated_context = await _collect_full_response(
                            stage["provider"], stage["model"], messages, advisor_system,
                        )
                        duration = int((time.time() - start) * 1000)
                        yield f"data: {json.dumps({'type': 'advisor_suggestion', 'content': accumulated_context})}\n\n"

                    elif stage["role"] == "builder":
                        builder_system = _build_aesthetic_system_prompt(base_system, visual_config, stage["provider"])
                        build_messages = messages.copy()
                        if accumulated_context:
                            build_messages.insert(-1, {
                                "author": "model",
                                "parts": [{"text": f"Prior analysis:\n{accumulated_context}"}],
                            })

                        if i == len(stages) - 1 or (i < len(stages) - 1 and stages[i + 1]["role"] != "critic"):
                            # Last builder stage or no critic after — stream output
                            async for event in _run_single_stage(stage, build_messages, builder_system, project_id, files):
                                yield event
                        else:
                            # Builder before critic — collect full response
                            start = time.time()
                            accumulated_context = await _collect_full_response(
                                stage["provider"], stage["model"], build_messages, builder_system,
                            )
                            duration = int((time.time() - start) * 1000)
                            accumulated_context = _normalize_model_output(accumulated_context)

                    elif stage["role"] == "critic":
                        critic_system = (
                            "You are an expert code reviewer. Provide specific improvements. "
                            "If quality is good, say 'APPROVED'."
                        )
                        critic_messages = [
                            {"author": "user", "parts": [{"text": f"Review:\n{accumulated_context}"}]},
                        ]
                        start = time.time()
                        critic_response = await _collect_full_response(
                            stage["provider"], stage["model"], critic_messages, critic_system,
                        )
                        duration = int((time.time() - start) * 1000)
                        yield f"data: {json.dumps({'type': 'critic_feedback', 'content': critic_response})}\n\n"

                        # If not approved and there's a builder after, feed critic notes back
                        if "APPROVED" not in critic_response.upper():
                            accumulated_context += f"\n\nCritic feedback:\n{critic_response}"

                    yield f"data: {json.dumps({'type': 'orchestration_stage', 'stage': stage_num, 'role': stage['role'], 'provider': stage['provider'], 'model': stage['model'], 'status': 'completed'})}\n\n"

            else:
                # ── Single (fallback) ─────────────────────────────
                single_provider = stages[0]["provider"] if stages else "gemini"
                single_model = stages[0]["model"] if stages else "gemini-2.5-flash"
                system = _build_aesthetic_system_prompt(base_system, visual_config, single_provider)

                stage_info = {"provider": single_provider, "model": single_model}
                async for event in _run_single_stage(stage_info, messages, system, project_id, files):
                    yield event

            # ── Image Pipeline: scan generated files for placeholder images ──
            image_stage = next((s for s in stages if s.get("role") == "image"), None)
            if image_stage or any(s.get("role") == "builder" for s in stages):
                # Get current project files to scan for placeholders
                try:
                    if project_id:
                        proj = studio_service.get_project(project_id)
                        proj_files = proj.get("files") or {} if proj else {}
                        if isinstance(proj_files, str):
                            proj_files = json.loads(proj_files)
                        all_code = "\n".join(
                            (f["content"] if isinstance(f, dict) else f) for f in proj_files.values()
                        )
                        image_needs = _extract_image_needs(all_code)
                        if image_needs:
                            yield f"data: {json.dumps({'type': 'orchestration_stage', 'stage': 99, 'role': 'image', 'provider': (image_stage or {}).get('provider', 'gemini'), 'model': 'imagen-4', 'status': 'started'})}\n\n"
                            async for img_event in _generate_images_for_code(image_needs, image_stage):
                                yield img_event
                            yield f"data: {json.dumps({'type': 'orchestration_stage', 'stage': 99, 'role': 'image', 'provider': (image_stage or {}).get('provider', 'gemini'), 'model': 'imagen-4', 'status': 'completed'})}\n\n"
                except Exception:
                    pass  # Image pipeline failure is non-critical

            # Emit cost estimate
            yield f"data: {json.dumps({'type': 'orchestration_cost', 'estimated_usd': round(total_cost, 4)})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(orchestrate(), media_type="text/event-stream")


async def _run_single_stage(stage: dict, messages: list, system: str, project_id: str | None, existing_files: dict | None):
    """Run a single builder stage, streaming tokens and file events. Yields SSE strings."""
    provider = stage.get("provider", "gemini")
    model = stage.get("model", "gemini-2.5-flash")

    stream = await _get_provider_stream(provider, model, messages, system)
    accumulated = ""
    emitted_files = set()
    emitted_deps = {}
    plan_emitted = False

    async for chunk in stream:
        if chunk.get("type") == "token":
            token_text = chunk["content"]
            accumulated += token_text
            yield f"data: {json.dumps({'type': 'token', 'content': token_text})}\n\n"

            plan_text, parsed_files, parsed_deps, _ = _parse_file_markers(accumulated)

            if not plan_emitted and plan_text and parsed_files:
                yield f"data: {json.dumps({'type': 'studio_plan', 'content': plan_text})}\n\n"
                plan_emitted = True

            for path, content in parsed_files.items():
                if path not in emitted_files:
                    emitted_files.add(path)
                    yield f"data: {json.dumps({'type': 'studio_file', 'path': path, 'content': content})}\n\n"

            for pkg, ver in parsed_deps.items():
                if pkg not in emitted_deps:
                    emitted_deps[pkg] = ver
                    yield f"data: {json.dumps({'type': 'studio_deps', 'dependencies': {pkg: ver}})}\n\n"

        elif chunk.get("type") == "done":
            plan_text, parsed_files, parsed_deps, _ = _parse_file_markers(accumulated)

            if not plan_emitted and plan_text:
                yield f"data: {json.dumps({'type': 'studio_plan', 'content': plan_text})}\n\n"

            for path, content in parsed_files.items():
                if path not in emitted_files:
                    emitted_files.add(path)
                    yield f"data: {json.dumps({'type': 'studio_file', 'path': path, 'content': content})}\n\n"

            for pkg, ver in parsed_deps.items():
                if pkg not in emitted_deps:
                    emitted_deps[pkg] = ver
                    yield f"data: {json.dumps({'type': 'studio_deps', 'dependencies': {pkg: ver}})}\n\n"

            # Auto-save
            if project_id and parsed_files:
                try:
                    project = studio_service.get_project(project_id)
                    if project:
                        ef = project.get("files") or {}
                        if isinstance(ef, str):
                            ef = json.loads(ef)
                        ef.update(parsed_files)
                        studio_service.update_project(project_id, {"files": ef})
                except Exception:
                    pass


async def _stream_accumulated_text(text: str, project_id: str | None, existing_files: dict | None):
    """Stream pre-accumulated text as if it were being generated — emit tokens and parse file blocks."""
    plan_text, parsed_files, parsed_deps, _ = _parse_file_markers(text)

    if plan_text:
        yield f"data: {json.dumps({'type': 'studio_plan', 'content': plan_text})}\n\n"

    # Emit the full text as a single token (for chat display)
    yield f"data: {json.dumps({'type': 'token', 'content': text})}\n\n"

    for path, content in parsed_files.items():
        yield f"data: {json.dumps({'type': 'studio_file', 'path': path, 'content': content})}\n\n"

    for pkg, ver in parsed_deps.items():
        yield f"data: {json.dumps({'type': 'studio_deps', 'dependencies': {pkg: ver}})}\n\n"

    # Auto-save
    if project_id and parsed_files:
        try:
            project = studio_service.get_project(project_id)
            if project:
                ef = project.get("files") or {}
                if isinstance(ef, str):
                    ef = json.loads(ef)
                ef.update(parsed_files)
                studio_service.update_project(project_id, {"files": ef})
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Project CRUD
# ---------------------------------------------------------------------------

@router.post("/studio/projects")
async def create_project(request: Request):
    """Create a new Studio project."""
    body = await request.json()
    name = body.get("name", "Untitled Project")
    description = body.get("description", "")
    try:
        project = studio_service.create_project(name, description)
        return project
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


@router.get("/studio/projects")
async def list_projects():
    """List all Studio projects (summaries)."""
    try:
        projects = studio_service.list_projects()
        return projects
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


@router.get("/studio/projects/{project_id}")
async def get_project(project_id: str):
    """Load a full project with files, chat, and versions."""
    try:
        project = studio_service.get_project(project_id)
        if not project:
            return JSONResponse(status_code=404, content={"message": "Project not found"})
        # _row_to_dict already parses JSON columns — only parse if still a string
        for key in ("files", "chat_history", "settings"):
            val = project.get(key)
            if isinstance(val, str):
                try:
                    project[key] = json.loads(val)
                except (json.JSONDecodeError, TypeError):
                    project[key] = {} if key != "chat_history" else []
        project["versions"] = studio_service.list_versions(project_id)
        return project
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


@router.put("/studio/projects/{project_id}")
async def update_project(project_id: str, request: Request):
    """Update project fields."""
    body = await request.json()
    try:
        # Serialize dicts to JSON strings for storage
        data = {}
        for key in ("name", "description"):
            if key in body:
                data[key] = body[key]
        for key in ("files", "chat_history", "settings"):
            if key in body:
                data[key] = json.dumps(body[key]) if isinstance(body[key], (dict, list)) else body[key]
        studio_service.update_project(project_id, data)
        return {"status": "ok"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


@router.delete("/studio/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project and all its versions."""
    try:
        studio_service.delete_project(project_id)
        return {"status": "deleted"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


# ---------------------------------------------------------------------------
# Version management
# ---------------------------------------------------------------------------

@router.post("/studio/projects/{project_id}/save")
async def save_version(project_id: str, request: Request):
    """Save a version snapshot of the current project files."""
    body = await request.json()
    message = body.get("message", "Manual save")
    try:
        version = studio_service.save_version(project_id, message)
        return version
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


@router.get("/studio/projects/{project_id}/versions")
async def list_versions(project_id: str):
    """List all versions for a project."""
    try:
        versions = studio_service.list_versions(project_id)
        return versions
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


@router.get("/studio/projects/{project_id}/versions/{version_number}")
async def get_version(project_id: str, version_number: int):
    """Get a specific version snapshot."""
    try:
        version = studio_service.get_version(project_id, version_number)
        if not version:
            return JSONResponse(status_code=404, content={"message": "Version not found"})
        if isinstance(version.get("files"), str):
            try:
                version["files"] = json.loads(version["files"])
            except (json.JSONDecodeError, TypeError):
                version["files"] = {}
        return version
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


@router.post("/studio/projects/{project_id}/versions/{version_number}/restore")
async def restore_version(project_id: str, version_number: int):
    """Restore a project to a specific version."""
    try:
        project = studio_service.restore_version(project_id, version_number)
        # Ensure JSON columns are parsed for the frontend
        for key in ("files", "settings", "chat_history"):
            val = project.get(key)
            if isinstance(val, str):
                try:
                    project[key] = json.loads(val)
                except (json.JSONDecodeError, TypeError):
                    project[key] = {} if key != "chat_history" else []
        return project
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


# ---------------------------------------------------------------------------
# Mock server management (wired to mock_server_manager)
# ---------------------------------------------------------------------------

@router.post("/studio/projects/{project_id}/mock/start")
async def start_mock(project_id: str):
    """Start a Node.js mock server for the project's API spec."""
    from services.mock_server_manager import start_mock_server
    try:
        from services.openapi_extractor import extract_openapi_from_code
        project = studio_service.get_project(project_id)
        files = json.loads(project.get("files", "{}")) if isinstance(project.get("files"), str) else project.get("files", {})
        # Combine all Python/TS files for extraction
        code_files = {p: f for p, f in files.items() if p.endswith(('.py', '.ts', '.js'))}
        combined = "\n\n".join(f"# {p}\n{c}" for p, c in code_files.items())
        spec = extract_openapi_from_code(combined) if combined.strip() else {"paths": {}}
        return start_mock_server(project_id, spec)
    except ImportError:
        return {"running": False, "error": "OpenAPI extractor not available"}
    except Exception as e:
        return {"running": False, "error": str(e)}


@router.post("/studio/projects/{project_id}/mock/stop")
async def stop_mock(project_id: str):
    """Stop the mock server for a project."""
    from services.mock_server_manager import stop_mock_server
    return stop_mock_server(project_id)


@router.get("/studio/projects/{project_id}/mock/status")
async def mock_status(project_id: str):
    """Get mock server status."""
    from services.mock_server_manager import get_mock_status
    return get_mock_status(project_id)


@router.post("/studio/projects/{project_id}/mock/update")
async def update_mock(project_id: str):
    """Restart mock server with updated routes."""
    from services.mock_server_manager import update_mock_server
    try:
        from services.openapi_extractor import extract_openapi_from_code
        project = studio_service.get_project(project_id)
        files = json.loads(project.get("files", "{}")) if isinstance(project.get("files"), str) else project.get("files", {})
        code_files = {p: f for p, f in files.items() if p.endswith(('.py', '.ts', '.js'))}
        combined = "\n\n".join(f"# {p}\n{c}" for p, c in code_files.items())
        spec = extract_openapi_from_code(combined) if combined.strip() else {"paths": {}}
        return update_mock_server(project_id, spec)
    except ImportError:
        return {"running": False, "error": "OpenAPI extractor not available"}
    except Exception as e:
        return {"running": False, "error": str(e)}


# ---------------------------------------------------------------------------
# Backend spec extraction & builder
# ---------------------------------------------------------------------------

EXTRACT_SPEC_SYSTEM_PROMPT = """\
You are a backend architecture analyzer. Analyze the provided project files and \
chat history, then extract a structured backend specification as JSON.

Return ONLY valid JSON with this exact structure (no markdown fences, no extra text):
{
  "version": "1.0",
  "framework": "fastapi",
  "language": "python",
  "database": {
    "type": "sqlite",
    "tables": [
      {
        "name": "table_name",
        "columns": [
          {"name": "id", "type": "TEXT", "primary_key": true, "unique": true, "nullable": false, "default": null},
          {"name": "title", "type": "TEXT", "primary_key": false, "unique": false, "nullable": false, "default": null}
        ],
        "indexes": ["idx_table_title"]
      }
    ]
  },
  "endpoints": [
    {"method": "GET", "path": "/api/items", "summary": "List all items", "request_body": null, "response": {"type": "array", "items": "Item"}, "auth_required": false},
    {"method": "POST", "path": "/api/items", "summary": "Create item", "request_body": {"title": "string", "done": "boolean"}, "response": {"type": "object", "model": "Item"}, "auth_required": false}
  ],
  "models": {
    "Item": {"name": "Item", "fields": {"id": "str", "title": "str", "done": "bool"}}
  },
  "dependencies": ["fastapi", "uvicorn", "sqlite3"],
  "environment_variables": ["DATABASE_URL"]
}

Infer the database schema, endpoints, and models from the code. If no backend files \
exist, infer what backend would be needed from the frontend code and chat context. \
Omit the database field if no persistence is needed. Always return valid JSON.
"""

BUILD_BACKEND_SYSTEM_PROMPT = """\
You are a backend code generator. Given a backend specification, generate complete \
Python backend files using FastAPI.

Generate each file wrapped in markers:

### FILE: /main.py
from fastapi import FastAPI
# ... complete file content
### END FILE

### FILE: /models.py
# ... content
### END FILE

Rules:
- Use FastAPI with proper type hints and Pydantic models
- Use SQLite via sqlite3 for persistence (unless spec says otherwise)
- Include proper error handling with HTTPException
- Generate complete, runnable code - no TODOs or placeholders
- Include requirements.txt with all dependencies
- IMPORTANT: Do NOT wrap file contents in markdown code fences
- If the spec includes database tables, generate migration/init code
- Follow the endpoint definitions exactly as specified
"""


@router.post("/studio/projects/{project_id}/extract-backend-spec")
async def extract_backend_spec(project_id: str, request: Request):
    """Use AI to analyze project files and extract structured backend specification."""
    body = await request.json()
    provider = body.get("provider", "gemini")
    model = body.get("model")

    project = studio_service.get_project(project_id)
    if not project:
        return JSONResponse(status_code=404, content={"message": "Project not found"})

    files = project.get("files") or {}
    if isinstance(files, str):
        files = json.loads(files)

    chat_history = project.get("chat_history") or []
    if isinstance(chat_history, str):
        chat_history = json.loads(chat_history)

    # Build the analysis prompt with file contents and chat context
    parts = ["Project files:\n"]
    for path, content in files.items():
        file_content = content["content"] if isinstance(content, dict) else content
        parts.append(f"### FILE: {path}\n{file_content}\n### END FILE\n")

    if chat_history:
        parts.append("\nRecent chat context:\n")
        for msg in chat_history[-10:]:
            author = msg.get("author", msg.get("role", "user"))
            text = msg.get("text", "")
            if not text and "parts" in msg:
                text = " ".join(p.get("text", "") for p in msg["parts"])
            if text:
                parts.append(f"[{author}]: {text}\n")

    parts.append("\nExtract the backend specification as JSON.")
    user_prompt = "\n".join(parts)

    try:
        raw_response = gemini_service.generate_content(
            prompt=user_prompt,
            model=model or "gemini-2.5-flash",
            system_instruction=EXTRACT_SPEC_SYSTEM_PROMPT,
            response_mime_type="application/json",
        )

        # Parse and validate through the Pydantic model
        spec_data = json.loads(raw_response)
        spec = BackendSpec(**spec_data)
        return spec.model_dump()
    except json.JSONDecodeError:
        # If AI returned non-JSON, try to extract JSON from the response
        json_match = re.search(r'\{[\s\S]*\}', raw_response)
        if json_match:
            spec_data = json.loads(json_match.group())
            spec = BackendSpec(**spec_data)
            return spec.model_dump()
        return JSONResponse(
            status_code=422,
            content={"message": "AI did not return valid JSON", "raw": raw_response[:500]},
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


@router.post("/studio/projects/{project_id}/build-backend")
async def build_backend(project_id: str, request: Request):
    """Generate backend implementation from specification. Returns SSE stream of files."""
    body = await request.json()
    spec_data = body.get("spec")
    prompt = body.get("prompt", "")
    provider = body.get("provider", "gemini")
    model = body.get("model")

    project = studio_service.get_project(project_id)
    if not project:
        return JSONResponse(status_code=404, content={"message": "Project not found"})

    # If no spec provided, extract one first
    if not spec_data:
        files = project.get("files") or {}
        if isinstance(files, str):
            files = json.loads(files)

        file_parts = ["Project files:\n"]
        for path, content in files.items():
            file_content = content["content"] if isinstance(content, dict) else content
            file_parts.append(f"### FILE: {path}\n{file_content}\n### END FILE\n")
        file_parts.append("\nExtract the backend specification as JSON.")

        raw_spec = gemini_service.generate_content(
            prompt="\n".join(file_parts),
            model=model or "gemini-2.5-flash",
            system_instruction=EXTRACT_SPEC_SYSTEM_PROMPT,
            response_mime_type="application/json",
        )
        try:
            spec_data = json.loads(raw_spec)
        except json.JSONDecodeError:
            json_match = re.search(r'\{[\s\S]*\}', raw_spec)
            if json_match:
                spec_data = json.loads(json_match.group())
            else:
                spec_data = {}

    # Build the generation prompt from the spec
    user_parts = [f"Backend specification:\n```json\n{json.dumps(spec_data, indent=2)}\n```\n"]
    if prompt:
        user_parts.append(f"Additional instructions: {prompt}\n")
    user_parts.append("Generate the complete backend implementation files.")
    user_prompt = "\n".join(user_parts)

    messages = [{"author": "user", "parts": [{"text": user_prompt}]}]

    async def generate():
        accumulated = ""
        emitted_files = set()
        emitted_deps = {}
        plan_emitted = False

        try:
            if provider == "claude" and MODE == "standalone" and ANTHROPIC_API_KEY:
                target_model = model or "claude-sonnet-4-6"
                stream = claude_service.stream_chat(
                    messages=messages,
                    model=target_model,
                    system=BUILD_BACKEND_SYSTEM_PROMPT,
                    max_tokens=16384,
                    temperature=0.7,
                )
            elif provider == "openai" and MODE == "standalone" and OPENAI_API_KEY:
                from services import openai_service
                target_model = model or "gpt-5-mini"
                stream = openai_service.stream_chat(
                    messages=messages,
                    model=target_model,
                    system=BUILD_BACKEND_SYSTEM_PROMPT,
                    max_tokens=16384,
                    temperature=0.7,
                )
            else:
                target_model = model or "gemini-2.5-flash"
                stream = gemini_service.stream_chat(
                    messages=messages,
                    model=target_model,
                    system_instruction=BUILD_BACKEND_SYSTEM_PROMPT,
                    temperature=0.7,
                )

            async for chunk in stream:
                if chunk.get("type") == "token":
                    token_text = chunk["content"]
                    accumulated += token_text

                    yield f"data: {json.dumps({'type': 'token', 'content': token_text})}\n\n"

                    plan_text, parsed_files, parsed_deps, _ = _parse_file_markers(accumulated)

                    if not plan_emitted and plan_text and parsed_files:
                        yield f"data: {json.dumps({'type': 'studio_plan', 'content': plan_text})}\n\n"
                        plan_emitted = True

                    for path, content in parsed_files.items():
                        if path not in emitted_files:
                            emitted_files.add(path)
                            yield f"data: {json.dumps({'type': 'studio_file', 'path': path, 'content': content})}\n\n"

                    for pkg, ver in parsed_deps.items():
                        if pkg not in emitted_deps:
                            emitted_deps[pkg] = ver
                            yield f"data: {json.dumps({'type': 'studio_deps', 'dependencies': {pkg: ver}})}\n\n"

                elif chunk.get("type") == "done":
                    plan_text, parsed_files, parsed_deps, _ = _parse_file_markers(accumulated)

                    if not plan_emitted and plan_text:
                        yield f"data: {json.dumps({'type': 'studio_plan', 'content': plan_text})}\n\n"

                    for path, content in parsed_files.items():
                        if path not in emitted_files:
                            emitted_files.add(path)
                            yield f"data: {json.dumps({'type': 'studio_file', 'path': path, 'content': content})}\n\n"

                    for pkg, ver in parsed_deps.items():
                        if pkg not in emitted_deps:
                            emitted_deps[pkg] = ver
                            yield f"data: {json.dumps({'type': 'studio_deps', 'dependencies': {pkg: ver}})}\n\n"

                    # Auto-save generated backend files to the project
                    if parsed_files:
                        try:
                            existing_files = project.get("files") or {}
                            if isinstance(existing_files, str):
                                existing_files = json.loads(existing_files)
                            existing_files.update(parsed_files)
                            studio_service.update_project(project_id, {"files": existing_files})
                        except Exception:
                            pass

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ---------------------------------------------------------------------------
# OpenAPI spec & TypeScript types (stubs calling extractors)
# ---------------------------------------------------------------------------

@router.get("/studio/projects/{project_id}/api-spec")
async def get_api_spec(project_id: str):
    """Extract OpenAPI spec from project's Python/FastAPI files."""
    try:
        project = studio_service.get_project(project_id)
        if not project:
            return JSONResponse(status_code=404, content={"message": "Project not found"})

        files = json.loads(project.get("files") or "{}")

        # Look for Python files that might contain FastAPI routes
        from services.openapi_extractor import extract_openapi_from_code
        combined_spec = {
            "openapi": "3.0.0",
            "info": {"title": "Generated API", "version": "1.0.0"},
            "paths": {},
            "components": {"schemas": {}},
        }
        for path, content in files.items():
            if path.endswith(".py"):
                spec = extract_openapi_from_code(content)
                combined_spec["paths"].update(spec.get("paths", {}))
                combined_spec["components"]["schemas"].update(
                    spec.get("components", {}).get("schemas", {})
                )
        return combined_spec
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


@router.get("/studio/projects/{project_id}/types")
async def get_ts_types(project_id: str):
    """Generate TypeScript interfaces from project's API spec."""
    try:
        project = studio_service.get_project(project_id)
        if not project:
            return JSONResponse(status_code=404, content={"message": "Project not found"})

        files = json.loads(project.get("files") or "{}")

        from services.openapi_extractor import extract_openapi_from_code
        from services.type_generator import generate_typescript_types

        combined_spec = {
            "openapi": "3.0.0",
            "info": {"title": "Generated API", "version": "1.0.0"},
            "paths": {},
            "components": {"schemas": {}},
        }
        for path, content in files.items():
            if path.endswith(".py"):
                spec = extract_openapi_from_code(content)
                combined_spec["components"]["schemas"].update(
                    spec.get("components", {}).get("schemas", {})
                )

        ts_code = generate_typescript_types(combined_spec)
        return {"types": ts_code}
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


# ---------------------------------------------------------------------------
# Export as ZIP
# ---------------------------------------------------------------------------

@router.get("/studio/projects/{project_id}/export")
async def export_project(project_id: str, request: Request):
    """Export project files as a downloadable ZIP archive."""
    scope = request.query_params.get("scope", "all")  # "all", "frontend", "backend"
    try:
        zip_bytes = studio_service.export_project_zip(project_id, scope)
        if zip_bytes is None:
            return JSONResponse(status_code=404, content={"message": "Project not found"})

        project = studio_service.get_project(project_id)
        name = project.get("name", "project").replace(" ", "-").lower()

        return StreamingResponse(
            io.BytesIO(zip_bytes),
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{name}.zip"',
            },
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})

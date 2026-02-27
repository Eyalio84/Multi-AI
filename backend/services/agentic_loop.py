"""Unified agentic loop — single pipeline replacing 4 fragmented streaming paths."""
import json
import logging
from typing import AsyncGenerator, Optional

from config import MODE, DEFAULT_GEMINI_MODEL, DEFAULT_CLAUDE_MODEL, DEFAULT_OPENAI_MODEL

logger = logging.getLogger(__name__)


class AgenticLoop:
    """8-stage pipeline: intake → memory → skills → context → infer → tools → stream → persist."""

    async def run(
        self,
        messages: list[dict],
        conversation_id: str | None = None,
        mode: str = "chat",
        provider: str = "gemini",
        model: str | None = None,
        system_prompt: str | None = None,
        persona: dict | None = None,
        custom_styles: list[dict] | None = None,
        tools: list[dict] | None = None,
        tools_claude: list[dict] | None = None,
        use_web_search: bool = False,
        thinking_budget: int = 0,
        kg_db_id: str | None = None,
        rag_query: str | None = None,
        rag_history: list[dict] | None = None,
        rag_limit: int = 10,
        source_platform: str | None = None,
        inject_skills: bool = True,
        use_llm_extraction: bool = False,
    ) -> AsyncGenerator[dict, None]:
        """
        Unified streaming pipeline.

        Modes: chat, coding, studio, rag, messaging
        Yields SSE-compatible dicts: {type, content, ...}
        """
        from services.memory_service import memory_service

        # ── Stage 1: INTAKE ──────────────────────────────────────────
        if model:
            target_model = model
        elif provider == "claude":
            target_model = DEFAULT_CLAUDE_MODEL
        elif provider == "openai":
            target_model = DEFAULT_OPENAI_MODEL
        else:
            target_model = DEFAULT_GEMINI_MODEL

        # Create or resume conversation
        if not conversation_id:
            conversation_id = memory_service.create_conversation(
                mode=mode, source=source_platform or "web"
            )

        # Emit conversation_id as first event
        yield {"type": "conversation_start", "conversation_id": conversation_id}

        # Extract user text from last message
        user_text = self._extract_user_text(messages)

        # Log user message
        if user_text:
            memory_service.log_message(
                conversation_id, "user", user_text, provider, target_model
            )

        # ── Stage 2: MEMORY RECALL ───────────────────────────────────
        memory_section = ""
        if user_text and mode != "rag":  # RAG has its own context
            try:
                memories = memory_service.recall(user_text, limit=5)
                memory_section = memory_service.format_memories_for_prompt(memories)
            except Exception as e:
                logger.debug(f"Memory recall failed: {e}")

        # ── Stage 3: SKILL INJECTION ─────────────────────────────────
        skill_section = ""
        if inject_skills and user_text and mode in ("chat", "coding", "messaging"):
            try:
                from services.skill_injector import skill_injector
                skill_section = await skill_injector.get_relevant_context(user_text, mode)
            except Exception as e:
                logger.debug(f"Skill injection failed: {e}")

        # ── Stage 4: CONTEXT ASSEMBLY ────────────────────────────────
        assembled_prompt = self._assemble_context(
            base_prompt=system_prompt,
            persona=persona,
            custom_styles=custom_styles,
            memory_section=memory_section,
            skill_section=skill_section,
            mode=mode,
        )

        # Emit metadata about injections (frontend can show indicators)
        injection_meta = {}
        if memory_section:
            injection_meta["memories"] = True
        if skill_section:
            injection_meta["skills"] = True
        if injection_meta:
            yield {"type": "injection_meta", **injection_meta}

        # ── Stage 5-7: MODEL INFERENCE + TOOL EXECUTION + STREAM ─────
        if mode == "rag" and kg_db_id:
            # RAG mode: delegate to rag_chat_service
            async for chunk in self._run_rag(
                kg_db_id, rag_query or user_text, rag_history or [], rag_limit
            ):
                yield chunk
            # Persist assistant reply handled below
            return

        # Check for Spotify/Calendar tool injection
        active_tools = tools
        active_tools_claude = tools_claude
        if mode in ("chat", "messaging"):
            extra_gemini, extra_claude = self._get_integration_tools()
            if extra_gemini:
                active_tools = (active_tools or []) + extra_gemini
                active_tools_claude = (active_tools_claude or []) + extra_claude

        accumulated_text = ""
        try:
            if provider == "claude":
                async for chunk in self._stream_claude(
                    messages, target_model, assembled_prompt,
                    active_tools_claude, thinking_budget
                ):
                    if chunk.get("type") == "token":
                        accumulated_text += chunk.get("content", "")
                    yield chunk
            elif provider == "openai":
                async for chunk in self._stream_openai(
                    messages, target_model, assembled_prompt,
                    active_tools
                ):
                    if chunk.get("type") == "token":
                        accumulated_text += chunk.get("content", "")
                    yield chunk
            else:
                async for chunk in self._stream_gemini(
                    messages, target_model, assembled_prompt,
                    active_tools, use_web_search
                ):
                    if chunk.get("type") == "token":
                        accumulated_text += chunk.get("content", "")
                    yield chunk
        except Exception as e:
            yield {"type": "error", "content": str(e)}
            yield {"type": "done"}
            return

        # ── Stage 8: PERSIST ─────────────────────────────────────────
        if accumulated_text:
            memory_service.log_message(
                conversation_id, "assistant", accumulated_text, provider, target_model
            )
            # Extract memories in background (don't block stream)
            if user_text:
                try:
                    memory_service.extract_and_store(
                        conversation_id, user_text, accumulated_text, use_llm=use_llm_extraction
                    )
                except Exception as e:
                    logger.debug(f"Memory extraction failed: {e}")

    # ── Private helpers ──────────────────────────────────────────────

    def _extract_user_text(self, messages: list[dict]) -> str:
        """Extract text content from the last user message."""
        for msg in reversed(messages):
            if msg.get("author") == "user" or msg.get("role") == "user":
                # Standard format: parts[].text
                for part in msg.get("parts", []):
                    if part.get("text"):
                        return part["text"]
                # RAG/simple format: content string
                if msg.get("content"):
                    return msg["content"]
        return ""

    def _assemble_context(
        self,
        base_prompt: str | None,
        persona: dict | None,
        custom_styles: list[dict] | None,
        memory_section: str,
        skill_section: str,
        mode: str,
    ) -> str | None:
        parts = []

        # Base system prompt (if provided)
        if base_prompt:
            parts.append(base_prompt)

        # Persona + styles
        if persona:
            if persona.get("baseInstructions"):
                parts.append(persona["baseInstructions"])
            for style in persona.get("composedStyles", []):
                style_name = style.get("name", "")
                weight = style.get("weight", 1)
                if custom_styles:
                    matched = next((s for s in custom_styles if s["name"] == style_name), None)
                    if matched:
                        parts.append(f"[Style: {style_name}, Weight: {weight}]\n{matched['instructions']}")

        # Memory injection
        if memory_section:
            parts.append(memory_section)

        # Skill injection
        if skill_section:
            parts.append(skill_section)

        return "\n\n".join(parts) if parts else None

    async def _stream_gemini(
        self,
        messages: list[dict],
        model: str,
        system_prompt: str | None,
        tools: list[dict] | None,
        use_web_search: bool,
    ) -> AsyncGenerator[dict, None]:
        from services import gemini_service

        if tools:
            gen = gemini_service.stream_with_tools(
                messages=messages,
                tool_declarations=tools,
                model=model,
                system_instruction=system_prompt,
                use_web_search=use_web_search,
            )
        else:
            gen = gemini_service.stream_chat(
                messages=messages,
                model=model,
                system_instruction=system_prompt,
                use_web_search=use_web_search,
            )
        async for chunk in gen:
            yield chunk

    async def _stream_claude(
        self,
        messages: list[dict],
        model: str,
        system_prompt: str | None,
        tools: list[dict] | None,
        thinking_budget: int,
    ) -> AsyncGenerator[dict, None]:
        from services import claude_service

        if MODE != "standalone":
            context = {
                "type": "claude_code_context",
                "messages": messages,
                "system": system_prompt,
                "model": model,
                "instruction": "Feed this context into your Claude Code session for processing.",
            }
            yield {"type": "claude_code_export", "content": context}
            yield {"type": "done"}
            return

        if tools:
            gen = claude_service.stream_with_tools(
                messages=messages,
                tools=tools,
                model=model,
                system=system_prompt,
            )
        elif thinking_budget and thinking_budget > 0:
            gen = claude_service.stream_with_thinking(
                messages=messages,
                model=model,
                system=system_prompt,
                thinking_budget=thinking_budget,
            )
        else:
            gen = claude_service.stream_chat(
                messages=messages,
                model=model,
                system=system_prompt,
            )
        async for chunk in gen:
            yield chunk

    async def _stream_openai(
        self,
        messages: list[dict],
        model: str,
        system_prompt: str | None,
        tools: list[dict] | None,
    ) -> AsyncGenerator[dict, None]:
        from services import openai_service

        if tools:
            gen = openai_service.stream_with_tools(
                messages=messages,
                tools=tools,
                model=model,
                system=system_prompt,
            )
        else:
            gen = openai_service.stream_chat(
                messages=messages,
                model=model,
                system=system_prompt,
            )
        async for chunk in gen:
            yield chunk

    async def _run_rag(
        self,
        db_id: str,
        query: str,
        history: list[dict],
        limit: int,
    ) -> AsyncGenerator[dict, None]:
        """Delegate to RAG chat service, re-emitting chunks."""
        from services.rag_chat_service import rag_chat_service

        async for raw in rag_chat_service.chat(db_id, query, history, "hybrid", limit):
            try:
                data = json.loads(raw)
                yield data
            except (json.JSONDecodeError, TypeError):
                yield {"type": "token", "content": str(raw)}
        yield {"type": "done"}

    def _get_integration_tools(self) -> tuple[list[dict], list[dict]]:
        """Return Spotify + Calendar tool declarations if configured."""
        gemini_tools = []
        claude_tools = []
        try:
            from services.memory_service import memory_service
            conn = memory_service._get_conn()

            # Check Spotify
            row = conn.execute(
                "SELECT enabled FROM integrations WHERE platform = 'spotify' AND enabled = 1"
            ).fetchone()
            if row:
                gemini_tools.extend(SPOTIFY_TOOL_DECLARATIONS)
                claude_tools.extend(SPOTIFY_TOOL_DEFINITIONS_CLAUDE)

            # Check Calendar
            row = conn.execute(
                "SELECT enabled FROM integrations WHERE platform = 'calendar' AND enabled = 1"
            ).fetchone()
            if row:
                gemini_tools.extend(CALENDAR_TOOL_DECLARATIONS)
                claude_tools.extend(CALENDAR_TOOL_DEFINITIONS_CLAUDE)

        except Exception:
            pass
        return gemini_tools, claude_tools


# ── Spotify + Calendar Tool Declarations ─────────────────────────────

SPOTIFY_TOOL_DECLARATIONS = [
    {
        "name": "searchSpotify",
        "description": "Search Spotify for tracks, artists, or albums",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "type": {"type": "string", "description": "track, artist, or album", "enum": ["track", "artist", "album"]},
            },
            "required": ["query"],
        },
    },
    {
        "name": "getNowPlaying",
        "description": "Get the currently playing track on Spotify",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "addToQueue",
        "description": "Add a track to the Spotify playback queue",
        "parameters": {
            "type": "object",
            "properties": {"uri": {"type": "string", "description": "Spotify track URI"}},
            "required": ["uri"],
        },
    },
    {
        "name": "getPlaylists",
        "description": "List the user's Spotify playlists",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
]

CALENDAR_TOOL_DECLARATIONS = [
    {
        "name": "listCalendarEvents",
        "description": "List upcoming calendar events",
        "parameters": {
            "type": "object",
            "properties": {
                "max_results": {"type": "integer", "description": "Maximum events to return"},
                "time_min": {"type": "string", "description": "ISO datetime start filter"},
            },
            "required": [],
        },
    },
    {
        "name": "createCalendarEvent",
        "description": "Create a new calendar event",
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "Event title"},
                "start": {"type": "string", "description": "ISO datetime start"},
                "end": {"type": "string", "description": "ISO datetime end"},
                "description": {"type": "string", "description": "Event description"},
            },
            "required": ["summary", "start", "end"],
        },
    },
    {
        "name": "updateCalendarEvent",
        "description": "Update an existing calendar event",
        "parameters": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string"},
                "summary": {"type": "string"},
                "start": {"type": "string"},
                "end": {"type": "string"},
            },
            "required": ["event_id"],
        },
    },
    {
        "name": "deleteCalendarEvent",
        "description": "Delete a calendar event",
        "parameters": {
            "type": "object",
            "properties": {"event_id": {"type": "string"}},
            "required": ["event_id"],
        },
    },
]

# Claude versions (input_schema instead of parameters)
SPOTIFY_TOOL_DEFINITIONS_CLAUDE = [
    {**t, "input_schema": t.pop("parameters")} if "parameters" in t else t
    for t in [dict(d) for d in SPOTIFY_TOOL_DECLARATIONS]
]
CALENDAR_TOOL_DEFINITIONS_CLAUDE = [
    {**t, "input_schema": t.pop("parameters")} if "parameters" in t else t
    for t in [dict(d) for d in CALENDAR_TOOL_DECLARATIONS]
]


# Singleton
agentic_loop = AgenticLoop()

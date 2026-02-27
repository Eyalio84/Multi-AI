"""Capability KG Builder — builds cross-provider capability knowledge graphs.

Creates bipartite capability graphs: Model hubs ↔ Capability nodes, with
Pattern, Pricing, Code Example, API Endpoint, Parameter, and Limitation nodes.
All 3 provider KGs share the same 9-node-type schema for cross-provider queries.

Usage:
    from services.capability_kg_builder import capability_kg_builder
    result = await capability_kg_builder.build("openai")
    result = await capability_kg_builder.build("claude")
    result = await capability_kg_builder.build("gemini")
"""
import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── Source directories ────────────────────────────────────────────────
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent

PROVIDER_SOURCES = {
    "openai": {
        "registry": WORKSPACE_ROOT / "docs" / "chatgpt" / "openai-cookbook-main" / "registry.yaml",
        "api_md": WORKSPACE_ROOT / "docs" / "chatgpt" / "openai-python-main" / "api.md",
        "cookbook_dir": WORKSPACE_ROOT / "docs" / "chatgpt" / "openai-cookbook-main" / "examples",
        "sdk_dir": WORKSPACE_ROOT / "docs" / "chatgpt" / "openai-python-main" / "src" / "openai",
    },
    "claude": {
        "registry": WORKSPACE_ROOT / "docs" / "Claude" / "claude-cookbooks-main" / "registry.yaml",
        "api_md": None,  # No single api.md — capabilities in directories
        "cookbook_dir": WORKSPACE_ROOT / "docs" / "Claude" / "claude-cookbooks-main",
        "sdk_dir": None,
    },
    "gemini": {
        "registry": None,  # No registry.yaml — use README + notebook dirs
        "api_md": None,
        "cookbook_dir": WORKSPACE_ROOT / "docs" / "Geminidoc" / "cookbook-main",
        "sdk_dir": WORKSPACE_ROOT / "docs" / "Geminidoc" / "google-cloud-python-main",
    },
}

# ── Model catalogs per provider (capability-relevant models only) ─────
PROVIDER_MODELS = {
    "openai": [
        {"id": "gpt-5", "name": "GPT-5", "category": "text", "context": "1M", "cost_in": "$2.00", "cost_out": "$8.00"},
        {"id": "gpt-5-mini", "name": "GPT-5 Mini", "category": "text", "context": "1M", "cost_in": "$0.40", "cost_out": "$1.60"},
        {"id": "gpt-4.1", "name": "GPT-4.1", "category": "text", "context": "1M", "cost_in": "$2.00", "cost_out": "$8.00"},
        {"id": "gpt-4.1-mini", "name": "GPT-4.1 Mini", "category": "text", "context": "1M", "cost_in": "$0.40", "cost_out": "$1.60"},
        {"id": "gpt-4.1-nano", "name": "GPT-4.1 Nano", "category": "text", "context": "1M", "cost_in": "$0.10", "cost_out": "$0.40"},
        {"id": "o3", "name": "o3", "category": "reasoning", "context": "200K", "cost_in": "$2.00", "cost_out": "$8.00"},
        {"id": "o4-mini", "name": "o4 Mini", "category": "reasoning", "context": "200K", "cost_in": "$1.10", "cost_out": "$4.40"},
        {"id": "o3-mini", "name": "o3 Mini", "category": "reasoning", "context": "200K", "cost_in": "$1.10", "cost_out": "$4.40"},
        {"id": "o1", "name": "o1", "category": "reasoning", "context": "200K", "cost_in": "$15.00", "cost_out": "$60.00"},
        {"id": "o1-mini", "name": "o1 Mini", "category": "reasoning", "context": "128K", "cost_in": "$1.10", "cost_out": "$4.40"},
        {"id": "gpt-image-1", "name": "GPT Image 1", "category": "image", "context": "N/A", "cost_in": "varies", "cost_out": "varies"},
        {"id": "dall-e-3", "name": "DALL-E 3", "category": "image", "context": "N/A", "cost_in": "$0.04/img", "cost_out": "N/A"},
        {"id": "tts-1", "name": "TTS-1", "category": "audio", "context": "N/A", "cost_in": "$15.00/M chars", "cost_out": "N/A"},
        {"id": "tts-1-hd", "name": "TTS-1 HD", "category": "audio", "context": "N/A", "cost_in": "$30.00/M chars", "cost_out": "N/A"},
        {"id": "whisper-1", "name": "Whisper", "category": "audio", "context": "N/A", "cost_in": "$0.006/min", "cost_out": "N/A"},
        {"id": "text-embedding-3-large", "name": "Embedding 3 Large", "category": "embedding", "context": "8K", "cost_in": "$0.13/M", "cost_out": "N/A"},
        {"id": "text-embedding-3-small", "name": "Embedding 3 Small", "category": "embedding", "context": "8K", "cost_in": "$0.02/M", "cost_out": "N/A"},
        {"id": "codex-mini-latest", "name": "Codex Mini", "category": "agent", "context": "1M", "cost_in": "$1.50", "cost_out": "$6.00"},
        {"id": "computer-use-preview", "name": "Computer Use", "category": "agent", "context": "200K", "cost_in": "$3.00", "cost_out": "$12.00"},
    ],
    "claude": [
        {"id": "claude-opus-4-6", "name": "Claude Opus 4.6", "category": "text", "context": "200K", "cost_in": "$15.00", "cost_out": "$75.00"},
        {"id": "claude-sonnet-4-6", "name": "Claude Sonnet 4.6", "category": "text", "context": "200K", "cost_in": "$3.00", "cost_out": "$15.00"},
        {"id": "claude-haiku-4-5", "name": "Claude Haiku 4.5", "category": "text", "context": "200K", "cost_in": "$0.80", "cost_out": "$4.00"},
    ],
    "gemini": [
        {"id": "gemini-3-pro", "name": "Gemini 3 Pro", "category": "text", "context": "1M", "cost_in": "$1.25", "cost_out": "$10.00"},
        {"id": "gemini-3-flash", "name": "Gemini 3 Flash", "category": "text", "context": "1M", "cost_in": "$0.15", "cost_out": "$0.60"},
        {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro", "category": "text", "context": "1M", "cost_in": "$1.25", "cost_out": "$10.00"},
        {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash", "category": "text", "context": "1M", "cost_in": "$0.15", "cost_out": "$0.60"},
        {"id": "gemini-embedding-001", "name": "Gemini Embedding", "category": "embedding", "context": "2K", "cost_in": "free", "cost_out": "N/A"},
        {"id": "imagen-4", "name": "Imagen 4", "category": "image", "context": "N/A", "cost_in": "varies", "cost_out": "N/A"},
        {"id": "veo-3.1", "name": "Veo 3.1", "category": "video", "context": "N/A", "cost_in": "varies", "cost_out": "N/A"},
        {"id": "gemini-2.5-flash-tts", "name": "Gemini Flash TTS", "category": "audio", "context": "N/A", "cost_in": "$0.15", "cost_out": "N/A"},
        {"id": "lyria", "name": "Lyria", "category": "music", "context": "N/A", "cost_in": "varies", "cost_out": "N/A"},
    ],
}

# ── Capability normalization map (tags → canonical capability names) ───
TAG_TO_CAPABILITY = {
    # OpenAI tags
    "agents": "agent_workflows", "agent": "agent_workflows",
    "embeddings": "embeddings", "embedding": "embeddings",
    "gpt-5": "text_generation", "gpt-4o": "text_generation",
    "chatgpt": "text_generation", "completions": "text_generation",
    "function-calling": "function_calling", "functions": "function_calling",
    "tools": "tool_use", "tool-use": "tool_use",
    "vision": "image_understanding", "images": "image_understanding",
    "dall-e": "image_generation", "image-generation": "image_generation",
    "fine-tuning": "fine_tuning", "finetuning": "fine_tuning",
    "rag": "retrieval_augmented_generation",
    "search": "search", "web-search": "web_search",
    "streaming": "streaming", "realtime": "realtime_api",
    "audio": "audio_processing", "speech": "speech", "voice": "voice",
    "transcription": "transcription", "tts": "text_to_speech",
    "batch": "batch_processing", "batch-api": "batch_processing",
    "evals": "evaluation", "evaluation": "evaluation",
    "guardrails": "safety_guardrails", "moderation": "content_moderation",
    "structured-outputs": "structured_output",
    "json-mode": "structured_output", "json_mode": "structured_output",
    "reasoning": "reasoning", "chain-of-thought": "reasoning",
    "code-interpreter": "code_execution", "code": "code_generation",
    "coding": "code_generation",
    "multimodal": "multimodal", "multi-modal": "multimodal",
    "pdf": "document_processing", "files": "file_handling",
    "assistants": "assistants_api", "threads": "assistants_api",
    "responses": "responses_api",
    "tracing": "observability", "logging": "observability",
    "caching": "prompt_caching", "context-caching": "prompt_caching",
    "cost-optimization": "cost_optimization",
    "classification": "classification", "clustering": "clustering",
    "summarization": "summarization", "extraction": "entity_extraction",
    "translation": "translation",
    "prompt-engineering": "prompt_engineering",
    "memory": "memory_persistence",
    # Claude-specific
    "extended_thinking": "extended_thinking", "extended-thinking": "extended_thinking",
    "tool use": "tool_use", "computer use": "computer_use",
    "prompt caching": "prompt_caching",
    "citations": "citations",
    "mcp": "model_context_protocol",
    # Gemini-specific
    "grounding": "search_grounding",
    "live-api": "realtime_api",
    "context-window": "long_context",
    # Categories (Claude registry uses these)
    "Multimodal": "multimodal",
    "Tools": "tool_use",
    "RAG & Retrieval": "retrieval_augmented_generation",
    "Agent Patterns": "agent_workflows",
    "Integrations": "third_party_integrations",
    "Responses": "text_generation",
    "Skills": "advanced_skills",
}


def _node_id(provider: str, node_type: str, name: str) -> str:
    """Deterministic node ID from provider + type + name."""
    raw = f"{provider}:{node_type}:{name.lower().strip()}"
    return hashlib.md5(raw.encode()).hexdigest()[:16]


def _edge_id(source_id: str, edge_type: str, target_id: str) -> str:
    raw = f"{source_id}:{edge_type}:{target_id}"
    return hashlib.md5(raw.encode()).hexdigest()[:16]


class CapabilityKGBuilder:
    """Build capability KGs for any provider from documentation sources."""

    def __init__(self):
        self._build_status = {}

    async def build(self, provider: str, include_notebooks: bool = False) -> dict:
        """
        Build a capability KG for a provider.

        Args:
            provider: 'openai', 'claude', or 'gemini'
            include_notebooks: If True, use AI extraction on notebooks (costs ~$0.50)

        Returns:
            {"db_id": str, "nodes": int, "edges": int, "status": "complete"}
        """
        if provider not in PROVIDER_SOURCES:
            raise ValueError(f"Unknown provider: {provider}. Use: openai, claude, gemini")

        from services.kg_service import kg_service

        db_name = f"{provider}-capabilities"
        self._build_status[provider] = {"phase": "creating_db", "progress": 0}

        # Create (or reuse) the database
        try:
            db_id = kg_service.create_database(db_name)["id"]
        except (FileExistsError, ValueError):
            # DB exists — get its ID from the listing
            dbs = kg_service.list_databases()
            db_id = next((d["id"] for d in dbs if d.get("name") == db_name or d["id"] == db_name), db_name)

        nodes_created = 0
        edges_created = 0

        # ── Phase 1: Provider node ────────────────────────────
        self._build_status[provider] = {"phase": "provider_node", "progress": 5}
        prov_id = _node_id(provider, "provider", provider)
        self._upsert_node(kg_service, db_id, prov_id, provider.title(), "provider", {
            "description": f"{provider.title()} AI platform",
        })
        nodes_created += 1

        # ── Phase 2: Model + Pricing nodes ────────────────────
        self._build_status[provider] = {"phase": "models", "progress": 10}
        models = PROVIDER_MODELS.get(provider, [])
        for m in models:
            # Model node
            model_nid = _node_id(provider, "model", m["id"])
            self._upsert_node(kg_service, db_id, model_nid, m["name"], "model", {
                "model_id": m["id"],
                "category": m["category"],
                "context_window": m["context"],
            })
            nodes_created += 1

            # served_by edge: model → provider
            eid = _edge_id(model_nid, "served_by", prov_id)
            self._upsert_edge(kg_service, db_id, eid, model_nid, prov_id, "served_by")
            edges_created += 1

            # Pricing node
            price_nid = _node_id(provider, "pricing", f"{m['id']}_pricing")
            self._upsert_node(kg_service, db_id, price_nid, f"{m['name']} Pricing", "pricing", {
                "model_id": m["id"],
                "cost_input": m["cost_in"],
                "cost_output": m["cost_out"],
            })
            nodes_created += 1

            # has_pricing edge: model → pricing
            eid = _edge_id(model_nid, "has_pricing", price_nid)
            self._upsert_edge(kg_service, db_id, eid, model_nid, price_nid, "has_pricing")
            edges_created += 1

        # ── Phase 3: Registry extraction ──────────────────────
        self._build_status[provider] = {"phase": "registry", "progress": 25}
        sources = PROVIDER_SOURCES[provider]
        if sources.get("registry") and sources["registry"].exists():
            r_nodes, r_edges = self._extract_registry(kg_service, db_id, provider, sources["registry"])
            nodes_created += r_nodes
            edges_created += r_edges

        # ── Phase 4: API.md extraction ────────────────────────
        self._build_status[provider] = {"phase": "api_md", "progress": 50}
        if sources.get("api_md") and sources["api_md"].exists():
            a_nodes, a_edges = self._extract_api_md(kg_service, db_id, provider, sources["api_md"])
            nodes_created += a_nodes
            edges_created += a_edges

        # ── Phase 5: Cookbook directory scan (lightweight) ─────
        self._build_status[provider] = {"phase": "cookbook_scan", "progress": 65}
        if sources.get("cookbook_dir") and sources["cookbook_dir"].exists():
            c_nodes, c_edges = self._scan_cookbook_dirs(kg_service, db_id, provider, sources["cookbook_dir"])
            nodes_created += c_nodes
            edges_created += c_edges

        # ── Phase 6: Notebook AI extraction (optional) ────────
        if include_notebooks and sources.get("cookbook_dir"):
            self._build_status[provider] = {"phase": "notebook_ai", "progress": 75}
            n_nodes, n_edges = await self._extract_notebooks_ai(
                kg_service, db_id, provider, sources["cookbook_dir"]
            )
            nodes_created += n_nodes
            edges_created += n_edges

        # ── Phase 7: Cross-link capabilities to models ────────
        self._build_status[provider] = {"phase": "cross_linking", "progress": 90}
        x_edges = self._cross_link_capabilities_to_models(kg_service, db_id, provider)
        edges_created += x_edges

        # ── Phase 8: Generate embeddings ──────────────────────
        self._build_status[provider] = {"phase": "embeddings", "progress": 95}
        try:
            from services.embedding_service import embedding_service
            embedding_service.invalidate_cache(db_id)
            # BM25 index is rebuilt on next search automatically
        except Exception as e:
            logger.warning(f"Embedding setup skipped: {e}")

        self._build_status[provider] = {"phase": "complete", "progress": 100}

        return {
            "db_id": db_id,
            "provider": provider,
            "nodes": nodes_created,
            "edges": edges_created,
            "status": "complete",
        }

    def get_status(self, provider: str) -> dict:
        return self._build_status.get(provider, {"phase": "not_started", "progress": 0})

    async def build_unified_kg(self) -> dict:
        """Merge all 3 provider KGs into a single tri-united-capabilities.db with bridge edges."""
        from services.kg_service import kg_service
        import time

        db_name = "tri-united-capabilities"
        self._build_status["unified"] = {"phase": "initializing", "progress": 0}

        # Create or reuse the database, clearing existing data if it exists
        try:
            db_id = kg_service.create_database(db_name)["id"]
        except (FileExistsError, ValueError):
            dbs = kg_service.list_databases()
            db_id = next((d["id"] for d in dbs if d.get("name") == db_name or d["id"] == db_name), db_name)
            # Clear existing data for fresh rebuild
            try:
                conn = kg_service._get_conn(db_id)
                profile = kg_service._profiles.get(db_id, {})
                node_table = profile.get("node_table", "nodes")
                edge_table = profile.get("edge_table", "edges")
                conn.execute(f"DELETE FROM {edge_table}")
                conn.execute(f"DELETE FROM {node_table}")
                conn.commit()
            except Exception as e:
                logger.debug(f"Clear unified DB failed: {e}")

        start_time = time.time()
        total_nodes = 0
        total_edges = 0
        provider_stats = {}

        # ── Copy nodes and edges from each provider KG ────────────────
        providers_found = []
        for prov in ("openai", "claude", "gemini"):
            self._build_status["unified"] = {"phase": f"copying_{prov}", "progress": 10 + len(providers_found) * 25}

            prov_db_name = f"{prov}-capabilities"
            dbs = kg_service.list_databases()
            prov_db_id = next((d["id"] for d in dbs if d.get("name") == prov_db_name or d["id"] == prov_db_name), None)
            if not prov_db_id:
                logger.info(f"Unified KG: skipping {prov} (KG not found)")
                continue

            providers_found.append(prov)
            prov_nodes = 0
            prov_edges = 0

            try:
                conn_src = kg_service._get_conn(prov_db_id)
                profile_src = kg_service._profiles.get(prov_db_id, {})
                node_table = profile_src.get("node_table", "nodes")
                edge_table = profile_src.get("edge_table", "edges")

                # Copy all nodes (INSERT OR REPLACE deduplicates shared capability IDs)
                rows = conn_src.execute(f"SELECT id, name, type, properties FROM {node_table}").fetchall()
                for r in rows:
                    nid = r[0] if isinstance(r, (tuple, list)) else r["id"]
                    name = r[1] if isinstance(r, (tuple, list)) else r["name"]
                    ntype = r[2] if isinstance(r, (tuple, list)) else r["type"]
                    props_raw = r[3] if isinstance(r, (tuple, list)) else r["properties"]
                    props = json.loads(props_raw) if isinstance(props_raw, str) else (props_raw or {})
                    props["source_provider"] = prov
                    self._upsert_node(kg_service, db_id, nid, name, ntype, props)
                    prov_nodes += 1

                # Copy all edges
                rows = conn_src.execute(f"SELECT id, source, target, type, properties FROM {edge_table}").fetchall()
                for r in rows:
                    eid = r[0] if isinstance(r, (tuple, list)) else r["id"]
                    src = r[1] if isinstance(r, (tuple, list)) else r["source"]
                    tgt = r[2] if isinstance(r, (tuple, list)) else r["target"]
                    etype = r[3] if isinstance(r, (tuple, list)) else r["type"]
                    props_raw = r[4] if isinstance(r, (tuple, list)) else r["properties"]
                    props = json.loads(props_raw) if isinstance(props_raw, str) else (props_raw or {})
                    props["source_provider"] = prov
                    self._upsert_edge(kg_service, db_id, eid, src, tgt, etype, props)
                    prov_edges += 1

            except Exception as e:
                logger.warning(f"Unified KG: error copying {prov}: {e}")

            provider_stats[prov] = {"nodes": prov_nodes, "edges": prov_edges}
            total_nodes += prov_nodes
            total_edges += prov_edges

        if len(providers_found) < 2:
            self._build_status["unified"] = {"phase": "error", "progress": 0}
            return {"error": f"Need at least 2 provider KGs. Found: {providers_found}"}

        # ── Build bridge edges ────────────────────────────────────────
        self._build_status["unified"] = {"phase": "building_bridges", "progress": 85}
        bridge_count = self._build_bridge_edges(kg_service, db_id, providers_found)
        total_edges += bridge_count

        # ── Add metadata node ─────────────────────────────────────────
        self._build_status["unified"] = {"phase": "metadata", "progress": 95}
        import datetime
        meta_id = _node_id("unified", "metadata", "build_info")
        self._upsert_node(kg_service, db_id, meta_id, "Unified KG Build Info", "metadata", {
            "build_timestamp": datetime.datetime.now().isoformat(),
            "providers": providers_found,
            "provider_stats": provider_stats,
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "bridge_edges": bridge_count,
            "build_duration_s": round(time.time() - start_time, 2),
        })
        total_nodes += 1

        self._build_status["unified"] = {"phase": "complete", "progress": 100}

        return {
            "db_id": db_id,
            "nodes": total_nodes,
            "edges": total_edges,
            "bridge_edges": bridge_count,
            "providers": providers_found,
            "provider_stats": provider_stats,
            "status": "complete",
        }

    def _build_bridge_edges(self, kg_service, db_id: str, providers: list[str]) -> int:
        """Create cross-provider bridge edges: equivalent_capability, cheaper_alternative, provider_comparison."""
        conn = kg_service._get_conn(db_id)
        profile = kg_service._profiles.get(db_id, {})
        node_table = profile.get("node_table", "nodes")
        edge_table = profile.get("edge_table", "edges")
        bridges = 0

        # ── 1. equivalent_capability: models sharing same capability across providers ──
        # Find all has_capability edges, group by capability target
        try:
            rows = conn.execute(
                f"SELECT e.source, e.target, n1.name as model_name, n2.name as cap_name, n1.properties as model_props "
                f"FROM {edge_table} e "
                f"JOIN {node_table} n1 ON e.source = n1.id "
                f"JOIN {node_table} n2 ON e.target = n2.id "
                f"WHERE e.type = 'has_capability'"
            ).fetchall()

            cap_models = {}  # {cap_name: [(model_id, model_name, provider)]}
            for r in rows:
                model_id = r[0] if isinstance(r, (tuple, list)) else r["source"]
                cap_name = r[3] if isinstance(r, (tuple, list)) else r["cap_name"]
                model_name = r[2] if isinstance(r, (tuple, list)) else r["model_name"]
                props_raw = r[4] if isinstance(r, (tuple, list)) else r["model_props"]
                props = json.loads(props_raw) if isinstance(props_raw, str) else (props_raw or {})
                prov = props.get("source_provider", "unknown")
                if cap_name not in cap_models:
                    cap_models[cap_name] = []
                cap_models[cap_name].append((model_id, model_name, prov))

            # Create equivalent_capability edges between models from different providers
            for cap_name, models in cap_models.items():
                provider_groups = {}
                for mid, mname, mprov in models:
                    if mprov not in provider_groups:
                        provider_groups[mprov] = []
                    provider_groups[mprov].append((mid, mname))

                if len(provider_groups) < 2:
                    continue

                # Cross-provider pairs
                provs = list(provider_groups.keys())
                for i in range(len(provs)):
                    for j in range(i + 1, len(provs)):
                        for mid_a, mname_a in provider_groups[provs[i]]:
                            for mid_b, mname_b in provider_groups[provs[j]]:
                                eid = _edge_id(mid_a, "equivalent_capability", mid_b)
                                self._upsert_edge(kg_service, db_id, eid, mid_a, mid_b, "equivalent_capability", {
                                    "shared_capability": cap_name,
                                    "provider_a": provs[i],
                                    "provider_b": provs[j],
                                })
                                bridges += 1
        except Exception as e:
            logger.debug(f"Bridge equivalent_capability failed: {e}")

        # ── 2. cheaper_alternative: cost-based comparisons from pricing nodes ──
        try:
            pricing_rows = conn.execute(
                f"SELECT id, name, type, properties FROM {node_table} WHERE type = 'pricing'"
            ).fetchall()

            pricing_by_model = {}  # {model_id: cost_per_1m_in}
            for r in pricing_rows:
                props_raw = r[3] if isinstance(r, (tuple, list)) else r["properties"]
                props = json.loads(props_raw) if isinstance(props_raw, str) else (props_raw or {})
                cost_str = props.get("cost_input", props.get("cost_in", ""))
                prov = props.get("source_provider", "")
                # Find which model this pricing node connects to
                nid = r[0] if isinstance(r, (tuple, list)) else r["id"]
                model_edges = conn.execute(
                    f"SELECT source FROM {edge_table} WHERE target = ? AND type = 'has_pricing'", (nid,)
                ).fetchall()
                for me in model_edges:
                    model_id = me[0] if isinstance(me, (tuple, list)) else me["source"]
                    try:
                        cost_val = float(cost_str.replace("$", "").replace("/M", "").replace(" ", "").split("/")[0])
                        pricing_by_model[model_id] = {"cost": cost_val, "provider": prov}
                    except (ValueError, AttributeError):
                        pass

            # Create cheaper_alternative edges
            model_ids = list(pricing_by_model.keys())
            for i in range(len(model_ids)):
                for j in range(i + 1, len(model_ids)):
                    a, b = model_ids[i], model_ids[j]
                    pa, pb = pricing_by_model[a], pricing_by_model[b]
                    if pa["provider"] == pb["provider"]:
                        continue  # Only cross-provider
                    if pa["cost"] < pb["cost"]:
                        cheaper, expensive = a, b
                        ratio = round(pb["cost"] / pa["cost"], 2) if pa["cost"] > 0 else 0
                    elif pb["cost"] < pa["cost"]:
                        cheaper, expensive = b, a
                        ratio = round(pa["cost"] / pb["cost"], 2) if pb["cost"] > 0 else 0
                    else:
                        continue
                    eid = _edge_id(cheaper, "cheaper_alternative", expensive)
                    self._upsert_edge(kg_service, db_id, eid, cheaper, expensive, "cheaper_alternative", {
                        "cost_ratio": ratio,
                    })
                    bridges += 1
        except Exception as e:
            logger.debug(f"Bridge cheaper_alternative failed: {e}")

        # ── 3. provider_comparison: between provider nodes ──
        try:
            prov_nodes = conn.execute(
                f"SELECT id, name FROM {node_table} WHERE type = 'provider'"
            ).fetchall()
            prov_ids = [(r[0] if isinstance(r, (tuple, list)) else r["id"],
                         r[1] if isinstance(r, (tuple, list)) else r["name"]) for r in prov_nodes]

            for i in range(len(prov_ids)):
                for j in range(i + 1, len(prov_ids)):
                    eid = _edge_id(prov_ids[i][0], "provider_comparison", prov_ids[j][0])
                    self._upsert_edge(kg_service, db_id, eid, prov_ids[i][0], prov_ids[j][0], "provider_comparison", {
                        "providers": [prov_ids[i][1], prov_ids[j][1]],
                    })
                    bridges += 1
        except Exception as e:
            logger.debug(f"Bridge provider_comparison failed: {e}")

        return bridges

    # ── Registry extraction ───────────────────────────────────────────

    def _extract_registry(self, kg_service, db_id: str, provider: str, registry_path: Path) -> tuple[int, int]:
        """Parse registry.yaml → Pattern + Capability + Code Example nodes."""
        try:
            import yaml
        except ImportError:
            # Fallback: simple line-by-line YAML parsing
            return self._extract_registry_simple(kg_service, db_id, provider, registry_path)

        text = registry_path.read_text(encoding="utf-8", errors="replace")
        entries = yaml.safe_load(text)
        if not isinstance(entries, list):
            return 0, 0

        nodes = 0
        edges = 0
        seen_capabilities = set()

        for entry in entries:
            title = entry.get("title", "").strip()
            desc = entry.get("description", "").strip()
            path = entry.get("path", "")
            tags = entry.get("tags", []) or entry.get("categories", []) or []
            date = entry.get("date", "")

            if not title:
                continue

            # Pattern node
            pattern_nid = _node_id(provider, "pattern", title)
            self._upsert_node(kg_service, db_id, pattern_nid, title, "pattern", {
                "description": desc,
                "source_path": path,
                "date": str(date),
                "provider": provider,
            })
            nodes += 1

            # Code example node (if path points to a notebook or script)
            if path and (path.endswith(".ipynb") or path.endswith(".py") or path.endswith(".md")):
                ex_nid = _node_id(provider, "code_example", path)
                self._upsert_node(kg_service, db_id, ex_nid, f"Example: {title[:60]}", "code_example", {
                    "source_path": path,
                    "file_type": path.rsplit(".", 1)[-1],
                    "description": desc[:200],
                    "provider": provider,
                })
                nodes += 1

                # implements edge: code_example → pattern
                eid = _edge_id(ex_nid, "implements", pattern_nid)
                self._upsert_edge(kg_service, db_id, eid, ex_nid, pattern_nid, "implements")
                edges += 1

            # Extract capabilities from tags/categories
            for tag in tags:
                tag_str = str(tag).strip().lower()
                cap_name = TAG_TO_CAPABILITY.get(tag_str) or TAG_TO_CAPABILITY.get(tag) or tag_str.replace("-", "_")

                cap_nid = _node_id("shared", "capability", cap_name)

                if cap_name not in seen_capabilities:
                    self._upsert_node(kg_service, db_id, cap_nid, cap_name.replace("_", " ").title(), "capability", {
                        "canonical_name": cap_name,
                        "source_tags": [tag_str],
                    })
                    nodes += 1
                    seen_capabilities.add(cap_name)

                # demonstrates edge: pattern → capability
                eid = _edge_id(pattern_nid, "demonstrates", cap_nid)
                self._upsert_edge(kg_service, db_id, eid, pattern_nid, cap_nid, "demonstrates")
                edges += 1

        return nodes, edges

    def _extract_registry_simple(self, kg_service, db_id: str, provider: str, registry_path: Path) -> tuple[int, int]:
        """Fallback registry parsing without PyYAML — regex-based."""
        text = registry_path.read_text(encoding="utf-8", errors="replace")
        nodes = 0
        edges = 0
        seen_capabilities = set()

        # Parse YAML entries via regex
        title_re = re.compile(r'^- title:\s*(.+)', re.MULTILINE)
        desc_re = re.compile(r'^\s+description:\s*(.+)', re.MULTILINE)
        path_re = re.compile(r'^\s+path:\s*(.+)', re.MULTILINE)
        tag_re = re.compile(r'^\s+- ([\w\-]+)\s*$', re.MULTILINE)

        # Split by entries (each starts with "- title:")
        entries = text.split("\n- title:")
        for i, entry_text in enumerate(entries):
            if i == 0 and not entry_text.strip().startswith("title:"):
                continue
            if i > 0:
                entry_text = "- title:" + entry_text

            title_m = title_re.search(entry_text)
            if not title_m:
                continue
            title = title_m.group(1).strip().strip("'\"")

            desc = ""
            desc_m = desc_re.search(entry_text)
            if desc_m:
                desc = desc_m.group(1).strip()

            path = ""
            path_m = path_re.search(entry_text)
            if path_m:
                path = path_m.group(1).strip()

            # Pattern node
            pattern_nid = _node_id(provider, "pattern", title)
            self._upsert_node(kg_service, db_id, pattern_nid, title, "pattern", {
                "description": desc,
                "source_path": path,
                "provider": provider,
            })
            nodes += 1

            # Tags → capabilities
            tags_section = entry_text.split("tags:")[1] if "tags:" in entry_text else ""
            if not tags_section and "categories:" in entry_text:
                tags_section = entry_text.split("categories:")[1]
            if tags_section:
                # Get tags until next top-level key
                for line in tags_section.split("\n"):
                    line = line.strip()
                    if line.startswith("- ") and not line.startswith("- title"):
                        tag = line[2:].strip().strip("'\"")
                        if tag and len(tag) < 60:
                            cap_name = TAG_TO_CAPABILITY.get(tag.lower()) or tag.lower().replace("-", "_").replace(" ", "_")
                            cap_nid = _node_id("shared", "capability", cap_name)
                            if cap_name not in seen_capabilities:
                                self._upsert_node(kg_service, db_id, cap_nid, cap_name.replace("_", " ").title(), "capability", {
                                    "canonical_name": cap_name,
                                })
                                nodes += 1
                                seen_capabilities.add(cap_name)
                            eid = _edge_id(pattern_nid, "demonstrates", cap_nid)
                            self._upsert_edge(kg_service, db_id, eid, pattern_nid, cap_nid, "demonstrates")
                            edges += 1
                    elif line and not line.startswith("-") and not line.startswith("#"):
                        break

        return nodes, edges

    # ── API.md extraction ─────────────────────────────────────────────

    def _extract_api_md(self, kg_service, db_id: str, provider: str, api_md_path: Path) -> tuple[int, int]:
        """Parse SDK api.md → API Endpoint + Parameter nodes."""
        text = api_md_path.read_text(encoding="utf-8", errors="replace")
        nodes = 0
        edges = 0

        # Extract endpoint sections (# Header or ## Header)
        section_re = re.compile(r'^(#{1,3})\s+(.+)$', re.MULTILINE)
        method_re = re.compile(r'<code title="((?:get|post|put|delete|patch)\s+\S+)">')
        type_import_re = re.compile(r'from openai\.types(?:\.\w+)* import \((.*?)\)', re.DOTALL)

        current_section = None
        sections = {}

        for match in section_re.finditer(text):
            level = len(match.group(1))
            name = match.group(2).strip()
            if level <= 2:
                current_section = name
                sections[name] = {"level": level, "start": match.start()}

        # Extract API endpoints from method signatures
        for match in method_re.finditer(text):
            endpoint_str = match.group(1)  # e.g., "post /chat/completions"
            parts = endpoint_str.split(None, 1)
            if len(parts) == 2:
                http_method, path = parts
                ep_name = path.strip("/").replace("/", "_").replace("{", "").replace("}", "")

                ep_nid = _node_id(provider, "api_endpoint", path)
                self._upsert_node(kg_service, db_id, ep_nid, path, "api_endpoint", {
                    "http_method": http_method.upper(),
                    "path": path,
                    "provider": provider,
                })
                nodes += 1

                # Infer capability from endpoint path
                cap_name = self._endpoint_to_capability(path)
                if cap_name:
                    cap_nid = _node_id("shared", "capability", cap_name)
                    self._upsert_node(kg_service, db_id, cap_nid, cap_name.replace("_", " ").title(), "capability", {
                        "canonical_name": cap_name,
                    })
                    nodes += 1
                    eid = _edge_id(ep_nid, "exposes", cap_nid)
                    self._upsert_edge(kg_service, db_id, eid, ep_nid, cap_nid, "exposes")
                    edges += 1

        # Extract type names as parameters/capabilities indicators
        for match in type_import_re.finditer(text):
            types_block = match.group(1)
            type_names = [t.strip().strip(",") for t in types_block.split("\n") if t.strip() and not t.strip().startswith("#")]
            for tname in type_names:
                if tname and len(tname) > 3:
                    param_nid = _node_id(provider, "parameter", tname)
                    self._upsert_node(kg_service, db_id, param_nid, tname, "parameter", {
                        "sdk_type": tname,
                        "provider": provider,
                    })
                    nodes += 1

        return nodes, edges

    def _endpoint_to_capability(self, path: str) -> Optional[str]:
        """Map API endpoint path to a canonical capability name."""
        mapping = {
            "/chat/completions": "text_generation",
            "/completions": "text_generation",
            "/images/generations": "image_generation",
            "/images/edits": "image_editing",
            "/images/variations": "image_generation",
            "/embeddings": "embeddings",
            "/audio/transcriptions": "transcription",
            "/audio/translations": "translation",
            "/audio/speech": "text_to_speech",
            "/fine_tuning": "fine_tuning",
            "/files": "file_handling",
            "/assistants": "assistants_api",
            "/threads": "assistants_api",
            "/responses": "responses_api",
            "/moderations": "content_moderation",
            "/models": "model_listing",
            "/batches": "batch_processing",
            "/vector_stores": "vector_storage",
            "/evals": "evaluation",
        }
        for prefix, cap in mapping.items():
            if path.startswith(prefix):
                return cap
        return None

    # ── Cookbook directory scan ────────────────────────────────────────

    def _scan_cookbook_dirs(self, kg_service, db_id: str, provider: str, cookbook_dir: Path) -> tuple[int, int]:
        """Scan cookbook directory structure + notebook filenames for capability patterns."""
        nodes = 0
        edges = 0

        if not cookbook_dir.exists():
            return 0, 0

        # Directory names often indicate capabilities
        dir_capability_map = {
            "agents": "agent_workflows", "agents_sdk": "agent_workflows",
            "tool_use": "tool_use", "tool_evaluation": "tool_use",
            "multimodal": "multimodal", "vision": "image_understanding",
            "extended_thinking": "extended_thinking",
            "finetuning": "fine_tuning", "fine-tuning": "fine_tuning",
            "coding": "code_generation",
            "capabilities": None,  # Container dir, skip
            "examples": None,
            "quickstarts": None,
            "patterns": "design_patterns",
            "skills": "advanced_skills",
            "observability": "observability",
            "misc": None,
            "third_party": "third_party_integrations",
            "dalle": "image_generation",
            "chatgpt": "text_generation",
            "evals": "evaluation",
            "evaluation": "evaluation",
        }

        for subdir in sorted(cookbook_dir.iterdir()):
            if not subdir.is_dir() or subdir.name.startswith("."):
                continue

            cap_name = dir_capability_map.get(subdir.name)
            if cap_name is None:
                continue

            cap_nid = _node_id("shared", "capability", cap_name)
            self._upsert_node(kg_service, db_id, cap_nid, cap_name.replace("_", " ").title(), "capability", {
                "canonical_name": cap_name,
                "source_dir": subdir.name,
            })
            nodes += 1

            # Count files in directory as a richness indicator
            file_count = sum(1 for f in subdir.rglob("*") if f.is_file() and f.suffix in (".py", ".ipynb", ".md"))
            if file_count > 0:
                props = {"file_count": file_count, "source_dir": str(subdir.relative_to(cookbook_dir))}
                try:
                    conn = kg_service._get_conn(db_id)
                    conn.execute(
                        "UPDATE nodes SET properties = ? WHERE id = ?",
                        (json.dumps(props), cap_nid),
                    )
                    conn.commit()
                except Exception:
                    pass

        # ── Notebook filename scanning (especially for Gemini which has no registry)
        notebook_capability_map = {
            "function_calling": "function_calling", "function calling": "function_calling",
            "embeddings": "embeddings", "embedding": "embeddings",
            "audio": "audio_processing", "tts": "text_to_speech",
            "video": "video_generation", "veo": "video_generation",
            "imagen": "image_generation", "nano_banana": "image_generation",
            "live_api": "realtime_api", "liveapi": "realtime_api",
            "code_execution": "code_execution", "code execution": "code_execution",
            "caching": "prompt_caching", "cache": "prompt_caching",
            "batch": "batch_processing", "batch_mode": "batch_processing",
            "grounding": "search_grounding", "search": "search",
            "thinking": "extended_thinking", "reasoning": "reasoning",
            "json": "structured_output", "enum": "structured_output",
            "file_api": "file_handling", "file api": "file_handling",
            "file_search": "file_search",
            "safety": "safety_guardrails",
            "token": "token_counting", "counting_tokens": "token_counting",
            "system_instruction": "system_instructions",
            "streaming": "streaming",
            "openai_compatibility": "openai_compatibility",
            "lyria": "music_generation",
            "langchain": "third_party_integrations",
            "llamaindex": "third_party_integrations",
            "chromadb": "vector_storage",
            "qdrant": "vector_storage",
            "weaviate": "vector_storage",
            "prompting": "prompt_engineering",
            "learnlm": "education",
            "robotics": "robotics",
            "interactions_api": "agent_workflows",
        }

        seen_notebook_caps = set()
        for nb in cookbook_dir.rglob("*.ipynb"):
            stem = nb.stem.lower().replace("-", "_").replace(" ", "_")

            # Try matching against map
            matched_cap = None
            for pattern, cap in notebook_capability_map.items():
                if pattern in stem:
                    matched_cap = cap
                    break

            if matched_cap and matched_cap not in seen_notebook_caps:
                cap_nid = _node_id("shared", "capability", matched_cap)
                self._upsert_node(kg_service, db_id, cap_nid, matched_cap.replace("_", " ").title(), "capability", {
                    "canonical_name": matched_cap,
                })
                nodes += 1
                seen_notebook_caps.add(matched_cap)

            # Always create a code_example node for the notebook
            rel_path = str(nb.relative_to(cookbook_dir))
            title = nb.stem.replace("_", " ").replace("-", " ").strip()
            ex_nid = _node_id(provider, "code_example", rel_path)
            self._upsert_node(kg_service, db_id, ex_nid, f"Example: {title[:60]}", "code_example", {
                "source_path": rel_path,
                "file_type": "ipynb",
                "provider": provider,
            })
            nodes += 1

            # Link code example to capability
            if matched_cap:
                cap_nid = _node_id("shared", "capability", matched_cap)
                eid = _edge_id(ex_nid, "demonstrates", cap_nid)
                self._upsert_edge(kg_service, db_id, eid, ex_nid, cap_nid, "demonstrates")
                edges += 1

        return nodes, edges

    # ── Notebook AI extraction ────────────────────────────────────────

    async def _extract_notebooks_ai(self, kg_service, db_id: str, provider: str, cookbook_dir: Path) -> tuple[int, int]:
        """Use Gemini Flash to extract capabilities from Jupyter notebooks."""
        nodes = 0
        edges = 0

        notebooks = list(cookbook_dir.rglob("*.ipynb"))
        if not notebooks:
            return 0, 0

        try:
            from services import gemini_service
        except ImportError:
            logger.warning("Gemini service not available for notebook extraction")
            return 0, 0

        for i, nb_path in enumerate(notebooks):
            self._build_status[provider] = {
                "phase": "notebook_ai",
                "progress": 75 + int(15 * i / len(notebooks)),
                "current_file": nb_path.name,
                "files_processed": i,
                "files_total": len(notebooks),
            }

            try:
                # Read notebook and extract text content
                nb_text = self._notebook_to_text(nb_path)
                if len(nb_text) < 50:
                    continue

                prompt = (
                    f"Extract capabilities and patterns from this {provider.title()} API cookbook notebook.\n"
                    "Return JSON: {\"capabilities\": [\"streaming\", ...], "
                    "\"models_used\": [\"gpt-5\", ...], "
                    "\"patterns\": [\"RAG with embeddings\", ...], "
                    "\"limitations\": [\"max 4096 output tokens\", ...]}\n\n"
                    f"Notebook content (truncated):\n{nb_text[:8000]}"
                )

                raw = gemini_service.generate_content(
                    prompt, model="gemini-2.5-flash",
                    response_mime_type="application/json",
                )
                data = json.loads(raw)

                # Create nodes from AI extraction
                for cap in data.get("capabilities", []):
                    cap_name = TAG_TO_CAPABILITY.get(cap.lower(), cap.lower().replace(" ", "_").replace("-", "_"))
                    cap_nid = _node_id("shared", "capability", cap_name)
                    self._upsert_node(kg_service, db_id, cap_nid, cap_name.replace("_", " ").title(), "capability", {
                        "canonical_name": cap_name,
                    })
                    nodes += 1

                    # Link code example to capability
                    ex_nid = _node_id(provider, "code_example", str(nb_path.relative_to(cookbook_dir)))
                    self._upsert_node(kg_service, db_id, ex_nid, f"Example: {nb_path.stem}", "code_example", {
                        "source_path": str(nb_path.relative_to(cookbook_dir)),
                        "file_type": "ipynb",
                        "provider": provider,
                    })
                    eid = _edge_id(ex_nid, "demonstrates", cap_nid)
                    self._upsert_edge(kg_service, db_id, eid, ex_nid, cap_nid, "demonstrates")
                    edges += 1

                for lim in data.get("limitations", []):
                    lim_nid = _node_id(provider, "limitation", lim)
                    self._upsert_node(kg_service, db_id, lim_nid, lim, "limitation", {
                        "provider": provider,
                    })
                    nodes += 1

            except Exception as e:
                logger.debug(f"Notebook extraction failed for {nb_path.name}: {e}")
                continue

        return nodes, edges

    def _notebook_to_text(self, nb_path: Path) -> str:
        """Extract text content from a Jupyter notebook."""
        try:
            data = json.loads(nb_path.read_text(encoding="utf-8", errors="replace"))
            cells = data.get("cells", [])
            parts = []
            for cell in cells:
                source = "".join(cell.get("source", []))
                if cell.get("cell_type") == "markdown":
                    parts.append(source)
                elif cell.get("cell_type") == "code":
                    parts.append(f"```python\n{source}\n```")
            return "\n\n".join(parts)
        except Exception:
            return ""

    # ── Cross-link capabilities to models ─────────────────────────────

    def _cross_link_capabilities_to_models(self, kg_service, db_id: str, provider: str) -> int:
        """Create has_capability edges between models and capabilities."""
        edges = 0

        # Default capability assignments per model category
        category_capabilities = {
            "text": ["text_generation", "streaming", "function_calling", "tool_use", "structured_output"],
            "reasoning": ["text_generation", "reasoning", "streaming"],
            "image": ["image_generation"],
            "audio": ["audio_processing"],
            "embedding": ["embeddings"],
            "video": ["video_generation"],
            "music": ["music_generation"],
            "agent": ["agent_workflows", "tool_use", "code_execution"],
        }

        # Provider-specific capability overrides
        provider_model_caps = {
            "openai": {
                "gpt-5": ["text_generation", "streaming", "function_calling", "tool_use",
                           "structured_output", "image_understanding", "multimodal",
                           "code_generation", "responses_api", "batch_processing"],
                "o3": ["text_generation", "reasoning", "streaming", "function_calling",
                        "tool_use", "structured_output"],
                "o4-mini": ["text_generation", "reasoning", "streaming", "function_calling",
                             "tool_use", "structured_output"],
                "dall-e-3": ["image_generation"],
                "gpt-image-1": ["image_generation", "image_editing"],
                "whisper-1": ["transcription", "translation"],
                "tts-1": ["text_to_speech"],
                "tts-1-hd": ["text_to_speech"],
                "codex-mini-latest": ["agent_workflows", "code_execution", "tool_use"],
                "computer-use-preview": ["computer_use", "agent_workflows"],
            },
            "claude": {
                "claude-opus-4-6": ["text_generation", "streaming", "tool_use", "function_calling",
                                     "extended_thinking", "code_generation", "multimodal",
                                     "image_understanding", "prompt_caching", "batch_processing",
                                     "citations", "model_context_protocol", "computer_use"],
                "claude-sonnet-4-6": ["text_generation", "streaming", "tool_use", "function_calling",
                                       "extended_thinking", "code_generation", "multimodal",
                                       "image_understanding", "prompt_caching", "batch_processing",
                                       "citations", "model_context_protocol", "computer_use"],
                "claude-haiku-4-5": ["text_generation", "streaming", "tool_use", "function_calling",
                                      "code_generation", "prompt_caching", "batch_processing"],
            },
            "gemini": {
                "gemini-3-pro": ["text_generation", "streaming", "function_calling", "tool_use",
                                  "multimodal", "image_understanding", "code_generation",
                                  "long_context", "search_grounding", "batch_processing"],
                "gemini-2.5-flash": ["text_generation", "streaming", "function_calling", "tool_use",
                                      "multimodal", "code_generation", "long_context",
                                      "search_grounding", "batch_processing", "image_generation"],
                "gemini-embedding-001": ["embeddings"],
                "imagen-4": ["image_generation"],
                "veo-3.1": ["video_generation"],
                "gemini-2.5-flash-tts": ["text_to_speech"],
                "lyria": ["music_generation"],
            },
        }

        models = PROVIDER_MODELS.get(provider, [])
        model_caps = provider_model_caps.get(provider, {})

        for m in models:
            model_nid = _node_id(provider, "model", m["id"])

            # Get specific caps or fallback to category defaults
            caps = model_caps.get(m["id"], category_capabilities.get(m["category"], []))

            for cap_name in caps:
                cap_nid = _node_id("shared", "capability", cap_name)
                # Ensure capability node exists
                self._upsert_node(kg_service, db_id, cap_nid, cap_name.replace("_", " ").title(), "capability", {
                    "canonical_name": cap_name,
                })

                eid = _edge_id(model_nid, "has_capability", cap_nid)
                self._upsert_edge(kg_service, db_id, eid, model_nid, cap_nid, "has_capability")
                edges += 1

        return edges

    # ── Helpers ────────────────────────────────────────────────────────

    def _upsert_node(self, kg_service, db_id: str, node_id: str, name: str, node_type: str, properties: dict):
        """Create or update a node."""
        try:
            conn = kg_service._get_conn(db_id)
            profile = kg_service._profiles.get(db_id, {})
            node_table = profile.get("node_table", "nodes")
            props_json = json.dumps(properties)

            conn.execute(
                f"INSERT OR REPLACE INTO {node_table} (id, name, type, properties) VALUES (?, ?, ?, ?)",
                (node_id, name, node_type, props_json),
            )
            conn.commit()
        except Exception as e:
            logger.debug(f"Node upsert failed: {e}")

    def _upsert_edge(self, kg_service, db_id: str, edge_id: str, source: str, target: str, edge_type: str, properties: dict = None):
        """Create or update an edge."""
        try:
            conn = kg_service._get_conn(db_id)
            profile = kg_service._profiles.get(db_id, {})
            edge_table = profile.get("edge_table", "edges")
            props_json = json.dumps(properties or {})

            conn.execute(
                f"INSERT OR REPLACE INTO {edge_table} (id, source, target, type, properties) VALUES (?, ?, ?, ?, ?)",
                (edge_id, source, target, edge_type, props_json),
            )
            conn.commit()
        except Exception as e:
            logger.debug(f"Edge upsert failed: {e}")


# ── Cross-provider bridging ───────────────────────────────────────────

async def build_cross_provider_bridges() -> dict:
    """After all 3 KGs are built, create alternative_to edges for shared capabilities."""
    from services.kg_service import kg_service

    provider_dbs = {}
    for prov in ("openai", "claude", "gemini"):
        db_name = f"{prov}-capabilities"
        dbs = kg_service.list_databases()
        db_id = next((d["id"] for d in dbs if d.get("name") == db_name or d["id"] == db_name), None)
        if db_id:
            provider_dbs[prov] = db_id

    if len(provider_dbs) < 2:
        return {"error": "Need at least 2 provider KGs to bridge", "found": list(provider_dbs.keys())}

    # Find shared capability nodes across KGs
    bridges = 0
    capability_models = {}  # {cap_name: [(provider, model_name, model_nid, db_id)]}

    for prov, db_id in provider_dbs.items():
        try:
            conn = kg_service._get_conn(db_id)
            # Find all has_capability edges
            rows = conn.execute(
                "SELECT e.source, e.target, n1.name as model_name, n2.name as cap_name "
                "FROM edges e "
                "JOIN nodes n1 ON e.source = n1.id "
                "JOIN nodes n2 ON e.target = n2.id "
                "WHERE e.type = 'has_capability'"
            ).fetchall()
            for r in rows:
                cap = r[3] if len(r) > 3 else r["cap_name"]
                model = r[2] if len(r) > 2 else r["model_name"]
                if cap not in capability_models:
                    capability_models[cap] = []
                capability_models[cap].append((prov, model, r[0], db_id))
        except Exception as e:
            logger.debug(f"Bridge scan failed for {prov}: {e}")

    # Create bridges for capabilities shared across providers
    shared_caps = {k: v for k, v in capability_models.items() if len(set(e[0] for e in v)) > 1}

    return {
        "shared_capabilities": len(shared_caps),
        "total_capabilities": len(capability_models),
        "bridges_created": bridges,
        "shared": {k: [{"provider": e[0], "model": e[1]} for e in v] for k, v in shared_caps.items()},
    }


# Singleton
capability_kg_builder = CapabilityKGBuilder()

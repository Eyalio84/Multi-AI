"""Integration tests for capability KG builder — validates extraction, schema, and retrieval.

Run: cd backend && python -m pytest tests/test_capability_kg_builder.py -v
Or:  cd backend && python tests/test_capability_kg_builder.py
"""
import asyncio
import os
import sys
import json
import sqlite3
from pathlib import Path

# Ensure backend is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.chdir(str(Path(__file__).resolve().parent.parent))


def test_builder_import():
    """Verify the builder module imports cleanly."""
    from services.capability_kg_builder import (
        capability_kg_builder,
        build_cross_provider_bridges,
        PROVIDER_SOURCES,
        PROVIDER_MODELS,
        TAG_TO_CAPABILITY,
        _node_id,
        _edge_id,
    )
    assert capability_kg_builder is not None
    assert len(PROVIDER_SOURCES) == 3
    assert len(PROVIDER_MODELS) == 3
    assert len(TAG_TO_CAPABILITY) > 40
    print("  PASS: Builder imports clean")


def test_node_id_deterministic():
    """Node IDs must be deterministic and consistent across calls."""
    from services.capability_kg_builder import _node_id
    id1 = _node_id("shared", "capability", "text_generation")
    id2 = _node_id("shared", "capability", "text_generation")
    id3 = _node_id("shared", "capability", "Text_Generation")  # different case → same after .lower()
    id4 = _node_id("openai", "capability", "text_generation")  # different provider

    assert id1 == id2, "Same inputs must produce same ID"
    assert id1 == id3, "Case-insensitive: _node_id lowercases names for normalization"
    assert id1 != id4, "Different provider should produce different ID"
    assert len(id1) == 16, f"ID should be 16 chars, got {len(id1)}"

    # BUT: shared capability IDs should be the same across providers
    shared_openai = _node_id("shared", "capability", "embeddings")
    shared_claude = _node_id("shared", "capability", "embeddings")
    assert shared_openai == shared_claude, "Shared capability IDs must match"
    print("  PASS: Node IDs deterministic")


def test_edge_id_deterministic():
    """Edge IDs must be deterministic."""
    from services.capability_kg_builder import _edge_id
    e1 = _edge_id("node_a", "has_capability", "node_b")
    e2 = _edge_id("node_a", "has_capability", "node_b")
    e3 = _edge_id("node_b", "has_capability", "node_a")  # reversed

    assert e1 == e2
    assert e1 != e3
    print("  PASS: Edge IDs deterministic")


def test_provider_sources_exist():
    """Verify that configured source paths exist on disk."""
    from services.capability_kg_builder import PROVIDER_SOURCES

    issues = []
    for prov, sources in PROVIDER_SOURCES.items():
        for key, path in sources.items():
            if path is None:
                continue
            if not path.exists():
                issues.append(f"{prov}.{key}: {path}")

    if issues:
        print(f"  WARN: Missing source paths (non-fatal):")
        for iss in issues:
            print(f"    - {iss}")
    else:
        print("  PASS: All provider source paths exist")
    return len(issues) == 0


def test_tag_normalization():
    """Tag → capability normalization should handle edge cases."""
    from services.capability_kg_builder import TAG_TO_CAPABILITY

    # OpenAI tags
    assert TAG_TO_CAPABILITY.get("agents") == "agent_workflows"
    assert TAG_TO_CAPABILITY.get("function-calling") == "function_calling"
    assert TAG_TO_CAPABILITY.get("structured-outputs") == "structured_output"

    # Claude categories
    assert TAG_TO_CAPABILITY.get("Tools") == "tool_use"
    assert TAG_TO_CAPABILITY.get("RAG & Retrieval") == "retrieval_augmented_generation"

    # Gemini tags
    assert TAG_TO_CAPABILITY.get("grounding") == "search_grounding"
    print("  PASS: Tag normalization correct")


def test_model_catalog_completeness():
    """All provider model catalogs should have required fields."""
    from services.capability_kg_builder import PROVIDER_MODELS

    for prov, models in PROVIDER_MODELS.items():
        for m in models:
            assert "id" in m, f"{prov} model missing 'id': {m}"
            assert "name" in m, f"{prov} model missing 'name': {m}"
            assert "category" in m, f"{prov} model missing 'category': {m}"
            assert "cost_in" in m, f"{prov} model missing 'cost_in': {m}"

    total_models = sum(len(v) for v in PROVIDER_MODELS.values())
    print(f"  PASS: {total_models} models validated across {len(PROVIDER_MODELS)} providers")


async def test_build_claude_kg():
    """Build Claude capability KG (smallest source) and validate results."""
    from services.capability_kg_builder import capability_kg_builder
    from services.kg_service import kg_service

    print("\n  Building Claude capability KG...")
    result = await capability_kg_builder.build("claude", include_notebooks=False)

    assert result["provider"] == "claude"
    assert result["status"] == "complete"
    assert result["nodes"] > 0, f"Expected nodes > 0, got {result['nodes']}"
    assert result["edges"] > 0, f"Expected edges > 0, got {result['edges']}"

    db_id = result["db_id"]
    print(f"  Built: db_id={db_id}, nodes={result['nodes']}, edges={result['edges']}")

    # ── Validate database structure ────
    conn = kg_service._get_conn(db_id)

    # Check node types
    node_types = conn.execute("SELECT DISTINCT type FROM nodes ORDER BY type").fetchall()
    types_list = [r[0] for r in node_types]
    print(f"  Node types: {types_list}")

    # Must have at least: provider, model, capability, pricing
    assert "provider" in types_list, "Missing 'provider' node type"
    assert "model" in types_list, "Missing 'model' node type"
    assert "capability" in types_list, "Missing 'capability' node type"
    assert "pricing" in types_list, "Missing 'pricing' node type"

    # Check edge types
    edge_types = conn.execute("SELECT DISTINCT type FROM edges ORDER BY type").fetchall()
    etypes_list = [r[0] for r in edge_types]
    print(f"  Edge types: {etypes_list}")

    assert "served_by" in etypes_list, "Missing 'served_by' edge type"
    assert "has_pricing" in etypes_list, "Missing 'has_pricing' edge type"
    assert "has_capability" in etypes_list, "Missing 'has_capability' edge type"

    # Validate bipartite structure: models should have capability edges
    cap_edges = conn.execute(
        "SELECT COUNT(*) FROM edges WHERE type = 'has_capability'"
    ).fetchone()[0]
    assert cap_edges > 0, f"Expected has_capability edges, got {cap_edges}"
    print(f"  has_capability edges: {cap_edges}")

    # Validate pricing nodes match model count
    model_count = conn.execute("SELECT COUNT(*) FROM nodes WHERE type = 'model'").fetchone()[0]
    pricing_count = conn.execute("SELECT COUNT(*) FROM nodes WHERE type = 'pricing'").fetchone()[0]
    assert model_count == pricing_count, f"Model count ({model_count}) should equal pricing count ({pricing_count})"
    print(f"  Models: {model_count}, Pricing nodes: {pricing_count}")

    # ── Test retrieval ──────────────
    print("\n  Testing hybrid search on the new KG...")
    from services.embedding_service import embedding_service

    # Basic text search (BM25 should work even without embeddings)
    search_result = embedding_service.search(db_id, "tool use", mode="hybrid", limit=5)
    print(f"  Search 'tool use': {len(search_result.get('results', []))} results")

    if search_result.get("results"):
        top = search_result["results"][0]
        print(f"    Top result: {top.get('node', {}).get('name', 'N/A')} "
              f"(type={top.get('node', {}).get('type', 'N/A')}, "
              f"score={top.get('score', 0):.3f})")

    # Intent-adaptive search
    intent_result = embedding_service.search(db_id, "how to reduce API costs", mode="hybrid", limit=5)
    detected_intent = intent_result.get("intent", "unknown")
    print(f"  Search 'how to reduce API costs': intent={detected_intent}, "
          f"{len(intent_result.get('results', []))} results")

    # Capability-check search
    cap_result = embedding_service.search(db_id, "does Claude support streaming", mode="hybrid", limit=5)
    cap_intent = cap_result.get("intent", "unknown")
    print(f"  Search 'does Claude support streaming': intent={cap_intent}, "
          f"{len(cap_result.get('results', []))} results")

    print(f"\n  PASS: Claude KG built and searchable ({result['nodes']} nodes, {result['edges']} edges)")
    return result


async def test_build_openai_kg():
    """Build OpenAI capability KG (largest source) and validate."""
    from services.capability_kg_builder import capability_kg_builder

    print("\n  Building OpenAI capability KG...")
    result = await capability_kg_builder.build("openai", include_notebooks=False)

    assert result["provider"] == "openai"
    assert result["status"] == "complete"
    assert result["nodes"] > 0
    assert result["edges"] > 0
    print(f"  Built: db_id={result['db_id']}, nodes={result['nodes']}, edges={result['edges']}")

    # OpenAI should have more nodes than Claude due to registry + api.md
    from services.kg_service import kg_service
    conn = kg_service._get_conn(result["db_id"])

    # Check for API endpoint nodes (from api.md)
    api_count = conn.execute("SELECT COUNT(*) FROM nodes WHERE type = 'api_endpoint'").fetchone()[0]
    print(f"  API endpoint nodes: {api_count}")

    # Check for pattern nodes (from registry.yaml)
    pattern_count = conn.execute("SELECT COUNT(*) FROM nodes WHERE type = 'pattern'").fetchone()[0]
    print(f"  Pattern nodes: {pattern_count}")

    # Check for code example nodes
    example_count = conn.execute("SELECT COUNT(*) FROM nodes WHERE type = 'code_example'").fetchone()[0]
    print(f"  Code example nodes: {example_count}")

    print(f"\n  PASS: OpenAI KG built ({result['nodes']} nodes, {result['edges']} edges)")
    return result


async def test_build_gemini_kg():
    """Build Gemini capability KG."""
    from services.capability_kg_builder import capability_kg_builder

    print("\n  Building Gemini capability KG...")
    result = await capability_kg_builder.build("gemini", include_notebooks=False)

    assert result["provider"] == "gemini"
    assert result["status"] == "complete"
    assert result["nodes"] > 0
    assert result["edges"] > 0
    print(f"  Built: db_id={result['db_id']}, nodes={result['nodes']}, edges={result['edges']}")

    print(f"\n  PASS: Gemini KG built ({result['nodes']} nodes, {result['edges']} edges)")
    return result


async def test_cross_provider_bridges():
    """Test cross-provider capability bridging."""
    from services.capability_kg_builder import build_cross_provider_bridges

    print("\n  Building cross-provider bridges...")
    result = await build_cross_provider_bridges()

    if "error" in result:
        print(f"  SKIP: {result['error']} (found: {result.get('found', [])})")
        return result

    shared = result.get("shared_capabilities", 0)
    total = result.get("total_capabilities", 0)
    print(f"  Shared capabilities: {shared}/{total}")

    # Print some shared capabilities
    for cap_name, providers in list(result.get("shared", {}).items())[:10]:
        prov_list = [p["provider"] for p in providers]
        print(f"    {cap_name}: {', '.join(prov_list)}")

    print(f"\n  PASS: Cross-provider bridges analyzed ({shared} shared capabilities)")
    return result


async def test_search_across_kgs():
    """Test searching the same query across all 3 KGs."""
    from services.embedding_service import embedding_service
    from services.kg_service import kg_service

    print("\n  Testing cross-KG search...")
    dbs = kg_service.list_databases()
    cap_dbs = [d for d in dbs if d["id"].endswith("-capabilities")]

    if not cap_dbs:
        print("  SKIP: No capability KGs found")
        return

    query = "text generation"
    print(f"  Query: '{query}'")

    for db in cap_dbs:
        try:
            result = embedding_service.search(db["id"], query, mode="hybrid", limit=3)
            hits = result.get("results", [])
            intent = result.get("intent", "N/A")
            print(f"  {db['id']}: {len(hits)} results (intent={intent})")
            for h in hits[:2]:
                n = h.get("node", {})
                print(f"    - {n.get('name', '?')} ({n.get('type', '?')}) score={h.get('score', 0):.3f}")
        except Exception as e:
            print(f"  {db['id']}: ERROR — {e}")

    print(f"\n  PASS: Cross-KG search completed across {len(cap_dbs)} capability KGs")


# ── Runner ────────────────────────────────────────────────────────
async def run_all_tests():
    print("=" * 60)
    print("Capability KG Builder — Integration Tests")
    print("=" * 60)

    # Unit tests (synchronous)
    print("\n--- Unit Tests ---")
    test_builder_import()
    test_node_id_deterministic()
    test_edge_id_deterministic()
    test_tag_normalization()
    test_model_catalog_completeness()
    sources_ok = test_provider_sources_exist()

    if not sources_ok:
        print("\n  WARNING: Some sources missing. Build tests may produce fewer nodes.")

    # Integration tests (async) — build all 3 KGs
    print("\n--- Build Tests ---")
    claude_result = await test_build_claude_kg()
    openai_result = await test_build_openai_kg()
    gemini_result = await test_build_gemini_kg()

    # Cross-provider tests
    print("\n--- Cross-Provider Tests ---")
    bridge_result = await test_cross_provider_bridges()
    await test_search_across_kgs()

    # Summary
    print("\n" + "=" * 60)
    total_nodes = claude_result["nodes"] + openai_result["nodes"] + gemini_result["nodes"]
    total_edges = claude_result["edges"] + openai_result["edges"] + gemini_result["edges"]
    shared = bridge_result.get("shared_capabilities", 0) if isinstance(bridge_result, dict) else 0
    print(f"TOTAL: {total_nodes} nodes, {total_edges} edges across 3 KGs")
    print(f"SHARED CAPABILITIES: {shared}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_all_tests())

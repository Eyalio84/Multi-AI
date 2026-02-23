"""Ingestion service — AI entity extraction, LightRAG pipeline, manual document storage."""
import json
import hashlib
from typing import Any

from services.kg_service import kg_service


EXTRACTION_PROMPT = """Extract entities and relationships from the following text.
Return a JSON object with exactly this structure:
{
  "entities": [
    {"name": "Entity Name", "type": "entity_type", "properties": {"key": "value"}}
  ],
  "relations": [
    {"source": "Source Entity Name", "target": "Target Entity Name", "type": "relationship_type"}
  ]
}

Rules:
- Entity types should be lowercase (e.g., "person", "concept", "tool", "organization")
- Relationship types should be lowercase with underscores (e.g., "relates_to", "part_of", "created_by")
- Extract ALL meaningful entities and relationships from the text
- Be specific with entity types — don't use generic "entity" unless nothing else fits

Text:
"""


class IngestionService:
    """Ingest text into knowledge graphs via AI extraction or manual methods."""

    async def ingest(self, db_id: str, text: str, method: str = "ai",
                     source: str | None = None) -> dict:
        if method == "ai":
            return await self._ingest_ai(db_id, text, source)
        elif method == "lightrag":
            return await self._ingest_lightrag(db_id, text, source)
        elif method == "manual":
            return self._ingest_manual(db_id, text, source)
        else:
            raise ValueError(f"Unknown ingestion method: {method}")

    async def _ingest_ai(self, db_id: str, text: str, source: str | None) -> dict:
        """Use Gemini to extract entities and relations, then insert into KG."""
        from config import GEMINI_API_KEY
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not configured — needed for AI extraction")

        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)

        prompt = EXTRACTION_PROMPT + text[:8000]
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )

        # Parse JSON response
        raw = response.text.strip()
        # Handle markdown code blocks
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]

        try:
            extracted = json.loads(raw)
        except json.JSONDecodeError:
            raise ValueError(f"AI returned invalid JSON: {raw[:200]}")

        entities = extracted.get("entities", [])
        relations = extracted.get("relations", [])

        # Build name->id mapping
        name_to_id = {}
        created_nodes = []
        for e in entities:
            name = e.get("name", "").strip()
            if not name:
                continue
            etype = e.get("type", "entity")
            props = e.get("properties", {})
            if source:
                props["source"] = source
            node = kg_service.create_node(db_id, name, etype, props)
            name_to_id[name.lower()] = node["id"]
            created_nodes.append(node)

        created_edges = []
        for r in relations:
            src_name = r.get("source", "").strip().lower()
            tgt_name = r.get("target", "").strip().lower()
            rtype = r.get("type", "relates_to")
            src_id = name_to_id.get(src_name)
            tgt_id = name_to_id.get(tgt_name)
            if src_id and tgt_id:
                edge = kg_service.create_edge(db_id, src_id, tgt_id, rtype)
                created_edges.append(edge)

        return {
            "method": "ai",
            "entities_extracted": len(entities),
            "relations_extracted": len(relations),
            "nodes_created": len(created_nodes),
            "edges_created": len(created_edges),
            "nodes": created_nodes,
            "edges": created_edges,
        }

    async def _ingest_lightrag(self, db_id: str, text: str, source: str | None) -> dict:
        """Use LightRAG pipeline for entity extraction + graph construction."""
        try:
            from lightrag import LightRAG, QueryParam
            from lightrag.llm.google import gpt_4o_mini_complete
        except ImportError:
            # Fallback to AI method if LightRAG not installed
            return await self._ingest_ai(db_id, text, source)

        from config import GEMINI_API_KEY, KGS_DIR
        import os
        import tempfile

        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not configured")

        # LightRAG needs a working directory
        work_dir = tempfile.mkdtemp(prefix="lightrag_")

        try:
            os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY
            rag = LightRAG(
                working_dir=work_dir,
                llm_model_func=gpt_4o_mini_complete,
                llm_model_name="gemini-2.5-flash",
            )
            await rag.ainsert(text)

            # Extract entities from LightRAG's internal storage
            # LightRAG stores entities in its own format — we convert to our KG
            entities_found = []
            edges_found = []

            if hasattr(rag, 'chunk_entity_relation_graph'):
                g = rag.chunk_entity_relation_graph
                for node_id in g.nodes():
                    node_data = g.nodes[node_id]
                    entities_found.append({
                        "name": str(node_id),
                        "type": node_data.get("entity_type", "entity"),
                        "properties": {"source": source} if source else {},
                    })
                for u, v, data in g.edges(data=True):
                    edges_found.append({
                        "source": str(u),
                        "target": str(v),
                        "type": data.get("relation", "relates_to"),
                    })

            # Insert into our KG
            created = kg_service.bulk_create(db_id,
                [{"name": e["name"], "type": e["type"], "properties": e.get("properties")} for e in entities_found],
                [{"source": e["source"], "target": e["target"], "type": e["type"]} for e in edges_found],
            )

            return {
                "method": "lightrag",
                "entities_extracted": len(entities_found),
                "relations_extracted": len(edges_found),
                **created,
            }
        finally:
            import shutil
            shutil.rmtree(work_dir, ignore_errors=True)

    def _ingest_manual(self, db_id: str, text: str, source: str | None) -> dict:
        """Store text as a single document node."""
        name = source or f"document_{hashlib.md5(text[:100].encode()).hexdigest()[:8]}"
        props = {"content": text[:5000], "length": len(text)}
        if source:
            props["source"] = source
        node = kg_service.create_node(db_id, name, "document", props)
        return {
            "method": "manual",
            "nodes_created": 1,
            "edges_created": 0,
            "nodes": [node],
            "edges": [],
        }


# Singleton
ingestion_service = IngestionService()

"""RAG Chat service — hybrid retrieval + Gemini generation with KG-augmented context."""
import json
from typing import AsyncGenerator

from services.kg_service import kg_service
from services.embedding_service import embedding_service


RAG_SYSTEM_PROMPT = """You are a knowledge graph assistant. You answer questions based on information retrieved from a knowledge graph database.

When answering:
- Use the provided knowledge graph context to inform your responses
- Cite specific entities and relationships when relevant
- If the context doesn't contain enough information, say so honestly
- Be concise but thorough

Knowledge Graph Context:
{context}
"""


class RagChatService:
    """RAG chat combining hybrid KG retrieval with Gemini generation."""

    async def chat(self, db_id: str, query: str, history: list[dict],
                   mode: str = "hybrid", limit: int = 10) -> AsyncGenerator[str, None]:
        """Stream a RAG response using KG context."""

        # Step 1: Retrieve relevant nodes via hybrid search
        search_results = embedding_service.search(db_id, query, "hybrid", limit)
        source_nodes = []
        context_parts = []

        for r in search_results.get("results", []):
            node = r["node"]
            source_nodes.append({
                "id": node["id"],
                "name": node["name"],
                "type": node["type"],
            })
            props_str = ""
            if node.get("properties"):
                props = {k: v for k, v in node["properties"].items()
                         if k not in ("embedding", "vector") and len(str(v)) < 500}
                if props:
                    props_str = f" | Properties: {json.dumps(props)}"
            context_parts.append(
                f"- [{node['type']}] {node['name']}{props_str}"
            )

        # Step 2: Expand with graph neighbors (1 hop) for top results
        for r in search_results.get("results", [])[:3]:
            try:
                neighbors = kg_service.get_neighbors(db_id, r["node"]["id"], depth=1, limit=10)
                for edge in neighbors.get("edges", []):
                    src_name = next((n["name"] for n in neighbors["nodes"] if n["id"] == edge["source"]), edge["source"])
                    tgt_name = next((n["name"] for n in neighbors["nodes"] if n["id"] == edge["target"]), edge["target"])
                    context_parts.append(f"  Relation: {src_name} --{edge['type']}--> {tgt_name}")
            except Exception:
                pass

        context = "\n".join(context_parts) if context_parts else "No relevant knowledge found in the graph."

        # Step 3: Emit sources first
        yield json.dumps({"type": "sources", "nodes": source_nodes})

        # Step 4: Generate response with Gemini
        from config import GEMINI_API_KEY
        if not GEMINI_API_KEY:
            yield json.dumps({"type": "content", "text": "Error: GEMINI_API_KEY not configured"})
            return

        from google import genai

        client = genai.Client(api_key=GEMINI_API_KEY)
        system_prompt = RAG_SYSTEM_PROMPT.format(context=context)

        # Build conversation
        messages = []
        for msg in history[-10:]:  # Last 10 messages
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ("user", "model"):
                messages.append({"role": role, "parts": [{"text": content}]})

        messages.append({"role": "user", "parts": [{"text": query}]})

        try:
            response = client.models.generate_content_stream(
                model="gemini-2.5-flash",
                contents=messages,
                config={
                    "system_instruction": system_prompt,
                    "temperature": 0.7,
                    "max_output_tokens": 2048,
                },
            )

            for chunk in response:
                if chunk.text:
                    yield json.dumps({"type": "content", "text": chunk.text})

        except Exception as e:
            yield json.dumps({"type": "content", "text": f"Error generating response: {str(e)}"})


# Singleton
rag_chat_service = RagChatService()

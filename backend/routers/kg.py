"""Knowledge Graph API router — browse, search, CRUD, analytics, RAG, merge."""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/kg", tags=["Knowledge Graph"])


# ── Pydantic models ────────────────────────────────────────────────
class CreateDBRequest(BaseModel):
    name: str

class CreateNodeRequest(BaseModel):
    name: str
    type: str = "entity"
    properties: dict | None = None

class UpdateNodeRequest(BaseModel):
    name: str | None = None
    type: str | None = None
    properties: dict | None = None

class CreateEdgeRequest(BaseModel):
    source: str
    target: str
    type: str = "relates_to"
    properties: dict | None = None

class UpdateEdgeRequest(BaseModel):
    type: str | None = None
    properties: dict | None = None

class BulkCreateRequest(BaseModel):
    nodes: list[dict] = []
    edges: list[dict] = []

class SearchRequest(BaseModel):
    query: str
    mode: str = "hybrid"  # fts | embedding | hybrid
    limit: int = 20
    alpha: float = 0.40
    beta: float = 0.45
    gamma: float = 0.15

class MultiSearchRequest(BaseModel):
    query: str
    db_ids: list[str]
    mode: str = "hybrid"
    limit: int = 10

class IngestRequest(BaseModel):
    text: str
    method: str = "ai"  # ai | lightrag | manual
    source: str | None = None

class CompareRequest(BaseModel):
    db_id_a: str
    db_id_b: str

class MergeRequest(BaseModel):
    source_db: str
    target_db: str
    strategy: str = "union"  # union | intersection

class PathRequest(BaseModel):
    source_node: str
    target_node: str

class BatchDeleteRequest(BaseModel):
    node_type: str

class BatchRetypeRequest(BaseModel):
    old_type: str
    new_type: str

class ChatRequest(BaseModel):
    query: str
    history: list[dict] = []
    mode: str = "hybrid"  # hybrid | graphrag
    limit: int = 10

class EmbeddingGenerateRequest(BaseModel):
    strategy: str = "gemini"  # gemini | model2vec


# ── Phase A: Browse ─────────────────────────────────────────────────
@router.get("/databases")
async def list_databases():
    from services.kg_service import kg_service
    return kg_service.list_databases()


@router.get("/databases/{db_id}/stats")
async def get_stats(db_id: str):
    from services.kg_service import kg_service
    try:
        return kg_service.get_database_stats(db_id)
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(404, str(e))


@router.get("/databases/{db_id}/nodes")
async def list_nodes(db_id: str, node_type: str | None = None,
                     search: str | None = None, limit: int = 100, offset: int = 0):
    from services.kg_service import kg_service
    try:
        return kg_service.get_nodes(db_id, node_type, search, limit, offset)
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(404, str(e))


@router.get("/databases/{db_id}/nodes/{node_id}")
async def get_node(db_id: str, node_id: str):
    from services.kg_service import kg_service
    try:
        node = kg_service.get_node(db_id, node_id)
        if not node:
            raise HTTPException(404, "Node not found")
        return node
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(404, str(e))


@router.get("/databases/{db_id}/nodes/{node_id}/neighbors")
async def get_neighbors(db_id: str, node_id: str, depth: int = 1, limit: int = 50):
    from services.kg_service import kg_service
    try:
        return kg_service.get_neighbors(db_id, node_id, depth, min(limit, 200))
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(404, str(e))


@router.get("/databases/{db_id}/edges")
async def list_edges(db_id: str, edge_type: str | None = None,
                     limit: int = 100, offset: int = 0):
    from services.kg_service import kg_service
    try:
        return kg_service.get_edges(db_id, edge_type, limit, offset)
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(404, str(e))


@router.get("/databases/{db_id}/types")
async def get_types(db_id: str):
    from services.kg_service import kg_service
    try:
        return kg_service.get_types(db_id)
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(404, str(e))


# ── Phase B: Search ─────────────────────────────────────────────────
@router.post("/databases/{db_id}/search")
async def search_kg(db_id: str, req: SearchRequest):
    from services.embedding_service import embedding_service
    try:
        return embedding_service.search(db_id, req.query, req.mode,
                                        req.limit, req.alpha, req.beta, req.gamma)
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/search/multi")
async def multi_search(req: MultiSearchRequest):
    from services.embedding_service import embedding_service
    results = {}
    for db_id in req.db_ids:
        try:
            results[db_id] = embedding_service.search(
                db_id, req.query, req.mode, req.limit)
        except Exception as e:
            results[db_id] = {"error": str(e)}
    return results


@router.get("/databases/{db_id}/embedding-status")
async def embedding_status(db_id: str):
    from services.embedding_service import embedding_service
    try:
        return embedding_service.get_status(db_id)
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(404, str(e))


# ── Phase C: CRUD ───────────────────────────────────────────────────
@router.post("/databases")
async def create_database(req: CreateDBRequest):
    from services.kg_service import kg_service
    try:
        return kg_service.create_database(req.name)
    except (ValueError, FileExistsError) as e:
        raise HTTPException(400, str(e))


@router.post("/databases/{db_id}/nodes")
async def create_node(db_id: str, req: CreateNodeRequest):
    from services.kg_service import kg_service
    try:
        return kg_service.create_node(db_id, req.name, req.type, req.properties)
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(404, str(e))


@router.put("/databases/{db_id}/nodes/{node_id}")
async def update_node(db_id: str, node_id: str, req: UpdateNodeRequest):
    from services.kg_service import kg_service
    try:
        result = kg_service.update_node(db_id, node_id, req.name, req.type, req.properties)
        if not result:
            raise HTTPException(404, "Node not found")
        return result
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(404, str(e))


@router.delete("/databases/{db_id}/nodes/{node_id}")
async def delete_node(db_id: str, node_id: str):
    from services.kg_service import kg_service
    try:
        if not kg_service.delete_node(db_id, node_id):
            raise HTTPException(404, "Node not found")
        return {"deleted": True}
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(404, str(e))


@router.post("/databases/{db_id}/edges")
async def create_edge(db_id: str, req: CreateEdgeRequest):
    from services.kg_service import kg_service
    try:
        return kg_service.create_edge(db_id, req.source, req.target, req.type, req.properties)
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(404, str(e))


@router.put("/databases/{db_id}/edges/{edge_id}")
async def update_edge(db_id: str, edge_id: str, req: UpdateEdgeRequest):
    from services.kg_service import kg_service
    try:
        result = kg_service.update_edge(db_id, edge_id, req.type, req.properties)
        if not result:
            raise HTTPException(404, "Edge not found")
        return result
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(404, str(e))


@router.delete("/databases/{db_id}/edges/{edge_id}")
async def delete_edge(db_id: str, edge_id: str):
    from services.kg_service import kg_service
    try:
        if not kg_service.delete_edge(db_id, edge_id):
            raise HTTPException(404, "Edge not found")
        return {"deleted": True}
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(404, str(e))


@router.post("/databases/{db_id}/bulk")
async def bulk_create(db_id: str, req: BulkCreateRequest):
    from services.kg_service import kg_service
    try:
        return kg_service.bulk_create(db_id, req.nodes, req.edges)
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(404, str(e))


@router.post("/databases/{db_id}/ingest")
async def ingest_text(db_id: str, req: IngestRequest):
    from services.ingestion_service import ingestion_service
    try:
        return await ingestion_service.ingest(db_id, req.text, req.method, req.source)
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))


# ── Phase D: Analytics ──────────────────────────────────────────────
@router.get("/databases/{db_id}/analytics/summary")
async def analytics_summary(db_id: str):
    from services.analytics_service import analytics_service
    try:
        return analytics_service.summary(db_id)
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(404, str(e))


@router.get("/databases/{db_id}/analytics/centrality")
async def analytics_centrality(db_id: str, metric: str = "degree", top_k: int = 20):
    from services.analytics_service import analytics_service
    try:
        return analytics_service.centrality(db_id, metric, top_k)
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(404, str(e))


@router.get("/databases/{db_id}/analytics/communities")
async def analytics_communities(db_id: str):
    from services.analytics_service import analytics_service
    try:
        return analytics_service.communities(db_id)
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(404, str(e))


@router.post("/databases/{db_id}/analytics/path")
async def analytics_path(db_id: str, req: PathRequest):
    from services.analytics_service import analytics_service
    try:
        return analytics_service.shortest_path(db_id, req.source_node, req.target_node)
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(404, str(e))


@router.get("/databases/{db_id}/analytics/pagerank")
async def analytics_pagerank(db_id: str, top_k: int = 20):
    from services.analytics_service import analytics_service
    try:
        return analytics_service.centrality(db_id, "pagerank", top_k)
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(404, str(e))


@router.post("/compare")
async def compare_kgs(req: CompareRequest):
    from services.analytics_service import analytics_service
    try:
        return analytics_service.compare(req.db_id_a, req.db_id_b)
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(404, str(e))


@router.post("/diff")
async def diff_kgs(req: CompareRequest):
    from services.analytics_service import analytics_service
    try:
        return analytics_service.diff(req.db_id_a, req.db_id_b)
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(404, str(e))


@router.post("/merge")
async def merge_kgs(req: MergeRequest):
    from services.analytics_service import analytics_service
    try:
        return analytics_service.merge(req.source_db, req.target_db, req.strategy)
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/databases/{db_id}/batch/delete-by-type")
async def batch_delete(db_id: str, req: BatchDeleteRequest):
    from services.kg_service import kg_service
    try:
        count = kg_service.batch_delete_by_type(db_id, req.node_type)
        return {"deleted": count}
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(404, str(e))


@router.post("/databases/{db_id}/batch/retype")
async def batch_retype(db_id: str, req: BatchRetypeRequest):
    from services.kg_service import kg_service
    try:
        count = kg_service.batch_retype(db_id, req.old_type, req.new_type)
        return {"updated": count}
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(404, str(e))


# ── Phase D: RAG Chat (via unified agentic loop) ─────────────────────
@router.post("/databases/{db_id}/chat")
async def rag_chat(db_id: str, req: ChatRequest):
    from services.agentic_loop import agentic_loop
    try:
        async def event_stream():
            async for chunk in agentic_loop.run(
                messages=[],
                mode="rag",
                kg_db_id=db_id,
                rag_query=req.query,
                rag_history=req.history,
                rag_limit=req.limit,
                inject_skills=False,
            ):
                yield f"data: {json.dumps(chunk)}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(event_stream(), media_type="text/event-stream")
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(404, str(e))


# ── Phase D: Embeddings dashboard ───────────────────────────────────
@router.get("/databases/{db_id}/embeddings/projection")
async def embedding_projection(db_id: str, method: str = "pca", max_points: int = 500):
    from services.embedding_service import embedding_service
    try:
        return embedding_service.get_projection(db_id, method, max_points)
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(404, str(e))


@router.post("/databases/{db_id}/embeddings/generate")
async def generate_embeddings(db_id: str, req: EmbeddingGenerateRequest):
    from services.embedding_service import embedding_service
    try:
        return await embedding_service.generate_embeddings(db_id, req.strategy)
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/databases/{db_id}/embeddings/quality")
async def embedding_quality(db_id: str):
    from services.embedding_service import embedding_service
    try:
        return embedding_service.get_quality_metrics(db_id)
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(404, str(e))

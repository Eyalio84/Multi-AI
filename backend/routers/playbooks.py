"""Playbook search and retrieval endpoints."""
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from typing import Optional

from services.playbook_index import playbook_index

router = APIRouter()


@router.get("/playbooks")
async def list_playbooks():
    """List all playbooks with metadata."""
    return {"playbooks": playbook_index.list_all()}


@router.get("/playbooks/search")
async def search_playbooks(q: str = Query(...), category: Optional[str] = None):
    """Search playbooks by keyword and optional category."""
    results = playbook_index.search(q, category)
    return {"results": results, "query": q, "count": len(results)}


@router.get("/playbooks/categories")
async def list_categories():
    """List playbook categories with counts."""
    return {"categories": playbook_index.list_categories()}


@router.get("/playbooks/{filename}")
async def get_playbook(filename: str):
    """Get full playbook content by filename."""
    pb = playbook_index.get_playbook(filename)
    if not pb:
        return JSONResponse(status_code=404, content={"error": f"Playbook not found: {filename}"})
    return pb

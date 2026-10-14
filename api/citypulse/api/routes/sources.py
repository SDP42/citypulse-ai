from fastapi import APIRouter

from citypulse.core.errors import NotFound
from citypulse.sources.registry import load_register

router = APIRouter(prefix="/sources")


@router.get("")
def list_sources():
    return {"items": load_register()}


@router.get("/{source_id}/status")
def source_status(source_id: str):
    for s in load_register():
        if s["source_id"] == source_id:
            return s
    raise NotFound(f"Unknown source '{source_id}'.")

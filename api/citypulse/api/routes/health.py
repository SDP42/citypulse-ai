from fastapi import APIRouter

from citypulse import __version__
from citypulse.core.settings import get_settings

router = APIRouter()


@router.get("/health")
def health():
    s = get_settings()
    return {
        "status": "ok",
        "version": __version__,
        "data_mode": s.data_mode,
        "network": s.network,
        "llm_provider": s.llm_provider,
    }

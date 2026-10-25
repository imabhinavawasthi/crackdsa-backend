from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from app.dependencies import require_role
from app.utils.cache import cache_manager
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin/cache",
    tags=["Admin Cache Management"]
)

class InvalidateCacheRequest(BaseModel):
    namespace: str = "all"


@router.get("/stats", response_model=Dict[str, Any])
async def get_cache_stats(
    user: Dict[str, Any] = Depends(require_role("admin"))
):
    """
    Returns current in-memory cache statistics, hit rate, and breakdown by namespace.
    Requires admin privileges.
    """
    try:
        return cache_manager.get_stats()
    except Exception as e:
        logger.error(f"[AdminCache] Error fetching cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/invalidate")
async def invalidate_cache(
    payload: InvalidateCacheRequest,
    user: Dict[str, Any] = Depends(require_role("admin"))
):
    """
    Invalidates in-memory cache for a specified namespace, or all if 'all'.
    Supported namespaces: 'all', 'courses', 'live_classes', 'videos', 'problems', 'sheets', 'contests'.
    Requires admin privileges.
    """
    target = payload.namespace.strip().lower()
    try:
        if target in ("all", "*"):
            cleared = cache_manager.clear_all()
            return {
                "success": True,
                "message": f"Successfully cleared all cache ({cleared} keys purged).",
                "namespace": "all",
                "invalidated_count": cleared
            }
        else:
            invalidated = cache_manager.invalidate_namespace(target)
            return {
                "success": True,
                "message": f"Successfully invalidated namespace '{target}' ({invalidated} keys purged).",
                "namespace": target,
                "invalidated_count": invalidated
            }
    except Exception as e:
        logger.error(f"[AdminCache] Error invalidating cache target '{target}': {e}")
        raise HTTPException(status_code=500, detail=str(e))

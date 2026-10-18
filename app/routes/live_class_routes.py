from fastapi import APIRouter, HTTPException, Query, status
from typing import Optional
from app.schemas.live_class import LiveClassResponseSchema, LiveClassPaginatedResponse
from app.services.live_class_service import LiveClassService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/live-classes",
    tags=["Live Classes"]
)

@router.get("", response_model=LiveClassPaginatedResponse)
@router.get("/", response_model=LiveClassPaginatedResponse, include_in_schema=False)
def list_live_classes(
    status: Optional[str] = Query("all", description="Filter by status: all, live, upcoming, completed"),
    topic: Optional[str] = Query(None, description="Filter by topic (e.g. dsa, competitive-programming)"),
    search: Optional[str] = Query(None, description="Search by lecture name"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(10, ge=1, le=100, description="Number of classes per page"),
):
    """
    Fetch paginated live classes with search by lecture name, topic filter, and visibility enforcement
    """
    try:
        return LiveClassService.list_live_classes(
            status_filter=status,
            topic=topic,
            search=search,
            page=page,
            limit=limit,
        )
    except Exception as e:
        logger.error(f"Error fetching live classes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch live classes catalog"
        )

@router.get("/topics", response_model=list[str])
@router.get("/topics/", response_model=list[str], include_in_schema=False)
def get_live_class_topics():
    """
    Fetch all unique topics present in public videos
    """
    try:
        return LiveClassService.get_public_topics()
    except Exception as e:
        logger.error(f"Error fetching live class topics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch live class topics"
        )

@router.get("/{id_or_slug}", response_model=LiveClassResponseSchema)
@router.get("/{id_or_slug}/", response_model=LiveClassResponseSchema, include_in_schema=False)
def get_live_class(id_or_slug: str):
    """
    Fetch details of a single live class by UUID or slug
    """
    try:
        c = LiveClassService.get_class_by_id_or_slug(id_or_slug)
        if not c:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Live class '{id_or_slug}' not found"
            )
        return c
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching live class {id_or_slug}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch live class details"
        )

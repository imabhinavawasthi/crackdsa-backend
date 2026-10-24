from fastapi import APIRouter, HTTPException, Query, Depends, status
from typing import Optional, Dict, Any
from app.schemas.live_class import LiveClassResponseSchema, LiveClassPaginatedResponse
from app.services.live_class_service import LiveClassService
from app.dependencies import get_current_user_optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/live-classes",
    tags=["Live Classes"]
)

@router.get("/featured", response_model=Optional[LiveClassResponseSchema])
@router.get("/featured/", response_model=Optional[LiveClassResponseSchema], include_in_schema=False)
def get_featured_dashboard_class(
    user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """
    Fetch a single featured live class for dashboard:
    1. Most recent ongoing live class, OR
    2. Most recent upcoming scheduled class (closest), OR
    3. Single most recent completed class.
    Non-pro users on non-free classes receive redacted sensitive links and is_locked=True.
    """
    try:
        return LiveClassService.get_dashboard_featured_class(user=user)
    except Exception as e:
        logger.error(f"Error fetching dashboard featured live class: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch dashboard live class"
        )

@router.get("", response_model=LiveClassPaginatedResponse)
@router.get("/", response_model=LiveClassPaginatedResponse, include_in_schema=False)
def list_live_classes(
    status: Optional[str] = Query("all", description="Filter by status: all, live, upcoming, completed, free"),
    topic: Optional[str] = Query(None, description="Filter by topic (e.g. dsa, competitive-programming)"),
    search: Optional[str] = Query(None, description="Search by lecture name"),
    visibility: Optional[str] = Query(None, description="Filter by visibility: all, free, public"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(10, ge=1, le=100, description="Number of classes per page"),
    user: Optional[Dict[str, Any]] = Depends(get_current_user_optional),
):
    """
    Fetch paginated live classes with search by lecture name, topic filter, and visibility enforcement.
    Non-pro users receive redacted sensitive fields for non-free classes.
    """
    try:
        return LiveClassService.list_live_classes(
            status_filter=status,
            topic=topic,
            search=search,
            visibility=visibility,
            page=page,
            limit=limit,
            user=user,
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
def get_live_class(
    id_or_slug: str,
    user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """
    Fetch details of a single live class by UUID or slug.
    If class is not free and user is not Pro, sensitive links are redacted and is_locked=True.
    """
    try:
        c = LiveClassService.get_class_by_id_or_slug(id_or_slug, user=user)
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

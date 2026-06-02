from fastapi import APIRouter, HTTPException, Query, Depends, status
from uuid import UUID
from app.services.instructor_service import InstructorService
from app.schemas.instructor import (
    InstructorCreateSchema,
    InstructorUpdateSchema,
    InstructorResponseSchema,
    InstructorListResponseSchema,
)
from app.dependencies import verify_admin_token
import logging

logger = logging.getLogger(__name__)

# --- Public Router ---
public_router = APIRouter(
    prefix="/instructors",
    tags=["Instructors (Public)"]
)

# --- Admin Router ---
admin_router = APIRouter(
    prefix="/admin/instructors",
    tags=["Instructors (Admin)"]
)


# ============ PUBLIC ENDPOINTS ============

@public_router.get("", response_model=InstructorListResponseSchema)
@public_router.get("/", response_model=InstructorListResponseSchema, include_in_schema=False)
def list_instructors(
    limit: int = Query(20, ge=1, le=100, description="Number of instructors to fetch"),
    offset: int = Query(0, ge=0, description="Number of instructors to skip"),
):
    """
    Get a list of all active instructors (public endpoint).
    
    **Query Parameters:**
    - `limit`: Number of results (default: 20, max: 100)
    - `offset`: Pagination offset (default: 0)
    
    **Returns:** List of active instructors with pagination metadata
    """
    try:
        result = InstructorService.list_instructors(limit=limit, offset=offset, include_inactive=False)
        return InstructorListResponseSchema(**result)
    except Exception as e:
        logger.error(f"Error listing instructors: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch instructors"
        )


@public_router.get("/search", response_model=list[InstructorResponseSchema])
@public_router.get("/search/", response_model=list[InstructorResponseSchema], include_in_schema=False)
def search_instructors(
    q: str = Query(..., min_length=1, description="Search query (name or role)"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
):
    """
    Search instructors by name or role (public endpoint).
    
    **Query Parameters:**
    - `q`: Search query string (required, min 1 character)
    - `limit`: Maximum results to return (default: 10, max: 50)
    
    **Returns:** List of matching instructors
    """
    try:
        instructors = InstructorService.search_instructors(query=q, limit=limit)
        return instructors
    except Exception as e:
        logger.error(f"Error searching instructors: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search instructors"
        )


@public_router.get("/{instructor_id}", response_model=InstructorResponseSchema)
@public_router.get("/{instructor_id}/", response_model=InstructorResponseSchema, include_in_schema=False)
def get_instructor(instructor_id: UUID):
    """
    Get a specific instructor by ID (public endpoint).
    
    **Path Parameters:**
    - `instructor_id`: UUID of the instructor
    
    **Returns:** Instructor details
    """
    try:
        instructor = InstructorService.get_instructor_by_id(instructor_id)
        return instructor
    except Exception as e:
        logger.error(f"Error fetching instructor {instructor_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Instructor with id {instructor_id} not found"
        )


# ============ ADMIN ENDPOINTS ============

@admin_router.post("", response_model=InstructorResponseSchema, status_code=status.HTTP_201_CREATED)
@admin_router.post("/", response_model=InstructorResponseSchema, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_instructor(
    data: InstructorCreateSchema,
    admin_user = Depends(verify_admin_token),
):
    """
    Create a new instructor (admin only).
    
    **Required Authorization:** Admin token in Authorization header
    
    **Request Body:** InstructorCreateSchema
    
    **Returns:** Created instructor with ID and timestamps
    """
    try:
        instructor = InstructorService.create_instructor(data)
        logger.info(f"Admin {admin_user['id']} created instructor: {instructor.id}")
        return instructor
    except Exception as e:
        logger.error(f"Error creating instructor: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create instructor: {str(e)}"
        )


@admin_router.put("/{instructor_id}", response_model=InstructorResponseSchema)
@admin_router.put("/{instructor_id}/", response_model=InstructorResponseSchema, include_in_schema=False)
def update_instructor(
    instructor_id: UUID,
    data: InstructorUpdateSchema,
    admin_user = Depends(verify_admin_token),
):
    """
    Update an instructor's details (admin only).
    
    **Required Authorization:** Admin token in Authorization header
    
    **Path Parameters:**
    - `instructor_id`: UUID of the instructor to update
    
    **Request Body:** InstructorUpdateSchema (all fields optional)
    
    **Returns:** Updated instructor details
    """
    try:
        instructor = InstructorService.update_instructor(instructor_id, data)
        logger.info(f"Admin {admin_user['id']} updated instructor: {instructor_id}")
        return instructor
    except Exception as e:
        logger.error(f"Error updating instructor {instructor_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Instructor not found or update failed: {str(e)}"
        )


@admin_router.delete("/{instructor_id}", status_code=status.HTTP_204_NO_CONTENT)
@admin_router.delete("/{instructor_id}/", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
def delete_instructor(
    instructor_id: UUID,
    hard_delete: bool = Query(False, description="If true, permanently delete; if false, soft delete"),
    admin_user = Depends(verify_admin_token),
):
    """
    Delete an instructor (admin only).
    
    **Required Authorization:** Admin token in Authorization header
    
    **Path Parameters:**
    - `instructor_id`: UUID of the instructor to delete
    
    **Query Parameters:**
    - `hard_delete`: If true, permanently delete from database; if false, soft delete (default: false)
    
    **Returns:** 204 No Content
    """
    try:
        InstructorService.delete_instructor(instructor_id, hard_delete=hard_delete)
        logger.info(f"Admin {admin_user['id']} deleted instructor: {instructor_id} (hard_delete={hard_delete})")
        return None
    except Exception as e:
        logger.error(f"Error deleting instructor {instructor_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Instructor not found or deletion failed: {str(e)}"
        )


@admin_router.get("", response_model=InstructorListResponseSchema)
@admin_router.get("/", response_model=InstructorListResponseSchema, include_in_schema=False)
def admin_list_all_instructors(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    include_inactive: bool = Query(True, description="Include inactive instructors"),
    admin_user = Depends(verify_admin_token),
):
    """
    List all instructors including inactive ones (admin only).
    
    **Required Authorization:** Admin token in Authorization header
    
    **Query Parameters:**
    - `limit`: Number of results (default: 20, max: 100)
    - `offset`: Pagination offset (default: 0)
    - `include_inactive`: Include inactive instructors (default: true)
    
    **Returns:** List of all instructors with pagination metadata
    """
    try:
        result = InstructorService.list_instructors(
            limit=limit,
            offset=offset,
            include_inactive=include_inactive
        )
        logger.info(f"Admin {admin_user['id']} accessed full instructor list")
        return InstructorListResponseSchema(**result)
    except Exception as e:
        logger.error(f"Error listing all instructors: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch instructors"
        )


@admin_router.get("/{instructor_id}", response_model=InstructorResponseSchema)
@admin_router.get("/{instructor_id}/", response_model=InstructorResponseSchema, include_in_schema=False)
def get_instructor_admin(
    instructor_id: UUID,
    admin_user = Depends(verify_admin_token),
):
    """
    Get a specific instructor by ID as an admin (can fetch inactive/soft-deleted ones).
    """
    try:
        instructor = InstructorService.get_instructor_by_id(instructor_id)
        return instructor
    except Exception as e:
        logger.error(f"Error fetching instructor {instructor_id} for admin: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Instructor with id {instructor_id} not found"
        )

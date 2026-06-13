from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List
from app.schemas.course import (
    CourseResponseSchema,
    CourseSummaryResponseSchema,
    CourseSection,
    CourseCreateSchema,
    CourseUpdateSchema,
)
from app.services.course_service import CourseService
from app.dependencies import verify_admin_token
import logging

logger = logging.getLogger(__name__)

# --- Public Router ---
# General student access: only list active courses and retrieve by ID/slug
public_router = APIRouter(
    prefix="/courses",
    tags=["Courses (Public)"]
)

@public_router.get("", response_model=List[CourseSummaryResponseSchema])
@public_router.get("/", response_model=List[CourseSummaryResponseSchema], include_in_schema=False)
def list_courses_public():
    """
    Fetch all active SDE preparation courses from the CrackDSA Academy catalog.
    """
    try:
        return CourseService.list_courses(all_status=False)
    except Exception as e:
        logger.error(f"Error fetching academy courses: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch course catalog"
        )

@public_router.get("/{course_id}", response_model=CourseSummaryResponseSchema)
@public_router.get("/{course_id}/", response_model=CourseSummaryResponseSchema, include_in_schema=False)
def get_course_public(course_id: str):
    """
    Fetch a specific course by its unique ID/slug.
    """
    try:
        return CourseService.get_course_summary_by_id(course_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error fetching course details for '{course_id}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch course details"
        )

@public_router.get("/{course_id}/curriculum", response_model=List[CourseSection])
def get_course_curriculum_public(course_id: str):
    """
    Fetch only the full curriculum tree for a specific course by its unique ID/slug.
    """
    try:
        return CourseService.get_course_curriculum(course_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error fetching curriculum details for '{course_id}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch course curriculum"
        )
# --- Admin Router ---
# Full CRUD control: reserved for SDE admins, includes draft/upcoming listings
admin_router = APIRouter(
    prefix="/admin/courses",
    tags=["Courses (Admin)"]
)

@admin_router.get("", response_model=List[CourseResponseSchema])
@admin_router.get("/", response_model=List[CourseResponseSchema], include_in_schema=False)
def list_courses_admin(admin_user = Depends(verify_admin_token)):
    """
    List all active + draft + upcoming courses for administrative audit.
    Requires 'admin' role.
    """
    try:
        return CourseService.list_courses(all_status=True)
    except Exception as e:
        logger.error(f"Error listing admin course catalog: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch course catalog"
        )

@admin_router.get("/{course_id}", response_model=CourseResponseSchema)
@admin_router.get("/{course_id}/", response_model=CourseResponseSchema, include_in_schema=False)
def get_course_admin(course_id: str, admin_user = Depends(verify_admin_token)):
    """
    Fetch any course by ID/slug (even if draft/upcoming).
    Requires 'admin' role.
    """
    try:
        return CourseService.get_course_by_id(course_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error fetching course details for '{course_id}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch course details"
        )

@admin_router.post("", response_model=CourseResponseSchema, status_code=status.HTTP_201_CREATED)
@admin_router.post("/", response_model=CourseResponseSchema, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_course_admin(
    data: CourseCreateSchema,
    admin_user = Depends(verify_admin_token),
):
    """
    Create a new course listing (Admin only).
    """
    try:
        course = CourseService.create_course(data)
        logger.info(f"Admin {admin_user['id']} successfully created course: {course.id}")
        return course
    except Exception as e:
        logger.error(f"Error creating course: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create course: {str(e)}"
        )

@admin_router.put("/{course_id}", response_model=CourseResponseSchema)
@admin_router.put("/{course_id}/", response_model=CourseResponseSchema, include_in_schema=False)
def update_course_admin(
    course_id: str,
    data: CourseUpdateSchema,
    admin_user = Depends(verify_admin_token),
):
    """
    Update an existing course's details, tags, co-instructors, or dynamic syllabus JSONB (Admin only).
    """
    try:
        course = CourseService.update_course(course_id, data)
        logger.info(f"Admin {admin_user['id']} successfully updated course: {course_id}")
        return course
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating course {course_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update course: {str(e)}"
        )

@admin_router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
@admin_router.delete("/{course_id}/", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
def delete_course_admin(
    course_id: str,
    hard_delete: bool = Query(False, description="If true, permanently delete from DB; if false, soft-delete"),
    admin_user = Depends(verify_admin_token),
):
    """
    Delete a course listing (Admin only). Defaults to soft-deleting.
    """
    try:
        CourseService.delete_course(course_id, hard_delete=hard_delete)
        logger.info(f"Admin {admin_user['id']} successfully deleted course: {course_id} (hard={hard_delete})")
        return None
    except Exception as e:
        logger.error(f"Error deleting course {course_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Failed to delete course or course not found: {str(e)}"
        )

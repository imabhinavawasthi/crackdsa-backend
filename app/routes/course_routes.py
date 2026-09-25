from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List, Optional, Dict, Any
from app.schemas.course import (
    CourseResponseSchema,
    CourseSummaryResponseSchema,
    CourseBasicResponseSchema,
    CourseDetailResponseSchema,
    CourseVideoAccessResponse,
    CourseSection,
    CourseCreateSchema,
    CourseUpdateSchema,
    BatchTopicRequestSchema,
    BatchTopicResponseSchema,
)
from app.services.course_service import CourseService
from app.dependencies import verify_admin_token, get_current_user, get_current_user_optional
import logging

logger = logging.getLogger(__name__)

# --- Public Router ---
public_router = APIRouter(
    prefix="/courses",
    tags=["Courses (Public)"]
)

@public_router.get("", response_model=List[CourseBasicResponseSchema])
@public_router.get("/", response_model=List[CourseBasicResponseSchema], include_in_schema=False)
def list_courses_public(include_upcoming: bool = Query(False, description="Set to true to also include upcoming courses alongside active")):
    """
    Fetch active SDE preparation courses with clean basic metadata:
    title, description, id, category, tags, is_pro, is_popular, price, original_price, status, slug
    """
    try:
        return CourseService.list_basic_courses(status="active", include_upcoming=include_upcoming)
    except Exception as e:
        logger.error(f"Error fetching active courses: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch course catalog"
        )

@public_router.get("/purchased", response_model=List[CourseBasicResponseSchema])
@public_router.get("/purchased/", response_model=List[CourseBasicResponseSchema], include_in_schema=False)
def list_purchased_courses(user: Dict[str, Any] = Depends(get_current_user)):
    """
    Fetch all courses accessible to the authenticated user.
    If the user has an active Pro subscription, returns all Pro courses plus any individual course purchases.
    """
    try:
        return CourseService.get_purchased_courses(user)
    except Exception as e:
        logger.error(f"Error fetching purchased courses for user {user.get('id')}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch purchased courses"
        )

@public_router.get("/{course_id_or_slug}", response_model=CourseDetailResponseSchema)
@public_router.get("/{course_id_or_slug}/", response_model=CourseDetailResponseSchema, include_in_schema=False)
def get_course_detail(
    course_id_or_slug: str,
    user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """
    Fetch full course details by unique UUID or SEO slug (every column, but without curriculum).
    If caller has admin credentials, returns the course regardless of status (active, draft, upcoming).
    Otherwise returns only if status is 'active'.
    """
    is_admin = bool(user and "admin" in (user.get("roles") or []))
    try:
        return CourseService.get_course_detail(course_id_or_slug, is_admin=is_admin)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error fetching course details for '{course_id_or_slug}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch course details"
        )

@public_router.get("/{course_id_or_slug}/curriculum", response_model=List[CourseSection])
def get_course_curriculum(
    course_id_or_slug: str,
    topic: Optional[str] = Query(None, description="Pass topic title or section ID to return only that topic curriculum"),
    user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """
    Fetch the curriculum tree for a course by UUID or slug.
    If 'topic' query parameter is provided, returns only that specific topic/section.
    """
    is_admin = bool(user and "admin" in (user.get("roles") or []))
    try:
        return CourseService.get_course_curriculum_by_topic(course_id_or_slug, topic=topic, is_admin=is_admin)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error fetching curriculum for '{course_id_or_slug}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch course curriculum"
        )

@public_router.get("/{course_id_or_slug}/curriculum/topic/{topic_name}", response_model=List[CourseSection])
def get_course_curriculum_by_topic_path(
    course_id_or_slug: str,
    topic_name: str,
    user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """
    Fetch only the specific topic/section curriculum by topic name.
    """
    is_admin = bool(user and "admin" in (user.get("roles") or []))
    try:
        return CourseService.get_course_curriculum_by_topic(course_id_or_slug, topic=topic_name, is_admin=is_admin)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error fetching topic curriculum for '{course_id_or_slug}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch topic curriculum"
        )

@public_router.get("/{course_id_or_slug}/video/{section_id}/{item_id}", response_model=CourseVideoAccessResponse)
def get_course_video_item(
    course_id_or_slug: str,
    section_id: str,
    item_id: str,
    user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """
    Access video streaming details for a curriculum video item.
    - Free lectures (is_free=true) are accessible to any user (even unauthenticated).
    - Paid lectures require an authenticated user with an active Pro subscription or course purchase.
    """
    try:
        return CourseService.get_course_video(
            course_id_or_slug=course_id_or_slug,
            section_id=section_id,
            item_id=item_id,
            user=user
        )
    except PermissionError as e:
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error fetching video item '{item_id}' in course '{course_id_or_slug}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch video details"
        )

@public_router.post("/{course_id}/batch-topic-details", response_model=BatchTopicResponseSchema)
@public_router.post("/{course_id}/batch-topic-details/", response_model=BatchTopicResponseSchema, include_in_schema=False)
def get_batch_topic_details_public(course_id: str, body: BatchTopicRequestSchema):
    """
    Fetch dynamic topic details (chapters, items, videos, problems, upcoming status)
    for multiple requested topic titles in a single batch call.
    """
    try:
        return CourseService.get_batch_topic_details(course_id, body.topics)
    except Exception as e:
        logger.error(f"Error fetching batch topic details for '{course_id}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch batch topic details"
        )

# --- Admin Router ---
# Full CRUD control: reserved for SDE admins, includes draft/upcoming listings
admin_router = APIRouter(
    prefix="/admin/courses",
    tags=["Courses (Admin)"]
)

@admin_router.get("", response_model=List[CourseBasicResponseSchema])
@admin_router.get("/", response_model=List[CourseBasicResponseSchema], include_in_schema=False)
def list_courses_admin(admin_user = Depends(verify_admin_token)):
    """
    List all courses (active + draft + upcoming) with basic metadata for administrative audit.
    Requires 'admin' role.
    """
    try:
        return CourseService.list_basic_courses(status=None)
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

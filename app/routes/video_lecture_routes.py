from typing import List, Optional
from fastapi import APIRouter, Depends
from app.schemas.video_lecture import VideoLecture, VideoLectureCreate, VideoLectureUpdate
from app.controllers import video_lecture_controller
from app.dependencies import require_role_with_token, get_token
from uuid import UUID

# --- Public Router ---
# General student access: only list active lectures and retrieve by ID
public_router = APIRouter(
    prefix="/video-lectures",
    tags=["Video Lectures (Public)"]
)

@public_router.get("", response_model=List[VideoLecture])
async def list_lectures_public(token: Optional[str] = Depends(get_token)):
    """
    List all active video lectures for student discovery.
    """
    return await video_lecture_controller.list_lectures_handler(include_inactive=False, token=token)

@public_router.get("/{id}", response_model=VideoLecture)
async def get_lecture_public(id: UUID, token: Optional[str] = Depends(get_token)):
    """
    Get a single active video lecture by its UUID.
    """
    return await video_lecture_controller.get_lecture_handler(id, include_inactive=False, token=token)


# --- Admin Router ---
# Full CRUD control: reserved for SDE moderators, includes soft-deleted items
admin_router = APIRouter(
    prefix="/admin/video-lectures",
    tags=["Video Lectures (Admin)"]
)

@admin_router.get("", response_model=List[VideoLecture])
async def list_lectures_admin(auth_data: dict = Depends(require_role_with_token("admin"))):
    """
    List all video lectures (active + soft-deleted) for administrative audit.
    Requires 'admin' role.
    """
    return await video_lecture_controller.list_lectures_handler(include_inactive=True, token=auth_data["token"])

@admin_router.get("/{id}", response_model=VideoLecture)
async def get_lecture_admin(id: UUID, auth_data: dict = Depends(require_role_with_token("admin"))):
    """
    Get any video lecture by its UUID (even if soft-deleted).
    Requires 'admin' role.
    """
    return await video_lecture_controller.get_lecture_handler(id, include_inactive=True, token=auth_data["token"])

@admin_router.post("", response_model=VideoLecture)
async def create_lecture_admin(lecture_data: VideoLectureCreate, auth_data: dict = Depends(require_role_with_token("admin"))):
    """
    Create a new reusable video lecture asset.
    Requires 'admin' role.
    """
    return await video_lecture_controller.create_lecture_handler(lecture_data, token=auth_data["token"])

@admin_router.put("/{id}", response_model=VideoLecture)
async def update_lecture_admin(id: UUID, update_data: VideoLectureUpdate, auth_data: dict = Depends(require_role_with_token("admin"))):
    """
    Update an existing video lecture asset details (supports partial updates).
    Requires 'admin' role.
    """
    return await video_lecture_controller.update_lecture_handler(id, update_data, token=auth_data["token"])

@admin_router.delete("/{id}")
async def delete_lecture_admin(id: UUID, auth_data: dict = Depends(require_role_with_token("admin"))):
    """
    Soft delete a video lecture.
    Requires 'admin' role.
    """
    return await video_lecture_controller.delete_lecture_handler(id, token=auth_data["token"])

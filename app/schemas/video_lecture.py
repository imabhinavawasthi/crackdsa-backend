from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID

# --- Video Lecture Base Schema ---
class VideoLectureBase(BaseModel):
    title: str
    description: Optional[str] = None
    video_url: Optional[str] = None
    duration_seconds: int = 0
    thumbnail_url: Optional[str] = None
    resources: Dict[str, Any] = Field(default_factory=dict)
    attributes: Dict[str, Any] = Field(default_factory=dict)

# --- Video Lecture Creation Schema ---
class VideoLectureCreate(VideoLectureBase):
    video_url: str
    is_free: Optional[bool] = None

# --- Video Lecture Update Schema ---
class VideoLectureUpdate(BaseModel):
    """
    Schema supporting partial updates for Video Lectures.
    """
    title: Optional[str] = None
    description: Optional[str] = None
    video_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    thumbnail_url: Optional[str] = None
    resources: Optional[Dict[str, Any]] = None
    attributes: Optional[Dict[str, Any]] = None
    is_free: Optional[bool] = None

# --- Complete Video Lecture Response Schema ---
class VideoLecture(VideoLectureBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    is_free: Optional[bool] = False
    is_locked: Optional[bool] = False

    class Config:
        from_attributes = True

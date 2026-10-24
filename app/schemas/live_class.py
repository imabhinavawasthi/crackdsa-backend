from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class LiveClassResponseSchema(BaseModel):
    id: str
    class_name: str
    class_topic: Optional[str] = None
    instructor_name: Optional[str] = None
    class_time_epoch: Optional[int] = 0
    class_duration: Optional[int] = 60
    class_link: Optional[str] = None
    class_recording: Optional[str] = None
    class_notes: Optional[str] = None
    class_subtopics: Optional[List[str]] = Field(default_factory=list)
    class_url_slug: Optional[str] = ""
    status: Optional[str] = "completed"  # live, upcoming, completed
    visibility: Optional[str] = "public"
    is_locked: Optional[bool] = False
    thumbnail_url: Optional[str] = None
    class_image: Optional[str] = None
    created_at: Optional[str] = None

class LiveClassCounts(BaseModel):
    all: int = 0
    live: int = 0
    upcoming: int = 0
    completed: int = 0
    free: int = 0

class LiveClassPaginatedResponse(BaseModel):
    items: List[LiveClassResponseSchema]
    total_count: int
    page: int
    limit: int
    total_pages: int
    counts: LiveClassCounts
    available_topics: List[str] = Field(default_factory=list)
    upcoming_classes: List[LiveClassResponseSchema] = Field(default_factory=list)

class LiveClassCreateSchema(BaseModel):
    class_name: str
    class_topic: Optional[str] = None
    instructor_name: Optional[str] = None
    class_time_epoch: int
    class_duration: Optional[int] = 60
    class_link: Optional[str] = None
    class_recording: Optional[str] = None
    class_notes: Optional[str] = None
    class_subtopics: Optional[List[str]] = Field(default_factory=list)
    class_url_slug: Optional[str] = None
    visibility: Optional[str] = "private"

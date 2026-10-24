from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum

class AssetTypeEnum(str, Enum):
    VIDEO = "video"
    PROBLEM = "problem"
    ARTICLE = "article"

class AssetStatusEnum(str, Enum):
    PENDING = "pending"
    DONE = "done"
    REVISION = "revision"

class NoteSchema(BaseModel):
    id: str
    text: str
    createdAt: str  # Matches frontend NotesTab display format

class UserAssetStateResponseSchema(BaseModel):
    id: str                     # UUID string
    user_id: str                # UUID string
    asset_id: str
    asset_type: AssetTypeEnum
    status: AssetStatusEnum
    is_bookmarked: bool
    bookmarked_at: Optional[datetime] = None
    notes: List[NoteSchema] = []
    metadata: dict = {}
    last_interacted_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserAssetStateUpdateSchema(BaseModel):
    status: Optional[AssetStatusEnum] = None
    is_bookmarked: Optional[bool] = None
    notes: Optional[List[NoteSchema]] = None
    metadata: Optional[dict] = None

class UserActivitySummarySchema(BaseModel):
    current_streak: int
    max_streak: int
    current_month: str
    month_active_dates: List[str]
    month_active_count: int
    total_active_days: int
    completed_lessons_count: int = 0
    cp_solved_count: int = 0

class UserBookmarkItemSchema(BaseModel):
    asset_id: str
    asset_type: str
    title: str
    subtitle: str
    href: str
    badge: Optional[str] = None
    badge_color: Optional[str] = None
    difficulty: Optional[str] = None
    status: Optional[str] = "pending"
    bookmarked_at: Optional[str] = None
    updated_at: Optional[str] = None
    notes_count: int = 0
    metadata: dict = {}

class UserNoteItemSchema(BaseModel):
    id: str
    text: str
    created_at: str
    asset_id: str
    asset_type: str
    title: str
    subtitle: str
    href: str
    badge: Optional[str] = None
    badge_color: Optional[str] = None
    status: Optional[str] = "pending"

class ProblemDifficultyStatsSchema(BaseModel):
    total: int = 0
    easy: int = 0
    medium: int = 0
    hard: int = 0

class UserProgressSummarySchema(BaseModel):
    problems_solved: ProblemDifficultyStatsSchema
    total_problems: ProblemDifficultyStatsSchema
    articles_read: int = 0
    lectures_completed: int = 0
    bookmarked_count: int = 0
    streak: int = 0
    recent_bookmarks: List[UserBookmarkItemSchema] = []
    recent_notes: List[UserNoteItemSchema] = []
    heatmap_activity: dict = {}
